# Pop-Scrape

A Python-based Depop web scraper application with an interactive GUI that helps users find high-value products with quick sale margins and low quantity, then calculates profit based on entered retail price, shipping, and tax information.

## Features

### 🔍 Scraping Module
- Search Depop **sold items** by keyword/category
- Extract item data: price, sale time, item details, seller info
- Implements rate limiting to avoid IP blocks
- Uses Depop's API endpoints where possible
- Playwright fallback for JS-rendered content

### 📊 Analysis Engine
- **Quick sale margin detection**: Calculate days on market before sale
- **Low quantity flagging**: Identify items with limited supply
- **Profit calculation** with comprehensive fee breakdown

### 💰 Fee Deductions (Auto-calculated)
All fees/taxes included in price calculation:
- **Depop fee**: 10% of sale price
- **Payment processing fee**: 2.9% + $0.30 (PayPal/Stripe standard)
- **Sales tax**: Configurable percentage (user input)
- **Shipping**: Manual input field (user enters their shipping cost)

### 🖥️ Interactive GUI (CustomTkinter)
- **Search Panel**: 
  - Search bar with keyword input
  - Category dropdown filter
  - Price range filters (min/max)
  
- **Results Table** with sorting capabilities:
  - Sort by price (ascending/descending)
  - Sort by profit margin
  - Sort by sale speed (days to sell)
  - Sort by quantity available
  - Clickable column headers to toggle sort
  
- **Profit Calculator Panel**:
  - Input field for retail/resale price
  - Input field for shipping cost (manual entry)
  - Input field for sales tax percentage
  - Auto-calculated fee deductions
  - Clear fee breakdown display
  
- **Export Options**: 
  - Export filtered results to CSV
  - Save/load search preferences

- **Theme Toggle**: Dark/Light mode support

## Installation

### Prerequisites
- Python 3.10 or higher
- pip (Python package installer)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/TZK-KG/Pop-Scrape.git
cd Pop-Scrape
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Install Playwright browsers for fallback scraping:
```bash
playwright install chromium
```

## Usage

Run the application:
```bash
python main.py
```

### Using the Application

1. **Search for Items**:
   - Enter a search keyword (e.g., "vintage denim jacket")
   - Select a category from the dropdown
   - Optionally set price range filters
   - Choose between "Sold Items" or "Available Items"
   - Click "Search" to fetch results

2. **View Results**:
   - Results appear in the sortable table
   - Click column headers to sort
   - Use the sort dropdown for additional options
   - Click on any row to select an item

3. **Calculate Profit**:
   - Enter your sale price in the calculator panel
   - Enter your shipping cost
   - Enter your local sales tax percentage
   - View the detailed fee breakdown
   - See your estimated net profit

4. **Export Data**:
   - Click "Export CSV" to save results
   - Choose a location and filename

## Project Structure

```
Pop-Scrape/
├── main.py                 # Application entry point
├── requirements.txt        # All dependencies
├── README.md              # Setup and usage instructions
├── src/
│   ├── __init__.py
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── depop_api.py    # API-based scraping
│   │   ├── browser.py      # Playwright fallback
│   │   └── parser.py       # Data extraction/parsing
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── calculator.py   # Profit/fee calculations
│   │   └── analyzer.py     # Sale speed, quantity analysis
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── app.py          # Main application window
│   │   ├── search_panel.py # Search interface
│   │   ├── results_table.py# Sortable results display
│   │   ├── calculator_panel.py # Profit calculator UI
│   │   └── fee_breakdown.py # Fee display component
│   └── utils/
│       ├── __init__.py
│       ├── config.py       # Configuration management
│       └── export.py       # CSV export functionality
└── tests/
    └── __init__.py
```

## Configuration

Configuration is automatically saved to `~/.popscrape/config.json` and includes:
- Theme preference (dark/light)
- Last search parameters
- Default tax and shipping values
- Rate limiting settings

## Dependencies

- `httpx` - Async HTTP client for API requests
- `playwright` - Browser automation fallback for JS-rendered content
- `customtkinter` - Modern GUI framework
- `pandas` - Data handling, sorting, filtering, CSV export
- `selectolax` - Fast HTML parsing
- `pillow` - Image handling for GUI

## Rate Limiting

The application implements rate limiting to avoid IP blocks:
- Default delay of 1 second between API requests
- Configurable via the configuration file

## License

This project is for educational purposes only. Use responsibly and in accordance with Depop's Terms of Service.

## Disclaimer

This tool is intended for market research and analysis purposes. Always ensure you comply with Depop's Terms of Service when using this application