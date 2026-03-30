# SQL Agent

LangGraph SQL agent with configurable middleware and database guardrails.

## Key Features

- **Multi-database** — SQLite for dev, Snowflake for production (more planned)
- **Configurable middleware** — HITL approval, retry, rate limits, summarization, fallback — all toggle-able via context flags
- **Query guardrails** — Read-only mode, schema/table restrictions, query timeouts
- **LangGraph Studio** — Full Studio UI integration with configurable context fields

## Quick Start

```bash
make install            # Install dependencies
make setup-chinook      # Download test database
make dev                # Start dev server with Studio UI
```

## Commands

```bash
# Setup
make install            # Install dependencies with uv
make setup-chinook      # Download Chinook test database

# Development
make dev                # Start LangGraph dev server with Studio UI
make dev-server         # Start server without browser

# Quality
make test               # Run all tests
make format             # Format with ruff
make lint               # Lint with ruff
make type-check         # Type check with ty
make check              # All of the above
make clean              # Remove caches
```

## Configuration

Copy `.env.example` to `.env`. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `AGENT_DATABASE_URI` | SQLAlchemy connection URI | (required) |
| `AGENT_MODEL` | LLM model | `claude-sonnet-4-5-20250929` |
| `AGENT_READ_ONLY` | Enforce read-only access | `true` |
| `AGENT_ENABLE_HITL` | Human-in-the-loop approval | `true` |

Config precedence: runtime context → environment → defaults.

## Example Prompts

```
Show me all tables

Who are the top 10 artists by track count?

For each billing country, what is total invoice revenue? Rank by total revenue desc, top 10.
```

## Notes

- API docs at `localhost:2024/docs`
- Safari viewing requires `--tunnel` flag
- See `CLAUDE.md` for architecture details
