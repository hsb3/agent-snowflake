"""Tests for event loop fix in REPLLoop.

Verifies that the fix for "Event loop is closed" error works correctly.
The issue was caused by multiple asyncio.run() calls which create/close
separate event loops, while httpx connection pools are tied to a single loop.

The fix runs the entire REPL under a single asyncio.run() call via _run_async().
"""

import asyncio
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
def mock_client():
    """Create mock client with async methods."""
    client = MagicMock()
    client.connect = AsyncMock(return_value=True)
    client.list_agents = AsyncMock(
        return_value=[{"assistant_id": "agent_test", "name": "Test Agent"}]
    )
    client.create_thread = AsyncMock(return_value="thread-123")
    return client


@pytest.fixture
def mock_session():
    """Create mock session."""
    session = MagicMock()
    session.current_thread_id = "thread-123"
    session.current_assistant_id = "agent_test"
    session.session_start_time = 0
    session.get_token_summary = MagicMock(return_value={"input": 0, "output": 0, "total": 0})
    return session


class TestEventLoopFix:
    """Tests specifically for the event loop fix."""

    @pytest.mark.asyncio
    async def test_run_async_single_event_loop(self, config, mock_client, mock_session):
        """Test that _run_async uses a single event loop for all operations.

        This is the core fix - all async operations should run under one loop.
        """
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)

            # Mock _get_input to return /exit immediately
            repl._get_input = MagicMock(return_value="/exit")
            repl.command_registry.execute = MagicMock(return_value=False)

            # Run the async main loop
            result = await repl._run_async()

            # Should complete successfully
            assert result == 0

            # Verify startup was called (connect, list_agents, create_thread)
            mock_client.connect.assert_called_once()
            mock_client.list_agents.assert_called_once()
            mock_client.create_thread.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_input_async_awaits_messages(self, config, mock_client, mock_session):
        """Test that _handle_input_async properly awaits message sending."""
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)

            # Mock _send_message as async
            repl._send_message = AsyncMock()

            # Call the async handler with a message
            result = await repl._handle_input_async("Hello, agent!")

            # Should await _send_message
            repl._send_message.assert_awaited_once_with("Hello, agent!")
            assert result is True

    @pytest.mark.asyncio
    async def test_handle_input_async_awaits_async_commands(
        self, config, mock_client, mock_session
    ):
        """Test that _handle_input_async properly awaits async commands."""
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)

            # Create an async command that returns a coroutine
            async def async_command():
                return "async result"

            # Command registry returns a coroutine
            repl.command_registry.execute = MagicMock(return_value=async_command())

            # Call the async handler with a command
            result = await repl._handle_input_async("/async_cmd")

            # Should complete without error
            assert result is True

    @pytest.mark.asyncio
    async def test_multiple_messages_same_event_loop(self, config, mock_client, mock_session):
        """Test that multiple messages can be sent without event loop issues.

        This simulates the original bug: multiple sequential async operations
        should work under a single event loop.
        """
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)

            # Track call count
            call_count = 0

            async def mock_send_message(msg):
                nonlocal call_count
                call_count += 1
                # Simulate async work that uses the event loop
                await asyncio.sleep(0)

            repl._send_message = mock_send_message

            # Send multiple messages - this would fail with the old code
            await repl._handle_input_async("message 1")
            await repl._handle_input_async("message 2")
            await repl._handle_input_async("message 3")

            # All messages should have been processed
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_startup_then_message_same_loop(self, config, mock_client, mock_session):
        """Test startup followed by message sending works under one loop.

        This is the exact sequence that caused the original bug:
        1. _startup() runs async code (connect, list_agents, create_thread)
        2. _send_message() runs async code (stream_message)

        With the old code, each had its own asyncio.run() = separate loops.
        With the fix, both run under _run_async()'s single loop.
        """
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)

            # Run startup
            startup_result = await repl._startup()
            assert startup_result is True

            # Now simulate sending a message (same loop!)
            repl._send_message = AsyncMock()
            await repl._handle_input_async("test message")

            # Both should work without "Event loop is closed" error
            repl._send_message.assert_awaited_once()

    def test_run_uses_single_asyncio_run(self, config, mock_client, mock_session):
        """Test that run() uses a single asyncio.run() call.

        The fix ensures we only call asyncio.run() once, not multiple times
        for different operations.
        """
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)

            # Mock _run_async to verify it's called
            repl._run_async = AsyncMock(return_value=0)

            with patch("asyncio.run") as mock_asyncio_run:
                mock_asyncio_run.return_value = 0
                result = repl.run()

                # asyncio.run should be called exactly once
                assert mock_asyncio_run.call_count == 1
                assert result == 0


class TestStreamingUnderSingleLoop:
    """Test that streaming operations work correctly under single event loop."""

    @pytest.mark.asyncio
    async def test_stream_processing_in_async_context(self, config, mock_client, mock_session):
        """Test that stream processing works in the async context."""

        async def mock_stream(thread_id, message, assistant_id):
            """Mock stream that yields events."""
            yield ("messages/partial", [{"id": "msg-1", "content": "Hello"}])
            yield ("messages/complete", [{"id": "msg-1", "content": "Hello world"}])

        mock_client.stream_message = mock_stream

        # Create async iterator for parsed chunks
        async def mock_process_stream(chunks):
            async for event_type, data in chunks:
                yield ParsedChunk(
                    chunk_type=ChunkType.TEXT_DELTA,
                    namespace=(),
                    text_delta="Hello",
                )

        mock_stream_handler = MagicMock()
        mock_stream_handler.process_stream = mock_process_stream

        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(return_value=mock_stream_handler),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)

            # Run startup first
            await repl._startup()

            # Now send a message - should process stream without issues
            await repl._send_message("test")

            # If we got here without "Event loop is closed", the fix works


class TestBackwardsCompatibility:
    """Ensure the refactoring maintains backwards compatibility."""

    def test_run_returns_exit_code(self, config, mock_client, mock_session):
        """Test that run() still returns proper exit codes."""
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)
            repl._run_async = AsyncMock(return_value=0)

            result = repl.run()
            assert result == 0

    def test_run_handles_fatal_errors(self, config, mock_client, mock_session):
        """Test that run() handles fatal errors gracefully."""
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)

            # Simulate fatal error in _run_async
            repl._run_async = AsyncMock(side_effect=RuntimeError("Test error"))

            result = repl.run()

            # Should return error code
            assert result == 1

    @pytest.mark.asyncio
    async def test_handle_input_async_returns_false_for_exit(
        self, config, mock_client, mock_session
    ):
        """Test that _handle_input_async returns False for exit command."""
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)
            repl.command_registry.execute = MagicMock(return_value=False)

            result = await repl._handle_input_async("/exit")

            assert result is False

    @pytest.mark.asyncio
    async def test_handle_input_async_ignores_empty_input(self, config, mock_client, mock_session):
        """Test that _handle_input_async ignores empty input."""
        with patch.multiple(
            "repl_client.__main__",
            LangGraphClient=MagicMock(return_value=mock_client),
            SessionState=MagicMock(return_value=mock_session),
            StreamHandler=MagicMock(),
            Renderer=MagicMock(),
            CommandRegistry=MagicMock(),
            CommandHandlers=MagicMock(),
        ):
            repl = REPLLoop(config)
            repl._send_message = AsyncMock()

            result = await repl._handle_input_async("")

            repl._send_message.assert_not_called()
            assert result is True

            result = await repl._handle_input_async("   ")

            repl._send_message.assert_not_called()
            assert result is True
