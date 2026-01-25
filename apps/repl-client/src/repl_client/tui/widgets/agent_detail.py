"""Agent detail widgets for TUI sidebar and selection modals."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Label, Static


class AgentDetailItem(Static):
    """Single agent display widget showing name, ID, and creation date."""

    def __init__(self, agent: dict, is_current: bool = False) -> None:
        super().__init__()
        self.agent = agent
        self.is_current = is_current
        if is_current:
            self.add_class("current")

    def compose(self) -> ComposeResult:
        with Vertical():
            # Line 1: agent name + checkmark if current
            name = self.agent.get("graph_id", "unknown")
            if self.is_current:
                name = f"{name} ✓"
            yield Label(name, classes="agent-name")

            # Line 2: full assistant_id UUID
            assistant_id = self.agent.get("assistant_id", "")
            yield Label(assistant_id, classes="agent-id")

            # Line 3: creation date (first 10 chars)
            created_at = self.agent.get("created_at", "")
            date_str = created_at[:10] if created_at else "unknown"
            yield Label(f"Created: {date_str}", classes="agent-meta")


class AgentDetailList(VerticalScroll):
    """Scrollable container for agent detail items."""

    def __init__(self, agents: list[dict] | None = None, current_id: str = "") -> None:
        super().__init__()
        self._agents = agents if agents is not None else []
        self._current_id = current_id

    def on_mount(self) -> None:
        # Always populate - handles both empty and non-empty lists
        self.populate(self._agents, self._current_id)

    def populate(self, agents: list[dict], current_id: str) -> None:
        """Populate the list with agent items."""
        # Store for future reference
        self._agents = agents
        self._current_id = current_id

        # Remove existing children
        self.remove_children()

        if not agents:
            self.mount(Label("No agents available", classes="empty-message"))
            return

        for agent in agents:
            is_current = agent.get("assistant_id") == current_id
            self.mount(AgentDetailItem(agent, is_current=is_current))


class AgentSelector(Container):
    """Agent list with keyboard navigation and selection."""

    class AgentSelected(Message):
        """Message posted when an agent is selected."""

        def __init__(self, agent: dict) -> None:
            super().__init__()
            self._agent = agent

        @property
        def agent(self) -> dict:
            return self._agent

        @property
        def assistant_id(self) -> str:
            return self._agent.get("assistant_id", "")

    def __init__(self, agents: list[dict] | None = None, current_id: str = "") -> None:
        super().__init__()
        self._agents = agents or []
        self._current_id = current_id
        self._focus_index = 0

    def compose(self) -> ComposeResult:
        yield AgentDetailList(self._agents, self._current_id)

    def on_mount(self) -> None:
        """Update focus after children are mounted."""
        # Use call_after_refresh to ensure AgentDetailList has populated
        self.call_after_refresh(self._update_focus)

    def populate(self, agents: list[dict], current_id: str) -> None:
        """Populate the agent list and reset focus."""
        self._agents = agents
        self._current_id = current_id
        self._focus_index = 0

        agent_list = self.query_one(AgentDetailList)
        agent_list.populate(agents, current_id)
        self._update_focus()

    def on_key(self, event) -> None:
        """Handle keyboard navigation."""
        if event.key == "up":
            self._navigate(-1)
            event.stop()
        elif event.key == "down":
            self._navigate(1)
            event.stop()
        elif event.key == "enter":
            self._select_focused()
            event.stop()

    def _navigate(self, direction: int) -> None:
        """Move focus by direction (-1 for up, 1 for down)."""
        if not self._agents:
            return

        new_index = self._focus_index + direction
        if 0 <= new_index < len(self._agents):
            self._focus_index = new_index
            self._update_focus()

    def _update_focus(self) -> None:
        """Update the focused class on agent items."""
        items = self.query(AgentDetailItem)
        for i, item in enumerate(items):
            if i == self._focus_index:
                item.add_class("focused")
            else:
                item.remove_class("focused")

    def _select_focused(self) -> None:
        """Post AgentSelected message for the currently focused agent."""
        if self._agents and 0 <= self._focus_index < len(self._agents):
            agent = self._agents[self._focus_index]
            self.post_message(self.AgentSelected(agent))
