#!/usr/bin/env python3
"""
Pop-Scrape - Depop Web Scraper & Profit Calculator

A Python-based Depop web scraper application with an interactive GUI
that helps users find high-value products with quick sale margins and
low quantity, then calculates profit based on entered retail price,
shipping, and tax information.

Usage:
    python main.py
"""

import sys


def main() -> int:
    """
    Main entry point for the Pop-Scrape application.

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    try:
        from src.gui.app import PopScrapeApp

        app = PopScrapeApp()
        app.run()
        return 0

    except ImportError as e:
        print(f"Error: Missing required dependency: {e}")
        print("\nPlease install dependencies with:")
        print("  pip install -r requirements.txt")
        return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
