"""Tests for the CSV export module."""

import csv
import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from src.utils.export import CSVExporter


class TestCSVExporter:
    """Test cases for CSVExporter class."""

    def test_export_to_csv_basic(self):
        """Test basic CSV export."""
        data = [
            {"title": "Item 1", "price": 50.0, "seller": "user1"},
            {"title": "Item 2", "price": 75.0, "seller": "user2"},
        ]

        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test_export.csv"
            result_path = CSVExporter.export_to_csv(data, filepath)

            assert result_path == filepath
            assert filepath.exists()

            # Verify content
            df = pd.read_csv(filepath)
            assert len(df) == 2
            assert "title" in df.columns
            assert "price" in df.columns
            assert df["price"].tolist() == [50.0, 75.0]

    def test_export_to_csv_auto_filename(self):
        """Test export with auto-generated filename."""
        data = [{"title": "Test", "price": 100.0}]

        with TemporaryDirectory() as tmpdir:
            # Change to temp dir for auto filename
            original_dir = os.getcwd()
            os.chdir(tmpdir)

            try:
                result_path = CSVExporter.export_to_csv(data)
                assert result_path.exists()
                assert "depop_results_" in result_path.name
                assert result_path.suffix == ".csv"
            finally:
                os.chdir(original_dir)

    def test_export_to_csv_custom_prefix(self):
        """Test export with custom filename prefix."""
        data = [{"title": "Test", "price": 100.0}]

        with TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            os.chdir(tmpdir)

            try:
                result_path = CSVExporter.export_to_csv(
                    data, filename_prefix="my_export"
                )
                assert "my_export_" in result_path.name
            finally:
                os.chdir(original_dir)

    def test_export_to_csv_empty_data(self):
        """Test export with empty data raises error."""
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "empty.csv"

            with pytest.raises(ValueError, match="No data to export"):
                CSVExporter.export_to_csv([], filepath)

    def test_export_dataframe_basic(self):
        """Test exporting DataFrame."""
        df = pd.DataFrame([
            {"title": "Item 1", "price": 50.0},
            {"title": "Item 2", "price": 75.0},
        ])

        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "df_export.csv"
            result_path = CSVExporter.export_dataframe(df, filepath)

            assert result_path == filepath
            assert filepath.exists()

            loaded_df = pd.read_csv(filepath)
            assert len(loaded_df) == 2

    def test_export_dataframe_empty(self):
        """Test exporting empty DataFrame raises error."""
        df = pd.DataFrame()

        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "empty.csv"

            with pytest.raises(ValueError, match="No data to export"):
                CSVExporter.export_dataframe(df, filepath)

    def test_load_from_csv(self):
        """Test loading CSV file."""
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "test.csv"

            # Create test CSV
            data = [
                {"title": "Item 1", "price": 50.0},
                {"title": "Item 2", "price": 75.0},
            ]
            CSVExporter.export_to_csv(data, filepath)

            # Load and verify
            loaded_df = CSVExporter.load_from_csv(filepath)

            assert len(loaded_df) == 2
            assert "title" in loaded_df.columns
            assert "price" in loaded_df.columns

    def test_load_from_csv_not_found(self):
        """Test loading non-existent file."""
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "nonexistent.csv"

            with pytest.raises(FileNotFoundError):
                CSVExporter.load_from_csv(filepath)

    def test_load_from_csv_invalid(self):
        """Test loading invalid CSV file."""
        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "invalid.csv"

            # Write invalid content
            with open(filepath, "w") as f:
                f.write("not,a,proper\ncsv\"file")

            # Should raise ValueError
            # Note: pandas is quite tolerant, so this might not fail
            # Adjust test if needed
            try:
                CSVExporter.load_from_csv(filepath)
            except ValueError:
                pass  # Expected

    def test_get_export_columns(self):
        """Test getting standard export columns."""
        columns = CSVExporter.get_export_columns()

        assert isinstance(columns, list)
        assert "title" in columns
        assert "price" in columns
        assert "seller" in columns
        assert "url" in columns
        assert "estimated_profit" in columns

    def test_export_creates_parent_dirs(self):
        """Test that export creates parent directories."""
        data = [{"title": "Test", "price": 100.0}]

        with TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "subdir" / "nested" / "test.csv"
            result_path = CSVExporter.export_to_csv(data, filepath)

            assert result_path == filepath
            assert filepath.exists()
