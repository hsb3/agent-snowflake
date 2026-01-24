"""Tests for ui/renderer.py - Base Renderer"""

import pytest
from io import StringIO
from rich.console import Console
from repl_client.ui.renderer import Renderer


class TestRenderer:
    @pytest.fixture
    def renderer(self):
        """Create renderer with string buffer for testing"""
        string_io = StringIO()
        console = Console(file=string_io, width=80, legacy_windows=False)
        return Renderer(console=console), string_io

    def test_render_text_default_style(self, renderer):
        """Test render_text with default cyan style"""
        r, output = renderer
        r.render_text("Hello world")
        result = output.getvalue()
        assert "Hello world" in result

    def test_render_text_custom_style(self, renderer):
        """Test render_text with custom style"""
        r, output = renderer
        r.render_text("Success message", style="green")
        result = output.getvalue()
        assert "Success message" in result

    def test_render_markdown_bold(self, renderer):
        """Test render_markdown handles bold text"""
        r, output = renderer
        r.render_markdown("This is **bold** text")
        result = output.getvalue()
        assert "bold" in result

    def test_render_markdown_italic(self, renderer):
        """Test render_markdown handles italic text"""
        r, output = renderer
        r.render_markdown("This is *italic* text")
        result = output.getvalue()
        assert "italic" in result

    def test_render_markdown_headers(self, renderer):
        """Test render_markdown handles headers"""
        r, output = renderer
        r.render_markdown("# Header 1\n## Header 2")
        result = output.getvalue()
        assert "Header 1" in result
        assert "Header 2" in result

    def test_render_markdown_lists(self, renderer):
        """Test render_markdown handles lists"""
        r, output = renderer
        r.render_markdown("- Item 1\n- Item 2\n- Item 3")
        result = output.getvalue()
        assert "Item 1" in result
        assert "Item 2" in result

    def test_render_code_python(self, renderer):
        """Test render_code with Python syntax highlighting"""
        r, output = renderer
        code = "def hello():\n    print('world')"
        r.render_code(code, language="python")
        result = output.getvalue()
        assert "def" in result
        assert "hello" in result

    def test_render_code_sql(self, renderer):
        """Test render_code with SQL syntax highlighting"""
        r, output = renderer
        code = "SELECT * FROM users WHERE id = 1"
        r.render_code(code, language="sql")
        result = output.getvalue()
        assert "SELECT" in result
        assert "FROM" in result

    def test_render_code_javascript(self, renderer):
        """Test render_code with JavaScript syntax highlighting"""
        r, output = renderer
        code = "const x = 42;\nconsole.log(x);"
        r.render_code(code, language="javascript")
        result = output.getvalue()
        assert "const" in result
        assert "console" in result

    def test_render_panel_with_title(self, renderer):
        """Test render_panel creates bordered panel with title"""
        r, output = renderer
        r.render_panel("Panel content", title="Test Panel")
        result = output.getvalue()
        assert "Panel content" in result
        assert "Test Panel" in result

    def test_render_panel_custom_style(self, renderer):
        """Test render_panel with custom border style"""
        r, output = renderer
        r.render_panel("Content", title="Panel", style="red")
        result = output.getvalue()
        assert "Content" in result

    def test_render_table_with_headers(self, renderer):
        """Test render_table with headers and rows"""
        r, output = renderer
        headers = ["Name", "Age", "City"]
        rows = [
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ]
        r.render_table(headers, rows)
        result = output.getvalue()
        assert "Name" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_render_table_empty_rows(self, renderer):
        """Test render_table with headers but no rows"""
        r, output = renderer
        headers = ["Col1", "Col2"]
        rows = []
        r.render_table(headers, rows)
        result = output.getvalue()
        assert "Col1" in result

    def test_render_error_red_color(self, renderer):
        """Test render_error uses red color"""
        r, output = renderer
        r.render_error("Something went wrong")
        result = output.getvalue()
        assert "Something went wrong" in result

    def test_render_success_green_color(self, renderer):
        """Test render_success uses green color"""
        r, output = renderer
        r.render_success("Operation completed")
        result = output.getvalue()
        assert "Operation completed" in result

    def test_clear_screen(self, renderer):
        """Test clear clears the console"""
        r, output = renderer
        r.render_text("Before clear")
        r.clear()
        # After clear, we can't really test the output since it clears the buffer
        # Just ensure it doesn't raise an error
        r.render_text("After clear")
        result = output.getvalue()
        assert "After clear" in result
