"""Rendering and session update nodes for REPL StateGraph.

Nodes for rendering output and updating session state.
"""

from repl_client_graph.context import get_renderer, get_session
from repl_client_graph.graph.state import REPLState


def render_output_node(state: REPLState) -> REPLState:
    """Render everything in the render queue.

    Processes render_queue and dispatches to appropriate renderer methods.
    Clears queue after rendering.

    Args:
        state: Current REPL state with render_queue

    Returns:
        Updated state with cleared render_queue
    """
    renderer = get_renderer()
    render_queue = state.get("render_queue", [])

    for item in render_queue:
        item_type = item.get("type")

        if item_type == "text":
            # Streaming text delta - print without newline
            content = item.get("content", "")
            print(content, end="", flush=True)

        elif item_type == "tool_call":
            # Tool call - check for display hints, otherwise generic
            tool = item.get("tool", {})
            tool_name = tool.get("name", "unknown")
            tool_args = tool.get("args", {})
            display = tool.get("display", {})

            # Check for specific display format
            display_format = display.get("format")

            if display_format == "sql":
                # SQL query with syntax highlighting
                query = display.get("query", "")
                renderer.render_code(query, language="sql", title=f"SQL Query ({tool_name})")

            elif display_format == "schema":
                # Schema query
                tables = display.get("tables", [])
                table_list = ", ".join(tables) if tables else "No tables specified"
                renderer.render_panel(
                    f"Requesting schema for tables:\n{table_list}",
                    title="Schema Query",
                    style="blue"
                )

            elif display_format == "list_tables":
                # List tables query
                renderer.render_panel(
                    "Requesting list of database tables...",
                    title="List Tables",
                    style="blue"
                )

            elif display_format == "question":
                # Interactive question prompt
                question = display.get("question", "")
                options = display.get("options", [])

                # Format options list
                if options:
                    options_text = "\nOptions:\n" + "\n".join(f"  - {opt}" for opt in options)
                else:
                    options_text = ""

                content = f"{question}{options_text}"
                renderer.render_panel(content, title="User Question", style="yellow")

            else:
                # Generic tool call panel
                renderer.render_panel(
                    str(tool_args),
                    title=f"Tool Call: {tool_name}",
                    style="yellow",
                )

        elif item_type == "panel":
            # Generic panel
            content = item.get("content", "")
            title = item.get("title", "")
            style = item.get("style", "blue")
            renderer.render_panel(content, title, style)

        elif item_type == "error":
            # Error message
            content = item.get("content", "")
            renderer.render_error(content)

        elif item_type == "success":
            # Success message
            content = item.get("content", "")
            renderer.render_success(content)

        elif item_type == "table":
            # Table rendering
            headers = item.get("headers", [])
            rows = item.get("rows", [])
            renderer.render_table(headers, rows)

        elif item_type == "clear":
            # Clear screen
            renderer.clear()

        elif item_type == "command_result":
            # Command result - already formatted
            content = item.get("content", "")
            title = item.get("title", "Result")
            renderer.render_panel(content, title)

        elif item_type == "state_update":
            # State update from updates stream mode
            # Show state changes in a subtle way
            content = item.get("content", {})
            # Only show non-empty updates
            if content:
                import json
                update_str = json.dumps(content, indent=2)
                renderer.render_text(f"\n[State Update: {len(content)} keys changed]", style="dim")
                # Uncomment below to see full state updates (verbose):
                # renderer.render_panel(update_str, "State Update", style="dim")

    # Print newline after streaming text
    if any(item.get("type") == "text" for item in render_queue):
        print()

    return {
        **state,
        "render_queue": [],  # Clear queue
    }


def update_session_node(state: REPLState) -> REPLState:
    """Update session state after message completion.

    Tracks tokens and increments message count.

    Args:
        state: Current REPL state with usage data

    Returns:
        Updated state with incremented message_count
    """
    session = get_session()
    usage = state.get("usage")

    # Track tokens if available
    if usage:
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        session.track_tokens(input_tokens, output_tokens)

        # Update session_tokens in state for final summary
        session_tokens = {
            "input": session.session_tokens["input"],
            "output": session.session_tokens["output"],
            "total": session.session_tokens["total"],
        }
    else:
        # Keep existing tokens
        session_tokens = state.get("session_tokens", {"input": 0, "output": 0, "total": 0})

    # Increment message count
    message_count = state.get("message_count", 0)

    return {
        **state,
        "message_count": message_count + 1,
        "session_tokens": session_tokens,
    }


def check_should_exit(state: REPLState) -> str:
    """Conditional edge - continue or exit REPL.

    Args:
        state: Current REPL state

    Returns:
        "exit" if should_exit flag is set, "continue" otherwise
    """
    return "exit" if state.get("should_exit") else "continue"
