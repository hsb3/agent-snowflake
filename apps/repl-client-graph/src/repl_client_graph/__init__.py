"""REPL Client StateGraph Implementation.

This package implements the REPL as a LangGraph StateGraph, providing
structured state management, control flow, and execution orchestration.

The StateGraph approach offers:
- Automatic state propagation through nodes
- Visual execution graph for debugging
- Checkpoint/resume capability
- Native HITL interrupt handling
- Better testing via state injection

Usage:
    from repl_client_graph import build_repl_graph, REPLState

    # Build graph
    graph = build_repl_graph()

    # Initialize state
    initial_state = REPLState(
        user_input="",
        current_assistant_id="agent_enhanced",
        should_exit=False,
        ...
    )

    # Run graph
    final_state = graph.invoke(initial_state)
"""

from .graph import REPLState, build_repl_graph

__all__ = ["build_repl_graph", "REPLState"]
