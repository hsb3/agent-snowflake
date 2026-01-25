"""Tests for ui/content_blocks.py - ToolRenderRegistry only.

NOTE: ContentBlockRenderer was removed (dead code). Only ToolRenderRegistry remains.
"""

import pytest

from repl_client.ui.content_blocks import ToolRenderRegistry


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


# NOTE: TestContentBlockRenderer removed - ContentBlockRenderer class was deleted (dead code).
# ToolRenderRegistry tests remain above - that's the only production code in content_blocks.py
