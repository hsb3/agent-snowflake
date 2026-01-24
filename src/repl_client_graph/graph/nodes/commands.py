"""Command execution node for REPL StateGraph.

Handles slash command execution. Phase 1 includes basic /help and /exit handlers inline.
Phase 2 adds /agents, /threads, /new, /info, /clear, and /session commands.
"""

from repl_client_graph.context import get_client, get_session
from repl_client_graph.graph.state import REPLState

# Module-level agent cache: name/graph_id → assistant_id
_agent_cache: dict[str, str] = {}


async def execute_command_node(state: REPLState) -> REPLState:
    """Execute slash command.

    Phase 1: Basic inline handlers for /help and /exit.
    Phase 2: Adds /agents, /threads, /new commands.

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

    # Route to handlers
    if cmd_name == "/help":
        return _handle_help(state, cmd_args)
    elif cmd_name == "/exit":
        return _handle_exit(state, cmd_args)
    elif cmd_name == "/agents":
        return await _handle_agents(state, cmd_args)
    elif cmd_name == "/threads":
        return await _handle_threads(state, cmd_args)
    elif cmd_name == "/new":
        return await _handle_new(state, cmd_args)
    elif cmd_name == "/info":
        return _handle_info(state, cmd_args)
    elif cmd_name == "/clear":
        return _handle_clear(state, cmd_args)
    elif cmd_name == "/session":
        return _handle_session(state, cmd_args)
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
        args: Command arguments (unused)

    Returns:
        Updated state with help text in render queue
    """
    help_text = """
Available Commands:
  /help              Show this help message
  /exit              Exit the REPL
  /agents [name]     List agents or switch to agent
  /agents <name> -n  Switch to agent with new thread
  /threads [id]      List threads or resume thread
  /new               Create new thread
  /info              Show session info
  /clear             Clear the screen
  /session           Show full session state dump

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


# Phase 2 Command Handlers


async def _resolve_agent_id(identifier: str) -> str | None:
    """Resolve agent name/graph_id to assistant_id UUID.

    Args:
        identifier: Can be assistant_id (UUID) or graph_id/name

    Returns:
        assistant_id UUID or None if not found
    """
    client = get_client()

    # If it looks like a UUID, use it directly
    if "-" in identifier and len(identifier) > 30:
        return identifier

    # Check cache first
    if identifier in _agent_cache:
        return _agent_cache[identifier]

    # Cache miss - fetch agents and populate cache
    try:
        agents = await client.list_agents()
        for agent in agents:
            assistant_id = agent.get("assistant_id", "")
            graph_id = agent.get("graph_id", "")
            name = agent.get("name", "")

            if graph_id:
                _agent_cache[graph_id] = assistant_id
            if name and name != graph_id:
                _agent_cache[name] = assistant_id

        # Try lookup again
        return _agent_cache.get(identifier)
    except Exception:
        return None


async def _handle_agents(state: REPLState, args: list[str]) -> REPLState:
    """Handle /agents command.

    Args:
        state: Current REPL state
        args: Optional agent_id/name to switch to, with optional --new flag

    Returns:
        Updated state with agents list or switch confirmation
    """
    client = get_client()
    session = get_session()

    if args:
        # Parse arguments
        agent_identifier = args[0]
        create_new_thread = "--new" in args or "-n" in args

        # Resolve name to UUID if needed
        agent_id = await _resolve_agent_id(agent_identifier)
        if not agent_id:
            return {
                **state,
                "render_queue": [
                    {
                        "type": "error",
                        "content": f"Agent not found: {agent_identifier}\nUse /agents to see available agents",
                    }
                ],
                "command_result": {"status": "error", "command": "/agents"},
            }

        # Switch to specified agent
        session.set_agent(agent_id)

        # Optionally create new thread
        if create_new_thread:
            try:
                new_thread_id = await client.create_thread()
                session.set_thread(new_thread_id)
                return {
                    **state,
                    "current_assistant_id": agent_id,
                    "current_thread_id": new_thread_id,
                    "render_queue": [
                        {
                            "type": "success",
                            "content": f"Switched to agent: {agent_identifier}\nCreated new thread: {new_thread_id}",
                        }
                    ],
                    "command_result": {"status": "success", "command": "/agents"},
                }
            except Exception as e:
                return {
                    **state,
                    "render_queue": [
                        {
                            "type": "error",
                            "content": f"Failed to create new thread: {e}",
                        }
                    ],
                    "command_result": {"status": "error", "command": "/agents"},
                }
        else:
            return {
                **state,
                "current_assistant_id": agent_id,
                "render_queue": [
                    {
                        "type": "success",
                        "content": f"Switched to agent: {agent_identifier}",
                    }
                ],
                "command_result": {"status": "success", "command": "/agents"},
            }
    else:
        # List all agents
        try:
            agents = await client.list_agents()
            if not agents:
                return {
                    **state,
                    "render_queue": [
                        {
                            "type": "text",
                            "content": "No agents available",
                            "style": "yellow",
                        }
                    ],
                    "command_result": {"status": "success", "command": "/agents"},
                }

            # Populate cache
            for agent in agents:
                assistant_id = agent.get("assistant_id", "")
                graph_id = agent.get("graph_id", "")
                name = agent.get("name", "")

                if graph_id:
                    _agent_cache[graph_id] = assistant_id
                if name and name != graph_id:
                    _agent_cache[name] = assistant_id

            # Build table
            headers = ["Name (use this)", "Assistant ID", "Current"]
            rows = []
            for agent in agents:
                graph_id = agent.get("graph_id", "unknown")
                assistant_id = agent.get("assistant_id", "unknown")
                is_current = "✓" if assistant_id == state.get("current_assistant_id") else ""
                rows.append([graph_id, assistant_id[:8] + "...", is_current])

            return {
                **state,
                "render_queue": [
                    {
                        "type": "table",
                        "headers": headers,
                        "rows": rows,
                    }
                ],
                "command_result": {"status": "success", "command": "/agents"},
            }
        except Exception as e:
            return {
                **state,
                "render_queue": [
                    {
                        "type": "error",
                        "content": f"Failed to list agents: {e}",
                    }
                ],
                "command_result": {"status": "error", "command": "/agents"},
            }


async def _handle_threads(state: REPLState, args: list[str]) -> REPLState:
    """Handle /threads command.

    Args:
        state: Current REPL state
        args: Optional thread_id to resume

    Returns:
        Updated state with threads list or resume confirmation
    """
    client = get_client()
    session = get_session()

    if args:
        # Resume specified thread
        thread_id = args[0]
        session.set_thread(thread_id)
        return {
            **state,
            "current_thread_id": thread_id,
            "render_queue": [
                {
                    "type": "success",
                    "content": f"Resumed thread: {thread_id}",
                }
            ],
            "command_result": {"status": "success", "command": "/threads"},
        }
    else:
        # List all threads
        try:
            threads = await client.list_threads()
            if not threads:
                return {
                    **state,
                    "render_queue": [
                        {
                            "type": "text",
                            "content": "No threads available",
                            "style": "yellow",
                        }
                    ],
                    "command_result": {"status": "success", "command": "/threads"},
                }

            # Build table
            headers = ["Thread ID", "Current"]
            rows = []
            for thread in threads:
                thread_id = thread.get("thread_id", "unknown")
                is_current = "✓" if thread_id == state.get("current_thread_id") else ""
                rows.append([thread_id, is_current])

            return {
                **state,
                "render_queue": [
                    {
                        "type": "table",
                        "headers": headers,
                        "rows": rows,
                    }
                ],
                "command_result": {"status": "success", "command": "/threads"},
            }
        except Exception as e:
            return {
                **state,
                "render_queue": [
                    {
                        "type": "error",
                        "content": f"Failed to list threads: {e}",
                    }
                ],
                "command_result": {"status": "error", "command": "/threads"},
            }


async def _handle_new(state: REPLState, args: list[str]) -> REPLState:
    """Handle /new command.

    Args:
        state: Current REPL state
        args: Unused

    Returns:
        Updated state with new thread ID
    """
    client = get_client()
    session = get_session()

    try:
        thread_id = await client.create_thread()
        session.set_thread(thread_id)
        return {
            **state,
            "current_thread_id": thread_id,
            "render_queue": [
                {
                    "type": "success",
                    "content": f"Created new thread: {thread_id}",
                }
            ],
            "command_result": {"status": "success", "command": "/new"},
        }
    except Exception as e:
        return {
            **state,
            "render_queue": [
                {
                    "type": "error",
                    "content": f"Failed to create thread: {e}",
                }
            ],
            "command_result": {"status": "error", "command": "/new"},
        }


def _handle_info(state: REPLState, args: list[str]) -> REPLState:
    """Handle /info command.

    Args:
        state: Current REPL state
        args: Command arguments (unused)

    Returns:
        Updated state with session info in render queue
    """
    session = get_session()
    summary = session.get_display_summary()

    return {
        **state,
        "render_queue": [
            {
                "type": "panel",
                "content": summary,
                "title": "Session Info",
                "style": "blue",
            }
        ],
        "command_result": {"status": "success", "command": "/info"},
    }


def _handle_clear(state: REPLState, args: list[str]) -> REPLState:
    """Handle /clear command.

    Args:
        state: Current REPL state
        args: Command arguments (unused)

    Returns:
        Updated state with clear directive in render queue
    """
    return {
        **state,
        "render_queue": [
            {
                "type": "clear",
            }
        ],
        "command_result": {"status": "success", "command": "/clear"},
    }


def _handle_session(state: REPLState, args: list[str]) -> REPLState:
    """Handle /session command - show full session state dump.

    Args:
        state: Current REPL state
        args: Command arguments (unused)

    Returns:
        Updated state with detailed session dump in render queue
    """
    session = get_session()

    # Build detailed session dump
    lines = [
        f"Thread ID: {session.current_thread_id or 'None'}",
        f"Agent ID: {session.current_assistant_id or 'None'}",
        "",
        "Token Usage:",
        f"  Input: {session.session_tokens['input']}",
        f"  Output: {session.session_tokens['output']}",
        f"  Total: {session.session_tokens['total']}",
        "",
        f"Session Start: {session.session_start_time}",
    ]

    content = "\n".join(lines)

    return {
        **state,
        "render_queue": [
            {
                "type": "panel",
                "content": content,
                "title": "Full Session State",
                "style": "blue",
            }
        ],
        "command_result": {"status": "success", "command": "/session"},
    }
