# =============================================================================
# REPL Client Makefile
# Classic REPL/TUI client for LangGraph Dev Server
#
# Prerequisites: A running LangGraph Dev Server
#   - From this monorepo: cd ../agent && make dev-server
#   - Or configure LANGGRAPH_DEV_SERVER_URL in .env
# =============================================================================

.DEFAULT_GOAL := help

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------
UV         := uv
SRC_DIR    := src
TEST_DIR   := tests
PACKAGE    := repl-client

# Color codes for output
GREEN      := \033[0;32m
YELLOW     := \033[0;33m
CYAN       := \033[0;36m
BOLD       := \033[1m
RESET      := \033[0m

# =============================================================================
# HELP
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "$(BOLD)REPL Client - Classic REPL/TUI for LangGraph Dev Server$(RESET)"
	@echo ""
	@echo "$(YELLOW)Prerequisites:$(RESET) A running LangGraph Dev Server"
	@echo "  - From this monorepo: cd ../agent && make dev-server"
	@echo "  - Or configure LANGGRAPH_DEV_SERVER_URL in .env"
	@echo ""
	@grep -E '^(## [A-Z]+|[a-zA-Z_-]+:.*?## .*)$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; \
		/^## / {printf "\n$(CYAN)%s$(RESET)\n", substr($$0, 4)} \
		!/^## / {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
## SETUP
# =============================================================================

.PHONY: install
install: ## Install dependencies with uv (creates local .venv)
	$(UV) sync --dev

# =============================================================================
## RUN
# =============================================================================

.PHONY: repl
repl: ## Start classic REPL interface
	$(UV) run python -m repl_client

.PHONY: tui
tui: ## Start TUI client
	@echo "$(CYAN)Starting TUI client...$(RESET)"
	@echo "$(YELLOW)Tip:$(RESET) Press Ctrl+P for commands, F4 for sidebar"
	$(UV) run python -m repl_client.tui

.PHONY: tui-dev
tui-dev: ## Start TUI with hot reload (dev mode)
	@echo "$(CYAN)Starting TUI in dev mode...$(RESET)"
	TEXTUAL_DEVTOOLS=1 $(UV) run python -m repl_client.tui

# =============================================================================
## TEST
# =============================================================================

.PHONY: test
test: ## Run all tests
	$(UV) run pytest $(TEST_DIR)/ -v

.PHONY: test-fast
test-fast: ## Run tests excluding slow/integration tests
	$(UV) run pytest $(TEST_DIR)/ -v -m "not integration"

.PHONY: test-core
test-core: ## Run core module tests only
	$(UV) run pytest $(TEST_DIR)/repl_client/core/ -v

.PHONY: test-tui
test-tui: ## Run TUI widget tests only
	$(UV) run pytest $(TEST_DIR)/repl_client/tui/ -v

# =============================================================================
## QUALITY
# =============================================================================

.PHONY: lint
lint: ## Lint code with ruff
	$(UV) run ruff check $(SRC_DIR)/ $(TEST_DIR)/

.PHONY: format
format: ## Format code with ruff
	$(UV) run ruff format $(SRC_DIR)/ $(TEST_DIR)/

.PHONY: type-check
type-check: ## Type check with ty
	$(UV) run ty check $(SRC_DIR)/

.PHONY: check
check: lint type-check test ## Run lint, type-check, and tests

# =============================================================================
## MAINTENANCE
# =============================================================================

.PHONY: build-css
build-css: ## Build concatenated CSS from modular files
	@cd $(SRC_DIR)/repl_client/tui/styles && \
	cat theme.tcss layout.tcss components.tcss sidebar.tcss modals.tcss states.tcss light-mode.tcss > index.tcss
	@echo "$(GREEN)Built index.tcss from modular CSS files$(RESET)"

.PHONY: clean
clean: ## Remove caches and generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cleaned caches$(RESET)"
