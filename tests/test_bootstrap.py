"""Tests for the bootstrap module."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from flutter_setup.bootstrap import ProjectBootstrap
from flutter_setup.config import Config


class TestProjectBootstrap:
    """Test cases for ProjectBootstrap class."""

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
    def bootstrap(self, config: Config) -> ProjectBootstrap:
        """Create a ProjectBootstrap instance."""
        return ProjectBootstrap(config)

    def test_init(self, bootstrap: ProjectBootstrap, config: Config) -> None:
        """Test ProjectBootstrap initialization."""
        assert bootstrap.config == config
        assert bootstrap.home == Path.home()
        assert bootstrap.flutter_root == Path.home() / "development" / "flutter"

    def test_bootstrap_project_dry_run(self, config: Config) -> None:
        """Test bootstrap_project in dry run mode."""
        config.dry_run = True
        bootstrap = ProjectBootstrap(config)
        bootstrap.bootstrap_project()  # Should not raise

    def test_bootstrap_project(
        self, bootstrap: ProjectBootstrap, config: Config
    ) -> None:
        """Test bootstrap_project calls all setup methods."""
        with patch.object(bootstrap, "_create_vscode_config"):
            with patch.object(bootstrap, "_create_makefile"):
                with patch.object(bootstrap, "_create_test_structure"):
                    with patch.object(bootstrap, "_create_analysis_options"):
                        with patch.object(bootstrap, "_create_github_actions"):
                            with patch.object(bootstrap, "_add_dependencies"):
                                with patch.object(
                                    bootstrap, "_create_environment_support"
                                ):
                                    with patch.object(bootstrap, "_create_readme"):
                                        with patch.object(bootstrap, "_format_code"):
                                            bootstrap.bootstrap_project()

    def test_create_vscode_config(self, config: Config) -> None:
        """Test creating VS Code configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_vscode_config()
            vscode_dir = config.project_path / ".vscode"
            assert vscode_dir.exists()
            assert (vscode_dir / "settings.json").exists()
            assert (vscode_dir / "launch.json").exists()

    def test_create_makefile(self, config: Config) -> None:
        """Test creating Makefile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_makefile()
            makefile = config.project_path / "Makefile"
            assert makefile.exists()
            content = makefile.read_text()
            assert "run:" in content
            assert "analyze:" in content

    def test_create_test_structure(self, config: Config) -> None:
        """Test creating test directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_test_structure()
            assert (config.project_path / "test" / "unit").exists()
            assert (config.project_path / "test" / "widget").exists()
            assert (config.project_path / "integration_test").exists()

    def test_create_sample_tests(self, config: Config) -> None:
        """Test creating sample test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "test" / "unit").mkdir(parents=True)
            (config.project_path / "test" / "widget").mkdir(parents=True)
            (config.project_path / "integration_test").mkdir(parents=True)
            bootstrap._create_sample_tests()
            assert (config.project_path / "test" / "unit" / "sanity_test.dart").exists()
            assert (
                config.project_path / "test" / "widget" / "app_widget_test.dart"
            ).exists()
            assert (config.project_path / "integration_test" / "app_test.dart").exists()

    def test_create_analysis_options(self, config: Config) -> None:
        """Test creating analysis options file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_analysis_options()
            analysis_file = config.project_path / "analysis_options.yaml"
            assert analysis_file.exists()
            content = analysis_file.read_text()
            assert "flutter_lints" in content

    def test_create_github_actions(self, config: Config) -> None:
        """Test creating GitHub Actions workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_github_actions()
            workflow_file = (
                config.project_path / ".github" / "workflows" / "flutter-ci.yml"
            )
            assert workflow_file.exists()
            content = workflow_file.read_text()
            assert "Flutter CI" in content

    def test_add_dependencies(
        self, bootstrap: ProjectBootstrap, config: Config
    ) -> None:
        """Test adding dependencies."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            bootstrap._add_dependencies()  # Should not raise

    def test_add_dependencies_failure(
        self, bootstrap: ProjectBootstrap, config: Config
    ) -> None:
        """Test adding dependencies with failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Failed")
            bootstrap._add_dependencies()  # Should not raise, just warn

    def test_create_environment_support(self, config: Config) -> None:
        """Test creating environment support."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            with patch.object(bootstrap, "_modify_main_dart"):
                bootstrap._create_environment_support()
                env_file = config.project_path / ".env"
                assert env_file.exists()

    def test_modify_main_dart_exists(self, config: Config) -> None:
        """Test modifying main.dart when it exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "lib").mkdir(parents=True)
            main_dart = config.project_path / "lib" / "main.dart"
            main_dart.write_text(
                "import 'package:flutter/material.dart';\nvoid main() {"
            )
            bootstrap._modify_main_dart()
            content = main_dart.read_text()
            assert "flutter_dotenv" in content

    def test_modify_main_dart_not_exists(self, config: Config) -> None:
        """Test modifying main.dart when it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            bootstrap._modify_main_dart()  # Should not raise

    def test_create_readme(self, config: Config) -> None:
        """Test creating README file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_readme()
            readme = config.project_path / "README.md"
            assert readme.exists()
            content = readme.read_text()
            assert config.project_name in content

    def test_format_code(self, bootstrap: ProjectBootstrap, config: Config) -> None:
        """Test formatting code."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)
            bootstrap._format_code()  # Should not raise

    def test_format_code_failure(
        self, bootstrap: ProjectBootstrap, config: Config
    ) -> None:
        """Test formatting code with failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Failed")
            bootstrap._format_code()  # Should not raise, just warn
