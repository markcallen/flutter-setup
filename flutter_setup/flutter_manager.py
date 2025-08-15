"""Flutter SDK management for Flutter setup."""

import subprocess
import sys
from pathlib import Path

from rich.console import Console

from .config import Config
from .exceptions import FlutterInstallationError

console = Console()


class FlutterManager:
    """Manages Flutter SDK installation and updates."""
    
    def __init__(self, config: Config):
        """Initialize FlutterManager."""
        self.config = config
        self.home = Path.home()
        self.flutter_root = self.home / "development" / "flutter"
        self.zprofile = self.home / ".zprofile"
    
    def ensure_flutter(self) -> None:
        """Ensure Flutter SDK is installed and up to date."""
        if self.config.dry_run:
            console.print("[yellow]DRY RUN: Would manage Flutter SDK[/yellow]")
            return
        
        # Handle reclone mode
        if self.config.flutter_update_mode == "reclone":
            self._reclone_flutter()
            return
        
        # Check if Flutter is already installed
        if not self.flutter_root.exists() or not (self.flutter_root / ".git").exists():
            self._install_flutter()
        else:
            self._update_flutter()
        
        # Ensure Flutter is in PATH
        self._ensure_flutter_path()
        
        # Run flutter doctor
        self._run_flutter_doctor()
    
    def _reclone_flutter(self) -> None:
        """Reclone Flutter repository."""
        console.print(f"  🔄 Recloning Flutter ({self.config.channel})...")
        
        try:
            if self.flutter_root.exists():
                import shutil
                shutil.rmtree(self.flutter_root)
            
            self._install_flutter()
        except Exception as e:
            raise FlutterInstallationError(f"Failed to reclone Flutter: {e}")
    
    def _install_flutter(self) -> None:
        """Install Flutter SDK."""
        console.print(f"  📥 Installing Flutter ({self.config.channel})...")
        
        try:
            # Create parent directory
            self.flutter_root.parent.mkdir(parents=True, exist_ok=True)
            
            # Clone Flutter repository
            subprocess.run(
                [
                    "git", "clone", "--depth", "1", "-b", self.config.channel,
                    "https://github.com/flutter/flutter.git", str(self.flutter_root)
                ],
                check=True,
                capture_output=True
            )
            
            console.print("  ✅ Flutter installed")
            
        except subprocess.CalledProcessError as e:
            raise FlutterInstallationError(f"Failed to install Flutter: {e}")
    
    def _update_flutter(self) -> None:
        """Update existing Flutter installation."""
        console.print(f"  🔄 Updating Flutter ({self.config.channel})...")
        
        try:
            # Set remote URL
            subprocess.run(
                ["git", "remote", "set-url", "origin", "https://github.com/flutter/flutter.git"],
                cwd=self.flutter_root,
                check=False,
                capture_output=True
            )
            
            # Fetch latest changes
            subprocess.run(
                ["git", "fetch", "origin", "--prune"],
                cwd=self.flutter_root,
                check=True,
                capture_output=True
            )
            
            # Try to checkout the target channel
            try:
                subprocess.run(
                    ["git", "checkout", self.config.channel],
                    cwd=self.flutter_root,
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                # Create new branch if it doesn't exist
                subprocess.run(
                    ["git", "checkout", "-b", self.config.channel, f"origin/{self.config.channel}"],
                    cwd=self.flutter_root,
                    check=True,
                    capture_output=True
                )
            
            # Try fast-forward merge
            try:
                subprocess.run(
                    ["git", "merge", "--ff-only", f"origin/{self.config.channel}"],
                    cwd=self.flutter_root,
                    check=True,
                    capture_output=True
                )
                console.print("  ✅ Flutter updated (fast-forward)")
                return
            except subprocess.CalledProcessError:
                pass
            
            # Handle diverged branches
            self._handle_diverged_branches()
            
        except subprocess.CalledProcessError as e:
            raise FlutterInstallationError(f"Failed to update Flutter: {e}")
    
    def _handle_diverged_branches(self) -> None:
        """Handle diverged Git branches."""
        if self.config.flutter_update_mode == "skip":
            console.print("  ⚠️  Flutter repo has diverged; skipping update (per --flutter-update skip)")
            return
        
        console.print("  ⚠️  Flutter repo has diverged from origin")
        
        # Get commit counts
        try:
            result = subprocess.run(
                ["git", "rev-list", "--left-right", "--count", f"origin/{self.config.channel}...{self.config.channel}"],
                cwd=self.flutter_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            counts = result.stdout.strip().split()
            if len(counts) == 2:
                left_ahead = counts[0]
                right_ahead = counts[1]
                console.print(f"  📊 Local ahead by: {right_ahead}, origin ahead by: {left_ahead}")
            
        except subprocess.CalledProcessError:
            pass
        
        # For now, we'll hard reset in reset mode
        if self.config.flutter_update_mode == "reset":
            console.print("  🔄 Resetting Flutter to origin (discarding local changes)")
            try:
                subprocess.run(
                    ["git", "reset", "--hard", f"origin/{self.config.channel}"],
                    cwd=self.flutter_root,
                    check=True,
                    capture_output=True
                )
                console.print("  ✅ Flutter reset to origin")
            except subprocess.CalledProcessError as e:
                raise FlutterInstallationError(f"Failed to reset Flutter: {e}")
    
    def _ensure_flutter_path(self) -> None:
        """Ensure Flutter is in PATH."""
        console.print("  🔧 Configuring Flutter PATH...")
        
        flutter_path = f'export PATH="{self.flutter_root}/bin:$PATH"'
        
        # Add to .zprofile if not already there
        if self.zprofile.exists():
            with open(self.zprofile, 'r') as f:
                content = f.read()
                if flutter_path not in content:
                    with open(self.zprofile, 'a') as f:
                        f.write(f'\n{flutter_path}\n')
                    console.print("  ✅ Flutter PATH added to .zprofile")
                else:
                    console.print("  ✅ Flutter PATH already in .zprofile")
        else:
            with open(self.zprofile, 'w') as f:
                f.write(f'{flutter_path}\n')
            console.print("  ✅ Flutter PATH added to .zprofile")
        
        # Add to current environment
        flutter_bin = self.flutter_root / "bin"
        if str(flutter_bin) not in sys.path:
            sys.path.insert(0, str(flutter_bin))
    
    def _run_flutter_doctor(self) -> None:
        """Run flutter doctor to check setup."""
        console.print("  🏥 Running Flutter doctor...")
        
        try:
            # Run flutter doctor
            result = subprocess.run(
                [str(self.flutter_root / "bin" / "flutter"), "doctor", "-v"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                console.print("  ✅ Flutter doctor passed")
            else:
                console.print("  ⚠️  Flutter doctor found issues:")
                console.print(result.stderr)
                
                # Check for Android licenses
                if "Some Android licenses not accepted" in result.stderr:
                    console.print("  📱 Android licenses need acceptance")
                    self._handle_android_licenses()
                    
        except Exception as e:
            console.print(f"  ⚠️  Flutter doctor warning: {e}")
    
    def _handle_android_licenses(self) -> None:
        """Handle Android license acceptance."""
        if "android" not in self.config.platforms:
            return
        
        console.print("  📱 Android licenses not accepted")
        console.print("  ℹ️  You can run 'flutter doctor --android-licenses' later to accept licenses")
