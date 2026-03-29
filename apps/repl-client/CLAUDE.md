# CLAUDE.md - repl-client

Classic REPL client for LangGraph Dev Server using traditional imperative control flow.

## Overview

**repl-client** is a standalone Python package providing terminal interfaces for LangGraph servers:

- **Classic REPL** (`python -m repl_client`) - Simple terminal interface with Rich formatting
- **TUI** (`python -m repl_client.tui`) - Full Textual-based UI with sidebar, tabs, modals, status area

**Design Goal**: Generic client for any LangGraph server, not coupled to specific agents.

## Critical: Use langgraph-sdk

**DO NOT use custom httpx clients for LangGraph API calls.** Use the official `langgraph-sdk` package.

```python
from langgraph_sdk import get_client  # async
from langgraph_sdk import get_sync_client  # sync
from langgraph_sdk.schema import Command

client = get_client(url="http://localhost:2024")
```

**Why**: The SDK provides features that would be complex to implement manually:
- `client.threads.get_history()` — retrieve conversation history
- `client.threads.get_state()` / `update_state()` — inspect/modify state
- Time travel via `checkpoint_id` — resume from any checkpoint
- `client.runs.wait()` — non-streaming execution
- Typed schemas (`Command`, response models)
- `subgraphs=True` for nested graph interrupt detection

**Status**: `core/client.py` uses langgraph-sdk. The `streaming/` layer processes SDK stream chunks.

**SDK docs**: https://docs.langchain.com/langsmith/langgraph-python-sdk

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

### Layer Details

| Layer | File | Purpose |
|-------|------|---------|
| 0 | `core/logging.py` | Client-side logging only (`.repl/client.log`). Does NOT duplicate server logs. |
| 1 | `core/client.py` | LangGraph API client using langgraph-sdk. Dual stream mode `["messages", "updates"]` for HITL. New methods: `get_thread_history()`, `get_thread_state()`. |
| 2 | `core/parsers.py` | Parse SSE events into typed structures. Text delta extraction (server sends cumulative text). Content block parsing (text, tool_use, tool_result). Tool call buffering for partial JSON. |
| 3 | `core/session.py` | Ephemeral state (cleared on exit). Tracks: thread_id, assistant_id, run_id, tokens, namespace_state. Server owns persistent state. |
| 4 | `streaming/handler.py` | Generator pattern (yields `ParsedChunk`, caller renders). Detects: text deltas, tool calls, interrupts, usage. Method-local buffers (auto-cleanup). |
| 5 | `streaming/hitl.py` | Human-in-the-loop approval prompts. Tool preview formatting with registry. Resume command construction. |
| 6 | `ui/` | `renderer.py` - Base Rich primitives. `content_blocks.py` - Content blocks + `ToolRenderRegistry`. |
| 7 | `commands/` | `registry.py` - Registry pattern for extensibility. `handlers.py` - Built-in commands. |
| 8 | `__main__.py` | REPLLoop class orchestrates all layers. Async main loop. Startup → Input loop → Shutdown flow. |

### Entry Points

- `src/repl_client/__main__.py` - Classic REPL entry point (`python -m repl_client`)
- `src/repl_client/tui/__main__.py` - TUI entry point (`python -m repl_client.tui`)

### Streaming Data Types

```python
# streaming/types.py
@dataclass
class ParsedChunk:
    chunk_type: ChunkType  # TEXT_DELTA, TOOL_CALL, TOOL_RESULT, INTERRUPT, USAGE, etc.
    content: ContentBlock | ToolCall | Usage | None

@dataclass
class ContentBlock:
    type: str  # "text", "tool_use", "tool_result"
    text: str | None
    tool_use_id: str | None

@dataclass
class ToolCall:
    id: str
    name: str
    input: dict

@dataclass
class Usage:
    input_tokens: int
    output_tokens: int
```

### TUI Implementation (`tui/`)

Full Textual-based terminal UI with MVC-like structure:

```
tui/
├── __main__.py              # TUI entry point
├── app.py                   # Main Textual App class
├── hitl.py                  # TUI-specific HITL handler
├── styles/                  # Modular CSS (Carbon theme)
│   ├── theme.tcss           # Colors, palette
│   ├── layout.tcss          # Layout structure
│   ├── components.tcss      # Widget styles
│   ├── sidebar.tcss         # Sidebar styles
│   ├── modals.tcss          # Modal styles
│   ├── states.tcss          # Interactive states
│   ├── light-mode.tcss      # Light mode overrides
│   └── index.tcss           # Concatenated output (build-css)
├── models/                  # State management
│   └── app_state.py         # Centralized app state
├── screens/                 # Modal screens
│   ├── agent_config.py      # Agent config viewer
│   └── welcome.py           # Welcome screen
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
└── widgets/                 # Reusable components
    ├── agent_detail.py      # Agent detail panel
    ├── command_palette.py   # Command palette
    ├── history.py           # History navigation
    ├── input.py             # Input widget
    ├── loading.py           # Loading indicators
    ├── messages.py          # Message widgets
    ├── sidebar.py           # Sidebar widget
    ├── status.py            # Status widget
    └── status_area.py       # Status area
```

## Configuration

### Environment Variables

Copy `.env.example` to `.env`:

```bash
# Required: LangGraph Dev Server URL
LANGGRAPH_DEV_SERVER_URL=http://localhost:2024

# Optional: Default agent/graph to use
LANGGRAPH_AGENT_NAME=agent
```

### Config Class (`core/config.py`)

```python
@dataclass
class Config:
    server_url: str              # http://localhost:2024
    default_agent: str           # Optional default agent ID
    stream_mode: list[str]       # ["messages", "updates"]
    debug: bool                  # Enable debug logging
```

## Key Design Decisions

### Streaming

- Server sends **cumulative text** (not deltas)
- Client extracts delta: `new_text[len(prev_text):]`
- Uses dual stream mode `["messages", "updates"]` for HITL support
- `__interrupt__` signals only appear in "updates" stream
- `messages` → Text chunks, tool calls, tool results
- `updates` → State changes, interrupt signals

### State Management

- **Client is stateless** - server owns threads/checkpoints
- **SessionState** tracks current context for display only
- **No local history cache** - fetch from server if needed

### Agent Switching

- User types friendly name: `agent_enhanced`
- Client resolves to UUID via cache
- Server receives UUID for API calls
- Default: keeps current thread (use `--new` flag for fresh thread)

### HITL Flow

1. Detect `__interrupt__` in updates stream
2. Show tool preview with approval prompt
3. Resume with `command: {resume: {approve: bool}}`
4. Continue processing resumed stream (recursive)

## Commands (Slash Commands)

| Command | Description |
|---------|-------------|
| `/help [command]` | Show help for all or specific command |
| `/exit` | Quit REPL |
| `/agents [name] [--new]` | List or switch agents |
| `/threads [id]` | List or resume threads |
| `/new` | Create new thread |
| `/info` | Show session summary |
| `/clear` | Clear screen |
| `/session` | Full state dump |

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

**Stream modes**: `["messages", "updates"]`

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
│   ├── core/                # Core module tests
│   ├── streaming/           # Streaming tests
│   ├── ui/                  # UI rendering tests
│   ├── commands/            # Command tests
│   ├── tui/                 # TUI widget tests
│   ├── test_main.py
│   └── test_hitl_e2e.py
└── docs/
    └── spec/research/       # Reference material
```

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Test by layer
uv run pytest tests/core/ -v           # Core layers
uv run pytest tests/streaming/ -v      # Streaming
uv run pytest tests/commands/ -v       # Commands
uv run pytest tests/ui/ -v             # UI rendering
uv run pytest tests/tui/ -v            # TUI widgets

# Integration tests (require running server)
uv run pytest -m integration -v
```

Tests are organized by layer, mirroring the source structure. Use `@pytest.mark.integration` for tests requiring a live server.

## Development Workflow

```bash
# Terminal 1: Server
cd ../agent && make dev-server

# Terminal 2: Development
uv run python -m repl_client.tui

# Make changes, test
uv run pytest tests/tui/ -v

# Format and type check
make format lint type-check
```

## Common Tasks

### Add New Command

1. Add handler in `commands/handlers.py`
2. Register in `register_all()` method
3. Add tests in `tests/commands/`
4. Help text auto-generated from registry

### Add Tool Preview Formatter

1. Register in `ui/content_blocks.py` via `ToolRenderRegistry`
2. Implement formatter function: `(dict) -> str`
3. Add to builtin formatters list

### Add TUI Widget

1. Create in `tui/widgets/<name>.py`
2. Add tests in `tests/tui/test_<name>.py`
3. Export from `tui/widgets/__init__.py`
4. Add CSS in `tui/styles/components.tcss`

### Debug Streaming Issues

1. Check `.repl/client.log` for parse errors
2. Verify server logs in `.repl/server.log` (when using combined make commands)
3. Run `make tui` to visually verify changes

## Dependencies

```toml
# Runtime
langgraph-sdk           # LangGraph API client (preferred over raw httpx)
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

## Known Issues & Limitations

**Current**:
- HITL approval prompt may not flush properly before `input()` (fixed with `renderer.flush()`)
- Middleware interrupts (ModelCallLimitMiddleware) need custom handling beyond tool approval
- Some async test fixtures need updates for streaming tests

**Future Enhancements**:
- Thread history display (use `client.get_thread_history()`)
- Time travel / checkpoint resumption (use checkpoint_id with SDK)
- Interactive HITL menus with arrow keys
- Artifact palette expanded mode in TUI
- Tool output caching in sidebar

## Notes for AI Agents

When modifying repl_client:

- **Use langgraph-sdk for all LangGraph API calls** — do not write custom httpx code
- Follow layer separation (don't mix API client with UI rendering)
- Use generator pattern for streaming (yield `ParsedChunk`, caller renders)
- All server interactions must be async
- Tests should use `@pytest.mark.integration` if they need live server
- TUI widgets should be self-contained with minimal dependencies

Common pitfalls:

- Writing custom HTTP/SSE code instead of using langgraph-sdk
- Mixing sync/async (all server calls are async)
- Not flushing output before `input()` calls
- Assuming text is delta when it's cumulative (server sends cumulative text)
