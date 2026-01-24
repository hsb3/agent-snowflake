"""Layer 5: HITL Handler for Phase 2

Handles Human-in-the-Loop (HITL) interrupts:
- Shows approval prompts
- Collects user decisions
- Formats resume commands
"""

from repl_client.streaming.types import Interrupt
from repl_client.ui.renderer import Renderer
from repl_client.ui.content_blocks import ToolRenderRegistry
from repl_client.core.session import SessionState


class HITLHandler:
    """Handle HITL interrupts - show approval prompts and collect decisions"""

    def __init__(self, renderer: Renderer, tool_registry: ToolRenderRegistry | None = None):
        """Initialize with renderer and optional tool registry

        Args:
            renderer: Renderer instance for displaying prompts
            tool_registry: ToolRenderRegistry for custom formatters. If None, creates default.
        """
        self.renderer = renderer
        self.tool_registry = tool_registry or ToolRenderRegistry()

    def handle_interrupt(self, interrupt: Interrupt, session: SessionState) -> dict:
        """Show approval prompt and return command payload for resume

        Args:
            interrupt: Interrupt containing tool info
            session: SessionState (for future use in Phase 3)

        Returns:
            Command dict ready for client: {"resume": {"approve": bool}}
        """
        # Extract tool info from interrupt value
        tool_name = interrupt.value.get("tool", "unknown")
        tool_args = interrupt.value.get("args", {})

        # Show approval prompt and get decision
        approved = self._show_approval_prompt(tool_name, tool_args)

        # Build and return resume command
        return self._build_resume_command(approved, interrupt)

    def _show_approval_prompt(self, tool_name: str, tool_args: dict) -> bool:
        """Display tool info and get y/n approval

        Args:
            tool_name: Name of the tool requesting approval
            tool_args: Arguments for the tool

        Returns:
            True if approved, False if rejected
        """
        # Format tool preview using registry
        preview = self._format_tool_preview(tool_name, tool_args)

        # Show in panel
        self.renderer.render_panel(
            content=preview,
            title=f"Tool Approval Required: {tool_name}",
            style="yellow"
        )

        # Get user input (simple y/n for Phase 2)
        while True:
            response = input("Approve? (y/n): ").strip().lower()

            if response in ('y', 'yes'):
                return True
            elif response in ('n', 'no'):
                return False
            else:
                # Invalid input - reprompt
                print("Please enter 'y' or 'n'")

    def _format_tool_preview(self, tool_name: str, tool_args: dict) -> str:
        """Format tool for preview - use registry or fallback

        Args:
            tool_name: Name of the tool
            tool_args: Tool arguments

        Returns:
            Formatted preview string
        """
        return self.tool_registry.format(tool_name, tool_args)

    def _build_resume_command(self, approved: bool, interrupt: Interrupt) -> dict:
        """Build command payload for resume

        Args:
            approved: Whether user approved the tool
            interrupt: Original interrupt (for future use)

        Returns:
            Command dict: {"resume": {"approve": bool}}
        """
        return {
            "resume": {
                "approve": approved
            }
        }
