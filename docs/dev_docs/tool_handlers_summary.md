# Tool Handlers Summary

Quick reference for tool-specific rendering in the REPL subgraph.

## Files Modified

1. **src/repl_client_graph/graph/subgraphs/nodes/tool_handlers.py** (NEW)
   - Tool-specific render nodes
   - Adds display hints to render_queue

2. **src/repl_client_graph/graph/nodes/rendering.py** (UPDATED)
   - Added display format handling in tool_call section
   - Dispatches to appropriate Rich renderers

3. **src/repl_client_graph/ui/renderer.py** (UPDATED)
   - Added optional `title` parameter to `render_code()`

4. **src/repl_client_graph/graph/subgraphs/stream_processor.py** (UPDATED)
   - Added routing for all SQL tool types
   - Updated docstring

## Tool → Display Format Mapping

```python
TOOL_DISPLAY_FORMATS = {
    # SQL Tools
    "sql_db_query": "sql",           # Syntax-highlighted query
    "sql_db_query_checker": "sql",   # Syntax-highlighted query
    "sql_db_schema": "schema",       # Table list panel
    "sql_db_list_tables": "list_tables",  # Info panel

    # Interactive Tools
    "AskUserQuestion": "question",   # Question with options

    # Fallback
    "*": None  # Generic JSON args panel
}
```

## Render Queue Item Structure

### SQL Query
```json
{
  "type": "tool_call",
  "tool": {
    "name": "sql_db_query",
    "args": {"query": "SELECT * FROM customers"},
    "display": {
      "format": "sql",
      "query": "SELECT * FROM customers"
    }
  }
}
```

### Schema Query
```json
{
  "type": "tool_call",
  "tool": {
    "name": "sql_db_schema",
    "args": {"table_names": "customer, orders"},
    "display": {
      "format": "schema",
      "tables": ["customer", "orders"]
    }
  }
}
```

### Question
```json
{
  "type": "tool_call",
  "tool": {
    "name": "AskUserQuestion",
    "args": {
      "question": "Which region?",
      "options": ["ASIA", "EUROPE"]
    },
    "display": {
      "format": "question",
      "question": "Which region?",
      "options": ["ASIA", "EUROPE"]
    }
  }
}
```

### Generic
```json
{
  "type": "tool_call",
  "tool": {
    "name": "unknown_tool",
    "args": {"param": "value"}
  }
}
```

## Key Functions

### tool_handlers.py

- `render_sql_tool_node(state)` - Handles all 4 SQL tools
- `render_question_tool_node(state)` - Handles AskUserQuestion
- `render_generic_tool_node(state)` - Fallback for unknown tools

### rendering.py

```python
# In render_output_node(), tool_call section:
display_format = tool.get("display", {}).get("format")

if display_format == "sql":
    renderer.render_code(query, language="sql", title=f"SQL Query ({tool_name})")
elif display_format == "schema":
    renderer.render_panel(f"Requesting schema for tables:\n{table_list}", ...)
elif display_format == "list_tables":
    renderer.render_panel("Requesting list of database tables...", ...)
elif display_format == "question":
    renderer.render_panel(f"{question}\n\nOptions:\n{options_list}", ...)
else:
    # Generic JSON fallback
    renderer.render_panel(str(tool_args), title=f"Tool Call: {tool_name}", ...)
```

## Testing

### Verify Tool Detection

```bash
# Check that tool routing works
uv run python -c "
from repl_client_graph.graph.subgraphs.stream_processor import build_stream_processor_subgraph
graph = build_stream_processor_subgraph()
print('Subgraph compiled successfully')
print('Nodes:', list(graph.nodes.keys()))
"
```

### Verify Rendering

```bash
# Test that render_output_node handles display formats
uv run python -c "
from repl_client_graph.graph.nodes.rendering import render_output_node
from repl_client_graph.ui.renderer import Renderer

state = {
    'render_queue': [{
        'type': 'tool_call',
        'tool': {
            'name': 'sql_db_query',
            'args': {'query': 'SELECT 1'},
            'display': {'format': 'sql', 'query': 'SELECT 1'}
        }
    }]
}

# This should print SQL with syntax highlighting
result = render_output_node(state)
print('Rendered successfully')
"
```

## Adding a New Tool Type

### 1. Add handler function

```python
# In tool_handlers.py
def render_my_tool_node(state):
    # ... extract tool data
    render_queue.append({
        "type": "tool_call",
        "tool": {
            "name": tool_name,
            "args": tool_args,
            "display": {
                "format": "my_format",
                "data": extracted_data
            }
        }
    })
    return {...state, "render_queue": render_queue}
```

### 2. Update routing

```python
# In stream_processor.py
graph.add_conditional_edges(
    "extract_tools",
    route_by_tool_name,
    {
        # ... existing
        "my_tool": "render_my_tool",
    }
)
```

### 3. Add renderer

```python
# In rendering.py
elif display_format == "my_format":
    data = display.get("data", "")
    renderer.render_panel(data, title="My Tool", style="magenta")
```

## Design Benefits

1. **Extensible**: Add new tools without modifying existing handlers
2. **Testable**: Each handler is a pure function
3. **Visible**: Tool-specific rendering shows in graph traces
4. **Clean**: Separation of data extraction (handlers) and UI (renderers)
5. **Safe**: Generic fallback ensures all tools are visible

## Known Limitations

1. Tool handlers currently process one tool at a time (could batch)
2. No async rendering (all synchronous)
3. No caching of formatted output (re-formats on each render)

## Future Enhancements

1. **Phase 3**: Interactive tool editing (arrow keys for AskUserQuestion)
2. **Collapsible panels**: Expand/collapse tool call details
3. **Tool templates**: Auto-generate handlers from tool metadata
4. **Streaming tool results**: Show partial results as they arrive
