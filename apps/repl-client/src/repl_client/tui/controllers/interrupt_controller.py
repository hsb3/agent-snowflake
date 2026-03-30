"""Interrupt controller for handling HITL interrupts.

Coordinates interrupt handling between HITLHandler and streaming.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from repl_client.core.logging import get_logger

if TYPE_CHECKING:
    from textual.containers import ScrollableContainer

    from repl_client.core.session import SessionState
    from repl_client.streaming.types import Interrupt
    from repl_client.tui.hitl import HITLHandler
    from repl_client.tui.services import LangGraphService, StreamService
    from repl_client.tui.widgets import AssistantMessage, StatusArea

logger = get_logger("tui.controllers.interrupt")


class InterruptController:
    """Handle HITL interrupt processing.

    Responsibilities:
    - Show approval prompts via HITLHandler
    - Resume stream with approval decision
    - Recursively process resumed stream
    - Coordinate between services and message widgets

    Design:
    - Encapsulates interrupt flow
    - Recursive handling for nested interrupts
    - Delegates UI to HITLHandler
    - Delegates streaming to StreamService
    """

    def __init__(
        self,
        langgraph_service: LangGraphService,
        stream_service: StreamService,
        hitl_handler: HITLHandler,
        session: SessionState,
        message_controller: Any = None,
    ):
        """Initialize interrupt controller.

        Args:
            langgraph_service: Service for LangGraph API calls
            stream_service: Service for stream processing
            hitl_handler: Handler for approval prompts
            session: Session state tracker
            message_controller: Controller for message processing (circular dep, set later)
        """
        self.langgraph = langgraph_service
        self.stream = stream_service
        self.hitl = hitl_handler
        self.session = session
        self.message_controller = message_controller

    def set_message_controller(self, controller: Any) -> None:
        """Set message controller (handle circular dependency).

        Args:
            controller: MessageController instance
        """
        self.message_controller = controller

    async def handle_interrupt(
        self,
        interrupt: Interrupt,
        ai_msg: AssistantMessage,
        messages_container: ScrollableContainer,
        status_area: StatusArea | None,
    ) -> None:
        """Handle HITL interrupt.

        Shows approval prompt, resumes stream, and recursively processes response.

        Args:
            interrupt: Interrupt object from stream
            ai_msg: Current assistant message widget
            messages_container: Container to mount widgets to
            status_area: Optional status area to update
        """
        logger.info("Handling interrupt")

        # Update status
        if status_area:
            status_area.set_status("Waiting for approval...")

        # Show approval prompt via HITL handler
        try:
            approved = await self.hitl.handle_interrupt(interrupt, self.session)
        except Exception as e:
            logger.exception("Failed to get approval")
            if status_area:
                status_area.set_status(f"Approval failed: {e}", error=True)
            return

        # Update status
        if status_area:
            status_area.set_status("Resuming stream...")

        # Build resume command
        command = {"resume": {"approve": approved}}

        # Resume stream with approval decision
        if not self.session.current_thread_id or not self.session.current_assistant_id:
            logger.error("No thread or agent set - cannot resume")
            if status_area:
                status_area.set_status("Cannot resume - no thread/agent", error=True)
            return

        try:
            chunks = self.langgraph.client.resume_after_interrupt(
                thread_id=self.session.current_thread_id,
                assistant_id=self.session.current_assistant_id,
                command=command,
            )

            # Recursively process resumed stream
            # Use message controller's stream processing logic
            if self.message_controller:
                await self.message_controller.process_stream(
                    chunks, ai_msg, messages_container, status_area
                )
            else:
                logger.warning("No message controller - cannot process resumed stream")

        except Exception as e:
            logger.exception("Failed to resume stream")
            if status_area:
                status_area.set_status(f"Resume failed: {e}", error=True)
