"""HITL approval modal screen.

Displays tool call details and collects user approval or rejection
before the agent continues execution.

Key Classes:
    HITLApprovalScreen: ModalScreen that returns True (approved) or False (rejected).

Dependencies:
    - textual: ModalScreen, widgets for UI composition
"""

from __future__ import annotations

import json

from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static


class HITLApprovalScreen(ModalScreen[bool]):
    """Modal screen for approving or rejecting a tool call.

    Shows the tool name and pretty-printed arguments, with Approve and Reject
    buttons. Returns True when approved, False when rejected.

    Keyboard shortcuts:
        Enter: Approve the tool call
        Escape: Reject the tool call
    """

    DEFAULT_CSS = """
    HITLApprovalScreen {
        align: center middle;
    }

    HITLApprovalScreen > Container {
        width: 70;
        height: auto;
        max-height: 35;
        background: $panel;
        border: thick $warning;
        padding: 1 2;
    }

    HITLApprovalScreen .modal-title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $warning;
        margin-bottom: 1;
    }

    HITLApprovalScreen .tool-name-label {
        width: 100%;
        color: $text-muted;
        margin-bottom: 0;
    }

    HITLApprovalScreen .tool-name-value {
        width: 100%;
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    HITLApprovalScreen .tool-args-label {
        width: 100%;
        color: $text-muted;
        margin-bottom: 0;
    }

    HITLApprovalScreen .tool-args-value {
        width: 100%;
        height: auto;
        max-height: 15;
        overflow-y: auto;
        padding: 1;
        background: $surface-darken-1;
        color: $text;
        margin-bottom: 1;
    }

    HITLApprovalScreen .hint-text {
        width: 100%;
        text-align: center;
        color: $text-muted;
        text-style: italic;
        margin-bottom: 1;
    }

    HITLApprovalScreen .button-row {
        width: 100%;
        height: 3;
        align: center middle;
    }

    HITLApprovalScreen .button-row Button {
        margin: 0 2;
        min-width: 16;
    }

    HITLApprovalScreen #btn-approve {
        background: $success;
        color: $text;
    }

    HITLApprovalScreen #btn-reject {
        background: $error;
        color: $text;
    }
    """

    BINDINGS = [
        ("enter", "approve", "Approve"),
        ("escape", "reject", "Reject"),
    ]

    def __init__(self, tool_name: str, tool_args: dict) -> None:
        """Initialize with tool call details.

        Args:
            tool_name: Name of the tool requesting approval.
            tool_args: Dictionary of arguments for the tool call.
        """
        super().__init__()
        self.tool_name = tool_name
        self.tool_args = tool_args

    def compose(self) -> ComposeResult:
        """Compose the approval modal layout."""
        with Container():
            yield Label("Tool Call Approval Required", classes="modal-title")

            yield Label("Tool:", classes="tool-name-label")
            yield Static(self.tool_name, classes="tool-name-value")

            yield Label("Arguments:", classes="tool-args-label")
            yield Static(self._format_args(), classes="tool-args-value")

            yield Label("Enter to approve / Escape to reject", classes="hint-text")

            with Horizontal(classes="button-row"):
                yield Button("Approve", id="btn-approve", variant="success")
                yield Button("Reject", id="btn-reject", variant="error")

    def on_mount(self) -> None:
        """Focus the approve button on mount."""
        self.query_one("#btn-approve", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses.

        Args:
            event: Button pressed event.
        """
        if event.button.id == "btn-approve":
            self.dismiss(True)
        elif event.button.id == "btn-reject":
            self.dismiss(False)

    def action_approve(self) -> None:
        """Approve the tool call (Enter key)."""
        self.dismiss(True)

    def action_reject(self) -> None:
        """Reject the tool call (Escape key)."""
        self.dismiss(False)

    def _format_args(self) -> str:
        """Format tool arguments for display.

        Returns:
            Pretty-printed string of tool arguments.
        """
        if not self.tool_args:
            return "(no arguments)"

        try:
            return json.dumps(self.tool_args, indent=2, default=str)
        except (TypeError, ValueError):
            # Fallback to simple key-value formatting
            lines = [f"{k}: {v!r}" for k, v in self.tool_args.items()]
            return "\n".join(lines)
