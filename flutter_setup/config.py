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
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """Validate configuration values."""
        if not self.project_name:
            raise ValueError("Project name cannot be empty")
        
        if not self.platforms:
            raise ValueError("At least one platform must be specified")
        
        # Validate platforms
        valid_platforms = {"ios", "android", "macos", "linux", "windows", "web"}
        for platform in self.platforms:
            if platform.lower() not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}")
        
        # Validate template-specific options
        if self.template == "plugin":
            if self.ios_language not in ["swift", "objc"]:
                raise ValueError(f"Invalid iOS language: {self.ios_language}")
            if self.android_language not in ["kotlin", "java"]:
                raise ValueError(f"Invalid Android language: {self.android_language}")
    
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
        sanitized = re.sub(r'[^a-z0-9_]', '_', name.lower())
        
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"app_{sanitized}"
        
        # Remove leading/trailing underscores
        sanitized = sanitized.strip('_')
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "app"
        
        return sanitized
