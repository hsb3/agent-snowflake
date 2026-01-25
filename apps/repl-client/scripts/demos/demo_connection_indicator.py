#!/usr/bin/env python
"""Demo script showing connection indicator in status area.

This demonstrates the connection health indicator feature that shows:
- Green ● when connected
- Red ○ when disconnected
- Server URL displayed next to indicator
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from repl_client.tui.widgets import StatusArea

from demo_fixtures import DEMO_URLS, setup_status_area

# TODO: define: get_semantic_tokens();
class ConnectionIndicatorDemo(App[None]):
    """Demo app showing connection indicator."""
    # TODO: use actual app css
    CSS = """
    Screen {
        background: $surface;
    }

    #demo-container {
        height: 100%;
        width: 100%;
        padding: 2;
    }

    #demo-info {
        height: auto;
        padding: 1;
        margin: 1 0;
        background: $surface-darken-1;
        border: solid $primary;
    }
    """

    # TODO: adopt similar bindings in REPL/TUI
    BINDINGS = [
        Binding("c", "toggle_connection", "Toggle Connection", show=True),
        Binding("u", "change_url", "Change URL", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.connected = True
        self.url_index = 0
        self.urls = DEMO_URLS

    def compose(self) -> ComposeResult:
        """Compose the demo layout."""
        yield Static(
            "Connection Indicator Demo\n\n"
            "Press 'c' to toggle connection state\n"
            "Press 'u' to cycle through different URLs\n"
            "Press 'q' to quit\n\n"
            "Watch the status area at the bottom:",
            id="demo-info",
        )
        yield StatusArea()

    def on_mount(self) -> None:
        """Initialize status area on mount."""
        status_area = self.query_one(StatusArea)
        setup_status_area(
            status_area,
            connected=self.connected,
            url=self.urls[self.url_index],
            status="Demo ready - Press 'c' to toggle connection",
        )

    def action_toggle_connection(self) -> None:
        """Toggle connection state."""
        self.connected = not self.connected
        status_area = self.query_one(StatusArea)
        status_area.set_connected(self.connected, self.urls[self.url_index])

        # Update status message
        if self.connected:
            status_area.set_status(f"Connected to {self.urls[self.url_index]}")
        else:
            status_area.set_status("Disconnected from server", error=True)

    def action_change_url(self) -> None:
        """Cycle through different URLs."""
        self.url_index = (self.url_index + 1) % len(self.urls)
        status_area = self.query_one(StatusArea)
        status_area.set_connected(self.connected, self.urls[self.url_index])
        status_area.set_status(f"Changed to {self.urls[self.url_index]}")


if __name__ == "__main__":
    app = ConnectionIndicatorDemo()
    app.run()
