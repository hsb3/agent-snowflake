#!/usr/bin/env python3
"""Quick test script to verify REPL client works with LangGraph server.

Run this after starting the LangGraph dev server:
    langgraph dev

Usage:
    uv run python scripts/test_repl_client.py
"""

import asyncio

from agent_snowflake.repl_client.core.client import LangGraphClient
from agent_snowflake.repl_client.core.logging import setup_client_logger


async def main():
    """Test basic client functionality."""
    # Setup logging
    logger = setup_client_logger(".repl/test_client.log", level="DEBUG")
    logger.info("Starting REPL client test")

    # Create client
    client = LangGraphClient("http://localhost:2024", timeout=30)

    # Test connection
    print("Testing connection...")
    connected = await client.connect()
    if not connected:
        print("❌ Failed to connect to server. Is it running on localhost:2024?")
        return

    print("✅ Connected to LangGraph server")

    # List agents
    print("\nListing agents...")
    agents = await client.list_agents(limit=5)
    print(f"✅ Found {len(agents)} agents:")
    for agent in agents:
        print(f"  - {agent.get('name', 'Unnamed')} ({agent['assistant_id']})")

    if not agents:
        print("⚠️  No agents available to test streaming")
        return

    # Create thread
    print("\nCreating thread...")
    thread_id = await client.create_thread(metadata={"test": "script_test"})
    print(f"✅ Created thread: {thread_id}")

    # Get thread details
    print("\nGetting thread details...")
    thread = await client.get_thread(thread_id)
    print(f"✅ Thread status: {thread.get('status', 'unknown')}")

    # Stream a message
    print("\nStreaming message to agent...")
    assistant_id = agents[0]["assistant_id"]
    event_count = 0

    async for event_type, data in client.stream_message(
        thread_id=thread_id, message="Count to 3, then stop.", assistant_id=assistant_id
    ):
        event_count += 1
        print(f"  Event {event_count}: {event_type}")

        # Stop after collecting some events
        if event_count >= 10:
            print("  (stopping after 10 events...)")
            break

    print(f"✅ Received {event_count} streaming events")

    # List threads
    print("\nListing threads...")
    threads = await client.list_threads(limit=5)
    print(f"✅ Found {len(threads)} threads")

    print("\n✅ All tests passed!")
    logger.info("REPL client test completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
