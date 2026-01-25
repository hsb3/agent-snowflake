#!/usr/bin/env python3
"""Demo script for TUI sidebar functionality.

Shows sidebar with populated content.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Footer, Header

from repl_client.tui.widgets import ChatInput, Sidebar, StatusArea, UserMessage

from demo_fixtures import populate_sidebar, setup_status_area


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
        Binding("f5", "expand_sidebar", "Expand", show=True), # does not work
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

        # Populate status area using helper
        setup_status_area(
            status_area,
            agent="demo_agent",
            thread="abc12345",
            tokens=2345,
            connected=True,
            last_update="2s ago",
        )

        # Populate sidebar using helper
        populate_sidebar(sidebar)

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
