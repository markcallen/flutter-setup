.PHONY: help install dev test lint type-check format check-all clean smoke-build-fast smoke-build-full smoke-test-fast smoke-test-full

help:
	@echo "Available commands:"
	@echo "  install            - Install dependencies"
	@echo "  dev                - Install in development mode"
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

install:
	uv pip install .

dev:
	uv pip install -e ".[dev]"

test:
	uv run pytest

lint:
	uv run ruff check .

type-check:
	uv run mypy .

format:
	uv run black .

check-all: lint type-check test

smoke-build-fast:
	docker compose -f docker-compose.smoke-fast.yaml build

smoke-build-full:
	docker compose -f docker-compose.smoke-full.yaml build

smoke-test-fast:
	docker compose -f docker-compose.smoke-fast.yaml up smoke-test-fast --exit-code-from smoke-test-fast

smoke-test-full:
	docker compose -f docker-compose.smoke-full.yaml up smoke-test-full --exit-code-from smoke-test-full

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} +
