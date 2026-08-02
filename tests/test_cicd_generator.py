"""Tests for the CI/CD generator module."""

import tempfile
from pathlib import Path

import pytest

from flutter_setup.cicd_generator import CicdGenerator
from flutter_setup.config import Config


class TestCicdGenerator:
    """Test cases for CicdGenerator class."""

    @pytest.fixture
    def config(self) -> Config:
        """Create a test configuration."""
        return Config(
            project_name="TestApp",
            platforms=["ios", "android", "web"],
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
    def cicd_generator(self, config: Config) -> CicdGenerator:
        """Create a CicdGenerator instance."""
        return CicdGenerator(config)

    def test_init(self, cicd_generator: CicdGenerator, config: Config) -> None:
        """Test CicdGenerator initialization."""
        assert cicd_generator.config == config
        assert cicd_generator.project_path == config.project_path
        assert cicd_generator.project_name == config.project_name
        assert cicd_generator.package_name == config.package_name
        assert cicd_generator.flutter_channel == config.channel

    def test_generate_cicd_dry_run(self, config: Config) -> None:
        """Test generate_cicd in dry run mode."""
        config.dry_run = True
        generator = CicdGenerator(config)
        generator.generate_cicd()  # Should not raise

    def test_generate_cicd_creates_structure(self, config: Config) -> None:
        """Test that generate_cicd creates the correct directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            generator.generate_cicd()

            github_dir = config.project_path / ".github"
            workflows_dir = github_dir / "workflows"

            assert github_dir.exists()
            assert workflows_dir.exists()

    def test_generate_lint_workflow(self, config: Config) -> None:
        """Test generating lint workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_lint_workflow(workflows_dir)

            lint_file = workflows_dir / "lint.yml"
            assert lint_file.exists()
            content = lint_file.read_text()
            assert "name: Lint" in content
            assert "flutter analyze" in content
            assert "pull_request" in content

    def test_generate_format_workflow(self, config: Config) -> None:
        """Test generating format workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_format_workflow(workflows_dir)

            format_file = workflows_dir / "format.yml"
            assert format_file.exists()
            content = format_file.read_text()
            assert "name: Format" in content
            assert "dart format" in content

    def test_generate_test_workflow(self, config: Config) -> None:
        """Test generating test workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_test_workflow(workflows_dir)

            test_file = workflows_dir / "test.yml"
            assert test_file.exists()
            content = test_file.read_text()
            assert "name: Test" in content
            assert "flutter test --coverage" in content

    def test_codecov_token_uses_double_brace_syntax(self, config: Config) -> None:
        """Test that the Codecov token uses correct ${{ }} expression syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            generator._generate_test_workflow(workflows_dir)
            content = (workflows_dir / "test.yml").read_text()
            assert "${{ secrets.CODECOV_TOKEN }}" in content
            assert "${ secrets.CODECOV_TOKEN }" not in content

    def test_workflows_use_correct_actions_versions(self, config: Config) -> None:
        """Test that generated workflows use valid GitHub Actions versions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            generator.generate_cicd()

            workflows_dir = config.project_path / ".github" / "workflows"
            for workflow_file in workflows_dir.glob("*.yml"):
                content = workflow_file.read_text()
                assert "actions/checkout@v6" not in content, workflow_file.name
                assert "actions/upload-artifact@v5" not in content, workflow_file.name
                assert "actions/github-script@v8" not in content, workflow_file.name
                assert "actions/checkout@v4" in content or "checkout" not in content

    def test_generate_build_workflows_ios(self, config: Config) -> None:
        """Test generating iOS build workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_build_workflows(workflows_dir)

            ios_file = workflows_dir / "build-ios.yml"
            assert ios_file.exists()
            content = ios_file.read_text()
            assert "name: Build iOS" in content
            assert "macos-latest" in content

    def test_generate_build_workflows_android(self, config: Config) -> None:
        """Test generating Android build workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_build_workflows(workflows_dir)

            android_file = workflows_dir / "build-android.yml"
            assert android_file.exists()
            content = android_file.read_text()
            assert "name: Build Android" in content
            assert "flutter build apk" in content
            assert "flutter build appbundle" in content

    def test_generate_build_workflows_web(self, config: Config) -> None:
        """Test generating Web build workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_build_workflows(workflows_dir)

            web_file = workflows_dir / "build-web.yml"
            assert web_file.exists()
            content = web_file.read_text()
            assert "name: Build Web" in content
            assert "flutter build web" in content

    def test_generate_build_workflows_all_platforms(self) -> None:
        """Test generating build workflows for all platforms."""
        config = Config(
            project_name="TestApp",
            platforms=["ios", "android", "web", "macos", "linux", "windows"],
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

        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_build_workflows(workflows_dir)

            assert (workflows_dir / "build-ios.yml").exists()
            assert (workflows_dir / "build-android.yml").exists()
            assert (workflows_dir / "build-web.yml").exists()
            assert (workflows_dir / "build-macos.yml").exists()
            assert (workflows_dir / "build-linux.yml").exists()
            assert (workflows_dir / "build-windows.yml").exists()

    def test_generate_build_workflows_only_enabled_platforms(self) -> None:
        """Test that only enabled platforms get build workflows."""
        config = Config(
            project_name="TestApp",
            platforms=["web"],
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

        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_build_workflows(workflows_dir)

            assert (workflows_dir / "build-web.yml").exists()
            assert not (workflows_dir / "build-ios.yml").exists()
            assert not (workflows_dir / "build-android.yml").exists()

    def test_generate_dependabot(self, config: Config) -> None:
        """Test generating dependabot configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            github_dir = config.project_path / ".github"
            github_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_dependabot(github_dir)

            dependabot_file = github_dir / "dependabot.yml"
            assert dependabot_file.exists()
            content = dependabot_file.read_text()
            assert "version: 2" in content
            assert 'package-ecosystem: "pub"' in content
            assert 'package-ecosystem: "github-actions"' in content

    def test_generate_setup_docs(self, config: Config) -> None:
        """Test generating setup documentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            github_dir = config.project_path / ".github"
            github_dir.mkdir(parents=True, exist_ok=True)

            generator._generate_setup_docs(github_dir)

            docs_file = github_dir / "CI_CD_SETUP.md"
            assert docs_file.exists()
            content = docs_file.read_text()
            assert "CI/CD Setup Guide" in content
            assert config.project_name in content
            assert "Lint Workflow" in content
            assert "Format Workflow" in content

    def test_generate_platform_notes(self, config: Config) -> None:
        """Test generating platform-specific notes."""
        generator = CicdGenerator(config)
        notes = generator._generate_platform_notes()
        assert "iOS" in notes
        assert "Android" in notes
        assert "Web" in notes

    def test_generate_platform_notes_all_platforms(self) -> None:
        """Test platform notes for all platforms."""
        config = Config(
            project_name="TestApp",
            platforms=["ios", "android", "web", "macos", "linux", "windows"],
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

        generator = CicdGenerator(config)
        notes = generator._generate_platform_notes()
        assert "iOS" in notes
        assert "Android" in notes
        assert "Web" in notes
        assert "macOS" in notes
        assert "Linux" in notes
        assert "Windows" in notes

    def test_generate_cicd_complete(self, config: Config) -> None:
        """Test complete CI/CD generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            generator.generate_cicd()

            github_dir = config.project_path / ".github"
            workflows_dir = github_dir / "workflows"

            # Check workflows exist
            assert (workflows_dir / "lint.yml").exists()
            assert (workflows_dir / "format.yml").exists()
            assert (workflows_dir / "test.yml").exists()
            assert (workflows_dir / "build-ios.yml").exists()
            assert (workflows_dir / "build-android.yml").exists()
            assert (workflows_dir / "build-web.yml").exists()

            # Check dependabot exists
            assert (github_dir / "dependabot.yml").exists()

            # Check documentation exists
            assert (github_dir / "CI_CD_SETUP.md").exists()

    def test_codegen_step_absent_without_sqlite(self, config: Config) -> None:
        """Test that no code generation step is added when database is not sqlite."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            generator.generate_cicd()

            workflows_dir = config.project_path / ".github" / "workflows"
            for wf in workflows_dir.glob("*.yml"):
                content = wf.read_text()
                assert "build_runner" not in content, wf.name

    def test_codegen_step_absent_in_lint_workflow_for_sqlite(self) -> None:
        """Test that lint workflow never includes build_runner (analyze doesn't need generated code)."""
        config = Config(
            project_name="TestApp",
            platforms=["android"],
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
            database="sqlite",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            generator._generate_lint_workflow(workflows_dir)
            content = (workflows_dir / "lint.yml").read_text()
            assert "build_runner" not in content

    def test_codegen_step_present_in_test_workflow_for_sqlite(self) -> None:
        """Test that code generation step is added to test workflow for sqlite projects."""
        config = Config(
            project_name="TestApp",
            platforms=["android"],
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
            database="sqlite",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            generator._generate_test_workflow(workflows_dir)
            content = (workflows_dir / "test.yml").read_text()
            assert "build_runner" in content
            assert "Generate code" in content

    def test_codegen_step_present_in_build_workflows_for_sqlite(self) -> None:
        """Test that code generation step is added to build workflows for sqlite projects."""
        config = Config(
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
            database="sqlite",
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            generator._generate_build_workflows(workflows_dir)
            for wf in ["build-ios.yml", "build-android.yml"]:
                content = (workflows_dir / wf).read_text()
                assert "build_runner" in content, wf
                assert "Generate code" in content, wf

    def test_lint_workflow_has_issue_write_permission(self, config: Config) -> None:
        """Test that lint workflow grants issues: write so it can post PR comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            generator._generate_lint_workflow(workflows_dir)
            content = (workflows_dir / "lint.yml").read_text()
            assert "permissions:" in content
            assert "contents: read" in content
            assert "issues: write" in content

    def test_format_workflow_has_issue_write_permission(self, config: Config) -> None:
        """Test that format workflow grants issues: write so it can post PR comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            generator._generate_format_workflow(workflows_dir)
            content = (workflows_dir / "format.yml").read_text()
            assert "permissions:" in content
            assert "contents: read" in content
            assert "issues: write" in content

    def test_git_hooks_generated(self, config: Config) -> None:
        """Test that pre-commit and pre-push hooks are created in .git-hooks/."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            generator.generate_cicd()

            hooks_dir = config.project_path / ".git-hooks"
            pre_commit = hooks_dir / "pre-commit"
            pre_push = hooks_dir / "pre-push"

            assert pre_commit.exists(), ".git-hooks/pre-commit must be created"
            assert pre_push.exists(), ".git-hooks/pre-push must be created"
            assert pre_commit.stat().st_mode & 0o111, "pre-commit must be executable"
            assert pre_push.stat().st_mode & 0o111, "pre-push must be executable"
            assert "dart format" in pre_commit.read_text()
            assert "flutter analyze" in pre_push.read_text()

    def test_build_artifacts_fail_when_missing(self, config: Config) -> None:
        """Test that build artifact uploads use if-no-files-found: error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            generator._generate_build_workflows(workflows_dir)
            for wf in workflows_dir.glob("build-*.yml"):
                content = wf.read_text()
                assert "if-no-files-found: error" in content, wf.name
                assert "if-no-files-found: ignore" not in content, wf.name

    def test_build_workflows_do_not_trigger_on_push_to_main(
        self, config: Config
    ) -> None:
        """Test that build workflows only fire on tags and workflow_dispatch, not main."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            workflows_dir = config.project_path / ".github" / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            generator._generate_build_workflows(workflows_dir)
            for wf in workflows_dir.glob("build-*.yml"):
                content = wf.read_text()
                # Triggering a full release build on every push to main wastes
                # expensive CI minutes (macOS runners cost 10x Linux) and produces
                # unsigned artifacts that cannot be shipped.
                assert (
                    "branches:" not in content
                ), f"{wf.name} must not trigger on branch push"
                assert "workflow_dispatch" in content, wf.name
                assert "tags:" in content, wf.name

    def test_pub_cache_key_includes_pubspec_yaml(self, config: Config) -> None:
        """Test that the pub cache key hashes both pubspec.yaml and pubspec.lock."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config.output_dir = Path(tmpdir)
            config.project_path.mkdir(parents=True, exist_ok=True)
            generator = CicdGenerator(config)
            generator.generate_cicd()
            workflows_dir = config.project_path / ".github" / "workflows"
            for wf in workflows_dir.glob("*.yml"):
                content = wf.read_text()
                if "Cache pub" in content:
                    assert "pubspec.yaml" in content, (
                        f"{wf.name}: cache key must hash pubspec.yaml to catch "
                        "constraint changes that don't update pubspec.lock"
                    )

    def test_platforms_lowercase(self) -> None:
        """Test that platforms are converted to lowercase."""
        config = Config(
            project_name="TestApp",
            platforms=["IOS", "ANDROID", "WEB"],
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

        generator = CicdGenerator(config)
        assert "ios" in generator.platforms
        assert "android" in generator.platforms
        assert "web" in generator.platforms


class TestWriteWorkflowFile:
    """Tests for _write_workflow_file skip/overwrite behavior."""

    def _make_generator(self, tmp_path: Path, force: bool = False) -> CicdGenerator:
        config = Config(
            project_name="myapp",
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
            flutter_location=tmp_path / "flutter",
        )
        return CicdGenerator(config, force=force)

    def test_skips_existing_file_when_force_false(self, tmp_path: Path) -> None:
        generator = self._make_generator(tmp_path, force=False)
        target = tmp_path / "existing.yml"
        target.write_text("original")
        generator._write_workflow_file(target, "new content")
        assert target.read_text() == "original"

    def test_overwrites_existing_file_when_force_true(self, tmp_path: Path) -> None:
        generator = self._make_generator(tmp_path, force=True)
        target = tmp_path / "existing.yml"
        target.write_text("original")
        generator._write_workflow_file(target, "new content")
        assert target.read_text() == "new content"

    def test_creates_file_when_absent(self, tmp_path: Path) -> None:
        generator = self._make_generator(tmp_path, force=False)
        target = tmp_path / "new.yml"
        generator._write_workflow_file(target, "content")
        assert target.read_text() == "content"
