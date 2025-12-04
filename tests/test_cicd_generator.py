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
            assert "flutter test" in content

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
