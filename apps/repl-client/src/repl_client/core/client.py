"""LangGraph client for REPL.

Provides async client for interacting with LangGraph API using the official SDK.
Handles streaming for message responses using dual stream mode.

Uses langgraph-sdk for all API calls. See: https://docs.langchain.com/langsmith/langgraph-python-sdk
"""

from typing import TYPE_CHECKING, Any, AsyncIterator, cast

from langgraph_sdk import get_client
from langgraph_sdk.schema import Command

from repl_client.core.logging import get_logger

if TYPE_CHECKING:
    from langgraph_sdk.client import LangGraphClient as SDKClient

logger = get_logger("client")

# Type alias for SDK responses (TypedDicts that are dict-compatible)
DictResponse = dict[str, Any]


class LangGraphClient:
    """Async client for LangGraph API using the official SDK.

    Handles connection, agent management, thread management, and streaming messages.
    """

    def __init__(self, base_url: str, timeout: int = 30):
        """Initialize client.

        Args:
            base_url: Base URL for LangGraph server (e.g., http://localhost:2024)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: "SDKClient" = get_client(url=self.base_url)
        logger.info(f"Initialized LangGraphClient with base_url={self.base_url}, timeout={timeout}")

    async def connect(self) -> bool:
        """Test connection to server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Use assistants.search as a health check
            await self._client.assistants.search(limit=1)
            logger.info("Successfully connected to LangGraph server")
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def list_agents(self, limit: int = 10) -> list[DictResponse]:
        """List available assistants/agents.

        Args:
            limit: Maximum number of agents to return

        Returns:
            List of agent dictionaries with assistant_id
        """
        try:
            agents = await self._client.assistants.search(limit=limit)
            logger.info(f"Listed {len(agents)} agents")
            # SDK returns TypedDicts which are dict subclasses
            return cast(list[DictResponse], agents)
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise

    async def get_agent(self, assistant_id: str) -> DictResponse:
        """Get details for specific agent.

        Args:
            assistant_id: Agent/assistant ID

        Returns:
            Agent details dictionary
        """
        try:
            agent = await self._client.assistants.get(assistant_id)
            logger.info(f"Retrieved agent {assistant_id}")
            return cast(DictResponse, agent)
        except Exception as e:
            logger.error(f"Failed to get agent {assistant_id}: {e}")
            raise

    async def get_agent_schemas(self, assistant_id: str) -> DictResponse:
        """Get schema information for specific agent.

        Fetches the schemas endpoint which includes input_schema, output_schema,
        state_schema, config_schema, and context_schema.

        Args:
            assistant_id: Agent/assistant ID

        Returns:
            Schema dictionary with graph_id and various schema definitions
        """
        try:
            schemas = await self._client.assistants.get_schemas(assistant_id)
            logger.info(f"Retrieved schemas for agent {assistant_id}")
            return cast(DictResponse, schemas)
        except Exception as e:
            logger.error(f"Failed to get schemas for agent {assistant_id}: {e}")
            raise

    async def create_thread(self, metadata: DictResponse | None = None) -> str:
        """Create new thread.

        Args:
            metadata: Optional metadata to attach to thread

        Returns:
            Thread ID string
        """
        try:
            thread = await self._client.threads.create(metadata=metadata)
            thread_id = thread["thread_id"]
            logger.info(f"Created thread {thread_id}")
            return thread_id
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise

    async def get_thread(self, thread_id: str) -> DictResponse:
        """Get thread details.

        Args:
            thread_id: Thread ID

        Returns:
            Thread details dictionary
        """
        try:
            thread = await self._client.threads.get(thread_id)
            logger.debug(f"Retrieved thread {thread_id}")
            return cast(DictResponse, thread)
        except Exception as e:
            logger.error(f"Failed to get thread {thread_id}: {e}")
            raise

    async def list_threads(self, limit: int = 10) -> list[DictResponse]:
        """List threads.

        Args:
            limit: Maximum number of threads to return

        Returns:
            List of thread dictionaries
        """
        try:
            threads = await self._client.threads.search(limit=limit)
            logger.info(f"Listed {len(threads)} threads")
            return cast(list[DictResponse], threads)
        except Exception as e:
            logger.error(f"Failed to list threads: {e}")
            raise

    async def get_thread_history(self, thread_id: str, limit: int = 100) -> list[DictResponse]:
        """Get thread history (checkpoints).

        Args:
            thread_id: Thread ID
            limit: Maximum number of history entries to return

        Returns:
            List of history entries (checkpoints)
        """
        try:
            history = await self._client.threads.get_history(thread_id, limit=limit)
            logger.info(f"Retrieved {len(history)} history entries for thread {thread_id}")
            return cast(list[DictResponse], history)
        except Exception as e:
            logger.error(f"Failed to get history for thread {thread_id}: {e}")
            raise

    async def get_thread_state(self, thread_id: str) -> DictResponse:
        """Get current state of a thread.

        Args:
            thread_id: Thread ID

        Returns:
            Thread state dictionary
        """
        try:
            state = await self._client.threads.get_state(thread_id)
            logger.debug(f"Retrieved state for thread {thread_id}")
            return cast(DictResponse, state)
        except Exception as e:
            logger.error(f"Failed to get state for thread {thread_id}: {e}")
            raise

    async def stream_message(
        self, thread_id: str, message: str, assistant_id: str
    ) -> AsyncIterator[tuple[str, DictResponse]]:
        """Stream message to agent and yield SSE events.

        Uses dual stream mode to get both message updates and state updates.
        This is required for HITL support - __interrupt__ signals only
        appear in the 'updates' stream.

        Args:
            thread_id: Thread ID
            message: User message
            assistant_id: Assistant/agent ID

        Yields:
            Tuples of (event_type, data) from SSE stream.
            Event types include:
            - messages/partial: Streaming message chunks
            - messages/complete: Complete messages (tool results)
            - messages/metadata: Message metadata
            - updates: State updates including __interrupt__ signals
            - metadata: Run metadata
        """
        logger.info(f"Streaming message to thread {thread_id} with agent {assistant_id}")

        try:
            stream = self._client.runs.stream(
                thread_id,
                assistant_id,
                input={"messages": [{"role": "user", "content": message}]},
                stream_mode=["messages", "updates"],
            )
            async for chunk in stream:
                yield (chunk.event, chunk.data)

            logger.info(f"Completed streaming message to thread {thread_id}")

        except Exception as e:
            logger.error(f"Failed to stream message: {e}")
            raise

    async def resume_after_interrupt(
        self, thread_id: str, assistant_id: str, command: DictResponse
    ) -> AsyncIterator[tuple[str, DictResponse]]:
        """Resume execution after HITL interrupt.

        Uses dual stream mode to detect any subsequent interrupts.

        Args:
            thread_id: Thread ID
            assistant_id: Assistant/agent ID
            command: Command dict (e.g., {"resume": {"approve": True}})

        Yields:
            Tuples of (event_type, data) from SSE stream.
            Same event types as stream_message.
        """
        # Extract resume value from command dict and convert to SDK Command
        resume_value = command.get("resume", {})
        approved = resume_value.get("approve", False) if isinstance(resume_value, dict) else False
        logger.info(f"Resuming thread {thread_id} with approval={approved}")

        try:
            sdk_command = Command(resume=resume_value)
            stream = self._client.runs.stream(
                thread_id,
                assistant_id,
                command=sdk_command,
                stream_mode=["messages", "updates"],
            )
            async for chunk in stream:
                yield (chunk.event, chunk.data)

            logger.info(f"Completed resuming thread {thread_id}")

        except Exception as e:
            logger.error(f"Failed to resume after interrupt: {e}")
            raise
