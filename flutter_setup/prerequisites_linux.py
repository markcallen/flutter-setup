"""Linux prerequisites management for Flutter setup."""

import shutil
import subprocess

from rich.console import Console

from .config import Config
from .exceptions import PrerequisitesError

console = Console()

# Core system utilities
CORE_PACKAGES = [
    "git",
    "curl",
    "unzip",
    "xz-utils",
    "zip",
]

# Linux desktop development requirements
LINUX_DESKTOP_PACKAGES = [
    "libglu1-mesa",
    "clang",
    "cmake",
    "ninja-build",
    "pkg-config",
    "libgtk-3-dev",
    "libayatana-appindicator3-dev",
    "liblzma-dev",
]

# Android development requirements
ANDROID_PACKAGES = [
    "openjdk-17-jdk",
]


class LinuxPrerequisites:
    """Manages Linux prerequisites for Flutter development."""

    def __init__(self, config: Config):
        """Initialize Linux prerequisites manager."""
        self.config = config
        self._check_package_manager()

    def _check_package_manager(self) -> None:
        """Ensure we are on a supported Debian-based system with APT."""
        if not shutil.which("apt-get") or not shutil.which("dpkg"):
            raise PrerequisitesError(
                "Unsupported Linux distribution. Only Debian-based distributions (using APT) are currently supported for automated prerequisite installation."
            )

    def check_and_install(self) -> None:
        """Check and install Linux prerequisites."""
        if self.config.dry_run:
            console.print(
                "[yellow]DRY RUN: Would check and install Linux prerequisites[/yellow]"
            )
            console.print(
                f"[yellow]DRY RUN: Would run: {self.install_command()}[/yellow]"
            )
            return

        missing = self._missing_packages()
        if missing:
            console.print(f"  📦 Missing Linux packages: {', '.join(missing)}")
            console.print("  🔧 Installing Linux prerequisites via APT...")
            try:
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(
                    ["sudo", "apt-get", "install", "-y", *missing],
                    check=True,
                )
                console.print("  ✅ Linux prerequisites installed")
            except subprocess.CalledProcessError as e:
                raise PrerequisitesError(f"Failed to install Linux prerequisites: {e}")
        else:
            console.print("  ✅ Linux prerequisites already installed")

        if "android" in self.config.platforms:
            self._setup_android_tools()

    def _setup_android_tools(self) -> None:
        """Additional Android toolchain setup instructions."""
        console.print("  🤖 Android JDK installed (openjdk-17-jdk)")
        console.print(
            "  ℹ️  Note: You may still need to install Android Command Line Tools manually"
        )
        console.print(
            "  ℹ️  Download from: https://developer.android.com/studio#command-tools"
        )

    def _get_required_packages(self) -> list[str]:
        """Get the full list of required packages based on target platforms."""
        packages = list(CORE_PACKAGES)

        if "linux" in self.config.platforms:
            packages.extend(LINUX_DESKTOP_PACKAGES)

        if "android" in self.config.platforms:
            packages.extend(ANDROID_PACKAGES)

        return sorted(list(set(packages)))

    def install_command(self) -> str:
        """Return the APT command users can run manually."""
        packages = self._get_required_packages()
        return f"sudo apt-get update && sudo apt-get install -y {' '.join(packages)}"

    def _missing_packages(self) -> list[str]:
        """Return missing APT packages."""
        required = self._get_required_packages()
        missing: list[str] = []
        for package in required:
            if not self._is_package_installed(package):
                missing.append(package)
        return missing

    def _is_package_installed(self, package: str) -> bool:
        """Check whether a package is installed via dpkg."""
        result = subprocess.run(
            ["dpkg", "-s", package],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0

    def check_only(self) -> bool:
        """Check Linux prerequisites without installing."""
        missing = self._missing_packages()
        if not missing:
            console.print("  ✅ Linux prerequisites found")
            return True

        console.print(f"  ❌ Missing Linux prerequisites: {', '.join(missing)}")
        console.print(f"  ℹ️  Install with: {self.install_command()}")
        return False
