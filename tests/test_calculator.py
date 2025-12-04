"""Tests for the profit calculator module."""

import pytest

from src.analysis.calculator import FeeBreakdownResult, ProfitCalculator


class TestProfitCalculator:
    """Test cases for ProfitCalculator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = ProfitCalculator()

    def test_calculate_depop_fee(self):
        """Test Depop fee calculation (10%)."""
        assert self.calculator.calculate_depop_fee(100.0) == 10.0
        assert self.calculator.calculate_depop_fee(50.0) == 5.0
        assert self.calculator.calculate_depop_fee(0.0) == 0.0

    def test_calculate_payment_processing_fee(self):
        """Test payment processing fee calculation (2.9% + $0.30)."""
        # $100 * 2.9% + $0.30 = $2.90 + $0.30 = $3.20
        assert self.calculator.calculate_payment_processing_fee(100.0) == 3.20
        # $50 * 2.9% + $0.30 = $1.45 + $0.30 = $1.75
        assert self.calculator.calculate_payment_processing_fee(50.0) == 1.75
        # $0 * 2.9% + $0.30 = $0.30
        assert self.calculator.calculate_payment_processing_fee(0.0) == 0.30

    def test_calculate_sales_tax(self):
        """Test sales tax calculation."""
        assert self.calculator.calculate_sales_tax(100.0, 10.0) == 10.0
        assert self.calculator.calculate_sales_tax(100.0, 8.5) == 8.5
        assert self.calculator.calculate_sales_tax(100.0, 0.0) == 0.0
        assert self.calculator.calculate_sales_tax(100.0, -5.0) == 0.0

    def test_calculate_full_breakdown_basic(self):
        """Test full breakdown calculation with basic inputs."""
        result = self.calculator.calculate_full_breakdown(
            sale_price=100.0,
            shipping_cost=0.0,
            tax_percent=0.0,
        )

        assert result.sale_price == 100.0
        assert result.depop_fee == 10.0  # 10%
        assert result.payment_processing_fee == 3.20  # 2.9% + $0.30
        assert result.sales_tax == 0.0
        assert result.shipping_cost == 0.0
        assert result.total_deductions == 13.20
        assert result.net_profit == 86.80

    def test_calculate_full_breakdown_with_all_fees(self):
        """Test full breakdown with all fee types."""
        result = self.calculator.calculate_full_breakdown(
            sale_price=50.0,
            shipping_cost=5.0,
            tax_percent=8.5,
            cost_basis=20.0,
        )

        assert result.sale_price == 50.0
        assert result.depop_fee == 5.0  # 10% of $50
        assert result.payment_processing_fee == 1.75  # 2.9% of $50 + $0.30
        assert result.sales_tax == 4.25  # 8.5% of $50
        assert result.shipping_cost == 5.0
        assert result.cost_basis == 20.0
        assert result.total_deductions == 16.0  # 5 + 1.75 + 4.25 + 5
        assert result.net_profit == 14.0  # 50 - 16 - 20

    def test_calculate_full_breakdown_profit_margin(self):
        """Test profit margin percentage calculation."""
        result = self.calculator.calculate_full_breakdown(
            sale_price=100.0,
            shipping_cost=0.0,
            tax_percent=0.0,
        )

        # Net profit is $86.80, profit margin = 86.80 / 100 * 100 = 86.8%
        assert result.profit_margin_percent == 86.80

    def test_calculate_full_breakdown_negative_profit(self):
        """Test breakdown when costs exceed sale price."""
        result = self.calculator.calculate_full_breakdown(
            sale_price=10.0,
            shipping_cost=20.0,
            tax_percent=0.0,
        )

        assert result.net_profit < 0

    def test_calculate_required_price_for_target_profit(self):
        """Test calculating required price to achieve target profit."""
        target_profit = 50.0
        required_price = self.calculator.calculate_required_price(
            target_profit=target_profit,
            shipping_cost=0.0,
            tax_percent=0.0,
        )

        # Verify by calculating breakdown at required price
        result = self.calculator.calculate_full_breakdown(
            sale_price=required_price,
            shipping_cost=0.0,
            tax_percent=0.0,
        )

        # Net profit should be approximately the target
        assert abs(result.net_profit - target_profit) < 0.01

    def test_calculate_required_price_with_costs(self):
        """Test required price calculation with shipping and tax."""
        target_profit = 30.0
        shipping = 5.0
        tax = 10.0
        cost_basis = 15.0

        required_price = self.calculator.calculate_required_price(
            target_profit=target_profit,
            shipping_cost=shipping,
            tax_percent=tax,
            cost_basis=cost_basis,
        )

        result = self.calculator.calculate_full_breakdown(
            sale_price=required_price,
            shipping_cost=shipping,
            tax_percent=tax,
            cost_basis=cost_basis,
        )

        # Use slightly larger tolerance due to rounding
        assert abs(result.net_profit - target_profit) < 0.05

    def test_custom_fee_rates(self):
        """Test calculator with custom fee rates."""
        custom_calc = ProfitCalculator(
            depop_fee_percent=12.0,
            payment_percent=3.5,
            payment_flat=0.50,
        )

        result = custom_calc.calculate_full_breakdown(
            sale_price=100.0,
            shipping_cost=0.0,
            tax_percent=0.0,
        )

        assert result.depop_fee == 12.0  # 12%
        assert result.payment_processing_fee == 4.0  # 3.5% + $0.50

    def test_fee_breakdown_result_to_dict(self):
        """Test FeeBreakdownResult to_dict method."""
        result = self.calculator.calculate_full_breakdown(
            sale_price=100.0,
            shipping_cost=10.0,
            tax_percent=5.0,
        )

        result_dict = result.to_dict()

        assert "sale_price" in result_dict
        assert "depop_fee" in result_dict
        assert "payment_processing_fee" in result_dict
        assert "sales_tax" in result_dict
        assert "shipping_cost" in result_dict
        assert "total_deductions" in result_dict
        assert "net_profit" in result_dict
        assert "profit_margin_percent" in result_dict

    def test_get_fee_summary_string(self):
        """Test formatted fee summary string."""
        result = self.calculator.calculate_full_breakdown(
            sale_price=100.0,
            shipping_cost=0.0,
            tax_percent=0.0,
        )

        summary = self.calculator.get_fee_summary_string(result)

        assert "Sale Price: $100.00" in summary
        assert "Depop Fee" in summary
        assert "Payment Processing" in summary
        assert "Net Profit" in summary

    def test_estimate_profit_from_item(self):
        """Test profit estimation for an item."""
        result = self.calculator.estimate_profit_from_item(
            item_price=75.0,
            estimated_shipping=8.0,
            tax_percent=6.0,
        )

        assert result is not None
        assert result.sale_price == 75.0
        assert result.net_profit > 0

    def test_estimate_profit_invalid_price(self):
        """Test profit estimation with invalid price."""
        result = self.calculator.estimate_profit_from_item(
            item_price=0.0,
            estimated_shipping=0.0,
            tax_percent=0.0,
        )

        assert result is None

        result = self.calculator.estimate_profit_from_item(
            item_price=-10.0,
            estimated_shipping=0.0,
            tax_percent=0.0,
        )

        assert result is None
