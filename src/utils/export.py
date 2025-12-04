"""CSV export functionality for Pop-Scrape application."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import pandas as pd


class CSVExporter:
    """Handle CSV export operations for scraped data."""

    @staticmethod
    def export_to_csv(
        data: list[dict[str, Any]],
        filepath: Optional[Path] = None,
        filename_prefix: str = "depop_results",
    ) -> Path:
        """
        Export data to a CSV file.

        Args:
            data: List of dictionaries containing item data.
            filepath: Optional specific path for the output file.
            filename_prefix: Prefix for auto-generated filenames.

        Returns:
            Path: The path to the created CSV file.

        Raises:
            ValueError: If data is empty.
        """
        if not data:
            raise ValueError("No data to export")

        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path.cwd() / f"{filename_prefix}_{timestamp}.csv"

        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Use pandas for clean CSV export
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, quoting=csv.QUOTE_NONNUMERIC)

        return filepath

    @staticmethod
    def export_dataframe(
        df: pd.DataFrame,
        filepath: Optional[Path] = None,
        filename_prefix: str = "depop_results",
    ) -> Path:
        """
        Export a pandas DataFrame to CSV.

        Args:
            df: DataFrame to export.
            filepath: Optional specific path for the output file.
            filename_prefix: Prefix for auto-generated filenames.

        Returns:
            Path: The path to the created CSV file.

        Raises:
            ValueError: If DataFrame is empty.
        """
        if df.empty:
            raise ValueError("No data to export")

        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = Path.cwd() / f"{filename_prefix}_{timestamp}.csv"

        filepath.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath, index=False, quoting=csv.QUOTE_NONNUMERIC)

        return filepath

    @staticmethod
    def load_from_csv(filepath: Path) -> pd.DataFrame:
        """
        Load data from a CSV file.

        Args:
            filepath: Path to the CSV file.

        Returns:
            pd.DataFrame: The loaded data as a DataFrame.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file is not a valid CSV.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"CSV file not found: {filepath}")

        try:
            return pd.read_csv(filepath)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file: {e}") from e

    @staticmethod
    def get_export_columns() -> list[str]:
        """
        Get the standard column names for export.

        Returns:
            list[str]: List of column names.
        """
        return [
            "title",
            "price",
            "original_price",
            "sale_date",
            "days_on_market",
            "seller",
            "seller_rating",
            "category",
            "condition",
            "size",
            "brand",
            "description",
            "url",
            "image_url",
            "quantity_available",
            "estimated_profit",
            "profit_margin_percent",
        ]
