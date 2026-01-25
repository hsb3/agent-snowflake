"""Sidebar view - tabbed sidebar with threads/agents/session/tools.

Wraps Sidebar widget and provides methods for populating content.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from repl_client.tui.widgets import Sidebar

if TYPE_CHECKING:
    pass


class SidebarView(Sidebar):
    """View wrapper for Sidebar widget.

    Provides methods for updating sidebar content.
    The widget handles rendering, this view adds semantic methods.

    Features:
    - Toggle visibility
    - Expand/collapse width
    - Update threads list
    - Update agents list
    - Update session info
    - Update tools list
    """

    def show(self) -> None:
        """Show the sidebar."""
        if not self.visible:
            self.toggle()

    def hide(self) -> None:
        """Hide the sidebar."""
        if self.visible:
            self.toggle()

    def toggle_visibility(self) -> None:
        """Toggle sidebar visibility."""
        self.toggle()

    def toggle_expanded(self) -> None:
        """Toggle expanded mode."""
        self.expand()

    def update_threads(self, threads: list[dict], current_thread_id: str) -> None:
        """Update the threads tab content.

        Args:
            threads: List of thread dicts with thread_id and created_at
            current_thread_id: ID of current thread
        """
        self.populate_threads(threads, current_thread_id)

    def update_agents(self, agents: list[dict], current_agent_id: str) -> None:
        """Update the agents tab content.

        Args:
            agents: List of agent dicts with assistant_id and graph_id
            current_agent_id: ID of current agent
        """
        self.populate_agents(agents, current_agent_id)

    def update_session_info(
        self,
        thread_id: str,
        agent_id: str,
        tokens: dict[str, int],
        model: str | None = None,
    ) -> None:
        """Update the session info tab content.

        Args:
            thread_id: Current thread ID
            agent_id: Current agent ID
            tokens: Token counts dict with 'total', 'input', 'output'
            model: Model name (optional)
        """
        self.populate_session_info(thread_id, agent_id, tokens, model)

    def update_tools(self, tool_calls: list[dict]) -> None:
        """Update the tools tab content.

        Args:
            tool_calls: List of tool call dicts with name, args, result, status
        """
        self.populate_tools(tool_calls)

    def refresh_all(
        self,
        threads: list[dict],
        agents: list[dict],
        current_thread_id: str,
        current_agent_id: str,
        tokens: dict[str, int],
        tool_calls: list[dict] | None = None,
    ) -> None:
        """Refresh all sidebar tabs at once.

        Args:
            threads: List of thread dicts
            agents: List of agent dicts
            current_thread_id: Current thread ID
            current_agent_id: Current agent ID
            tokens: Token counts
            tool_calls: Optional list of tool calls
        """
        self.update_threads(threads, current_thread_id)
        self.update_agents(agents, current_agent_id)
        self.update_session_info(current_thread_id, current_agent_id, tokens)
        if tool_calls:
            self.update_tools(tool_calls)
