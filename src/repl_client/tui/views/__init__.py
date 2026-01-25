"""TUI presentational views for REPL client.

Views are responsible for:
- Composing widgets into layouts
- Managing widget mounting/unmounting
- Coordinating visual arrangement

Views do NOT contain:
- Business logic
- API calls
- State management
"""

from .layout_view import LayoutView
from .message_area_view import MessageAreaView
from .sidebar_view import SidebarView
from .status_area_view import StatusAreaView

__all__ = [
    "LayoutView",
    "MessageAreaView",
    "SidebarView",
    "StatusAreaView",
]
