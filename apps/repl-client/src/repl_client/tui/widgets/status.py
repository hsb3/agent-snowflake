"""Status bar widget for REPL client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Horizontal
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult


class StatusBar(Horizontal):
    """Status bar showing agent, thread, tokens, and connection status."""

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
        background: $surface;
        padding: 0 1;
    }

    StatusBar .status-agent {
        width: auto;
        padding: 0 1;
        color: $text-muted;
    }

    StatusBar .status-thread {
        width: auto;
        padding: 0 1;
        color: $text-muted;
    }

    StatusBar .status-tokens {
        width: auto;
        padding: 0 1;
        color: $text-muted;
    }

    StatusBar .status-message {
        width: auto;
        padding: 0 1;
        color: $text;
    }

    StatusBar .status-message.error {
        color: $error;
    }

    StatusBar .status-connection {
        width: auto;
        padding: 0 1;
    }

    StatusBar .status-connection.connected {
        background: #10b981;
        color: black;
    }

    StatusBar .status-connection.disconnected {
        background: #ef4444;
        color: white;
    }

    StatusBar .status-spacer {
        width: 1fr;
    }

    StatusBar .status-divider {
        color: $text-muted;
        padding: 0 1;
    }
    """

    agent: reactive[str] = reactive("", init=False)
    thread: reactive[str] = reactive("", init=False)
    tokens: reactive[int] = reactive(0, init=False)
    connected: reactive[bool] = reactive(True, init=False)
    status_message: reactive[str] = reactive("", init=False)
    status_error: reactive[bool] = reactive(False, init=False)

    def compose(self) -> ComposeResult:
        """Compose the status bar layout."""
        yield Static("Agent: (none)", classes="status-agent", id="agent-status")
        yield Static("│", classes="status-divider")
        yield Static("Thread: (none)", classes="status-thread", id="thread-status")
        yield Static("│", classes="status-divider")
        yield Static("", classes="status-message", id="status-msg")
        yield Static("", classes="status-spacer")
        yield Static("0 tokens", classes="status-tokens", id="token-count")
        yield Static("│", classes="status-divider")
        yield Static(
            "●", classes="status-connection connected", id="connection-status"
        )

    def watch_agent(self, new_agent: str) -> None:
        """Update agent display when agent changes."""
        try:
            display = self.query_one("#agent-status", Static)
        except NoMatches:
            return

        if new_agent:
            display.update(f"Agent: {new_agent}")
        else:
            display.update("")

    def watch_thread(self, new_thread: str) -> None:
        """Update thread display when thread changes."""
        try:
            display = self.query_one("#thread-status", Static)
        except NoMatches:
            return

        if new_thread:
            display.update(f"Thread: {new_thread}")
        else:
            display.update("")

    def watch_tokens(self, new_value: int) -> None:
        """Update token display when count changes."""
        try:
            display = self.query_one("#token-count", Static)
        except NoMatches:
            return

        if new_value > 0:
            formatted = self._format_tokens(new_value)
            display.update(formatted)
        else:
            display.update("")

    def watch_connected(self, new_value: bool) -> None:  # noqa: FBT001
        """Update connection status when state changes."""
        try:
            display = self.query_one("#connection-status", Static)
        except NoMatches:
            return

        display.remove_class("connected", "disconnected")

        if new_value:
            display.update("●")
            display.add_class("connected")
        else:
            display.update("○")
            display.add_class("disconnected")

    def _format_tokens(self, count: int) -> str:
        """Format token count with K suffix for thousands.

        Args:
            count: Token count to format

        Returns:
            Formatted string (e.g., "1.2K tokens" or "456 tokens")
        """
        if count >= 1000:
            return f"{count / 1000:.1f}K tokens"
        return f"{count} tokens"

    def set_agent(self, agent: str) -> None:
        """Set the agent name.

        Args:
            agent: Agent identifier
        """
        self.agent = agent

    def set_thread(self, thread: str) -> None:
        """Set the thread identifier.

        Args:
            thread: Thread identifier
        """
        self.thread = thread

    def set_tokens(self, count: int) -> None:
        """Set the token count.

        Args:
            count: Current context token count
        """
        self.tokens = count

    def hide_tokens(self) -> None:
        """Hide the token display."""
        try:
            self.query_one("#token-count", Static).update("")
        except NoMatches:
            pass

    def set_connected(self, connected: bool) -> None:  # noqa: FBT001
        """Set the connection status.

        Args:
            connected: Whether connected to server
        """
        self.connected = connected

    def set_status(self, message: str, *, error: bool = False) -> None:
        """Set a status message.

        Args:
            message: Status message text
            error: Whether this is an error message
        """
        self.status_message = message
        self.status_error = error

    def watch_status_message(self, new_message: str) -> None:
        """Update status message display."""
        try:
            display = self.query_one("#status-msg", Static)
        except NoMatches:
            return

        if new_message:
            display.update(new_message)
        else:
            display.update("")

    def watch_status_error(self, is_error: bool) -> None:  # noqa: FBT001
        """Update status message styling based on error state."""
        try:
            display = self.query_one("#status-msg", Static)
        except NoMatches:
            return

        display.remove_class("error")
        if is_error:
            display.add_class("error")
