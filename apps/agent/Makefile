.PHONY: help install setup-chinook setup-fakesnow dev dev-server test lint format type-check clean

help:
	@echo "Agent Snowflake - LangGraph SQL Agent"
	@echo ""
	@echo "Commands:"
	@echo "  make install        - Install dependencies with uv"
	@echo "  make setup-chinook  - Download Chinook test database"
	@echo "  make setup-fakesnow - Create FakeSnow TPC-H stub database"
	@echo "  make dev            - Start LangGraph dev server with Studio UI"
	@echo "  make dev-server     - Start server without browser"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Lint code"
	@echo "  make format         - Format code"
	@echo "  make type-check     - Type check"
	@echo "  make clean          - Remove caches"

install:
	uv sync --package agent-snowflake

setup-chinook:
	uv run python scripts/setup_chinook_db.py

setup-fakesnow:
	uv run python scripts/setup_fakesnow_db.py

dev:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	uv run langgraph dev --allow-blocking --port $$PORT

dev-server:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	uv run langgraph dev --allow-blocking --port $$PORT --no-browser

test:
	uv run pytest tests/ -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

type-check:
	uv run ty check src/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
