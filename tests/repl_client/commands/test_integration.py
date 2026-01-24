"""Integration tests for command system.

Tests the full command system working together:
registry + handlers + client + session + renderer.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from repl_client.commands.handlers import CommandHandlers
from repl_client.commands.registry import CommandRegistry
from repl_client.core.session import SessionState
from repl_client.ui.renderer import Renderer


@pytest.fixture
def full_system():
    """Setup full command system."""
    # Create mock client
    client = MagicMock()
    client.list_agents = AsyncMock(
        return_value=[
            {"assistant_id": "uuid-agent-1", "graph_id": "agent_1", "name": "Agent 1"},
            {"assistant_id": "uuid-agent-2", "graph_id": "agent_2", "name": "Agent 2"},
        ]
    )
    client.list_threads = AsyncMock(
        return_value=[{"thread_id": "thread-abc"}, {"thread_id": "thread-xyz"}]
    )
    client.create_thread = AsyncMock(return_value="thread-new")

    # Create real components
    session = SessionState()
    renderer = MagicMock(spec=Renderer)
    registry = CommandRegistry()
    handlers = CommandHandlers(client=client, session=session, renderer=renderer)

    # Register all commands
    handlers.register_all(registry)

    return {
        "client": client,
        "session": session,
        "renderer": renderer,
        "registry": registry,
        "handlers": handlers,
    }


class TestCommandSystemIntegration:
    """Test full command system integration."""

    def test_full_workflow(self, full_system):
        """Test typical command workflow."""
        registry = full_system["registry"]
        session = full_system["session"]
        renderer = full_system["renderer"]

        # 1. Start with /help
        registry.execute("help", [])
        renderer.render_panel.assert_called()

        # 2. Show info
        registry.execute("info", [])
        assert renderer.render_panel.call_count == 2

        # 3. Clear screen
        registry.execute("clear", [])
        renderer.clear.assert_called_once()

        # 4. Exit
        result = registry.execute("exit", [])
        assert result is False
        renderer.render_success.assert_called()

    @pytest.mark.asyncio
    async def test_agent_and_thread_workflow(self, full_system):
        """Test agent and thread management workflow."""
        handlers = full_system["handlers"]
        session = full_system["session"]
        renderer = full_system["renderer"]

        # 1. List agents
        await handlers.handle_agents([])
        renderer.render_table.assert_called()

        # 2. Switch agent by graph_id (resolves to UUID)
        await handlers.handle_agents(["agent_2"])
        assert session.current_assistant_id == "uuid-agent-2"

        # 3. Create new thread
        await handlers.handle_new([])
        assert session.current_thread_id == "thread-new"

        # 4. List threads
        await handlers.handle_threads([])
        assert renderer.render_table.call_count == 2

        # 5. Switch thread
        await handlers.handle_threads(["thread-abc"])
        assert session.current_thread_id == "thread-abc"

    def test_all_commands_registered(self, full_system):
        """Test that all expected commands are registered."""
        registry = full_system["registry"]
        commands = registry.list_commands()
        command_names = [cmd.name for cmd in commands]

        # Phase 1
        assert "help" in command_names
        assert "exit" in command_names

        # Phase 2
        assert "agents" in command_names
        assert "threads" in command_names
        assert "new" in command_names
        assert "info" in command_names

        # Phase 3
        assert "clear" in command_names
        assert "session" in command_names

        # Should have exactly 8 commands
        assert len(commands) == 8

    def test_command_descriptions(self, full_system):
        """Test that all commands have descriptions."""
        registry = full_system["registry"]
        commands = registry.list_commands()

        for cmd in commands:
            assert cmd.description, f"Command {cmd.name} missing description"
            assert len(cmd.description) > 0

    def test_error_handling(self, full_system):
        """Test error handling in commands."""
        registry = full_system["registry"]
        renderer = full_system["renderer"]

        # Unknown command
        with pytest.raises(ValueError):
            registry.execute("unknown", [])

        # Help for unknown command
        registry.execute("help", ["unknown"])
        renderer.render_error.assert_called()
