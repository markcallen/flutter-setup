"""Tests for the cli module."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from flutter_setup.cli import cli, print_banner
from flutter_setup.exceptions import FlutterSetupError


class TestCLI:
    """Test cases for CLI functions."""

    def test_print_banner(self) -> None:
        """Test printing banner."""
        print_banner()  # Should not raise

    def test_init_config_new(self) -> None:
        """Test init_config creating new config."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.config_file.exists.return_value = False
            mock_manager.detect_flutter_location.return_value = Path("/flutter")
            with patch(
                "click.prompt",
                side_effect=["/flutter", "stable", "com.test"],
            ):
                result = runner.invoke(cli, ["init"])
                assert result.exit_code == 0

    def test_init_config_existing(self) -> None:
        """Test init_config with existing config."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.config_file.exists.return_value = True
            mock_manager.load_config.return_value = {
                "flutter": {"location": "/flutter", "channel": "stable"},
                "project": {"org": "com.test"},
            }
            with patch(
                "click.prompt",
                side_effect=["/flutter", "stable", "com.test"],
            ):
                result = runner.invoke(cli, ["init"])
                assert result.exit_code == 0

    def test_check_command_success(self) -> None:
        """Test check_command when all checks pass."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {"location": "/flutter", "channel": "stable"},
                "project": {},
            }
            with patch("flutter_setup.cli.PrerequisitesManager") as mock_prereq_class:
                mock_prereq = Mock()
                mock_prereq_class.return_value = mock_prereq
                mock_prereq.check_only.return_value = True
                with patch("flutter_setup.cli.FlutterManager") as mock_flutter_class:
                    mock_flutter = Mock()
                    mock_flutter_class.return_value = mock_flutter
                    mock_flutter.check_only.return_value = True
                    result = runner.invoke(cli, ["check"])
                    assert result.exit_code == 0

    def test_check_command_failure(self) -> None:
        """Test check_command when checks fail."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {"location": "/flutter", "channel": "stable"},
                "project": {},
            }
            with patch("flutter_setup.cli.PrerequisitesManager") as mock_prereq_class:
                mock_prereq = Mock()
                mock_prereq_class.return_value = mock_prereq
                mock_prereq.check_only.return_value = False
                with patch("flutter_setup.cli.FlutterManager") as mock_flutter_class:
                    mock_flutter = Mock()
                    mock_flutter_class.return_value = mock_flutter
                    mock_flutter.check_only.return_value = False
                    result = runner.invoke(cli, ["check"])
                    assert result.exit_code == 1

    def test_setup_command_success(self) -> None:
        """Test setup_command successful execution."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {"location": "/flutter", "channel": "stable"},
                "project": {"org": "com.example"},
            }
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                mock_setup = Mock()
                mock_setup_class.return_value = mock_setup
                result = runner.invoke(
                    cli,
                    [
                        "setup",
                        "TestApp",
                        "ios",
                        "android",
                        "--architecture",
                        "clean",
                        "--database",
                        "sqlite",
                        "--testing",
                        "mocktail",
                        "--auth-provider",
                        "firebase",
                        "--cloud-database",
                        "firestore",
                        "--notifications-provider",
                        "firebase",
                        "--template",
                        "app",
                        "--ios-language",
                        "swift",
                        "--android-language",
                        "kotlin",
                        "--flutter-update",
                        "reset",
                    ],
                )
                assert result.exit_code == 0
                config = mock_setup_class.call_args.args[0]
                assert config.architecture == "clean"
                assert config.database == "sqlite"
                assert config.testing == "mocktail"
                assert config.auth_provider == "firebase"
                assert config.cloud_database == "firestore"
                assert config.notifications_provider == "firebase"

    def test_setup_command_interactive_prompts(self) -> None:
        """Test setup_command prompts for project name, platforms, and options not in config."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {
                    "location": "/flutter",
                    "channel": "stable",
                    "update_mode": "reset",
                },
                "project": {"org": "com.mycompany"},
            }
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                mock_setup = Mock()
                mock_setup_class.return_value = mock_setup
                # Prompts in order: project name, platforms, template, architecture,
                # database, testing, auth_provider, cloud_database, notifications_provider.
                # ios/android language are NOT prompted because template="app".
                user_input = (
                    "\n".join(
                        [
                            "MyApp",
                            "ios android",
                            "app",
                            "clean",
                            "sqlite",
                            "mocktail",
                            "none",
                            "none",
                            "none",
                        ]
                    )
                    + "\n"
                )
                # Simulate a TTY so get_merged_or_prompt falls through to click.prompt
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    result = runner.invoke(cli, ["setup"], input=user_input)
                assert result.exit_code == 0
                config = mock_setup_class.call_args.args[0]
                assert config.project_name == "MyApp"
                assert config.platforms == ["ios", "android"]
                assert config.org == "com.mycompany"
                assert config.architecture == "clean"
                assert config.database == "sqlite"
                assert config.testing == "mocktail"

    def test_setup_command_plugin_template_prompts_languages(self) -> None:
        """ios/android language prompts appear only for plugin template."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {
                    "location": "/flutter",
                    "channel": "stable",
                    "update_mode": "skip",
                },
                "project": {"org": "com.test"},
            }
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                mock_setup = Mock()
                mock_setup_class.return_value = mock_setup
                # template=plugin → language prompts appear after the standard ones
                user_input = (
                    "\n".join(
                        [
                            "plugin",  # template
                            "basic",  # architecture
                            "none",  # database
                            "standard",  # testing
                            "none",  # auth_provider
                            "none",  # cloud_database
                            "none",  # notifications_provider
                            "objc",  # ios_language (only for plugin)
                            "java",  # android_language (only for plugin)
                        ]
                    )
                    + "\n"
                )
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    result = runner.invoke(
                        cli, ["setup", "MyPlugin", "ios", "android"], input=user_input
                    )
                assert result.exit_code == 0
                config = mock_setup_class.call_args.args[0]
                assert config.template == "plugin"
                assert config.ios_language == "objc"
                assert config.android_language == "java"

    def test_setup_command_invalid_config_value_triggers_prompt(self) -> None:
        """An invalid value in the config file falls through to interactive prompt."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {
                    "location": "/flutter",
                    "channel": "stable",
                    "update_mode": "skip",
                },
                "project": {
                    "org": "com.test",
                    "template": "INVALID",  # bad value → should prompt
                    "architecture": "basic",
                    "database": "none",
                    "testing": "standard",
                    "auth_provider": "none",
                    "cloud_database": "none",
                    "notifications_provider": "none",
                    "ios_language": "swift",
                    "android_language": "kotlin",
                },
            }
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                mock_setup = Mock()
                mock_setup_class.return_value = mock_setup
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    result = runner.invoke(
                        cli, ["setup", "TestApp", "ios"], input="app\n"
                    )
                assert result.exit_code == 0
                config = mock_setup_class.call_args.args[0]
                assert config.template == "app"

    def test_setup_command_with_flutter_version(self) -> None:
        """--flutter-version is passed through to Config."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {
                    "location": "/flutter",
                    "channel": "stable",
                    "update_mode": "skip",
                },
                "project": {
                    "org": "com.example",
                    "template": "app",
                    "architecture": "basic",
                    "database": "none",
                    "testing": "standard",
                    "auth_provider": "none",
                    "cloud_database": "none",
                    "notifications_provider": "none",
                    "ios_language": "swift",
                    "android_language": "kotlin",
                },
            }
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                mock_setup = Mock()
                mock_setup_class.return_value = mock_setup
                result = runner.invoke(
                    cli,
                    ["setup", "TestApp", "ios", "--flutter-version", "3.24.0"],
                )
                assert result.exit_code == 0
                config = mock_setup_class.call_args.args[0]
                assert config.flutter_version == "3.24.0"

    def test_init_config_preserves_project_settings(self) -> None:
        """Re-running init preserves existing project settings like architecture."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.config_file.exists.return_value = True
            mock_manager.load_config.return_value = {
                "flutter": {"location": "/flutter", "channel": "stable"},
                "project": {
                    "org": "com.test",
                    "template": "plugin",
                    "architecture": "clean",
                    "database": "sqlite",
                    "testing": "mocktail",
                    "auth_provider": "firebase",
                    "cloud_database": "firestore",
                    "notifications_provider": "firebase",
                    "ios_language": "objc",
                    "android_language": "java",
                },
            }
            with patch(
                "click.prompt",
                side_effect=["/flutter", "stable", "com.test"],
            ):
                result = runner.invoke(cli, ["init"])
                assert result.exit_code == 0
                saved = mock_manager.save_config.call_args.args[0]
                assert saved["project"]["template"] == "plugin"
                assert saved["project"]["architecture"] == "clean"
                assert saved["project"]["database"] == "sqlite"
                assert saved["project"]["testing"] == "mocktail"
                assert saved["project"]["auth_provider"] == "firebase"
                assert saved["project"]["ios_language"] == "objc"
                assert saved["project"]["android_language"] == "java"

    def test_setup_command_no_platforms_prompts(self) -> None:
        """Test setup_command prompts for platforms when not provided."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {
                    "location": "/flutter",
                    "channel": "stable",
                    "update_mode": "reset",
                },
                "project": {
                    "org": "com.example",
                    "template": "app",
                    "architecture": "basic",
                    "database": "none",
                    "testing": "standard",
                    "auth_provider": "none",
                    "cloud_database": "none",
                    "notifications_provider": "none",
                    "ios_language": "swift",
                    "android_language": "kotlin",
                },
            }
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                mock_setup = Mock()
                mock_setup_class.return_value = mock_setup
                result = runner.invoke(cli, ["setup", "TestApp"], input="ios android\n")
                assert result.exit_code == 0
                config = mock_setup_class.call_args.args[0]
                assert config.platforms == ["ios", "android"]

    def test_setup_command_flutter_setup_error(self) -> None:
        """Test setup_command with FlutterSetupError."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {
                    "location": "/flutter",
                    "channel": "stable",
                    "update_mode": "reset",
                },
                "project": {
                    "org": "com.example",
                    "template": "app",
                    "architecture": "basic",
                    "database": "none",
                    "testing": "standard",
                    "auth_provider": "none",
                    "cloud_database": "none",
                    "notifications_provider": "none",
                    "ios_language": "swift",
                    "android_language": "kotlin",
                },
            }
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                mock_setup = Mock()
                mock_setup_class.return_value = mock_setup
                mock_setup.run.side_effect = FlutterSetupError("Setup failed")
                result = runner.invoke(cli, ["setup", "TestApp", "ios"])
                assert result.exit_code == 1

    def test_setup_command_keyboard_interrupt(self) -> None:
        """Test setup_command with KeyboardInterrupt."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            mock_manager.load_config.return_value = {
                "flutter": {
                    "location": "/flutter",
                    "channel": "stable",
                    "update_mode": "reset",
                },
                "project": {
                    "org": "com.example",
                    "template": "app",
                    "architecture": "basic",
                    "database": "none",
                    "testing": "standard",
                    "auth_provider": "none",
                    "cloud_database": "none",
                    "notifications_provider": "none",
                    "ios_language": "swift",
                    "android_language": "kotlin",
                },
            }
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                mock_setup = Mock()
                mock_setup_class.return_value = mock_setup
                mock_setup.run.side_effect = KeyboardInterrupt()
                result = runner.invoke(cli, ["setup", "TestApp", "ios"])
                assert result.exit_code == 1


class TestAppendCommand:
    """Tests for the append CLI command."""

    def _base_config(self) -> dict[str, dict[str, str]]:
        return {
            "flutter": {"location": "/flutter", "channel": "stable"},
            "project": {},
        }

    def test_append_existing_flutter_project(self, tmp_path: Path) -> None:
        """append on an existing Flutter project calls bootstrap.append_project()."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=True):
                with patch("flutter_setup.cli.get_pubspec_name", return_value="myapp"):
                    with patch(
                        "flutter_setup.cli.detect_platforms",
                        return_value=["ios", "android"],
                    ):
                        with patch(
                            "flutter_setup.cli.ProjectBootstrap"
                        ) as mock_bs_class:
                            mock_bs = Mock()
                            mock_bs_class.return_value = mock_bs
                            result = runner.invoke(
                                cli, ["append", "--dir", str(tmp_path)]
                            )
                            assert result.exit_code == 0
                            mock_bs.append_project.assert_called_once()

    def test_append_existing_flutter_project_no_pubspec_name(
        self, tmp_path: Path
    ) -> None:
        """Falls back to directory name when pubspec has no name field."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=True):
                with patch("flutter_setup.cli.get_pubspec_name", return_value=None):
                    with patch(
                        "flutter_setup.cli.detect_platforms",
                        return_value=["ios"],
                    ):
                        with patch(
                            "flutter_setup.cli.ProjectBootstrap"
                        ) as mock_bs_class:
                            mock_bs = Mock()
                            mock_bs_class.return_value = mock_bs
                            result = runner.invoke(
                                cli, ["append", "--dir", str(tmp_path)]
                            )
                            assert result.exit_code == 0
                            config = mock_bs_class.call_args.args[0]
                            assert config.project_name == tmp_path.name

    def test_append_existing_flutter_project_with_force(self, tmp_path: Path) -> None:
        """--force is forwarded to ProjectBootstrap."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=True):
                with patch("flutter_setup.cli.get_pubspec_name", return_value="app"):
                    with patch(
                        "flutter_setup.cli.detect_platforms", return_value=["web"]
                    ):
                        with patch(
                            "flutter_setup.cli.ProjectBootstrap"
                        ) as mock_bs_class:
                            mock_bs = Mock()
                            mock_bs_class.return_value = mock_bs
                            result = runner.invoke(
                                cli,
                                ["append", "--dir", str(tmp_path), "--force"],
                            )
                            assert result.exit_code == 0
                            assert mock_bs_class.call_args.kwargs["force"] is True

    def test_append_non_flutter_with_project_name(self, tmp_path: Path) -> None:
        """Non-Flutter directory with project_name argument runs full FlutterSetup."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli._is_interactive", return_value=False):
                    with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                        mock_setup = Mock()
                        mock_setup_class.return_value = mock_setup
                        result = runner.invoke(
                            cli,
                            ["append", "myapp", "--dir", str(tmp_path)],
                        )
                        assert result.exit_code == 0
                        mock_setup.run.assert_called_once()

    def test_append_non_flutter_without_project_name_raises_usage_error(
        self, tmp_path: Path
    ) -> None:
        """Non-Flutter directory without project_name raises UsageError."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                result = runner.invoke(cli, ["append", "--dir", str(tmp_path)])
                assert result.exit_code != 0

    def test_append_non_flutter_interactive_prompts_platforms(
        self, tmp_path: Path
    ) -> None:
        """In interactive mode, platforms are prompted."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                        mock_setup = Mock()
                        mock_setup_class.return_value = mock_setup
                        result = runner.invoke(
                            cli,
                            ["append", "myapp", "--dir", str(tmp_path)],
                            input="ios android\n",
                        )
                        assert result.exit_code == 0
                        config = mock_setup_class.call_args.args[0]
                        assert config.platforms == ["ios", "android"]

    def test_append_non_flutter_non_interactive_uses_default_platforms(
        self, tmp_path: Path
    ) -> None:
        """Non-interactive mode uses default platforms without prompting."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli._is_interactive", return_value=False):
                    with patch("flutter_setup.cli.FlutterSetup") as mock_setup_class:
                        mock_setup = Mock()
                        mock_setup_class.return_value = mock_setup
                        result = runner.invoke(
                            cli,
                            ["append", "myapp", "--dir", str(tmp_path)],
                        )
                        assert result.exit_code == 0
                        config = mock_setup_class.call_args.args[0]
                        assert config.platforms == ["ios", "android", "web"]

    def test_append_flutter_setup_error(self, tmp_path: Path) -> None:
        """FlutterSetupError exits with code 1."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=True):
                with patch("flutter_setup.cli.get_pubspec_name", return_value="app"):
                    with patch(
                        "flutter_setup.cli.detect_platforms", return_value=["ios"]
                    ):
                        with patch(
                            "flutter_setup.cli.ProjectBootstrap"
                        ) as mock_bs_class:
                            mock_bs = Mock()
                            mock_bs_class.return_value = mock_bs
                            mock_bs.append_project.side_effect = FlutterSetupError(
                                "boom"
                            )
                            result = runner.invoke(
                                cli, ["append", "--dir", str(tmp_path)]
                            )
                            assert result.exit_code == 1

    def test_append_keyboard_interrupt(self, tmp_path: Path) -> None:
        """KeyboardInterrupt exits with code 1."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=True):
                with patch("flutter_setup.cli.get_pubspec_name", return_value="app"):
                    with patch(
                        "flutter_setup.cli.detect_platforms", return_value=["ios"]
                    ):
                        with patch(
                            "flutter_setup.cli.ProjectBootstrap"
                        ) as mock_bs_class:
                            mock_bs = Mock()
                            mock_bs_class.return_value = mock_bs
                            mock_bs.append_project.side_effect = KeyboardInterrupt()
                            result = runner.invoke(
                                cli, ["append", "--dir", str(tmp_path)]
                            )
                            assert result.exit_code == 1

    def test_append_unexpected_exception(self, tmp_path: Path) -> None:
        """Unexpected exceptions exit with code 1."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=True):
                with patch("flutter_setup.cli.get_pubspec_name", return_value="app"):
                    with patch(
                        "flutter_setup.cli.detect_platforms", return_value=["ios"]
                    ):
                        with patch(
                            "flutter_setup.cli.ProjectBootstrap"
                        ) as mock_bs_class:
                            mock_bs = Mock()
                            mock_bs_class.return_value = mock_bs
                            mock_bs.append_project.side_effect = RuntimeError("oops")
                            result = runner.invoke(
                                cli, ["append", "--dir", str(tmp_path)]
                            )
                            assert result.exit_code == 1

    def test_append_dry_run(self, tmp_path: Path) -> None:
        """--dry-run is forwarded to Config."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=True):
                with patch("flutter_setup.cli.get_pubspec_name", return_value="app"):
                    with patch(
                        "flutter_setup.cli.detect_platforms", return_value=["ios"]
                    ):
                        with patch(
                            "flutter_setup.cli.ProjectBootstrap"
                        ) as mock_bs_class:
                            mock_bs = Mock()
                            mock_bs_class.return_value = mock_bs
                            result = runner.invoke(
                                cli,
                                ["append", "--dir", str(tmp_path), "--dry-run"],
                            )
                            assert result.exit_code == 0
                            config = mock_bs_class.call_args.args[0]
                            assert config.dry_run is True

    def test_append_no_flutter_location_in_config(self, tmp_path: Path) -> None:
        """Falls back to default flutter location when not set in config."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = {
                "flutter": {},
                "project": {},
            }
            with patch("flutter_setup.cli.detect_flutter_project", return_value=True):
                with patch("flutter_setup.cli.get_pubspec_name", return_value="app"):
                    with patch(
                        "flutter_setup.cli.detect_platforms", return_value=["ios"]
                    ):
                        with patch(
                            "flutter_setup.cli.ProjectBootstrap"
                        ) as mock_bs_class:
                            mock_bs = Mock()
                            mock_bs_class.return_value = mock_bs
                            result = runner.invoke(
                                cli, ["append", "--dir", str(tmp_path)]
                            )
                            assert result.exit_code == 0
                            config = mock_bs_class.call_args.args[0]
                            assert "flutter" in str(config.flutter_location)

    def test_append_non_flutter_interactive_invalid_platforms(
        self, tmp_path: Path
    ) -> None:
        """Invalid platform names in interactive mode raise a UsageError."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config()
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    result = runner.invoke(
                        cli,
                        ["append", "myapp", "--dir", str(tmp_path)],
                        input="ios typo\n",
                    )
                    assert result.exit_code != 0
