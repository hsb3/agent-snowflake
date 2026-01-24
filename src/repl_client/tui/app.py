"""Main Textual TUI application for REPL client.

Integrates all widgets (UserMessage, AssistantMessage, ToolCallMessage, ChatInput,
StatusBar, LoadingWidget) with the streaming backend (LangGraphClient, StreamHandler,
HITLHandler, SessionState).

Architecture:
- Layer 1: LangGraphClient (HTTP/SSE)
- Layer 2: Parsers (SSE → ParsedChunk)
- Layer 3: SessionState (thread/agent tracking)
- Layer 4: StreamHandler (ParsedChunk generator)
- Layer 5: HITLHandler (approval prompts)
- Layer 8: This app (orchestration + widgets)
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Label, OptionList
from textual.widgets.option_list import Option

from repl_client.core.client import LangGraphClient
from repl_client.core.config import Config
from repl_client.core.logging import get_logger
from repl_client.core.session import SessionState
from repl_client.streaming.handler import StreamHandler
from repl_client.streaming.types import ChunkType
from repl_client.tui.hitl import HITLHandler
from repl_client.tui.widgets import (
    AssistantMessage,
    ChatInput,
    LoadingWidget,
    Sidebar,
    StatusArea,
    ToolCallMessage,
    UserMessage,
)

if TYPE_CHECKING:
    from textual.widgets import Static

logger = get_logger("tui.app")


class AgentSelectionScreen(ModalScreen[str | None]):
    """Modal screen for selecting an agent."""

    def __init__(self, agents: list[dict], current_agent_id: str):
        super().__init__()
        self.agents = agents
        self.current_agent_id = current_agent_id

    def compose(self) -> ComposeResult:
        """Compose the selection screen."""
        yield Label("Select Agent (Enter to confirm, Esc to cancel)")

        # Build options
        options = []
        for agent in self.agents:
            agent_id = agent.get("assistant_id", "")
            graph_id = agent.get("graph_id", "")
            is_current = " ✓" if agent_id == self.current_agent_id else ""

            options.append(
                Option(
                    f"{graph_id}{is_current}",
                    id=agent_id
                )
            )

        yield OptionList(*options, id="agent-list")

    def on_mount(self) -> None:
        """Focus the option list on mount."""
        self.query_one("#agent-list", OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle agent selection."""
        self.dismiss(event.option.id)

    def on_key(self, event) -> None:
        """Handle escape to cancel."""
        if event.key == "escape":
            self.dismiss(None)


class ThreadSelectionScreen(ModalScreen[str | None]):
    """Modal screen for selecting a thread."""

    def __init__(self, threads: list[dict], current_thread_id: str):
        super().__init__()
        self.threads = threads
        self.current_thread_id = current_thread_id

    def compose(self) -> ComposeResult:
        """Compose the selection screen."""
        yield Label("Select Thread (Enter to confirm, Esc to cancel, N for new)")

        # Build options
        options = [Option("+ New Thread", id="__new__")]

        for thread in self.threads:
            thread_id = thread.get("thread_id", "")
            created = thread.get("created_at", "")
            is_current = " ✓" if thread_id == self.current_thread_id else ""

            # Format: "thread-id... (created time) ✓"
            display = f"{thread_id[:16]}... ({created[:10]}){is_current}"
            options.append(Option(display, id=thread_id))

        yield OptionList(*options, id="thread-list")

    def on_mount(self) -> None:
        """Focus the option list on mount."""
        self.query_one("#thread-list", OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle thread selection."""
        self.dismiss(event.option.id)

    def on_key(self, event) -> None:
        """Handle escape to cancel."""
        if event.key == "escape":
            self.dismiss(None)


class REPLApp(App[None]):
    """Main REPL TUI application.

    Features:
    - Connect to LangGraph server
    - Stream messages with real-time rendering
    - Handle HITL interrupts
    - Display user/AI/tool messages
    - Status bar with connection/agent info

    Key bindings:
    - Ctrl+C: Quit
    - Ctrl+L: Clear messages
    """

    CSS_PATH = "repl.tcss"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+l", "clear_messages", "Clear", show=True),
        Binding("f2", "select_agent", "Agents", show=True),
        Binding("f3", "select_thread", "Threads", show=True),
        Binding("f4", "toggle_sidebar", "Sidebar", show=True),
        Binding("f5", "expand_sidebar", "Expand", show=True),
    ]

    def __init__(
        self,
        config: Config | None = None,
        **kwargs,
    ):
        """Initialize REPL app.

        Args:
            config: Configuration object (defaults to Config.from_env())
            **kwargs: Additional arguments for App
        """
        super().__init__(**kwargs)
        self.config = config or Config.from_env()

        # Core components
        self.client = LangGraphClient(
            base_url=self.config.server_url,
            timeout=30,
        )
        self.session = SessionState()
        self.stream_handler = StreamHandler(self.session)
        self.hitl_handler = HITLHandler(app=self)

        # Widget references (set in on_mount)
        self._status_area: StatusArea | None = None
        self._chat_input: ChatInput | None = None
        self._messages_container: ScrollableContainer | None = None
        self._sidebar: Sidebar | None = None

        # State
        self._streaming = False
        self._agents: list[dict] = []
        self._threads_cache: list[dict] = []

    def compose(self) -> ComposeResult:
        """Compose the app layout.

        Layout from top to bottom:
        - Header (docked top)
        - Horizontal container with:
          - Messages (scrollable, fills remaining space)
          - Sidebar (toggleable, hidden by default)
        - ChatInput (multi-line, auto-height)
        - StatusArea (2 lines, shows agent/thread/tokens + connection)
        - Footer (docked bottom, shows key bindings)
        """
        yield Header()
        with Horizontal(id="main-content"):
            yield ScrollableContainer(id="messages")
            yield Sidebar(id="sidebar")
        yield ChatInput(
            cwd=Path.cwd(),
            history_file=Path.cwd() / ".repl" / "history.jsonl",
        )
        yield StatusArea()
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize after mounting."""
        # Cache widget references
        self._status_area = self.query_one(StatusArea)
        self._chat_input = self.query_one(ChatInput)
        self._messages_container = self.query_one("#messages", ScrollableContainer)
        self._sidebar = self.query_one("#sidebar", Sidebar)

        # Start connection and setup
        self._startup()

    @work(exclusive=True)
    async def _startup(self) -> None:
        """Connect to server, load agents, create thread, update status."""
        # Update status
        if self._status_area:
            self._status_area.set_status("Connecting to server...")

        # Connect to server
        try:
            connected = await self.client.connect()
            if not connected:
                if self._status_area:
                    self._status_area.set_status("Connection failed", error=True)
                logger.error("Failed to connect to server")
                return

            if self._status_area:
                self._status_area.set_status("Loading agents...")

            # List agents
            self._agents = await self.client.list_agents(limit=10)
            if not self._agents:
                if self._status_area:
                    self._status_area.set_status("No agents available", error=True)
                logger.error("No agents available")
                return

            # Set default agent (first one or from config)
            default_agent = None
            if self.config.default_agent:
                # Find agent by ID
                for agent in self._agents:
                    if agent.get("assistant_id") == self.config.default_agent:
                        default_agent = agent
                        break

            if not default_agent:
                default_agent = self._agents[0]

            agent_id = default_agent.get("assistant_id", "")
            agent_name = default_agent.get("name", agent_id)
            self.session.set_agent(agent_id)

            if self._status_area:
                self._status_area.set_status(f"Creating thread...")

            # Create initial thread
            thread_id = await self.client.create_thread()
            self.session.set_thread(thread_id)

            # Update status bar
            if self._status_area:
                self._status_area.set_agent(agent_name)
                self._status_area.set_thread(thread_id[:8])  # Show first 8 chars
                self._status_area.set_status("Ready", error=False)

            logger.info(f"Connected to server, agent={agent_name}, thread={thread_id}")

        except Exception as e:
            logger.exception("Startup failed")
            if self._status_area:
                self._status_area.set_status(f"Startup failed: {e}", error=True)

    async def on_chat_input_submitted(self, message: ChatInput.Submitted) -> None:
        """Handle user input submission.

        Args:
            message: Submitted message event
        """
        user_text = message.value

        # Handle commands (start with /)
        if message.mode == "command":
            await self._handle_command(user_text)
            return

        # Handle normal messages
        # Note: _send_message is decorated with @work, returns Worker (not awaitable)
        self._send_message(user_text)

    async def _handle_command(self, command: str) -> None:
        """Handle slash commands.

        Args:
            command: Command string (includes leading /)
        """
        cmd = command.lower().strip()

        if cmd == "/help":
            await self._show_help()
        elif cmd == "/clear":
            self.action_clear_messages()
        elif cmd == "/agents":
            await self._list_agents()
        elif cmd.startswith("/agents "):
            # Switch agent
            agent_id = command.split(maxsplit=1)[1].strip()
            await self._switch_agent(agent_id)
        elif cmd == "/new":
            await self._new_thread()
        elif cmd == "/info":
            await self._show_info()
        else:
            # Unknown command
            if self._messages_container:
                error_msg = UserMessage(f"Unknown command: {cmd}")
                await self._messages_container.mount(error_msg)

    async def _show_help(self) -> None:
        """Show help message."""
        help_text = """Available commands:
/help          - Show this help
/clear         - Clear message history
/agents        - List available agents
/agents <id>   - Switch to agent
/new           - Create new thread
/info          - Show session info"""

        if self._messages_container:
            msg = UserMessage(help_text)
            await self._messages_container.mount(msg)

    async def _list_agents(self) -> None:
        """List available agents."""
        if not self._agents:
            if self._messages_container:
                msg = UserMessage("No agents available")
                await self._messages_container.mount(msg)
            return

        agent_list = "Available agents:\n"
        for agent in self._agents:
            agent_id = agent.get("assistant_id", "")
            agent_name = agent.get("name", agent_id)
            current = " (current)" if agent_id == self.session.current_assistant_id else ""
            agent_list += f"  - {agent_name} [{agent_id}]{current}\n"

        if self._messages_container:
            msg = UserMessage(agent_list)
            await self._messages_container.mount(msg)

    async def _switch_agent(self, agent_id: str) -> None:
        """Switch to a different agent.

        Args:
            agent_id: Agent ID to switch to
        """
        # Find agent
        agent = None
        for a in self._agents:
            if a.get("assistant_id") == agent_id:
                agent = a
                break

        if not agent:
            if self._messages_container:
                msg = UserMessage(f"Agent not found: {agent_id}")
                await self._messages_container.mount(msg)
            return

        agent_name = agent.get("name", agent_id)
        self.session.set_agent(agent_id)

        if self._status_area:
            self._status_area.set_agent(agent_name)

        if self._messages_container:
            msg = UserMessage(f"Switched to agent: {agent_name}")
            await self._messages_container.mount(msg)

    async def _new_thread(self) -> None:
        """Create a new thread."""
        try:
            thread_id = await self.client.create_thread()
            self.session.set_thread(thread_id)

            if self._status_area:
                self._status_area.set_thread(thread_id[:8])

            if self._messages_container:
                msg = UserMessage(f"Created new thread: {thread_id}")
                await self._messages_container.mount(msg)

            logger.info(f"Created new thread: {thread_id}")
        except Exception as e:
            logger.exception("Failed to create thread")
            if self._messages_container:
                msg = UserMessage(f"Failed to create thread: {e}")
                await self._messages_container.mount(msg)

    async def _show_info(self) -> None:
        """Show session info."""
        tokens = self.session.get_token_summary()
        info = f"""Session info:
Thread: {self.session.current_thread_id}
Agent: {self.session.current_assistant_id}
Tokens: {tokens['total']} (in: {tokens['input']}, out: {tokens['output']})"""

        if self._messages_container:
            msg = UserMessage(info)
            await self._messages_container.mount(msg)

    @work(exclusive=True)
    async def _send_message(self, text: str) -> None:
        """Send message to agent and stream response.

        Args:
            text: User message text
        """
        if self._streaming:
            logger.warning("Already streaming, ignoring new message")
            return

        if not self.session.current_thread_id or not self.session.current_assistant_id:
            logger.error("No thread or agent set")
            return

        self._streaming = True

        # Disable input during streaming
        if self._chat_input:
            self._chat_input.set_disabled(disabled=True)

        try:
            # Add user message widget
            user_msg = UserMessage(text)
            if self._messages_container:
                await self._messages_container.mount(user_msg)
                self._messages_container.scroll_end(animate=False)

            # Show loading indicator
            loading = LoadingWidget()
            if self._messages_container:
                await self._messages_container.mount(loading)
                self._messages_container.scroll_end(animate=False)

            # Update status
            if self._status_area:
                self._status_area.set_status("Streaming...")

            # Stream from server
            chunks = self.client.stream_message(
                thread_id=self.session.current_thread_id,
                message=text,
                assistant_id=self.session.current_assistant_id,
            )

            # Create assistant message (empty initially)
            ai_msg = AssistantMessage()
            if self._messages_container:
                await self._messages_container.mount(ai_msg)

            # Remove loading widget
            await loading.remove()

            # Process stream
            await self._handle_stream(chunks, ai_msg)

            # Finalize assistant message
            await ai_msg.stop_stream()

            # Update status
            if self._status_area:
                self._status_area.set_status("Ready")

        except Exception as e:
            logger.exception("Failed to send message")
            if self._status_area:
                self._status_area.set_status(f"Error: {e}", error=True)
        finally:
            self._streaming = False
            if self._chat_input:
                self._chat_input.set_disabled(disabled=False)
                self._chat_input.focus_input()

    async def _handle_stream(
        self,
        chunks,
        ai_msg: AssistantMessage,
    ) -> None:
        """Process stream chunks and update widgets.

        Args:
            chunks: AsyncIterator of (event_type, data) tuples
            ai_msg: Assistant message widget to update
        """
        current_tool_msg: ToolCallMessage | None = None

        async for parsed in self.stream_handler.process_stream(chunks):
            # Handle text deltas
            if parsed.chunk_type == ChunkType.TEXT_DELTA and parsed.text_delta:
                await ai_msg.append_content(parsed.text_delta)
                if self._messages_container:
                    self._messages_container.scroll_end(animate=False)

            # Handle complete tool calls
            elif parsed.chunk_type == ChunkType.TOOL_CALL_COMPLETE and parsed.tool_call:
                tool_call = parsed.tool_call
                tool_msg = ToolCallMessage(
                    tool_name=tool_call.name,
                    args=tool_call.args,
                )
                if self._messages_container:
                    await self._messages_container.mount(tool_msg)
                    self._messages_container.scroll_end(animate=False)
                current_tool_msg = tool_msg

            # Handle tool results
            elif parsed.chunk_type == ChunkType.TOOL_RESULT and parsed.tool_result:
                # Update the current tool message with result
                if current_tool_msg:
                    result = parsed.tool_result.result
                    if parsed.tool_result.status == "error":
                        current_tool_msg.set_error(result)
                    else:
                        current_tool_msg.set_success(result)
                    current_tool_msg = None

            # Handle interrupts (HITL)
            elif parsed.chunk_type == ChunkType.INTERRUPT and parsed.interrupt:
                await self._handle_interrupt(parsed.interrupt, ai_msg)

            # Handle usage metadata
            elif parsed.chunk_type == ChunkType.USAGE and parsed.usage:
                self.session.track_tokens(
                    parsed.usage.input_tokens,
                    parsed.usage.output_tokens,
                )
                if self._status_area:
                    tokens = self.session.get_token_summary()
                    self._status_area.set_tokens(tokens["total"])

    async def _handle_interrupt(self, interrupt, ai_msg: AssistantMessage) -> None:
        """Handle HITL interrupt.

        Args:
            interrupt: Interrupt object
            ai_msg: Current assistant message
        """
        # Show approval prompt via HITL handler
        approved = await self.hitl_handler.handle_interrupt(interrupt, self.session)

        # Build resume command
        command = {"resume": {"approve": approved}}

        # Resume stream with approval decision
        if self.session.current_thread_id and self.session.current_assistant_id:
            chunks = self.client.resume_after_interrupt(
                thread_id=self.session.current_thread_id,
                assistant_id=self.session.current_assistant_id,
                command=command,
            )
            # Continue streaming
            await self._handle_stream(chunks, ai_msg)

    def action_clear_messages(self) -> None:
        """Clear all messages from the container."""
        if self._messages_container:
            self._messages_container.remove_children()
            logger.info("Cleared message history")

    async def action_select_agent(self) -> None:
        """Show agent selection screen."""
        if not self._agents:
            # Load agents if not cached
            try:
                self._agents = await self.client.list_agents()
            except Exception as e:
                logger.error(f"Failed to load agents: {e}")
                return

        # Show selection screen
        result = await self.push_screen(
            AgentSelectionScreen(self._agents, self.session.current_assistant_id)
        )

        if result:
            # User selected an agent
            self.session.set_agent(result)
            if self._status_area:
                # Extract graph_id for display
                agent = next((a for a in self._agents if a.get("assistant_id") == result), None)
                display_name = agent.get("graph_id", result[:8]) if agent else result[:8]
                self._status_area.set_agent(display_name)
            logger.info(f"Switched to agent: {result}")

    async def action_select_thread(self) -> None:
        """Show thread selection screen."""
        try:
            threads = await self.client.list_threads(limit=20)
            self._threads_cache = threads  # Cache for sidebar
        except Exception as e:
            logger.error(f"Failed to load threads: {e}")
            return

        # Show selection screen
        result = await self.push_screen(
            ThreadSelectionScreen(threads, self.session.current_thread_id or "")
        )

        if result:
            if result == "__new__":
                # Create new thread
                try:
                    new_thread_id = await self.client.create_thread()
                    self.session.set_thread(new_thread_id)
                    if self._status_area:
                        self._status_area.set_thread(new_thread_id[:8])
                    logger.info(f"Created new thread: {new_thread_id}")

                    # Clear messages for new thread
                    self.action_clear_messages()
                except Exception as e:
                    logger.error(f"Failed to create thread: {e}")
            else:
                # Resume existing thread
                self.session.set_thread(result)
                if self._status_area:
                    self._status_area.set_thread(result[:8])
                logger.info(f"Switched to thread: {result}")

                # Clear messages when switching threads
                self.action_clear_messages()

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        if self._sidebar:
            self._sidebar.toggle()

            # Update sidebar content when shown
            if self._sidebar.visible:
                self._update_sidebar_content()

    def action_expand_sidebar(self) -> None:
        """Toggle expanded sidebar mode."""
        if self._sidebar:
            self._sidebar.expand()

            # Update sidebar content when shown
            if self._sidebar.visible:
                self._update_sidebar_content()

    def _update_sidebar_content(self) -> None:
        """Update sidebar with current session data."""
        if not self._sidebar:
            return

        # Update threads tab
        self._sidebar.populate_threads(
            self._threads_cache,
            self.session.current_thread_id or "",
        )

        # Update agents tab
        self._sidebar.populate_agents(
            self._agents,
            self.session.current_assistant_id or "",
        )

        # Update session info tab
        tokens = self.session.get_token_summary()
        self._sidebar.populate_session_info(
            thread_id=self.session.current_thread_id or "(none)",
            agent_id=self.session.current_assistant_id or "(none)",
            tokens=tokens,
        )

        # Update tools tab (placeholder - need to track tool calls)
        self._sidebar.populate_tools([])

    async def action_quit(self) -> None:
        """Quit the application."""
        logger.info("Quitting REPL")
        self.exit()
