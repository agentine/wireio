.PHONY: install build test lint fmt clean ci

install:
	uv sync

build:
	uv build

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/
	uv run mypy src/

fmt:
	uv run ruff format src/ tests/

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .mypy_cache/

ci: lint test
