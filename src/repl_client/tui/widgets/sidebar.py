"""Sidebar widget with tabs for context, threads, agents, and tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual.containers import Container, Vertical, VerticalScroll
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
    """

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

    Sidebar TabPane {
        padding: 1;
    }

    Sidebar .thread-item {
        padding: 0 1;
        margin: 0 0 1 0;
        background: $surface-darken-1;
        height: auto;
    }

    Sidebar .thread-item:hover {
        background: $surface-lighten-1;
    }

    Sidebar .thread-item.current {
        background: $primary-darken-1;
    }

    Sidebar .agent-item {
        padding: 0 1;
        margin: 0 0 1 0;
        background: $surface-darken-1;
        height: auto;
    }

    Sidebar .agent-item:hover {
        background: $surface-lighten-1;
    }

    Sidebar .agent-item.current {
        background: $primary-darken-1;
    }

    Sidebar .session-info {
        padding: 1;
        background: $surface-darken-1;
        margin: 0 0 1 0;
        height: auto;
    }

    Sidebar .tool-call-item {
        padding: 0 1;
        margin: 0 0 1 0;
        background: $surface-darken-1;
        height: auto;
    }

    Sidebar .tool-call-item:hover {
        background: $surface-lighten-1;
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

    # Content population methods

    def populate_threads(self, threads: list[dict], current_thread_id: str) -> None:
        """Populate the threads tab with thread list.

        Args:
            threads: List of thread dicts with thread_id and created_at
            current_thread_id: ID of current thread
        """
        container = self.query_one("#threads-list", VerticalScroll)
        container.remove_children()

        if not threads:
            container.mount(Label("No threads available", classes="empty-message"))
            return

        # Add "+ New Thread" button
        new_thread_btn = Static("+ New Thread", classes="thread-item")
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
        container = self.query_one("#agents-list", VerticalScroll)
        container.remove_children()

        if not agents:
            container.mount(Label("No agents available", classes="empty-message"))
            return

        for agent in agents:
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
  Total: {tokens.get('total', 0):,}
  Input: {tokens.get('input', 0):,}
  Output: {tokens.get('output', 0):,}"""

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

        for i, tool_call in enumerate(tool_calls):
            name = tool_call.get("name", "unknown")
            args = tool_call.get("args", {})
            result = tool_call.get("result", "")
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
