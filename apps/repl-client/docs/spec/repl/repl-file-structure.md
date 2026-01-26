# REPL File Structure Analysis


## Kanban

**backlog**

- [ ] inventory existing repl's created .. look for "chat session" + "app"
- [ ] create command menu first
- [ ] create settings menu next
- [ ] mock up screens
- [ ] console color/grid ux
- [ ] console controllers arch?


---

## Features

- Dual-mode streaming (`messages` + `updates`)
- HITL approval menu with arrow key navigation
- Tool call buffering (partial JSON assembly)
- Spinner management during tool execution
- Interrupt/resume state machine
- Graceful shutdown handling
- Tool-specific formatters
- Diff rendering with line numbers and colors
- Token tracking (baseline + conversation)
- Agent Todo list rendering
- Smart line wrapping for terminal width
- Table rendering
- Context-aware completers (@file, /command)
- Key bindings (Enter, Alt+Enter, Ctrl+E, Ctrl+T)
- Bottom toolbar
- File mention parsing and content injection
- External editor integration
- Backend routing (composite filesystem) -- deepagents BackendProtocol
- Long-term memory setup --- currently local file system but better I think to have that just as fall back
- Middleware stack composition
- HITL formatters per tool
- Checkpoint configuration

---

##  Structure

```
src/repl_client
├── __init__.py
├── __main__.py              # Entry point, basic REPL loop (150-200 lines)
│
├── core/
│   ├── __init__.py
│   ├── client.py            # RemoteClient - langgraph-sdk wrapper (100-150 lines)
│   ├── session.py           # SessionState - thread/agent tracking (80-100 lines)
│   └── config.py            # Config loading from .env (50-80 lines)
│
├── streaming/
│   ├── __init__.py
│   ├── handler.py           # StreamHandler - parse chunks (200-300 lines)
│   └── hitl.py              # HITL approval logic (100-150 lines)
│
├── ui/
│   ├── __init__.py
│   ├── renderer.py          # Base Renderer - Rich output (150-200 lines)
│   ├── message.py           # Message-specific rendering (150-200 lines)
│   ├── content_blocks.py    # Content block handlers (100-150 lines)
│   └── input.py             # Input handling (prompt-toolkit Phase 3) (150-200 lines)
│
└── commands/
    ├── __init__.py
    ├── registry.py          # CommandRegistry pattern (80-100 lines)
    └── handlers.py          # Command implementations (150-200 lines)
```
---

## Detailed File Breakdown (Classes, Methods, Functions)

### `__main__.py` (Entry Point - 150-200 lines)

```python
class REPLLoop:
    """Main REPL orchestrator."""

    def __init__(self, config: Config, client: RemoteClient):
        self.config = config
        self.client = client
        self.session = SessionState()
        self.registry = CommandRegistry()
        self.renderer = Renderer()

    def run(self) -> None:
        """Main REPL loop."""

    def handle_input(self, user_input: str) -> bool:
        """Route input to command or message handler. Returns False to exit."""

    def _get_input(self) -> str:
        """Get input from user (plain input in Phase 1, prompt-toolkit in Phase 3)."""

    def _show_welcome(self) -> None:
        """Display welcome banner with connection info."""

def main() -> None:
    """Entry point for python -m agent_snowflake.repl"""
```

---

### `core/client.py` (RemoteClient - 100-150 lines)

```python
class RemoteClient:
    """Wrapper around langgraph-sdk for server communication."""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = None  # get_client() from langgraph-sdk

    def connect(self) -> bool:
        """Establish connection to server. Returns True if successful."""

    def list_agents(self) -> list[dict]:
        """List available agents from server."""

    def list_threads(self) -> list[dict]:
        """List existing threads."""

    def create_thread(self) -> str:
        """Create new thread, return thread_id."""

    def get_thread(self, thread_id: str) -> dict:
        """Get thread metadata."""

    def stream_message(
        self,
        thread_id: str,
        message: str,
        agent_id: str = "agent"
    ) -> Iterator[dict]:
        """Stream message to agent, yield chunks."""

    def handle_interrupt(
        self,
        thread_id: str,
        approval: bool
    ) -> Iterator[dict]:
        """Resume after HITL interrupt with approval decision."""
```

---

### `core/session.py` (SessionState - 80-100 lines)

```python
class SessionState:
    """Track current session state."""

    def __init__(self):
        self.current_thread_id: str | None = None
        self.current_agent: str = "agent"
        self.message_history: list[dict] = []  # Local cache for display

    def set_thread(self, thread_id: str) -> None:
        """Set active thread."""

    def set_agent(self, agent_id: str) -> None:
        """Set active agent."""

    def add_message(self, role: str, content: str) -> None:
        """Add message to local history cache."""

    def clear_history(self) -> None:
        """Clear local history cache."""

    def get_context_summary(self) -> str:
        """Return summary for display (thread ID, agent, message count)."""
```

---

### `core/config.py` (Config - 50-80 lines)

```python
@dataclass
class Config:
    """REPL configuration."""
    server_url: str
    default_agent: str = "agent"
    stream_mode: str = "messages"
    debug: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        """Load config from .env file."""

    @classmethod
    def get_defaults(cls) -> dict:
        """Return default config values."""

def load_config() -> Config:
    """Load configuration from environment."""
```

---

### `streaming/handler.py` (StreamHandler - 200-300 lines)

```python
class StreamHandler:
    """Parse and process streaming chunks from server."""

    def __init__(self, renderer: Renderer):
        self.renderer = renderer
        self.tool_call_buffer: dict[str, dict] = {}
        self.current_message: list[str] = []

    def process_stream(
        self,
        stream: Iterator[dict],
        session: SessionState
    ) -> StreamResult:
        """Process streaming chunks, render output, detect interrupts."""

    def _handle_message_chunk(self, chunk: dict) -> None:
        """Handle text/token chunks."""

    def _handle_tool_call(self, chunk: dict) -> None:
        """Buffer and assemble tool call chunks."""

    def _detect_interrupt(self, chunk: dict) -> bool:
        """Check if chunk indicates HITL interrupt."""

    def _flush_current_message(self) -> None:
        """Render accumulated message tokens."""

@dataclass
class StreamResult:
    """Result of stream processing."""
    interrupted: bool
    tool_call_id: str | None
    tool_name: str | None
    tool_args: dict | None
```

---

### `streaming/hitl.py` (HITL - 100-150 lines)

```python
class HITLHandler:
    """Handle Human-in-the-Loop approval prompts."""

    def __init__(self, renderer: Renderer):
        self.renderer = renderer

    def show_approval_prompt(
        self,
        tool_name: str,
        tool_args: dict
    ) -> bool:
        """Show tool approval prompt, return True if approved."""

    def _format_tool_preview(
        self,
        tool_name: str,
        tool_args: dict
    ) -> str:
        """Format tool call for preview (e.g., show SQL query)."""

    def _get_approval_input(self) -> bool:
        """Get y/n input from user."""

def format_sql_query_preview(query: str) -> str:
    """Format SQL query with syntax highlighting for preview."""
```

---

### `ui/renderer.py` (Base Renderer - 150-200 lines)

```python
class Renderer:
    """Base renderer using Rich for terminal output."""

    def __init__(self):
        self.console = Console()

    def render_text(self, text: str) -> None:
        """Render plain text."""

    def render_markdown(self, text: str) -> None:
        """Render markdown with Rich Markdown."""

    def render_panel(
        self,
        content: str,
        title: str,
        style: str = "blue"
    ) -> None:
        """Render content in Rich Panel."""

    def render_table(self, headers: list[str], rows: list[list]) -> None:
        """Render table using Rich Table."""

    def render_error(self, message: str) -> None:
        """Render error message in red."""

    def render_success(self, message: str) -> None:
        """Render success message in green."""

    def render_spinner(self, text: str) -> ContextManager:
        """Context manager for spinner during operations."""

    def clear_screen(self) -> None:
        """Clear terminal screen."""
```

---

### `ui/message.py` (Message Rendering - 150-200 lines)

```python
class MessageRenderer:
    """Render different message types."""

    def __init__(self, renderer: Renderer):
        self.renderer = renderer

    def render_user_message(self, content: str) -> None:
        """Render user message with formatting."""

    def render_ai_message(self, content: str) -> None:
        """Render AI message with markdown support."""

    def render_tool_message(
        self,
        tool_name: str,
        result: str
    ) -> None:
        """Render tool execution result."""

    def render_system_message(self, content: str) -> None:
        """Render system message (connection status, etc.)."""

    def _extract_code_blocks(self, text: str) -> list[tuple[str, str]]:
        """Extract code blocks from markdown text."""

    def _render_code_block(self, code: str, language: str) -> None:
        """Render code block with syntax highlighting."""
```

---

### `ui/content_blocks.py` (Content Blocks - 100-150 lines)

```python
class ContentBlockHandler:
    """Handle various content block types."""

    def __init__(self, renderer: Renderer):
        self.renderer = renderer

    def render_content_block(self, block: dict) -> None:
        """Route content block to appropriate handler."""

    def _render_text_block(self, block: dict) -> None:
        """Render text content block."""

    def _render_tool_use_block(self, block: dict) -> None:
        """Render tool use block (tool name + args)."""

    def _render_tool_result_block(self, block: dict) -> None:
        """Render tool result block."""

    def _render_thinking_block(self, block: dict) -> None:
        """Render thinking/reasoning block (if present)."""

    def _truncate_large_content(self, content: str, max_len: int = 1000) -> str:
        """Truncate large content with ellipsis."""
```

---

### `ui/input.py` (Enhanced Input - 150-200 lines, Phase 3)

```python
class InputHandler:
    """Enhanced input with prompt-toolkit."""

    def __init__(self):
        self.session = PromptSession()
        self.history = FileHistory(".repl_history")
        self.completer = CommandCompleter()

    def get_input(self, prompt: str = "> ") -> str:
        """Get input with completions and history."""

    def get_multiline_input(self, prompt: str = "... ") -> str:
        """Get multiline input (Ctrl+D to finish)."""

class CommandCompleter(Completer):
    """Auto-complete for slash commands."""

    def get_completions(
        self,
        document: Document,
        complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Return command completions."""
```

---

### `commands/registry.py` (Registry - 80-100 lines)

```python
class CommandRegistry:
    """Registry pattern for extensible commands."""

    def __init__(self):
        self._commands: dict[str, Command] = {}

    def register(
        self,
        name: str,
        handler: Callable,
        description: str,
        syntax: str = ""
    ) -> None:
        """Register a command."""

    def execute(self, name: str, args: list[str], context: dict) -> Any:
        """Execute registered command."""

    def get_command(self, name: str) -> Command | None:
        """Get command by name."""

    def list_commands(self) -> list[Command]:
        """List all registered commands."""

    def get_help_text(self) -> str:
        """Generate help text for all commands."""

@dataclass
class Command:
    """Command definition."""
    name: str
    handler: Callable
    description: str
    syntax: str
```

---

### `commands/handlers.py` (Handlers - 150-200 lines)

```python
class CommandHandlers:
    """Implementations for all slash commands."""

    def __init__(
        self,
        client: RemoteClient,
        session: SessionState,
        renderer: Renderer
    ):
        self.client = client
        self.session = session
        self.renderer = renderer

    def register_all(self, registry: CommandRegistry) -> None:
        """Register all command handlers."""

    # Phase 1 Commands
    def handle_help(self, args: list[str]) -> None:
        """Show help for all commands or specific command."""

    def handle_exit(self, args: list[str]) -> bool:
        """Exit REPL. Returns False to signal exit."""

    # Phase 2 Commands
    def handle_agents(self, args: list[str]) -> None:
        """List agents or switch to specified agent."""

    def handle_threads(self, args: list[str]) -> None:
        """List threads or resume specified thread."""

    def handle_new(self, args: list[str]) -> None:
        """Create new thread."""

    # Phase 3 Commands
    def handle_clear(self, args: list[str]) -> None:
        """Clear screen."""

    def handle_tokens(self, args: list[str]) -> None:
        """Show token usage stats."""

    def _list_agents(self) -> None:
        """Display formatted list of available agents."""

    def _switch_agent(self, agent_id: str) -> None:
        """Switch to specified agent."""

    def _list_threads(self) -> None:
        """Display formatted list of threads."""

    def _resume_thread(self, thread_id: str) -> None:
        """Resume specified thread."""
```

---

## Process Flows with Component Annotations

### Flow 1: Startup & Connection

```
User: python -m agent_snowflake.repl
  │
  ├─> __main__.main()
  │     ├─> config.load_config()              [Load .env]
  │     ├─> RemoteClient(server_url)          [Initialize client]
  │     └─> REPLLoop(config, client)          [Create REPL]
  │
  ├─> REPLLoop.run()
  │     ├─> client.connect()                  [Connect to server]
  │     │     └─> langgraph-sdk.get_client()
  │     │
  │     ├─> renderer.render_panel()           [Show welcome]
  │     │     └─> Rich console output
  │     │
  │     └─> session.set_agent("agent")        [Set default agent]
  │
  └─> Display: "Connected to http://localhost:2024"
              "Current agent: agent"
              "Type /help for commands"
```

**Components Used**:
- `__main__.main()` - Entry point
- `core/config.py` - Load configuration
- `core/client.py` - Server connection
- `core/session.py` - Initialize state
- `ui/renderer.py` - Welcome banner

---

### Flow 2: Send Message (Basic Chat)

```
User: "Show me the customers table"
  │
  ├─> REPLLoop.handle_input(text)
  │     ├─> Check if starts with "/" → No
  │     ├─> session.add_message("user", text)
  │     └─> client.stream_message(
  │           thread_id=session.current_thread_id,
  │           message=text,
  │           agent_id=session.current_agent
  │         )
  │           │
  │           └─> langgraph-sdk: runs.stream()
  │
  ├─> StreamHandler.process_stream(chunks)
  │     │
  │     ├─> For each chunk:
  │     │     ├─> _handle_message_chunk()
  │     │     │     └─> renderer.render_text(token)  [Stream tokens]
  │     │     │
  │     │     ├─> _handle_tool_call()
  │     │     │     └─> Buffer tool call JSON
  │     │     │
  │     │     └─> _detect_interrupt() → False
  │     │
  │     └─> _flush_current_message()
  │           └─> MessageRenderer.render_ai_message()
  │                 ├─> _extract_code_blocks()
  │                 └─> _render_code_block()  [SQL with syntax highlighting]
  │
  └─> Display: AI response with formatted SQL
```

**Components Used**:
- `__main__.REPLLoop` - Input routing
- `core/client.py` - Streaming API call
- `core/session.py` - Track message history
- `streaming/handler.py` - Parse chunks
- `ui/renderer.py` - Base rendering
- `ui/message.py` - Message formatting
- `ui/content_blocks.py` - Code block rendering

---

### Flow 3: Tool Call with HITL Approval

```
User: "Query the database for customer names"
  │
  ├─> [Same as Flow 2 until tool call detected]
  │
  ├─> StreamHandler.process_stream(chunks)
  │     │
  │     ├─> Chunk indicates tool call: "sql_db_query"
  │     │     └─> _handle_tool_call()
  │     │           ├─> Buffer JSON: {"query": "SELECT name FROM customers"}
  │     │           └─> Store in tool_call_buffer
  │     │
  │     ├─> _detect_interrupt() → True
  │     │     └─> Return StreamResult(interrupted=True, tool_name="sql_db_query", ...)
  │     │
  │     └─> REPLLoop receives interrupt signal
  │
  ├─> HITLHandler.show_approval_prompt(tool_name, tool_args)
  │     │
  │     ├─> _format_tool_preview("sql_db_query", {...})
  │     │     └─> format_sql_query_preview(query)  [Syntax highlight SQL]
  │     │
  │     ├─> renderer.render_panel()  [Show preview]
  │     │     └─> "Tool: sql_db_query"
  │     │         "Query: SELECT name FROM customers"
  │     │         "Approve? (y/n)"
  │     │
  │     └─> _get_approval_input() → True
  │
  ├─> client.handle_interrupt(thread_id, approval=True)
  │     └─> langgraph-sdk: Update with approval, continue stream
  │
  ├─> StreamHandler.process_stream(resumed_chunks)
  │     │
  │     ├─> Tool result chunk arrives
  │     │     └─> ContentBlockHandler.render_content_block()
  │     │           └─> _render_tool_result_block()
  │     │                 └─> renderer.render_panel("Results: ...")
  │     │
  │     └─> AI response continues
  │           └─> MessageRenderer.render_ai_message()
  │
  └─> Display: Tool results + AI interpretation
```

**Components Used**:
- `streaming/handler.py` - Detect interrupt
- `streaming/hitl.py` - Approval prompt
- `core/client.py` - Resume after approval
- `ui/renderer.py` - Preview panel
- `ui/content_blocks.py` - Tool result rendering
- `ui/message.py` - Final response

---

### Flow 4: List & Switch Agents

```
User: /agents
  │
  ├─> REPLLoop.handle_input("/agents")
  │     ├─> Check if starts with "/" → Yes
  │     ├─> Parse: command="/agents", args=[]
  │     └─> registry.execute("agents", args, context)
  │
  ├─> CommandHandlers.handle_agents([])
  │     │
  │     ├─> No args → List agents
  │     │
  │     └─> _list_agents()
  │           ├─> client.list_agents()
  │           │     └─> langgraph-sdk: assistants.search()
  │           │           Returns: [
  │           │             {"assistant_id": "agent", "name": "Basic Agent"},
  │           │             {"assistant_id": "agent_enhanced", "name": "Enhanced"},
  │           │             {"assistant_id": "agent_minimal", "name": "Minimal"}
  │           │           ]
  │           │
  │           └─> renderer.render_table(
  │                 headers=["ID", "Name", "Current"],
  │                 rows=[
  │                   ["agent", "Basic Agent", "✓"],
  │                   ["agent_enhanced", "Enhanced", ""],
  │                   ["agent_minimal", "Minimal", ""]
  │                 ]
  │               )
  │
  └─> Display: Table of agents with checkmark on current

---

User: /agents agent_enhanced
  │
  ├─> REPLLoop.handle_input("/agents agent_enhanced")
  │     └─> registry.execute("agents", ["agent_enhanced"], context)
  │
  ├─> CommandHandlers.handle_agents(["agent_enhanced"])
  │     │
  │     ├─> Has args → Switch agent
  │     │
  │     └─> _switch_agent("agent_enhanced")
  │           ├─> Validate agent exists
  │           │     └─> client.list_agents()
  │           │
  │           ├─> session.set_agent("agent_enhanced")
  │           │
  │           └─> renderer.render_success(
  │                 "Switched to agent: agent_enhanced"
  │               )
  │
  └─> Display: Success message, future messages use new agent
```

**Components Used**:
- `__main__.REPLLoop` - Command detection
- `commands/registry.py` - Route to handler
- `commands/handlers.py` - Implement /agents
- `core/client.py` - List agents API
- `core/session.py` - Update agent state
- `ui/renderer.py` - Table and success message

---

### Flow 5: Create & Resume Threads

```
User: /new
  │
  ├─> REPLLoop.handle_input("/new")
  │     └─> registry.execute("new", [], context)
  │
  ├─> CommandHandlers.handle_new([])
  │     │
  │     ├─> client.create_thread()
  │     │     └─> langgraph-sdk: threads.create()
  │     │           Returns: {"thread_id": "abc-123"}
  │     │
  │     ├─> session.set_thread("abc-123")
  │     │
  │     ├─> session.clear_history()
  │     │
  │     └─> renderer.render_success(
  │           "Created new thread: abc-123"
  │         )
  │
  └─> Display: New thread ID, ready for conversation

---

User: /threads
  │
  ├─> REPLLoop.handle_input("/threads")
  │     └─> registry.execute("threads", [], context)
  │
  ├─> CommandHandlers.handle_threads([])
  │     │
  │     ├─> No args → List threads
  │     │
  │     └─> _list_threads()
  │           ├─> client.list_threads()
  │           │     └─> langgraph-sdk: threads.search()
  │           │           Returns: [
  │           │             {
  │           │               "thread_id": "abc-123",
  │           │               "created_at": "2026-01-23T...",
  │           │               "metadata": {...}
  │           │             },
  │           │             ...
  │           │           ]
  │           │
  │           └─> renderer.render_table(
  │                 headers=["Thread ID", "Created", "Current"],
  │                 rows=[
  │                   ["abc-123", "2026-01-23 10:30", "✓"],
  │                   ["def-456", "2026-01-22 15:20", ""],
  │                 ]
  │               )
  │
  └─> Display: Table of threads

---

User: /threads def-456
  │
  ├─> REPLLoop.handle_input("/threads def-456")
  │     └─> registry.execute("threads", ["def-456"], context)
  │
  ├─> CommandHandlers.handle_threads(["def-456"])
  │     │
  │     ├─> Has args → Resume thread
  │     │
  │     └─> _resume_thread("def-456")
  │           ├─> client.get_thread("def-456")
  │           │     └─> Validate thread exists
  │           │
  │           ├─> session.set_thread("def-456")
  │           │
  │           ├─> session.clear_history()
  │           │
  │           └─> renderer.render_success(
  │                 "Resumed thread: def-456"
  │               )
  │
  └─> Display: Thread resumed, conversation continues
```

**Components Used**:
- `commands/handlers.py` - Implement /new, /threads
- `core/client.py` - Thread management APIs
- `core/session.py` - Track current thread
- `ui/renderer.py` - Tables and messages

---

### Flow 6: Error Handling

```
Scenario: Server disconnected during message

User: "Show me data"
  │
  ├─> client.stream_message(...)
  │     │
  │     └─> langgraph-sdk raises ConnectionError
  │
  ├─> StreamHandler.process_stream()
  │     │
  │     └─> Catches exception
  │           │
  │           ├─> renderer.render_error(
  │           │     "Lost connection to server"
  │           │   )
  │           │
  │           └─> Attempt reconnection?
  │                 ├─> client.connect()
  │                 │     └─> If successful:
  │                 │           renderer.render_success(
  │                 │             "Reconnected to server"
  │                 │           )
  │                 │
  │                 └─> If failed:
  │                       renderer.render_error(
  │                         "Could not reconnect. Is server running?"
  │                       )
  │
  └─> Display: Error message, REPL continues (doesn't crash)
```

**Components Used**:
- `streaming/handler.py` - Exception handling
- `core/client.py` - Reconnection logic
- `ui/renderer.py` - Error/success messages

---

## Summary of Component Interactions

| Flow | Entry | Routing | API | State | Rendering | Special |
|------|-------|---------|-----|-------|-----------|---------|
| **Startup** | `__main__` | - | `client.connect` | `session.init` | `renderer.panel` | - |
| **Chat** | `REPLLoop` | - | `client.stream` | `session.add_msg` | `message.render_ai` | `streaming.handler` |
| **HITL** | `REPLLoop` | - | `client.interrupt` | - | `hitl.approval` | `streaming.hitl` |
| **Commands** | `REPLLoop` | `registry.execute` | `client.*` | `session.set_*` | `renderer.*` | `commands.handlers` |
| **Errors** | Any | - | `client.*` | - | `renderer.error` | Exception handling |

---

## Existing REPL Architectures (From Agent Analysis)

### 1. deepagents-cli (Most Complete - 2,400+ lines)

```
deepagents_cli/
├── __init__.py
├── main.py                 # Entry point, CLI args, async REPL loop (~200 lines)
├── execution.py            # 617 lines - Core streaming, HITL approval system
├── agent.py                # 271 lines - Agent creation, middleware composition
├── input.py                # 271 lines - Prompt toolkit, completers, key bindings
├── ui.py                   # 610 lines - Rich formatting (diffs, todos, tokens)
├── file_ops.py             # 360 lines - File operation tracking & metrics
├── config.py               # 119 lines - Constants, model creation, session state
├── agent_memory.py         # 227 lines - Memory middleware
└── commands.py             # Command definitions
```

**Key Insight**: Large files for complex features (execution, ui). Heavy separation by concern.

---

### 2. langchain_repl_v1 (~1,500 lines)

```
langchain_repl_v1/
├── __init__.py
├── session.py              # Main orchestrator - event loop, input handling
├── commands.py             # Slash command handlers with extensible pattern
├── renderer.py             # Message formatting and output display
├── filters.py              # Message visibility rules and filtering logic
├── config.py               # Unified, hierarchical configuration management
├── streaming.py            # Real-time token display using astream_events
├── mcp_integration.py      # MCP protocol integration
├── mcp_session_manager.py  # Stateful MCP server management
└── content_blocks.py       # Multimodal content handler (12+ types)
```

**Key Insight**: Separation of streaming, filtering, and content blocks. MCP as separate module.

---

### 3. codeassist (~1,200 lines)

```
src/codeassist/
├── __init__.py
├── __main__.py             # Entry point
├── cli/
│   └── main.py             # Typer CLI app, main loop
├── ui/
│   ├── display.py          # Rich-based console rendering
│   └── input_handler.py    # prompt_toolkit input with completers
├── core/
│   ├── services/
│   │   ├── tool_manager.py         # Dynamic tool discovery
│   │   ├── conversation_manager.py # History + token tracking
│   │   └── command_processor.py    # Command registry (unused)
│   └── tools/
│       └── base.py         # BaseTool interface
├── api/
│   └── message_processor.py # Langchain client wrapper
└── config/
    └── settings.py          # Pydantic settings with YAML loading
```

**Key Insight**: Layered architecture (ui, core, api, config). Tool system as separate subsystem.

---

### 4. agent0 (~1,000 lines)

```
src/app/
├── __init__.py
├── app.py                  # Main loop, agent switching
├── config.py               # Environment/Settings singleton
├── discovery.py            # Agent discovery from src.agents
├── commands/
│   ├── registry.py         # CommandRegistry pattern
│   └── handlers.py         # Command implementations, multiline input
├── ui/
│   ├── chat_interface.py   # Chat loop orchestration
│   ├── autocomplete.py     # Tab completion with prompt_toolkit
│   ├── message_formatting.py # Type-specific message renderers
│   ├── splash.py           # ASCII art splash screens
│   ├── banners.py          # Banner styles
│   └── interactive_commands.py # Session-specific command registration
└── chatsession/            # (external) - core API
```

**Key Insight**: Commands as subsystem. UI components highly modular. Agent switching architecture.

---

