#!/usr/bin/env bash
set -euo pipefail

# ===== config =====
DEFAULT_CHANNEL="stable"
DEFAULT_ORG="com.example"
DEFAULT_DIR="$PWD"
FLUTTER_ROOT="${HOME}/development/flutter"
ZPROFILE="${HOME}/.zprofile"

SUPPORTED_PLATFORMS=(ios android macos linux windows web)
declare -A PLATFORM_ALIASES=([osx]=macos [win]=windows)

# template & langs (langs apply only to plugin templates)
TEMPLATE="app"          # app | plugin
IOS_LANG="swift"        # swift|objc (plugin only)
ANDROID_LANG="kotlin"   # kotlin|java (plugin only)

DRY_RUN=0
FLUTTER_UPDATE_MODE="reset"   # reset | reclone | skip

# ===== helpers =====
b(){ printf "\033[1m%s\033[0m\n" "$*"; }
i(){ printf "➜ %s\n" "$*"; }
ok(){ printf "✅ %s\n" "$*"; }
warn(){ printf "⚠️  %s\n" "$*"; }
die(){ printf "❌ %s\n" "$*" >&2; exit 2; }
need_cmd(){ command -v "$1" >/dev/null 2>&1; }
append_once(){ local l="$1" f="$2"; grep -Fqx "$l" "$f" 2>/dev/null || echo "$l" >> "$f"; }
to_lower(){ tr '[:upper:]' '[:lower:]'; }
is_supported(){ local x="$1"; for p in "${SUPPORTED_PLATFORMS[@]}"; do [[ "$x" == "$p" ]] && return 0; done; return 1; }
resolve_platform(){ local raw="$(echo "$1" | to_lower)"; [[ -n "${PLATFORM_ALIASES[$raw]+x}" ]] && echo "${PLATFORM_ALIASES[$raw]}" || echo "$raw"; }
sanitize_pkg(){
  # Flutter package name: lowercase_with_underscores, start with a letter
  local s; s="$(echo "$1" | to_lower | sed 's/[^a-z0-9_]/_/g')"
  s="$(echo "$s" | sed 's/^[^a-z]*/ /; s/^ *//')"
  [[ -z "$s" ]] && s="app"
  echo "$s"
}
run(){ if [[ "$DRY_RUN" -eq 1 ]]; then echo "[dry-run] $*"; else eval "$*"; fi; }

join_csv(){
  local out="" first=1 x
  for x in "$@"; do
    if [[ $first -eq 1 ]]; then out="$x"; first=0; else out="$out,$x"; fi
  done
  echo "$out"
}

# ===== args =====
ORG="$DEFAULT_ORG"; CHANNEL="$DEFAULT_CHANNEL"; OUT_DIR="$DEFAULT_DIR"

if [[ $# -lt 2 ]]; then
  cat <<USAGE
Usage:
  $0 [options] <ProjectFolderName> <platform...>

Options:
  --org <bundle.id>             Default: $DEFAULT_ORG
  --channel <stable|beta>       Default: $DEFAULT_CHANNEL
  --dir <path>                  Default: current directory
  --template <app|plugin>       Default: app
  --swift|--objc                (plugin only) iOS language
  --kotlin|--java               (plugin only) Android language
  --flutter-update <mode>       reset|reclone|skip (default: reset with prompt)
  --dry-run                     Preview actions

Examples:
  $0 MyApp ios android macos web
  $0 --template plugin --objc --java MyPlugin ios android
  $0 --flutter-update reclone MyApp ios
USAGE
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --org) ORG="$2"; shift 2 ;;
    --channel) CHANNEL="$2"; shift 2 ;;
    --dir) OUT_DIR="$2"; shift 2 ;;
    --template) TEMPLATE="$(echo "$2" | to_lower)"; shift 2 ;;
    --swift) IOS_LANG="swift"; shift ;;
    --objc) IOS_LANG="objc"; shift ;;
    --kotlin) ANDROID_LANG="kotlin"; shift ;;
    --java) ANDROID_LANG="java"; shift ;;
    --flutter-update) FLUTTER_UPDATE_MODE="$(echo "$2" | to_lower)"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --) shift; break ;;
    -*) die "Unknown option: $1" ;;
    *) PROJECT_DIR_NAME="$1"; shift; break ;;
  esac
done

[[ -z "${PROJECT_DIR_NAME:-}" ]] && die "Project folder name is required."
[[ $# -lt 1 ]] && die "At least one platform is required (e.g., ios android macos web)."
[[ "$TEMPLATE" != "app" && "$TEMPLATE" != "plugin" ]] && die "Invalid --template. Use app|plugin."
case "$FLUTTER_UPDATE_MODE" in reset|reclone|skip) ;; *) die "Invalid --flutter-update. Use reset|reclone|skip." ;; esac

RAW_PLATFORMS=("$@")
# resolve + validate + dedupe (preserve order)
DEDUP_PLATFORMS=()
for rp in "${RAW_PLATFORMS[@]}"; do
  rp="${rp// /}"; [[ -z "$rp" ]] && continue
  resolved="$(resolve_platform "$rp")"
  is_supported "$resolved" || { warn "Unsupported platform: '$rp'"; echo "Allowed: ${SUPPORTED_PLATFORMS[*]}"; exit 2; }
  # dedupe
  already=0; for q in "${DEDUP_PLATFORMS[@]}"; do [[ "$q" == "$resolved" ]] && already=1 && break; done
  [[ $already -eq 0 ]] && DEDUP_PLATFORMS+=("$resolved")
done

PLAT_CSV="$(join_csv "${DEDUP_PLATFORMS[@]}")"
PKG_NAME="$(sanitize_pkg "$PROJECT_DIR_NAME")"
OUTPUT_PATH="$OUT_DIR/$PROJECT_DIR_NAME"

b "Setting up Flutter for: $PROJECT_DIR_NAME"
i "Template: $TEMPLATE | Org: $ORG | Channel: $CHANNEL | Out dir: $OUT_DIR"
i "Platforms: ${DEDUP_PLATFORMS[*]}"
i "Package name: $PKG_NAME"
i "Flutter update mode: $FLUTTER_UPDATE_MODE"
[[ "$TEMPLATE" == "plugin" ]] && i "Plugin langs  iOS: $IOS_LANG  Android: $ANDROID_LANG"
[[ "$DRY_RUN" -eq 1 ]] && warn "Dry-run mode."

# ===== prerequisites =====
need_cmd xcode-select || die "xcode-select missing; install Xcode Command Line Tools."
xcode-select -p >/dev/null 2>&1 || run "xcode-select --install || true"

if ! need_cmd brew; then
  run 'NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  if [[ -x /opt/homebrew/bin/brew ]]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi
else
  if [[ -x /opt/homebrew/bin/brew ]]; then eval "$(/opt/homebrew/bin/brew shellenv)" || true; fi
fi
run "brew list git >/dev/null 2>&1 || brew install git"
run "brew list cocoapods >/dev/null 2>&1 || brew install cocoapods"

# ===== Flutter SDK (robust updater) =====
ensure_flutter() {
  local root="$FLUTTER_ROOT" channel="$CHANNEL"

  # reclone on demand
  if [[ "$FLUTTER_UPDATE_MODE" == "reclone" ]]; then
    warn "Recloning Flutter ($channel) into $root …"
    run "rm -rf \"$root\""
  fi

  if [[ ! -d "$root/.git" ]]; then
    run "mkdir -p \"$(dirname "$root")\""
    i "Cloning Flutter ($channel) to $root…"
    run "git clone --depth 1 -b \"$channel\" https://github.com/flutter/flutter.git \"$root\""
    return
  fi

  # Existing repo: fetch & check status
  i "Updating Flutter ($channel) at $root..."
  run "(cd \"$root\" && git remote set-url origin https://github.com/flutter/flutter.git >/dev/null 2>&1 || true)"
  run "(cd \"$root\" && git fetch origin --prune)"
  if ! (cd "$root" && git checkout "$channel" >/dev/null 2>&1); then
    run "(cd \"$root\" && git checkout -b \"$channel\" \"origin/$channel\")"
  fi

  # Try fast-forward first
  if run "(cd \"$root\" && git merge --ff-only \"origin/$channel\")"; then
    ok "Fast-forwarded Flutter to origin/$channel."
    return
  fi

  # Diverged handling
  if [[ "$FLUTTER_UPDATE_MODE" == "skip" ]]; then
    warn "Flutter repo has diverged; skipping update (per --flutter-update skip)."
    return
  fi

  b "Flutter repo has diverged from origin/$channel."
  local counts; counts="$(cd "$root" && git rev-list --left-right --count "origin/$channel...$channel" 2>/dev/null || echo "0 0")"
  local left_ahead right_ahead
  left_ahead="${counts%% *}"; right_ahead="${counts##* }"
  echo "Local ahead by: ${right_ahead:-0}; origin ahead by: ${left_ahead:-0}"

  read -rp "Hard reset Flutter to origin/$channel now? This discards local changes. [y/N] " ans
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    run "(cd \"$root\" && git reset --hard \"origin/$channel\")"
    ok "Reset Flutter to origin/$channel."
  else
    warn "Skipped reset. You can re-run with: --flutter-update reclone  (or fix manually)."
  fi
}
ensure_flutter

# Ensure PATH (persist + current shell)
append_once 'export PATH="$HOME/development/flutter/bin:$PATH"' "$ZPROFILE"
export PATH="$HOME/development/flutter/bin:$PATH"

# ===== doctor (summary + interactive licenses) =====
DOCTOR_OUT="$(flutter doctor -v 2>&1 || true)"
ISSUES="$(echo "$DOCTOR_OUT" | grep -E '(^|\s)✗' || true)"
if [[ -n "$ISSUES" ]]; then
  warn "flutter doctor found issues:"
  echo "$ISSUES"
fi
if echo "$DOCTOR_OUT" | grep -q "Some Android licenses not accepted"; then
  b "Android licenses not accepted."
  read -rp "Run 'flutter doctor --android-licenses' now? [y/N] " ans
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    flutter doctor --android-licenses
  else
    warn "Skipped license acceptance. You can run: flutter doctor --android-licenses"
  fi
fi

# ===== enable platform toggles =====
for p in "${DEDUP_PLATFORMS[@]}"; do
  case "$p" in
    ios) run "flutter config --enable-ios" ;;
    android) run "flutter config --enable-android" ;;
    macos) run "flutter config --enable-macos-desktop" ;;
    linux) run "flutter config --enable-linux-desktop" ;;
    windows) run "flutter config --enable-windows-desktop" ;;
    web) run "flutter config --enable-web" ;;
  esac
done

# Android extras if requested
for p in "${DEDUP_PLATFORMS[@]}"; do [[ "$p" == "android" ]] && {
  run "brew list --cask temurin >/dev/null 2>&1 || brew install --cask temurin"
  run "brew list --cask android-commandlinetools >/dev/null 2>&1 || brew install --cask android-commandlinetools"
  break
}; done

# CocoaPods spec update if iOS requested
for p in "${DEDUP_PLATFORMS[@]}"; do [[ "$p" == "ios" ]] && { run "pod repo update || true"; break; }; done

# ===== create project (explicit output path) =====
run "mkdir -p \"$OUT_DIR\""

if [[ -d "$OUTPUT_PATH" ]]; then
  warn "Directory '$OUTPUT_PATH' exists—skipping create."
else
  CREATE_CMD=(flutter create
    --org "$ORG"
    --project-name "$PKG_NAME"
    --platforms="$PLAT_CSV"
    --template "$TEMPLATE"
  )
  if [[ "$TEMPLATE" == "plugin" ]]; then
    CREATE_CMD+=(--ios-language "$IOS_LANG" --android-language "$ANDROID_LANG")
  fi
  CREATE_CMD+=("$OUTPUT_PATH")

  i "Creating Flutter project at $OUTPUT_PATH..."
  run "${CREATE_CMD[@]}"
  ok "Project created at: $OUTPUT_PATH"
fi

# ===== Cursor-friendly bootstrapping =====
app_post_bootstrap() {
  local path="$1" pkg="$2"
  i "Bootstrapping development & testing helpers…"

  # .vscode (Cursor/VSCode config)
  run "mkdir -p \"$path/.vscode\""
  cat > "$path/.vscode/settings.json" <<'JSON'
{
  "dart.flutterHotReloadOnSave": "all",
  "dart.lineLength": 100,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "Dart-Code.dart-code",
  "files.exclude": {
    "**/.dart_tool": true,
    "**/build": true
  }
}
JSON
  cat > "$path/.vscode/launch.json" <<'JSON'
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Flutter Debug",
      "request": "launch",
      "type": "dart"
    }
  ]
}
JSON

  # Makefile
  cat > "$path/Makefile" <<'MAKE'
run:
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
MAKE

  # Tests layout
  run "mkdir -p \"$path/test/unit\" \"$path/test/widget\" \"$path/integration_test\""

  # Unit test
  cat > "$path/test/unit/sanity_test.dart" <<'DART'
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('sanity check', () {
    expect(1 + 1, equals(2));
  });
}
DART

  # Widget test (imports app)
  cat > "$path/test/widget/app_widget_test.dart" <<DART
import 'package:flutter_test/flutter_test.dart';
import 'package:$pkg/main.dart';

void main() {
  testWidgets('App loads without errors', (tester) async {
    await tester.pumpWidget(const MyApp());
    expect(find.byType(MyApp), findsOneWidget);
  });
}
DART

  # Integration test
  cat > "$path/integration_test/app_test.dart" <<DART
import 'package:integration_test/integration_test.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:$pkg/main.dart';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('home page renders', (tester) async {
    await tester.pumpWidget(const MyApp());
    expect(find.byType(MyApp), findsOneWidget);
  });
}
DART

  # Lints & analysis
  cat > "$path/analysis_options.yaml" <<'YAML'
include: package:flutter_lints/flutter.yaml

linter:
  rules:
    avoid_print: false
    prefer_const_constructors: true
YAML

  # GitHub Actions CI
  run "mkdir -p \"$path/.github/workflows\""
  cat > "$path/.github/workflows/flutter-ci.yml" <<'YAML'
name: Flutter CI

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
YAML

  # .env support via flutter_dotenv
  # Add deps using flutter tooling (avoids manual YAML edits):
  (cd "$path" && flutter pub add flutter_dotenv >/dev/null 2>&1 || true)
  (cd "$path" && flutter pub add --dev flutter_lints integration_test >/dev/null 2>&1 || true)

  # Create a sample .env (not committed if you add to .gitignore)
  cat > "$path/.env" <<'ENV'
# Example environment variables
API_URL=https://api.example.com
ENV

  # Patch lib/main.dart to load .env (safe-ish sed edits)
  if [[ -f "$path/lib/main.dart" ]] && ! grep -q "flutter_dotenv" "$path/lib/main.dart"; then
    # insert import after first 'import 'package:flutter' line or at top
    if grep -n "package:flutter/" "$path/lib/main.dart" >/dev/null 2>&1; then
      line_no="$(grep -n "package:flutter/" "$path/lib/main.dart" | head -n1 | cut -d: -f1)"
      awk -v n="$line_no" 'NR==n{print; print "import '\''package:flutter_dotenv/flutter_dotenv.dart'\'';"; next}1' "$path/lib/main.dart" > "$path/lib/main.tmp.dart" && mv "$path/lib/main.tmp.dart" "$path/lib/main.dart"
    else
      { echo "import 'package:flutter_dotenv/flutter_dotenv.dart';"; cat "$path/lib/main.dart"; } > "$path/lib/main.tmp.dart" && mv "$path/lib/main.tmp.dart" "$path/lib/main.dart"
    fi
    # make main async and load dotenv if we find 'void main() {'
    if grep -q "^void main()" "$path/lib/main.dart"; then
      sed -i '' 's/^void main() {/Future<void> main() async {/' "$path/lib/main.dart"
      # insert dotenv.load just after the opening brace
      sed -i '' '0,/Future<void> main() async {/{/Future<void> main() async {/a\
  await dotenv.load(fileName: ".env");
}' "$path/lib/main.dart"
    fi
    # If the app uses runApp(MyApp()) elsewhere, leave as-is.
  fi

  # README quickstart
  cat > "$path/README.md" <<MD
# ${PROJECT_DIR_NAME}

Flutter app scaffolded for Cursor.

## Quickstart
\`\`\`bash
flutter pub get
make run            # runs on Chrome by default
\`\`\`

## Testing
\`\`\`bash
make test           # unit + widget tests
make integration    # integration_test/
\`\`\`

## Linting
\`\`\`bash
make analyze
\`\`\`

## Env vars
Edit \`.env\` and access with \`dotenv.env['KEY']\` after startup.
MD

  # Format everything (best effort)
  (cd "$path" && dart format . >/dev/null 2>&1 || true)
}
app_post_bootstrap "$OUTPUT_PATH" "$PKG_NAME"

cat <<'NEXT'
Next steps:
  source ~/.zprofile
  cd "<OUT_DIR>/<PROJECT_DIR_NAME>"
  make run           # or: flutter run -d chrome / ios / android
  make test          # run tests
  make analyze       # check lints

Open in Cursor and hit F5 ("Flutter Debug") to start debugging.
NEXT
