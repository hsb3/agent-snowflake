"""HITL interrupt handling node for REPL StateGraph.

Phase 2 implementation - stub for now.
"""

from repl_client_graph.graph.state import REPLState


def handle_interrupt_node(state: REPLState) -> REPLState:
    """Handle HITL approval prompt (Phase 2).

    This is a stub for Phase 1. Full implementation will:
    1. Display tool approval prompt to user
    2. Get approval decision (y/n)
    3. Resume streaming with approval status

    Args:
        state: Current REPL state with pending_interrupt

    Returns:
        Updated state (stub - just clears interrupt for now)
    """
    # Phase 2 implementation will:
    # - Get interrupt details from state
    # - Render approval prompt via renderer
    # - Get user input (y/n)
    # - Call client.resume_after_interrupt() with approval
    # - Collect new stream chunks
    # - Return updated state with new chunks

    # For Phase 1, just clear the interrupt
    return {
        **state,
        "pending_interrupt": None,
        "interrupt_approved": False,
    }
