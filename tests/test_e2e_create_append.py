"""End-to-end tests for the create → append workflow and their safeguards.

These tests drive the CLI commands through Click's CliRunner without touching
the real filesystem outside of tmp_path, and mock only the expensive external
calls (FlutterSetup.run, ProjectBootstrap.append_project, etc.).  Each test
exercises a realistic scenario or safeguard.
"""

import contextlib
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from flutter_setup.bootstrap import ProjectBootstrap
from flutter_setup.cicd_generator import CicdGenerator
from flutter_setup.cli import cli

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _flutter_config(tmp_path: Path) -> dict[str, Any]:
    return {
        "flutter": {"location": str(tmp_path / "flutter_sdk"), "channel": "stable"},
        "project": {"org": "com.example"},
    }


def _patch_config(tmp_path: Path) -> AbstractContextManager[Any]:
    """Context manager that patches ConfigManager to return a minimal config."""

    @contextlib.contextmanager
    def _ctx() -> Any:
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = _flutter_config(tmp_path)
            yield mock_cm

    return _ctx()


# ---------------------------------------------------------------------------
# Happy-path: create then append
# ---------------------------------------------------------------------------


class TestCreateThenAppend:
    def test_create_new_project_succeeds(self, tmp_path: Path) -> None:
        """create on a fresh directory calls FlutterSetup.run and exits 0."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_cls:
                mock_cls.return_value = MagicMock()
                result = runner.invoke(
                    cli,
                    ["create", "MyApp", "ios", "android", "--dir", str(tmp_path)],
                )
        assert result.exit_code == 0
        mock_cls.return_value.run.assert_called_once()

    def test_append_existing_flutter_project(self, tmp_path: Path) -> None:
        """append on a Flutter project calls bootstrap.append_project and exits 0."""
        runner = CliRunner()
        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        (project_dir / "pubspec.yaml").write_text(
            "name: my_app\nflutter:\n  uses-material-design: true\n"
        )
        (project_dir / "ios").mkdir()
        (project_dir / "android").mkdir()

        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.ProjectBootstrap") as mock_bs:
                mock_bs.return_value = MagicMock()
                result = runner.invoke(cli, ["append", "--dir", str(project_dir)])

        assert result.exit_code == 0
        mock_bs.return_value.append_project.assert_called_once()

    def test_create_then_append_full_flow(self, tmp_path: Path) -> None:
        """Simulate a complete create → append flow on the same project."""
        runner = CliRunner()

        # Step 1: create
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_setup:
                mock_setup.return_value = MagicMock()
                result = runner.invoke(
                    cli,
                    ["create", "MyApp", "ios", "android", "--dir", str(tmp_path)],
                )
        assert result.exit_code == 0

        # Simulate what flutter create would have produced
        project_dir = tmp_path / "MyApp"
        project_dir.mkdir(exist_ok=True)
        (project_dir / "pubspec.yaml").write_text(
            "name: my_app\nflutter:\n  uses-material-design: true\n"
        )
        (project_dir / "ios").mkdir(exist_ok=True)
        (project_dir / "android").mkdir(exist_ok=True)

        # Step 2: append tooling to the newly created project
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.ProjectBootstrap") as mock_bs:
                mock_bs.return_value = MagicMock()
                result = runner.invoke(cli, ["append", "--dir", str(project_dir)])
        assert result.exit_code == 0
        mock_bs.return_value.append_project.assert_called_once()


# ---------------------------------------------------------------------------
# create safeguards
# ---------------------------------------------------------------------------


class TestCreateSafeguards:
    def test_blocks_when_project_dir_already_exists(self, tmp_path: Path) -> None:
        """create refuses to run when <output_dir>/<project_name>/ already exists."""
        runner = CliRunner()
        (tmp_path / "MyApp").mkdir()

        with _patch_config(tmp_path):
            result = runner.invoke(
                cli, ["create", "MyApp", "ios", "--dir", str(tmp_path)]
            )

        assert result.exit_code != 0
        assert "already exists" in result.output
        assert "append" in result.output

    def test_error_message_names_the_directory(self, tmp_path: Path) -> None:
        """The error message includes the conflicting directory name."""
        runner = CliRunner()
        (tmp_path / "CoolProject").mkdir()

        with _patch_config(tmp_path):
            result = runner.invoke(
                cli, ["create", "CoolProject", "ios", "--dir", str(tmp_path)]
            )

        assert "CoolProject" in result.output

    def test_proceeds_when_sibling_dir_exists_but_not_project(
        self, tmp_path: Path
    ) -> None:
        """create proceeds when a different directory exists, not the target one."""
        runner = CliRunner()
        (tmp_path / "OtherApp").mkdir()  # different name, should not block

        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_cls:
                mock_cls.return_value = MagicMock()
                result = runner.invoke(
                    cli,
                    ["create", "MyApp", "ios", "--dir", str(tmp_path)],
                )

        assert result.exit_code == 0

    def test_requires_project_name(self, tmp_path: Path) -> None:
        """create in non-interactive mode without a project name fails."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli._is_interactive", return_value=False):
                result = runner.invoke(cli, ["create", "--dir", str(tmp_path)])
        # Either a non-zero exit or a prompt that needs input
        # In non-interactive mode with no name given this should not exit 0
        # without producing a project (FlutterSetup never called)
        assert result.exit_code != 0 or "Project name" in result.output

    def test_dry_run_does_not_call_flutter_setup(self, tmp_path: Path) -> None:
        """--dry-run exits 0 without invoking FlutterSetup.run."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.FlutterSetup") as mock_cls:
                mock_cls.return_value = MagicMock()
                result = runner.invoke(
                    cli,
                    ["create", "MyApp", "ios", "--dir", str(tmp_path), "--dry-run"],
                )
        assert result.exit_code == 0
        mock_cls.return_value.run.assert_not_called()


# ---------------------------------------------------------------------------
# append safeguards
# ---------------------------------------------------------------------------


class TestAppendSafeguards:
    def test_non_flutter_dir_requires_project_name(self, tmp_path: Path) -> None:
        """append on a non-Flutter directory without a project name fails."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            result = runner.invoke(cli, ["append", "--dir", str(tmp_path)])
        assert result.exit_code != 0
        assert (
            "project_name" in result.output
            or "required" in result.output.lower()
            or "Error" in result.output
        )

    def test_non_flutter_dir_with_project_name_runs_full_setup(
        self, tmp_path: Path
    ) -> None:
        """append on a non-Flutter directory with a name runs FlutterSetup."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli._is_interactive", return_value=False):
                with patch("flutter_setup.cli.FlutterSetup") as mock_cls:
                    mock_cls.return_value = MagicMock()
                    result = runner.invoke(
                        cli, ["append", "MyApp", "--dir", str(tmp_path)]
                    )
        assert result.exit_code == 0
        mock_cls.return_value.run.assert_called_once()

    def test_invalid_platform_name_raises_usage_error(self, tmp_path: Path) -> None:
        """Interactive append with an invalid platform name exits non-zero."""
        runner = CliRunner()
        with _patch_config(tmp_path):
            with patch("flutter_setup.cli._is_interactive", return_value=True):
                result = runner.invoke(
                    cli,
                    ["append", "MyApp", "--dir", str(tmp_path)],
                    input="ios badplatform\n",
                )
        assert result.exit_code != 0
        assert "badplatform" in result.output or "Unknown" in result.output

    def test_force_flag_passes_through_to_bootstrap(self, tmp_path: Path) -> None:
        """--force is forwarded to ProjectBootstrap(force=True)."""
        runner = CliRunner()
        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        (project_dir / "pubspec.yaml").write_text(
            "name: my_app\nflutter:\n  uses-material-design: true\n"
        )

        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.ProjectBootstrap") as mock_bs:
                mock_bs.return_value = MagicMock()
                result = runner.invoke(
                    cli, ["append", "--dir", str(project_dir), "--force"]
                )

        assert result.exit_code == 0
        assert mock_bs.call_args.kwargs["force"] is True

    def test_dry_run_does_not_call_append_project(self, tmp_path: Path) -> None:
        """--dry-run exits 0 without calling bootstrap.append_project."""
        runner = CliRunner()
        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        (project_dir / "pubspec.yaml").write_text(
            "name: my_app\nflutter:\n  uses-material-design: true\n"
        )

        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.ProjectBootstrap") as mock_bs:
                mock_bs.return_value = MagicMock()
                result = runner.invoke(
                    cli, ["append", "--dir", str(project_dir), "--dry-run"]
                )

        assert result.exit_code == 0
        mock_bs.return_value.append_project.assert_not_called()

    def test_append_detects_platforms_from_existing_dirs(self, tmp_path: Path) -> None:
        """Platform detection reads existing ios/android/web subdirectories."""
        runner = CliRunner()
        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        (project_dir / "pubspec.yaml").write_text(
            "name: my_app\nflutter:\n  uses-material-design: true\n"
        )
        (project_dir / "ios").mkdir()
        (project_dir / "web").mkdir()

        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.ProjectBootstrap") as mock_bs:
                mock_bs.return_value = MagicMock()
                runner.invoke(cli, ["append", "--dir", str(project_dir)])

        config = mock_bs.call_args.args[0]
        assert set(config.platforms) == {"ios", "web"}

    def test_append_uses_directory_name_as_project_name(self, tmp_path: Path) -> None:
        """Config.project_name is always the directory name, not the pubspec name."""
        runner = CliRunner()
        project_dir = tmp_path / "my_app_dir"
        project_dir.mkdir()
        (project_dir / "pubspec.yaml").write_text(
            "name: real_package_name\nflutter:\n  uses-material-design: true\n"
        )

        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.ProjectBootstrap") as mock_bs:
                mock_bs.return_value = MagicMock()
                result = runner.invoke(cli, ["append", "--dir", str(project_dir)])

        assert result.exit_code == 0
        assert "my_app_dir" in result.output
        config = mock_bs.call_args.args[0]
        assert config.project_name == "my_app_dir"

    def test_append_org_from_config_file(self, tmp_path: Path) -> None:
        """org is read from the user config file when not passed on CLI."""
        runner = CliRunner()
        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        (project_dir / "pubspec.yaml").write_text(
            "name: my_app\nflutter:\n  uses-material-design: true\n"
        )

        custom_config = {
            "flutter": {"location": str(tmp_path / "flutter_sdk"), "channel": "stable"},
            "project": {"org": "com.customorg"},
        }
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = custom_config
            with patch("flutter_setup.cli.ProjectBootstrap") as mock_bs:
                mock_bs.return_value = MagicMock()
                result = runner.invoke(cli, ["append", "--dir", str(project_dir)])

        assert result.exit_code == 0
        config = mock_bs.call_args.args[0]
        assert config.org == "com.customorg"

    def test_append_passes_patrol_e2e_option(self, tmp_path: Path) -> None:
        """append passes the selected end-to-end framework into bootstrap."""
        runner = CliRunner()
        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        (project_dir / "pubspec.yaml").write_text(
            "name: my_app\nflutter:\n  uses-material-design: true\n"
        )

        with _patch_config(tmp_path):
            with patch("flutter_setup.cli.ProjectBootstrap") as mock_bs:
                mock_bs.return_value = MagicMock()
                result = runner.invoke(
                    cli,
                    [
                        "append",
                        "--dir",
                        str(project_dir),
                        "--e2e-testing",
                        "patrol",
                    ],
                )

        assert result.exit_code == 0
        config = mock_bs.call_args.args[0]
        assert config.e2e_testing == "patrol"


# ---------------------------------------------------------------------------
# README safeguard (bootstrap level)
# ---------------------------------------------------------------------------


class TestReadmeSafeguard:
    def test_create_readme_skips_existing_file(self, tmp_path: Path) -> None:
        """_create_readme does not overwrite an existing README.md."""
        from flutter_setup.bootstrap import ProjectBootstrap
        from flutter_setup.config import Config

        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        readme = project_dir / "README.md"
        readme.write_text("# Original content\n")

        config = Config(
            project_name="MyApp",
            platforms=["ios"],
            org="com.example",
            channel="stable",
            output_dir=tmp_path,
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="skip",
            dry_run=False,
            verbose=False,
            flutter_location=tmp_path / "flutter_sdk",
        )
        bootstrap = ProjectBootstrap(config)
        bootstrap._create_readme()

        assert readme.read_text() == "# Original content\n"

    def test_append_readme_adds_section_without_overwriting(
        self, tmp_path: Path
    ) -> None:
        """_append_readme appends a section and preserves existing content."""
        from flutter_setup.bootstrap import ProjectBootstrap
        from flutter_setup.config import Config

        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        readme = project_dir / "README.md"
        readme.write_text("# My Existing App\n\nSome existing docs.\n")

        config = Config(
            project_name="MyApp",
            platforms=["ios", "android"],
            org="com.example",
            channel="stable",
            output_dir=tmp_path,
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="skip",
            dry_run=False,
            verbose=False,
            flutter_location=tmp_path / "flutter_sdk",
        )
        bootstrap = ProjectBootstrap(config)
        bootstrap._append_readme()

        content = readme.read_text()
        assert "# My Existing App" in content
        assert "## flutter-setup" in content

    def test_append_readme_idempotent(self, tmp_path: Path) -> None:
        """Calling _append_readme twice does not duplicate the section."""
        from flutter_setup.bootstrap import ProjectBootstrap
        from flutter_setup.config import Config

        project_dir = tmp_path / "MyApp"
        project_dir.mkdir()
        readme = project_dir / "README.md"
        readme.write_text("# App\n")

        config = Config(
            project_name="MyApp",
            platforms=["ios"],
            org="com.example",
            channel="stable",
            output_dir=tmp_path,
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="skip",
            dry_run=False,
            verbose=False,
            flutter_location=tmp_path / "flutter_sdk",
        )
        bootstrap = ProjectBootstrap(config)
        bootstrap._append_readme()
        bootstrap._append_readme()

        content = readme.read_text()
        assert content.count("## flutter-setup") == 1


# ---------------------------------------------------------------------------
# Makefile safeguard (bootstrap level)
# ---------------------------------------------------------------------------


class TestMakefileSafeguard:
    def _make_bootstrap(self, tmp_path: Path) -> ProjectBootstrap:
        from flutter_setup.config import Config

        project_dir = tmp_path / "MyApp"
        project_dir.mkdir(exist_ok=True)
        config = Config(
            project_name="MyApp",
            platforms=["ios", "android"],
            org="com.example",
            channel="stable",
            output_dir=tmp_path,
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="skip",
            dry_run=False,
            verbose=False,
            flutter_location=tmp_path / "flutter_sdk",
        )
        return ProjectBootstrap(config)

    def test_append_makefile_creates_when_absent(self, tmp_path: Path) -> None:
        """_append_makefile creates a Makefile when none exists."""
        bootstrap = self._make_bootstrap(tmp_path)
        with patch.object(bootstrap, "_detect_flutter_version", return_value=None):
            bootstrap._append_makefile()
        assert (tmp_path / "MyApp" / "Makefile").exists()

    def test_append_makefile_adds_missing_targets(self, tmp_path: Path) -> None:
        """_append_makefile appends targets absent from the existing Makefile."""
        bootstrap = self._make_bootstrap(tmp_path)
        makefile = tmp_path / "MyApp" / "Makefile"
        makefile.write_text("test:\n\tflutter test\n")

        with patch.object(bootstrap, "_detect_flutter_version", return_value=None):
            bootstrap._append_makefile()

        content = makefile.read_text()
        assert "analyze:" in content

    def test_append_makefile_does_not_duplicate_existing_targets(
        self, tmp_path: Path
    ) -> None:
        """_append_makefile does not re-add targets already in the Makefile."""
        bootstrap = self._make_bootstrap(tmp_path)

        with patch.object(bootstrap, "_detect_flutter_version", return_value=None):
            full = bootstrap._build_makefile_content()

        makefile = tmp_path / "MyApp" / "Makefile"
        makefile.write_text(full)
        original_len = len(full)

        bootstrap2 = self._make_bootstrap(tmp_path)
        with patch.object(bootstrap2, "_detect_flutter_version", return_value=None):
            bootstrap2._append_makefile()

        assert len(makefile.read_text()) == original_len


# ---------------------------------------------------------------------------
# VS Code config safeguard (bootstrap level)
# ---------------------------------------------------------------------------


class TestVscodeConfigSafeguard:
    def _make_bootstrap(self, tmp_path: Path, force: bool = False) -> ProjectBootstrap:
        from flutter_setup.config import Config

        (tmp_path / "MyApp").mkdir(exist_ok=True)
        config = Config(
            project_name="MyApp",
            platforms=["ios"],
            org="com.example",
            channel="stable",
            output_dir=tmp_path,
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="skip",
            dry_run=False,
            verbose=False,
            flutter_location=tmp_path / "flutter_sdk",
        )
        return ProjectBootstrap(config, force=force)

    def test_skips_existing_settings_without_force(self, tmp_path: Path) -> None:
        """Existing settings.json is preserved when force=False."""
        import json

        vscode = tmp_path / "MyApp" / ".vscode"
        vscode.mkdir(parents=True)
        (vscode / "settings.json").write_text('{"existing": true}')
        (vscode / "launch.json").write_text('{"existing": true}')

        self._make_bootstrap(tmp_path, force=False)._append_vscode_config()

        assert json.loads((vscode / "settings.json").read_text()) == {"existing": True}

    def test_overwrites_existing_settings_with_force(self, tmp_path: Path) -> None:
        """Existing settings.json is overwritten when force=True."""
        import json

        vscode = tmp_path / "MyApp" / ".vscode"
        vscode.mkdir(parents=True)
        (vscode / "settings.json").write_text('{"existing": true}')
        (vscode / "launch.json").write_text('{"existing": true}')

        self._make_bootstrap(tmp_path, force=True)._append_vscode_config()

        settings = json.loads((vscode / "settings.json").read_text())
        assert "dart.flutterHotReloadOnSave" in settings

    def test_creates_vscode_dir_when_absent(self, tmp_path: Path) -> None:
        """_append_vscode_config creates .vscode/ when it does not exist."""
        self._make_bootstrap(tmp_path, force=False)._append_vscode_config()
        assert (tmp_path / "MyApp" / ".vscode" / "settings.json").exists()
        assert (tmp_path / "MyApp" / ".vscode" / "launch.json").exists()


# ---------------------------------------------------------------------------
# CI/CD file safeguard (cicd_generator level)
# ---------------------------------------------------------------------------


class TestCicdFileSafeguard:
    def _make_generator(self, tmp_path: Path, force: bool = False) -> CicdGenerator:
        from flutter_setup.config import Config

        config = Config(
            project_name="MyApp",
            platforms=["ios", "android"],
            org="com.example",
            channel="stable",
            output_dir=tmp_path,
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="skip",
            dry_run=False,
            verbose=False,
            flutter_location=tmp_path / "flutter_sdk",
        )
        return CicdGenerator(config, force=force)

    def test_skips_existing_workflow_without_force(self, tmp_path: Path) -> None:
        """An existing workflow file is preserved when force=False."""
        workflow = tmp_path / "existing.yml"
        workflow.write_text("original: true\n")
        gen = self._make_generator(tmp_path, force=False)
        gen._write_workflow_file(workflow, "replaced: true\n")
        assert workflow.read_text() == "original: true\n"

    def test_overwrites_existing_workflow_with_force(self, tmp_path: Path) -> None:
        """An existing workflow file is overwritten when force=True."""
        workflow = tmp_path / "existing.yml"
        workflow.write_text("original: true\n")
        gen = self._make_generator(tmp_path, force=True)
        gen._write_workflow_file(workflow, "replaced: true\n")
        assert workflow.read_text() == "replaced: true\n"

    def test_creates_workflow_file_when_absent(self, tmp_path: Path) -> None:
        """A new workflow file is always created when it does not exist."""
        workflow = tmp_path / "new.yml"
        gen = self._make_generator(tmp_path, force=False)
        gen._write_workflow_file(workflow, "content: true\n")
        assert workflow.read_text() == "content: true\n"
