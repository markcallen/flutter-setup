"""Tests for the project_creator module."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from flutter_setup.config import Config
from flutter_setup.exceptions import ProjectCreationError
from flutter_setup.project_creator import ProjectCreator


class TestProjectCreator:
    """Test cases for ProjectCreator class."""

    @pytest.fixture
    def config(self) -> Config:
        """Create a test configuration."""
        return Config(
            project_name="TestApp",
            platforms=["ios", "android"],
            org="com.test",
            channel="stable",
            output_dir=Path("/tmp"),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=False,
            verbose=False,
            flutter_location=Path("/flutter"),
        )

    @pytest.fixture
    def creator(self, config: Config) -> ProjectCreator:
        """Create a ProjectCreator instance."""
        return ProjectCreator(config)

    def test_init(self, creator: ProjectCreator, config: Config) -> None:
        """Test ProjectCreator initialization."""
        assert creator.config == config
        assert creator.flutter_root == config.flutter_location

    def test_create_project_dry_run(self, config: Config) -> None:
        """Test create_project in dry run mode."""
        config.dry_run = True
        creator = ProjectCreator(config)
        creator.create_project()  # Should not raise

    def test_create_project_already_exists(
        self, creator: ProjectCreator, config: Config
    ) -> None:
        """Test create_project skips when pubspec.yaml already exists."""
        mock_output_dir = MagicMock()
        mock_project_path = MagicMock()
        mock_project_path.__truediv__.return_value.exists.return_value = True
        mock_output_dir.__truediv__.return_value = mock_project_path
        creator.config.output_dir = mock_output_dir
        creator.create_project()  # Should not raise

    def test_create_project_success(
        self, creator: ProjectCreator, config: Config
    ) -> None:
        """Test successful project creation when pubspec.yaml is absent."""
        mock_output_dir = MagicMock()
        mock_project_path = MagicMock()
        mock_project_path.__truediv__.return_value.exists.return_value = False
        mock_output_dir.__truediv__.return_value = mock_project_path
        creator.config.output_dir = mock_output_dir
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            creator.create_project()
            mock_run.assert_called_once()

    def test_create_project_failure(
        self, creator: ProjectCreator, config: Config
    ) -> None:
        """Test project creation failure."""
        mock_output_dir = MagicMock()
        mock_project_path = MagicMock()
        mock_project_path.__truediv__.return_value.exists.return_value = False
        mock_output_dir.__truediv__.return_value = mock_project_path
        creator.config.output_dir = mock_output_dir
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "flutter")
            with pytest.raises(ProjectCreationError):
                creator.create_project()

    def test_build_create_command_app(self, creator: ProjectCreator) -> None:
        """Test building create command for app template."""
        cmd = creator._build_create_command()
        assert "create" in cmd
        assert "--org" in cmd
        assert "--template" in cmd
        assert "app" in cmd
        assert str(creator.config.project_path) in cmd

    def test_build_create_command_plugin(self, config: Config) -> None:
        """Test building create command for plugin template."""
        config.template = "plugin"
        creator = ProjectCreator(config)
        cmd = creator._build_create_command()
        assert "--ios-language" in cmd
        assert "--android-language" in cmd
        assert "swift" in cmd
        assert "kotlin" in cmd

    def test_build_create_command_platforms(self, creator: ProjectCreator) -> None:
        """Test building create command includes platforms."""
        cmd = creator._build_create_command()
        assert "--platforms" in cmd
        assert "ios,android" in cmd
