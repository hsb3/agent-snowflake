"""Tests for REPLLoop and main entry point (Layer 8).

Test-driven development for main REPL loop orchestration.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from repl_client.__main__ import REPLLoop
from repl_client.core.config import Config
from repl_client.streaming.types import ChunkType, ParsedChunk


@pytest.fixture
def config():
    """Test config."""
    return Config(
        server_url="http://localhost:2024",
        default_agent="agent_test",
        stream_mode=["messages"],
        debug=False,
    )


@pytest.fixture
def mock_components():
    """Mock all REPL components."""
    # Create mocks
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.list_agents = AsyncMock(
        return_value=[
            {"assistant_id": "agent_test", "name": "Test Agent"},
        ]
    )
    client.create_thread = AsyncMock(return_value="thread-123")

    session = MagicMock()
    session.current_thread_id = "thread-123"
    session.current_assistant_id = "agent_test"
    session.get_display_summary = MagicMock(
        return_value="Thread: thread-123 | Agent: agent_test | Tokens: 0 in / 0 out / 0 total"
    )

    stream_handler = MagicMock()
    renderer = MagicMock()
    command_registry = MagicMock()
    command_handlers = MagicMock()

    return {
        "client": client,
        "session": session,
        "stream_handler": stream_handler,
        "renderer": renderer,
        "command_registry": command_registry,
        "command_handlers": command_handlers,
    }


class TestREPLLoop:
    """Test REPLLoop class."""

    def test_init(self, config):
        """Test REPLLoop initialization."""
        repl = REPLLoop(config)

        assert repl.config == config
        assert repl.client is not None
        assert repl.session is not None
        assert repl.stream_handler is not None
        assert repl.renderer is not None
        assert repl.command_registry is not None
        assert repl.command_handlers is not None

    @pytest.mark.asyncio
    async def test_startup_success(self, config, mock_components):
        """Test successful startup sequence."""
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_components["client"]),
            SessionState=MagicMock(return_value=mock_components["session"]),
            StreamHandler=MagicMock(return_value=mock_components["stream_handler"]),
            Renderer=MagicMock(return_value=mock_components["renderer"]),
            CommandRegistry=MagicMock(return_value=mock_components["command_registry"]),
            CommandHandlers=MagicMock(return_value=mock_components["command_handlers"]),
        ):
            repl = REPLLoop(config)
            result = await repl._startup()

            assert result is True
            mock_components["client"].connect.assert_called_once()
            mock_components["client"].list_agents.assert_called_once()
            mock_components["client"].create_thread.assert_called_once()
            mock_components["renderer"].render_panel.assert_called()

    @pytest.mark.asyncio
    async def test_startup_connection_failure(self, config, mock_components):
        """Test startup with connection failure."""
        mock_components["client"].connect = AsyncMock(return_value=False)

        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_components["client"]),
            SessionState=MagicMock(return_value=mock_components["session"]),
            StreamHandler=MagicMock(return_value=mock_components["stream_handler"]),
            Renderer=MagicMock(return_value=mock_components["renderer"]),
            CommandRegistry=MagicMock(return_value=mock_components["command_registry"]),
            CommandHandlers=MagicMock(return_value=mock_components["command_handlers"]),
        ):
            repl = REPLLoop(config)
            result = await repl._startup()

            assert result is False
            mock_components["renderer"].render_error.assert_called()

    def test_handle_input_command(self, config):
        """Test _handle_input routes commands correctly."""
        repl = REPLLoop(config)
        repl.command_registry = MagicMock()
        repl.command_registry.execute = MagicMock(return_value=None)

        # Test command routing
        result = repl._handle_input("/help")

        repl.command_registry.execute.assert_called_once_with("help", [])
        assert result is True

    def test_handle_input_command_with_args(self, config):
        """Test _handle_input routes commands with arguments."""
        repl = REPLLoop(config)
        repl.command_registry = MagicMock()
        repl.command_registry.execute = MagicMock(return_value=None)

        result = repl._handle_input("/agents agent_test")

        repl.command_registry.execute.assert_called_once_with("agents", ["agent_test"])
        assert result is True

    def test_handle_input_exit_command(self, config):
        """Test _handle_input handles exit command."""
        repl = REPLLoop(config)
        repl.command_registry = MagicMock()
        repl.command_registry.execute = MagicMock(return_value=False)

        result = repl._handle_input("/exit")

        repl.command_registry.execute.assert_called_once_with("exit", [])
        assert result is False

    def test_handle_input_message(self, config):
        """Test _handle_input routes messages correctly."""
        repl = REPLLoop(config)
        repl._send_message = AsyncMock()

        result = repl._handle_input("Hello, agent!")

        repl._send_message.assert_called_once_with("Hello, agent!")
        assert result is True

    def test_handle_input_empty(self, config):
        """Test _handle_input handles empty input."""
        repl = REPLLoop(config)
        repl._send_message = MagicMock()

        result = repl._handle_input("")

        # Empty input should be ignored
        repl._send_message.assert_not_called()
        assert result is True

    @pytest.mark.asyncio
    async def test_send_message(self, config, mock_components):
        """Test _send_message streams and renders response."""

        # Setup mock stream
        async def mock_stream(thread_id, message, assistant_id):
            yield (
                "messages/partial",
                {"id": "msg-1", "content": [{"type": "text", "text": "Hello"}]},
            )

        mock_components["client"].stream_message = mock_stream

        # Setup parsed chunks
        parsed_chunks = [
            ParsedChunk(
                chunk_type=ChunkType.TEXT_DELTA,
                namespace=(),
                text_delta="Hello",
            )
        ]
        mock_components["stream_handler"].process_stream = MagicMock(
            return_value=iter(parsed_chunks)
        )

        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_components["client"]),
            SessionState=MagicMock(return_value=mock_components["session"]),
            StreamHandler=MagicMock(return_value=mock_components["stream_handler"]),
            Renderer=MagicMock(return_value=mock_components["renderer"]),
            CommandRegistry=MagicMock(return_value=mock_components["command_registry"]),
            CommandHandlers=MagicMock(return_value=mock_components["command_handlers"]),
        ):
            repl = REPLLoop(config)
            await repl._send_message("Test message")

            # Verify stream_handler was called
            mock_components["stream_handler"].process_stream.assert_called_once()

    def test_parse_command_input(self, config):
        """Test _parse_command_input splits commands correctly."""
        repl = REPLLoop(config)

        # Test simple command
        cmd, args = repl._parse_command_input("/help")
        assert cmd == "help"
        assert args == []

        # Test command with single arg
        cmd, args = repl._parse_command_input("/agents agent_test")
        assert cmd == "agents"
        assert args == ["agent_test"]

        # Test command with multiple args
        cmd, args = repl._parse_command_input("/help agents")
        assert cmd == "help"
        assert args == ["agents"]

    def test_shutdown(self, config, mock_components):
        """Test _shutdown displays summary."""
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_components["client"]),
            SessionState=MagicMock(return_value=mock_components["session"]),
            StreamHandler=MagicMock(return_value=mock_components["stream_handler"]),
            Renderer=MagicMock(return_value=mock_components["renderer"]),
            CommandRegistry=MagicMock(return_value=mock_components["command_registry"]),
            CommandHandlers=MagicMock(return_value=mock_components["command_handlers"]),
        ):
            repl = REPLLoop(config)
            repl._shutdown()

            # Verify summary was shown
            mock_components["renderer"].render_panel.assert_called()


class TestMainEntryPoint:
    """Test main() entry point."""

    @patch("repl_client.__main__.Config")
    @patch("repl_client.__main__.REPLLoop")
    def test_main_success(self, mock_repl_class, mock_config_class):
        """Test main() entry point."""
        from repl_client.__main__ import main

        # Setup mocks
        mock_config = MagicMock()
        mock_config_class.from_env.return_value = mock_config

        mock_repl = MagicMock()
        mock_repl.run.return_value = 0
        mock_repl_class.return_value = mock_repl

        # Call main (will raise SystemExit)
        with pytest.raises(SystemExit) as exc_info:
            main()

        # Verify flow
        mock_config_class.from_env.assert_called_once()
        mock_repl_class.assert_called_once_with(mock_config)
        mock_repl.run.assert_called_once()
        assert exc_info.value.code == 0

    @patch("repl_client.__main__.Config")
    @patch("repl_client.__main__.REPLLoop")
    def test_main_exit_code(self, mock_repl_class, mock_config_class):
        """Test main() propagates exit code."""
        from repl_client.__main__ import main

        # Setup mocks
        mock_config = MagicMock()
        mock_config_class.from_env.return_value = mock_config

        mock_repl = MagicMock()
        mock_repl.run.return_value = 1  # Non-zero exit
        mock_repl_class.return_value = mock_repl

        # Call main
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
