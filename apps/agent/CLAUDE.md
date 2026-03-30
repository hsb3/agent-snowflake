# CLAUDE.md - SQL Agent

This file provides guidance to Claude Code when working with the `agent` module.

## Overview

A LangGraph SQL agent for database interactions with built-in guardrails. Provides intelligent natural language access to databases (Snowflake, SQLite, with more planned) with configurable security constraints and optional middleware.

## Architecture

### Entry Point

Single graph defined in `langgraph.json`:

```json
{"graphs": {"agent": "agent:graph"}}
```

`graph.py:build_graph()` is the sole entry point. Middleware is conditionally assembled based on `ContextSchema` configuration flags — no separate "enhanced" or "minimal" variants needed.

### Context-Driven Configuration

The agent uses a three-layer configuration priority system:

1. **Runtime context** (highest) - Passed via `graph.invoke(..., context={...})`
2. **Environment variables** - Loaded from `.env` with `AGENT_` prefix
3. **Defaults** (lowest) - Hardcoded in `config.py` and `context.py`

**Key files:**
- `context.py` - `ContextSchema` dataclass (core settings + middleware config)
- `config.py` - `Settings` class with defaults and environment loading

The `ContextSchema` uses `Annotated` metadata for LangGraph Studio UI enhancements:
- `{"__template_metadata__": {"kind": "llm"}}` - Shows LLM selector dropdown
- `metadata={"description": "..."}` - Tooltips in Studio UI

### Graph Building

`build_graph(config: RunnableConfig)` is the entry point called by LangGraph:

1. Loads context from `RunnableConfig` via `ContextSchema.from_runnable_config()`
2. Initializes LLM via `utils.init_model()`
3. Creates SQL tools with guardrails via `tools.create_sql_tools()`
4. Conditionally assembles middleware based on context `enable_*` flags
5. Builds agent using `langchain.agents.create_agent()`

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

### Middleware

All middleware is configurable via `ContextSchema` flags. Each can be enabled/disabled independently:

| Middleware | Enable Flag | Purpose |
|------------|-------------|---------|
| `ModelRetryMiddleware` | `retry_max_retries > 0` | Handle transient network failures |
| `ModelFallbackMiddleware` | `enable_fallback` | Fallback to alternative models |
| `ModelCallLimitMiddleware` | `model_call_*_limit > 0` | Prevent runaway costs |
| `ToolCallLimitMiddleware` | `tool_call_*_limit > 0` | Limit expensive SQL queries |
| `HumanInTheLoopMiddleware` | `enable_hitl` (+ `read_only=false`) | Require approval for write operations |
| `SummarizationMiddleware` | `enable_summarization` | Compress conversation history |
| `TodoListMiddleware` | `enable_todo` | Task planning for complex analysis |

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
AGENT_DATABASE_URI=sqlite:////absolute/path/to/test_chinook.db

# Option 2: Snowflake URI
# AGENT_DATABASE_URI=snowflake://user:password@account/database/schema?warehouse=wh&role=role

# Option 3: Individual Snowflake parameters
# AGENT_SNOWFLAKE_ACCOUNT=your_account
# AGENT_SNOWFLAKE_USER=your_user
# AGENT_SNOWFLAKE_PASSWORD=your_password
# AGENT_SNOWFLAKE_DATABASE=your_database
# AGENT_SNOWFLAKE_SCHEMA=your_schema
# AGENT_SNOWFLAKE_WAREHOUSE=your_warehouse
# AGENT_SNOWFLAKE_ROLE=your_role
```

### Agent Configuration

```bash
AGENT_MODEL=claude-sonnet-4-5-20250929
AGENT_TEMPERATURE=0.0
AGENT_MAX_ITERATIONS=25
AGENT_ENABLE_DEBUG=false
```

### Guardrails

```bash
AGENT_ALLOWED_SCHEMAS=*     # Comma-separated or * for all
AGENT_ALLOWED_TABLES=*      # Comma-separated or * for all
AGENT_READ_ONLY=true        # Enforce read-only access
AGENT_QUERY_TIMEOUT=30      # Timeout in seconds
```

### Development

```bash
LANGGRAPH_DEV_SERVER_PORT=2024
```

## Module Structure

```
src/agent/
├── __init__.py          # Exports: graph, ContextSchema, settings
├── graph.py             # build_graph() + _build_middleware() + _detect_db_type()
├── context.py           # ContextSchema (core + middleware config)
├── config.py            # Settings - defaults and env loading
├── utils.py             # init_model(), create_sql_database(), create_db_engine()
├── state.py             # AgentState (optional customization)
├── models.py            # Model-related utilities
├── prompts/
│   ├── __init__.py      # Exports: build_system_prompt
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
- `test_graph2.py` - Middleware assembly and ContextSchema middleware fields
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
