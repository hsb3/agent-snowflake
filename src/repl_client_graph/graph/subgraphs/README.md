# Stream Processing Subgraph

This directory contains a fine-grained subgraph implementation for processing streaming chunks from the LangGraph server.

## Overview

This is a proof-of-concept demonstrating an alternative architecture to the single-node `process_stream_node` approach. Instead of processing all chunks in one node with internal loops and conditionals, this subgraph breaks down stream processing into multiple focused nodes with explicit control flow managed by the graph.

## Architecture Comparison

### Coarse-Grained Approach (Current)
```
[process_stream_node]
  ├─ for chunk in chunks:
  │   ├─ if event_type == "messages/partial": extract_text()
  │   ├─ if event_type == "messages/complete": extract_tools()
  │   ├─ if event_type == "updates": check_interrupt()
  │   └─ render_queue.append(...)
  └─ return state
```

**Characteristics:**
- Single large node with internal control flow
- Loop and conditionals embedded in node logic
- Fast execution, minimal graph overhead
- Harder to visualize flow, test individual steps

### Fine-Grained Approach (This Subgraph)
```
[fetch_chunk] → [parse_chunk] → {route_by_event_type}
                                   ├─ messages/partial → [extract_text] → loop
                                   ├─ messages/complete → [extract_tools] → {route_by_tool}
                                   │                                          ├─ sql → [render_sql_tool]
                                   │                                          ├─ question → [render_question_tool]
                                   │                                          └─ generic → [render_generic_tool]
                                   └─ updates → [process_updates] → [detect_interrupt] → loop or exit
```

**Characteristics:**
- Multiple small nodes, each with single responsibility
- Control flow via graph edges (conditional and direct)
- Graph manages iteration and routing
- Better visibility, easier testing, clearer flow
- Slight overhead from graph execution

## Components

### State Definition
**File:** `stream_processor.py`

```python
class StreamSubgraphState(TypedDict):
    # Input from parent
    stream_chunks: list[tuple[str, dict]]

    # Processing state
    chunk_index: int
    current_chunk: tuple[str, dict] | None
    prev_text: str

    # Output accumulation
    render_queue: list[dict]
    pending_interrupt: dict | None
    usage: dict | None

    # Control
    is_complete: bool
```

### Node Modules

#### 1. Chunk Fetcher (`nodes/chunk_fetcher.py`)
- **fetch_next_chunk_node**: Get next chunk by index, increment counter
- **check_has_more_chunks**: Conditional edge to continue or exit loop

#### 2. Chunk Parser (`nodes/chunk_parser.py`)
- **parse_chunk_type_node**: Extract event type from chunk
- **route_by_event_type**: Route to appropriate handler based on event type

#### 3. Text Handler (`nodes/text_handler.py`)
- **extract_text_delta_node**: Extract text delta from cumulative stream

#### 4. Tool Router (`nodes/tool_router.py`)
- **extract_tools_node**: Extract tool calls and usage from complete message
- **route_by_tool_name**: Route to tool-specific renderer

#### 5. Tool Handlers (`nodes/tool_handlers.py`)
- **render_sql_tool_node**: Format SQL queries with syntax highlighting info
- **render_question_tool_node**: Format AskUserQuestion prompts
- **render_generic_tool_node**: Fallback for unknown tools

#### 6. State Handler (`nodes/state_handler.py`)
- **process_updates_node**: Add state updates to render queue
- **detect_interrupt_node**: Detect __interrupt__ signal, exit subgraph

## Control Flow

### Main Loop
1. **fetch_chunk**: Get next chunk from list
2. **parse_chunk**: Prepare for routing
3. **route_by_event_type**: Branch based on SSE event type
4. **Process chunk**: Event-specific handling
5. **Check continuation**: More chunks? Loop back. Interrupt? Exit.

### Event-Specific Flows

#### messages/partial
```
[parse_chunk] → [extract_text] → {check_has_more} → [fetch_chunk] (loop)
```
- Extract text delta
- Add to render_queue
- Continue to next chunk

#### messages/complete
```
[parse_chunk] → [extract_tools] → {route_by_tool} → [render_*_tool] → {check_has_more}
```
- Extract tool calls and usage
- Route to tool-specific renderer
- Add formatted tool to render_queue
- Continue to next chunk

#### updates
```
[parse_chunk] → [process_updates] → [detect_interrupt] → {interrupt or continue}
```
- Add state update to render_queue
- Check for __interrupt__
- If interrupt: Exit immediately
- Else: Continue to next chunk

## Integration with Parent Graph

### Current Pattern (Coarse-Grained)
```python
# In builder.py
from .nodes import process_stream_node

graph.add_node("process_stream", process_stream_node)
graph.add_edge("send_message", "process_stream")
```

### Subgraph Pattern (Fine-Grained)
```python
# In builder.py
from repl_client_graph.graph.subgraphs import build_stream_processor_subgraph

# Build subgraph
stream_processor = build_stream_processor_subgraph()

# Add as a node
graph.add_node("process_stream", stream_processor)
graph.add_edge("send_message", "process_stream")
```

The parent graph doesn't need to know about the internal structure of the subgraph. It just passes `stream_chunks` in the state and receives `render_queue`, `pending_interrupt`, and `usage` back.

## Usage Example

```python
from repl_client_graph.graph.subgraphs import build_stream_processor_subgraph

# Build and compile subgraph
subgraph = build_stream_processor_subgraph()

# Execute with state
result = subgraph.invoke({
    "stream_chunks": [
        ("messages/partial", [{"content": [{"type": "text", "text": "Hello"}]}]),
        ("messages/partial", [{"content": [{"type": "text", "text": "Hello, world"}]}]),
        ("messages/complete", [{"content": [], "tool_calls": [...], "usage_metadata": {...}}]),
    ],
    "chunk_index": 0,
    "prev_text": "",
    "render_queue": [],
    "pending_interrupt": None,
    "usage": None,
    "is_complete": False,
})

# Result contains:
# - render_queue: List of items to render
# - pending_interrupt: Interrupt object if HITL triggered
# - usage: Token usage from final chunk
```

## Design Trade-offs

### Advantages of Fine-Grained Approach
1. **Visibility**: Graph visualization shows exact flow
2. **Testability**: Each node can be tested in isolation
3. **Debuggability**: Can inspect state between each step
4. **Maintainability**: Easy to add new event types or tool handlers
5. **Clarity**: Control flow is explicit in graph structure

### Disadvantages
1. **Performance**: More graph overhead vs. single node loop
2. **Complexity**: More files and components to manage
3. **State size**: State must be serializable for graph execution
4. **Learning curve**: Requires understanding subgraph patterns

## When to Use Each Approach

### Use Coarse-Grained (Single Node)
- Performance is critical
- Flow is simple and unlikely to change
- Team prefers traditional imperative code
- Debugging via logging is sufficient

### Use Fine-Grained (Subgraph)
- Flow needs to be visible/documented
- Individual steps need isolated testing
- Team wants to leverage LangGraph features
- Flow may evolve with new event types

## Future Enhancements

### Possible Extensions
1. **Parallel processing**: Process independent chunks in parallel
2. **Conditional rendering**: Skip certain render items based on state
3. **Buffering strategies**: Accumulate multiple text deltas before rendering
4. **Error recovery**: Handle parse errors with retry logic
5. **Metrics collection**: Track timing for each node

### Integration with HITL
The subgraph is designed to work with the HITL handler:
```python
# After subgraph execution
if result["pending_interrupt"]:
    # Show approval prompt
    approved = hitl_handler.handle_interrupt(result["pending_interrupt"])

    # Resume streaming with approval
    # (not implemented in this POC)
```

## Testing

See `tests/repl_client_graph/` for examples of testing the subgraph.

Key test scenarios:
- Text delta extraction with multiple partial chunks
- Tool call routing to correct handler
- Interrupt detection causes immediate exit
- Empty/malformed chunks handled gracefully
- Usage metadata extracted from final chunk

## Conclusion

This subgraph demonstrates that fine-grained decomposition is possible and beneficial for certain use cases. The choice between coarse and fine-grained approaches depends on project priorities:

- **Coarse**: Performance, simplicity
- **Fine**: Visibility, testability, maintainability

Both approaches are valid and can coexist in the same project for different components.
