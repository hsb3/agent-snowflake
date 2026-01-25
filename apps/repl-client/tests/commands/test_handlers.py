"""Tests for CommandHandlers (Layer 7).

Test-driven development for command handler implementations.
Tests both Phase 1 (help, exit) and Phase 2 (agents, threads, new, info) commands.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from repl_client.commands.handlers import CommandHandlers
from repl_client.commands.registry import CommandRegistry
from repl_client.core.session import SessionState
from repl_client.ui.renderer import Renderer


@pytest.fixture
def mock_client():
    """Mock LangGraphClient."""
    client = MagicMock()
    client.list_agents = AsyncMock(
        return_value=[
            {"assistant_id": "uuid-basic-123", "graph_id": "agent_basic", "name": "Basic Agent"},
            {
                "assistant_id": "uuid-enhanced-456",
                "graph_id": "agent_enhanced",
                "name": "Enhanced Agent",
            },
        ]
    )
    client.list_threads = AsyncMock(
        return_value=[
            {"thread_id": "thread-123", "metadata": {}},
            {"thread_id": "thread-456", "metadata": {}},
        ]
    )
    client.create_thread = AsyncMock(return_value="thread-789")
    return client


@pytest.fixture
def session():
    """SessionState instance."""
    sess = SessionState()
    sess.set_agent("agent_basic")
    sess.set_thread("thread-123")
    return sess


@pytest.fixture
def renderer():
    """Mock Renderer."""
    return MagicMock(spec=Renderer)


@pytest.fixture
def handlers(mock_client, session, renderer):
    """CommandHandlers instance."""
    return CommandHandlers(client=mock_client, session=session, renderer=renderer)


class TestCommandHandlersRegistration:
    """Test command registration."""

    def test_register_all(self, handlers):
        """Test that register_all registers all commands."""
        registry = CommandRegistry()
        handlers.register_all(registry)

        commands = registry.list_commands()
        command_names = [cmd.name for cmd in commands]

        # Phase 1 commands
        assert "help" in command_names
        assert "exit" in command_names

        # Phase 2 commands
        assert "agents" in command_names
        assert "threads" in command_names
        assert "new" in command_names
        assert "info" in command_names

        # Phase 3 stubs
        assert "clear" in command_names
        assert "session" in command_names


class TestHandleHelp:
    """Test /help command."""

    def test_handle_help_no_args(self, handlers, renderer):
        """Test /help with no arguments shows all commands."""
        registry = CommandRegistry()
        handlers.register_all(registry)

        handlers.handle_help([])

        # Should render panel with help text
        renderer.render_panel.assert_called_once()
        call_args = renderer.render_panel.call_args
        content = call_args[0][0]
        title = call_args[0][1]

        assert title == "Available Commands"
        assert "/help" in content
        assert "/exit" in content

    def test_handle_help_with_command(self, handlers, renderer):
        """Test /help <command> shows specific command help."""
        registry = CommandRegistry()
        handlers.register_all(registry)

        handlers.handle_help(["exit"])

        # Should render panel with specific command help
        renderer.render_panel.assert_called_once()
        call_args = renderer.render_panel.call_args
        content = call_args[0][0]

        assert "exit" in content

    def test_handle_help_unknown_command(self, handlers, renderer):
        """Test /help <unknown> shows error."""
        registry = CommandRegistry()
        handlers.register_all(registry)

        handlers.handle_help(["unknown"])

        # Should show error
        renderer.render_error.assert_called_once()


class TestHandleExit:
    """Test /exit command."""

    def test_handle_exit_returns_false(self, handlers, renderer):
        """Test /exit returns False to signal exit."""
        result = handlers.handle_exit([])

        assert result is False
        # Should show goodbye message
        renderer.render_success.assert_called_once()


class TestHandleAgents:
    """Test /agents command."""

    @pytest.mark.asyncio
    async def test_handle_agents_list(self, handlers, mock_client, renderer):
        """Test /agents with no args lists all agents."""
        await handlers.handle_agents([])

        # Should call client.list_agents
        mock_client.list_agents.assert_called_once()

        # Should render table
        renderer.render_table.assert_called_once()
        call_args = renderer.render_table.call_args
        headers = call_args[0][0]
        rows = call_args[0][1]

        # Updated headers for Phase 2: Name (use this), Assistant ID, Current
        assert "Name (use this)" in headers or "Assistant ID" in headers
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_handle_agents_switch(self, handlers, session, renderer, mock_client):
        """Test /agents <agent_id> switches agent by name."""
        await handlers.handle_agents(["agent_enhanced"])

        # Should resolve name to UUID and set in session
        assert session.current_assistant_id == "uuid-enhanced-456"

        # Should show success message
        renderer.render_success.assert_called_once()


class TestHandleThreads:
    """Test /threads command."""

    @pytest.mark.asyncio
    async def test_handle_threads_list(self, handlers, mock_client, renderer):
        """Test /threads with no args lists all threads."""
        await handlers.handle_threads([])

        # Should call client.list_threads
        mock_client.list_threads.assert_called_once()

        # Should render table
        renderer.render_table.assert_called_once()
        call_args = renderer.render_table.call_args
        headers = call_args[0][0]
        rows = call_args[0][1]

        assert "Thread ID" in headers or "ID" in headers
        assert len(rows) == 2

    @pytest.mark.asyncio
    async def test_handle_threads_resume(self, handlers, session, renderer):
        """Test /threads <thread_id> resumes thread."""
        await handlers.handle_threads(["thread-456"])

        # Should set thread in session
        assert session.current_thread_id == "thread-456"

        # Should show success message
        renderer.render_success.assert_called_once()


class TestHandleNew:
    """Test /new command."""

    @pytest.mark.asyncio
    async def test_handle_new_creates_thread(self, handlers, mock_client, session, renderer):
        """Test /new creates new thread and sets it in session."""
        await handlers.handle_new([])

        # Should call client.create_thread
        mock_client.create_thread.assert_called_once()

        # Should set new thread in session
        assert session.current_thread_id == "thread-789"

        # Should show success message
        renderer.render_success.assert_called_once()


class TestHandleInfo:
    """Test /info command."""

    def test_handle_info_shows_summary(self, handlers, session, renderer):
        """Test /info shows session summary."""
        handlers.handle_info([])

        # Should render panel with session info
        renderer.render_panel.assert_called_once()
        call_args = renderer.render_panel.call_args
        content = call_args[0][0]
        title = call_args[0][1]

        assert title == "Session Info"
        assert "thread-123" in content  # Current thread
        assert "agent_basic" in content  # Current agent


class TestHandleClear:
    """Test /clear command (Phase 3 stub)."""

    def test_handle_clear(self, handlers, renderer):
        """Test /clear clears screen."""
        handlers.handle_clear([])

        # Should call renderer.clear
        renderer.clear.assert_called_once()


class TestHandleSession:
    """Test /session command (Phase 3 stub)."""

    def test_handle_session(self, handlers, session, renderer):
        """Test /session shows full session dump."""
        handlers.handle_session([])

        # Should render panel with full session state
        renderer.render_panel.assert_called_once()
        call_args = renderer.render_panel.call_args
        content = call_args[0][0]

        assert "thread-123" in content
        assert "agent_basic" in content
