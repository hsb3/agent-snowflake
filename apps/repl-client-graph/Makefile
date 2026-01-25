# ============================================================================
# REPL Client Graph - StateGraph REPL for LangGraph Dev Server
# ============================================================================
# A terminal REPL client using LangGraph StateGraph for control flow.
# Requires a running LangGraph Dev Server (start with: make dev-server from agent/)
# ============================================================================

.DEFAULT_GOAL := help

# ============================================================================
# CONFIGURATION
# ============================================================================

UV := uv
SRC_DIR := src
TEST_DIR := tests
PACKAGE := repl-client-graph

# Color codes for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m
BOLD := \033[1m

# ============================================================================
# HELP
# ============================================================================

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "$(BOLD)REPL Client Graph$(RESET) - StateGraph REPL for LangGraph Dev Server"
	@echo ""
	@echo "$(YELLOW)Prerequisites:$(RESET)"
	@echo "  A running LangGraph Dev Server is required before starting the REPL."
	@echo "  Start it with: $(CYAN)cd ../agent && make dev-server$(RESET)"
	@echo "  Or configure LANGGRAPH_DEV_SERVER_URL in .env"
	@echo ""
	@grep -E '^(## [A-Z]+|[a-zA-Z_-]+:.*?## .*)$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; \
		/^## / {printf "\n$(BOLD)%s$(RESET)\n", substr($$0, 4); next} \
		{printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'

# ============================================================================
# SETUP
# ============================================================================

## SETUP

.PHONY: install
install: ## Install dependencies with uv
	@echo "$(CYAN)Installing dependencies...$(RESET)"
	$(UV) sync --package $(PACKAGE)
	@echo "$(GREEN)Dependencies installed$(RESET)"

# ============================================================================
# DEV
# ============================================================================

## DEV

.PHONY: repl
repl: ## Start StateGraph REPL (requires running server)
	@echo "$(CYAN)Starting StateGraph REPL...$(RESET)"
	@echo "$(YELLOW)Note: Ensure LangGraph Dev Server is running$(RESET)"
	$(UV) run python -m repl_client_graph

# ============================================================================
# TEST
# ============================================================================

## TEST

.PHONY: test
test: ## Run all tests with pytest
	@echo "$(CYAN)Running tests...$(RESET)"
	$(UV) run pytest $(TEST_DIR)/ -v
	@echo "$(GREEN)Tests complete$(RESET)"

# ============================================================================
# QUALITY
# ============================================================================

## QUALITY

.PHONY: lint
lint: ## Lint code with ruff
	@echo "$(CYAN)Linting code...$(RESET)"
	$(UV) run ruff check $(SRC_DIR)/ $(TEST_DIR)/

.PHONY: format
format: ## Format code with ruff
	@echo "$(CYAN)Formatting code...$(RESET)"
	$(UV) run ruff format $(SRC_DIR)/ $(TEST_DIR)/
	@echo "$(GREEN)Formatting complete$(RESET)"

.PHONY: type-check
type-check: ## Type check with ty
	@echo "$(CYAN)Type checking...$(RESET)"
	$(UV) run ty check $(SRC_DIR)/

.PHONY: check
check: lint type-check test ## Run lint, type-check, and test
	@echo "$(GREEN)All checks passed$(RESET)"

# ============================================================================
# MAINT
# ============================================================================

## MAINT

.PHONY: clean
clean: ## Remove cache directories
	@echo "$(CYAN)Cleaning caches...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Caches cleaned$(RESET)"
