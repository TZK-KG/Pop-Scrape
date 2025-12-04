"""Tests for the configuration module."""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.utils.config import Config, AppConfig, FeeConfig, SearchPreferences


class TestConfig:
    """Test cases for Config class."""

    def test_default_config_creation(self):
        """Test creating config with defaults."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = Config(config_path)

            assert config.config.theme == "dark"
            assert config.depop_fee_percent == 10.0
            assert config.payment_processing_percent == 2.9
            assert config.payment_processing_flat == 0.30

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"

            # Create and modify config
            config = Config(config_path)
            config.set_theme("light")
            config.update_search_preferences(keyword="test", tax_percent=8.5)
            config.save()

            # Load config again
            config2 = Config(config_path)

            assert config2.config.theme == "light"
            assert config2.config.search_preferences.last_keyword == "test"
            assert config2.config.search_preferences.default_tax_percent == 8.5

    def test_set_theme_valid(self):
        """Test setting valid themes."""
        with TemporaryDirectory() as tmpdir:
            config = Config(Path(tmpdir) / "config.json")

            config.set_theme("light")
            assert config.theme == "light"

            config.set_theme("dark")
            assert config.theme == "dark"

    def test_set_theme_invalid(self):
        """Test setting invalid theme."""
        with TemporaryDirectory() as tmpdir:
            config = Config(Path(tmpdir) / "config.json")

            with pytest.raises(ValueError):
                config.set_theme("invalid")

    def test_update_search_preferences_partial(self):
        """Test updating only some search preferences."""
        with TemporaryDirectory() as tmpdir:
            config = Config(Path(tmpdir) / "config.json")

            # Set initial values
            config.update_search_preferences(
                keyword="original",
                category="Menswear",
                tax_percent=5.0,
            )

            # Update only keyword
            config.update_search_preferences(keyword="updated")

            assert config.config.search_preferences.last_keyword == "updated"
            assert config.config.search_preferences.category == "Menswear"
            assert config.config.search_preferences.default_tax_percent == 5.0

    def test_rate_limit_property(self):
        """Test rate limit delay property."""
        with TemporaryDirectory() as tmpdir:
            config = Config(Path(tmpdir) / "config.json")
            assert config.rate_limit_delay == 1.0

    def test_load_corrupted_config(self):
        """Test loading corrupted config file."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"

            # Write invalid JSON
            with open(config_path, "w") as f:
                f.write("not valid json {}")

            # Should fall back to defaults
            config = Config(config_path)
            assert config.config.theme == "dark"


class TestFeeConfig:
    """Test cases for FeeConfig dataclass."""

    def test_default_values(self):
        """Test default fee configuration values."""
        fees = FeeConfig()

        assert fees.depop_fee_percent == 10.0
        assert fees.payment_processing_percent == 2.9
        assert fees.payment_processing_flat == 0.30

    def test_custom_values(self):
        """Test custom fee configuration."""
        fees = FeeConfig(
            depop_fee_percent=12.0,
            payment_processing_percent=3.5,
            payment_processing_flat=0.50,
        )

        assert fees.depop_fee_percent == 12.0
        assert fees.payment_processing_percent == 3.5
        assert fees.payment_processing_flat == 0.50


class TestSearchPreferences:
    """Test cases for SearchPreferences dataclass."""

    def test_default_values(self):
        """Test default search preferences."""
        prefs = SearchPreferences()

        assert prefs.last_keyword == ""
        assert prefs.category == "All"
        assert prefs.min_price is None
        assert prefs.max_price is None
        assert prefs.default_tax_percent == 0.0
        assert prefs.default_shipping_cost == 0.0

    def test_custom_values(self):
        """Test custom search preferences."""
        prefs = SearchPreferences(
            last_keyword="vintage jacket",
            category="Menswear",
            min_price=20.0,
            max_price=100.0,
            default_tax_percent=8.25,
            default_shipping_cost=5.50,
        )

        assert prefs.last_keyword == "vintage jacket"
        assert prefs.category == "Menswear"
        assert prefs.min_price == 20.0
        assert prefs.max_price == 100.0
        assert prefs.default_tax_percent == 8.25
        assert prefs.default_shipping_cost == 5.50


class TestAppConfig:
    """Test cases for AppConfig dataclass."""

    def test_default_values(self):
        """Test default application configuration."""
        config = AppConfig()

        assert config.theme == "dark"
        assert config.window_width == 1200
        assert config.window_height == 800
        assert config.rate_limit_delay == 1.0
        assert config.max_results == 100

    def test_nested_defaults(self):
        """Test nested dataclass defaults."""
        config = AppConfig()

        assert config.fees.depop_fee_percent == 10.0
        assert config.search_preferences.category == "All"
