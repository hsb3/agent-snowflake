"""Text delta extraction node."""


def extract_text_delta_node(state: dict) -> dict:
    """Extract text delta from messages/partial chunk.

    The messages stream returns cumulative text, so we need to extract
    the delta (new text since last chunk) for incremental rendering.

    Flow:
    1. Extract current text from chunk
    2. Compare with prev_text to get delta
    3. Add delta to render_queue
    4. Update prev_text for next iteration

    Args:
        state: Subgraph state with current_chunk and prev_text

    Returns:
        Updated state with render_queue entry and updated prev_text
    """
    current_chunk = state.get("current_chunk")
    prev_text = state.get("prev_text", "")
    render_queue = list(state.get("render_queue", []))

    if not current_chunk:
        return state

    event_type, data = current_chunk

    # Extract text from messages/partial
    # Data is a list of messages, we want the last one (AI response)
    if isinstance(data, list) and data:
        message = data[-1]
        if isinstance(message, dict):
            content = message.get("content", [])
            if content and isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        current_text = block.get("text", "")

                        # Extract delta
                        if current_text and current_text != prev_text:
                            delta = current_text[len(prev_text):]
                            if delta:
                                # Add to render queue
                                render_queue.append({
                                    "type": "text",
                                    "content": delta,
                                })
                                # Update prev_text
                                prev_text = current_text

    return {
        **state,
        "render_queue": render_queue,
        "prev_text": prev_text,
    }
