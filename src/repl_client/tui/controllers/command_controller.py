"""Command controller for handling slash commands.

Processes slash commands and returns result messages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from repl_client.core.logging import get_logger

if TYPE_CHECKING:
    from repl_client.core.session import SessionState
    from repl_client.tui.controllers.session_controller import SessionController
    from repl_client.tui.services import LangGraphService

logger = get_logger("tui.controllers.command")


class CommandController:
    """Handle slash command execution.

    Responsibilities:
    - Parse and route commands
    - Execute command logic
    - Return result messages for display
    - Coordinate with SessionController for state changes

    Design:
    - Commands return messages instead of rendering
    - Easy to test in isolation
    - Separates command logic from UI
    """

    def __init__(
        self,
        langgraph_service: LangGraphService,
        session: SessionState,
        session_controller: SessionController,
    ):
        """Initialize command controller.

        Args:
            langgraph_service: Service for LangGraph API calls
            session: Session state tracker
            session_controller: Controller for session operations
        """
        self.langgraph = langgraph_service
        self.session = session
        self.session_controller = session_controller

    async def execute_command(self, command: str) -> str:
        """Execute slash command and return result message.

        Args:
            command: Command string (includes leading /)

        Returns:
            Result message to display to user
        """
        cmd = command.lower().strip()

        if cmd == "/help":
            return self._show_help()
        elif cmd == "/clear":
            # Special case - app handles clearing, return message
            return "(clearing messages...)"
        elif cmd == "/agents":
            return await self._list_agents()
        elif cmd.startswith("/agents "):
            # Switch agent
            agent_id = command.split(maxsplit=1)[1].strip()
            return await self._switch_agent(agent_id)
        elif cmd == "/new":
            return await self._new_thread()
        elif cmd == "/info":
            return self._show_info()
        else:
            # Unknown command
            return f"Unknown command: {cmd}\nType /help for available commands"

    def _show_help(self) -> str:
        """Show help message.

        Returns:
            Help text
        """
        return """Available commands:
/help          - Show this help
/clear         - Clear message history
/agents        - List available agents
/agents <id>   - Switch to agent
/new           - Create new thread
/info          - Show session info"""

    async def _list_agents(self) -> str:
        """List available agents.

        Returns:
            Agent list message
        """
        try:
            agents = await self.langgraph.get_agents()
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return f"Failed to list agents: {e}"

        if not agents:
            return "No agents available"

        agent_list = "Available agents:\n"
        for agent in agents:
            agent_id = agent.get("assistant_id", "")
            graph_id = agent.get("graph_id", "")
            agent_name = agent.get("name", agent_id)
            current = " (current)" if agent_id == self.session.current_assistant_id else ""

            # Use graph_id if available, otherwise name
            display = graph_id or agent_name
            agent_list += f"  - {display} [{agent_id[:8]}...]{current}\n"

        return agent_list.rstrip()

    async def _switch_agent(self, agent_id: str) -> str:
        """Switch to a different agent.

        Args:
            agent_id: Agent ID or name to switch to

        Returns:
            Result message
        """
        result = await self.session_controller.switch_agent(agent_id)

        if result["success"]:
            return result["message"]
        else:
            return result["message"]

    async def _new_thread(self) -> str:
        """Create a new thread.

        Returns:
            Result message
        """
        result = await self.session_controller.create_thread()

        if result["success"]:
            thread_id = result["thread_id"]
            return f"Created new thread: {thread_id}"
        else:
            return result["message"]

    def _show_info(self) -> str:
        """Show session info.

        Returns:
            Session info message
        """
        tokens = self.session.get_token_summary()
        info = f"""Session info:
Thread: {self.session.current_thread_id or "(none)"}
Agent: {self.session.current_assistant_id or "(none)"}
Tokens: {tokens["total"]} (in: {tokens["input"]}, out: {tokens["output"]})"""

        return info
