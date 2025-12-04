"""Tests for the data parser module."""

import pytest
from datetime import datetime

from src.scraper.parser import DataParser, DepopItem


class TestDepopItem:
    """Test cases for DepopItem dataclass."""

    def test_create_basic_item(self):
        """Test creating a basic item."""
        item = DepopItem(
            id="123",
            title="Test Item",
            price=50.0,
        )

        assert item.id == "123"
        assert item.title == "Test Item"
        assert item.price == 50.0
        assert item.currency == "USD"
        assert item.is_sold is False

    def test_item_to_dict(self):
        """Test converting item to dictionary."""
        item = DepopItem(
            id="123",
            title="Test Item",
            price=50.0,
            seller="testuser",
            category="Vintage",
        )

        result = item.to_dict()

        assert result["id"] == "123"
        assert result["title"] == "Test Item"
        assert result["price"] == 50.0
        assert result["seller"] == "testuser"
        assert result["category"] == "Vintage"

    def test_item_to_dict_with_dates(self):
        """Test dictionary conversion with dates."""
        now = datetime.now()
        item = DepopItem(
            id="123",
            title="Test Item",
            price=50.0,
            sale_date=now,
            listed_date=now,
        )

        result = item.to_dict()

        assert result["sale_date"] == now.isoformat()
        assert result["listed_date"] == now.isoformat()


class TestDataParser:
    """Test cases for DataParser class."""

    def test_get_category_names(self):
        """Test getting category names."""
        categories = DataParser.get_category_names()

        assert isinstance(categories, list)
        assert "All" in categories
        assert "Menswear" in categories
        assert "Womenswear" in categories
        assert "Vintage" in categories

    def test_get_category_slug(self):
        """Test getting category slugs."""
        assert DataParser.get_category_slug("All") == ""
        assert DataParser.get_category_slug("Menswear") == "mens"
        assert DataParser.get_category_slug("Womenswear") == "womens"
        assert DataParser.get_category_slug("Unknown") == ""

    def test_parse_price_valid(self):
        """Test parsing valid price strings."""
        assert DataParser._parse_price("$50.00") == 50.0
        assert DataParser._parse_price("50.00") == 50.0
        assert DataParser._parse_price("$100") == 100.0
        assert DataParser._parse_price("€25.50") == 25.5

    def test_parse_price_invalid(self):
        """Test parsing invalid price strings."""
        assert DataParser._parse_price("") == 0.0
        assert DataParser._parse_price("free") == 0.0
        assert DataParser._parse_price("abc") == 0.0

    def test_parse_date_iso_format(self):
        """Test parsing ISO format dates."""
        result = DataParser._parse_date("2024-01-15T10:30:00.000Z")
        assert result is not None
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_parse_date_simple_format(self):
        """Test parsing simple date format."""
        result = DataParser._parse_date("2024-01-15")
        assert result is not None
        assert result.year == 2024

    def test_parse_date_none(self):
        """Test parsing None/empty dates."""
        assert DataParser._parse_date(None) is None
        assert DataParser._parse_date("") is None

    def test_parse_date_invalid(self):
        """Test parsing invalid date strings."""
        assert DataParser._parse_date("not a date") is None
        assert DataParser._parse_date("2024/01/15") is None

    def test_parse_api_product_basic(self):
        """Test parsing basic API product data."""
        data = {
            "id": "product-123",
            "description": "Vintage Denim Jacket",
            "price": {
                "priceAmount": 75.0,
                "currencyName": "USD",
            },
            "seller": {
                "username": "seller123",
                "rating": 4.8,
                "reviewCount": 25,
            },
            "status": "available",
        }

        item = DataParser.parse_api_product(data)

        assert item is not None
        assert item.id == "product-123"
        assert item.title == "Vintage Denim Jacket"
        assert item.price == 75.0
        assert item.seller == "seller123"
        assert item.seller_rating == 4.8
        assert item.is_sold is False

    def test_parse_api_product_sold(self):
        """Test parsing sold API product."""
        data = {
            "id": "product-456",
            "description": "Sold Item",
            "price": {"priceAmount": 50.0},
            "seller": {"username": "seller"},
            "status": "sold",
            "soldAt": "2024-01-15T10:00:00Z",
        }

        item = DataParser.parse_api_product(data)

        assert item is not None
        assert item.is_sold is True
        assert item.sale_date is not None

    def test_parse_api_product_with_discount(self):
        """Test parsing product with original price."""
        data = {
            "id": "product-789",
            "description": "Discounted Item",
            "price": {"priceAmount": 40.0},
            "originalPrice": {"priceAmount": 60.0},
            "seller": {"username": "seller"},
        }

        item = DataParser.parse_api_product(data)

        assert item is not None
        assert item.price == 40.0
        assert item.original_price == 60.0

    def test_parse_api_product_invalid(self):
        """Test parsing invalid product data."""
        # Empty dict - returns item with empty/default values
        result = DataParser.parse_api_product({})
        # The parser is tolerant and returns an item with defaults
        assert result is not None
        assert result.id == ""
        assert result.price == 0.0

        # Missing required fields shouldn't crash
        result = DataParser.parse_api_product({"random": "data"})
        # Returns item with defaults
        assert result is not None

    def test_parse_api_product_with_pictures(self):
        """Test parsing product with pictures."""
        data = {
            "id": "product-123",
            "description": "Item with Pictures",
            "price": {"priceAmount": 50.0},
            "seller": {"username": "seller"},
            "pictures": [
                {"url": "https://example.com/image1.jpg"},
                {"url": "https://example.com/image2.jpg"},
            ],
        }

        item = DataParser.parse_api_product(data)

        assert item is not None
        assert item.image_url == "https://example.com/image1.jpg"

    def test_parse_api_product_days_on_market(self):
        """Test calculating days on market."""
        data = {
            "id": "product-123",
            "description": "Test Item",
            "price": {"priceAmount": 50.0},
            "seller": {"username": "seller"},
            "listedAt": "2024-01-01T00:00:00Z",
            "soldAt": "2024-01-11T00:00:00Z",
        }

        item = DataParser.parse_api_product(data)

        assert item is not None
        assert item.days_on_market == 10
