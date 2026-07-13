"""Tests for the flutter_manager module."""

import subprocess
import tempfile
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
        assert len(manager.path_profiles) >= 1

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
        """Test ensuring Flutter PATH in new profile file."""
        mock_profile = MagicMock()
        mock_profile.exists.return_value = False
        mock_profile.name = ".bashrc"
        manager.path_profiles = [mock_profile]
        with patch("builtins.open", mock_open()) as mock_file:
            manager._ensure_flutter_path()
            mock_file.assert_called()

    def test_ensure_flutter_path_existing(self, manager: FlutterManager) -> None:
        """Test ensuring Flutter PATH when already configured."""
        mock_profile = MagicMock()
        mock_profile.exists.return_value = True
        mock_profile.name = ".bashrc"
        manager.path_profiles = [mock_profile]
        with patch(
            "builtins.open", mock_open(read_data='export PATH="/flutter/bin:$PATH"')
        ):
            manager._ensure_flutter_path()  # Should not raise

    def test_normalize_flutter_bin_path_home_forms(
        self, manager: FlutterManager
    ) -> None:
        """Test normalizing common shell home path forms."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager.home = Path(tmpdir)
            assert manager._normalize_flutter_bin_path("$HOME/flutter/bin") == str(
                Path(tmpdir) / "flutter" / "bin"
            )
            assert manager._normalize_flutter_bin_path("~/flutter/bin") == str(
                Path(tmpdir) / "flutter" / "bin"
            )

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
        with tempfile.TemporaryDirectory() as tmpdir:
            flutter_root = Path(tmpdir) / "flutter"
            (flutter_root / ".git").mkdir(parents=True)
            (flutter_root / "bin").mkdir(parents=True)
            (flutter_root / "bin" / "flutter").touch()
            manager.flutter_root = flutter_root

            mock_profile = MagicMock()
            mock_profile.exists.return_value = True
            mock_profile.name = ".bashrc"
            manager.path_profiles = [mock_profile]

            with patch(
                "builtins.open",
                mock_open(read_data=f'export PATH="{flutter_root}/bin:$PATH"'),
            ):
                with patch("subprocess.run") as mock_run:
                    # Mock the git rev-list command to return proper output
                    def run_side_effect(*args: Any, **kwargs: Any) -> Mock:
                        if "rev-list" in args[0]:
                            result = Mock(returncode=0, stdout="0 0\n", stderr="")
                            return result
                        return Mock(returncode=0, stdout="", stderr="")

                    mock_run.side_effect = run_side_effect
                    assert manager.check_only() is True

    def test_check_only_accepts_home_path_forms(self, manager: FlutterManager) -> None:
        """Test check_only accepts $HOME and tilde Flutter PATH entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            home = Path(tmpdir)
            flutter_root = home / "development" / "flutter"
            (flutter_root / ".git").mkdir(parents=True)
            (flutter_root / "bin").mkdir(parents=True)
            (flutter_root / "bin" / "flutter").touch()
            manager.home = home
            manager.flutter_root = flutter_root

            mock_profile = MagicMock()
            mock_profile.exists.return_value = True
            mock_profile.name = ".bashrc"
            manager.path_profiles = [mock_profile]

            with patch(
                "builtins.open",
                mock_open(
                    read_data='export PATH="$HOME/development/flutter/bin:$PATH"'
                ),
            ):
                with patch("subprocess.run") as mock_run:

                    def run_side_effect(*args: Any, **kwargs: Any) -> Mock:
                        if "rev-list" in args[0]:
                            return Mock(returncode=0, stdout="0 0\n", stderr="")
                        return Mock(returncode=0, stdout="", stderr="")

                    mock_run.side_effect = run_side_effect
                    assert manager.check_only() is True

    def test_check_only_path_not_configured(self, manager: FlutterManager) -> None:
        """Test check_only when PATH is not configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            flutter_root = Path(tmpdir) / "flutter"
            (flutter_root / ".git").mkdir(parents=True)
            (flutter_root / "bin").mkdir(parents=True)
            (flutter_root / "bin" / "flutter").touch()
            manager.flutter_root = flutter_root

            mock_profile = MagicMock()
            mock_profile.exists.return_value = False
            mock_profile.name = ".bashrc"
            manager.path_profiles = [mock_profile]

            with patch("subprocess.run") as mock_run:
                # Mock the git rev-list command to return proper output
                def run_side_effect(*args: Any, **kwargs: Any) -> Mock:
                    if "rev-list" in args[0]:
                        result = Mock(returncode=0, stdout="0 0\n", stderr="")
                        return result
                    return Mock(returncode=0, stdout="", stderr="")

                mock_run.side_effect = run_side_effect
                assert manager.check_only() is False

    # --- _get_current_flutter_version ---

    def test_get_current_flutter_version_from_stdout(
        self, manager: FlutterManager
    ) -> None:
        """Version is parsed from stdout."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="Flutter 3.24.0 • channel stable", stderr=""
            )
            assert manager._get_current_flutter_version() == "3.24.0"

    def test_get_current_flutter_version_from_stderr(
        self, manager: FlutterManager
    ) -> None:
        """Version falls back to stderr when stdout is empty."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="", stderr="Flutter 3.22.1 • channel stable"
            )
            assert manager._get_current_flutter_version() == "3.22.1"

    def test_get_current_flutter_version_not_found(
        self, manager: FlutterManager
    ) -> None:
        """Returns None when neither stdout nor stderr contains a version."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="")
            assert manager._get_current_flutter_version() is None

    def test_get_current_flutter_version_subprocess_error(
        self, manager: FlutterManager
    ) -> None:
        """Returns None when subprocess raises."""
        with patch("subprocess.run", side_effect=OSError("no flutter")):
            assert manager._get_current_flutter_version() is None

    # --- _check_flutter_version ---

    def test_check_flutter_version_no_constraint(self, manager: FlutterManager) -> None:
        """No flutter_version constraint → check is a no-op."""
        manager.config.flutter_version = None
        with patch.object(manager, "_get_current_flutter_version") as mock_get:
            manager._check_flutter_version()
            mock_get.assert_not_called()

    def test_check_flutter_version_exact_match_passes(
        self, manager: FlutterManager
    ) -> None:
        """Exact match satisfies >= constraint."""
        manager.config.flutter_version = "3.24.0"
        with patch.object(
            manager, "_get_current_flutter_version", return_value="3.24.0"
        ):
            manager._check_flutter_version()  # should not raise

    def test_check_flutter_version_newer_passes(self, manager: FlutterManager) -> None:
        """A newer installed version satisfies the >= constraint."""
        manager.config.flutter_version = "3.24.0"
        with patch.object(
            manager, "_get_current_flutter_version", return_value="3.25.1"
        ):
            manager._check_flutter_version()  # should not raise

    def test_check_flutter_version_older_fails(self, manager: FlutterManager) -> None:
        """An older installed version raises FlutterInstallationError."""
        manager.config.flutter_version = "3.24.0"
        with patch.object(
            manager, "_get_current_flutter_version", return_value="3.22.3"
        ):
            with pytest.raises(FlutterInstallationError, match="version too old"):
                manager._check_flutter_version()

    def test_check_flutter_version_undetectable_fails(
        self, manager: FlutterManager
    ) -> None:
        """Undetectable version raises FlutterInstallationError."""
        manager.config.flutter_version = "3.24.0"
        with patch.object(manager, "_get_current_flutter_version", return_value=None):
            with pytest.raises(FlutterInstallationError, match="Could not determine"):
                manager._check_flutter_version()

    # --- ensure_flutter skip mode ---

    def test_ensure_flutter_skip_mode_does_not_update(
        self, manager: FlutterManager
    ) -> None:
        """In skip mode with SDK present, _update_flutter is never called."""
        manager.config.flutter_update_mode = "skip"
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
                    mock_update.assert_not_called()

    def test_ensure_flutter_version_check_called_when_constraint_set(
        self, manager: FlutterManager
    ) -> None:
        """_check_flutter_version is called when flutter_version is set."""
        manager.config.flutter_update_mode = "skip"
        manager.config.flutter_version = "3.24.0"
        mock_root = MagicMock()
        mock_root.exists.return_value = True
        mock_git = MagicMock()
        mock_git.exists.return_value = True
        mock_root.__truediv__.return_value = mock_git
        manager.flutter_root = mock_root
        with patch.object(manager, "_check_flutter_version") as mock_check:
            with patch.object(manager, "_ensure_flutter_path"):
                with patch.object(manager, "_run_flutter_doctor"):
                    manager.ensure_flutter()
                    mock_check.assert_called_once()
