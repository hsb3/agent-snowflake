# CLAUDE.md - repl-client

Classic REPL client for LangGraph Dev Server using traditional imperative control flow.

## Overview

**repl-client** is a standalone Python package providing terminal interfaces for LangGraph servers:

- **Classic REPL** (`python -m repl_client`) - Simple terminal interface with Rich formatting
- **TUI** (`python -m repl_client.tui`) - Full Textual-based UI with sidebar, tabs, modals, status area

This is a generic client that works with any LangGraph dev server (not coupled to specific agents).

## Prerequisites

A running LangGraph Dev Server is required. Options:

```bash
# From the monorepo agent app
cd ../agent && make dev-server

# Or configure server URL in .env
LANGGRAPH_DEV_SERVER_URL=http://localhost:2024
```

## Essential Commands

```bash
make install      # Install dependencies with uv
make repl         # Start classic REPL
make tui          # Start TUI client
make tui-dev      # Start TUI with hot reload (TEXTUAL_DEVTOOLS=1)
make test         # Run tests with pytest
make lint         # Lint with ruff
make format       # Format with ruff
make type-check   # Type check with ty
make clean        # Remove caches
```

## Architecture

### Layer Overview

The client follows a layered architecture (Layers 0-8):

```
Layer 8: Main Loop (__main__.py)          - Orchestrates all components
Layer 7: Commands (commands/)              - Slash command system
Layer 6: Renderer (ui/)                    - Rich-based terminal output
Layer 5: HITL Handler (streaming/hitl.py) - Human-in-the-loop approval
Layer 4: Stream Handler (streaming/)       - SSE event processing
Layer 3: Session State (core/session.py)  - Ephemeral client state
Layer 2: Parsers (core/parsers.py)        - SSE event parsing
Layer 1: HTTP Client (core/client.py)     - LangGraph REST API wrapper
Layer 0: Logging (core/logging.py)        - Client-side logging
```

### Entry Points

- `src/repl_client/__main__.py` - Classic REPL entry point (`python -m repl_client`)
- `src/repl_client/tui/__main__.py` - TUI entry point (`python -m repl_client.tui`)

### Core Components (`core/`)

| File | Purpose |
|------|---------|
| `client.py` | Async HTTP client for LangGraph API using httpx. Handles SSE streaming with dual mode `["messages", "updates"]` for HITL support. |
| `session.py` | Ephemeral session state (thread_id, assistant_id, token counts). Server owns persistent state. |
| `parsers.py` | Parse SSE events into typed structures. Handles cumulative text (extracts deltas), tool call buffering. |
| `config.py` | Configuration from environment via pydantic-settings. |
| `logging.py` | Client-side logging to `.repl/client.log`. |

### Command System (`commands/`)

| File | Purpose |
|------|---------|
| `registry.py` | Registry pattern for command extensibility. |
| `handlers.py` | Built-in commands: `/help`, `/exit`, `/agents`, `/threads`, `/new`, `/info`, `/clear`, `/session`. |

### Streaming (`streaming/`)

| File | Purpose |
|------|---------|
| `handler.py` | Generator pattern for stream processing. Yields `ParsedChunk`, caller renders. Detects text deltas, tool calls, interrupts, usage. |
| `hitl.py` | Human-in-the-loop approval prompts. Tool preview formatting, resume command construction. |
| `types.py` | Data classes: `ParsedChunk`, `ContentBlock`, `ToolCall`, `Usage`, `ChunkType` enum. |

### UI Rendering (`ui/`)

| File | Purpose |
|------|---------|
| `renderer.py` | Base Rich primitives for terminal output. |
| `content_blocks.py` | Content blocks + `ToolRenderRegistry` for tool previews. |

### TUI Implementation (`tui/`)

Full Textual-based terminal UI with MVC-like structure:

```
tui/
├── __main__.py              # TUI entry point
├── app.py                   # Main Textual App class
├── repl.tcss                # Legacy styles (deprecated)
├── styles/                  # Modular CSS
│   ├── theme.tcss           # Colors, palette (Carbon theme)
│   ├── layout.tcss          # Layout structure
│   ├── components.tcss      # Widget styles
│   └── states.tcss          # Interactive states
├── models/                  # State management
│   └── app_state.py         # Centralized app state
├── views/                   # UI composition
│   ├── layout_view.py       # Main layout
│   ├── message_area_view.py # Message display
│   ├── sidebar_view.py      # Sidebar with sessions
│   └── status_area_view.py  # Status bar
├── controllers/             # Logic handlers
│   ├── message_controller.py
│   ├── session_controller.py
│   ├── command_controller.py
│   └── interrupt_controller.py
├── services/                # Backend integration
│   ├── langgraph_service.py # LangGraph API wrapper
│   └── stream_service.py    # Stream processing
├── widgets/                 # Reusable components
│   ├── messages.py          # Message widgets
│   ├── input.py             # Input widget
│   ├── sidebar.py           # Sidebar widget
│   ├── status.py            # Status widget
│   ├── status_area.py       # Status area
│   ├── history.py           # History navigation
│   ├── loading.py           # Loading indicators
│   └── command_palette.py   # Command palette
└── hitl.py                  # TUI-specific HITL handler
```

## Environment Configuration

Copy `.env.example` to `.env`:

```bash
# Required: LangGraph Dev Server URL
LANGGRAPH_DEV_SERVER_URL=http://localhost:2024

# Optional: Default agent/graph to use
LANGGRAPH_AGENT_NAME=agent
```

## Module Structure

```
apps/repl-client/
├── CLAUDE.md                # This file
├── Makefile                 # Development commands
├── pyproject.toml           # Package configuration
├── .env.example             # Environment template
├── src/
│   └── repl_client/
│       ├── __init__.py
│       ├── __main__.py      # Classic REPL entry
│       ├── core/            # Foundation (HTTP, parsing, state)
│       ├── streaming/       # Stream handling, HITL
│       ├── ui/              # Rich-based rendering
│       ├── commands/        # Command system
│       └── tui/             # Textual TUI
├── tests/
│   └── repl_client/
│       ├── core/
│       ├── streaming/
│       ├── ui/
│       ├── commands/
│       └── tui/
├── scripts/
│   ├── demos/               # Visual TUI demos
│   └── tests/               # Manual test scripts
└── docs/
    └── spec/                # Specifications
```

## Testing Strategy

```bash
# Run all tests
uv run pytest tests/ -v

# Test by layer
uv run pytest tests/repl_client/core/ -v           # Core layers
uv run pytest tests/repl_client/streaming/ -v      # Streaming
uv run pytest tests/repl_client/commands/ -v       # Commands
uv run pytest tests/repl_client/ui/ -v             # UI rendering
uv run pytest tests/repl_client/tui/ -v            # TUI widgets

# Integration tests (require running server)
uv run pytest -m integration -v
```

Tests are organized by layer, mirroring the source structure. Use `@pytest.mark.integration` for tests requiring a live server.

## Key Design Decisions

### Streaming

- Server sends **cumulative text** (not deltas)
- Client extracts delta: `new_text[len(prev_text):]`
- Uses dual stream mode `["messages", "updates"]` for HITL support
- `__interrupt__` signals only appear in "updates" stream

### State Management

- **Client is stateless** - server owns threads/checkpoints
- **SessionState** tracks current context for display only
- **No local history cache** - fetch from server if needed

### HITL Flow

1. Detect `__interrupt__` in updates stream
2. Show tool preview with approval prompt
3. Resume with `command: {resume: {approve: bool}}`
4. Continue processing resumed stream (recursive)

## TUI Key Bindings

| Key | Action |
|-----|--------|
| F2 | Agent selection modal |
| F3 | Thread selection modal |
| F4 | Toggle sidebar |
| F5 | Expand sidebar |
| Ctrl+L | Clear messages |
| Ctrl+C | Quit |
| Ctrl+P | Command palette |
| Enter | Submit message |
| Up/Down | History navigation |

## API Endpoints Used

From LangGraph Dev Server:

```
GET  /ok                            # Health check
POST /assistants/search             # List agents
GET  /assistants/{id}               # Get agent details
POST /threads                       # Create thread
GET  /threads/{id}                  # Get thread
POST /threads/search                # List threads
POST /threads/{id}/runs/stream      # Stream messages (SSE)
```

## Common Tasks

### Add New Command

1. Add handler in `commands/handlers.py`
2. Register in `register_all()` method
3. Add tests in `tests/repl_client/commands/`

### Add Tool Preview Formatter

1. Register in `ui/content_blocks.py` via `ToolRenderRegistry`
2. Implement formatter function: `(dict) -> str`

### Add TUI Widget

1. Create in `tui/widgets/<name>.py`
2. Add tests in `tests/repl_client/tui/test_<name>.py`
3. Export from `tui/widgets/__init__.py`
4. Add CSS in `tui/styles/components.tcss`

## Dependencies

```toml
# Runtime
httpx>=0.27.0           # HTTP/SSE client
pydantic-settings>=2.12 # Configuration
python-dotenv>=1.2.1    # Environment loading
rich>=13.0.0            # Terminal formatting
textual>=7.3.0          # TUI framework

# Development
pytest>=9.0.2           # Testing
pytest-asyncio>=1.3.0   # Async test support
ruff>=0.14.14           # Linting/formatting
ty>=0.0.13              # Type checking
```

## Debugging

- Check `.repl/client.log` for client-side issues
- Use `scripts/demos/demo_tui_*.py` for visual verification
- Server logs at `.repl/server.log` (when using combined make commands)

## Notes for AI Agents

When modifying repl_client:

- Follow layer separation (don't mix HTTP client with UI rendering)
- Use generator pattern for streaming (yield `ParsedChunk`, caller renders)
- All server interactions must be async
- Tests should use `@pytest.mark.integration` if they need live server
- TUI widgets should be self-contained with minimal dependencies

Common pitfalls:

- Forgetting to wrap message data in array (LangGraph API returns `[{message}]`)
- Mixing sync/async (all server calls are async)
- Not flushing output before `input()` calls
- Assuming text is delta when it's cumulative
