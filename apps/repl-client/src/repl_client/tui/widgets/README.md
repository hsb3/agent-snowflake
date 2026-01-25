# Textual Message Widgets

TUI widgets for REPL message display, based on deepagents patterns.

## Components

### UserMessage

Static widget displaying user input with green styling.

**Features:**
- Green left border (thick)
- Styled prefix `"> "` in bold green
- Auto height
- Safe from markup injection

**Usage:**
```python
from repl_client.tui.widgets import UserMessage

widget = UserMessage("Hello, agent!")
```

**CSS Classes:**
- `UserMessage` - Main container

### AssistantMessage

Vertical container displaying assistant responses with markdown support.

**Features:**
- Markdown rendering via Textual's Markdown widget
- Efficient streaming using MarkdownStream
- Cyan left border
- Methods: `append_content()`, `stop_stream()`, `set_content()`

**Usage:**
```python
from repl_client.tui.widgets import AssistantMessage

# Create with initial content
widget = AssistantMessage("Initial markdown content")

# Stream content incrementally
await widget.append_content("More ")
await widget.append_content("content...")
await widget.stop_stream()

# Set full content (stops stream if active)
await widget.set_content("New full content")
```

**CSS Classes:**
- `AssistantMessage` - Container
- `AssistantMessage Markdown` - Inner markdown widget

### ToolCallMessage

Vertical container displaying tool calls with collapsible output.

**Features:**
- Multi-state: pending, success, error, rejected
- Collapsible output (3-line preview by default)
- Click to expand/collapse
- Status indicators with colors
- Auto-expand for errors
- Filters large args for file tools

**Usage:**
```python
from repl_client.tui.widgets import ToolCallMessage

# Create tool call
widget = ToolCallMessage(
    "sql_db_query",
    {"query": "SELECT * FROM users", "limit": 10}
)

# Set success with result
widget.set_success("Found 10 users")

# Set error (auto-expands)
widget.set_error("Connection failed")

# Set rejected
widget.set_rejected()

# Toggle output expansion
widget.toggle_output()

# Check if has output
if widget.has_output:
    print("Tool has output to display")
```

**States:**
- `pending` - Initial state (yellow border)
- `success` - Successful execution (green status, show output)
- `error` - Failed execution (red status, auto-expanded)
- `rejected` - User rejected (yellow status)

**CSS Classes:**
- `ToolCallMessage` - Container
- `.tool-header` - Tool name header
- `.tool-args` - Arguments display
- `.tool-status` - Status indicator
- `.tool-output-preview` - Collapsed preview
- `.tool-output-hint` - Expand hint
- `.tool-output` - Full output (scrollable)

**Preview Behavior:**
- Shows first 3 lines OR 200 characters (whichever is smaller)
- Click to expand/collapse
- Errors always expanded
- Empty output not shown

**Arg Filtering:**
- `write_file`, `edit_file`: Only shows `file_path`, `path`, `replace_all`
- Other tools: Shows all args (max 3 inline)

## Demo App

Run the demo to see all widgets in action:

```bash
uv run python scripts/repl_client/demo_tui_messages.py
```

**Key bindings:**
- `q` - Quit
- `t` - Toggle tool output expansion
- `s` - Demo streaming to assistant widget

## Tests

Run widget tests:

```bash
uv run pytest tests/repl_client/tui/test_messages.py -v
```

## Design Patterns

### From deepagents

1. **UserMessage**: Static widget with Rich Text object for styled prefix
2. **AssistantMessage**: Uses MarkdownStream for efficient streaming
3. **ToolCallMessage**: Multi-state with collapsible output, click to toggle
4. **Markup Safety**: User content uses `markup=False` to prevent injection

### CSS Styling

- Green: User messages
- Cyan: Assistant messages
- Yellow: Tool calls (default)
- Red: Errors
- Green: Success
- Muted: Secondary text

### State Management

- Widgets are presentation only
- State transitions via explicit methods (`set_success()`, etc.)
- No automatic state changes
- Parent manages lifecycle (mounting, updates, removal)
