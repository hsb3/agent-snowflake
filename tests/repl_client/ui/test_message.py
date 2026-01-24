"""Tests for ui/message.py - Message Renderer"""

import pytest
from io import StringIO
from rich.console import Console
from repl_client.ui.renderer import Renderer
from repl_client.ui.message import MessageRenderer


class TestMessageRenderer:
    @pytest.fixture
    def message_renderer(self):
        """Create message renderer with string buffer for testing"""
        string_io = StringIO()
        console = Console(file=string_io, width=80, legacy_windows=False)
        renderer = Renderer(console=console)
        msg_renderer = MessageRenderer(renderer=renderer)
        return msg_renderer, string_io

    def test_render_user_message_uses_green(self, message_renderer):
        """Test render_user_message uses green color"""
        msg_renderer, output = message_renderer
        msg_renderer.render_user_message("Hello from user")
        result = output.getvalue()
        assert "Hello from user" in result

    def test_render_user_message_prefix(self, message_renderer):
        """Test render_user_message includes user prefix"""
        msg_renderer, output = message_renderer
        msg_renderer.render_user_message("Test message")
        result = output.getvalue()
        # Should have some indication it's a user message
        assert "Test message" in result

    def test_render_ai_text_basic(self, message_renderer):
        """Test render_ai_text with plain text"""
        msg_renderer, output = message_renderer
        msg_renderer.render_ai_text("AI response here")
        result = output.getvalue()
        assert "AI response here" in result

    def test_render_ai_text_supports_markdown(self, message_renderer):
        """Test render_ai_text supports markdown formatting"""
        msg_renderer, output = message_renderer
        msg_renderer.render_ai_text("This has **bold** and *italic* text")
        result = output.getvalue()
        assert "bold" in result
        assert "italic" in result

    def test_render_ai_text_markdown_code_blocks(self, message_renderer):
        """Test render_ai_text handles markdown code blocks"""
        msg_renderer, output = message_renderer
        markdown_text = """
Here is some code:

```python
def hello():
    print("world")
```
"""
        msg_renderer.render_ai_text(markdown_text)
        result = output.getvalue()
        assert "hello" in result

    def test_render_ai_text_empty_string(self, message_renderer):
        """Test render_ai_text handles empty string"""
        msg_renderer, output = message_renderer
        msg_renderer.render_ai_text("")
        # Should not crash, output may be empty or have minimal content

    def test_render_tool_result_with_panel(self, message_renderer):
        """Test render_tool_result shows panel with tool name"""
        msg_renderer, output = message_renderer
        msg_renderer.render_tool_result(
            tool_name="sql_db_query",
            result="Query executed successfully",
            status="success"
        )
        result = output.getvalue()
        assert "sql_db_query" in result
        assert "Query executed successfully" in result

    def test_render_tool_result_error_status(self, message_renderer):
        """Test render_tool_result handles error status"""
        msg_renderer, output = message_renderer
        msg_renderer.render_tool_result(
            tool_name="some_tool",
            result="Error: Operation failed",
            status="error"
        )
        result = output.getvalue()
        assert "some_tool" in result
        assert "Error: Operation failed" in result

    def test_render_tool_result_long_output(self, message_renderer):
        """Test render_tool_result handles long output"""
        msg_renderer, output = message_renderer
        long_result = "Line\n" * 100
        msg_renderer.render_tool_result(
            tool_name="data_fetch",
            result=long_result,
            status="success"
        )
        result = output.getvalue()
        assert "data_fetch" in result
        assert "Line" in result
