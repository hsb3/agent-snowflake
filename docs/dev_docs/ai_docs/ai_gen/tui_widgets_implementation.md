---
title: TUI Message Widgets Implementation
date: 2026-01-24
status: complete
related_docs:
  - spec-repl-v1/repl_spec.json
  - spec-repl-v1/repl_components.jsonc
---

# TUI Message Widgets Implementation

## Overview

Implemented Textual message widgets for REPL TUI using TDD approach. Based on deepagents patterns for optimal UX.

## Components Delivered

### 1. UserMessage Widget
**Location**: `src/repl_client/tui/widgets/messages.py`

**Features**:
- Static widget with green border (thick)
- Styled prefix "> " in bold green
- Auto height
- Safe from markup injection

**Usage**:
```python
from repl_client.tui.widgets import UserMessage
widget = UserMessage("Hello, agent!")
```

### 2. AssistantMessage Widget
**Location**: `src/repl_client/tui/widgets/messages.py`

**Features**:
- Vertical container with Markdown support
- Efficient streaming via MarkdownStream
- Cyan border styling
- Methods: `append_content()`, `stop_stream()`, `set_content()`

**Usage**:
```python
from repl_client.tui.widgets import AssistantMessage

# Streaming
widget = AssistantMessage()
await widget.append_content("Streaming ")
await widget.append_content("content...")
await widget.stop_stream()

# Set full content
await widget.set_content("Full markdown content")
```

### 3. ToolCallMessage Widget
**Location**: `src/repl_client/tui/widgets/messages.py`

**Features**:
- Multi-state: pending, success, error, rejected
- Collapsible output (3-line/200-char preview)
- Click to toggle expansion
- Auto-expand for errors
- Filters large args for file tools

**Usage**:
```python
from repl_client.tui.widgets import ToolCallMessage

widget = ToolCallMessage("sql_db_query", {"query": "SELECT * FROM users"})
widget.set_success("Found 10 users")  # Or set_error(), set_rejected()
widget.toggle_output()  # Expand/collapse
```

## Tests

**Location**: `tests/repl_client/tui/test_messages.py`

**Coverage**:
- 17 unit tests
- All widgets tested for creation, state transitions, content updates
- Markup safety verified
- Arg filtering tested

**Run**:
```bash
uv run pytest tests/repl_client/tui/test_messages.py -v
```

**Results**: ✓ 17/17 passed

## Demo App

**Location**: `scripts/repl_client/demo_tui_messages.py`

**Features**:
- Shows all widget types in action
- Demonstrates streaming
- Key bindings:
  - `q` - Quit
  - `t` - Toggle tool output
  - `s` - Stream to assistant

**Run**:
```bash
uv run python scripts/repl_client/demo_tui_messages.py
```

## Design Patterns from deepagents

### 1. UserMessage
- Rich Text object for styled prefix + unstyled content
- Prevents markup injection

### 2. AssistantMessage
- MarkdownStream for smooth incremental rendering
- No full re-render on each chunk

### 3. ToolCallMessage
- Multi-state with visual indicators
- Preview/expand pattern (3 lines or 200 chars)
- Click to toggle
- Errors always expanded
- Large args filtered for display

## CSS Styling

- **Green**: User messages
- **Cyan**: Assistant messages
- **Yellow**: Tool calls (pending)
- **Red**: Errors
- **Green**: Success
- **Muted**: Secondary text

## Configuration Changes

### pyproject.toml
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/agent_snowflake", "src/repl_client"]

[tool.pytest.ini_options]
pythonpath = [".", "src"]
```

### Dependencies Added
```toml
dependencies = [
    "textual>=7.3.0",
    # ... existing deps
]

[dependency-groups]
dev = [
    "pytest-asyncio>=1.3.0",
    # ... existing deps
]
```

## Issues Resolved

### Test Import Conflict
**Problem**: `tests/repl_client/__init__.py` conflicted with `src/repl_client/`

**Solution**: Removed `__init__.py` from test directories - tests don't need to be packages

**Files Removed**:
- `tests/repl_client/__init__.py`
- `tests/repl_client/tui/__init__.py`

## Documentation

**README**: `src/repl_client/tui/widgets/README.md`
- Usage examples for all widgets
- API documentation
- Design patterns explanation
- Testing instructions

## Next Steps

These widgets are ready for integration into the REPL TUI:

1. **Layer 6 Integration**: Use in main TUI layout
2. **Streaming Handler**: Connect to streaming/handler.py output
3. **HITL Integration**: Use ToolCallMessage for tool approval prompts
4. **Layout Manager**: Create scrolling conversation area

## Files Created

```
src/repl_client/tui/widgets/
├── __init__.py (updated)
├── messages.py (new)
└── README.md (new)

tests/repl_client/tui/
└── test_messages.py (new)

scripts/
└── demo_tui_messages.py (new)

docs/dev_docs/
└── tui_widgets_implementation.md (this file)
```

## Success Metrics

- ✅ All 17 tests passing
- ✅ Demo app runs without errors
- ✅ Follows deepagents patterns
- ✅ TDD approach used throughout
- ✅ Comprehensive documentation
- ✅ Safe from markup injection
- ✅ Efficient streaming support
