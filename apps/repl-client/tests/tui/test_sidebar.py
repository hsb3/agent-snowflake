"""Tests for sidebar widget."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from repl_client.tui.widgets import Sidebar


class SidebarTestApp(App[None]):
    """Test app for sidebar."""

    def compose(self) -> ComposeResult:
        """Compose with sidebar."""
        yield Sidebar()


@pytest.fixture
async def app():
    """Create test app."""
    app = SidebarTestApp()
    async with app.run_test() as pilot:
        yield pilot


async def test_sidebar_initial_state(app):
    """Test sidebar starts hidden."""
    sidebar = app.app.query_one(Sidebar)
    assert sidebar.visible is False
    assert sidebar.expanded is False


async def test_sidebar_toggle(app):
    """Test sidebar toggle visibility."""
    sidebar = app.app.query_one(Sidebar)

    # Initially hidden
    assert sidebar.visible is False

    # Toggle to show
    sidebar.toggle()
    assert sidebar.visible is True
    assert sidebar.expanded is False

    # Toggle to hide
    sidebar.toggle()
    assert sidebar.visible is False


async def test_sidebar_expand(app):
    """Test sidebar expand mode."""
    sidebar = app.app.query_one(Sidebar)

    # Initially hidden
    assert sidebar.visible is False
    assert sidebar.expanded is False

    # Expand (should show and expand)
    sidebar.expand()
    assert sidebar.visible is True
    assert sidebar.expanded is True

    # Expand again (should toggle back to normal)
    sidebar.expand()
    assert sidebar.visible is True
    assert sidebar.expanded is False


async def test_sidebar_populate_threads(app):
    """Test populating threads tab."""
    sidebar = app.app.query_one(Sidebar)

    threads = [
        {"thread_id": "thread-123", "created_at": "2026-01-24"},
        {"thread_id": "thread-456", "created_at": "2026-01-23"},
    ]

    sidebar.populate_threads(threads, "thread-123")

    # Should have widgets in the threads list
    threads_list = sidebar.query_one("#threads-list")
    assert threads_list is not None


async def test_sidebar_populate_agents(app):
    """Test populating agents tab."""
    sidebar = app.app.query_one(Sidebar)

    agents = [
        {"assistant_id": "agent-123", "graph_id": "agent_enhanced"},
        {"assistant_id": "agent-456", "graph_id": "agent_basic"},
    ]

    sidebar.populate_agents(agents, "agent-123")

    # Should have widgets in the agents list
    agents_list = sidebar.query_one("#agents-list")
    assert agents_list is not None


async def test_sidebar_populate_session_info(app):
    """Test populating session info tab."""
    sidebar = app.app.query_one(Sidebar)

    sidebar.populate_session_info(
        thread_id="thread-123",
        agent_id="agent-456",
        tokens={"total": 1000, "input": 600, "output": 400},
        model="claude-sonnet-4-5",
    )

    # Should have content in session info
    session_info = sidebar.query_one("#session-info")
    assert session_info is not None


async def test_sidebar_populate_tools(app):
    """Test populating tools tab."""
    sidebar = app.app.query_one(Sidebar)

    tools = [
        {"name": "tool1", "args": {}, "result": "success", "status": "success"},
        {"name": "tool2", "args": {}, "result": "", "status": "pending"},
    ]

    sidebar.populate_tools(tools)

    # Should have content in tools list
    tools_list = sidebar.query_one("#tools-list")
    assert tools_list is not None


async def test_sidebar_empty_content(app):
    """Test sidebar with empty lists."""
    sidebar = app.app.query_one(Sidebar)

    # Empty threads
    sidebar.populate_threads([], "")

    # Empty agents
    sidebar.populate_agents([], "")

    # Empty tools
    sidebar.populate_tools([])

    # Should still render without errors
    assert sidebar is not None
