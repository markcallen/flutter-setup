"""Project creation for Flutter setup."""

import subprocess
from pathlib import Path
from typing import List

from rich.console import Console

from .config import Config
from .exceptions import ProjectCreationError

console = Console()


class ProjectCreator:
    """Creates Flutter projects with specified configuration."""
    
    def __init__(self, config: Config):
        """Initialize ProjectCreator."""
        self.config = config
        self.home = Path.home()
        self.flutter_root = self.home / "development" / "flutter"
    
    def create_project(self) -> None:
        """Create the Flutter project."""
        if self.config.dry_run:
            console.print("[yellow]DRY RUN: Would create Flutter project[/yellow]")
            return
        
        # Check if project already exists
        if self.config.project_path.exists():
            console.print(f"  ⚠️  Directory '{self.config.project_path}' exists—skipping create.")
            return
        
        # Create output directory
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build flutter create command
        create_cmd = self._build_create_command()
        
        # Execute flutter create
        console.print(f"  🏗️  Creating Flutter project at {self.config.project_path}...")
        
        try:
            subprocess.run(
                create_cmd,
                check=True,
                capture_output=True,
                text=True
            )
            console.print(f"  ✅ Project created at: {self.config.project_path}")
            
        except subprocess.CalledProcessError as e:
            raise ProjectCreationError(f"Failed to create project: {e}")
    
    def _build_create_command(self) -> List[str]:
        """Build the flutter create command."""
        cmd = [
            str(self.flutter_root / "bin" / "flutter"),
            "create",
            "--org", self.config.org,
            "--project-name", self.config.package_name,
            "--platforms", self.config.platforms_csv,
            "--template", self.config.template,
        ]
        
        # Add template-specific options
        if self.config.template == "plugin":
            cmd.extend([
                "--ios-language", self.config.ios_language,
                "--android-language", self.config.android_language
            ])
        
        # Add output path
        cmd.append(str(self.config.project_path))
        
        return cmd
