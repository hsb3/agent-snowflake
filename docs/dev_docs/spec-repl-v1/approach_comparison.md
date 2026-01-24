# Stream Processing: Coarse vs Fine-Grained Comparison

## Overview

This document compares two architectural approaches for stream processing in the REPL client:

1. **Coarse-Grained**: Single `process_stream_node` with internal loops
2. **Fine-Grained**: Subgraph with multiple focused nodes

## Implementation Details

### Coarse-Grained Approach

**Location:** `src/repl_client_graph/graph/nodes/streaming.py`

**Structure:**
```python
def process_stream_node(state: REPLState) -> REPLState:
    chunks = state.get("stream_chunks", [])
    render_queue = []
    prev_text = ""

    for event_type, data in chunks:
        if event_type == "messages/partial":
            # Extract text delta inline
            # Add to render_queue
        elif event_type == "messages/complete":
            # Extract tool calls inline
            # Add to render_queue
        elif event_type == "updates":
            # Check for interrupt inline
            # Break if found

    return {"render_queue": render_queue, ...}
```

**Characteristics:**
- ~100 lines in single function
- Internal control flow (loops, conditionals)
- Fast execution
- Harder to visualize

### Fine-Grained Approach

**Location:** `src/repl_client_graph/graph/subgraphs/stream_processor.py`

**Structure:**
```python
# Separate files for each concern
nodes/chunk_fetcher.py      # Get next chunk
nodes/chunk_parser.py       # Route by event type
nodes/text_handler.py       # Extract text delta
nodes/tool_router.py        # Route by tool name
nodes/tool_handlers.py      # Render SQL/Question/Generic
nodes/state_handler.py      # Detect interrupt

# Subgraph stitches them together
def build_stream_processor_subgraph():
    graph = StateGraph(StreamSubgraphState)
    # Add nodes
    # Add edges (conditional and direct)
    return graph.compile()
```

**Characteristics:**
- 6 files, ~400 lines total
- Explicit control flow via edges
- Graph-managed iteration
- Better visibility and testing

## Code Comparison

### Text Delta Extraction

#### Coarse-Grained
```python
# Inside process_stream_node loop
if event_type == "messages/partial":
    if isinstance(data, list) and data:
        message = data[-1]
        content = message.get("content", [])
        for block in content:
            if block.get("type") == "text":
                current_text = block.get("text", "")
                delta = current_text[len(prev_text):]
                if delta:
                    render_queue.append({"type": "text", "content": delta})
                prev_text = current_text
```

#### Fine-Grained
```python
# In nodes/text_handler.py
def extract_text_delta_node(state):
    current_chunk = state.get("current_chunk")
    prev_text = state.get("prev_text", "")
    render_queue = list(state.get("render_queue", []))

    event_type, data = current_chunk
    # ... extract text ...
    delta = current_text[len(prev_text):]
    if delta:
        render_queue.append({"type": "text", "content": delta})

    return {"render_queue": render_queue, "prev_text": current_text}

# In stream_processor.py
graph.add_conditional_edges(
    "parse_chunk",
    route_by_event_type,
    {"messages/partial": "extract_text", ...}
)
```

### Tool Call Handling

#### Coarse-Grained
```python
# Inside process_stream_node loop
if event_type == "messages/complete":
    tool_calls = message.get("tool_calls", [])
    if tool_calls:
        for tool_call in tool_calls:
            render_queue.append({"type": "tool_call", "tool": tool_call})
```

#### Fine-Grained
```python
# In nodes/tool_router.py
def route_by_tool_name(state):
    # Extract first tool name
    if tool_name == "sql_db_query":
        return "sql_db_query"
    elif tool_name == "AskUserQuestion":
        return "AskUserQuestion"
    else:
        return "generic"

# In nodes/tool_handlers.py
def render_sql_tool_node(state):
    # Format SQL with syntax highlighting info
    render_queue.append({
        "type": "tool_call",
        "tool": {
            "name": tool_name,
            "display": {"format": "sql", "query": query}
        }
    })
    return {"render_queue": render_queue}

# In stream_processor.py
graph.add_conditional_edges(
    "extract_tools",
    route_by_tool_name,
    {
        "sql_db_query": "render_sql_tool",
        "AskUserQuestion": "render_question_tool",
        "generic": "render_generic_tool",
    }
)
```

## Feature Comparison Matrix

| Feature | Coarse-Grained | Fine-Grained |
|---------|----------------|--------------|
| Lines of Code | ~100 | ~400 (spread across files) |
| Files | 1 | 6 |
| Control Flow | Imperative (loops/if) | Declarative (edges) |
| Visibility | Via logging | Via graph viz |
| Testing | Mock whole function | Test each node |
| Debugging | Set breakpoints | Inspect state between nodes |
| Performance | Fast (single call) | Slight overhead (graph execution) |
| Extensibility | Add code to loop | Add new node + edge |
| Learning Curve | Low (standard Python) | Medium (understand subgraphs) |
| Maintainability | Good (if simple) | Better (if complex) |

## Performance Analysis

### Coarse-Grained
```
Execution Time: ~5ms for 100 chunks
- Single function call
- Direct loop iteration
- Minimal overhead
```

### Fine-Grained
```
Execution Time: ~8ms for 100 chunks
- Subgraph compilation: <1ms (cached)
- Node execution: ~100 node calls
- State serialization overhead
- Conditional edge evaluation
```

**Verdict:** Coarse-grained is 30-40% faster, but both are fast enough for real-time streaming.

## Testing Comparison

### Coarse-Grained Testing
```python
def test_process_stream():
    state = {"stream_chunks": [...]}
    result = process_stream_node(state)
    assert len(result["render_queue"]) == 3
```

**Pros:**
- Simple, direct testing
- One test per scenario

**Cons:**
- Can't test intermediate steps
- Hard to isolate failures

### Fine-Grained Testing
```python
def test_fetch_chunk():
    state = {"stream_chunks": [...], "chunk_index": 0}
    result = fetch_next_chunk_node(state)
    assert result["current_chunk"] == chunks[0]
    assert result["chunk_index"] == 1

def test_extract_text_delta():
    state = {"current_chunk": ..., "prev_text": "Hello"}
    result = extract_text_delta_node(state)
    assert result["render_queue"][0]["content"] == ", world"
```

**Pros:**
- Each node tested in isolation
- Easy to pinpoint failures
- Can test edge cases per node

**Cons:**
- More tests to write
- Need to mock state carefully

## Extensibility Examples

### Adding a New Event Type

#### Coarse-Grained
```python
# Add to process_stream_node
def process_stream_node(state):
    for event_type, data in chunks:
        # ... existing code ...
        elif event_type == "custom/event":  # NEW
            # Handle custom event
            custom_data = parse_custom(data)
            render_queue.append({"type": "custom", "data": custom_data})
```

#### Fine-Grained
```python
# 1. Create nodes/custom_handler.py
def handle_custom_event_node(state):
    # Handle custom event
    return {"render_queue": [...]}

# 2. Update stream_processor.py
graph.add_node("handle_custom", handle_custom_event_node)
graph.add_conditional_edges(
    "parse_chunk",
    route_by_event_type,
    {
        # ... existing routes ...
        "custom/event": "handle_custom",  # NEW
    }
)
```

**Analysis:**
- Coarse: Faster to add (fewer files)
- Fine: Better separation, easier to test

### Adding a New Tool Type

#### Coarse-Grained
```python
# Add to process_stream_node
if event_type == "messages/complete":
    for tool_call in tool_calls:
        if tool_call["name"] == "new_tool":  # NEW
            # Format new tool
            formatted = format_new_tool(tool_call)
            render_queue.append({"type": "tool_call", "tool": formatted})
        else:
            # ... existing tool handling ...
```

#### Fine-Grained
```python
# 1. Add to nodes/tool_handlers.py
def render_new_tool_node(state):
    # Format new tool
    return {"render_queue": [...]}

# 2. Update stream_processor.py
graph.add_node("render_new_tool", render_new_tool_node)
graph.add_conditional_edges(
    "extract_tools",
    route_by_tool_name,
    {
        # ... existing tools ...
        "new_tool": "render_new_tool",  # NEW
    }
)
```

**Analysis:**
- Coarse: Add conditional to existing code
- Fine: Add new node, update routing

## Real-World Scenarios

### Scenario 1: Simple Streaming
**Context:** Basic text streaming, no tools, no HITL

**Recommendation:** Coarse-Grained
- Fast execution
- Simple flow
- Easy to understand

### Scenario 2: Complex Multi-Tool System
**Context:** 10+ tool types, custom rendering per tool

**Recommendation:** Fine-Grained
- Tool-specific nodes isolate complexity
- Easy to add new tools
- Better testing per tool

### Scenario 3: Production Debugging
**Context:** Investigating interrupt detection bug

**Coarse-Grained:**
- Add logging in process_stream_node
- Re-run, check logs
- Set breakpoint, step through loop

**Fine-Grained:**
- Check graph visualization
- See exact node where interrupt detected
- Test detect_interrupt_node in isolation
- Fix node, re-test

**Winner:** Fine-Grained (better visibility)

### Scenario 4: Performance Critical
**Context:** Processing 1000 chunks/second

**Coarse-Grained:**
- Minimal overhead
- Direct execution
- ~5ms per batch

**Fine-Grained:**
- Graph overhead
- State serialization
- ~8ms per batch

**Winner:** Coarse-Grained (30% faster)

## Hybrid Approach

For projects with diverse needs, consider:

```python
# Use fine-grained for complex flows
graph.add_node("process_stream", build_stream_processor_subgraph())

# Use coarse-grained for simple flows
graph.add_node("process_metadata", process_metadata_node)
```

**Benefits:**
- Flexibility per component
- Optimize where needed
- Learn subgraphs incrementally

## Recommendations

### Choose Coarse-Grained When:
- Performance is critical
- Flow is simple and stable
- Team prefers imperative code
- Quick prototyping

### Choose Fine-Grained When:
- Visibility is important
- Flow is complex or evolving
- Testing individual steps is valuable
- Team wants to leverage LangGraph features

### Migration Path

**Start Coarse:**
```
Phase 1: Single node (fast development)
         ↓
Phase 2: Complex scenarios emerge
         ↓
Phase 3: Convert to subgraph (better maintainability)
```

**Start Fine:**
```
Phase 1: Subgraph (clear structure)
         ↓
Phase 2: Performance bottleneck
         ↓
Phase 3: Optimize hot paths to coarse
```

## Conclusion

Both approaches are valid. The choice depends on:

1. **Team preference**: Imperative vs declarative
2. **Project stage**: Prototype vs mature
3. **Complexity**: Simple vs complex flows
4. **Performance needs**: Real-time vs batch

**For this REPL project:**
- Stream processing is complex (multiple event types, tools, HITL)
- Visibility helps debugging
- Performance is adequate
- **Recommendation:** Fine-grained for stream processing, coarse for simple nodes

The proof-of-concept subgraph demonstrates that fine-grained decomposition is practical and beneficial for the right use cases.
