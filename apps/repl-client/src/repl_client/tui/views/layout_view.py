"""Main layout view - coordinates major screen areas.

Like a webapp layout template - composes all major UI sections.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from textual.containers import Container, Horizontal
from textual.widgets import Footer, Header

from repl_client.tui.views.message_area_view import MessageAreaView
from repl_client.tui.views.sidebar_view import SidebarView
from repl_client.tui.views.status_area_view import StatusAreaView
from repl_client.tui.widgets import ChatInput

if TYPE_CHECKING:
    from textual.app import ComposeResult


class LayoutView(Container):
    """Main layout container for the REPL app.

    Coordinates major screen areas:
    - Header (docked top)
    - Main content (horizontal split):
      - Message area (fills space)
      - Sidebar (toggleable)
    - Chat input (multi-line, auto-height)
    - Status area (2 lines)
    - Footer (docked bottom, key bindings)

    This is the top-level presentational component.
    Styling is in styles/index.tcss
    """

    def __init__(
        self,
        cwd: Path | None = None,
        history_file: Path | None = None,
        **kwargs,
    ):
        """Initialize the layout view.

        Args:
            cwd: Current working directory for file completion
            history_file: Path to history file
            **kwargs: Additional arguments for parent
        """
        super().__init__(**kwargs)
        self._cwd = cwd or Path.cwd()
        self._history_file = history_file or (Path.cwd() / ".repl" / "history.jsonl")

    def compose(self) -> ComposeResult:
        """Compose the main layout.

        Layout from top to bottom:
        - Header
        - Horizontal container (messages + sidebar)
        - Chat input
        - Status area
        - Footer
        """
        yield Header()

        with Horizontal(id="main-content"):
            yield MessageAreaView(id="message-area")
            yield SidebarView(id="sidebar")

        yield ChatInput(
            cwd=self._cwd,
            history_file=self._history_file,
            id="chat-input",
        )

        yield StatusAreaView(id="status-area")

        yield Footer()

    def get_message_area(self) -> MessageAreaView:
        """Get the message area view.

        Returns:
            MessageAreaView instance
        """
        return self.query_one("#message-area", MessageAreaView)

    def get_sidebar(self) -> SidebarView:
        """Get the sidebar view.

        Returns:
            SidebarView instance
        """
        return self.query_one("#sidebar", SidebarView)

    def get_chat_input(self) -> ChatInput:
        """Get the chat input widget.

        Returns:
            ChatInput instance
        """
        return self.query_one("#chat-input", ChatInput)

    def get_status_area(self) -> StatusAreaView:
        """Get the status area view.

        Returns:
            StatusAreaView instance
        """
        return self.query_one("#status-area", StatusAreaView)
