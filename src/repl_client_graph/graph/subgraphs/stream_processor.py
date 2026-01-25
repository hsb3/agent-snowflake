"""Stream processor subgraph builder.

This module defines a fine-grained subgraph for processing streaming chunks.
Instead of a single coarse-grained process_stream_node, this subgraph breaks
down stream processing into multiple small, focused nodes with explicit
control flow.

Key design decisions:
1. Stream chunks are passed as a list (already collected)
2. Subgraph iterates through chunks using an index
3. Each chunk is parsed and routed based on event type
4. Tool-specific rendering nodes handle different tool types
5. Interrupt detection causes immediate subgraph exit
6. Render queue accumulates UI elements to be rendered by parent

Comparison to coarse-grained approach:
- Coarse: Single large node with internal loop and conditionals
- Fine: Multiple small nodes, explicit edges, graph-managed control flow
- Advantage: Better visibility, easier to test individual steps, clearer flow
- Trade-off: More nodes and edges to manage
"""

from typing import TypedDict

from langgraph.graph import END, StateGraph

from .nodes import (
    check_has_more_chunks,
    detect_interrupt_node,
    extract_text_delta_node,
    extract_tools_node,
    fetch_next_chunk_node,
    parse_chunk_type_node,
    process_updates_node,
    render_generic_tool_node,
    render_question_tool_node,
    render_sql_tool_node,
    route_by_event_type,
    route_by_tool_name,
)


class StreamSubgraphState(TypedDict, total=False):
    """State for stream processing subgraph.

    This state is internal to the subgraph and separate from the parent
    REPLState. The subgraph receives stream_chunks from parent and returns
    render_queue and optional pending_interrupt.

    Input from parent:
        stream_chunks: List of (event_type, data) tuples from SSE stream

    Internal processing state:
        chunk_index: Current position in stream_chunks list
        current_chunk: Currently processing chunk (event_type, data)
        prev_text: Previous cumulative text for delta extraction

    Output accumulation:
        render_queue: List of render items (text deltas, tool calls, etc.)
        pending_interrupt: Interrupt object if HITL was triggered
        usage: Token usage from final chunk

    Control:
        is_complete: Flag indicating all chunks processed or interrupted
    """

    # Input from parent (immutable during subgraph execution)
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


def build_stream_processor_subgraph() -> StateGraph:
    """Build the fine-grained stream processor subgraph.

    This subgraph processes a list of streaming chunks and produces:
    - render_queue: Items to render (text deltas, tool calls, etc.)
    - pending_interrupt: Optional HITL interrupt
    - usage: Optional token usage

    Flow:
    1. fetch_chunk: Get next chunk by index, increment index
    2. check_has_more: Continue if more chunks, else done
    3. parse_chunk: Extract event_type from current_chunk
    4. route_event: Branch based on event type:
       - messages/partial: extract_text_delta
       - messages/complete: extract_tools
       - updates: process_updates
    5. Tool routing (for messages/complete):
       - route_tool: Branch by tool.name
       - Tool-specific render nodes:
         * SQL tools: sql_db_query, sql_db_schema, sql_db_list_tables, sql_db_query_checker
         * Interactive: AskUserQuestion
         * Generic: fallback for unknown tools
    6. Interrupt detection:
       - detect_interrupt: Check for __interrupt__, exit if found
    7. Loop back to fetch_chunk or exit

    Returns:
        Compiled StateGraph ready to use as a node in parent graph
    """
    graph = StateGraph(StreamSubgraphState)  # type: ignore[arg-type]

    # Core processing nodes
    graph.add_node("fetch_chunk", fetch_next_chunk_node)
    graph.add_node("parse_chunk", parse_chunk_type_node)
    graph.add_node("extract_text", extract_text_delta_node)
    graph.add_node("extract_tools", extract_tools_node)
    graph.add_node("process_updates", process_updates_node)
    graph.add_node("detect_interrupt", detect_interrupt_node)

    # Tool-specific rendering nodes
    graph.add_node("render_sql_tool", render_sql_tool_node)
    graph.add_node("render_question_tool", render_question_tool_node)
    graph.add_node("render_generic_tool", render_generic_tool_node)

    # Entry point: fetch first chunk
    graph.set_entry_point("fetch_chunk")

    # After fetching, always parse (fetch sets current_chunk or None)
    graph.add_edge("fetch_chunk", "parse_chunk")

    # Route based on event type (including check for None)
    def route_parse_chunk(state):
        if not state.get("current_chunk"):
            return "done"  # No chunk means we're out of chunks
        return route_by_event_type(state)

    graph.add_conditional_edges(
        "parse_chunk",
        route_parse_chunk,
        {
            "messages/partial": "extract_text",
            "messages/complete": "extract_tools",
            "updates": "process_updates",
            "skip": "fetch_chunk",  # Unknown event, skip
            "done": END,  # No more chunks
        },
    )

    # After extracting text delta, check for more chunks
    graph.add_conditional_edges(
        "extract_text",
        check_has_more_chunks,
        {
            "more": "fetch_chunk",
            "done": END,
        },
    )

    # After extracting tools, route by tool name
    graph.add_conditional_edges(
        "extract_tools",
        route_by_tool_name,
        {
            "sql_db_query": "render_sql_tool",
            "sql_db_schema": "render_sql_tool",
            "sql_db_list_tables": "render_sql_tool",
            "sql_db_query_checker": "render_sql_tool",
            "AskUserQuestion": "render_question_tool",
            "generic": "render_generic_tool",
            "none": "fetch_chunk",  # No tools, continue
        },
    )

    # After tool rendering, check for more chunks
    for tool_node in ["render_sql_tool", "render_question_tool", "render_generic_tool"]:
        graph.add_conditional_edges(
            tool_node,
            check_has_more_chunks,
            {
                "more": "fetch_chunk",
                "done": END,
            },
        )

    # After processing updates, check for interrupt
    graph.add_edge("process_updates", "detect_interrupt")

    # After interrupt detection, either exit (interrupt) or continue
    graph.add_conditional_edges(
        "detect_interrupt",
        lambda state: "interrupt" if state.get("pending_interrupt") else "continue",
        {
            "interrupt": END,  # Exit subgraph immediately
            "continue": "fetch_chunk",  # Process more chunks
        },
    )

    return graph.compile()
