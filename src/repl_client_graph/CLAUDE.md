# CLAUDE.md - StateGraph REPL Client

This file provides guidance for working on the **StateGraph-based REPL client** (`repl_client_graph`).

## Project Overview

**What this is:** Terminal REPL client for LangGraph Dev Server REST API, implemented using LangGraph StateGraph for control flow.

**What it's NOT:** Not an agent builder - just a client for interacting with existing LangGraph agents.

**Design Philosophy:** Use StateGraph to manage REPL control flow with automatic state management, built-in observability, and natural HITL support.

## Quick Start

```bash
# Run the StateGraph REPL
make repl-graph

# Or manually (two terminals)
make dev-server              # Terminal 1: Start LangGraph server
uv run python -m repl_client_graph  # Terminal 2: Start REPL

# Available commands in REPL
/help      # Show all commands
/agents    # List/switch agents
/threads   # List/resume threads
/new       # Create new thread
/info      # Session info
/exit      # Quit
```

## Architecture

### StateGraph Structure

**Main Graph** (10 nodes, 14 edges):
```
get_input → route_input → [command OR message]
                             ↓         ↓
                       execute_cmd  send_message
                             ↓         ↓
                          render   process_stream → [interrupt?]
                             ↓         ↓              ↓
                             └── update_session  handle_interrupt
                                     ↓              ↓
                                  render         (resume)
                                     ↓
                                [loop OR exit]
```

**Conditional Routing Points:**
1. `route_input` → 4 routes (command/message/empty/exit)
2. `process_stream` → 2 routes (interrupt/complete)
3. `render_output` → 2 routes (continue/exit)

### Key Design Decisions

**State Management:**
- Single `REPLState` TypedDict flows through all nodes
- Automatic propagation via StateGraph
- Each node receives state, updates it, returns modified state

**Dependency Injection:**
- Context vars for client, renderer, session, HITL handler, tool registry
- Avoids polluting state with dependencies
- Easy to mock for testing

**Streaming Strategy:**
- Dual mode: `["messages", "updates"]` for LLM tokens + state changes
- Coarse-grained: Collect all SSE chunks, then process in one node
- Natural buffering avoids per-chunk graph overhead

**HITL Support:**
- Server-side interrupts, client detects and coordinates UI
- Approval prompts via `HITLHandler`
- Resume streaming after approval/rejection

**Stateless Client:**
- Server owns conversation history (threads, checkpoints)
- Client just displays and coordinates
- No local persistence (by design)

## File Organization

```
src/repl_client_graph/
├── __main__.py              # Entry point, initializes graph
├── context.py               # Dependency injection via context vars
├── graph/
│   ├── builder.py          # Main graph builder (single-node streaming) ✅ ACTIVE
│   ├── builder_subgraph.py # Alternative with fine-grained subgraph (WIP)
│   ├── state.py            # REPLState TypedDict definition
│   ├── nodes/              # Graph node implementations
│   │   ├── input.py        # get_input, route_input
│   │   ├── commands.py     # execute_command (all 9 commands)
│   │   ├── streaming.py    # send_message, process_stream (single node)
│   │   ├── streaming_subgraph.py # Subgraph nodes (alternative, WIP)
│   │   ├── hitl.py         # handle_interrupt
│   │   └── rendering.py    # render_output, update_session
│   └── subgraphs/          # Fine-grained stream processing (PoC, WIP)
│       └── stream_processor.py  # 15+ nodes for chunk/tool handling
├── core/                    # Shared with repl_client
│   ├── client.py           # LangGraph HTTP client (async)
│   ├── config.py           # Load from .env
│   ├── parsers.py          # SSE/chunk parsing
│   ├── session.py          # SessionState tracking
│   └── logging.py          # Client-side logging
├── streaming/
│   ├── types.py            # ParsedChunk, ChunkType, Interrupt types
│   └── hitl.py             # HITLHandler for approval prompts
└── ui/
    ├── renderer.py         # Rich-based rendering
    ├── content_blocks.py   # ToolRenderRegistry, ContentBlockRenderer
    └── message.py          # MessageRenderer
```

## Current Implementation Status

### ✅ Complete (Phase 1 & 2)

**Commands (9 total):**
- `/help`, `/exit` - Basic
- `/agents`, `/threads`, `/new` - Management
- `/info`, `/clear`, `/session` - Info/debug

**Streaming:**
- Dual mode (messages + updates)
- Real-time LLM token streaming
- State change tracking
- Text delta extraction

**Infrastructure:**
- HITL detection in updates stream
- Approval prompts ready
- Tool rendering registry
- Agent name caching

### 🚧 In Progress

**Bugs:**
- Token tracking shows 0 (usage_metadata not flowing correctly)
- State updates too verbose (need config flag)

**Subgraph PoC:**
- Built and tested standalone ✅
- Integration produces 0 output (needs debugging)
- Temporarily using single-node approach

### ⏳ Planned (Phase 3)

- Enhanced input (prompt-toolkit)
- Command completion
- Status bar
- Session persistence

## Specifications & Documentation

### Design Specs (Read First)
- **Architecture:** `docs/dev_docs/repl_data_flow.md` - Data/control flow diagrams
- **StateGraph Design:** `docs/dev_docs/spec-repl-graph-v1/repl_as_stategraph.md` - Why StateGraph, design rationale
- **Components:** `repl_components.jsonc` - Layered architecture
- **Requirements:** `repl_spec.json` - Feature specs and acceptance criteria

### Implementation Docs
- **Phase 1:** `docs/dev_docs/ai_docs/ai_gen/*/repl_layer8_completed.md`
- **Phase 2:** `docs/dev_docs/phase2_implementation_complete.md`
- **Subgraph PoC:** `docs/dev_docs/stream_subgraph_poc.md`
- **TODO List:** `docs/dev_docs/GRAPH_REPL_TODO.md`

### Quick Reference
- **Quickstart:** `docs/QUICKSTART_REPL_GRAPH.md`
- **Summary:** `docs/dev_docs/spec-repl-graph-v1/repl_client_graph_summary.md`

## Work Documentation Guidelines

When creating work documentation for this subproject:

**Location:** `docs/dev_docs/ai_docs/ai_gen/YYYY-MM-DD-{type}-{description}.md`

**Frontmatter (Required):**
```yaml
---
doc_id: CC-YYYY-NNN
title: Brief description
date: YYYY-MM-DD
type: planning|solution|investigation|status|summary
project: repl_client_graph
focus: graph-based-repl
status: draft|complete
tags: [stategraph, repl, phase-N, ...]
---
```

**Document Types:**
- `planning` - Before implementing complex features
- `solution` - After solving problems
- `investigation` - Research, comparisons, analysis
- `status` - Progress updates
- `summary` - Milestone completions

**Example:**
```yaml
---
doc_id: CC-2026-042
title: "Phase 3 Enhanced Input Implementation"
date: 2026-01-24
type: planning
project: repl_client_graph
focus: graph-based-repl
status: draft
tags: [stategraph, repl, phase-3, prompt-toolkit]
---
```

## Common Development Tasks

### Adding a New Command

1. **Add handler in `graph/nodes/commands.py`:**
   ```python
   async def execute_command_node(state: REPLState) -> REPLState:
       # ...
       elif command == "mycommand":
           # Logic here
           return {**state, "render_queue": [...]}
   ```

2. **Update help text** in same function

3. **Test:** `echo "/mycommand" | uv run python -m repl_client_graph`

### Adding a New Tool Renderer (Future - Subgraph)

1. **Add node in `graph/subgraphs/nodes/tool_handlers.py`:**
   ```python
   def render_my_tool_node(state: dict) -> dict:
       tool = state.get("current_tool", {})
       # Format for render_queue
       return {**state, "render_queue": [...]}
   ```

2. **Register in `graph/subgraphs/stream_processor.py`:**
   ```python
   graph.add_node("render_my_tool", render_my_tool_node)
   # Add to conditional routing
   ```

3. **Add render type in `graph/nodes/rendering.py`**

### Modifying State Schema

1. **Update `graph/state.py`:**
   ```python
   class REPLState(TypedDict, total=False):
       # ... existing fields
       my_new_field: str
   ```

2. **Initialize in `__main__.py`:**
   ```python
   initial_state = {
       # ... existing
       "my_new_field": "default",
   }
   ```

3. **Use in nodes:** Access via `state.get("my_new_field")`

### Testing a Node

```python
# tests/repl_client_graph/test_my_node.py
from repl_client_graph.graph.nodes.my_module import my_node

def test_my_node():
    state = {"user_input": "test"}
    result = my_node(state)
    assert result["some_field"] == expected
```

### Visualizing the Graph

```bash
# Generate PNG and Mermaid diagram
make visualize-graph

# Or manually
uv run python scripts/visualize_stategraph.py repl_client_graph:build_repl_graph
```

## Debugging

### Enable Debug Mode

```bash
# Set in .env
REPL_DEBUG=true

# Or inline
REPL_DEBUG=true uv run python -m repl_client_graph
```

### Check Logs

```bash
# Client logs
cat .repl/client.log

# Server logs (when using make commands)
tail -f .repl/server.log
```

### Graph Execution Traces

```python
# In __main__.py (development only)
for step in repl_graph.get_trace():
    print(f"Node: {step.node_name}, Duration: {step.duration_ms}ms")
```

### Common Issues

**Server connection failed:**
- Check server is running: `curl http://localhost:2024/ok`
- Start server: `make dev-server`
- Check port in `.env`: `LANGGRAPH_DEV_SERVER_PORT`

**Agent not found:**
- List agents: `curl -X POST http://localhost:2024/assistants/search -d '{"limit": 10}'`
- Check `langgraph.json` has agent definitions

**Streaming not working:**
- Check `stream_mode` in `client.py` (should be `["messages", "updates"]`)
- Verify SSE parsing in `process_stream_node`
- Check render_queue is populated

## Performance Considerations

**Current Performance:**
- Single-node stream processing: ~0.01ms per message
- Graph overhead: ~10 invocations per user message
- Total latency: < 1ms (imperceptible)

**Subgraph Approach (When Migrated):**
- Fine-grained: ~30-45ms per message
- More invocations: 64-320 per message
- Still < 2% of LLM wait time (acceptable)

## Comparison to Classic REPL

| Feature | repl_client (Classic) | repl_client_graph (StateGraph) |
|---------|----------------------|--------------------------------|
| Control flow | Imperative loop | StateGraph declarative |
| State | Manual threading | Automatic propagation |
| Testing | Integration-heavy | Unit-testable nodes |
| Observability | Manual logging | Built-in traces |
| Complexity | Lower | Slightly higher |
| Maintainability | Good | Better (structured) |
| HITL | Custom logic | Native graph interrupts |

**Use StateGraph REPL when:** Better structure, testability, and observability matter more than simplicity.

## Important Notes

### Do NOT Add Checkpointer

The REPL graph is **ephemeral** - each user message is one complete graph invocation. No need for checkpointing because:
- Client is stateless by design
- Server manages conversation history
- Each invocation is atomic
- HITL checkpoints belong on server

### Streaming is Coarse-Grained

We intentionally process entire stream in single node (not per-chunk) to avoid overhead:
- Collect all SSE chunks in `send_message_node`
- Process all at once in `process_stream_node`
- Only ~1 graph invocation (not 100+)

Subgraph approach is for **tool/UI routing**, not chunk iteration.

### Commands Use Context Mutations

Commands directly mutate session state (via context vars):
```python
session = get_session()
session.set_agent(agent_id)  # Direct mutation OK
```

This is acceptable because:
- Session is injected, not in graph state
- Mutations are side effects
- State dict tracks "what happened" for routing

## Dependencies

**Required:**
- `langgraph` - StateGraph and graph execution
- `httpx` - Async HTTP client for SSE streaming
- `rich` - Terminal rendering
- `python-dotenv` - Config loading

**Optional (Phase 3):**
- `prompt-toolkit` - Enhanced input

## Related Files

**Specs:** `docs/dev_docs/spec-repl-graph-v1/`
**Work Docs:** `docs/dev_docs/ai_docs/ai_gen/` (with `project: repl_client_graph` in frontmatter)
**TODO:** `docs/dev_docs/GRAPH_REPL_TODO.md`
**Comparison:** Classic REPL at `src/repl_client/`

## Next Steps

See `docs/dev_docs/GRAPH_REPL_TODO.md` for complete task list.

**Immediate priorities:**
1. Fix token tracking (usage_metadata flow)
2. Test HITL end-to-end
3. Quiet state update messages

**Phase 3:**
1. Enhanced input (prompt-toolkit)
2. Command completion
3. Status bar

**Future:**
1. Debug subgraph integration
2. Migrate to fine-grained tool routing
3. Add 20+ tool-specific renderers
