"""Playwright-based browser scraping fallback for Depop."""

import asyncio
import logging
import random
from typing import Any, Optional

from .parser import DataParser, DepopItem

logger = logging.getLogger(__name__)

# Playwright is imported lazily to avoid errors if not installed
try:
    from playwright.async_api import async_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# Stealth script to avoid detection
STEALTH_SCRIPT = """
// Overwrite navigator.webdriver to be undefined
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

// Mock plugins array
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const pluginArray = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }
        ];
        pluginArray.item = (i) => pluginArray[i];
        pluginArray.namedItem = (name) => pluginArray.find(p => p.name === name);
        pluginArray.refresh = () => {};
        return pluginArray;
    }
});

// Mock languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});

// Mock hardware concurrency
Object.defineProperty(navigator, 'hardwareConcurrency', {
    get: () => 8
});

// Mock device memory
Object.defineProperty(navigator, 'deviceMemory', {
    get: () => 8
});

// Mock permissions API
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// Remove automation indicators from chrome object
if (window.chrome) {
    window.chrome.runtime = undefined;
}

// Mock WebGL vendor and renderer
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) {
        return 'Intel Inc.';
    }
    if (parameter === 37446) {
        return 'Intel Iris OpenGL Engine';
    }
    return getParameter.call(this, parameter);
};
"""


class BrowserScraper:
    """
    Browser-based scraper using Playwright for JS-rendered content.

    This serves as a fallback when API-based scraping fails or
    when content requires JavaScript to render.
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: float = 30000,
        min_delay: float = 0.5,
        max_delay: float = 2.0,
    ):
        """
        Initialize the browser scraper.

        Args:
            headless: Whether to run browser in headless mode.
            timeout: Page load timeout in milliseconds.
            min_delay: Minimum random delay between actions in seconds.
            max_delay: Maximum random delay between actions in seconds.
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. "
                "Install it with: pip install playwright && playwright install"
            )

        self.headless = headless
        self.timeout = timeout
        self.min_delay = min_delay
        self.max_delay = max_delay
        self._browser: Optional[Browser] = None
        self._playwright: Any = None

    async def __aenter__(self) -> "BrowserScraper":
        """Async context manager entry."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def _random_delay(self) -> None:
        """Add a random delay between actions to appear more human-like."""
        delay = random.uniform(self.min_delay, self.max_delay)
        await asyncio.sleep(delay)

    async def _create_page(self) -> Page:
        """Create a new browser page with stealth settings."""
        if not self._browser:
            raise RuntimeError("Browser not initialized. Use async context manager.")

        context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            },
        )

        page = await context.new_page()

        # Apply stealth script to avoid detection
        await page.add_init_script(STEALTH_SCRIPT)

        # Block unnecessary resources to speed up scraping
        await page.route(
            "**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf,otf}",
            lambda route: route.abort(),
        )

        page.set_default_timeout(self.timeout)
        return page

    async def _handle_cookie_consent(self, page: Page) -> None:
        """Handle cookie consent dialogs if present."""
        try:
            # Common cookie consent button selectors
            selectors = [
                "button[data-testid='accept-cookies']",
                "button:has-text('Accept')",
                "button:has-text('Accept All')",
                "button:has-text('Accept Cookies')",
                "[id*='accept'][class*='cookie']",
                "[class*='cookie'] button:has-text('Accept')",
            ]
            for selector in selectors:
                try:
                    button = page.locator(selector).first
                    if await button.is_visible(timeout=2000):
                        await button.click()
                        await self._random_delay()
                        logger.debug("Clicked cookie consent button: %s", selector)
                        return
                except Exception:
                    continue
        except Exception as e:
            logger.debug("No cookie consent found or handled: %s", e)

    async def search_sold_items(
        self,
        keyword: str,
        category: str = "",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        max_scroll: int = 5,
    ) -> list[DepopItem]:
        """
        Search for sold items using browser automation.

        Args:
            keyword: Search keyword.
            category: Category filter.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            max_scroll: Maximum number of scroll actions to load more items.

        Returns:
            List of DepopItem objects.
        """
        from .depop_api import DepopAPI

        url = DepopAPI.build_search_url(
            keyword=keyword,
            category=category,
            min_price=min_price,
            max_price=max_price,
            sold_only=True,
        )

        page = await self._create_page()

        try:
            await page.goto(url)
            await self._random_delay()

            # Handle cookie consent if present
            await self._handle_cookie_consent(page)

            # Wait for products to load
            await page.wait_for_selector(
                "[data-testid='product'], .styles_productCard__"
            )

            # Scroll to load more items with random delays
            for _ in range(max_scroll):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self._random_delay()

            # Extract product data
            items = await self._extract_items_from_page(page)
            return items

        except Exception as e:
            logger.error("Browser scraping error: %s", e)
            return []
        finally:
            await page.close()

    async def search_available_items(
        self,
        keyword: str,
        category: str = "",
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        max_scroll: int = 5,
    ) -> list[DepopItem]:
        """
        Search for available items using browser automation.

        Args:
            keyword: Search keyword.
            category: Category filter.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            max_scroll: Maximum number of scroll actions to load more items.

        Returns:
            List of DepopItem objects.
        """
        from .depop_api import DepopAPI

        url = DepopAPI.build_search_url(
            keyword=keyword,
            category=category,
            min_price=min_price,
            max_price=max_price,
            sold_only=False,
        )

        page = await self._create_page()

        try:
            await page.goto(url)
            await self._random_delay()

            # Handle cookie consent if present
            await self._handle_cookie_consent(page)

            await page.wait_for_selector(
                "[data-testid='product'], .styles_productCard__"
            )

            for _ in range(max_scroll):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self._random_delay()

            items = await self._extract_items_from_page(page)
            return items

        except Exception as e:
            logger.error("Browser scraping error: %s", e)
            return []
        finally:
            await page.close()

    async def get_product_details(self, product_id: str) -> Optional[DepopItem]:
        """
        Get detailed information about a specific product.

        Args:
            product_id: The Depop product ID or URL slug.

        Returns:
            DepopItem or None if not found.
        """
        url = f"https://www.depop.com/products/{product_id}"
        page = await self._create_page()

        try:
            await page.goto(url)
            await self._random_delay()

            # Handle cookie consent if present
            await self._handle_cookie_consent(page)

            await page.wait_for_selector("[data-testid='product-details']")

            # Extract product data from page
            data = await page.evaluate(
                """() => {
                const title = document.querySelector('[data-testid="product-title"]')?.textContent || '';
                const priceEl = document.querySelector('[data-testid="product-price"]');
                const price = priceEl?.textContent || '0';
                const seller = document.querySelector('[data-testid="seller-username"]')?.textContent || '';
                const desc = document.querySelector('[data-testid="product-description"]')?.textContent || '';
                const img = document.querySelector('[data-testid="product-image"] img')?.src || '';
                const sold = document.querySelector('[data-testid="sold-badge"]') !== null;

                return {
                    title,
                    price,
                    seller,
                    description: desc,
                    image_url: img,
                    is_sold: sold
                };
            }"""
            )

            if not data:
                return None

            return DepopItem(
                id=product_id,
                title=data.get("title", "")[:100],
                price=DataParser._parse_price(data.get("price", "0")),
                seller=data.get("seller", ""),
                description=data.get("description", ""),
                url=url,
                image_url=data.get("image_url", ""),
                is_sold=data.get("is_sold", False),
            )

        except Exception as e:
            logger.error("Failed to get product details: %s", e)
            return None
        finally:
            await page.close()

    async def _extract_items_from_page(self, page: Page) -> list[DepopItem]:
        """
        Extract product items from a search results page.

        Args:
            page: Playwright page object.

        Returns:
            List of DepopItem objects.
        """
        # Extract product data using JavaScript
        products_data = await page.evaluate(
            """() => {
            const products = [];
            const cards = document.querySelectorAll('[data-testid="product"], .styles_productCard__');

            cards.forEach((card) => {
                try {
                    const link = card.querySelector('a[href*="/products/"]');
                    if (!link) return;

                    const href = link.getAttribute('href') || '';
                    const id = href.split('/products/')[1]?.split('/')[0]?.split('?')[0] || '';

                    const priceEl = card.querySelector('[data-testid="price"], .styles_price__');
                    const price = priceEl?.textContent || '0';

                    const titleEl = card.querySelector('[data-testid="title"], .styles_description__');
                    const title = titleEl?.textContent || '';

                    const sellerEl = card.querySelector('[data-testid="username"], .styles_username__');
                    const seller = sellerEl?.textContent || '';

                    const img = card.querySelector('img');
                    const imgUrl = img?.src || img?.getAttribute('data-src') || '';

                    const soldBadge = card.querySelector('[data-testid="sold"], .styles_sold__');
                    const isSold = soldBadge !== null;

                    products.push({
                        id,
                        href,
                        price,
                        title,
                        seller,
                        image_url: imgUrl,
                        is_sold: isSold
                    });
                } catch (e) {
                    console.error('Error extracting product:', e);
                }
            });

            return products;
        }"""
        )

        items = []
        for data in products_data:
            try:
                item = DepopItem(
                    id=data.get("id", ""),
                    title=data.get("title", "")[:100],
                    price=DataParser._parse_price(data.get("price", "0")),
                    seller=data.get("seller", ""),
                    url=f"https://www.depop.com{data.get('href', '')}"
                    if not data.get("href", "").startswith("http")
                    else data.get("href", ""),
                    image_url=data.get("image_url", ""),
                    is_sold=data.get("is_sold", False),
                )
                items.append(item)
            except Exception as e:
                logger.warning("Failed to create item: %s", e)

        return items

    @staticmethod
    def is_available() -> bool:
        """Check if Playwright is available for use."""
        return PLAYWRIGHT_AVAILABLE
