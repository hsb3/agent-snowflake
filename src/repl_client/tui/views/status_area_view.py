"""Status area view - two-line status display.

Wraps StatusArea widget and provides methods for updating status information.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from repl_client.tui.widgets import StatusArea

if TYPE_CHECKING:
    pass


class StatusAreaView(StatusArea):
    """View wrapper for StatusArea widget.

    Provides a clean interface for updating status display.
    The widget handles rendering, this view adds semantic methods.

    Note: AppState is managed at the app level. Views are updated
    through their public methods when state changes.
    """

    def update_agent(self, agent_name: str) -> None:
        """Update the agent display.

        Args:
            agent_name: Name of the current agent
        """
        self.set_agent(agent_name)

    def update_thread(self, thread_id: str, *, truncate: bool = True) -> None:
        """Update the thread display.

        Args:
            thread_id: Current thread ID
            truncate: Whether to truncate to first 8 chars (default: True)
        """
        display_id = thread_id[:8] if truncate and len(thread_id) > 8 else thread_id
        self.set_thread(display_id)

    def update_tokens(self, count: int) -> None:
        """Update the token count display.

        Args:
            count: Total token count
        """
        self.set_tokens(count)

    def update_connection_status(self, connected: bool, server_url: str = "") -> None:  # noqa: FBT001
        """Update connection status indicator.

        Args:
            connected: Whether the client is connected
            server_url: Server URL (optional)
        """
        self.set_connected(connected, server_url)

    def update_status_message(
        self,
        message: str,
        *,
        error: bool = False,
        warning: bool = False,
    ) -> None:
        """Update the status message line.

        Args:
            message: Status message text
            error: Whether this is an error message
            warning: Whether this is a warning message
        """
        self.set_status(message, error=error, warning=warning)

    def clear_status_message(self) -> None:
        """Clear the status message."""
        self.set_status("")
