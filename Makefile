# ============================================================================
# Agent Snowflake Monorepo
# ============================================================================
# Orchestration Makefile for multi-app repository
#
# Apps (each has its own .venv):
#   - agent           : LangGraph SQL agent with guardrails
#   - repl-client     : Classic REPL client for LangGraph servers
#   - repl-client-graph : StateGraph-based REPL implementation
#
# Usage: make <target>
# ============================================================================

.DEFAULT_GOAL := help

# ============================================================================
# CONFIGURATION
# ============================================================================

# App directories
APPS_DIR := apps
APP_AGENT := $(APPS_DIR)/agent
APP_REPL := $(APPS_DIR)/repl-client
APP_REPL_GRAPH := $(APPS_DIR)/repl-client-graph

# Default port for LangGraph dev server
DEFAULT_PORT := 2024

# ============================================================================
# COLORS
# ============================================================================

RESET := \033[0m
BOLD := \033[1m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
CYAN := \033[36m

# ============================================================================
# PHONY TARGETS
# ============================================================================

.PHONY: help install install-agent install-repl test clean dev dev-server

# ============================================================================
# HELP
# ============================================================================

help:
	@echo ""
	@printf "$(BOLD)Agent Snowflake Monorepo$(RESET)\n"
	@echo ""
	@printf "$(YELLOW)Note:$(RESET) Each app has its own virtual environment.\n"
	@echo ""
	@printf "$(BOLD)Setup$(RESET):\n"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "install" "Install all apps (creates separate .venv per app)"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "install-agent" "Install agent app only"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "install-repl" "Install repl-client app only"
	@echo ""
	@printf "$(BOLD)Development$(RESET):\n"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "dev" "Start LangGraph dev server with Studio UI"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "dev-server" "Start dev server without browser"
	@echo ""
	@printf "$(BOLD)Testing$(RESET):\n"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "test" "Run tests for all apps"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "test-agent" "Run agent tests only"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "test-repl" "Run repl-client tests only"
	@echo ""
	@printf "$(BOLD)Maintenance$(RESET):\n"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "clean" "Remove caches (preserves .venv)"
	@printf "  $(CYAN)%-20s$(RESET) %s\n" "clean-venvs" "Remove all .venv directories"
	@echo ""
	@printf "$(BOLD)Per-App Commands$(RESET):\n"
	@echo "  cd $(APP_AGENT) && make help"
	@echo "  cd $(APP_REPL) && make help"
	@echo ""

# ============================================================================
# SETUP
# ============================================================================

install: install-agent install-repl
	@echo "$(GREEN)All apps installed.$(RESET)"

install-agent:
	@echo "$(BLUE)Installing agent dependencies...$(RESET)"
	cd $(APP_AGENT) && make install
	@echo "$(GREEN)Agent installed.$(RESET)"

install-repl:
	@echo "$(BLUE)Installing repl-client dependencies...$(RESET)"
	cd $(APP_REPL) && make install
	@echo "$(GREEN)REPL client installed.$(RESET)"

# ============================================================================
# DEVELOPMENT
# ============================================================================

dev:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-$(DEFAULT_PORT)}; \
	echo "$(GREEN)Starting LangGraph dev server on port $$PORT...$(RESET)"; \
	echo "$(CYAN)Studio UI will be available at http://localhost:$$PORT$(RESET)"; \
	cd $(APP_AGENT) && uv run langgraph dev --allow-blocking --port $$PORT

dev-server:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-$(DEFAULT_PORT)}; \
	echo "$(GREEN)Starting LangGraph dev server on port $$PORT (no browser)...$(RESET)"; \
	cd $(APP_AGENT) && uv run langgraph dev --allow-blocking --port $$PORT --no-browser

# ============================================================================
# TESTING
# ============================================================================

test: test-agent test-repl
	@echo "$(GREEN)All tests complete.$(RESET)"

test-agent:
	@echo "$(YELLOW)Testing agent...$(RESET)"
	cd $(APP_AGENT) && make test

test-repl:
	@echo "$(YELLOW)Testing repl-client...$(RESET)"
	cd $(APP_REPL) && make test

# ============================================================================
# MAINTENANCE
# ============================================================================

clean:
	@echo "$(YELLOW)Cleaning up caches...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete (preserved .venv directories)$(RESET)"

clean-venvs:
	@echo "$(YELLOW)Removing all .venv directories...$(RESET)"
	rm -rf .venv $(APP_AGENT)/.venv $(APP_REPL)/.venv $(APP_REPL_GRAPH)/.venv
	@echo "$(GREEN)All virtual environments removed.$(RESET)"
