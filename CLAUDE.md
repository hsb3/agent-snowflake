# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **monorepo** containing two independent applications under `apps/`:

| App | Directory | Description |
|-----|-----------|-------------|
| **agent** | `apps/agent/` | LangGraph SQL agent with database guardrails |
| **repl-client** | `apps/repl-client/` | Terminal client (REPL + TUI) for LangGraph Dev Server |

Each app can be used independently. The REPL client works with any LangGraph Dev Server, not just the agent in this repo.

## Quick Start

### Full Monorepo
```bash
make install              # Install all apps (creates separate .venv per app)
make dev                  # Start agent dev server with Studio UI
# In another terminal:
cd apps/repl-client && make tui    # Start TUI client
```

### Individual App
```bash
cd apps/agent
make install              # Install this app only (creates apps/agent/.venv)
make setup-chinook        # Download test database
make dev                  # Start dev server
```

## Monorepo Structure

```
agent-snowflake/
├── apps/
│   ├── agent/                 # SQL agent (langgraph + langchain)
│   │   ├── .venv/             # Independent virtual environment
│   │   ├── src/agent/
│   │   ├── tests/
│   │   ├── docs/spec/
│   │   ├── pyproject.toml
│   │   ├── Makefile
│   │   └── CLAUDE.md          # Agent-specific guidance
│   │
│   └── repl-client/           # Terminal client (langgraph-sdk + textual)
│       ├── .venv/             # Independent virtual environment
│       ├── src/repl_client/
│       ├── tests/
│       ├── docs/spec/
│       ├── pyproject.toml
│       ├── Makefile
│       └── CLAUDE.md          # REPL-specific guidance
│
├── Makefile                   # Orchestration commands
└── CLAUDE.md                  # This file (monorepo overview)
```

## Essential Commands

### Monorepo-Level (from root)
```bash
make install              # Install all apps (creates separate .venv per app)
make test                 # Run all app tests
make format               # Format all code
make lint                 # Lint all code
make type-check           # Type check all code
make check                # Run format + lint + type-check
make clean                # Remove caches (preserves .venv)
make clean-venvs          # Remove all .venv directories
```

### Starting the Dev Server
```bash
cd apps/agent && make dev         # With Studio UI
cd apps/agent && make dev-server  # Without browser
```

### Per-App Commands
Each app has its own Makefile. Navigate to the app directory and run `make help`:
```bash
cd apps/agent && make help
cd apps/repl-client && make help
```

## Dependencies & Virtual Environments

Each app has its **own independent virtual environment** to avoid dependency conflicts:

```
apps/agent/.venv/        # Has langgraph-cli, langchain, etc.
apps/repl-client/.venv/  # Has langgraph-sdk, textual
```

This separation is important because:
- The agent needs heavy server-side dependencies (`langgraph-cli[inmem]`)
- The REPL client only needs the lightweight SDK (`langgraph-sdk`)
- Mixing these in one venv causes version conflicts

### Installing Dependencies
```bash
# From root - install all apps
make install

# Or install individual apps
cd apps/agent && make install
cd apps/repl-client && make install
```

Each app declares only the dependencies it needs in its own `pyproject.toml`.

## Environment Configuration

- Root `.env` is used by `langgraph dev` for the agent server
- Each app has `.env.example` with app-specific variables
- REPL client needs `LANGGRAPH_DEV_SERVER_URL` (defaults to `http://localhost:2024`)

## Working with Apps

### Agent (apps/agent/)
- Context-driven configuration with three-layer priority
- Single graph with configurable middleware (enabled/disabled via context flags)
- See `apps/agent/CLAUDE.md` for architecture details

### REPL Client (apps/repl-client/)
- TUI built with Textual framework, plus a classic REPL mode
- Uses official `langgraph-sdk` for all server communication
- See `apps/repl-client/CLAUDE.md` for architecture details

## Testing

```bash
# All tests (from root)
make test

# Single app (from app directory)
cd apps/agent && make test
cd apps/repl-client && make test

# Specific test (from app directory)
cd apps/agent && uv run pytest tests/test_agent.py::test_name -v
```

Integration tests require a running server and are marked with `@pytest.mark.integration`.

## Tooling

- **Package Manager**: `uv` (independent venvs per app)
- **Formatting/Linting**: `ruff`
- **Type Checking**: `ty`
- **Testing**: `pytest` with `pytest-asyncio`
- **TUI Framework**: `textual`
- **Agent Framework**: `langgraph` + `langchain`
