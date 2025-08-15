# Flutter Setup CLI

A modern Python CLI tool for setting up complete Flutter development environments on macOS. This tool automates the entire process of installing Flutter SDK, configuring development tools, and bootstrapping new Flutter projects with industry best practices.

## Features

- 🚀 **Automated Setup**: Complete Flutter development environment setup in minutes
- 🦋 **Flutter SDK Management**: Install, update, and manage Flutter SDK with multiple channels
- 🛠️ **Prerequisites Installation**: Automatically install Xcode tools, Homebrew, and platform-specific dependencies
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
uv pip install git+https://github.com/yourusername/flutter-setup.git
```

### Basic Usage

```bash
# Create a new Flutter app with iOS, Android, and Web support
flutter-setup MyAwesomeApp ios android web

# Create a plugin with specific language preferences
flutter-setup MyPlugin --template plugin --objc --java ios android

# Use beta channel and custom organization
flutter-setup MyApp --channel beta --org com.mycompany ios android macos

# Preview what would happen (dry run)
flutter-setup MyApp --dry-run ios android
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--org` | Organization identifier | `com.example` |
| `--channel` | Flutter channel (stable/beta) | `stable` |
| `--dir` | Output directory | Current directory |
| `--template` | Project template (app/plugin) | `app` |
| `--ios-language` | iOS language for plugins (swift/objc) | `swift` |
| `--android-language` | Android language for plugins (kotlin/java) | `kotlin` |
| `--flutter-update` | Flutter update mode (reset/reclone/skip) | `reset` |
| `--dry-run` | Preview actions without executing | `false` |
| `--verbose` | Enable verbose output | `false` |

## What Gets Set Up

### 1. System Prerequisites
- ✅ Xcode Command Line Tools
- ✅ Homebrew package manager
- ✅ Git, CocoaPods, and platform-specific tools
- ✅ Android development tools (if Android platform selected)
- ✅ iOS development tools (if iOS platform selected)

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

## Architecture

The package is built with modern Python best practices:

- **Modular Design**: Separate modules for different concerns
- **Type Safety**: Full type hints with mypy support
- **Error Handling**: Comprehensive exception handling
- **Rich CLI**: Beautiful terminal output with progress indicators
- **Configuration**: Flexible configuration system
- **Testing**: Built-in test structure and CI/CD

## Development

### Prerequisites

- Python 3.12+
- uv package manager

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
