"""Tests for the platform module."""

from unittest.mock import patch

from flutter_setup.platform import detect_runtime_platform


def test_detect_runtime_platform_darwin() -> None:
    """Test platform detection for macOS."""
    with patch("sys.platform", "darwin"):
        assert detect_runtime_platform() == "darwin"


def test_detect_runtime_platform_linux() -> None:
    """Test platform detection for Linux."""
    with patch("sys.platform", "linux"):
        assert detect_runtime_platform() == "linux"


def test_detect_runtime_platform_unsupported() -> None:
    """Test platform detection for unsupported OS."""
    with patch("sys.platform", "win32"):
        assert detect_runtime_platform() == "unsupported"
