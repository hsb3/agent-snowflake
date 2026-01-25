# =============================================================================
# Agent Snowflake - LangGraph SQL Agent
# =============================================================================

.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

UV := uv
SRC_DIR := src
TEST_DIR := tests
PACKAGE := agent-snowflake

# Port configuration (reads from .env or defaults to 2024)
PORT = $(shell grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' ' || echo 2024)
DEFAULT_PORT := 2024

# Color codes for terminal output
BLUE := \033[34m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m
BOLD := \033[1m

# -----------------------------------------------------------------------------
# HELP
# -----------------------------------------------------------------------------

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "$(BOLD)Agent Snowflake - LangGraph SQL Agent$(RESET)"
	@echo ""
	@grep -E '^(## |[a-zA-Z_-]+:.*?## )' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; \
		/^## / {printf "\n$(BOLD)%s$(RESET)\n", substr($$0, 4); next} \
		{printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# -----------------------------------------------------------------------------
## SETUP
# -----------------------------------------------------------------------------

.PHONY: install
install: ## Install dependencies with uv
	@echo "$(BLUE)Installing dependencies...$(RESET)"
	$(UV) sync --package $(PACKAGE)
	@echo "$(GREEN)Dependencies installed$(RESET)"

.PHONY: setup-chinook
setup-chinook: ## Download Chinook test database
	@echo "$(BLUE)Setting up Chinook database...$(RESET)"
	$(UV) run python scripts/setup_chinook_db.py
	@echo "$(GREEN)Chinook database ready$(RESET)"

.PHONY: setup-fakesnow
setup-fakesnow: ## Create FakeSnow TPC-H stub database
	@echo "$(BLUE)Setting up FakeSnow database...$(RESET)"
	$(UV) run python scripts/setup_fakesnow_db.py
	@echo "$(GREEN)FakeSnow database ready$(RESET)"

# -----------------------------------------------------------------------------
## DEVELOPMENT
# -----------------------------------------------------------------------------

.PHONY: dev
dev: ## Start LangGraph dev server with Studio UI
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-$(DEFAULT_PORT)}; \
	echo "$(BLUE)Starting dev server on port $$PORT...$(RESET)"; \
	$(UV) run langgraph dev --allow-blocking --port $$PORT

.PHONY: dev-server
dev-server: ## Start dev server without browser
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-$(DEFAULT_PORT)}; \
	echo "$(BLUE)Starting dev server (no browser) on port $$PORT...$(RESET)"; \
	$(UV) run langgraph dev --allow-blocking --port $$PORT --no-browser

# -----------------------------------------------------------------------------
## TESTING
# -----------------------------------------------------------------------------

.PHONY: test
test: ## Run all tests
	@echo "$(BLUE)Running tests...$(RESET)"
	$(UV) run pytest $(TEST_DIR)/ -v
	@echo "$(GREEN)Tests complete$(RESET)"

.PHONY: test-fast
test-fast: ## Run tests excluding slow tests
	@echo "$(BLUE)Running fast tests...$(RESET)"
	$(UV) run pytest $(TEST_DIR)/ -v -m "not slow"
	@echo "$(GREEN)Fast tests complete$(RESET)"

# -----------------------------------------------------------------------------
## QUALITY
# -----------------------------------------------------------------------------

.PHONY: format
format: ## Format code with ruff
	@echo "$(BLUE)Formatting code...$(RESET)"
	$(UV) run ruff format $(SRC_DIR)/ $(TEST_DIR)/
	@echo "$(GREEN)Formatting complete$(RESET)"

.PHONY: lint
lint: ## Lint code with ruff
	@echo "$(BLUE)Linting code...$(RESET)"
	$(UV) run ruff check $(SRC_DIR)/ $(TEST_DIR)/
	@echo "$(GREEN)Linting complete$(RESET)"

.PHONY: type-check
type-check: ## Type check with ty
	@echo "$(BLUE)Type checking...$(RESET)"
	$(UV) run ty check $(SRC_DIR)/
	@echo "$(GREEN)Type check complete$(RESET)"

.PHONY: check
check: format lint type-check test-fast ## Run format + lint + type-check + test-fast
	@echo "$(GREEN)All checks passed$(RESET)"

# -----------------------------------------------------------------------------
## MAINTENANCE
# -----------------------------------------------------------------------------

.PHONY: clean
clean: ## Remove caches and generated files
	@echo "$(BLUE)Cleaning caches...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete$(RESET)"
