"""Welcome screen modal shown on first startup.

Provides quick start info and navigation options.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Markdown


class WelcomeScreen(ModalScreen[str | None]):
    """Welcome modal screen shown on startup.

    Returns:
        "commands" to open command palette, None to dismiss
    """

    BINDINGS = [
        ("escape", "dismiss_welcome", "Close"),
        ("enter", "dismiss_welcome", "Close"),
    ]

    DEFAULT_CSS = """
    WelcomeScreen {
        align: center middle;
    }

    WelcomeScreen > Container {
        width: 70;
        height: auto;
        max-height: 80%;
        background: $surface-lighten-1;
        border: thick $primary;
        padding: 1 2;
    }

    WelcomeScreen .welcome-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        padding: 1;
    }

    WelcomeScreen Markdown {
        margin: 1 0;
        padding: 0 1;
    }

    WelcomeScreen .button-bar {
        height: auto;
        align: center middle;
        padding: 1;
    }

    WelcomeScreen Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the welcome screen."""
        with Container():
            yield Label("Welcome to REPL!", classes="welcome-title")

            yield Markdown(
                "**Quick Start:**\n"
                "- **Ctrl+P** - Open command palette (all commands & shortcuts)\n"
                "- **F4** - Toggle sidebar (view threads, agents, session info)\n"
                "- Type `/help` to see available slash commands\n\n"
                "**Common Shortcuts:**\n"
                "- **Ctrl+B** - Focus sidebar\n"
                "- **F2** - Quick agent selection\n"
                "- **F6** - Agent configuration\n"
                "- **Ctrl+L** - Clear messages\n"
                "- **Ctrl+C** - Quit\n\n"
                "Start chatting or explore the command palette!"
            )

            with Horizontal(classes="button-bar"):
                yield Button("Start Chatting", variant="primary", id="btn-dismiss")
                yield Button("Open Commands", variant="default", id="btn-commands")

    def on_mount(self) -> None:
        """Focus the primary button on mount."""
        self.query_one("#btn-dismiss", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-dismiss":
            self.dismiss(None)
        elif event.button.id == "btn-commands":
            self.dismiss("commands")

    def action_dismiss_welcome(self) -> None:
        """Handle escape/enter to dismiss."""
        self.dismiss(None)
