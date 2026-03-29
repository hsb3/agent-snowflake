"""LangGraph service wrapper with app-specific logic.

Wraps LangGraphClient with caching, error handling, and UI-friendly formatting.
Like a webapp API service layer.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from repl_client.core.logging import get_logger

if TYPE_CHECKING:
    from repl_client.core.client import LangGraphClient

logger = get_logger("tui.services.langgraph")


class LangGraphService:
    """Wrapper around LangGraphClient with app-specific logic.

    Responsibilities:
    - Cache agents and threads to avoid redundant API calls
    - Provide UI-friendly error messages
    - Handle agent name resolution (friendly name → UUID)
    - Centralize retry logic (future)

    Design rationale:
    - Separates caching logic from UI
    - Makes testing easier (can mock this service)
    - Provides single source of truth for cached data
    """

    def __init__(self, client: LangGraphClient):
        """Initialize service with LangGraph client.

        Args:
            client: LangGraphClient instance
        """
        self.client = client
        self._agent_cache: list[dict] | None = None
        self._threads_cache: list[dict] | None = None
        self._schema_cache: dict[str, dict] = {}  # assistant_id -> schemas

    async def get_agents(self, limit: int = 10, force_refresh: bool = False) -> list[dict]:
        """Get agents with caching.

        Args:
            limit: Maximum number of agents to fetch
            force_refresh: Force API call even if cached

        Returns:
            List of agent dictionaries with 'assistant_id', 'graph_id', etc.

        Raises:
            Exception: If API call fails (propagated from client)
        """
        if self._agent_cache is not None and not force_refresh:
            logger.debug(f"Returning {len(self._agent_cache)} cached agents")
            return self._agent_cache

        try:
            agents = await self.client.list_agents(limit=limit)
            self._agent_cache = agents
            logger.info(f"Fetched and cached {len(agents)} agents")
            return agents
        except Exception as e:
            logger.error(f"Failed to fetch agents: {e}")
            raise

    async def resolve_agent_name(self, name: str) -> str | None:
        """Resolve friendly agent name to UUID.

        Checks both 'graph_id' and 'name' fields against provided name.
        Falls back to exact match on 'assistant_id' if no friendly name matches.

        Args:
            name: Agent name (graph_id, name, or assistant_id)

        Returns:
            Assistant UUID if found, None otherwise
        """
        agents = await self.get_agents()

        for agent in agents:
            graph_id = agent.get("graph_id", "")
            agent_name = agent.get("name", "")
            assistant_id = agent.get("assistant_id", "")

            # Check friendly names first
            if name.lower() in (graph_id.lower(), agent_name.lower()):
                logger.debug(f"Resolved '{name}' to agent {assistant_id}")
                return assistant_id

            # Fallback to exact UUID match
            if name == assistant_id:
                logger.debug(f"Matched exact assistant_id: {assistant_id}")
                return assistant_id

        logger.warning(f"No agent found matching '{name}'")
        return None

    async def get_threads(self, limit: int = 20, force_refresh: bool = False) -> list[dict]:
        """Get threads with caching.

        Args:
            limit: Maximum number of threads to fetch
            force_refresh: Force API call even if cached

        Returns:
            List of thread dictionaries with 'thread_id', 'created_at', etc.

        Raises:
            Exception: If API call fails (propagated from client)
        """
        if self._threads_cache is not None and not force_refresh:
            logger.debug(f"Returning {len(self._threads_cache)} cached threads")
            return self._threads_cache

        try:
            threads = await self.client.list_threads(limit=limit)
            self._threads_cache = threads
            logger.info(f"Fetched and cached {len(threads)} threads")
            return threads
        except Exception as e:
            logger.error(f"Failed to fetch threads: {e}")
            raise

    async def create_thread_with_metadata(self, metadata: dict | None = None) -> tuple[str, dict]:
        """Create thread and cache metadata.

        Creates thread via client, then fetches full details and updates cache.

        Args:
            metadata: Optional metadata to attach to thread

        Returns:
            Tuple of (thread_id, thread_dict)

        Raises:
            Exception: If API call fails (propagated from client)
        """
        try:
            # Create thread
            thread_id = await self.client.create_thread(metadata=metadata)
            logger.info(f"Created thread {thread_id}")

            # Fetch full thread details
            try:
                thread_dict = await self.client.get_thread(thread_id)
            except Exception as e:
                # If get fails, construct minimal dict
                logger.warning(f"Failed to fetch thread details: {e}")
                thread_dict = {
                    "thread_id": thread_id,
                    "metadata": metadata or {},
                }

            # Update cache (prepend new thread)
            if self._threads_cache is not None:
                self._threads_cache.insert(0, thread_dict)
            else:
                self._threads_cache = [thread_dict]

            return thread_id, thread_dict

        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise

    async def get_agent_schemas(self, assistant_id: str, force_refresh: bool = False) -> dict:
        """Get schema information for specific agent with caching.

        Args:
            assistant_id: Agent/assistant ID
            force_refresh: Force API call even if cached

        Returns:
            Schema dictionary with graph_id, context_schema, etc.

        Raises:
            Exception: If API call fails (propagated from client)
        """
        if assistant_id in self._schema_cache and not force_refresh:
            logger.debug(f"Returning cached schemas for agent {assistant_id}")
            return self._schema_cache[assistant_id]

        try:
            schemas = await self.client.get_agent_schemas(assistant_id)
            self._schema_cache[assistant_id] = schemas
            logger.info(f"Fetched and cached schemas for agent {assistant_id}")
            return schemas
        except Exception as e:
            logger.error(f"Failed to fetch schemas for agent {assistant_id}: {e}")
            raise

    def invalidate_agent_cache(self) -> None:
        """Invalidate agent cache to force refresh on next get."""
        logger.debug("Invalidating agent cache")
        self._agent_cache = None

    def invalidate_thread_cache(self) -> None:
        """Invalidate thread cache to force refresh on next get."""
        logger.debug("Invalidating thread cache")
        self._threads_cache = None

    def invalidate_schema_cache(self, assistant_id: str | None = None) -> None:
        """Invalidate schema cache.

        Args:
            assistant_id: Specific agent to invalidate, or None for all
        """
        if assistant_id:
            logger.debug(f"Invalidating schema cache for agent {assistant_id}")
            self._schema_cache.pop(assistant_id, None)
        else:
            logger.debug("Invalidating all schema caches")
            self._schema_cache.clear()

    def invalidate_all_caches(self) -> None:
        """Invalidate all caches."""
        logger.debug("Invalidating all caches")
        self._agent_cache = None
        self._threads_cache = None
        self._schema_cache.clear()
