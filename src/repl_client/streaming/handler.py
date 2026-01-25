"""Stream handler for processing SSE chunks (Layer 4).

Processes streaming chunks from LangGraph server, extracting:
- Text deltas (from cumulative text)
- Tool calls (with buffering for partial JSON)
- Usage metadata
- Interrupts (Phase 2)

Uses generator pattern for loose coupling - yields ParsedChunk objects,
caller decides how to render.
"""

import json
from typing import AsyncIterator

from repl_client.core.parsers import ToolCall, Usage, extract_text_delta
from repl_client.core.session import SessionState
from repl_client.streaming.types import ChunkType, Interrupt, ParsedChunk


class StreamHandler:
    """Process streaming chunks and yield structured ParsedChunk objects.

    Design:
    - Generator pattern (loose coupling - no rendering)
    - Method-local buffers (auto-cleanup)
    - Uses parsers from Layer 2
    - Updates session tokens when usage received
    """

    def __init__(self, session: SessionState):
        """Initialize handler with session.

        Args:
            session: SessionState for tracking tokens
        """
        self.session = session

    async def process_stream(
        self,
        chunks: AsyncIterator[tuple[str, dict]],
        namespace: list | None = None,
    ) -> AsyncIterator[ParsedChunk]:
        """Process SSE stream and yield ParsedChunk objects.

        Handles:
        - Text delta extraction (cumulative → delta)
        - Tool call buffering (accumulate partial_json)
        - Usage tracking (update session)
        - Namespace tracking (for parallel agents)

        Args:
            chunks: AsyncIterator of (event_type, data) tuples from client
            namespace: Optional namespace for parallel agent tracking

        Yields:
            ParsedChunk objects with appropriate chunk_type
        """
        # Method-local state (auto-cleanup)
        prev_text_map: dict[str, str] = {}  # message_id -> cumulative text
        tool_call_buffer: dict[str, dict] = {}  # tool_id -> buffer state
        yielded_tool_ids: set[str] = set()  # Track tools already yielded via buffering

        # Convert namespace to hashable tuple
        ns_key = self.session.get_namespace_key(namespace)

        async for event_type, data in chunks:
            # Handle metadata events
            if event_type == "metadata":
                yield ParsedChunk(
                    chunk_type=ChunkType.METADATA,
                    namespace=ns_key,
                    metadata=data,
                )
                continue

            # Handle messages/metadata events
            if event_type == "messages/metadata":
                yield ParsedChunk(
                    chunk_type=ChunkType.METADATA,
                    namespace=ns_key,
                    metadata=data,
                )
                continue

            # Handle messages/partial and messages/complete
            if event_type in ("messages/partial", "messages/complete"):
                # Data is an array containing a single message object
                if not isinstance(data, list) or not data:
                    continue

                message = data[0]  # Extract first (and only) message from array
                message_id = message.get("id", "")
                content = message.get("content", [])
                usage_metadata = message.get("usage_metadata")
                response_metadata = message.get("response_metadata", {})
                stop_reason = response_metadata.get("stop_reason")
                tool_calls = message.get("tool_calls", [])

                # Handle content as string (fallback for simple messages)
                if isinstance(content, str):
                    delta = self._extract_text_delta(message_id, content, prev_text_map)
                    if delta:
                        yield ParsedChunk(
                            chunk_type=ChunkType.TEXT_DELTA,
                            namespace=ns_key,
                            message_id=message_id,
                            text_delta=delta,
                            metadata=response_metadata,
                        )
                    content = []  # Reset to empty list to skip block processing

                # Process content blocks
                for block in content:
                    # Handle string content (simple message format)
                    if isinstance(block, str):
                        # Treat string as text block
                        delta = self._extract_text_delta(message_id, block, prev_text_map)
                        if delta:
                            yield ParsedChunk(
                                chunk_type=ChunkType.TEXT_DELTA,
                                namespace=ns_key,
                                message_id=message_id,
                                text_delta=delta,
                                metadata=response_metadata,
                            )
                        continue

                    # Handle dict content blocks
                    if not isinstance(block, dict):
                        continue

                    block_type = block.get("type")

                    # Handle text blocks
                    if block_type == "text":
                        current_text = block.get("text", "")

                        # Extract delta
                        delta = self._extract_text_delta(message_id, current_text, prev_text_map)

                        # Only yield if there's new text
                        if delta:
                            yield ParsedChunk(
                                chunk_type=ChunkType.TEXT_DELTA,
                                namespace=ns_key,
                                message_id=message_id,
                                text_delta=delta,
                            )

                    # Handle tool_use blocks (buffering)
                    elif block_type == "tool_use":
                        complete_tool = self._buffer_tool_call(block, tool_call_buffer)

                        # If tool call is complete, yield it
                        if complete_tool:
                            tool_id = complete_tool["id"]
                            yielded_tool_ids.add(tool_id)  # Track that we yielded this

                            yield ParsedChunk(
                                chunk_type=ChunkType.TOOL_CALL_COMPLETE,
                                namespace=ns_key,
                                tool_call=ToolCall(
                                    id=tool_id,
                                    name=complete_tool["name"],
                                    args=complete_tool["args"],
                                    type=complete_tool.get("type", "tool_call"),
                                ),
                            )

                    # Handle tool_result blocks
                    elif block_type == "tool_result":
                        # Phase 1: Skip tool results (server-side execution)
                        # Phase 2: May need to display these
                        pass

                # Check for complete tool calls (from tool_calls array)
                if stop_reason == "tool_use" and tool_calls:
                    # Tool call detected via stop_reason
                    for tc in tool_calls:
                        tool_id = tc.get("id", "")

                        # Skip if already yielded via buffering
                        if tool_id in yielded_tool_ids:
                            continue

                        yield ParsedChunk(
                            chunk_type=ChunkType.TOOL_CALL_COMPLETE,
                            namespace=ns_key,
                            tool_call=ToolCall(
                                id=tool_id,
                                name=tc.get("name", ""),
                                args=tc.get("args", {}),
                                type=tc.get("type", "tool_call"),
                            ),
                        )

                # Handle usage metadata
                if usage_metadata:
                    usage = Usage(
                        input_tokens=usage_metadata.get("input_tokens", 0),
                        output_tokens=usage_metadata.get("output_tokens", 0),
                        total_tokens=usage_metadata.get("total_tokens", 0),
                    )

                    # Update session
                    self.session.track_tokens(usage.input_tokens, usage.output_tokens)

                    # Yield usage chunk
                    yield ParsedChunk(
                        chunk_type=ChunkType.USAGE,
                        namespace=ns_key,
                        usage=usage,
                    )

            # Handle updates stream (Phase 2 - interrupts)
            elif event_type == "updates":
                interrupt = self._parse_interrupt(data)
                if interrupt:
                    yield ParsedChunk(
                        chunk_type=ChunkType.INTERRUPT,
                        namespace=ns_key,
                        interrupt=interrupt,
                    )

    def _extract_text_delta(
        self,
        message_id: str,
        current_text: str,
        prev_text_map: dict[str, str],
    ) -> str:
        """Extract new text from cumulative update.

        Args:
            message_id: Message identifier
            current_text: Current cumulative text
            prev_text_map: Dict tracking previous text per message

        Returns:
            Delta (new text added)
        """
        prev_text = prev_text_map.get(message_id, "")
        delta = extract_text_delta(prev_text, current_text)

        # Update map
        prev_text_map[message_id] = current_text

        return delta

    def _buffer_tool_call(
        self,
        block: dict,
        buffer: dict[str, dict],
    ) -> dict | None:
        """Buffer tool call chunks, return complete tool when ready.

        Accumulates partial_json strings and attempts to parse.
        When JSON is valid, tool call is complete.

        Args:
            block: Content block with tool_use data
            buffer: Buffer dict (tool_id -> state)

        Returns:
            Complete tool dict or None if still buffering
        """
        tool_id = block.get("id")
        tool_name = block.get("name")
        partial_json = block.get("partial_json", "")

        if not tool_id:
            return None

        # Initialize buffer for this tool
        if tool_id not in buffer:
            buffer[tool_id] = {
                "id": tool_id,
                "name": tool_name,
                "partial_json": "",
            }

        # Update buffer with latest partial JSON
        buffer[tool_id]["partial_json"] = partial_json

        # Try to parse JSON
        try:
            args = json.loads(partial_json)

            # Success - tool call is complete
            complete_tool = {
                "id": tool_id,
                "name": tool_name,
                "args": args,
                "type": "tool_call",
            }

            # Clean up buffer
            del buffer[tool_id]

            return complete_tool

        except json.JSONDecodeError:
            # Still buffering
            return None

    def _parse_interrupt(self, updates_data: dict) -> Interrupt | None:
        """Extract __interrupt__ from updates stream (Phase 2).

        Args:
            updates_data: Data from updates stream event
                Expected format: {"__interrupt__": [{"value": {...}, "when": "during"}]}

        Returns:
            Interrupt object or None if no interrupt present
        """
        # Check for __interrupt__ key
        interrupts = updates_data.get("__interrupt__")

        if not interrupts or not isinstance(interrupts, list) or len(interrupts) == 0:
            return None

        # Take first interrupt (typically only one)
        interrupt_data = interrupts[0]

        # Validate interrupt_data is a dict
        if not isinstance(interrupt_data, dict):
            return None

        # Extract value (contains tool info)
        value = interrupt_data.get("value", {})

        # Generate interrupt ID (use tool name + timestamp for uniqueness)
        # In production, server might provide an ID
        tool_name = value.get("tool", "unknown")
        interrupt_id = f"interrupt_{tool_name}_{id(interrupt_data)}"

        return Interrupt(id=interrupt_id, value=value)
