.PHONY: help install setup-test-db dev test test-fast format lint type-check clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies with uv"
	@echo "  make setup-test-db  - Create test SQLite database with sample data"
	@echo "  make dev            - Start LangGraph dev server with Studio UI"
	@echo "  make test           - Run all tests with pytest"
	@echo "  make test-fast      - Run tests excluding slow tests"
	@echo "  make format         - Format code with ruff"
	@echo "  make lint           - Lint code with ruff"
	@echo "  make type-check     - Type check with ty"
	@echo "  make clean          - Remove generated files and caches"

# Installation
install:
	uv sync

# Test Database Setup
setup-test-db:
	uv run python scripts/setup_fakesnow_db.py

# Development
dev:
	@echo "Starting LangGraph dev server..."
	@echo "Studio UI will be available at http://localhost:8123"
	langgraph dev

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
	@echo "Cleanup complete"
