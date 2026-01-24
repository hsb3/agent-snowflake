#!/usr/bin/env python3
"""Manual HITL verification script.

This script demonstrates the HITL flow manually:
1. Connects to LangGraph server
2. Sends a message that should trigger a tool call
3. Shows the approval prompt (if HITL configured)
4. Allows manual approval/rejection
5. Shows the final response

Usage:
    uv run python scripts/repl_client/tests/test_hitl_manual.py

Prerequisites:
- LangGraph server running (http://localhost:2024)
- Agent with HITL enabled (e.g., agent_enhanced)
- Agent must have interrupt_before or interrupt_after configured

Expected flow:
    1. Script sends: "Query the customers table"
    2. Agent plans to use sql_db_query tool
    3. Server sends __interrupt__ signal
    4. Script shows approval prompt with SQL query
    5. User types 'y' or 'n'
    6. Script resumes execution
    7. If approved: Shows query results
    8. If rejected: Shows agent's response to rejection
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repl_client.core.client import LangGraphClient
from repl_client.core.session import SessionState
from repl_client.streaming.handler import StreamHandler
from repl_client.streaming.hitl import HITLHandler
from repl_client.streaming.types import ChunkType
from repl_client.ui.renderer import Renderer


async def main():
    """Run manual HITL test"""
    print("=" * 80)
    print("HITL Manual Verification Script")
    print("=" * 80)
    print()

    # Initialize components
    renderer = Renderer()
    client = LangGraphClient(base_url="http://localhost:2024", timeout=30)
    session = SessionState()
    stream_handler = StreamHandler(session=session)
    hitl_handler = HITLHandler(renderer=renderer)

    # Connect to server
    print("1. Connecting to LangGraph server...")
    connected = await client.connect()

    if not connected:
        renderer.render_error("Failed to connect to server at http://localhost:2024")
        renderer.render_text(
            "\nMake sure LangGraph server is running:\n"
            "  cd src/agent_snowflake\n"
            "  langgraph dev\n",
            style="yellow"
        )
        return 1

    renderer.render_success("Connected to server")
    print()

    # List agents and find HITL-enabled one
    print("2. Looking for HITL-enabled agent...")
    agents = await client.list_agents(limit=10)

    if not agents:
        renderer.render_error("No agents found on server")
        return 1

    # Try to find agent_enhanced or use first agent
    agent_id = None
    for agent in agents:
        aid = agent.get("assistant_id", "")
        if "enhanced" in aid:
            agent_id = aid
            break

    if not agent_id:
        agent_id = agents[0].get("assistant_id", "")
        renderer.render_text(
            f"Warning: Could not find 'agent_enhanced'. Using {agent_id}",
            style="yellow"
        )
        renderer.render_text(
            "This agent may not have HITL enabled. Check graph2.py configuration.",
            style="yellow"
        )
    else:
        renderer.render_success(f"Found HITL-enabled agent: {agent_id}")

    session.set_agent(agent_id)
    print()

    # Create thread
    print("3. Creating thread...")
    thread_id = await client.create_thread()
    session.set_thread(thread_id)
    renderer.render_success(f"Created thread: {thread_id}")
    print()

    # Send message that should trigger tool call
    print("4. Sending message that should trigger tool call...")
    message = "Query the customers table and show me the first 3 rows"
    renderer.render_text(f"Message: {message}", style="green")
    print()

    # Stream message
    print("5. Processing response stream...")
    print()
    renderer.console.print("Agent: ", style="cyan", end="")

    chunks = client.stream_message(
        thread_id=thread_id,
        message=message,
        assistant_id=agent_id
    )

    # Process stream
    interrupt_detected = False

    async def handle_stream(chunks_iter):
        """Helper to handle stream (supports recursion for resume)"""
        nonlocal interrupt_detected

        async for parsed in stream_handler.process_stream(chunks_iter):
            if parsed.chunk_type == ChunkType.TEXT_DELTA:
                # Print text delta
                if parsed.text_delta:
                    renderer.console.print(parsed.text_delta, style="cyan", end="")

            elif parsed.chunk_type == ChunkType.TOOL_CALL_COMPLETE:
                # Log tool call
                if parsed.tool_call:
                    print()
                    renderer.render_text(
                        f"[Tool called: {parsed.tool_call.name}]",
                        style="yellow"
                    )

            elif parsed.chunk_type == ChunkType.INTERRUPT:
                # HITL interrupt detected!
                interrupt_detected = True

                if parsed.interrupt:
                    print()
                    print()
                    renderer.render_panel(
                        "HITL interrupt detected! This means:\n"
                        "1. Agent wants to use a tool\n"
                        "2. Server is configured with interrupt_before or interrupt_after\n"
                        "3. You can approve or reject the tool call\n",
                        "Interrupt Detected",
                        style="green"
                    )
                    print()

                    # Show approval prompt
                    command = hitl_handler.handle_interrupt(parsed.interrupt, session)

                    # Resume
                    print()
                    renderer.render_text("Resuming execution...", style="cyan")
                    print()
                    renderer.console.print("Agent: ", style="cyan", end="")

                    resume_chunks = client.resume_after_interrupt(
                        thread_id=thread_id,
                        assistant_id=agent_id,
                        command=command
                    )

                    # Recursively handle resumed stream
                    await handle_stream(resume_chunks)

            elif parsed.chunk_type == ChunkType.USAGE:
                # Log usage
                if parsed.usage:
                    print()
                    renderer.render_text(
                        f"[Tokens: {parsed.usage.total_tokens}]",
                        style="dim"
                    )

    # Handle the stream
    await handle_stream(chunks)

    print()
    print()

    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)

    if interrupt_detected:
        renderer.render_success(
            "HITL interrupt was detected and handled successfully!"
        )
        print()
        renderer.render_text(
            "This confirms:\n"
            "✓ Server has HITL configured\n"
            "✓ Interrupt detection works\n"
            "✓ Approval prompt works\n"
            "✓ Resume flow works\n",
            style="green"
        )
    else:
        renderer.render_text(
            "No HITL interrupt was detected.",
            style="yellow"
        )
        print()
        renderer.render_text(
            "This could mean:\n"
            "- Agent didn't need to use a tool for this query\n"
            "- Agent doesn't have HITL configured (no interrupt_before/after)\n"
            "- Tool call succeeded without requiring approval\n",
            style="yellow"
        )
        print()
        renderer.render_text(
            "To enable HITL:\n"
            "1. Check src/agent_snowflake/graph2.py\n"
            "2. Ensure agent has interrupt_before=['sql_db_query'] or similar\n"
            "3. Restart server with 'langgraph dev'\n",
            style="cyan"
        )

    print()
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
