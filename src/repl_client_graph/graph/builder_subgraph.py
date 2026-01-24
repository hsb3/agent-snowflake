"""Alternative StateGraph builder using process_stream as a subgraph.

This module provides an alternative implementation of build_repl_graph() that
replaces the single process_stream_node with a fine-grained subgraph.

This is a proof-of-concept to compare:
- Single coarse-grained node (builder.py)
- Fine-grained subgraph approach (this file)

Key differences from builder.py:
1. process_stream is a compiled subgraph instead of a single node
2. State transformation needed between REPLState and StreamSubgraphState
3. Higher node invocation count per message
4. Better separation of concerns and tool routing
"""

from typing import Any

from langgraph.graph import END, StateGraph

from .nodes import (
    check_for_interrupt,
    check_should_exit,
    execute_command_node,
    get_input_node,
    handle_interrupt_node,
    render_output_node,
    route_decision,
    route_input_node,
    send_message_node,
    update_session_node,
)
from .nodes.streaming_subgraph import build_process_stream_subgraph
from .state import REPLState


def transform_to_subgraph_input(state: REPLState) -> dict:
    """Transform REPLState to StreamSubgraphState input.

    The subgraph expects:
    - stream_chunks: list[tuple[str, dict]]
    - Initial processing state

    Args:
        state: Current REPL state

    Returns:
        Dictionary compatible with StreamSubgraphState
    """
    return {
        "stream_chunks": state.get("stream_chunks", []),
        "chunk_index": 0,
        "current_chunk": None,
        "current_event_type": None,
        "prev_text": "",
        "render_queue": [],
        "pending_interrupt": None,
        "current_tools": [],
        "tool_index": 0,
        "current_tool": None,
        "processing_complete": False,
    }


def transform_from_subgraph_output(parent_state: REPLState, subgraph_state: dict) -> REPLState:
    """Transform StreamSubgraphState output back to REPLState.

    The subgraph produces:
    - render_queue: list[dict]
    - pending_interrupt: dict | None

    Args:
        parent_state: Original REPL state
        subgraph_state: Output from subgraph

    Returns:
        Updated REPLState with subgraph results
    """
    return {
        **parent_state,
        "render_queue": subgraph_state.get("render_queue", []),
        "pending_interrupt": subgraph_state.get("pending_interrupt"),
    }


def build_repl_graph_with_subgraph() -> Any:
    """Build REPL StateGraph with process_stream as a subgraph.

    This is an alternative to build_repl_graph() from builder.py.
    Instead of using a single process_stream_node, it uses a compiled
    subgraph with fine-grained nodes for chunk processing.

    Differences from builder.py:
    - process_stream is a subgraph (build_process_stream_subgraph())
    - State transformations are handled automatically by LangGraph
    - Higher node count but better separation of concerns

    The graph structure remains the same:
        1. get_input: Blocking terminal input
        2. route_input: Classify input type
        3. execute_command: Handle slash commands
        4. send_message: Initiate streaming to LangGraph server
        5. process_stream: [SUBGRAPH] Process all SSE chunks
        6. handle_interrupt: HITL approval flow
        7. update_session: Update session stats
        8. render_output: Render queued output
        9. Loop back or exit

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(REPLState)  # type: ignore[arg-type]

    # Core nodes - same as builder.py
    graph.add_node("get_input", get_input_node)
    graph.add_node("route_input", route_input_node)
    graph.add_node("execute_command", execute_command_node)
    graph.add_node("send_message", send_message_node)

    # DIFFERENCE: process_stream is a subgraph instead of a single node
    # Wrap the subgraph with state transformation
    def process_stream_wrapper(state: REPLState) -> REPLState:
        """Wrapper that transforms state for subgraph invocation.

        Args:
            state: Parent REPLState

        Returns:
            Updated REPLState with subgraph results
        """
        # Debug: Check input
        chunks = state.get("stream_chunks", [])
        print(f"\n[DEBUG] Wrapper received {len(chunks)} chunks")
        if chunks:
            # Count event types
            from collections import Counter
            event_types = Counter(chunk[0] for chunk in chunks)
            print(f"[DEBUG] Event types: {dict(event_types)}")

        # Transform to subgraph input
        subgraph_input = transform_to_subgraph_input(state)
        print(f"[DEBUG] Subgraph input keys: {list(subgraph_input.keys())}")

        # Invoke subgraph (sync invocation) - build fresh to pick up latest code
        try:
            print("[DEBUG] Invoking subgraph...")
            fresh_subgraph = build_process_stream_subgraph()
            subgraph_output = fresh_subgraph.invoke(subgraph_input)
            print(f"[DEBUG] Subgraph returned: {list(subgraph_output.keys())}")
        except Exception as e:
            print(f"[DEBUG] Subgraph error: {e}")
            import traceback
            traceback.print_exc()
            subgraph_output = subgraph_input  # Return input unchanged on error

        # Transform back to parent state
        result = transform_from_subgraph_output(state, subgraph_output)

        # Debug: Print what we got
        print(f"[DEBUG] Subgraph produced {len(result.get('render_queue', []))} render items")
        if result.get('render_queue'):
            print(f"[DEBUG] First item type: {result['render_queue'][0].get('type')}")

        return result

    graph.add_node("process_stream", process_stream_wrapper)

    # Remaining nodes - same as builder.py
    graph.add_node("handle_interrupt", handle_interrupt_node)
    graph.add_node("update_session", update_session_node)
    graph.add_node("render_output", render_output_node)

    # Entry point - start with input
    graph.set_entry_point("get_input")

    # Flow from input to routing
    graph.add_edge("get_input", "route_input")

    # Routing from input classification
    graph.add_conditional_edges(
        "route_input",
        route_decision,
        {
            "command": "execute_command",
            "message": "send_message",
            "empty": "get_input",  # Loop back for empty input
            "exit": END,
        },
    )

    # Command flow - execute then render
    graph.add_edge("execute_command", "render_output")

    # Message flow - send, stream (subgraph), optionally interrupt, update, render
    graph.add_edge("send_message", "process_stream")

    # SAME: Conditional edge after process_stream
    # The subgraph populates the same state fields (render_queue, pending_interrupt)
    # so the conditional edge logic remains unchanged
    graph.add_conditional_edges(
        "process_stream",
        check_for_interrupt,
        {
            "interrupt": "handle_interrupt",
            "complete": "update_session",
        },
    )

    # After interrupt approval, resume streaming
    # NOTE: In the subgraph version, this would need additional logic
    # to resume from where it left off. For the PoC, we treat interrupt
    # as terminal (processing_complete = True in subgraph)
    graph.add_edge("handle_interrupt", "process_stream")

    # After session update, render output
    graph.add_edge("update_session", "render_output")

    # After rendering, check if we should continue or exit
    graph.add_conditional_edges(
        "render_output",
        check_should_exit,
        {
            "continue": "get_input",
            "exit": END,
        },
    )

    return graph.compile()


if __name__ == "__main__":
    # For quick testing

    # Generate main graph visualization (collapsed)
    repl_graph = build_repl_graph_with_subgraph()
    graph_image = repl_graph.get_graph().draw_mermaid_png()
    with open("docs/assets/graph-based-repl/repl_graph.png", "wb") as f:
        f.write(graph_image)

    # Generate main graph with xray (expanded subgraphs)
    graph_xray = repl_graph.get_graph(xray=True).draw_mermaid_png()
    with open("docs/assets/graph-based-repl/repl_graph_xray.png", "wb") as f:
        f.write(graph_xray)

    # Generate subgraph visualization (standalone)
    process_stream_subgraph = build_process_stream_subgraph()
    subgraph_image = process_stream_subgraph.get_graph().draw_mermaid_png()
    with open("docs/assets/graph-based-repl/process_stream_subgraph.png", "wb") as f:
        f.write(subgraph_image)
