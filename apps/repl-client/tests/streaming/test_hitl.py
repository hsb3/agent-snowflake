"""Tests for Layer 5 HITL Handler (Phase 2)"""

from unittest.mock import Mock, patch

import pytest

from repl_client.core.session import SessionState
from repl_client.streaming.hitl import HITLHandler
from repl_client.streaming.types import Interrupt
from repl_client.ui.content_blocks import ToolRenderRegistry
from repl_client.ui.renderer import Renderer


@pytest.fixture
def mock_renderer():
    """Create mock renderer for testing"""
    return Mock(spec=Renderer)


@pytest.fixture
def session_state():
    """Create session state for testing"""
    return SessionState()


@pytest.fixture
def tool_registry():
    """Create tool registry for testing"""
    return ToolRenderRegistry()


@pytest.fixture
def hitl_handler(mock_renderer, tool_registry):
    """Create HITL handler with mock renderer"""
    return HITLHandler(renderer=mock_renderer, tool_registry=tool_registry)


class TestShowApprovalPrompt:
    """Test _show_approval_prompt method"""

    def test_approval_with_y(self, hitl_handler):
        """Test user approves with 'y'"""
        with patch("builtins.input", return_value="y"):
            result = hitl_handler._show_approval_prompt(
                tool_name="sql_db_query", tool_args={"query": "SELECT * FROM users"}
            )
        assert result is True

    def test_approval_with_yes(self, hitl_handler):
        """Test user approves with 'yes'"""
        with patch("builtins.input", return_value="yes"):
            result = hitl_handler._show_approval_prompt(
                tool_name="sql_db_query", tool_args={"query": "SELECT * FROM users"}
            )
        assert result is True

    def test_rejection_with_n(self, hitl_handler):
        """Test user rejects with 'n'"""
        with patch("builtins.input", return_value="n"):
            result = hitl_handler._show_approval_prompt(
                tool_name="sql_db_query", tool_args={"query": "DELETE FROM users"}
            )
        assert result is False

    def test_rejection_with_no(self, hitl_handler):
        """Test user rejects with 'no'"""
        with patch("builtins.input", return_value="no"):
            result = hitl_handler._show_approval_prompt(
                tool_name="sql_db_query", tool_args={"query": "DELETE FROM users"}
            )
        assert result is False

    def test_case_insensitive(self, hitl_handler):
        """Test input is case-insensitive"""
        with patch("builtins.input", return_value="Y"):
            result = hitl_handler._show_approval_prompt(tool_name="test_tool", tool_args={})
        assert result is True

        with patch("builtins.input", return_value="N"):
            result = hitl_handler._show_approval_prompt(tool_name="test_tool", tool_args={})
        assert result is False

    def test_invalid_input_reprompts(self, hitl_handler):
        """Test invalid input causes reprompt"""
        # Simulate invalid input followed by valid 'y'
        with patch("builtins.input", side_effect=["invalid", "maybe", "y"]):
            result = hitl_handler._show_approval_prompt(tool_name="test_tool", tool_args={})
        assert result is True


class TestFormatToolPreview:
    """Test _format_tool_preview method"""

    def test_format_sql_query_tool(self, hitl_handler):
        """Test SQL query tool gets syntax highlighted"""
        tool_args = {"query": "SELECT * FROM users WHERE id = 1"}
        result = hitl_handler._format_tool_preview("sql_db_query", tool_args)

        # Should contain the query text
        assert "SELECT * FROM users WHERE id = 1" in result
        # Should use SQL formatter from registry
        assert "SQL Query:" in result

    def test_format_generic_tool(self, hitl_handler):
        """Test unknown tool uses generic format"""
        tool_args = {"param1": "value1", "param2": 42}
        result = hitl_handler._format_tool_preview("unknown_tool", tool_args)

        # Should show tool name
        assert "Tool: unknown_tool" in result
        # Should show JSON args
        assert "param1" in result
        assert "value1" in result
        assert "42" in result

    def test_format_tool_no_args(self, hitl_handler):
        """Test tool with no arguments"""
        result = hitl_handler._format_tool_preview("simple_tool", {})

        assert "Tool: simple_tool" in result
        assert "(none)" in result or "Args:" in result


class TestBuildResumeCommand:
    """Test _build_resume_command method"""

    def test_build_approve_command(self, hitl_handler):
        """Test building resume command for approval"""
        interrupt = Interrupt(id="test_interrupt_1", value={"tool": "sql_db_query"})
        result = hitl_handler._build_resume_command(approved=True, interrupt=interrupt)

        assert result == {"resume": {"approve": True}}

    def test_build_reject_command(self, hitl_handler):
        """Test building resume command for rejection"""
        interrupt = Interrupt(id="test_interrupt_2", value={"tool": "dangerous_tool"})
        result = hitl_handler._build_resume_command(approved=False, interrupt=interrupt)

        assert result == {"resume": {"approve": False}}


class TestHandleInterrupt:
    """Test handle_interrupt full flow"""

    def test_handle_interrupt_approved(self, hitl_handler, session_state):
        """Test full flow when user approves"""
        interrupt = Interrupt(
            id="int_123", value={"tool": "sql_db_query", "args": {"query": "SELECT * FROM users"}}
        )

        # Mock user approving
        with patch("builtins.input", return_value="y"):
            result = hitl_handler.handle_interrupt(interrupt, session_state)

        # Should return resume command with approval
        assert result == {"resume": {"approve": True}}

        # Renderer should have been called to show panel
        hitl_handler.renderer.render_panel.assert_called_once()

    def test_handle_interrupt_rejected(self, hitl_handler, session_state):
        """Test full flow when user rejects"""
        interrupt = Interrupt(
            id="int_456", value={"tool": "dangerous_operation", "args": {"action": "delete_all"}}
        )

        # Mock user rejecting
        with patch("builtins.input", return_value="n"):
            result = hitl_handler.handle_interrupt(interrupt, session_state)

        # Should return resume command with rejection
        assert result == {"resume": {"approve": False}}

        # Renderer should have been called
        hitl_handler.renderer.render_panel.assert_called_once()

    def test_handle_interrupt_extracts_tool_info(self, hitl_handler, session_state):
        """Test interrupt handler extracts tool name and args correctly"""
        interrupt = Interrupt(id="int_789", value={"tool": "custom_tool", "args": {"key": "value"}})

        with patch("builtins.input", return_value="y"):
            hitl_handler.handle_interrupt(interrupt, session_state)

        # Verify panel was called with correct tool info
        call_args = hitl_handler.renderer.render_panel.call_args
        # Panel should contain formatted tool info
        assert call_args is not None


class TestToolRegistry:
    """Test tool registry integration"""

    def test_custom_formatter_used(self, mock_renderer):
        """Test custom formatter is used when registered"""
        # Create registry with custom formatter
        registry = ToolRenderRegistry()

        def custom_formatter(args: dict) -> str:
            return f"CUSTOM: {args.get('test', 'N/A')}"

        registry.register("my_custom_tool", custom_formatter)

        # Create handler with custom registry
        handler = HITLHandler(renderer=mock_renderer, tool_registry=registry)

        # Format should use custom formatter
        result = handler._format_tool_preview("my_custom_tool", {"test": "value123"})
        assert result == "CUSTOM: value123"

    def test_builtin_sql_formatter(self, hitl_handler):
        """Test builtin SQL formatter is registered"""
        result = hitl_handler._format_tool_preview(
            "sql_db_query", {"query": "SELECT COUNT(*) FROM orders"}
        )

        # Should use SQL formatter
        assert "SQL Query:" in result
        assert "SELECT COUNT(*) FROM orders" in result

    def test_fallback_for_unknown_tool(self, hitl_handler):
        """Test fallback formatter for unknown tools"""
        result = hitl_handler._format_tool_preview(
            "totally_unknown_tool", {"arg1": "test", "arg2": 123}
        )

        # Should use generic format
        assert "Tool: totally_unknown_tool" in result
        assert "arg1" in result or "test" in result
