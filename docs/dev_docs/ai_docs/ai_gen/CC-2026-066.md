---
doc_id: CC-2026-066
title: "ChatInput Widget Implementation"
date: 2026-01-24
type: solution
project: repl_client
focus: tui
status: complete
tags: [tui, widgets, repl, textual, history, input]
---

# ChatInput Widget with History Support

## Overview

Implemented a ChatInput widget with history and multi-line support using TDD, based on patterns from deepagents. The widget provides a rich input experience for the REPL TUI.

## Components Delivered

### 1. HistoryManager (`src/repl_client/tui/widgets/history.py`)

Command history manager with file persistence.

**Features:**
- JSON-lines file format for concurrent-safe append-only writes
- Automatic deduplication of consecutive entries
- Prefix-based search navigation
- Temporary input saving during navigation
- Automatic compaction when exceeding 2x max entries
- Skips empty entries and slash commands

**Key Methods:**
- `add(text)` - Add entry to history
- `get_previous(current_input, prefix="")` - Navigate backward
- `get_next(prefix="")` - Navigate forward
- `reset_navigation()` - Clear navigation state

### 2. ChatTextArea (`src/repl_client/tui/widgets/input.py`)

TextArea subclass with custom key handling.

**Features:**
- Shift+Enter, Ctrl+J for newline insertion
- Plain Enter for submission
- Up/Down arrow history navigation (on first/last line)
- Ctrl+A for select all
- Custom messages: Submitted, HistoryPrevious, HistoryNext

**Key Bindings:**
- `Enter` → Submit (if not modified)
- `Shift+Enter`, `Ctrl+J`, `Alt+Enter`, `Ctrl+Enter` → Insert newline
- `Up` (on first line) → Previous history
- `Down` (on last line) → Next history
- `Ctrl+A` → Select all

### 3. ChatInput (`src/repl_client/tui/widgets/input.py`)

Main chat input widget with prompt, text area, and history integration.

**Features:**
- Vertical container with prompt indicator (">" symbol)
- Mode detection (normal, command `/`, bash `!`)
- Automatic history persistence
- Focus management
- Custom messages: Submitted, ModeChanged

**Properties:**
- `value` - Get/set current input text
- `mode` - Current input mode (reactive)
- `input_widget` - Access to underlying TextArea

**Methods:**
- `focus_input()` - Focus the text area
- `clear_input()` - Clear the input
- `set_disabled(disabled=True)` - Enable/disable input
- `set_submit_enabled(enabled=True)` - Enable/disable submission

### 4. Tests (`tests/repl_client/tui/test_input.py`)

Comprehensive test suite with 24 tests covering:

**HistoryManager Tests (12):**
- Initialization
- Adding entries
- Skipping empty/slash commands/duplicates
- Navigation (previous/next)
- Temp input preservation
- Prefix search
- Persistence to file
- Max entries limit

**ChatInput Tests (12):**
- Widget initialization
- Submit message emission
- Mode detection (command, bash, normal)
- Multiline input
- Input clearing
- History integration
- Navigation (up/down)
- Focus management
- Value property
- Mode change messages

**All tests pass:** ✓ 24/24

### 5. Demo App (`scripts/repl_client/demo_tui_input.py`)

Interactive demo application showcasing features.

**Features:**
- Message log showing submitted inputs
- Color-coded modes (normal, command, bash)
- Real-time mode indicator
- Welcome screen with usage instructions

**Run:**
```bash
uv run python scripts/repl_client/demo_tui_input.py
```

## Design Patterns from deepagents

### History Management
- File-based persistence with JSON-lines format
- Concurrent-safe append-only writes
- Lazy compaction (only when needed)
- Prefix-based filtering for smart navigation

### Input Handling
- Separate TextArea subclass for key event isolation
- Message-based communication between components
- Mode detection via reactive properties
- Clean separation of concerns

### Testing Strategy
- TDD approach (tests written first)
- Async test support with Textual pilot
- Message handler verification
- State transition testing

## Integration Points

### Export in __init__.py
```python
from .history import HistoryManager
from .input import ChatInput, ChatTextArea

__all__ = ["ChatInput", "ChatTextArea", "HistoryManager", ...]
```

### Usage Example
```python
from pathlib import Path
from textual.app import App
from repl_client.tui.widgets import ChatInput

class MyApp(App):
    def compose(self):
        yield ChatInput(
            cwd=Path.cwd(),
            history_file=Path.cwd() / ".repl" / "history.jsonl"
        )

    def on_chat_input_submitted(self, message: ChatInput.Submitted):
        # Handle submitted text
        text = message.value
        mode = message.mode  # "normal", "command", or "bash"

    def on_chat_input_mode_changed(self, message: ChatInput.ModeChanged):
        # Handle mode changes
        mode = message.mode
```

## Files Created/Modified

**New Files:**
- `/Users/henry/Developer/_SANDBOX/agent-snowflake/src/repl_client/tui/widgets/history.py`
- `/Users/henry/Developer/_SANDBOX/agent-snowflake/src/repl_client/tui/widgets/input.py`
- `/Users/henry/Developer/_SANDBOX/agent-snowflake/tests/repl_client/tui/test_input.py`
- `/Users/henry/Developer/_SANDBOX/agent-snowflake/scripts/repl_client/demo_tui_input.py`

**Modified Files:**
- `/Users/henry/Developer/_SANDBOX/agent-snowflake/src/repl_client/tui/widgets/__init__.py` - Added exports

**Deleted Files:**
- `tests/repl_client/__init__.py` - Removed to fix import shadowing
- `tests/repl_client/tui/__init__.py` - Removed to fix import shadowing
- `tests/repl_client/commands/__init__.py` - Removed to fix import shadowing

## Bug Fixes

### Import Shadowing Issue
Tests were failing because `tests/repl_client/__init__.py` created a package that shadowed `src/repl_client`.

**Solution:** Removed all `__init__.py` files from `tests/repl_client/*` directories to allow pytest to properly import from `src/`.

**Impact:** This fix also resolved import issues for other existing tests in the codebase.

## Next Steps

1. **Autocomplete Support** - Add file/command completion (following deepagents patterns)
2. **CompletionPopup Widget** - Display suggestions above input
3. **Integration** - Wire into main REPL app
4. **Keybindings** - Add to footer display
5. **Styling** - Customize colors/themes

## Reference

**deepagents source:**
- `/Users/henry/Developer/OSS/deepagents-20260123/libs/deepagents-cli/deepagents_cli/widgets/history.py`
- `/Users/henry/Developer/OSS/deepagents-20260123/libs/deepagents-cli/deepagents_cli/widgets/chat_input.py`

## Verification

```bash
# Run all tests
uv run pytest tests/repl_client/tui/test_input.py -v

# Run demo
uv run python scripts/repl_client/demo_tui_input.py

# Test import
uv run python -c "from repl_client.tui.widgets import ChatInput, HistoryManager; print('✓')"
```

All components tested and working correctly.
