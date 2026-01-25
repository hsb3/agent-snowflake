"""Streaming nodes for REPL StateGraph.

Nodes for sending messages to LangGraph server and processing streaming responses.
"""

from dataclasses import asdict

from repl_client_graph.core.parsers import parse_message_chunk
from repl_client_graph.context import get_client, get_session
from repl_client_graph.graph.state import REPLState
from repl_client_graph.streaming.types import ChunkType, Interrupt


async def send_message_node(state: REPLState) -> REPLState:
    """Initiate streaming request to LangGraph server.

    Creates thread if needed, sends message, and collects stream chunks.

    Args:
        state: Current REPL state with user_input

    Returns:
        Updated state with stream_chunks and thread_id populated
    """
    client = get_client()
    session = get_session()

    # Ensure we have thread and agent
    thread_id = session.current_thread_id
    if not thread_id:
        # Create new thread
        thread_id = await client.create_thread()
        session.set_thread(thread_id)

    assistant_id = session.current_assistant_id
    message = state.get("user_input", "")

    # Stream message - collect chunks
    chunks = []
    async for chunk in client.stream_message(thread_id, message, assistant_id):
        chunks.append(chunk)

    return {
        **state,
        "current_thread_id": thread_id,
        "stream_chunks": chunks,
        "stream_buffer": {},
    }


def process_stream_node(state: REPLState) -> REPLState:
    """Process all streaming chunks (coarse-grained approach).

    Parses chunks, accumulates text deltas, detects tool calls and interrupts.
    Builds render queue for output node.

    Args:
        state: Current REPL state with stream_chunks

    Returns:
        Updated state with render_queue and optional pending_interrupt
    """
    chunks = state.get("stream_chunks", [])
    render_queue = []
    pending_interrupt = None
    usage = None

    # Track previous text for delta extraction
    prev_text = ""

    # Process all chunks
    for event_type, data in chunks:
        try:
            # Handle messages stream mode - data is array of messages
            if event_type in ("messages/partial", "messages/complete"):
                # data is a list of message objects
                if not isinstance(data, list):
                    continue

                # Process last message in array (the AI response)
                if data:
                    message = data[-1]  # Get the most recent message
                    if not isinstance(message, dict):
                        continue

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
                                        render_queue.append(
                                            {
                                                "type": "text",
                                                "content": delta,
                                            }
                                        )
                                    prev_text = current_text

                    # Check for tool calls (in complete messages)
                    if event_type == "messages/complete":
                        tool_calls = message.get("tool_calls", [])
                        if tool_calls:
                            for tool_call in tool_calls:
                                render_queue.append(
                                    {
                                        "type": "tool_call",
                                        "tool": tool_call,
                                    }
                                )

                        # Extract usage if present
                        usage_metadata = message.get("usage_metadata")
                        if usage_metadata:
                            usage = {
                                "input_tokens": usage_metadata.get("input_tokens", 0),
                                "output_tokens": usage_metadata.get("output_tokens", 0),
                                "total_tokens": usage_metadata.get("total_tokens", 0),
                            }

            # Handle updates stream mode - state changes after each step
            elif event_type == "updates":
                # data is a dict with state updates from the step
                if isinstance(data, dict):
                    # Check for interrupt signal first
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
                                interrupt_obj = Interrupt(id=interrupt_id, value=value)
                                pending_interrupt = asdict(interrupt_obj)

                                # Stop processing stream - interrupt stops streaming
                                break

                    # Add state update to render queue for visibility
                    render_queue.append(
                        {
                            "type": "state_update",
                            "content": data,
                        }
                    )

        except Exception as e:
            # Log parse error and continue
            render_queue.append(
                {
                    "type": "error",
                    "content": f"Parse error: {str(e)}",
                }
            )

    return {
        **state,
        "render_queue": render_queue,
        "pending_interrupt": pending_interrupt,
    }


def check_for_interrupt(state: REPLState) -> str:
    """Conditional edge - check if stream was interrupted.

    Args:
        state: Current REPL state

    Returns:
        "interrupt" if pending_interrupt exists, "complete" otherwise
    """
    return "interrupt" if state.get("pending_interrupt") else "complete"
