"""Models - Reactive state management for TUI.

Single source of truth using Textual's reactive system.
Like a webapp store (Redux/Vuex pattern).
"""

from repl_client.tui.models.app_state import AppState

__all__ = ["AppState"]
