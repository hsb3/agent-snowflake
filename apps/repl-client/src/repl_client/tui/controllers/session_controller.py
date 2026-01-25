"""Session controller for handling agent and thread switching.

Coordinates session state changes with server API calls.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from repl_client.core.logging import get_logger

if TYPE_CHECKING:
    from repl_client.core.session import SessionState
    from repl_client.tui.models import AppState
    from repl_client.tui.services import LangGraphService

logger = get_logger("tui.controllers.session")


class SessionController:
    """Handle agent and thread switching.

    Responsibilities:
    - Switch agents with name resolution
    - Switch threads
    - Create new threads
    - Update session state
    - Coordinate with LangGraphService

    Design:
    - Encapsulates agent/thread switching logic
    - Separates name resolution from UI
    - Returns rich results for UI display
    """

    def __init__(
        self,
        langgraph_service: LangGraphService,
        session: SessionState,
        app_state: AppState | None = None,
    ):
        """Initialize session controller.

        Args:
            langgraph_service: Service for LangGraph API calls
            session: Session state tracker (legacy, kept for compatibility)
            app_state: Reactive app state (new, preferred)
        """
        self.langgraph = langgraph_service
        self.session = session
        self.app_state = app_state

    async def switch_agent(self, agent_identifier: str) -> dict:
        """Switch to different agent.

        Resolves agent name/ID and updates session state.

        Args:
            agent_identifier: Agent name, graph_id, or assistant_id

        Returns:
            Dict with 'success' (bool), 'message' (str), 'agent_id' (str if success)

        Example:
            result = await controller.switch_agent("agent_enhanced")
            if result["success"]:
                print(f"Switched to {result['agent_id']}")
            else:
                print(f"Error: {result['message']}")
        """
        try:
            # Resolve name to UUID via service (uses cache)
            agent_id = await self.langgraph.resolve_agent_name(agent_identifier)

            if not agent_id:
                return {
                    "success": False,
                    "message": f"Agent not found: {agent_identifier}",
                }

            # Get agents list (uses cache)
            agents = await self.langgraph.get_agents()
            agent = next((a for a in agents if a.get("assistant_id") == agent_id), None)

            # Extract display name
            if agent:
                display_name = agent.get("graph_id") or agent.get("name") or agent_id[:8]
            else:
                display_name = agent_id[:8]

            # Update session state (both legacy and new)
            old_agent = self.session.current_assistant_id
            self.session.set_agent(agent_id)
            if self.app_state:
                self.app_state.set_agent(agent_id, display_name)
                # Ensure app_state has latest agents
                self.app_state.update_agents_cache(agents)

            logger.info(f"Switched agent: {old_agent} → {agent_id}")

            return {
                "success": True,
                "message": f"Switched to agent: {display_name}",
                "agent_id": agent_id,
                "display_name": display_name,
            }

        except Exception as e:
            logger.exception(f"Failed to switch agent: {agent_identifier}")
            return {
                "success": False,
                "message": f"Failed to switch agent: {e}",
            }

    async def switch_thread(self, thread_id: str) -> dict:
        """Switch to different thread.

        Args:
            thread_id: Thread ID to switch to

        Returns:
            Dict with 'success' (bool), 'message' (str), 'thread_id' (str if success)
        """
        try:
            # Force refresh to ensure we have latest threads
            threads = await self.langgraph.get_threads(force_refresh=True)
            thread = next((t for t in threads if t.get("thread_id") == thread_id), None)

            if not thread:
                logger.warning(f"Thread {thread_id} not in cache - may not exist")

            # Update session state (both legacy and new)
            old_thread = self.session.current_thread_id
            self.session.set_thread(thread_id)
            if self.app_state:
                self.app_state.set_thread(thread_id)
                self.app_state.update_threads_cache(threads)

            logger.info(f"Switched thread: {old_thread} → {thread_id}")

            return {
                "success": True,
                "message": f"Switched to thread: {thread_id[:8]}...",
                "thread_id": thread_id,
            }

        except Exception as e:
            logger.exception(f"Failed to switch thread: {thread_id}")
            return {
                "success": False,
                "message": f"Failed to switch thread: {e}",
            }

    async def create_thread(self, metadata: dict | None = None) -> dict:
        """Create new thread.

        Args:
            metadata: Optional metadata to attach to thread

        Returns:
            Dict with 'success' (bool), 'message' (str), 'thread_id' (str if success)
        """
        try:
            # Create thread via service (handles caching)
            thread_id, thread_dict = await self.langgraph.create_thread_with_metadata(
                metadata=metadata
            )

            # Update session state (both legacy and new)
            old_thread = self.session.current_thread_id
            self.session.set_thread(thread_id)
            if self.app_state:
                self.app_state.set_thread(thread_id)
                # Update cache with new thread
                if self.app_state.threads:
                    self.app_state.threads = [thread_dict] + self.app_state.threads
                else:
                    self.app_state.update_threads_cache([thread_dict])

            # Invalidate service cache to force refresh on next get
            self.langgraph.invalidate_thread_cache()

            logger.info(f"Created thread: {thread_id} (previous: {old_thread})")

            return {
                "success": True,
                "message": f"Created new thread: {thread_id[:8]}...",
                "thread_id": thread_id,
                "thread_dict": thread_dict,
            }

        except Exception as e:
            logger.exception("Failed to create thread")
            return {
                "success": False,
                "message": f"Failed to create thread: {e}",
            }

    async def get_agent_display_name(self, agent_id: str | None = None) -> str:
        """Get display name for agent.

        Args:
            agent_id: Agent ID (defaults to current agent)

        Returns:
            Display name (graph_id, name, or shortened UUID)
        """
        target_id = agent_id or self.session.current_assistant_id
        if not target_id:
            return "(none)"

        try:
            agents = await self.langgraph.get_agents()
            agent = next((a for a in agents if a.get("assistant_id") == target_id), None)

            if agent:
                return agent.get("graph_id") or agent.get("name") or target_id[:8]
            else:
                return target_id[:8]

        except Exception as e:
            logger.error(f"Failed to get agent display name: {e}")
            return target_id[:8]
