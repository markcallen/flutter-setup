"""Project bootstrapping for Flutter setup."""

import subprocess
from pathlib import Path

from rich.console import Console

from .config import Config

console = Console()


class ProjectBootstrap:
    """Bootstraps development environment for Flutter projects."""
    
    def __init__(self, config: Config):
        """Initialize ProjectBootstrap."""
        self.config = config
        self.home = Path.home()
        self.flutter_root = self.home / "development" / "flutter"
    
    def bootstrap_project(self) -> None:
        """Bootstrap the development environment."""
        if self.config.dry_run:
            console.print("[yellow]DRY RUN: Would bootstrap development environment[/yellow]")
            return
        
        console.print("  🔧 Bootstrapping development & testing helpers...")
        
        # Create VS Code/Cursor configuration
        self._create_vscode_config()
        
        # Create Makefile
        self._create_makefile()
        
        # Create test structure
        self._create_test_structure()
        
        # Create analysis options
        self._create_analysis_options()
        
        # Create GitHub Actions CI
        self._create_github_actions()
        
        # Add dependencies
        self._add_dependencies()
        
        # Create environment support
        self._create_environment_support()
        
        # Create README
        self._create_readme()
        
        # Format code
        self._format_code()
    
    def _create_vscode_config(self) -> None:
        """Create VS Code/Cursor configuration files."""
        vscode_dir = self.config.project_path / ".vscode"
        vscode_dir.mkdir(exist_ok=True)
        
        # Settings
        settings = {
            "dart.flutterHotReloadOnSave": "all",
            "dart.lineLength": 100,
            "editor.formatOnSave": True,
            "editor.defaultFormatter": "Dart-Code.dart-code",
            "files.exclude": {
                "**/.dart_tool": True,
                "**/build": True
            }
        }
        
        import json
        with open(vscode_dir / "settings.json", "w") as f:
            json.dump(settings, f, indent=2)
        
        # Launch configuration
        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "Flutter Debug",
                    "request": "launch",
                    "type": "dart"
                }
            ]
        }
        
        with open(vscode_dir / "launch.json", "w") as f:
            json.dump(launch_config, f, indent=2)
        
        console.print("  ✅ VS Code/Cursor configuration created")
    
    def _create_makefile(self) -> None:
        """Create Makefile with common commands."""
        makefile_content = """run:
	flutter run -d chrome

run_ios:
	flutter run -d ios

run_android:
	flutter run -d android

analyze:
	flutter analyze

test:
	flutter test

integration:
	flutter test integration_test
"""
        
        with open(self.config.project_path / "Makefile", "w") as f:
            f.write(makefile_content)
        
        console.print("  ✅ Makefile created")
    
    def _create_test_structure(self) -> None:
        """Create test directory structure."""
        test_dir = self.config.project_path / "test"
        test_dir.mkdir(exist_ok=True)
        
        # Unit test directory
        unit_dir = test_dir / "unit"
        unit_dir.mkdir(exist_ok=True)
        
        # Widget test directory
        widget_dir = test_dir / "widget"
        widget_dir.mkdir(exist_ok=True)
        
        # Integration test directory
        integration_dir = self.config.project_path / "integration_test"
        integration_dir.mkdir(exist_ok=True)
        
        # Create sample tests
        self._create_sample_tests()
        
        console.print("  ✅ Test structure created")
    
    def _create_sample_tests(self) -> None:
        """Create sample test files."""
        # Unit test
        unit_test = '''import 'package:flutter_test/flutter_test.dart';

void main() {
  test('sanity check', () {
    expect(1 + 1, equals(2));
  });
}
'''
        
        with open(self.config.project_path / "test" / "unit" / "sanity_test.dart", "w") as f:
            f.write(unit_test)
        
        # Widget test
        widget_test = f'''import 'package:flutter_test/flutter_test.dart';
import 'package:{self.config.package_name}/main.dart';

void main() {{
  testWidgets('App loads without errors', (tester) async {{
    await tester.pumpWidget(const MyApp());
    expect(find.byType(MyApp), findsOneWidget);
  }});
}}
'''
        
        with open(self.config.project_path / "test" / "widget" / "app_widget_test.dart", "w") as f:
            f.write(widget_test)
        
        # Integration test
        integration_test = f'''import 'package:integration_test/integration_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:{self.config.package_name}/main.dart';

void main() {{
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('home page renders', (tester) async {{
    await tester.pumpWidget(const MyApp());
    expect(find.byType(MyApp), findsOneWidget);
  }});
}}
'''
        
        with open(self.config.project_path / "integration_test" / "app_test.dart", "w") as f:
            f.write(integration_test)
    
    def _create_analysis_options(self) -> None:
        """Create analysis options file."""
        analysis_content = """include: package:flutter_lints/flutter.yaml

linter:
  rules:
    avoid_print: false
    prefer_const_constructors: true
"""
        
        with open(self.config.project_path / "analysis_options.yaml", "w") as f:
            f.write(analysis_content)
        
        console.print("  ✅ Analysis options created")
    
    def _create_github_actions(self) -> None:
        """Create GitHub Actions CI workflow."""
        workflows_dir = self.config.project_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        ci_content = """name: Flutter CI

on:
  push:
    branches: [ main ]
  pull_request:

jobs:
  build:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: 'stable'
      - run: flutter pub get
      - run: flutter analyze
      - run: flutter test
"""
        
        with open(workflows_dir / "flutter-ci.yml", "w") as f:
            f.write(ci_content)
        
        console.print("  ✅ GitHub Actions CI created")
    
    def _add_dependencies(self) -> None:
        """Add required dependencies to the project."""
        try:
            # Add flutter_dotenv
            subprocess.run(
                [str(self.flutter_root / "bin" / "flutter"), "pub", "add", "flutter_dotenv"],
                cwd=self.config.project_path,
                check=False,
                capture_output=True
            )
            
            # Add dev dependencies
            subprocess.run(
                [str(self.flutter_root / "bin" / "flutter"), "pub", "add", "--dev", "flutter_lints", "integration_test"],
                cwd=self.config.project_path,
                check=False,
                capture_output=True
            )
            
            console.print("  ✅ Dependencies added")
            
        except Exception as e:
            console.print(f"  ⚠️  Dependency addition warning: {e}")
    
    def _create_environment_support(self) -> None:
        """Create environment variable support."""
        # Create .env file
        env_content = """# Example environment variables
API_URL=https://api.example.com
"""
        
        with open(self.config.project_path / ".env", "w") as f:
            f.write(env_content)
        
        # Modify main.dart to load .env
        self._modify_main_dart()
        
        console.print("  ✅ Environment support created")
    
    def _modify_main_dart(self) -> None:
        """Modify main.dart to load environment variables."""
        main_dart = self.config.project_path / "lib" / "main.dart"
        
        if not main_dart.exists():
            return
        
        try:
            with open(main_dart, "r") as f:
                content = f.read()
            
            # Add import if not present
            if "flutter_dotenv" not in content:
                # Find first import line
                lines = content.split("\n")
                import_index = -1
                for i, line in enumerate(lines):
                    if line.strip().startswith("import ") and "package:flutter" in line:
                        import_index = i
                        break
                
                if import_index >= 0:
                    lines.insert(import_index + 1, "import 'package:flutter_dotenv/flutter_dotenv.dart';")
                else:
                    lines.insert(0, "import 'package:flutter_dotenv/flutter_dotenv.dart';")
                
                # Modify main function
                modified_content = "\n".join(lines)
                modified_content = modified_content.replace(
                    "void main() {",
                    "Future<void> main() async {\n  await dotenv.load(fileName: \".env\");"
                )
                
                with open(main_dart, "w") as f:
                    f.write(modified_content)
                    
        except Exception as e:
            console.print(f"  ⚠️  Main.dart modification warning: {e}")
    
    def _create_readme(self) -> None:
        """Create README file."""
        readme_content = f"""# {self.config.project_name}

Flutter app scaffolded for Cursor.

## Quickstart
```bash
flutter pub get
make run            # runs on Chrome by default
```

## Testing
```bash
make test           # unit + widget tests
make integration    # integration_test/
```

## Linting
```bash
make analyze
```

## Env vars
Edit `.env` and access with `dotenv.env['KEY']` after startup.
"""
        
        with open(self.config.project_path / "README.md", "w") as f:
            f.write(readme_content)
        
        console.print("  ✅ README created")
    
    def _format_code(self) -> None:
        """Format the generated code."""
        try:
            subprocess.run(
                [str(self.flutter_root / "bin" / "dart"), "format", "."],
                cwd=self.config.project_path,
                check=False,
                capture_output=True
            )
            console.print("  ✅ Code formatted")
        except Exception as e:
            console.print(f"  ⚠️  Code formatting warning: {e}")
