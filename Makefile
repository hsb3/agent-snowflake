# Agent Snowflake Monorepo
#
# For app-specific commands:
#   cd apps/agent && make help
#   cd apps/repl-client && make help

.DEFAULT_GOAL := help

APPS := apps/agent apps/repl-client

GREEN  := \033[32m
YELLOW := \033[33m
CYAN   := \033[36m
RESET  := \033[0m

.PHONY: help install dev test format lint type-check check clean clean-venvs

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "App-specific commands:"
	@echo "  cd apps/agent && make help"
	@echo "  cd apps/repl-client && make help"

install: ## Install all apps (creates .venv per app)
	@for app in $(APPS); do \
		echo "$(GREEN)Installing $$app...$(RESET)"; \
		(cd $$app && make install); \
	done
	@echo "$(GREEN)All apps installed.$(RESET)"

dev: ## Start agent dev server with Studio UI
	cd apps/agent && make dev

test: ## Run tests for all apps
	@for app in $(APPS); do \
		echo "$(YELLOW)Testing $$app...$(RESET)"; \
		(cd $$app && make test); \
	done
	@echo "$(GREEN)All tests complete.$(RESET)"

format: ## Format code in all apps
	@for app in $(APPS); do \
		echo "$(YELLOW)Formatting $$app...$(RESET)"; \
		(cd $$app && make format); \
	done

lint: ## Lint code in all apps
	@for app in $(APPS); do \
		echo "$(YELLOW)Linting $$app...$(RESET)"; \
		(cd $$app && make lint); \
	done

type-check: ## Type check all apps
	@for app in $(APPS); do \
		echo "$(YELLOW)Type checking $$app...$(RESET)"; \
		(cd $$app && make type-check); \
	done

check: format lint type-check ## Run format + lint + type-check
	@echo "$(GREEN)All checks passed.$(RESET)"

clean: ## Remove caches (preserves .venv)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

clean-venvs: ## Remove all .venv directories
	rm -rf apps/agent/.venv apps/repl-client/.venv
	@echo "$(GREEN)All venvs removed.$(RESET)"
