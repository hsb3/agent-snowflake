"""Stream service wrapper with UI-specific logic.

Wraps StreamHandler to dispatch stream events to UI callbacks.
Provides clean separation between streaming mechanics and widget updates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator, Awaitable, Callable

from repl_client.core.logging import get_logger
from repl_client.streaming.types import ChunkType

if TYPE_CHECKING:
    from repl_client.streaming.handler import StreamHandler
    from repl_client.streaming.types import Interrupt, ToolCall, ToolResult, Usage

logger = get_logger("tui.services.stream")


class StreamService:
    """Wrapper around StreamHandler with UI-specific logic.

    Responsibilities:
    - Process stream and dispatch to UI callbacks
    - Centralize event routing logic
    - Make streaming testable via callbacks

    Design rationale:
    - Separates streaming mechanics (StreamHandler) from widget mounting (app)
    - Callbacks make it easy to test without TUI
    - Can swap StreamHandler implementation
    - Single place to add logging, error handling, etc.
    """

    def __init__(self, handler: StreamHandler):
        """Initialize service with stream handler.

        Args:
            handler: StreamHandler instance
        """
        self.handler = handler

    async def stream_with_widgets(
        self,
        chunks: AsyncIterator[tuple[str, dict]],
        on_text: Callable[[str], Awaitable[None]] | None = None,
        on_tool_call: Callable[[ToolCall], Awaitable[None]] | None = None,
        on_tool_result: Callable[[ToolResult], Awaitable[None]] | None = None,
        on_interrupt: Callable[[Interrupt], Awaitable[None]] | None = None,
        on_usage: Callable[[Usage], Awaitable[None]] | None = None,
        on_metadata: Callable[[dict], Awaitable[None]] | None = None,
        namespace: list | None = None,
    ) -> None:
        """Stream chunks and dispatch to UI callbacks.

        Processes stream via StreamHandler and routes ParsedChunk events to
        appropriate callbacks. Callbacks are optional - only specified handlers
        are invoked.

        Args:
            chunks: AsyncIterator of (event_type, data) tuples from client
            on_text: Callback for text deltas - receives text string
            on_tool_call: Callback for complete tool calls - receives ToolCall
            on_tool_result: Callback for tool results - receives ToolResult
            on_interrupt: Callback for interrupts - receives Interrupt
            on_usage: Callback for usage metadata - receives Usage
            on_metadata: Callback for metadata - receives dict
            namespace: Optional namespace for parallel agent tracking

        Example:
            async def handle_text(text: str):
                await ai_msg.append_content(text)

            async def handle_tool(tool_call: ToolCall):
                await mount_tool_widget(tool_call)

            await stream_service.stream_with_widgets(
                chunks,
                on_text=handle_text,
                on_tool_call=handle_tool,
            )
        """
        logger.debug("Starting stream processing with callbacks")

        parsed_count = 0
        async for parsed in self.handler.process_stream(chunks, namespace=namespace):
            parsed_count += 1

            try:
                # Dispatch text deltas
                if parsed.chunk_type == ChunkType.TEXT_DELTA:
                    if on_text and parsed.text_delta:
                        await on_text(parsed.text_delta)

                # Dispatch complete tool calls
                elif parsed.chunk_type == ChunkType.TOOL_CALL_COMPLETE:
                    if on_tool_call and parsed.tool_call:
                        await on_tool_call(parsed.tool_call)

                # Dispatch tool results
                elif parsed.chunk_type == ChunkType.TOOL_RESULT:
                    if on_tool_result and parsed.tool_result:
                        await on_tool_result(parsed.tool_result)

                # Dispatch interrupts (HITL)
                elif parsed.chunk_type == ChunkType.INTERRUPT:
                    if on_interrupt and parsed.interrupt:
                        await on_interrupt(parsed.interrupt)

                # Dispatch usage metadata
                elif parsed.chunk_type == ChunkType.USAGE:
                    if on_usage and parsed.usage:
                        await on_usage(parsed.usage)

                # Dispatch metadata
                elif parsed.chunk_type == ChunkType.METADATA:
                    if on_metadata and parsed.metadata:
                        await on_metadata(parsed.metadata)

            except Exception as e:
                logger.error(f"Error in stream callback for {parsed.chunk_type}: {e}")
                # Don't raise - continue processing stream
                # Individual callback failures shouldn't kill entire stream

        logger.debug(f"Stream processing complete - processed {parsed_count} chunks")
