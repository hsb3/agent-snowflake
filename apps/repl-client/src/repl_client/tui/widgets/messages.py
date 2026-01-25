"""Message widgets for REPL TUI.

Based on deepagents patterns:
- UserMessage: Static widget with green border and styled prefix
- AssistantMessage: Vertical container with MarkdownStream for efficient streaming
- ToolCallMessage: Vertical container with multi-state and collapsible output
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rich.text import Text
from textual.containers import Vertical
from textual.widgets import Markdown, Static
from textual.widgets._markdown import MarkdownStream

if TYPE_CHECKING:
    from textual.app import ComposeResult


class UserMessage(Static):
    """Widget displaying a user message.

    Features:
    - Green left border (thick)
    - Styled prefix "> " in bold green
    - Auto height
    - Safe from markup injection
    """

    DEFAULT_CSS = """
    UserMessage {
        height: auto;
        padding: 0 1;
        margin: 1 0;
        background: $surface;
        border-left: thick green;
    }
    """

    def __init__(self, content: str, **kwargs: Any) -> None:
        """Initialize a user message.

        Args:
            content: The message content
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(**kwargs)
        self._content = content

    def compose(self) -> ComposeResult:
        """Compose the user message layout."""
        # Use Text object to combine styled prefix with unstyled user content
        text = Text()
        text.append("> ", style="bold green")
        text.append(self._content)
        yield Static(text)


class AssistantMessage(Vertical):
    """Widget displaying an assistant message with markdown support.

    Uses MarkdownStream for smoother streaming instead of re-rendering
    the full content on each update.

    Features:
    - Markdown rendering
    - Efficient streaming via MarkdownStream
    - Methods: append_content, stop_stream, set_content
    """

    DEFAULT_CSS = """
    AssistantMessage {
        height: auto;
        padding: 0 1;
        margin: 1 0;
    }

    AssistantMessage Markdown {
        padding: 0;
        margin: 0;
        border-left: thick cyan;
    }
    """

    def __init__(self, content: str = "", **kwargs: Any) -> None:
        """Initialize an assistant message.

        Args:
            content: Initial markdown content
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(**kwargs)
        self._content = content
        self._markdown: Markdown | None = None
        self._stream: MarkdownStream | None = None

    def compose(self) -> ComposeResult:
        """Compose the assistant message layout."""
        yield Markdown("", id="assistant-content")

    def on_mount(self) -> None:
        """Store reference to markdown widget."""
        self._markdown = self.query_one("#assistant-content", Markdown)

    def _get_markdown(self) -> Markdown:
        """Get the markdown widget, querying if not cached."""
        if self._markdown is None:
            self._markdown = self.query_one("#assistant-content", Markdown)
        return self._markdown

    def _ensure_stream(self) -> MarkdownStream:
        """Ensure the markdown stream is initialized."""
        if self._stream is None:
            self._stream = Markdown.get_stream(self._get_markdown())
        return self._stream

    async def append_content(self, text: str) -> None:
        """Append content to the message (for streaming).

        Uses MarkdownStream for smoother rendering instead of re-rendering
        the full content on each chunk.

        Args:
            text: Text to append
        """
        if not text:
            return
        self._content += text
        stream = self._ensure_stream()
        await stream.write(text)

    async def write_initial_content(self) -> None:
        """Write initial content if provided at construction time."""
        if self._content:
            stream = self._ensure_stream()
            await stream.write(self._content)

    async def stop_stream(self) -> None:
        """Stop the streaming and finalize the content."""
        if self._stream is not None:
            await self._stream.stop()
            self._stream = None

    async def set_content(self, content: str) -> None:
        """Set the full message content.

        This stops any active stream and sets content directly.

        Args:
            content: The markdown content to display
        """
        await self.stop_stream()
        self._content = content
        if self._markdown:
            await self._markdown.update(content)


class ToolCallMessage(Vertical):
    """Widget displaying a tool call with collapsible output.

    Tool outputs are shown as a 3-line preview by default.
    Click to expand/collapse the full output.

    Features:
    - Multi-state: pending, success, error, rejected
    - Collapsible output (3-line preview)
    - Click to toggle expansion
    - Status indicator with colors
    """

    DEFAULT_CSS = """
    ToolCallMessage {
        height: auto;
        padding: 0 1;
        margin: 1 0;
        background: $surface;
        border-left: thick yellow;
    }

    ToolCallMessage .tool-header {
        color: yellow;
        text-style: bold;
    }

    ToolCallMessage .tool-args {
        color: $text-muted;
        margin-left: 2;
    }

    ToolCallMessage .tool-status {
        margin-left: 2;
    }

    ToolCallMessage .tool-status.pending {
        color: $warning;
    }

    ToolCallMessage .tool-status.success {
        color: $success;
    }

    ToolCallMessage .tool-status.error {
        color: $error;
    }

    ToolCallMessage .tool-status.rejected {
        color: $warning;
    }

    ToolCallMessage .tool-output {
        margin-left: 2;
        margin-top: 1;
        padding: 1;
        background: $surface-darken-1;
        color: $text-muted;
        max-height: 20;
        overflow-y: auto;
    }

    ToolCallMessage .tool-output-preview {
        margin-left: 2;
        color: $text-muted;
    }

    ToolCallMessage .tool-output-hint {
        margin-left: 2;
        color: cyan;
        text-style: italic;
    }

    ToolCallMessage:hover {
        background: $surface-lighten-1;
    }
    """

    # Max lines/chars to show in preview mode
    _PREVIEW_LINES = 3
    _PREVIEW_CHARS = 200
    _MAX_INLINE_ARGS = 3

    def __init__(
        self,
        tool_name: str,
        args: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a tool call message.

        Args:
            tool_name: Name of the tool being called
            args: Tool arguments (optional)
            **kwargs: Additional arguments passed to parent
        """
        super().__init__(**kwargs)
        self._tool_name = tool_name
        self._args = args or {}
        self._status = "pending"
        self._output: str = ""
        self._expanded: bool = False
        # Widget references (set in on_mount)
        self._status_widget: Static | None = None
        self._preview_widget: Static | None = None
        self._hint_widget: Static | None = None
        self._full_widget: Static | None = None

    def compose(self) -> ComposeResult:
        """Compose the tool call message layout."""
        yield Static(
            f"[bold yellow]Tool:[/bold yellow] {self._tool_name}",
            classes="tool-header",
        )
        args = self._filtered_args()
        if args:
            args_str = ", ".join(
                f"{k}={v!r}" for k, v in list(args.items())[: self._MAX_INLINE_ARGS]
            )
            if len(args) > self._MAX_INLINE_ARGS:
                args_str += ", ..."
            yield Static(f"({args_str})", classes="tool-args")
        # Status - hidden by default, only shown for errors/rejections
        yield Static("", classes="tool-status", id="status")
        # Output area - hidden initially, shown when output is set
        # Use markup=False for output content to prevent Rich markup injection
        yield Static(
            "", classes="tool-output-preview", id="output-preview", markup=False
        )
        yield Static(
            "", classes="tool-output-hint", id="output-hint"
        )  # hint uses our markup
        yield Static("", classes="tool-output", id="output-full", markup=False)

    def on_mount(self) -> None:
        """Cache widget references and hide status/output areas initially."""
        self._status_widget = self.query_one("#status", Static)
        self._preview_widget = self.query_one("#output-preview", Static)
        self._hint_widget = self.query_one("#output-hint", Static)
        self._full_widget = self.query_one("#output-full", Static)
        self._status_widget.display = False
        self._preview_widget.display = False
        self._hint_widget.display = False
        self._full_widget.display = False

    def set_success(self, result: str = "") -> None:
        """Mark the tool call as successful.

        Args:
            result: Tool output/result to display
        """
        self._status = "success"
        self._output = result
        # No status label for success - just show output
        self._update_output_display()

    def set_error(self, error: str) -> None:
        """Mark the tool call as failed.

        Args:
            error: Error message
        """
        self._status = "error"
        self._output = error
        if self._status_widget:
            self._status_widget.add_class("error")
            self._status_widget.update("[red]✗ Error[/red]")
            self._status_widget.display = True
        # Always show full error - errors should be visible
        self._expanded = True
        self._update_output_display()

    def set_rejected(self) -> None:
        """Mark the tool call as rejected by user."""
        self._status = "rejected"
        if self._status_widget:
            self._status_widget.add_class("rejected")
            self._status_widget.update("[yellow]✗ Rejected[/yellow]")
            self._status_widget.display = True

    def toggle_output(self) -> None:
        """Toggle between preview and full output display."""
        if not self._output:
            return
        self._expanded = not self._expanded
        self._update_output_display()

    def on_click(self) -> None:
        """Handle click to toggle output expansion."""
        self.toggle_output()

    def _update_output_display(self) -> None:
        """Update the output display based on expanded state."""
        if not self._output or not self._preview_widget:
            return

        output_stripped = self._output.strip()
        lines = output_stripped.split("\n")
        total_lines = len(lines)
        total_chars = len(output_stripped)

        # Truncate if too many lines OR too many characters
        needs_truncation = (
            total_lines > self._PREVIEW_LINES or total_chars > self._PREVIEW_CHARS
        )

        if self._expanded:
            # Show full output
            if self._preview_widget:
                self._preview_widget.display = False
            if self._hint_widget:
                self._hint_widget.display = False
            if self._full_widget:
                self._full_widget.update(self._output)
                self._full_widget.display = True
        else:
            # Show preview
            if self._full_widget:
                self._full_widget.display = False
            if needs_truncation:
                # Truncate by lines first, then by chars
                if total_lines > self._PREVIEW_LINES:
                    preview_text = "\n".join(lines[: self._PREVIEW_LINES])
                else:
                    preview_text = output_stripped

                # Also truncate by chars if still too long
                if len(preview_text) > self._PREVIEW_CHARS:
                    preview_text = preview_text[: self._PREVIEW_CHARS] + "..."

                if self._preview_widget:
                    self._preview_widget.update(preview_text)
                    self._preview_widget.display = True

                # Show expand hint
                if self._hint_widget:
                    self._hint_widget.update("[dim]... (click to expand)[/dim]")
                    self._hint_widget.display = True
            elif output_stripped:
                # Output fits in preview, just show it
                if self._preview_widget:
                    self._preview_widget.update(output_stripped)
                    self._preview_widget.display = True
                if self._hint_widget:
                    self._hint_widget.display = False
            else:
                if self._preview_widget:
                    self._preview_widget.display = False
                if self._hint_widget:
                    self._hint_widget.display = False

    @property
    def has_output(self) -> bool:
        """Check if this tool message has output to display."""
        return bool(self._output)

    def _filtered_args(self) -> dict[str, Any]:
        """Filter large tool args for display."""
        if self._tool_name not in {"write_file", "edit_file"}:
            return self._args

        filtered: dict[str, Any] = {}
        for key in ("file_path", "path", "replace_all"):
            if key in self._args:
                filtered[key] = self._args[key]
        return filtered
