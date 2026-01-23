# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LangGraph agent for Snowflake database interactions using LangChain v1. The agent uses SQL toolkit to explore schemas and execute queries with configurable guardrails.

## Build & Development Commands

```bash
make install        # Install dependencies with uv
make setup-test-db  # Create SQLite test database with TPC-H sample data
make dev            # Start LangGraph dev server (uses --allow-blocking for SQLite)
make test           # Run all tests
make test-fast      # Run tests excluding slow tests
make format         # Format with ruff
make lint           # Lint with ruff
make type-check     # Type check with ty
```

**Run single test:**
```bash
uv run pytest tests/test_tools.py::test_create_engine_from_uri -v
```

**Run graph locally:**
```bash
uv run python -c "from agent_snowflake import graph; g = graph(); result = g.invoke({'messages': [...]})"
```

## Architecture

### Three-Layer Configuration System

The project uses a layered configuration approach:

**Layer 1: config.py (Base Settings)**
- `Settings` dataclass with `from_env()` method
- Loads from `SNOWFLAKE_AGENT_*` environment variables
- Provides defaults for all configuration
- Module-level `settings` instance

**Layer 2: Context Schemas (Runtime Context)**
- **context.py**: `ContextSchema` - Base configuration (used by graph.py)
  - Model configuration, Snowflake connection, guardrails, execution settings
- **context2.py**: `EnhancedContextSchema` - Extends base with middleware config (used by graph2.py)
  - All base fields plus middleware: HITL, call limits, retry, summarization, todo, fallback
  - See `docs/ENHANCED_CONTEXT.md` for complete reference
- Both schemas support:
  - `from_env()` - Loads from environment (deployment-time)
  - `from_runnable_config()` - Loads from LangGraph runtime (Studio UI)
- All fields exposed in LangGraph Studio for assistant configuration
- Uses `Annotated[str, {"__template_metadata__": {"kind": "llm"}}]` for LLM selector dropdown
- Uses `field(metadata={"description": "...", "json_schema_extra": {...}})` for Studio UI

**Layer 3: Runtime Values**
- Actual values passed via `graph.invoke(..., context={...})`
- Or configured in Studio UI when creating assistants
- Priority: Runtime context → Environment → Defaults

### Graph Variants

The project provides three graph variants with different middleware configurations:

**langgraph.json** defines:
```json
{
  "graphs": {
    "agent": "src.agent_snowflake:graph",
    "agent_enhanced": "src.agent_snowflake:graph_enhanced",
    "agent_minimal": "src.agent_snowflake:graph_minimal"
  }
}
```

1. **agent** (graph.py) - Basic agent, no middleware
   - Uses `ContextSchema`
   - Zero middleware overhead
   - Best for: Learning, debugging, simple use cases

2. **agent_enhanced** (graph2.py) - Production-ready with full middleware stack
   - Uses `EnhancedContextSchema`
   - 7 middleware components: HITL, call limits, retry, summarization, todo, fallback
   - Best for: Production deployments, real Snowflake, complex analysis

3. **agent_minimal** (graph2.py) - Development-friendly minimal middleware
   - Uses `EnhancedContextSchema`
   - 2 middleware components: call limits, retry
   - Best for: Fast iteration, local testing

All graph builders are **functions** (not instances) that return `CompiledStateGraph`. LangGraph calls them automatically.

See `docs/MIDDLEWARE.md` for middleware details and `docs/ENHANCED_CONTEXT.md` for configuration.

### Prompt System

Modular prompt composition in `src/agent_snowflake/prompts/`:
- `core.py` - Base instructions
- `db_specific.py` - SQLite vs Snowflake SQL guidance
- `special.py` - Placeholder for custom instructions
- `builder.py` - Composes prompts together

`build_system_prompt(db_type="sqlite")` combines components. Currently hardcoded to SQLite mode.

**To switch to Snowflake:** Change in `prompts/builder.py`:
```python
system_prompt = build_system_prompt(db_type="snowflake")
```

### Tools Architecture

Uses LangChain's pre-built `SQLDatabaseToolkit` from `langchain_community`:
- `sql_db_query` - Execute SELECT queries
- `sql_db_schema` - Get table schema
- `sql_db_list_tables` - List tables
- `sql_db_query_checker` - Validate SQL

**Tool creation flow:**
1. `graph.py:build_graph()` loads context
2. Calls `utils.create_snowflake_engine()` - Creates SQLAlchemy engine
3. Calls `utils.create_sql_database()` - Wraps engine with guardrails
4. Calls `tools/sql.py:create_sql_tools()` - Creates toolkit with guardrails applied

**Guardrails from context:**
- `allowed_schemas` - Schema restrictions (applied to SQLDatabase)
- `allowed_tables` - Table restrictions (applied to SQLDatabase)
- `read_only` - Enforced via tool descriptions
- `query_timeout` - Applied to engine (Snowflake only, not SQLite)

### State Management

Uses default LangChain v1 `AgentState` (not custom state):
- `messages: list[AnyMessage]` - Conversation history
- `jump_to` (optional) - For conditional routing
- `structured_response` (optional) - For typed outputs

`src/agent_snowflake/state.py` is a placeholder for future custom state fields.

## Testing Strategy

**SQLite for local development:**

Option 1: Chinook Database (recommended for testing)
- Use `make setup-chinook` to download realistic music store database
- 11 tables, 3,500+ tracks, sales data, customers, playlists
- ~900 KB database with real relationships
- See `docs/CHINOOK_QUERIES.md` for 100+ example queries

Option 2: Minimal stub data
- Use `make setup-test-db` to create `test_snowflake.db` with minimal TPC-H data
- 3 tables (REGION, CUSTOMER, ORDERS) with handful of rows

Both options:
- Set `SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///...` in `.env`
- Limitations: No VARIANT, FLATTEN(), QUALIFY, or Snowflake-specific functions
- See `docs/SQL_COMPATIBILITY.md` for SQL syntax differences

**Tests use pytest fixtures:**
- `conftest.py` - Reusable fixtures (fakesnow_connection, sample_database, etc.)
- Tests run against SQLite, no Snowflake needed
- 32 passing tests

## SQLite Blocking Issue

SQLite uses file I/O which is blocking. Must run dev server with:
```bash
uv run langgraph dev --allow-blocking
```

Or use `make dev` (already configured). Production Snowflake connections are network-based and don't need this flag.

## Environment Variables

All configuration uses `SNOWFLAKE_AGENT_*` prefix:
- `SNOWFLAKE_AGENT_MODEL` - LLM model
- `SNOWFLAKE_AGENT_SNOWFLAKE_URI` - Database connection URI
- `SNOWFLAKE_AGENT_ALLOWED_SCHEMAS` - Schema restrictions (comma-separated or *)
- `SNOWFLAKE_AGENT_ALLOWED_TABLES` - Table restrictions (comma-separated or *)
- `SNOWFLAKE_AGENT_READ_ONLY` - Enforce read-only (true/false)
- `SNOWFLAKE_AGENT_ENVIRONMENT` - Environment (development/staging/production)

Set in `.env` file. Loaded via `Settings.from_env()` in `config.py`.

## Key Files

### Graph Builders

**graph.py** - `build_graph(config)` function (basic agent):
1. Loads context via `ContextSchema.from_runnable_config()`
2. Initializes LLM via `utils.init_model()`
3. Creates SQL tools via `tools.create_sql_tools()`
4. Returns `create_agent(model, tools, system_prompt, context_schema)`

**graph2.py** - Enhanced graph builders with middleware:
- `build_graph_with_middleware(config)` - Full middleware stack (agent_enhanced)
  - Dynamically configures 7 middleware components based on `EnhancedContextSchema`
  - Human-in-the-loop, call limits, retry, summarization, todo, fallback
- `build_graph_minimal_middleware(config)` - Minimal middleware (agent_minimal)
  - Only essential middleware: call limits, retry

### Configuration

**config.py** - Base settings with `Settings` dataclass

**context.py** - `ContextSchema` for basic agent (graph.py)

**context2.py** - `EnhancedContextSchema` for middleware-enabled agents (graph2.py)
- Extends base schema with 20+ middleware configuration fields
- `get_middleware_config()` helper to extract middleware fields
- Full Studio UI integration with metadata

### Utilities and Tools

**utils.py** - Helper functions:
- `init_model()` - Wrapper around `init_chat_model()` for special cases
- `create_snowflake_engine()` - Creates SQLAlchemy engine (handles URI or parameters)
- `create_sql_database()` - Creates SQLDatabase with guardrails

**tools/sql.py** - SQL toolkit wrapper:
- `create_sql_tools()` - Creates LangChain SQLDatabaseToolkit with context guardrails

## Important: Don't Use Snowflake SQL Commands Directly

The agent has tools and should use them instead of raw Snowflake commands:
- ❌ `SHOW TABLES` - Use `sql_db_list_tables` tool
- ❌ `DESCRIBE TABLE` - Use `sql_db_schema` tool
- ✅ `SELECT ...` - Use `sql_db_query` tool with SELECT statements

This is configured in `prompts/db_specific.py` based on `db_type` ("sqlite" or "snowflake").
