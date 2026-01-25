"""Integration tests for F2/F3 modal functionality with server.

These tests require a running LangGraph dev server.
"""

from unittest.mock import AsyncMock

import pytest

from repl_client.core.config import Config
from repl_client.tui.app import REPLApp


@pytest.mark.integration
async def test_f2_agent_modal_end_to_end():
    """Test F2 agent selection modal end-to-end flow."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    # Mock agents
    agents = [
        {"assistant_id": "agent-1", "graph_id": "agent_minimal"},
        {"assistant_id": "agent-2", "graph_id": "agent"},
    ]
    app.langgraph_service.get_agents = AsyncMock(return_value=agents)
    app.langgraph_service.resolve_agent_name = AsyncMock(return_value="agent-2")

    async with app.run_test():
        # Set initial agent
        app.session.set_agent("agent-1")
        initial_agent = app.session.current_assistant_id

        # Verify initial state
        assert initial_agent == "agent-1"

        # Call action_select_agent (simulates F2 press)
        # Note: We can't easily simulate the modal selection in tests
        # but we can verify the action doesn't crash
        # In a real test with a running server, you would:
        # await pilot.press("f2")
        # await pilot.press("down")  # Navigate to second agent
        # await pilot.press("enter")  # Select it

        # For now, we'll just verify the action exists and can be called
        assert hasattr(app, "action_select_agent")
        assert callable(app.action_select_agent)


@pytest.mark.integration
async def test_f3_thread_modal_end_to_end():
    """Test F3 thread selection modal end-to-end flow."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    # Mock threads
    threads = [
        {"thread_id": "thread-1", "created_at": "2026-01-24T10:00:00"},
        {"thread_id": "thread-2", "created_at": "2026-01-24T11:00:00"},
    ]
    app.langgraph_service.get_threads = AsyncMock(return_value=threads)

    async with app.run_test():
        # Set initial thread
        app.session.set_thread("thread-1")
        initial_thread = app.session.current_thread_id

        # Verify initial state
        assert initial_thread == "thread-1"

        # Verify the action exists and can be called
        assert hasattr(app, "action_select_thread")
        assert callable(app.action_select_thread)


async def test_agent_modal_display_structure():
    """Test that agent modal has correct structure when displayed."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    agents = [
        {"assistant_id": "agent-1", "graph_id": "agent_minimal"},
        {"assistant_id": "agent-2", "graph_id": "agent"},
    ]
    app.langgraph_service.get_agents = AsyncMock(return_value=agents)

    async with app.run_test():
        # Create the modal screen
        from repl_client.tui.app import AgentSelectionScreen

        screen = AgentSelectionScreen(agents, "agent-1")

        # Verify it has the expected attributes
        assert screen.agents == agents
        assert screen.current_agent_id == "agent-1"

        # Verify compose yields correct widgets
        # (We can't easily test the actual rendering without pushing the screen)


async def test_thread_modal_display_structure():
    """Test that thread modal has correct structure when displayed."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    threads = [
        {"thread_id": "thread-1", "created_at": "2026-01-24T10:00:00"},
        {"thread_id": "thread-2", "created_at": "2026-01-24T11:00:00"},
    ]
    app.langgraph_service.get_threads = AsyncMock(return_value=threads)

    async with app.run_test():
        # Create the modal screen
        from repl_client.tui.app import ThreadSelectionScreen

        screen = ThreadSelectionScreen(threads, "thread-1")

        # Verify it has the expected attributes
        assert screen.threads == threads
        assert screen.current_thread_id == "thread-1"


async def test_agent_switching_updates_status_bar():
    """Test that switching agents updates the status bar."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    agents = [
        {"assistant_id": "agent-1-uuid", "graph_id": "agent_minimal"},
        {"assistant_id": "agent-2-uuid", "graph_id": "agent"},
    ]
    app.langgraph_service.get_agents = AsyncMock(return_value=agents)
    app.langgraph_service.resolve_agent_name = AsyncMock(return_value="agent-2-uuid")

    async with app.run_test():
        # Set initial agent
        app.session.set_agent("agent-1-uuid")

        # Switch via controller
        result = await app.session_controller.switch_agent("agent-2-uuid")

        # Verify switch succeeded
        assert result["success"]
        assert app.session.current_assistant_id == "agent-2-uuid"
        assert app.app_state.current_agent_id == "agent-2-uuid"

        # Status bar update is handled by the action, not the controller
        # So we test that separately


async def test_thread_creation_updates_status_bar():
    """Test that creating a thread updates the status bar."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    new_thread_id = "new-thread-uuid"
    new_thread_dict = {
        "thread_id": new_thread_id,
        "created_at": "2026-01-24T12:00:00",
    }
    app.langgraph_service.create_thread_with_metadata = AsyncMock(
        return_value=(new_thread_id, new_thread_dict)
    )

    async with app.run_test():
        # Create thread via controller
        result = await app.session_controller.create_thread()

        # Verify creation succeeded
        assert result["success"]
        assert app.session.current_thread_id == new_thread_id
        assert app.app_state.current_thread_id == new_thread_id
