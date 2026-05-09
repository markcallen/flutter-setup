"""Tests for the configuration module."""

import pytest
from pathlib import Path

from flutter_setup.config import Config


class TestConfig:
    """Test cases for Config class."""

    def test_valid_config_creation(self) -> None:
        """Test creating a valid configuration."""
        config = Config(
            project_name="TestApp",
            platforms=["ios", "android", "web"],
            org="com.test",
            channel="stable",
            output_dir=Path("."),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=True,
            verbose=True,
            flutter_location=Path.home() / "development" / "flutter",
        )

        assert config.project_name == "TestApp"
        assert config.platforms == ["ios", "android", "web"]
        assert config.org == "com.test"
        assert config.channel == "stable"
        assert config.template == "app"
        assert config.ios_language == "swift"
        assert config.android_language == "kotlin"
        assert config.flutter_update_mode == "reset"
        assert config.dry_run is True
        assert config.verbose is True

    def test_package_name_sanitization(self) -> None:
        """Test package name sanitization."""
        config = Config(
            project_name="My Test App!",
            platforms=["ios"],
            org="com.test",
            channel="stable",
            output_dir=Path("."),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=False,
            verbose=False,
            flutter_location=Path.home() / "development" / "flutter",
        )

        assert config.package_name == "my_test_app"

    def test_platforms_csv(self) -> None:
        """Test platforms CSV generation."""
        config = Config(
            project_name="TestApp",
            platforms=["ios", "android", "web"],
            org="com.test",
            channel="stable",
            output_dir=Path("."),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=False,
            verbose=False,
            flutter_location=Path.home() / "development" / "flutter",
        )

        assert config.platforms_csv == "ios,android,web"

    def test_project_path(self) -> None:
        """Test project path generation."""
        config = Config(
            project_name="TestApp",
            platforms=["ios"],
            org="com.test",
            channel="stable",
            output_dir=Path("/tmp"),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=False,
            verbose=False,
            flutter_location=Path.home() / "development" / "flutter",
        )

        assert config.project_path == Path("/tmp/TestApp")

    def test_invalid_project_name(self) -> None:
        """Test validation of empty project name."""
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            Config(
                project_name="",
                platforms=["ios"],
                org="com.test",
                channel="stable",
                output_dir=Path("."),
                template="app",
                ios_language="swift",
                android_language="kotlin",
                flutter_update_mode="reset",
                dry_run=False,
                verbose=False,
                flutter_location=Path.home() / "development" / "flutter",
            )

    def test_invalid_platforms(self) -> None:
        """Test validation of invalid platforms."""
        with pytest.raises(ValueError, match="Invalid platform: invalid"):
            Config(
                project_name="TestApp",
                platforms=["ios", "invalid"],
                org="com.test",
                channel="stable",
                output_dir=Path("."),
                template="app",
                ios_language="swift",
                android_language="kotlin",
                flutter_update_mode="reset",
                dry_run=False,
                verbose=False,
                flutter_location=Path.home() / "development" / "flutter",
            )

    def test_empty_platforms(self) -> None:
        """Test validation of empty platforms list."""
        with pytest.raises(ValueError, match="At least one platform must be specified"):
            Config(
                project_name="TestApp",
                platforms=[],
                org="com.test",
                channel="stable",
                output_dir=Path("."),
                template="app",
                ios_language="swift",
                android_language="kotlin",
                flutter_update_mode="reset",
                dry_run=False,
                verbose=False,
                flutter_location=Path.home() / "development" / "flutter",
            )

    def test_sanitize_package_name_with_special_chars(self) -> None:
        """Test package name sanitization with special characters."""
        config = Config(
            project_name="My-App@123!",
            platforms=["ios"],
            org="com.test",
            channel="stable",
            output_dir=Path("."),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=False,
            verbose=False,
            flutter_location=Path.home() / "development" / "flutter",
        )
        assert config.package_name == "my_app_123"

    def test_sanitize_package_name_starts_with_number(self) -> None:
        """Test package name sanitization when it starts with a number."""
        config = Config(
            project_name="123App",
            platforms=["ios"],
            org="com.test",
            channel="stable",
            output_dir=Path("."),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=False,
            verbose=False,
            flutter_location=Path.home() / "development" / "flutter",
        )
        assert config.package_name.startswith("app_")

    def test_sanitize_package_name_empty_after_sanitization(self) -> None:
        """Test package name sanitization when result would be empty."""
        config = Config(
            project_name="!!!",
            platforms=["ios"],
            org="com.test",
            channel="stable",
            output_dir=Path("."),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=False,
            verbose=False,
            flutter_location=Path.home() / "development" / "flutter",
        )
        assert config.package_name == "app"

    def test_invalid_ios_language_for_plugin(self) -> None:
        """Test validation of invalid iOS language for plugin template."""
        with pytest.raises(ValueError, match="Invalid iOS language"):
            Config(
                project_name="TestApp",
                platforms=["ios"],
                org="com.test",
                channel="stable",
                output_dir=Path("."),
                template="plugin",
                ios_language="python",  # type: ignore[arg-type]  # Invalid
                android_language="kotlin",
                flutter_update_mode="reset",
                dry_run=False,
                verbose=False,
                flutter_location=Path.home() / "development" / "flutter",
            )

    def test_invalid_android_language_for_plugin(self) -> None:
        """Test validation of invalid Android language for plugin template."""
        with pytest.raises(ValueError, match="Invalid Android language"):
            Config(
                project_name="TestApp",
                platforms=["ios"],
                org="com.test",
                channel="stable",
                output_dir=Path("."),
                template="plugin",
                ios_language="swift",
                android_language="python",  # type: ignore[arg-type]  # Invalid
                flutter_update_mode="reset",
                dry_run=False,
                verbose=False,
                flutter_location=Path.home() / "development" / "flutter",
            )

    def test_all_valid_platforms(self) -> None:
        """Test that all valid platforms are accepted."""
        config = Config(
            project_name="TestApp",
            platforms=["ios", "android", "macos", "linux", "windows", "web"],
            org="com.test",
            channel="stable",
            output_dir=Path("."),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=False,
            verbose=False,
            flutter_location=Path.home() / "development" / "flutter",
        )
        assert len(config.platforms) == 6

    def test_platforms_normalization(self) -> None:
        """Test that platform names are normalized to lowercase."""
        config = Config(
            project_name="TestApp",
            platforms=["iOS", "Android", "Web"],
            org="com.test",
            channel="stable",
            output_dir=Path("."),
            template="app",
            ios_language="swift",
            android_language="kotlin",
            flutter_update_mode="reset",
            dry_run=False,
            verbose=False,
            flutter_location=Path.home() / "development" / "flutter",
        )
        assert config.platforms == ["ios", "android", "web"]
