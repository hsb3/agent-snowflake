"""HITL handler for Textual TUI.

Handles Human-in-the-Loop (HITL) interrupts in the TUI by pushing
an approval modal screen and awaiting the user's decision.

Key Classes:
    HITLHandler: Bridges interrupt events to the approval modal screen.

Dependencies:
    - repl_client.tui.screens: HITLApprovalScreen modal
    - repl_client.streaming.types: Interrupt data class
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from repl_client.streaming.types import Interrupt
from repl_client.tui.screens import HITLApprovalScreen

if TYPE_CHECKING:
    from repl_client.core.session import SessionState
    from repl_client.tui.app import REPLApp


class HITLHandler:
    """Handle HITL interrupts in Textual TUI.

    Pushes an HITLApprovalScreen modal to collect the user's approve/reject
    decision for tool calls that require human approval.
    """

    def __init__(self, app: REPLApp):
        """Initialize with app reference.

        Args:
            app: REPLApp instance for pushing modal screens.
        """
        self.app = app

    async def handle_interrupt(
        self,
        interrupt: Interrupt,
        session: SessionState,  # noqa: ARG002
    ) -> bool:
        """Show approval modal and return user decision.

        Args:
            interrupt: Interrupt containing tool info.
            session: SessionState (reserved for future use).

        Returns:
            True if approved, False if rejected.
        """
        tool_name = interrupt.value.get("tool", "unknown")
        tool_args = interrupt.value.get("args", {})

        approved = await self.app.push_screen(
            HITLApprovalScreen(tool_name, tool_args),
        )

        return bool(approved)
