"""Centralized state for TUI application.

Single source of truth for all app state. Simple Python class without
Textual reactive magic - controllers mutate state, app coordinates view updates.
"""


class AppState:
    """Centralized state for TUI app.

    Like a webapp store (Redux/Vuex pattern).
    Controllers mutate state, app coordinates view updates.

    State is organized into categories:
    - Connection: Server connectivity and URL
    - Session: Current agent, thread, and data lists
    - UI: Visual state like streaming, sidebar visibility
    - Status: Status messages and error state
    - Metrics: Token usage

    Design:
    - Plain Python class (no Textual reactivity to avoid complexity)
    - Controllers update state through methods
    - App watches state and updates views
    - Single source of truth for debugging

    Usage:
        # In app initialization
        self.state = AppState()

        # In controllers - mutate state
        self.state.set_agent("uuid-123", "agent_name")
        self.state.streaming = True

        # In app - read state and update views
        if self.state.streaming:
            self.disable_input()
    """

    def __init__(self):
        """Initialize app state with defaults."""
        # Connection state
        self.connected: bool = False
        self.server_url: str = ""

        # Session state - current context
        self.current_agent_id: str = ""
        self.current_agent_name: str = ""
        self.current_thread_id: str = ""

        # Session state - data lists (cached from services)
        self.agents: list[dict] = []
        self.threads: list[dict] = []

        # UI state
        self.streaming: bool = False
        self.sidebar_visible: bool = False
        self.sidebar_expanded: bool = False

        # Status state
        self.status_message: str = ""
        self.status_error: bool = False

        # Metrics
        self.tokens: int = 0

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
