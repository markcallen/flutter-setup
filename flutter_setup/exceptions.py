"""Custom exceptions for Flutter Setup."""


class FlutterSetupError(Exception):
    """Base exception for Flutter setup errors."""

    pass


class PrerequisitesError(FlutterSetupError):
    """Raised when prerequisites are not met."""

    pass


class FlutterInstallationError(FlutterSetupError):
    """Raised when Flutter installation fails."""

    pass


class ProjectCreationError(FlutterSetupError):
    """Raised when project creation fails."""

    pass


class ConfigurationError(FlutterSetupError):
    """Raised when configuration is invalid."""

    pass


class SystemError(FlutterSetupError):
    """Raised when system-level operations fail."""

    pass
