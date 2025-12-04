"""Sortable results table for Pop-Scrape GUI."""

from typing import Any, Callable, Optional

import customtkinter as ctk

from ..scraper.parser import DepopItem


class ResultsTable(ctk.CTkScrollableFrame):
    """
    Sortable table for displaying search results.

    Features:
    - Clickable column headers for sorting
    - Ascending/descending toggle
    - Row selection with callback
    - Multiple sort options
    """

    # Column definitions: (key, display_name, width, sortable)
    COLUMNS = [
        ("title", "Title", 200, True),
        ("price", "Price", 80, True),
        ("days_on_market", "Days Listed", 90, True),
        ("quantity_available", "Qty", 50, True),
        ("seller", "Seller", 100, True),
        ("category", "Category", 100, True),
        ("is_sold", "Status", 70, False),
    ]

    def __init__(
        self,
        master: ctk.CTk,
        on_row_select: Optional[Callable[[DepopItem], None]] = None,
        on_sort: Optional[Callable[[str, bool], None]] = None,
        **kwargs,
    ):
        """
        Initialize the results table.

        Args:
            master: Parent widget.
            on_row_select: Callback when a row is selected.
            on_sort: Callback when sort is triggered.
            **kwargs: Additional frame arguments.
        """
        super().__init__(master, **kwargs)

        self.on_row_select = on_row_select
        self.on_sort = on_sort

        self._items: list[DepopItem] = []
        self._row_frames: list[ctk.CTkFrame] = []
        self._selected_index: Optional[int] = None
        self._sort_column: str = "price"
        self._sort_ascending: bool = True

        # Configure grid
        for i, (_, _, width, _) in enumerate(self.COLUMNS):
            self.grid_columnconfigure(i, weight=1, minsize=width)

        # Create header row
        self._create_headers()

    def _create_headers(self) -> None:
        """Create the header row with sortable columns."""
        self.header_frame = ctk.CTkFrame(self, fg_color="gray25")
        self.header_frame.grid(row=0, column=0, columnspan=len(self.COLUMNS), sticky="ew")

        for i, (key, name, width, sortable) in enumerate(self.COLUMNS):
            self.header_frame.grid_columnconfigure(i, weight=1, minsize=width)

            header_text = name
            if sortable and key == self._sort_column:
                arrow = "▲" if self._sort_ascending else "▼"
                header_text = f"{name} {arrow}"

            header_btn = ctk.CTkButton(
                self.header_frame,
                text=header_text,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent",
                hover_color="gray35",
                anchor="w",
                command=lambda k=key, s=sortable: self._on_header_click(k, s),
            )
            header_btn.grid(row=0, column=i, padx=2, pady=2, sticky="ew")

    def _on_header_click(self, column_key: str, sortable: bool) -> None:
        """Handle header click for sorting."""
        if not sortable:
            return

        if column_key == self._sort_column:
            # Toggle sort direction
            self._sort_ascending = not self._sort_ascending
        else:
            # New column, default to ascending
            self._sort_column = column_key
            self._sort_ascending = True

        # Update headers to show sort indicator
        self._create_headers()

        # Re-sort and redisplay
        self._sort_items()
        self._display_items()

        # Trigger callback
        if self.on_sort:
            self.on_sort(self._sort_column, self._sort_ascending)

    def _sort_items(self) -> None:
        """Sort items based on current sort settings."""
        if not self._items:
            return

        def get_sort_key(item: DepopItem) -> Any:
            value = getattr(item, self._sort_column, None)
            if value is None:
                # Put None values at the end
                return (1, "")
            if isinstance(value, str):
                return (0, value.lower())
            return (0, value)

        self._items.sort(key=get_sort_key, reverse=not self._sort_ascending)

    def set_items(self, items: list[DepopItem]) -> None:
        """
        Set the items to display in the table.

        Args:
            items: List of DepopItem objects.
        """
        self._items = items.copy()
        self._selected_index = None
        self._sort_items()
        self._display_items()

    def _display_items(self) -> None:
        """Display all items in the table."""
        # Clear existing rows
        for frame in self._row_frames:
            frame.destroy()
        self._row_frames.clear()

        # Create new rows
        for i, item in enumerate(self._items):
            self._create_row(i, item)

    def _create_row(self, index: int, item: DepopItem) -> None:
        """Create a row for an item."""
        # Alternate row colors
        bg_color = "gray20" if index % 2 == 0 else "gray17"

        row_frame = ctk.CTkFrame(self, fg_color=bg_color, corner_radius=0)
        row_frame.grid(row=index + 1, column=0, columnspan=len(self.COLUMNS), sticky="ew")

        for j, (key, _, width, _) in enumerate(self.COLUMNS):
            row_frame.grid_columnconfigure(j, weight=1, minsize=width)

            value = getattr(item, key, "")

            # Format value for display
            display_value = self._format_value(key, value)

            label = ctk.CTkLabel(
                row_frame,
                text=display_value,
                font=ctk.CTkFont(size=12),
                anchor="w",
            )
            label.grid(row=0, column=j, padx=5, pady=4, sticky="w")

            # Bind click event
            label.bind("<Button-1>", lambda e, idx=index: self._on_row_click(idx))

        row_frame.bind("<Button-1>", lambda e, idx=index: self._on_row_click(idx))
        self._row_frames.append(row_frame)

    def _format_value(self, key: str, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "-"

        if key == "price":
            return f"${value:.2f}"
        elif key == "days_on_market":
            if value is None:
                return "-"
            return str(int(value))
        elif key == "is_sold":
            return "Sold" if value else "Available"
        elif key == "title":
            # Truncate long titles
            return value[:40] + "..." if len(str(value)) > 40 else str(value)
        else:
            return str(value)

    def _on_row_click(self, index: int) -> None:
        """Handle row click for selection."""
        # Update selection highlighting
        if self._selected_index is not None and self._selected_index < len(self._row_frames):
            old_bg = "gray20" if self._selected_index % 2 == 0 else "gray17"
            self._row_frames[self._selected_index].configure(fg_color=old_bg)

        self._selected_index = index
        self._row_frames[index].configure(fg_color="gray40")

        # Trigger callback
        if self.on_row_select and index < len(self._items):
            self.on_row_select(self._items[index])

    def get_selected_item(self) -> Optional[DepopItem]:
        """Get the currently selected item."""
        if self._selected_index is not None and self._selected_index < len(self._items):
            return self._items[self._selected_index]
        return None

    def clear(self) -> None:
        """Clear all items from the table."""
        for frame in self._row_frames:
            frame.destroy()
        self._row_frames.clear()
        self._items.clear()
        self._selected_index = None

    def sort_by(self, column: str, ascending: bool = True) -> None:
        """
        Sort the table by the specified column.

        Args:
            column: Column key to sort by.
            ascending: Sort order.
        """
        self._sort_column = column
        self._sort_ascending = ascending
        self._create_headers()
        self._sort_items()
        self._display_items()

    def get_items(self) -> list[DepopItem]:
        """Get all items currently in the table."""
        return self._items.copy()

    def get_sort_options(self) -> list[str]:
        """Get list of sortable column keys."""
        return [key for key, _, _, sortable in self.COLUMNS if sortable]
