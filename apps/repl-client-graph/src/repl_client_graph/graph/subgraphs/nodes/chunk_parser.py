"""Chunk parser node - parse chunk type and route."""


def parse_chunk_type_node(state: dict) -> dict:
    """Parse chunk to extract event type.

    This node doesn't transform the chunk, just ensures it's available
    for routing. The actual routing happens in route_by_event_type.

    Args:
        state: Subgraph state with current_chunk

    Returns:
        State unchanged (parsing happens in routing function)
    """
    # No transformation needed - routing edge will inspect current_chunk
    return state


def route_by_event_type(state: dict) -> str:
    """Conditional edge: route based on event type.

    Routes chunks to different processing nodes based on SSE event type:
    - messages/partial: Text streaming in progress
    - messages/complete: Final message with tool calls
    - updates: State updates (may contain __interrupt__)
    - Other: Skip unknown events

    Args:
        state: Subgraph state with current_chunk

    Returns:
        Routing key for conditional edge
    """
    current_chunk = state.get("current_chunk")

    if not current_chunk:
        print("[ROUTER] No current chunk")
        return "skip"

    event_type, _data = current_chunk

    print(f"[ROUTER] Routing event: {event_type}")

    # Route based on event type
    if event_type == "messages/partial":
        return "messages/partial"
    elif event_type == "messages/complete":
        return "messages/complete"
    elif event_type == "updates":
        return "updates"
    else:
        # Unknown event type - skip
        print(f"[ROUTER] Unknown event type: {event_type}, skipping")
        return "skip"
