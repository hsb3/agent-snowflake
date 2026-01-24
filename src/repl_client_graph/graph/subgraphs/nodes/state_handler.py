"""State update and interrupt handling nodes."""

from dataclasses import asdict

from repl_client_graph.streaming.types import Interrupt


def process_updates_node(state: dict) -> dict:
    """Process updates event from stream.

    The updates stream contains state changes after each graph step.
    These are added to render_queue for visibility (debugging).

    Note: __interrupt__ detection happens in detect_interrupt_node.

    Args:
        state: Subgraph state with current_chunk

    Returns:
        Updated state with render_queue entry for state update
    """
    current_chunk = state.get("current_chunk")
    render_queue = list(state.get("render_queue", []))

    if not current_chunk:
        return state

    event_type, data = current_chunk

    # Add state update to render queue
    if isinstance(data, dict):
        render_queue.append({
            "type": "state_update",
            "content": data,
        })

    return {
        **state,
        "render_queue": render_queue,
    }


def detect_interrupt_node(state: dict) -> dict:
    """Detect HITL interrupt in updates stream.

    Checks for __interrupt__ key in updates data. If found:
    1. Extract interrupt payload
    2. Create Interrupt object
    3. Set pending_interrupt in state
    4. Subgraph will exit via conditional edge

    The __interrupt__ signal indicates the server has paused execution
    and is waiting for user approval (HITL pattern).

    Args:
        state: Subgraph state with current_chunk

    Returns:
        Updated state with pending_interrupt if interrupt detected
    """
    current_chunk = state.get("current_chunk")
    pending_interrupt = state.get("pending_interrupt")

    if not current_chunk:
        return state

    event_type, data = current_chunk

    # Only check updates events
    if event_type == "updates" and isinstance(data, dict):
        # Check for __interrupt__ signal
        if "__interrupt__" in data:
            interrupt_list = data["__interrupt__"]

            # Extract interrupt data (list format from server)
            if isinstance(interrupt_list, list) and len(interrupt_list) > 0:
                interrupt_data = interrupt_list[0]  # Take first interrupt

                if isinstance(interrupt_data, dict):
                    # Extract value (contains tool info)
                    value = interrupt_data.get("value", {})

                    # Generate interrupt ID
                    tool_name = value.get("tool", "unknown")
                    interrupt_id = f"interrupt_{tool_name}_{id(interrupt_data)}"

                    # Create Interrupt object and convert to dict for state
                    interrupt_obj = Interrupt(
                        id=interrupt_id,
                        value=value
                    )
                    pending_interrupt = asdict(interrupt_obj)

    return {
        **state,
        "pending_interrupt": pending_interrupt,
    }
