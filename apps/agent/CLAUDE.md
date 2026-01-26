# CLAUDE.md - Agent Snowflake

This file provides guidance to Claude Code when working with the `agent_snowflake` module.

## Overview

Agent Snowflake is a LangGraph SQL agent for database interactions with built-in guardrails. It provides intelligent natural language access to Snowflake databases (and SQLite for testing) with configurable security constraints including read-only mode, schema/table restrictions, and query timeouts.

## Architecture

### Entry Points

Three graph variants are defined in `langgraph.json` and exported from `__init__.py`:

| Entry Point | Function | Description |
|-------------|----------|-------------|
| `agent` | `graph.py:build_graph` | Core SQL agent with context-driven configuration |
| `agent_enhanced` | `graph2.py:build_graph_with_middleware` | Full-featured variant with configurable middleware (HITL, retry, summarization, etc.) |
| `agent_minimal` | `graph2.py:build_graph_minimal_middleware` | Minimal variant with only essential middleware (model limits, retry) |

### Context-Driven Configuration

The agent uses a three-layer configuration priority system:

1. **Runtime context** (highest) - Passed via `graph.invoke(..., context={...})`
2. **Environment variables** - Loaded from `.env` with `SNOWFLAKE_AGENT_` prefix
3. **Defaults** (lowest) - Hardcoded in `config.py`

**Key files:**
- `context.py` - `ContextSchema` dataclass for runtime configuration
- `context2.py` - `EnhancedContextSchema` with additional middleware controls
- `config.py` - `Settings` class with defaults and environment loading

The `ContextSchema` uses `Annotated` metadata for LangGraph Studio UI enhancements:
- `{"__template_metadata__": {"kind": "llm"}}` - Shows LLM selector dropdown
- `metadata={"description": "..."}` - Tooltips in Studio UI

### Graph Building

`build_graph(config: RunnableConfig)` is the entry point called by LangGraph:

1. Loads context from `RunnableConfig` via `ContextSchema.from_runnable_config()`
2. Initializes LLM via `utils.init_model()`
3. Creates SQL tools with guardrails via `tools.create_sql_tools()`
4. Builds agent using `langchain.agents.create_agent()`

### Tools and Guardrails

SQL tools are created via `tools/sql.py:create_sql_tools()`:

**Available tools** (from LangChain's `SQLDatabaseToolkit`):
- `sql_db_query` - Execute SELECT queries
- `sql_db_schema` - Get schema info for tables
- `sql_db_list_tables` - List available tables
- `sql_db_query_checker` - Validate SQL queries

**Guardrails** (applied from context):
- `read_only` - Enforces read-only access (adds restrictions to tool descriptions)
- `allowed_schemas` - Limits accessible schemas
- `allowed_tables` - Limits accessible tables
- `query_timeout` - Query execution timeout

### Middleware (Enhanced Variants)

The `agent_enhanced` variant supports configurable middleware:

| Middleware | Purpose |
|------------|---------|
| `HumanInTheLoopMiddleware` | Require approval for write operations |
| `ModelCallLimitMiddleware` | Prevent runaway costs |
| `ToolCallLimitMiddleware` | Limit expensive SQL queries |
| `ModelRetryMiddleware` | Handle transient network failures |
| `SummarizationMiddleware` | Compress conversation history |
| `TodoListMiddleware` | Task planning for complex analysis |
| `ModelFallbackMiddleware` | Fallback to alternative models |

## Essential Commands

```bash
# Setup
make install          # Install dependencies with uv
make setup-chinook    # Download Chinook test database

# Development
make dev              # Start LangGraph dev server with Studio UI
make dev-server       # Start server without browser

# Quality
make test             # Run tests with pytest
make lint             # Lint with ruff
make format           # Format with ruff
make type-check       # Type check with ty

# Cleanup
make clean            # Remove caches
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

### Required

```bash
# At least one API key
ANTHROPIC_API_KEY=your_key
# OPENAI_API_KEY=your_key
# GOOGLE_API_KEY=your_key

# Database connection (choose one option)
# Option 1: SQLite for local testing
SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:////absolute/path/to/test_chinook.db

# Option 2: Snowflake URI
# SNOWFLAKE_AGENT_SNOWFLAKE_URI=snowflake://user:password@account/database/schema?warehouse=wh&role=role

# Option 3: Individual Snowflake parameters
# SNOWFLAKE_AGENT_SNOWFLAKE_ACCOUNT=your_account
# SNOWFLAKE_AGENT_SNOWFLAKE_USER=your_user
# SNOWFLAKE_AGENT_SNOWFLAKE_PASSWORD=your_password
# SNOWFLAKE_AGENT_SNOWFLAKE_DATABASE=your_database
# SNOWFLAKE_AGENT_SNOWFLAKE_SCHEMA=your_schema
# SNOWFLAKE_AGENT_SNOWFLAKE_WAREHOUSE=your_warehouse
# SNOWFLAKE_AGENT_SNOWFLAKE_ROLE=your_role
```

### Agent Configuration

```bash
SNOWFLAKE_AGENT_MODEL=claude-sonnet-4-5-20250929
SNOWFLAKE_AGENT_TEMPERATURE=0.0
SNOWFLAKE_AGENT_MAX_ITERATIONS=25
SNOWFLAKE_AGENT_ENABLE_DEBUG=false
```

### Guardrails

```bash
SNOWFLAKE_AGENT_ALLOWED_SCHEMAS=*     # Comma-separated or * for all
SNOWFLAKE_AGENT_ALLOWED_TABLES=*      # Comma-separated or * for all
SNOWFLAKE_AGENT_READ_ONLY=true        # Enforce read-only access
SNOWFLAKE_AGENT_QUERY_TIMEOUT=30      # Timeout in seconds
```

### Development

```bash
LANGGRAPH_DEV_SERVER_PORT=2024
```

## Module Structure

```
src/agent_snowflake/
├── __init__.py          # Exports: graph, graph_enhanced, graph_minimal, ContextSchema
├── graph.py             # Core agent builder (build_graph)
├── graph2.py            # Enhanced variants with middleware
├── context.py           # ContextSchema - runtime configuration
├── context2.py          # EnhancedContextSchema - middleware configuration
├── config.py            # Settings - defaults and env loading
├── utils.py             # init_model(), create_sql_database(), create_snowflake_engine()
├── state.py             # AgentState (optional customization)
├── models.py            # Model-related utilities
├── prompts/
│   ├── __init__.py      # Exports: system_prompt, build_system_prompt
│   ├── builder.py       # Prompt composition
│   ├── core.py          # Core prompt templates
│   ├── special.py       # Special-case prompts
│   └── db_specific.py   # Database-specific prompts
└── tools/
    ├── __init__.py      # Exports: create_sql_tools
    └── sql.py           # SQL toolkit with guardrails
```

## Testing Strategy

Tests are located in `tests/` and organized by focus:

- `test_agent.py` - Graph building and compilation tests
- `test_tools.py` - SQL tool creation and guardrails
- `test_graph_with_tools.py` - Integration tests with mock databases

**Key patterns:**
- Use `mock_sqlite_db` fixture for testing without real database
- Mock `create_sql_database` when testing graph building
- Mark tests requiring external services with `@pytest.mark.skip`
- Tests requiring API keys should be skipped by default

**Running tests:**
```bash
make test                                    # All tests
uv run pytest tests/test_agent.py -v         # Specific file
uv run pytest tests/test_agent.py::test_name -v  # Specific test
```

## Key Patterns

**Configuration loading:**
```python
# Context loads with fallback to environment
context = ContextSchema.from_runnable_config(config, fallback_env=True)
```

**Tool creation with guardrails:**
```python
# Tools respect read_only, allowed_tables, allowed_schemas from context
tools = create_sql_tools(llm=llm, context=context)
```

**Graph invocation:**
```python
result = graph.invoke(
    {"messages": [{"role": "user", "content": "List tables"}]},
    context={"read_only": True, "allowed_schemas": "PUBLIC"}
)
```

## LangGraph Dev Server

- Start with `make dev` (opens Studio UI) or `make dev-server` (no browser)
- Uses `--allow-blocking` flag for SQLite file operations
- API docs at `http://localhost:2024/docs`
- Studio UI at `http://localhost:2024`
