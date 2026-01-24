# REPL Client Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         REPL Client                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐         ┌─────────────────┐                │
│  │  InputHandler  │────────▶│ CommandRouter   │                │
│  │  prompt_toolkit│         │  /help, /clear  │                │
│  └────────┬───────┘         └────────┬────────┘                │
│           │                          │                          │
│           │                          ▼                          │
│           │                 ┌─────────────────┐                │
│           │                 │  SessionState   │                │
│           │                 │  thread_id      │                │
│           │                 │  assistant_id   │                │
│           │                 └────────┬────────┘                │
│           │                          │                          │
│           ▼                          ▼                          │
│  ┌────────────────────────────────────────────┐                │
│  │         ConnectionManager                  │                │
│  │         langgraph_sdk client               │                │
│  └────────────────┬───────────────────────────┘                │
│                   │                                             │
│                   ▼                                             │
│          ┌─────────────────┐                                   │
│          │  StreamHandler  │                                   │
│          │  Parse events   │                                   │
│          └────────┬────────┘                                   │
│                   │                                             │
│                   ▼                                             │
│          ┌─────────────────┐                                   │
│          │ OutputRenderer  │                                   │
│          │  Rich/markdown  │                                   │
│          └─────────────────┘                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │      LangGraph Dev Server             │
         │      HTTP API localhost:2024          │
         └───────────────────────────────────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │      Agent Graph Execution            │
         │      agent_snowflake                  │
         └───────────────────────────────────────┘
```

## Component Details

### 1. InputHandler
```python
class InputHandler:
    """Handles user input with rich terminal features"""

    def __init__(self, session: 'PromptSession'):
        self.session = session
        self.history = InMemoryHistory()
        self.completer = CommandCompleter()

    def read_input(self) -> str:
        """Read and return user input"""
        return self.session.prompt(
            "You: ",
            history=self.history,
            completer=self.completer,
            complete_while_typing=True
        )

    def is_command(self, text: str) -> bool:
        """Check if input is a command"""
        return text.strip().startswith('/')
```

### 2. CommandRouter
```python
class CommandRouter:
    """Routes and executes commands"""

    def __init__(self, session_state: SessionState, renderer: OutputRenderer):
        self.state = session_state
        self.renderer = renderer
        self.commands = {
            'help': self.cmd_help,
            'exit': self.cmd_exit,
            'quit': self.cmd_exit,
            'clear': self.cmd_clear,
            'history': self.cmd_history,
            'info': self.cmd_info,
            'assistant': self.cmd_assistant,
        }

    def execute(self, command_line: str) -> bool:
        """Execute command, return False if should exit"""
        cmd, *args = command_line[1:].split()

        if cmd not in self.commands:
            self.renderer.error(f"Unknown command: /{cmd}")
            return True

        return self.commands[cmd](*args)
```

### 3. SessionState
```python
@dataclass
class SessionState:
    """Maintains REPL session state"""

    url: str
    thread_id: str | None = None
    assistant_id: str | None = None
    message_history: list[dict] = field(default_factory=list)
    max_history: int = 50

    def add_message(self, role: str, content: str):
        """Add message to local history"""
        self.message_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last N messages
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]

    def reset_thread(self):
        """Clear thread and start fresh"""
        self.thread_id = None
        self.message_history.clear()
```

### 4. ConnectionManager
```python
class ConnectionManager:
    """Manages connection to LangGraph server"""

    def __init__(self, url: str, api_key: str | None = None):
        self.url = url
        self.client = get_sync_client(url=url, api_key=api_key)

    def validate_connection(self) -> bool:
        """Test server connectivity"""
        try:
            self.client.assistants.search()
            return True
        except Exception as e:
            raise ConnectionError(f"Cannot connect to server: {e}")

    def list_assistants(self) -> list[Assistant]:
        """Fetch available assistants"""
        response = self.client.assistants.search()
        return response['assistants']

    def create_thread(self, metadata: dict | None = None) -> Thread:
        """Create new conversation thread"""
        return self.client.threads.create(metadata=metadata)

    def stream_message(
        self,
        thread_id: str,
        assistant_id: str,
        message: str
    ) -> Iterator[StreamPart]:
        """Send message and stream responses"""
        input_data = {
            "messages": [{"role": "user", "content": message}]
        }

        return self.client.runs.stream(
            thread_id=thread_id,
            assistant_id=assistant_id,
            input=input_data,
            stream_mode="messages"
        )
```

### 5. StreamHandler
```python
class StreamHandler:
    """Processes streaming responses from server"""

    def __init__(self, renderer: OutputRenderer):
        self.renderer = renderer

    def process_stream(self, stream: Iterator[StreamPart]) -> str:
        """
        Consume stream and render output.
        Returns final message content.
        """
        final_content = ""

        with self.renderer.live_spinner("Agent is thinking..."):
            for part in stream:
                if part.event == "messages/partial":
                    # Streaming message chunk
                    chunk = self._extract_content(part.data)
                    if chunk:
                        self.renderer.append_chunk(chunk)
                        final_content += chunk

                elif part.event == "messages/complete":
                    # Final message
                    final_content = self._extract_content(part.data)
                    break

                elif part.event == "error":
                    raise RuntimeError(f"Stream error: {part.data}")

        return final_content

    def _extract_content(self, data: dict) -> str:
        """Extract message content from stream data"""
        # Handle different message formats
        if isinstance(data, list) and len(data) > 0:
            message = data[-1]  # Latest message
            if isinstance(message, dict):
                return message.get('content', '')
        return str(data)
```

### 6. OutputRenderer
```python
class OutputRenderer:
    """Renders output with Rich formatting"""

    def __init__(self, console: Console):
        self.console = console
        self.current_live = None

    def user_message(self, text: str):
        """Render user message"""
        self.console.print(f"[bold cyan]You:[/bold cyan] {text}")

    def agent_message(self, text: str):
        """Render agent message with markdown"""
        from rich.markdown import Markdown

        self.console.print("[bold green]Agent:[/bold green]")
        self.console.print(Markdown(text), style="green")

    def system_message(self, text: str):
        """Render system message"""
        self.console.print(f"[yellow]{text}[/yellow]")

    def error(self, text: str):
        """Render error message"""
        self.console.print(f"[bold red]Error:[/bold red] {text}")

    def live_spinner(self, message: str):
        """Context manager for live spinner"""
        from rich.spinner import Spinner
        from contextlib import contextmanager

        @contextmanager
        def _spinner():
            with Live(Spinner("dots", text=message), console=self.console):
                yield

        return _spinner()

    def separator(self):
        """Render message separator"""
        self.console.print("─" * 60, style="dim")
```

## Data Flow Diagrams

### Startup Flow
```
User executes: python -m agent_snowflake.repl
        │
        ▼
┌─────────────────┐
│ Parse CLI args  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load config     │
│ (.env, args)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ConnectionMgr   │
│ .validate()     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ List assistants │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Select/prompt   │
│ assistant       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Create thread   │
│ Initialize state│
└────────┬────────┘
         │
         ▼
    REPL Loop
```

### Message Flow
```
User types message
        │
        ▼
┌─────────────────┐
│ InputHandler    │
│ .read_input()   │
└────────┬────────┘
         │
         ▼
    [Is command?]
         │
    ┌────┴─────┐
   Yes        No
    │          │
    ▼          ▼
┌────────┐  ┌──────────────┐
│Command │  │SessionState  │
│Router  │  │get thread_id │
└────────┘  └──────┬───────┘
               │
               ▼
        ┌──────────────────┐
        │ConnectionManager │
        │.stream_message() │
        └─────────┬────────┘
                  │
                  ▼
          Server processes
                  │
                  ▼
        ┌─────────────────┐
        │ StreamHandler   │
        │ .process_stream()│
        └─────────┬───────┘
                  │
                  ▼
        ┌─────────────────┐
        │ OutputRenderer  │
        │ .agent_message()│
        └─────────┬───────┘
                  │
                  ▼
        Update SessionState
                  │
                  ▼
          Back to input
```

## State Machine

### REPL States
```
        START
          │
          ▼
    ┌──────────┐
    │CONNECTING│
    └─────┬────┘
          │ [success]
          ▼
  ┌───────────────┐
  │SELECT_ASSISTANT│
  └──────┬─────────┘
         │ [selected]
         ▼
   ┌──────────┐
   │READY     │◄──────────────┐
   └─────┬────┘               │
         │                    │
    [user input]              │
         │                    │
    ┌────┴────┐               │
    │         │               │
    ▼         ▼               │
┌────────┐  ┌─────────┐      │
│COMMAND │  │STREAMING│      │
└───┬────┘  └────┬────┘      │
    │            │            │
    │       [complete]        │
    │            │            │
    └────────────┴────────────┘
         [continue]
              │
         [/exit]
              │
              ▼
           EXIT
```

## Error Handling Strategy

### Connection Errors
```python
try:
    client.validate_connection()
except httpx.ConnectError:
    renderer.error("Cannot connect to server")
    renderer.system("Ensure server is running: make dev")
    sys.exit(1)
except Exception as e:
    renderer.error(f"Unexpected error: {e}")
    sys.exit(1)
```

### Streaming Errors
```python
try:
    for part in stream:
        process_part(part)
except httpx.ReadTimeout:
    renderer.error("Request timed out")
    renderer.system("The agent took too long to respond")
    # Return to prompt
except KeyboardInterrupt:
    renderer.system("Interrupted by user")
    # Return to prompt
except Exception as e:
    renderer.error(f"Stream error: {e}")
    # Return to prompt
```

### Graceful Degradation
```python
try:
    from rich.console import Console
    console = Console()
except ImportError:
    # Fallback to plain output
    class PlainConsole:
        def print(self, *args, **kwargs):
            print(*args)
    console = PlainConsole()
```

## Configuration Management

### Config Priority
```python
@dataclass
class Config:
    url: str
    assistant: str | None
    thread_id: str | None
    no_color: bool
    api_key: str | None

    @classmethod
    def from_environment(cls) -> 'Config':
        """Load from environment variables"""
        port = os.getenv('LANGGRAPH_DEV_SERVER_PORT', '2024')
        url = os.getenv('LANGGRAPH_URL', f'http://localhost:{port}')

        return cls(
            url=url,
            assistant=os.getenv('REPL_ASSISTANT'),
            thread_id=None,
            no_color=os.getenv('NO_COLOR') is not None,
            api_key=os.getenv('LANGGRAPH_API_KEY')
        )

    @classmethod
    def from_cli_args(cls, args: argparse.Namespace) -> 'Config':
        """Override with CLI arguments"""
        base = cls.from_environment()

        if args.url:
            base.url = args.url
        if args.assistant:
            base.assistant = args.assistant
        if args.thread_id:
            base.thread_id = args.thread_id
        if args.no_color:
            base.no_color = True

        return base
```

## Testing Architecture

### Unit Test Structure
```
tests/repl/
├── __init__.py
├── test_commands.py          # Command router and handlers
├── test_session.py           # Session state management
├── test_stream.py            # Stream parsing logic
├── test_render.py            # Output formatting
└── conftest.py               # Shared fixtures
```

### Mock Strategy
```python
# tests/conftest.py
@pytest.fixture
def mock_client():
    """Mock LangGraph client"""
    client = Mock(spec=SyncLangGraphClient)
    client.assistants.search.return_value = {
        'assistants': [
            {'assistant_id': 'test-1', 'name': 'test_agent'}
        ]
    }
    return client

@pytest.fixture
def mock_stream():
    """Mock streaming response"""
    return [
        StreamPart(event="messages/partial", data={'content': 'Hello'}),
        StreamPart(event="messages/complete", data={'content': 'Hello World'})
    ]
```

## Performance Considerations

### Streaming Buffering
- Buffer stream chunks to reduce render calls
- Flush buffer every 100ms or 10 chunks
- Prevents UI flicker with rapid updates

### Memory Management
- Limit message history to 50 messages
- Clear old messages from SessionState
- Don't store full stream responses

### Connection Pooling
- `httpx` client handles connection pooling automatically
- Reuse single client instance across requests
- No need for manual connection management

## Security Considerations

### API Key Handling
- Never prompt for API keys
- Read only from environment variables
- Don't log or display full API keys
- Mask in /info output: `LANGGRAPH_API_KEY=sk-***************xyz`

### Server URL Validation
```python
def validate_url(url: str) -> str:
    """Validate and normalize server URL"""
    if not url.startswith(('http://', 'https://')):
        raise ValueError("URL must start with http:// or https://")

    # Prevent SSRF by checking for localhost/127.0.0.1 or explicit whitelist
    parsed = urlparse(url)
    if parsed.hostname not in ['localhost', '127.0.0.1']:
        logger.warning(f"Connecting to non-local server: {parsed.hostname}")

    return url
```

### Input Sanitization
- Commands: Allow only alphanumeric + dash
- Messages: No sanitization needed (sent to agent)
- No shell command execution from user input

## Deployment Checklist

- [ ] Add `repl` module to `agent_snowflake/`
- [ ] Install dependencies: `uv add rich prompt-toolkit`
- [ ] Create `__main__.py` entry point
- [ ] Add CLI argument parsing
- [ ] Write unit tests
- [ ] Test against live server
- [ ] Add documentation to main README
- [ ] Create usage examples
- [ ] Add error message guides
