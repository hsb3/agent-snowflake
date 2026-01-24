"""Tool extraction and routing nodes."""


def extract_tools_node(state: dict) -> dict:
    """Extract tool calls and usage from messages/complete chunk.

    The messages/complete event contains:
    - tool_calls: List of tools the agent wants to invoke
    - usage_metadata: Token usage for the completion

    This node extracts both and stores them in state for routing
    and final output.

    Args:
        state: Subgraph state with current_chunk

    Returns:
        Updated state with usage and prepared for tool routing
    """
    current_chunk = state.get("current_chunk")
    usage = state.get("usage")

    if not current_chunk:
        return state

    event_type, data = current_chunk

    # Extract from messages/complete
    # Data is a list of messages, we want the last one (AI response)
    if isinstance(data, list) and data:
        message = data[-1]
        if isinstance(message, dict):
            # Extract usage metadata
            usage_metadata = message.get("usage_metadata")
            if usage_metadata:
                usage = {
                    "input_tokens": usage_metadata.get("input_tokens", 0),
                    "output_tokens": usage_metadata.get("output_tokens", 0),
                    "total_tokens": usage_metadata.get("total_tokens", 0),
                }

    return {
        **state,
        "usage": usage,
    }


def route_by_tool_name(state: dict) -> str:
    """Conditional edge: route based on tool name.

    Routes to tool-specific rendering nodes based on the first tool
    in the tool_calls array. Different tools need different UI formatting:
    - sql_db_query: Show formatted SQL with syntax highlighting
    - sql_db_schema: Show table/schema info
    - AskUserQuestion: Custom UI for user input prompts
    - Other: Generic tool display

    Args:
        state: Subgraph state with current_chunk

    Returns:
        Routing key for conditional edge
    """
    current_chunk = state.get("current_chunk")

    if not current_chunk:
        return "none"

    event_type, data = current_chunk

    # Extract tool calls from messages/complete
    if isinstance(data, list) and data:
        message = data[-1]
        if isinstance(message, dict):
            tool_calls = message.get("tool_calls", [])
            if tool_calls and isinstance(tool_calls, list):
                # Route based on first tool
                first_tool = tool_calls[0]
                if isinstance(first_tool, dict):
                    tool_name = first_tool.get("name", "")

                    # Route to specific handler
                    if tool_name in ("sql_db_query", "sql_db_schema"):
                        return "sql_db_query"
                    elif tool_name == "AskUserQuestion":
                        return "AskUserQuestion"
                    else:
                        return "generic"

    return "none"
