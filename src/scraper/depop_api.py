"""Depop API-based scraping functionality."""

import asyncio
import logging
import random
import time
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from .parser import DataParser, DepopItem

logger = logging.getLogger(__name__)


# User-Agent pool for rotation to avoid detection
USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
        "Gecko/20100101 Firefox/121.0"
    ),
]


class DepopAPI:
    """Handle API-based scraping of Depop data."""

    # Depop API endpoints
    BASE_URL = "https://webapi.depop.com/api/v2"
    SEARCH_ENDPOINT = "/search/products"

    # Mobile API (sometimes has different data)
    MOBILE_BASE_URL = "https://api.depop.com/api/v1"

    # Headers to mimic browser requests with anti-detection measures
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Origin": "https://www.depop.com",
        "Referer": "https://www.depop.com/",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0  # seconds
    BACKOFF_MULTIPLIER = 2.0

    def __init__(
        self,
        rate_limit_delay: float = 1.0,
        timeout: float = 30.0,
        enable_browser_fallback: bool = True,
    ):
        """
        Initialize the Depop API scraper.

        Args:
            rate_limit_delay: Delay between requests in seconds.
            timeout: Request timeout in seconds.
            enable_browser_fallback: Whether to use browser scraping as fallback.
        """
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self.enable_browser_fallback = enable_browser_fallback
        self._last_request_time: float = 0
        self._client: Optional[httpx.AsyncClient] = None
        self._browser_scraper: Any = None

    async def __aenter__(self) -> "DepopAPI":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
        if self._browser_scraper:
            await self._browser_scraper.__aexit__(exc_type, exc_val, exc_tb)

    def _get_rotated_headers(self) -> dict[str, str]:
        """Get headers with a randomly rotated User-Agent."""
        headers = self.DEFAULT_HEADERS.copy()
        headers["User-Agent"] = random.choice(USER_AGENTS)
        return headers

    async def _get_browser_scraper(self) -> Any:
        """
        Get or initialize the browser scraper for fallback.

        Returns:
            BrowserScraper instance or None if not available.
        """
        if self._browser_scraper is not None:
            return self._browser_scraper

        try:
            from .browser import BrowserScraper

            if not BrowserScraper.is_available():
                logger.warning("Browser fallback not available: Playwright not installed")
                return None

            self._browser_scraper = BrowserScraper()
            await self._browser_scraper.__aenter__()
            return self._browser_scraper
        except ImportError:
            logger.warning("Browser fallback not available: browser module not found")
            return None
        except Exception as e:
            logger.warning("Failed to initialize browser fallback: %s", e)
            return None

    async def _rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.time()

    async def _make_request(
        self, url: str, params: Optional[dict[str, Any]] = None
    ) -> Optional[dict[str, Any]]:
        """
        Make a rate-limited API request with retry logic.

        Args:
            url: The URL to request.
            params: Optional query parameters.

        Returns:
            JSON response as dictionary or None if failed.
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        await self._rate_limit()

        last_exception: Optional[Exception] = None
        backoff = self.INITIAL_BACKOFF

        for attempt in range(self.MAX_RETRIES):
            try:
                # Rotate headers for each retry attempt
                headers = self._get_rotated_headers()
                response = await self._client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                last_exception = e
                status_code = e.response.status_code

                # Only retry on 403 (Forbidden) or 429 (Too Many Requests)
                if status_code in (403, 429):
                    logger.warning(
                        "HTTP %d on attempt %d/%d, retrying in %.1fs...",
                        status_code,
                        attempt + 1,
                        self.MAX_RETRIES,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= self.BACKOFF_MULTIPLIER
                    continue
                else:
                    logger.error(
                        "HTTP error: %d - %s",
                        e.response.status_code,
                        e.response.text[:200],
                    )
                    return None
            except httpx.RequestError as e:
                last_exception = e
                logger.warning(
                    "Request error on attempt %d/%d: %s",
                    attempt + 1,
                    self.MAX_RETRIES,
                    e,
                )
                await asyncio.sleep(backoff)
                backoff *= self.BACKOFF_MULTIPLIER
                continue
            except Exception as e:
                logger.error("Unexpected error: %s", e)
                return None

        # All retries exhausted
        if last_exception:
            logger.error(
                "All %d retry attempts failed. Last error: %s",
                self.MAX_RETRIES,
                last_exception,
            )
        return None

    async def search_sold_items(
        self,
        keyword: str,
        category: str = "",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DepopItem]:
        """
        Search for sold items on Depop.

        Args:
            keyword: Search keyword.
            category: Category filter.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            List of DepopItem objects.
        """
        params: dict[str, Any] = {
            "what": keyword,
            "status": "sold",
            "itemsPerPage": min(limit, 100),
            "offset": offset,
        }

        if category:
            params["category"] = category

        if min_price is not None:
            params["priceMin"] = int(min_price * 100)  # API uses cents

        if max_price is not None:
            params["priceMax"] = int(max_price * 100)

        url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"
        data = await self._make_request(url, params)

        if not data:
            # Fallback to browser scraping if enabled
            if self.enable_browser_fallback:
                logger.info("API request failed, falling back to browser scraping")
                browser = await self._get_browser_scraper()
                if browser:
                    return await browser.search_sold_items(
                        keyword=keyword,
                        category=category,
                        min_price=min_price,
                        max_price=max_price,
                    )
            return []

        products = data.get("products", data.get("items", []))
        items = []

        for product_data in products:
            item = DataParser.parse_api_product(product_data)
            if item:
                items.append(item)

        return items

    async def search_available_items(
        self,
        keyword: str,
        category: str = "",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DepopItem]:
        """
        Search for available (not sold) items on Depop.

        Args:
            keyword: Search keyword.
            category: Category filter.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            List of DepopItem objects.
        """
        params: dict[str, Any] = {
            "what": keyword,
            "status": "available",
            "itemsPerPage": min(limit, 100),
            "offset": offset,
        }

        if category:
            params["category"] = category

        if min_price is not None:
            params["priceMin"] = int(min_price * 100)

        if max_price is not None:
            params["priceMax"] = int(max_price * 100)

        url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"
        data = await self._make_request(url, params)

        if not data:
            # Fallback to browser scraping if enabled
            if self.enable_browser_fallback:
                logger.info("API request failed, falling back to browser scraping")
                browser = await self._get_browser_scraper()
                if browser:
                    return await browser.search_available_items(
                        keyword=keyword,
                        category=category,
                        min_price=min_price,
                        max_price=max_price,
                    )
            return []

        products = data.get("products", data.get("items", []))
        items = []

        for product_data in products:
            item = DataParser.parse_api_product(product_data)
            if item:
                items.append(item)

        return items

    async def get_product_details(self, product_id: str) -> Optional[DepopItem]:
        """
        Get detailed information about a specific product.

        Args:
            product_id: The Depop product ID.

        Returns:
            DepopItem or None if not found.
        """
        url = f"{self.BASE_URL}/products/{product_id}"
        data = await self._make_request(url)

        if not data:
            # Fallback to browser scraping if enabled
            if self.enable_browser_fallback:
                logger.info("API request failed, falling back to browser scraping")
                browser = await self._get_browser_scraper()
                if browser:
                    return await browser.get_product_details(product_id)
            return None

        return DataParser.parse_api_product(data)

    async def get_seller_products(
        self, username: str, limit: int = 50, offset: int = 0
    ) -> list[DepopItem]:
        """
        Get products from a specific seller.

        Args:
            username: Seller's username.
            limit: Maximum number of results.
            offset: Pagination offset.

        Returns:
            List of DepopItem objects.
        """
        params = {
            "itemsPerPage": min(limit, 100),
            "offset": offset,
        }

        url = f"{self.BASE_URL}/shop/{username}/products"
        data = await self._make_request(url, params)

        if not data:
            return []

        products = data.get("products", data.get("items", []))
        items = []

        for product_data in products:
            item = DataParser.parse_api_product(product_data)
            if item:
                items.append(item)

        return items

    @staticmethod
    def build_search_url(
        keyword: str,
        category: str = "",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sold_only: bool = True,
    ) -> str:
        """
        Build a Depop search URL for browser-based scraping.

        Args:
            keyword: Search keyword.
            category: Category filter.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            sold_only: Whether to show only sold items.

        Returns:
            Complete Depop search URL.
        """
        params: dict[str, Any] = {"q": keyword}

        if category:
            params["categories"] = category

        if min_price is not None:
            params["priceMin"] = int(min_price)

        if max_price is not None:
            params["priceMax"] = int(max_price)

        if sold_only:
            params["status"] = "sold"

        base = "https://www.depop.com/search/"
        return f"{base}?{urlencode(params)}"
