"""Main entry point for StateGraph-based REPL.

This module initializes the REPL using LangGraph StateGraph for control flow.

Entry point: python -m repl_client_graph
"""

import asyncio
import sys
import time

from repl_client.core.client import LangGraphClient
from repl_client.core.config import Config
from repl_client.core.session import SessionState
from repl_client.ui.renderer import Renderer

from repl_client_graph.context import (
    set_client,
    set_renderer,
    set_session,
    set_hitl_handler,
    set_tool_registry,
)
from repl_client_graph.graph import REPLState, build_repl_graph
from repl_client_graph.streaming.hitl import HITLHandler
from repl_client_graph.ui.content_blocks import ToolRenderRegistry


async def main() -> int:
    """Main entry point for StateGraph REPL.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Load configuration
        config = Config.from_env()

        # Initialize components
        client = LangGraphClient(base_url=config.server_url, timeout=30)
        renderer = Renderer()
        session = SessionState()
        tool_registry = ToolRenderRegistry()
        hitl_handler = HITLHandler(renderer, tool_registry)

        # Set up context vars for dependency injection
        set_client(client)
        set_renderer(renderer)
        set_session(session)
        set_tool_registry(tool_registry)
        set_hitl_handler(hitl_handler)

        # Test connection
        renderer.render_text("Connecting to LangGraph server...", style="cyan")
        connected = await client.connect()

        if not connected:
            renderer.render_error(
                f"Failed to connect to server at {config.server_url}\n"
                f"Make sure the LangGraph dev server is running:\n"
                f"  langgraph dev\n"
                f"or\n"
                f"  make dev"
            )
            return 1

        renderer.render_success(f"Connected to {config.server_url}")

        # List agents and set default
        agents = await client.list_agents(limit=10)
        if agents:
            # Use config default if set, otherwise use first agent
            if config.default_agent:
                agent_id = config.default_agent
            else:
                agent_id = agents[0].get("assistant_id", "")

            session.set_agent(agent_id)
            renderer.render_text(f"Using agent: {agent_id}", style="cyan")
        else:
            renderer.render_text("Warning: No agents available", style="yellow")

        # Create initial thread
        thread_id = await client.create_thread()
        session.set_thread(thread_id)

        # Show welcome banner
        welcome = (
            "Welcome to LangGraph REPL (StateGraph Edition)!\n\n"
            "Type your message to chat with the agent.\n"
            "Type /help for available commands.\n"
            "Type /exit to quit.\n\n"
            "Powered by LangGraph StateGraph for control flow.\n"
            "Dual streaming mode: messages (LLM tokens) + updates (state changes)."
        )
        renderer.render_panel(welcome, "LangGraph REPL", style="blue")

        # Build the REPL graph
        repl_graph = build_repl_graph()

        # Create initial state with all required fields
        initial_state: REPLState = {
            "user_input": "",
            "input_type": None,
            "current_thread_id": session.current_thread_id,
            "current_assistant_id": session.current_assistant_id,
            "current_run_id": None,
            "stream_chunks": [],
            "stream_buffer": {},
            "render_queue": [],
            "pending_interrupt": None,
            "interrupt_approved": None,
            "session_tokens": {"input": 0, "output": 0, "total": 0},
            "session_start_time": session.session_start_time,
            "message_count": 0,
            "should_exit": False,
            "error": None,
            "command_result": None,
        }

        # Run the REPL graph
        renderer.render_text("\nStarting REPL loop...\n", style="green")

        try:
            final_state = await repl_graph.ainvoke(initial_state)
            session.session_tokens = final_state.get("session_tokens", session.session_tokens)
            session.message_count = final_state.get("message_count", 0)
        except KeyboardInterrupt:
            renderer.render_text("\n\nInterrupted by user", style="yellow")
            final_state = initial_state
        except Exception as e:
            renderer.render_error(f"\nGraph execution error: {e}")
            import traceback

            traceback.print_exc()
            final_state = initial_state

        # Show session summary
        duration = time.time() - session.session_start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        token_summary = session.get_token_summary()
        summary = (
            f"Session Duration: {minutes}m {seconds}s\n"
            f"Tokens Used: {token_summary['total']} "
            f"({token_summary['input']} in / {token_summary['output']} out)"
        )

        renderer.render_panel(summary, "Session Summary", style="blue")

        return 0

    except KeyboardInterrupt:
        if "renderer" in locals():
            renderer.render_text("\nInterrupted by user", style="yellow")
        return 0

    except Exception as e:
        if "renderer" in locals():
            renderer.render_error(f"Fatal error: {e}")
        else:
            print(f"Fatal error: {e}", file=sys.stderr)
        return 1


def entry_point() -> None:
    """Synchronous entry point wrapper."""
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


if __name__ == "__main__":
    entry_point()
