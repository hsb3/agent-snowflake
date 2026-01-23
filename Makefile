.PHONY: help install setup-test-db setup-chinook dev test test-fast format lint type-check clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies with uv"
	@echo "  make setup-test-db  - Create test SQLite database with stub TPC-H data"
	@echo "  make setup-chinook  - Download Chinook database (digital media store, 11 tables)"
	@echo "  make dev            - Start LangGraph dev server with Studio UI"
	@echo "  make test           - Run all tests with pytest"
	@echo "  make test-fast      - Run tests excluding slow tests"
	@echo "  make format         - Format code with ruff"
	@echo "  make lint           - Lint code with ruff"
	@echo "  make type-check     - Type check with ty"
	@echo "  make clean          - Remove generated files and caches"

# Installation
install:
	uv sync --group dev

# Test Database Setup
setup-fakesnow:
	uv run python scripts/setup_fakesnow_db.py

# Chinook Database Setup (recommended for testing)
setup-chinook:
	uv run python scripts/setup_chinook_db.py

# Development
dev:
	@echo "Starting LangGraph dev server..."
	@echo "Studio UI will be available at http://localhost:8123"
	@echo "Note: Using --allow-blocking for SQLite file operations"
	uv run langgraph dev --allow-blocking

# Testing
test:
	uv run pytest tests/ -v

test-fast:
	uv run pytest tests/ -v -k "not emulator"

# Code Quality
format:
	uv run ruff format src/ tests/

lint:
	uv run ruff check src/ tests/

type-check:
	uv run ty check src/

# Cleanup
clean:
	@echo "Cleaning up generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -f test_snowflake.db test_chinook.db 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true
	rm -rf .venv .langgraph_api
	@echo "Cleanup complete (preserved .env, .env.local)"
