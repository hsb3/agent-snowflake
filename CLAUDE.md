# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository contains three development efforts under `src/`:

1. **agent_snowflake**: LangGraph agents for database interactions (SQL agents with guardrails)
2. **repl_client**: Classic REPL client using LangGraph Dev Server REST API
3. **repl_client_graph**: Experimental REPL implementation using LangGraph StateGraph for control flow

Both REPL clients are designed to work with any LangGraph Dev Server (not just `agent_snowflake`), though custom config/context schemas may require modifications.

## Essential Commands

### Setup & Installation
```bash
make install              # Install dependencies with uv sync
make setup-chinook        # Download Chinook test database (recommended)
make setup-fakesnow       # Create stub TPC-H test database
```

### Development Server
```bash
make dev                  # Start LangGraph dev server + Studio UI (browser opens)
make dev-server           # Start server without browser (for REPL clients)
```

### REPL Clients
```bash
# Standalone TUI (server must be running separately)
make tui                  # Start TUI only
make tui-dev              # Start TUI in dev mode with hot reload

# Combined (server + client)
make repl                 # Start server + classic REPL together
make repl-tui             # Start server + TUI client together
make repl-graph           # Start server + StateGraph REPL together
```

### Testing
```bash
make test                 # Run all tests with pytest
make test-fast            # Skip slow tests (excludes 'emulator' tests)
uv run pytest tests/repl_client -v              # Test specific module
uv run pytest tests/test_agent.py::test_name -v # Test specific function
```

### Code Quality
```bash
make format              # Format with ruff
make lint                # Lint with ruff
make type-check          # Type check with ty
make check-repl          # Run lint + type-check + test on repl_client only
```

### Utilities
```bash
make visualize-graph     # Generate StateGraph visualization
make clean               # Remove caches, generated files (preserves .env)
```

## Architecture & Key Concepts

### LangGraph Agent (agent_snowflake)

**Entry Points** (defined in `langgraph.json`):
- `agent`: Core SQL agent (`src.agent_snowflake:graph`)
- `agent_enhanced`: Full-featured variant (`src.agent_snowflake:graph_enhanced`)
- `agent_minimal`: Minimal variant with guardrails (`src.agent_snowflake:graph_minimal`)

**Context-Driven Configuration** (`context.py`):
- Uses LangGraph's `ContextSchema` pattern for per-invocation configuration
- Three-layer priority: Runtime context → Environment variables → Defaults
- Context is read-only and NOT persisted between invocations
- Fields are exposed in LangGraph Studio UI and Dev Server API
- The schema uses `Annotated` metadata for Studio UI enhancements (LLM dropdowns, tooltips)

**Graph Building** (`graph.py`):
- `build_graph(config: RunnableConfig)` is the entry point called by LangGraph
- Loads context from `RunnableConfig`, initializes LLM, creates tools with guardrails
- Uses `create_agent()` from langchain to build the graph
- Tools are created via `create_sql_tools()` which applies context-based guardrails

**Configuration Priority**:
1. Runtime context (highest) - passed via `graph.invoke(..., context={...})`
2. Environment variables - loaded from `.env`
3. Defaults - hardcoded in `ContextSchema`

### REPL Clients

**Classic REPL** (`repl_client`):
- Traditional imperative control flow
- Core components in `core/`: `client.py`, `session.py`, `parsers.py`
- Streaming handled in `streaming/`
- Commands in `commands/`
- TUI widgets in `tui/widgets/`

**StateGraph REPL** (`repl_client_graph`):
- Implements REPL as LangGraph StateGraph for structured state management
- Graph definition: `graph/builder.py` and `graph/builder_subgraph.py`
- State schema: `graph/state.py` - single TypedDict with all REPL state
- Nodes: `graph/nodes/` - each major operation is a node (get_input, route_input, send_message, process_stream, handle_interrupt, etc.)
- Subgraphs: `graph/subgraphs/` - modular streaming logic
- Benefits: automatic state propagation, visual debugging, checkpointing, built-in HITL interrupts

**Shared Pattern**: Both REPLs interact with LangGraph Dev Server via REST API, handle streaming SSE responses, support slash commands, and manage conversation threads.

## Environment Configuration

Copy `.env.example` to `.env` and configure:

**Required**:
- `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`, `GOOGLE_API_KEY`)
- `SNOWFLAKE_AGENT_SNOWFLAKE_URI` - Database connection (SQLite for testing, Snowflake for production)

**Optional Agent Settings**:
- `SNOWFLAKE_AGENT_MODEL` - LLM model (default: claude-sonnet-4-5-20250929)
- `SNOWFLAKE_AGENT_READ_ONLY` - Prevent write operations (default: true)
- `SNOWFLAKE_AGENT_ALLOWED_SCHEMAS`, `SNOWFLAKE_AGENT_ALLOWED_TABLES` - Schema/table access control
- `SNOWFLAKE_AGENT_QUERY_TIMEOUT` - Query timeout in seconds
- `LANGGRAPH_DEV_SERVER_PORT` - Dev server port (default: 2024)

**Testing with SQLite**:
```bash
SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:////absolute/path/to/test_chinook.db
```

## Project Structure Patterns

**Agent Module** (`src/agent_snowflake/`):
- `graph.py`, `graph2.py` - Graph builders (different variants)
- `context.py`, `context2.py` - Context schemas (v1 and v2 approaches)
- `config.py` - Settings loaded from environment via `pydantic-settings`
- `tools/` - SQL toolkit and guardrails
- `prompts/` - System prompts
- `utils.py` - Model initialization helpers

**REPL Modules** (`src/repl_client/`, `src/repl_client_graph/`):
- Follow similar patterns but implement different control flow strategies
- Both have `core/` (shared logic), `commands/` (slash commands), `streaming/` (SSE handling)
- StateGraph variant adds `graph/` directory with nodes/subgraphs

## Testing Strategy

- Integration tests marked with `@pytest.mark.integration` (require running server)
- Use `pytest.mark.skip` when tests require external services
- `conftest.py` provides shared fixtures
- Tests organized by module: `tests/repl_client/`, `tests/repl_client_graph/`, root-level for agents

## LangGraph Dev Server

- Server starts with `langgraph dev` (uses `langgraph.json` config)
- Requires `--allow-blocking` flag for SQLite file operations
- API docs available at `http://localhost:2024/docs`
- Studio UI at `http://localhost:2024`
- Use `--tunnel` flag for Safari viewing

## Documentation

- `docs/dev_docs/spec-agent/` - Agent specifications and research
- `docs/dev_docs/spec-repl/` - Classic REPL specifications
- `docs/dev_docs/spec-repl-graph/` - StateGraph REPL specifications
- `docs/dev_docs/ai_docs/ai_gen/` - AI-generated work documentation

## Dependencies & Tooling

- **Package Manager**: `uv` (all commands use `uv run` or `uv sync`)
- **Virtual Environment**: `.venv` (automatically managed by uv)
- **Formatting/Linting**: `ruff` (configured in `pyproject.toml`)
- **Type Checking**: `ty` (configured in `pyproject.toml`)
- **Testing**: `pytest` with `pytest-asyncio` (asyncio_mode = "auto")
- **TUI Framework**: `textual` (for REPL interfaces)
- **Agent Framework**: `langgraph` + `langchain`

## Working with the Codebase

**When modifying agents**:
- Changes to context schema require understanding the three-layer priority system
- Tool modifications should respect guardrails from context (read_only, allowed_tables, etc.)
- Graph variants share tooling but differ in middleware/prompts

**When modifying REPLs**:
- Classic REPL: imperative control flow in `__main__.py`
- StateGraph REPL: modify graph nodes/edges in `builder.py`, state in `state.py`
- Both share similar streaming/command patterns

**Running a single test**:
```bash
uv run pytest tests/test_agent.py::test_function_name -v -s
```

**Checking server logs** (when using `make repl` or `make repl-graph`):
```bash
tail -f .repl/server.log
```

## AI Coding Agent Plugins

This project uses Claude Code with:
- `work-documentation@hsb3-custom-plugins` - Controls .md documentation generation
- `ty@hsb3-custom-plugins` - Type checking integration
- `python-project-standards@hsb3-custom-plugins` - Project standards enforcement
- `docs-langchain` MCP server - LangChain documentation access
- Permissions configured in `.claude/settings.local.json`


## Work Docs

work documentation should be stored in docs/dev_docs/ai_gen/

**Work Doc Frontmatter Template:**
```yaml
---
doc_id:CC-YYYY-NNN
title: Brief description
date: YYYY-MM-DD
type: planning|solution|investigation|status|summary
project: repl_client_graph|repl_client|agent_snowflake
focus: ...
status: draft|complete
tags: [stategraph, repl, ...]
---
```