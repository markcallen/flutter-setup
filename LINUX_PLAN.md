# Linux Enablement Plan

## 1. Scope and Target Distros
- Support Ubuntu/Debian first (APT).
- Add Fedora support (DNF) in phase 2.
- Define minimum supported versions for Python, Flutter, and optional Android tooling.

## 2. Platform Abstraction
- Add explicit OS detection (`darwin` vs `linux`) in orchestration code.
- Refactor macOS-only prerequisite logic into platform-specific handlers:
  - `prerequisites_macos.py`
  - `prerequisites_linux.py`

## 3. Linux Prerequisites
- Implement checks/install flow for core Linux dependencies:
  - `git`, `curl`, `unzip`, `xz-utils`, `zip`, `libglu1-mesa`, `clang`, `cmake`, `ninja-build`, `pkg-config`
- Generate package manager commands for APT in phase 1.
- Keep install actions promptable and compatible with dry-run mode.

## 4. Flutter Setup on Linux
- Remove macOS assumptions from Flutter path and environment setup.
- Add Linux shell profile updates (`~/.bashrc`, `~/.zshrc`) for PATH.
- Run `flutter doctor` and provide Linux-specific remediation guidance.

## 5. Bootstrap and Project Creation Compatibility
- Make generated setup artifacts OS-aware.
- Keep iOS setup conditional and explicitly skipped on Linux.
- Preserve Android/Web/Linux targets.

## 6. Test Coverage
- Add Linux-path unit tests in:
  - `tests/test_prerequisites.py`
  - `tests/test_flutter_manager.py`
  - `tests/test_core.py`
- Add mocks/fixtures for distro and package manager behavior.

## 7. CI Updates
- Ensure CI validates Linux support on `ubuntu-latest` with Python 3.12.
- Keep current quality gates: Black, Ruff, mypy, pytest, and coverage.

## 8. Documentation
- Update `README.md` with Linux install and usage examples.
- Document supported distros, package requirements, and known limitations.

## 9. Rollout
- Ship as a minor version release.
- Collect early Linux feedback and iterate with Fedora support next.
