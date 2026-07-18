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

        # Patch Android NDK version in build.gradle.kts
        if "android" in self.config.platforms:
            self._patch_android_ndk_version()

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

        # Pin Flutter SDK version in pubspec.yaml
        ver = self.config.flutter_version or self._detect_flutter_version()
        if ver:
            self._pin_flutter_sdk_version(ver)

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

    def _detect_flutter_version(self) -> str | None:
        """Return the version string of the Flutter SDK at config.flutter_location."""
        import re

        flutter_bin = self.config.flutter_location / "bin" / "flutter"
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

    def _create_makefile(self) -> None:
        """Create Makefile with common commands."""
        # Always lock the project to the Flutter version present at creation time.
        # --flutter-version provides an explicit pin; otherwise detect from the SDK.
        ver = self.config.flutter_version or self._detect_flutter_version()
        flutter_home = str(self.config.flutter_location)

        if ver:
            version_header = (
                f"FLUTTER_HOME := {flutter_home}\n"
                f'FLUTTER := "$(FLUTTER_HOME)/bin/flutter"\n'
                f"FLUTTER_REQUIRED_VERSION := {ver}\n\n"
            )
            version_dep = " check-flutter-version"
            version_target = """
check-flutter-version:
\t@ACTUAL=$$($(FLUTTER) --version 2>&1 | awk '/^Flutter [0-9]/{print $$2; exit}'); \\
\tif [ -z "$$ACTUAL" ]; then \\
\t\techo "ERROR: Could not determine Flutter version at $(FLUTTER_HOME)"; exit 1; \\
\tfi; \\
\techo "  Detected Flutter $$ACTUAL (required: >=$(FLUTTER_REQUIRED_VERSION))"; \\
\tpython3 -c "import sys; a=tuple(map(int,'$$ACTUAL'.split('.'))); r=tuple(map(int,'$(FLUTTER_REQUIRED_VERSION)'.split('.'))); sys.exit(0 if a>=r else 1)" 2>/dev/null || \\
\t{ echo "ERROR: Flutter $$ACTUAL does not satisfy >=$$FLUTTER_REQUIRED_VERSION"; exit 1; }
\t@$(FLUTTER) pub get

.PHONY: check-flutter-version
"""
        else:
            version_header = ""
            version_dep = ""
            version_target = ""

        flutter_cmd = "$(FLUTTER)" if ver else "flutter"

        generate_target = ""
        if self.config.database == "sqlite":
            generate_target = f"""
generate:{version_dep}
\tdart run build_runner build --delete-conflicting-outputs
"""

        web_target = ""
        if "web" in self.config.platforms:
            web_target = f"run-chrome:{version_dep}\n\t{flutter_cmd} run -d chrome\n\n"

        android_sdk_header = ""
        android_sdk_dep = ""
        android_sdk_target = ""
        if "android" in self.config.platforms:
            android_sdk_header = (
                "ANDROID_SDK_ROOT ?= $(or $(ANDROID_HOME),/opt/android-sdk)\n"
                "SDKMANAGER := $(ANDROID_SDK_ROOT)/cmdline-tools/latest/bin/sdkmanager\n"
                "REQUIRED_NDK := 27.0.12077973\n\n"
            )
            android_sdk_dep = " check-android-sdk"
            android_sdk_target = """
check-android-sdk:
\t@if [ ! -f "$(ANDROID_SDK_ROOT)/ndk/$(REQUIRED_NDK)/source.properties" ]; then \\
\t\techo "NDK $(REQUIRED_NDK) missing or incomplete, installing..."; \\
\t\t$(SDKMANAGER) "ndk;$(REQUIRED_NDK)"; \\
\telse \\
\t\techo "NDK $(REQUIRED_NDK) ok"; \\
\tfi

.PHONY: check-android-sdk
"""

        makefile_content = f"""{version_header}{android_sdk_header}{web_target}run-ios:{version_dep}
\t{flutter_cmd} run -d ios

run-android:{version_dep}{android_sdk_dep}
\t{flutter_cmd} run -d android

analyze:{version_dep}
\t{flutter_cmd} analyze

test:{version_dep}
\t{flutter_cmd} test

integration:{version_dep}
\t{flutter_cmd} test integration_test

upgrade:{version_dep}
\t{flutter_cmd} pub upgrade

upgrade-check:{version_dep}
\t{flutter_cmd} pub get
{generate_target}{android_sdk_target}{version_target}"""

        with open(self.config.project_path / "Makefile", "w") as f:
            f.write(makefile_content)

        console.print("  ✅ Makefile created")

    def _patch_android_ndk_version(self) -> None:
        """Pin the Android NDK version in build.gradle.kts.

        flutter create sets ndkVersion = flutter.ndkVersion (currently 26.x), but
        path_provider_android and sqlite3_flutter_libs require NDK 27.0.12077973.
        NDK versions are backward-compatible, so pinning to the highest required
        version fixes the mismatch warning and avoids a failed build.
        """
        gradle_path = self.config.project_path / "android" / "app" / "build.gradle.kts"
        if not gradle_path.exists():
            return

        content = gradle_path.read_text()
        patched = content.replace(
            "ndkVersion = flutter.ndkVersion",
            'ndkVersion = "27.0.12077973"',
        )
        if patched != content:
            gradle_path.write_text(patched)
            console.print("  ✅ Android NDK version pinned in build.gradle.kts")

    def _create_test_structure(self) -> None:
        """Create test directory structure."""
        test_dir = self.config.project_path / "test"
        test_dir.mkdir(exist_ok=True)

        # Remove the stale counter test that `flutter create` generates; it
        # references `MyApp` which doesn't exist in the scaffolded project.
        default_test = test_dir / "widget_test.dart"
        if default_test.exists():
            default_test.unlink()

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
  try {{
    await dotenv.load(fileName: '.env');
  }} catch (_) {{}}
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

            # Ensure drift_dev is in pubspec.yaml for sqlite projects even if
            # flutter pub add failed silently in restricted environments
            if self.config.database == "sqlite":
                self._add_drift_dev_to_pubspec()

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

    def _pin_flutter_sdk_version(self, version: str) -> None:
        """Set the flutter SDK constraint in pubspec.yaml to >= the given version."""
        pubspec_path = self.config.project_path / "pubspec.yaml"
        if not pubspec_path.exists():
            console.print("  ⚠️  pubspec.yaml not found, skipping Flutter version pin")
            return

        try:
            with open(pubspec_path, "r") as f:
                pubspec = yaml.safe_load(f) or {}

            if "environment" not in pubspec:
                pubspec["environment"] = {}
            pubspec["environment"]["flutter"] = f">={version}"

            with open(pubspec_path, "w") as f:
                yaml.dump(pubspec, f, default_flow_style=False, sort_keys=False)

            console.print(f"  ✅ Pinned flutter SDK to >={version} in pubspec.yaml")
        except Exception as e:
            console.print(f"  ⚠️  Failed to pin Flutter version in pubspec.yaml: {e}")

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

    def _add_drift_dev_to_pubspec(self) -> None:
        """Write drift_dev directly to pubspec.yaml dev_dependencies for sqlite projects.

        flutter pub add can silently fail in some environments; this guarantees
        the entry is present regardless.
        """
        pubspec_path = self.config.project_path / "pubspec.yaml"
        if not pubspec_path.exists():
            return
        try:
            with open(pubspec_path, "r") as f:
                pubspec = yaml.safe_load(f) or {}
            dev_deps = pubspec.setdefault("dev_dependencies", {})
            if "drift_dev" not in dev_deps:
                dev_deps["drift_dev"] = "any"
                with open(pubspec_path, "w") as f:
                    yaml.dump(pubspec, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            console.print(f"  ⚠️  Failed to add drift_dev to pubspec.yaml: {e}")

    def _create_environment_support(self) -> None:
        """Create environment variable support."""
        env_example_content = """# Environment variables — copy to .env and fill in real values.
# .env is gitignored; .env.example is checked in as a reference.
API_URL=https://api.example.com
"""
        env_content = """# Local environment variables (gitignored — never commit real secrets).
API_URL=https://api.example.com
"""

        env_example = self.config.project_path / ".env.example"
        if not env_example.exists():
            env_example.write_text(env_example_content)

        env_file = self.config.project_path / ".env"
        if not env_file.exists():
            env_file.write_text(env_content)

        # Keep .env out of version control
        self._add_env_to_gitignore()

        # Declare .env as a Flutter asset so it gets bundled into the app
        self._add_env_asset_to_pubspec()

        # Modify main.dart to load .env
        self._modify_main_dart()

        console.print("  ✅ Environment support created")

    def _add_env_to_gitignore(self) -> None:
        """Ensure .env is listed in .gitignore."""
        gitignore_path = self.config.project_path / ".gitignore"
        entry = ".env\n"
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            lines = content.splitlines()
            if any(line.strip() == ".env" for line in lines):
                return
            with open(gitignore_path, "a") as f:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write("\n# Environment variables\n")
                f.write(entry)
        else:
            gitignore_path.write_text(f"# Environment variables\n{entry}")

    def _add_env_asset_to_pubspec(self) -> None:
        """Add .env to the flutter assets list in pubspec.yaml."""
        pubspec_path = self.config.project_path / "pubspec.yaml"
        if not pubspec_path.exists():
            return
        try:
            with open(pubspec_path, "r") as f:
                pubspec = yaml.safe_load(f) or {}
            flutter_section = pubspec.setdefault("flutter", {})
            assets = flutter_section.setdefault("assets", [])
            if ".env" not in assets:
                assets.append(".env")
            with open(pubspec_path, "w") as f:
                yaml.dump(pubspec, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            console.print(f"  ⚠️  Failed to add .env to pubspec.yaml assets: {e}")

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
                    'Future<void> main() async {\n  try {\n    await dotenv.load(fileName: ".env");\n  } catch (_) {}',
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
        if "web" in self.config.platforms:
            run_cmd = "make run-chrome      # runs on Chrome"
        elif "ios" in self.config.platforms:
            run_cmd = "make run-ios         # runs on iOS simulator"
        elif "android" in self.config.platforms:
            run_cmd = "make run-android     # runs on Android emulator"
        else:
            run_cmd = "flutter run"

        readme_content = f"""# {self.config.project_name}

Flutter app scaffolded for Cursor.

## Quickstart
```bash
flutter pub get
{run_cmd}
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
