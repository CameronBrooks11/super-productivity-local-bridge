.PHONY: install format lint typecheck test cov check clean

## Install dependencies
install:
	uv sync

## Format code
format:
	uv run ruff format .

## Lint code (with auto-fix)
lint:
	uv run ruff check --fix .

## Type check
typecheck:
	uv run pyright

## Run tests
test:
	uv run pytest

## Run tests with coverage
cov:
	uv run pytest --cov --cov-report=term-missing

## Run all checks (CI-equivalent)
check: install
	uv run ruff format --check .
	uv run ruff check .
	uv run pyright
	uv run pytest
	uv build --quiet

## Remove build artifacts
clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage
