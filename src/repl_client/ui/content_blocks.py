"""Tool rendering registry for formatting tool previews.

NOTE: ToolRenderRegistry is used by streaming/hitl.py for HITL approval prompts.
This is shared infrastructure between classic REPL and TUI (both need tool formatting).

ContentBlockRenderer was removed (dead code). See git history if needed.

Future: Consider extracting ToolRenderRegistry to core/formatters.py for clearer ownership.
"""

from dataclasses import dataclass
from typing import Callable
import json

from repl_client.ui.renderer import Renderer


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


# NOTE: ContentBlockRenderer was removed (dead code - never used in production)
# Classic REPL renders chunks inline in __main__.py _handle_stream()
# TUI uses Textual widgets (ToolCallMessage, AssistantMessage)
# If content block rendering is needed in future, see git history for ContentBlockRenderer class
