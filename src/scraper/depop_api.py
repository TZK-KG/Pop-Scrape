"""Depop API-based scraping functionality."""

import asyncio
import time
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from .parser import DataParser, DepopItem


class DepopAPI:
    """Handle API-based scraping of Depop data."""

    # Depop API endpoints
    BASE_URL = "https://webapi.depop.com/api/v2"
    SEARCH_ENDPOINT = "/search/products"

    # Mobile API (sometimes has different data)
    MOBILE_BASE_URL = "https://api.depop.com/api/v1"

    # Headers to mimic browser/app requests
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        ),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://www.depop.com",
        "Referer": "https://www.depop.com/",
    }

    def __init__(self, rate_limit_delay: float = 1.0, timeout: float = 30.0):
        """
        Initialize the Depop API scraper.

        Args:
            rate_limit_delay: Delay between requests in seconds.
            timeout: Request timeout in seconds.
        """
        self.rate_limit_delay = rate_limit_delay
        self.timeout = timeout
        self._last_request_time: float = 0
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "DepopAPI":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(
            headers=self.DEFAULT_HEADERS,
            timeout=self.timeout,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()

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
        Make a rate-limited API request.

        Args:
            url: The URL to request.
            params: Optional query parameters.

        Returns:
            JSON response as dictionary or None if failed.
        """
        if not self._client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        await self._rate_limit()

        try:
            response = await self._client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code} - {e.response.text[:200]}")
            return None
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
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
