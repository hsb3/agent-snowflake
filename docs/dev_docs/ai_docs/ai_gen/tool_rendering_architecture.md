# Tool Rendering Architecture

## Overview

This document describes the tool-specific rendering system for the REPL subgraph approach. The architecture separates tool call detection, formatting hints, and UI rendering into distinct layers.

## Architecture Layers

### Layer 1: Tool Detection (tool_router.py)

The tool router examines incoming tool calls and routes them to appropriate handlers:

```python
def route_by_tool_name(state: StreamSubgraphState) -> str:
    """Route to tool-specific render node based on tool name."""
    # Routes:
    # - sql_db_query → render_sql_tool
    # - sql_db_schema → render_sql_tool
    # - sql_db_list_tables → render_sql_tool
    # - sql_db_query_checker → render_sql_tool
    # - AskUserQuestion → render_question_tool
    # - * → render_generic_tool
```

### Layer 2: Format Hint Generation (tool_handlers.py)

Each tool handler extracts relevant data and adds "display" hints to render_queue:

```python
# Example: SQL query tool
render_queue.append({
    "type": "tool_call",
    "tool": {
        "name": "sql_db_query",
        "args": {"query": "SELECT * FROM customers"},
        "display": {
            "format": "sql",
            "query": "SELECT * FROM customers"
        }
    }
})
```

### Layer 3: UI Rendering (rendering.py)

The render_output_node() reads display hints and dispatches to Rich-based renderers:

```python
display_format = tool.get("display", {}).get("format")

if display_format == "sql":
    renderer.render_code(query, language="sql", title="SQL Query")
elif display_format == "schema":
    renderer.render_panel(table_list, title="Schema Query")
# ...etc
```

## Tool Coverage

### SQL Tools (LangChain SQLDatabaseToolkit)

| Tool Name | Display Format | UI Element | Description |
|-----------|----------------|------------|-------------|
| `sql_db_query` | `sql` | Syntax-highlighted code block | Execute SELECT queries |
| `sql_db_query_checker` | `sql` | Syntax-highlighted code block | Validate SQL queries |
| `sql_db_schema` | `schema` | Table list panel | Get table schemas |
| `sql_db_list_tables` | `list_tables` | Info panel | List available tables |

### Interactive Tools

| Tool Name | Display Format | UI Element | Description |
|-----------|----------------|------------|-------------|
| `AskUserQuestion` | `question` | Question panel with options | User prompts (Phase 3: arrow keys) |

### Generic Fallback

| Tool Name | Display Format | UI Element | Description |
|-----------|----------------|------------|-------------|
| (any unknown) | (none) | JSON args panel | Fallback for unhandled tools |

## Display Format Types

### "sql" - SQL Syntax Highlighting

**Used by:** sql_db_query, sql_db_query_checker

**Render Queue Item:**
```json
{
  "type": "tool_call",
  "tool": {
    "name": "sql_db_query",
    "args": {"query": "SELECT c_name, c_acctbal FROM customer WHERE c_region = 'ASIA'"},
    "display": {
      "format": "sql",
      "query": "SELECT c_name, c_acctbal FROM customer WHERE c_region = 'ASIA'"
    }
  }
}
```

**UI Output:**
```
┌─ SQL Query (sql_db_query) ─┐
│ SELECT c_name, c_acctbal    │
│ FROM customer               │
│ WHERE c_region = 'ASIA'     │
└─────────────────────────────┘
```

### "schema" - Table Schema Query

**Used by:** sql_db_schema

**Render Queue Item:**
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

**UI Output:**
```
┌─ Schema Query ──────────────┐
│ Requesting schema for       │
│ tables:                     │
│ customer, orders            │
└─────────────────────────────┘
```

### "list_tables" - List Database Tables

**Used by:** sql_db_list_tables

**Render Queue Item:**
```json
{
  "type": "tool_call",
  "tool": {
    "name": "sql_db_list_tables",
    "args": {},
    "display": {
      "format": "list_tables"
    }
  }
}
```

**UI Output:**
```
┌─ List Tables ───────────────┐
│ Requesting list of          │
│ database tables...          │
└─────────────────────────────┘
```

### "question" - Interactive User Question

**Used by:** AskUserQuestion

**Render Queue Item:**
```json
{
  "type": "tool_call",
  "tool": {
    "name": "AskUserQuestion",
    "args": {
      "question": "Which region should I analyze?",
      "options": ["ASIA", "EUROPE", "AMERICAS"]
    },
    "display": {
      "format": "question",
      "question": "Which region should I analyze?",
      "options": ["ASIA", "EUROPE", "AMERICAS"]
    }
  }
}
```

**UI Output (Current):**
```
┌─ User Question ─────────────┐
│ Which region should I       │
│ analyze?                    │
│                             │
│ Options:                    │
│   - ASIA                    │
│   - EUROPE                  │
│   - AMERICAS                │
└─────────────────────────────┘
```

**UI Output (Phase 3 - Future):**
```
┌─ User Question ─────────────┐
│ Which region should I       │
│ analyze?                    │
│                             │
│ > ASIA                      │  ← Arrow key selection
│   EUROPE                    │
│   AMERICAS                  │
└─────────────────────────────┘
```

### Generic - Unknown Tools

**Used by:** All unhandled tools

**Render Queue Item:**
```json
{
  "type": "tool_call",
  "tool": {
    "name": "custom_tool",
    "args": {"param1": "value1", "param2": 123}
  }
}
```

**UI Output:**
```
┌─ Tool Call: custom_tool ────┐
│ {                           │
│   "param1": "value1",       │
│   "param2": 123             │
│ }                           │
└─────────────────────────────┘
```

## Control Flow

### 1. Tool Call in Stream

```
SSE Event: messages/complete
├─ event_type: "messages/complete"
└─ data:
   └─ tool_calls: [
       {
         "name": "sql_db_query",
         "args": {"query": "SELECT * FROM customers"}
       }
     ]
```

### 2. Subgraph Processing

```
extract_tools_node
  ↓
route_by_tool_name
  ↓ (routes to "sql_db_query")
render_sql_tool_node
  ↓
render_queue.append({
  "type": "tool_call",
  "tool": {
    "name": "sql_db_query",
    "args": {...},
    "display": {"format": "sql", "query": "..."}
  }
})
```

### 3. Rendering Layer

```
render_output_node (rendering.py)
  ↓
for item in render_queue:
  ↓
  if item["type"] == "tool_call":
    ↓
    display_format = item["tool"]["display"]["format"]
    ↓
    if display_format == "sql":
      ↓
      renderer.render_code(query, language="sql", title="...")
```

## Adding New Tool Types

### Step 1: Create Tool Handler

Add handler to `tool_handlers.py`:

```python
def render_my_tool_node(state: "StreamSubgraphState") -> "StreamSubgraphState":
    """Render my custom tool."""
    current_chunk = state.get("current_chunk")
    render_queue = list(state.get("render_queue", []))

    if not current_chunk:
        return state

    event_type, data = current_chunk

    if isinstance(data, list) and data:
        message = data[-1]
        if isinstance(message, dict):
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict):
                        tool_name = tool_call.get("name", "")
                        if tool_name == "my_custom_tool":
                            tool_args = tool_call.get("args", {})

                            # Extract relevant data
                            custom_data = tool_args.get("data", "")

                            # Add display hint
                            render_queue.append({
                                "type": "tool_call",
                                "tool": {
                                    "name": tool_name,
                                    "args": tool_args,
                                    "display": {
                                        "format": "my_custom_format",
                                        "data": custom_data,
                                    }
                                },
                            })

    return {
        **state,
        "render_queue": render_queue,
    }
```

### Step 2: Add Route

Update `stream_processor.py`:

```python
graph.add_conditional_edges(
    "extract_tools",
    route_by_tool_name,
    {
        # ... existing routes
        "my_custom_tool": "render_my_tool",  # Add this
        "generic": "render_generic_tool",
        "none": "fetch_chunk",
    },
)

# Add node
graph.add_node("render_my_tool", render_my_tool_node)

# Add edge
graph.add_conditional_edges(
    "render_my_tool",
    check_has_more_chunks,
    {"more": "fetch_chunk", "done": END},
)
```

### Step 3: Add Renderer

Update `rendering.py`:

```python
elif display_format == "my_custom_format":
    # Custom rendering logic
    custom_data = display.get("data", "")
    renderer.render_panel(
        custom_data,
        title="My Custom Tool",
        style="magenta"
    )
```

### Step 4: Update Exports

Update `tool_handlers.py` exports:

```python
# In __init__.py
from .tool_handlers import (
    render_sql_tool_node,
    render_question_tool_node,
    render_generic_tool_node,
    render_my_tool_node,  # Add this
)
```

## Design Principles

1. **Separation of Concerns**
   - Tool handlers: Extract data, add hints
   - Rendering: Read hints, display UI
   - No direct UI calls from handlers

2. **Extensibility**
   - Add new tool type: Create handler + add route
   - No changes to existing handlers

3. **Fallback Safety**
   - Unknown tools route to generic handler
   - Always visible, never silently dropped

4. **UI Intent, Not Implementation**
   - Handlers specify "what" (format="sql")
   - Renderers decide "how" (Syntax highlighting)

5. **Future-Proof**
   - Display hints can evolve (add fields)
   - Renderers can enhance (add colors, interactions)
   - Handlers remain stable

## Testing Strategy

### Unit Tests (tool_handlers.py)

```python
def test_render_sql_query_node():
    state = {
        "current_chunk": (
            "messages/complete",
            [{
                "tool_calls": [{
                    "name": "sql_db_query",
                    "args": {"query": "SELECT * FROM test"}
                }]
            }]
        ),
        "render_queue": []
    }

    result = render_sql_tool_node(state)

    assert len(result["render_queue"]) == 1
    item = result["render_queue"][0]
    assert item["type"] == "tool_call"
    assert item["tool"]["display"]["format"] == "sql"
    assert item["tool"]["display"]["query"] == "SELECT * FROM test"
```

### Integration Tests (subgraph)

```python
def test_sql_tool_rendering_flow():
    # Test full flow: extract → route → render → output
    chunks = [
        ("messages/complete", [{
            "tool_calls": [{
                "name": "sql_db_query",
                "args": {"query": "SELECT 1"}
            }]
        }])
    ]

    graph = build_stream_processor_subgraph()
    result = graph.invoke({"stream_chunks": chunks})

    assert "render_queue" in result
    assert len(result["render_queue"]) == 1
```

## Performance Considerations

### Node Invocations per Tool

- Extract tools: 1 invocation
- Route tool: 1 invocation
- Render tool: 1 invocation
- **Total: 3 nodes per tool call**

### Optimization Opportunities

1. **Batch tool rendering**: Process all tools in single node
2. **Cached routing**: Pre-compute tool → handler mapping
3. **Lazy rendering**: Only format when actually displayed

### Current Trade-offs

- **More nodes**: Better visibility, easier testing
- **Slight overhead**: 3 nodes vs 1 coarse node
- **Worth it**: For < 100 tool calls per message, negligible impact

## Future Enhancements

### Phase 3: Interactive Tools

- Arrow key navigation for AskUserQuestion
- Real-time validation for SQL query input
- Inline editing for tool args before execution

### Advanced Rendering

- Collapsible/expandable tool call panels
- Tool execution progress indicators
- Side-by-side diff for sql_db_query_checker
- Table preview for schema queries

### Tool Discovery

- Auto-register tools from server metadata
- Dynamic handler generation for simple tools
- Tool documentation in help panels
