"""E2E tests for flag-based and TTY (interactive) invocation of init, create, append.

Each test class covers one command and one input mode:
  - *Flags  — all values supplied as CLI flags; no TTY prompts fired
  - *TTY    — values supplied via stdin (CliRunner input=); simulates an interactive session

External calls (FlutterSetup.run, ProjectBootstrap.append_project, ConfigManager) are
mocked throughout so these tests run without a real Flutter SDK or filesystem side-effects
beyond tmp_path.
"""

import contextlib
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from flutter_setup.cli import cli

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _base_config(tmp_path: Path) -> dict[str, Any]:
    return {
        "flutter": {
            "location": str(tmp_path / "flutter_sdk"),
            "channel": "stable",
            "update_mode": "skip",
        },
        "project": {
            "org": "com.example",
            "template": "app",
            "architecture": "basic",
            "database": "none",
            "testing": "standard",
            "e2e_testing": "integration_test",
            "auth_provider": "none",
            "cloud_database": "none",
            "notifications_provider": "none",
            "ios_language": "swift",
            "android_language": "kotlin",
        },
    }


@contextlib.contextmanager
def _patch_config(tmp_path: Path) -> Any:
    with patch("flutter_setup.cli.ConfigManager") as mock_cm:
        mock_cm.return_value.load_config.return_value = _base_config(tmp_path)
        mock_cm.return_value.config_file.exists.return_value = False
        mock_cm.return_value.detect_flutter_location.return_value = None
        yield mock_cm


# ---------------------------------------------------------------------------
# init — flags
# ---------------------------------------------------------------------------


class TestInitFlags:
    """init accepts all values via flags and skips every interactive prompt."""

    def test_flags_exit_zero(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = False
            mock_cm.return_value.detect_flutter_location.return_value = None
            result = runner.invoke(
                cli,
                [
                    "init",
                    "--flutter-location",
                    str(tmp_path / "flutter"),
                    "--channel",
                    "stable",
                    "--org",
                    "com.acme",
                ],
            )
        assert result.exit_code == 0, result.output

    def test_flags_save_correct_flutter_location(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = False
            mock_cm.return_value.detect_flutter_location.return_value = None
            runner.invoke(
                cli,
                [
                    "init",
                    "--flutter-location",
                    str(tmp_path / "sdk"),
                    "--channel",
                    "beta",
                    "--org",
                    "com.test",
                ],
            )
        saved = mock_cm.return_value.save_config.call_args.args[0]
        assert "sdk" in saved["flutter"]["location"]

    def test_flags_save_correct_channel(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = False
            mock_cm.return_value.detect_flutter_location.return_value = None
            runner.invoke(
                cli,
                [
                    "init",
                    "--flutter-location",
                    str(tmp_path / "sdk"),
                    "--channel",
                    "beta",
                    "--org",
                    "com.test",
                ],
            )
        saved = mock_cm.return_value.save_config.call_args.args[0]
        assert saved["flutter"]["channel"] == "beta"

    def test_flags_save_correct_org(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = False
            mock_cm.return_value.detect_flutter_location.return_value = None
            runner.invoke(
                cli,
                [
                    "init",
                    "--flutter-location",
                    str(tmp_path / "sdk"),
                    "--channel",
                    "stable",
                    "--org",
                    "com.mycompany",
                ],
            )
        saved = mock_cm.return_value.save_config.call_args.args[0]
        assert saved["project"]["org"] == "com.mycompany"

    def test_invalid_channel_flag_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = False
            result = runner.invoke(
                cli,
                [
                    "init",
                    "--flutter-location",
                    str(tmp_path / "sdk"),
                    "--channel",
                    "nightly",
                    "--org",
                    "com.test",
                ],
            )
        assert result.exit_code != 0

    def test_partial_flags_org_only_prompts_for_location_and_channel(
        self, tmp_path: Path
    ) -> None:
        """Supplying only --org still prompts for location and channel."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = False
            mock_cm.return_value.detect_flutter_location.return_value = None
            result = runner.invoke(
                cli,
                ["init", "--org", "com.partial"],
                input=f"{tmp_path / 'sdk'}\nstable\n",
            )
        assert result.exit_code == 0
        saved = mock_cm.return_value.save_config.call_args.args[0]
        assert saved["project"]["org"] == "com.partial"
        assert saved["flutter"]["channel"] == "stable"


# ---------------------------------------------------------------------------
# init — TTY
# ---------------------------------------------------------------------------


class TestInitTTY:
    """init prompts for all three values when no flags are provided."""

    def test_tty_exit_zero(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = False
            mock_cm.return_value.detect_flutter_location.return_value = None
            result = runner.invoke(
                cli,
                ["init"],
                input=f"{tmp_path / 'flutter'}\nstable\ncom.ttytest\n",
            )
        assert result.exit_code == 0, result.output

    def test_tty_saves_prompted_values(self, tmp_path: Path) -> None:
        runner = CliRunner()
        sdk_path = str(tmp_path / "myflutter")
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = False
            mock_cm.return_value.detect_flutter_location.return_value = None
            runner.invoke(
                cli,
                ["init"],
                input=f"{sdk_path}\nbeta\ncom.prompted\n",
            )
        saved = mock_cm.return_value.save_config.call_args.args[0]
        assert "myflutter" in saved["flutter"]["location"]
        assert saved["flutter"]["channel"] == "beta"
        assert saved["project"]["org"] == "com.prompted"

    def test_tty_accepts_default_location_when_detected(self, tmp_path: Path) -> None:
        """Pressing Enter uses the auto-detected Flutter location."""
        detected = tmp_path / "detected_flutter"
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = False
            mock_cm.return_value.detect_flutter_location.return_value = detected
            result = runner.invoke(
                cli,
                ["init"],
                input="\nstable\ncom.default\n",
            )
        assert result.exit_code == 0
        saved = mock_cm.return_value.save_config.call_args.args[0]
        assert "detected_flutter" in saved["flutter"]["location"]

    def test_tty_existing_config_shows_current_values(self, tmp_path: Path) -> None:
        """When a config exists, prompts show current values as defaults."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.config_file.exists.return_value = True
            mock_cm.return_value.load_config.return_value = {
                "flutter": {
                    "location": str(tmp_path / "existing_sdk"),
                    "channel": "stable",
                },
                "project": {"org": "com.existing"},
            }
            result = runner.invoke(
                cli,
                ["init"],
                # Accept all defaults by pressing Enter three times
                input="\n\n\n",
            )
        assert result.exit_code == 0
        saved = mock_cm.return_value.save_config.call_args.args[0]
        assert "existing_sdk" in saved["flutter"]["location"]
        assert saved["project"]["org"] == "com.existing"


# ---------------------------------------------------------------------------
# create — flags
# ---------------------------------------------------------------------------


class TestCreateFlags:
    """create accepts platforms and all options as flags."""

    def test_platforms_flag_single(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                mock_setup.return_value = MagicMock()
                result = runner.invoke(
                    cli,
                    ["create", "MyApp", "--platforms", "linux", "--dir", str(tmp_path)],
                )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert config.platforms == ["linux"]

    def test_platforms_flag_multiple(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                mock_setup.return_value = MagicMock()
                result = runner.invoke(
                    cli,
                    [
                        "create",
                        "MyApp",
                        "--platforms",
                        "ios",
                        "--platforms",
                        "android",
                        "--platforms",
                        "web",
                        "--dir",
                        str(tmp_path),
                    ],
                )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert set(config.platforms) == {"ios", "android", "web"}

    def test_invalid_platform_flag_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with _patch_config(tmp_path):
            result = runner.invoke(
                cli,
                ["create", "MyApp", "--platforms", "atari", "--dir", str(tmp_path)],
            )
        assert result.exit_code != 0

    def test_all_flags_no_prompts(self, tmp_path: Path) -> None:
        """Providing all flags should produce a zero exit without any interactive prompts."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                mock_setup.return_value = MagicMock()
                result = runner.invoke(
                    cli,
                    [
                        "create",
                        "MyApp",
                        "--platforms",
                        "ios",
                        "--platforms",
                        "android",
                        "--org",
                        "com.flags",
                        "--channel",
                        "stable",
                        "--template",
                        "app",
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
                        "--dir",
                        str(tmp_path),
                    ],
                )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert config.org == "com.flags"
        assert config.architecture == "clean"
        assert config.database == "sqlite"
        assert config.testing == "mocktail"
        assert config.auth_provider == "firebase"

    def test_no_platforms_and_non_interactive_fails(self, tmp_path: Path) -> None:
        """Omitting --platforms in non-interactive mode must not exit 0 silently."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli._is_interactive", return_value=False):
                with patch("flutter_setup.cli.FlutterSetup"):
                    result = runner.invoke(
                        cli,
                        ["create", "MyApp", "--dir", str(tmp_path)],
                    )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# create — TTY
# ---------------------------------------------------------------------------


class TestCreateTTY:
    """create prompts for project name and platforms when not given as flags."""

    def test_tty_prompts_for_project_name(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                mock_setup.return_value = MagicMock()
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    result = runner.invoke(
                        cli,
                        ["create", "--dir", str(tmp_path)],
                        # project name, then platforms
                        input="TTYApp\nios android\n",
                    )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert config.project_name == "TTYApp"

    def test_tty_prompts_for_platforms(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                mock_setup.return_value = MagicMock()
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    result = runner.invoke(
                        cli,
                        # Name given as positional; no --platforms flag
                        ["create", "TTYApp", "--dir", str(tmp_path)],
                        input="ios android\n",
                    )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert set(config.platforms) == {"ios", "android"}

    def test_tty_name_as_positional_platforms_as_tty(self, tmp_path: Path) -> None:
        """Name given on command line; platforms prompted interactively."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                mock_setup.return_value = MagicMock()
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    result = runner.invoke(
                        cli,
                        ["create", "NamedApp", "--dir", str(tmp_path)],
                        input="linux\n",
                    )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert config.project_name == "NamedApp"
        assert config.platforms == ["linux"]

    def test_tty_platforms_flag_overrides_prompt(self, tmp_path: Path) -> None:
        """--platforms flag wins over any TTY input for platforms."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                mock_setup.return_value = MagicMock()
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    result = runner.invoke(
                        cli,
                        [
                            "create",
                            "FlagApp",
                            "--platforms",
                            "web",
                            "--dir",
                            str(tmp_path),
                        ],
                        # No platforms input needed because flag was given
                    )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert config.platforms == ["web"]


# ---------------------------------------------------------------------------
# append — flags (non-Flutter directory path)
# ---------------------------------------------------------------------------


class TestAppendFlags:
    """append --platforms is used for the non-Flutter directory path."""

    def test_platforms_flag_used_for_non_flutter_dir(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                    mock_setup.return_value = MagicMock()
                    result = runner.invoke(
                        cli,
                        [
                            "append",
                            "MyApp",
                            "--platforms",
                            "ios",
                            "--platforms",
                            "android",
                            "--dir",
                            str(tmp_path),
                        ],
                    )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert set(config.platforms) == {"ios", "android"}

    def test_platforms_flag_single_platform(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                    mock_setup.return_value = MagicMock()
                    result = runner.invoke(
                        cli,
                        [
                            "append",
                            "MyApp",
                            "--platforms",
                            "linux",
                            "--dir",
                            str(tmp_path),
                        ],
                    )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert config.platforms == ["linux"]

    def test_platforms_flag_ignored_for_existing_flutter_project(
        self, tmp_path: Path
    ) -> None:
        """--platforms is not used when the target already is a Flutter project."""
        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        (project_dir / "pubspec.yaml").write_text(
            "name: my_app\nflutter:\n  uses-material-design: true\n"
        )
        (project_dir / "ios").mkdir()
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.ProjectBootstrap") as mock_bs:
                mock_bs.return_value = MagicMock()
                result = runner.invoke(
                    cli,
                    # Pass --platforms web but the project already has ios/ detected
                    ["append", "--platforms", "web", "--dir", str(project_dir)],
                )
        assert result.exit_code == 0, result.output
        config = mock_bs.call_args.args[0]
        # Detected platforms win; the flag is irrelevant for existing Flutter projects
        assert "ios" in config.platforms

    def test_no_platforms_flag_non_interactive_uses_default(
        self, tmp_path: Path
    ) -> None:
        """Without --platforms in non-interactive mode the default ios/android/web is used."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli._is_interactive", return_value=False):
                    with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                        mock_setup.return_value = MagicMock()
                        result = runner.invoke(
                            cli,
                            ["append", "MyApp", "--dir", str(tmp_path)],
                        )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert set(config.platforms) == {"ios", "android", "web"}


# ---------------------------------------------------------------------------
# append — TTY (non-Flutter directory path)
# ---------------------------------------------------------------------------


class TestAppendTTY:
    """append prompts for platforms in interactive mode when --platforms is not given."""

    def test_tty_prompts_for_platforms(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                        mock_setup.return_value = MagicMock()
                        result = runner.invoke(
                            cli,
                            ["append", "MyApp", "--dir", str(tmp_path)],
                            input="ios android\n",
                        )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert set(config.platforms) == {"ios", "android"}

    def test_tty_platforms_flag_skips_prompt(self, tmp_path: Path) -> None:
        """--platforms flag prevents the platforms prompt even in interactive mode."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                        mock_setup.return_value = MagicMock()
                        result = runner.invoke(
                            cli,
                            [
                                "append",
                                "MyApp",
                                "--platforms",
                                "macos",
                                "--dir",
                                str(tmp_path),
                            ],
                            # No input needed; flag should have bypassed the prompt
                        )
        assert result.exit_code == 0, result.output
        config = mock_setup.call_args.args[0]
        assert config.platforms == ["macos"]

    def test_tty_invalid_platform_fails(self, tmp_path: Path) -> None:
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.detect_flutter_project", return_value=False):
                with patch("flutter_setup.cli._is_interactive", return_value=True):
                    result = runner.invoke(
                        cli,
                        ["append", "MyApp", "--dir", str(tmp_path)],
                        input="ios badplatform\n",
                    )
        assert result.exit_code != 0
        assert "badplatform" in result.output or "Unknown" in result.output
