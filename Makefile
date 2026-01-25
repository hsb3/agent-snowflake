# Agent Snowflake Monorepo
# Orchestration commands for multi-app repository
#
# For app-specific commands, use:
#   cd apps/agent && make help
#   cd apps/repl-client && make help

.DEFAULT_GOAL := help

APPS := apps/agent apps/repl-client

# Colors
GREEN := \033[32m
YELLOW := \033[33m
CYAN := \033[36m
RESET := \033[0m

.PHONY: help install test format lint type-check check clean clean-venvs

help:
	@echo ""
	@echo "Monorepo orchestration commands:"
	@echo ""
	@echo "  $(CYAN)install$(RESET)      Install all apps (creates .venv per app)"
	@echo "  $(CYAN)test$(RESET)         Run tests for all apps"
	@echo "  $(CYAN)format$(RESET)       Format code in all apps"
	@echo "  $(CYAN)lint$(RESET)         Lint code in all apps"
	@echo "  $(CYAN)type-check$(RESET)   Type check all apps"
	@echo "  $(CYAN)check$(RESET)        Run format + lint + type-check"
	@echo "  $(CYAN)clean$(RESET)        Remove caches (preserves .venv)"
	@echo "  $(CYAN)clean-venvs$(RESET)  Remove all .venv directories"
	@echo ""
	@echo "App-specific commands:"
	@echo "  cd apps/agent && make help"
	@echo "  cd apps/repl-client && make help"
	@echo ""

install:
	@for app in $(APPS); do \
		echo "$(GREEN)Installing $$app...$(RESET)"; \
		(cd $$app && make install); \
	done
	@echo "$(GREEN)All apps installed.$(RESET)"

test:
	@for app in $(APPS); do \
		echo "$(YELLOW)Testing $$app...$(RESET)"; \
		(cd $$app && make test); \
	done
	@echo "$(GREEN)All tests complete.$(RESET)"

format:
	@for app in $(APPS); do \
		echo "$(YELLOW)Formatting $$app...$(RESET)"; \
		(cd $$app && make format); \
	done
	@echo "$(GREEN)Formatting complete.$(RESET)"

lint:
	@for app in $(APPS); do \
		echo "$(YELLOW)Linting $$app...$(RESET)"; \
		(cd $$app && make lint); \
	done
	@echo "$(GREEN)Linting complete.$(RESET)"

type-check:
	@for app in $(APPS); do \
		echo "$(YELLOW)Type checking $$app...$(RESET)"; \
		(cd $$app && make type-check); \
	done
	@echo "$(GREEN)Type check complete.$(RESET)"

check: format lint type-check
	@echo "$(GREEN)All checks passed.$(RESET)"

clean:
	@echo "$(YELLOW)Cleaning caches...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Clean complete.$(RESET)"

clean-venvs:
	@echo "$(YELLOW)Removing all .venv directories...$(RESET)"
	rm -rf apps/agent/.venv apps/repl-client/.venv apps/repl-client-graph/.venv
	@echo "$(GREEN)All venvs removed.$(RESET)"
