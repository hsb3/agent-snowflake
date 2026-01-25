"""Command handlers for REPL (Layer 7).

Implements handlers for all REPL commands:
- Phase 1: help, exit
- Phase 2: agents, threads, new, info
- Phase 3: clear, session (stubs)
"""

from repl_client.commands.registry import CommandRegistry
from repl_client.core.client import LangGraphClient
from repl_client.core.session import SessionState
from repl_client.ui.renderer import Renderer


class CommandHandlers:
    """Handler implementations for all REPL commands.

    Coordinates between client, session, and renderer to execute commands.
    """

    def __init__(self, client: LangGraphClient, session: SessionState, renderer: Renderer):
        """Initialize with dependencies.

        Args:
            client: LangGraphClient for API calls
            session: SessionState for tracking state
            renderer: Renderer for output
        """
        self.client = client
        self.session = session
        self.renderer = renderer
        self._registry: CommandRegistry | None = None
        self._agent_cache: dict[str, str] = {}  # name/graph_id → assistant_id

    def register_all(self, registry: CommandRegistry) -> None:
        """Register all command handlers.

        Args:
            registry: CommandRegistry to register commands with
        """
        self._registry = registry

        # Phase 1 commands
        registry.register(
            name="help",
            handler=self.handle_help,
            description="Show this help message or help for a specific command",
            syntax="help [command]",
        )

        registry.register(
            name="exit",
            handler=self.handle_exit,
            description="Exit the REPL",
            syntax="exit",
        )

        # Phase 2 commands
        registry.register(
            name="agents",
            handler=self.handle_agents,
            description="List available agents or switch to a specific agent\n"
            "  /agents                  - List all agents\n"
            "  /agents <name>           - Switch to agent by name (keeps thread)\n"
            "  /agents <name> --new     - Switch to agent with new thread\n"
            "Examples: /agents agent_enhanced, /agents agent --new",
            syntax="agents [name|uuid] [--new|-n]",
        )

        registry.register(
            name="threads",
            handler=self.handle_threads,
            description="List available threads or resume a specific thread",
            syntax="threads [thread_id]",
        )

        registry.register(
            name="new",
            handler=self.handle_new,
            description="Create a new thread",
            syntax="new",
        )

        registry.register(
            name="info",
            handler=self.handle_info,
            description="Show current session information",
            syntax="info",
        )

        # Phase 3 stubs
        registry.register(
            name="clear",
            handler=self.handle_clear,
            description="Clear the screen",
            syntax="clear",
        )

        registry.register(
            name="session",
            handler=self.handle_session,
            description="Show full session state dump (debug)",
            syntax="session",
        )

    # Phase 1 Commands

    def handle_help(self, args: list[str]) -> None:
        """Show help text.

        Args:
            args: Optional command name to get help for
        """
        if not self._registry:
            self.renderer.render_error("Command registry not initialized")
            return

        if args:
            # Show help for specific command
            cmd_name = args[0]
            cmd = self._registry.get_command(cmd_name)
            if cmd:
                syntax = cmd.syntax if cmd.syntax else cmd.name
                help_text = f"/{syntax}\n\n{cmd.description}"
                self.renderer.render_panel(help_text, f"Help: /{cmd_name}")
            else:
                self.renderer.render_error(f"Unknown command: {cmd_name}")
        else:
            # Show all commands
            help_text = self._registry.get_help_text()
            self.renderer.render_panel(help_text, "Available Commands")

    def handle_exit(self, args: list[str]) -> bool:
        """Exit the REPL.

        Args:
            args: Unused

        Returns:
            False to signal exit
        """
        self.renderer.render_success("Goodbye!")
        return False

    # Phase 2 Commands

    async def handle_agents(self, args: list[str]) -> None:
        """List or switch agents.

        Args:
            args: Optional agent_id/name to switch to, with optional --new flag
        """
        if args:
            # Parse arguments
            agent_identifier = args[0]
            create_new_thread = "--new" in args or "-n" in args

            # Resolve name to UUID if needed (check cache first)
            agent_id = await self._resolve_agent_id(agent_identifier)
            if not agent_id:
                self.renderer.render_error(
                    f"Agent not found: {agent_identifier}\nUse /agents to see available agents"
                )
                return

            # Switch to specified agent
            self.session.set_agent(agent_id)

            # Optionally create new thread
            if create_new_thread:
                try:
                    new_thread_id = await self.client.create_thread()
                    self.session.set_thread(new_thread_id)
                    self.renderer.render_success(
                        f"Switched to agent: {agent_identifier}\n"
                        f"Created new thread: {new_thread_id}"
                    )
                except Exception as e:
                    self.renderer.render_error(f"Failed to create new thread: {e}")
            else:
                self.renderer.render_success(f"Switched to agent: {agent_identifier}")
        else:
            # List all agents and populate cache
            try:
                agents = await self.client.list_agents()
                if not agents:
                    self.renderer.render_text("No agents available", style="yellow")
                    return

                # Populate cache: graph_id → assistant_id, name → assistant_id
                for agent in agents:
                    assistant_id = agent.get("assistant_id", "")
                    graph_id = agent.get("graph_id", "")
                    name = agent.get("name", "")

                    if graph_id:
                        self._agent_cache[graph_id] = assistant_id
                    if name and name != graph_id:
                        self._agent_cache[name] = assistant_id

                # Build table with graph_id (more readable than UUID)
                headers = ["Name (use this)", "Assistant ID", "Current"]
                rows = []
                for agent in agents:
                    graph_id = agent.get("graph_id", "unknown")
                    assistant_id = agent.get("assistant_id", "unknown")
                    is_current = "✓" if assistant_id == self.session.current_assistant_id else ""
                    rows.append([graph_id, assistant_id[:8] + "...", is_current])

                self.renderer.render_table(headers, rows)
            except Exception as e:
                self.renderer.render_error(f"Failed to list agents: {e}")

    async def _resolve_agent_id(self, identifier: str) -> str | None:
        """Resolve agent name/graph_id to assistant_id UUID.

        Args:
            identifier: Can be assistant_id (UUID) or graph_id/name

        Returns:
            assistant_id UUID or None if not found
        """
        # If it looks like a UUID, use it directly
        if "-" in identifier and len(identifier) > 30:
            return identifier

        # Check cache first
        if identifier in self._agent_cache:
            return self._agent_cache[identifier]

        # Cache miss - fetch agents and populate cache
        try:
            agents = await self.client.list_agents()
            for agent in agents:
                assistant_id = agent.get("assistant_id", "")
                graph_id = agent.get("graph_id", "")
                name = agent.get("name", "")

                if graph_id:
                    self._agent_cache[graph_id] = assistant_id
                if name and name != graph_id:
                    self._agent_cache[name] = assistant_id

            # Try lookup again
            return self._agent_cache.get(identifier)
        except Exception:
            return None

    async def handle_threads(self, args: list[str]) -> None:
        """List or resume threads.

        Args:
            args: Optional thread_id to resume
        """
        if args:
            # Resume specified thread
            thread_id = args[0]
            self.session.set_thread(thread_id)
            self.renderer.render_success(f"Resumed thread: {thread_id}")
        else:
            # List all threads
            try:
                threads = await self.client.list_threads()
                if not threads:
                    self.renderer.render_text("No threads available", style="yellow")
                    return

                # Build table
                headers = ["Thread ID", "Current"]
                rows = []
                for thread in threads:
                    thread_id = thread.get("thread_id", "unknown")
                    is_current = "✓" if thread_id == self.session.current_thread_id else ""
                    rows.append([thread_id, is_current])

                self.renderer.render_table(headers, rows)
            except Exception as e:
                self.renderer.render_error(f"Failed to list threads: {e}")

    async def handle_new(self, args: list[str]) -> None:
        """Create a new thread.

        Args:
            args: Unused
        """
        try:
            thread_id = await self.client.create_thread()
            self.session.set_thread(thread_id)
            self.renderer.render_success(f"Created new thread: {thread_id}")
        except Exception as e:
            self.renderer.render_error(f"Failed to create thread: {e}")

    def handle_info(self, args: list[str]) -> None:
        """Show session information.

        Args:
            args: Unused
        """
        summary = self.session.get_display_summary()
        self.renderer.render_panel(summary, "Session Info")

    # Phase 3 Stubs

    def handle_clear(self, args: list[str]) -> None:
        """Clear the screen.

        Args:
            args: Unused
        """
        self.renderer.clear()

    def handle_session(self, args: list[str]) -> None:
        """Show full session state dump.

        Args:
            args: Unused
        """
        # Build detailed session dump
        lines = [
            f"Thread ID: {self.session.current_thread_id or 'None'}",
            f"Agent ID: {self.session.current_assistant_id or 'None'}",
            f"Run ID: {self.session.current_run_id or 'None'}",
            "",
            "Token Usage:",
            f"  Input: {self.session.session_tokens['input']}",
            f"  Output: {self.session.session_tokens['output']}",
            f"  Total: {self.session.session_tokens['total']}",
            "",
            f"Namespace State: {len(self.session.namespace_state)} entries",
        ]

        content = "\n".join(lines)
        self.renderer.render_panel(content, "Full Session State")
