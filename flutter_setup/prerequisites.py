"""Platform-aware prerequisites facade for Flutter setup."""

from typing import Protocol

from .config import Config
from .exceptions import PrerequisitesError
from .platform import detect_runtime_platform
from .prerequisites_linux import LinuxPrerequisites
from .prerequisites_macos import MacOSPrerequisites


class _PrerequisitesBackend(Protocol):
    def check_and_install(self) -> None: ...
    def check_only(self) -> bool: ...


class PrerequisitesManager:
    """Manages system prerequisites via platform-specific backends."""

    def __init__(self, config: Config):
        """Initialize PrerequisitesManager."""
        self.config = config
        self.platform = detect_runtime_platform()
        self.backend = self._select_backend()

    def _select_backend(self) -> _PrerequisitesBackend:
        if self.platform == "darwin":
            return MacOSPrerequisites(self.config)
        if self.platform == "linux":
            return LinuxPrerequisites(self.config)
        raise PrerequisitesError(f"Unsupported host platform: {self.platform}")

    def check_and_install(self) -> None:
        """Check and install prerequisites for the active platform."""
        self.backend.check_and_install()

    def check_only(self) -> bool:
        """Check prerequisites for the active platform."""
        return self.backend.check_only()
