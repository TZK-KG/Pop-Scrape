"""Profit calculator panel for Pop-Scrape GUI."""

from typing import Callable, Optional

import customtkinter as ctk

from ..analysis.calculator import FeeBreakdownResult, ProfitCalculator
from .fee_breakdown import FeeBreakdown


class CalculatorPanel(ctk.CTkFrame):
    """
    Profit calculator panel with input fields and fee breakdown.

    Features:
    - Input field for retail/resale price
    - Input field for shipping cost (manual entry)
    - Input field for sales tax percentage
    - Auto-calculated fee deductions
    - Detailed fee breakdown display
    """

    def __init__(
        self,
        master: ctk.CTk,
        on_calculate: Optional[Callable[[FeeBreakdownResult], None]] = None,
        **kwargs,
    ):
        """
        Initialize the calculator panel.

        Args:
            master: Parent widget.
            on_calculate: Optional callback when calculation is performed.
            **kwargs: Additional frame arguments.
        """
        super().__init__(master, **kwargs)

        self.on_calculate = on_calculate
        self.calculator = ProfitCalculator()

        # Configure grid
        self.grid_columnconfigure(0, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Profit Calculator",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, pady=(15, 20), padx=15, sticky="w")

        # Input fields frame
        self.inputs_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.inputs_frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        self.inputs_frame.grid_columnconfigure(1, weight=1)

        # Sale Price input
        self.price_label = ctk.CTkLabel(
            self.inputs_frame,
            text="Sale Price ($):",
            font=ctk.CTkFont(size=13),
        )
        self.price_label.grid(row=0, column=0, padx=(0, 10), pady=8, sticky="w")

        self.price_entry = ctk.CTkEntry(
            self.inputs_frame,
            placeholder_text="0.00",
            width=120,
        )
        self.price_entry.grid(row=0, column=1, pady=8, sticky="w")
        self.price_entry.bind("<KeyRelease>", self._on_input_change)

        # Cost Basis input (optional)
        self.cost_label = ctk.CTkLabel(
            self.inputs_frame,
            text="Cost Basis ($):",
            font=ctk.CTkFont(size=13),
        )
        self.cost_label.grid(row=1, column=0, padx=(0, 10), pady=8, sticky="w")

        self.cost_entry = ctk.CTkEntry(
            self.inputs_frame,
            placeholder_text="0.00 (optional)",
            width=120,
        )
        self.cost_entry.grid(row=1, column=1, pady=8, sticky="w")
        self.cost_entry.bind("<KeyRelease>", self._on_input_change)

        # Shipping Cost input
        self.shipping_label = ctk.CTkLabel(
            self.inputs_frame,
            text="Shipping Cost ($):",
            font=ctk.CTkFont(size=13),
        )
        self.shipping_label.grid(row=2, column=0, padx=(0, 10), pady=8, sticky="w")

        self.shipping_entry = ctk.CTkEntry(
            self.inputs_frame,
            placeholder_text="0.00",
            width=120,
        )
        self.shipping_entry.grid(row=2, column=1, pady=8, sticky="w")
        self.shipping_entry.bind("<KeyRelease>", self._on_input_change)

        # Sales Tax Percentage input
        self.tax_label = ctk.CTkLabel(
            self.inputs_frame,
            text="Sales Tax (%):",
            font=ctk.CTkFont(size=13),
        )
        self.tax_label.grid(row=3, column=0, padx=(0, 10), pady=8, sticky="w")

        self.tax_entry = ctk.CTkEntry(
            self.inputs_frame,
            placeholder_text="0.0",
            width=120,
        )
        self.tax_entry.grid(row=3, column=1, pady=8, sticky="w")
        self.tax_entry.bind("<KeyRelease>", self._on_input_change)

        # Calculate button
        self.calculate_button = ctk.CTkButton(
            self,
            text="Calculate Profit",
            command=self._calculate,
            width=200,
            height=35,
        )
        self.calculate_button.grid(row=2, column=0, pady=15)

        # Fee breakdown display
        self.fee_breakdown = FeeBreakdown(self)
        self.fee_breakdown.grid(row=3, column=0, padx=15, pady=10, sticky="ew")

        # Last calculated result
        self._last_result: Optional[FeeBreakdownResult] = None

    def _on_input_change(self, event=None) -> None:
        """Handle input field changes for auto-calculation."""
        # Auto-calculate on input change
        self._calculate()

    def _calculate(self) -> None:
        """Perform profit calculation and update display."""
        try:
            # Parse inputs
            price_text = self.price_entry.get().strip()
            sale_price = float(price_text) if price_text else 0.0

            cost_text = self.cost_entry.get().strip()
            cost_basis = float(cost_text) if cost_text else 0.0

            shipping_text = self.shipping_entry.get().strip()
            shipping_cost = float(shipping_text) if shipping_text else 0.0

            tax_text = self.tax_entry.get().strip()
            tax_percent = float(tax_text) if tax_text else 0.0

            # Validate inputs
            if sale_price < 0 or shipping_cost < 0 or tax_percent < 0:
                return

            # Calculate breakdown
            result = self.calculator.calculate_full_breakdown(
                sale_price=sale_price,
                shipping_cost=shipping_cost,
                tax_percent=tax_percent,
                cost_basis=cost_basis,
            )

            # Update display
            self.fee_breakdown.update_breakdown(result)
            self.fee_breakdown.update_tax_label(tax_percent)

            self._last_result = result

            # Trigger callback if set
            if self.on_calculate:
                self.on_calculate(result)

        except ValueError:
            # Invalid input, ignore
            pass

    def set_price(self, price: float) -> None:
        """
        Set the sale price input value.

        Args:
            price: The price to set.
        """
        self.price_entry.delete(0, "end")
        self.price_entry.insert(0, f"{price:.2f}")
        self._calculate()

    def set_shipping(self, shipping: float) -> None:
        """
        Set the shipping cost input value.

        Args:
            shipping: The shipping cost to set.
        """
        self.shipping_entry.delete(0, "end")
        self.shipping_entry.insert(0, f"{shipping:.2f}")
        self._calculate()

    def set_tax_percent(self, tax: float) -> None:
        """
        Set the sales tax percentage input value.

        Args:
            tax: The tax percentage to set.
        """
        self.tax_entry.delete(0, "end")
        self.tax_entry.insert(0, f"{tax:.1f}")
        self._calculate()

    def set_cost_basis(self, cost: float) -> None:
        """
        Set the cost basis input value.

        Args:
            cost: The cost basis to set.
        """
        self.cost_entry.delete(0, "end")
        self.cost_entry.insert(0, f"{cost:.2f}")
        self._calculate()

    def get_last_result(self) -> Optional[FeeBreakdownResult]:
        """Get the last calculated result."""
        return self._last_result

    def clear(self) -> None:
        """Clear all inputs and reset display."""
        self.price_entry.delete(0, "end")
        self.cost_entry.delete(0, "end")
        self.shipping_entry.delete(0, "end")
        self.tax_entry.delete(0, "end")
        self.fee_breakdown.clear()
        self._last_result = None
