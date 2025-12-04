"""Fee breakdown display component for Pop-Scrape GUI."""

import customtkinter as ctk

from ..analysis.calculator import FeeBreakdownResult, ProfitCalculator


class FeeBreakdown(ctk.CTkFrame):
    """
    Display component showing detailed fee breakdown.

    Shows all fees/taxes included in price calculation:
    - Depop fee (10%)
    - Payment processing fee (2.9% + $0.30)
    - Sales tax (configurable)
    - Shipping cost (user input)
    - Total deductions
    - Net profit
    """

    def __init__(self, master: ctk.CTk, **kwargs):
        """
        Initialize the fee breakdown display.

        Args:
            master: Parent widget.
            **kwargs: Additional frame arguments.
        """
        super().__init__(master, **kwargs)

        self.calculator = ProfitCalculator()

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Fee Breakdown",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(10, 15), sticky="w")

        # Fee labels (left column: names, right column: values)
        self.fee_labels: dict[str, tuple[ctk.CTkLabel, ctk.CTkLabel]] = {}
        self._create_fee_row(1, "Sale Price", "sale_price")
        self._create_separator(2)
        self._create_fee_row(3, f"Depop Fee ({self.calculator.depop_fee_percent}%)", "depop_fee")
        self._create_fee_row(
            4,
            f"Payment Processing ({self.calculator.payment_percent}% + ${self.calculator.payment_flat:.2f})",
            "payment_fee",
        )
        self._create_fee_row(5, "Sales Tax", "sales_tax")
        self._create_fee_row(6, "Shipping Cost", "shipping_cost")
        self._create_separator(7)
        self._create_fee_row(8, "Total Deductions", "total_deductions", bold=True)
        self._create_separator(9)
        self._create_fee_row(10, "Net Profit", "net_profit", bold=True, highlight=True)
        self._create_fee_row(11, "Profit Margin", "profit_margin")

        # Initialize with zeros
        self.clear()

    def _create_fee_row(
        self,
        row: int,
        label_text: str,
        key: str,
        bold: bool = False,
        highlight: bool = False,
    ) -> None:
        """Create a row with label and value."""
        font = ctk.CTkFont(size=13, weight="bold" if bold else "normal")

        name_label = ctk.CTkLabel(
            self,
            text=label_text + ":",
            font=font,
            anchor="w",
        )
        name_label.grid(row=row, column=0, padx=(10, 5), pady=2, sticky="w")

        text_color = "#4CAF50" if highlight else None
        value_label = ctk.CTkLabel(
            self,
            text="$0.00",
            font=font,
            anchor="e",
            text_color=text_color,
        )
        value_label.grid(row=row, column=1, padx=(5, 10), pady=2, sticky="e")

        self.fee_labels[key] = (name_label, value_label)

    def _create_separator(self, row: int) -> None:
        """Create a visual separator line."""
        separator = ctk.CTkFrame(self, height=1, fg_color="gray50")
        separator.grid(row=row, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

    def update_breakdown(self, breakdown: FeeBreakdownResult) -> None:
        """
        Update the display with new breakdown values.

        Args:
            breakdown: FeeBreakdownResult containing all fee details.
        """
        self._set_value("sale_price", f"${breakdown.sale_price:.2f}")
        self._set_value("depop_fee", f"-${breakdown.depop_fee:.2f}")
        self._set_value("payment_fee", f"-${breakdown.payment_processing_fee:.2f}")
        self._set_value("sales_tax", f"-${breakdown.sales_tax:.2f}")
        self._set_value("shipping_cost", f"-${breakdown.shipping_cost:.2f}")
        self._set_value("total_deductions", f"-${breakdown.total_deductions:.2f}")

        # Color net profit based on positive/negative
        net_profit_label = self.fee_labels["net_profit"][1]
        if breakdown.net_profit >= 0:
            net_profit_label.configure(text_color="#4CAF50")  # Green
            self._set_value("net_profit", f"${breakdown.net_profit:.2f}")
        else:
            net_profit_label.configure(text_color="#F44336")  # Red
            self._set_value("net_profit", f"-${abs(breakdown.net_profit):.2f}")

        self._set_value("profit_margin", f"{breakdown.profit_margin_percent:.1f}%")

    def _set_value(self, key: str, value: str) -> None:
        """Set the value for a specific fee row."""
        if key in self.fee_labels:
            self.fee_labels[key][1].configure(text=value)

    def clear(self) -> None:
        """Clear all values to zero."""
        self._set_value("sale_price", "$0.00")
        self._set_value("depop_fee", "$0.00")
        self._set_value("payment_fee", "$0.00")
        self._set_value("sales_tax", "$0.00")
        self._set_value("shipping_cost", "$0.00")
        self._set_value("total_deductions", "$0.00")
        self._set_value("net_profit", "$0.00")
        self._set_value("profit_margin", "0.0%")

        # Reset color
        net_profit_label = self.fee_labels["net_profit"][1]
        net_profit_label.configure(text_color="#4CAF50")

    def update_tax_label(self, tax_percent: float) -> None:
        """Update the sales tax label with current percentage."""
        if "sales_tax" in self.fee_labels:
            self.fee_labels["sales_tax"][0].configure(
                text=f"Sales Tax ({tax_percent:.1f}%):"
            )
