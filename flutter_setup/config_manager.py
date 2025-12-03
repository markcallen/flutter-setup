"""Configuration file management with XDG Base Directory Specification support."""

import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

import yaml  # type: ignore[import-untyped]
from rich.console import Console

console = Console()


class ConfigManager:
    """Manages configuration file using XDG Base Directory Specification."""

    def __init__(self) -> None:
        """Initialize ConfigManager with XDG-compliant paths."""
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.yaml"

    def _get_config_dir(self) -> Path:
        """Get config directory following XDG Base Directory Specification."""
        # XDG_CONFIG_HOME takes precedence, fallback to ~/.config
        xdg_config_home = os.getenv("XDG_CONFIG_HOME")
        if xdg_config_home:
            config_dir = Path(xdg_config_home) / "flutter-setup"
        else:
            config_dir = Path.home() / ".config" / "flutter-setup"

        return config_dir

    def ensure_config_dir(self) -> None:
        """Ensure config directory exists, creating it if necessary."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        home = Path.home()
        default_flutter_location = str(home / "development" / "flutter")

        return {
            "flutter": {
                "location": default_flutter_location,
                "channel": "stable",
                "update_mode": "reset",
            },
            "project": {
                "org": "com.example",
                "template": "app",
                "ios_language": "swift",
                "android_language": "kotlin",
            },
        }

    def create_default_config(self) -> None:
        """Create default config file if it doesn't exist."""
        if self.config_file.exists():
            return

        self.ensure_config_dir()

        default_config = self.get_default_config()

        try:
            with open(self.config_file, "w") as f:
                yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)
            console.print(
                f"[dim]Created default config file at: {self.config_file}[/dim]"
            )
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not create config file: {e}[/yellow]"
            )

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file, creating default if it doesn't exist."""
        # Create default config if it doesn't exist
        if not self.config_file.exists():
            self.create_default_config()

        if not self.config_file.exists():
            # If we still can't create it, return defaults
            return self.get_default_config()

        try:
            with open(self.config_file, "r") as f:
                config = yaml.safe_load(f) or {}
            return config
        except Exception as e:
            console.print(
                f"[yellow]Warning: Could not load config file: {e}. Using defaults.[/yellow]"
            )
            return self.get_default_config()

    def save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        self.ensure_config_dir()

        try:
            with open(self.config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save config file: {e}[/yellow]")

    def get_flutter_location(self) -> Optional[Path]:
        """Get Flutter location from config file."""
        config = self.load_config()
        flutter_location = config.get("flutter", {}).get("location")
        if flutter_location:
            return Path(flutter_location)
        return None

    def set_flutter_location(self, location: Path) -> None:
        """Set Flutter location in config file."""
        config = self.load_config()
        if "flutter" not in config:
            config["flutter"] = {}
        config["flutter"]["location"] = str(location)
        self.save_config(config)

    def detect_flutter_location(self) -> Optional[Path]:
        """Detect Flutter location from environment variables or PATH."""
        # Check FLUTTER_ROOT environment variable
        flutter_root = os.getenv("FLUTTER_ROOT")
        if flutter_root:
            path = Path(flutter_root)
            if path.exists() and (path / "bin" / "flutter").exists():
                return path

        # Check if flutter is in PATH
        flutter_bin = shutil.which("flutter")
        if flutter_bin:
            # flutter_bin is something like /path/to/flutter/bin/flutter
            flutter_path = Path(flutter_bin).parent.parent
            if flutter_path.exists() and (flutter_path / ".git").exists():
                return flutter_path

        # Check common installation locations
        home = Path.home()
        common_paths = [
            home / "development" / "flutter",
            home / "flutter",
            home / ".flutter",
            Path("/usr/local/flutter"),
            Path("/opt/flutter"),
        ]

        for path in common_paths:
            if path.exists() and (path / "bin" / "flutter").exists():
                return path

        return None
