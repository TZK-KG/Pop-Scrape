"""Tests for the browser scraper module with stealth features."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.scraper.browser import BrowserScraper, STEALTH_SCRIPT, PLAYWRIGHT_AVAILABLE


class TestBrowserScraperConfiguration:
    """Test cases for browser scraper configuration."""

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    def test_default_configuration(self):
        """Test default configuration values."""
        scraper = BrowserScraper()
        assert scraper.headless is True
        assert scraper.timeout == 30000
        assert scraper.min_delay == 0.5
        assert scraper.max_delay == 2.0
        assert scraper.block_resources is True

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    def test_custom_configuration(self):
        """Test custom configuration values."""
        scraper = BrowserScraper(
            headless=False,
            timeout=60000,
            min_delay=1.0,
            max_delay=3.0,
            block_resources=False,
        )
        assert scraper.headless is False
        assert scraper.timeout == 60000
        assert scraper.min_delay == 1.0
        assert scraper.max_delay == 3.0
        assert scraper.block_resources is False

    def test_is_available(self):
        """Test is_available returns correct value."""
        # Should match the module-level constant
        assert BrowserScraper.is_available() == PLAYWRIGHT_AVAILABLE


class TestStealthScript:
    """Test cases for the stealth script."""

    def test_stealth_script_not_empty(self):
        """Test that stealth script is defined."""
        assert STEALTH_SCRIPT is not None
        assert len(STEALTH_SCRIPT) > 0

    def test_stealth_script_contains_webdriver_override(self):
        """Test that stealth script overrides webdriver property."""
        assert "navigator.webdriver" in STEALTH_SCRIPT

    def test_stealth_script_contains_plugins_mock(self):
        """Test that stealth script mocks plugins."""
        assert "'plugins'" in STEALTH_SCRIPT

    def test_stealth_script_contains_languages_mock(self):
        """Test that stealth script mocks languages."""
        assert "'languages'" in STEALTH_SCRIPT


class TestBrowserScraperRandomDelay:
    """Test cases for random delay functionality."""

    @pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
    @pytest.mark.asyncio
    async def test_random_delay_within_bounds(self):
        """Test that random delay is within configured bounds."""
        scraper = BrowserScraper(min_delay=0.1, max_delay=0.2)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await scraper._random_delay()

        # Check that sleep was called with a value in the expected range
        mock_sleep.assert_called_once()
        delay = mock_sleep.call_args[0][0]
        assert 0.1 <= delay <= 0.2


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
class TestBrowserScraperPageCreation:
    """Test cases for page creation with stealth settings."""

    @pytest.mark.asyncio
    async def test_create_page_applies_stealth_script(self):
        """Test that stealth script is applied to new pages."""
        scraper = BrowserScraper()

        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()
        mock_page.route = AsyncMock()
        mock_page.set_default_timeout = MagicMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        scraper._browser = mock_browser

        page = await scraper._create_page()

        # Verify stealth script was added
        mock_page.add_init_script.assert_called_once_with(STEALTH_SCRIPT)

        # Verify resource blocking was set up (default is True)
        mock_page.route.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_page_without_resource_blocking(self):
        """Test that resource blocking is skipped when disabled."""
        scraper = BrowserScraper(block_resources=False)

        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()
        mock_page.route = AsyncMock()
        mock_page.set_default_timeout = MagicMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        scraper._browser = mock_browser

        await scraper._create_page()

        # Verify resource blocking was NOT set up
        mock_page.route.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_page_sets_viewport(self):
        """Test that page is created with correct viewport."""
        scraper = BrowserScraper()

        mock_page = AsyncMock()
        mock_page.add_init_script = AsyncMock()
        mock_page.route = AsyncMock()
        mock_page.set_default_timeout = MagicMock()

        mock_context = AsyncMock()
        mock_context.new_page = AsyncMock(return_value=mock_page)

        mock_browser = AsyncMock()
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        scraper._browser = mock_browser

        await scraper._create_page()

        # Verify new_context was called with viewport settings
        call_kwargs = mock_browser.new_context.call_args[1]
        assert call_kwargs["viewport"] == {"width": 1920, "height": 1080}
        assert "Chrome/120" in call_kwargs["user_agent"]
        assert call_kwargs["locale"] == "en-US"
        assert call_kwargs["timezone_id"] == "America/New_York"


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
class TestBrowserScraperCookieConsent:
    """Test cases for cookie consent handling."""

    @pytest.mark.asyncio
    async def test_handle_cookie_consent_clicks_button(self):
        """Test that cookie consent button is clicked if visible."""
        scraper = BrowserScraper(min_delay=0.01, max_delay=0.02)

        mock_button = AsyncMock()
        mock_button.is_visible = AsyncMock(return_value=True)
        mock_button.click = AsyncMock()

        mock_locator = MagicMock()
        mock_locator.first = mock_button

        mock_page = AsyncMock()
        mock_page.locator = MagicMock(return_value=mock_locator)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await scraper._handle_cookie_consent(mock_page)

        mock_button.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_cookie_consent_no_error_if_not_found(self):
        """Test that no error is raised if no cookie consent is found."""
        scraper = BrowserScraper()

        mock_button = AsyncMock()
        mock_button.is_visible = AsyncMock(return_value=False)

        mock_locator = MagicMock()
        mock_locator.first = mock_button

        mock_page = AsyncMock()
        mock_page.locator = MagicMock(return_value=mock_locator)

        # Should not raise an error
        await scraper._handle_cookie_consent(mock_page)


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="Playwright not installed")
class TestBrowserScraperContextManager:
    """Test cases for async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_launches_browser(self):
        """Test that context manager launches browser with correct args."""
        with patch("src.scraper.browser.async_playwright") as mock_pw:
            mock_browser = AsyncMock()
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(
                return_value=mock_browser
            )
            mock_pw.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            scraper = BrowserScraper(headless=True)
            async with scraper:
                pass

            # Verify launch was called with anti-detection args
            launch_kwargs = mock_playwright_instance.chromium.launch.call_args[1]
            assert launch_kwargs["headless"] is True
            assert "--disable-blink-features=AutomationControlled" in launch_kwargs["args"]

    @pytest.mark.asyncio
    async def test_context_manager_closes_browser(self):
        """Test that context manager closes browser on exit."""
        with patch("src.scraper.browser.async_playwright") as mock_pw:
            mock_browser = AsyncMock()
            mock_browser.close = AsyncMock()
            mock_playwright_instance = AsyncMock()
            mock_playwright_instance.chromium.launch = AsyncMock(
                return_value=mock_browser
            )
            mock_playwright_instance.stop = AsyncMock()
            mock_pw.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            scraper = BrowserScraper()
            async with scraper:
                pass

            mock_browser.close.assert_called_once()
            mock_playwright_instance.stop.assert_called_once()
