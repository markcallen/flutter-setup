"""Tests for the bootstrap module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

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
                        with patch.object(bootstrap, "_create_cicd"):
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

    def test_create_cicd(self, config: Config) -> None:
        """Test creating CI/CD workflows and configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_cicd()
            workflows_dir = config.project_path / ".github" / "workflows"
            assert workflows_dir.exists()
            # Check that at least one workflow file exists
            workflow_files = list(workflows_dir.glob("*.yml"))
            assert len(workflow_files) > 0

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

    def test_add_integration_test_sdk_dependency_no_pubspec(
        self, bootstrap: ProjectBootstrap, config: Config
    ) -> None:
        """Test adding integration_test when pubspec.yaml doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap._add_integration_test_sdk_dependency()  # Should not raise

    def test_add_integration_test_sdk_dependency_no_dev_deps(
        self, bootstrap: ProjectBootstrap, config: Config
    ) -> None:
        """Test adding integration_test when dev_dependencies section doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec_path.write_text("name: test_app\nversion: 1.0.0\n")
            bootstrap._add_integration_test_sdk_dependency()
            content = yaml.safe_load(pubspec_path.read_text())
            assert "dev_dependencies" in content
            assert content["dev_dependencies"]["integration_test"] == {"sdk": "flutter"}

    def test_add_integration_test_sdk_dependency_already_exists_correct(
        self, bootstrap: ProjectBootstrap, config: Config
    ) -> None:
        """Test adding integration_test when it already exists correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec = {
                "name": "test_app",
                "version": "1.0.0",
                "dev_dependencies": {"integration_test": {"sdk": "flutter"}},
            }
            pubspec_path.write_text(yaml.dump(pubspec))
            bootstrap._add_integration_test_sdk_dependency()
            # Should remain unchanged
            content = yaml.safe_load(pubspec_path.read_text())
            assert content["dev_dependencies"]["integration_test"] == {"sdk": "flutter"}

    def test_add_integration_test_sdk_dependency_exists_incorrect(
        self, bootstrap: ProjectBootstrap, config: Config
    ) -> None:
        """Test adding integration_test when it exists but incorrectly configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec = {
                "name": "test_app",
                "version": "1.0.0",
                "dev_dependencies": {"integration_test": "1.0.0"},
            }
            pubspec_path.write_text(yaml.dump(pubspec))
            bootstrap._add_integration_test_sdk_dependency()
            content = yaml.safe_load(pubspec_path.read_text())
            assert content["dev_dependencies"]["integration_test"] == {"sdk": "flutter"}

    def test_add_integration_test_sdk_dependency_yaml_error(
        self, bootstrap: ProjectBootstrap, config: Config
    ) -> None:
        """Test adding integration_test when YAML parsing fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec_path.write_text("invalid: yaml: content: [")
            bootstrap._add_integration_test_sdk_dependency()  # Should not raise, just warn

    def test_modify_main_dart_no_imports(self, config: Config) -> None:
        """Test modifying main.dart when it has no imports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "lib").mkdir(parents=True)
            main_dart = config.project_path / "lib" / "main.dart"
            main_dart.write_text("void main() {\n  print('test');\n}")
            bootstrap._modify_main_dart()
            content = main_dart.read_text()
            assert "flutter_dotenv" in content
            assert "Future<void> main() async" in content

    def test_modify_main_dart_already_has_dotenv(self, config: Config) -> None:
        """Test modifying main.dart when flutter_dotenv import already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "lib").mkdir(parents=True)
            main_dart = config.project_path / "lib" / "main.dart"
            original_content = (
                "import 'package:flutter_dotenv/flutter_dotenv.dart';\nvoid main() {"
            )
            main_dart.write_text(original_content)
            bootstrap._modify_main_dart()
            content = main_dart.read_text()
            # Should not modify when flutter_dotenv already exists
            assert content == original_content

    def test_modify_main_dart_already_async(self, config: Config) -> None:
        """Test modifying main.dart when main() is already async."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "lib").mkdir(parents=True)
            main_dart = config.project_path / "lib" / "main.dart"
            main_dart.write_text(
                "import 'package:flutter/material.dart';\nFuture<void> main() async {"
            )
            bootstrap._modify_main_dart()
            content = main_dart.read_text()
            # Should add import but not modify async main() since it looks for "void main() {"
            assert "flutter_dotenv" in content
            # The replacement only works for "void main() {" so async main won't be changed
            assert "Future<void> main() async {" in content

    def test_modify_main_dart_write_error(self, config: Config) -> None:
        """Test modifying main.dart when file write fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "lib").mkdir(parents=True)
            main_dart = config.project_path / "lib" / "main.dart"
            main_dart.write_text(
                "import 'package:flutter/material.dart';\nvoid main() {"
            )
            with patch("builtins.open", side_effect=IOError("Permission denied")):
                bootstrap._modify_main_dart()  # Should not raise, just warn

    def test_create_vscode_config_content(self, config: Config) -> None:
        """Test VS Code configuration file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_vscode_config()
            settings_file = config.project_path / ".vscode" / "settings.json"
            launch_file = config.project_path / ".vscode" / "launch.json"
            settings = json.loads(settings_file.read_text())
            launch = json.loads(launch_file.read_text())
            assert settings["dart.flutterHotReloadOnSave"] == "all"
            assert settings["editor.formatOnSave"] is True
            assert launch["configurations"][0]["name"] == "Flutter Debug"

    def test_create_makefile_content(self, config: Config) -> None:
        """Test Makefile content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_makefile()
            makefile = config.project_path / "Makefile"
            content = makefile.read_text()
            assert "run:" in content
            assert "run_ios:" in content
            assert "run_android:" in content
            assert "analyze:" in content
            assert "test:" in content
            assert "integration:" in content

    def test_create_sample_tests_content(self, config: Config) -> None:
        """Test sample test files content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "test" / "unit").mkdir(parents=True)
            (config.project_path / "test" / "widget").mkdir(parents=True)
            (config.project_path / "integration_test").mkdir(parents=True)
            bootstrap._create_sample_tests()
            unit_test = (
                config.project_path / "test" / "unit" / "sanity_test.dart"
            ).read_text()
            widget_test = (
                config.project_path / "test" / "widget" / "app_widget_test.dart"
            ).read_text()
            integration_test = (
                config.project_path / "integration_test" / "app_test.dart"
            ).read_text()
            assert "flutter_test" in unit_test
            assert "sanity check" in unit_test
            assert config.package_name in widget_test
            assert config.package_name in integration_test
            assert "IntegrationTestWidgetsFlutterBinding" in integration_test

    def test_create_environment_support_env_content(self, config: Config) -> None:
        """Test .env file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            with patch.object(bootstrap, "_modify_main_dart"):
                bootstrap._create_environment_support()
                env_file = config.project_path / ".env"
                content = env_file.read_text()
                assert "API_URL" in content
                assert "https://api.example.com" in content

    def test_create_readme_content(self, config: Config) -> None:
        """Test README file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_readme()
            readme = config.project_path / "README.md"
            content = readme.read_text()
            assert config.project_name in content
            assert "flutter pub get" in content
            assert "make run" in content
            assert "make test" in content
            assert "make integration" in content
            assert "make analyze" in content
            assert ".env" in content
