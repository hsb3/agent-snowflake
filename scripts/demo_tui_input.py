#!/usr/bin/env python3
"""Demo app for ChatInput widget with history and completion support."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import ScrollableContainer
from textual.widgets import Footer, Header, Static

from repl_client.tui.widgets.input import ChatInput


class MessageLog(ScrollableContainer):
    """Container for displaying submitted messages."""

    DEFAULT_CSS = """
    MessageLog {
        height: 1fr;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }

    MessageLog .message {
        margin: 1 0;
    }

    MessageLog .message-normal {
        color: $text;
    }

    MessageLog .message-command {
        color: $success;
    }

    MessageLog .message-bash {
        color: $warning;
    }
    """

    def add_message(self, text: str, mode: str = "normal") -> None:
        """Add a message to the log."""
        style_class = f"message message-{mode}"
        mode_label = f"[{mode.upper()}]" if mode != "normal" else ""
        message = Static(
            f"{mode_label} {text}" if mode_label else text,
            classes=style_class,
        )
        self.mount(message)
        self.scroll_end(animate=False)


class InputDemo(App):
    """Demo application for ChatInput widget."""

    CSS = """
    Screen {
        layout: vertical;
    }

    MessageLog {
        height: 1fr;
    }

    ChatInput {
        dock: bottom;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, **kwargs):
        """Initialize the demo app."""
        super().__init__(**kwargs)
        self._message_log: MessageLog | None = None

    def compose(self) -> ComposeResult:
        """Compose the demo application."""
        yield Header()
        yield MessageLog()
        yield ChatInput(history_file=Path.cwd() / ".repl" / "demo_history.jsonl")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the application after mounting."""
        self._message_log = self.query_one(MessageLog)
        self._message_log.add_message("Welcome to ChatInput Demo!", "normal")
        self._message_log.add_message("Features:", "normal")
        self._message_log.add_message("• Enter to submit, Ctrl+J for newline", "normal")
        self._message_log.add_message("• Up/Down arrows for history (on first/last line)", "normal")
        self._message_log.add_message("• /command for command mode", "command")
        self._message_log.add_message("• !bash for bash mode", "bash")
        self._message_log.add_message("", "normal")

    def on_chat_input_submitted(self, message: ChatInput.Submitted) -> None:
        """Handle submitted input."""
        if self._message_log:
            self._message_log.add_message(message.value, message.mode)
        self.notify(f"Submitted [{message.mode}]: {message.value}")

    def on_chat_input_mode_changed(self, message: ChatInput.ModeChanged) -> None:
        """Handle mode changes."""
        mode_colors = {
            "normal": "white",
            "command": "green",
            "bash": "yellow",
        }
        color = mode_colors.get(message.mode, "white")
        self.notify(f"Mode: {message.mode}", severity="information", timeout=1)


def main():
    """Run the demo application."""
    app = InputDemo()
    app.run()


if __name__ == "__main__":
    main()
