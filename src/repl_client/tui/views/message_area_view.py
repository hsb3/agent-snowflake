"""Message area view - scrollable message display.

Manages mounting and unmounting of message widgets.
This is the presentational layer - no business logic.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import ScrollableContainer

from repl_client.tui.widgets import (
    AssistantMessage,
    LoadingWidget,
    ToolCallMessage,
    UserMessage,
)

if TYPE_CHECKING:
    from typing import Any


class MessageAreaView(ScrollableContainer):
    """View for displaying messages in a scrollable container.

    Coordinates mounting/unmounting of message widgets.
    Like a webapp list view - manages the display, not the data.

    Features:
    - Mount user messages
    - Mount/stream assistant messages
    - Mount tool call messages
    - Show/hide loading indicators
    - Clear all messages
    """

    DEFAULT_CSS = """
    MessageAreaView {
        height: 1fr;
        width: 1fr;
        background: $surface;
        padding: 0 1;
        overflow-y: auto;
    }
    """

    async def add_user_message(self, text: str) -> UserMessage:
        """Mount a user message widget.

        Args:
            text: User message text

        Returns:
            The mounted UserMessage widget
        """
        msg = UserMessage(text)
        await self.mount(msg)
        self.scroll_end(animate=False)
        return msg

    async def add_assistant_message(self, initial_text: str = "") -> AssistantMessage:
        """Mount an assistant message widget.

        Args:
            initial_text: Optional initial text content

        Returns:
            The mounted AssistantMessage widget (ready for streaming)
        """
        msg = AssistantMessage(initial_text)
        await self.mount(msg)
        self.scroll_end(animate=False)
        return msg

    async def add_tool_call(
        self,
        tool_name: str,
        args: dict[str, Any] | None = None,
    ) -> ToolCallMessage:
        """Mount a tool call message widget.

        Args:
            tool_name: Name of the tool being called
            args: Tool arguments (optional)

        Returns:
            The mounted ToolCallMessage widget
        """
        msg = ToolCallMessage(tool_name=tool_name, args=args)
        await self.mount(msg)
        self.scroll_end(animate=False)
        return msg

    async def show_loading(self, message: str = "Thinking...") -> LoadingWidget:
        """Mount a loading indicator widget.

        Args:
            message: Loading message to display

        Returns:
            The mounted LoadingWidget
        """
        loading = LoadingWidget()
        await self.mount(loading)
        self.scroll_end(animate=False)
        return loading

    async def clear_messages(self) -> None:
        """Remove all message widgets from the view."""
        self.remove_children()

    def scroll_to_bottom(self, *, animate: bool = False) -> None:
        """Scroll to the bottom of the message area.

        Args:
            animate: Whether to animate the scroll
        """
        self.scroll_end(animate=animate)
