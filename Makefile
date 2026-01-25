.PHONY: help install setup-test-db setup-chinook dev dev-server repl repl-tui repl-graph tui tui-dev test test-fast test-repl check-repl format format-repl lint lint-repl type-check type-check-repl clean

# Default target
help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies with uv"
	@echo "  make setup-test-db  - Create test SQLite database with stub TPC-H data"
	@echo "  make setup-chinook  - Download Chinook database (digital media store, 11 tables)"
	@echo "  make dev            - Start LangGraph dev server with Studio UI"
	@echo "  make dev-server     - Start LangGraph dev server without browser (for REPL)"
	@echo "  make tui            - Start TUI client only (requires server running)"
	@echo "  make tui-dev        - Start TUI in dev mode with hot reload"
	@echo "  make repl           - Start server + classic REPL client together"
	@echo "  make repl-tui       - Start server + TUI client together"
	@echo "  make repl-graph     - Start server + StateGraph REPL client together"
	@echo "  make test           - Run all tests with pytest"
	@echo "  make test-fast      - Run tests excluding slow tests"
	@echo "  make test-repl      - Run only repl_client tests"
	@echo "  make check-repl     - Run lint + type-check + test on repl_client"
	@echo "  make format         - Format code with ruff"
	@echo "  make format-repl    - Format only repl_client code"
	@echo "  make lint           - Lint code with ruff"
	@echo "  make lint-repl      - Lint only repl_client code"
	@echo "  make type-check     - Type check with ty"
	@echo "  make type-check-repl - Type check only repl_client code"
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
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	echo "Starting LangGraph dev server on port $$PORT..."; \
	echo "Studio UI will be available at http://localhost:$$PORT"; \
	echo "Note: Using --allow-blocking for SQLite file operations"; \
	uv run langgraph dev --allow-blocking --port $$PORT

dev-server:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	echo "Starting LangGraph dev server on port $$PORT (no browser)..."; \
	echo "API available at http://localhost:$$PORT"; \
	echo "Press Ctrl+C to stop"; \
	uv run langgraph dev --allow-blocking --port $$PORT --no-browser

repl:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	mkdir -p .repl; \
	echo "Starting LangGraph server + classic REPL..."; \
	echo "Server logs: .repl/server.log"; \
	uv run langgraph dev --allow-blocking --port $$PORT --no-browser > .repl/server.log 2>&1 & \
	SERVER_PID=$$!; \
	trap "echo 'Stopping server...'; kill $$SERVER_PID 2>/dev/null; exit" INT TERM; \
	sleep 3; \
	echo "Server ready on port $$PORT"; \
	echo "Starting classic REPL client..."; \
	uv run python -m repl_client || true; \
	echo "Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null

repl-tui:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	mkdir -p .repl; \
	echo "Starting LangGraph server + TUI client..."; \
	echo "Server logs: .repl/server.log"; \
	uv run langgraph dev --allow-blocking --port $$PORT --no-browser > .repl/server.log 2>&1 & \
	SERVER_PID=$$!; \
	trap "echo 'Stopping server...'; kill $$SERVER_PID 2>/dev/null; exit" INT TERM; \
	sleep 3; \
	echo "Server ready on port $$PORT"; \
	echo "Starting TUI client..."; \
	echo ""; \
	echo "TIP: Press Ctrl+P for command palette, F4 for sidebar"; \
	echo ""; \
	uv run python -m repl_client.tui || true; \
	echo "Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null

repl-graph:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	mkdir -p .repl; \
	echo "Starting LangGraph server + StateGraph REPL..."; \
	echo "Server logs: .repl/server.log"; \
	uv run langgraph dev --allow-blocking --port $$PORT --no-browser > .repl/server.log 2>&1 & \
	SERVER_PID=$$!; \
	trap "echo 'Stopping server...'; kill $$SERVER_PID 2>/dev/null; exit" INT TERM; \
	sleep 3; \
	echo "Server ready on port $$PORT"; \
	echo "Starting StateGraph REPL client..."; \
	uv run python -m repl_client_graph || true; \
	echo "Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null

# TUI Only (decoupled from server)
tui:
	@echo "Starting TUI client..."; \
	echo ""; \
	echo "Tip: Press Ctrl+P for commands, F4 for sidebar"; \
	echo ""; \
	uv run python -m repl_client.tui

tui-dev:
	@echo "Starting TUI in dev mode..."; \
	echo ""; \
	echo "Tip: Restart after file changes to see updates"; \
	echo "     Press Ctrl+P for command palette"; \
	echo "     Press Ctrl+D to toggle light/dark mode"; \
	echo ""; \
	TEXTUAL_DEVTOOLS=1 uv run python -m repl_client.tui

# Testing
test:
	uv run pytest tests/ -v

test-fast:
	uv run pytest tests/ -v -k "not emulator"

test-repl:
	uv run pytest tests/repl_client/ -v

# REPL Client Quality Checks (focused on repl_client only)
check-repl: lint-repl type-check-repl test-repl
	@echo ""
	@echo "✓ All repl_client checks passed!"

# Code Quality
format:
	uv run ruff format src/ tests/

format-repl:
	uv run ruff format src/repl_client/ tests/repl_client/

lint:
	uv run ruff check src/ tests/

lint-repl:
	uv run ruff check src/repl_client/ tests/repl_client/

type-check:
	uv run ty check src/

type-check-repl:
	uv run ty check src/repl_client/

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