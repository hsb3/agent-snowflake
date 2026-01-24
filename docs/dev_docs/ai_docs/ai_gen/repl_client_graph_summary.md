# StateGraph-Based REPL Implementation Summary

## Overview

Successfully built a StateGraph-based REPL client in `src/repl_client_graph/` using LangGraph's StateGraph for control flow management. This implementation follows the **Coarse-Grained approach (Approach 1)** from the design document.

## Architecture

### Directory Structure

```
src/repl_client_graph/
├── __init__.py              # Package exports
├── __main__.py              # Entry point (python -m repl_client_graph)
├── context.py               # Dependency injection via context vars
├── README.md                # Comprehensive documentation
├── core/                    # Core components (copied from repl_client)
│   ├── client.py           # LangGraph HTTP client (async)
│   ├── config.py           # Configuration from .env
│   ├── logging.py          # Client-side logging
│   ├── parsers.py          # SSE/chunk parsers
│   └── session.py          # SessionState tracking
├── graph/                   # StateGraph infrastructure
│   ├── builder.py          # build_repl_graph() implementation
│   ├── state.py            # REPLState TypedDict
│   └── nodes/              # Graph node implementations
│       ├── input.py        # get_input, route_input nodes
│       ├── commands.py     # execute_command node
│       ├── streaming.py    # send_message, process_stream nodes
│       ├── rendering.py    # render_output, update_session nodes
│       └── hitl.py         # handle_interrupt node (Phase 2 stub)
├── streaming/              # Streaming types
│   └── types.py           # ParsedChunk, ChunkType enums
└── ui/                     # Terminal rendering
    └── renderer.py        # Rich-based output
```

## Key Components

### 1. StateGraph Structure

**9 nodes in the graph:**
1. `get_input` - Blocking terminal input
2. `route_input` - Classify input (command/message/empty/exit)
3. `execute_command` - Handle slash commands
4. `send_message` - Initiate streaming to LangGraph server
5. `process_stream` - Process all SSE chunks in one pass
6. `handle_interrupt` - HITL approval flow (Phase 2)
7. `update_session` - Track tokens and message count
8. `render_output` - Render queued output
9. Loop back to `get_input` or exit

**Control flow:**
```
get_input → route_input → [command OR message OR empty OR exit]
                             ↓        ↓         ↓        ↓
                       exec_cmd   send_msg   loop     END
                             ↓        ↓
                          render  process_stream → [interrupt?]
                             ↓        ↓              ↓
                             └── update_session  handle_interrupt
                                     ↓              ↓
                                  render         loop back
                                     ↓
                                [continue OR exit]
```

### 2. State Management

**REPLState TypedDict** (`graph/state.py`) contains:
- **Input**: `user_input`, `input_type`
- **Session**: `current_thread_id`, `current_assistant_id`, `current_run_id`
- **Streaming**: `stream_chunks`, `stream_buffer`
- **Rendering**: `render_queue`
- **HITL**: `pending_interrupt`, `interrupt_approved`
- **Stats**: `session_tokens`, `message_count`, `session_start_time`
- **Control**: `should_exit`, `error`, `command_result`

State flows through nodes automatically - each node receives state, updates it, and returns modified state.

### 3. Dependency Injection

**Context variables** (`context.py`) provide:
- `get_client()` / `set_client()` - LangGraphClient
- `get_renderer()` / `set_renderer()` - Renderer
- `get_session()` / `set_session()` - SessionState

Nodes access dependencies without polluting state:
```python
def some_node(state: REPLState) -> REPLState:
    client = get_client()  # Access via context
    # ... do work
    return {**state, "updated_field": value}
```

### 4. Node Implementation Pattern

All nodes follow this pattern:
```python
def node_name(state: REPLState) -> REPLState:
    """Docstring explaining what this node does."""
    # 1. Get dependencies from context
    client = get_client()
    renderer = get_renderer()

    # 2. Extract needed state
    user_input = state["user_input"]

    # 3. Do work
    result = process(user_input)

    # 4. Return updated state
    return {**state, "some_field": result}
```

### 5. Conditional Edges

Three routing functions:
- `route_decision(state)` → "command" | "message" | "empty" | "exit"
- `check_for_interrupt(state)` → "interrupt" | "complete"
- `check_should_exit(state)` → "continue" | "exit"

## Benefits Over Traditional Loop

### 1. **Automatic State Management**
- No manual state threading
- Type-safe state propagation
- Single source of truth (REPLState)

### 2. **Visual Architecture**
- Graph IS the documentation
- Can visualize execution flow
- Clear control flow routing

### 3. **Observability**
- Built-in execution traces
- State snapshots at each node
- Easy debugging

### 4. **Testability**
- Test nodes in isolation
- Inject state, verify output
- Mock context vars

### 5. **Natural HITL**
- Interrupt handling is native to LangGraph
- Checkpoint/resume built-in
- State preserved across interrupts

### 6. **Low Overhead**
- Only 8-10 node invocations per user message
- Streaming handled efficiently in single node
- No per-chunk graph traversal

## Running the REPL

### Prerequisites
```bash
# Install dependencies
uv add langgraph

# Start LangGraph dev server
langgraph dev
# or
make dev
```

### Run REPL
```bash
# From project root
uv run python -m repl_client_graph

# Or with explicit PYTHONPATH
PYTHONPATH=src uv run python -m repl_client_graph
```

### Expected Flow
1. Loads config from `.env`
2. Connects to LangGraph server (localhost:2024)
3. Lists agents, sets default
4. Creates initial thread
5. Shows welcome banner
6. Enters REPL loop (graph execution)
7. On exit, shows session summary

## Implementation Status

### ✅ Completed (Phase 1)

**Infrastructure:**
- [x] StateGraph builder
- [x] REPLState definition
- [x] Dependency injection via context vars
- [x] Entry point (`__main__.py`)
- [x] All node functions implemented
- [x] Conditional edge functions
- [x] Graph compiles successfully

**Core Components (copied from repl_client):**
- [x] Config loading
- [x] LangGraph HTTP client
- [x] SSE/chunk parsers
- [x] Rich renderer
- [x] SessionState tracking
- [x] Logging setup

**Nodes:**
- [x] get_input_node - terminal input
- [x] route_input_node - classify input
- [x] execute_command_node - /help, /exit
- [x] send_message_node - initiate streaming
- [x] process_stream_node - parse all chunks
- [x] render_output_node - display output
- [x] update_session_node - track stats

### 🚧 Phase 2 (Planned)

**Features:**
- [ ] HITL interrupt handling (handle_interrupt_node)
- [ ] Additional commands (/agents, /threads, /new, /info)
- [ ] Tool rendering registry
- [ ] Dual stream mode (messages + updates)

### 📋 Phase 3 (Future)

**Enhancements:**
- [ ] prompt-toolkit for enhanced input
- [ ] Command completion
- [ ] Status bar
- [ ] Session persistence/replay

## Design Decisions

### Why Coarse-Grained Nodes?

**Pros:**
- Simple graph structure (9 nodes vs thousands)
- Streaming handled efficiently in one node
- Low overhead (~10 invocations per message)
- Easy to understand and debug

**Cons:**
- Less granular observability
- Can't checkpoint mid-stream

**Verdict:** Perfect fit for REPL use case

### Why Context Vars?

**Alternative:** Pass client/renderer through state

**Chosen:** Context variables

**Rationale:**
- Keeps state focused on data, not dependencies
- Cleaner node signatures
- Set once, use everywhere
- Easy to test (mock context vars)

### Why StateGraph vs Traditional Loop?

**Traditional loop pros:**
- Simpler
- Less abstraction
- Familiar pattern

**StateGraph pros:**
- Automatic state management
- Built-in observability
- Natural HITL support
- Better testability
- Visual documentation

**Verdict:** StateGraph overhead is worth the benefits

## Comparison with repl_client

| Feature | repl_client | repl_client_graph |
|---------|-------------|-------------------|
| Control flow | Manual loop | StateGraph |
| State management | Manual threading | Automatic |
| Input routing | if/else | Conditional edges |
| Observability | Manual logging | Built-in traces |
| HITL | Custom logic | Native support |
| Testing | Integration-heavy | Unit-testable nodes |
| Complexity | Lower | Slightly higher |
| Maintainability | Good | Better |

## Files Copied from repl_client

These were stable enough to reuse:
- `core/config.py` - No changes needed
- `core/client.py` - Import updates only
- `core/parsers.py` - No changes needed
- `core/logging.py` - Logger name updated
- `streaming/types.py` - Import updates only
- `ui/renderer.py` - No changes needed

## Next Steps

1. **Test with running server**: Verify end-to-end flow
2. **Implement Phase 2 features**: HITL, agent/thread management
3. **Add execution tracing**: Leverage StateGraph observability
4. **Create test suite**: Unit tests for nodes, integration tests for graph
5. **Performance benchmark**: Compare with traditional loop
6. **Documentation**: Add mermaid diagram of actual graph

## Key Insights

### StateGraph is Perfect for DAG Control Flow
- REPL was already a DAG conceptually
- StateGraph formalizes and enforces this
- Visual representation matches mental model

### Coarse-Grained Wins for Performance
- Fine-grained (per-chunk nodes) would be too slow
- Coarse-grained (per-operation nodes) is optimal
- Get benefits of StateGraph without overhead

### Context Vars Clean Up State
- State should be data, not dependencies
- Context vars keep concerns separated
- Easy to mock for testing

### HITL Becomes Trivial
- LangGraph's native interrupts handle it
- No custom checkpoint/resume logic needed
- State automatically preserved

## References

- Design doc: `docs/dev_docs/repl_as_stategraph.md`
- Data flow: `docs/dev_docs/repl_data_flow.md`
- Spec: `repl_spec.json`
- Components: `repl_components.jsonc`
