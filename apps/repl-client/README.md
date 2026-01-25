# repl-client

Terminal client for LangGraph Dev Server. Provides both a classic REPL and a full TUI.





**BOTH ARE EARLY DEV**




## Quick Start

```bash
# Install
make install

# Start (requires a running LangGraph server)
make tui          # Full TUI with sidebar, modals, status area
make repl         # Simple terminal REPL
```

## What You Need

A LangGraph Dev Server running somewhere. Configure the URL in `.env`:

```bash
cp .env.example .env
# Edit LANGGRAPH_DEV_SERVER_URL if not using localhost:2024
```

Or start one from the agent app:

```bash
cd ../agent && make dev-server
```

## Features

- Stream LLM responses in real-time
- Human-in-the-loop tool approval
- Switch between agents and threads
- Slash commands (`/help`, `/agents`, `/threads`, `/new`, etc.)

## Development

```bash
make test         # Run tests
make format       # Format code
make lint         # Lint code
make type-check   # Type check
```

See `CLAUDE.md` for architecture details and development guidance.
