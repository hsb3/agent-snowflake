# Agent Snowflake

SQL agent with database guardrails and terminal clients for LangGraph servers.

**ROUGH DRAFT**

## Key Features

- **SQL Agent** - LangGraph-powered agent with query validation and guardrails
- **TUI Client** - Rich terminal interface built with Textual framework
- **Human-in-the-Loop** - Approve or reject tool calls before execution
- **Multi-Agent Support** - Switch between agent variants on the fly
- **Independent Apps** - Each app has isolated dependencies, works standalone

## Quick Start

```bash
# Install both apps (creates separate virtual environments)
make install

# Terminal 1: Start the agent server
cd apps/agent && make dev-server

# Terminal 2: Launch the TUI client
cd apps/repl-client && make tui
```

## Project Structure

```
agent-snowflake/
├── apps/
│   ├── agent/           # LangGraph SQL agent
│   │   └── .venv/       # Agent dependencies (langgraph, langchain)
│   └── repl-client/     # Terminal UI client
│       └── .venv/       # Client dependencies (textual, httpx)
├── Makefile             # Orchestration commands
└── CLAUDE.md            # AI coding assistant guidance
```

## Apps

| App | Purpose | Run |
|-----|---------|-----|
| **agent** | SQL agent with LangGraph | `cd apps/agent && make dev` |
| **repl-client** | Terminal UI for any LangGraph server | `cd apps/repl-client && make tui` |

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager

## Development

Each app is self-contained with its own Makefile:

```bash
cd apps/agent && make help       # Agent commands
cd apps/repl-client && make help # TUI commands
```

See `CLAUDE.md` for detailed architecture and development guidance.
