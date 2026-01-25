"""Render user/AI/tool messages"""

from repl_client_graph.ui.renderer import Renderer


class MessageRenderer:
    """Render user, AI, and tool messages"""

    def __init__(self, renderer: Renderer):
        """Initialize with base renderer

        Args:
            renderer: Base Renderer instance
        """
        self.renderer = renderer

    def render_user_message(self, content: str) -> None:
        """Render user message in green

        Args:
            content: User message text
        """
        self.renderer.render_text(f"User: {content}", style="green")

    def render_ai_text(self, text: str) -> None:
        """Render AI text with markdown support (cyan)

        Args:
            text: AI response text (supports markdown)
        """
        if not text:
            return

        # Use markdown rendering for AI responses to support formatting
        self.renderer.render_markdown(text)

    def render_tool_result(self, tool_name: str, result: str, status: str) -> None:
        """Render tool result in panel

        Args:
            tool_name: Name of the tool that was executed
            result: Tool execution result/output
            status: Status of execution (success, error, etc.)
        """
        # Choose style based on status
        style = "green" if status == "success" else "yellow" if status == "error" else "blue"

        # Create panel with tool name as title
        self.renderer.render_panel(content=result, title=f"Tool: {tool_name}", style=style)
