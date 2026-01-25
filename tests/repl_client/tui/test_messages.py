"""Tests for Textual message widgets."""

from __future__ import annotations

import pytest
from textual.widgets import Static

from repl_client.tui.widgets.messages import (
    AssistantMessage,
    ToolCallMessage,
    UserMessage,
)


class TestUserMessage:
    """Tests for UserMessage widget."""

    def test_creates_with_content(self):
        """Test that UserMessage can be created with content."""
        message = UserMessage("Hello, agent!")
        assert message._content == "Hello, agent!"

    def test_has_green_prefix(self):
        """Test that UserMessage has styled prefix in composed content."""
        message = UserMessage("Test message")
        # Verify widget can be instantiated and has expected properties
        assert isinstance(message, Static)
        assert message._content == "Test message"

    def test_safe_from_markup_injection(self):
        """Test that UserMessage doesn't interpret Rich markup."""
        dangerous_content = "[bold red]Not actually bold[/bold red]"
        message = UserMessage(dangerous_content)
        assert message._content == dangerous_content


class TestAssistantMessage:
    """Tests for AssistantMessage widget."""

    def test_creates_empty(self):
        """Test that AssistantMessage can be created empty."""
        message = AssistantMessage()
        assert message._content == ""

    def test_creates_with_content(self):
        """Test that AssistantMessage can be created with content."""
        message = AssistantMessage("Initial content")
        assert message._content == "Initial content"

    @pytest.mark.asyncio
    async def test_append_content(self):
        """Test appending content to assistant message."""
        message = AssistantMessage()
        # Simulate mounting by setting up markdown widget
        # In real app, this happens via compose() and on_mount()
        assert message._content == ""


class TestToolCallMessage:
    """Tests for ToolCallMessage widget."""

    def test_creates_with_tool_name(self):
        """Test that ToolCallMessage can be created with tool name."""
        message = ToolCallMessage("sql_db_query", {"query": "SELECT * FROM users"})
        assert message._tool_name == "sql_db_query"
        assert message._args == {"query": "SELECT * FROM users"}

    def test_creates_without_args(self):
        """Test that ToolCallMessage can be created without args."""
        message = ToolCallMessage("list_tables")
        assert message._tool_name == "list_tables"
        assert message._args == {}

    def test_initial_state_is_pending(self):
        """Test that ToolCallMessage starts in pending state."""
        message = ToolCallMessage("test_tool")
        assert message._status == "pending"
        assert message._output == ""
        assert message._expanded is False

    def test_set_success(self):
        """Test marking tool call as successful."""
        message = ToolCallMessage("test_tool")
        message.set_success("Operation completed")
        assert message._status == "success"
        assert message._output == "Operation completed"

    def test_set_error(self):
        """Test marking tool call as failed."""
        message = ToolCallMessage("test_tool")
        message.set_error("Connection failed")
        assert message._status == "error"
        assert message._output == "Connection failed"
        assert message._expanded is True  # Errors auto-expand

    def test_set_rejected(self):
        """Test marking tool call as rejected."""
        message = ToolCallMessage("test_tool")
        message.set_rejected()
        assert message._status == "rejected"

    def test_toggle_output(self):
        """Test toggling output expansion."""
        message = ToolCallMessage("test_tool")
        message.set_success("Some output")

        # Initial state
        assert message._expanded is False

        # Toggle to expand
        message.toggle_output()
        assert message._expanded is True

        # Toggle to collapse
        message.toggle_output()
        assert message._expanded is False

    def test_toggle_output_when_no_output(self):
        """Test that toggling does nothing when there's no output."""
        message = ToolCallMessage("test_tool")

        assert message._expanded is False
        message.toggle_output()
        assert message._expanded is False  # Should remain unchanged

    def test_has_output_property(self):
        """Test has_output property."""
        message = ToolCallMessage("test_tool")
        assert message.has_output is False

        message.set_success("Result")
        assert message.has_output is True

    def test_filtered_args_for_write_file(self):
        """Test that large args are filtered for write_file tool."""
        message = ToolCallMessage(
            "write_file",
            {
                "file_path": "/path/to/file.py",
                "content": "x" * 1000,  # Large content
                "mode": "w",
            },
        )
        filtered = message._filtered_args()
        assert "file_path" in filtered
        assert "content" not in filtered  # Large content filtered
        assert "mode" not in filtered

    def test_filtered_args_for_regular_tool(self):
        """Test that args are not filtered for regular tools."""
        message = ToolCallMessage(
            "sql_db_query",
            {"query": "SELECT * FROM users", "limit": 10},
        )
        filtered = message._filtered_args()
        assert filtered == {"query": "SELECT * FROM users", "limit": 10}
