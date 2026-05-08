# Repository Guidelines

## Project Structure & Module Organization
- Core package code lives in `flutter_setup/`.
- CLI entrypoint: `flutter_setup/cli.py` (`flutter-setup` console script).
- Functional modules are split by concern: `config_manager.py`, `prerequisites.py`, `flutter_manager.py`, `project_creator.py`, `bootstrap.py`, and orchestration in `core.py`.
- Tests live in `tests/` and follow per-module coverage (for example, `tests/test_cli.py`, `tests/test_bootstrap.py`).
- Planning and design docs live at repository root (`README.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `PRD.md`).

## Build, Test, and Development Commands
- Install for development: `uv pip install -e ".[dev]"`
- Run CLI locally: `uv run flutter-setup --help`
- Run tests: `uv run pytest`
- Run tests with coverage report: `uv run pytest --cov=flutter_setup --cov-report=term-missing`
- Format code: `uv run black .`
- Lint: `uv run ruff check .`
- Type check: `uv run mypy .`
- Optional pre-commit gate: `uv run pre-commit run --all-files`

## Coding Style & Naming Conventions
- Python 3.12+ with 4-space indentation and type hints.
- Formatting is enforced by Black (`line-length = 88`).
- Linting uses Ruff; keep imports and control flow lint-clean.
- `mypy` runs in strict mode; new code should include precise types and avoid implicit `Any`.
- Naming: modules/functions in `snake_case`, classes in `PascalCase`, constants in `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Framework: `pytest` with `pytest-cov`.
- Test discovery is configured for `tests/test_*.py`, classes `Test*`, and functions `test_*`.
- Add or update tests for each behavior change; prefer module-aligned test files (for example, changes in `flutter_setup/config.py` should include updates in `tests/test_config.py`).

## Commit & Pull Request Guidelines
- Follow the repository’s existing style: short, imperative, descriptive subjects (for example, `Add tests for bootstrap flow`, `Fix CLI config override behavior`).
- Keep commits focused; avoid mixing refactors and feature changes.
- PRs should include:
  - concise summary of behavior changes,
  - linked issue (if applicable),
  - test evidence (`uv run pytest`, plus lint/type checks),
  - CLI output snippets when user-facing behavior changes.
- CI runs Black check, Ruff, mypy, and pytest coverage on pull requests and `main`; ensure all checks pass before merge.

## Installed agent rules

Created by [Ballast](https://github.com/everydaydevopsio/ballast) v5.9.3. Do not edit this section.

Read and follow these rule files in `.codex/rules/` when they apply:

- `.codex/rules/local-dev-badges.md` — Add standard badges (CI, Release, License, GitHub Release, npm) to the top of README.md
- `.codex/rules/local-dev-env.md` — Local development environment specialist - reproducible dev setup, DX, and documentation
- `.codex/rules/local-dev-license.md` — License setup - ensure LICENSE file, package.json license field, and README reference (default MIT; overridable in AGENTS.md/CLAUDE.md)
- `.codex/rules/local-dev-mcp.md` — Optional: use GitHub MCP and issues MCP (Jira/Linear/GitHub) for local-dev context
- `.codex/rules/cicd.md` — CI/CD specialist - pipeline design, quality gates, and deployment
- `.codex/rules/observability.md` — Observability specialist - logging, tracing, metrics, and SLOs
- `.codex/rules/typescript-linting.md` — TypeScript linting specialist - implements comprehensive linting and code formatting for TypeScript/JavaScript projects
- `.codex/rules/typescript-logging.md` — Centralized logging specialist - configures Pino with Fluentd for Node/Next.js, and pino-browser to /api/logs
- `.codex/rules/typescript-testing.md` — Testing specialist - sets up Jest (default) or Vitest for Vite projects, 50% coverage, and test step in build GitHub Action
- `.codex/rules/git-hooks.md` — Git hook specialist - configure pre-commit, pre-push, and Husky workflows that match the repository layout
