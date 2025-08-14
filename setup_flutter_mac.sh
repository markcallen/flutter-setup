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

dedupe_preserve_order(){
  # prints each unique arg once, preserving order
  local out=() p q found
  for p in "$@"; do
    found=0
    for q in "${out[@]}"; do [[ "$p" == "$q" ]] && found=1 && break; done
    [[ $found -eq 0 ]] && out+=("$p")
  done
  printf "%s\n" "${out[@]}"
}

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
# resolve + validate
declare -a CLEAN_PLATFORMS=()
for rp in "${RAW_PLATFORMS[@]}"; do
  rp="${rp// /}"; [[ -z "$rp" ]] && continue
  resolved="$(resolve_platform "$rp")"
  is_supported "$resolved" || { warn "Unsupported platform: '$rp'"; echo "Allowed: ${SUPPORTED_PLATFORMS[*]}"; exit 2; }
  CLEAN_PLATFORMS+=("$resolved")
done
# de-duplicate while preserving order
DEDUP_PLATFORMS=()
for p in "${CLEAN_PLATFORMS[@]}"; do
  found=0
  for q in "${DEDUP_PLATFORMS[@]}"; do [[ "$p" == "$q" ]] && found=1 && break; done
  [[ $found -eq 0 ]] && DEDUP_PLATFORMS+=("$p")
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
  # Add brew to PATH for Apple Silicon
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  fi
else
  # Ensure shellenv in current session if available
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)" || true
  fi
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
  i "Updating Flutter ($channel) at $root…"
  run "(cd \"$root\" && git remote set-url origin https://github.com/flutter/flutter.git >/dev/null 2>&1 || true)"
  run "(cd \"$root\" && git fetch origin --prune)"
  # ensure we’re on the channel branch and tracking origin
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
  # Show how far each side is ahead (no awk; parse with shell)
  local counts
  counts="$(cd "$root" && git rev-list --left-right --count "origin/$channel...$channel" 2>/dev/null || echo "0 0")"
  local left_ahead right_ahead
  left_ahead="${counts%% *}"
  right_ahead="${counts##* }"
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

# Offer to run android-licenses if needed (interactive; user accepts)
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

# Extra Android deps if requested
for p in "${DEDUP_PLATFORMS[@]}"; do [[ "$p" == "android" ]] && {
  run "brew list --cask temurin >/dev/null 2>&1 || brew install --cask temurin"
  run "brew list --cask android-commandlinetools >/dev/null 2>&1 || brew install --cask android-commandlinetools"
  break
}; done

# CocoaPods spec update for iOS
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
  # Only plugin supports language flags
  if [[ "$TEMPLATE" == "plugin" ]]; then
    CREATE_CMD+=(--ios-language "$IOS_LANG" --android-language "$ANDROID_LANG")
  fi
  CREATE_CMD+=("$OUTPUT_PATH")

  i "Creating Flutter project at $OUTPUT_PATH…"
  run "${CREATE_CMD[@]}"
  ok "Project created at: $OUTPUT_PATH"
fi

cat <<'NEXT'
Next steps:
  source ~/.zprofile
  cd "<OUT_DIR>/<PROJECT_DIR_NAME>"
  flutter run -d macos   # macOS desktop
  flutter run -d chrome  # Web
  flutter run -d ios     # iOS Simulator
  flutter run -d android # Android Emulator

If flutter doctor listed issues, fix them (Android SDK, Xcode signing, licenses) and re-run.
NEXT

