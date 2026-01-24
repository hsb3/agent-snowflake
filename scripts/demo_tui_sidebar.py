#!/usr/bin/env python3
"""Demo script for TUI sidebar functionality.

Shows sidebar with populated content.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Footer, Header

from repl_client.tui.widgets import ChatInput, Sidebar, StatusArea, UserMessage


class SidebarDemo(App[None]):
    """Demo app showcasing sidebar functionality."""

    CSS = """
    #main-content {
        height: 1fr;
        width: 100%;
    }

    #messages {
        height: 1fr;
        width: 1fr;
        background: $surface;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    BINDINGS = [
        Binding("f4", "toggle_sidebar", "Sidebar", show=True),
        Binding("f5", "expand_sidebar", "Expand", show=True),
        Binding("ctrl+c", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        """Compose the demo layout."""
        yield Header()
        with Horizontal(id="main-content"):
            yield ScrollableContainer(id="messages")
            yield Sidebar(id="sidebar")
        yield ChatInput(cwd=Path.cwd())
        yield StatusArea()
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize with demo data."""
        # Get widget references
        sidebar = self.query_one("#sidebar", Sidebar)
        status_area = self.query_one(StatusArea)
        messages = self.query_one("#messages", ScrollableContainer)

        # Populate status area
        status_area.set_agent("demo_agent")
        status_area.set_thread("abc12345")
        status_area.set_tokens(2345)
        status_area.set_connected(True)
        status_area.set_last_update("2s ago")
        status_area.set_status("Ready")

        # Populate sidebar with demo data
        demo_threads = [
            {
                "thread_id": "thread-abc123456789",
                "created_at": "2026-01-24T10:00:00",
            },
            {
                "thread_id": "thread-def987654321",
                "created_at": "2026-01-23T15:30:00",
            },
            {
                "thread_id": "thread-ghi111222333",
                "created_at": "2026-01-22T09:15:00",
            },
        ]

        demo_agents = [
            {
                "assistant_id": "agent-enhanced-123",
                "graph_id": "agent_enhanced",
            },
            {
                "assistant_id": "agent-basic-456",
                "graph_id": "agent_basic",
            },
            {
                "assistant_id": "agent-research-789",
                "graph_id": "agent_research",
            },
        ]

        demo_tools = [
            {
                "name": "sql_db_query",
                "args": {"query": "SELECT * FROM users LIMIT 10"},
                "result": "[10 rows returned]",
                "status": "success",
            },
            {
                "name": "search_web",
                "args": {"query": "LangGraph documentation"},
                "result": "Found 5 results",
                "status": "success",
            },
            {
                "name": "code_interpreter",
                "args": {"code": "print('hello')"},
                "result": "",
                "status": "pending",
            },
        ]

        sidebar.populate_threads(demo_threads, "thread-abc123456789")
        sidebar.populate_agents(demo_agents, "agent-enhanced-123")
        sidebar.populate_session_info(
            thread_id="thread-abc123456789",
            agent_id="agent-enhanced-123",
            tokens={"total": 2345, "input": 1200, "output": 1145},
            model="claude-sonnet-4-5-20250929",
        )
        sidebar.populate_tools(demo_tools)

        # Add some demo messages
        await messages.mount(UserMessage("Hello! This is a demo message."))
        await messages.mount(
            UserMessage(
                "Press F4 to toggle the sidebar.\nPress F5 to expand/collapse it."
            )
        )

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.toggle()

    def action_expand_sidebar(self) -> None:
        """Toggle expanded sidebar mode."""
        sidebar = self.query_one("#sidebar", Sidebar)
        sidebar.expand()


if __name__ == "__main__":
    app = SidebarDemo()
    app.run()
