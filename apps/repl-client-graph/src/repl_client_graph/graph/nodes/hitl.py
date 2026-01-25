"""HITL interrupt handling node for REPL StateGraph.

Phase 2 implementation - handles HITL interrupts.
"""

from repl_client_graph.context import get_client, get_hitl_handler, get_session
from repl_client_graph.graph.state import REPLState
from repl_client_graph.streaming.types import Interrupt


async def handle_interrupt_node(state: REPLState) -> REPLState:
    """Handle HITL approval prompt (Phase 2).

    This implementation:
    1. Gets pending interrupt from state
    2. Uses HITLHandler to display approval prompt and get decision
    3. Calls client.resume_after_interrupt() with approval
    4. Collects resume stream chunks
    5. Returns updated state with new chunks

    Args:
        state: Current REPL state with pending_interrupt

    Returns:
        Updated state with stream_chunks from resume and cleared interrupt
    """
    # Get dependencies from context
    client = get_client()
    hitl_handler = get_hitl_handler()
    session = get_session()

    # Get pending interrupt from state
    pending_interrupt = state.get("pending_interrupt")
    if not pending_interrupt:
        # No interrupt to handle - shouldn't happen
        return {
            **state,
            "pending_interrupt": None,
        }

    # Convert dict to Interrupt object
    interrupt = Interrupt(
        id=pending_interrupt.get("id", ""), value=pending_interrupt.get("value", {})
    )

    # Use HITLHandler to show approval prompt and get decision
    # Returns {"resume": {"approve": bool}}
    resume_command = hitl_handler.handle_interrupt(interrupt, session)
    approved = resume_command.get("resume", {}).get("approve", False)

    # Get thread and assistant IDs
    thread_id = session.current_thread_id
    assistant_id = session.current_assistant_id

    if not thread_id or not assistant_id:
        # Can't resume without thread ID and assistant ID
        return {
            **state,
            "pending_interrupt": None,
            "render_queue": [
                {
                    "type": "error",
                    "content": "Cannot resume: no active thread or assistant",
                }
            ],
        }

    # Call client.resume_after_interrupt() with approval
    chunks = []
    try:
        async for chunk in client.resume_after_interrupt(thread_id, assistant_id, approved):
            chunks.append(chunk)
    except Exception as e:
        # Handle resume error
        return {
            **state,
            "pending_interrupt": None,
            "render_queue": [
                {
                    "type": "error",
                    "content": f"Failed to resume after interrupt: {e}",
                }
            ],
        }

    # Return updated state with new stream chunks
    return {
        **state,
        "stream_chunks": chunks,
        "pending_interrupt": None,
        "interrupt_approved": approved,
    }
