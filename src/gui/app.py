"""Main application window for Pop-Scrape."""

import asyncio
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from ..analysis.analyzer import SaleAnalyzer
from ..analysis.calculator import FeeBreakdownResult, ProfitCalculator
from ..scraper.depop_api import DepopAPI
from ..scraper.parser import DataParser, DepopItem
from ..utils.config import Config
from ..utils.export import CSVExporter
from .calculator_panel import CalculatorPanel
from .results_table import ResultsTable
from .search_panel import SearchPanel


class PopScrapeApp(ctk.CTk):
    """
    Main application window for Pop-Scrape.

    Features:
    - Search panel for Depop searches
    - Results table with sorting
    - Profit calculator panel
    - Export functionality
    - Dark/light mode toggle
    """

    def __init__(self):
        """Initialize the Pop-Scrape application."""
        super().__init__()

        # Load configuration
        self.config = Config()

        # Set appearance mode
        ctk.set_appearance_mode(self.config.theme)
        ctk.set_default_color_theme("blue")

        # Window setup
        self.title("Pop-Scrape - Depop Product Analyzer")
        self.geometry(
            f"{self.config.config.window_width}x{self.config.config.window_height}"
        )
        self.minsize(1000, 700)

        # Initialize components
        self.analyzer = SaleAnalyzer()
        self.calculator = ProfitCalculator()
        self._current_items: list[DepopItem] = []

        # Configure main grid
        self.grid_columnconfigure(0, weight=1)  # Left panel
        self.grid_columnconfigure(1, weight=2)  # Center (results)
        self.grid_columnconfigure(2, weight=1)  # Right panel
        self.grid_rowconfigure(1, weight=1)

        # Create UI components
        self._create_header()
        self._create_search_panel()
        self._create_results_panel()
        self._create_calculator_panel()
        self._create_status_bar()

        # Load saved preferences
        self._load_preferences()

    def _create_header(self) -> None:
        """Create the header with title and controls."""
        self.header_frame = ctk.CTkFrame(self, height=50)
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))
        self.header_frame.grid_columnconfigure(1, weight=1)

        # App title
        self.app_title = ctk.CTkLabel(
            self.header_frame,
            text="🛍️ Pop-Scrape",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        self.app_title.grid(row=0, column=0, padx=15, pady=10)

        # Subtitle
        self.subtitle = ctk.CTkLabel(
            self.header_frame,
            text="Depop Product Analyzer & Profit Calculator",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        )
        self.subtitle.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Theme toggle
        self.theme_switch = ctk.CTkSwitch(
            self.header_frame,
            text="Dark Mode",
            command=self._toggle_theme,
            onvalue="dark",
            offvalue="light",
        )
        self.theme_switch.grid(row=0, column=2, padx=15, pady=10)
        if self.config.theme == "dark":
            self.theme_switch.select()

        # Export button
        self.export_button = ctk.CTkButton(
            self.header_frame,
            text="📁 Export CSV",
            command=self._export_results,
            width=100,
        )
        self.export_button.grid(row=0, column=3, padx=10, pady=10)

    def _create_search_panel(self) -> None:
        """Create the search panel on the left."""
        self.search_panel = SearchPanel(
            self,
            on_search=self._on_search,
        )
        self.search_panel.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=5)

        # Analysis summary frame
        self.summary_frame = ctk.CTkFrame(self)
        self.summary_frame.grid(row=2, column=0, sticky="ew", padx=(10, 5), pady=(0, 10))

        self.summary_title = ctk.CTkLabel(
            self.summary_frame,
            text="Analysis Summary",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.summary_title.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.summary_text = ctk.CTkLabel(
            self.summary_frame,
            text="No data loaded",
            font=ctk.CTkFont(size=11),
            justify="left",
        )
        self.summary_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="w")

    def _create_results_panel(self) -> None:
        """Create the results panel in the center."""
        self.results_frame = ctk.CTkFrame(self)
        self.results_frame.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=5, pady=5)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(1, weight=1)

        # Results header with sort controls
        self.results_header = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        self.results_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.results_header.grid_columnconfigure(1, weight=1)

        self.results_title = ctk.CTkLabel(
            self.results_header,
            text="Search Results",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.results_title.grid(row=0, column=0, sticky="w")

        self.results_count = ctk.CTkLabel(
            self.results_header,
            text="0 items",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        )
        self.results_count.grid(row=0, column=1, padx=15, sticky="w")

        # Sort controls
        self.sort_label = ctk.CTkLabel(
            self.results_header,
            text="Sort by:",
            font=ctk.CTkFont(size=12),
        )
        self.sort_label.grid(row=0, column=2, padx=(0, 5))

        self.sort_dropdown = ctk.CTkComboBox(
            self.results_header,
            values=["Price", "Days Listed", "Quantity", "Seller", "Title"],
            width=120,
            command=self._on_sort_change,
        )
        self.sort_dropdown.set("Price")
        self.sort_dropdown.grid(row=0, column=3, padx=5)

        self.sort_direction = ctk.CTkButton(
            self.results_header,
            text="▲",
            width=30,
            command=self._toggle_sort_direction,
        )
        self.sort_direction.grid(row=0, column=4, padx=5)
        self._sort_ascending = True

        # Results table
        self.results_table = ResultsTable(
            self.results_frame,
            on_row_select=self._on_item_select,
            on_sort=self._on_table_sort,
        )
        self.results_table.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _create_calculator_panel(self) -> None:
        """Create the calculator panel on the right."""
        self.calculator_panel = CalculatorPanel(
            self,
            on_calculate=self._on_calculate,
        )
        self.calculator_panel.grid(row=1, column=2, rowspan=2, sticky="nsew", padx=(5, 10), pady=5)

    def _create_status_bar(self) -> None:
        """Create the status bar at the bottom."""
        self.status_frame = ctk.CTkFrame(self, height=30)
        self.status_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=11),
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

    def _toggle_theme(self) -> None:
        """Toggle between dark and light mode."""
        new_theme = self.theme_switch.get()
        ctk.set_appearance_mode(new_theme)
        self.config.set_theme(new_theme)
        self.config.save()

    def _on_search(self, params: dict) -> None:
        """Handle search request."""
        keyword = params.get("keyword", "").strip()
        if not keyword:
            messagebox.showwarning("Search", "Please enter a search keyword.")
            return

        # Update status
        self._set_status("Searching...")
        self.search_panel.set_loading(True, "Searching Depop...")

        # Run search in background thread
        thread = threading.Thread(target=self._run_search, args=(params,))
        thread.daemon = True
        thread.start()

    def _run_search(self, params: dict) -> None:
        """Run search in background thread."""
        try:
            # Create event loop for async operations
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            items = loop.run_until_complete(self._async_search(params))
            loop.close()

            # Update UI in main thread
            self.after(0, lambda: self._handle_search_results(items))

        except Exception as e:
            self.after(0, lambda: self._handle_search_error(str(e)))

    async def _async_search(self, params: dict) -> list[DepopItem]:
        """Perform async search."""
        async with DepopAPI(rate_limit_delay=self.config.rate_limit_delay) as api:
            if params.get("search_type") == "sold":
                return await api.search_sold_items(
                    keyword=params["keyword"],
                    category=params.get("category", ""),
                    min_price=params.get("min_price"),
                    max_price=params.get("max_price"),
                    limit=self.config.config.max_results,
                )
            else:
                return await api.search_available_items(
                    keyword=params["keyword"],
                    category=params.get("category", ""),
                    min_price=params.get("min_price"),
                    max_price=params.get("max_price"),
                    limit=self.config.config.max_results,
                )

    def _handle_search_results(self, items: list[DepopItem]) -> None:
        """Handle search results in main thread."""
        self._current_items = items
        self.results_table.set_items(items)
        self.results_count.configure(text=f"{len(items)} items")

        # Update analysis summary
        analysis = self.analyzer.analyze_items(items)
        summary_lines = [
            f"Total items: {analysis.total_items}",
            f"Quick sales: {analysis.quick_sale_items}",
            f"Low quantity: {analysis.low_quantity_items}",
            f"Avg price: ${analysis.avg_price:.2f}",
            f"Median price: ${analysis.median_price:.2f}",
        ]
        if analysis.avg_days_to_sell is not None:
            summary_lines.append(f"Avg days to sell: {analysis.avg_days_to_sell:.1f}")

        self.summary_text.configure(text="\n".join(summary_lines))

        # Save search preferences
        params = self.search_panel.get_search_params()
        self.config.update_search_preferences(
            keyword=params["keyword"],
            category=params["category_name"],
            min_price=params.get("min_price"),
            max_price=params.get("max_price"),
        )
        self.config.save()

        self.search_panel.set_loading(False)
        self._set_status(f"Found {len(items)} items")

    def _handle_search_error(self, error: str) -> None:
        """Handle search error."""
        self.search_panel.set_loading(False)
        self._set_status(f"Error: {error}")
        messagebox.showerror("Search Error", f"Failed to search: {error}")

    def _on_item_select(self, item: DepopItem) -> None:
        """Handle item selection in results table."""
        # Populate calculator with item price
        self.calculator_panel.set_price(item.price)
        self._set_status(f"Selected: {item.title[:50]}...")

    def _on_calculate(self, result: FeeBreakdownResult) -> None:
        """Handle calculation result."""
        pass  # Could be used for additional processing

    def _on_sort_change(self, value: str) -> None:
        """Handle sort dropdown change."""
        sort_map = {
            "Price": "price",
            "Days Listed": "days_on_market",
            "Quantity": "quantity_available",
            "Seller": "seller",
            "Title": "title",
        }
        column = sort_map.get(value, "price")
        self.results_table.sort_by(column, self._sort_ascending)

    def _toggle_sort_direction(self) -> None:
        """Toggle sort direction."""
        self._sort_ascending = not self._sort_ascending
        arrow = "▲" if self._sort_ascending else "▼"
        self.sort_direction.configure(text=arrow)

        # Re-sort current column
        self._on_sort_change(self.sort_dropdown.get())

    def _on_table_sort(self, column: str, ascending: bool) -> None:
        """Handle sort from table header click."""
        self._sort_ascending = ascending
        arrow = "▲" if ascending else "▼"
        self.sort_direction.configure(text=arrow)

        # Update dropdown to match
        column_map = {
            "price": "Price",
            "days_on_market": "Days Listed",
            "quantity_available": "Quantity",
            "seller": "Seller",
            "title": "Title",
        }
        if column in column_map:
            self.sort_dropdown.set(column_map[column])

    def _export_results(self) -> None:
        """Export results to CSV file."""
        if not self._current_items:
            messagebox.showwarning("Export", "No data to export. Run a search first.")
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Results",
        )

        if filepath:
            try:
                data = [item.to_dict() for item in self._current_items]
                CSVExporter.export_to_csv(data, Path(filepath))
                self._set_status(f"Exported to {filepath}")
                messagebox.showinfo("Export", f"Successfully exported {len(data)} items.")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {e}")

    def _load_preferences(self) -> None:
        """Load saved search preferences."""
        prefs = self.config.config.search_preferences
        if prefs.last_keyword:
            self.search_panel.set_search_params(
                keyword=prefs.last_keyword,
                category=prefs.category,
                min_price=prefs.min_price,
                max_price=prefs.max_price,
            )
        if prefs.default_tax_percent > 0:
            self.calculator_panel.set_tax_percent(prefs.default_tax_percent)
        if prefs.default_shipping_cost > 0:
            self.calculator_panel.set_shipping(prefs.default_shipping_cost)

    def _set_status(self, message: str) -> None:
        """Update status bar message."""
        self.status_label.configure(text=message)

    def run(self) -> None:
        """Run the application main loop."""
        self.mainloop()
