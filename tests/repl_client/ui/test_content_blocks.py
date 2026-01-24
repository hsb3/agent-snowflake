"""Tests for ui/content_blocks.py - Content Block Renderer + Tool Registry"""

import pytest
from io import StringIO
from dataclasses import dataclass
from rich.console import Console
from repl_client.ui.renderer import Renderer
from repl_client.ui.content_blocks import (
    ContentBlockRenderer,
    ToolRenderRegistry,
    ContentBlock,
    ToolCall,
)


# Mock data structures for testing
@dataclass
class MockContentBlock:
    """Mock ContentBlock for testing"""
    type: str
    index: int
    text: str | None = None
    tool_id: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None
    partial_json: str | None = None


@dataclass
class MockToolCall:
    """Mock ToolCall for testing"""
    id: str
    name: str
    args: dict
    type: str = "function"


class TestToolRenderRegistry:
    @pytest.fixture
    def registry(self):
        """Create fresh registry for each test"""
        return ToolRenderRegistry()

    def test_register_custom_formatter(self, registry):
        """Test registering a custom formatter"""
        def custom_formatter(args: dict) -> str:
            return f"Custom: {args}"

        registry.register("my_tool", custom_formatter)
        result = registry.format("my_tool", {"key": "value"})
        assert "Custom:" in result

    def test_format_with_registered_formatter(self, registry):
        """Test format uses registered formatter"""
        def sql_formatter(args: dict) -> str:
            return f"SQL: {args.get('query', '')}"

        registry.register("sql_db_query", sql_formatter)
        result = registry.format("sql_db_query", {"query": "SELECT * FROM users"})
        assert "SQL:" in result
        assert "SELECT * FROM users" in result

    def test_format_unknown_tool_fallback(self, registry):
        """Test fallback for unknown tools"""
        result = registry.format("unknown_tool", {"arg1": "value1"})
        # Should return some generic format
        assert "unknown_tool" in result or "arg1" in result

    def test_builtin_formatter_sql_db_query(self, registry):
        """Test builtin formatter for sql_db_query shows syntax highlighted SQL"""
        # Registry should have builtin for sql_db_query
        result = registry.format("sql_db_query", {"query": "SELECT id FROM users"})
        assert "SELECT" in result

    def test_format_empty_args(self, registry):
        """Test format handles empty args dict"""
        result = registry.format("some_tool", {})
        # Should not crash
        assert isinstance(result, str)

    def test_register_overwrites_existing(self, registry):
        """Test that registering same tool twice overwrites"""
        registry.register("tool1", lambda args: "First")
        registry.register("tool1", lambda args: "Second")
        result = registry.format("tool1", {})
        assert "Second" in result


class TestContentBlockRenderer:
    @pytest.fixture
    def content_renderer(self):
        """Create content block renderer with string buffer"""
        string_io = StringIO()
        console = Console(file=string_io, width=80, legacy_windows=False)
        renderer = Renderer(console=console)
        registry = ToolRenderRegistry()
        content_renderer = ContentBlockRenderer(renderer=renderer, registry=registry)
        return content_renderer, string_io

    def test_render_content_block_text_type(self, content_renderer):
        """Test render_content_block routes text blocks correctly"""
        cb_renderer, output = content_renderer
        block = MockContentBlock(type="text", index=0, text="Hello world")
        cb_renderer.render_content_block(block)
        result = output.getvalue()
        assert "Hello world" in result

    def test_render_content_block_tool_use_type(self, content_renderer):
        """Test render_content_block routes tool_use blocks correctly"""
        cb_renderer, output = content_renderer
        block = MockContentBlock(
            type="tool_use",
            index=0,
            tool_id="call_123",
            tool_name="sql_db_query",
            tool_input={"query": "SELECT * FROM users"}
        )
        cb_renderer.render_content_block(block)
        result = output.getvalue()
        # Should show tool name
        assert "sql_db_query" in result

    def test_render_content_block_tool_result_type(self, content_renderer):
        """Test render_content_block routes tool_result blocks correctly"""
        cb_renderer, output = content_renderer
        block = MockContentBlock(
            type="tool_result",
            index=0,
            tool_id="call_123",
            text="Query returned 10 rows"
        )
        cb_renderer.render_content_block(block)
        result = output.getvalue()
        assert "Query returned 10 rows" in result

    def test_render_tool_call_displays_name_and_args(self, content_renderer):
        """Test render_tool_call displays tool name and args"""
        cb_renderer, output = content_renderer
        tool_call = MockToolCall(
            id="call_456",
            name="get_weather",
            args={"city": "New York", "units": "celsius"}
        )
        cb_renderer.render_tool_call(tool_call)
        result = output.getvalue()
        assert "get_weather" in result

    def test_render_tool_call_with_sql_query(self, content_renderer):
        """Test render_tool_call with sql_db_query uses custom formatter"""
        cb_renderer, output = content_renderer
        tool_call = MockToolCall(
            id="call_789",
            name="sql_db_query",
            args={"query": "SELECT name FROM customers WHERE id = 1"}
        )
        cb_renderer.render_tool_call(tool_call)
        result = output.getvalue()
        assert "sql_db_query" in result
        assert "SELECT" in result

    def test_render_tool_preview_generic_fallback(self, content_renderer):
        """Test render_tool_preview falls back for unknown tools"""
        cb_renderer, output = content_renderer
        preview = cb_renderer.render_tool_preview("unknown_tool", {"param": "value"})
        assert isinstance(preview, str)
        assert "unknown_tool" in preview or "param" in preview

    def test_render_tool_preview_sql_db_query_formatted(self, content_renderer):
        """Test render_tool_preview formats SQL nicely"""
        cb_renderer, output = content_renderer
        preview = cb_renderer.render_tool_preview(
            "sql_db_query",
            {"query": "SELECT id, name FROM users WHERE active = true"}
        )
        assert "SELECT" in preview

    def test_content_block_renderer_with_custom_registry(self):
        """Test ContentBlockRenderer works with custom registry"""
        string_io = StringIO()
        console = Console(file=string_io, width=80, legacy_windows=False)
        renderer = Renderer(console=console)

        # Create custom registry with special formatter
        registry = ToolRenderRegistry()
        registry.register("custom_tool", lambda args: f"CUSTOM: {args.get('data')}")

        cb_renderer = ContentBlockRenderer(renderer=renderer, registry=registry)
        preview = cb_renderer.render_tool_preview("custom_tool", {"data": "test"})
        assert "CUSTOM:" in preview
        assert "test" in preview

    def test_render_content_block_unknown_type(self, content_renderer):
        """Test render_content_block handles unknown block types gracefully"""
        cb_renderer, output = content_renderer
        block = MockContentBlock(type="unknown_type", index=0)
        # Should not crash
        cb_renderer.render_content_block(block)
