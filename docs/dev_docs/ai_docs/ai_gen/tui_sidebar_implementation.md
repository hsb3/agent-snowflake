---
title: TUI Advanced Layout Implementation
date: 2026-01-24
status: completed
tags: [tui, ui, sidebar, status-bar, responsive]
---

# TUI Advanced Layout Implementation

Implementation of advanced TUI layout with optional sidebar, two-line status area, and responsive design.

## Changes Made

### 1. New Widgets

#### Sidebar (`src/repl_client/tui/widgets/sidebar.py`)
- Container with four tabs: Threads, Agents, Session, Tools
- Toggleable visibility (hidden by default)
- Two display modes:
  - Normal: 40% width
  - Expanded: 60% width
- Key methods:
  - `toggle()`: Toggle visibility
  - `expand()`: Toggle expanded mode
  - `populate_threads()`: Update threads list
  - `populate_agents()`: Update agents list
  - `populate_session_info()`: Update session info
  - `populate_tools()`: Update recent tool calls

#### StatusArea (`src/repl_client/tui/widgets/status_area.py`)
Replaces single-line StatusBar with two-line status area:

**Line 1 - UserStatusLine**:
- Agent: Current agent name
- Thread: Current thread ID (truncated)
- Tokens: Token count (formatted with K suffix)

**Line 2 - ClientInfoLine**:
- Connection: Connected/disconnected indicator
- Last update: Time since last update
- Status: Info/error/warning messages

### 2. App Layout Updates

#### Main Layout (`src/repl_client/tui/app.py`)
```
┌─ Header ──────────────────────────────────────┐
│ LangGraph REPL                                │
├────────────────────┬──────────────────────────┤
│                    │                          │
│  Messages          │  Sidebar (toggleable)    │
│  (fills space)     │  - Threads               │
│                    │  - Agents                │
│                    │  - Session               │
│                    │  - Tools                 │
├────────────────────┴──────────────────────────┤
│  > Input Area                                 │
├───────────────────────────────────────────────┤
│  Agent: xxx │ Thread: xxx │ Tokens: 1.2K      │ ← Line 1
│  ● Connected │ Last update: 2s ago            │ ← Line 2
├───────────────────────────────────────────────┤
│  Footer (key bindings)                        │
└───────────────────────────────────────────────┘
```

#### Key Bindings
- **F2**: Select agent (existing)
- **F3**: Select thread (existing)
- **F4**: Toggle sidebar visibility (new)
- **F5**: Toggle sidebar expand mode (new)
- **Ctrl+C**: Quit
- **Ctrl+L**: Clear messages

### 3. Responsive Design

#### Layout Behavior
- Messages container uses `width: 1fr` (fills available space)
- When sidebar hidden: messages take full width
- When sidebar visible (40%): messages automatically resize
- When sidebar expanded (60%): messages get even narrower
- All handled automatically by Textual's layout system

#### CSS Updates (`src/repl_client/tui/repl.tcss`)
- Added `#main-content` Horizontal container
- Messages container width changed from `100%` to `1fr`
- Sidebar has conditional CSS classes for visibility/expansion
- StatusArea height set to 2 lines

### 4. Testing

#### New Tests
- `tests/repl_client/tui/test_sidebar.py`: 8 tests for sidebar functionality
- `tests/repl_client/tui/test_status_area.py`: 10 tests for status area

#### Updated Tests
- `tests/repl_client/tui/test_app.py`: Updated to use StatusArea instead of StatusBar

All 98 TUI tests pass.

### 5. Demo

**Demo script**: `scripts/repl_client/demo_tui_sidebar.py`

Run with:
```bash
uv run python scripts/repl_client/demo_tui_sidebar.py
```

Features demonstrated:
- Sidebar toggle (F4)
- Sidebar expand (F5)
- Populated content in all tabs
- Two-line status area
- Responsive layout

## Usage

### For Users

1. **Toggle sidebar**: Press F4
2. **Expand sidebar**: Press F5 (expands if hidden, toggles if visible)
3. **View threads**: Sidebar → Threads tab
4. **View agents**: Sidebar → Agents tab
5. **View session info**: Sidebar → Session tab
6. **View tool calls**: Sidebar → Tools tab (Phase 3)

### For Developers

#### Updating Sidebar Content

```python
# In REPLApp
self._sidebar.populate_threads(threads, current_thread_id)
self._sidebar.populate_agents(agents, current_agent_id)
self._sidebar.populate_session_info(
    thread_id=thread_id,
    agent_id=agent_id,
    tokens={"total": 1000, "input": 600, "output": 400},
    model="claude-sonnet-4-5",
)
self._sidebar.populate_tools(recent_tool_calls)
```

#### Updating Status Area

```python
# User status (line 1)
self._status_area.set_agent("agent_name")
self._status_area.set_thread("thread_id")
self._status_area.set_tokens(1234)

# Client info (line 2)
self._status_area.set_connected(True)
self._status_area.set_last_update("2s ago")
self._status_area.set_status("Ready")  # info level
self._status_area.set_status("Error", error=True)  # error level
self._status_area.set_status("Warning", warning=True)  # warning level
```

## Implementation Notes

### Sidebar Population
- Sidebar content is updated when sidebar becomes visible
- Thread cache (`_threads_cache`) maintained for sidebar display
- Agents list already cached for agent selection
- Tool calls tracking is placeholder (Phase 3 feature)

### StatusArea vs StatusBar
- StatusBar still exists for backward compatibility
- New code should use StatusArea
- StatusArea provides same interface as StatusBar plus additional methods
- All app references updated to use StatusArea

### Responsive Behavior
- No manual width calculations needed
- Textual's Horizontal container handles layout
- Sidebar CSS controls width via classes (visible, expanded)
- Messages container automatically fills remaining space

## Future Enhancements

### Phase 3 (Tool Tracking)
- Track tool calls during streaming
- Store in app state
- Update sidebar tools tab in real-time
- Allow expanding tool outputs in sidebar

### Potential Features
- Clickable thread/agent items in sidebar
- Thread/agent search/filter
- Pinned threads
- Session history
- Export session data
- Collapsible sections in sidebar tabs

## Files Changed

**New files**:
- `src/repl_client/tui/widgets/sidebar.py`
- `src/repl_client/tui/widgets/status_area.py`
- `tests/repl_client/tui/test_sidebar.py`
- `tests/repl_client/tui/test_status_area.py`
- `scripts/repl_client/demo_tui_sidebar.py`

**Modified files**:
- `src/repl_client/tui/widgets/__init__.py`
- `src/repl_client/tui/app.py`
- `src/repl_client/tui/repl.tcss`
- `tests/repl_client/tui/test_app.py`

## Success Criteria

All success criteria from specification met:

- ✅ F4 toggles sidebar visibility
- ✅ F5 expands sidebar to full mode
- ✅ Status shows on two lines
- ✅ Chat area width adjusts when sidebar opens
- ✅ All existing functionality still works
- ✅ All tests pass (98/98)
- ✅ Demo script created and functional
