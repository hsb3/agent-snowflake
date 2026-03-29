"""Tests for TUI service layer.

Simple integration tests to verify service wrappers work correctly.
"""

from repl_client.core.client import LangGraphClient
from repl_client.core.session import SessionState
from repl_client.streaming.handler import StreamHandler
from repl_client.tui.services import LangGraphService, StreamService


class TestLangGraphService:
    """Test LangGraphService wrapper."""

    def test_initialization(self):
        """Test service can be initialized."""
        client = LangGraphClient(base_url="http://localhost:2024")
        service = LangGraphService(client)

        assert service.client is client
        assert service._agent_cache is None
        assert service._threads_cache is None

    def test_cache_invalidation(self):
        """Test cache invalidation methods."""
        client = LangGraphClient(base_url="http://localhost:2024")
        service = LangGraphService(client)

        # Set some cached data
        service._agent_cache = [{"assistant_id": "agent1"}]
        service._threads_cache = [{"thread_id": "thread1"}]

        # Invalidate individual caches
        service.invalidate_agent_cache()
        assert service._agent_cache is None
        assert service._threads_cache == [{"thread_id": "thread1"}]

        # Reset
        service._agent_cache = [{"assistant_id": "agent1"}]
        service._threads_cache = [{"thread_id": "thread1"}]

        service.invalidate_thread_cache()
        assert service._agent_cache == [{"assistant_id": "agent1"}]
        assert service._threads_cache is None

        # Invalidate all
        service._agent_cache = [{"assistant_id": "agent1"}]
        service._threads_cache = [{"thread_id": "thread1"}]

        service.invalidate_all_caches()
        assert service._agent_cache is None
        assert service._threads_cache is None

    async def test_resolve_agent_name_with_cache(self):
        """Test agent name resolution uses cached data."""
        client = LangGraphClient(base_url="http://localhost:2024")
        service = LangGraphService(client)

        # Pre-populate cache
        service._agent_cache = [
            {"assistant_id": "uuid1", "graph_id": "agent_enhanced", "name": "Enhanced"},
            {"assistant_id": "uuid2", "graph_id": "agent_minimal", "name": "Minimal"},
        ]

        # Resolve by graph_id
        result = await service.resolve_agent_name("agent_enhanced")
        assert result == "uuid1"

        # Resolve by name (case insensitive)
        result = await service.resolve_agent_name("Minimal")
        assert result == "uuid2"

        # Resolve by exact UUID
        result = await service.resolve_agent_name("uuid1")
        assert result == "uuid1"

        # Not found
        result = await service.resolve_agent_name("nonexistent")
        assert result is None


class TestStreamService:
    """Test StreamService wrapper."""

    def test_initialization(self):
        """Test service can be initialized."""
        session = SessionState()
        handler = StreamHandler(session)
        service = StreamService(handler)

        assert service.handler is handler

    async def test_stream_with_widgets_basic(self):
        """Test basic streaming without callbacks."""
        session = SessionState()
        handler = StreamHandler(session)
        service = StreamService(handler)

        # Create async iterator from list
        async def async_chunks():
            chunks = [
                (
                    "messages/partial",
                    [{"id": "msg1", "content": [{"type": "text", "text": "Hello"}]}],
                ),
            ]
            for chunk in chunks:
                yield chunk

        # Should not raise exception even with no callbacks
        await service.stream_with_widgets(async_chunks())

    async def test_stream_with_widgets_text_callback(self):
        """Test text callback is invoked."""
        session = SessionState()
        handler = StreamHandler(session)
        service = StreamService(handler)

        # Track callback invocations
        received_texts = []

        async def on_text(text: str):
            received_texts.append(text)

        async def async_chunks():
            chunks = [
                (
                    "messages/partial",
                    [{"id": "msg1", "content": [{"type": "text", "text": "Hello"}]}],
                ),
                (
                    "messages/partial",
                    [{"id": "msg1", "content": [{"type": "text", "text": "Hello World"}]}],
                ),
            ]
            for chunk in chunks:
                yield chunk

        await service.stream_with_widgets(
            async_chunks(),
            on_text=on_text,
        )

        # Should receive two deltas: "Hello" and " World"
        assert len(received_texts) == 2
        assert received_texts[0] == "Hello"
        assert received_texts[1] == " World"

    async def test_stream_with_widgets_usage_callback(self):
        """Test usage callback is invoked."""
        session = SessionState()
        handler = StreamHandler(session)
        service = StreamService(handler)

        # Track callback invocations
        received_usage = []

        async def on_usage(usage):
            received_usage.append(usage)

        async def async_chunks():
            chunks = [
                (
                    "messages/partial",
                    [
                        {
                            "id": "msg1",
                            "content": [],
                            "usage_metadata": {
                                "input_tokens": 100,
                                "output_tokens": 50,
                                "total_tokens": 150,
                            },
                        }
                    ],
                ),
            ]
            for chunk in chunks:
                yield chunk

        await service.stream_with_widgets(
            async_chunks(),
            on_usage=on_usage,
        )

        # Should receive usage
        assert len(received_usage) == 1
        assert received_usage[0].input_tokens == 100
        assert received_usage[0].output_tokens == 50

    async def test_stream_with_widgets_callback_error_resilience(self):
        """Test that callback errors don't stop stream processing."""
        session = SessionState()
        handler = StreamHandler(session)
        service = StreamService(handler)

        # Track all invocations
        call_count = 0

        async def failing_callback(text: str):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Test error")

        async def async_chunks():
            chunks = [
                (
                    "messages/partial",
                    [{"id": "msg1", "content": [{"type": "text", "text": "First"}]}],
                ),
                (
                    "messages/partial",
                    [{"id": "msg1", "content": [{"type": "text", "text": "First Second"}]}],
                ),
            ]
            for chunk in chunks:
                yield chunk

        # Should not raise - errors are caught
        await service.stream_with_widgets(
            async_chunks(),
            on_text=failing_callback,
        )

        # Both callbacks were attempted
        assert call_count == 2
