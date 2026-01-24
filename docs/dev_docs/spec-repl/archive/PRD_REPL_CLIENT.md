# LangGraph REPL Client - Product Requirements Document

## Vision
A minimal, terminal-based REPL client that connects to a running LangGraph dev server, enabling interactive chat sessions with agents through a clean command-line interface with streaming responses.

---

## Core Features (MVP)

### 1. Connection Management
**Why**: Users need to connect to their locally running LangGraph server without complex configuration.

**How**:
- Connect to server via URL (default: `http://localhost:2024`)
- Auto-detect server from `LANGGRAPH_DEV_SERVER_PORT` env var if present
- Test connection on startup, show clear error if server unreachable
- Support optional API key via env var (`LANGGRAPH_API_KEY`)

**Implementation**:
- Use `langgraph_sdk.get_sync_client()` (synchronous for simpler REPL loop)
- Read port from `.env` file if available
- Validate connection by listing available assistants

### 2. Assistant Selection
**Why**: LangGraph servers can host multiple agents/graphs. Users need to choose which one to chat with.

**How**:
- On startup, list available assistants from server
- If only one assistant, auto-select it
- If multiple, prompt user to choose
- Display assistant metadata (name, graph_id)
- Allow switching assistants via `/assistant` command

**Implementation**:
- `client.assistants.search()` to list
- Store selected assistant_id in session state
- Default to first assistant if not specified

### 3. Interactive Chat Loop
**Why**: Core functionality - send messages and receive streaming responses.

**How**:
- Accept user input via prompt
- Send message to agent with streaming enabled
- Display agent responses as they arrive (streaming)
- Maintain conversation context via persistent thread
- Clear indication when agent is "thinking"

**Implementation**:
- Create thread on first message: `client.threads.create()`
- Stream responses: `client.runs.stream(thread_id, assistant_id, input={"messages": [...]}, stream_mode="messages")`
- Parse `StreamPart` events (event type + data)
- Extract and display message content from stream events

### 4. Visual Feedback
**Why**: Users need to know when the agent is processing vs ready for input.

**How**:
- Show spinner/indicator during agent processing
- Clear visual separation between user and agent messages
- Timestamp messages (optional, toggleable)
- Error messages in distinct color/format

**Implementation**:
- Use `Rich` library for:
  - Live spinner during streaming
  - Syntax highlighting for messages
  - Panels/boxes for message framing
  - Color-coded prefixes (You:, Agent:, System:)
- Plain fallback if Rich not available

### 5. Built-in Commands
**Why**: Users need control over session state and access to help.

**Commands**:
- `/help` - Show available commands and usage
- `/clear` - Start new conversation (new thread)
- `/exit` or `/quit` - Exit REPL
- `/history` - Show recent message history
- `/assistant [name]` - Switch assistant or show current
- `/info` - Display connection info and session details

**Implementation**:
- Parse commands before sending to agent (check for `/` prefix)
- Maintain command registry for easy extension
- Help text auto-generated from command definitions

### 6. Conversation Persistence
**Why**: Allow users to continue conversations across sessions.

**How**:
- Each session creates a thread that persists on server
- Display thread_id on startup (can be used to resume)
- Optional: `/resume <thread_id>` command to continue existing conversation

**Implementation**:
- Store thread_id in session state
- Thread persists on server automatically
- Optional: Save thread_id to local file for easy resume

---

## Architecture

### Components

#### 1. **ConnectionManager**
**Responsibility**: Establish and validate connection to LangGraph server
- Initialize langgraph_sdk client
- Validate server connectivity
- Fetch available assistants
- Handle connection errors gracefully

#### 2. **SessionState**
**Responsibility**: Maintain current session context
- Current thread_id
- Selected assistant_id
- Message history (local cache for /history command)
- Configuration (server URL, API key)

#### 3. **InputHandler**
**Responsibility**: Process user input and route to appropriate handler
- Read input from terminal (prompt_toolkit for rich input)
- Distinguish commands (/) from messages
- Handle input history (up/down arrows)
- Tab completion for commands

#### 4. **CommandRouter**
**Responsibility**: Execute built-in commands
- Command registry (mapping command name → handler function)
- Help text generation
- Error handling for invalid commands

#### 5. **StreamHandler**
**Responsibility**: Consume and display streaming responses
- Iterate over `client.runs.stream()` async iterator
- Parse StreamPart events
- Extract message content from stream data
- Display formatted output via OutputRenderer

#### 6. **OutputRenderer**
**Responsibility**: Format and display messages/output
- Rich-based rendering (panels, syntax highlighting, spinners)
- Message formatting (user vs agent)
- Error/warning display
- Progress indicators

### Data Flow

```
User Input → InputHandler → [Is Command?]
                                 ↓ No
                            SessionState (get thread_id, assistant_id)
                                 ↓
                            StreamHandler (send to LangGraph API)
                                 ↓
                            Server streams responses
                                 ↓
                            StreamHandler (parse StreamPart events)
                                 ↓
                            OutputRenderer (display formatted messages)
                                 ↓
                            Back to User Input
```

**Command Flow**:
```
User Input → InputHandler → [Is Command?]
                                 ↓ Yes
                            CommandRouter → Execute Command
                                 ↓
                            Update SessionState if needed
                                 ↓
                            OutputRenderer (display result)
                                 ↓
                            Back to User Input
```

### Dependencies

**Core**:
- `langgraph-sdk` - LangGraph client (already available in project)
- `httpx` - HTTP client (dependency of langgraph-sdk)

**Enhanced UX**:
- `rich` - Terminal formatting, spinners, syntax highlighting
- `prompt-toolkit` - Advanced input (history, completion)

**Standard Library**:
- `os`, `sys` - Environment and system interaction
- `argparse` - CLI argument parsing
- `json` - Message serialization
- `asyncio` - May need for async operations (or stick to sync client)

---

## UX Flow

### Startup
```
$ python -m agent_snowflake.repl

🔌 Connecting to LangGraph server at http://localhost:2024...
✓ Connected successfully

📋 Available assistants:
  1. agent (src.agent_snowflake:graph)
  2. agent_enhanced (src.agent_snowflake:graph_enhanced)
  3. agent_minimal (src.agent_snowflake:graph_minimal)

Select assistant [1-3] (default: 1): 2

✓ Using assistant: agent_enhanced
🧵 Thread ID: 8d3f7a2e-9b1c-4f8e-a7d9-3e5c8b9f2d1a

Type /help for commands, /exit to quit
────────────────────────────────────────────────────────
You:
```

### Chat Interaction
```
You: Show me all tables in the database

Agent: ⠋ Thinking...

Agent: I'll query the database to list all available tables.

[Agent shows thinking process if stream_mode includes intermediate steps]

Agent: Here are all the tables in the Chinook database:

1. albums
2. artists
3. customers
4. employees
5. genres
6. invoice_items
7. invoices
8. media_types
9. playlist_track
10. playlists
11. tracks

Would you like me to describe any specific table?

────────────────────────────────────────────────────────
You: /help

Available Commands:
  /help              Show this help message
  /clear             Start a new conversation (new thread)
  /exit, /quit       Exit the REPL
  /history           Show recent conversation history
  /assistant [name]  Switch assistant or show current
  /info              Display connection and session info

────────────────────────────────────────────────────────
You: /info

Connection Info:
  Server URL: http://localhost:2024
  Assistant: agent_enhanced (src.agent_snowflake:graph_enhanced)
  Thread ID: 8d3f7a2e-9b1c-4f8e-a7d9-3e5c8b9f2d1a
  Messages: 2

────────────────────────────────────────────────────────
You: /exit

Goodbye!
```

### Error Handling
```
$ python -m agent_snowflake.repl

🔌 Connecting to LangGraph server at http://localhost:2024...
✗ Connection failed: Server not reachable

Please ensure the LangGraph dev server is running:
  make dev

Or specify a different URL:
  python -m agent_snowflake.repl --url http://localhost:8000
```

---

## Configuration

### Environment Variables
- `LANGGRAPH_DEV_SERVER_PORT` - Server port (default: 2024)
- `LANGGRAPH_API_KEY` - API key if required (optional)
- `LANGGRAPH_URL` - Full server URL override (optional)
- `REPL_ASSISTANT` - Pre-select assistant by name (optional)

### CLI Arguments
```bash
python -m agent_snowflake.repl [OPTIONS]

Options:
  --url TEXT              LangGraph server URL [default: http://localhost:2024]
  --assistant TEXT        Assistant name to use
  --thread-id TEXT        Resume existing thread
  --no-color              Disable colored output
  --help                  Show this message and exit
```

### Configuration Priority
1. CLI arguments (highest priority)
2. Environment variables
3. Default values (lowest priority)

---

## Out of Scope (v1)

### Deferred Features
- **Multi-turn conversation editing** - Edit previous messages (requires API support)
- **Conversation export** - Save conversations to file (can add later)
- **Multiple simultaneous threads** - Switch between active conversations (complex state management)
- **Advanced streaming modes** - Only implement "messages" mode initially (can add "events", "debug" later)
- **Thread search/list** - Browse historical threads (needs server query features)
- **File upload** - Attach files to messages (needs API support)
- **Streaming interruption** - Cancel in-flight requests (complex async handling)
- **Configuration file** - Persistent config beyond env vars (`.repl.yaml`)
- **Plugin system** - Custom commands/handlers (over-engineered for v1)
- **TUI mode** - Split-pane interface (textual/rich-based) vs simple REPL

### Explicitly Not Building
- **Web interface** - Terminal only
- **Authentication UI** - Use env vars for API keys
- **Server management** - Assumes server already running (use `make dev`)
- **Assistant deployment** - Out of scope, use LangGraph CLI
- **Custom agent development** - REPL is for interaction only

---

## Open Questions

### 1. Synchronous vs Asynchronous Client?
**Question**: Use `SyncLangGraphClient` or `LangGraphClient` (async)?

**Options**:
- **Sync**: Simpler REPL loop, blocking calls, easier error handling
- **Async**: Better for streaming, but requires `asyncio.run()` wrapper or async REPL

**Recommendation**: Start with **sync client** for simplicity. The streaming API works with sync iterator pattern.

### 2. Stream Mode Selection?
**Question**: Which `stream_mode` to use for messages?

**Options**:
- `"messages"` - Only final messages (cleanest output)
- `"values"` - Full state updates (more verbose)
- `"events"` - All events including tool calls (debugging)

**Recommendation**: Default to `"messages"` for clean UX. Add `--stream-mode` flag for power users.

### 3. Message History Storage?
**Question**: Store message history locally or rely on server thread state?

**Options**:
- **Server only**: Simpler, but no offline history
- **Local cache**: Keep last N messages for `/history` command
- **Both**: Hybrid approach

**Recommendation**: **Local cache** of last 50 messages for `/history` command. Server is source of truth.

### 4. Error Recovery?
**Question**: How to handle streaming errors (network dropout, server restart)?

**Options**:
- **Fail fast**: Exit REPL on error
- **Retry**: Automatic reconnection attempts
- **Graceful**: Show error, return to prompt

**Recommendation**: **Graceful** - catch exceptions, display error, return to input prompt. Add optional retry for connection errors.

### 5. Input Format?
**Question**: How should users structure multi-line input or complex queries?

**Options**:
- **Single line only**: Simple but limiting
- **Multi-line mode**: Press Enter twice to submit (like IPython)
- **Explicit mode**: `/multi` command to enter multi-line mode

**Recommendation**: Start with **single line**. Add multi-line in v1.1 if needed (prompt-toolkit supports this easily).

### 6. Message Formatting?
**Question**: How to format agent responses with code, tables, etc.?

**Options**:
- **Plain text**: No formatting
- **Markdown rendering**: Parse and render markdown with Rich
- **Pass-through**: Display exactly as agent sends

**Recommendation**: **Markdown rendering** with Rich for code blocks, tables, and emphasis. Adds polish for minimal effort.

### 7. Thread Management?
**Question**: Auto-create thread on first message or require explicit creation?

**Options**:
- **Auto-create**: Transparent, thread created on first message
- **Explicit**: `/new` command to create thread

**Recommendation**: **Auto-create** for simplicity. Thread ID displayed after creation. Add `/clear` to start fresh.

### 8. Deployment?
**Question**: How should users install/run the REPL?

**Options**:
- **Module invocation**: `python -m agent_snowflake.repl` (no install needed)
- **Entry point**: `uv run snowflake-repl` (requires setup.py entry point)
- **Script**: Standalone `repl.py` (simple but not packaged)

**Recommendation**: **Module invocation** initially (`python -m agent_snowflake.repl`). Add entry point in pyproject.toml once stable.

---

## Implementation Plan

### Phase 1: Core REPL (Essential)
1. ConnectionManager - connect to server, validate, list assistants
2. Basic REPL loop - input → send → receive → display
3. Streaming handler - parse StreamPart, display messages
4. Basic commands - /help, /exit, /clear
5. Simple output - plain text with minimal formatting

**Deliverable**: Working REPL that can chat with agent via streaming

### Phase 2: Enhanced UX (Polish)
6. Rich integration - spinners, colored output, panels
7. prompt-toolkit integration - input history, command completion
8. Additional commands - /history, /info, /assistant
9. Error handling - connection failures, API errors, graceful recovery
10. CLI arguments - --url, --assistant, --thread-id

**Deliverable**: Polished REPL with professional UX

### Phase 3: Optional Enhancements (Nice-to-Have)
11. Markdown rendering - code blocks, tables, emphasis
12. Multi-line input support
13. Configuration file support (.repl.yaml)
14. Thread resume functionality
15. Streaming mode selection (--stream-mode flag)

**Deliverable**: Feature-complete REPL with power-user options

---

## Success Criteria

### Must Have (MVP)
- ✓ Connect to local LangGraph server
- ✓ Select assistant from available options
- ✓ Send messages and receive streaming responses
- ✓ Display agent responses in real-time
- ✓ Basic commands (/help, /exit, /clear)
- ✓ Handle connection errors gracefully

### Should Have (v1.0)
- ✓ Rich terminal formatting (colors, panels, spinners)
- ✓ Input history and command completion
- ✓ Message history display (/history)
- ✓ Session info display (/info)
- ✓ CLI arguments for configuration
- ✓ Markdown rendering in responses

### Nice to Have (v1.1+)
- ○ Multi-line input mode
- ○ Thread resume across sessions
- ○ Configuration file support
- ○ Custom streaming mode selection
- ○ Conversation export to file

---

## Technical Constraints

### Performance
- Streaming must feel responsive (< 100ms first token)
- Local message cache capped at 50 messages to prevent memory issues
- Network timeout: 30s for initial connection, 5m for streaming

### Compatibility
- Python 3.12+ (matches project requirement)
- Terminal support: any ANSI-compatible terminal
- Fallback to plain text if Rich not available

### Security
- API keys only via environment variables (never prompt or hardcode)
- No credential storage in local files
- Validate server URL format to prevent SSRF

---

## File Structure

```
agent_snowflake/
├── repl/
│   ├── __init__.py
│   ├── __main__.py           # Entry point: python -m agent_snowflake.repl
│   ├── client.py             # ConnectionManager
│   ├── session.py            # SessionState
│   ├── commands.py           # CommandRouter + built-in commands
│   ├── stream.py             # StreamHandler
│   ├── render.py             # OutputRenderer (Rich-based)
│   └── config.py             # Configuration management
```

**Rationale**: Separate module for clean separation from agent code. Easy to test and extend.

---

## Testing Strategy

### Unit Tests
- `test_commands.py` - Command parsing and execution
- `test_session.py` - Session state management
- `test_render.py` - Output formatting

### Integration Tests
- `test_repl_integration.py` - Full REPL flow with mock server
- Requires `responses` or `httpx_mock` for HTTP mocking

### Manual Testing
- Test against live dev server with all three agents
- Verify streaming behavior with slow responses
- Test error scenarios (server down, invalid input)
- Cross-platform testing (macOS, Linux, Windows)

---

## Documentation Needs

### User Documentation
- **README.md** section on REPL usage
- **Quickstart guide** - Getting started in 30 seconds
- **Command reference** - All commands with examples
- **Troubleshooting** - Common issues and solutions

### Developer Documentation
- **Architecture overview** - Component responsibilities
- **Extension guide** - Adding custom commands
- **API reference** - Public APIs for each module

---

## Future Enhancements (Post-v1)

### v1.1 - Enhanced Interaction
- Multi-line input mode
- Conversation export (JSON, Markdown)
- Thread search and resume
- Custom streaming modes

### v1.2 - Advanced Features
- Configuration file support (`.repl.yaml`)
- Plugin system for custom commands
- Integration with LangSmith for tracing
- File upload support (if API supports)

### v2.0 - TUI Mode
- Split-pane interface (messages + state viewer)
- Real-time state visualization
- Interactive graph execution control
- Built with `textual` framework

---

## Alternatives Considered

### 1. Jupyter Notebook Extension
**Why not**: Requires Jupyter environment, not terminal-native. Overkill for simple chat.

### 2. Web-based UI
**Why not**: LangGraph Studio already provides this. Goal is terminal-only workflow.

### 3. Simple curl scripts
**Why not**: No conversation state, no streaming display, poor UX. REPL provides better DX.

### 4. LangChain CLI extension
**Why not**: LangGraph has separate CLI. Keep focused on LangGraph ecosystem.

---

## Summary

This PRD defines a **focused, terminal-based REPL client** for interacting with LangGraph agents. The MVP prioritizes:

1. **Simplicity** - Minimal configuration, works out of the box with `make dev`
2. **Streaming** - Real-time response display for agent interactions
3. **Usability** - Rich terminal UX with clear visual feedback
4. **Extensibility** - Clean architecture for future enhancements

The implementation uses proven libraries (`langgraph-sdk`, `rich`, `prompt-toolkit`) and follows established REPL patterns from IPython and other interactive tools.

**Next Steps**:
1. Review and approve PRD
2. Create feature branch: `feature/repl-client`
3. Implement Phase 1 (Core REPL)
4. Test with existing agents
5. Iterate based on user feedback
