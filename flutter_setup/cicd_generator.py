"""CI/CD code generation for Flutter projects."""

import re
import subprocess
from pathlib import Path

from rich.console import Console

from .config import Config

console = Console()


class CicdGenerator:
    """Generates CI/CD workflows and configuration for Flutter projects."""

    def __init__(self, config: Config, force: bool = False) -> None:
        """Initialize CicdGenerator."""
        self.config = config
        self.force = force
        self.project_path = config.project_path
        self.project_name = config.project_name
        self.package_name = config.package_name
        self.platforms = [p.lower() for p in config.platforms]
        self.flutter_channel = config.channel
        self.flutter_version = self._get_current_flutter_version()
        self.needs_codegen = config.database == "sqlite"

    def _get_current_flutter_version(self) -> str:
        """Get the current Flutter version from the installed Flutter SDK."""
        try:
            flutter_bin = self.config.flutter_location / "bin" / "flutter"
            if not flutter_bin.exists():
                # Fallback: try to find flutter in PATH
                import shutil

                flutter_path = shutil.which("flutter")
                if not flutter_path:
                    console.print(
                        "  ⚠️  Flutter not found, using 'stable' as default version"
                    )
                    return "stable"
                flutter_bin = Path(flutter_path)

            # Run flutter --version to get the version
            result = subprocess.run(
                [str(flutter_bin), "--version"],
                capture_output=True,
                text=True,
                check=False,
            )

            # Parse version from output
            # Output format: "Flutter 3.24.0 • channel stable • ..."
            output = result.stdout or result.stderr or ""
            match = re.search(r"Flutter\s+([\d.]+)", output)
            if match:
                version = match.group(1)
                console.print(f"  ℹ️  Detected Flutter version: {version}")
                return version
            else:
                console.print(
                    "  ⚠️  Could not parse Flutter version, using '3.38.0' as default"
                )
                return "3.38.0"
        except Exception as e:
            console.print(
                f"  ⚠️  Error detecting Flutter version: {e}, using '3.38.0' as default"
            )
            return "3.38.0"

    def _write_workflow_file(self, filepath: Path, content: str) -> None:
        """Write a workflow file, skipping if it exists and force is False."""
        if filepath.exists() and not self.force:
            console.print(
                f"  ⚠️  {filepath.name} already exists — skipping (use --force to overwrite)"
            )
            return
        filepath.write_text(content)

    def _codegen_step(self) -> str:
        """Return the build_runner code generation step for workflows that need it."""
        if not self.needs_codegen:
            return ""
        return """
      - name: Generate code
        run: dart run build_runner build --delete-conflicting-outputs
"""

    def generate_cicd(self) -> None:
        """Generate all CI/CD files."""
        if self.config.dry_run:
            console.print("[yellow]DRY RUN: Would generate CI/CD files[/yellow]")
            return

        console.print("  🔧 Generating CI/CD workflows and configuration...")

        # Create .github directory structure
        github_dir = self.project_path / ".github"
        workflows_dir = github_dir / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)

        # Generate workflows
        self._generate_lint_workflow(workflows_dir)
        self._generate_format_workflow(workflows_dir)
        self._generate_test_workflow(workflows_dir)
        self._generate_build_workflows(workflows_dir)

        # Generate dependabot configuration
        self._generate_dependabot(github_dir)

        # Generate setup documentation
        self._generate_setup_docs(github_dir)

        # Generate git hooks for local quality gates
        self._generate_git_hooks()

        console.print("  ✅ CI/CD workflows and configuration generated")

    def _generate_lint_workflow(self, workflows_dir: Path) -> None:
        """Generate lint workflow for flutter analyze."""
        workflow_content = f"""name: Lint

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  push:
    branches: ["main"]

concurrency:
  group: lint-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:
  lint:
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: ${{{{ secrets.FLUTTER_CHANNEL || 'stable' }}}}
          version: ${{{{ secrets.FLUTTER_VERSION || '{self.flutter_version}' }}}}

      - name: Cache pub
        uses: actions/cache@v4
        with:
          path: ~/.pub-cache
          key: pub-${{{{ runner.os }}}}-${{{{ hashFiles('**/pubspec.yaml', '**/pubspec.lock') }}}}

      - name: Install dependencies
        run: flutter pub get

      - name: Analyze
        run: flutter analyze

      - name: Comment PR with results
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({{
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ Linting failed. Please run `flutter analyze` locally and fix the issues.'
            }})
"""

        workflow_file = workflows_dir / "lint.yml"
        self._write_workflow_file(workflow_file, workflow_content)

    def _generate_format_workflow(self, workflows_dir: Path) -> None:
        """Generate format workflow for dart format."""
        workflow_content = f"""name: Format

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  push:
    branches: ["main"]

concurrency:
  group: format-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:
  format:
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: ${{{{ secrets.FLUTTER_CHANNEL || 'stable' }}}}
          version: ${{{{ secrets.FLUTTER_VERSION || '{self.flutter_version}' }}}}

      - name: Cache pub
        uses: actions/cache@v4
        with:
          path: ~/.pub-cache
          key: pub-${{{{ runner.os }}}}-${{{{ hashFiles('**/pubspec.yaml', '**/pubspec.lock') }}}}

      - name: Install dependencies
        run: flutter pub get

      - name: Check formatting
        run: dart format --set-exit-if-changed .

      - name: Comment PR with results
        if: github.event_name == 'pull_request' && failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.createComment({{
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ Code formatting check failed. Please run `dart format .` locally and commit the changes.'
            }})
"""

        workflow_file = workflows_dir / "format.yml"
        self._write_workflow_file(workflow_file, workflow_content)

    def _generate_test_workflow(self, workflows_dir: Path) -> None:
        """Generate test workflow."""
        workflow_content = f"""name: Test

on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  push:
    branches: ["main"]

concurrency:
  group: test-${{{{ github.ref }}}}
  cancel-in-progress: true

jobs:
  test:
    if: github.event_name != 'pull_request' || github.event.pull_request.draft == false
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: ${{{{ secrets.FLUTTER_CHANNEL || 'stable' }}}}
          version: ${{{{ secrets.FLUTTER_VERSION || '{self.flutter_version}' }}}}

      - name: Cache pub
        uses: actions/cache@v4
        with:
          path: ~/.pub-cache
          key: pub-${{{{ runner.os }}}}-${{{{ hashFiles('**/pubspec.yaml', '**/pubspec.lock') }}}}

      - name: Install dependencies
        run: flutter pub get
{self._codegen_step()}
      - name: Run unit tests
        run: flutter test --coverage

      - name: Upload coverage
        if: github.event_name == 'pull_request'
        uses: codecov/codecov-action@v5
        with:
          token: ${{{{ secrets.CODECOV_TOKEN }}}}
          files: ./coverage/lcov.info
          fail_ci_if_error: false
"""

        workflow_file = workflows_dir / "test.yml"
        self._write_workflow_file(workflow_file, workflow_content)

    def _generate_build_workflows(self, workflows_dir: Path) -> None:
        """Generate build workflows for enabled platforms."""
        if "ios" in self.platforms:
            self._generate_ios_build_workflow(workflows_dir)
        if "android" in self.platforms:
            self._generate_android_build_workflow(workflows_dir)
        if "web" in self.platforms:
            self._generate_web_build_workflow(workflows_dir)
        if "macos" in self.platforms:
            self._generate_macos_build_workflow(workflows_dir)
        if "linux" in self.platforms:
            self._generate_linux_build_workflow(workflows_dir)
        if "windows" in self.platforms:
            self._generate_windows_build_workflow(workflows_dir)

    def _generate_ios_build_workflow(self, workflows_dir: Path) -> None:
        """Generate iOS build workflow."""
        workflow_content = f"""name: Build iOS

on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-ios:
    runs-on: macos-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: ${{{{ secrets.FLUTTER_CHANNEL || 'stable' }}}}
          version: ${{{{ secrets.FLUTTER_VERSION || '{self.flutter_version}' }}}}

      - name: Cache pub
        uses: actions/cache@v4
        with:
          path: ~/.pub-cache
          key: pub-${{{{ runner.os }}}}-${{{{ hashFiles('**/pubspec.yaml', '**/pubspec.lock') }}}}

      - name: Install dependencies
        run: flutter pub get
{self._codegen_step()}
      - name: Build iOS
        run: flutter build ios --release --no-codesign

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ios-build
          path: build/ios/iphoneos/Runner.app
          if-no-files-found: error
"""

        workflow_file = workflows_dir / "build-ios.yml"
        self._write_workflow_file(workflow_file, workflow_content)

    def _generate_android_build_workflow(self, workflows_dir: Path) -> None:
        """Generate Android build workflow."""
        workflow_content = f"""name: Build Android

on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-android:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: ${{{{ secrets.FLUTTER_CHANNEL || 'stable' }}}}
          version: ${{{{ secrets.FLUTTER_VERSION || '{self.flutter_version}' }}}}

      - name: Cache pub
        uses: actions/cache@v4
        with:
          path: ~/.pub-cache
          key: pub-${{{{ runner.os }}}}-${{{{ hashFiles('**/pubspec.yaml', '**/pubspec.lock') }}}}

      - name: Install dependencies
        run: flutter pub get
{self._codegen_step()}
      - name: Build APK
        run: flutter build apk --release

      - name: Build AAB
        run: flutter build appbundle --release

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: android-apk
          path: build/app/outputs/flutter-apk/app-release.apk
          if-no-files-found: error

      - name: Upload AAB
        uses: actions/upload-artifact@v4
        with:
          name: android-aab
          path: build/app/outputs/bundle/release/app-release.aab
          if-no-files-found: error
"""

        workflow_file = workflows_dir / "build-android.yml"
        self._write_workflow_file(workflow_file, workflow_content)

    def _generate_web_build_workflow(self, workflows_dir: Path) -> None:
        """Generate Web build workflow."""
        workflow_content = f"""name: Build Web

on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-web:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: ${{{{ secrets.FLUTTER_CHANNEL || 'stable' }}}}
          version: ${{{{ secrets.FLUTTER_VERSION || '{self.flutter_version}' }}}}

      - name: Cache pub
        uses: actions/cache@v4
        with:
          path: ~/.pub-cache
          key: pub-${{{{ runner.os }}}}-${{{{ hashFiles('**/pubspec.yaml', '**/pubspec.lock') }}}}

      - name: Install dependencies
        run: flutter pub get
{self._codegen_step()}
      - name: Build Web
        run: flutter build web --release

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: web-build
          path: build/web
          if-no-files-found: error
"""

        workflow_file = workflows_dir / "build-web.yml"
        self._write_workflow_file(workflow_file, workflow_content)

    def _generate_macos_build_workflow(self, workflows_dir: Path) -> None:
        """Generate macOS build workflow."""
        workflow_content = f"""name: Build macOS

on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: ${{{{ secrets.FLUTTER_CHANNEL || 'stable' }}}}
          version: ${{{{ secrets.FLUTTER_VERSION || '{self.flutter_version}' }}}}

      - name: Cache pub
        uses: actions/cache@v4
        with:
          path: ~/.pub-cache
          key: pub-${{{{ runner.os }}}}-${{{{ hashFiles('**/pubspec.yaml', '**/pubspec.lock') }}}}

      - name: Install dependencies
        run: flutter pub get
{self._codegen_step()}
      - name: Build macOS
        run: flutter build macos --release

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: macos-build
          path: build/macos/Build/Products/Release
          if-no-files-found: error
"""

        workflow_file = workflows_dir / "build-macos.yml"
        self._write_workflow_file(workflow_file, workflow_content)

    def _generate_linux_build_workflow(self, workflows_dir: Path) -> None:
        """Generate Linux build workflow."""
        workflow_content = f"""name: Build Linux

on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: ${{{{ secrets.FLUTTER_CHANNEL || 'stable' }}}}
          version: ${{{{ secrets.FLUTTER_VERSION || '{self.flutter_version}' }}}}

      - name: Cache pub
        uses: actions/cache@v4
        with:
          path: ~/.pub-cache
          key: pub-${{{{ runner.os }}}}-${{{{ hashFiles('**/pubspec.yaml', '**/pubspec.lock') }}}}

      - name: Install Linux dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y \\
            libgtk-3-dev \\
            libayatana-appindicator3-dev \\
            clang \\
            cmake \\
            ninja-build \\
            pkg-config \\
            liblzma-dev

      - name: Install dependencies
        run: flutter pub get
{self._codegen_step()}
      - name: Build Linux
        run: flutter build linux --release

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: linux-build
          path: build/linux/x64/release/bundle
          if-no-files-found: error
"""

        workflow_file = workflows_dir / "build-linux.yml"
        self._write_workflow_file(workflow_file, workflow_content)

    def _generate_windows_build_workflow(self, workflows_dir: Path) -> None:
        """Generate Windows build workflow."""
        workflow_content = f"""name: Build Windows

on:
  workflow_dispatch:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Flutter
        uses: subosito/flutter-action@v2
        with:
          channel: ${{{{ secrets.FLUTTER_CHANNEL || 'stable' }}}}
          version: ${{{{ secrets.FLUTTER_VERSION || '{self.flutter_version}' }}}}

      - name: Cache pub
        uses: actions/cache@v4
        with:
          path: ~/.pub-cache
          key: pub-${{{{ runner.os }}}}-${{{{ hashFiles('**/pubspec.yaml', '**/pubspec.lock') }}}}

      - name: Install dependencies
        run: flutter pub get
{self._codegen_step()}
      - name: Build Windows
        run: flutter build windows --release

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: windows-build
          path: build/windows/x64/runner/Release
          if-no-files-found: error
"""

        workflow_file = workflows_dir / "build-windows.yml"
        self._write_workflow_file(workflow_file, workflow_content)

    def _generate_dependabot(self, github_dir: Path) -> None:
        """Generate dependabot.yml configuration."""
        dependabot_content = """version: 2
updates:
  # Enable version updates for Flutter/Dart dependencies
  - package-ecosystem: "pub"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    groups:
      flutter-dependencies:
        patterns:
          - "flutter*"
          - "dart*"
      dev-dependencies:
        patterns:
          - "*_test"
          - "*test*"
          - "mockito"
          - "build_runner"

  # Enable version updates for GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
"""

        dependabot_file = github_dir / "dependabot.yml"
        self._write_workflow_file(dependabot_file, dependabot_content)

    def _generate_setup_docs(self, github_dir: Path) -> None:
        """Generate CI/CD setup documentation."""
        docs_content = f"""# CI/CD Setup Guide

This document provides instructions for setting up and configuring the CI/CD workflows for {self.project_name}.

## Overview

The CI/CD workflows in this repository include:

- **Lint Workflow** (`lint.yml`): Runs `flutter analyze` on pull requests and pushes
- **Format Workflow** (`format.yml`): Checks code formatting with `dart format`
- **Test Workflow** (`test.yml`): Runs unit tests
- **Build Workflows**: Platform-specific build workflows for enabled platforms

## Prerequisites

1. **GitHub Actions enabled**: Ensure GitHub Actions are enabled in your repository settings
2. **Flutter Configuration**: Set Flutter channel and version secrets (optional, defaults to `stable` channel)

## Configuration

### GitHub Secrets

Go to **Settings → Secrets → Actions** and create the following secrets:

| Secret | Value | Description | Required |
|--------|-------|-------------|----------|
| `FLUTTER_CHANNEL` | `stable`, `beta`, or `dev` | Flutter channel to use in workflows. Defaults to `stable` if not set. | No |
| `FLUTTER_VERSION` | Specific version (e.g., `3.24.0`) or empty | Flutter SDK version to use. If not set, defaults to the Flutter version that was installed when the project was created ({self.flutter_version}). Examples: `3.24.0`, `3.24.1`, `3.25.0`. Check [Flutter releases](https://docs.flutter.dev/release/archive) for available versions. | No |
| `CODECOV_TOKEN` | Codecov upload token | Token for uploading test coverage reports to Codecov. See [Codecov Token Setup](#codecov-token-setup) below for instructions. | No |

**Note**: If `FLUTTER_VERSION` is not set, the workflow will use the Flutter version that was installed when the project was created ({self.flutter_version}) as the default. Setting a specific version ensures consistent builds across all CI runs and allows you to override the default version.

### Codecov Token Setup

To enable test coverage reporting in pull requests, you'll need to set up a Codecov token:

1. **Sign in to Codecov**:
   - Go to [codecov.io](https://codecov.io) and sign in with your GitHub account
   - Grant Codecov access to your repository when prompted

2. **Get your upload token**:
   - Navigate to your repository on Codecov (or go to **Settings → Integrations**)
   - Copy your repository's upload token (it will look like: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`)

3. **Add the secret to GitHub**:
   - Go to your repository on GitHub
   - Navigate to **Settings → Secrets and variables → Actions**
   - Click **New repository secret**
   - Name: `CODECOV_TOKEN`
   - Value: Paste your Codecov upload token
   - Click **Add secret**

**Note**: The Codecov token is optional. The test workflow will still run tests without it, but coverage reports won't be uploaded to Codecov. If you don't plan to use Codecov, you can skip this step.

### Additional Secrets (for App Store Deployment)

If you plan to deploy to app stores or use code signing, you'll need to configure additional secrets:

#### iOS App Store Connect (for TestFlight/App Store deployment)

1. Go to [App Store Connect API Keys](https://appstoreconnect.apple.com/access/api)
2. Create a new API key
3. Download the `.p8` file (⚠️ only available once!)
4. Convert to Base64:
   ```bash
   base64 -i AuthKey_ABC12345.p8 | pbcopy
   ```
5. Add the following secrets in **Settings → Secrets → Actions**:

| Secret | Description |
|--------|-------------|
| `APPLE_NOTARY_KEY_ID` | Key ID (example: ABC123DEFG) |
| `APPLE_NOTARY_ISSUER_ID` | Issuer ID (UUID on App Store Connect) |
| `APPLE_NOTARY_KEY_BASE64` | Base64 of the `.p8` key |

#### Google Play Console (for Play Store deployment)

1. Go to [Google Play Console](https://play.google.com/console)
2. Navigate to **Setup → API access**
3. Create a service account
4. Download the JSON key file
5. Add the following secret in **Settings → Secrets → Actions**:

| Secret | Description |
|--------|-------------|
| `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` | Contents of the JSON key file |

## Workflow Triggers

### Automatic Triggers

- **Lint, Format, Test**: Run on pull requests and pushes to `main` branch
- **Build Workflows**: Run on version tags (`v*.*.*`) only — not on every push to `main`

### Manual Triggers

All build workflows can be triggered manually via **Actions → [Workflow Name] → Run workflow**

## Platform-Specific Notes

{self._generate_platform_notes()}

## Troubleshooting

### Common Issues

1. **Workflow fails with "Flutter not found" or version error**
   - Ensure the `FLUTTER_CHANNEL` secret is set correctly (`stable`, `beta`, or `dev`)
   - If using `FLUTTER_VERSION`, verify the version exists for the specified channel
   - Check [Flutter releases](https://docs.flutter.dev/release/archive) for valid version numbers
   - If `FLUTTER_VERSION` is set incorrectly, remove it to use the latest version from the channel

2. **Build fails on specific platform**
   - Verify that the platform is enabled in your `pubspec.yaml`
   - Check platform-specific dependencies are installed

3. **Dependabot not creating PRs**
   - Ensure Dependabot is enabled in repository settings
   - Check that `dependabot.yml` is in the `.github` directory

### Getting Help

- Check workflow logs in the **Actions** tab
- Review Flutter documentation for platform-specific requirements
- Consult GitHub Actions documentation for workflow syntax

## Security Best Practices

1. **Never commit secrets**: Always use GitHub Secrets for sensitive information
2. **Review Dependabot PRs**: Regularly review and merge dependency updates
3. **Limit workflow permissions**: Use minimal required permissions in workflows
4. **Regular updates**: Keep GitHub Actions versions up to date

## Next Steps

1. Set up repository variables (if needed)
2. Configure secrets (if deploying to app stores)
3. Push your code to trigger workflows
4. Monitor workflow runs in the **Actions** tab
"""

        docs_file = github_dir / "CI_CD_SETUP.md"
        self._write_workflow_file(docs_file, docs_content)

    def _generate_platform_notes(self) -> str:
        """Generate platform-specific notes for the documentation."""
        notes = []
        if "ios" in self.platforms:
            notes.append(
                "### iOS\n"
                "- Requires macOS runner\n"
                "- Builds are unsigned by default\n"
                "- For code signing, configure Apple Developer certificates"
            )
        if "android" in self.platforms:
            notes.append(
                "### Android\n"
                "- Builds both APK and AAB formats\n"
                "- Requires Java 17\n"
                "- For Play Store deployment, configure Google Play Console API"
            )
        if "web" in self.platforms:
            notes.append(
                "### Web\n"
                "- Builds optimized web assets\n"
                "- Can be deployed to any static hosting service"
            )
        if "macos" in self.platforms:
            notes.append(
                "### macOS\n"
                "- Requires macOS runner\n"
                "- Builds unsigned .app bundles by default\n"
                "- For distribution, configure code signing and notarization"
            )
        if "linux" in self.platforms:
            notes.append(
                "### Linux\n"
                "- Installs required system dependencies automatically\n"
                "- Builds bundle directory structure\n"
                "- Can be packaged as .deb, .rpm, or AppImage"
            )
        if "windows" in self.platforms:
            notes.append(
                "### Windows\n"
                "- Builds Windows executable\n"
                "- Can be packaged as MSIX or installer"
            )
        return "\n\n".join(notes) if notes else "No platform-specific notes."

    def _generate_git_hooks(self) -> None:
        """Generate .git-hooks/ scripts that mirror the CI quality gates locally."""
        hooks_dir = self.project_path / ".git-hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        pre_commit = hooks_dir / "pre-commit"
        if not pre_commit.exists() or self.force:
            pre_commit.write_text(
                "#!/usr/bin/env bash\n"
                "# pre-commit: run dart format to catch style issues before CI.\n"
                "set -euo pipefail\n"
                "\n"
                'FLUTTER_BIN="${FLUTTER_ROOT:-}/bin"\n'
                'DART="${FLUTTER_BIN}/dart"\n'
                '[ -x "$DART" ] || DART="$(command -v dart 2>/dev/null)" || '
                '{ echo "dart not found"; exit 1; }\n'
                "\n"
                'echo "pre-commit: dart format --set-exit-if-changed ."\n'
                '"$DART" format --set-exit-if-changed . || {\n'
                '  echo ""\n'
                '  echo "Formatting errors found. Run:  dart format ."\n'
                '  echo "then re-stage the changed files and commit again."\n'
                "  exit 1\n"
                "}\n"
            )
            pre_commit.chmod(0o755)

        pre_push = hooks_dir / "pre-push"
        if not pre_push.exists() or self.force:
            pre_push.write_text(
                "#!/usr/bin/env bash\n"
                "# pre-push: run flutter analyze before pushing to catch lint issues.\n"
                "set -euo pipefail\n"
                "\n"
                'FLUTTER_BIN="${FLUTTER_ROOT:-}/bin"\n'
                'FLUTTER="${FLUTTER_BIN}/flutter"\n'
                '[ -x "$FLUTTER" ] || FLUTTER="$(command -v flutter 2>/dev/null)" || '
                '{ echo "flutter not found"; exit 1; }\n'
                "\n"
                'echo "pre-push: flutter analyze"\n'
                '"$FLUTTER" analyze || {\n'
                '  echo ""\n'
                '  echo "flutter analyze reported issues. Fix them before pushing."\n'
                "  exit 1\n"
                "}\n"
            )
            pre_push.chmod(0o755)

        console.print(
            "  ✅ Git hooks created in .git-hooks/ — "
            "run `git config core.hooksPath .git-hooks` to activate"
        )
