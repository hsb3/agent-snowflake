# Stream Processor Subgraph - Complete Documentation Index

## Quick Links

### Getting Started
1. **[README.md](./README.md)** - Architecture overview and design patterns
2. **[subgraph_flow_diagram.md](../../../docs/dev_docs/spec-repl-v1/subgraph_flow_diagram.md)** - Visual flow diagrams
3. **[SUBGRAPH_POC_SUMMARY.md](../../../docs/dev_docs/spec-repl-v1/SUBGRAPH_POC_SUMMARY.md)** - Executive summary

### Implementation
- **[stream_processor.py](./stream_processor.py)** - Main subgraph builder
- **[nodes/](./nodes/)** - Individual node implementations

### Testing & Comparison
- **[test_subgraph_stream.py](../../../scripts/repl_client_graph/test_subgraph_stream.py)** - Comprehensive tests
- **[compare_stream_approaches.py](../../../scripts/repl_client_graph/compare_stream_approaches.py)** - Performance comparison
- **[approach_comparison.md](../../../docs/dev_docs/spec-repl-v1/approach_comparison.md)** - Detailed analysis

### Integration
- **[subgraph_integration_example.py](../../../docs/dev_docs/spec-repl-v1/subgraph_integration_example.py)** - Usage example

## What Is This?

This is a proof-of-concept implementation of stream processing using a **fine-grained subgraph** approach, as an alternative to the current **coarse-grained single-node** approach.

### Current Approach (Coarse-Grained)
```python
# Single node with internal loop
def process_stream_node(state):
    for chunk in chunks:
        if event == "partial": extract_text()
        elif event == "complete": extract_tools()
    return state
```

### Alternative Approach (Fine-Grained)
```python
# Multiple nodes with graph-managed flow
fetch_chunk → parse_chunk → route_by_event →
    ├─ extract_text → check_more → loop
    ├─ extract_tools → route_by_tool → render_tool → check_more → loop
    └─ process_updates → detect_interrupt → exit_or_loop
```

## File Structure

```
src/repl_client_graph/graph/subgraphs/
├── INDEX.md                      ← You are here
├── README.md                     ← Start here for architecture
├── __init__.py                   ← Public API
├── stream_processor.py           ← Subgraph builder
└── nodes/
    ├── __init__.py               ← Node exports
    ├── chunk_fetcher.py          ← Fetch next chunk, check if more
    ├── chunk_parser.py           ← Parse and route by event type
    ├── text_handler.py           ← Extract text deltas
    ├── tool_router.py            ← Extract tools, route by name
    ├── tool_handlers.py          ← SQL/Question/Generic renderers
    └── state_handler.py          ← Process updates, detect interrupt

docs/dev_docs/spec-repl-v1/
├── SUBGRAPH_POC_SUMMARY.md       ← Executive summary
├── approach_comparison.md        ← Detailed comparison
├── subgraph_flow_diagram.md      ← Visual diagrams
└── subgraph_integration_example.py ← Usage example

scripts/
├── test_subgraph_stream.py       ← Tests
└── compare_stream_approaches.py  ← Performance benchmarks
```

## Node Breakdown

### 1. chunk_fetcher.py
- **fetch_next_chunk_node**: Get chunk at current index, increment
- **check_has_more_chunks**: Conditional edge (more/done)

### 2. chunk_parser.py
- **parse_chunk_type_node**: Prepare chunk for routing
- **route_by_event_type**: Route to handler based on event type

### 3. text_handler.py
- **extract_text_delta_node**: Extract delta from cumulative text

### 4. tool_router.py
- **extract_tools_node**: Extract tool_calls and usage metadata
- **route_by_tool_name**: Route to tool-specific renderer

### 5. tool_handlers.py
- **render_sql_tool_node**: Format SQL queries
- **render_question_tool_node**: Format interactive questions
- **render_generic_tool_node**: Fallback formatter

### 6. state_handler.py
- **process_updates_node**: Add state updates to queue
- **detect_interrupt_node**: Check for __interrupt__, exit if found

## Key Decisions

### State Design
```python
class StreamSubgraphState(TypedDict):
    # Input (from parent)
    stream_chunks: list[tuple[str, dict]]

    # Processing
    chunk_index: int
    current_chunk: tuple[str, dict] | None
    prev_text: str

    # Output (to parent)
    render_queue: list[dict]
    pending_interrupt: dict | None
    usage: dict | None

    # Control
    is_complete: bool
```

### Control Flow
- **Loop**: fetch_chunk → process → check_has_more → fetch_chunk
- **Exit**: detect_interrupt → END or check_has_more → END
- **No infinite loops**: current_chunk=None → END immediately

### Routing Strategy
1. **Event type**: messages/partial, messages/complete, updates
2. **Tool type**: sql_db_query, AskUserQuestion, generic

## Performance

From test results:

| Metric | Coarse-Grained | Fine-Grained | Overhead |
|--------|----------------|--------------|----------|
| Small (10 chunks) | 0.01ms | 31.40ms | 3140x |
| Medium (20 chunks) | 0.01ms | 19.00ms | 1900x |
| Large (50 chunks) | 0.01ms | 43.63ms | 4363x |
| With Interrupt | 0.03ms | 7.51ms | 250x |

**Conclusion:** Subgraph is slower but still fast enough (< 50ms) for real-time use.

## Trade-offs

### Pros of Fine-Grained
- Better visibility (graph visualization)
- Easier testing (isolated nodes)
- Clearer structure (single responsibility)
- Easier maintenance (add nodes vs edit loop)

### Cons of Fine-Grained
- Performance overhead (300-4000x slower)
- More code (400 lines vs 100)
- More files (7 vs 1)
- Steeper learning curve

## When to Use Each

### Use Fine-Grained If:
- Flow is complex (many event types, tools)
- Team values visibility and testing
- Flow will evolve frequently
- Performance < 50ms is acceptable

### Use Coarse-Grained If:
- Performance is critical
- Flow is simple and stable
- Team prefers imperative code
- Code volume matters

## Integration Pattern

Both approaches have the same interface:

```python
# In parent graph builder

# Option 1: Coarse-grained
from .nodes import process_stream_node
graph.add_node("process_stream", process_stream_node)

# Option 2: Fine-grained
from repl_client_graph.graph.subgraphs import build_stream_processor_subgraph
graph.add_node("process_stream", build_stream_processor_subgraph())
```

Parent graph doesn't need to change - just swap the node.

## Testing

Run tests:
```bash
# Comprehensive functional tests
uv run python scripts/repl_client_graph/test_subgraph_stream.py

# Performance comparison
uv run python scripts/repl_client_graph/compare_stream_approaches.py
```

Expected output:
- All tests pass
- Render queues match between approaches
- Subgraph is 300-4000x slower (but < 50ms)

## Next Steps

### To Adopt Fine-Grained
1. Update `builder.py` to use subgraph
2. Update tests
3. Add graph visualization
4. Monitor real-world performance

### To Stick with Coarse-Grained
1. Archive this POC for reference
2. Document learnings
3. Consider for future complex components
4. Use diagrams for documentation

## Questions?

Refer to:
- **Architecture**: README.md
- **Flow**: subgraph_flow_diagram.md
- **Comparison**: approach_comparison.md
- **Summary**: SUBGRAPH_POC_SUMMARY.md

## Status

- ✅ Implementation complete
- ✅ Tests passing
- ✅ Documentation complete
- ✅ Performance benchmarks done
- 🔄 Awaiting decision on adoption

This is a complete, working proof-of-concept ready for evaluation.
