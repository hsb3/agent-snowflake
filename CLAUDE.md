# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **monorepo** containing three independent applications under `apps/`:

| App | Directory | Description |
|-----|-----------|-------------|
| **agent** | `apps/agent/` | LangGraph SQL agent with database guardrails |
| **repl-client** | `apps/repl-client/` | Classic REPL client using traditional control flow |
| **repl-client-graph** | `apps/repl-client-graph/` | StateGraph-based REPL using LangGraph for control flow |

Each app can be used independently. REPL clients work with any LangGraph Dev Server, not just the agent in this repo.

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
│   │   ├── src/agent_snowflake/
│   │   ├── tests/
│   │   ├── scripts/
│   │   ├── docs/spec/
│   │   ├── pyproject.toml
│   │   ├── Makefile
│   │   └── CLAUDE.md          # Agent-specific guidance
│   │
│   ├── repl-client/           # Classic REPL (httpx + textual)
│   │   ├── .venv/             # Independent virtual environment
│   │   ├── src/repl_client/
│   │   ├── tests/
│   │   ├── scripts/
│   │   ├── docs/spec/
│   │   ├── pyproject.toml
│   │   ├── Makefile
│   │   └── CLAUDE.md          # REPL-specific guidance
│   │
│   └── repl-client-graph/     # StateGraph REPL (langgraph + httpx)
│       ├── .venv/             # Independent virtual environment
│       ├── src/repl_client_graph/
│       ├── tests/
│       ├── scripts/
│       ├── docs/spec/
│       ├── pyproject.toml
│       ├── Makefile
│       └── CLAUDE.md          # StateGraph REPL guidance
│
├── packages/                   # Shared code (if needed)
├── scripts/                    # Root-level utilities
├── docs/                       # Monorepo-wide documentation
│   └── dev_docs/ai_docs/ai_gen/  # AI work documentation
│
├── pyproject.toml             # Ruff/tool config (no workspace)
├── Makefile                   # Orchestration commands
└── CLAUDE.md                  # This file (monorepo overview)
```

## Essential Commands

### Monorepo-Level (from root)
```bash
make install              # Install all apps (creates separate .venv per app)
make test                 # Run all app tests
make dev                  # Start agent dev server
make dev-server           # Start server without browser
make clean                # Remove caches (preserves .venv)
make clean-venvs          # Remove all .venv directories
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
apps/repl-client/.venv/  # Has langgraph-sdk, textual, httpx
```

This separation is important because:
- The agent needs heavy server-side dependencies (`langgraph-cli[inmem]`)
- REPL clients only need the lightweight SDK (`langgraph-sdk`)
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
- REPL clients only need `LANGGRAPH_DEV_SERVER_URL` (defaults to `http://localhost:2024`)

## Working with Apps

### Agent (apps/agent/)
- Context-driven configuration with three-layer priority
- Graph variants: `agent`, `agent_enhanced`, `agent_minimal`
- See `apps/agent/CLAUDE.md` for architecture details

### REPL Client (apps/repl-client/)
- Traditional imperative control flow
- TUI built with Textual framework
- See `apps/repl-client/CLAUDE.md` for architecture details

### StateGraph REPL (apps/repl-client-graph/)
- Uses LangGraph StateGraph for control flow
- Benefits: visual debugging, automatic state propagation
- See `apps/repl-client-graph/CLAUDE.md` for architecture details

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

## Documentation

| Location | Content |
|----------|---------|
| `apps/*/CLAUDE.md` | App-specific guidance for AI coding |
| `apps/*/docs/spec/` | Specifications and research |
| `docs/dev_docs/ai_docs/ai_gen/` | AI-generated work documentation |

## Tooling

- **Package Manager**: `uv` (independent venvs per app)
- **Formatting/Linting**: `ruff`
- **Type Checking**: `ty`
- **Testing**: `pytest` with `pytest-asyncio`
- **TUI Framework**: `textual`
- **Agent Framework**: `langgraph` + `langchain`

## AI Coding Agent Plugins

This project uses Claude Code with:
- `work-documentation@hsb3-custom-plugins` - Controls .md documentation generation
- `ty@hsb3-custom-plugins` - Type checking integration
- `python-project-standards@hsb3-custom-plugins` - Project standards enforcement
- `docs-langchain` MCP server - LangChain documentation access

## Work Docs

Work documentation should be stored in `docs/dev_docs/ai_docs/ai_gen/`

**Frontmatter Template:**
```yaml
---
doc_id: CC-YYYY-NNN
title: Brief description
date: YYYY-MM-DD
type: planning|solution|investigation|status|summary
project: repl_client_graph|repl_client|agent_snowflake
focus: ...
status: draft|complete
tags: [stategraph, repl, ...]
---
```
