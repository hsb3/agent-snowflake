"""Message controller for handling message sending and streaming.

Coordinates between services (LangGraph, Stream) and views (message widgets).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from repl_client.core.logging import get_logger
from repl_client.tui.widgets import AssistantMessage, LoadingWidget, ToolCallMessage, UserMessage

if TYPE_CHECKING:
    from textual.containers import ScrollableContainer

    from repl_client.core.session import SessionState
    from repl_client.streaming.types import Interrupt, ToolCall, ToolResult, Usage
    from repl_client.tui.models import AppState
    from repl_client.tui.services import LangGraphService, StreamService
    from repl_client.tui.widgets import StatusArea

logger = get_logger("tui.controllers.message")


class MessageController:
    """Handle message sending and streaming.

    Responsibilities:
    - Orchestrate user message submission
    - Manage loading indicators
    - Stream AI responses with real-time widget updates
    - Handle tool calls and results
    - Track token usage
    - Delegate interrupts to InterruptController

    Design:
    - Coordinates between services (data) and views (widgets)
    - Contains business logic for message flow
    - Testable via mocking services and views
    """

    def __init__(
        self,
        langgraph_service: LangGraphService,
        stream_service: StreamService,
        session: SessionState,
        interrupt_controller: Any = None,
        app_state: AppState | None = None,
    ):
        """Initialize message controller.

        Args:
            langgraph_service: Service for LangGraph API calls
            stream_service: Service for stream processing
            session: Session state tracker (legacy, kept for compatibility)
            interrupt_controller: Controller for HITL interrupts (circular dep, set later)
            app_state: Reactive app state (new, preferred)
        """
        self.langgraph = langgraph_service
        self.stream = stream_service
        self.session = session
        self.interrupt_controller = interrupt_controller
        self.app_state = app_state

    def set_interrupt_controller(self, controller: Any) -> None:
        """Set interrupt controller (handle circular dependency).

        Args:
            controller: InterruptController instance
        """
        self.interrupt_controller = controller

    async def send_message(
        self,
        text: str,
        messages_container: ScrollableContainer,
        status_area: StatusArea | None = None,
    ) -> None:
        """Send message and stream response.

        Orchestrates full message flow:
        1. Mount user message widget
        2. Show loading indicator
        3. Create AI message widget
        4. Stream chunks and update widgets
        5. Handle tool calls, interrupts, usage
        6. Finalize streaming

        Args:
            text: User message text
            messages_container: Container to mount message widgets to
            status_area: Optional status area to update

        Raises:
            Exception: If streaming fails (propagated after logging)
        """
        if not self.session.current_thread_id or not self.session.current_assistant_id:
            logger.error("No thread or agent set - cannot send message")
            raise ValueError("No thread or agent configured")

        # 1. Add user message widget
        user_msg = UserMessage(text)
        await messages_container.mount(user_msg)
        messages_container.scroll_end(animate=False)

        # 2. Show loading indicator
        loading = LoadingWidget()
        await messages_container.mount(loading)
        messages_container.scroll_end(animate=False)

        # Update status
        if status_area:
            status_area.set_status("Streaming...")

        try:
            # 3. Stream from server
            chunks = self.langgraph.client.stream_message(
                thread_id=self.session.current_thread_id,
                message=text,
                assistant_id=self.session.current_assistant_id,
            )

            # 4. Create AI message widget (empty initially)
            ai_msg = AssistantMessage()
            await messages_container.mount(ai_msg)

            # 5. Remove loading widget
            await loading.remove()

            # 6. Process stream with callbacks
            await self._process_stream(chunks, ai_msg, messages_container, status_area)

            # 7. Finalize assistant message
            await ai_msg.stop_stream()

            # Update status
            if status_area:
                status_area.set_status("Ready")

        except Exception as e:
            logger.exception("Failed to send message")
            # Remove loading if still present
            try:
                await loading.remove()
            except Exception:
                pass

            if status_area:
                status_area.set_status(f"Error: {e}", error=True)
            raise

    async def _process_stream(
        self,
        chunks,
        ai_msg: AssistantMessage,
        messages_container: ScrollableContainer,
        status_area: StatusArea | None,
    ) -> None:
        """Process stream chunks and update widgets.

        Args:
            chunks: AsyncIterator of (event_type, data) tuples from client
            ai_msg: AI message widget to update
            messages_container: Container to mount tool widgets to
            status_area: Optional status area to update tokens
        """
        current_tool_msg: ToolCallMessage | None = None

        # Define callbacks for stream service
        async def on_text(text_delta: str) -> None:
            await ai_msg.append_content(text_delta)
            messages_container.scroll_end(animate=False)

        async def on_tool_call(tool_call: ToolCall) -> None:
            nonlocal current_tool_msg
            tool_msg = ToolCallMessage(
                tool_name=tool_call.name,
                args=tool_call.args,
            )
            await messages_container.mount(tool_msg)
            messages_container.scroll_end(animate=False)
            current_tool_msg = tool_msg

        async def on_tool_result(tool_result: ToolResult) -> None:
            nonlocal current_tool_msg
            if current_tool_msg:
                result = tool_result.result
                if tool_result.status == "error":
                    current_tool_msg.set_error(result)
                else:
                    current_tool_msg.set_success(result)
                current_tool_msg = None

        async def on_interrupt(interrupt: Interrupt) -> None:
            if self.interrupt_controller:
                await self.interrupt_controller.handle_interrupt(
                    interrupt, ai_msg, messages_container, status_area
                )

        async def on_usage(usage: Usage) -> None:
            self.session.track_tokens(usage.input_tokens, usage.output_tokens)
            tokens_summary = self.session.get_token_summary()
            total_tokens = tokens_summary["total"]

            # Update app state
            if self.app_state:
                self.app_state.tokens = total_tokens

            if status_area:
                status_area.set_tokens(total_tokens)

        # Use stream service to process chunks
        await self.stream.stream_with_widgets(
            chunks,
            on_text=on_text,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
            on_interrupt=on_interrupt,
            on_usage=on_usage,
        )
