"""Streaming types for Layer 4.

Defines ParsedChunk and ChunkType enum for StreamHandler output.
"""

from dataclasses import dataclass
from enum import Enum, auto

from repl_client.core.parsers import ToolCall, Usage


class ChunkType(Enum):
    """Type discriminator for ParsedChunk."""

    TEXT_DELTA = auto()
    TOOL_CALL_START = auto()
    TOOL_CALL_COMPLETE = auto()
    TOOL_RESULT = auto()
    INTERRUPT = auto()
    USAGE = auto()
    METADATA = auto()
    ERROR = auto()


@dataclass
class ToolResult:
    """Tool execution result."""

    tool_id: str
    tool_name: str
    result: str
    status: str = "success"


@dataclass
class Interrupt:
    """HITL interrupt signal (Phase 2)."""

    # Stub for Phase 2
    pass


@dataclass
class ParsedChunk:
    """Parsed chunk from StreamHandler.

    Uses chunk_type discriminator to determine which fields are populated.

    Field usage by chunk_type:
    - TEXT_DELTA: text_delta, message_id, namespace
    - TOOL_CALL_START: tool_call (partial), namespace
    - TOOL_CALL_COMPLETE: tool_call (complete), namespace
    - TOOL_RESULT: tool_result, namespace
    - INTERRUPT: interrupt, namespace (Phase 2)
    - USAGE: usage
    - METADATA: metadata
    - ERROR: metadata (contains error info)
    """

    chunk_type: ChunkType
    namespace: tuple = ()
    message_id: str | None = None
    text_delta: str | None = None
    tool_call: ToolCall | None = None
    tool_result: ToolResult | None = None
    interrupt: Interrupt | None = None
    usage: Usage | None = None
    metadata: dict | None = None
