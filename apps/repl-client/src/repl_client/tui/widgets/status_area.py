"""Two-line status area widget for REPL client."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Container, Horizontal
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import Static

if TYPE_CHECKING:
    from textual.app import ComposeResult


class UserStatusLine(Horizontal):
    """Line 1: User status with agent, thread, and tokens."""

    DEFAULT_CSS = """
    UserStatusLine {
        height: 1;
        width: 100%;
        background: $surface;
        padding: 0 1;
    }

    UserStatusLine .status-agent {
        width: auto;
        padding: 0 1;
        color: cyan;
    }

    UserStatusLine .status-thread {
        width: auto;
        padding: 0 1;
        color: yellow;
    }

    UserStatusLine .status-tokens {
        width: auto;
        padding: 0 1;
        color: green;
    }

    UserStatusLine .status-divider {
        color: $text-muted;
        padding: 0 1;
    }

    UserStatusLine .status-spacer {
        width: 1fr;
    }
    """

    agent: reactive[str] = reactive("", init=False)
    thread: reactive[str] = reactive("", init=False)
    tokens: reactive[int] = reactive(0, init=False)

    def compose(self) -> ComposeResult:
        """Compose the user status line."""
        yield Static("Agent: (none)", classes="status-agent", id="agent-status")
        yield Static("│", classes="status-divider")
        yield Static("Thread: (none)", classes="status-thread", id="thread-status")
        yield Static("│", classes="status-divider")
        yield Static("Tokens: 0", classes="status-tokens", id="token-count")
        yield Static("", classes="status-spacer")

    def watch_agent(self, new_agent: str) -> None:
        """Update agent display when agent changes."""
        try:
            display = self.query_one("#agent-status", Static)
        except NoMatches:
            return

        if new_agent:
            display.update(f"Agent: {new_agent}")
        else:
            display.update("Agent: (none)")

    def watch_thread(self, new_thread: str) -> None:
        """Update thread display when thread changes."""
        try:
            display = self.query_one("#thread-status", Static)
        except NoMatches:
            return

        if new_thread:
            display.update(f"Thread: {new_thread}")
        else:
            display.update("Thread: (none)")

    def watch_tokens(self, new_value: int) -> None:
        """Update token display when count changes."""
        try:
            display = self.query_one("#token-count", Static)
        except NoMatches:
            return

        formatted = self._format_tokens(new_value)
        display.update(f"Tokens: {formatted}")

    def _format_tokens(self, count: int) -> str:
        """Format token count with K suffix for thousands.

        Args:
            count: Token count to format

        Returns:
            Formatted string (e.g., "1.2K" or "456")
        """
        if count >= 1000:
            return f"{count / 1000:.1f}K"
        return str(count)


class ClientInfoLine(Horizontal):
    """Line 2: Client info with connection status, last update, and errors."""

    DEFAULT_CSS = """
    ClientInfoLine {
        height: 1;
        width: 100%;
        background: $surface;
        padding: 0 1;
    }

    ClientInfoLine .status-connection {
        width: auto;
        padding: 0 1;
    }

    ClientInfoLine .status-connection.connected {
        color: $success;
    }

    ClientInfoLine .status-connection.disconnected {
        color: $error;
    }

    ClientInfoLine .status-last-update {
        width: auto;
        padding: 0 1;
        color: $text-muted;
    }

    ClientInfoLine .status-message {
        width: auto;
        padding: 0 1;
        color: $text;
    }

    ClientInfoLine .status-message.error {
        color: $error;
    }

    ClientInfoLine .status-message.warning {
        color: $warning;
    }

    ClientInfoLine .status-divider {
        color: $text-muted;
        padding: 0 1;
    }

    ClientInfoLine .status-spacer {
        width: 1fr;
    }
    """

    connected: reactive[bool] = reactive(True, init=False)
    server_url: reactive[str] = reactive("", init=False)
    last_update: reactive[str] = reactive("", init=False)
    status_message: reactive[str] = reactive("", init=False)
    status_level: reactive[str] = reactive("info", init=False)  # info, error, warning

    def compose(self) -> ComposeResult:
        """Compose the client info line."""
        yield Static("● Connected", classes="status-connection connected", id="connection-status")
        yield Static("│", classes="status-divider")
        yield Static("", classes="status-last-update", id="last-update")
        yield Static("│", classes="status-divider")
        yield Static("", classes="status-message", id="status-msg")
        yield Static("", classes="status-spacer")

    def watch_connected(self, new_value: bool) -> None:  # noqa: FBT001
        """Update connection status when state changes."""
        try:
            display = self.query_one("#connection-status", Static)
        except NoMatches:
            return

        display.remove_class("connected", "disconnected")

        # Show server URL if available, otherwise just Connected/Disconnected
        url_part = f" {self.server_url}" if self.server_url else ""

        if new_value:
            display.update(f"●{url_part}" if url_part else "● Connected")
            display.add_class("connected")
        else:
            display.update(f"○{url_part}" if url_part else "○ Disconnected")
            display.add_class("disconnected")

    def watch_server_url(self, new_url: str) -> None:
        """Update connection display when server URL changes."""
        # Trigger connected watcher to update display with new URL
        self.watch_connected(self.connected)

    def watch_last_update(self, new_value: str) -> None:
        """Update last update time when it changes."""
        try:
            display = self.query_one("#last-update", Static)
        except NoMatches:
            return

        if new_value:
            display.update(f"Last update: {new_value}")
        else:
            display.update("")

    def watch_status_message(self, new_message: str) -> None:
        """Update status message display."""
        try:
            display = self.query_one("#status-msg", Static)
        except NoMatches:
            return

        display.update(new_message)

    def watch_status_level(self, new_level: str) -> None:
        """Update status message styling based on level."""
        try:
            display = self.query_one("#status-msg", Static)
        except NoMatches:
            return

        display.remove_class("error", "warning")
        if new_level == "error":
            display.add_class("error")
        elif new_level == "warning":
            display.add_class("warning")


class StatusArea(Container):
    """Two-line status area container.

    Line 1: User status (agent, thread, tokens)
    Line 2: Client info (connection, last update, errors/warnings)
    """

    DEFAULT_CSS = """
    StatusArea {
        height: 2;
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the status area with two lines."""
        yield UserStatusLine(id="user-status-line")
        yield ClientInfoLine(id="client-info-line")

    # Convenience methods to forward to child widgets

    def set_agent(self, agent: str) -> None:
        """Set the agent name."""
        try:
            user_line = self.query_one("#user-status-line", UserStatusLine)
            user_line.agent = agent
        except NoMatches:
            pass

    def set_thread(self, thread: str) -> None:
        """Set the thread identifier."""
        try:
            user_line = self.query_one("#user-status-line", UserStatusLine)
            user_line.thread = thread
        except NoMatches:
            pass

    def set_tokens(self, count: int) -> None:
        """Set the token count."""
        try:
            user_line = self.query_one("#user-status-line", UserStatusLine)
            user_line.tokens = count
        except NoMatches:
            pass

    def set_connected(self, connected: bool, server_url: str = "") -> None:  # noqa: FBT001
        """Set the connection status.

        Args:
            connected: Whether connected to server
            server_url: Optional server URL to display
        """
        try:
            client_line = self.query_one("#client-info-line", ClientInfoLine)
            client_line.connected = connected
            if server_url:
                client_line.server_url = server_url
        except NoMatches:
            pass

    def set_last_update(self, time_ago: str) -> None:
        """Set the last update time.

        Args:
            time_ago: Human-readable time string (e.g., "2s ago", "1m ago")
        """
        try:
            client_line = self.query_one("#client-info-line", ClientInfoLine)
            client_line.last_update = time_ago
        except NoMatches:
            pass

    def set_status(self, message: str, *, error: bool = False, warning: bool = False) -> None:
        """Set a status message.

        Args:
            message: Status message text
            error: Whether this is an error message
            warning: Whether this is a warning message
        """
        try:
            client_line = self.query_one("#client-info-line", ClientInfoLine)
            client_line.status_message = message

            if error:
                client_line.status_level = "error"
            elif warning:
                client_line.status_level = "warning"
            else:
                client_line.status_level = "info"
        except NoMatches:
            pass
