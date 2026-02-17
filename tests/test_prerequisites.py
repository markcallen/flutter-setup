"""Tests for prerequisites managers."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from flutter_setup.config import Config
from flutter_setup.exceptions import PrerequisitesError
from flutter_setup.prerequisites import PrerequisitesManager
from flutter_setup.prerequisites_linux import LinuxPrerequisites
from flutter_setup.prerequisites_macos import MacOSPrerequisites


@pytest.fixture
def config() -> Config:
    """Create a test configuration."""
    return Config(
        project_name="TestApp",
        platforms=["ios", "android"],
        org="com.test",
        channel="stable",
        output_dir=Path("."),
        template="app",
        ios_language="swift",
        android_language="kotlin",
        flutter_update_mode="reset",
        dry_run=False,
        verbose=False,
        flutter_location=Path("/flutter"),
    )


class TestPrerequisitesFacade:
    """Test platform-aware prerequisites facade."""

    def test_selects_macos_backend(self, config: Config) -> None:
        with patch(
            "flutter_setup.prerequisites.detect_runtime_platform", return_value="darwin"
        ):
            manager = PrerequisitesManager(config)
            assert isinstance(manager.backend, MacOSPrerequisites)

    def test_selects_linux_backend(self, config: Config) -> None:
        with patch(
            "flutter_setup.prerequisites.detect_runtime_platform", return_value="linux"
        ):
            manager = PrerequisitesManager(config)
            assert isinstance(manager.backend, LinuxPrerequisites)

    def test_rejects_unsupported_platform(self, config: Config) -> None:
        with patch(
            "flutter_setup.prerequisites.detect_runtime_platform",
            return_value="unsupported",
        ):
            with pytest.raises(PrerequisitesError):
                PrerequisitesManager(config)


class TestLinuxPrerequisites:
    """Test Linux prerequisites logic."""

    def test_check_only_all_installed(self, config: Config) -> None:
        manager = LinuxPrerequisites(config)
        with patch.object(manager, "_is_package_installed", return_value=True):
            assert manager.check_only() is True

    def test_check_only_missing_packages(self, config: Config) -> None:
        manager = LinuxPrerequisites(config)
        with patch.object(manager, "_is_package_installed", return_value=False):
            assert manager.check_only() is False

    def test_check_and_install_dry_run(self, config: Config) -> None:
        config.dry_run = True
        manager = LinuxPrerequisites(config)
        manager.check_and_install()

    def test_check_and_install_installs_missing(self, config: Config) -> None:
        manager = LinuxPrerequisites(config)
        with patch.object(
            manager,
            "_missing_packages",
            return_value=["git", "curl"],
        ):
            with patch("subprocess.run") as mock_run:
                manager.check_and_install()
                assert mock_run.call_count == 2

    def test_check_and_install_raises_on_apt_failure(self, config: Config) -> None:
        manager = LinuxPrerequisites(config)
        with patch.object(manager, "_missing_packages", return_value=["git"]):
            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = subprocess.CalledProcessError(1, "apt-get")
                with pytest.raises(PrerequisitesError):
                    manager.check_and_install()

    def test_is_package_installed(self, config: Config) -> None:
        manager = LinuxPrerequisites(config)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            assert manager._is_package_installed("git") is True


class TestMacOSPrerequisites:
    """Test macOS prerequisites logic."""

    def test_check_only_all_pass(self, config: Config) -> None:
        manager = MacOSPrerequisites(config)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            assert manager.check_only() is True

    def test_check_xcode_tools_not_found(self, config: Config) -> None:
        manager = MacOSPrerequisites(config)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [Mock(returncode=1), Mock(returncode=0)]
            with pytest.raises(PrerequisitesError):
                manager._check_xcode_tools()
