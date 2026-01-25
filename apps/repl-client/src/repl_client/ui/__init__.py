"""UI rendering components for classic REPL client.

NOTE: This module is used by classic REPL (__main__.py) only.
TUI uses Textual widgets instead (see tui/widgets/).
May be deprecated in future if TUI becomes primary interface.
"""

from repl_client.ui.content_blocks import ToolRenderRegistry
from repl_client.ui.renderer import Renderer

__all__ = [
    "Renderer",
    "ToolRenderRegistry",
]
