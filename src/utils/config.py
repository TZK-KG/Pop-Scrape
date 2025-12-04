"""Configuration management for Pop-Scrape application."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class FeeConfig:
    """Fee configuration settings."""

    depop_fee_percent: float = 10.0  # Depop's 10% fee
    payment_processing_percent: float = 2.9  # PayPal/Stripe percentage
    payment_processing_flat: float = 0.30  # PayPal/Stripe flat fee


@dataclass
class SearchPreferences:
    """Search preferences that can be saved/loaded."""

    last_keyword: str = ""
    category: str = "All"
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    default_tax_percent: float = 0.0
    default_shipping_cost: float = 0.0


@dataclass
class AppConfig:
    """Main application configuration."""

    theme: str = "dark"  # dark or light
    window_width: int = 1200
    window_height: int = 800
    rate_limit_delay: float = 1.0  # Seconds between requests
    max_results: int = 100
    fees: FeeConfig = field(default_factory=FeeConfig)
    search_preferences: SearchPreferences = field(default_factory=SearchPreferences)


class Config:
    """Configuration manager for the Pop-Scrape application."""

    DEFAULT_CONFIG_PATH = Path.home() / ".popscrape" / "config.json"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.

        Args:
            config_path: Optional path to the configuration file.
                        Defaults to ~/.popscrape/config.json
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()

    def _load_config(self) -> AppConfig:
        """
        Load configuration from file or create default.

        Returns:
            AppConfig: The loaded or default configuration.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Reconstruct nested dataclasses
                    fees_data = data.pop("fees", {})
                    search_data = data.pop("search_preferences", {})
                    return AppConfig(
                        **data,
                        fees=FeeConfig(**fees_data),
                        search_preferences=SearchPreferences(**search_data),
                    )
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                print(f"Warning: Could not load config, using defaults: {e}")
                return AppConfig()
        return AppConfig()

    def save(self) -> None:
        """Save current configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.config), f, indent=2)

    def update_search_preferences(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        tax_percent: Optional[float] = None,
        shipping_cost: Optional[float] = None,
    ) -> None:
        """
        Update search preferences.

        Args:
            keyword: Last searched keyword.
            category: Selected category.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            tax_percent: Default tax percentage.
            shipping_cost: Default shipping cost.
        """
        prefs = self.config.search_preferences
        if keyword is not None:
            prefs.last_keyword = keyword
        if category is not None:
            prefs.category = category
        if min_price is not None:
            prefs.min_price = min_price
        if max_price is not None:
            prefs.max_price = max_price
        if tax_percent is not None:
            prefs.default_tax_percent = tax_percent
        if shipping_cost is not None:
            prefs.default_shipping_cost = shipping_cost

    def set_theme(self, theme: str) -> None:
        """
        Set the application theme.

        Args:
            theme: Theme name ("dark" or "light").
        """
        if theme in ("dark", "light"):
            self.config.theme = theme
        else:
            raise ValueError(f"Invalid theme: {theme}. Use 'dark' or 'light'.")

    @property
    def depop_fee_percent(self) -> float:
        """Get Depop fee percentage."""
        return self.config.fees.depop_fee_percent

    @property
    def payment_processing_percent(self) -> float:
        """Get payment processing percentage."""
        return self.config.fees.payment_processing_percent

    @property
    def payment_processing_flat(self) -> float:
        """Get payment processing flat fee."""
        return self.config.fees.payment_processing_flat

    @property
    def rate_limit_delay(self) -> float:
        """Get rate limit delay between requests."""
        return self.config.rate_limit_delay

    @property
    def theme(self) -> str:
        """Get current theme."""
        return self.config.theme
