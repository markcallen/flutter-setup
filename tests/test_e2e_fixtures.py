"""Integration tests using the real fixture projects in e2e/.

Each test copies a fixture to a fresh temp directory, then exercises the real
bootstrap or CLI code paths.  Only the subprocess calls that require an
installed Flutter SDK are patched out — all file reads, writes, and directory
creation run against the real filesystem.

Fixtures
--------
* e2e/photo_slideshow  – partially built Flutter app (has pubspec.yaml / lib/)
  → exercises ``append_project()``

* e2e/shopping_list    – documentation-only directory (no Flutter files)
  → exercises CLI-level ``create`` and ``append`` routing
"""

import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import patch

import pytest
import yaml
from click.testing import CliRunner

from flutter_setup.bootstrap import ProjectBootstrap
from flutter_setup.cli import cli
from flutter_setup.config import Config

E2E_DIR = Path(__file__).parent.parent / "e2e"


# ---------------------------------------------------------------------------
# pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def photo_slideshow(tmp_path: Path) -> Path:
    """Fresh copy of e2e/photo_slideshow in a temp directory."""
    dst = tmp_path / "photo_slideshow"
    shutil.copytree(E2E_DIR / "photo_slideshow", dst)
    return dst


@pytest.fixture
def shopping_list(tmp_path: Path) -> Path:
    """Fresh copy of e2e/shopping_list in a temp directory."""
    dst = tmp_path / "shopping_list"
    shutil.copytree(E2E_DIR / "shopping_list", dst)
    return dst


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_config(project_dir: Path, **overrides: Any) -> Config:
    """Minimal Config for append_project on a real directory."""
    defaults: dict[str, Any] = dict(
        project_name=project_dir.name,
        platforms=["ios", "android"],
        org="com.example",
        channel="stable",
        output_dir=project_dir.parent,
        template="app",
        ios_language="swift",
        android_language="kotlin",
        flutter_update_mode="skip",
        dry_run=False,
        verbose=False,
        flutter_location=project_dir.parent / "flutter_sdk",
    )
    defaults.update(overrides)
    return Config(**defaults)


@contextmanager
def _no_flutter_sdk() -> Iterator[None]:
    """Suppress subprocess calls that require an installed Flutter SDK.

    Patches:
    * ProjectBootstrap._detect_flutter_version – used by _build_makefile_content
    * CicdGenerator subprocess.run            – used to detect Flutter version
    """
    with (
        patch(
            "flutter_setup.bootstrap.ProjectBootstrap._detect_flutter_version",
            return_value="3.24.0",
        ),
        patch("flutter_setup.cicd_generator.subprocess.run"),
    ):
        yield


def _cli_config(sdk_parent: Path) -> dict[str, Any]:
    return {
        "flutter": {
            "location": str(sdk_parent / "flutter_sdk"),
            "channel": "stable",
        },
        "project": {"org": "com.example"},
    }


# ---------------------------------------------------------------------------
# Bootstrap-level: real append_project() on the photo_slideshow fixture
# ---------------------------------------------------------------------------


class TestPhotoSlideshowAppend:
    """Calls real ProjectBootstrap.append_project() on the photo_slideshow fixture.

    No CLI layer — tests the bootstrap API directly so failures point straight
    at the responsible method.
    """

    def _run(self, project_dir: Path, *, force: bool = False, **overrides: Any) -> None:
        bootstrap = ProjectBootstrap(
            _make_config(project_dir, **overrides), force=force
        )
        with _no_flutter_sdk():
            bootstrap.append_project()

    # --- files that must be created -----------------------------------------

    def test_creates_makefile(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        assert (photo_slideshow / "Makefile").exists()

    def test_makefile_contains_test_target(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        makefile = (photo_slideshow / "Makefile").read_text()
        assert "test:" in makefile

    def test_makefile_contains_build_target(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        makefile = (photo_slideshow / "Makefile").read_text()
        assert "build" in makefile

    def test_creates_vscode_settings(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        assert (photo_slideshow / ".vscode" / "settings.json").exists()

    def test_vscode_settings_contains_dart_config(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        content = (photo_slideshow / ".vscode" / "settings.json").read_text()
        assert "dart" in content.lower()

    def test_creates_vscode_launch(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        assert (photo_slideshow / ".vscode" / "launch.json").exists()

    def test_creates_github_workflows_directory(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        assert (photo_slideshow / ".github" / "workflows").is_dir()

    def test_creates_workflow_yml_files(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        workflows = list((photo_slideshow / ".github" / "workflows").glob("*.yml"))
        assert len(workflows) >= 1

    def test_creates_dependabot_config(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        assert (photo_slideshow / ".github" / "dependabot.yml").exists()

    def test_appends_flutter_setup_section_to_readme(
        self, photo_slideshow: Path
    ) -> None:
        self._run(photo_slideshow)
        readme = (photo_slideshow / "README.md").read_text()
        assert "## flutter-setup" in readme

    def test_append_patrol_e2e_scaffold(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow, e2e_testing="patrol")

        patrol_test = photo_slideshow / "patrol_test" / "app_test.dart"
        assert patrol_test.exists()
        assert "patrolTest" in patrol_test.read_text()

        pubspec = yaml.safe_load((photo_slideshow / "pubspec.yaml").read_text())
        assert pubspec["dev_dependencies"]["patrol"] == "any"
        assert (
            pubspec["patrol"]["android"]["package_name"]
            == "com.example.photo_slideshow"
        )

        makefile = (photo_slideshow / "Makefile").read_text()
        assert "patrol-test:" in makefile
        assert "patrol-doctor:" in makefile

    # --- existing files that must not be touched ----------------------------

    def test_preserves_pubspec_yaml(self, photo_slideshow: Path) -> None:
        original = (photo_slideshow / "pubspec.yaml").read_text()
        self._run(photo_slideshow)
        assert (photo_slideshow / "pubspec.yaml").read_text() == original

    def test_preserves_main_dart(self, photo_slideshow: Path) -> None:
        original = (photo_slideshow / "lib" / "main.dart").read_text()
        self._run(photo_slideshow)
        assert (photo_slideshow / "lib" / "main.dart").read_text() == original

    def test_preserves_album_model(self, photo_slideshow: Path) -> None:
        original = (photo_slideshow / "lib" / "models" / "album.dart").read_text()
        self._run(photo_slideshow)
        assert (
            photo_slideshow / "lib" / "models" / "album.dart"
        ).read_text() == original

    def test_preserves_slideshow_screen(self, photo_slideshow: Path) -> None:
        original = (
            photo_slideshow / "lib" / "screens" / "slideshow_screen.dart"
        ).read_text()
        self._run(photo_slideshow)
        assert (
            photo_slideshow / "lib" / "screens" / "slideshow_screen.dart"
        ).read_text() == original

    def test_preserves_existing_test_file(self, photo_slideshow: Path) -> None:
        original = (photo_slideshow / "test" / "album_test.dart").read_text()
        self._run(photo_slideshow)
        assert (photo_slideshow / "test" / "album_test.dart").read_text() == original

    def test_existing_readme_content_kept_at_top(self, photo_slideshow: Path) -> None:
        original_first_line = (
            (photo_slideshow / "README.md").read_text().splitlines()[0]
        )
        self._run(photo_slideshow)
        assert (
            (photo_slideshow / "README.md").read_text().startswith(original_first_line)
        )

    # --- force / no-force safeguards ----------------------------------------

    def test_skips_existing_vscode_settings_without_force(
        self, photo_slideshow: Path
    ) -> None:
        settings = photo_slideshow / ".vscode" / "settings.json"
        settings.parent.mkdir()
        settings.write_text('{"sentinel": true}')

        self._run(photo_slideshow, force=False)

        assert settings.read_text() == '{"sentinel": true}'

    def test_skips_existing_vscode_launch_without_force(
        self, photo_slideshow: Path
    ) -> None:
        vscode = photo_slideshow / ".vscode"
        vscode.mkdir()
        (vscode / "launch.json").write_text('{"version": "custom"}')

        self._run(photo_slideshow, force=False)

        assert (vscode / "launch.json").read_text() == '{"version": "custom"}'

    def test_overwrites_vscode_settings_with_force(self, photo_slideshow: Path) -> None:
        settings = photo_slideshow / ".vscode" / "settings.json"
        settings.parent.mkdir()
        settings.write_text('{"sentinel": true}')

        self._run(photo_slideshow, force=True)

        new = settings.read_text()
        assert '"sentinel"' not in new
        assert "dart" in new.lower()

    def test_skips_existing_ci_workflow_without_force(
        self, photo_slideshow: Path
    ) -> None:
        workflows = photo_slideshow / ".github" / "workflows"
        workflows.mkdir(parents=True)
        lint = workflows / "lint.yml"
        lint.write_text("# custom lint workflow\n")

        self._run(photo_slideshow, force=False)

        assert lint.read_text() == "# custom lint workflow\n"

    def test_overwrites_existing_ci_workflow_with_force(
        self, photo_slideshow: Path
    ) -> None:
        workflows = photo_slideshow / ".github" / "workflows"
        workflows.mkdir(parents=True)
        lint = workflows / "lint.yml"
        lint.write_text("# custom lint workflow\n")

        self._run(photo_slideshow, force=True)

        assert lint.read_text() != "# custom lint workflow\n"

    # --- idempotency --------------------------------------------------------

    def test_makefile_idempotent_on_second_run(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        after_first = (photo_slideshow / "Makefile").read_text()
        self._run(photo_slideshow)
        assert (photo_slideshow / "Makefile").read_text() == after_first

    def test_readme_idempotent_on_second_run(self, photo_slideshow: Path) -> None:
        self._run(photo_slideshow)
        after_first = (photo_slideshow / "README.md").read_text()
        self._run(photo_slideshow)
        assert (photo_slideshow / "README.md").read_text() == after_first

    def test_flutter_setup_readme_section_appears_exactly_once(
        self, photo_slideshow: Path
    ) -> None:
        self._run(photo_slideshow)
        self._run(photo_slideshow)
        readme = (photo_slideshow / "README.md").read_text()
        assert readme.count("## flutter-setup") == 1


# ---------------------------------------------------------------------------
# CLI-level: full chain CLI → real bootstrap → real filesystem
# ---------------------------------------------------------------------------


class TestPhotoSlideshowAppendCLI:
    """Invokes the CLI through CliRunner on the photo_slideshow fixture.

    Only ConfigManager and Flutter SDK subprocess calls are patched; all
    bootstrap file operations run against the real temp directory.
    """

    def _invoke(self, project_dir: Path, *extra: str) -> Any:
        runner = CliRunner()
        with (
            patch("flutter_setup.cli.ConfigManager") as mock_cm,
            _no_flutter_sdk(),
        ):
            mock_cm.return_value.load_config.return_value = _cli_config(
                project_dir.parent
            )
            return runner.invoke(cli, ["append", "--dir", str(project_dir), *extra])

    def test_exits_zero(self, photo_slideshow: Path) -> None:
        result = self._invoke(photo_slideshow)
        assert result.exit_code == 0, result.output

    def test_creates_makefile(self, photo_slideshow: Path) -> None:
        self._invoke(photo_slideshow)
        assert (photo_slideshow / "Makefile").exists()

    def test_creates_vscode_settings(self, photo_slideshow: Path) -> None:
        self._invoke(photo_slideshow)
        assert (photo_slideshow / ".vscode" / "settings.json").exists()

    def test_creates_github_workflows(self, photo_slideshow: Path) -> None:
        self._invoke(photo_slideshow)
        assert (photo_slideshow / ".github" / "workflows").is_dir()

    def test_preserves_pubspec_yaml(self, photo_slideshow: Path) -> None:
        original = (photo_slideshow / "pubspec.yaml").read_text()
        self._invoke(photo_slideshow)
        assert (photo_slideshow / "pubspec.yaml").read_text() == original

    def test_preserves_all_dart_source_files(self, photo_slideshow: Path) -> None:
        snapshots = {
            p: p.read_text() for p in (photo_slideshow / "lib").rglob("*.dart")
        }
        self._invoke(photo_slideshow)
        for path, original in snapshots.items():
            assert (
                path.read_text() == original
            ), f"{path.name} was unexpectedly modified"

    def test_generates_ios_build_workflow(self, photo_slideshow: Path) -> None:
        """photo_slideshow has an ios/ dir so an iOS workflow must be created."""
        self._invoke(photo_slideshow)
        workflows = {
            p.name for p in (photo_slideshow / ".github" / "workflows").glob("*.yml")
        }
        assert any("ios" in w for w in workflows)

    def test_generates_android_build_workflow(self, photo_slideshow: Path) -> None:
        """photo_slideshow has an android/ dir so an Android workflow must be created."""
        self._invoke(photo_slideshow)
        workflows = {
            p.name for p in (photo_slideshow / ".github" / "workflows").glob("*.yml")
        }
        assert any("android" in w for w in workflows)

    def test_dry_run_leaves_filesystem_unchanged(self, photo_slideshow: Path) -> None:
        before = {
            str(p.relative_to(photo_slideshow)) for p in photo_slideshow.rglob("*")
        }
        result = self._invoke(photo_slideshow, "--dry-run")
        assert result.exit_code == 0
        after = {
            str(p.relative_to(photo_slideshow)) for p in photo_slideshow.rglob("*")
        }
        assert before == after

    def test_force_overwrites_existing_vscode_settings(
        self, photo_slideshow: Path
    ) -> None:
        settings = photo_slideshow / ".vscode" / "settings.json"
        settings.parent.mkdir()
        settings.write_text('{"sentinel": true}')

        self._invoke(photo_slideshow, "--force")

        assert '"sentinel"' not in settings.read_text()

    def test_without_force_preserves_existing_vscode_settings(
        self, photo_slideshow: Path
    ) -> None:
        settings = photo_slideshow / ".vscode" / "settings.json"
        settings.parent.mkdir()
        settings.write_text('{"sentinel": true}')

        self._invoke(photo_slideshow)

        assert settings.read_text() == '{"sentinel": true}'

    def test_second_invocation_is_idempotent(self, photo_slideshow: Path) -> None:
        self._invoke(photo_slideshow)
        snapshot = {p: p.read_text() for p in photo_slideshow.rglob("*") if p.is_file()}
        self._invoke(photo_slideshow)
        for path, content in snapshot.items():
            assert path.read_text() == content, f"{path.name} changed on second run"


# ---------------------------------------------------------------------------
# CLI-level: shopping_list fixture (docs-only, no pubspec.yaml)
# ---------------------------------------------------------------------------


class TestShoppingListCLI:
    """Tests CLI routing decisions when the target directory has no Flutter project."""

    def _base_config(self, parent: Path) -> dict[str, Any]:
        return _cli_config(parent)

    def test_create_blocks_when_directory_exists(self, shopping_list: Path) -> None:
        """flutter-setup create must refuse because shopping_list/ already exists."""
        runner = CliRunner()
        parent = shopping_list.parent
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config(parent)
            result = runner.invoke(
                cli,
                [
                    "create",
                    "shopping_list",
                    "--platforms",
                    "ios",
                    "--platforms",
                    "android",
                    "--dir",
                    str(parent),
                ],
            )
        assert result.exit_code != 0
        assert "shopping_list" in result.output
        assert "append" in result.output.lower()

    def test_create_error_message_names_the_existing_directory(
        self, shopping_list: Path
    ) -> None:
        runner = CliRunner()
        parent = shopping_list.parent
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config(parent)
            result = runner.invoke(
                cli,
                ["create", "shopping_list", "--platforms", "ios", "--dir", str(parent)],
            )
        assert "shopping_list" in result.output

    def test_append_without_project_name_fails(self, shopping_list: Path) -> None:
        """append on a non-Flutter dir must require a project name."""
        runner = CliRunner()
        with patch("flutter_setup.cli.ConfigManager") as mock_cm:
            mock_cm.return_value.load_config.return_value = self._base_config(
                shopping_list.parent
            )
            result = runner.invoke(cli, ["append", "--dir", str(shopping_list)])
        assert result.exit_code != 0

    def test_append_with_project_name_calls_flutter_setup(
        self, shopping_list: Path
    ) -> None:
        """append with a name on a non-Flutter dir must run the full setup."""
        runner = CliRunner()
        with (
            patch("flutter_setup.cli.ConfigManager") as mock_cm,
            patch("flutter_setup.cli._is_interactive", return_value=False),
            patch("flutter_setup.cli.FlutterSetup") as mock_setup,
        ):
            mock_cm.return_value.load_config.return_value = self._base_config(
                shopping_list.parent
            )
            mock_setup.return_value.run.return_value = None
            result = runner.invoke(
                cli,
                ["append", "shopping_list", "--dir", str(shopping_list.parent)],
            )
        assert result.exit_code == 0
        mock_setup.return_value.run.assert_called_once()

    def test_append_non_flutter_preserves_existing_docs(
        self, shopping_list: Path
    ) -> None:
        """The design docs must survive even when FlutterSetup.run is called."""
        readme_before = (shopping_list / "README.md").read_text()
        prd_before = (shopping_list / "PRD.md").read_text()

        runner = CliRunner()
        with (
            patch("flutter_setup.cli.ConfigManager") as mock_cm,
            patch("flutter_setup.cli._is_interactive", return_value=False),
            patch("flutter_setup.cli.FlutterSetup"),
        ):
            mock_cm.return_value.load_config.return_value = self._base_config(
                shopping_list.parent
            )
            runner.invoke(
                cli,
                ["append", "shopping_list", "--dir", str(shopping_list.parent)],
            )

        assert (shopping_list / "README.md").read_text() == readme_before
        assert (shopping_list / "PRD.md").read_text() == prd_before

    def test_create_succeeds_for_different_project_name_in_same_parent(
        self, shopping_list: Path
    ) -> None:
        """create must work when only the sibling shopping_list dir exists."""
        runner = CliRunner()
        parent = shopping_list.parent
        with (
            patch("flutter_setup.cli.ConfigManager") as mock_cm,
            patch("flutter_setup.cli.FlutterSetup") as mock_setup,
        ):
            mock_cm.return_value.load_config.return_value = self._base_config(parent)
            mock_setup.return_value.run.return_value = None
            result = runner.invoke(
                cli,
                [
                    "create",
                    "recipe_app",
                    "--platforms",
                    "ios",
                    "--platforms",
                    "android",
                    "--dir",
                    str(parent),
                ],
            )
        assert result.exit_code == 0
        mock_setup.return_value.run.assert_called_once()
