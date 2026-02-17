"""Linux prerequisites management for Flutter setup."""

import subprocess

from rich.console import Console

from .config import Config
from .exceptions import PrerequisitesError

console = Console()

LINUX_APT_PACKAGES = [
    "git",
    "curl",
    "unzip",
    "xz-utils",
    "zip",
    "libglu1-mesa",
    "clang",
    "cmake",
    "ninja-build",
    "pkg-config",
]


class LinuxPrerequisites:
    """Manages Linux prerequisites for Flutter development."""

    def __init__(self, config: Config):
        """Initialize Linux prerequisites manager."""
        self.config = config

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
        if not missing:
            console.print("  ✅ Linux prerequisites already installed")
            return

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

    def install_command(self) -> str:
        """Return the APT command users can run manually."""
        return f"sudo apt-get update && sudo apt-get install -y {' '.join(LINUX_APT_PACKAGES)}"

    def _missing_packages(self) -> list[str]:
        """Return missing APT packages."""
        missing: list[str] = []
        for package in LINUX_APT_PACKAGES:
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
