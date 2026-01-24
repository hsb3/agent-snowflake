# Tool Rendering Flow Diagram

## Complete Flow: Tool Call → Rendered Output

```
┌─────────────────────────────────────────────────────────────────────┐
│ SSE Stream Event                                                    │
│                                                                     │
│ event: messages/complete                                            │
│ data: {                                                             │
│   "data": [{                                                        │
│     "tool_calls": [{                                                │
│       "name": "sql_db_query",                                       │
│       "args": {"query": "SELECT * FROM customer"}                   │
│     }]                                                              │
│   }]                                                                │
│ }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Stream Processing Subgraph                                          │
│                                                                     │
│  1. fetch_chunk                                                     │
│     └─> Extracts next chunk from stream                            │
│                                                                     │
│  2. parse_chunk                                                     │
│     └─> Identifies event_type: "messages/complete"                 │
│                                                                     │
│  3. route_by_event_type                                             │
│     └─> Routes to "extract_tools"                                  │
│                                                                     │
│  4. extract_tools_node                                              │
│     └─> Finds tool_calls array                                     │
│                                                                     │
│  5. route_by_tool_name                                              │
│     └─> Checks tool.name: "sql_db_query"                           │
│     └─> Routes to "render_sql_tool"                                │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Tool Handler: render_sql_tool_node                                  │
│ (tool_handlers.py)                                                  │
│                                                                     │
│  Input:                                                             │
│    current_chunk = ("messages/complete", [{"tool_calls": [...]}])  │
│                                                                     │
│  Processing:                                                        │
│    1. Extract tool_name: "sql_db_query"                            │
│    2. Extract tool_args: {"query": "SELECT * FROM customer"}       │
│    3. Extract query: "SELECT * FROM customer"                      │
│                                                                     │
│  Output:                                                            │
│    render_queue.append({                                            │
│      "type": "tool_call",                                           │
│      "tool": {                                                      │
│        "name": "sql_db_query",                                      │
│        "args": {"query": "SELECT * FROM customer"},                 │
│        "display": {                                                 │
│          "format": "sql",        ◄─── UI HINT                       │
│          "query": "SELECT * FROM customer"                          │
│        }                                                            │
│      }                                                              │
│    })                                                               │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Subgraph Complete                                                   │
│                                                                     │
│  Returns to parent graph with:                                     │
│    {                                                                │
│      "render_queue": [                                              │
│        {                                                            │
│          "type": "tool_call",                                       │
│          "tool": {..., "display": {"format": "sql", ...}}           │
│        }                                                            │
│      ]                                                              │
│    }                                                                │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Main Graph: render_output_node                                      │
│ (rendering.py)                                                      │
│                                                                     │
│  for item in render_queue:                                          │
│    if item["type"] == "tool_call":                                  │
│      tool = item["tool"]                                            │
│      display = tool.get("display", {})                              │
│      display_format = display.get("format")                         │
│                                                                     │
│      if display_format == "sql":         ◄─── READS HINT            │
│        query = display["query"]                                     │
│        renderer.render_code(                                        │
│          query,                                                     │
│          language="sql",                                            │
│          title=f"SQL Query ({tool['name']})"                        │
│        )                                                            │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Rich Renderer: renderer.render_code()                               │
│ (renderer.py)                                                       │
│                                                                     │
│  def render_code(code, language, title=None):                       │
│    syntax = Syntax(code, language, theme="monokai")                 │
│    if title:                                                        │
│      panel = Panel(syntax, title=title, border_style="blue")        │
│      console.print(panel)                                           │
└─────────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Terminal Output                                                     │
│                                                                     │
│  ╭────────────────── SQL Query (sql_db_query) ──────────────────╮   │
│  │ SELECT * FROM customer                                        │   │
│  ╰───────────────────────────────────────────────────────────────╯   │
└─────────────────────────────────────────────────────────────────────┘
```

## Tool Routing Matrix

```
Tool Name               Route Target          Display Format    UI Element
═══════════════════════════════════════════════════════════════════════════
sql_db_query           render_sql_tool       "sql"             Code block + title
sql_db_query_checker   render_sql_tool       "sql"             Code block + title
sql_db_schema          render_sql_tool       "schema"          Table list panel
sql_db_list_tables     render_sql_tool       "list_tables"     Info panel
AskUserQuestion        render_question_tool  "question"        Question + options
custom_tool            render_generic_tool   (none)            JSON args panel
```

## State Transformations

### 1. Initial State (fetch_chunk)
```python
{
    "stream_chunks": [(event, data), ...],
    "chunk_index": 0,
    "current_chunk": None,
    "render_queue": [],
    # ...
}
```

### 2. After fetch_chunk
```python
{
    "stream_chunks": [(event, data), ...],
    "chunk_index": 1,  # ← Incremented
    "current_chunk": ("messages/complete", [...]),  # ← Set
    "render_queue": [],
    # ...
}
```

### 3. After render_sql_tool_node
```python
{
    "stream_chunks": [(event, data), ...],
    "chunk_index": 1,
    "current_chunk": ("messages/complete", [...]),
    "render_queue": [  # ← Item added
        {
            "type": "tool_call",
            "tool": {
                "name": "sql_db_query",
                "display": {"format": "sql", "query": "..."}
            }
        }
    ],
    # ...
}
```

### 4. After render_output_node (parent graph)
```python
{
    # ... other state ...
    "render_queue": [],  # ← Cleared after rendering
}
```

## Data Flow Summary

```
SSE Event
   │
   ├─> Stream Subgraph
   │      │
   │      ├─> Tool Router
   │      │      │
   │      │      └─> Determines handler by tool.name
   │      │
   │      └─> Tool Handler
   │             │
   │             └─> Adds display hints to render_queue
   │
   └─> render_queue returned to parent
          │
          └─> render_output_node
                 │
                 ├─> Reads display.format
                 │
                 └─> Dispatches to Rich renderer
                        │
                        └─> Terminal output
```

## Key Insight: Display Hints as Contract

The `display` object serves as a contract between layers:

```python
# Tool handler says: "This is SQL, here's the query"
"display": {
    "format": "sql",
    "query": "SELECT ..."
}

# Renderer reads: "Ah, SQL format! Use syntax highlighting"
if display_format == "sql":
    renderer.render_code(query, language="sql", ...)
```

This separation allows:
- Handlers to focus on data extraction
- Renderers to focus on presentation
- Easy extension (add new formats without changing handlers)
- Clear testing boundaries (test handlers and renderers separately)

## Extensibility Example

Adding a new chart tool:

### 1. Handler
```python
def render_chart_tool_node(state):
    # Extract chart data
    render_queue.append({
        "type": "tool_call",
        "tool": {
            "display": {
                "format": "chart",  # ← New format
                "chart_type": "bar",
                "data": [...]
            }
        }
    })
```

### 2. Router
```python
"generate_chart": "render_chart_tool"  # ← New route
```

### 3. Renderer
```python
elif display_format == "chart":  # ← New handler
    chart_type = display["chart_type"]
    data = display["data"]
    # Render ASCII chart or table
```

No changes needed to existing tool handlers or renderers!
