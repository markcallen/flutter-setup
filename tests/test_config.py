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
            )
