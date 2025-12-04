"""Sale speed and quantity analysis for Depop items."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd

from ..scraper.parser import DepopItem


@dataclass
class AnalysisResult:
    """Result of item analysis."""

    avg_days_to_sell: Optional[float] = None
    median_days_to_sell: Optional[float] = None
    avg_price: float = 0.0
    median_price: float = 0.0
    low_quantity_items: int = 0
    quick_sale_items: int = 0
    total_items: int = 0


class SaleAnalyzer:
    """Analyze sale patterns and identify opportunities."""

    # Thresholds for analysis
    QUICK_SALE_THRESHOLD_DAYS = 7  # Items sold within 7 days
    LOW_QUANTITY_THRESHOLD = 3  # Items with quantity <= 3

    def __init__(
        self,
        quick_sale_days: int = QUICK_SALE_THRESHOLD_DAYS,
        low_quantity_limit: int = LOW_QUANTITY_THRESHOLD,
    ):
        """
        Initialize the sale analyzer.

        Args:
            quick_sale_days: Threshold for quick sale detection.
            low_quantity_limit: Threshold for low quantity flagging.
        """
        self.quick_sale_days = quick_sale_days
        self.low_quantity_limit = low_quantity_limit

    def calculate_days_on_market(self, item: DepopItem) -> Optional[int]:
        """
        Calculate days an item was on the market before sale.

        Args:
            item: The Depop item to analyze.

        Returns:
            Number of days or None if cannot be determined.
        """
        if item.days_on_market is not None:
            return item.days_on_market

        if item.sale_date and item.listed_date:
            delta = item.sale_date - item.listed_date
            return max(0, delta.days)

        return None

    def is_quick_sale(self, item: DepopItem) -> bool:
        """
        Check if an item sold quickly.

        Args:
            item: The Depop item to check.

        Returns:
            True if the item sold within the quick sale threshold.
        """
        days = self.calculate_days_on_market(item)
        if days is None:
            return False
        return days <= self.quick_sale_days

    def is_low_quantity(self, item: DepopItem) -> bool:
        """
        Check if an item has low quantity available.

        Args:
            item: The Depop item to check.

        Returns:
            True if the item has limited supply.
        """
        return item.quantity_available <= self.low_quantity_limit

    def analyze_items(self, items: list[DepopItem]) -> AnalysisResult:
        """
        Analyze a list of items for patterns.

        Args:
            items: List of DepopItem objects.

        Returns:
            AnalysisResult with aggregated analysis.
        """
        if not items:
            return AnalysisResult()

        days_list = []
        prices = []
        low_quantity_count = 0
        quick_sale_count = 0

        for item in items:
            prices.append(item.price)

            days = self.calculate_days_on_market(item)
            if days is not None:
                days_list.append(days)
                if days <= self.quick_sale_days:
                    quick_sale_count += 1

            if self.is_low_quantity(item):
                low_quantity_count += 1

        result = AnalysisResult(
            total_items=len(items),
            low_quantity_items=low_quantity_count,
            quick_sale_items=quick_sale_count,
        )

        if prices:
            result.avg_price = round(sum(prices) / len(prices), 2)
            sorted_prices = sorted(prices)
            mid = len(sorted_prices) // 2
            if len(sorted_prices) % 2 == 0:
                result.median_price = (sorted_prices[mid - 1] + sorted_prices[mid]) / 2
            else:
                result.median_price = sorted_prices[mid]

        if days_list:
            result.avg_days_to_sell = round(sum(days_list) / len(days_list), 1)
            sorted_days = sorted(days_list)
            mid = len(sorted_days) // 2
            if len(sorted_days) % 2 == 0:
                result.median_days_to_sell = (
                    sorted_days[mid - 1] + sorted_days[mid]
                ) / 2
            else:
                result.median_days_to_sell = float(sorted_days[mid])

        return result

    def items_to_dataframe(self, items: list[DepopItem]) -> pd.DataFrame:
        """
        Convert list of items to pandas DataFrame for analysis.

        Args:
            items: List of DepopItem objects.

        Returns:
            pandas DataFrame with item data.
        """
        data = [item.to_dict() for item in items]
        df = pd.DataFrame(data)

        # Add calculated columns
        if not df.empty:
            df["is_quick_sale"] = df.apply(
                lambda row: (
                    row["days_on_market"] is not None
                    and row["days_on_market"] <= self.quick_sale_days
                ),
                axis=1,
            )
            df["is_low_quantity"] = df["quantity_available"] <= self.low_quantity_limit

        return df

    def filter_quick_sales(self, items: list[DepopItem]) -> list[DepopItem]:
        """
        Filter items to only include quick sales.

        Args:
            items: List of DepopItem objects.

        Returns:
            Filtered list of items that sold quickly.
        """
        return [item for item in items if self.is_quick_sale(item)]

    def filter_low_quantity(self, items: list[DepopItem]) -> list[DepopItem]:
        """
        Filter items to only include low quantity items.

        Args:
            items: List of DepopItem objects.

        Returns:
            Filtered list of items with limited supply.
        """
        return [item for item in items if self.is_low_quantity(item)]

    def sort_items(
        self,
        items: list[DepopItem],
        sort_by: str = "price",
        ascending: bool = True,
    ) -> list[DepopItem]:
        """
        Sort items by specified field.

        Args:
            items: List of DepopItem objects.
            sort_by: Field to sort by ('price', 'days_on_market', 'quantity_available').
            ascending: Sort order.

        Returns:
            Sorted list of items.
        """
        if not items:
            return items

        sort_key_map = {
            "price": lambda x: x.price,
            "days_on_market": lambda x: x.days_on_market if x.days_on_market else float("inf"),
            "quantity_available": lambda x: x.quantity_available,
            "seller_rating": lambda x: x.seller_rating if x.seller_rating else 0,
            "title": lambda x: x.title.lower(),
        }

        key_func = sort_key_map.get(sort_by, lambda x: x.price)
        return sorted(items, key=key_func, reverse=not ascending)

    def get_high_value_opportunities(
        self, items: list[DepopItem], min_profit_margin: float = 20.0
    ) -> list[DepopItem]:
        """
        Identify items with high profit potential.

        Items that sold quickly and had limited quantity suggest
        high demand that could be profitable to resell.

        Args:
            items: List of DepopItem objects.
            min_profit_margin: Minimum profit margin percentage to consider.

        Returns:
            List of items with high value potential.
        """
        # Filter for quick sales with low quantity
        opportunities = []
        for item in items:
            if self.is_quick_sale(item) and self.is_low_quantity(item):
                opportunities.append(item)

        # Sort by price descending (higher priced items = more profit potential)
        return self.sort_items(opportunities, sort_by="price", ascending=False)
