"""Tests for StreamHandler (Layer 4)."""

import json
from pathlib import Path

import pytest

from repl_client.core.parsers import ToolCall, Usage
from repl_client.core.session import SessionState
from repl_client.streaming.handler import StreamHandler
from repl_client.streaming.types import ChunkType, ParsedChunk


async def _async_iter(iterable):
    """Convert sync iterable to async iterator for testing."""
    for item in iterable:
        yield item


@pytest.fixture
def session():
    """Create test session."""
    return SessionState()


@pytest.fixture
def handler(session):
    """Create test handler."""
    return StreamHandler(session)


@pytest.fixture
def sample_stream_data():
    """Load real SSE data from debug output."""
    # Use the most recent stream_messages file
    data_file = (
        Path(__file__).parent.parent.parent.parent
        / "scripts"
        / "debug"
        / "output"
        / "stream_messages_20260123_210128.json"
    )

    with open(data_file) as f:
        chunks = json.load(f)

    # Convert to (event, data) tuples
    # Note: data is wrapped in array, need to unwrap
    result = []
    for chunk in chunks:
        event = chunk["event"]
        data = chunk["data"]

        # Unwrap array if present (messages/partial format)
        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        result.append((event, data))

    return result


async def test_process_stream_basic(handler, sample_stream_data):
    """Test basic stream processing yields ParsedChunk objects."""
    chunks = [c async for c in handler.process_stream(_async_iter(sample_stream_data))]

    # Should have multiple chunks
    assert len(chunks) > 0

    # All should be ParsedChunk
    for chunk in chunks:
        assert isinstance(chunk, ParsedChunk)

    # Should have TEXT_DELTA chunks
    text_chunks = [c for c in chunks if c.chunk_type == ChunkType.TEXT_DELTA]
    assert len(text_chunks) > 0

    # Should have USAGE chunk at end
    usage_chunks = [c for c in chunks if c.chunk_type == ChunkType.USAGE]
    assert len(usage_chunks) == 1


async def test_text_delta_extraction(handler):
    """Test that cumulative text is correctly converted to deltas."""
    # Simulate cumulative text chunks
    chunks = [
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [{"type": "text", "index": 0, "text": "Hello"}],
                "response_metadata": {},
            },
        ),
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [{"type": "text", "index": 0, "text": "Hello world"}],
                "response_metadata": {},
            },
        ),
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [{"type": "text", "index": 0, "text": "Hello world!"}],
                "response_metadata": {},
            },
        ),
    ]

    results = [c async for c in handler.process_stream(_async_iter(chunks))]

    # Filter to TEXT_DELTA chunks
    text_deltas = [c for c in results if c.chunk_type == ChunkType.TEXT_DELTA]

    # Should have 3 deltas
    assert len(text_deltas) == 3

    # First chunk: full text
    assert text_deltas[0].text_delta == "Hello"

    # Second chunk: delta only
    assert text_deltas[1].text_delta == " world"

    # Third chunk: delta only
    assert text_deltas[2].text_delta == "!"


async def test_tool_call_buffering(handler):
    """Test tool call buffering with partial_json chunks."""
    # Simulate tool call stream with partial JSON
    chunks = [
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [
                    {
                        "type": "tool_use",
                        "index": 0,
                        "id": "tool-1",
                        "name": "test_tool",
                        "partial_json": '{"arg',
                    }
                ],
                "response_metadata": {},
            },
        ),
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [
                    {
                        "type": "tool_use",
                        "index": 0,
                        "id": "tool-1",
                        "name": "test_tool",
                        "partial_json": '{"arg1": "val',
                    }
                ],
                "response_metadata": {},
            },
        ),
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [
                    {
                        "type": "tool_use",
                        "index": 0,
                        "id": "tool-1",
                        "name": "test_tool",
                        "partial_json": '{"arg1": "value"}',
                    }
                ],
                "response_metadata": {"stop_reason": "tool_use"},
                "tool_calls": [
                    {
                        "id": "tool-1",
                        "name": "test_tool",
                        "args": {"arg1": "value"},
                        "type": "tool_call",
                    }
                ],
            },
        ),
    ]

    results = [c async for c in handler.process_stream(_async_iter(chunks))]

    # Should have TOOL_CALL_COMPLETE chunk
    tool_chunks = [c for c in results if c.chunk_type == ChunkType.TOOL_CALL_COMPLETE]
    assert len(tool_chunks) == 1

    # Check tool call details
    tool_call = tool_chunks[0].tool_call
    assert tool_call is not None
    assert tool_call.id == "tool-1"
    assert tool_call.name == "test_tool"
    assert tool_call.args == {"arg1": "value"}


async def test_namespace_tracking(handler):
    """Test namespace tracking in ParsedChunk."""
    # Test with namespace
    chunks = [
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [{"type": "text", "index": 0, "text": "Hello"}],
                "response_metadata": {},
            },
        )
    ]

    # Process with namespace
    namespace = ["subagent", "task1"]
    results = [c async for c in handler.process_stream(_async_iter(chunks), namespace=namespace)]

    # Check namespace is set
    assert len(results) > 0
    text_chunk = [c for c in results if c.chunk_type == ChunkType.TEXT_DELTA][0]
    assert text_chunk.namespace == ("subagent", "task1")

    # Test without namespace (default empty tuple)
    results2 = [c async for c in handler.process_stream(_async_iter(chunks))]
    text_chunk2 = [c for c in results2 if c.chunk_type == ChunkType.TEXT_DELTA][0]
    assert text_chunk2.namespace == ()


async def test_usage_tracking(handler, session):
    """Test usage metadata extraction and session tracking."""
    # Final chunk with usage
    chunks = [
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [{"type": "text", "index": 0, "text": "Done"}],
                "response_metadata": {"stop_reason": "end_turn"},
                "usage_metadata": {
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "total_tokens": 150,
                },
            },
        )
    ]

    # Initial token state
    assert session.session_tokens["input"] == 0
    assert session.session_tokens["output"] == 0

    results = [c async for c in handler.process_stream(_async_iter(chunks))]

    # Should have USAGE chunk
    usage_chunks = [c for c in results if c.chunk_type == ChunkType.USAGE]
    assert len(usage_chunks) == 1

    # Check usage data
    usage = usage_chunks[0].usage
    assert usage is not None
    assert usage.input_tokens == 100
    assert usage.output_tokens == 50
    assert usage.total_tokens == 150

    # Session should be updated
    assert session.session_tokens["input"] == 100
    assert session.session_tokens["output"] == 50
    assert session.session_tokens["total"] == 150


async def test_metadata_chunk(handler):
    """Test metadata event handling."""
    chunks = [
        (
            "metadata",
            {
                "run_id": "run-123",
                "attempt": 1,
            },
        )
    ]

    results = [c async for c in handler.process_stream(_async_iter(chunks))]

    # Should have METADATA chunk
    metadata_chunks = [c for c in results if c.chunk_type == ChunkType.METADATA]
    assert len(metadata_chunks) == 1

    # Check metadata
    assert metadata_chunks[0].metadata is not None
    assert metadata_chunks[0].metadata["run_id"] == "run-123"


async def test_empty_content_handling(handler):
    """Test handling of chunks with empty content."""
    chunks = [
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [],  # Empty content
                "response_metadata": {},
            },
        )
    ]

    # Should not crash, should skip empty chunks
    results = [c async for c in handler.process_stream(_async_iter(chunks))]

    # No text deltas should be yielded for empty content
    text_chunks = [c for c in results if c.chunk_type == ChunkType.TEXT_DELTA]
    assert len(text_chunks) == 0


async def test_multiple_messages_in_stream(handler):
    """Test handling multiple distinct messages in one stream."""
    chunks = [
        (
            "messages/partial",
            {
                "id": "msg-1",
                "type": "ai",
                "content": [{"type": "text", "index": 0, "text": "First"}],
                "response_metadata": {},
            },
        ),
        (
            "messages/partial",
            {
                "id": "msg-2",  # Different message ID
                "type": "ai",
                "content": [{"type": "text", "index": 0, "text": "Second"}],
                "response_metadata": {},
            },
        ),
    ]

    results = [c async for c in handler.process_stream(_async_iter(chunks))]

    # Should have text deltas for both messages
    text_chunks = [c for c in results if c.chunk_type == ChunkType.TEXT_DELTA]
    assert len(text_chunks) == 2

    # Each should have full text (different message IDs)
    assert text_chunks[0].text_delta == "First"
    assert text_chunks[0].message_id == "msg-1"

    assert text_chunks[1].text_delta == "Second"
    assert text_chunks[1].message_id == "msg-2"


async def test_parse_interrupt_stub(handler):
    """Test _parse_interrupt stub (Phase 2)."""
    # Should return None for now
    result = handler._parse_interrupt({})
    assert result is None

    result = handler._parse_interrupt({"__interrupt__": {"some": "data"}})
    assert result is None  # Stub implementation


async def test_extract_text_delta_method(handler):
    """Test _extract_text_delta helper method."""
    prev_text_map = {}

    # First call - no previous text
    delta1 = handler._extract_text_delta("msg-1", "Hello", prev_text_map)
    assert delta1 == "Hello"
    assert prev_text_map["msg-1"] == "Hello"

    # Second call - extract delta
    delta2 = handler._extract_text_delta("msg-1", "Hello world", prev_text_map)
    assert delta2 == " world"
    assert prev_text_map["msg-1"] == "Hello world"

    # Different message ID
    delta3 = handler._extract_text_delta("msg-2", "New", prev_text_map)
    assert delta3 == "New"
    assert prev_text_map["msg-2"] == "New"


async def test_buffer_tool_call_method(handler):
    """Test _buffer_tool_call helper method."""
    buffer = {}

    # First partial chunk
    block1 = {
        "type": "tool_use",
        "index": 0,
        "id": "tool-1",
        "name": "test_tool",
        "partial_json": '{"key":',
    }

    result1 = handler._buffer_tool_call(block1, buffer)
    assert result1 is None  # Not complete
    assert "tool-1" in buffer

    # Second partial chunk
    block2 = {
        "type": "tool_use",
        "index": 0,
        "id": "tool-1",
        "name": "test_tool",
        "partial_json": '{"key": "value"}',
    }

    result2 = handler._buffer_tool_call(block2, buffer)
    assert result2 is not None  # Complete!
    assert result2["id"] == "tool-1"
    assert result2["name"] == "test_tool"
    assert result2["args"] == {"key": "value"}


async def test_real_stream_end_to_end(handler, sample_stream_data, session):
    """End-to-end test with real captured stream data."""
    # Process entire real stream
    results = [c async for c in handler.process_stream(_async_iter(sample_stream_data))]

    # Categorize chunks
    text_chunks = [c for c in results if c.chunk_type == ChunkType.TEXT_DELTA]
    usage_chunks = [c for c in results if c.chunk_type == ChunkType.USAGE]
    metadata_chunks = [c for c in results if c.chunk_type == ChunkType.METADATA]

    # Should have text deltas
    assert len(text_chunks) > 0

    # Should have exactly one usage chunk
    assert len(usage_chunks) == 1

    # Should have metadata chunk
    assert len(metadata_chunks) > 0

    # Usage should be tracked in session
    assert session.session_tokens["total"] > 0

    # Text deltas should reconstruct to final text
    full_text = "".join(c.text_delta for c in text_chunks)
    assert "Complete!" in full_text  # From the sample data
