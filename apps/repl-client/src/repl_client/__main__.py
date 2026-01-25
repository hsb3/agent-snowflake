"""Main REPL loop (Layer 8) - Classic Terminal REPL.

Entry point for the classic REPL client. Orchestrates all components:
- Client connection
- Session state
- Stream handling
- Rendering
- Command routing

NOTE: This is the classic terminal REPL (Phase 1 implementation).
For production use, consider the Textual TUI instead: python -m repl_client.tui

The TUI provides:
- Better UX (sidebar, tabs, modals, status area)
- More features (session management, artifact palette)
- Proper layout and responsive design

This classic REPL is maintained for:
- Simplicity/minimalism preference
- Fallback if TUI has issues
- Reference implementation

May be deprecated in future releases if TUI proves sufficient.
See: src/repl_client/tui/ for TUI implementation.
"""

import asyncio
import sys
import time

from repl_client.commands.handlers import CommandHandlers
from repl_client.commands.registry import CommandRegistry
from repl_client.core.client import LangGraphClient
from repl_client.core.config import Config
from repl_client.core.logging import get_logger
from repl_client.core.session import SessionState
from repl_client.streaming.handler import StreamHandler
from repl_client.streaming.hitl import HITLHandler
from repl_client.streaming.types import ChunkType
from repl_client.ui.renderer import Renderer

logger = get_logger("main")


class REPLLoop:
    """Main REPL orchestrator.

    Coordinates all components and manages the main input loop.
    """

    def __init__(self, config: Config):
        """Initialize REPL with all components.

        Args:
            config: Configuration instance
        """
        self.config = config

        # Initialize components
        self.client = LangGraphClient(
            base_url=config.server_url,
            timeout=30,
        )
        self.session = SessionState()
        self.stream_handler = StreamHandler(session=self.session)
        self.renderer = Renderer()
        self.hitl_handler = HITLHandler(renderer=self.renderer)
        self.command_registry = CommandRegistry()
        self.command_handlers = CommandHandlers(
            client=self.client,
            session=self.session,
            renderer=self.renderer,
        )

        # Register commands
        self.command_handlers.register_all(self.command_registry)

        logger.info("REPLLoop initialized")

    def run(self) -> int:
        """Main REPL loop.

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Startup
            if not asyncio.run(self._startup()):
                return 1

            # Main loop
            while True:
                try:
                    user_input = self._get_input()
                    should_continue = self._handle_input(user_input)

                    if not should_continue:
                        break

                except KeyboardInterrupt:
                    self.renderer.render_text("\nInterrupted by user", style="yellow")
                    break
                except EOFError:
                    self.renderer.render_text("\nEOF received", style="yellow")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    self.renderer.render_error(f"Unexpected error: {e}")

            # Shutdown
            self._shutdown()
            return 0

        except Exception as e:
            logger.error(f"Fatal error: {e}", exc_info=True)
            self.renderer.render_error(f"Fatal error: {e}")
            return 1

    async def _startup(self) -> bool:
        """Startup sequence.

        Returns:
            True if startup successful, False otherwise
        """
        try:
            # 1. Connect to server
            self.renderer.render_text("Connecting to LangGraph server...", style="cyan")
            connected = await self.client.connect()

            if not connected:
                self.renderer.render_error(
                    f"Failed to connect to server at {self.config.server_url}"
                )
                return False

            self.renderer.render_success(f"Connected to {self.config.server_url}")

            # 2. List agents and set default
            agents = await self.client.list_agents(limit=10)
            if agents:
                # Use config default if set, otherwise use first agent
                if self.config.default_agent:
                    agent_id = self.config.default_agent
                else:
                    agent_id = agents[0].get("assistant_id", "")

                self.session.set_agent(agent_id)
                self.renderer.render_text(f"Using agent: {agent_id}", style="cyan")
            else:
                self.renderer.render_text("Warning: No agents available", style="yellow")

            # 3. Create initial thread
            thread_id = await self.client.create_thread()
            self.session.set_thread(thread_id)
            logger.info(f"Created initial thread: {thread_id}")

            # 4. Show welcome banner
            welcome = (
                "Welcome to LangGraph REPL!\n\n"
                "Type your message to chat with the agent.\n"
                "Type /help for available commands.\n"
                "Type /exit to quit."
            )
            self.renderer.render_panel(welcome, "LangGraph REPL", style="blue")

            return True

        except Exception as e:
            logger.error(f"Startup failed: {e}", exc_info=True)
            self.renderer.render_error(f"Startup failed: {e}")
            return False

    def _get_input(self) -> str:
        """Get user input.

        Returns:
            User input string
        """
        # Phase 1: Simple input() - Phase 3 will use prompt-toolkit
        try:
            return input("> ")
        except (EOFError, KeyboardInterrupt):
            raise

    def _handle_input(self, user_input: str) -> bool:
        """Handle user input - route to command or message.

        Args:
            user_input: Raw user input

        Returns:
            True to continue loop, False to exit
        """
        # Strip whitespace
        user_input = user_input.strip()

        # Ignore empty input
        if not user_input:
            return True

        # Route to command or message
        if user_input.startswith("/"):
            # Parse command
            cmd_name, args = self._parse_command_input(user_input)

            try:
                # Execute command
                result = self.command_registry.execute(cmd_name, args)

                # Check if command returned False (exit signal)
                if result is False:
                    return False

                # Handle async commands
                if asyncio.iscoroutine(result):
                    asyncio.run(result)

            except ValueError as e:
                self.renderer.render_error(str(e))
            except Exception as e:
                logger.error(f"Command execution error: {e}", exc_info=True)
                self.renderer.render_error(f"Command error: {e}")

            return True
        else:
            # Send as message
            asyncio.run(self._send_message(user_input))
            return True

    def _parse_command_input(self, user_input: str) -> tuple[str, list[str]]:
        """Parse command input into name and arguments.

        Args:
            user_input: Command input (e.g., "/help agents")

        Returns:
            Tuple of (command_name, args_list)
        """
        # Remove leading /
        command_str = user_input[1:]

        # Split into parts
        parts = command_str.split()

        if not parts:
            return ("", [])

        cmd_name = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        return (cmd_name, args)

    async def _send_message(self, message: str) -> None:
        """Send message to agent and render response.

        Args:
            message: User message
        """
        try:
            # Verify we have thread and agent
            if not self.session.current_thread_id:
                self.renderer.render_error("No active thread. Use /new to create one.")
                return

            if not self.session.current_assistant_id:
                self.renderer.render_error("No active agent. Use /agents to select one.")
                return

            # Display user message
            self.renderer.render_text(f"\nYou: {message}", style="green")
            self.renderer.console.print("\nAgent: ", style="cyan", end="")

            # Stream response
            chunks = self.client.stream_message(
                thread_id=self.session.current_thread_id,
                message=message,
                assistant_id=self.session.current_assistant_id,
            )

            # Process stream
            await self._handle_stream(chunks)

            # Add newline after response
            self.renderer.render_text("")

        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
            self.renderer.render_error(f"\nError: {e}")

    async def _handle_stream(self, chunks) -> None:
        """Process stream chunks and render.

        Args:
            chunks: AsyncIterator of (event_type, data) tuples
        """
        # Process through StreamHandler
        parsed_chunks = self.stream_handler.process_stream(chunks)

        # Render each chunk
        async for parsed in parsed_chunks:
            if parsed.chunk_type == ChunkType.TEXT_DELTA:
                # Render text delta (no newline)
                if parsed.text_delta:
                    self.renderer.console.print(parsed.text_delta, style="cyan", end="")

            elif parsed.chunk_type == ChunkType.TOOL_CALL_COMPLETE:
                # Log tool calls
                if parsed.tool_call:
                    logger.info(f"Tool call: {parsed.tool_call.name}({parsed.tool_call.args})")

            elif parsed.chunk_type == ChunkType.USAGE:
                # Usage already tracked by StreamHandler
                logger.debug(f"Usage: {parsed.usage}")

            elif parsed.chunk_type == ChunkType.METADATA:
                # Log metadata
                logger.debug(f"Metadata: {parsed.metadata}")

            elif parsed.chunk_type == ChunkType.INTERRUPT:
                # Phase 2: Handle HITL interrupts
                if parsed.interrupt:
                    logger.info(f"Interrupt received: {parsed.interrupt.id}")

                    # Add newline before approval prompt
                    self.renderer.render_text("")

                    # Show approval prompt and get command
                    command = self.hitl_handler.handle_interrupt(parsed.interrupt, self.session)

                    # Check required IDs are present before resuming
                    if not self.session.current_thread_id or not self.session.current_assistant_id:
                        logger.error("Cannot resume interrupt: missing thread_id or assistant_id")
                        return

                    # Resume with approval
                    resume_chunks = self.client.resume_after_interrupt(
                        self.session.current_thread_id, self.session.current_assistant_id, command
                    )

                    # Continue processing resumed stream (recursive call)
                    # Add newline and reset agent prompt
                    self.renderer.render_text("\nAgent: ", style="cyan")
                    await self._handle_stream(resume_chunks)

    def _shutdown(self) -> None:
        """Cleanup and show session summary."""
        # Calculate session duration
        duration = time.time() - self.session.session_start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)

        # Build summary
        token_summary = self.session.get_token_summary()
        summary = (
            f"Session Duration: {minutes}m {seconds}s\n"
            f"Tokens Used: {token_summary['total']} "
            f"({token_summary['input']} in / {token_summary['output']} out)"
        )

        self.renderer.render_panel(summary, "Session Summary", style="blue")


def main():
    """Main entry point."""
    config = Config.from_env()
    repl = REPLLoop(config)
    exit_code = repl.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
