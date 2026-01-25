# CLAUDE.md - repl_client

Terminal REPL client for LangGraph HTTP API. Generic client that works with any LangGraph dev server.

## Project Overview

**repl_client** is a standalone Python package providing terminal interfaces for LangGraph servers:
- **Classic REPL** (`python -m repl_client`) - Simple terminal interface
- **TUI** (`python -m repl_client.tui`) - Full Textual-based UI with sidebar, tabs, status area

**Design Goal**: Generic client for any LangGraph server, not coupled to agent_snowflake agents.

## Quick Start

```bash
# Install dependencies
uv sync --group repl

# Start server (in repo with LangGraph agents)
make dev-server

# Run REPL
python -m repl_client           # Classic REPL
python -m repl_client.tui       # Full TUI

# Or combined
make repl                       # Server + classic REPL
```

## Architecture

### Layer 0: Logging (`core/logging.py`)
- Client-side logging only (`.repl/client.log`)
- Does NOT duplicate server logs

### Layer 1: HTTP Client (`core/client.py`)
- REST API wrapper for LangGraph HTTP endpoints
- SSE streaming support via httpx
- Dual stream mode: `["messages", "updates"]` for HITL
- Methods: `list_agents`, `create_thread`, `stream_message`, `resume_after_interrupt`

### Layer 2: Parsers (`core/parsers.py`)
- Parse SSE events into typed structures
- Text delta extraction (server sends cumulative text)
- Content block parsing (text, tool_use, tool_result)
- Tool call buffering for partial JSON
- Data classes: `ParsedChunk`, `ContentBlock`, `ToolCall`, `Usage`

### Layer 3: Session State (`core/session.py`)
- Ephemeral state (cleared on exit)
- Tracks: thread_id, assistant_id, run_id, tokens, namespace_state
- Server owns persistent state (threads, checkpoints)

### Layer 4: Stream Handler (`streaming/handler.py`)
- Generator pattern (yields `ParsedChunk`, caller renders)
- Detects: text deltas, tool calls, interrupts, usage
- Method-local buffers (auto-cleanup)
- Namespace tracking for parallel agents (future)

### Layer 5: HITL Handler (`streaming/hitl.py`)
- Human-in-the-loop approval prompts
- Tool preview formatting with registry
- Resume command construction
- Phase 2: Simple y/n prompts (Phase 3: interactive menus)

### Layer 6: Renderer (`ui/`)
- **renderer.py** - Base Rich primitives
- **message.py** - User/AI/tool message formatting
- **content_blocks.py** - Content blocks + tool registry

### Layer 7: Commands (`commands/`)
- **registry.py** - Registry pattern for extensibility
- **handlers.py** - 8 commands: /help, /exit, /agents, /threads, /new, /info, /clear, /session

### Layer 8: Main Loop (`__main__.py`)
- REPLLoop class orchestrates all layers
- Async main loop
- Startup → Input loop → Shutdown flow

### TUI (`tui/`)
- **app.py** - Main Textual app
- **widgets/** - Message widgets, input, sidebar, status area, loading
- **repl.tcss** - Textual CSS styling
- **hitl.py** - TUI-specific HITL handler

## Key Design Decisions

### Streaming
- Server sends **cumulative text** (not deltas)
- Must extract delta: `new_text[len(prev_text):]`
- Uses dual stream mode `["messages", "updates"]` for HITL support
- `__interrupt__` signals only appear in "updates" stream

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

### State Management
- **Client is stateless** - server owns threads/checkpoints
- **SessionState** tracks current context for display only
- **No local history cache** - fetch from server if needed

## File Organization

```
src/repl_client/
├── __main__.py              # Classic REPL entry point
├── core/                    # Foundation (HTTP, parsing, state)
├── streaming/               # Stream handling, HITL
├── ui/                      # Rich-based rendering (classic REPL)
├── commands/                # Command system
└── tui/                     # Textual-based full TUI
    ├── __main__.py          # TUI entry point
    ├── app.py               # Main Textual app
    ├── widgets/             # Textual widgets
    └── repl.tcss            # CSS styling
```

## Testing

**Test Organization**:
```
tests/repl_client/
├── core/                    # Layer 1-3 tests
├── streaming/               # Layer 4-5 tests
├── ui/                      # Layer 6 tests (Rich)
├── commands/                # Layer 7 tests
├── tui/                     # TUI widget tests
├── test_main.py             # Layer 8 tests
└── test_hitl_e2e.py         # End-to-end HITL tests
```

**Running Tests**:
```bash
uv run pytest tests/repl_client/ -v                    # All tests
uv run pytest tests/repl_client/core/ -v               # Core layers
uv run pytest tests/repl_client/tui/ -v                # TUI widgets
uv run pytest -m integration                           # Integration tests (need server)
```

**Current Status**: 316 tests (98 TUI, 218 core/streaming/commands)

## Configuration

**Environment Variables** (read from `.env`):
- `LANGGRAPH_DEV_SERVER_PORT` - Server port (default: 2024)

**REPL Config** (`core/config.py`):
```python
@dataclass
class Config:
    server_url: str              # http://localhost:2024
    default_agent: str           # Optional default agent ID
    stream_mode: list[str]       # ["messages", "updates"]
    debug: bool                  # Enable debug logging
```

## Commands (Slash Commands)

**Phase 1** (Basic):
- `/help [command]` - Show help
- `/exit` - Quit REPL

**Phase 2** (Features):
- `/agents [name] [--new]` - List or switch agents
- `/threads [id]` - List or resume threads
- `/new` - Create new thread
- `/info` - Show session summary

**Phase 3** (Polish):
- `/clear` - Clear screen
- `/session` - Full state dump

## TUI Key Bindings

- **F2** - Agent selection modal
- **F3** - Thread selection modal
- **F4** - Toggle sidebar
- **F5** - Expand sidebar
- **Ctrl+L** - Clear messages
- **Ctrl+C** - Quit
- **Ctrl+P** - Command palette
- **Enter** - Submit message
- **Up/Down** - History navigation

## Common Tasks

### Add New Command
1. Add handler in `commands/handlers.py`
2. Register in `register_all()` method
3. Add tests in `tests/repl_client/commands/test_handlers.py`
4. Update help text (auto-generated from registry)

### Add Tool Preview Formatter
1. Register in `ui/content_blocks.py` → `ToolRenderRegistry`
2. Implement formatter function: `(dict) -> str`
3. Add to builtin formatters list

### Add TUI Widget
1. Create in `tui/widgets/<name>.py`
2. Add tests in `tests/repl_client/tui/test_<name>.py`
3. Export from `tui/widgets/__init__.py`
4. Add CSS in `tui/repl.tcss`

### Debug Streaming Issues
1. Check `.repl/client.log` for parse errors
2. Capture raw SSE with `scripts/debug/test_stream_modes.py`
3. Verify server logs in `.repl/server.log` (when using `make repl`)

## Specifications & Documentation

**Driving Specifications** (in repo root):
- `/repl_spec.json` - Requirements, features, phases, success criteria
- `/repl_components.jsonc` - Layer 0-8 architecture (1095 lines)

**Supporting Docs** (`docs/dev_docs/spec-repl-v1/`):
- `README.md` - Navigation guide
- `research/` - HTTP stream format, file structure analysis, OpenAPI spec
- `archive/` - Outdated prose docs (replaced by JSON specs)

**Work Documentation** (`docs/dev_docs/ai_docs/ai_gen/`):
- Implementation notes, decisions, solutions
- **Frontmatter template**:
```yaml
---
doc_id: CC-YYYY-NNN
title: Brief description
date: YYYY-MM-DD
type: planning|solution|investigation|status|summary
project: repl_client
focus: tui|streaming|commands|core
status: draft|complete
tags: [textual, hitl, sse, ...]
---
```

## Known Issues & Limitations

**Phase 2 (Current)**:
- HITL approval prompt may not flush properly before `input()` (fixed with `renderer.flush()`)
- Middleware interrupts (ModelCallLimitMiddleware) need custom handling beyond tool approval
- Some async test fixtures need updates for streaming tests

**Future (Phase 3)**:
- Enhanced input with prompt-toolkit (classic REPL)
- Interactive HITL menus with arrow keys
- Artifact palette expanded mode in TUI
- Tool output caching in sidebar
- Thread resumption with history display

## Development Workflow

**Typical session**:
```bash
# Terminal 1: Server
make dev-server

# Terminal 2: Development
uv run python -m repl_client.tui

# Make changes, test
uv run pytest tests/repl_client/tui/ -v

# Format and type check
make format lint type-check
```

## API Endpoints Used

From LangGraph Dev Server (OpenAPI spec in `docs/dev_docs/spec-repl-v1/research/openapi.json`):

```
POST /assistants/search         # List agents
GET  /assistants/{id}           # Get agent details
POST /threads                   # Create thread
GET  /threads/{id}              # Get thread
POST /threads/search            # List threads
POST /threads/{id}/runs/stream  # Stream messages (SSE)
```

**Stream modes**: `["messages", "updates"]`
- `messages` → Text chunks, tool calls, tool results
- `updates` → State changes, `__interrupt__` signals

## Dependencies

**Required** (`[dependency-groups] repl`):
- `httpx>=0.27.0` - HTTP/SSE client
- `rich>=13.0.0` - Terminal formatting (classic REPL)
- `textual>=1.0.0` - TUI framework

**Dev** (`[dependency-groups] dev`):
- `pytest>=9.0.2` - Testing
- `pytest-asyncio>=1.3.0` - Async test support
- `ruff>=0.14.14` - Linting/formatting
- `ty>=0.0.13` - Type checking

## Entry Points

```bash
# Classic REPL
python -m repl_client

# TUI
python -m repl_client.tui

# With uv tool install (future)
repl-client
repl-tui
```

## Notes for AI Agents

**When modifying repl_client**:
- Follow layer separation (don't mix HTTP client with UI rendering)
- Use generator pattern for streaming (yield ParsedChunk, caller renders)
- All server interactions must be async
- Tests should use `@pytest.mark.integration` if they need live server
- TUI widgets should be self-contained with minimal dependencies
- Update `repl_components.jsonc` when changing architecture

**Common pitfalls**:
- Forgetting to wrap message data in array (LangGraph API returns `[{message}]`)
- Mixing sync/async (all server calls are async)
- Not flushing output before `input()` calls
- Assuming text is delta when it's cumulative

**Debugging**:
- Check `.repl/client.log` for client-side issues
- Check `.repl/server.log` (when using make commands) for server issues
- Use `scripts/debug/test_stream_modes.py` to capture raw SSE streams
- Visual verification of TUI: `scripts/repl_client/demos/demo_tui_*.py` scripts
