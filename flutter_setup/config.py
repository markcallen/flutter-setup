"""Configuration and data models for Flutter Setup."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal

# Type aliases
FlutterChannel = Literal["stable", "beta"]
TemplateType = Literal["app", "plugin"]
IosLanguage = Literal["swift", "objc"]
AndroidLanguage = Literal["kotlin", "java"]
UpdateMode = Literal["reset", "reclone", "skip"]
Platform = Literal["ios", "android", "macos", "linux", "windows", "web"]
Architecture = Literal["basic", "clean"]
Database = Literal["none", "sqlite"]
Testing = Literal["standard", "mocktail"]
E2ETesting = Literal["integration_test", "patrol"]
AuthProvider = Literal["none", "firebase"]
CloudDatabase = Literal["none", "firestore"]
NotificationsProvider = Literal["none", "firebase"]


@dataclass
class Config:
    """Configuration for Flutter setup."""

    project_name: str
    platforms: List[str]
    org: str
    channel: FlutterChannel
    output_dir: Path
    template: TemplateType
    ios_language: IosLanguage
    android_language: AndroidLanguage
    flutter_update_mode: UpdateMode
    dry_run: bool
    verbose: bool
    flutter_location: Path
    architecture: Architecture = "basic"
    database: Database = "none"
    testing: Testing = "standard"
    e2e_testing: E2ETesting = "integration_test"
    auth_provider: AuthProvider = "none"
    cloud_database: CloudDatabase = "none"
    notifications_provider: NotificationsProvider = "none"
    flutter_version: str | None = None

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        if not self.project_name:
            raise ValueError("Project name cannot be empty")

        if not self.platforms:
            raise ValueError("At least one platform must be specified")

        # Basic normalization
        self.platforms = [p.strip().lower() for p in self.platforms if p.strip()]

        # Validate platforms
        valid_platforms = {"ios", "android", "macos", "linux", "windows", "web"}
        for platform in self.platforms:
            if platform not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}")

        # Validate template-specific options
        if self.template == "plugin":
            if self.ios_language not in ["swift", "objc"]:
                raise ValueError(f"Invalid iOS language: {self.ios_language}")
            if self.android_language not in ["kotlin", "java"]:
                raise ValueError(f"Invalid Android language: {self.android_language}")

        if self.architecture not in ["basic", "clean"]:
            raise ValueError(f"Invalid architecture: {self.architecture}")

        if self.database not in ["none", "sqlite"]:
            raise ValueError(f"Invalid database: {self.database}")

        if self.testing not in ["standard", "mocktail"]:
            raise ValueError(f"Invalid testing framework: {self.testing}")

        if self.e2e_testing not in ["integration_test", "patrol"]:
            raise ValueError(
                f"Invalid end-to-end testing framework: {self.e2e_testing}"
            )

        if self.auth_provider not in ["none", "firebase"]:
            raise ValueError(f"Invalid auth provider: {self.auth_provider}")

        if self.cloud_database not in ["none", "firestore"]:
            raise ValueError(f"Invalid cloud database: {self.cloud_database}")

        if self.notifications_provider not in ["none", "firebase"]:
            raise ValueError(
                f"Invalid notifications provider: {self.notifications_provider}"
            )

        if self.flutter_version is not None:
            import re

            if not re.fullmatch(r"\d+\.\d+\.\d+", self.flutter_version):
                raise ValueError(
                    f"Invalid flutter_version '{self.flutter_version}': must be X.Y.Z (e.g. 3.24.0)"
                )

    @property
    def project_path(self) -> Path:
        """Get the full project path."""
        return self.output_dir / self.project_name

    @property
    def package_name(self) -> str:
        """Get the sanitized package name."""
        return self._sanitize_package_name(self.project_name)

    @property
    def platforms_csv(self) -> str:
        """Get platforms as comma-separated string."""
        return ",".join(self.platforms)

    def _sanitize_package_name(self, name: str) -> str:
        """Sanitize package name for Flutter."""
        import re

        # Convert to lowercase and replace non-alphanumeric with underscores
        sanitized = re.sub(r"[^a-z0-9_]", "_", name.lower())

        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"app_{sanitized}"

        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")

        # Ensure it's not empty
        if not sanitized:
            sanitized = "app"

        return sanitized
