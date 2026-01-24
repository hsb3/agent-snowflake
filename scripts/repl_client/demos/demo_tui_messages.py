#!/usr/bin/env python
"""Demo app to showcase Textual message widgets.

Run with:
    uv run python scripts/repl_client/demos/demo_tui_messages.py
"""

from __future__ import annotations

import asyncio

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header

from repl_client.tui.widgets.messages import (
    AssistantMessage,
    ToolCallMessage,
    UserMessage,
)


class MessageDemo(App):
    """Demo app showing all message widget types."""

    CSS = """
    Screen {
        background: $surface;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "toggle_tool", "Toggle tool output"),
        ("s", "stream_assistant", "Stream assistant"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tool_widgets = []
        self.assistant_widget = None

    def compose(self) -> ComposeResult:
        """Compose the demo layout."""
        yield Header()

        # User message
        yield UserMessage("Hello, agent! Can you help me query the database?")

        # Assistant message (with markdown)
        assistant = AssistantMessage(
            "Sure! I'll help you query the database. "
            "Here's what I can do:\n\n"
            "- **Query** the database\n"
            "- Show **schema** information\n"
            "- Execute `SELECT` statements\n\n"
            "Let me know what you need!"
        )
        self.assistant_widget = assistant
        yield assistant

        # User follow-up
        yield UserMessage("Show me all users from the database")

        # Tool call message - pending
        tool1 = ToolCallMessage(
            "sql_db_query",
            {"query": "SELECT * FROM users LIMIT 10", "limit": 10},
        )
        self.tool_widgets.append(tool1)
        yield tool1

        # Tool call message - success with short output
        tool2 = ToolCallMessage("sql_db_schema", {"table_names": ["users", "orders"]})
        tool2.set_success("Schema for users:\n  - id: INTEGER\n  - name: TEXT\n  - email: TEXT")
        self.tool_widgets.append(tool2)
        yield tool2

        # Tool call message - success with long output (will be collapsed)
        tool3 = ToolCallMessage(
            "sql_db_query",
            {"query": "SELECT * FROM products WHERE category = 'electronics'"},
        )
        long_output = "\n".join(
            [
                f"Product {i}: {{'id': {i}, 'name': 'Product {i}', 'price': {i * 10}}}"
                for i in range(20)
            ]
        )
        tool3.set_success(long_output)
        self.tool_widgets.append(tool3)
        yield tool3

        # Tool call message - error
        tool4 = ToolCallMessage("sql_db_query", {"query": "SELECT * FROM invalid_table"})
        tool4.set_error("Error: Table 'invalid_table' does not exist in the database")
        self.tool_widgets.append(tool4)
        yield tool4

        # Tool call message - rejected
        tool5 = ToolCallMessage("delete_all_users", {})
        tool5.set_rejected()
        self.tool_widgets.append(tool5)
        yield tool5

        # Another user message
        yield UserMessage("Thanks! That's helpful.")

        # Assistant response
        yield AssistantMessage("You're welcome! Let me know if you need anything else.")

        yield Footer()

    def action_toggle_tool(self) -> None:
        """Toggle first tool with long output."""
        if len(self.tool_widgets) >= 3:
            self.tool_widgets[2].toggle_output()

    async def action_stream_assistant(self) -> None:
        """Demo streaming to assistant widget."""
        if not self.assistant_widget:
            return

        # Clear existing content
        await self.assistant_widget.set_content("")

        # Stream some content
        chunks = [
            "Let me ",
            "stream ",
            "some **content** ",
            "to show ",
            "how streaming ",
            "works!\n\n",
            "- Item 1\n",
            "- Item 2\n",
            "- Item 3\n",
        ]

        for chunk in chunks:
            await self.assistant_widget.append_content(chunk)
            await asyncio.sleep(0.2)

        await self.assistant_widget.stop_stream()


def main():
    """Run the demo app."""
    app = MessageDemo()
    app.run()


if __name__ == "__main__":
    main()
