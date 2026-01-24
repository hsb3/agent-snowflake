---
title: Layer 5 HITL Handler Implementation
date: 2026-01-23
status: complete
layer: 5
phase: 2
---

# Layer 5: HITL Handler Implementation

## Overview

Layer 5 provides Human-in-the-Loop (HITL) interrupt handling for Phase 2 of the REPL. It allows users to approve or reject tool calls before execution.

**Status**: ✅ Complete
**Test Coverage**: 17/17 tests passing
**Type Safety**: All checks pass

## Architecture

### Components

1. **HITLHandler** (`src/repl_client/streaming/hitl.py`)
   - Main handler class for HITL interrupts
   - Integrates with Renderer (Layer 6) and ToolRenderRegistry

2. **Interrupt** (`src/repl_client/streaming/types.py`)
   - Dataclass representing HITL interrupt signals
   - Contains interrupt ID and value payload

### Dependencies

- **Layer 2** (parsers): Uses `ToolCall` and other types
- **Layer 6** (renderer): Uses `Renderer` for UI output
- **Layer 6** (content_blocks): Uses `ToolRenderRegistry` for tool-specific formatting

## Implementation Details

### HITLHandler Class

```python
class HITLHandler:
    def __init__(self, renderer: Renderer, tool_registry: ToolRenderRegistry | None = None)
    def handle_interrupt(self, interrupt: Interrupt, session: SessionState) -> dict
    def _show_approval_prompt(self, tool_name: str, tool_args: dict) -> bool
    def _format_tool_preview(self, tool_name: str, tool_args: dict) -> str
    def _build_resume_command(self, approved: bool, interrupt: Interrupt) -> dict
```

### Interrupt Dataclass

```python
@dataclass
class Interrupt:
    id: str
    value: dict  # The interrupt payload (tool name, args, etc.)
```

### Approval Flow

1. **Interrupt Detection**: StreamHandler detects `__interrupt__` in 'updates' stream
2. **Display Tool Info**: HITL handler formats tool preview using registry
3. **Get User Decision**: Simple y/n prompt (Phase 2 - arrow keys in Phase 3)
4. **Build Resume Command**: Create `{"resume": {"approve": bool}}` payload
5. **Resume Stream**: Client sends resume command to continue execution

## Tool Preview Formatting

### Builtin Formatters

- **sql_db_query**: Extracts and displays SQL with syntax highlighting info
- Generic fallback: Shows tool name and JSON-formatted args

### Custom Formatters

```python
registry = ToolRenderRegistry()

def custom_formatter(args: dict) -> str:
    return f"Custom format: {args}"

registry.register("my_tool", custom_formatter)
handler = HITLHandler(renderer, tool_registry=registry)
```

## Test Coverage

### Test Categories

1. **Approval Prompt Tests** (6 tests)
   - User approves with 'y' or 'yes'
   - User rejects with 'n' or 'no'
   - Case insensitive input
   - Invalid input reprompts

2. **Tool Preview Tests** (3 tests)
   - SQL query tool formatting
   - Generic tool fallback
   - Tool with no args

3. **Resume Command Tests** (2 tests)
   - Build approve command
   - Build reject command

4. **Integration Tests** (3 tests)
   - Full interrupt handling flow
   - Tool info extraction
   - Renderer integration

5. **Registry Tests** (3 tests)
   - Custom formatter registration
   - Builtin SQL formatter
   - Fallback for unknown tools

### Running Tests

```bash
# Run HITL tests only
uv run pytest tests/repl_client/streaming/test_hitl.py -v

# Run with coverage
uv run pytest tests/repl_client/streaming/test_hitl.py --cov=repl_client.streaming.hitl

# Type check
uv run ty check src/repl_client/streaming/hitl.py
```

## Usage Example

```python
from repl_client.streaming.hitl import HITLHandler
from repl_client.streaming.types import Interrupt
from repl_client.ui.renderer import Renderer
from repl_client.core.session import SessionState

# Setup
renderer = Renderer()
handler = HITLHandler(renderer=renderer)
session = SessionState()

# Handle interrupt
interrupt = Interrupt(
    id="int_001",
    value={
        "tool": "sql_db_query",
        "args": {"query": "SELECT * FROM users"}
    }
)

# This will show approval prompt and return resume command
resume_cmd = handler.handle_interrupt(interrupt, session)
# Returns: {"resume": {"approve": True/False}}
```

## Integration with Main Loop

```python
# In REPLLoop._handle_stream()
for parsed in stream_handler.process_stream(chunks):
    if parsed.chunk_type == ChunkType.INTERRUPT:
        # Get approval from user
        resume_cmd = hitl_handler.handle_interrupt(
            parsed.interrupt,
            session
        )

        # Resume with approval decision
        resume_chunks = client.resume_after_interrupt(
            thread_id=session.current_thread_id,
            assistant_id=session.current_assistant_id,
            command=resume_cmd
        )

        # Continue processing resumed stream
        for resumed in stream_handler.process_stream(resume_chunks):
            # ... render resumed chunks
```

## Phase 2 vs Phase 3

### Phase 2 (Current)
- Simple y/n text input
- Basic tool preview with panels
- Builtin SQL formatter only

### Phase 3 (Future)
- Arrow key selection (approve/reject/modify)
- Rich interactive prompts with prompt_toolkit
- More builtin formatters (AskUserQuestion, etc.)
- Tool modification before approval
- Status line integration

## Design Decisions

1. **Simple Input for Phase 2**: Using basic `input()` for MVP, will upgrade to arrow keys in Phase 3
2. **Registry Pattern**: Extensible tool formatting via registry, easy to add custom formatters
3. **Loose Coupling**: Handler only depends on Renderer interface, not implementation
4. **Session Parameter**: Included for future use (Phase 3 might track approval history)
5. **Resume Command Format**: Follows LangGraph API spec exactly

## Files Modified/Created

### Created
- `src/repl_client/streaming/hitl.py` - HITL handler implementation
- `tests/repl_client/streaming/test_hitl.py` - Comprehensive test suite
- `scripts/debug/demo_hitl.py` - Demo script

### Modified
- `src/repl_client/streaming/types.py` - Added `id` and `value` fields to Interrupt

## Next Steps

1. **Layer 4 Integration**: Update StreamHandler to detect and yield INTERRUPT chunks
2. **Client Integration**: Add `resume_after_interrupt()` method to LangGraphClient
3. **Main Loop**: Wire HITL handler into REPLLoop._handle_stream()
4. **Phase 3 Enhancements**: Upgrade to arrow key selection with prompt_toolkit

## References

- Spec: `/repl_components.jsonc` - Layer 5 specification
- Dependencies: Layer 2 (parsers), Layer 6 (renderer)
- API Docs: `docs/openapi.json` - RunCreateStateful schema for resume command
