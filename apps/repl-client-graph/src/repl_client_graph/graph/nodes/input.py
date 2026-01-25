"""Input handling nodes for REPL StateGraph.

Nodes for getting user input and routing it to appropriate handlers.
"""

from repl_client_graph.context import get_session
from repl_client_graph.graph.state import REPLState


def get_input_node(state: REPLState) -> REPLState:
    """Get user input from terminal (blocking).

    Renders a prompt based on current agent and waits for user input.

    Args:
        state: Current REPL state

    Returns:
        Updated state with user_input populated
    """
    session = get_session()

    # Render prompt - show agent name if available
    agent_name = session.current_assistant_id or "repl"
    prompt = f"[{agent_name}] > "

    # Get input (blocking) - using built-in input() for Phase 1
    user_input = input(prompt).strip()

    return {
        **state,
        "user_input": user_input,
        "input_type": None,  # Will be determined by route_input_node
    }


def route_input_node(state: REPLState) -> REPLState:
    """Classify input type for routing.

    Examines user_input and determines if it's a command, message, or empty.
    Special handling for /exit command to set should_exit flag.

    Args:
        state: Current REPL state with user_input

    Returns:
        Updated state with input_type set
    """
    user_input = state.get("user_input", "")

    # Empty input - loop back to get_input
    if not user_input:
        return {**state, "input_type": "empty"}

    # Exit command - set exit flag
    if user_input.strip() == "/exit":
        return {
            **state,
            "input_type": "exit",
            "should_exit": True,
        }

    # Command (starts with /)
    if user_input.startswith("/"):
        return {**state, "input_type": "command"}

    # Regular message
    return {**state, "input_type": "message"}


def route_decision(state: REPLState) -> str:
    """Conditional edge routing function.

    Used by LangGraph conditional_edges to determine next node.

    Args:
        state: Current REPL state

    Returns:
        String key for routing: "command", "message", "empty", or "exit"
    """
    return state.get("input_type", "empty")
