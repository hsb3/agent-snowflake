---
title: "StateGraph REPL: README / QUICKSTART"
created: 2026-01-23
updated: 2026-01-24
status: current
tags: [repl, quickstart, stategraph, tutorial]
type: guide
---

# StateGraph REPL: README / QUICKSTART

## Prerequisites

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Set up test database** (if not already done):
   ```bash
   make setup-chinook
   ```

3. **Configure environment** (copy `.env.example` to `.env` and add your API key):
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

## Option 1: Two Terminal Setup (Recommended)

### Terminal 1: Start LangGraph Server
```bash
make dev-server
```

This starts the server on port 2024 (from `.env`) without opening a browser.

You should see:
```
Starting LangGraph dev server on port 2024 (no browser)...
API available at http://localhost:2024
Ready!
```

### Terminal 2: Start StateGraph REPL
```bash
uv run python -m repl_client_graph
```

You should see:
```
Connecting to LangGraph server...
Connected to http://localhost:2024
Using agent: 3f239ca8-eb8a-5b20-977f-da398159f544

╭─────────────────── LangGraph REPL ───────────────────╮
│ Welcome to LangGraph REPL (StateGraph Edition)!      │
│                                                      │
│ Powered by LangGraph StateGraph for control flow.    │
│ Dual streaming mode: messages + updates.             │
╰──────────────────────────────────────────────────────╯

[agent] >
```

## Option 2: One-Command Start

Add this to your `Makefile` for convenience:

```bash
repl-graph:
	@PORT=$$(grep LANGGRAPH_DEV_SERVER_PORT .env 2>/dev/null | cut -d= -f2 | tr -d ' '); \
	PORT=$${PORT:-2024}; \
	mkdir -p .repl; \
	echo "Starting LangGraph server + StateGraph REPL..."; \
	echo "Server logs: .repl/server.log"; \
	uv run langgraph dev --allow-blocking --port $$PORT --no-browser > .repl/server.log 2>&1 & \
	SERVER_PID=$$!; \
	trap "echo 'Stopping server...'; kill $$SERVER_PID 2>/dev/null; exit" INT TERM; \
	sleep 3; \
	echo "Server ready on port $$PORT"; \
	echo "Starting StateGraph REPL client..."; \
	uv run python -m repl_client_graph || true; \
	echo "Stopping server..."; \
	kill $$SERVER_PID 2>/dev/null
```

Then run:
```bash
make repl-graph
```

## Usage

Once the REPL starts, you can:

### Chat with the Agent
```
[agent] > Show me all tables in the database
[agent] > What columns are in the Album table?
[agent] > Count how many artists we have
```

### Use Commands
```
[agent] > /help        # Show available commands
[agent] > /exit        # Exit the REPL
```

## Troubleshooting

### Server Connection Failed
```
Error connecting to LangGraph server at http://localhost:2024
```

**Fix:** Make sure the server is running in Terminal 1
```bash
# Check if server is running
curl http://localhost:2024/ok
# Should return: {"ok":true}
```

### Port Already in Use
```
Error: Address already in use
```

**Fix:** Kill existing server or change port in `.env`:
```bash
# Kill existing server
pkill -f "langgraph dev"

# Or change port in .env
LANGGRAPH_DEV_SERVER_PORT=2025
```

### Agent Not Found
```
Warning: No agents available
```

**Fix:** Make sure your agent graphs are in `src/agent_snowflake/` and the server detected them. Check server logs.

## Features

### Dual Streaming Mode
The REPL uses `stream_mode=["messages", "updates"]`:
- **messages:** See LLM tokens stream in real-time
- **updates:** State changes tracked (for observability)

### StateGraph Architecture
- 9 nodes orchestrate the REPL flow
- Automatic state management
- Type-safe with REPLState TypedDict
- Testable nodes in isolation

### Commands (Phase 1)
- `/help` - Show available commands
- `/exit` - Exit cleanly

### Coming Soon (Phase 2)
- `/agents` - List and switch agents
- `/threads` - List and resume threads
- `/new` - Create new thread
- `/info` - Show session info

## Stopping

**Two-terminal setup:**
- Terminal 2: Type `/exit` or press `Ctrl+C`
- Terminal 1: Press `Ctrl+C` to stop server

**One-command setup:**
- Press `Ctrl+C` (stops both server and REPL)

## Comparison: Classic vs StateGraph REPL

| Feature | `repl_client` | `repl_client_graph` |
|---------|---------------|---------------------|
| Control flow | Traditional loop | StateGraph |
| State management | Manual | Automatic |
| Streaming | Single mode | Dual mode |
| Testability | Integration | Unit + Integration |
| Observability | Manual logging | Built-in traces |
| Status | Experimental | Working ✅ |

**Recommendation:** Use `repl_client_graph` for the improved architecture and dual streaming.
