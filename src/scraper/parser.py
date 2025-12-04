"""Data extraction and parsing for Depop scraping."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass
class DepopItem:
    """Represents a scraped Depop item."""

    id: str
    title: str
    price: float
    original_price: Optional[float] = None
    currency: str = "USD"
    sale_date: Optional[datetime] = None
    listed_date: Optional[datetime] = None
    days_on_market: Optional[int] = None
    seller: str = ""
    seller_rating: Optional[float] = None
    seller_reviews: int = 0
    category: str = ""
    condition: str = ""
    size: str = ""
    brand: str = ""
    description: str = ""
    url: str = ""
    image_url: str = ""
    quantity_available: int = 1
    is_sold: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert item to dictionary for export."""
        return {
            "id": self.id,
            "title": self.title,
            "price": self.price,
            "original_price": self.original_price,
            "currency": self.currency,
            "sale_date": self.sale_date.isoformat() if self.sale_date else None,
            "listed_date": self.listed_date.isoformat() if self.listed_date else None,
            "days_on_market": self.days_on_market,
            "seller": self.seller,
            "seller_rating": self.seller_rating,
            "seller_reviews": self.seller_reviews,
            "category": self.category,
            "condition": self.condition,
            "size": self.size,
            "brand": self.brand,
            "description": self.description,
            "url": self.url,
            "image_url": self.image_url,
            "quantity_available": self.quantity_available,
            "is_sold": self.is_sold,
        }


class DataParser:
    """Parse and extract data from Depop API responses and HTML."""

    # Depop categories mapping
    CATEGORIES = {
        "All": "",
        "Menswear": "mens",
        "Womenswear": "womens",
        "Accessories": "accessories",
        "Jewelry": "jewelry",
        "Bags": "bags",
        "Shoes": "shoes",
        "Vintage": "vintage",
        "Streetwear": "streetwear",
        "Designer": "designer",
    }

    @staticmethod
    def parse_api_product(data: dict[str, Any]) -> Optional[DepopItem]:
        """
        Parse a product from Depop API response.

        Args:
            data: Raw product data from API.

        Returns:
            DepopItem or None if parsing fails.
        """
        try:
            # Extract price info
            price_info = data.get("price", {})
            price = float(price_info.get("priceAmount", 0))
            currency = price_info.get("currencyName", "USD")

            # Extract original price if discounted
            original_price = None
            if "originalPrice" in data:
                original_price = float(data["originalPrice"].get("priceAmount", 0))

            # Extract seller info
            seller_info = data.get("seller", {})
            seller_name = seller_info.get("username", "")
            seller_rating = seller_info.get("rating")
            seller_reviews = seller_info.get("reviewCount", 0)

            # Parse dates
            sale_date = None
            listed_date = None
            days_on_market = None

            if "soldAt" in data:
                sale_date = DataParser._parse_date(data["soldAt"])
            if "listedAt" in data or "dateUpdated" in data:
                listed_date = DataParser._parse_date(
                    data.get("listedAt") or data.get("dateUpdated")
                )
            if sale_date and listed_date:
                days_on_market = (sale_date - listed_date).days

            # Build item URL
            product_id = str(data.get("id", data.get("slug", "")))
            url = f"https://www.depop.com/products/{product_id}"

            # Get image URL
            pictures = data.get("pictures", data.get("preview", []))
            image_url = ""
            if pictures:
                if isinstance(pictures, list) and len(pictures) > 0:
                    first_pic = pictures[0]
                    if isinstance(first_pic, dict):
                        image_url = first_pic.get("url", first_pic.get("src", ""))
                    elif isinstance(first_pic, str):
                        image_url = first_pic

            return DepopItem(
                id=product_id,
                title=data.get("description", data.get("title", ""))[:100],
                price=price,
                original_price=original_price,
                currency=currency,
                sale_date=sale_date,
                listed_date=listed_date,
                days_on_market=days_on_market,
                seller=seller_name,
                seller_rating=float(seller_rating) if seller_rating else None,
                seller_reviews=int(seller_reviews) if seller_reviews else 0,
                category=data.get("category", {}).get("name", ""),
                condition=data.get("condition", ""),
                size=data.get("size", {}).get("name", ""),
                brand=data.get("brand", {}).get("name", ""),
                description=data.get("description", ""),
                url=url,
                image_url=image_url,
                quantity_available=data.get("quantity", 1),
                is_sold=data.get("status") == "sold" or "soldAt" in data,
            )
        except (KeyError, TypeError, ValueError) as e:
            print(f"Warning: Failed to parse product: {e}")
            return None

    @staticmethod
    def parse_html_product(element: Any) -> Optional[DepopItem]:
        """
        Parse a product from HTML element using selectolax.

        Args:
            element: HTML element from selectolax parser.

        Returns:
            DepopItem or None if parsing fails.
        """
        try:
            # Extract product link and ID
            link = element.css_first("a[href*='/products/']")
            if not link:
                return None

            href = link.attributes.get("href", "")
            product_id = href.split("/products/")[-1].split("/")[0].split("?")[0]

            # Extract title
            title_elem = element.css_first("[class*='title'], [class*='description']")
            title = title_elem.text() if title_elem else ""

            # Extract price
            price_elem = element.css_first("[class*='price']")
            price_text = price_elem.text() if price_elem else "0"
            price = DataParser._parse_price(price_text)

            # Extract image
            img_elem = element.css_first("img")
            image_url = ""
            if img_elem:
                image_url = img_elem.attributes.get(
                    "src", img_elem.attributes.get("data-src", "")
                )

            # Extract seller
            seller_elem = element.css_first("[class*='username'], [class*='seller']")
            seller = seller_elem.text() if seller_elem else ""

            # Check if sold
            sold_elem = element.css_first("[class*='sold']")
            is_sold = sold_elem is not None

            return DepopItem(
                id=product_id,
                title=title.strip()[:100],
                price=price,
                seller=seller.strip(),
                url=f"https://www.depop.com{href}" if not href.startswith("http") else href,
                image_url=image_url,
                is_sold=is_sold,
            )
        except Exception as e:
            print(f"Warning: Failed to parse HTML product: {e}")
            return None

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
        """Parse a date string to datetime object."""
        if not date_str:
            return None

        # Try different date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def _parse_price(price_str: str) -> float:
        """Parse a price string to float."""
        # Remove currency symbols and whitespace
        cleaned = "".join(c for c in price_str if c.isdigit() or c == ".")
        try:
            return float(cleaned) if cleaned else 0.0
        except ValueError:
            return 0.0

    @classmethod
    def get_category_slug(cls, category_name: str) -> str:
        """Get the URL slug for a category name."""
        return cls.CATEGORIES.get(category_name, "")

    @classmethod
    def get_category_names(cls) -> list[str]:
        """Get list of available category names."""
        return list(cls.CATEGORIES.keys())
