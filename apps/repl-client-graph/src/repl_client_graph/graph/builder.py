"""StateGraph builder for REPL control flow.

This module implements the REPL as a LangGraph StateGraph using the
Coarse-Grained approach (Approach 1 from design doc). Major operations
are implemented as nodes, streaming is handled within a single node,
and control flow is managed via conditional edges.
"""

from typing import Any

from langgraph.graph import END, StateGraph

from .nodes import (
    check_for_interrupt,
    check_should_exit,
    execute_command_node,
    get_input_node,
    handle_interrupt_node,
    process_stream_node,
    render_output_node,
    route_decision,
    route_input_node,
    send_message_node,
    update_session_node,
)
from .state import REPLState


def build_repl_graph() -> Any:
    """Build and compile the REPL StateGraph.

    Creates a StateGraph with REPLState and implements the full REPL control
    flow using coarse-grained nodes and conditional edges.

    The graph structure:
        1. get_input: Blocking terminal input
        2. route_input: Classify input type
        3. execute_command: Handle slash commands
        4. send_message: Initiate streaming to LangGraph server
        5. process_stream: Process all SSE chunks
        6. handle_interrupt: HITL approval flow
        7. update_session: Update session stats
        8. render_output: Render queued output
        9. Loop back or exit

    Returns:
        Compiled StateGraph ready for execution
    """
    graph = StateGraph(REPLState)  # type: ignore[arg-type]

    # Core nodes - stubbed for now, will be implemented in separate modules
    graph.add_node("get_input", get_input_node)
    graph.add_node("route_input", route_input_node)
    graph.add_node("execute_command", execute_command_node)
    graph.add_node("send_message", send_message_node)
    graph.add_node("process_stream", process_stream_node)
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

    # Message flow - send, stream, optionally interrupt, update, render
    graph.add_edge("send_message", "process_stream")
    graph.add_conditional_edges(
        "process_stream",
        check_for_interrupt,
        {
            "interrupt": "handle_interrupt",
            "complete": "update_session",
        },
    )

    # After interrupt approval, resume streaming
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
