# REPL Client Scripts

Test, demo, and debugging scripts for the `repl_client` package (classic async REPL).

## Scripts

### Integration Tests

#### `test_repl_client.py`
Quick integration test to verify REPL client works with LangGraph server.

**Purpose:**
- Test basic client functionality
- Verify connection to server
- Test agent and thread operations
- Validate streaming

**Prerequisites:**
```bash
# Start LangGraph dev server first
langgraph dev
```

**Usage:**
```bash
uv run python scripts/repl_client/test_repl_client.py
```

**Tests:**
1. Connection to `http://localhost:2024`
2. List agents
3. Create thread
4. Get thread details
5. Stream message to agent
6. List threads

**Expected Output:**
```
✅ Connected to LangGraph server
✅ Found N agents
✅ Created thread: thread_xxx
✅ Thread status: idle
✅ Received streaming events
✅ All tests passed!
```

---

#### `test_hitl_manual.py`
Manual verification script for Human-in-the-Loop (HITL) flow.

**Purpose:**
- Test full HITL approval/rejection flow
- Demonstrate interrupt detection and handling
- Validate resume after interrupt

**Prerequisites:**
- LangGraph server running (`http://localhost:2024`)
- Agent with HITL enabled (e.g., `agent_enhanced`)
- Agent must have `interrupt_before` or `interrupt_after` configured

**Usage:**
```bash
uv run python scripts/repl_client/test_hitl_manual.py
```

**Expected Flow:**
1. Script sends: "Query the customers table"
2. Agent plans to use `sql_db_query` tool
3. Server sends `__interrupt__` signal
4. Script shows approval prompt with SQL query
5. User types 'y' or 'n'
6. Script resumes execution
7. If approved: Shows query results
8. If rejected: Shows agent's response to rejection

---

### TUI Demos

All TUI demo scripts demonstrate Textual-based widgets and components used in the REPL interface.

#### `demo_tui_full.py`
Complete REPL TUI demonstration with all features.

**Purpose:**
- Show full integrated REPL app
- Demonstrate all widgets working together
- Test streaming, HITL, and commands

**Prerequisites:**
```bash
# LangGraph server must be running
make dev-server
```

**Usage:**
```bash
uv run python scripts/repl_client/demo_tui_full.py
```

**Features Demonstrated:**
- Connection to LangGraph server
- Agent and thread management
- Streaming messages with live updates
- User/AI/Tool message widgets
- Status bar with connection/agent/thread info
- Command system (`/help`, `/agents`, `/new`, `/info`, `/clear`)
- HITL interrupts (if triggered)

**Key Bindings:**
- `Enter` - Send message
- `Ctrl+J` - New line in input
- `Up/Down` - History navigation
- `Ctrl+L` - Clear messages
- `Ctrl+C` - Quit

---

#### `demo_tui_messages.py`
Demo of message widgets (User, AI, Tool).

**Purpose:**
- Show individual message widget styling
- Test streaming to AI messages
- Demonstrate tool call states

**Usage:**
```bash
uv run python scripts/repl_client/demo_tui_messages.py
```

**Key Bindings:**
- `q` - Quit
- `t` - Toggle tool output expansion
- `s` - Demo streaming to assistant widget

**Widgets Shown:**
- `UserMessage` - Green styled user input
- `AssistantMessage` - Cyan styled with markdown streaming
- `ToolCallMessage` - Tool calls with collapsible output, multiple states

---

#### `demo_tui_sidebar.py`
Demo of sidebar with agent/thread info.

**Purpose:**
- Show sidebar layout and styling
- Demonstrate agent/thread display
- Test info sections

**Usage:**
```bash
uv run python scripts/repl_client/demo_tui_sidebar.py
```

**Features:**
- Agent information panel
- Thread information panel
- Connection status
- Key bindings help

---

#### `demo_tui_input.py`
Demo of chat input widget with multi-line support.

**Purpose:**
- Test ChatInput widget
- Show multi-line input handling
- Demonstrate history navigation

**Usage:**
```bash
uv run python scripts/repl_client/demo_tui_input.py
```

**Key Bindings:**
- `Enter` - Submit message (or new line if Shift held)
- `Ctrl+J` - Force new line
- `Up/Down` - Navigate history (when on first/last line)
- `Ctrl+C` - Quit

---

#### `demo_tui_status.py`
Demo of status bar widget.

**Purpose:**
- Show status bar layout
- Test status indicators
- Demonstrate mode changes

**Usage:**
```bash
uv run python scripts/repl_client/demo_tui_status.py
```

**Status Elements:**
- Connection indicator (connected/disconnected)
- Agent name
- Thread ID
- Message count
- Current mode

---

## Architecture Context

These scripts support the **repl_client** package, which implements a classic async REPL for interacting with LangGraph agents.

### Package Structure

```
src/repl_client/
├── core/           # HTTP client, config, logging
├── streaming/      # SSE stream handling, HITL
├── tui/           # Textual-based UI components
│   ├── app.py     # Main TUI app
│   └── widgets/   # Custom widgets
└── ui/            # Rich-based rendering
```

### Design Philosophy

- **Async-first**: Uses `asyncio` and `httpx` for non-blocking I/O
- **Modular**: Separate concerns (client, streaming, UI)
- **Testable**: Integration tests with graceful server detection
- **Rich UI**: Textual for TUI, Rich for terminal rendering

## Development Workflow

### Testing Changes

1. **Make changes** to `repl_client` code
2. **Start server**:
   ```bash
   make dev-server
   ```
3. **Run integration test**:
   ```bash
   uv run python scripts/repl_client/test_repl_client.py
   ```
4. **Test TUI changes** with relevant demo:
   ```bash
   uv run python scripts/repl_client/demo_tui_<component>.py
   ```

### Testing HITL

1. Ensure agent has HITL configured in `langgraph.json`
2. Run manual HITL test:
   ```bash
   uv run python scripts/repl_client/test_hitl_manual.py
   ```
3. Follow prompts to approve/reject

### Widget Development

1. Create/modify widget in `src/repl_client/tui/widgets/`
2. Add to appropriate demo script or create new one
3. Run demo to verify styling and behavior
4. Add to main app (`src/repl_client/tui/app.py`)

## Related Documentation

**Architecture:**
- `docs/dev_docs/repl_data_flow.md` - Data flow diagrams
- `docs/dev_docs/ai_docs/ai_gen/layer_0_1_implementation.md` - Core client implementation
- `docs/dev_docs/ai_docs/ai_gen/tui-app-guide.md` - TUI app guide

**Widget Docs:**
- `src/repl_client/tui/widgets/README.md` - Widget specifications
- `docs/dev_docs/ai_docs/ai_gen/tui_widgets_implementation.md` - Implementation details

**Comparison:**
- StateGraph version: `src/repl_client_graph/` (alternative architecture)

## Notes

- **Integration tests** require server - will skip if unavailable
- **Demo scripts** are standalone and don't require server (except `demo_tui_full.py`)
- All demos use **Rich** for beautiful terminal output
- TUI demos use **Textual** framework
- Scripts are **reference implementations** for widget usage
