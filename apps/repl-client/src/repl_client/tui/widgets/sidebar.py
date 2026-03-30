"""Sidebar widget with tabs for context, threads, agents, and tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Container, VerticalScroll
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Label, Static, TabbedContent, TabPane

if TYPE_CHECKING:
    from textual.app import ComposeResult


class Sidebar(Container):
    """Sidebar with tabs for Threads, Agents, Session, and Tools.

    Features:
    - Toggleable visibility (hidden by default)
    - Two modes: normal (40% width) and expanded (60% width)
    - Tabs: Threads, Agents, Session, Tools
    - Keyboard navigation: Tab to switch tabs, arrows for lists, Enter to select

    Messages:
    - AgentSelected: Emitted when an agent is selected
    - ThreadSelected: Emitted when a thread is selected
    - NewThreadRequested: Emitted when "+ New Thread" is selected
    """

    class AgentSelected(Message):
        """Message emitted when an agent is selected."""

        def __init__(self, agent_id: str) -> None:
            super().__init__()
            self.agent_id = agent_id

    class ThreadSelected(Message):
        """Message emitted when a thread is selected."""

        def __init__(self, thread_id: str) -> None:
            super().__init__()
            self.thread_id = thread_id

    class NewThreadRequested(Message):
        """Message emitted when new thread is requested."""

    DEFAULT_CSS = """
    Sidebar {
        width: 0;
        height: 1fr;
        background: $surface;
        border-left: solid $primary;
        display: none;
    }

    Sidebar.visible {
        width: 40%;
        display: block;
    }

    Sidebar.expanded {
        width: 60%;
        display: block;
    }

    Sidebar TabbedContent {
        height: 1fr;
        width: 100%;
    }

    Sidebar TabbedContent:focus-within {
        border: tall $primary;
    }

    Sidebar TabPane {
        padding: 1;
    }

    Sidebar .thread-item {
        padding: 0 1;
        margin: 0 0 1 0;
        background: $surface;
        height: auto;
    }

    Sidebar .thread-item:hover {
        background: $surface;
    }

    Sidebar .thread-item.current {
        background: $primary;
    }

    Sidebar .thread-item.focused {
        background: $surface;
        border-left: thick $primary;
    }

    Sidebar .agent-item {
        padding: 0 1;
        margin: 0 0 1 0;
        background: $surface;
        height: auto;
    }

    Sidebar .agent-item:hover {
        background: $surface;
    }

    Sidebar .agent-item.current {
        background: $primary;
    }

    Sidebar .agent-item.focused {
        background: $surface;
        border-left: thick $primary;
    }

    Sidebar .session-info {
        padding: 1;
        background: $surface;
        margin: 0 0 1 0;
        height: auto;
    }

    Sidebar .tool-call-item {
        padding: 0 1;
        margin: 0 0 1 0;
        background: $surface;
        height: auto;
    }

    Sidebar .tool-call-item:hover {
        background: $surface;
    }

    Sidebar .section-header {
        color: $primary;
        text-style: bold;
        padding: 1 0;
    }

    Sidebar .empty-message {
        color: $text-muted;
        text-style: italic;
        padding: 1;
    }
    """

    visible: reactive[bool] = reactive(False, init=False)
    expanded: reactive[bool] = reactive(False, init=False)

    def __init__(self, **kwargs) -> None:
        """Initialize sidebar."""
        super().__init__(**kwargs)
        self._focused_thread_index: int = 0
        self._focused_agent_index: int = 0
        self._threads_data: list[dict] = []
        self._agents_data: list[dict] = []
        self.can_focus = True

    def compose(self) -> ComposeResult:
        """Compose the sidebar layout."""
        with TabbedContent(id="sidebar-tabs"):
            with TabPane("Threads", id="threads-tab"):
                yield VerticalScroll(id="threads-list")
            with TabPane("Agents", id="agents-tab"):
                yield VerticalScroll(id="agents-list")
            with TabPane("Session", id="session-tab"):
                yield VerticalScroll(id="session-info")
            with TabPane("Tools", id="tools-tab"):
                yield VerticalScroll(id="tools-list")

    def watch_visible(self, new_value: bool) -> None:  # noqa: FBT001
        """Update visibility when state changes."""
        self.remove_class("visible", "expanded")

        if new_value:
            if self.expanded:
                self.add_class("expanded")
            else:
                self.add_class("visible")

    def watch_expanded(self, new_value: bool) -> None:  # noqa: FBT001
        """Update expanded state when it changes."""
        self.remove_class("visible", "expanded")

        if self.visible:
            if new_value:
                self.add_class("expanded")
            else:
                self.add_class("visible")

    def toggle(self) -> None:
        """Toggle sidebar visibility."""
        self.visible = not self.visible

    def expand(self) -> None:
        """Toggle expanded mode."""
        if not self.visible:
            self.visible = True
            self.expanded = True
        else:
            self.expanded = not self.expanded

    def collapse(self) -> None:
        """Collapse to normal width or hide."""
        if self.expanded:
            self.expanded = False
        else:
            self.visible = False

    # Keyboard navigation methods

    # Tab IDs in order for left/right cycling
    _TAB_ORDER = ("threads-tab", "agents-tab", "session-tab", "tools-tab")

    def on_key(self, event) -> None:
        """Handle keyboard navigation.

        Keys:
        - Left/Right or [/]: Cycle between tabs
        - Up/Down: Navigate items within a tab
        - Enter: Select focused item
        - Escape: Close sidebar and return focus to input
        """
        if not self.visible:
            return

        # Get active tab
        tabbed = self.query_one(TabbedContent)
        active_tab_id = tabbed.active

        # Tab cycling with left/right arrows or [ / ]
        if event.key in ("left", "right", "open_bracket", "close_bracket"):
            current_idx = (
                self._TAB_ORDER.index(active_tab_id)
                if active_tab_id in self._TAB_ORDER
                else 0
            )
            if event.key in ("right", "close_bracket"):
                next_idx = (current_idx + 1) % len(self._TAB_ORDER)
            else:
                next_idx = (current_idx - 1) % len(self._TAB_ORDER)
            tabbed.active = self._TAB_ORDER[next_idx]
            event.prevent_default()
            event.stop()
            return

        # Close sidebar with Escape
        if event.key == "escape":
            self.toggle()
            event.prevent_default()
            event.stop()
            # Return focus to input via action dispatch
            self.app.run_action("focus_input")
            return

        if event.key == "up":
            if active_tab_id == "threads-tab":
                self._navigate_threads(-1)
                event.prevent_default()
            elif active_tab_id == "agents-tab":
                self._navigate_agents(-1)
                event.prevent_default()
        elif event.key == "down":
            if active_tab_id == "threads-tab":
                self._navigate_threads(1)
                event.prevent_default()
            elif active_tab_id == "agents-tab":
                self._navigate_agents(1)
                event.prevent_default()
        elif event.key == "enter":
            if active_tab_id == "threads-tab":
                self._select_focused_thread()
                event.prevent_default()
            elif active_tab_id == "agents-tab":
                self._select_focused_agent()
                event.prevent_default()

    def _navigate_threads(self, direction: int) -> None:
        """Navigate thread list up or down."""
        if not self._threads_data:
            return

        # Clear old focus
        container = self.query_one("#threads-list", VerticalScroll)
        children = list(container.children)
        if 0 <= self._focused_thread_index < len(children):
            children[self._focused_thread_index].remove_class("focused")

        # Update index (including "+ New Thread" button at index 0)
        max_index = len(children) - 1
        self._focused_thread_index = max(0, min(max_index, self._focused_thread_index + direction))

        # Add new focus
        if 0 <= self._focused_thread_index < len(children):
            children[self._focused_thread_index].add_class("focused")
            children[self._focused_thread_index].scroll_visible()

    def _navigate_agents(self, direction: int) -> None:
        """Navigate agent list up or down."""
        if not self._agents_data:
            return

        # Clear old focus
        container = self.query_one("#agents-list", VerticalScroll)
        children = list(container.children)
        if 0 <= self._focused_agent_index < len(children):
            children[self._focused_agent_index].remove_class("focused")

        # Update index
        max_index = len(children) - 1
        self._focused_agent_index = max(0, min(max_index, self._focused_agent_index + direction))

        # Add new focus
        if 0 <= self._focused_agent_index < len(children):
            children[self._focused_agent_index].add_class("focused")
            children[self._focused_agent_index].scroll_visible()

    def _select_focused_thread(self) -> None:
        """Select the currently focused thread."""
        if not self._threads_data:
            return

        # Index 0 is "+ New Thread", rest are threads
        if self._focused_thread_index == 0:
            self.post_message(self.NewThreadRequested())
        elif 0 < self._focused_thread_index <= len(self._threads_data):
            thread = self._threads_data[self._focused_thread_index - 1]
            thread_id = thread.get("thread_id", "")
            if thread_id:
                self.post_message(self.ThreadSelected(thread_id))

    def _select_focused_agent(self) -> None:
        """Select the currently focused agent."""
        if not self._agents_data:
            return

        if 0 <= self._focused_agent_index < len(self._agents_data):
            agent = self._agents_data[self._focused_agent_index]
            agent_id = agent.get("assistant_id", "")
            if agent_id:
                self.post_message(self.AgentSelected(agent_id))

    # Content population methods

    def populate_threads(self, threads: list[dict], current_thread_id: str) -> None:
        """Populate the threads tab with thread list.

        Args:
            threads: List of thread dicts with thread_id and created_at
            current_thread_id: ID of current thread
        """
        self._threads_data = threads
        self._focused_thread_index = 0

        container = self.query_one("#threads-list", VerticalScroll)
        container.remove_children()

        if not threads:
            container.mount(Label("No threads available", classes="empty-message"))
            return

        # Add "+ New Thread" button
        new_thread_btn = Static("+ New Thread", classes="thread-item focused")
        container.mount(new_thread_btn)

        # Add threads
        for thread in threads:
            thread_id = thread.get("thread_id", "")
            created = thread.get("created_at", "")
            is_current = thread_id == current_thread_id

            # Format display
            display = f"{thread_id[:16]}...\n{created[:10]}"
            if is_current:
                display += " ✓"

            thread_item = Static(display, classes="thread-item")
            if is_current:
                thread_item.add_class("current")

            container.mount(thread_item)

    def populate_agents(self, agents: list[dict], current_agent_id: str) -> None:
        """Populate the agents tab with agent list.

        Args:
            agents: List of agent dicts with assistant_id and graph_id
            current_agent_id: ID of current agent
        """
        self._agents_data = agents
        self._focused_agent_index = 0

        container = self.query_one("#agents-list", VerticalScroll)
        container.remove_children()

        if not agents:
            container.mount(Label("No agents available", classes="empty-message"))
            return

        for i, agent in enumerate(agents):
            agent_id = agent.get("assistant_id", "")
            graph_id = agent.get("graph_id", "")
            is_current = agent_id == current_agent_id

            # Format display
            display = f"{graph_id}\n{agent_id[:16]}..."
            if is_current:
                display += " ✓"

            agent_item = Static(display, classes="agent-item")
            if is_current:
                agent_item.add_class("current")
            if i == 0:
                agent_item.add_class("focused")

            container.mount(agent_item)

    def populate_session_info(
        self,
        thread_id: str,
        agent_id: str,
        tokens: dict[str, int],
        model: str | None = None,
    ) -> None:
        """Populate the session tab with session info.

        Args:
            thread_id: Current thread ID
            agent_id: Current agent ID
            tokens: Token counts dict with 'total', 'input', 'output'
            model: Model name (optional)
        """
        container = self.query_one("#session-info", VerticalScroll)
        container.remove_children()

        # Build info display
        info_text = f"""Thread ID:
{thread_id}

Agent ID:
{agent_id}

Tokens:
  Total: {tokens.get("total", 0):,}
  Input: {tokens.get("input", 0):,}
  Output: {tokens.get("output", 0):,}"""

        if model:
            info_text += f"\n\nModel:\n{model}"

        info_widget = Static(info_text, classes="session-info")
        container.mount(info_widget)

    def populate_tools(self, tool_calls: list[dict]) -> None:
        """Populate the tools tab with recent tool calls.

        Args:
            tool_calls: List of tool call dicts with name, args, result
        """
        container = self.query_one("#tools-list", VerticalScroll)
        container.remove_children()

        if not tool_calls:
            container.mount(Label("No tool calls yet", classes="empty-message"))
            return

        for tool_call in tool_calls:
            name = tool_call.get("name", "unknown")
            args = tool_call.get("args", {})
            status = tool_call.get("status", "pending")

            # Format display
            status_symbol = {
                "success": "✓",
                "error": "✗",
                "pending": "⋯",
            }.get(status, "?")

            display = f"{status_symbol} {name}\n"

            # Show first arg if available
            if args:
                first_key = list(args.keys())[0]
                first_val = str(args[first_key])[:40]
                display += f"  {first_key}: {first_val}..."

            tool_item = Static(display, classes="tool-call-item")
            container.mount(tool_item)
