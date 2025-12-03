"""Tests for the prerequisites module."""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from flutter_setup.config import Config
from flutter_setup.exceptions import PrerequisitesError
from flutter_setup.prerequisites import PrerequisitesManager


class TestPrerequisitesManager:
    """Test cases for PrerequisitesManager class."""

    @pytest.fixture
    def config(self) -> Config:
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

    @pytest.fixture
    def manager(self, config: Config) -> PrerequisitesManager:
        """Create a PrerequisitesManager instance."""
        return PrerequisitesManager(config)

    def test_init(self, manager: PrerequisitesManager, config: Config) -> None:
        """Test PrerequisitesManager initialization."""
        assert manager.config == config
        assert manager.home == Path.home()

    def test_check_and_install_dry_run(self, config: Config) -> None:
        """Test check_and_install in dry run mode."""
        config.dry_run = True
        manager = PrerequisitesManager(config)
        manager.check_and_install()  # Should not raise

    def test_check_xcode_tools_found(self, manager: PrerequisitesManager) -> None:
        """Test checking Xcode tools when found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            manager._check_xcode_tools()  # Should not raise

    def test_check_xcode_tools_not_found(self, manager: PrerequisitesManager) -> None:
        """Test checking Xcode tools when not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=1)
            mock_run.side_effect = [
                Mock(returncode=1),  # xcode-select -p
                Mock(returncode=0),  # xcode-select --install
            ]
            with pytest.raises(PrerequisitesError):
                manager._check_xcode_tools()

    def test_check_homebrew_found(self, manager: PrerequisitesManager) -> None:
        """Test checking Homebrew when found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            with patch.object(manager, "_ensure_homebrew_path"):
                manager._check_homebrew()  # Should not raise

    def test_check_homebrew_not_found(self, manager: PrerequisitesManager) -> None:
        """Test checking Homebrew when not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1),  # brew --version
                Mock(returncode=0),  # install script
            ]
            with patch.object(manager, "_install_homebrew") as mock_install:
                manager._check_homebrew()
                mock_install.assert_called_once()

    def test_install_homebrew(self, manager: PrerequisitesManager) -> None:
        """Test installing Homebrew."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            with patch.object(manager, "_ensure_homebrew_path"):
                manager._install_homebrew()  # Should not raise

    def test_install_homebrew_failure(self, manager: PrerequisitesManager) -> None:
        """Test Homebrew installation failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "bash")
            with pytest.raises(PrerequisitesError):
                manager._install_homebrew()

    def test_ensure_homebrew_path(self, manager: PrerequisitesManager) -> None:
        """Test ensuring Homebrew is in PATH."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("subprocess.run") as mock_run:
                mock_run.return_value = Mock(returncode=0)
                manager._ensure_homebrew_path()  # Should not raise

    def test_install_packages(self, manager: PrerequisitesManager) -> None:
        """Test installing required packages."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            manager._install_packages()  # Should not raise

    def test_install_packages_already_installed(
        self, manager: PrerequisitesManager
    ) -> None:
        """Test installing packages when already installed."""
        with patch("subprocess.run") as mock_run:
            # First call (install) fails, second call (list) succeeds
            call_count = 0

            def side_effect(*args: Any, **kwargs: Any) -> Mock:
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise subprocess.CalledProcessError(1, "brew")
                return Mock(returncode=0)

            mock_run.side_effect = side_effect
            manager._install_packages()  # Should not raise

    def test_setup_platform_tools_android(self, config: Config) -> None:
        """Test setting up Android tools."""
        config.platforms = ["android"]
        manager = PrerequisitesManager(config)
        with patch.object(manager, "_setup_android_tools") as mock_setup:
            manager._setup_platform_tools()
            mock_setup.assert_called_once()

    def test_setup_platform_tools_ios(self, config: Config) -> None:
        """Test setting up iOS tools."""
        config.platforms = ["ios"]
        manager = PrerequisitesManager(config)
        with patch.object(manager, "_setup_ios_tools") as mock_setup:
            manager._setup_platform_tools()
            mock_setup.assert_called_once()

    def test_setup_android_tools(self, manager: PrerequisitesManager) -> None:
        """Test setting up Android development tools."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            manager._setup_android_tools()  # Should not raise

    def test_setup_ios_tools(self, manager: PrerequisitesManager) -> None:
        """Test setting up iOS development tools."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            manager._setup_ios_tools()  # Should not raise

    def test_check_only_all_pass(self, manager: PrerequisitesManager) -> None:
        """Test check_only when all checks pass."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            result = manager.check_only()
            assert result is True

    def test_check_only_xcode_fails(self, manager: PrerequisitesManager) -> None:
        """Test check_only when Xcode check fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=1),  # xcode-select fails
                Mock(returncode=0),  # brew --version
                Mock(returncode=0),  # brew list git
                Mock(returncode=0),  # brew list cocoapods
            ]
            result = manager.check_only()
            assert result is False

    def test_check_only_homebrew_fails(self, manager: PrerequisitesManager) -> None:
        """Test check_only when Homebrew check fails."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0),  # xcode-select
                Mock(returncode=1),  # brew --version fails
            ]
            result = manager.check_only()
            assert result is False
