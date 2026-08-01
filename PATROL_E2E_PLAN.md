# Add Patrol as an End-to-End Test Option

## Goal

Add an end-to-end testing selection that is independent of the existing unit/widget
testing scaffold. The default Flutter end-to-end framework should remain available
as `integration_test`, and Patrol should be selectable for projects that need
native platform automation.

References:

- Flutter integration testing concepts: https://docs.flutter.dev/cookbook/testing/integration/introduction
- Flutter integration test guide: https://docs.flutter.dev/testing/integration-tests
- Patrol documentation: https://patrol.leancode.co/documentation

## Product Shape

Use a new option named `--e2e-testing` for both `create` and `append`.

Allowed values:

- `integration_test`: default. Uses Flutter SDK `integration_test`.
- `patrol`: adds Patrol setup in addition to the normal Flutter integration test
  structure where useful.

Keep `--testing` unchanged. It controls unit/widget starter choices such as
`standard` and `mocktail`.

Document this as its own "End-to-End Testing" section immediately after the
unit/widget testing section in the `create` and `append` command docs. In the
README options table, place `--e2e-testing` directly after `--testing`.

## Implementation Plan

1. Add configuration support.
   - Add `E2ETesting = Literal["integration_test", "patrol"]` in
     `flutter_setup/config.py`.
   - Add `e2e_testing: E2ETesting = "integration_test"` to `Config`.
   - Validate the value in `Config._validate()`.
   - Add `e2e_testing: integration_test` to the default config in
     `flutter_setup/config_manager.py`.
   - Preserve `e2e_testing` in `flutter-setup init` when an existing config file
     already contains it.

2. Add CLI support for `create`.
   - Import `E2ETesting` in `flutter_setup/cli.py`.
   - Add `--e2e-testing` after `--testing` in the `create` command definition.
   - Merge CLI, config, and prompt values using the existing
     `get_merged_or_prompt()` pattern.
   - Prompt label: `End-to-end testing framework`.
   - Pass `e2e_testing=merged_e2e_testing` into `Config`.

3. Add CLI support for `append`.
   - Add `--e2e-testing` after `--testing` in the `append` command definition.
   - For existing Flutter projects, include the selected value in the `Config`
     used by `ProjectBootstrap.append_project()`.
   - For non-Flutter directories that route to full setup, pass it into `Config`.
   - Prefer config-file values when the user did not explicitly pass the option,
     matching the intent of the existing `append` config merge behavior.

4. Generate project files for `integration_test`.
   - Keep the current `integration_test/` directory and
     `integration_test/app_test.dart` sample.
   - Keep adding `integration_test: {sdk: flutter}` to `dev_dependencies`.
   - Keep the Makefile `integration` target as:
     `flutter test integration_test`.

5. Generate project files for `patrol`.
   - Add a `patrol_test/` directory and sample `patrol_test/app_test.dart`.
   - Add `patrol` as a dev dependency when `e2e_testing == "patrol"`.
   - Add a helper that writes the required `patrol:` pubspec section with:
     `app_name`, Android package name when Android is selected, iOS bundle id
     when iOS is selected, and macOS bundle id when macOS is selected.
   - Derive identifiers from existing config conventions:
     `android.package_name = {org}.{package_name}`,
     `ios.bundle_id = {org}.{package_name}`,
     `macos.bundle_id = {org}.{package_name}`.
   - Add Patrol-generated and local-secret files to `.gitignore`:
     `**/test_bundle.dart` and `.patrol.env`.
   - Add a Makefile target after `integration`:
     `patrol-test: ...`
     `patrol test -t patrol_test/app_test.dart`
   - Add a `patrol-doctor` target:
     `patrol doctor`
   - Consider keeping `integration` even when Patrol is selected so projects can
     still run the default Flutter framework.

6. Append behavior.
   - `_append_makefile()` should naturally append new Patrol targets because it
     filters by target name.
   - `append_project()` currently avoids mutating `pubspec.yaml` and source
     files. Decide explicitly whether `append --e2e-testing patrol` may update
     `pubspec.yaml` and `.gitignore`.
   - Recommended behavior: allow only additive, idempotent updates for Patrol
     when explicitly selected. Do not overwrite existing `patrol:` config or
     test files unless `--force` is used.
   - Add console output that distinguishes "Makefile targets appended" from
     "Patrol e2e scaffold added".

7. README and generated README updates.
   - Add a README "End-to-End Testing" subsection after the unit/widget testing
     content.
   - List `integration_test` as the default Flutter SDK option.
   - List `patrol` as the option for native UI automation, permission dialogs,
     notifications, and platform views.
   - Add examples:
     `flutter-setup create MyApp ios android --e2e-testing patrol`
     `flutter-setup append --dir ./MyApp --e2e-testing patrol`
   - Update generated README text in `ProjectBootstrap._create_readme()` and
     `_append_readme()` to show `make integration`, and conditionally show
     `make patrol-test` / `make patrol-doctor`.

8. Tests.
   - `tests/test_config.py`: default `e2e_testing`, valid values, invalid value.
   - `tests/test_cli.py`: `create --e2e-testing patrol` reaches `Config`; config
     file value is honored; interactive prompt order puts e2e after testing.
   - `tests/test_cli.py` or `tests/test_e2e_create_append.py`: `append
     --e2e-testing patrol` reaches `ProjectBootstrap`.
   - `tests/test_bootstrap.py`: Makefile includes default `integration` and
     Patrol targets when selected.
   - `tests/test_bootstrap.py`: Patrol dev dependency and `patrol:` pubspec
     section are added idempotently.
   - `tests/test_bootstrap.py`: `.gitignore` gains `**/test_bundle.dart` and
     `.patrol.env` without duplicates.
   - `tests/test_e2e_fixtures.py`: append with default config preserves existing
     files; append with Patrol selected performs only the explicitly allowed
     additive changes.

9. Verification.
   - Run `uv run pytest`.
   - Run `uv run ruff check .`.
   - Run `uv run mypy .`.
   - Optionally run `uv run flutter-setup create --help` and
     `uv run flutter-setup append --help` to confirm option ordering and help
     text.

## Open Decisions

- Should `append --e2e-testing patrol` mutate `pubspec.yaml` by default, or
  should it only append Makefile/README guidance and require a separate explicit
  setup command later?
- Should Patrol use its default `patrol_test/` directory, or configure
  `test_directory: integration_test` so all end-to-end tests stay in one
  directory? The docs support either; `patrol_test/` is clearer for generated
  projects because both frameworks remain visible.
- Should the Patrol sample pump the app directly, or should generated projects
  expose a reusable app factory to reduce duplication between widget,
  integration, and Patrol tests?
