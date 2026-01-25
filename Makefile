.PHONY: help install-all test-all format-all lint-all type-check-all clean-all dev dev-server

# Default target
help:
	@echo "Agent Snowflake Monorepo"
	@echo ""
	@echo "Orchestration Commands:"
	@echo "  make install-all    - Install all apps"
	@echo "  make test-all       - Run all tests"
	@echo "  make format-all     - Format all code"
	@echo "  make lint-all       - Lint all code"
	@echo "  make type-check-all - Type check all code"
	@echo "  make clean-all      - Clean all caches"
	@echo ""
	@echo "Quick Start (Agent + REPL):"
	@echo "  make dev            - Start LangGraph dev server with Studio UI"
	@echo "  make dev-server     - Start server without browser"
	@echo ""
	@echo "Per-App Commands:"
	@echo "  cd apps/agent && make help"
	@echo "  cd apps/repl-client && make help"
	@echo "  cd apps/repl-client-graph && make help"

# Install all apps
install-all:
	uv sync

# Test all apps
test-all:
	cd apps/agent && make test
	cd apps/repl-client && make test
	cd apps/repl-client-graph && make test

# Format all code
format-all:
	uv run ruff format apps/ packages/

# Lint all code
lint-all:
	uv run ruff check apps/ packages/

# Type check all code
type-check-all:
	uv run ty check apps/agent/src/ apps/repl-client/src/ apps/repl-client-graph/src/

# Clean all caches
clean-all:
	@echo "Cleaning up all generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true
	@echo "Cleanup complete (preserved .env, .venv)"

# Quick start - dev server with Studio
dev:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	echo "Starting LangGraph dev server on port $$PORT..."; \
	echo "Studio UI will be available at http://localhost:$$PORT"; \
	uv run langgraph dev --allow-blocking --port $$PORT

# Dev server without browser (for REPL clients)
dev-server:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	echo "Starting LangGraph dev server on port $$PORT (no browser)..."; \
	uv run langgraph dev --allow-blocking --port $$PORT --no-browser
