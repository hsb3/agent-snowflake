---
title: "REPL TUI Application Guide"
date: 2026-01-24
tags: ["tui", "repl", "textual", "guide"]
---

# REPL TUI Application Guide

Complete Textual-based terminal user interface for interacting with LangGraph agents.

## Overview

The REPL TUI provides a rich, interactive interface for:
- Streaming conversations with LangGraph agents
- Real-time message display with markdown rendering
- Tool call visualization and approval (HITL)
- Session management (threads, agents, tokens)
- Command system for navigation and control

## Architecture

```
Layer 8: TUI App (tui/app.py)
├── Widgets (tui/widgets/)
│   ├── UserMessage - User message display
│   ├── AssistantMessage - AI responses with markdown streaming
│   ├── ToolCallMessage - Tool execution with collapsible output
│   ├── ChatInput - Multi-line input with history
│   ├── StatusBar - Connection/agent/thread/token info
│   └── LoadingWidget - Animated loading indicator
├── HITL Handler (tui/hitl.py)
│   └── Approval prompts for tool execution
└── Integrations
    ├── LangGraphClient (Layer 1) - HTTP/SSE
    ├── StreamHandler (Layer 4) - Chunk processing
    ├── SessionState (Layer 3) - State tracking
    └── Config (Layer 0) - Environment config
```

## Running the TUI

### Prerequisites

1. **LangGraph server running**:
   ```bash
   make dev-server
   # Or: langgraph dev
   ```

2. **Environment configured**:
   ```bash
   # .env file
   LANGGRAPH_DEV_SERVER_PORT=2024
   REPL_DEFAULT_AGENT=agent_enhanced  # Optional
   REPL_DEBUG=false  # Optional
   ```

### Launch Methods

**Method 1: Python module**
```bash
uv run python -m repl_client.tui
```

**Method 2: Entry point** (if installed)
```bash
uv run repl-tui
```

**Method 3: Demo script**
```bash
uv run python scripts/demo_tui_full.py
```

## Features

### 1. Message Display

**User messages**: Green left border
```
> What tables are available?
```

**AI messages**: Cyan left border with markdown
```
Here are the available tables:
- customers
- orders
- products
```

**Tool calls**: Yellow border with collapsible output
```
Tool: sql_db_list_tables
(database='snowflake')
✓ Success

Output:
customers, orders, products
... (click to expand)
```

### 2. Chat Input

**Features**:
- Multi-line input (Ctrl+J for newlines)
- History navigation (Up/Down on first/last line)
- Enter to submit
- Command detection (starts with `/`)

**Example**:
```
> Can you query the customers table
> for all records where status='active'?
```

### 3. Status Bar

Shows real-time session info:
```
Agent: agent_enhanced | Thread: abc12345 | Connecting... | 1.2K tokens | ●
```

Components:
- **Agent**: Current agent name
- **Thread**: Thread ID (first 8 chars)
- **Status**: Connection/activity status
- **Tokens**: Context token count
- **Indicator**: Connection state (● = connected, ○ = disconnected)

### 4. Commands

All commands start with `/`:

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show available commands | `/help` |
| `/agents` | List all agents | `/agents` |
| `/agents <id>` | Switch to agent | `/agents agent_enhanced` |
| `/new` | Create new thread | `/new` |
| `/info` | Show session info | `/info` |
| `/clear` | Clear message history | `/clear` |

### 5. Key Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `Enter` | Submit | Send message |
| `Ctrl+J` | New line | Insert newline in input |
| `Ctrl+L` | Clear | Clear all messages |
| `Ctrl+C` | Quit | Exit application |
| `Up/Down` | History | Navigate input history |
| `Click` | Expand | Toggle tool output expansion |

## Workflow Examples

### Example 1: Basic Query

1. Launch TUI: `uv run python -m repl_client.tui`
2. Wait for connection (status bar shows "Ready")
3. Type message: `Show me all tables`
4. Press Enter
5. Watch streaming response
6. See tool calls in yellow panels

### Example 2: Agent Switching

1. List agents: `/agents`
2. See available agents with IDs
3. Switch: `/agents agent_basic`
4. Status bar updates with new agent
5. Continue conversation with new agent

### Example 3: Thread Management

1. Start conversation in current thread
2. Create new thread: `/new`
3. Status bar shows new thread ID
4. Previous thread history preserved on server
5. Can resume old thread later (future feature)

### Example 4: Tool Approval (HITL)

1. Agent requests tool execution
2. Yellow tool panel appears
3. Approval prompt shows tool details
4. User approves/rejects (Phase 2: auto-approve)
5. Tool executes or skips
6. Result displayed in tool panel

## Implementation Details

### File Locations

```
src/repl_client/tui/
├── __init__.py          # Package exports
├── __main__.py          # Entry point
├── app.py               # Main REPLApp class
├── hitl.py              # HITL handler for TUI
├── repl.tcss            # Textual CSS styling
└── widgets/             # UI components
    ├── __init__.py
    ├── input.py         # ChatInput + ChatTextArea
    ├── messages.py      # UserMessage, AssistantMessage, ToolCallMessage
    ├── status.py        # StatusBar
    ├── loading.py       # LoadingWidget
    └── history.py       # HistoryManager
```

### Key Classes

**REPLApp** (`app.py`):
- Main Textual application
- Coordinates all widgets and backend
- Handles commands and message routing
- Manages streaming flow

**ChatInput** (`widgets/input.py`):
- Multi-line text input
- History navigation
- Mode detection (command vs message)

**AssistantMessage** (`widgets/messages.py`):
- Uses MarkdownStream for efficient rendering
- Supports live streaming updates
- Methods: `append_content()`, `stop_stream()`

**ToolCallMessage** (`widgets/messages.py`):
- Multi-state: pending → success/error/rejected
- Collapsible output (3-line preview)
- Click to expand/collapse

**StatusBar** (`widgets/status.py`):
- Reactive properties (agent, thread, tokens)
- Status messages with error styling
- Connection indicator

### Streaming Flow

1. User submits message
2. `_send_message()` creates widgets and starts stream
3. `_handle_stream()` processes ParsedChunks:
   - TEXT_DELTA → append to AssistantMessage
   - TOOL_CALL_COMPLETE → create ToolCallMessage
   - TOOL_RESULT → update ToolCallMessage
   - INTERRUPT → show HITL prompt
   - USAGE → update token count
4. Finalize: stop stream, update status, re-enable input

### Testing

**Unit tests**:
```bash
uv run pytest tests/repl_client/tui/test_app.py -v
```

Tests cover:
- Widget composition
- Command handling
- Message mounting
- Key bindings
- State management

**Integration tests** (require running server):
```bash
# Start server
make dev-server

# Run integration tests
uv run pytest tests/repl_client/tui/test_app_integration.py -v -m integration
```

## Configuration

### Environment Variables

```bash
# .env file
LANGGRAPH_DEV_SERVER_PORT=2024       # Server port
REPL_DEFAULT_AGENT=agent_enhanced    # Default agent ID
REPL_DEBUG=false                     # Debug logging
```

### CSS Customization

Edit `src/repl_client/tui/repl.tcss` to customize:
- Colors (borders, text, backgrounds)
- Spacing (padding, margins)
- Layout (heights, widths)

Example - change AI message border color:
```css
AssistantMessage Markdown {
    border-left: thick magenta;  /* Was cyan */
}
```

## Debugging

### Enable Debug Logging

```bash
# In .env
REPL_DEBUG=true

# Run TUI
uv run python -m repl_client.tui
```

Logs written to `.repl/client.log`

### Textual DevTools

```bash
# In one terminal
textual console

# In another terminal
uv run python -m repl_client.tui
```

Shows live updates, events, and DOM tree.

### Common Issues

**Connection fails**:
- Check server is running: `make dev-server`
- Verify port in `.env` matches server
- Check `.repl/client.log` for errors

**Messages don't stream**:
- Verify agent exists: `/agents`
- Check thread created: `/info`
- Look for errors in status bar

**History not working**:
- History saved to `.repl/history.jsonl`
- Ensure directory is writable
- Up/Down only works on first/last line

## Future Enhancements

### Phase 3 Features

- **Interactive HITL**: Arrow-key menu for approval (like deepagents)
- **Thread resumption**: List and switch between threads
- **Enhanced input**: Auto-completion, syntax highlighting
- **Status line**: Live token tracking during streaming
- **Export**: Save conversation to markdown
- **Themes**: Multiple color schemes

### Possible Extensions

- **Multi-pane**: Side-by-side comparisons
- **Image support**: iTerm2/Kitty protocols
- **Notifications**: Desktop alerts for long-running tasks
- **Shortcuts**: Custom keybindings
- **Plugins**: User-defined widget extensions

## References

- [Textual Documentation](https://textual.textualize.io/)
- [repl_components.jsonc](../../repl_components.jsonc) - Architecture spec
- [repl_spec.json](../../repl_spec.json) - Requirements spec
- [deepagents CLI](https://github.com/deepagents/deepagents-cli) - Reference implementation
