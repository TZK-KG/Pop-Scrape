"""Tests for the main module error handling."""

import pytest

from main import is_tk_tcl_error, get_tk_installation_instructions


class TestIsTkTclError:
    """Test cases for is_tk_tcl_error function."""

    def test_libtk_error(self):
        """Test detection of libtk error."""
        error_msg = "libtk8.6.so: cannot open shared object file: No such file or directory"
        assert is_tk_tcl_error(error_msg)

    def test_libtcl_error(self):
        """Test detection of libtcl error."""
        error_msg = "libtcl8.6.so: cannot open shared object file: No such file or directory"
        assert is_tk_tcl_error(error_msg)

    def test_tkinter_error(self):
        """Test detection of _tkinter error."""
        error_msg = "No module named '_tkinter'"
        assert is_tk_tcl_error(error_msg)

    def test_case_insensitive_libtk(self):
        """Test case insensitive detection of libtk."""
        error_msg = "LIBTK8.6.so: cannot open shared object file"
        assert is_tk_tcl_error(error_msg)

    def test_case_insensitive_tkinter(self):
        """Test case insensitive detection of _tkinter."""
        error_msg = "No module named '_TKINTER'"
        assert is_tk_tcl_error(error_msg)

    def test_non_tk_error(self):
        """Test that non-Tk errors are not detected as Tk errors."""
        error_msg = "No module named 'customtkinter'"
        assert not is_tk_tcl_error(error_msg)

    def test_pip_package_error(self):
        """Test that pip package errors are not detected as Tk errors."""
        error_msg = "No module named 'pandas'"
        assert not is_tk_tcl_error(error_msg)

    def test_empty_error_message(self):
        """Test empty error message."""
        assert not is_tk_tcl_error("")


class TestGetTkInstallationInstructions:
    """Test cases for get_tk_installation_instructions function."""

    def test_returns_string(self):
        """Test that function returns a string."""
        result = get_tk_installation_instructions()
        assert isinstance(result, str)

    def test_contains_arch_instructions(self):
        """Test that Arch Linux instructions are included."""
        result = get_tk_installation_instructions()
        assert "Arch Linux" in result
        assert "sudo pacman -S tk" in result

    def test_contains_debian_instructions(self):
        """Test that Debian/Ubuntu instructions are included."""
        result = get_tk_installation_instructions()
        assert "Debian" in result
        assert "Ubuntu" in result
        assert "sudo apt-get install python3-tk" in result

    def test_contains_fedora_instructions(self):
        """Test that Fedora instructions are included."""
        result = get_tk_installation_instructions()
        assert "Fedora" in result
        assert "sudo dnf install python3-tkinter" in result

    def test_contains_opensuse_instructions(self):
        """Test that openSUSE instructions are included."""
        result = get_tk_installation_instructions()
        assert "openSUSE" in result
        assert "sudo zypper install python3-tk" in result

    def test_contains_macos_instructions(self):
        """Test that macOS instructions are included."""
        result = get_tk_installation_instructions()
        assert "macOS" in result
        assert "brew install python-tk" in result

    def test_contains_explanation(self):
        """Test that function includes explanation about system dependency."""
        result = get_tk_installation_instructions()
        assert "system-level dependency" in result
        assert "cannot be installed via pip" in result
