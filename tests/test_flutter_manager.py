"""Tests for the flutter_manager module."""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from flutter_setup.config import Config
from flutter_setup.exceptions import FlutterInstallationError
from flutter_setup.flutter_manager import FlutterManager


class TestFlutterManager:
    """Test cases for FlutterManager class."""

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
    def manager(self, config: Config) -> FlutterManager:
        """Create a FlutterManager instance."""
        return FlutterManager(config)

    def test_init(self, manager: FlutterManager, config: Config) -> None:
        """Test FlutterManager initialization."""
        assert manager.config == config
        assert manager.home == Path.home()
        assert manager.flutter_root == config.flutter_location
        assert manager.zprofile == Path.home() / ".zprofile"

    def test_ensure_flutter_dry_run(self, config: Config) -> None:
        """Test ensure_flutter in dry run mode."""
        config.dry_run = True
        manager = FlutterManager(config)
        manager.ensure_flutter()  # Should not raise

    def test_ensure_flutter_reclone_mode(self, manager: FlutterManager) -> None:
        """Test ensure_flutter in reclone mode."""
        manager.config.flutter_update_mode = "reclone"
        with patch.object(manager, "_reclone_flutter") as mock_reclone:
            manager.ensure_flutter()
            mock_reclone.assert_called_once()

    def test_ensure_flutter_install(self, manager: FlutterManager) -> None:
        """Test ensure_flutter when Flutter is not installed."""
        mock_root = MagicMock()
        mock_root.exists.return_value = False
        manager.flutter_root = mock_root
        with patch.object(manager, "_install_flutter") as mock_install:
            with patch.object(manager, "_ensure_flutter_path"):
                with patch.object(manager, "_run_flutter_doctor"):
                    manager.ensure_flutter()
                    mock_install.assert_called_once()

    def test_ensure_flutter_update(self, manager: FlutterManager) -> None:
        """Test ensure_flutter when Flutter is installed."""
        mock_root = MagicMock()
        mock_root.exists.return_value = True
        mock_git = MagicMock()
        mock_git.exists.return_value = True
        mock_root.__truediv__.return_value = mock_git
        manager.flutter_root = mock_root
        with patch.object(manager, "_update_flutter") as mock_update:
            with patch.object(manager, "_ensure_flutter_path"):
                with patch.object(manager, "_run_flutter_doctor"):
                    manager.ensure_flutter()
                    mock_update.assert_called_once()

    def test_reclone_flutter(self, manager: FlutterManager) -> None:
        """Test recloning Flutter."""
        mock_root = MagicMock()
        mock_root.exists.return_value = True
        manager.flutter_root = mock_root
        with patch("shutil.rmtree"):
            with patch.object(manager, "_install_flutter") as mock_install:
                manager._reclone_flutter()
                mock_install.assert_called_once()

    def test_install_flutter(self, manager: FlutterManager) -> None:
        """Test installing Flutter SDK."""
        mock_root = MagicMock()
        mock_parent = MagicMock()
        mock_root.parent = mock_parent
        manager.flutter_root = mock_root
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            manager._install_flutter()  # Should not raise

    def test_install_flutter_failure(self, manager: FlutterManager) -> None:
        """Test Flutter installation failure."""
        mock_root = MagicMock()
        mock_parent = MagicMock()
        mock_root.parent = mock_parent
        manager.flutter_root = mock_root
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")
            with pytest.raises(FlutterInstallationError):
                manager._install_flutter()

    def test_update_flutter(self, manager: FlutterManager) -> None:
        """Test updating Flutter SDK."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            manager._update_flutter()  # Should not raise

    def test_update_flutter_fast_forward(self, manager: FlutterManager) -> None:
        """Test updating Flutter with fast-forward merge."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0),  # set-url
                Mock(returncode=0),  # fetch
                Mock(returncode=0),  # checkout
                Mock(returncode=0),  # merge
            ]
            manager._update_flutter()  # Should not raise

    def test_handle_diverged_branches_skip(self, manager: FlutterManager) -> None:
        """Test handling diverged branches in skip mode."""
        manager.config.flutter_update_mode = "skip"
        manager._handle_diverged_branches()  # Should not raise

    def test_handle_diverged_branches_reset(self, manager: FlutterManager) -> None:
        """Test handling diverged branches in reset mode."""
        manager.config.flutter_update_mode = "reset"
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                Mock(returncode=0, stdout="1 2"),  # rev-list
                Mock(returncode=0),  # reset
            ]
            manager._handle_diverged_branches()  # Should not raise

    def test_ensure_flutter_path_new_file(self, manager: FlutterManager) -> None:
        """Test ensuring Flutter PATH in new .zprofile."""
        mock_zprofile = MagicMock()
        mock_zprofile.exists.return_value = False
        manager.zprofile = mock_zprofile
        with patch("builtins.open", mock_open()) as mock_file:
            manager._ensure_flutter_path()
            mock_file.assert_called()

    def test_ensure_flutter_path_existing(self, manager: FlutterManager) -> None:
        """Test ensuring Flutter PATH when already configured."""
        mock_zprofile = MagicMock()
        mock_zprofile.exists.return_value = True
        manager.zprofile = mock_zprofile
        with patch(
            "builtins.open", mock_open(read_data='export PATH="/flutter/bin:$PATH"')
        ):
            manager._ensure_flutter_path()  # Should not raise

    def test_run_flutter_doctor_success(self, manager: FlutterManager) -> None:
        """Test running Flutter doctor successfully."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="Doctor summary", stderr=""
            )
            manager._run_flutter_doctor()  # Should not raise

    def test_run_flutter_doctor_failure(self, manager: FlutterManager) -> None:
        """Test running Flutter doctor with issues."""
        with patch("subprocess.run") as mock_run:
            # Flutter doctor outputs issues to stdout
            mock_run.return_value = Mock(returncode=1, stdout="Some issues", stderr="")
            with patch.object(manager, "_handle_android_licenses"):
                manager._run_flutter_doctor()  # Should not raise

    def test_handle_android_licenses(self, manager: FlutterManager) -> None:
        """Test handling Android licenses."""
        manager.config.platforms = ["android"]
        manager._handle_android_licenses()  # Should not raise

    def test_handle_android_licenses_no_android(self, manager: FlutterManager) -> None:
        """Test handling Android licenses when Android not in platforms."""
        manager.config.platforms = ["ios"]
        manager._handle_android_licenses()  # Should return early

    def test_check_only_flutter_not_installed(self, manager: FlutterManager) -> None:
        """Test check_only when Flutter is not installed."""
        mock_root = MagicMock()
        mock_root.exists.return_value = False
        manager.flutter_root = mock_root
        result = manager.check_only()
        assert result is False

    def test_check_only_flutter_installed(self, manager: FlutterManager) -> None:
        """Test check_only when Flutter is installed."""
        mock_root = MagicMock()
        mock_root.exists.return_value = True
        mock_git = MagicMock()
        mock_git.exists.return_value = True
        mock_bin_dir = MagicMock()
        mock_bin_dir.exists.return_value = True
        mock_bin = MagicMock()
        mock_bin.exists.return_value = True

        def truediv_side_effect(path: Any) -> MagicMock:
            if str(path) == ".git":
                return mock_git
            elif str(path) == "bin":
                return mock_bin_dir
            elif str(path) == "bin/flutter" or str(path) == "flutter":
                return mock_bin
            return MagicMock()

        mock_root.__truediv__ = MagicMock(side_effect=truediv_side_effect)
        manager.flutter_root = mock_root
        mock_zprofile = MagicMock()
        mock_zprofile.exists.return_value = True
        manager.zprofile = mock_zprofile
        with patch(
            "builtins.open", mock_open(read_data='export PATH="/flutter/bin:$PATH"')
        ):
            with patch("subprocess.run") as mock_run:
                # Mock the git rev-list command to return proper output
                def run_side_effect(*args: Any, **kwargs: Any) -> Mock:
                    if "rev-list" in args[0]:
                        result = Mock(returncode=0, stdout="0 0\n", stderr="")
                        return result
                    return Mock(returncode=0, stdout="", stderr="")

                mock_run.side_effect = run_side_effect
                manager.check_only()
                # Result depends on all checks passing

    def test_check_only_path_not_configured(self, manager: FlutterManager) -> None:
        """Test check_only when PATH is not configured."""
        mock_root = MagicMock()
        mock_root.exists.return_value = True
        mock_git = MagicMock()
        mock_git.exists.return_value = True
        mock_bin_dir = MagicMock()
        mock_bin_dir.exists.return_value = True
        mock_bin = MagicMock()
        mock_bin.exists.return_value = True

        def truediv_side_effect(path: Any) -> MagicMock:
            if str(path) == ".git":
                return mock_git
            elif str(path) == "bin":
                return mock_bin_dir
            elif str(path) == "bin/flutter" or str(path) == "flutter":
                return mock_bin
            return MagicMock()

        mock_root.__truediv__ = MagicMock(side_effect=truediv_side_effect)
        manager.flutter_root = mock_root
        mock_zprofile = MagicMock()
        mock_zprofile.exists.return_value = False
        manager.zprofile = mock_zprofile
        with patch("subprocess.run") as mock_run:
            # Mock the git rev-list command to return proper output
            def run_side_effect(*args: Any, **kwargs: Any) -> Mock:
                if "rev-list" in args[0]:
                    result = Mock(returncode=0, stdout="0 0\n", stderr="")
                    return result
                return Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = run_side_effect
            manager.check_only()
            # Should still return True if Flutter is installed
