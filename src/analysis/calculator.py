"""Profit and fee calculations for Depop sales."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FeeBreakdownResult:
    """Result of fee calculation breakdown."""

    sale_price: float
    depop_fee: float
    payment_processing_fee: float
    sales_tax: float
    shipping_cost: float
    total_deductions: float
    net_profit: float
    profit_margin_percent: float
    cost_basis: float = 0.0

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary."""
        return {
            "sale_price": self.sale_price,
            "depop_fee": self.depop_fee,
            "payment_processing_fee": self.payment_processing_fee,
            "sales_tax": self.sales_tax,
            "shipping_cost": self.shipping_cost,
            "total_deductions": self.total_deductions,
            "net_profit": self.net_profit,
            "profit_margin_percent": self.profit_margin_percent,
            "cost_basis": self.cost_basis,
        }


class ProfitCalculator:
    """Calculate profit and fees for Depop sales."""

    # Default fee rates
    DEFAULT_DEPOP_FEE_PERCENT = 10.0  # 10% of sale price
    DEFAULT_PAYMENT_PERCENT = 2.9  # PayPal/Stripe percentage
    DEFAULT_PAYMENT_FLAT = 0.30  # PayPal/Stripe flat fee

    def __init__(
        self,
        depop_fee_percent: float = DEFAULT_DEPOP_FEE_PERCENT,
        payment_percent: float = DEFAULT_PAYMENT_PERCENT,
        payment_flat: float = DEFAULT_PAYMENT_FLAT,
    ):
        """
        Initialize the profit calculator.

        Args:
            depop_fee_percent: Depop's percentage fee (default 10%).
            payment_percent: Payment processor percentage (default 2.9%).
            payment_flat: Payment processor flat fee (default $0.30).
        """
        self.depop_fee_percent = depop_fee_percent
        self.payment_percent = payment_percent
        self.payment_flat = payment_flat

    def calculate_depop_fee(self, sale_price: float) -> float:
        """
        Calculate Depop's fee (10% of sale price).

        Args:
            sale_price: The sale price of the item.

        Returns:
            The Depop fee amount.
        """
        return round(sale_price * (self.depop_fee_percent / 100), 2)

    def calculate_payment_processing_fee(self, sale_price: float) -> float:
        """
        Calculate payment processing fee (2.9% + $0.30).

        Args:
            sale_price: The sale price of the item.

        Returns:
            The payment processing fee amount.
        """
        percentage_fee = sale_price * (self.payment_percent / 100)
        return round(percentage_fee + self.payment_flat, 2)

    def calculate_sales_tax(
        self, sale_price: float, tax_percent: float = 0.0
    ) -> float:
        """
        Calculate sales tax.

        Args:
            sale_price: The sale price of the item.
            tax_percent: The sales tax percentage.

        Returns:
            The sales tax amount.
        """
        if tax_percent <= 0:
            return 0.0
        return round(sale_price * (tax_percent / 100), 2)

    def calculate_full_breakdown(
        self,
        sale_price: float,
        shipping_cost: float = 0.0,
        tax_percent: float = 0.0,
        cost_basis: float = 0.0,
    ) -> FeeBreakdownResult:
        """
        Calculate complete fee breakdown and profit.

        Args:
            sale_price: The sale price of the item.
            shipping_cost: The shipping cost (user's actual cost).
            tax_percent: The sales tax percentage.
            cost_basis: The original cost/purchase price of the item.

        Returns:
            FeeBreakdownResult with all fee details and net profit.
        """
        depop_fee = self.calculate_depop_fee(sale_price)
        payment_fee = self.calculate_payment_processing_fee(sale_price)
        sales_tax = self.calculate_sales_tax(sale_price, tax_percent)

        total_deductions = round(
            depop_fee + payment_fee + sales_tax + shipping_cost, 2
        )
        net_profit = round(sale_price - total_deductions - cost_basis, 2)

        # Calculate profit margin as percentage of sale price
        profit_margin_percent = 0.0
        if sale_price > 0:
            profit_margin_percent = round((net_profit / sale_price) * 100, 2)

        return FeeBreakdownResult(
            sale_price=sale_price,
            depop_fee=depop_fee,
            payment_processing_fee=payment_fee,
            sales_tax=sales_tax,
            shipping_cost=shipping_cost,
            total_deductions=total_deductions,
            net_profit=net_profit,
            profit_margin_percent=profit_margin_percent,
            cost_basis=cost_basis,
        )

    def calculate_required_price(
        self,
        target_profit: float,
        shipping_cost: float = 0.0,
        tax_percent: float = 0.0,
        cost_basis: float = 0.0,
    ) -> float:
        """
        Calculate required sale price to achieve target profit.

        Args:
            target_profit: Desired net profit.
            shipping_cost: The shipping cost.
            tax_percent: The sales tax percentage.
            cost_basis: The original cost/purchase price of the item.

        Returns:
            The required sale price.
        """
        # Net = Sale - (Sale * depop%) - (Sale * payment% + flat) - (Sale * tax%) - shipping - cost
        # Net = Sale * (1 - depop% - payment% - tax%) - flat - shipping - cost
        # Sale = (Net + flat + shipping + cost) / (1 - depop% - payment% - tax%)

        total_percent = (
            self.depop_fee_percent + self.payment_percent + tax_percent
        ) / 100

        if total_percent >= 1:
            raise ValueError("Total fee percentages cannot exceed 100%")

        numerator = target_profit + self.payment_flat + shipping_cost + cost_basis
        denominator = 1 - total_percent

        return round(numerator / denominator, 2)

    def estimate_profit_from_item(
        self,
        item_price: float,
        estimated_shipping: float = 0.0,
        tax_percent: float = 0.0,
    ) -> Optional[FeeBreakdownResult]:
        """
        Estimate profit for an item at its current price.

        Args:
            item_price: The current price of the item.
            estimated_shipping: Estimated shipping cost.
            tax_percent: The sales tax percentage.

        Returns:
            FeeBreakdownResult or None if invalid.
        """
        if item_price <= 0:
            return None

        return self.calculate_full_breakdown(
            sale_price=item_price,
            shipping_cost=estimated_shipping,
            tax_percent=tax_percent,
        )

    def get_fee_summary_string(self, breakdown: FeeBreakdownResult) -> str:
        """
        Get a formatted string summary of fees.

        Args:
            breakdown: The fee breakdown result.

        Returns:
            Formatted multi-line string showing all fees.
        """
        lines = [
            f"Sale Price: ${breakdown.sale_price:.2f}",
            "",
            "Fee Breakdown:",
            f"  Depop Fee ({self.depop_fee_percent}%): ${breakdown.depop_fee:.2f}",
            f"  Payment Processing ({self.payment_percent}% + ${self.payment_flat:.2f}): ${breakdown.payment_processing_fee:.2f}",
            f"  Sales Tax: ${breakdown.sales_tax:.2f}",
            f"  Shipping Cost: ${breakdown.shipping_cost:.2f}",
            "",
            f"Total Deductions: ${breakdown.total_deductions:.2f}",
        ]

        if breakdown.cost_basis > 0:
            lines.append(f"Cost Basis: ${breakdown.cost_basis:.2f}")

        lines.extend(
            [
                "",
                f"Net Profit: ${breakdown.net_profit:.2f}",
                f"Profit Margin: {breakdown.profit_margin_percent:.1f}%",
            ]
        )

        return "\n".join(lines)
