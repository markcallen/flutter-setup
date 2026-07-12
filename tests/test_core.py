"""Tests for the core module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from flutter_setup.config import Config
from flutter_setup.core import FlutterSetup
from flutter_setup.exceptions import (
    FlutterInstallationError,
    PrerequisitesError,
    ProjectCreationError,
)


class TestFlutterSetup:
    """Test cases for FlutterSetup class."""

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
    def setup(self, config: Config) -> FlutterSetup:
        """Create a FlutterSetup instance."""
        return FlutterSetup(config)

    def test_init(self, setup: FlutterSetup, config: Config) -> None:
        """Test FlutterSetup initialization."""
        assert setup.config == config
        assert setup.prerequisites is not None
        assert setup.flutter_manager is not None
        assert setup.project_creator is not None
        assert setup.bootstrap is not None

    def test_run_success(self, setup: FlutterSetup) -> None:
        """Test successful run of Flutter setup."""
        with patch.object(setup, "_run_prerequisites"):
            with patch.object(setup, "_run_flutter_installation"):
                with patch.object(setup, "_run_project_creation"):
                    with patch.object(setup, "_run_bootstrap"):
                        with patch.object(setup, "_show_next_steps"):
                            setup.run()  # Should not raise

    def test_run_prerequisites_error(self, setup: FlutterSetup) -> None:
        """Test run with prerequisites error."""
        with patch.object(setup, "_run_prerequisites") as mock_prereq:
            mock_prereq.side_effect = PrerequisitesError("Prerequisites failed")
            with pytest.raises(PrerequisitesError):
                setup.run()

    def test_run_flutter_installation_error(self, setup: FlutterSetup) -> None:
        """Test run with Flutter installation error."""
        with patch.object(setup, "_run_prerequisites"):
            with patch.object(setup, "_run_flutter_installation") as mock_flutter:
                mock_flutter.side_effect = FlutterInstallationError(
                    "Installation failed"
                )
                with pytest.raises(FlutterInstallationError):
                    setup.run()

    def test_run_project_creation_error(self, setup: FlutterSetup) -> None:
        """Test run with project creation error."""
        with patch.object(setup, "_run_prerequisites"):
            with patch.object(setup, "_run_flutter_installation"):
                with patch.object(setup, "_run_project_creation") as mock_project:
                    mock_project.side_effect = ProjectCreationError("Creation failed")
                    with pytest.raises(ProjectCreationError):
                        setup.run()

    def test_run_dry_run(self, config: Config) -> None:
        """Test run in dry run mode."""
        config.dry_run = True
        setup = FlutterSetup(config)
        with patch.object(setup, "_run_prerequisites"):
            with patch.object(setup, "_run_flutter_installation"):
                with patch.object(setup, "_run_project_creation"):
                    with patch.object(setup, "_run_bootstrap"):
                        with patch.object(setup, "_show_next_steps"):
                            setup.run()  # Should not raise

    def test_run_prerequisites(self, setup: FlutterSetup) -> None:
        """Test running prerequisites step."""
        with patch.object(setup.prerequisites, "check_and_install"):
            setup._run_prerequisites()  # Should not raise

    def test_run_prerequisites_internal_error(self, setup: FlutterSetup) -> None:
        """Test running prerequisites with error."""
        with patch.object(setup.prerequisites, "check_and_install") as mock_check:
            mock_check.side_effect = Exception("Failed")
            with pytest.raises(PrerequisitesError):
                setup._run_prerequisites()

    def test_run_flutter_installation(self, setup: FlutterSetup) -> None:
        """Test running Flutter installation step."""
        with patch.object(setup.flutter_manager, "ensure_flutter"):
            setup._run_flutter_installation()  # Should not raise

    def test_run_flutter_installation_internal_error(self, setup: FlutterSetup) -> None:
        """Test running Flutter installation with error."""
        with patch.object(setup.flutter_manager, "ensure_flutter") as mock_ensure:
            mock_ensure.side_effect = Exception("Failed")
            with pytest.raises(FlutterInstallationError):
                setup._run_flutter_installation()

    def test_run_project_creation(self, setup: FlutterSetup) -> None:
        """Test running project creation step."""
        with patch.object(setup.project_creator, "create_project"):
            setup._run_project_creation()  # Should not raise

    def test_run_project_creation_internal_error(self, setup: FlutterSetup) -> None:
        """Test running project creation with error."""
        with patch.object(setup.project_creator, "create_project") as mock_create:
            mock_create.side_effect = Exception("Failed")
            with pytest.raises(ProjectCreationError):
                setup._run_project_creation()

    def test_run_bootstrap(self, setup: FlutterSetup) -> None:
        """Test running bootstrap step."""
        with patch.object(setup.bootstrap, "bootstrap_project"):
            setup._run_bootstrap()  # Should not raise

    def test_run_bootstrap_error(self, setup: FlutterSetup) -> None:
        """Test running bootstrap with error."""
        with patch.object(setup.bootstrap, "bootstrap_project") as mock_bootstrap:
            mock_bootstrap.side_effect = Exception("Failed")
            with pytest.raises(Exception):
                setup._run_bootstrap()

    def test_show_next_steps(self, setup: FlutterSetup) -> None:
        """Test showing next steps."""
        setup._show_next_steps()  # Should not raise

    def test_show_next_steps_linux_profile(self, setup: FlutterSetup) -> None:
        """Test Linux-specific shell profile guidance."""
        setup.platform = "linux"
        with patch("flutter_setup.core.console.print") as mock_print:
            setup._show_next_steps()
            panel = mock_print.call_args_list[-1][0][0]
            assert "source ~/.bashrc" in str(panel.renderable)
            assert "source ~/.zshrc" in str(panel.renderable)

    def test_show_next_steps_macos_profile(self, setup: FlutterSetup) -> None:
        """Test macOS-specific shell profile guidance."""
        setup.platform = "darwin"
        with patch("flutter_setup.core.console.print") as mock_print:
            setup._show_next_steps()
            panel = mock_print.call_args_list[-1][0][0]
            assert "source ~/.zprofile" in str(panel.renderable)
            assert "source ~/.zshrc" in str(panel.renderable)
