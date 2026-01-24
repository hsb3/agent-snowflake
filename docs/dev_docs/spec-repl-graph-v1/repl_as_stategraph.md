# REPL as LangGraph StateGraph

Exploration of implementing the REPL client using LangGraph StateGraph for control flow, state management, and execution orchestration.

## Why This Could Work

### Natural Mapping
- REPL flow is already a DAG (as documented in `repl_data_flow.md`)
- LangGraph provides state management, routing, and interrupts out-of-the-box
- Input → Process → Render → Loop maps to graph nodes and edges
- HITL interrupts are a core LangGraph primitive

### Potential Benefits
1. **State management**: StateGraph handles state propagation automatically
2. **Debugging**: Visual graph execution, state snapshots at each node
3. **Testing**: Inject state, run from specific nodes
4. **Replay**: Re-run sessions from checkpoints
5. **Interrupts**: Native HITL support with `.interrupt()`
6. **Routing**: Conditional edges handle command vs message logic
7. **Observability**: Built-in execution traces

### Challenges to Consider
1. **Performance**: Graph execution overhead for tight streaming loops?
2. **Streaming**: Processing thousands of SSE chunks through graph nodes?

>>> NEED TO BUILD BUFFER


3. **Blocking I/O**: Terminal input is blocking - conflicts with async?
4. **Loop detection**: Infinite input loop needs special handling
5. **Overhead**: Is StateGraph too heavy for simple REPL operations?

## State Schema Design

```python
from typing import TypedDict, Literal
from dataclasses import dataclass

class REPLState(TypedDict):
    """State that flows through the graph"""

    # Input
    user_input: str
    input_type: Literal["command", "message", "empty"] | None

    # Session context
    current_thread_id: str | None
    current_assistant_id: str
    current_run_id: str | None

    # Streaming state
    stream_chunks: list[dict]  # Accumulate chunks for processing
    stream_buffer: dict  # Text accumulation, tool buffers

    # Rendering queue
    render_queue: list[dict]  # ParsedChunks waiting to render

    # HITL interrupt state
    pending_interrupt: dict | None
    interrupt_approved: bool | None

    # Session stats
    session_tokens: dict  # {input, output, total}
    session_start_time: float
    message_count: int

    # Control flow
    should_exit: bool
    error: str | None

    # Command execution result
    command_result: dict | None
```

## Graph Architecture

### Approach 1: Coarse-Grained (Recommended)

Major operations as nodes, streaming handled within nodes.

```python
from langgraph.graph import StateGraph, END

def build_repl_graph() -> StateGraph:
    graph = StateGraph(REPLState)

    # Core nodes
    graph.add_node("get_input", get_input_node)
    graph.add_node("route_input", route_input_node)
    graph.add_node("execute_command", execute_command_node)
    graph.add_node("send_message", send_message_node)
    graph.add_node("process_stream", process_stream_node)  # Handles all chunks internally
    graph.add_node("render_output", render_output_node)
    graph.add_node("handle_interrupt", handle_interrupt_node)
    graph.add_node("update_session", update_session_node)

    # Entry point
    graph.set_entry_point("get_input")

    # Routing from input
    graph.add_conditional_edges(
        "route_input",
        route_decision,
        {
            "command": "execute_command",
            "message": "send_message",
            "empty": "get_input",  # Loop back
            "exit": END
        }
    )

    # Command flow
    graph.add_edge("execute_command", "render_output")

    # Message flow
    graph.add_edge("send_message", "process_stream")
    graph.add_conditional_edges(
        "process_stream",
        check_for_interrupt,
        {
            "interrupt": "handle_interrupt",
            "complete": "update_session"
        }
    )
    graph.add_edge("handle_interrupt", "process_stream")  # Resume after approval
    graph.add_edge("update_session", "render_output")

    # Loop back to input
    graph.add_conditional_edges(
        "render_output",
        check_should_exit,
        {
            "continue": "get_input",
            "exit": END
        }
    )

    return graph.compile()
```

### Approach 2: Fine-Grained with Stream Subgraph

Dedicated subgraph for streaming, each chunk type as conditional routing.

```python
def build_stream_subgraph() -> StateGraph:
    """Subgraph that processes streaming chunks"""

    subgraph = StateGraph(REPLState)

    subgraph.add_node("fetch_chunk", fetch_next_chunk_node)
    subgraph.add_node("parse_chunk", parse_chunk_node)
    subgraph.add_node("render_text", render_text_delta_node)
    subgraph.add_node("render_tool", render_tool_call_node)
    subgraph.add_node("track_usage", track_usage_node)
    subgraph.add_node("detect_interrupt", detect_interrupt_node)

    subgraph.set_entry_point("fetch_chunk")

    subgraph.add_conditional_edges(
        "parse_chunk",
        route_by_chunk_type,
        {
            "text_delta": "render_text",
            "tool_call": "render_tool",
            "usage": "track_usage",
            "interrupt": "detect_interrupt",
            "complete": END
        }
    )

    # All paths loop back to fetch next chunk
    for node in ["render_text", "render_tool", "track_usage"]:
        subgraph.add_edge(node, "fetch_chunk")

    # Interrupt exits subgraph
    subgraph.add_edge("detect_interrupt", END)

    return subgraph.compile()

def build_repl_graph_v2() -> StateGraph:
    """Main graph using stream subgraph"""

    graph = StateGraph(REPLState)

    graph.add_node("get_input", get_input_node)
    graph.add_node("route_input", route_input_node)
    graph.add_node("execute_command", execute_command_node)
    graph.add_node("send_message", send_message_node)
    graph.add_node("stream_handler", build_stream_subgraph())  # Subgraph
    graph.add_node("handle_interrupt", handle_interrupt_node)
    graph.add_node("render_output", render_output_node)

    # ... edges similar to Approach 1

    return graph.compile()
```

## Node Implementations

### get_input_node

```python
def get_input_node(state: REPLState) -> REPLState:
    """Blocking input from terminal"""

    # Render prompt
    agent_name = state.get("current_assistant_id", "repl")
    prompt = f"[{agent_name}] > "

    # Get input (blocking)
    user_input = input(prompt).strip()

    return {
        **state,
        "user_input": user_input,
        "input_type": None,  # Will be determined by route_input
    }
```

### route_input_node

```python
def route_input_node(state: REPLState) -> REPLState:
    """Classify input type"""

    user_input = state["user_input"]

    if not user_input:
        input_type = "empty"
    elif user_input.startswith("/"):
        input_type = "command"
        if user_input.strip() == "/exit":
            return {**state, "should_exit": True, "input_type": "exit"}
    else:
        input_type = "message"

    return {**state, "input_type": input_type}

def route_decision(state: REPLState) -> str:
    """Conditional edge routing"""
    return state["input_type"]
```

### send_message_node

```python
def send_message_node(state: REPLState) -> REPLState:
    """Initiate streaming request to LangGraph server"""

    # Get client from config/context (injected)
    client = get_client()

    # Ensure we have thread and agent
    thread_id = state.get("current_thread_id")
    if not thread_id:
        thread_id = client.create_thread()

    assistant_id = state["current_assistant_id"]
    message = state["user_input"]

    # Stream message - collect chunks
    chunks = list(client.stream_message(thread_id, message, assistant_id))

    return {
        **state,
        "current_thread_id": thread_id,
        "stream_chunks": chunks,
        "stream_buffer": {},
    }
```

### process_stream_node

```python
def process_stream_node(state: REPLState) -> REPLState:
    """Process all streaming chunks (Approach 1 - coarse-grained)"""

    chunks = state["stream_chunks"]
    stream_handler = StreamHandler(state)
    render_queue = []
    pending_interrupt = None

    # Process all chunks
    for event_type, data in chunks:
        parsed = parse_message_chunk(event_type, data)

        if parsed.chunk_type == ChunkType.TEXT_DELTA:
            render_queue.append({
                "type": "text",
                "content": parsed.text_delta
            })

        elif parsed.chunk_type == ChunkType.TOOL_CALL_COMPLETE:
            render_queue.append({
                "type": "tool_call",
                "tool": parsed.tool_call
            })

        elif parsed.chunk_type == ChunkType.INTERRUPT:
            pending_interrupt = parsed.interrupt
            break  # Exit to handle interrupt

        elif parsed.chunk_type == ChunkType.USAGE:
            # Update in state
            pass

    return {
        **state,
        "render_queue": render_queue,
        "pending_interrupt": pending_interrupt,
    }

def check_for_interrupt(state: REPLState) -> str:
    """Conditional edge - check if interrupted"""
    return "interrupt" if state.get("pending_interrupt") else "complete"
```

### handle_interrupt_node

```python
def handle_interrupt_node(state: REPLState) -> REPLState:
    """Handle HITL approval - uses LangGraph's interrupt system"""

    interrupt = state["pending_interrupt"]

    # Render approval prompt
    renderer = get_renderer()
    renderer.render_tool_preview(
        interrupt["tool_name"],
        interrupt["tool_args"]
    )

    # Block for approval (this could use graph.interrupt())
    approval = input("Approve? (y/n): ").strip().lower() == 'y'

    # Resume streaming with approval
    client = get_client()
    resume_chunks = list(client.resume_after_interrupt(
        state["current_thread_id"],
        state["current_assistant_id"],
        approved=approval
    ))

    return {
        **state,
        "stream_chunks": resume_chunks,
        "pending_interrupt": None,
        "interrupt_approved": approval,
    }
```

### render_output_node

```python
def render_output_node(state: REPLState) -> REPLState:
    """Render everything in the queue"""

    renderer = get_renderer()
    render_queue = state.get("render_queue", [])

    for item in render_queue:
        if item["type"] == "text":
            renderer.render_text(item["content"])
        elif item["type"] == "tool_call":
            renderer.render_tool_call(item["tool"])
        elif item["type"] == "command_result":
            renderer.render_panel(item["content"], item["title"])

    return {
        **state,
        "render_queue": [],  # Clear queue
    }

def check_should_exit(state: REPLState) -> str:
    """Conditional edge - continue or exit"""
    return "exit" if state.get("should_exit") else "continue"
```

## Dependency Injection

```python
from contextvars import ContextVar

# Context vars for injecting dependencies
_client_ctx: ContextVar[LangGraphClient] = ContextVar("client")
_renderer_ctx: ContextVar[Renderer] = ContextVar("renderer")
_session_ctx: ContextVar[SessionState] = ContextVar("session")

def get_client() -> LangGraphClient:
    return _client_ctx.get()

def get_renderer() -> Renderer:
    return _renderer_ctx.get()

def get_session() -> SessionState:
    return _session_ctx.get()
```

## Running the Graph

```python
def main():
    # Initialize components
    config = Config.from_env()
    client = LangGraphClient(config.server_url)
    renderer = Renderer()
    session = SessionState()

    # Build graph
    repl_graph = build_repl_graph()

    # Set context
    _client_ctx.set(client)
    _renderer_ctx.set(renderer)
    _session_ctx.set(session)

    # Initial state
    initial_state: REPLState = {
        "user_input": "",
        "input_type": None,
        "current_thread_id": None,
        "current_assistant_id": config.default_assistant_id,
        "current_run_id": None,
        "stream_chunks": [],
        "stream_buffer": {},
        "render_queue": [],
        "pending_interrupt": None,
        "interrupt_approved": None,
        "session_tokens": {"input": 0, "output": 0, "total": 0},
        "session_start_time": time.time(),
        "message_count": 0,
        "should_exit": False,
        "error": None,
        "command_result": None,
    }

    # Run graph (will loop until should_exit=True)
    final_state = repl_graph.invoke(initial_state)

    # Cleanup
    print(f"\nSession complete. Messages: {final_state['message_count']}")
    print(f"Tokens used: {final_state['session_tokens']['total']}")
```

## Tradeoffs Analysis

### Approach 1: Coarse-Grained Nodes ✅ RECOMMENDED

**Pros:**
- Simple graph structure (8-10 nodes)
- Streaming handled efficiently in single node
- Low overhead
- Easy to understand and debug
- State propagation clear

**Cons:**
- Less granular observability
- Can't checkpoint mid-stream
- Node functions do more work

**Best for:** This REPL use case

### Approach 2: Fine-Grained with Subgraph

**Pros:**
- Detailed execution traces
- Checkpoint at every chunk
- Perfect observability
- Maximum testability

**Cons:**
- Hundreds/thousands of node invocations per message
- Performance overhead
- Complex graph structure
- Overkill for REPL

**Best for:** When you need forensic-level debugging/replay

## Hybrid Approach: Best of Both Worlds

```python
def build_hybrid_repl_graph() -> StateGraph:
    """
    Coarse-grained for normal operation,
    fine-grained subgraph available for debugging
    """

    graph = StateGraph(REPLState)

    # Use coarse-grained nodes
    graph.add_node("get_input", get_input_node)
    graph.add_node("route_input", route_input_node)
    graph.add_node("execute_command", execute_command_node)
    graph.add_node("send_message", send_message_node)

    # Switch based on debug mode
    if config.debug_streaming:
        # Fine-grained subgraph for detailed traces
        graph.add_node("process_stream", build_stream_subgraph())
    else:
        # Fast coarse-grained processing
        graph.add_node("process_stream", process_stream_node)

    graph.add_node("handle_interrupt", handle_interrupt_node)
    graph.add_node("render_output", render_output_node)

    # ... edges

    return graph.compile()
```

## Key Insights

### State Management Win
- Single `REPLState` type replaces `SessionState` + scattered variables
- State propagation is automatic and type-safe
- No manual state threading through function calls

### Interrupt Handling Win
- LangGraph's native interrupt system maps perfectly to HITL
- Could use `graph.interrupt()` for approval prompts
- Checkpoint/resume built-in

### Testing Win
```python
def test_command_execution():
    # Inject state, run single node
    state = {
        "user_input": "/help",
        "input_type": "command",
        # ... minimal state
    }
    result = execute_command_node(state)
    assert "Available commands" in result["render_queue"][0]["content"]
```

### Observability Win
```python
# Get execution trace
trace = repl_graph.get_trace()

# See state at each node
for step in trace:
    print(f"Node: {step.node_name}")
    print(f"State: {step.state}")
    print(f"Duration: {step.duration_ms}ms")
```

### Streaming Challenge
- Processing thousands of SSE chunks through graph nodes is overhead
- **Solution**: Coarse-grained approach - one node processes entire stream
- Still get benefits of state management and routing

## Recommendation

**Use Approach 1 (Coarse-Grained) with these modifications:**

1. **Major operations as nodes**: Input, routing, command execution, streaming, rendering
2. **Streaming handled in single node**: Avoids per-chunk overhead
3. **HITL as dedicated node**: Uses conditional edge to route through approval
4. **State-based routing**: All control flow via conditional edges
5. **Dependency injection**: Use context vars for client/renderer/session

**Benefits over traditional approach:**
- Cleaner state management (single StateGraph vs manual propagation)
- Visual execution graph (debugging/documentation)
- Checkpoint/resume capability (replay sessions)
- Natural interrupt handling (HITL approval)
- Better testing (inject state, run nodes in isolation)

**Minimal overhead because:**
- Only 8-10 node invocations per user message
- Streaming chunks processed efficiently in single node
- No unnecessary graph traversal

## Next Steps

1. **Prototype Phase 1**: Implement core nodes (input, routing, streaming, rendering)
2. **Measure Performance**: Compare graph overhead vs traditional loop
3. **Add Observability**: Hook up execution traces to logging
4. **Test Interrupts**: Verify HITL flow with real LangGraph server
5. **Consider Persistence**: Could save graph checkpoints to resume sessions

## File Structure with StateGraph

```
src/agent_snowflake/repl/
├── __init__.py
├── __main__.py              # Entry point, runs graph
├── graph/
│   ├── __init__.py
│   ├── builder.py           # build_repl_graph()
│   ├── state.py             # REPLState TypedDict
│   └── nodes/
│       ├── __init__.py
│       ├── input.py         # get_input_node, route_input_node
│       ├── commands.py      # execute_command_node
│       ├── streaming.py     # send_message_node, process_stream_node
│       ├── hitl.py          # handle_interrupt_node
│       └── rendering.py     # render_output_node
├── core/
│   ├── client.py            # LangGraphClient (unchanged)
│   ├── parsers.py           # Chunk parsers (unchanged)
│   └── config.py            # Config (unchanged)
├── ui/
│   ├── renderer.py          # Renderer (unchanged)
│   └── ...
└── commands/
    ├── registry.py          # Command handlers (unchanged)
    └── ...
```
