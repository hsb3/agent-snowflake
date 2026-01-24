"""Base rendering primitives using Rich"""

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table


class Renderer:
    """Base renderer for terminal output using Rich"""

    def __init__(self, console: Console | None = None):
        """Initialize with Rich Console

        Args:
            console: Rich Console instance. If None, creates a default console.
        """
        self.console = console or Console()

    def render_text(self, text: str, style: str = "cyan") -> None:
        """Print text with color

        Args:
            text: Text to render
            style: Rich style string (color name or style)
        """
        self.console.print(text, style=style)

    def render_markdown(self, text: str) -> None:
        """Render markdown using Rich Markdown

        Args:
            text: Markdown text to render
        """
        md = Markdown(text)
        self.console.print(md)

    def render_code(self, code: str, language: str) -> None:
        """Syntax highlighted code block

        Args:
            code: Source code to render
            language: Language name for syntax highlighting (python, sql, javascript, etc.)
        """
        syntax = Syntax(code, language, theme="monokai", line_numbers=False)
        self.console.print(syntax)

    def render_panel(self, content: str, title: str, style: str = "blue") -> None:
        """Render Rich Panel with border

        Args:
            content: Panel content
            title: Panel title
            style: Border style/color
        """
        panel = Panel(content, title=title, border_style=style)
        self.console.print(panel)

    def render_table(self, headers: list[str], rows: list[list]) -> None:
        """Render Rich Table

        Args:
            headers: Column headers
            rows: List of rows, each row is a list of values
        """
        table = Table()

        # Add columns
        for header in headers:
            table.add_column(header)

        # Add rows
        for row in rows:
            # Convert all values to strings
            table.add_row(*[str(val) for val in row])

        self.console.print(table)

    def render_error(self, message: str) -> None:
        """Red error message

        Args:
            message: Error message to display
        """
        self.console.print(f"Error: {message}", style="bold red")

    def render_success(self, message: str) -> None:
        """Green success message

        Args:
            message: Success message to display
        """
        self.console.print(message, style="bold green")

    def clear(self) -> None:
        """Clear terminal screen"""
        self.console.clear()

    def flush(self) -> None:
        """Flush console output to ensure it's displayed before blocking input."""
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
