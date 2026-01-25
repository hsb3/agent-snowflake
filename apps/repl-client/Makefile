.PHONY: help install repl tui tui-dev test lint format type-check clean

help:
	@echo "REPL Client - Classic REPL for LangGraph Dev Server"
	@echo ""
	@echo "Prerequisites: A running LangGraph Dev Server"
	@echo "  - From this monorepo: cd ../agent && make dev-server"
	@echo "  - Or configure LANGGRAPH_DEV_SERVER_URL in .env"
	@echo ""
	@echo "Commands:"
	@echo "  make install    - Install dependencies with uv"
	@echo "  make repl       - Start classic REPL"
	@echo "  make tui        - Start TUI client"
	@echo "  make tui-dev    - Start TUI with hot reload"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Lint code"
	@echo "  make format     - Format code"
	@echo "  make type-check - Type check"
	@echo "  make clean      - Remove caches"

install:
	uv sync --package repl-client

repl:
	uv run python -m repl_client

tui:
	@echo "Starting TUI client..."
	@echo "Tip: Press Ctrl+P for commands, F4 for sidebar"
	uv run python -m repl_client.tui

tui-dev:
	@echo "Starting TUI in dev mode..."
	TEXTUAL_DEVTOOLS=1 uv run python -m repl_client.tui

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
