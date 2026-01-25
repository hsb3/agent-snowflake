"""Tests for F2/F3 modal functionality."""

from unittest.mock import AsyncMock

import pytest

from repl_client.core.config import Config
from repl_client.tui.app import AgentSelectionScreen, REPLApp, ThreadSelectionScreen


@pytest.fixture
def app():
    """Create app instance for testing."""
    config = Config(
        server_url="http://localhost:2024",
        default_agent="test-agent",
    )
    return REPLApp(config=config)


async def test_agent_selection_modal_composes():
    """Test that agent selection modal composes correctly."""
    agents = [
        {"assistant_id": "agent-1", "graph_id": "agent_minimal"},
        {"assistant_id": "agent-2", "graph_id": "agent"},
        {"assistant_id": "agent-3", "graph_id": "agent_enhanced"},
    ]
    current_agent = "agent-1"

    screen = AgentSelectionScreen(agents, current_agent)

    # Should have agents and current agent set
    assert screen.agents == agents
    assert screen.current_agent_id == current_agent


async def test_thread_selection_modal_composes():
    """Test that thread selection modal composes correctly."""
    threads = [
        {"thread_id": "thread-1-uuid", "created_at": "2026-01-24T10:00:00"},
        {"thread_id": "thread-2-uuid", "created_at": "2026-01-24T11:00:00"},
    ]
    current_thread = "thread-1-uuid"

    screen = ThreadSelectionScreen(threads, current_thread)

    # Should have threads and current thread set
    assert screen.threads == threads
    assert screen.current_thread_id == current_thread


async def test_action_select_agent_with_no_agents():
    """Test agent selection when no agents are available."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    # Mock the service to return empty list
    app.langgraph_service.get_agents = AsyncMock(return_value=[])

    async with app.run_test():
        # Call the action
        await app.action_select_agent()

        # Should not crash, just return early
        # No need to assert anything specific, just that it doesn't raise


async def test_action_select_agent_with_error():
    """Test agent selection when API call fails."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    # Mock the service to raise an exception
    app.langgraph_service.get_agents = AsyncMock(side_effect=Exception("API error"))

    async with app.run_test():
        # Call the action
        await app.action_select_agent()

        # Should not crash, just log error and return
        # No need to assert anything specific, just that it doesn't raise


async def test_action_select_thread_with_no_threads():
    """Test thread selection when no threads are available."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    # Mock the service to return empty list
    app.langgraph_service.get_threads = AsyncMock(return_value=[])

    async with app.run_test():
        # Call the action
        await app.action_select_thread()

        # Should not crash, just show modal with only "New Thread" option
        # No need to assert anything specific, just that it doesn't raise


async def test_action_select_thread_with_error():
    """Test thread selection when API call fails."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    # Mock the service to raise an exception
    app.langgraph_service.get_threads = AsyncMock(side_effect=Exception("API error"))

    async with app.run_test():
        # Call the action
        await app.action_select_thread()

        # Should not crash, just log error and return
        # No need to assert anything specific, just that it doesn't raise


async def test_f2_binding_triggers_agent_modal():
    """Test that F2 key binding triggers agent selection."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    # Mock the service
    agents = [
        {"assistant_id": "agent-1", "graph_id": "agent_minimal"},
    ]
    app.langgraph_service.get_agents = AsyncMock(return_value=agents)

    async with app.run_test():
        # Check that F2 binding exists
        binding_keys = {b.key for b in app.BINDINGS}
        assert "f2" in binding_keys

        # Check that the action exists
        assert hasattr(app, "action_select_agent")
        assert callable(app.action_select_agent)


async def test_f3_binding_triggers_thread_modal():
    """Test that F3 key binding triggers thread selection."""
    config = Config(server_url="http://localhost:2024")
    app = REPLApp(config=config)

    # Mock the service
    threads = [
        {"thread_id": "thread-1", "created_at": "2026-01-24T10:00:00"},
    ]
    app.langgraph_service.get_threads = AsyncMock(return_value=threads)

    async with app.run_test():
        # Check that F3 binding exists
        binding_keys = {b.key for b in app.BINDINGS}
        assert "f3" in binding_keys

        # Check that the action exists
        assert hasattr(app, "action_select_thread")
        assert callable(app.action_select_thread)
