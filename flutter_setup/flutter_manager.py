"""Flutter SDK management for Flutter setup."""

import re
import subprocess
import sys
from pathlib import Path

from rich.console import Console

from .config import Config
from .exceptions import FlutterInstallationError
from .platform import detect_runtime_platform

console = Console()


class FlutterManager:
    """Manages Flutter SDK installation and updates."""

    def __init__(self, config: Config):
        """Initialize FlutterManager."""
        self.config = config
        self.platform = detect_runtime_platform()
        self.home = Path.home()
        self.flutter_root = config.flutter_location
        self.path_profiles = self._path_profiles_for_platform()

    def _path_profiles_for_platform(self) -> list[Path]:
        """Return shell profile files that should contain Flutter PATH."""
        if self.platform == "darwin":
            return [self.home / ".zprofile", self.home / ".zshrc"]
        if self.platform == "linux":
            return [self.home / ".bashrc", self.home / ".zshrc"]
        return [self.home / ".profile"]

    def _normalize_flutter_bin_path(self, path: str) -> str:
        """Normalize common shell home forms before comparing Flutter bin paths."""
        expanded = path.replace("$HOME", str(self.home))
        if expanded == "~":
            expanded = str(self.home)
        elif expanded.startswith("~/"):
            expanded = str(self.home / expanded[2:])
        return str(Path(expanded))

    def _expected_flutter_bin_path(self) -> str:
        """Return the normalized expected Flutter bin path."""
        return self._normalize_flutter_bin_path(str(self.flutter_root / "bin"))

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
        elif self.config.flutter_update_mode == "skip":
            console.print("  ⏭️  Skipping Flutter SDK update (update mode: skip)")
        else:
            self._update_flutter()

        # Verify version constraint before proceeding
        if self.config.flutter_version:
            self._check_flutter_version()

        # Ensure Flutter is in PATH
        self._ensure_flutter_path()

        # Run flutter doctor
        self._run_flutter_doctor()

    def _get_current_flutter_version(self) -> str | None:
        """Return the installed Flutter version string, or None if not detectable."""
        flutter_bin = self.flutter_root / "bin" / "flutter"
        try:
            result = subprocess.run(
                [str(flutter_bin), "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stdout or result.stderr or ""
            match = re.search(r"Flutter\s+([\d.]+)", output)
            if match:
                return match.group(1)
        except Exception:
            pass
        return None

    def _check_flutter_version(self) -> None:
        """Raise FlutterInstallationError if the installed version is older than config.flutter_version."""
        required = self.config.flutter_version
        if not required:
            return

        current = self._get_current_flutter_version()
        if current is None:
            raise FlutterInstallationError(
                f"Could not determine Flutter version. "
                f"Ensure Flutter is installed at {self.flutter_root}."
            )

        def parse(v: str) -> tuple[int, ...]:
            return tuple(int(x) for x in v.split("."))

        if parse(current) < parse(required):
            raise FlutterInstallationError(
                f"Flutter version too old: found {current}, requires >={required}.\n"
                f"  To upgrade: git -C {self.flutter_root} fetch && "
                f"git -C {self.flutter_root} checkout {required}"
            )
        console.print(f"  ✅ Flutter {current} satisfies >={required}")

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
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "-b",
                    self.config.channel,
                    "https://github.com/flutter/flutter.git",
                    str(self.flutter_root),
                ],
                check=True,
                capture_output=True,
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
                [
                    "git",
                    "remote",
                    "set-url",
                    "origin",
                    "https://github.com/flutter/flutter.git",
                ],
                cwd=self.flutter_root,
                check=False,
                capture_output=True,
            )

            # Fetch latest changes
            subprocess.run(
                ["git", "fetch", "origin", "--prune"],
                cwd=self.flutter_root,
                check=True,
                capture_output=True,
            )

            # Try to checkout the target channel
            try:
                subprocess.run(
                    ["git", "checkout", self.config.channel],
                    cwd=self.flutter_root,
                    check=True,
                    capture_output=True,
                )
            except subprocess.CalledProcessError:
                # Create new branch if it doesn't exist
                subprocess.run(
                    [
                        "git",
                        "checkout",
                        "-b",
                        self.config.channel,
                        f"origin/{self.config.channel}",
                    ],
                    cwd=self.flutter_root,
                    check=True,
                    capture_output=True,
                )

            # Try fast-forward merge
            try:
                subprocess.run(
                    ["git", "merge", "--ff-only", f"origin/{self.config.channel}"],
                    cwd=self.flutter_root,
                    check=True,
                    capture_output=True,
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
            console.print(
                "  ⚠️  Flutter repo has diverged; skipping update (per --flutter-update skip)"
            )
            return

        console.print("  ⚠️  Flutter repo has diverged from origin")

        # Get commit counts
        try:
            result = subprocess.run(
                [
                    "git",
                    "rev-list",
                    "--left-right",
                    "--count",
                    f"origin/{self.config.channel}...{self.config.channel}",
                ],
                cwd=self.flutter_root,
                capture_output=True,
                text=True,
                check=True,
            )

            counts = result.stdout.strip().split()
            if len(counts) == 2:
                left_ahead = counts[0]
                right_ahead = counts[1]
                console.print(
                    f"  📊 Local ahead by: {right_ahead}, origin ahead by: {left_ahead}"
                )

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
                    capture_output=True,
                )
                console.print("  ✅ Flutter reset to origin")
            except subprocess.CalledProcessError as e:
                raise FlutterInstallationError(f"Failed to reset Flutter: {e}")

    def _ensure_flutter_path(self) -> None:
        """Ensure Flutter is in PATH."""
        console.print("  🔧 Configuring Flutter PATH...")

        flutter_path = f'export PATH="{self.flutter_root}/bin:$PATH"'
        flutter_path_pattern = (
            r'export\s+PATH=["\']([^"\']*flutter[^"\']*/bin):\$PATH["\']'
        )

        for profile in self.path_profiles:
            if profile.exists():
                with open(profile, "r") as f:
                    content = f.read()

                existing_match = re.search(flutter_path_pattern, content)
                if existing_match:
                    existing_flutter_path = existing_match.group(1)
                    normalized_existing_path = self._normalize_flutter_bin_path(
                        existing_flutter_path
                    )
                    if normalized_existing_path == self._expected_flutter_bin_path():
                        console.print(f"  ✅ Flutter PATH already in {profile.name}")
                    else:
                        console.print(
                            f"  ⚠️  Different Flutter PATH in {profile.name}: {existing_flutter_path}"
                        )
                    continue

                with open(profile, "a") as f:
                    f.write(f"\n{flutter_path}\n")
                console.print(f"  ✅ Flutter PATH added to {profile.name}")
            else:
                with open(profile, "w") as f:
                    f.write(f"{flutter_path}\n")
                console.print(f"  ✅ Flutter PATH added to {profile.name}")

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
                check=False,
            )

            # Flutter doctor outputs to stdout, but may also use stderr
            output = result.stdout or result.stderr or ""

            if result.returncode == 0:
                console.print("  ✅ Flutter doctor passed")
            else:
                console.print("  ⚠️  Flutter doctor found issues:")
                # Print output (stdout takes precedence, fallback to stderr)
                if result.stdout:
                    console.print(result.stdout)
                if result.stderr:
                    console.print(result.stderr)

                # Check for Android licenses in either stream
                combined_output = output
                if "Some Android licenses not accepted" in combined_output:
                    console.print("  📱 Android licenses need acceptance")
                    self._handle_android_licenses()
                if self.platform == "linux":
                    self._print_linux_doctor_guidance(combined_output)

        except Exception as e:
            console.print(f"  ⚠️  Flutter doctor warning: {e}")

    def _print_linux_doctor_guidance(self, output: str) -> None:
        """Print Linux-specific remediation hints for doctor issues."""
        if "Linux toolchain" in output or "Unable to locate" in output:
            console.print("  🐧 Linux toolchain issues detected")
            console.print(
                "  ℹ️  Ensure required packages are installed via apt (git curl unzip xz-utils zip libglu1-mesa clang cmake ninja-build pkg-config)"
            )

    def _handle_android_licenses(self) -> None:
        """Handle Android license acceptance."""
        if "android" not in self.config.platforms:
            return

        console.print("  📱 Android licenses not accepted")
        console.print(
            "  ℹ️  You can run 'flutter doctor --android-licenses' later to accept licenses"
        )

    def check_only(self) -> bool:
        """Check Flutter SDK installation without installing/updating. Returns True if all checks pass."""
        all_ok = True

        # Check if Flutter is installed
        console.print("  🔍 Checking Flutter SDK installation...")
        if not self.flutter_root.exists() or not (self.flutter_root / ".git").exists():
            console.print(f"  ❌ Flutter SDK not found at {self.flutter_root}")
            all_ok = False
        else:
            console.print(f"  ✅ Flutter SDK found at {self.flutter_root}")

            # Check Flutter binary
            flutter_bin = self.flutter_root / "bin" / "flutter"
            if not flutter_bin.exists():
                console.print("  ❌ Flutter binary not found")
                all_ok = False
            else:
                console.print("  ✅ Flutter binary found")

        # Check Flutter PATH configuration
        console.print("  🔧 Checking Flutter PATH configuration...")
        flutter_path_pattern = (
            r'export\s+PATH=["\']([^"\']*flutter[^"\']*/bin):\$PATH["\']'
        )
        expected_path = self._expected_flutter_bin_path()
        found_expected = False
        found_any = False
        for profile in self.path_profiles:
            if not profile.exists():
                continue

            with open(profile, "r") as f:
                content = f.read()

            existing_match = re.search(flutter_path_pattern, content)
            if existing_match:
                found_any = True
                existing_flutter_path = existing_match.group(1)
                normalized_existing_path = self._normalize_flutter_bin_path(
                    existing_flutter_path
                )
                if normalized_existing_path == expected_path:
                    console.print(
                        f"  ✅ Flutter PATH correctly configured in {profile.name}"
                    )
                    found_expected = True
                else:
                    console.print(
                        f"  ⚠️  Different Flutter PATH in {profile.name}: {existing_flutter_path}"
                    )

        if not found_any:
            console.print("  ⚠️  Flutter PATH not found in shell profiles")
            all_ok = False
        elif not found_expected:
            all_ok = False

        # Check if Flutter is up to date (if installed)
        if self.flutter_root.exists() and (self.flutter_root / ".git").exists():
            console.print(
                f"  🔄 Checking Flutter update status ({self.config.channel})..."
            )
            try:
                # Fetch latest changes
                subprocess.run(
                    ["git", "fetch", "origin", "--prune"],
                    cwd=self.flutter_root,
                    check=True,
                    capture_output=True,
                )

                # Check if local branch is up to date
                result = subprocess.run(
                    [
                        "git",
                        "rev-list",
                        "--left-right",
                        "--count",
                        f"origin/{self.config.channel}...{self.config.channel}",
                    ],
                    cwd=self.flutter_root,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                counts = result.stdout.strip().split()
                if len(counts) == 2:
                    left_ahead = int(counts[0])
                    right_ahead = int(counts[1])
                    if left_ahead == 0 and right_ahead == 0:
                        console.print("  ✅ Flutter is up to date")
                    elif left_ahead > 0:
                        console.print(
                            f"  ⚠️  Flutter is {left_ahead} commit(s) behind origin"
                        )
                    elif right_ahead > 0:
                        console.print(
                            f"  ℹ️  Flutter has {right_ahead} local commit(s) ahead of origin"
                        )
            except subprocess.CalledProcessError:
                console.print("  ⚠️  Could not check Flutter update status")

        # Run flutter doctor
        if (
            self.flutter_root.exists()
            and (self.flutter_root / "bin" / "flutter").exists()
        ):
            console.print("  🏥 Running Flutter doctor...")
            try:
                result = subprocess.run(
                    [str(self.flutter_root / "bin" / "flutter"), "doctor", "-v"],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                # Flutter doctor outputs to stdout, but may also use stderr
                output = result.stdout or result.stderr or ""

                if result.returncode == 0:
                    console.print("  ✅ Flutter doctor passed")
                else:
                    console.print("  ⚠️  Flutter doctor found issues:")
                    # Print only the summary, not the full verbose output
                    # Check both stdout (primary) and stderr (secondary)
                    lines = output.split("\n")
                    summary_lines = [
                        line
                        for line in lines
                        if "•" in line or "!" in line or "✗" in line or "✓" in line
                    ]
                    if summary_lines:
                        for line in summary_lines[:10]:  # Limit output
                            console.print(f"    {line}")
                    all_ok = False
            except Exception as e:
                console.print(f"  ⚠️  Flutter doctor warning: {e}")
                all_ok = False

        return all_ok
