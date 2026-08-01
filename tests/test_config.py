"""Tests for the configuration module."""

import pytest
from pathlib import Path
from typing import Any

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
        assert config.architecture == "basic"
        assert config.database == "none"
        assert config.testing == "standard"
        assert config.e2e_testing == "integration_test"
        assert config.auth_provider == "none"
        assert config.cloud_database == "none"
        assert config.notifications_provider == "none"

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

    def test_valid_architecture_and_services(self) -> None:
        """Test optional architecture, persistence, testing, and services."""
        config = Config(
            project_name="TestApp",
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
            architecture="clean",
            database="sqlite",
            testing="mocktail",
            e2e_testing="patrol",
            auth_provider="firebase",
            cloud_database="firestore",
            notifications_provider="firebase",
        )

        assert config.architecture == "clean"
        assert config.database == "sqlite"
        assert config.testing == "mocktail"
        assert config.e2e_testing == "patrol"
        assert config.auth_provider == "firebase"
        assert config.cloud_database == "firestore"
        assert config.notifications_provider == "firebase"

    def test_invalid_architecture(self) -> None:
        """Test validation of invalid architecture."""
        with pytest.raises(ValueError, match="Invalid architecture"):
            Config(
                project_name="TestApp",
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
                architecture="layered",  # type: ignore[arg-type]
            )

    @pytest.mark.parametrize(
        ("field", "value", "message"),
        [
            ("database", "postgres", "Invalid database"),
            ("testing", "pytest", "Invalid testing framework"),
            ("e2e_testing", "espresso", "Invalid end-to-end testing framework"),
            ("auth_provider", "custom", "Invalid auth provider"),
            ("cloud_database", "supabase", "Invalid cloud database"),
            (
                "notifications_provider",
                "apns",
                "Invalid notifications provider",
            ),
        ],
    )
    def test_invalid_optional_starter_values(
        self, field: str, value: str, message: str
    ) -> None:
        """Test validation of invalid starter option values."""
        kwargs = {
            "project_name": "TestApp",
            "platforms": ["ios"],
            "org": "com.test",
            "channel": "stable",
            "output_dir": Path("."),
            "template": "app",
            "ios_language": "swift",
            "android_language": "kotlin",
            "flutter_update_mode": "reset",
            "dry_run": False,
            "verbose": False,
            "flutter_location": Path.home() / "development" / "flutter",
            field: value,
        }
        with pytest.raises(ValueError, match=message):
            Config(**kwargs)  # type: ignore[arg-type]

    def _base_kwargs(self) -> dict[str, Any]:
        return {
            "project_name": "TestApp",
            "platforms": ["ios"],
            "org": "com.test",
            "channel": "stable",
            "output_dir": Path("."),
            "template": "app",
            "ios_language": "swift",
            "android_language": "kotlin",
            "flutter_update_mode": "reset",
            "dry_run": False,
            "verbose": False,
            "flutter_location": Path.home() / "development" / "flutter",
        }

    def test_flutter_version_none_accepted(self) -> None:
        """flutter_version=None is the default and should be accepted."""
        config = Config(**self._base_kwargs())
        assert config.flutter_version is None

    def test_flutter_version_valid(self) -> None:
        """A correctly formatted X.Y.Z version is accepted."""
        config = Config(**{**self._base_kwargs(), "flutter_version": "3.24.0"})
        assert config.flutter_version == "3.24.0"

    def test_flutter_version_invalid_two_parts(self) -> None:
        """A version with only two parts should be rejected."""
        with pytest.raises(ValueError, match="Invalid flutter_version"):
            Config(**{**self._base_kwargs(), "flutter_version": "3.24"})

    def test_flutter_version_invalid_channel_name(self) -> None:
        """A channel name instead of a version number should be rejected."""
        with pytest.raises(ValueError, match="Invalid flutter_version"):
            Config(**{**self._base_kwargs(), "flutter_version": "stable"})

    def test_flutter_version_invalid_with_prefix(self) -> None:
        """A version string with a 'v' prefix should be rejected."""
        with pytest.raises(ValueError, match="Invalid flutter_version"):
            Config(**{**self._base_kwargs(), "flutter_version": "v3.24.0"})
