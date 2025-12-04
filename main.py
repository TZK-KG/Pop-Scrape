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


def is_tk_tcl_error(error_message: str) -> bool:
    """
    Check if an ImportError is related to missing Tk/Tcl system libraries.

    Args:
        error_message: The error message from the ImportError.

    Returns:
        True if the error is related to Tk/Tcl, False otherwise.
    """
    tk_indicators = ["libtk", "libtcl", "_tkinter"]
    error_lower = error_message.lower()
    return any(indicator.lower() in error_lower for indicator in tk_indicators)


def get_tk_installation_instructions() -> str:
    """
    Get platform-specific installation instructions for Tk/Tcl libraries.

    Returns:
        A formatted string with installation instructions for various platforms.
    """
    return """The Tk/Tcl libraries are required for the GUI but are not installed.
This is a system-level dependency that cannot be installed via pip.

Please install using your system's package manager:

  Arch Linux / Manjaro:
    sudo pacman -S tk

  Debian / Ubuntu / Pop!_OS:
    sudo apt-get install python3-tk

  Fedora / RHEL / CentOS:
    sudo dnf install python3-tkinter

  openSUSE:
    sudo zypper install python3-tk

  macOS (with Homebrew):
    brew install python-tk"""


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
        error_message = str(e)
        if is_tk_tcl_error(error_message):
            print(f"Error: Missing system dependency: {error_message}")
            print()
            print(get_tk_installation_instructions())
        else:
            print(f"Error: Missing required dependency: {error_message}")
            print("\nPlease install dependencies with:")
            print("  pip install -r requirements.txt")
        return 1

    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
