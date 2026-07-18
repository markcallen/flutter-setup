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
        assert bootstrap.flutter_root == config.flutter_location

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
                with patch.object(bootstrap, "_patch_android_ndk_version"):
                    with patch.object(bootstrap, "_create_test_structure"):
                        with patch.object(bootstrap, "_create_analysis_options"):
                            with patch.object(bootstrap, "_create_cicd"):
                                with patch.object(bootstrap, "_add_dependencies"):
                                    with patch.object(
                                        bootstrap, "_create_environment_support"
                                    ):
                                        with patch.object(bootstrap, "_create_readme"):
                                            with patch.object(
                                                bootstrap, "_format_code"
                                            ):
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
            assert "run-chrome:" not in content
            assert "analyze:" in content

    def test_check_flutter_version_target_verifies_version(
        self, config: Config
    ) -> None:
        """Test that check-flutter-version target compares actual vs required version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.flutter_version = "3.32.0"
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_makefile()
            content = (config.project_path / "Makefile").read_text()
            # The target must run flutter --version and compare against the required version
            assert "--version" in content
            assert "FLUTTER_REQUIRED_VERSION" in content
            # python3 comparison must be present in the target body
            assert "python3" in content

    def test_patch_android_ndk_version(self, config: Config) -> None:
        """Test that build.gradle.kts is patched to pin the NDK version."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            gradle_dir = config.project_path / "android" / "app"
            gradle_dir.mkdir(parents=True, exist_ok=True)
            gradle_file = gradle_dir / "build.gradle.kts"
            gradle_file.write_text(
                "android {\n    ndkVersion = flutter.ndkVersion\n}\n"
            )
            bootstrap = ProjectBootstrap(config)
            bootstrap._patch_android_ndk_version()
            content = gradle_file.read_text()
            assert 'ndkVersion = "27.0.12077973"' in content
            assert "flutter.ndkVersion" not in content

    def test_patch_android_ndk_version_missing_file(self, config: Config) -> None:
        """Test that patching is a no-op when build.gradle.kts does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            bootstrap._patch_android_ndk_version()  # should not raise

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

    def test_create_test_structure_removes_default_widget_test(
        self, config: Config
    ) -> None:
        """Test that the stale flutter-create widget_test.dart is removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            stale = config.project_path / "test" / "widget_test.dart"
            stale.parent.mkdir(parents=True, exist_ok=True)
            stale.write_text("void main() {}")
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_test_structure()
            assert not stale.exists()

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

    def test_integration_test_initializes_dotenv(self, config: Config) -> None:
        """Test that the generated integration test calls dotenv.load() in setUpAll."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "test" / "unit").mkdir(parents=True)
            (config.project_path / "test" / "widget").mkdir(parents=True)
            (config.project_path / "integration_test").mkdir(parents=True)
            bootstrap._create_sample_tests()
            content = (
                config.project_path / "integration_test" / "app_test.dart"
            ).read_text()
            assert "flutter_dotenv" in content
            assert "setUpAll" in content
            assert "dotenv.load" in content

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
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec_path.write_text("flutter:\n  uses-material-design: true\n")
            bootstrap = ProjectBootstrap(config)
            with patch.object(bootstrap, "_modify_main_dart"):
                bootstrap._create_environment_support()
                assert (config.project_path / ".env").exists()
                assert (config.project_path / ".env.example").exists()
                gitignore = config.project_path / ".gitignore"
                assert gitignore.exists()
                assert ".env" in gitignore.read_text()
                pubspec = yaml.safe_load(pubspec_path.read_text())
                assert ".env" in pubspec["flutter"]["assets"]

    def test_create_environment_support_skips_existing_files(
        self, config: Config
    ) -> None:
        """Test that existing .env and .env.example are not overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec_path.write_text("flutter:\n  uses-material-design: true\n")
            (config.project_path / ".env").write_text("EXISTING=1\n")
            (config.project_path / ".env.example").write_text("EXISTING_EXAMPLE=1\n")
            bootstrap = ProjectBootstrap(config)
            with patch.object(bootstrap, "_modify_main_dart"):
                bootstrap._create_environment_support()
                assert (config.project_path / ".env").read_text() == "EXISTING=1\n"
                assert (
                    config.project_path / ".env.example"
                ).read_text() == "EXISTING_EXAMPLE=1\n"

    def test_add_env_to_gitignore_appends(self, config: Config) -> None:
        """Test that .env is appended to an existing .gitignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            gitignore = config.project_path / ".gitignore"
            gitignore.write_text("build/\n")
            bootstrap = ProjectBootstrap(config)
            bootstrap._add_env_to_gitignore()
            assert ".env" in gitignore.read_text()

    def test_add_env_to_gitignore_no_duplicate(self, config: Config) -> None:
        """Test that .env is not duplicated if already in .gitignore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            gitignore = config.project_path / ".gitignore"
            gitignore.write_text(".env\nbuild/\n")
            bootstrap = ProjectBootstrap(config)
            bootstrap._add_env_to_gitignore()
            assert gitignore.read_text().count(".env") == 1

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

    def test_modify_main_dart_wraps_dotenv_in_try_catch(self, config: Config) -> None:
        """Test that the dotenv.load() call is wrapped in try/catch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "lib").mkdir(parents=True)
            main_dart = config.project_path / "lib" / "main.dart"
            main_dart.write_text(
                "import 'package:flutter/material.dart';\nvoid main() {\n  runApp(MyApp());\n}"
            )
            bootstrap._modify_main_dart()
            content = main_dart.read_text()
            assert "try {" in content
            assert "dotenv.load" in content
            assert "} catch (_) {}" in content

    def test_modify_main_dart_not_exists(self, config: Config) -> None:
        """Test modifying main.dart when it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            bootstrap._modify_main_dart()  # Should not raise

    def test_sqlite_scaffold_includes_migration_strategy(self, config: Config) -> None:
        """Test that the generated AppDatabase includes a MigrationStrategy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.database = "sqlite"
            data_dir = config.project_path / "lib" / "src" / "core" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_sqlite_scaffold()
            content = (data_dir / "app_database.dart").read_text()
            assert "MigrationStrategy" in content
            assert "onCreate" in content
            assert "onUpgrade" in content

    def test_sqlite_scaffold_onupgrade_is_not_silent_noop(self, config: Config) -> None:
        """Test that onUpgrade throws instead of silently skipping migrations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.database = "sqlite"
            data_dir = config.project_path / "lib" / "src" / "core" / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_sqlite_scaffold()
            content = (data_dir / "app_database.dart").read_text()
            # onUpgrade must not be an empty async stub
            assert "onUpgrade: (m, from, to) async {}," not in content
            # must actively signal that migration is needed
            assert "UnimplementedError" in content

    def test_add_drift_dev_to_pubspec(self, config: Config) -> None:
        """Test that drift_dev is written directly to pubspec.yaml for sqlite projects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.database = "sqlite"
            config.project_path.mkdir(parents=True, exist_ok=True)
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec_path.write_text(
                "name: test\ndev_dependencies:\n  build_runner: ^2.9.0\n"
            )
            bootstrap = ProjectBootstrap(config)
            bootstrap._add_drift_dev_to_pubspec()
            content = yaml.safe_load(pubspec_path.read_text())
            assert "drift_dev" in content["dev_dependencies"]

    def test_add_drift_dev_to_pubspec_skips_if_already_present(
        self, config: Config
    ) -> None:
        """Test that drift_dev is not duplicated if already in pubspec.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.database = "sqlite"
            config.project_path.mkdir(parents=True, exist_ok=True)
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec_path.write_text(
                "name: test\ndev_dependencies:\n  drift_dev: ^2.0.0\n"
            )
            bootstrap = ProjectBootstrap(config)
            bootstrap._add_drift_dev_to_pubspec()
            content = yaml.safe_load(pubspec_path.read_text())
            assert content["dev_dependencies"]["drift_dev"] == "^2.0.0"

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

    def test_modify_main_dart_adds_firebase_initializer(self, config: Config) -> None:
        """Test modifying main.dart for Firebase initialization."""
        config.auth_provider = "firebase"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "lib").mkdir(parents=True)
            main_dart = config.project_path / "lib" / "main.dart"
            main_dart.write_text(
                "import 'package:flutter/material.dart';\n"
                "Future<void> main() async {\n"
                "  runApp(const MyApp());\n"
                "}\n"
            )

            bootstrap._modify_main_dart()

            content = main_dart.read_text()
            assert "firebase_initializer.dart" in content
            assert "await initializeFirebase();" in content

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
            assert "run-chrome:" not in content
            assert "run-ios:" in content
            assert "run-android:" in content
            assert "check-android-sdk" in content
            assert "ANDROID_SDK_ROOT" in content
            assert "REQUIRED_NDK" in content
            assert "analyze:" in content
            assert "test:" in content
            assert "integration:" in content
            assert "generate:" not in content

    def test_create_makefile_web_run_chrome(self, config: Config) -> None:
        """Test Makefile includes run-chrome target only when web platform is selected."""
        config.platforms = ["web"]
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_makefile()
            makefile = config.project_path / "Makefile"
            content = makefile.read_text()
            assert "run-chrome:" in content
            assert "flutter run -d chrome" in content

    def test_create_makefile_sqlite_generate_target(self, config: Config) -> None:
        """Test Makefile includes build_runner target for SQLite projects."""
        config.database = "sqlite"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_makefile()
            makefile = config.project_path / "Makefile"
            content = makefile.read_text()
            assert "generate:" in content
            assert "build_runner build" in content

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

    def test_widget_test_includes_pump_and_settle(self, config: Config) -> None:
        """Test that generated widget test calls pumpAndSettle before asserting."""
        config.architecture = "clean"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "test" / "unit").mkdir(parents=True)
            (config.project_path / "test" / "widget").mkdir(parents=True)
            (config.project_path / "integration_test").mkdir(parents=True)
            bootstrap._create_sample_tests()
            widget_content = (
                config.project_path / "test" / "widget" / "app_widget_test.dart"
            ).read_text()
            assert "pumpAndSettle" in widget_content
            assert "find.text('Home')" in widget_content

    def test_integration_test_includes_pump_and_settle(self, config: Config) -> None:
        """Test that generated integration test calls pumpAndSettle before asserting."""
        config.architecture = "clean"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            bootstrap = ProjectBootstrap(config)
            (config.project_path / "test" / "unit").mkdir(parents=True)
            (config.project_path / "test" / "widget").mkdir(parents=True)
            (config.project_path / "integration_test").mkdir(parents=True)
            bootstrap._create_sample_tests()
            integration_content = (
                config.project_path / "integration_test" / "app_test.dart"
            ).read_text()
            assert "pumpAndSettle" in integration_content
            assert "find.text('Home')" in integration_content

    def test_create_environment_support_env_content(self, config: Config) -> None:
        """Test .env file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            (config.project_path / "pubspec.yaml").write_text(
                "flutter:\n  uses-material-design: true\n"
            )
            bootstrap = ProjectBootstrap(config)
            with patch.object(bootstrap, "_modify_main_dart"):
                bootstrap._create_environment_support()
                env_file = config.project_path / ".env"
                content = env_file.read_text()
                assert "API_URL" in content
                assert "https://api.example.com" in content

    def test_add_env_asset_to_pubspec(self, config: Config) -> None:
        """Test that .env is added to pubspec.yaml flutter assets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec_path.write_text("flutter:\n  uses-material-design: true\n")
            bootstrap = ProjectBootstrap(config)
            bootstrap._add_env_asset_to_pubspec()
            pubspec = yaml.safe_load(pubspec_path.read_text())
            assert ".env" in pubspec["flutter"]["assets"]

    def test_add_env_asset_to_pubspec_no_file(self, config: Config) -> None:
        """Test _add_env_asset_to_pubspec is a no-op when pubspec.yaml is absent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._add_env_asset_to_pubspec()  # should not raise

    def test_add_env_asset_to_pubspec_idempotent(self, config: Config) -> None:
        """Test _add_env_asset_to_pubspec does not duplicate .env."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            pubspec_path = config.project_path / "pubspec.yaml"
            pubspec_path.write_text("flutter:\n  assets:\n    - .env\n")
            bootstrap = ProjectBootstrap(config)
            bootstrap._add_env_asset_to_pubspec()
            pubspec = yaml.safe_load(pubspec_path.read_text())
            assert pubspec["flutter"]["assets"].count(".env") == 1

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
            assert "make run-ios" in content
            assert "make test" in content
            assert "make integration" in content
            assert "make analyze" in content
            assert ".env" in content

    def test_create_clean_architecture_scaffold(self, config: Config) -> None:
        """Test creating Clean Architecture scaffold."""
        config.architecture = "clean"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            (config.project_path / "lib").mkdir(parents=True, exist_ok=True)
            (config.project_path / "lib" / "main.dart").write_text("void main() {}")
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_architecture_scaffold()

            assert (config.project_path / "lib" / "src" / "app" / "app.dart").exists()
            assert (
                config.project_path
                / "lib"
                / "src"
                / "features"
                / "home"
                / "presentation"
                / "home_screen.dart"
            ).exists()
            main_content = (config.project_path / "lib" / "main.dart").read_text()
            assert "ProviderScope" in main_content
            assert "src/app/app.dart" in main_content

    def test_clean_architecture_app_uses_stateless_widget(self, config: Config) -> None:
        """Test that App uses StatelessWidget, not ConsumerWidget."""
        config.architecture = "clean"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            (config.project_path / "lib").mkdir(parents=True, exist_ok=True)
            (config.project_path / "lib" / "main.dart").write_text("void main() {}")
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_architecture_scaffold()
            app_content = (
                config.project_path / "lib" / "src" / "app" / "app.dart"
            ).read_text()
            assert "StatelessWidget" in app_content
            assert "ConsumerWidget" not in app_content
            assert "WidgetRef" not in app_content

    def test_clean_architecture_home_screen_uses_stateless_widget(
        self, config: Config
    ) -> None:
        """Test that HomeScreen uses StatelessWidget, not ConsumerWidget."""
        config.architecture = "clean"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            (config.project_path / "lib").mkdir(parents=True, exist_ok=True)
            (config.project_path / "lib" / "main.dart").write_text("void main() {}")
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_architecture_scaffold()
            screen_content = (
                config.project_path
                / "lib"
                / "src"
                / "features"
                / "home"
                / "presentation"
                / "home_screen.dart"
            ).read_text()
            assert "StatelessWidget" in screen_content
            assert "ConsumerWidget" not in screen_content
            assert "WidgetRef" not in screen_content

    def test_create_sqlite_scaffold(self, config: Config) -> None:
        """Test creating Drift SQLite scaffold."""
        config.database = "sqlite"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_architecture_scaffold()

            database_file = (
                config.project_path
                / "lib"
                / "src"
                / "core"
                / "data"
                / "app_database.dart"
            )
            assert database_file.exists()
            content = database_file.read_text()
            assert "DriftDatabase" in content
            assert "AppSettings" in content

    def test_create_mocktail_scaffold(self, config: Config) -> None:
        """Test creating mocktail helpers."""
        config.testing = "mocktail"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_architecture_scaffold()

            mocks_file = config.project_path / "test" / "helpers" / "mocks.dart"
            assert mocks_file.exists()
            assert "MockRepository" in mocks_file.read_text()

    def test_create_firebase_scaffold(self, config: Config) -> None:
        """Test creating Firebase service scaffolds."""
        config.auth_provider = "firebase"
        config.cloud_database = "firestore"
        config.notifications_provider = "firebase"
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            bootstrap = ProjectBootstrap(config)
            bootstrap._create_architecture_scaffold()

            firebase_dir = config.project_path / "lib" / "src" / "core" / "firebase"
            assert (firebase_dir / "firebase_initializer.dart").exists()
            assert (firebase_dir / "firebase_auth_service.dart").exists()
            assert (firebase_dir / "firestore_database.dart").exists()
            assert (firebase_dir / "firebase_notifications_service.dart").exists()

    def test_dependency_selection(self, config: Config) -> None:
        """Test dependency lists include selected starter dependencies."""
        config.architecture = "clean"
        config.database = "sqlite"
        config.testing = "mocktail"
        config.auth_provider = "firebase"
        config.cloud_database = "firestore"
        config.notifications_provider = "firebase"
        bootstrap = ProjectBootstrap(config)

        runtime_dependencies = bootstrap._runtime_dependencies()
        dev_dependencies = bootstrap._dev_dependencies()

        assert "flutter_riverpod" in runtime_dependencies
        assert "drift" in runtime_dependencies
        assert "firebase_core" in runtime_dependencies
        assert "firebase_auth" in runtime_dependencies
        assert "cloud_firestore" in runtime_dependencies
        assert "firebase_messaging" in runtime_dependencies
        assert "drift_dev" in dev_dependencies
        assert "build_runner" in dev_dependencies
        assert "mocktail" in dev_dependencies

    # --- _detect_flutter_version ---

    def test_detect_flutter_version_from_stdout(
        self, bootstrap: ProjectBootstrap
    ) -> None:
        """Version is read from stdout."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="Flutter 3.24.0 • channel stable", stderr=""
            )
            assert bootstrap._detect_flutter_version() == "3.24.0"

    def test_detect_flutter_version_from_stderr(
        self, bootstrap: ProjectBootstrap
    ) -> None:
        """Version falls back to stderr when stdout is empty."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="", stderr="Flutter 3.22.1 • channel stable"
            )
            assert bootstrap._detect_flutter_version() == "3.22.1"

    def test_detect_flutter_version_not_found(
        self, bootstrap: ProjectBootstrap
    ) -> None:
        """Returns None when the version cannot be parsed."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="")
            assert bootstrap._detect_flutter_version() is None

    def test_detect_flutter_version_subprocess_error(
        self, bootstrap: ProjectBootstrap
    ) -> None:
        """Returns None when subprocess raises."""
        with patch("subprocess.run", side_effect=OSError("not found")):
            assert bootstrap._detect_flutter_version() is None

    # --- _pin_flutter_sdk_version ---

    def test_pin_flutter_sdk_version_writes_constraint(
        self, config: Config, tmp_path: Path
    ) -> None:
        """Writes environment.flutter >= constraint into pubspec.yaml."""
        config.output_dir = tmp_path
        project_dir = tmp_path / config.project_name
        project_dir.mkdir()
        pubspec_path = project_dir / "pubspec.yaml"
        pubspec_path.write_text("name: test_app\nenvironment:\n  sdk: '>=3.4.0'\n")

        bootstrap = ProjectBootstrap(config)
        bootstrap._pin_flutter_sdk_version("3.24.0")

        with open(pubspec_path) as f:
            pubspec = yaml.safe_load(f)
        assert pubspec["environment"]["flutter"] == ">=3.24.0"
        assert pubspec["environment"]["sdk"] == ">=3.4.0"  # preserved

    def test_pin_flutter_sdk_version_creates_environment_section(
        self, config: Config, tmp_path: Path
    ) -> None:
        """Creates environment section if absent."""
        config.output_dir = tmp_path
        project_dir = tmp_path / config.project_name
        project_dir.mkdir()
        pubspec_path = project_dir / "pubspec.yaml"
        pubspec_path.write_text("name: test_app\n")

        bootstrap = ProjectBootstrap(config)
        bootstrap._pin_flutter_sdk_version("3.24.0")

        with open(pubspec_path) as f:
            pubspec = yaml.safe_load(f)
        assert pubspec["environment"]["flutter"] == ">=3.24.0"

    def test_pin_flutter_sdk_version_missing_pubspec(
        self, config: Config, tmp_path: Path
    ) -> None:
        """Does not raise when pubspec.yaml does not exist."""
        config.output_dir = tmp_path
        (tmp_path / config.project_name).mkdir()
        bootstrap = ProjectBootstrap(config)
        bootstrap._pin_flutter_sdk_version("3.24.0")  # should not raise

    # --- Makefile version check target ---

    def test_create_makefile_with_detected_version(
        self, config: Config, tmp_path: Path
    ) -> None:
        """Makefile includes check-flutter-version when a version is detected."""
        config.output_dir = tmp_path
        project_dir = tmp_path / config.project_name
        project_dir.mkdir()
        bootstrap = ProjectBootstrap(config)

        with patch.object(bootstrap, "_detect_flutter_version", return_value="3.24.0"):
            bootstrap._create_makefile()

        makefile = (project_dir / "Makefile").read_text()
        assert "FLUTTER_REQUIRED_VERSION := 3.24.0" in makefile
        assert f"FLUTTER_HOME := {config.flutter_location}" in makefile
        assert 'FLUTTER := "$(FLUTTER_HOME)/bin/flutter"' in makefile
        assert "check-flutter-version" in makefile
        assert "$(FLUTTER_REQUIRED_VERSION)" in makefile
        assert "$(FLUTTER) run" in makefile
        assert "run-ios: check-flutter-version" in makefile
        # Version check uses native resolver, not shell parsing
        assert "pub get" in makefile

    def test_create_makefile_upgrade_depends_on_version_check(
        self, config: Config, tmp_path: Path
    ) -> None:
        """upgrade and upgrade-check targets depend on check-flutter-version."""
        config.output_dir = tmp_path
        project_dir = tmp_path / config.project_name
        project_dir.mkdir()
        bootstrap = ProjectBootstrap(config)

        with patch.object(bootstrap, "_detect_flutter_version", return_value="3.24.0"):
            bootstrap._create_makefile()

        makefile = (project_dir / "Makefile").read_text()
        assert "upgrade: check-flutter-version" in makefile
        assert "upgrade-check: check-flutter-version" in makefile

    def test_create_makefile_generate_depends_on_version_check(
        self, config: Config, tmp_path: Path
    ) -> None:
        """generate target depends on check-flutter-version when database=sqlite."""
        config.output_dir = tmp_path
        config.database = "sqlite"
        project_dir = tmp_path / config.project_name
        project_dir.mkdir()
        bootstrap = ProjectBootstrap(config)

        with patch.object(bootstrap, "_detect_flutter_version", return_value="3.24.0"):
            bootstrap._create_makefile()

        makefile = (project_dir / "Makefile").read_text()
        assert "generate: check-flutter-version" in makefile

    def test_create_makefile_test_depends_on_generate_for_sqlite(
        self, config: Config, tmp_path: Path
    ) -> None:
        """test, analyze, and integration targets depend on generate for sqlite projects."""
        config.output_dir = tmp_path
        config.database = "sqlite"
        project_dir = tmp_path / config.project_name
        project_dir.mkdir()
        bootstrap = ProjectBootstrap(config)

        with patch.object(bootstrap, "_detect_flutter_version", return_value="3.24.0"):
            bootstrap._create_makefile()

        makefile = (project_dir / "Makefile").read_text()
        assert "test: check-flutter-version generate" in makefile
        assert "analyze: check-flutter-version generate" in makefile
        assert "integration: check-flutter-version generate" in makefile

    def test_create_makefile_test_does_not_depend_on_generate_without_sqlite(
        self, config: Config, tmp_path: Path
    ) -> None:
        """test target does not depend on generate for non-sqlite projects."""
        config.output_dir = tmp_path
        project_dir = tmp_path / config.project_name
        project_dir.mkdir()
        bootstrap = ProjectBootstrap(config)

        with patch.object(bootstrap, "_detect_flutter_version", return_value="3.24.0"):
            bootstrap._create_makefile()

        makefile = (project_dir / "Makefile").read_text()
        assert "test: check-flutter-version\n" in makefile
        assert "generate" not in makefile

    def test_create_makefile_explicit_version_overrides_detected(
        self, config: Config, tmp_path: Path
    ) -> None:
        """Explicit flutter_version takes precedence over detected version."""
        config.output_dir = tmp_path
        config.flutter_version = "3.22.0"
        project_dir = tmp_path / config.project_name
        project_dir.mkdir()
        bootstrap = ProjectBootstrap(config)

        with patch.object(bootstrap, "_detect_flutter_version", return_value="3.24.0"):
            bootstrap._create_makefile()

        makefile = (project_dir / "Makefile").read_text()
        assert "FLUTTER_REQUIRED_VERSION := 3.22.0" in makefile

    def test_create_makefile_no_version_check_when_undetectable(
        self, config: Config, tmp_path: Path
    ) -> None:
        """Makefile has no version check when Flutter version cannot be detected."""
        config.output_dir = tmp_path
        project_dir = tmp_path / config.project_name
        project_dir.mkdir()
        bootstrap = ProjectBootstrap(config)

        with patch.object(bootstrap, "_detect_flutter_version", return_value=None):
            bootstrap._create_makefile()

        makefile = (project_dir / "Makefile").read_text()
        assert "check-flutter-version" not in makefile
        assert "FLUTTER_REQUIRED_VERSION" not in makefile
