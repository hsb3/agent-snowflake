#!/usr/bin/env python
"""Quick manual test for sidebar keyboard navigation.

Run with: uv run python test_sidebar_keyboard_nav.py

Instructions:
1. Press F4 to open sidebar
2. Press Ctrl+B to focus sidebar (or Tab to focus)
3. Use Up/Down arrows to navigate threads/agents list
4. Press Enter to select an item
5. Watch status bar for changes
"""
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from repl_client.tui.widgets.sidebar import Sidebar


class TestApp(App):
    """Test app for sidebar keyboard navigation."""

    CSS = """
    Screen {
        layout: horizontal;
    }

    Sidebar {
        width: 40%;
    }
    """

    BINDINGS = [
        ("f4", "toggle_sidebar", "Toggle Sidebar"),
        ("ctrl+b", "focus_sidebar", "Focus Sidebar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Sidebar()
        yield Footer()

    def on_mount(self) -> None:
        """Setup test data on mount."""
        sidebar = self.query_one(Sidebar)

        # Populate with test data
        test_threads = [
            {"thread_id": "thread-001-abc123", "created_at": "2024-01-20T10:00:00"},
            {"thread_id": "thread-002-def456", "created_at": "2024-01-21T11:00:00"},
            {"thread_id": "thread-003-ghi789", "created_at": "2024-01-22T12:00:00"},
        ]

        test_agents = [
            {"assistant_id": "agent-001", "graph_id": "agent_enhanced"},
            {"assistant_id": "agent-002", "graph_id": "agent_minimal"},
            {"assistant_id": "agent-003", "graph_id": "agent"},
        ]

        sidebar.populate_threads(test_threads, "thread-001-abc123")
        sidebar.populate_agents(test_agents, "agent-001")
        sidebar.populate_session_info(
            thread_id="thread-001-abc123",
            agent_id="agent-001",
            tokens={"total": 1234, "input": 567, "output": 667},
        )

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        sidebar = self.query_one(Sidebar)
        sidebar.toggle()

    def action_focus_sidebar(self) -> None:
        """Focus sidebar."""
        sidebar = self.query_one(Sidebar)
        if not sidebar.visible:
            sidebar.toggle()
        sidebar.focus()

    def on_sidebar_agent_selected(self, message: Sidebar.AgentSelected) -> None:
        """Handle agent selection."""
        self.notify(f"Agent selected: {message.agent_id}", severity="information")

    def on_sidebar_thread_selected(self, message: Sidebar.ThreadSelected) -> None:
        """Handle thread selection."""
        self.notify(f"Thread selected: {message.thread_id}", severity="information")

    def on_sidebar_new_thread_requested(self, message: Sidebar.NewThreadRequested) -> None:
        """Handle new thread request."""
        self.notify("New thread requested", severity="information")


if __name__ == "__main__":
    app = TestApp()
    app.run()
