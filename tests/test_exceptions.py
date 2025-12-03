"""Tests for the exceptions module."""

import pytest

from flutter_setup.exceptions import (
    FlutterSetupError,
    PrerequisitesError,
    FlutterInstallationError,
    ProjectCreationError,
    ConfigurationError,
    SystemError,
)


class TestFlutterSetupError:
    """Test cases for FlutterSetupError."""

    def test_flutter_setup_error_can_be_raised(self) -> None:
        """Test that FlutterSetupError can be raised."""
        with pytest.raises(FlutterSetupError):
            raise FlutterSetupError("Test error")

    def test_flutter_setup_error_message(self) -> None:
        """Test that FlutterSetupError preserves message."""
        error = FlutterSetupError("Test error message")
        assert str(error) == "Test error message"


class TestPrerequisitesError:
    """Test cases for PrerequisitesError."""

    def test_prerequisites_error_can_be_raised(self) -> None:
        """Test that PrerequisitesError can be raised."""
        with pytest.raises(PrerequisitesError):
            raise PrerequisitesError("Prerequisites failed")

    def test_prerequisites_error_is_flutter_setup_error(self) -> None:
        """Test that PrerequisitesError is a FlutterSetupError."""
        error = PrerequisitesError("Test")
        assert isinstance(error, FlutterSetupError)


class TestFlutterInstallationError:
    """Test cases for FlutterInstallationError."""

    def test_flutter_installation_error_can_be_raised(self) -> None:
        """Test that FlutterInstallationError can be raised."""
        with pytest.raises(FlutterInstallationError):
            raise FlutterInstallationError("Installation failed")

    def test_flutter_installation_error_is_flutter_setup_error(self) -> None:
        """Test that FlutterInstallationError is a FlutterSetupError."""
        error = FlutterInstallationError("Test")
        assert isinstance(error, FlutterSetupError)


class TestProjectCreationError:
    """Test cases for ProjectCreationError."""

    def test_project_creation_error_can_be_raised(self) -> None:
        """Test that ProjectCreationError can be raised."""
        with pytest.raises(ProjectCreationError):
            raise ProjectCreationError("Project creation failed")

    def test_project_creation_error_is_flutter_setup_error(self) -> None:
        """Test that ProjectCreationError is a FlutterSetupError."""
        error = ProjectCreationError("Test")
        assert isinstance(error, FlutterSetupError)


class TestConfigurationError:
    """Test cases for ConfigurationError."""

    def test_configuration_error_can_be_raised(self) -> None:
        """Test that ConfigurationError can be raised."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Configuration failed")

    def test_configuration_error_is_flutter_setup_error(self) -> None:
        """Test that ConfigurationError is a FlutterSetupError."""
        error = ConfigurationError("Test")
        assert isinstance(error, FlutterSetupError)


class TestSystemError:
    """Test cases for SystemError."""

    def test_system_error_can_be_raised(self) -> None:
        """Test that SystemError can be raised."""
        with pytest.raises(SystemError):
            raise SystemError("System operation failed")

    def test_system_error_is_flutter_setup_error(self) -> None:
        """Test that SystemError is a FlutterSetupError."""
        error = SystemError("Test")
        assert isinstance(error, FlutterSetupError)
