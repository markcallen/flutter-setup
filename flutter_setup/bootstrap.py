"""Project bootstrapping for Flutter setup."""

import re as _re
import subprocess
from pathlib import Path

import yaml
from rich.console import Console

from .cicd_generator import CicdGenerator
from .config import Config

console = Console()


def _extract_makefile_target_names(content: str) -> set[str]:
    """Return set of target names defined in a Makefile."""
    # Match 'name:' but NOT 'name:=' (variable assignment)
    names = set(
        _re.findall(r"^([a-zA-Z][a-zA-Z0-9_-]*)\s*:(?!=)", content, _re.MULTILINE)
    )
    names.discard(".PHONY")
    return names


def _is_var_defined_in(line: str, content: str) -> bool:
    """Return True if line is a variable assignment whose name is already defined in content."""
    m = _re.match(r"^([A-Z_][A-Z0-9_]*)\s*[:?]?=", line)
    if not m:
        return False
    var_name = m.group(1)
    return bool(
        _re.search(rf"^{_re.escape(var_name)}\s*[:?]?=", content, _re.MULTILINE)
    )


def _filter_new_makefile_content(
    new_content: str, existing_targets: set[str], existing_content: str = ""
) -> str:
    """Return parts of new_content not already present in the existing Makefile.

    Target blocks whose names are in existing_targets are skipped. Preamble
    variable lines are included only when their variable name is not already
    defined in existing_content — ensuring appended targets that reference
    $(FLUTTER), $(ANDROID_SDK_ROOT), etc. will find those variables.
    """
    blocks = _re.split(
        r"(?=^[a-zA-Z][a-zA-Z0-9_-]*\s*:(?!=))", new_content, flags=_re.MULTILINE
    )
    result = []
    for block in blocks:
        if not block.strip():
            continue
        first_line = block.splitlines()[0] if block.splitlines() else ""
        target_match = _re.match(r"^([a-zA-Z][a-zA-Z0-9_-]*)\s*:(?!=)", first_line)
        if target_match:
            target_name = target_match.group(1)
            if target_name not in existing_targets:
                result.append(block)
        else:
            # Preamble block: include variable lines not already defined
            missing = [
                line
                for line in block.splitlines(keepends=True)
                if not _is_var_defined_in(line, existing_content)
            ]
            if any(ln.strip() for ln in missing):
                result.append("".join(missing))
    return "".join(result)


class ProjectBootstrap:
    """Bootstraps development environment for Flutter projects."""

    def __init__(self, config: Config, force: bool = False) -> None:
        """Initialize ProjectBootstrap."""
        self.config = config
        self.force = force
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

        # Update pubspec description (flutter create leaves a generic placeholder)
        self._update_pubspec_description()

        # Create environment support (.env file + gitignore entry; NOT added to assets)
        self._create_environment_support()

        # Pin Flutter SDK version in pubspec.yaml
        ver = self.config.flutter_version or self._detect_flutter_version()
        if ver:
            self._pin_flutter_sdk_version(ver)

        # Re-run pub get after all pubspec.yaml modifications are complete so
        # packages added by yaml.dump-based edits (integration_test, .env asset,
        # flutter version pin) are resolved before the user's first make target.
        self._run_pub_get()

        # Run build_runner for projects that require code generation (Drift,
        # Riverpod, Freezed) so the project compiles immediately after setup.
        if self.config.database == "sqlite" or self.config.architecture == "clean":
            self._run_build_runner()

        # Create README (append section if file already exists)
        self._append_readme()

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

    def _build_makefile_content(self) -> str:
        """Build and return the Makefile content string."""
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
\tawk -v a="$$ACTUAL" -v r="$(FLUTTER_REQUIRED_VERSION)" 'BEGIN{split(a,av,".");split(r,rv,".");for(i=1;i<=3;i++){sub(/[^0-9].*/,"",av[i]);sub(/[^0-9].*/,"",rv[i])};if(av[1]+0>rv[1]+0)exit 0;if(av[1]+0<rv[1]+0)exit 1;if(av[2]+0>rv[2]+0)exit 0;if(av[2]+0<rv[2]+0)exit 1;if(av[3]+0>=rv[3]+0)exit 0;exit 1}' /dev/null || \\
\t{ echo "ERROR: Flutter $$ACTUAL does not satisfy >=$$FLUTTER_REQUIRED_VERSION"; exit 1; }

.PHONY: check-flutter-version
"""
        else:
            version_header = ""
            version_dep = ""
            version_target = ""

        flutter_cmd = "$(FLUTTER)" if ver else "flutter"

        generate_target = ""
        codegen_dep = ""
        if self.config.database == "sqlite" or self.config.architecture == "clean":
            generate_target = f"""
generate:{version_dep}
\tdart run build_runner build --delete-conflicting-outputs
"""
            codegen_dep = " generate"

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
                "AVDMANAGER := $(ANDROID_SDK_ROOT)/cmdline-tools/latest/bin/avdmanager\n"
                "REQUIRED_NDK := 27.0.12077973\n"
                "ANDROID_AVD_NAME := flutter_dev\n"
                "ANDROID_API_LEVEL := 35\n"
                "ANDROID_AVD_DEVICE := pixel_6\n"
                "ANDROID_SYSTEM_IMAGE := system-images;android-$(ANDROID_API_LEVEL);google_apis;x86_64\n\n"
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

setup-emulator:
\t@if $(AVDMANAGER) list avd | grep -q "Name: $(ANDROID_AVD_NAME)"; then \\
\t\techo "Emulator '$(ANDROID_AVD_NAME)' already exists"; \\
\telse \\
\t\techo "Installing system image $(ANDROID_SYSTEM_IMAGE)..."; \\
\t\t$(SDKMANAGER) "$(ANDROID_SYSTEM_IMAGE)"; \\
\t\techo "Creating emulator '$(ANDROID_AVD_NAME)'..."; \\
\t\techo no | $(AVDMANAGER) create avd --name "$(ANDROID_AVD_NAME)" --package "$(ANDROID_SYSTEM_IMAGE)" --device "$(ANDROID_AVD_DEVICE)"; \\
\tfi

.PHONY: setup-emulator
"""

        if "android" in self.config.platforms:
            run_android_emulator_check = (
                '\t@if ! adb devices | grep -q "^emulator"; then \\\n'
                '\t\techo "No emulator running, launching $(ANDROID_AVD_NAME)..."; \\\n'
                f"\t\t{flutter_cmd} emulators --launch $(ANDROID_AVD_NAME); \\\n"
                '\t\techo "Waiting for emulator to boot..."; \\\n'
                '\t\tadb -e wait-for-device && adb -e shell \'while [ "$$(getprop sys.boot_completed)" != "1" ]; do sleep 2; done\'; \\\n'
                '\t\techo "Emulator ready."; \\\n'
                "\tfi\n"
            )
        else:
            run_android_emulator_check = ""

        ios_target = ""
        if "ios" in self.config.platforms:
            ios_target = f"run-ios:{version_dep}\n\t{flutter_cmd} run -d ios\n\n"

        android_target = ""
        if "android" in self.config.platforms:
            android_target = (
                f"run-android:{version_dep}{android_sdk_dep}\n"
                f"{run_android_emulator_check}\t{flutter_cmd} run -d android\n\n"
            )

        return f"""{version_header}{android_sdk_header}{web_target}{ios_target}{android_target}analyze:{version_dep}{codegen_dep}
\t{flutter_cmd} analyze

test:{version_dep}{codegen_dep}
\t{flutter_cmd} test

integration:{version_dep}{codegen_dep}
\t{flutter_cmd} test integration_test

upgrade:{version_dep}
\t{flutter_cmd} pub upgrade

upgrade-check:{version_dep}
\t{flutter_cmd} pub get
{generate_target}{android_sdk_target}{version_target}"""

    def _create_makefile(self) -> None:
        """Create Makefile with common commands."""
        # Always lock the project to the Flutter version present at creation time.
        # --flutter-version provides an explicit pin; otherwise detect from the SDK.
        makefile_content = self._build_makefile_content()

        with open(self.config.project_path / "Makefile", "w") as f:
            f.write(makefile_content)

        console.print("  ✅ Makefile created")

    def _append_vscode_config(self) -> None:
        """Append VS Code/Cursor configuration files, skipping existing unless --force."""
        import json

        vscode_dir = self.config.project_path / ".vscode"
        vscode_dir.mkdir(exist_ok=True)

        settings = {
            "dart.flutterHotReloadOnSave": "all",
            "dart.lineLength": 100,
            "editor.formatOnSave": True,
            "editor.defaultFormatter": "Dart-Code.dart-code",
            "files.exclude": {"**/.dart_tool": True, "**/build": True},
        }
        settings_file = vscode_dir / "settings.json"
        if settings_file.exists() and not self.force:
            console.print(
                "  ⚠️  .vscode/settings.json already exists — skipping (use --force to overwrite)"
            )
        else:
            settings_file.write_text(json.dumps(settings, indent=2))
            console.print("  ✅ .vscode/settings.json written")

        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {"name": "Flutter Debug", "request": "launch", "type": "dart"}
            ],
        }
        launch_file = vscode_dir / "launch.json"
        if launch_file.exists() and not self.force:
            console.print(
                "  ⚠️  .vscode/launch.json already exists — skipping (use --force to overwrite)"
            )
        else:
            launch_file.write_text(json.dumps(launch_config, indent=2))
            console.print("  ✅ .vscode/launch.json written")

    def _append_makefile(self) -> None:
        """Append missing Makefile targets, or create Makefile if absent."""
        new_content = self._build_makefile_content()
        makefile = self.config.project_path / "Makefile"

        if not makefile.exists():
            makefile.write_text(new_content)
            console.print("  ✅ Makefile created")
            return

        existing = makefile.read_text()
        existing_targets = _extract_makefile_target_names(existing)
        to_append = _filter_new_makefile_content(
            new_content, existing_targets, existing
        )

        if to_append:
            with open(makefile, "a") as f:
                f.write("\n# Added by flutter-setup\n")
                f.write(to_append)
            console.print("  ✅ Makefile targets appended")
        else:
            console.print(
                "  ℹ️  Makefile already has all flutter-setup targets — nothing to append"
            )

    def append_project(self) -> None:
        """Append flutter-setup tooling to an existing project directory."""
        if self.config.dry_run:
            console.print(
                "[yellow]DRY RUN: Would append flutter-setup tooling[/yellow]"
            )
            return
        console.print("  🔧 Appending flutter-setup tooling...")
        self._append_vscode_config()
        self._append_makefile()
        self._create_cicd()
        self._append_readme()
        console.print("  ✅ Tooling appended")

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
        if self.config.architecture == "clean":
            widget_assertion = "expect(find.text('Home'), findsOneWidget);"
        else:
            widget_assertion = f"expect(find.byType({app_widget}), findsOneWidget);"

        widget_test = f"""import 'package:flutter_test/flutter_test.dart';
{riverpod_import}import '{app_import}';

void main() {{
  testWidgets('App loads without errors', (tester) async {{
    await tester.pumpWidget({pump_widget});
    await tester.pumpAndSettle();
    {widget_assertion}
  }});
}}
"""

        with open(
            self.config.project_path / "test" / "widget" / "app_widget_test.dart", "w"
        ) as f:
            f.write(widget_test)

        # Integration test
        if self.config.architecture == "clean":
            integration_assertion = "expect(find.text('Home'), findsOneWidget);"
        else:
            integration_assertion = (
                f"expect(find.byType({app_widget}), findsOneWidget);"
            )

        integration_test = f"""import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
{riverpod_import}import '{app_import}';

void main() {{
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() async {{
    await dotenv.load(fileName: '.env', isOptional: true);
  }});

  testWidgets('home page renders', (tester) async {{
    await tester.pumpWidget({pump_widget});
    await tester.pumpAndSettle();
    {integration_assertion}
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

        (src_dir / "app" / "router.dart").write_text(
            """import 'package:go_router/go_router.dart';

import '../features/home/presentation/home_screen.dart';

final router = GoRouter(
  routes: [
    GoRoute(
      path: '/',
      builder: (context, state) => const HomeScreen(),
    ),
  ],
);
"""
        )

        safe_title = self.config.project_name.replace("'", "\\'")
        (src_dir / "app" / "app.dart").write_text(
            f"""import 'package:flutter/material.dart';

import 'router.dart';

class App extends StatelessWidget {{
  const App({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp.router(
      title: '{safe_title}',
      theme: ThemeData(useMaterial3: true),
      routerConfig: router,
    );
  }}
}}
"""
        )

        (
            src_dir / "features" / "home" / "presentation" / "home_screen.dart"
        ).write_text(
            """import 'package:flutter/material.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
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
  await dotenv.load(fileName: '.env', isOptional: true);
{firebase_init}\
  runApp(const ProviderScope(child: App()));
}}
""")

        self._create_assets_scaffold()

        console.print("  ✅ Clean Architecture scaffold created")

    def _create_assets_scaffold(self) -> None:
        """Create assets/ directories and declare them in pubspec.yaml.

        Uses .gitkeep sentinels so the empty directories are tracked in git.
        """
        assets_root = self.config.project_path / "assets"
        asset_dirs = [
            assets_root / "images",
            assets_root / "fonts",
        ]
        for asset_dir in asset_dirs:
            asset_dir.mkdir(parents=True, exist_ok=True)
            (asset_dir / ".gitkeep").touch()

        pubspec_path = self.config.project_path / "pubspec.yaml"
        if not pubspec_path.exists():
            return
        try:
            with open(pubspec_path, "r") as f:
                pubspec = yaml.safe_load(f) or {}
            flutter_section = pubspec.setdefault("flutter", {})
            assets = flutter_section.setdefault("assets", [])
            if "assets/images/" not in assets:
                assets.append("assets/images/")
            with open(pubspec_path, "w") as f:
                yaml.dump(pubspec, f, default_flow_style=False, sort_keys=False)
            console.print("  ✅ Assets directories created")
        except Exception as e:
            console.print(f"  ⚠️  Failed to declare assets in pubspec.yaml: {e}")

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

  @override
  MigrationStrategy get migration => MigrationStrategy(
    onCreate: (m) => m.createAll(),
    onUpgrade: (m, from, to) async {
      throw UnimplementedError('Add migration steps for v$from -> v$to');
    },
  );
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
        cicd_generator = CicdGenerator(self.config, force=self.force)
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
            dependencies.extend(
                [
                    "flutter_riverpod",
                    "riverpod_annotation",
                    "go_router",
                    "freezed_annotation",
                    "json_annotation",
                    "collection",
                    "intl",
                    "uuid",
                ]
            )

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

        if self.config.architecture == "clean":
            # build_runner is required to run riverpod_generator, freezed, and
            # json_serializable — add it here so clean-arch projects without
            # sqlite still get code generation support.
            dependencies.extend(
                ["riverpod_generator", "freezed", "json_serializable", "build_runner"]
            )

        if self.config.database == "sqlite":
            dependencies.extend(["drift_dev", "build_runner"])

        if self.config.testing == "mocktail":
            dependencies.append("mocktail")

        return dependencies

    _GENERIC_PUBSPEC_DESCRIPTION = "A new Flutter project."

    def _update_pubspec_description(self) -> None:
        """Replace the generic flutter-create description in pubspec.yaml.

        Only overwrites the known placeholder left by `flutter create` so that
        re-running bootstrap does not clobber a description the developer has
        already customised.
        """
        pubspec_path = self.config.project_path / "pubspec.yaml"
        if not pubspec_path.exists():
            return
        try:
            with open(pubspec_path, "r") as f:
                pubspec = yaml.safe_load(f) or {}
            if pubspec.get("description") != self._GENERIC_PUBSPEC_DESCRIPTION:
                return
            pubspec["description"] = (
                f"A {self.config.project_name} Flutter application."
            )
            with open(pubspec_path, "w") as f:
                yaml.dump(pubspec, f, default_flow_style=False, sort_keys=False)
            console.print("  ✅ pubspec description updated")
        except Exception as e:
            console.print(f"  ⚠️  Failed to update pubspec description: {e}")

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
        the entry is present regardless. The version constraint is derived from
        the runtime drift package so the code-generator version always matches.
        """
        import re

        pubspec_path = self.config.project_path / "pubspec.yaml"
        if not pubspec_path.exists():
            return
        try:
            with open(pubspec_path, "r") as f:
                pubspec = yaml.safe_load(f) or {}
            dev_deps = pubspec.setdefault("dev_dependencies", {})
            if "drift_dev" not in dev_deps:
                # Pin drift_dev to the same full version as the runtime drift
                # package: drift_dev must match drift's minor version since each
                # minor release may add new codegen features the old generator
                # doesn't know about. e.g. drift: ^2.31.0 -> drift_dev: ^2.31.0
                drift_constraint = pubspec.get("dependencies", {}).get("drift", "")
                match = re.match(r"[\^~]?(\d+\.\d+\.\d+)", str(drift_constraint))
                version = f"^{match.group(1)}" if match else "any"
                dev_deps["drift_dev"] = version
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

        # .env is intentionally NOT added to pubspec.yaml assets: bundling it
        # would hard-fail CI builds on a clean checkout (file is gitignored).
        # Add it manually and remove from .gitignore when you need runtime env vars,
        # or use --dart-define-from-file for build-time injection.

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
                    'Future<void> main() async {\n  await dotenv.load(fileName: ".env", isOptional: true);',
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
                            '  await dotenv.load(fileName: ".env", isOptional: true);',
                            '  await dotenv.load(fileName: ".env", isOptional: true);\n'
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

    def _build_readme_section(self) -> str:
        """Return the flutter-setup tooling section for README.md."""
        if "web" in self.config.platforms:
            run_cmd = "make run-chrome      # runs on Chrome"
        elif "ios" in self.config.platforms:
            run_cmd = "make run-ios         # runs on iOS simulator"
        elif "android" in self.config.platforms:
            run_cmd = "make run-android     # runs on Android emulator"
        else:
            run_cmd = "flutter run"

        codegen_section = ""
        if self.config.database == "sqlite" or self.config.architecture == "clean":
            codegen_section = """
### Code generation
This project uses `build_runner` for code generation (Drift, Riverpod, Freezed).
Generation runs automatically during setup. To re-run manually:
```bash
make generate
```
"""

        return f"""## flutter-setup

### Quickstart
```bash
flutter pub get
{run_cmd}
```
{codegen_section}
### Testing
```bash
make test           # unit + widget tests
make integration    # integration_test/
```

### Linting
```bash
make analyze
```

### Env vars
Copy `.env.example` to `.env` and fill in values. The file is gitignored and
not bundled as an asset by default, so `dotenv.env['KEY']` returns null until
you either add `.env` to `pubspec.yaml` assets (and remove it from `.gitignore`),
or use `--dart-define-from-file=.env.json` for build-time injection.

### Scaffold configuration
- Architecture: `{self.config.architecture}`
- Database: `{self.config.database}`
- Testing: `{self.config.testing}`
- Auth provider: `{self.config.auth_provider}`
- Cloud database: `{self.config.cloud_database}`
- Notifications: `{self.config.notifications_provider}`
"""

    def _create_readme(self) -> None:
        """Create README file."""
        readme_path = self.config.project_path / "README.md"
        if readme_path.exists():
            console.print(
                "  ⚠️  README.md already exists — skipping (use append to add a section)"
            )
            return

        readme_content = (
            f"# {self.config.project_name}\n\nFlutter app scaffolded for Cursor.\n\n"
            + self._build_readme_section()
        )
        readme_path.write_text(readme_content)
        console.print("  ✅ README created")

    def _append_readme(self) -> None:
        """Append a flutter-setup section to an existing README, or create one."""
        readme_path = self.config.project_path / "README.md"
        section = self._build_readme_section()
        if not readme_path.exists():
            readme_path.write_text(f"# {self.config.project_name}\n\n" + section)
            console.print("  ✅ README created")
        else:
            existing = readme_path.read_text()
            if "## flutter-setup" in existing:
                console.print(
                    "  ⚠️  README.md already has a flutter-setup section — skipping"
                )
            else:
                with open(readme_path, "a") as f:
                    f.write("\n" + section)
                console.print("  ✅ flutter-setup section appended to README.md")

    def _run_pub_get(self) -> None:
        """Run flutter pub get after all pubspec.yaml modifications are complete."""
        try:
            subprocess.run(
                [str(self.flutter_root / "bin" / "flutter"), "pub", "get"],
                cwd=self.config.project_path,
                check=False,
                capture_output=True,
            )
            console.print("  ✅ flutter pub get completed")
        except Exception as e:
            console.print(f"  ⚠️  flutter pub get warning: {e}")

    def _run_build_runner(self) -> None:
        """Run build_runner to generate code for Drift, Riverpod, and Freezed.

        Projects using sqlite or clean architecture include code-generated files
        (*.g.dart, *.freezed.dart). Without this step the project will not
        compile on first checkout.
        """
        try:
            result = subprocess.run(
                [
                    str(self.flutter_root / "bin" / "dart"),
                    "run",
                    "build_runner",
                    "build",
                    "--delete-conflicting-outputs",
                ],
                cwd=self.config.project_path,
                check=False,
                capture_output=True,
            )
            if result.returncode == 0:
                console.print("  ✅ Code generation completed (build_runner)")
            else:
                stderr = result.stderr.decode(errors="replace") if result.stderr else ""
                console.print(
                    f"  ⚠️  build_runner exited with code {result.returncode}"
                    + (f": {stderr.strip()}" if stderr.strip() else "")
                )
        except Exception as e:
            console.print(f"  ⚠️  build_runner warning: {e}")

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
