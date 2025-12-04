"""Tests for the sale analyzer module."""

import pytest
from datetime import datetime, timedelta

from src.analysis.analyzer import SaleAnalyzer, AnalysisResult
from src.scraper.parser import DepopItem


class TestSaleAnalyzer:
    """Test cases for SaleAnalyzer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = SaleAnalyzer()

    def create_test_item(
        self,
        price: float = 50.0,
        days_on_market: int | None = None,
        quantity: int = 1,
        is_sold: bool = True,
    ) -> DepopItem:
        """Create a test item with specified attributes."""
        now = datetime.now()
        listed_date = now - timedelta(days=days_on_market) if days_on_market else None
        sale_date = now if is_sold and days_on_market else None

        return DepopItem(
            id="test-123",
            title="Test Item",
            price=price,
            sale_date=sale_date,
            listed_date=listed_date,
            days_on_market=days_on_market,
            quantity_available=quantity,
            is_sold=is_sold,
        )

    def test_calculate_days_on_market_with_value(self):
        """Test days calculation when value is set."""
        item = self.create_test_item(days_on_market=5)
        days = self.analyzer.calculate_days_on_market(item)
        assert days == 5

    def test_calculate_days_on_market_none(self):
        """Test days calculation when not available."""
        item = self.create_test_item(days_on_market=None)
        days = self.analyzer.calculate_days_on_market(item)
        assert days is None

    def test_is_quick_sale_true(self):
        """Test quick sale detection for fast selling items."""
        item = self.create_test_item(days_on_market=3)
        assert self.analyzer.is_quick_sale(item) is True

    def test_is_quick_sale_false(self):
        """Test quick sale detection for slow selling items."""
        item = self.create_test_item(days_on_market=30)
        assert self.analyzer.is_quick_sale(item) is False

    def test_is_quick_sale_threshold(self):
        """Test quick sale at exactly threshold."""
        item = self.create_test_item(days_on_market=7)  # Default threshold
        assert self.analyzer.is_quick_sale(item) is True

    def test_is_quick_sale_no_data(self):
        """Test quick sale when data not available."""
        item = self.create_test_item(days_on_market=None)
        assert self.analyzer.is_quick_sale(item) is False

    def test_is_low_quantity_true(self):
        """Test low quantity detection."""
        item = self.create_test_item(quantity=1)
        assert self.analyzer.is_low_quantity(item) is True

        item = self.create_test_item(quantity=3)
        assert self.analyzer.is_low_quantity(item) is True

    def test_is_low_quantity_false(self):
        """Test items with adequate quantity."""
        item = self.create_test_item(quantity=10)
        assert self.analyzer.is_low_quantity(item) is False

    def test_analyze_items_empty(self):
        """Test analysis with empty list."""
        result = self.analyzer.analyze_items([])
        assert result.total_items == 0
        assert result.avg_price == 0.0

    def test_analyze_items_basic(self):
        """Test basic item analysis."""
        items = [
            self.create_test_item(price=50.0, days_on_market=3, quantity=1),
            self.create_test_item(price=100.0, days_on_market=10, quantity=5),
            self.create_test_item(price=75.0, days_on_market=5, quantity=2),
        ]

        result = self.analyzer.analyze_items(items)

        assert result.total_items == 3
        assert result.avg_price == 75.0  # (50 + 100 + 75) / 3
        assert result.low_quantity_items == 2  # qty 1 and 2
        assert result.quick_sale_items == 2  # 3 and 5 days

    def test_analyze_items_median_price_odd(self):
        """Test median price with odd number of items."""
        items = [
            self.create_test_item(price=10.0),
            self.create_test_item(price=20.0),
            self.create_test_item(price=30.0),
        ]

        result = self.analyzer.analyze_items(items)
        assert result.median_price == 20.0

    def test_analyze_items_median_price_even(self):
        """Test median price with even number of items."""
        items = [
            self.create_test_item(price=10.0),
            self.create_test_item(price=20.0),
            self.create_test_item(price=30.0),
            self.create_test_item(price=40.0),
        ]

        result = self.analyzer.analyze_items(items)
        assert result.median_price == 25.0  # (20 + 30) / 2

    def test_items_to_dataframe(self):
        """Test converting items to DataFrame."""
        items = [
            self.create_test_item(price=50.0, days_on_market=3),
            self.create_test_item(price=100.0, days_on_market=10),
        ]

        df = self.analyzer.items_to_dataframe(items)

        assert len(df) == 2
        assert "price" in df.columns
        assert "is_quick_sale" in df.columns
        assert "is_low_quantity" in df.columns

    def test_filter_quick_sales(self):
        """Test filtering for quick sales only."""
        items = [
            self.create_test_item(price=50.0, days_on_market=3),  # Quick
            self.create_test_item(price=100.0, days_on_market=30),  # Not quick
            self.create_test_item(price=75.0, days_on_market=5),  # Quick
        ]

        quick_sales = self.analyzer.filter_quick_sales(items)

        assert len(quick_sales) == 2
        assert all(item.days_on_market <= 7 for item in quick_sales)

    def test_filter_low_quantity(self):
        """Test filtering for low quantity items."""
        items = [
            self.create_test_item(quantity=1),
            self.create_test_item(quantity=10),
            self.create_test_item(quantity=2),
        ]

        low_qty = self.analyzer.filter_low_quantity(items)

        assert len(low_qty) == 2
        assert all(item.quantity_available <= 3 for item in low_qty)

    def test_sort_items_by_price_asc(self):
        """Test sorting items by price ascending."""
        items = [
            self.create_test_item(price=100.0),
            self.create_test_item(price=50.0),
            self.create_test_item(price=75.0),
        ]

        sorted_items = self.analyzer.sort_items(items, "price", ascending=True)

        prices = [item.price for item in sorted_items]
        assert prices == [50.0, 75.0, 100.0]

    def test_sort_items_by_price_desc(self):
        """Test sorting items by price descending."""
        items = [
            self.create_test_item(price=100.0),
            self.create_test_item(price=50.0),
            self.create_test_item(price=75.0),
        ]

        sorted_items = self.analyzer.sort_items(items, "price", ascending=False)

        prices = [item.price for item in sorted_items]
        assert prices == [100.0, 75.0, 50.0]

    def test_sort_items_by_days(self):
        """Test sorting items by days on market."""
        items = [
            self.create_test_item(days_on_market=10),
            self.create_test_item(days_on_market=3),
            self.create_test_item(days_on_market=7),
        ]

        sorted_items = self.analyzer.sort_items(
            items, "days_on_market", ascending=True
        )

        days = [item.days_on_market for item in sorted_items]
        assert days == [3, 7, 10]

    def test_sort_items_empty_list(self):
        """Test sorting empty list."""
        sorted_items = self.analyzer.sort_items([], "price", ascending=True)
        assert sorted_items == []

    def test_get_high_value_opportunities(self):
        """Test identifying high value opportunities."""
        items = [
            # Quick sale, low qty = opportunity
            self.create_test_item(price=100.0, days_on_market=3, quantity=1),
            # Not quick, low qty
            self.create_test_item(price=50.0, days_on_market=30, quantity=1),
            # Quick, not low qty
            self.create_test_item(price=75.0, days_on_market=2, quantity=10),
            # Quick sale, low qty = opportunity
            self.create_test_item(price=80.0, days_on_market=5, quantity=2),
        ]

        opportunities = self.analyzer.get_high_value_opportunities(items)

        assert len(opportunities) == 2
        # Should be sorted by price descending
        assert opportunities[0].price == 100.0
        assert opportunities[1].price == 80.0

    def test_custom_thresholds(self):
        """Test analyzer with custom thresholds."""
        custom_analyzer = SaleAnalyzer(quick_sale_days=3, low_quantity_limit=2)

        item = self.create_test_item(days_on_market=5, quantity=3)

        # With default thresholds this would be quick sale and low qty
        # With custom thresholds, neither is true
        assert custom_analyzer.is_quick_sale(item) is False
        assert custom_analyzer.is_low_quantity(item) is False
