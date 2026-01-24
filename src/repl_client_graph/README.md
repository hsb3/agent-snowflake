# REPL Client StateGraph

This package implements the REPL as a LangGraph StateGraph, providing structured state management, control flow orchestration, and built-in support for debugging and checkpointing.

## Architecture

Based on **Approach 1 (Coarse-Grained)** from `docs/dev_docs/repl_as_stategraph.md`:

- Major operations implemented as graph nodes
- Streaming handled within a single node (efficient)
- Control flow managed via conditional edges
- HITL interrupts as dedicated routing path

## Core Components

### State (`graph/state.py`)

`REPLState` TypedDict with all fields needed for REPL execution:
- Input/routing state
- Session context (thread, agent, run IDs)
- Streaming state (chunks, buffers)
- Render queue
- HITL interrupt state
- Session statistics
- Control flow flags

### Graph Builder (`graph/builder.py`)

`build_repl_graph()` creates the StateGraph with:

**Nodes:**
1. `get_input` - Blocking terminal input
2. `route_input` - Classify input type
3. `execute_command` - Handle slash commands
4. `send_message` - Initiate streaming
5. `process_stream` - Process SSE chunks
6. `handle_interrupt` - HITL approval
7. `update_session` - Update stats
8. `render_output` - Render queued output

**Flow:**
```
get_input -> route_input -> [command|message|empty|exit]
                             |        |        |      |
                             v        v        |      v
                         execute  send_msg     |     END
                             |        |        |
                             v        v        |
                         render   process -----+
                                      |
                                  [interrupt|complete]
                                      |        |
                                      v        v
                                  handle   update
                                      |        |
                                      +-> process
                                             |
                                             v
                                          render
                                             |
                                    [continue|exit]
                                             |      |
                                             v      v
                                         get_input END
```

## Usage

```python
from repl_client_graph import build_repl_graph, REPLState

# Build graph
graph = build_repl_graph()

# Create initial state
initial_state: REPLState = {
    "user_input": "",
    "current_assistant_id": "agent_enhanced",
    "should_exit": False,
    "message_count": 0,
    # ... other fields as needed
}

# Run graph (loops until should_exit=True)
final_state = graph.invoke(initial_state)
```

## Node Implementation Status

Currently all nodes have **stub implementations**. They need to be replaced with actual logic:

- [ ] `get_input_node` - Implement terminal input (prompt-toolkit or input())
- [ ] `execute_command_node` - Integrate with command registry
- [ ] `send_message_node` - Integrate with LangGraphClient
- [ ] `process_stream_node` - Integrate with StreamHandler
- [ ] `handle_interrupt_node` - Implement HITL approval flow
- [ ] `update_session_node` - Implement session tracking
- [ ] `render_output_node` - Integrate with Renderer

## Design Benefits

1. **State Management**: Automatic propagation, no manual threading
2. **Debugging**: Visual graph execution, state snapshots at each node
3. **Testing**: Inject state, run specific nodes in isolation
4. **Replay**: Re-run sessions from checkpoints
5. **Interrupts**: Native HITL support
6. **Observability**: Built-in execution traces

## Performance

Minimal overhead:
- Only 8-10 node invocations per user message
- Streaming chunks processed efficiently in single node
- No unnecessary graph traversal

## Next Steps

1. Implement node functions (integrate with existing REPL components)
2. Add dependency injection for client/renderer
3. Wire up to actual entry point
4. Add execution tracing/logging
5. Implement checkpoint persistence (optional)

## References

- Design Doc: `docs/dev_docs/repl_as_stategraph.md`
- REPL Spec: `repl_spec.json`
- Component List: `repl_components.jsonc`
