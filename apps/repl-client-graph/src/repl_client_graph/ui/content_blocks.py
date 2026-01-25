"""Render content blocks and tool calls with registry-based tool formatters"""

from dataclasses import dataclass
from typing import Callable
import json

from repl_client_graph.ui.renderer import Renderer


# Data structures for content blocks and tool calls
@dataclass
class ContentBlock:
    """Content block from message stream"""

    type: str
    index: int
    text: str | None = None
    tool_id: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None
    partial_json: str | None = None


@dataclass
class ToolCall:
    """Complete tool call"""

    id: str
    name: str
    args: dict
    type: str = "function"


class ToolRenderRegistry:
    """Registry for tool-specific formatters with generic fallback"""

    def __init__(self):
        """Initialize registry with builtin formatters"""
        self._formatters: dict[str, Callable[[dict], str]] = {}
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register builtin formatters for common tools"""

        # SQL query formatter with syntax highlighting info
        def format_sql(args: dict) -> str:
            query = args.get("query", "")
            return f"SQL Query:\n{query}"

        self.register("sql_db_query", format_sql)

    def register(self, tool_name: str, formatter: Callable[[dict], str]) -> None:
        """Register custom formatter for a tool

        Args:
            tool_name: Name of the tool
            formatter: Function that takes args dict and returns formatted string
        """
        self._formatters[tool_name] = formatter

    def format(self, tool_name: str, args: dict) -> str:
        """Format tool args using registered formatter or fallback

        Args:
            tool_name: Name of the tool
            args: Tool arguments dict

        Returns:
            Formatted string representation of the tool call
        """
        # Use registered formatter if available
        if tool_name in self._formatters:
            return self._formatters[tool_name](args)

        # Generic fallback
        return self._generic_format(tool_name, args)

    def _generic_format(self, tool_name: str, args: dict) -> str:
        """Generic fallback formatter for unknown tools

        Args:
            tool_name: Name of the tool
            args: Tool arguments dict

        Returns:
            Generic formatted string
        """
        if not args:
            return f"Tool: {tool_name}\nArgs: (none)"

        # Pretty print args as JSON
        args_str = json.dumps(args, indent=2)
        return f"Tool: {tool_name}\nArgs:\n{args_str}"


class ContentBlockRenderer:
    """Render content blocks and tool calls"""

    def __init__(self, renderer: Renderer, registry: ToolRenderRegistry | None = None):
        """Initialize with renderer and optional tool registry

        Args:
            renderer: Base Renderer instance
            registry: ToolRenderRegistry for custom formatters. If None, creates default.
        """
        self.renderer = renderer
        self.registry = registry or ToolRenderRegistry()

    def render_content_block(self, block: ContentBlock) -> None:
        """Route content block to type-specific renderer

        Args:
            block: ContentBlock to render
        """
        if block.type == "text" and block.text:
            self.renderer.render_text(block.text, style="cyan")

        elif block.type == "tool_use":
            # Render tool call preview
            if block.tool_name and block.tool_input:
                preview = self.render_tool_preview(block.tool_name, block.tool_input)
                self.renderer.render_panel(
                    content=preview, title=f"Calling Tool: {block.tool_name}", style="yellow"
                )

        elif block.type == "tool_result":
            # Render tool result
            result_text = block.text or "(no output)"
            self.renderer.render_panel(
                content=result_text,
                title=f"Tool Result: {block.tool_id or 'unknown'}",
                style="blue",
            )

        else:
            # Unknown block type - just log or ignore
            pass

    def render_tool_call(self, tool_call: ToolCall) -> None:
        """Show tool call preview

        Args:
            tool_call: ToolCall to render
        """
        preview = self.render_tool_preview(tool_call.name, tool_call.args)
        self.renderer.render_panel(
            content=preview, title=f"Tool Call: {tool_call.name}", style="yellow"
        )

    def render_tool_preview(self, tool_name: str, args: dict) -> str:
        """Format tool for preview using registry

        Args:
            tool_name: Name of the tool
            args: Tool arguments

        Returns:
            Formatted preview string
        """
        return self.registry.format(tool_name, args)
