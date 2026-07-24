"""Detection utilities for the append command."""

from pathlib import Path

import yaml

PLATFORM_DIRS = {
    "ios": "ios",
    "android": "android",
    "web": "web",
    "macos": "macos",
    "linux": "linux",
    "windows": "windows",
}


def detect_flutter_project(path: Path) -> bool:
    """Return True if path contains a Flutter project (pubspec.yaml with flutter key)."""
    pubspec = path / "pubspec.yaml"
    if not pubspec.exists():
        return False
    try:
        data = yaml.safe_load(pubspec.read_text())
        return isinstance(data, dict) and "flutter" in data
    except Exception:
        return False


def detect_platforms(path: Path) -> list[str]:
    """Detect enabled platforms from existing platform directories."""
    platforms = [p for p, d in PLATFORM_DIRS.items() if (path / d).is_dir()]
    return platforms if platforms else ["ios", "android", "web"]


def get_pubspec_name(path: Path) -> str | None:
    """Read name from pubspec.yaml, return None on failure."""
    pubspec = path / "pubspec.yaml"
    if not pubspec.exists():
        return None
    try:
        data = yaml.safe_load(pubspec.read_text())
        if isinstance(data, dict):
            return data.get("name")
    except Exception:
        pass
    return None
