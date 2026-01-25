"""
SSE and streaming chunk parsers.

Parse raw SSE events and streaming chunks into structured data.
Handles text delta extraction, content block parsing, and tool call detection.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Usage:
    """Token usage metadata."""

    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass
class ToolCall:
    """Detected tool call."""

    id: str
    name: str
    args: dict
    type: str


@dataclass
class ContentBlock:
    """Parsed content block (text, tool_use, tool_result)."""

    type: str
    index: int
    text: str | None = None
    tool_id: str | None = None
    tool_name: str | None = None
    tool_input: dict | None = None
    partial_json: str | None = None


@dataclass
class ParsedChunk:
    """Parsed message chunk from streaming response."""

    event_type: str
    message_type: str
    message_id: str
    content_blocks: list[ContentBlock]
    tool_calls: list[ToolCall] | None = None
    usage: Usage | None = None
    stop_reason: str | None = None
    metadata: dict = field(default_factory=dict)


def parse_sse_line(line: str) -> tuple[str, str] | None:
    """
    Parse SSE line into (field, value) tuple.

    SSE format: "field: value"
    Common fields: event, data

    Args:
        line: Raw SSE line

    Returns:
        (field, value) tuple or None if empty/malformed
    """
    line = line.strip()

    if not line:
        return None

    if ":" not in line:
        return None

    # Split on first colon only
    field, _, value = line.partition(":")
    value = value.lstrip()  # Remove leading space after colon

    return (field, value)


def extract_text_delta(prev_text: str, curr_text: str) -> str:
    """
    Extract new text from cumulative update.

    The messages stream returns cumulative text (not deltas),
    so we need to extract the new portion.

    Args:
        prev_text: Previous cumulative text
        curr_text: Current cumulative text

    Returns:
        New text added (delta)
    """
    if not prev_text:
        return curr_text

    if curr_text.startswith(prev_text):
        return curr_text[len(prev_text) :]

    # Shouldn't happen, but handle gracefully
    return curr_text


def extract_content_blocks(content: list[dict]) -> list[ContentBlock]:
    """
    Parse content array into typed ContentBlock objects.

    Args:
        content: List of content block dicts

    Returns:
        List of ContentBlock objects
    """
    blocks = []

    for item in content:
        block_type = item.get("type")
        index = item.get("index", 0)

        if block_type == "text":
            blocks.append(
                ContentBlock(
                    type=block_type,
                    index=index,
                    text=item.get("text"),
                )
            )
        elif block_type == "tool_use":
            blocks.append(
                ContentBlock(
                    type=block_type,
                    index=index,
                    tool_id=item.get("id"),
                    tool_name=item.get("name"),
                    tool_input=item.get("input"),
                    partial_json=item.get("partial_json"),
                )
            )
        elif block_type == "tool_result":
            blocks.append(
                ContentBlock(
                    type=block_type,
                    index=index,
                    tool_id=item.get("tool_use_id"),
                    text=item.get("content"),
                )
            )
        else:
            # Unknown type - store as-is
            blocks.append(
                ContentBlock(
                    type=block_type or "unknown",
                    index=index,
                )
            )

    return blocks


def detect_tool_call(message: dict) -> ToolCall | None:
    """
    Detect if message contains a complete tool call.

    Tool call is complete when:
    - stop_reason is "tool_use" (in response_metadata)
    - tool_calls array is populated

    Args:
        message: Message dict from stream

    Returns:
        ToolCall or None
    """
    # Check stop_reason in response_metadata (LangGraph format)
    response_metadata = message.get("response_metadata", {})
    stop_reason = response_metadata.get("stop_reason")
    tool_calls = message.get("tool_calls", [])

    if stop_reason == "tool_use" and tool_calls:
        # Return first tool call
        tc = tool_calls[0]
        return ToolCall(
            id=tc.get("id", ""),
            name=tc.get("name", ""),
            args=tc.get("args", {}),
            type=tc.get("type", "tool_call"),
        )

    return None


def is_stream_complete(chunk: dict) -> bool:
    """
    Check if this is the final chunk in the stream.

    Final chunk indicators:
    - usage_metadata is present
    - stop_reason is present (in response_metadata)

    Args:
        chunk: Message chunk dict

    Returns:
        True if stream is complete
    """
    has_usage = chunk.get("usage_metadata") is not None

    # Check stop_reason in response_metadata (LangGraph format)
    response_metadata = chunk.get("response_metadata", {})
    has_stop_reason = response_metadata.get("stop_reason") is not None

    return has_usage or has_stop_reason


def parse_message_chunk(event_type: str, data: dict) -> ParsedChunk:
    """
    Parse messages/partial or messages/complete event into ParsedChunk.

    Args:
        event_type: SSE event type (e.g., "messages/partial")
        data: Message data dict

    Returns:
        ParsedChunk object
    """
    message_type = data.get("type", "unknown")
    message_id = data.get("id", "")
    content = data.get("content", [])
    usage_metadata = data.get("usage_metadata")
    response_metadata = data.get("response_metadata", {})

    # Extract stop_reason from response_metadata
    stop_reason = response_metadata.get("stop_reason")

    # Parse content blocks
    content_blocks = extract_content_blocks(content)

    # Parse usage
    usage = None
    if usage_metadata:
        usage = Usage(
            input_tokens=usage_metadata.get("input_tokens", 0),
            output_tokens=usage_metadata.get("output_tokens", 0),
            total_tokens=usage_metadata.get("total_tokens", 0),
        )

    # Detect tool calls
    tool_call = detect_tool_call(data)
    tool_calls = [tool_call] if tool_call else None

    # Extract metadata
    metadata = {
        "response_metadata": response_metadata,
        "additional_kwargs": data.get("additional_kwargs", {}),
    }

    return ParsedChunk(
        event_type=event_type,
        message_type=message_type,
        message_id=message_id,
        content_blocks=content_blocks,
        tool_calls=tool_calls,
        usage=usage,
        stop_reason=stop_reason,
        metadata=metadata,
    )
