# Agent Snowflake

SQL agent with database guardrails and a terminal client for LangGraph servers.

## Key Features

- **SQL Agent** — LangGraph-powered agent with query validation and guardrails
- **TUI Client** — Rich terminal interface built with Textual
- **Human-in-the-Loop** — Approve or reject tool calls before execution
- **Multi-Agent Support** — Switch between agent variants on the fly

## Quick Start

```bash
# Install both apps (creates separate virtual environments)
make install

# Terminal 1: Start the agent server
cd apps/agent && make dev-server

# Terminal 2: Launch the TUI client
cd apps/repl-client && make tui
```

## Structure

```
apps/
├── agent/           # LangGraph SQL agent
└── repl-client/     # Terminal UI client
```

| App | Purpose | Run |
|-----|---------|-----|
| **agent** | SQL agent with LangGraph | `cd apps/agent && make dev` |
| **repl-client** | Terminal UI for any LangGraph server | `cd apps/repl-client && make tui` |

Each app is self-contained with its own virtual environment, Makefile, and `CLAUDE.md`:

```bash
cd apps/agent && make help
cd apps/repl-client && make help
```

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
