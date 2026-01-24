"""Command execution node for REPL StateGraph.

Handles slash command execution. Phase 1 includes basic /help and /exit handlers inline.
Full command registry integration will be added in later phases.
"""

from repl_client_graph.graph.state import REPLState


def execute_command_node(state: REPLState) -> REPLState:
    """Execute slash command.

    Phase 1: Basic inline handlers for /help and /exit.
    Phase 2+: Will integrate with CommandRegistry for full command support.

    Args:
        state: Current REPL state with user_input containing command

    Returns:
        Updated state with command_result and render_queue populated
    """
    user_input = state.get("user_input", "")
    command = user_input.strip()

    # Parse command and args
    parts = command.split()
    cmd_name = parts[0] if parts else ""
    cmd_args = parts[1:] if len(parts) > 1 else []

    # Phase 1 handlers - inline for simplicity
    if cmd_name == "/help":
        return _handle_help(state, cmd_args)
    elif cmd_name == "/exit":
        return _handle_exit(state, cmd_args)
    else:
        # Unknown command
        return {
            **state,
            "render_queue": [
                {
                    "type": "error",
                    "content": f"Unknown command: {cmd_name}",
                }
            ],
            "command_result": {"status": "error", "command": cmd_name},
        }


def _handle_help(state: REPLState, args: list[str]) -> REPLState:
    """Handle /help command.

    Args:
        state: Current REPL state
        args: Command arguments (unused in Phase 1)

    Returns:
        Updated state with help text in render queue
    """
    help_text = """
Available Commands (Phase 1):
  /help     Show this help message
  /exit     Exit the REPL

Phase 2 commands (coming soon):
  /agents   List and switch agents
  /threads  List and resume threads
  /new      Create new thread
  /info     Show session info

Type a message (without /) to chat with the agent.
"""

    return {
        **state,
        "render_queue": [
            {
                "type": "panel",
                "content": help_text.strip(),
                "title": "REPL Help",
                "style": "blue",
            }
        ],
        "command_result": {"status": "success", "command": "/help"},
    }


def _handle_exit(state: REPLState, args: list[str]) -> REPLState:
    """Handle /exit command.

    Args:
        state: Current REPL state
        args: Command arguments (unused)

    Returns:
        Updated state with should_exit flag set
    """
    return {
        **state,
        "should_exit": True,
        "render_queue": [
            {
                "type": "success",
                "content": "Exiting REPL...",
            }
        ],
        "command_result": {"status": "success", "command": "/exit"},
    }
