"""
Test suite for parsers.py - SSE and streaming chunk parsing.

Tests use real data from scripts/debug/output/*.json files.
"""

import json
import pytest
from pathlib import Path

from repl_client.core.parsers import (
    parse_sse_line,
    extract_text_delta,
    parse_message_chunk,
    extract_content_blocks,
    detect_tool_call,
    is_stream_complete,
    ParsedChunk,
    ContentBlock,
    ToolCall,
    Usage,
)


# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent.parent.parent / "scripts" / "debug" / "output"


def load_test_data(filename: str) -> list[dict]:
    """Load test data from JSON file."""
    with open(TEST_DATA_DIR / filename) as f:
        return json.load(f)


class TestParseSSELine:
    """Test SSE line parsing."""

    def test_parse_event_line(self):
        """Parse event: line."""
        result = parse_sse_line("event: messages/partial")
        assert result == ("event", "messages/partial")

    def test_parse_data_line(self):
        """Parse data: line with JSON."""
        data_line = 'data: {"key": "value"}'
        result = parse_sse_line(data_line)
        assert result == ("data", '{"key": "value"}')

    def test_parse_data_line_complex_json(self):
        """Parse data: line with complex nested JSON."""
        data_line = 'data: {"content": [{"type": "text", "text": "hello"}], "id": "123"}'
        result = parse_sse_line(data_line)
        assert result is not None
        assert result[0] == "data"
        assert "content" in result[1]

    def test_parse_empty_line(self):
        """Empty line returns None."""
        result = parse_sse_line("")
        assert result is None

    def test_parse_whitespace_line(self):
        """Whitespace-only line returns None."""
        result = parse_sse_line("   \n")
        assert result is None

    def test_parse_malformed_line(self):
        """Malformed line (no colon) returns None."""
        result = parse_sse_line("invalid line without colon")
        assert result is None

    def test_parse_line_with_colon_in_value(self):
        """Handle colon in the value part."""
        result = parse_sse_line("data: http://example.com")
        assert result == ("data", "http://example.com")


class TestExtractTextDelta:
    """Test text delta extraction from cumulative updates."""

    def test_extract_delta_new_text(self):
        """Extract new text from cumulative update."""
        prev = "Hello"
        curr = "Hello world"
        delta = extract_text_delta(prev, curr)
        assert delta == " world"

    def test_extract_delta_first_chunk(self):
        """First chunk (prev is empty)."""
        prev = ""
        curr = "Hello"
        delta = extract_text_delta(prev, curr)
        assert delta == "Hello"

    def test_extract_delta_identical(self):
        """No change returns empty string."""
        prev = "Hello world"
        curr = "Hello world"
        delta = extract_text_delta(prev, curr)
        assert delta == ""

    def test_extract_delta_multiline(self):
        """Handle multiline text."""
        prev = "Line 1\nLine 2"
        curr = "Line 1\nLine 2\nLine 3"
        delta = extract_text_delta(prev, curr)
        assert delta == "\nLine 3"

    def test_extract_delta_from_real_data(self):
        """Test with real streaming data."""
        chunks = load_test_data("stream_messages_20260123_210128.json")

        # Find text chunks
        text_chunks = [
            c for c in chunks
            if c["event"] == "messages/partial"
            and c["data"][0].get("content")
        ]

        # Extract first two text updates
        text1 = text_chunks[0]["data"][0]["content"][0]["text"]
        text2 = text_chunks[1]["data"][0]["content"][0]["text"]

        delta = extract_text_delta(text1, text2)

        # Verify delta is the new part
        assert text2 == text1 + delta
        assert len(delta) > 0


class TestParseMessageChunk:
    """Test parsing of message chunks."""

    def test_parse_initial_chunk(self):
        """Parse initial messages/partial chunk with empty content."""
        event_type = "messages/partial"
        data = {
            "content": [],
            "type": "ai",
            "id": "msg_123",
            "tool_calls": [],
            "usage_metadata": None
        }

        chunk = parse_message_chunk(event_type, data)

        assert chunk.event_type == "messages/partial"
        assert chunk.message_type == "ai"
        assert chunk.message_id == "msg_123"
        assert chunk.content_blocks == []
        assert chunk.tool_calls is None
        assert chunk.usage is None

    def test_parse_text_chunk(self):
        """Parse chunk with text content."""
        event_type = "messages/partial"
        data = {
            "content": [
                {"type": "text", "text": "Hello", "index": 0}
            ],
            "type": "ai",
            "id": "msg_123",
            "tool_calls": [],
            "usage_metadata": None
        }

        chunk = parse_message_chunk(event_type, data)

        assert len(chunk.content_blocks) == 1
        assert chunk.content_blocks[0].type == "text"
        assert chunk.content_blocks[0].text == "Hello"
        assert chunk.content_blocks[0].index == 0

    def test_parse_final_chunk_with_usage(self):
        """Parse final chunk with usage metadata."""
        chunks = load_test_data("stream_messages_20260123_210128.json")
        final_chunk = chunks[-1]

        data = final_chunk["data"][0]
        chunk = parse_message_chunk(final_chunk["event"], data)

        assert chunk.usage is not None
        assert chunk.usage.input_tokens > 0
        assert chunk.usage.output_tokens > 0
        assert chunk.usage.total_tokens > 0
        assert chunk.stop_reason == "end_turn"

    def test_parse_chunk_from_real_data(self):
        """Parse actual streaming chunks."""
        chunks = load_test_data("stream_messages_20260123_210128.json")

        # Parse a text chunk
        text_chunk_raw = chunks[3]  # First chunk with text
        data = text_chunk_raw["data"][0]

        parsed = parse_message_chunk(text_chunk_raw["event"], data)

        assert parsed.message_type == "ai"
        assert len(parsed.content_blocks) > 0
        assert parsed.content_blocks[0].type == "text"


class TestExtractContentBlocks:
    """Test content block extraction."""

    def test_extract_text_block(self):
        """Extract text content block."""
        content = [
            {"type": "text", "text": "Hello world", "index": 0}
        ]

        blocks = extract_content_blocks(content)

        assert len(blocks) == 1
        assert blocks[0].type == "text"
        assert blocks[0].text == "Hello world"
        assert blocks[0].index == 0
        assert blocks[0].tool_id is None

    def test_extract_empty_content(self):
        """Empty content returns empty list."""
        blocks = extract_content_blocks([])
        assert blocks == []

    def test_extract_multiple_blocks(self):
        """Extract multiple content blocks."""
        content = [
            {"type": "text", "text": "First", "index": 0},
            {"type": "text", "text": "Second", "index": 1}
        ]

        blocks = extract_content_blocks(content)

        assert len(blocks) == 2
        assert blocks[0].text == "First"
        assert blocks[1].text == "Second"

    def test_extract_tool_use_block(self):
        """Extract tool_use content block."""
        content = [
            {
                "type": "tool_use",
                "id": "tool_123",
                "name": "search",
                "input": {"query": "test"},
                "index": 0
            }
        ]

        blocks = extract_content_blocks(content)

        assert len(blocks) == 1
        assert blocks[0].type == "tool_use"
        assert blocks[0].tool_id == "tool_123"
        assert blocks[0].tool_name == "search"
        assert blocks[0].tool_input == {"query": "test"}

    def test_extract_tool_use_with_partial_json(self):
        """Extract tool_use with partial JSON."""
        content = [
            {
                "type": "tool_use",
                "id": "tool_123",
                "name": "search",
                "partial_json": '{"query": "te',
                "index": 0
            }
        ]

        blocks = extract_content_blocks(content)

        assert len(blocks) == 1
        assert blocks[0].type == "tool_use"
        assert blocks[0].partial_json == '{"query": "te'
        assert blocks[0].tool_input is None


class TestDetectToolCall:
    """Test tool call detection."""

    def test_detect_tool_call_complete(self):
        """Detect complete tool call."""
        message = {
            "response_metadata": {
                "stop_reason": "tool_use"
            },
            "tool_calls": [
                {
                    "id": "call_123",
                    "name": "search",
                    "args": {"query": "test"},
                    "type": "tool_call"
                }
            ]
        }

        tool_call = detect_tool_call(message)

        assert tool_call is not None
        assert tool_call.id == "call_123"
        assert tool_call.name == "search"
        assert tool_call.args == {"query": "test"}

    def test_detect_tool_call_none_without_stop_reason(self):
        """No tool call without stop_reason."""
        message = {
            "tool_calls": []
        }

        tool_call = detect_tool_call(message)
        assert tool_call is None

    def test_detect_tool_call_none_empty_array(self):
        """No tool call with empty tool_calls array."""
        message = {
            "response_metadata": {
                "stop_reason": "tool_use"
            },
            "tool_calls": []
        }

        tool_call = detect_tool_call(message)
        assert tool_call is None

    def test_detect_tool_call_first_only(self):
        """Return only first tool call if multiple."""
        message = {
            "response_metadata": {
                "stop_reason": "tool_use"
            },
            "tool_calls": [
                {"id": "1", "name": "tool1", "args": {}, "type": "tool_call"},
                {"id": "2", "name": "tool2", "args": {}, "type": "tool_call"}
            ]
        }

        tool_call = detect_tool_call(message)
        assert tool_call is not None
        assert tool_call.id == "1"


class TestIsStreamComplete:
    """Test stream completion detection."""

    def test_complete_with_usage_metadata(self):
        """Stream complete when usage_metadata present."""
        chunk = {
            "usage_metadata": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150
            }
        }

        assert is_stream_complete(chunk) is True

    def test_complete_with_stop_reason(self):
        """Stream complete when stop_reason present."""
        chunk = {
            "response_metadata": {
                "stop_reason": "end_turn"
            },
            "usage_metadata": None
        }

        assert is_stream_complete(chunk) is True

    def test_not_complete_partial_chunk(self):
        """Partial chunk is not complete."""
        chunk = {
            "usage_metadata": None,
            "response_metadata": {}
        }

        assert is_stream_complete(chunk) is False

    def test_complete_with_both(self):
        """Stream complete with both indicators."""
        chunk = {
            "response_metadata": {
                "stop_reason": "end_turn"
            },
            "usage_metadata": {
                "input_tokens": 100,
                "output_tokens": 50,
                "total_tokens": 150
            }
        }

        assert is_stream_complete(chunk) is True

    def test_detect_completion_in_real_data(self):
        """Detect completion in real streaming data."""
        chunks = load_test_data("stream_messages_20260123_210128.json")

        # All chunks except the last should not be complete
        for chunk in chunks[:-1]:
            if chunk["event"] == "messages/partial":
                data = chunk["data"][0]
                assert is_stream_complete(data) is False

        # Last chunk should be complete
        final_chunk = chunks[-1]["data"][0]
        assert is_stream_complete(final_chunk) is True


class TestDataClasses:
    """Test dataclass creation."""

    def test_create_content_block(self):
        """Create ContentBlock dataclass."""
        block = ContentBlock(
            type="text",
            index=0,
            text="Hello",
            tool_id=None,
            tool_name=None,
            tool_input=None,
            partial_json=None
        )

        assert block.type == "text"
        assert block.text == "Hello"

    def test_create_tool_call(self):
        """Create ToolCall dataclass."""
        tool = ToolCall(
            id="call_123",
            name="search",
            args={"query": "test"},
            type="tool_call"
        )

        assert tool.name == "search"
        assert tool.args["query"] == "test"

    def test_create_usage(self):
        """Create Usage dataclass."""
        usage = Usage(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150
        )

        assert usage.total_tokens == 150

    def test_create_parsed_chunk(self):
        """Create ParsedChunk dataclass."""
        chunk = ParsedChunk(
            event_type="messages/partial",
            message_type="ai",
            message_id="msg_123",
            content_blocks=[],
            tool_calls=None,
            usage=None,
            stop_reason=None,
            metadata={}
        )

        assert chunk.event_type == "messages/partial"
        assert chunk.message_type == "ai"
