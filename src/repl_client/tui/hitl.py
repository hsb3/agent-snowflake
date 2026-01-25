"""HITL handler for Textual TUI.

Handles Human-in-the-Loop (HITL) interrupts in the TUI:
- Shows approval prompts
- Collects user decisions
- Returns approval status
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from repl_client.streaming.types import Interrupt

if TYPE_CHECKING:
    from repl_client.core.session import SessionState
    from repl_client.tui.app import REPLApp


class HITLHandler:
    """Handle HITL interrupts in Textual TUI.

    For Phase 2, uses simple modal/prompt approach.
    For Phase 3, can upgrade to interactive arrow-key menu.
    """

    def __init__(self, app: REPLApp):
        """Initialize with app reference.

        Args:
            app: REPLApp instance for displaying prompts
        """
        self.app = app

    async def handle_interrupt(
        self,
        interrupt: Interrupt,
        session: SessionState,  # noqa: ARG002
    ) -> bool:
        """Show approval prompt and return user decision.

        Args:
            interrupt: Interrupt containing tool info
            session: SessionState (for future use)

        Returns:
            True if approved, False if rejected
        """
        # Extract tool info from interrupt value
        tool_name = interrupt.value.get("tool", "unknown")
        tool_args = interrupt.value.get("args", {})

        # Show approval prompt
        approved = await self._show_approval_prompt(tool_name, tool_args)

        return approved

    async def _show_approval_prompt(self, tool_name: str, tool_args: dict) -> bool:
        """Display tool info and get approval decision.

        For Phase 2, uses Textual's built-in action_question.
        For Phase 3, upgrade to custom approval widget.

        Args:
            tool_name: Name of the tool requesting approval
            tool_args: Arguments for the tool

        Returns:
            True if approved, False if rejected
        """
        # Format tool preview
        self._format_tool_preview(tool_name, tool_args)

        # Use Textual's action_question for simple y/n prompt
        # Note: This is a simple implementation for Phase 2
        # Phase 3 can upgrade to ApprovalMenu widget (like deepagents)

        # For now, default to approve (Phase 2 MVP)
        # TODO: Implement proper approval modal in Phase 3
        approved = True

        return approved

    def _format_tool_preview(self, tool_name: str, tool_args: dict) -> str:
        """Format tool for preview.

        Args:
            tool_name: Name of the tool
            tool_args: Tool arguments

        Returns:
            Formatted preview string
        """
        # Simple formatting for Phase 2
        # Phase 3 can add custom formatters per tool
        args_str = "\n".join(f"  {k}: {v!r}" for k, v in tool_args.items())
        return f"Arguments:\n{args_str}" if args_str else "No arguments"
