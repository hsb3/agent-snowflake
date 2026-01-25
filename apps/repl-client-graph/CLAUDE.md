# CLAUDE.md - StateGraph REPL Client

This file provides guidance for working on the **repl_client_graph** module.

## Overview

A terminal REPL client for LangGraph Dev Server REST API, implemented using **LangGraph StateGraph** for control flow instead of imperative loops. The StateGraph approach provides automatic state propagation, visual debugging capabilities, and structured control flow.

**Key distinction**: This is a client for interacting with existing LangGraph agents, not an agent builder.

## Prerequisites

A running LangGraph Dev Server is required. Start it with:

```bash
# From monorepo root
make dev-server

# Or from agent package
cd ../agent && make dev-server
```

The server must be running before starting the REPL.

## Architecture

### Entry Point

**`__main__.py`** - Initializes components and runs the StateGraph:
- Loads configuration from environment
- Creates dependencies: `LangGraphClient`, `Renderer`, `SessionState`, `HITLHandler`, `ToolRenderRegistry`
- Sets up context variables for dependency injection
- Builds and invokes the REPL StateGraph
- Handles session lifecycle (connect, welcome, run loop, summary)

### Graph-Based Control Flow

**`graph/builder.py`** - Main graph builder using coarse-grained nodes:

```
get_input → route_input → [command | message | empty | exit]
                              ↓           ↓
                        execute_cmd   send_message
                              ↓           ↓
                           render    process_stream
                              ↓           ↓
                              └── update_session → render → [loop | END]
```

**`graph/builder_subgraph.py`** - Alternative builder with fine-grained stream processing subgraph (experimental). Replaces single `process_stream_node` with a multi-node subgraph for better separation of concerns.

### State Schema

**`graph/state.py`** - Defines `REPLState` TypedDict:

| Field | Type | Purpose |
|-------|------|---------|
| `user_input` | `str` | Raw terminal input |
| `input_type` | `Literal[...]` | Classification (command/message/empty/exit) |
| `current_thread_id` | `str \| None` | Active LangGraph thread |
| `current_assistant_id` | `str` | Active agent ID |
| `current_run_id` | `str \| None` | Current streaming run |
| `stream_chunks` | `list[dict]` | Accumulated SSE chunks |
| `stream_buffer` | `dict` | Text/tool buffers |
| `render_queue` | `list[dict]` | Items waiting to render |
| `pending_interrupt` | `dict \| None` | HITL interrupt data |
| `interrupt_approved` | `bool \| None` | User approval decision |
| `session_tokens` | `dict` | Token usage tracking |
| `should_exit` | `bool` | Exit flag |
| `error` | `str \| None` | Error message |
| `command_result` | `dict \| None` | Command execution result |

### Nodes

**`graph/nodes/`** - Each major operation implemented as a graph node:

| Node | File | Purpose |
|------|------|---------|
| `get_input_node` | `input.py` | Blocking terminal input |
| `route_input_node` | `input.py` | Classify input type |
| `execute_command_node` | `commands.py` | Handle slash commands |
| `send_message_node` | `streaming.py` | Initiate streaming to server |
| `process_stream_node` | `streaming.py` | Process SSE chunks |
| `handle_interrupt_node` | `hitl.py` | HITL approval flow |
| `update_session_node` | `rendering.py` | Update session stats |
| `render_output_node` | `rendering.py` | Render queued output |

**Conditional edge functions**: `route_decision`, `check_for_interrupt`, `check_should_exit`

### Subgraphs

**`graph/subgraphs/`** - Fine-grained stream processing (experimental):

- **`stream_processor.py`** - Builds subgraph with 10+ nodes for chunk-by-chunk processing
- **`nodes/`** - Individual processing nodes:
  - `chunk_fetcher.py` - Fetch next chunk by index
  - `chunk_parser.py` - Parse event type
  - `text_handler.py` - Extract text deltas
  - `tool_router.py` - Route by tool name
  - `tool_handlers.py` - Tool-specific rendering
  - `state_handler.py` - Process state updates

### Core Components

**`core/`** - Shared utilities:

| File | Purpose |
|------|---------|
| `client.py` | Async HTTP client for LangGraph Dev Server |
| `config.py` | Load configuration from `.env` |
| `session.py` | Session state tracking |
| `parsers.py` | SSE and chunk parsing |
| `logging.py` | Client-side logging |

### Streaming Types

**`streaming/`** - Type definitions for stream processing:

- **`types.py`** - `ParsedChunk`, `ChunkType` enum, `Interrupt`, `ToolResult`
- **`hitl.py`** - `HITLHandler` for approval prompts

### UI Rendering

**`ui/`** - Terminal output:

| File | Purpose |
|------|---------|
| `renderer.py` | Rich-based rendering |
| `content_blocks.py` | `ToolRenderRegistry`, `ContentBlockRenderer` |
| `message.py` | `MessageRenderer` |

### Dependency Injection

**`context.py`** - Context variables for injecting dependencies into nodes without explicit parameter passing:

- `get_client()` / `set_client()` - LangGraph HTTP client
- `get_renderer()` / `set_renderer()` - Terminal renderer
- `get_session()` / `set_session()` - Session state
- `get_hitl_handler()` / `set_hitl_handler()` - HITL handler
- `get_tool_registry()` / `set_tool_registry()` - Tool rendering

## Benefits of StateGraph Approach

1. **Automatic state propagation** - State flows through nodes without manual threading
2. **Visual debugging** - Generate graph visualizations with `draw_mermaid_png()`
3. **Checkpointing potential** - Built-in support for state persistence (not currently used)
4. **Structured control flow** - Explicit edges make flow clear and testable
5. **HITL support** - Natural interrupt/resume pattern via conditional edges
6. **Testability** - Individual nodes can be unit tested in isolation

## Essential Commands

```bash
# Install dependencies
make install

# Start REPL (requires running dev server)
make repl

# Run tests
make test

# Code quality
make lint
make format
make type-check

# Clean caches
make clean
```

## Environment Configuration

Create `.env` file or set environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGGRAPH_DEV_SERVER_PORT` | `2024` | Server port |
| `REPL_DEFAULT_AGENT` | `""` | Default agent/assistant ID |
| `REPL_DEBUG` | `false` | Enable debug logging |

Example `.env`:
```bash
LANGGRAPH_DEV_SERVER_PORT=2024
REPL_DEFAULT_AGENT=agent
REPL_DEBUG=true
```

## Module Structure

```
apps/repl-client-graph/
├── src/repl_client_graph/
│   ├── __init__.py
│   ├── __main__.py              # Entry point
│   ├── context.py               # Dependency injection
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── builder.py           # Main graph builder
│   │   ├── builder_subgraph.py  # Alternative with subgraph
│   │   ├── state.py             # REPLState TypedDict
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── input.py         # Input handling
│   │   │   ├── commands.py      # Slash commands
│   │   │   ├── streaming.py     # Stream processing
│   │   │   ├── streaming_subgraph.py
│   │   │   ├── hitl.py          # HITL handling
│   │   │   └── rendering.py     # Output rendering
│   │   └── subgraphs/
│   │       ├── __init__.py
│   │       ├── stream_processor.py
│   │       └── nodes/
│   │           ├── __init__.py
│   │           ├── chunk_fetcher.py
│   │           ├── chunk_parser.py
│   │           ├── text_handler.py
│   │           ├── tool_router.py
│   │           ├── tool_handlers.py
│   │           └── state_handler.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── config.py
│   │   ├── session.py
│   │   ├── parsers.py
│   │   └── logging.py
│   ├── streaming/
│   │   ├── __init__.py
│   │   ├── types.py
│   │   └── hitl.py
│   └── ui/
│       ├── __init__.py
│       ├── renderer.py
│       ├── content_blocks.py
│       └── message.py
├── tests/
│   └── repl_client_graph/
│       ├── __init__.py
│       └── test_streaming_interrupt.py
├── .env.example
├── Makefile
└── pyproject.toml
```

## Testing Strategy

### Unit Tests

Test individual nodes in isolation:

```python
# tests/repl_client_graph/test_input_node.py
from repl_client_graph.graph.nodes.input import route_input_node

def test_route_input_command():
    state = {"user_input": "/help"}
    result = route_input_node(state)
    assert result["input_type"] == "command"
```

### Integration Tests

Test full graph execution with mocked server:

```python
@pytest.mark.integration
async def test_full_message_flow():
    # Setup mocked client
    graph = build_repl_graph()
    state = {...}
    result = await graph.ainvoke(state)
    assert result["should_exit"] is False
```

### Running Tests

```bash
# All tests
make test

# Specific file
uv run pytest tests/repl_client_graph/test_streaming_interrupt.py -v

# With output
uv run pytest tests/ -v -s
```

## Available REPL Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/exit` | Quit the REPL |
| `/agents` | List available agents |
| `/threads` | List/resume threads |
| `/new` | Create new thread |
| `/info` | Show session info |
| `/clear` | Clear screen |
| `/session` | Session details |

## Design Decisions

### Coarse-Grained Streaming

Stream processing uses a single node (`process_stream_node`) that collects all SSE chunks before processing. This avoids per-chunk graph overhead while maintaining the StateGraph benefits for overall control flow.

### Stateless Client

The server owns conversation history (threads, checkpoints). The client just displays and coordinates. No local persistence by design.

### Context Variables for DI

Dependencies (client, renderer, session) are injected via Python context variables rather than being included in state. This keeps state focused on data flow while allowing nodes to access shared resources.

## Dependencies

**Runtime:**
- `langgraph` - StateGraph and graph execution
- `httpx` - Async HTTP client for SSE streaming
- `rich` - Terminal rendering
- `python-dotenv` - Configuration loading
- `pydantic-settings` - Settings management

**Development:**
- `pytest`, `pytest-asyncio` - Testing
- `ruff` - Linting and formatting
- `ty` - Type checking
