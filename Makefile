# ============================================================================
# Agent Snowflake Monorepo
# ============================================================================
# Orchestration Makefile for multi-app workspace
#
# Apps:
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

UV := uv
APPS_DIR := apps
PACKAGES_DIR := packages

# App directories
APP_AGENT := $(APPS_DIR)/agent
APP_REPL := $(APPS_DIR)/repl-client
APP_REPL_GRAPH := $(APPS_DIR)/repl-client-graph

# All app source directories for type checking
APP_SOURCES := $(APP_AGENT)/src $(APP_REPL)/src $(APP_REPL_GRAPH)/src

# Default port for LangGraph dev server
DEFAULT_PORT := 2024

# ============================================================================
# COLORS (for visual output)
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

.PHONY: help install test format lint type-check clean dev dev-server check

# ============================================================================
# HELP
# ============================================================================

## help: Show this help message
help:
	@echo ""
	@printf "$(BOLD)Agent Snowflake Monorepo$(RESET)\n"
	@echo ""
	@printf "$(BOLD)Usage:$(RESET) make $(CYAN)<target>$(RESET)\n"
	@awk '/^## [A-Z]+:$$/ { \
		gsub(/^## /, ""); gsub(/:$$/, ""); \
		printf "\n$(BOLD)%s$(RESET):\n", $$0; \
		next \
	} \
	/^## [a-z]/ { \
		gsub(/^## /, ""); \
		split($$0, parts, ": "); \
		printf "  $(CYAN)%-18s$(RESET) %s\n", parts[1], parts[2] \
	}' $(MAKEFILE_LIST)
	@echo ""
	@printf "$(BOLD)Per-App Commands$(RESET):\n"
	@echo "  cd $(APP_AGENT) && make help"
	@echo "  cd $(APP_REPL) && make help"
	@echo "  cd $(APP_REPL_GRAPH) && make help"
	@echo ""

# ============================================================================
# SETUP
# ============================================================================

## SETUP:

## install: Install all workspace dependencies
install:
	@echo "$(GREEN)Installing workspace dependencies...$(RESET)"
	$(UV) sync
	@echo "$(GREEN)Done.$(RESET)"

# ============================================================================
# DEVELOPMENT
# ============================================================================

## DEV:

## dev: Start LangGraph dev server with Studio UI
dev:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-$(DEFAULT_PORT)}; \
	echo "$(GREEN)Starting LangGraph dev server on port $$PORT...$(RESET)"; \
	echo "$(CYAN)Studio UI will be available at http://localhost:$$PORT$(RESET)"; \
	$(UV) run langgraph dev --config $(APP_AGENT)/langgraph.json --allow-blocking --port $$PORT

## dev-server: Start dev server without browser (for REPL clients)
dev-server:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-$(DEFAULT_PORT)}; \
	echo "$(GREEN)Starting LangGraph dev server on port $$PORT (no browser)...$(RESET)"; \
	$(UV) run langgraph dev --config $(APP_AGENT)/langgraph.json --allow-blocking --port $$PORT --no-browser

# ============================================================================
# TESTING
# ============================================================================

## TEST:

## test: Run all app tests
test:
	@echo "$(GREEN)Running tests for all apps...$(RESET)"
	@echo "$(YELLOW)Testing agent...$(RESET)"
	cd $(APP_AGENT) && make test
	@echo "$(YELLOW)Testing repl-client...$(RESET)"
	cd $(APP_REPL) && make test
	@echo "$(YELLOW)Testing repl-client-graph...$(RESET)"
	cd $(APP_REPL_GRAPH) && make test
	@echo "$(GREEN)All tests complete.$(RESET)"

# ============================================================================
# CODE QUALITY
# ============================================================================

## QUALITY:

## format: Format all code with ruff
format:
	@echo "$(GREEN)Formatting code...$(RESET)"
	$(UV) run ruff format $(APPS_DIR)/ $(PACKAGES_DIR)/
	@echo "$(GREEN)Done.$(RESET)"

## lint: Lint all code with ruff
lint:
	@echo "$(GREEN)Linting code...$(RESET)"
	$(UV) run ruff check $(APPS_DIR)/ $(PACKAGES_DIR)/
	@echo "$(GREEN)Done.$(RESET)"

## type-check: Type check all code with ty
type-check:
	@echo "$(GREEN)Type checking code...$(RESET)"
	$(UV) run ty check $(APP_SOURCES)
	@echo "$(GREEN)Done.$(RESET)"

## check: Run lint + type-check
check: lint type-check
	@echo "$(GREEN)All quality checks passed.$(RESET)"

# ============================================================================
# MAINTENANCE
# ============================================================================

## MAINT:

## clean: Remove all caches and generated files
clean:
	@echo "$(YELLOW)Cleaning up generated files...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete (preserved .env, .venv)$(RESET)"
