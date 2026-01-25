"""Main Textual TUI application for REPL client - WITH CONTROLLERS.

Architecture (Phase 3 refactor):
- Controllers: Business logic (MessageController, SessionController, CommandController, InterruptController)
- Services: External integrations (LangGraphService, StreamService)
- Views: Presentational components (LayoutView, MessageAreaView, etc.)
- App: Event routing only
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import Label, OptionList
from textual.widgets.option_list import Option

from repl_client.core.client import LangGraphClient
from repl_client.core.config import Config
from repl_client.core.logging import get_logger
from repl_client.core.session import SessionState
from repl_client.streaming.handler import StreamHandler
from repl_client.tui.controllers import (
    CommandController,
    InterruptController,
    MessageController,
    SessionController,
)
from repl_client.tui.hitl import HITLHandler
from repl_client.tui.models import AppState
from repl_client.tui.screens import AgentConfigScreen, WelcomeScreen
from repl_client.tui.services import LangGraphService, StreamService
from repl_client.tui.views import LayoutView, MessageAreaView, SidebarView, StatusAreaView
from repl_client.tui.widgets import ChatInput, Command, CommandPalette

if TYPE_CHECKING:
    pass

logger = get_logger("tui.app")


class AgentSelectionScreen(ModalScreen[str | None]):
    """Modal screen for selecting an agent."""

    def __init__(self, agents: list[dict], current_agent_id: str):
        super().__init__()
        self.agents = agents
        self.current_agent_id = current_agent_id

    def compose(self) -> ComposeResult:
        """Compose the selection screen."""
        with Container():
            yield Label("Select Agent (Enter to confirm, Esc to cancel)")

            # Build options
            options = []
            for agent in self.agents:
                agent_id = agent.get("assistant_id", "")
                graph_id = agent.get("graph_id", "")
                is_current = " ✓" if agent_id == self.current_agent_id else ""

                options.append(Option(f"{graph_id}{is_current}", id=agent_id))

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
        with Container():
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

    Responsibilities (after Phase 3 refactor):
    - Event routing (user input → controllers)
    - UI coordination (modals, key bindings)
    - Component initialization
    - NO business logic (delegated to controllers)

    Key bindings:
    - Ctrl+C: Quit
    - Ctrl+L: Clear messages
    - Ctrl+D: Toggle light/dark mode
    - F2: Agent selection
    - F3: Thread selection
    """

    # CSS loaded from concatenated modular files (see styles/README.md)
    # Build with: cat theme.tcss layout.tcss components.tcss sidebar.tcss modals.tcss states.tcss light-mode.tcss > index.tcss
    CSS_PATH = "styles/index.tcss"
    ENABLE_COMMAND_PALETTE = False  # Disable Textual's built-in (we use custom)

    # Start in dark mode (Carbon Gray 100 theme)
    dark: reactive[bool] = reactive(True)

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("ctrl+c", "quit", "Quit", show=True),
        Binding("ctrl+p", "show_command_palette", "Commands", show=True),  # Our custom palette
        Binding("f4", "toggle_sidebar", "Sidebar", show=True),
        Binding("ctrl+l", "clear_messages", "Clear", show=True),
        Binding("ctrl+d", "toggle_dark", "Light/Dark", show=True),
        Binding("f2", "select_agent", "Agents", show=True),
        Binding("f3", "select_thread", "Threads", show=False),
        Binding("f5", "expand_sidebar", "Expand", show=False),
        Binding("f6", "show_agent_config", "Config", show=True),
        Binding("ctrl+b", "focus_sidebar", "Focus Sidebar", show=False),
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

        # Centralized reactive state (NEW - Phase 5)
        self.app_state = AppState()
        self.app_state.set_connection(False, self.config.server_url)

        # Core components
        self.client = LangGraphClient(
            base_url=self.config.server_url,
            timeout=30,
        )
        self.session = SessionState()
        self.stream_handler = StreamHandler(self.session)
        self.hitl_handler = HITLHandler(app=self)

        # Services
        self.langgraph_service = LangGraphService(self.client)
        self.stream_service = StreamService(self.stream_handler)

        # Controllers (Phase 3) with AppState (Phase 5)
        self.session_controller = SessionController(
            self.langgraph_service, self.session, self.app_state
        )
        self.command_controller = CommandController(
            self.langgraph_service, self.session, self.session_controller
        )

        # Message and Interrupt controllers have circular dependency, create them together
        self.interrupt_controller = InterruptController(
            self.langgraph_service, self.stream_service, self.hitl_handler, self.session
        )
        self.message_controller = MessageController(
            self.langgraph_service,
            self.stream_service,
            self.session,
            self.interrupt_controller,
            self.app_state,
        )

        # Set circular references
        self.interrupt_controller.set_message_controller(self.message_controller)
        self.message_controller.set_interrupt_controller(self.interrupt_controller)

        # View references (set in on_mount)
        self._layout: LayoutView | None = None
        self._status_area: StatusAreaView | None = None
        self._chat_input: ChatInput | None = None
        self._message_area: MessageAreaView | None = None
        self._sidebar: SidebarView | None = None

    def compose(self) -> ComposeResult:
        """Compose the app layout using LayoutView."""
        yield LayoutView(
            cwd=Path.cwd(),
            history_file=Path.cwd() / ".repl" / "history.jsonl",
        )

    async def on_mount(self) -> None:
        """Initialize after mounting."""
        # Cache view references
        self._layout = self.query_one(LayoutView)
        self._status_area = self._layout.get_status_area()
        self._chat_input = self._layout.get_chat_input()
        self._message_area = self._layout.get_message_area()
        self._sidebar = self._layout.get_sidebar()

        # Start connection and setup
        self._startup()

    @work(exclusive=True)
    async def _startup(self) -> None:
        """Connect to server, load agents, create thread, update status."""
        self.app_state.set_status("Connecting to server...")

        try:
            connected = await self.client.connect()
            if not connected:
                self.app_state.set_status("Connection failed", error=True)
                self.app_state.set_connection(False, self.config.server_url)
                if self._status_area:
                    self._status_area.update_connection_status(False, self.config.server_url)
                logger.error("Failed to connect to server")
                return

            self.app_state.set_connection(True, self.config.server_url)
            if self._status_area:
                self._status_area.update_connection_status(True, self.config.server_url)
            self.app_state.set_status("Loading agents...")

            # List agents via service
            agents = await self.langgraph_service.get_agents(limit=10)
            if not agents:
                self.app_state.set_status("No agents available", error=True)
                logger.error("No agents available")
                return

            # Update app state with agents list
            self.app_state.update_agents_cache(agents)

            # Set default agent
            default_agent = None
            if self.config.default_agent:
                for agent in agents:
                    if agent.get("assistant_id") == self.config.default_agent:
                        default_agent = agent
                        break

            if not default_agent:
                default_agent = agents[0]

            agent_id = default_agent.get("assistant_id", "")
            agent_name = default_agent.get("graph_id") or default_agent.get("name", agent_id)

            # Update state (both legacy and new)
            self.session.set_agent(agent_id)
            self.app_state.set_agent(agent_id, agent_name)

            self.app_state.set_status("Creating thread...")

            # Create initial thread via SessionController to handle caching
            create_result = await self.session_controller.create_thread()

            if not create_result["success"]:
                self.app_state.set_status("Failed to create thread", error=True)
                logger.error(f"Failed to create thread: {create_result['message']}")
                return

            thread_id = create_result["thread_id"]

            # Update status bar (still needed for immediate UI update)
            if self._status_area:
                self._status_area.set_agent(agent_name)
                self._status_area.set_thread(thread_id[:8])

            self.app_state.set_status("Ready - Press Ctrl+P for commands", error=False)

            logger.info(f"Connected to server, agent={agent_name}, thread={thread_id}")

            # Show welcome modal
            await self._show_welcome()

        except Exception as e:
            logger.exception("Startup failed")
            self.app_state.set_status(f"Startup failed: {e}", error=True)

    async def on_chat_input_submitted(self, message: ChatInput.Submitted) -> None:
        """Route user input to appropriate controller.

        Args:
            message: Submitted message event
        """
        user_text = message.value

        # Route commands to CommandController
        if message.mode == "command":
            await self._handle_command_routing(user_text)
            return

        # Route messages to MessageController
        self._send_message(user_text)

    async def _handle_command_routing(self, command: str) -> None:
        """Route command to CommandController and display result.

        Args:
            command: Command string (includes leading /)
        """
        # Special case: /clear clears UI directly
        if command.lower().strip() == "/clear":
            self.action_clear_messages()
            return

        # Execute command via controller
        result_message = await self.command_controller.execute_command(command)

        # Display result via view
        if self._message_area and result_message and not result_message.startswith("("):
            await self._message_area.add_user_message(result_message)

    @work(exclusive=True)
    async def _send_message(self, text: str) -> None:
        """Delegate message sending to MessageController.

        Args:
            text: User message text
        """
        if self.app_state.streaming:
            logger.warning("Already streaming, ignoring new message")
            return

        if not self.session.current_thread_id or not self.session.current_assistant_id:
            logger.error("No thread or agent set")
            return

        self.app_state.streaming = True

        # Disable input during streaming
        if self._chat_input:
            self._chat_input.set_disabled(disabled=True)

        try:
            # Delegate to MessageController
            if self._message_area:
                await self.message_controller.send_message(
                    text,
                    self._message_area,  # MessageAreaView IS the ScrollableContainer
                    self._status_area,
                )

        except Exception as e:
            logger.exception("Failed to send message")
            self.app_state.set_status(f"Error: {e}", error=True)
        finally:
            self.app_state.streaming = False
            if self._chat_input:
                self._chat_input.set_disabled(disabled=False)
                self._chat_input.focus_input()

    def action_clear_messages(self) -> None:
        """Clear all messages from the container."""
        if self._message_area:
            self._message_area.remove_children()
            logger.info("Cleared message history")

    def action_toggle_dark(self) -> None:
        """Toggle between light and dark mode."""
        self.dark = not self.dark
        mode = "dark" if self.dark else "light"
        logger.info(f"Switched to {mode} mode")
        self.app_state.set_status(f"Switched to {mode} mode")

    async def action_select_agent(self) -> None:
        """Show agent selection modal and delegate switching to SessionController."""
        try:
            # Force refresh to get latest agents
            agents = await self.langgraph_service.get_agents(force_refresh=True)
            # Update app_state cache
            self.app_state.update_agents_cache(agents)
        except Exception as e:
            logger.error(f"Failed to load agents: {e}")
            return

        # Show selection screen
        result = await self.push_screen(
            AgentSelectionScreen(agents, self.session.current_assistant_id)
        )

        if result:
            # Delegate to SessionController
            switch_result = await self.session_controller.switch_agent(result)

            if switch_result["success"] and self._status_area:
                self._status_area.set_agent(switch_result["display_name"])
                logger.info(f"Switched to agent: {result}")
                # Update sidebar to show current agent
                self._update_sidebar_content()
            else:
                logger.error(f"Failed to switch agent: {switch_result['message']}")

    async def action_select_thread(self) -> None:
        """Show thread selection modal and delegate to SessionController."""
        try:
            # Force refresh to get latest threads
            threads = await self.langgraph_service.get_threads(limit=20, force_refresh=True)
            # Update app_state cache
            self.app_state.update_threads_cache(threads)
        except Exception as e:
            logger.error(f"Failed to load threads: {e}")
            return

        # Show selection screen
        result = await self.push_screen(
            ThreadSelectionScreen(threads, self.session.current_thread_id or "")
        )

        if result:
            if result == "__new__":
                # Delegate to SessionController
                create_result = await self.session_controller.create_thread()
                if create_result["success"]:
                    if self._status_area:
                        self._status_area.set_thread(create_result["thread_id"][:8])
                    logger.info(f"Created new thread: {create_result['thread_id']}")
                    self.action_clear_messages()
                    # Update sidebar to show new thread
                    self._update_sidebar_content()
                else:
                    logger.error(f"Failed to create thread: {create_result['message']}")
            else:
                # Delegate to SessionController
                switch_result = await self.session_controller.switch_thread(result)
                if switch_result["success"]:
                    if self._status_area:
                        self._status_area.set_thread(result[:8])
                    logger.info(f"Switched to thread: {result}")
                    self.action_clear_messages()
                    # Update sidebar to show current thread
                    self._update_sidebar_content()
                else:
                    logger.error(f"Failed to switch thread: {switch_result['message']}")

    async def action_show_agent_config(self) -> None:
        """Show agent configuration modal with agent selector and schema viewer."""
        logger.info("action_show_agent_config called")

        current_agent_id = self.session.current_assistant_id or ""
        logger.debug(f"Current assistant_id from session: {current_agent_id}")

        # Fetch agents list (use cache if available)
        try:
            agents = await self.langgraph_service.get_agents()
            logger.debug(f"Found {len(agents)} agents for config screen")
        except Exception as e:
            logger.exception("Failed to load agents for config screen")
            self.app_state.set_status(f"Failed to load agents: {e}", error=True)
            return

        if not agents:
            logger.error("No agents available")
            self.app_state.set_status("No agents available", error=True)
            return

        self.app_state.set_status("Ready")

        # Show config screen with agent selector
        logger.info(f"Pushing AgentConfigScreen with {len(agents)} agents, current={current_agent_id}")
        result = await self.push_screen(
            AgentConfigScreen(agents, current_agent_id, self.langgraph_service)
        )

        if result:
            # Handle any returned action (future: create assistant)
            logger.info(f"Agent config result: {result}")

    async def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        if self._sidebar:
            self._sidebar.toggle()
            self.app_state.sidebar_visible = self._sidebar.visible
            if self._sidebar.visible:
                # Refresh data when opening sidebar
                await self._refresh_sidebar_data()
                self._update_sidebar_content()

    async def action_expand_sidebar(self) -> None:
        """Toggle expanded sidebar mode."""
        if self._sidebar:
            self._sidebar.expand()
            self.app_state.sidebar_expanded = not self.app_state.sidebar_expanded
            if self._sidebar.visible:
                # Refresh data when opening sidebar
                await self._refresh_sidebar_data()
                self._update_sidebar_content()

    async def action_focus_sidebar(self) -> None:
        """Focus sidebar and make visible if hidden."""
        if self._sidebar:
            if not self._sidebar.visible:
                self._sidebar.toggle()
                self.app_state.sidebar_visible = True
                # Refresh data when opening sidebar
                await self._refresh_sidebar_data()
                self._update_sidebar_content()
            self._sidebar.focus()

    def _update_sidebar_content(self) -> None:
        """Update sidebar with current session data.

        Uses app_state as single source of truth for consistency.
        """
        if not self._sidebar:
            return

        # Use app_state as single source of truth
        # If empty, sidebar will show "No threads/agents available"
        threads = self.app_state.threads
        agents = self.app_state.agents

        # Update tabs
        self._sidebar.populate_threads(
            threads, self.app_state.current_thread_id or self.session.current_thread_id or ""
        )
        self._sidebar.populate_agents(
            agents, self.app_state.current_agent_id or self.session.current_assistant_id or ""
        )

        tokens = self.session.get_token_summary()
        self._sidebar.populate_session_info(
            thread_id=self.app_state.current_thread_id
            or self.session.current_thread_id
            or "(none)",
            agent_id=self.app_state.current_agent_id
            or self.session.current_assistant_id
            or "(none)",
            tokens=tokens,
        )

        self._sidebar.populate_tools([])

    async def _refresh_sidebar_data(self) -> None:
        """Refresh sidebar data from server.

        Fetches latest agents and threads, updates app_state cache.
        Call this before showing sidebar to ensure data is fresh.
        """
        try:
            # Fetch latest data with force_refresh
            agents = await self.langgraph_service.get_agents(force_refresh=True)
            threads = await self.langgraph_service.get_threads(force_refresh=True)

            # Update app_state cache
            self.app_state.update_agents_cache(agents)
            self.app_state.update_threads_cache(threads)

            logger.debug(f"Refreshed sidebar data: {len(agents)} agents, {len(threads)} threads")
        except Exception as e:
            logger.error(f"Failed to refresh sidebar data: {e}")
            # Continue with stale data rather than crashing

    async def on_sidebar_agent_selected(self, message) -> None:
        """Handle agent selection from sidebar."""
        from repl_client.tui.widgets.sidebar import Sidebar

        if not isinstance(message, Sidebar.AgentSelected):
            return

        # Delegate to SessionController
        switch_result = await self.session_controller.switch_agent(message.agent_id)

        if switch_result["success"] and self._status_area:
            self._status_area.set_agent(switch_result["display_name"])
            logger.info(f"Switched to agent: {message.agent_id}")
            self._update_sidebar_content()
        else:
            logger.error(f"Failed to switch agent: {switch_result['message']}")

    async def on_sidebar_thread_selected(self, message) -> None:
        """Handle thread selection from sidebar."""
        from repl_client.tui.widgets.sidebar import Sidebar

        if not isinstance(message, Sidebar.ThreadSelected):
            return

        # Delegate to SessionController
        switch_result = await self.session_controller.switch_thread(message.thread_id)

        if switch_result["success"] and self._status_area:
            self._status_area.set_thread(message.thread_id[:8])
            logger.info(f"Switched to thread: {message.thread_id}")
            self.action_clear_messages()
            self._update_sidebar_content()
        else:
            logger.error(f"Failed to switch thread: {switch_result['message']}")

    async def on_sidebar_new_thread_requested(self, message) -> None:
        """Handle new thread request from sidebar."""
        from repl_client.tui.widgets.sidebar import Sidebar

        if not isinstance(message, Sidebar.NewThreadRequested):
            return

        # Delegate to SessionController
        create_result = await self.session_controller.create_thread()

        if create_result["success"]:
            if self._status_area:
                self._status_area.set_thread(create_result["thread_id"][:8])
            logger.info(f"Created new thread: {create_result['thread_id']}")
            self.action_clear_messages()
            self._update_sidebar_content()
        else:
            logger.error(f"Failed to create thread: {create_result['message']}")

    async def action_show_command_palette(self) -> None:
        """Show command palette for quick navigation."""
        commands = self._build_command_list()
        result = await self.push_screen(CommandPalette(commands))

        if result:
            # Execute the selected command's action
            try:
                await result.action()
            except Exception as e:
                logger.exception(f"Failed to execute command: {result.id}")
                self.app_state.set_status(f"Command failed: {e}", error=True)

    def _build_command_list(self) -> list[Command]:
        """Build list of available commands for palette.

        Returns:
            List of Command objects
        """
        commands = []

        # Agent operations
        commands.append(
            Command(
                id="agents-list",
                label="List Agents",
                category="Agents",
                description="Show all available agents",
                action=self.action_select_agent,
            )
        )
        commands.append(
            Command(
                id="agents-switch",
                label="Switch Agent",
                category="Agents",
                description="Change current agent (F2)",
                action=self.action_select_agent,
            )
        )
        commands.append(
            Command(
                id="agents-config",
                label="Agent Configuration",
                category="Agents",
                description="View agent context schema (F6)",
                action=self.action_show_agent_config,
            )
        )

        # Thread operations
        commands.append(
            Command(
                id="threads-list",
                label="List Threads",
                category="Threads",
                description="Show all threads",
                action=self.action_select_thread,
            )
        )
        commands.append(
            Command(
                id="threads-switch",
                label="Switch Thread",
                category="Threads",
                description="Change current thread (F3)",
                action=self.action_select_thread,
            )
        )
        commands.append(
            Command(
                id="threads-new",
                label="New Thread",
                category="Threads",
                description="Create new conversation thread",
                action=self._cmd_new_thread,
            )
        )

        # Navigation operations
        commands.append(
            Command(
                id="nav-toggle-sidebar",
                label="Toggle Sidebar",
                category="Navigation",
                description="Show/hide sidebar (F4)",
                action=self._cmd_toggle_sidebar,
            )
        )
        commands.append(
            Command(
                id="nav-expand-sidebar",
                label="Expand Sidebar",
                category="Navigation",
                description="Toggle sidebar width (F5)",
                action=self._cmd_expand_sidebar,
            )
        )
        commands.append(
            Command(
                id="nav-focus-chat",
                label="Focus Chat Input",
                category="Navigation",
                description="Move focus to chat input",
                action=self._cmd_focus_chat,
            )
        )

        # Command operations (slash commands)
        commands.append(
            Command(
                id="cmd-help",
                label="/help",
                category="Commands",
                description="Show help and command list",
                action=self._cmd_help,
            )
        )
        commands.append(
            Command(
                id="cmd-info",
                label="/info",
                category="Commands",
                description="Show session information",
                action=self._cmd_info,
            )
        )
        commands.append(
            Command(
                id="cmd-agents",
                label="/agents",
                category="Commands",
                description="List all agents",
                action=self._cmd_agents,
            )
        )
        commands.append(
            Command(
                id="cmd-threads",
                label="/threads",
                category="Commands",
                description="List all threads",
                action=self._cmd_threads,
            )
        )
        commands.append(
            Command(
                id="cmd-clear",
                label="/clear",
                category="Commands",
                description="Clear message history (Ctrl+L)",
                action=self._cmd_clear,
            )
        )
        commands.append(
            Command(
                id="cmd-session",
                label="/session",
                category="Commands",
                description="Show detailed session state",
                action=self._cmd_session,
            )
        )

        # System operations
        commands.append(
            Command(
                id="sys-toggle-dark",
                label="Toggle Light/Dark Mode",
                category="System",
                description="Switch between light and dark themes (Ctrl+D)",
                action=self._cmd_toggle_dark,
            )
        )
        commands.append(
            Command(
                id="sys-clear-messages",
                label="Clear Messages",
                category="System",
                description="Clear all messages (Ctrl+L)",
                action=self._cmd_clear,
            )
        )
        commands.append(
            Command(
                id="sys-quit",
                label="Quit",
                category="System",
                description="Exit application (Ctrl+C)",
                action=self.action_quit,
            )
        )

        return commands

    # Command action helpers

    async def _cmd_new_thread(self) -> None:
        """Create new thread via session controller."""
        create_result = await self.session_controller.create_thread()
        if create_result["success"]:
            if self._status_area:
                self._status_area.set_thread(create_result["thread_id"][:8])
            logger.info(f"Created new thread: {create_result['thread_id']}")
            self.action_clear_messages()
            # Update sidebar to show new thread
            self._update_sidebar_content()
        else:
            logger.error(f"Failed to create thread: {create_result['message']}")

    async def _cmd_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        await self.action_toggle_sidebar()

    async def _cmd_expand_sidebar(self) -> None:
        """Toggle expanded sidebar."""
        await self.action_expand_sidebar()

    async def _cmd_focus_chat(self) -> None:
        """Focus the chat input."""
        if self._chat_input:
            self._chat_input.focus_input()

    async def _cmd_help(self) -> None:
        """Execute /help command."""
        await self._handle_command_routing("/help")

    async def _cmd_info(self) -> None:
        """Execute /info command."""
        await self._handle_command_routing("/info")

    async def _cmd_agents(self) -> None:
        """Execute /agents command."""
        await self._handle_command_routing("/agents")

    async def _cmd_threads(self) -> None:
        """Execute /threads command."""
        await self._handle_command_routing("/threads")

    async def _cmd_clear(self) -> None:
        """Execute /clear command."""
        self.action_clear_messages()

    async def _cmd_session(self) -> None:
        """Execute /session command."""
        await self._handle_command_routing("/session")

    async def _cmd_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.action_toggle_dark()

    async def _show_welcome(self) -> None:
        """Show welcome modal on startup."""
        result = await self.push_screen(WelcomeScreen())

        if result == "commands":
            # User chose to open command palette
            await self.action_show_command_palette()

    async def action_quit(self) -> None:
        """Quit the application."""
        logger.info("Quitting REPL")
        self.exit()
