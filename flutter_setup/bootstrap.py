"""Project bootstrapping for Flutter setup."""

import subprocess
from pathlib import Path

import yaml
from rich.console import Console

from .cicd_generator import CicdGenerator
from .config import Config

console = Console()


class ProjectBootstrap:
    """Bootstraps development environment for Flutter projects."""

    def __init__(self, config: Config):
        """Initialize ProjectBootstrap."""
        self.config = config
        self.home = Path.home()
        self.flutter_root = config.flutter_location

    def bootstrap_project(self) -> None:
        """Bootstrap the development environment."""
        if self.config.dry_run:
            console.print(
                "[yellow]DRY RUN: Would bootstrap development environment[/yellow]"
            )
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

        # Create optional architecture and persistence scaffolds
        self._create_architecture_scaffold()

        # Create CI/CD workflows and configuration
        self._create_cicd()

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
            "files.exclude": {"**/.dart_tool": True, "**/build": True},
        }

        import json

        with open(vscode_dir / "settings.json", "w") as f:
            json.dump(settings, f, indent=2)

        # Launch configuration
        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {"name": "Flutter Debug", "request": "launch", "type": "dart"}
            ],
        }

        with open(vscode_dir / "launch.json", "w") as f:
            json.dump(launch_config, f, indent=2)

        console.print("  ✅ VS Code/Cursor configuration created")

    def _create_makefile(self) -> None:
        """Create Makefile with common commands."""
        generate_target = ""
        if self.config.database == "sqlite":
            generate_target = """
generate:
	dart run build_runner build --delete-conflicting-outputs
"""

        makefile_content = f"""run:
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
{generate_target}"""

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
        unit_test = """import 'package:flutter_test/flutter_test.dart';

void main() {
  test('sanity check', () {
    expect(1 + 1, equals(2));
  });
}
"""

        with open(
            self.config.project_path / "test" / "unit" / "sanity_test.dart", "w"
        ) as f:
            f.write(unit_test)

        app_import = f"package:{self.config.package_name}/main.dart"
        app_widget = "MyApp"
        riverpod_import = ""
        pump_widget = f"const {app_widget}()"
        if self.config.architecture == "clean":
            app_import = f"package:{self.config.package_name}/src/app/app.dart"
            app_widget = "App"
            riverpod_import = (
                "import 'package:flutter_riverpod/flutter_riverpod.dart';\n"
            )
            pump_widget = f"const ProviderScope(child: {app_widget}())"

        # Widget test
        widget_test = f"""import 'package:flutter_test/flutter_test.dart';
{riverpod_import}import '{app_import}';

void main() {{
  testWidgets('App loads without errors', (tester) async {{
    await tester.pumpWidget({pump_widget});
    expect(find.byType({app_widget}), findsOneWidget);
  }});
}}
"""

        with open(
            self.config.project_path / "test" / "widget" / "app_widget_test.dart", "w"
        ) as f:
            f.write(widget_test)

        # Integration test
        integration_test = f"""import 'package:integration_test/integration_test.dart';
import 'package:flutter_test/flutter_test.dart';
{riverpod_import}import '{app_import}';

void main() {{
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('home page renders', (tester) async {{
    await tester.pumpWidget({pump_widget});
    expect(find.byType({app_widget}), findsOneWidget);
  }});
}}
"""

        with open(
            self.config.project_path / "integration_test" / "app_test.dart", "w"
        ) as f:
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

    def _create_architecture_scaffold(self) -> None:
        """Create optional reusable application architecture scaffolds."""
        if self.config.architecture == "clean":
            self._create_clean_architecture_scaffold()

        if self.config.database == "sqlite":
            self._create_sqlite_scaffold()

        if self.config.testing == "mocktail":
            self._create_mocktail_scaffold()

        if self._uses_firebase():
            self._create_firebase_scaffold()

    def _uses_firebase(self) -> bool:
        """Return whether any Firebase integration was selected."""
        return (
            self.config.auth_provider == "firebase"
            or self.config.cloud_database == "firestore"
            or self.config.notifications_provider == "firebase"
        )

    def _create_clean_architecture_scaffold(self) -> None:
        """Create a Clean Architecture starter layout."""
        src_dir = self.config.project_path / "lib" / "src"
        directories = [
            src_dir / "app",
            src_dir / "core" / "error",
            src_dir / "core" / "routing",
            src_dir / "core" / "theme",
            src_dir / "features" / "home" / "data",
            src_dir / "features" / "home" / "domain",
            src_dir / "features" / "home" / "presentation",
            self.config.project_path / "test" / "features" / "home",
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

        (src_dir / "app" / "app.dart").write_text(
            """import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../features/home/presentation/home_screen.dart';

class App extends ConsumerWidget {
  const App({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return MaterialApp(
      title: 'Flutter App',
      theme: ThemeData(useMaterial3: true),
      home: const HomeScreen(),
    );
  }
}
"""
        )

        (
            src_dir / "features" / "home" / "presentation" / "home_screen.dart"
        ).write_text(
            """import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return const Scaffold(
      body: Center(
        child: Text('Home'),
      ),
    );
  }
}
"""
        )

        (src_dir / "core" / "error" / "app_failure.dart").write_text(
            """class AppFailure {
  const AppFailure(this.message);

  final String message;
}
"""
        )

        firebase_import = ""
        firebase_init = ""
        if self._uses_firebase():
            firebase_import = "import 'src/core/firebase/firebase_initializer.dart';\n"
            firebase_init = "  await initializeFirebase();\n"

        main_dart = self.config.project_path / "lib" / "main.dart"
        if main_dart.exists():
            main_dart.write_text(f"""import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

{firebase_import}\
import 'src/app/app.dart';

Future<void> main() async {{
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: '.env');
{firebase_init}\
  runApp(const ProviderScope(child: App()));
}}
""")

        console.print("  ✅ Clean Architecture scaffold created")

    def _create_sqlite_scaffold(self) -> None:
        """Create a Drift/SQLite starter database scaffold."""
        data_dir = self.config.project_path / "lib" / "src" / "core" / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        (data_dir / "app_database.dart").write_text("""import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

part 'app_database.g.dart';

class AppSettings extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();
  DateTimeColumn get updatedAt => dateTime().withDefault(currentDateAndTime)();

  @override
  Set<Column<Object>> get primaryKey => {key};
}

@DriftDatabase(tables: [AppSettings])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => 1;
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, 'app.sqlite'));
    return NativeDatabase.createInBackground(file);
  });
}
""")

        console.print("  ✅ SQLite persistence scaffold created")

    def _create_mocktail_scaffold(self) -> None:
        """Create shared mocktail test helpers."""
        helpers_dir = self.config.project_path / "test" / "helpers"
        helpers_dir.mkdir(parents=True, exist_ok=True)

        (helpers_dir / "mocks.dart").write_text(
            """import 'package:mocktail/mocktail.dart';

class MockRepository extends Mock {}
"""
        )

        console.print("  ✅ Mocktail testing scaffold created")

    def _create_firebase_scaffold(self) -> None:
        """Create Firebase integration starter files."""
        firebase_dir = self.config.project_path / "lib" / "src" / "core" / "firebase"
        firebase_dir.mkdir(parents=True, exist_ok=True)

        (firebase_dir / "firebase_initializer.dart").write_text(
            """import 'package:firebase_core/firebase_core.dart';

Future<void> initializeFirebase() async {
  await Firebase.initializeApp();
}
"""
        )

        if self.config.auth_provider == "firebase":
            (firebase_dir / "firebase_auth_service.dart").write_text(
                """import 'package:firebase_auth/firebase_auth.dart';

class FirebaseAuthService {
  FirebaseAuthService({FirebaseAuth? auth}) : _auth = auth ?? FirebaseAuth.instance;

  final FirebaseAuth _auth;

  Stream<User?> authStateChanges() => _auth.authStateChanges();
}
"""
            )

        if self.config.cloud_database == "firestore":
            (firebase_dir / "firestore_database.dart").write_text(
                """import 'package:cloud_firestore/cloud_firestore.dart';

class FirestoreDatabase {
  FirestoreDatabase({FirebaseFirestore? firestore})
    : _firestore = firestore ?? FirebaseFirestore.instance;

  final FirebaseFirestore _firestore;

  CollectionReference<Map<String, dynamic>> collection(String path) {
    return _firestore.collection(path);
  }
}
"""
            )

        if self.config.notifications_provider == "firebase":
            (firebase_dir / "firebase_notifications_service.dart").write_text(
                """import 'package:firebase_messaging/firebase_messaging.dart';

class FirebaseNotificationsService {
  FirebaseNotificationsService({FirebaseMessaging? messaging})
    : _messaging = messaging ?? FirebaseMessaging.instance;

  final FirebaseMessaging _messaging;

  Future<NotificationSettings> requestPermission() {
    return _messaging.requestPermission();
  }

  Future<String?> getToken() {
    return _messaging.getToken();
  }
}
"""
            )

        console.print("  ✅ Firebase integration scaffold created")

    def _create_cicd(self) -> None:
        """Create CI/CD workflows and configuration."""
        cicd_generator = CicdGenerator(self.config)
        cicd_generator.generate_cicd()

    def _add_dependencies(self) -> None:
        """Add required dependencies to the project."""
        try:
            for dependency in self._runtime_dependencies():
                subprocess.run(
                    [
                        str(self.flutter_root / "bin" / "flutter"),
                        "pub",
                        "add",
                        dependency,
                    ],
                    cwd=self.config.project_path,
                    check=False,
                    capture_output=True,
                )

            for dependency in self._dev_dependencies():
                subprocess.run(
                    [
                        str(self.flutter_root / "bin" / "flutter"),
                        "pub",
                        "add",
                        "--dev",
                        dependency,
                    ],
                    cwd=self.config.project_path,
                    check=False,
                    capture_output=True,
                )

            # Add integration_test as SDK dependency by directly editing pubspec.yaml
            # flutter pub add doesn't correctly handle SDK dependencies
            self._add_integration_test_sdk_dependency()

            console.print("  ✅ Dependencies added")

        except Exception as e:
            console.print(f"  ⚠️  Dependency addition warning: {e}")

    def _runtime_dependencies(self) -> list[str]:
        """Return runtime dependencies required by selected scaffolds."""
        dependencies = ["flutter_dotenv"]

        if self.config.architecture == "clean":
            dependencies.append("flutter_riverpod")

        if self.config.database == "sqlite":
            dependencies.extend(
                ["drift", "sqlite3_flutter_libs", "path_provider", "path"]
            )

        if self._uses_firebase():
            dependencies.append("firebase_core")

        if self.config.auth_provider == "firebase":
            dependencies.append("firebase_auth")

        if self.config.cloud_database == "firestore":
            dependencies.append("cloud_firestore")

        if self.config.notifications_provider == "firebase":
            dependencies.append("firebase_messaging")

        return dependencies

    def _dev_dependencies(self) -> list[str]:
        """Return dev dependencies required by selected scaffolds."""
        dependencies = ["flutter_lints"]

        if self.config.database == "sqlite":
            dependencies.extend(["drift_dev", "build_runner"])

        if self.config.testing == "mocktail":
            dependencies.append("mocktail")

        return dependencies

    def _add_integration_test_sdk_dependency(self) -> None:
        """Add integration_test as an SDK dependency to pubspec.yaml."""
        pubspec_path = self.config.project_path / "pubspec.yaml"
        if not pubspec_path.exists():
            console.print("  ⚠️  pubspec.yaml not found, skipping integration_test")
            return

        try:
            # Read pubspec.yaml
            with open(pubspec_path, "r") as f:
                pubspec = yaml.safe_load(f) or {}

            # Ensure dev_dependencies section exists
            if "dev_dependencies" not in pubspec:
                pubspec["dev_dependencies"] = {}

            # Check if integration_test already exists
            existing = pubspec["dev_dependencies"].get("integration_test")
            if (
                existing
                and isinstance(existing, dict)
                and existing.get("sdk") == "flutter"
            ):
                # Already correctly configured, skip
                return

            # Add or update integration_test with SDK specification
            pubspec["dev_dependencies"]["integration_test"] = {"sdk": "flutter"}

            # Write back to pubspec.yaml
            with open(pubspec_path, "w") as f:
                yaml.dump(pubspec, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            console.print(f"  ⚠️  Failed to add integration_test SDK dependency: {e}")

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
                    lines.insert(
                        import_index + 1,
                        "import 'package:flutter_dotenv/flutter_dotenv.dart';",
                    )
                else:
                    lines.insert(
                        0, "import 'package:flutter_dotenv/flutter_dotenv.dart';"
                    )

                # Modify main function
                modified_content = "\n".join(lines)
                modified_content = modified_content.replace(
                    "void main() {",
                    'Future<void> main() async {\n  await dotenv.load(fileName: ".env");',
                )

                with open(main_dart, "w") as f:
                    f.write(modified_content)

            if self._uses_firebase():
                content = main_dart.read_text()
                if "firebase_initializer.dart" not in content:
                    lines = content.split("\n")
                    import_index = -1
                    for i, line in enumerate(lines):
                        if line.strip().startswith("import "):
                            import_index = i

                    firebase_import = (
                        "import 'src/core/firebase/firebase_initializer.dart';"
                    )
                    if import_index >= 0:
                        lines.insert(import_index + 1, firebase_import)
                    else:
                        lines.insert(0, firebase_import)

                    modified_content = "\n".join(lines)
                    if "await dotenv.load" in modified_content:
                        modified_content = modified_content.replace(
                            '  await dotenv.load(fileName: ".env");',
                            '  await dotenv.load(fileName: ".env");\n'
                            "  await initializeFirebase();",
                        )
                    elif "Future<void> main() async {" in modified_content:
                        modified_content = modified_content.replace(
                            "Future<void> main() async {",
                            "Future<void> main() async {\n"
                            "  await initializeFirebase();",
                        )

                    main_dart.write_text(modified_content)

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

## Architecture
Architecture scaffold: `{self.config.architecture}`.

## Persistence
Local database scaffold: `{self.config.database}`.

## Testing
Testing starter: `{self.config.testing}`.

## Firebase
Auth provider: `{self.config.auth_provider}`.
Cloud database: `{self.config.cloud_database}`.
Notifications: `{self.config.notifications_provider}`.

When Firebase options are enabled, run `flutterfire configure` for this
project before using the generated Firebase services.
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
                capture_output=True,
            )
            console.print("  ✅ Code formatted")
        except Exception as e:
            console.print(f"  ⚠️  Code formatting warning: {e}")
