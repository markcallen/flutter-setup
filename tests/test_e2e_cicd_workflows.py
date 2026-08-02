"""E2E tests verifying that generated GitHub Actions workflows are structurally valid.

These tests drive CicdGenerator directly, parse the produced YAML files, and
assert the properties that matter for a CI run to succeed on GitHub Actions:
- jobs that post PR comments carry `permissions: issues: write`
- `build_runner` never runs in the lint workflow (it fails when source_gen is
  incompatible with the Flutter-bundled analyzer, as seen in practice)
- `build_runner` still runs in test/build workflows for sqlite projects
- every workflow that can post a PR comment uses `continue-on-error` or the
  permissions block so the check step doesn't mask the real failure
"""

from pathlib import Path
from typing import Any, Literal
from unittest.mock import patch

import pytest
import yaml

from flutter_setup.cicd_generator import CicdGenerator
from flutter_setup.config import Config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    database: Literal["none", "sqlite"] = "none",
    platforms: list[str] | None = None,
) -> Config:
    return Config(
        project_name="TestApp",
        platforms=platforms or ["android", "ios"],
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
        database=database,
    )


def _generate_workflows(config: Config, tmp_path: Path) -> dict[str, dict[str, Any]]:
    """Generate all workflows and return parsed YAML keyed by filename."""
    config.output_dir = tmp_path
    config.project_path.mkdir(parents=True, exist_ok=True)
    with patch.object(
        CicdGenerator, "_get_current_flutter_version", return_value="3.24.0"
    ):
        generator = CicdGenerator(config)
        generator.generate_cicd()
    workflows_dir = config.project_path / ".github" / "workflows"
    return {
        wf.name: yaml.safe_load(wf.read_text())
        for wf in sorted(workflows_dir.glob("*.yml"))
    }


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------


class TestWorkflowPermissions:
    """Jobs that post PR comments must carry issues: write."""

    def test_lint_job_has_required_permissions(self, tmp_path: Path) -> None:
        workflows = _generate_workflows(_make_config(), tmp_path)
        perms = workflows["lint.yml"]["jobs"]["lint"].get("permissions", {})
        assert (
            perms.get("issues") == "write"
        ), "lint job must grant issues: write so PR comment step works"
        assert perms.get("contents") == "read", (
            "lint job must grant contents: read — setting any job permission "
            "drops all others to none, which breaks actions/checkout"
        )

    def test_format_job_has_required_permissions(self, tmp_path: Path) -> None:
        workflows = _generate_workflows(_make_config(), tmp_path)
        perms = workflows["format.yml"]["jobs"]["format"].get("permissions", {})
        assert (
            perms.get("issues") == "write"
        ), "format job must grant issues: write so PR comment step works"
        assert (
            perms.get("contents") == "read"
        ), "format job must grant contents: read so actions/checkout can clone"

    def test_permissions_present_for_sqlite_project(self, tmp_path: Path) -> None:
        workflows = _generate_workflows(_make_config(database="sqlite"), tmp_path)
        for wf_name in ("lint.yml", "format.yml"):
            job_key = wf_name.replace(".yml", "")
            perms = workflows[wf_name]["jobs"][job_key].get("permissions", {})
            assert (
                perms.get("issues") == "write"
            ), f"{wf_name} sqlite project must still have issues: write"
            assert (
                perms.get("contents") == "read"
            ), f"{wf_name} sqlite project must still have contents: read"


# ---------------------------------------------------------------------------
# build_runner placement
# ---------------------------------------------------------------------------


class TestBuildRunnerPlacement:
    """build_runner must never appear in lint; it must appear in test/build for sqlite."""

    def _step_names(self, job: dict[str, Any]) -> list[str]:
        return [s.get("name", "") for s in job.get("steps", [])]

    def _has_build_runner(self, job: dict[str, Any]) -> bool:
        return any("build_runner" in s.get("run", "") for s in job.get("steps", []))

    def test_lint_never_runs_build_runner(self, tmp_path: Path) -> None:
        workflows = _generate_workflows(_make_config(database="none"), tmp_path)
        assert not self._has_build_runner(workflows["lint.yml"]["jobs"]["lint"])

    def test_lint_never_runs_build_runner_even_for_sqlite(self, tmp_path: Path) -> None:
        """flutter analyze doesn't need generated code; build_runner here breaks when
        source_gen is incompatible with the Flutter-bundled analyzer version."""
        workflows = _generate_workflows(_make_config(database="sqlite"), tmp_path)
        assert not self._has_build_runner(workflows["lint.yml"]["jobs"]["lint"]), (
            "lint must not call build_runner — source_gen version mismatches "
            "cause spurious CI failures independent of lint correctness"
        )

    def test_test_workflow_runs_build_runner_for_sqlite(self, tmp_path: Path) -> None:
        workflows = _generate_workflows(_make_config(database="sqlite"), tmp_path)
        assert self._has_build_runner(
            workflows["test.yml"]["jobs"]["test"]
        ), "test workflow must generate code for sqlite projects before running tests"

    def test_test_workflow_skips_build_runner_for_non_sqlite(
        self, tmp_path: Path
    ) -> None:
        workflows = _generate_workflows(_make_config(database="none"), tmp_path)
        assert not self._has_build_runner(workflows["test.yml"]["jobs"]["test"])

    def test_build_workflows_run_build_runner_for_sqlite(self, tmp_path: Path) -> None:
        workflows = _generate_workflows(
            _make_config(database="sqlite", platforms=["android", "ios"]), tmp_path
        )
        for wf_name in ("build-android.yml", "build-ios.yml"):
            job_key = next(iter(workflows[wf_name]["jobs"]))
            assert self._has_build_runner(
                workflows[wf_name]["jobs"][job_key]
            ), f"{wf_name} must generate code for sqlite projects"


# ---------------------------------------------------------------------------
# Structural sanity — workflows that must pass on GitHub Actions
# ---------------------------------------------------------------------------


class TestWorkflowStructure:
    """Sanity checks on workflow shape that affect whether GitHub Actions accepts them."""

    @pytest.fixture
    def all_workflows(self, tmp_path: Path) -> dict[str, dict[str, Any]]:
        return _generate_workflows(
            _make_config(database="sqlite", platforms=["android", "ios", "web"]),
            tmp_path,
        )

    def test_all_workflows_parse_as_valid_yaml(self, tmp_path: Path) -> None:
        config = _make_config(platforms=["android"])
        config.output_dir = tmp_path
        config.project_path.mkdir(parents=True, exist_ok=True)
        with patch.object(
            CicdGenerator, "_get_current_flutter_version", return_value="3.24.0"
        ):
            CicdGenerator(config).generate_cicd()
        workflows_dir = config.project_path / ".github" / "workflows"
        for wf in workflows_dir.glob("*.yml"):
            parsed: dict[str, Any] = yaml.safe_load(wf.read_text())
            assert parsed is not None, f"{wf.name} parsed as empty"
            assert "jobs" in parsed, f"{wf.name} missing top-level 'jobs' key"

    def test_checkout_step_present_in_every_workflow(
        self, all_workflows: dict[str, dict[str, Any]]
    ) -> None:
        for wf_name, wf in all_workflows.items():
            for job in wf["jobs"].values():
                step_names = [s.get("name", "") for s in job.get("steps", [])]
                assert any(
                    "checkout" in n.lower() for n in step_names
                ), f"{wf_name}: missing Checkout step"

    def test_flutter_setup_step_present_in_every_workflow(
        self, all_workflows: dict[str, dict[str, Any]]
    ) -> None:
        for wf_name, wf in all_workflows.items():
            for job in wf["jobs"].values():
                step_names = [s.get("name", "") for s in job.get("steps", [])]
                assert any(
                    "flutter" in n.lower() for n in step_names
                ), f"{wf_name}: missing Setup Flutter step"

    def test_flutter_pub_get_present_in_every_workflow(
        self, all_workflows: dict[str, dict[str, Any]]
    ) -> None:
        for wf_name, wf in all_workflows.items():
            for job in wf["jobs"].values():
                runs = [s.get("run", "") for s in job.get("steps", [])]
                assert any(
                    "flutter pub get" in r for r in runs
                ), f"{wf_name}: missing 'flutter pub get' step"

    def test_pr_comment_steps_use_github_script(
        self, all_workflows: dict[str, dict[str, Any]]
    ) -> None:
        """Steps that post PR comments must use actions/github-script (not raw curl)."""
        for wf_name, wf in all_workflows.items():
            for job in wf["jobs"].values():
                for step in job.get("steps", []):
                    if "comment" in step.get("name", "").lower():
                        assert "github-script" in step.get(
                            "uses", ""
                        ), f"{wf_name}: PR comment step should use actions/github-script"

    def test_concurrency_group_defined_in_pr_workflows(
        self, all_workflows: dict[str, dict[str, Any]]
    ) -> None:
        pr_workflows = {
            k: v
            for k, v in all_workflows.items()
            if k in ("lint.yml", "format.yml", "test.yml")
        }
        for wf_name, wf in pr_workflows.items():
            assert (
                "concurrency" in wf
            ), f"{wf_name}: missing concurrency block (stacked PRs will queue up)"
