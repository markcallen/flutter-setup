.PHONY: help deps setup check-deps install dev test lint type-check format check-all clean smoke-build-fast smoke-build-full smoke-test-fast smoke-test-full

help:
	@echo "Available commands:"
	@echo "  deps               - Install Python via pyenv and uv (run once per machine)"
	@echo "  setup              - Set up the full dev environment (run after deps)"
	@echo "  check-deps         - Check that required tools are installed"
	@echo "  install            - Install package (production)"
	@echo "  dev                - Install package in development mode"
	@echo "  test               - Run tests with coverage"
	@echo "  lint               - Run ruff linter"
	@echo "  type-check         - Run mypy type checker"
	@echo "  format             - Format code with black"
	@echo "  check-all          - Run all quality checks (lint, type-check, test)"
	@echo "  smoke-build-fast   - Build image for fast smoke test"
	@echo "  smoke-build-full   - Build image for full smoke test"
	@echo "  smoke-test-fast    - Run fast smoke test (warm SDK)"
	@echo "  smoke-test-full    - Run full E2E smoke test (clean environment)"
	@echo "  clean              - Remove build artifacts and caches"

PYTHON_VERSION := $(shell cat .python-version 2>/dev/null || echo "3.12")

deps:
	@command -v pyenv > /dev/null 2>&1 || (echo "ERROR: pyenv not found. Install from https://github.com/pyenv/pyenv#installation" && exit 1)
	@command -v git > /dev/null 2>&1 || (echo "ERROR: git not found. Install git and try again." && exit 1)
	@echo "Installing Python $(PYTHON_VERSION) via pyenv..."
	@pyenv install --skip-existing $(PYTHON_VERSION)
	@pyenv local $(PYTHON_VERSION)
	@echo "Installing uv for Python $(PYTHON_VERSION)..."
	@pyenv exec pip install --quiet uv
	@echo "OK: Python $(PYTHON_VERSION) and uv installed via pyenv"

check-deps:
	@command -v pyenv > /dev/null 2>&1 || (echo "ERROR: pyenv not found. Install from https://github.com/pyenv/pyenv#installation" && exit 1)
	@command -v git > /dev/null 2>&1 || (echo "ERROR: git not found. Install git and try again." && exit 1)
	@pyenv version-name 2>/dev/null | grep -q "$(PYTHON_VERSION)" \
		|| (echo "ERROR: pyenv is not set to Python $(PYTHON_VERSION). Run 'make deps' first." && exit 1)
	@pyenv exec python -c "import sys; sys.exit(0) if sys.version_info >= (3, 12) else sys.exit('Python 3.12+ required, found ' + sys.version)" \
		|| (echo "ERROR: Python 3.12+ required." && exit 1)
	@pyenv exec python -m uv --version > /dev/null 2>&1 \
		|| (echo "ERROR: uv not found. Run 'make deps' first." && exit 1)
	@echo "OK: pyenv, Python $(PYTHON_VERSION), uv, and git all present"

setup: check-deps
	pyenv exec python -m uv sync
	pyenv exec python -m uv pip install -e ".[dev]"
	pyenv exec python -m uv run pre-commit install
	@echo ""
	@echo "Dev environment ready. Try 'make test' to verify."

install:
	pyenv exec python -m uv pip install .

dev:
	pyenv exec python -m uv pip install -e ".[dev]"

test:
	pyenv exec python -m uv run pytest

lint:
	pyenv exec python -m uv run ruff check .

type-check:
	pyenv exec python -m uv run mypy .

format:
	pyenv exec python -m uv run black .

check-all: lint type-check test

smoke-build-fast:
	docker compose -f docker-compose.smoke-fast-build.yaml build

smoke-build-full:
	docker compose -f docker-compose.smoke-full.yaml build

smoke-test-fast:
	docker compose -f docker-compose.smoke-fast.yaml up smoke-test-fast --exit-code-from smoke-test-fast

smoke-test-full:
	docker compose -f docker-compose.smoke-full.yaml up smoke-test-full --exit-code-from smoke-test-full

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
