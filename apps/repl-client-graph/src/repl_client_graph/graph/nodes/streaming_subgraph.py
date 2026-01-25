"""Process stream as fine-grained subgraph (PoC for design comparison).

This module implements the process_stream operation as a LangGraph subgraph
with individual nodes for each chunk processing step. This is a proof-of-concept
to compare against the coarse-grained single-node approach.

Key differences from streaming.py:
- Each chunk processing step is a separate node
- Tool routing happens via conditional edges
- Enables per-tool rendering strategies
- Higher node invocation count but better separation of concerns
"""

from typing import Literal, TypedDict

from langgraph.graph import END, StateGraph

from repl_client_graph.streaming.types import ChunkType, Interrupt


class StreamSubgraphState(TypedDict, total=False):
    """State for the process_stream subgraph.

    This state is separate from REPLState and handles chunk-by-chunk processing.
    """

    # Input from parent graph
    stream_chunks: list[tuple[str, dict]]

    # Processing state
    chunk_index: int
    current_chunk: tuple[str, dict] | None
    current_event_type: str | None

    # Accumulation buffers
    prev_text: str
    render_queue: list[dict]
    pending_interrupt: dict | None

    # Tool processing
    current_tools: list[dict]
    tool_index: int
    current_tool: dict | None

    # Completion flag
    processing_complete: bool


def fetch_next_chunk_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Fetch next chunk from stream_chunks list.

    Args:
        state: Current subgraph state

    Returns:
        Updated state with current_chunk and incremented index
    """
    chunks = state.get("stream_chunks", [])
    chunk_index = state.get("chunk_index", 0)

    if chunk_index < len(chunks):
        current_chunk = chunks[chunk_index]
        return {
            **state,
            "current_chunk": current_chunk,
            "chunk_index": chunk_index + 1,
        }
    else:
        # No more chunks - signal completion
        return {
            **state,
            "processing_complete": True,
            "current_chunk": None,
        }


def parse_chunk_type_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Parse current chunk and determine event type.

    Args:
        state: Current subgraph state with current_chunk

    Returns:
        Updated state with current_event_type
    """
    current_chunk = state.get("current_chunk")

    if not current_chunk:
        return {**state, "current_event_type": "done"}

    event_type, data = current_chunk

    return {
        **state,
        "current_event_type": event_type,
    }


def extract_text_delta_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Extract text delta from messages/partial event.

    Args:
        state: Current subgraph state

    Returns:
        Updated state with text delta added to render_queue
    """
    current_chunk = state.get("current_chunk")
    if not current_chunk:
        return state

    event_type, data = current_chunk
    render_queue = state.get("render_queue", [])
    prev_text = state.get("prev_text", "")

    # Handle messages stream mode - data is array of messages
    if not isinstance(data, list):
        return state

    # Process last message in array (the AI response)
    if data:
        message = data[-1]
        if not isinstance(message, dict):
            return state

        # Extract content blocks
        content = message.get("content", [])
        if content and isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    current_text = block.get("text", "")
                    # Extract delta (new text since last chunk)
                    if current_text and current_text != prev_text:
                        delta = current_text[len(prev_text) :]
                        if delta:
                            render_queue = render_queue.copy()
                            render_queue.append(
                                {
                                    "type": "text",
                                    "content": delta,
                                }
                            )
                        prev_text = current_text

    return {
        **state,
        "render_queue": render_queue,
        "prev_text": prev_text,
    }


def extract_tools_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Extract tool calls from messages/complete event.

    Args:
        state: Current subgraph state

    Returns:
        Updated state with current_tools populated
    """
    current_chunk = state.get("current_chunk")
    if not current_chunk:
        return state

    event_type, data = current_chunk

    if not isinstance(data, list) or not data:
        return state

    message = data[-1]
    if not isinstance(message, dict):
        return state

    tool_calls = message.get("tool_calls", [])

    return {
        **state,
        "current_tools": tool_calls if tool_calls else [],
        "tool_index": 0,
    }


def fetch_next_tool_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Fetch next tool from current_tools list.

    Args:
        state: Current subgraph state

    Returns:
        Updated state with current_tool
    """
    tools = state.get("current_tools", [])
    tool_index = state.get("tool_index", 0)

    if tool_index < len(tools):
        return {
            **state,
            "current_tool": tools[tool_index],
            "tool_index": tool_index + 1,
        }
    else:
        return {
            **state,
            "current_tool": None,
        }


def route_by_tool_name_node(state: StreamSubgraphState) -> str:
    """Route to tool-specific handler based on tool name.

    This is a conditional edge function.

    Args:
        state: Current subgraph state with current_tool

    Returns:
        Tool name or "generic" for routing
    """
    current_tool = state.get("current_tool")

    if not current_tool:
        return "done_tools"

    tool_name = current_tool.get("name", "")

    # Map known tools to specific handlers
    tool_mapping = {
        "sql_db_query": "sql",
        "sql_db_schema": "sql",
        "sql_db_list_tables": "sql",
        "AskUserQuestion": "question",
        "python_repl": "code",
    }

    return tool_mapping.get(tool_name, "generic")


def render_sql_tool_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Render SQL tool call to render queue.

    Args:
        state: Current subgraph state

    Returns:
        Updated state with SQL tool added to render_queue
    """
    current_tool = state.get("current_tool")
    if not current_tool:
        return state

    render_queue = state.get("render_queue", []).copy()

    # Extract SQL query from args
    args = current_tool.get("args", {})
    query = args.get("query", "") or args.get("command", "")

    render_queue.append(
        {
            "type": "code_block",
            "language": "sql",
            "content": query,
            "title": f"Tool: {current_tool.get('name', 'sql')}",
        }
    )

    return {
        **state,
        "render_queue": render_queue,
    }


def render_question_tool_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Render AskUserQuestion tool to render queue.

    Args:
        state: Current subgraph state

    Returns:
        Updated state with question tool added to render_queue
    """
    current_tool = state.get("current_tool")
    if not current_tool:
        return state

    render_queue = state.get("render_queue", []).copy()
    args = current_tool.get("args", {})

    render_queue.append(
        {
            "type": "interactive_question",
            "question": args.get("question", ""),
            "options": args.get("options", []),
        }
    )

    return {
        **state,
        "render_queue": render_queue,
    }


def render_code_tool_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Render code execution tool to render queue.

    Args:
        state: Current subgraph state

    Returns:
        Updated state with code tool added to render_queue
    """
    current_tool = state.get("current_tool")
    if not current_tool:
        return state

    render_queue = state.get("render_queue", []).copy()
    args = current_tool.get("args", {})

    render_queue.append(
        {
            "type": "code_block",
            "language": "python",
            "content": args.get("code", ""),
            "title": f"Tool: {current_tool.get('name', 'code')}",
        }
    )

    return {
        **state,
        "render_queue": render_queue,
    }


def render_generic_tool_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Render generic tool call to render queue.

    Args:
        state: Current subgraph state

    Returns:
        Updated state with generic tool added to render_queue
    """
    current_tool = state.get("current_tool")
    if not current_tool:
        return state

    render_queue = state.get("render_queue", []).copy()

    render_queue.append(
        {
            "type": "tool_call",
            "tool": current_tool,
        }
    )

    return {
        **state,
        "render_queue": render_queue,
    }


def detect_interrupt_node(state: StreamSubgraphState) -> StreamSubgraphState:
    """Detect interrupt in updates event.

    Args:
        state: Current subgraph state

    Returns:
        Updated state with pending_interrupt if found
    """
    current_chunk = state.get("current_chunk")
    if not current_chunk:
        return state

    event_type, data = current_chunk

    if not isinstance(data, dict):
        return state

    # Check for interrupt signal
    if "__interrupt__" in data:
        interrupt_list = data["__interrupt__"]

        # Extract interrupt data
        if isinstance(interrupt_list, list) and len(interrupt_list) > 0:
            interrupt_data = interrupt_list[0]

            if isinstance(interrupt_data, dict):
                # Extract value
                value = interrupt_data.get("value", {})
                tool_name = value.get("tool", "unknown")
                interrupt_id = f"interrupt_{tool_name}_{id(interrupt_data)}"

                pending_interrupt = {
                    "id": interrupt_id,
                    "value": value,
                }

                return {
                    **state,
                    "pending_interrupt": pending_interrupt,
                    "processing_complete": True,  # Interrupt stops processing
                }

    return state


def route_by_event_type(state: StreamSubgraphState) -> str:
    """Conditional edge - route based on event_type.

    Args:
        state: Current subgraph state

    Returns:
        Routing key for conditional edge
    """
    event_type = state.get("current_event_type")

    if event_type == "messages/partial":
        return "text"
    elif event_type == "messages/complete":
        return "tools"
    elif event_type == "updates":
        return "updates"
    elif event_type == "done":
        return "done"
    else:
        return "next_chunk"


def check_more_tools(state: StreamSubgraphState) -> str:
    """Conditional edge - check if more tools to process.

    Args:
        state: Current subgraph state

    Returns:
        "more" if more tools, "next_chunk" otherwise
    """
    tools = state.get("current_tools", [])
    tool_index = state.get("tool_index", 0)

    return "more" if tool_index < len(tools) else "next_chunk"


def check_processing_complete(state: StreamSubgraphState) -> str:
    """Conditional edge - check if all chunks processed.

    Args:
        state: Current subgraph state

    Returns:
        "complete" if done, "continue" otherwise
    """
    return "complete" if state.get("processing_complete", False) else "continue"


def build_process_stream_subgraph() -> StateGraph:
    """Build the process_stream operation as a fine-grained subgraph.

    This subgraph replaces the single process_stream_node with multiple
    nodes for chunk fetching, parsing, and tool routing.

    Graph structure:
        fetch_chunk → parse_chunk → [route by event_type]
            → text: extract_text_delta → fetch_chunk (loop)
            → tools: extract_tools → fetch_next_tool → [route by tool_name]
                → sql/question/code/generic render → check_more_tools
                    → more: fetch_next_tool (loop)
                    → next_chunk: fetch_chunk (loop)
            → updates: detect_interrupt → [may exit]
            → done: END

    Returns:
        Compiled StateGraph for process_stream subgraph
    """
    subgraph = StateGraph(StreamSubgraphState)  # type: ignore[arg-type]

    # Chunk processing nodes
    subgraph.add_node("fetch_chunk", fetch_next_chunk_node)
    subgraph.add_node("parse_chunk", parse_chunk_type_node)

    # Event type handlers
    subgraph.add_node("extract_text_delta", extract_text_delta_node)
    subgraph.add_node("extract_tools", extract_tools_node)
    subgraph.add_node("detect_interrupt", detect_interrupt_node)

    # Tool processing nodes
    subgraph.add_node("fetch_next_tool", fetch_next_tool_node)
    subgraph.add_node("render_sql", render_sql_tool_node)
    subgraph.add_node("render_question", render_question_tool_node)
    subgraph.add_node("render_code", render_code_tool_node)
    subgraph.add_node("render_generic", render_generic_tool_node)

    # Entry point
    subgraph.set_entry_point("fetch_chunk")

    # Chunk fetching → parsing
    subgraph.add_conditional_edges(
        "fetch_chunk",
        check_processing_complete,
        {
            "complete": END,
            "continue": "parse_chunk",
        },
    )

    # Parse → route by event type
    subgraph.add_conditional_edges(
        "parse_chunk",
        route_by_event_type,
        {
            "text": "extract_text_delta",
            "tools": "extract_tools",
            "updates": "detect_interrupt",
            "done": END,
            "next_chunk": "fetch_chunk",
        },
    )

    # Text delta → loop back
    subgraph.add_edge("extract_text_delta", "fetch_chunk")

    # Tools → fetch first tool
    subgraph.add_edge("extract_tools", "fetch_next_tool")

    # Route by tool name
    subgraph.add_conditional_edges(
        "fetch_next_tool",
        route_by_tool_name_node,
        {
            "sql": "render_sql",
            "question": "render_question",
            "code": "render_code",
            "generic": "render_generic",
            "done_tools": "fetch_chunk",  # No tools, continue
        },
    )

    # All render nodes → check for more tools
    for render_node in ["render_sql", "render_question", "render_code", "render_generic"]:
        subgraph.add_conditional_edges(
            render_node,
            check_more_tools,
            {
                "more": "fetch_next_tool",
                "next_chunk": "fetch_chunk",
            },
        )

    # Interrupt → exit immediately
    subgraph.add_edge("detect_interrupt", END)

    return subgraph.compile()
