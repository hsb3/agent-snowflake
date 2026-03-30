"""Centralized state for TUI application.

Single source of truth for all app state. Mutations propagate to the UI
automatically via reactive properties on the App class.

Design:
- AppState is a plain Python class (grouping related state)
- Setter methods update both local fields AND the App's reactive properties
- The App defines watchers on its reactive properties that update widgets
- Controllers only need to call app_state methods; no dual writes needed
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual.app import App


class AppState:
    """Centralized state for TUI app.

    Like a webapp store (Redux/Vuex pattern).
    Controllers mutate state through methods, which push changes
    to the App's reactive properties. App watchers then update widgets.

    State is organized into categories:
    - Connection: Server connectivity and URL
    - Session: Current agent, thread, and data lists
    - UI: Visual state like streaming, sidebar visibility
    - Status: Status messages and error state
    - Metrics: Token usage

    Usage:
        # In app initialization
        self.app_state = AppState()
        self.app_state.bind(self)  # connects to App reactive props

        # In controllers - just mutate state (UI updates automatically)
        self.app_state.set_agent("uuid-123", "agent_name")
        self.app_state.set_status("Streaming...")
        self.app_state.streaming = True
    """

    def __init__(self):
        """Initialize app state with defaults."""
        self._app: App | None = None

        # Connection state
        self._connected: bool = False
        self._server_url: str = ""

        # Session state - current context
        self._current_agent_id: str = ""
        self._current_agent_name: str = ""
        self._current_thread_id: str = ""

        # Session state - data lists (cached from services)
        self.agents: list[dict] = []
        self.threads: list[dict] = []

        # UI state
        self._streaming: bool = False
        self.sidebar_visible: bool = False
        self.sidebar_expanded: bool = False

        # Status state
        self._status_message: str = ""
        self._status_error: bool = False

        # Metrics
        self._tokens: int = 0

    def bind(self, app: App) -> None:
        """Bind this state container to an App instance.

        After binding, setter methods will push changes to the App's
        reactive properties, which trigger watchers that update widgets.

        Args:
            app: The REPLApp instance
        """
        self._app = app

    def _set_reactive(self, name: str, value: object) -> None:
        """Set a reactive property on the bound App, if available.

        Args:
            name: Reactive property name on the App
            value: New value
        """
        if self._app is not None:
            setattr(self._app, name, value)

    # --- Properties that propagate to App reactive system ---

    @property
    def connected(self) -> bool:
        return self._connected

    @connected.setter
    def connected(self, value: bool) -> None:
        self._connected = value
        self._set_reactive("state_connected", value)

    @property
    def server_url(self) -> str:
        return self._server_url

    @server_url.setter
    def server_url(self, value: str) -> None:
        self._server_url = value
        self._set_reactive("state_server_url", value)

    @property
    def current_agent_id(self) -> str:
        return self._current_agent_id

    @current_agent_id.setter
    def current_agent_id(self, value: str) -> None:
        self._current_agent_id = value

    @property
    def current_agent_name(self) -> str:
        return self._current_agent_name

    @current_agent_name.setter
    def current_agent_name(self, value: str) -> None:
        self._current_agent_name = value
        self._set_reactive("state_agent_name", value)

    @property
    def current_thread_id(self) -> str:
        return self._current_thread_id

    @current_thread_id.setter
    def current_thread_id(self, value: str) -> None:
        self._current_thread_id = value
        self._set_reactive("state_thread_id", value)

    @property
    def streaming(self) -> bool:
        return self._streaming

    @streaming.setter
    def streaming(self, value: bool) -> None:
        self._streaming = value
        self._set_reactive("state_streaming", value)

    @property
    def status_message(self) -> str:
        return self._status_message

    @status_message.setter
    def status_message(self, value: str) -> None:
        self._status_message = value
        self._set_reactive("state_status_message", value)

    @property
    def status_error(self) -> bool:
        return self._status_error

    @status_error.setter
    def status_error(self, value: bool) -> None:
        self._status_error = value
        self._set_reactive("state_status_error", value)

    @property
    def tokens(self) -> int:
        return self._tokens

    @tokens.setter
    def tokens(self, value: int) -> None:
        self._tokens = value
        self._set_reactive("state_tokens", value)

    # --- Atomic update methods ---

    def reset_session(self) -> None:
        """Reset session-specific state (e.g., when switching threads)."""
        self.current_thread_id = ""
        self.tokens = 0

    def set_connection(self, connected: bool, url: str = "") -> None:
        """Update connection state atomically.

        Args:
            connected: Whether connected to server
            url: Server URL (optional)
        """
        self.connected = connected
        if url:
            self.server_url = url

    def set_agent(self, agent_id: str, agent_name: str = "") -> None:
        """Update current agent atomically.

        Args:
            agent_id: Agent UUID
            agent_name: Friendly agent name (optional)
        """
        self.current_agent_id = agent_id
        if agent_name:
            self.current_agent_name = agent_name

    def set_thread(self, thread_id: str) -> None:
        """Update current thread.

        Args:
            thread_id: Thread UUID
        """
        self.current_thread_id = thread_id

    def set_status(self, message: str, error: bool = False) -> None:
        """Update status message atomically.

        Args:
            message: Status message text
            error: Whether this is an error
        """
        self.status_message = message
        self.status_error = error

    def clear_status(self) -> None:
        """Clear status message."""
        self.status_message = ""
        self.status_error = False

    def update_agents_cache(self, agents: list[dict]) -> None:
        """Update cached agents list.

        Args:
            agents: List of agent dicts from API
        """
        self.agents = agents

    def update_threads_cache(self, threads: list[dict]) -> None:
        """Update cached threads list.

        Args:
            threads: List of thread dicts from API
        """
        self.threads = threads
