"""Platform detection helpers."""

import sys
from typing import Literal

SetupPlatform = Literal["darwin", "linux", "unsupported"]


def detect_runtime_platform() -> SetupPlatform:
    """Return the normalized runtime platform for setup flows."""
    if sys.platform == "darwin":
        return "darwin"
    if sys.platform.startswith("linux"):
        return "linux"
    return "unsupported"
