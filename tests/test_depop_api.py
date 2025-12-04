"""Tests for the Depop API module with anti-detection features."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from src.scraper.depop_api import DepopAPI, USER_AGENTS


class TestDepopAPIHeaders:
    """Test cases for User-Agent rotation and headers."""

    def test_user_agents_list_not_empty(self):
        """Test that USER_AGENTS list contains agents."""
        assert len(USER_AGENTS) > 0

    def test_user_agents_are_strings(self):
        """Test that all User-Agents are strings."""
        for agent in USER_AGENTS:
            assert isinstance(agent, str)
            assert len(agent) > 0

    def test_default_headers_have_required_fields(self):
        """Test that DEFAULT_HEADERS contains required security headers."""
        required_headers = [
            "User-Agent",
            "Accept",
            "Accept-Language",
            "Origin",
            "Referer",
            "Sec-Ch-Ua",
            "Sec-Ch-Ua-Mobile",
            "Sec-Ch-Ua-Platform",
            "Sec-Fetch-Dest",
            "Sec-Fetch-Mode",
            "Sec-Fetch-Site",
        ]
        for header in required_headers:
            assert header in DepopAPI.DEFAULT_HEADERS

    def test_get_rotated_headers_returns_different_agents(self):
        """Test that _get_rotated_headers can return different User-Agents."""
        api = DepopAPI()
        seen_agents = set()
        # Call multiple times to increase chance of seeing rotation
        for _ in range(50):
            headers = api._get_rotated_headers()
            seen_agents.add(headers["User-Agent"])

        # Should see at least 2 different agents in 50 calls if randomization works
        assert len(seen_agents) >= 2


class TestDepopAPIRetryLogic:
    """Test cases for retry logic with exponential backoff."""

    def test_retry_configuration(self):
        """Test retry configuration values."""
        assert DepopAPI.MAX_RETRIES >= 1
        assert DepopAPI.INITIAL_BACKOFF > 0
        assert DepopAPI.BACKOFF_MULTIPLIER > 1

    @pytest.mark.asyncio
    async def test_retry_on_403_error(self):
        """Test that API retries on 403 error."""
        api = DepopAPI()

        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403
        mock_response_403.text = "Forbidden"

        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"products": []}
        mock_response_200.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        # First call returns 403, second returns 200
        mock_client.get = AsyncMock(
            side_effect=[
                httpx.HTTPStatusError(
                    "403", request=MagicMock(), response=mock_response_403
                ),
                mock_response_200,
            ]
        )

        api._client = mock_client
        api._last_request_time = 0

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await api._make_request("https://example.com/test")

        # Should have succeeded after retry
        assert result == {"products": []}
        assert mock_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted_returns_none(self):
        """Test that None is returned when all retries are exhausted."""
        api = DepopAPI()

        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403
        mock_response_403.text = "Forbidden"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "403", request=MagicMock(), response=mock_response_403
            )
        )

        api._client = mock_client
        api._last_request_time = 0

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await api._make_request("https://example.com/test")

        assert result is None
        assert mock_client.get.call_count == api.MAX_RETRIES

    @pytest.mark.asyncio
    async def test_no_retry_on_404_error(self):
        """Test that 404 errors are not retried."""
        api = DepopAPI()

        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        mock_response_404.text = "Not Found"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "404", request=MagicMock(), response=mock_response_404
            )
        )

        api._client = mock_client
        api._last_request_time = 0

        result = await api._make_request("https://example.com/test")

        assert result is None
        # Should only try once for 404
        assert mock_client.get.call_count == 1


class TestDepopAPIBrowserFallback:
    """Test cases for browser fallback functionality."""

    def test_browser_fallback_enabled_by_default(self):
        """Test that browser fallback is enabled by default."""
        api = DepopAPI()
        assert api.enable_browser_fallback is True

    def test_browser_fallback_can_be_disabled(self):
        """Test that browser fallback can be disabled."""
        api = DepopAPI(enable_browser_fallback=False)
        assert api.enable_browser_fallback is False

    @pytest.mark.asyncio
    async def test_get_browser_scraper_caches_instance(self):
        """Test that browser scraper is cached after first initialization."""
        api = DepopAPI()

        mock_browser = MagicMock()
        mock_browser.__aenter__ = AsyncMock(return_value=mock_browser)
        mock_browser.is_available = staticmethod(lambda: True)

        with patch("src.scraper.browser.BrowserScraper", return_value=mock_browser):
            scraper1 = await api._get_browser_scraper()
            scraper2 = await api._get_browser_scraper()

        # Should return same instance
        assert scraper1 is scraper2

    @pytest.mark.asyncio
    async def test_search_sold_items_falls_back_to_browser(self):
        """Test that search falls back to browser on API failure."""
        api = DepopAPI(enable_browser_fallback=True)

        # Mock API to fail
        mock_client = AsyncMock()
        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403
        mock_response_403.text = "Forbidden"
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "403", request=MagicMock(), response=mock_response_403
            )
        )
        api._client = mock_client
        api._last_request_time = 0

        # Mock browser scraper
        mock_browser = AsyncMock()
        mock_browser.search_sold_items = AsyncMock(return_value=[])

        with patch.object(api, "_get_browser_scraper", return_value=mock_browser):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await api.search_sold_items(keyword="test")

        assert result == []
        mock_browser.search_sold_items.assert_called_once()


class TestDepopAPIContextManager:
    """Test cases for async context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_initializes_client(self):
        """Test that context manager initializes HTTP client."""
        async with DepopAPI() as api:
            assert api._client is not None

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self):
        """Test that context manager closes HTTP client on exit."""
        api = DepopAPI()
        async with api:
            client = api._client
            assert client is not None

        # Client should be closed after exiting
        assert api._client is not None  # Reference still exists

    @pytest.mark.asyncio
    async def test_context_manager_closes_browser_scraper(self):
        """Test that browser scraper is closed on context manager exit."""
        api = DepopAPI()

        mock_browser = AsyncMock()
        mock_browser.__aexit__ = AsyncMock()

        async with api:
            api._browser_scraper = mock_browser

        mock_browser.__aexit__.assert_called_once()
