"""Tests for the appender module and append-related bootstrap functionality."""

import json
from pathlib import Path
from unittest.mock import patch

from flutter_setup.appender import (
    detect_flutter_project,
    detect_platforms,
    get_pubspec_name,
)
from flutter_setup.bootstrap import (
    ProjectBootstrap,
    _extract_makefile_target_names,
    _filter_new_makefile_content,
)
from flutter_setup.config import Config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(tmp_path: Path, project_name: str = "myapp") -> Config:
    """Return a minimal Config rooted at tmp_path."""
    return Config(
        project_name=project_name,
        platforms=["ios", "android", "web"],
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


# ---------------------------------------------------------------------------
# detect_flutter_project
# ---------------------------------------------------------------------------


class TestDetectFlutterProject:
    def test_returns_true_when_pubspec_has_flutter_key(self, tmp_path: Path) -> None:
        pubspec = tmp_path / "pubspec.yaml"
        pubspec.write_text("name: myapp\nflutter:\n  uses-material-design: true\n")
        assert detect_flutter_project(tmp_path) is True

    def test_returns_false_when_pubspec_missing_flutter_key(
        self, tmp_path: Path
    ) -> None:
        pubspec = tmp_path / "pubspec.yaml"
        pubspec.write_text("name: myapp\ndependencies:\n  yaml: ^3.0.0\n")
        assert detect_flutter_project(tmp_path) is False

    def test_returns_false_when_no_pubspec(self, tmp_path: Path) -> None:
        assert detect_flutter_project(tmp_path) is False

    def test_returns_false_on_malformed_yaml(self, tmp_path: Path) -> None:
        pubspec = tmp_path / "pubspec.yaml"
        pubspec.write_text(": : : invalid yaml ::: {{{")
        assert detect_flutter_project(tmp_path) is False

    def test_returns_false_when_pubspec_is_not_a_dict(self, tmp_path: Path) -> None:
        pubspec = tmp_path / "pubspec.yaml"
        pubspec.write_text("- item1\n- item2\n")
        assert detect_flutter_project(tmp_path) is False


# ---------------------------------------------------------------------------
# detect_platforms
# ---------------------------------------------------------------------------


class TestDetectPlatforms:
    def test_detects_ios_only(self, tmp_path: Path) -> None:
        (tmp_path / "ios").mkdir()
        result = detect_platforms(tmp_path)
        assert result == ["ios"]

    def test_detects_multiple_platforms(self, tmp_path: Path) -> None:
        for d in ["ios", "android", "web"]:
            (tmp_path / d).mkdir()
        result = detect_platforms(tmp_path)
        assert set(result) == {"ios", "android", "web"}

    def test_falls_back_when_no_platform_dirs(self, tmp_path: Path) -> None:
        result = detect_platforms(tmp_path)
        assert result == ["ios", "android", "web"]

    def test_detects_macos_linux_windows(self, tmp_path: Path) -> None:
        for d in ["macos", "linux", "windows"]:
            (tmp_path / d).mkdir()
        result = detect_platforms(tmp_path)
        assert set(result) == {"macos", "linux", "windows"}

    def test_detects_all_platforms(self, tmp_path: Path) -> None:
        for d in ["ios", "android", "web", "macos", "linux", "windows"]:
            (tmp_path / d).mkdir()
        result = detect_platforms(tmp_path)
        assert set(result) == {"ios", "android", "web", "macos", "linux", "windows"}


# ---------------------------------------------------------------------------
# get_pubspec_name
# ---------------------------------------------------------------------------


class TestGetPubspecName:
    def test_returns_name_from_pubspec(self, tmp_path: Path) -> None:
        pubspec = tmp_path / "pubspec.yaml"
        pubspec.write_text("name: my_flutter_app\nversion: 1.0.0\n")
        assert get_pubspec_name(tmp_path) == "my_flutter_app"

    def test_returns_none_when_pubspec_missing(self, tmp_path: Path) -> None:
        assert get_pubspec_name(tmp_path) is None

    def test_returns_none_on_malformed_yaml(self, tmp_path: Path) -> None:
        pubspec = tmp_path / "pubspec.yaml"
        pubspec.write_text(": : invalid :")
        assert get_pubspec_name(tmp_path) is None

    def test_returns_none_when_name_key_absent(self, tmp_path: Path) -> None:
        pubspec = tmp_path / "pubspec.yaml"
        pubspec.write_text("version: 1.0.0\n")
        assert get_pubspec_name(tmp_path) is None

    def test_returns_none_when_pubspec_not_a_dict(self, tmp_path: Path) -> None:
        pubspec = tmp_path / "pubspec.yaml"
        pubspec.write_text("- a\n- b\n")
        assert get_pubspec_name(tmp_path) is None


# ---------------------------------------------------------------------------
# _extract_makefile_target_names
# ---------------------------------------------------------------------------


class TestExtractMakefileTargetNames:
    def test_extracts_simple_targets(self) -> None:
        content = "test:\n\tflutter test\n\nanalyze:\n\tflutter analyze\n"
        result = _extract_makefile_target_names(content)
        assert "test" in result
        assert "analyze" in result

    def test_excludes_phony(self) -> None:
        content = ".PHONY: test analyze\ntest:\n\tflutter test\n"
        result = _extract_makefile_target_names(content)
        assert ".PHONY" not in result
        assert "test" in result

    def test_extracts_hyphenated_targets(self) -> None:
        content = (
            "run-ios:\n\tflutter run -d ios\n\nrun-android:\n\tflutter run -d android\n"
        )
        result = _extract_makefile_target_names(content)
        assert "run-ios" in result
        assert "run-android" in result

    def test_empty_content(self) -> None:
        assert _extract_makefile_target_names("") == set()

    def test_ignores_variable_assignments(self) -> None:
        content = "FLUTTER := flutter\ntest:\n\t$(FLUTTER) test\n"
        result = _extract_makefile_target_names(content)
        assert "FLUTTER" not in result
        assert "test" in result


# ---------------------------------------------------------------------------
# _filter_new_makefile_content
# ---------------------------------------------------------------------------


class TestFilterNewMakefileContent:
    def test_filters_out_existing_targets(self) -> None:
        new_content = "test:\n\tflutter test\n\nanalyze:\n\tflutter analyze\n"
        existing = {"test"}
        result = _filter_new_makefile_content(new_content, existing)
        assert "analyze:" in result
        assert "test:" not in result

    def test_returns_all_when_no_overlap(self) -> None:
        new_content = "test:\n\tflutter test\n\nanalyze:\n\tflutter analyze\n"
        existing: set[str] = set()
        result = _filter_new_makefile_content(new_content, existing)
        assert "test:" in result
        assert "analyze:" in result

    def test_returns_empty_when_all_existing(self) -> None:
        new_content = "test:\n\tflutter test\n\nanalyze:\n\tflutter analyze\n"
        existing = {"test", "analyze"}
        result = _filter_new_makefile_content(new_content, existing)
        assert result.strip() == ""

    def test_preserves_target_body(self) -> None:
        new_content = "run-ios:\n\tflutter run -d ios\n\ntest:\n\tflutter test\n"
        existing = {"test"}
        result = _filter_new_makefile_content(new_content, existing)
        assert "flutter run -d ios" in result

    def test_includes_missing_preamble_variables(self) -> None:
        new_content = "FLUTTER := flutter\n\ntest:\n\tflutter test\n"
        existing_targets: set[str] = set()
        existing_content = "# My Makefile\n"
        result = _filter_new_makefile_content(
            new_content, existing_targets, existing_content
        )
        assert "FLUTTER :=" in result
        assert "test:" in result

    def test_skips_already_defined_preamble_variables(self) -> None:
        new_content = "FLUTTER := flutter\n\ntest:\n\tflutter test\n"
        existing_targets: set[str] = set()
        existing_content = "FLUTTER := /usr/local/flutter/bin/flutter\n"
        result = _filter_new_makefile_content(
            new_content, existing_targets, existing_content
        )
        assert "FLUTTER :=" not in result
        assert "test:" in result

    def test_includes_only_missing_variables_from_preamble(self) -> None:
        new_content = (
            "FLUTTER_HOME := /flutter\nFLUTTER := flutter\n\ntest:\n\t$(FLUTTER) test\n"
        )
        existing_targets: set[str] = set()
        existing_content = "FLUTTER_HOME := /other/flutter\n"
        result = _filter_new_makefile_content(
            new_content, existing_targets, existing_content
        )
        assert "FLUTTER_HOME" not in result
        assert "FLUTTER :=" in result
        assert "test:" in result


# ---------------------------------------------------------------------------
# ProjectBootstrap.append_project
# ---------------------------------------------------------------------------


class TestAppendProject:
    def test_append_project_dry_run(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        config.dry_run = True
        bootstrap = ProjectBootstrap(config, force=False)
        # Should not call any of the sub-methods in dry_run mode
        with patch.object(bootstrap, "_append_vscode_config") as mock_vscode:
            with patch.object(bootstrap, "_append_makefile") as mock_makefile:
                with patch.object(bootstrap, "_create_cicd") as mock_cicd:
                    bootstrap.append_project()
                    mock_vscode.assert_not_called()
                    mock_makefile.assert_not_called()
                    mock_cicd.assert_not_called()

    def test_append_project_calls_sub_methods(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        bootstrap = ProjectBootstrap(config, force=False)
        with patch.object(bootstrap, "_append_vscode_config") as mock_vscode:
            with patch.object(bootstrap, "_append_makefile") as mock_makefile:
                with patch.object(bootstrap, "_create_cicd") as mock_cicd:
                    bootstrap.append_project()
                    mock_vscode.assert_called_once()
                    mock_makefile.assert_called_once()
                    mock_cicd.assert_called_once()

    def test_append_vscode_config_skips_existing_without_force(
        self, tmp_path: Path
    ) -> None:
        config = _make_config(tmp_path)
        project_dir = tmp_path / "myapp"
        project_dir.mkdir()
        vscode_dir = project_dir / ".vscode"
        vscode_dir.mkdir()
        # Pre-create settings.json
        (vscode_dir / "settings.json").write_text('{"existing": true}')
        (vscode_dir / "launch.json").write_text('{"existing": true}')

        bootstrap = ProjectBootstrap(config, force=False)
        bootstrap._append_vscode_config()

        # Files should be unchanged
        assert json.loads((vscode_dir / "settings.json").read_text()) == {
            "existing": True
        }
        assert json.loads((vscode_dir / "launch.json").read_text()) == {
            "existing": True
        }

    def test_append_vscode_config_overwrites_with_force(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        project_dir = tmp_path / "myapp"
        project_dir.mkdir()
        vscode_dir = project_dir / ".vscode"
        vscode_dir.mkdir()
        (vscode_dir / "settings.json").write_text('{"existing": true}')
        (vscode_dir / "launch.json").write_text('{"existing": true}')

        bootstrap = ProjectBootstrap(config, force=True)
        bootstrap._append_vscode_config()

        settings = json.loads((vscode_dir / "settings.json").read_text())
        assert "dart.flutterHotReloadOnSave" in settings

        launch = json.loads((vscode_dir / "launch.json").read_text())
        assert "configurations" in launch

    def test_append_vscode_config_creates_when_absent(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        project_dir = tmp_path / "myapp"
        project_dir.mkdir()

        bootstrap = ProjectBootstrap(config, force=False)
        bootstrap._append_vscode_config()

        vscode_dir = project_dir / ".vscode"
        assert (vscode_dir / "settings.json").exists()
        assert (vscode_dir / "launch.json").exists()

    def test_append_makefile_creates_when_absent(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        project_dir = tmp_path / "myapp"
        project_dir.mkdir()

        bootstrap = ProjectBootstrap(config, force=False)
        with patch.object(bootstrap, "_detect_flutter_version", return_value=None):
            bootstrap._append_makefile()

        assert (project_dir / "Makefile").exists()

    def test_append_makefile_appends_missing_targets(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        project_dir = tmp_path / "myapp"
        project_dir.mkdir()
        # Pre-create a Makefile with only 'test'
        (project_dir / "Makefile").write_text("test:\n\tflutter test\n")

        bootstrap = ProjectBootstrap(config, force=False)
        with patch.object(bootstrap, "_detect_flutter_version", return_value=None):
            bootstrap._append_makefile()

        content = (project_dir / "Makefile").read_text()
        # 'test' already existed — should only appear once (original + possibly appended block without it)
        # 'analyze' was NOT in the original, so it should be appended
        assert "analyze:" in content

    def test_append_makefile_no_op_when_all_targets_exist(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path)
        project_dir = tmp_path / "myapp"
        project_dir.mkdir()

        bootstrap = ProjectBootstrap(config, force=False)
        with patch.object(bootstrap, "_detect_flutter_version", return_value=None):
            # Build the full content and use it as the pre-existing Makefile
            full_content = bootstrap._build_makefile_content()

        (project_dir / "Makefile").write_text(full_content)
        original_size = len(full_content)

        bootstrap2 = ProjectBootstrap(config, force=False)
        with patch.object(bootstrap2, "_detect_flutter_version", return_value=None):
            bootstrap2._append_makefile()

        final_content = (project_dir / "Makefile").read_text()
        # Content should not grow (no new targets to add)
        assert len(final_content) == original_size
