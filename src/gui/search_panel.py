"""Search panel for Pop-Scrape GUI."""

from typing import Callable, Optional

import customtkinter as ctk

from ..scraper.parser import DataParser


class SearchPanel(ctk.CTkFrame):
    """
    Search interface panel with filters.

    Features:
    - Search bar with keyword input
    - Category dropdown filter
    - Price range filters (min/max)
    - Search button with callback
    """

    def __init__(
        self,
        master: ctk.CTk,
        on_search: Optional[Callable[[dict], None]] = None,
        **kwargs,
    ):
        """
        Initialize the search panel.

        Args:
            master: Parent widget.
            on_search: Callback when search is triggered.
            **kwargs: Additional frame arguments.
        """
        super().__init__(master, **kwargs)

        self.on_search = on_search

        # Configure grid
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Search Depop",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.title_label.grid(row=0, column=0, columnspan=4, pady=(15, 20), padx=15, sticky="w")

        # Search keyword
        self.keyword_label = ctk.CTkLabel(
            self,
            text="Keyword:",
            font=ctk.CTkFont(size=13),
        )
        self.keyword_label.grid(row=1, column=0, padx=(15, 10), pady=8, sticky="w")

        self.keyword_entry = ctk.CTkEntry(
            self,
            placeholder_text="Enter search term...",
            width=250,
        )
        self.keyword_entry.grid(row=1, column=1, columnspan=3, padx=(0, 15), pady=8, sticky="ew")
        self.keyword_entry.bind("<Return>", lambda e: self._trigger_search())

        # Category dropdown
        self.category_label = ctk.CTkLabel(
            self,
            text="Category:",
            font=ctk.CTkFont(size=13),
        )
        self.category_label.grid(row=2, column=0, padx=(15, 10), pady=8, sticky="w")

        categories = DataParser.get_category_names()
        self.category_dropdown = ctk.CTkComboBox(
            self,
            values=categories,
            width=150,
            state="readonly",
        )
        self.category_dropdown.set("All")
        self.category_dropdown.grid(row=2, column=1, pady=8, sticky="w")

        # Price range filters
        self.price_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.price_frame.grid(row=3, column=0, columnspan=4, padx=15, pady=8, sticky="ew")

        self.min_price_label = ctk.CTkLabel(
            self.price_frame,
            text="Min Price ($):",
            font=ctk.CTkFont(size=13),
        )
        self.min_price_label.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="w")

        self.min_price_entry = ctk.CTkEntry(
            self.price_frame,
            placeholder_text="0",
            width=80,
        )
        self.min_price_entry.grid(row=0, column=1, padx=(0, 20), pady=0, sticky="w")

        self.max_price_label = ctk.CTkLabel(
            self.price_frame,
            text="Max Price ($):",
            font=ctk.CTkFont(size=13),
        )
        self.max_price_label.grid(row=0, column=2, padx=(0, 10), pady=0, sticky="w")

        self.max_price_entry = ctk.CTkEntry(
            self.price_frame,
            placeholder_text="999",
            width=80,
        )
        self.max_price_entry.grid(row=0, column=3, pady=0, sticky="w")

        # Search type toggle (sold items vs available)
        self.search_type_label = ctk.CTkLabel(
            self,
            text="Show:",
            font=ctk.CTkFont(size=13),
        )
        self.search_type_label.grid(row=4, column=0, padx=(15, 10), pady=8, sticky="w")

        self.search_type_var = ctk.StringVar(value="sold")
        self.sold_radio = ctk.CTkRadioButton(
            self,
            text="Sold Items",
            variable=self.search_type_var,
            value="sold",
        )
        self.sold_radio.grid(row=4, column=1, pady=8, sticky="w")

        self.available_radio = ctk.CTkRadioButton(
            self,
            text="Available Items",
            variable=self.search_type_var,
            value="available",
        )
        self.available_radio.grid(row=4, column=2, pady=8, sticky="w")

        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.buttons_frame.grid(row=5, column=0, columnspan=4, padx=15, pady=15, sticky="ew")

        self.search_button = ctk.CTkButton(
            self.buttons_frame,
            text="🔍 Search",
            command=self._trigger_search,
            width=120,
            height=35,
            font=ctk.CTkFont(size=14),
        )
        self.search_button.grid(row=0, column=0, padx=(0, 10))

        self.clear_button = ctk.CTkButton(
            self.buttons_frame,
            text="Clear",
            command=self.clear,
            width=80,
            height=35,
            fg_color="gray40",
            hover_color="gray50",
        )
        self.clear_button.grid(row=0, column=1)

        # Loading indicator (hidden by default)
        self.loading_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray60",
        )
        self.loading_label.grid(row=6, column=0, columnspan=4, pady=5)

    def _trigger_search(self) -> None:
        """Trigger search with current parameters."""
        if self.on_search:
            params = self.get_search_params()
            self.on_search(params)

    def get_search_params(self) -> dict:
        """
        Get current search parameters.

        Returns:
            Dictionary with search parameters.
        """
        keyword = self.keyword_entry.get().strip()
        category = self.category_dropdown.get()
        search_type = self.search_type_var.get()

        # Parse price filters
        min_price = None
        max_price = None

        try:
            min_text = self.min_price_entry.get().strip()
            if min_text:
                min_price = float(min_text)
        except ValueError:
            pass

        try:
            max_text = self.max_price_entry.get().strip()
            if max_text:
                max_price = float(max_text)
        except ValueError:
            pass

        return {
            "keyword": keyword,
            "category": DataParser.get_category_slug(category),
            "category_name": category,
            "min_price": min_price,
            "max_price": max_price,
            "search_type": search_type,
        }

    def set_search_params(
        self,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        search_type: Optional[str] = None,
    ) -> None:
        """
        Set search parameters.

        Args:
            keyword: Search keyword.
            category: Category name.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            search_type: 'sold' or 'available'.
        """
        if keyword is not None:
            self.keyword_entry.delete(0, "end")
            self.keyword_entry.insert(0, keyword)

        if category is not None:
            self.category_dropdown.set(category)

        if min_price is not None:
            self.min_price_entry.delete(0, "end")
            self.min_price_entry.insert(0, str(min_price))

        if max_price is not None:
            self.max_price_entry.delete(0, "end")
            self.max_price_entry.insert(0, str(max_price))

        if search_type is not None:
            self.search_type_var.set(search_type)

    def clear(self) -> None:
        """Clear all search fields."""
        self.keyword_entry.delete(0, "end")
        self.category_dropdown.set("All")
        self.min_price_entry.delete(0, "end")
        self.max_price_entry.delete(0, "end")
        self.search_type_var.set("sold")

    def set_loading(self, loading: bool, message: str = "") -> None:
        """
        Set loading state.

        Args:
            loading: Whether loading is in progress.
            message: Loading message to display.
        """
        if loading:
            self.search_button.configure(state="disabled", text="Searching...")
            self.loading_label.configure(text=message or "Searching...")
        else:
            self.search_button.configure(state="normal", text="🔍 Search")
            self.loading_label.configure(text="")

    def enable_search(self, enabled: bool = True) -> None:
        """Enable or disable the search button."""
        state = "normal" if enabled else "disabled"
        self.search_button.configure(state=state)
