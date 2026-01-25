"""Demo app for StatusBar and LoadingWidget.

Run with: uv run python scripts/repl_client/demos/demo_tui_status.py
"""

import asyncio

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Header, Static

from repl_client.tui.widgets import LoadingWidget, StatusBar


class StatusDemo(App):
    """Demo application for TUI status widgets."""

    CSS = """
    Container {
        height: 1fr;
        padding: 1 2;
    }

    .demo-section {
        height: auto;
        margin: 1 0;
        padding: 1;
        border: solid $primary;
    }

    .demo-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    .demo-info {
        color: $text-muted;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the demo UI."""
        yield Header()

        with Container():
            with Vertical(classes="demo-section"):
                yield Static("LoadingWidget Demo", classes="demo-title")
                yield Static(
                    "Watch the animated spinner and elapsed time counter",
                    classes="demo-info",
                )
                yield LoadingWidget("Processing")

            with Vertical(classes="demo-section"):
                yield Static("StatusBar Demo", classes="demo-title")
                yield Static(
                    "Status updates will cycle through different states",
                    classes="demo-info",
                )

        yield StatusBar()

    def on_mount(self) -> None:
        """Start demo updates on mount."""
        self.set_interval(3, self._demo_status_updates)
        self.set_interval(7, self._demo_loading_states)

    async def _demo_status_updates(self) -> None:
        """Cycle through different status states."""
        status_bar = self.query_one(StatusBar)

        # Cycle through different states
        states = [
            {"agent": "agent_basic", "thread": "", "tokens": 0, "connected": True},
            {
                "agent": "agent_enhanced",
                "thread": "thread_abc123",
                "tokens": 456,
                "connected": True,
            },
            {
                "agent": "agent_enhanced",
                "thread": "thread_abc123",
                "tokens": 1234,
                "connected": True,
            },
            {
                "agent": "agent_enhanced",
                "thread": "thread_abc123",
                "tokens": 5678,
                "connected": False,
            },
            {"agent": "", "thread": "", "tokens": 0, "connected": True},
        ]

        current_state = getattr(self, "_status_state_index", 0)
        state = states[current_state]

        status_bar.agent = state["agent"]
        status_bar.thread = state["thread"]
        status_bar.tokens = state["tokens"]
        status_bar.connected = state["connected"]

        self._status_state_index = (current_state + 1) % len(states)

    async def _demo_loading_states(self) -> None:
        """Cycle through loading widget states."""
        loading = self.query_one(LoadingWidget)

        # Cycle through different operations
        operations = [
            "Processing",
            "Analyzing",
            "Generating",
            "Streaming response",
        ]

        current_op = getattr(self, "_loading_op_index", 0)
        loading.set_status(operations[current_op])

        self._loading_op_index = (current_op + 1) % len(operations)

        # Occasionally pause/resume
        if current_op == 2:
            loading.pause("Awaiting approval")
            await asyncio.sleep(2)
            loading.resume()


if __name__ == "__main__":
    app = StatusDemo()
    app.run()
