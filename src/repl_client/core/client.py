"""LangGraph HTTP client for REPL.

Provides async client for interacting with LangGraph Cloud API.
Handles SSE streaming for message responses using dual stream mode.

Phase 2 Enhancement:
- Uses dual stream mode: ["messages", "updates"]
- "messages" stream: LLM tokens, tool calls, message metadata
- "updates" stream: State updates, __interrupt__ signals for HITL
"""

import json
from typing import Any, AsyncIterator

import httpx

from repl_client.core.logging import get_logger

logger = get_logger("client")


class LangGraphClient:
    """Async HTTP client for LangGraph Cloud API.

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
        logger.info(f"Initialized LangGraphClient with base_url={self.base_url}, timeout={timeout}")

    async def connect(self) -> bool:
        """Test connection to server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/ok")
                success = response.status_code == 200
                if success:
                    logger.info("Successfully connected to LangGraph server")
                else:
                    logger.error(f"Connection failed with status {response.status_code}")
                return success
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    async def list_agents(self, limit: int = 10) -> list[dict]:
        """List available assistants/agents.

        Args:
            limit: Maximum number of agents to return

        Returns:
            List of agent dictionaries with assistant_id
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/assistants/search", json={"limit": limit}
                )
                response.raise_for_status()
                data = response.json()

                # Response format: list of assistants
                agents = data if isinstance(data, list) else data.get("assistants", [])
                logger.info(f"Listed {len(agents)} agents")
                return agents
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            raise

    async def get_agent(self, assistant_id: str) -> dict:
        """Get details for specific agent.

        Args:
            assistant_id: Agent/assistant ID

        Returns:
            Agent details dictionary
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/assistants/{assistant_id}")
                response.raise_for_status()
                agent = response.json()
                logger.info(f"Retrieved agent {assistant_id}")
                return agent
        except Exception as e:
            logger.error(f"Failed to get agent {assistant_id}: {e}")
            raise

    async def create_thread(self, metadata: dict | None = None) -> str:
        """Create new thread.

        Args:
            metadata: Optional metadata to attach to thread

        Returns:
            Thread ID string
        """
        try:
            body = {}
            if metadata:
                body["metadata"] = metadata

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/threads", json=body)
                response.raise_for_status()
                data = response.json()
                thread_id = data["thread_id"]
                logger.info(f"Created thread {thread_id}")
                return thread_id
        except Exception as e:
            logger.error(f"Failed to create thread: {e}")
            raise

    async def get_thread(self, thread_id: str) -> dict:
        """Get thread details.

        Args:
            thread_id: Thread ID

        Returns:
            Thread details dictionary
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/threads/{thread_id}")
                response.raise_for_status()
                thread = response.json()
                logger.debug(f"Retrieved thread {thread_id}")
                return thread
        except Exception as e:
            logger.error(f"Failed to get thread {thread_id}: {e}")
            raise

    async def list_threads(self, limit: int = 10) -> list[dict]:
        """List threads.

        Args:
            limit: Maximum number of threads to return

        Returns:
            List of thread dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/threads/search", json={"limit": limit})
                response.raise_for_status()
                data = response.json()

                # Response format: list of threads
                threads = data if isinstance(data, list) else data.get("threads", [])
                logger.info(f"Listed {len(threads)} threads")
                return threads
        except Exception as e:
            logger.error(f"Failed to list threads: {e}")
            raise

    async def stream_message(
        self, thread_id: str, message: str, assistant_id: str
    ) -> AsyncIterator[tuple[str, dict]]:
        """Stream message to agent and yield SSE events.

        Uses dual stream mode to get both message updates and state updates.
        This is required for Phase 2 HITL support - __interrupt__ signals only
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
        body = {
            "assistant_id": assistant_id,
            "input": {"messages": [{"role": "user", "content": message}]},
            "stream_mode": ["messages", "updates"],
        }

        logger.info(f"Streaming message to thread {thread_id} with agent {assistant_id}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/threads/{thread_id}/runs/stream", json=body
                ) as response:
                    response.raise_for_status()

                    # Parse SSE stream
                    async for chunk in self._parse_sse_stream(response):
                        yield chunk

            logger.info(f"Completed streaming message to thread {thread_id}")

        except Exception as e:
            logger.error(f"Failed to stream message: {e}")
            raise

    async def resume_after_interrupt(
        self, thread_id: str, assistant_id: str, command: dict
    ) -> AsyncIterator[tuple[str, dict]]:
        """Resume execution after HITL interrupt.

        Uses dual stream mode to detect any subsequent interrupts.

        Args:
            thread_id: Thread ID
            assistant_id: Assistant/agent ID
            command: Command dict from HITLHandler (e.g., {"resume": {"approve": True}})

        Yields:
            Tuples of (event_type, data) from SSE stream.
            Same event types as stream_message.
        """
        body = {
            "assistant_id": assistant_id,
            "command": command,
            "stream_mode": ["messages", "updates"],
        }

        approved = command.get("resume", {}).get("approve", False)
        logger.info(f"Resuming thread {thread_id} with approval={approved}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/threads/{thread_id}/runs/stream", json=body
                ) as response:
                    response.raise_for_status()

                    # Parse SSE stream
                    async for chunk in self._parse_sse_stream(response):
                        yield chunk

            logger.info(f"Completed resuming thread {thread_id}")

        except Exception as e:
            logger.error(f"Failed to resume after interrupt: {e}")
            raise

    async def _parse_sse_stream(self, response: httpx.Response) -> AsyncIterator[tuple[str, dict]]:
        """Parse Server-Sent Events stream.

        SSE format:
            event: <event_type>
            data: <json_data>

            (blank line separates events)

        Args:
            response: httpx streaming response

        Yields:
            Tuples of (event_type, data_dict)
        """
        event_type = None
        data_lines = []

        async for line in response.aiter_lines():
            line = line.strip()

            # Empty line signals end of event
            if not line:
                if event_type and data_lines:
                    # Join data lines and parse JSON
                    data_str = "\n".join(data_lines)
                    try:
                        data = json.loads(data_str)
                        logger.debug(f"Parsed SSE event: {event_type}")
                        yield (event_type, data)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse SSE data: {e}")

                # Reset for next event
                event_type = None
                data_lines = []
                continue

            # Parse event line
            if line.startswith("event:"):
                event_type = line[6:].strip()

            # Parse data line
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())
