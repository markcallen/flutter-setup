"""macOS prerequisites management for Flutter setup."""

import subprocess
from pathlib import Path

from rich.console import Console

from .config import Config
from .exceptions import PrerequisitesError

console = Console()


class MacOSPrerequisites:
    """Manages macOS prerequisites for Flutter development."""

    def __init__(self, config: Config):
        """Initialize macOS prerequisites manager."""
        self.config = config
        self.home = Path.home()

    def check_and_install(self) -> None:
        """Check and install all required prerequisites."""
        if self.config.dry_run:
            console.print(
                "[yellow]DRY RUN: Would check and install macOS prerequisites[/yellow]"
            )
            return

        self._check_xcode_tools()
        self._check_homebrew()
        self._install_packages()
        self._setup_platform_tools()

    def _check_xcode_tools(self) -> None:
        """Check and install Xcode Command Line Tools."""
        console.print("  📱 Checking Xcode Command Line Tools...")

        try:
            result = subprocess.run(
                ["xcode-select", "-p"], capture_output=True, text=True, check=False
            )

            if result.returncode != 0:
                console.print("  ⚠️  Xcode Command Line Tools not found, installing...")
                subprocess.run(["xcode-select", "--install"], check=True)
                console.print("  ✅ Xcode Command Line Tools installation initiated")
                console.print(
                    "  ℹ️  Please complete the installation in the popup window"
                )
                console.print(
                    "  ℹ️  You may need to restart the setup after installation"
                )
                raise PrerequisitesError(
                    "Xcode Command Line Tools installation required"
                )

            console.print("  ✅ Xcode Command Line Tools found")
        except subprocess.CalledProcessError as e:
            raise PrerequisitesError(f"Failed to check Xcode tools: {e}")

    def _check_homebrew(self) -> None:
        """Check and install Homebrew."""
        console.print("  🍺 Checking Homebrew...")

        try:
            result = subprocess.run(
                ["brew", "--version"], capture_output=True, text=True, check=False
            )

            if result.returncode != 0:
                console.print("  ⚠️  Homebrew not found, installing...")
                self._install_homebrew()
            else:
                console.print("  ✅ Homebrew found")
                self._ensure_homebrew_path()
        except subprocess.CalledProcessError as e:
            raise PrerequisitesError(f"Failed to check Homebrew: {e}")

    def _install_homebrew(self) -> None:
        """Install Homebrew."""
        try:
            install_script = (
                "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
            )
            subprocess.run(
                ["/bin/bash", "-c", f'curl -fsSL "{install_script}" | bash'],
                env={"NONINTERACTIVE": "1"},
                check=True,
            )
            console.print("  ✅ Homebrew installed")
            self._ensure_homebrew_path()
        except subprocess.CalledProcessError as e:
            raise PrerequisitesError(f"Failed to install Homebrew: {e}")

    def _ensure_homebrew_path(self) -> None:
        """Ensure Homebrew is in PATH."""
        try:
            if Path("/opt/homebrew/bin/brew").exists():
                subprocess.run(["/opt/homebrew/bin/brew", "shellenv"], check=True)
                console.print("  ✅ Homebrew path configured")
        except subprocess.CalledProcessError:
            console.print(
                "  ⚠️  Homebrew path configuration failed (may need manual setup)"
            )

    def _install_packages(self) -> None:
        """Install required packages via Homebrew."""
        required_packages = ["git", "cocoapods"]

        for package in required_packages:
            console.print(f"  📦 Installing {package}...")
            try:
                subprocess.run(
                    ["brew", "install", package], check=True, capture_output=True
                )
                console.print(f"  ✅ {package} installed")
            except subprocess.CalledProcessError as e:
                result = subprocess.run(
                    ["brew", "list", package],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    console.print(f"  ✅ {package} already installed")
                else:
                    raise PrerequisitesError(f"Failed to install {package}: {e}")

    def _setup_platform_tools(self) -> None:
        """Setup platform-specific development tools."""
        if "android" in self.config.platforms:
            self._setup_android_tools()
        if "ios" in self.config.platforms:
            self._setup_ios_tools()

    def _setup_android_tools(self) -> None:
        """Setup Android development tools."""
        console.print("  🤖 Setting up Android development tools...")

        android_packages = [
            ("--cask", "temurin"),
            ("--cask", "android-commandlinetools"),
        ]

        for args in android_packages:
            package = args[1]
            try:
                subprocess.run(
                    ["brew", "install"] + list(args), check=True, capture_output=True
                )
                console.print(f"  ✅ {package} installed")
            except subprocess.CalledProcessError as e:
                result = subprocess.run(
                    ["brew", "list", "--cask", package],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    console.print(f"  ✅ {package} already installed")
                else:
                    console.print(f"  ⚠️  Failed to install {package}: {e}")

    def _setup_ios_tools(self) -> None:
        """Setup iOS development tools."""
        console.print("  🍎 Setting up iOS development tools...")

        try:
            subprocess.run(["pod", "repo", "update"], check=False, capture_output=True)
            console.print("  ✅ iOS tools configured")
        except Exception as e:
            console.print(f"  ⚠️  iOS tools configuration warning: {e}")

    def check_only(self) -> bool:
        """Check prerequisites without installing."""
        all_ok = True

        console.print("  📱 Checking Xcode Command Line Tools...")
        try:
            result = subprocess.run(
                ["xcode-select", "-p"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                console.print("  ✅ Xcode Command Line Tools found")
            else:
                console.print("  ❌ Xcode Command Line Tools not found")
                all_ok = False
        except Exception as e:
            console.print(f"  ❌ Failed to check Xcode tools: {e}")
            all_ok = False

        console.print("  🍺 Checking Homebrew...")
        try:
            result = subprocess.run(
                ["brew", "--version"], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                console.print("  ✅ Homebrew found")
            else:
                console.print("  ❌ Homebrew not found")
                all_ok = False
        except Exception as e:
            console.print(f"  ❌ Failed to check Homebrew: {e}")
            all_ok = False

        required_packages = ["git", "cocoapods"]
        for package in required_packages:
            console.print(f"  📦 Checking {package}...")
            try:
                result = subprocess.run(
                    ["brew", "list", package],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    console.print(f"  ✅ {package} installed")
                else:
                    console.print(f"  ❌ {package} not installed")
                    all_ok = False
            except Exception as e:
                console.print(f"  ❌ Failed to check {package}: {e}")
                all_ok = False

        return all_ok
