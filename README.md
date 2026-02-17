# Flutter Setup CLI

A modern Python CLI tool for setting up complete Flutter development environments on macOS and Linux. This tool automates Flutter SDK setup, prerequisite checks, and project bootstrapping with practical defaults.

## Features

- 🚀 **Automated Setup**: Complete Flutter development environment setup in minutes
- 🦋 **Flutter SDK Management**: Install, update, and manage Flutter SDK with multiple channels
- 🛠️ **Prerequisites Installation**: Platform-aware prerequisite checks and installation flows for macOS and Linux
- 📱 **Multi-Platform Support**: Create projects for iOS, Android, macOS, Linux, Windows, and Web
- 🔧 **Development Environment**: Pre-configured VS Code/Cursor settings, testing framework, and CI/CD
- 🎯 **Best Practices**: Industry-standard project structure with linting, testing, and analysis tools
- 🧪 **Testing Ready**: Built-in test structure for unit, widget, and integration tests
- 📦 **Easy Deployment**: Simple Python package that can be easily installed on any developer machine

## Quick Start

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd flutter-setup

# Install the package
uv pip install -e .

# Or install directly from GitHub (when published)
uv pip install git+https://github.com/markcallen/flutter-setup.git
```

### Linux Prerequisites (Ubuntu/Debian)

For Linux hosts, ensure APT is available and `sudo` is configured:

```bash
sudo apt-get update
sudo apt-get install -y git curl unzip xz-utils zip libglu1-mesa clang cmake ninja-build pkg-config
```

### Configuration Setup

Before your first use, initialize your configuration:

```bash
# Interactive configuration setup
flutter-setup init
```

This will:
- Detect Flutter location from environment variables or PATH
- Prompt for Flutter channel (stable/beta)
- Prompt for organization ID
- Create config file at `~/.config/flutter-setup/config.yaml`

You can run `flutter-setup init` again anytime to update your configuration.

### Basic Usage

```bash
# Create a new Flutter app with iOS, Android, and Web support
flutter-setup setup MyAwesomeApp ios android web

# Create a plugin with specific language preferences
flutter-setup setup MyPlugin --template plugin --ios-language objc --android-language java ios android

# Use beta channel and custom organization
flutter-setup setup MyApp --channel beta --org com.mycompany ios android macos

# Preview what would happen (dry run)
flutter-setup setup MyApp --dry-run ios android
```

## Commands

### `init` - Configuration Setup
Initialize or update your configuration file:

```bash
flutter-setup init              # Create or update config interactively
flutter-setup init --force      # Overwrite existing config
```

The config file is stored at `~/.config/flutter-setup/config.yaml` (or `$XDG_CONFIG_HOME/flutter-setup/config.yaml`).

### `setup` - Project Setup
Set up a new Flutter project:

```bash
flutter-setup setup MyApp ios android web
```

## Command Line Options

| Option | Description | Default | Config File |
|--------|-------------|---------|-------------|
| `--org` | Organization identifier | `com.example` | ✅ |
| `--channel` | Flutter channel (stable/beta) | `stable` | ✅ |
| `--dir` | Output directory | Current directory | ❌ |
| `--template` | Project template (app/plugin) | `app` | ✅ |
| `--ios-language` | iOS language for plugins (swift/objc) | `swift` | ✅ |
| `--android-language` | Android language for plugins (kotlin/java) | `kotlin` | ✅ |
| `--flutter-update` | Flutter update mode (reset/reclone/skip) | `reset` | ✅ |
| `--dry-run` | Preview actions without executing | `false` | ❌ |
| `--verbose` | Enable verbose output | `false` | ❌ |

**Note:** Options marked with ✅ can be set in the config file via `flutter-setup init`. Command-line arguments override config file values.

## What Gets Set Up

### 1. System Prerequisites
- ✅ macOS: Xcode Command Line Tools + Homebrew + CocoaPods
- ✅ Linux (Ubuntu/Debian): APT-managed packages (`git`, `curl`, `unzip`, `xz-utils`, `zip`, `libglu1-mesa`, `clang`, `cmake`, `ninja-build`, `pkg-config`)
- ✅ Android development tools when Android platform is selected
- ✅ iOS development tools only on macOS when iOS platform is selected

### 2. Flutter SDK
- ✅ Flutter SDK installation/update
- ✅ Channel management (stable/beta)
- ✅ PATH configuration
- ✅ Flutter doctor validation

### 3. Project Structure
- ✅ Flutter project creation with specified platforms
- ✅ Package name sanitization
- ✅ Template-specific configuration

### 4. Development Environment
- ✅ VS Code/Cursor configuration
- ✅ Makefile with common commands
- ✅ Testing framework structure
- ✅ Code analysis and linting setup
- ✅ GitHub Actions CI pipeline
- ✅ Environment variable support
- ✅ Comprehensive README

## Project Structure

```
MyAwesomeApp/
├── .vscode/                 # VS Code/Cursor configuration
├── .github/workflows/       # CI/CD pipeline
├── lib/                     # Flutter source code
├── test/                    # Test files
│   ├── unit/               # Unit tests
│   └── widget/             # Widget tests
├── integration_test/        # Integration tests
├── Makefile                 # Common development commands
├── analysis_options.yaml    # Linting and analysis rules
├── .env                     # Environment variables
└── README.md               # Project documentation
```

## Development Commands

After setup, use these commands in your project:

```bash
# Run the app
make run              # Chrome (default)
make run_ios          # iOS simulator
make run_android      # Android emulator

# Testing
make test             # Unit + widget tests
make integration      # Integration tests

# Code quality
make analyze          # Flutter analyze
```

## Configuration

The tool uses a YAML-based configuration file that stores your preferences:

**Location:** `~/.config/flutter-setup/config.yaml` (or `$XDG_CONFIG_HOME/flutter-setup/config.yaml`)

**Example config:**
```yaml
flutter:
  location: ~/development/flutter
  channel: stable
  update_mode: reset

project:
  org: com.mycompany
  template: app
  ios_language: swift
  android_language: kotlin
```

**Configuration Features:**
- ✅ XDG Base Directory Specification compliant
- ✅ Automatic Flutter location detection from environment
- ✅ Interactive setup via `flutter-setup init`
- ✅ Command-line arguments override config values
- ✅ Persistent settings across sessions

## Architecture

The package is built with modern Python best practices:

- **Modular Design**: Separate modules for different concerns
- **Type Safety**: Full type hints with mypy support
- **Error Handling**: Comprehensive exception handling
- **Rich CLI**: Beautiful terminal output with progress indicators
- **Configuration**: Flexible configuration system with XDG support
- **Testing**: Built-in test structure and CI/CD

## Development

### Prerequisites

- Python 3.12+
- uv package manager

### Supported Hosts

- macOS (Darwin)
- Linux (Ubuntu/Debian via APT)

### Known Limitations

- Fedora/DNF support is planned but not yet implemented.
- iOS setup is not available on Linux hosts.

### Setup Development Environment

```bash
# Clone and install
git clone <repo-url>
cd flutter-setup
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .

# Type checking
uv run mypy .
```

### Project Structure

```
flutter-setup/
├── flutter_setup/           # Main package
│   ├── __init__.py
│   ├── cli.py              # CLI entry point
│   ├── config.py            # Configuration management
│   ├── core.py              # Main orchestration
│   ├── exceptions.py        # Custom exceptions
│   ├── prerequisites.py     # System prerequisites
│   ├── flutter_manager.py   # Flutter SDK management
│   ├── project_creator.py   # Project creation
│   └── bootstrap.py         # Development environment setup
├── pyproject.toml           # Package configuration
├── README.md                # This file
└── test_cli.py             # Simple test script
```

## Comparison with Bash Script

This Python CLI package provides several advantages over the original bash script:

| Feature | Bash Script | Python CLI |
|---------|-------------|------------|
| **Installation** | Manual download | `pip install` |
| **Dependencies** | Manual management | Automatic with uv |
| **Error Handling** | Basic | Comprehensive |
| **Testing** | None | Full test suite |
| **Type Safety** | None | Full mypy support |
| **Packaging** | Manual | Standard Python package |
| **Distribution** | Manual | PyPI ready |
| **Maintenance** | Harder | Easier with Python tools |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the PRD.md for detailed requirements

---

**Built with ❤️ for the Flutter community**
