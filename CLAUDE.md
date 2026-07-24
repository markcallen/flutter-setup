# CLAUDE.md

This file provides guidance to Claude Code for working in this repository.

## Before Starting Work

Run `make setup` before making any code changes. This installs dependencies, sets up the local dev environment, and installs pre-commit hooks:

```bash
make setup
```

This must be run once per worktree or fresh checkout. Without it, pre-commit hooks won't run and the linter/formatter won't be available.

## Repository Facts

Use this section for durable repo-specific facts that agents repeatedly need. Prefer facts stored here over re-deriving them with shell commands on every task.

Keep only stable, reviewable metadata here. Do not store secrets, credentials, or ephemeral runtime state.

Suggested facts to record:

- Canonical GitHub repo: `markcallen/flutter-setup`
- Default branch: `main`
- Primary package manager: `uv`
- Version-file locations agents should check first: `pyproject.toml, uv.lock, .python-version`
- Canonical config files: `pyproject.toml`
- Primary CI workflows: `testing.yaml`
- Primary release/publish workflows: `<workflow filenames>`
- Preferred build/test/lint/format/coverage commands: `make test, make lint`
- Coverage threshold: `<value>`
- Generated or protected paths agents should avoid editing directly: `.ballast/`

Update this section when those facts change. If live runtime state is required, discover it separately instead of treating it as a durable repo fact.

## Installed agent rules

Created by Ballast. Do not edit this section.

Read and follow these rule files in `.claude/rules/` when they apply:
