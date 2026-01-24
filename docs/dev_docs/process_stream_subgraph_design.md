# Process Stream Subgraph Design

## Current Problem

The `process_stream_node` is a single coarse-grained node that handles:
- Text delta extraction
- Tool call parsing
- Interrupt detection
- Usage tracking
- State updates
- Render queue building

**As tool complexity grows, this node could become:**
- 500+ lines with tool-specific logic
- Hard to test individual tool handlers
- Difficult to add new tool types
- Mixing concerns (parsing + UI decisions)

## Tool-Specific UI Requirements

Different tools need different UI components:

| Tool | Current Rendering | Ideal Rendering |
|------|-------------------|-----------------|
| `sql_db_query` | Generic panel | Syntax-highlighted SQL + result table |
| `AskUserQuestion` | Generic JSON | Interactive menu with options |
| `python_repl` | Generic panel | Code block with syntax highlighting |
| `search_tool` | Generic panel | Formatted search results |
| `file_operations` | Generic panel | File tree or diff display |
| `chart_generator` | Generic panel | ASCII chart or data table |

**Key insight:** Tool rendering is not one-size-fits-all!

## Option 1: Current Approach (Single Node)

**Structure:**
```python
def process_stream_node(state):
    for event_type, data in chunks:
        if event_type == "messages/partial":
            # Extract text delta
        elif event_type == "messages/complete":
            # Extract tool calls
            for tool in tool_calls:
                # Big if/elif for each tool type
                if tool.name == "sql_db_query":
                    # SQL-specific formatting
                elif tool.name == "AskUserQuestion":
                    # Question-specific formatting
                # ... 20+ more tool types
```

**Pros:**
- Simple graph structure
- Low overhead
- All logic in one place

**Cons:**
- God object anti-pattern
- Hard to test individual tools
- Will grow to 500+ lines
- Mixing parsing and UI concerns

## Option 2: Process Stream as Subgraph (Fine-Grained)

**Structure:**
```
process_stream_subgraph:
  fetch_next_chunk
      ↓
  parse_chunk_type
      ↓
  [route by event_type] → messages/partial → extract_text_delta → queue_text
                        → messages/complete → extract_tools → route_by_tool
                        → updates → detect_interrupt → queue_interrupt
      ↓
  check_done → [more chunks OR complete]
```

**Graph definition:**
```python
def build_stream_subgraph() -> StateGraph:
    subgraph = StateGraph(StreamState)

    # Chunk processing
    subgraph.add_node("fetch_chunk", fetch_next_chunk_node)
    subgraph.add_node("parse_chunk", parse_chunk_type_node)

    # Event type handlers
    subgraph.add_node("handle_text", extract_text_delta_node)
    subgraph.add_node("handle_tools", extract_tools_node)
    subgraph.add_node("handle_updates", process_updates_node)
    subgraph.add_node("handle_interrupt", detect_interrupt_node)

    # Tool-specific routing (this is the key!)
    subgraph.add_node("route_tool", route_by_tool_name_node)
    subgraph.add_node("render_sql", render_sql_tool_node)
    subgraph.add_node("render_question", render_question_tool_node)
    subgraph.add_node("render_generic", render_generic_tool_node)

    # Routing
    subgraph.add_conditional_edges(
        "parse_chunk",
        route_by_event_type,
        {
            "text": "handle_text",
            "tools": "handle_tools",
            "updates": "handle_updates",
            "done": END,
        }
    )

    subgraph.add_conditional_edges(
        "route_tool",
        route_by_tool_name,
        {
            "sql_db_query": "render_sql",
            "AskUserQuestion": "render_question",
            "default": "render_generic",
        }
    )

    # Loop back
    for node in ["handle_text", "render_sql", "render_question", "render_generic"]:
        subgraph.add_edge(node, "fetch_chunk")

    # Interrupt exits subgraph
    subgraph.add_edge("handle_interrupt", END)

    return subgraph.compile()
```

**Pros:**
- Clean separation per tool type
- Easy to add new tool handlers (just add node)
- Each handler is testable in isolation
- Tool-specific UI logic is encapsulated
- Detailed execution traces
- Can checkpoint mid-stream (debugging)

**Cons:**
- 100+ node invocations per message (if streaming 100 chunks)
- Performance overhead from graph traversal
- Complex graph structure
- Harder to understand overall flow

## Option 3: Hybrid Approach (RECOMMENDED)

**Structure:**
```
process_stream_node (handles SSE parsing)
    ↓
tool_handler_subgraph (only for tool calls)
    ↓
back to main graph
```

**Main graph:**
```python
def process_stream_node(state):
    """Fast parsing of SSE chunks, minimal logic"""
    for event_type, data in chunks:
        if event_type == "messages/partial":
            # Extract text delta (simple)
            render_queue.append({"type": "text", "content": delta})

        elif event_type == "messages/complete":
            # Extract tool calls
            tool_calls = extract_tool_calls(data)
            if tool_calls:
                # Delegate to tool handler subgraph
                return {
                    **state,
                    "pending_tools": tool_calls,
                    "partial_render_queue": render_queue,
                }

        elif event_type == "updates":
            # Simple interrupt check
            if "__interrupt__" in data:
                return {..., "pending_interrupt": interrupt}

    # No tools, complete normally
    return {**state, "render_queue": render_queue}
```

**Tool handler as subgraph:**
```python
def build_tool_handler_subgraph() -> StateGraph:
    subgraph = StateGraph(ToolHandlerState)

    subgraph.add_node("fetch_next_tool", fetch_next_tool_node)
    subgraph.add_node("route_tool", route_by_tool_node)

    # Tool-specific handlers
    subgraph.add_node("render_sql", render_sql_node)
    subgraph.add_node("render_question", render_question_node)
    subgraph.add_node("render_search", render_search_node)
    subgraph.add_node("render_chart", render_chart_node)
    subgraph.add_node("render_generic", render_generic_node)

    subgraph.add_conditional_edges(
        "route_tool",
        lambda state: get_tool_type(state["current_tool"]),
        {
            "sql_db_query": "render_sql",
            "AskUserQuestion": "render_question",
            "search_tool": "render_search",
            "chart_tool": "render_chart",
            "default": "render_generic",
        }
    )

    # Check if more tools to process
    subgraph.add_conditional_edges(
        "render_*",  # All render nodes
        lambda state: "more" if state["remaining_tools"] else "done",
        {
            "more": "fetch_next_tool",
            "done": END,
        }
    )

    return subgraph.compile()
```

**Main graph integration:**
```python
def build_repl_graph():
    graph = StateGraph(REPLState)

    # ... existing nodes
    graph.add_node("process_stream", process_stream_node)
    graph.add_node("handle_tools", build_tool_handler_subgraph())  # Subgraph!

    # Conditional routing
    graph.add_conditional_edges(
        "process_stream",
        check_stream_result,
        {
            "has_tools": "handle_tools",
            "has_interrupt": "handle_interrupt",
            "complete": "update_session",
        }
    )

    graph.add_edge("handle_tools", "update_session")
    # ...
```

**Pros:**
- SSE parsing stays fast (single node, few invocations)
- Tool handling is extensible (subgraph per tool)
- Only pay overhead when tools are present
- Clear separation: parsing vs rendering
- Easy to add new tools (just add node to subgraph)

**Cons:**
- More complex than single node
- Still some overhead (but only for tools)

## Option 4: Tool Registry Pattern (Current + Extension)

**Keep single node, but use ToolRegistry for delegation:**

```python
# Current pattern
def process_stream_node(state):
    tool_registry = get_tool_registry()

    for tool_call in tool_calls:
        # Delegate to registry instead of if/elif
        render_item = tool_registry.render_to_queue(tool_call)
        render_queue.append(render_item)
```

**ToolRegistry with Strategy Pattern:**
```python
class ToolRenderRegistry:
    def __init__(self):
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, tool_name: str, handler: ToolHandler):
        self._handlers[tool_name] = handler

    def render_to_queue(self, tool_call: dict) -> dict:
        """Convert tool call to render queue item"""
        tool_name = tool_call["name"]
        handler = self._handlers.get(tool_name, GenericHandler())

        # Each handler returns render queue item
        return handler.to_render_item(tool_call)

class SQLToolHandler(ToolHandler):
    def to_render_item(self, tool_call: dict) -> dict:
        query = tool_call["args"]["query"]
        return {
            "type": "code_block",
            "language": "sql",
            "content": query,
            "title": "SQL Query"
        }

class QuestionToolHandler(ToolHandler):
    def to_render_item(self, tool_call: dict) -> dict:
        question = tool_call["args"]["question"]
        options = tool_call["args"]["options"]
        return {
            "type": "interactive_menu",
            "question": question,
            "options": options,
        }
```

**Pros:**
- Single node stays simple
- Registry handles complexity
- Easy to test each handler
- No graph overhead
- Extensible via registration

**Cons:**
- Less visibility than subgraph
- No execution traces per tool
- Not using StateGraph capabilities

## Recommendation Matrix

| Use Case | Recommended Approach |
|----------|---------------------|
| **Simple tools (5-10 types)** | Option 4 (Registry) |
| **Complex tools (10-20 types)** | Option 3 (Hybrid) |
| **Very complex (20+ with interactions)** | Option 2 (Full subgraph) |
| **Interactive tools (user input mid-tool)** | Option 2 (Full subgraph) |

## Current State Analysis

**How many tool types do we expect?**

Looking at typical LangGraph agents:
- `sql_db_query` - Execute SQL
- `sql_db_schema` - Get schema
- `sql_db_list_tables` - List tables
- `AskUserQuestion` - User prompts (HITL adjacent)
- `python_repl` - Execute Python
- `search_tool` - Web search
- Custom domain tools (5-10?)

**Estimate: 10-15 tool types**

## My Recommendation: Start with Option 4, Migrate to Option 3 if Needed

### Phase 2 (Current): Keep Single Node + Registry

```python
def process_stream_node(state):
    tool_registry = get_tool_registry()

    for event_type, data in chunks:
        # ... simple parsing

        if tool_calls:
            for tool in tool_calls:
                # Delegate to registry
                render_item = tool_registry.render_to_queue(tool)
                render_queue.append(render_item)
```

**Benefits:**
- Simple to implement (mostly done)
- Low overhead
- Registry already exists
- Good for 10-15 tools

### Phase 3 (If Needed): Migrate to Subgraph

**Trigger: When one of these happens:**
- Tool count > 15
- Tools need multi-step rendering
- Interactive tools (user input during render)
- Complex state machines per tool

**Migration:**
```python
# Add subgraph to main graph
graph.add_node("handle_tools", build_tool_handler_subgraph())

# Route to it when tools detected
graph.add_conditional_edges(
    "process_stream",
    check_for_tools,
    {
        "has_tools": "handle_tools",
        "no_tools": "update_session",
    }
)
```

## Proposed Enhancement for Current Approach

**Extend ToolRenderRegistry with type-based routing:**

```python
class EnhancedToolRenderRegistry:
    """Registry with render type routing"""

    def __init__(self):
        self._handlers: dict[str, ToolRenderStrategy] = {}
        self._register_builtins()

    def _register_builtins(self):
        # SQL tools → code block
        self.register("sql_db_query", SQLRenderStrategy())
        self.register("sql_db_schema", SchemaRenderStrategy())

        # Interactive tools → special handling
        self.register("AskUserQuestion", QuestionRenderStrategy())

        # Generic fallback
        self.register("*", GenericRenderStrategy())

    def render_to_queue(self, tool_call: dict) -> dict:
        """Convert tool call to render queue item with proper type"""
        tool_name = tool_call["name"]
        strategy = self._handlers.get(tool_name, self._handlers["*"])
        return strategy.to_render_item(tool_call)

class SQLRenderStrategy:
    def to_render_item(self, tool_call: dict) -> dict:
        query = tool_call["args"].get("query", "")
        return {
            "type": "code_block",
            "language": "sql",
            "content": query,
            "title": f"Tool: {tool_call['name']}"
        }

class QuestionRenderStrategy:
    def to_render_item(self, tool_call: dict) -> dict:
        return {
            "type": "interactive_question",
            "question": tool_call["args"]["question"],
            "options": tool_call["args"]["options"],
        }
```

**Then extend render_output_node:**
```python
def render_output_node(state):
    for item in render_queue:
        if item["type"] == "code_block":
            renderer.render_code(item["content"], item["language"])

        elif item["type"] == "interactive_question":
            # Render interactive menu
            renderer.render_question(item["question"], item["options"])

        # ... other types
```

## Decision Framework

### When to Use Subgraph

**Use subgraph if ANY of these are true:**
1. ✅ Tools have multi-step rendering logic
2. ✅ Tools need user interaction during rendering
3. ✅ Tools have complex state machines
4. ✅ Need detailed execution traces per tool
5. ✅ Tools can fail and need retry logic
6. ✅ 20+ tool types with diverse requirements

### When to Use Registry

**Use registry if:**
1. ✅ Tools map 1:1 to render types
2. ✅ Rendering is stateless
3. ✅ < 20 tool types
4. ✅ Performance matters
5. ✅ Simplicity preferred

## Hybrid Architecture Proposal

```
Main Graph:
  process_stream_node
      ↓
  [check for complex tools]
      ↓
  simple_tools → update_session
  complex_tools → tool_handler_subgraph → update_session
```

**Classification:**
```python
def check_for_complex_tools(state):
    tools = state.get("pending_tools", [])

    complex_tool_names = {"AskUserQuestion", "chart_generator", "file_browser"}

    for tool in tools:
        if tool["name"] in complex_tool_names:
            return "complex"

    return "simple"
```

**Benefits:**
- Fast path for simple tools (SQL, search, etc.)
- Subgraph only for complex tools
- Best of both worlds

## My Recommendation

**For Current Implementation (Phase 2):**
Start with **enhanced registry pattern** (Option 4+):
- Keep `process_stream_node` as single node
- Enhance `ToolRenderRegistry` with render strategies
- Add new render types to `render_output_node`
- Measure complexity as tools grow

**Migration Path (Phase 3+):**
If we hit any of these:
- 20+ tool types
- Interactive tools (AskUserQuestion with arrow keys)
- Multi-step tool rendering
- Tool-specific state machines

**Then migrate to:**
- Option 3 (Hybrid) - Simple tools stay fast, complex tools get subgraph
- Or Option 2 (Full subgraph) - If most tools are complex

## Proof of Concept: Subgraph Version

Want me to create a proof-of-concept showing:
1. process_stream as subgraph with tool routing
2. Performance comparison (single node vs subgraph)
3. Complexity analysis

This would help us make an informed decision about whether the overhead is worth it.

## Questions to Consider

1. **How many tool types do you expect?**
   - < 10: Registry is fine
   - 10-20: Registry with strategies
   - 20+: Consider subgraph

2. **Do tools need user interaction during rendering?**
   - No: Registry works
   - Yes: Subgraph is better (can pause mid-tool)

3. **Is detailed tool-level observability important?**
   - No: Registry is simpler
   - Yes: Subgraph gives traces per tool

4. **Are tools stateful/multi-step?**
   - No: Registry works
   - Yes: Subgraph is natural fit

What do you think? Should we:
- **A)** Enhance the current registry approach
- **B)** Build a proof-of-concept subgraph version
- **C)** Implement the hybrid approach now
