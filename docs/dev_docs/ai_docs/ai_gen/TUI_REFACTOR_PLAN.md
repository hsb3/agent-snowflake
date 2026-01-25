# TUI Refactor Plan - Webapp-Style Architecture

## Current State

**Monolithic Structure**:
```
tui/
├── app.py (690 lines)      # Everything: routing, state, rendering, business logic
├── widgets/ (12 files)     # UI components (good)
├── hitl.py (92 lines)      # HITL handler (good)
└── repl.tcss (180 lines)   # All CSS together (needs organization)
```

**Problems**:
1. **God object** - `app.py` does too much (connect, route, render, handle interrupts, manage state)
2. **CSS monolith** - Layout + component styles + theme all mixed together
3. **Hard to test** - Business logic embedded in UI code
4. **Hard to theme** - Can't easily swap layouts or color schemes
5. **Hard to extend** - Adding features requires touching 690-line file

---

## Target Architecture (Webapp-Style MVC)

### Directory Structure

```
tui/
├── app.py                          # App shell only (~100 lines)
│
├── controllers/                    # Business logic (like webapp controllers)
│   ├── __init__.py
│   ├── message_controller.py      # Handle message send/stream/display
│   ├── session_controller.py      # Handle agent/thread switching
│   ├── command_controller.py      # Handle slash commands
│   └── interrupt_controller.py    # Handle HITL interrupts
│
├── views/                          # UI layer (presentational widgets)
│   ├── __init__.py
│   ├── layout_view.py             # Main layout container
│   ├── message_area_view.py       # Message display container
│   ├── sidebar_view.py            # Sidebar with tabs
│   └── status_area_view.py        # Two-line status area
│
├── widgets/                        # Atomic UI components (existing)
│   ├── messages.py                # UserMessage, AssistantMessage, ToolCallMessage
│   ├── input.py                   # ChatInput, ChatTextArea
│   ├── status.py                  # StatusBar (deprecated for StatusArea)
│   ├── status_area.py             # Two-line status
│   ├── sidebar.py                 # Sidebar with tabs
│   └── loading.py                 # LoadingWidget
│
├── models/                         # State layer (reactive state)
│   ├── __init__.py
│   └── app_state.py               # App-level reactive state
│
├── services/                       # External integration wrappers
│   ├── __init__.py
│   ├── langgraph_service.py       # Wraps LangGraphClient
│   └── stream_service.py          # Wraps StreamHandler
│
├── styles/                         # CSS organization (NEW)
│   ├── layout.tcss                # Screen layout, grids, containers
│   ├── components.tcss            # Widget-specific styles
│   ├── theme.tcss                 # Colors, fonts, spacing
│   └── states.tcss                # State-based styling (focus, error, etc.)
│
├── hitl.py                         # HITL handler (keep as-is)
└── __main__.py                     # Entry point (keep as-is)
```

---

## CSS Organization Strategy

### Current Problem (repl.tcss - 180 lines)

Mixed concerns:
```css
/* Layout */
#messages { height: 1fr; width: 1fr; }

/* Component styling */
UserMessage { border-left: thick green; }

/* Theme */
StatusBar { background: $panel; }

/* State */
StatusBar .status-connection.connected { background: #10b981; }
```

All in one file - hard to:
- Change layout without affecting components
- Swap themes
- Find specific styles

### Proposed: Modular CSS

#### **styles/layout.tcss** (Screen structure)

```css
/* Screen and container layout - THE MASTER BLUEPRINT */

/* Main app grid */
Screen {
    layout: grid;
    grid-size: 1;           /* Single column */
    grid-rows: auto 1fr auto auto auto;
    /*          ^    ^   ^    ^    ^
              header msg input status footer */
}

/* Main content area - horizontal split */
#main-content {
    layout: horizontal;
    height: 1fr;            /* Fill available space */
}

/* Message scrollable area */
#messages {
    width: 1fr;             /* Fill remaining space */
    height: 1fr;
    overflow-y: auto;
}

/* Sidebar (hidden by default) */
#sidebar {
    width: 0;               /* Hidden */
    height: 1fr;
}

#sidebar.visible {
    width: 40;              /* 40 columns when visible */
}

#sidebar.expanded {
    width: 60;              /* 60 columns when expanded */
}

/* Input area */
ChatInput {
    height: auto;
    min-height: 3;
    max-height: 12;
}

/* Status area */
StatusArea {
    height: 2;              /* Two lines */
}

/* Docked elements */
Header {
    dock: top;
    height: 1;
}

Footer {
    dock: bottom;
    height: 1;
}
```

**Benefit**: Change entire layout in one place. Want sidebar on left vs right? Change one line.

---

#### **styles/components.tcss** (Widget-specific styles)

```css
/* Individual widget styling - COMPONENT LIBRARY */

/* User messages */
UserMessage {
    height: auto;
    border-left: thick $success;
    padding: 0 1;
    margin: 1 0;
}

/* Assistant messages */
AssistantMessage {
    height: auto;
    border-left: thick $primary;
    padding: 0 1;
    margin: 1 0;
}

/* Tool call messages */
ToolCallMessage {
    height: auto;
    border-left: thick $warning;
    padding: 0 1;
    margin: 1 0;
}

ToolCallMessage .tool-header {
    background: $surface;
}

ToolCallMessage .tool-output {
    max-height: 20;
    overflow-y: auto;
}

/* Chat input */
ChatInput .input-prompt {
    width: 3;
    color: $primary;
    text-style: bold;
}

ChatInput ChatTextArea {
    width: 1fr;
    border: none;
    background: transparent;
}

/* Sidebar tabs */
Sidebar TabbedContent {
    height: 1fr;
}

Sidebar TabPane {
    padding: 1;
}

/* Loading widget */
LoadingWidget {
    height: auto;
    text-align: center;
    padding: 1;
}
```

**Benefit**: Each component self-contained. Easy to find UserMessage styles. Can extract to component library.

---

#### **styles/theme.tcss** (Colors, spacing, typography)

```css
/* Theme variables and design tokens - DESIGN SYSTEM */

/* Color palette */
$primary: #3b82f6;          /* Blue */
$secondary: #8b5cf6;        /* Purple */
$success: #10b981;          /* Green */
$warning: #f59e0b;          /* Yellow */
$error: #ef4444;            /* Red */
$info: #06b6d4;             /* Cyan */

/* Surface colors */
$surface: #1e1e2e;          /* Dark bg */
$surface-light: #2a2a3e;    /* Lighter bg */
$panel: #181825;            /* Panel bg */

/* Text colors */
$text: #cdd6f4;             /* Normal text */
$text-muted: #6c7086;       /* Muted text */
$text-bright: #ffffff;      /* Bright text */

/* Spacing scale */
$spacing-xs: 1;
$spacing-sm: 2;
$spacing-md: 4;
$spacing-lg: 8;

/* Typography */
$font-family: monospace;
$font-size-sm: 12;
$font-size-md: 14;
$font-size-lg: 16;

/* Borders */
$border-normal: solid $text-muted;
$border-thick: thick $primary;

/* Shadows (if supported) */
$shadow-sm: 0 1 2 0 rgba(0, 0, 0, 0.05);
```

**Benefit**: Change theme in one file. Want light mode? Swap color values. Want different accent color? One variable change.

---

#### **styles/states.tcss** (State-based styling)

```css
/* State-dependent styling - INTERACTION STATES */

/* Focus states */
ChatTextArea:focus {
    border: solid $primary;
}

OptionList:focus {
    border: solid $primary;
}

/* Connection states */
.status-connection.connected {
    background: $success;
    color: black;
}

.status-connection.disconnected {
    background: $error;
    color: white;
}

/* Tool states */
ToolCallMessage.pending {
    border-left: thick $warning;
}

ToolCallMessage.success {
    border-left: thick $success;
}

ToolCallMessage.error {
    border-left: thick $error;
}

ToolCallMessage.rejected {
    border-left: thick $text-muted;
}

/* Sidebar states */
Sidebar.collapsed {
    width: 0;
}

Sidebar.visible {
    width: 40;
}

Sidebar.expanded {
    width: 60;
}

/* Input modes */
ChatInput.command-mode {
    border: solid $warning;
}

ChatInput.bash-mode {
    border: solid $info;
}

/* Loading states */
.streaming {
    opacity: 0.7;
}

.disabled {
    opacity: 0.5;
    text-style: dim;
}

/* Error states */
.error-message {
    color: $error;
    text-style: bold;
}

.warning-message {
    color: $warning;
}
```

**Benefit**: All interaction states in one place. Easy to ensure consistent hover/focus/error styling.

---

### CSS Import Strategy

**Main entry**: `tui/app.py`
```python
CSS_PATH = "styles/index.tcss"  # Master CSS file
```

**styles/index.tcss** (CSS imports):
```css
/* Master CSS - imports in order */

/* 1. Theme (variables first) */
@import "theme.tcss";

/* 2. Layout (uses theme variables) */
@import "layout.tcss";

/* 3. Components (uses theme + layout) */
@import "components.tcss";

/* 4. States (overrides based on interaction) */
@import "states.tcss";
```

**Cascading order**:
1. Theme variables defined
2. Layout structure applied
3. Component base styles
4. State overrides on top

---

## Refactor Breakdown by Layer

### Layer 1: Models (State Management)

**File**: `models/app_state.py`

```python
from textual.reactive import reactive

class AppState:
    """Centralized reactive state for TUI app.

    Like a webapp store (Redux/Vuex pattern).
    All state changes trigger UI updates via reactivity.
    """

    # Connection
    connected: reactive[bool] = reactive(False)
    server_url: reactive[str] = reactive("")

    # Session
    current_agent_id: reactive[str] = reactive("")
    current_agent_name: reactive[str] = reactive("")
    current_thread_id: reactive[str] = reactive("")

    # UI state
    streaming: reactive[bool] = reactive(False)
    sidebar_visible: reactive[bool] = reactive(False)
    sidebar_expanded: reactive[bool] = reactive(False)

    # Data
    agents: reactive[list[dict]] = reactive([], init=False)
    threads: reactive[list[dict]] = reactive([], init=False)
    tokens: reactive[int] = reactive(0)

    # Status
    status_message: reactive[str] = reactive("")
    status_error: reactive[bool] = reactive(False)
```

**Why**:
- Single source of truth
- Reactive updates propagate automatically
- Easy to debug (all state in one place)
- Can save/restore state easily

---

### Layer 2: Services (External Integration)

**File**: `services/langgraph_service.py`

```python
class LangGraphService:
    """Wrapper around LangGraphClient with app-specific logic.

    Like a webapp API service layer.
    Handles retries, caching, error formatting for UI.
    """

    def __init__(self, client: LangGraphClient):
        self.client = client
        self._agent_cache: dict[str, dict] = {}
        self._thread_cache: dict[str, dict] = {}

    async def get_agents(self) -> list[dict]:
        """Get agents with caching"""

    async def resolve_agent_name(self, name: str) -> str:
        """Resolve friendly name to UUID"""

    async def get_threads(self) -> list[dict]:
        """Get threads with caching"""

    async def create_thread_with_metadata(self, agent_id: str) -> str:
        """Create thread and cache metadata"""
```

**Why**:
- Caching logic separate from UI
- Error handling centralized
- Easy to mock for testing
- Can add retry logic without touching UI

**File**: `services/stream_service.py`

```python
class StreamService:
    """Wrapper around StreamHandler with UI-specific logic."""

    def __init__(self, handler: StreamHandler):
        self.handler = handler

    async def stream_with_widgets(
        self,
        chunks: AsyncIterator,
        on_text: Callable,
        on_tool: Callable,
        on_interrupt: Callable,
        on_usage: Callable,
    ):
        """Stream and dispatch to UI callbacks"""
        async for parsed in self.handler.process_stream(chunks):
            if parsed.chunk_type == ChunkType.TEXT_DELTA:
                await on_text(parsed.text_delta)
            elif parsed.chunk_type == ChunkType.TOOL_CALL_COMPLETE:
                await on_tool(parsed.tool_call)
            # ...
```

**Why**:
- Separates streaming mechanics from widget mounting
- Callbacks make it easy to test
- Can swap StreamHandler implementation

---

### Layer 3: Controllers (Business Logic)

**File**: `controllers/message_controller.py`

```python
class MessageController:
    """Handle message sending and streaming.

    Like a webapp controller - coordinates between services and views.
    """

    def __init__(
        self,
        langgraph_service: LangGraphService,
        stream_service: StreamService,
        app_state: AppState,
    ):
        self.langgraph = langgraph_service
        self.stream = stream_service
        self.state = app_state

    async def send_message(
        self,
        text: str,
        message_view: MessageAreaView,
    ) -> None:
        """Send message and handle streaming response.

        Args:
            text: User message
            message_view: View to mount widgets to
        """
        # 1. Add user message widget
        await message_view.add_user_message(text)

        # 2. Show loading
        loading = await message_view.show_loading()

        # 3. Create AI message widget
        ai_msg = await message_view.add_assistant_message()

        # 4. Hide loading
        await loading.remove()

        # 5. Stream from server
        chunks = self.langgraph.client.stream_message(...)

        # 6. Process stream with callbacks
        await self.stream.stream_with_widgets(
            chunks,
            on_text=ai_msg.append_content,
            on_tool=message_view.add_tool_call,
            on_interrupt=self._handle_interrupt,
            on_usage=self._update_tokens,
        )

        # 7. Finalize
        await ai_msg.stop_stream()

    async def _handle_interrupt(self, interrupt):
        """Delegate to InterruptController"""

    async def _update_tokens(self, usage):
        """Update app state tokens"""
```

**Why**:
- Business logic separate from widgets
- Easy to test (mock services and views)
- Clear flow (1-7 steps)
- Can reuse in different contexts

**File**: `controllers/session_controller.py`

```python
class SessionController:
    """Handle agent and thread switching."""

    async def switch_agent(
        self,
        agent_identifier: str,
        create_new_thread: bool = False,
    ) -> None:
        """Switch to different agent.

        Args:
            agent_identifier: Name or UUID
            create_new_thread: Whether to create fresh thread
        """
        # 1. Resolve name to UUID
        agent_id = await self.langgraph.resolve_agent_name(agent_identifier)

        # 2. Update state
        self.state.current_agent_id = agent_id
        self.state.current_agent_name = agent_identifier

        # 3. Optionally create new thread
        if create_new_thread:
            thread_id = await self.langgraph.create_thread_with_metadata(agent_id)
            self.state.current_thread_id = thread_id

    async def switch_thread(self, thread_id: str) -> None:
        """Switch to different thread"""

    async def create_thread(self) -> str:
        """Create new thread"""
```

**File**: `controllers/command_controller.py`

```python
class CommandController:
    """Handle slash commands."""

    def __init__(self, app_state: AppState, session_controller: SessionController):
        self.state = app_state
        self.session = session_controller

    async def execute_command(self, command: str, args: list[str]) -> str | None:
        """Execute command and return result message.

        Returns:
            Success/error message to display, or None
        """
        if command == "agents":
            return await self._handle_agents(args)
        elif command == "threads":
            return await self._handle_threads(args)
        # ...

    async def _handle_agents(self, args: list[str]) -> str:
        """Handle /agents command"""
```

**Why**:
- Command logic separate from routing
- Returns messages instead of rendering
- Easy to test commands in isolation

---

### Layer 4: Views (Presentational Components)

**File**: `views/layout_view.py`

```python
class LayoutView(Container):
    """Main layout container.

    Coordinates major screen areas.
    Like a webapp layout template.
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield MessageAreaView(id="message-area")
        yield SidebarView(id="sidebar")
        yield ChatInput(id="chat-input")
        yield StatusAreaView(id="status")
        yield Footer()

    def on_mount(self) -> None:
        """Wire up reactive bindings"""
        # Watch app state and update layout
```

**File**: `views/message_area_view.py`

```python
class MessageAreaView(ScrollableContainer):
    """Message display area.

    Manages mounting/unmounting message widgets.
    Like a webapp list view.
    """

    async def add_user_message(self, text: str) -> UserMessage:
        """Mount user message widget"""
        msg = UserMessage(text)
        await self.mount(msg)
        self.scroll_end(animate=False)
        return msg

    async def add_assistant_message(self, initial_text: str = "") -> AssistantMessage:
        """Mount assistant message widget"""

    async def add_tool_call(self, tool_call: ToolCall) -> ToolCallMessage:
        """Mount tool call widget"""

    async def show_loading(self, message: str = "Thinking...") -> LoadingWidget:
        """Mount loading widget"""

    async def clear_messages(self) -> None:
        """Remove all message widgets"""
```

**Why**:
- Message mounting logic in one place
- Easy to test (mock widget creation)
- Can implement message virtualization later (performance)
- Presentational only (no business logic)

**File**: `views/sidebar_view.py`

```python
class SidebarView(Container):
    """Sidebar with tabs for threads/agents/session/tools.

    Watches app state and updates content.
    """

    def __init__(self):
        super().__init__()
        self.visible = False
        self.expanded = False

    def watch_app_state_agents(self, agents: list[dict]):
        """Update agents tab when state changes"""

    def watch_app_state_threads(self, threads: list[dict]):
        """Update threads tab when state changes"""
```

---

### Layer 5: App Shell (Coordination Only)

**File**: `app.py` (~100 lines instead of 690)

```python
class REPLApp(App):
    """Main TUI application - coordination only.

    Like a webapp app.js - wires controllers to views.
    """

    CSS_PATH = "styles/index.tcss"

    BINDINGS = [
        Binding("f2", "select_agent", "Agents"),
        Binding("f3", "select_thread", "Threads"),
        Binding("f4", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+l", "clear_messages", "Clear"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()

        # Models
        self.state = AppState()

        # Services
        config = Config.from_env()
        client = LangGraphClient(config.server_url)
        self.langgraph_service = LangGraphService(client)
        self.stream_service = StreamService(StreamHandler(session))

        # Controllers
        self.message_ctrl = MessageController(
            self.langgraph_service,
            self.stream_service,
            self.state,
        )
        self.session_ctrl = SessionController(
            self.langgraph_service,
            self.state,
        )
        self.command_ctrl = CommandController(
            self.state,
            self.session_ctrl,
        )

    def compose(self) -> ComposeResult:
        """Compose layout"""
        yield LayoutView()

    async def on_mount(self) -> None:
        """Startup"""
        await self._startup()

    async def on_chat_input_submitted(self, message) -> None:
        """Route input to command or message controller"""
        if message.value.startswith("/"):
            await self._handle_command(message.value)
        else:
            await self._handle_message(message.value)

    async def _handle_message(self, text: str) -> None:
        """Delegate to MessageController"""
        message_view = self.query_one(MessageAreaView)
        await self.message_ctrl.send_message(text, message_view)

    async def _handle_command(self, text: str) -> None:
        """Delegate to CommandController"""
        cmd, *args = text[1:].split()
        result = await self.command_ctrl.execute_command(cmd, args)
        if result:
            # Show result message
            pass

    # Action methods just delegate to controllers
    def action_select_agent(self):
        """Push agent selection modal"""

    def action_toggle_sidebar(self):
        """Toggle via state"""
        self.state.sidebar_visible = not self.state.sidebar_visible
```

**Why**:
- Thin coordination layer
- All logic in controllers
- Easy to understand flow
- Can swap implementations

---

## Migration Strategy

### Phase 1: CSS Organization (Low Risk)

**Steps**:
1. Create `styles/` directory
2. Split current `repl.tcss` into 4 files
3. Create `styles/index.tcss` with imports
4. Update `app.py`: `CSS_PATH = "styles/index.tcss"`
5. Test visually - should look identical

**Benefit**: Better CSS maintenance with zero functional change

**Time**: 1-2 hours

---

### Phase 2: Extract Services (Medium Risk)

**Steps**:
1. Create `services/langgraph_service.py` wrapping client
2. Create `services/stream_service.py` wrapping handler
3. Update `app.py` to use services instead of direct client
4. Add service tests
5. Verify existing tests still pass

**Benefit**: Caching and retry logic centralized

**Time**: 2-3 hours

---

### Phase 3: Extract Controllers (Medium Risk)

**Steps**:
1. Create `controllers/message_controller.py`
2. Extract message handling from `app.py`
3. Create `controllers/session_controller.py`
4. Extract agent/thread switching
5. Create `controllers/command_controller.py`
6. Extract command logic
7. Update `app.py` to delegate to controllers
8. Add controller tests

**Benefit**: Business logic testable in isolation

**Time**: 4-6 hours

---

### Phase 4: Create Views (Low Risk)

**Steps**:
1. Create `views/message_area_view.py` wrapping ScrollableContainer
2. Create `views/sidebar_view.py` wrapping Sidebar widget
3. Create `views/layout_view.py` composing main layout
4. Update `app.py` to use views
5. Slim down `app.py` to ~100 lines

**Benefit**: Presentational components separated

**Time**: 2-3 hours

---

### Phase 5: Extract State Model (Medium Risk)

**Steps**:
1. Create `models/app_state.py`
2. Move all reactive properties from widgets to AppState
3. Update widgets to watch AppState
4. Update controllers to mutate AppState
5. Test state flow

**Benefit**: Centralized state management

**Time**: 3-4 hours

---

## Testing Strategy

**Current**: Widget tests, app integration tests

**After Refactor**:

```
tests/repl_client/tui/
├── models/
│   └── test_app_state.py           # Test state changes, reactivity
├── services/
│   ├── test_langgraph_service.py   # Test caching, retries
│   └── test_stream_service.py      # Test callback dispatching
├── controllers/
│   ├── test_message_controller.py  # Test message flow (mock services/views)
│   ├── test_session_controller.py  # Test switching logic
│   └── test_command_controller.py  # Test command execution
├── views/
│   ├── test_message_area_view.py   # Test widget mounting
│   ├── test_sidebar_view.py        # Test tab updates
│   └── test_layout_view.py         # Test composition
├── widgets/                         # Existing widget tests (keep)
└── test_app.py                      # Integration tests (slim down)
```

**Benefit**:
- Each layer tested independently
- Mock at layer boundaries
- Integration tests just verify wiring

---

## Benefits Summary

### Maintainability
- ✅ Single-purpose files (~100-200 lines each)
- ✅ Easy to find code (controllers vs views vs widgets)
- ✅ CSS organized by concern (layout vs theme vs components)

### Testability
- ✅ Controllers testable without UI
- ✅ Services testable without controllers
- ✅ Widgets testable in isolation
- ✅ Can mock at every layer boundary

### Extensibility
- ✅ Add new controller without touching app shell
- ✅ Add new view without changing layout
- ✅ Add new theme by swapping theme.tcss
- ✅ Add new layout by swapping layout.tcss

### Debuggability
- ✅ State in one place (AppState)
- ✅ Logic in controllers (set breakpoints)
- ✅ Rendering in views (visual debugging)
- ✅ Clear data flow: Service → Controller → State → View

### Theme/Layout Flexibility
- ✅ Change colors: Edit `styles/theme.tcss`
- ✅ Change layout: Edit `styles/layout.tcss`
- ✅ Change component style: Edit `styles/components.tcss`
- ✅ Add dark/light mode: Swap theme.tcss files
- ✅ Responsive layouts: Media queries in layout.tcss (if Textual supports)

---

## File Count Comparison

**Current**:
```
tui/ - 4 files + widgets/ (12 files) = 16 files total
```

**After Refactor**:
```
tui/
├── app.py (1)
├── __main__.py (1)
├── models/ (1 file)
├── services/ (2 files)
├── controllers/ (4 files)
├── views/ (4 files)
├── widgets/ (12 files - no change)
└── styles/ (5 files: index + 4 modules)
= 30 files total
```

**Trade-off**: 14 more files, but each is smaller and focused.

---

## Risks & Mitigation

### Risk 1: Breaks existing functionality
**Mitigation**:
- Refactor incrementally (phase by phase)
- Keep all tests passing at each phase
- Visual testing after each phase

### Risk 2: Over-engineering
**Mitigation**:
- Only extract when clear benefit
- Don't create layers we don't need
- Skip Phase 5 (AppState) if reactivity becomes complex

### Risk 3: CSS cascade issues
**Mitigation**:
- Test CSS split first (Phase 1)
- Keep import order strict (theme → layout → components → states)
- Visual diff before/after

---

## Recommended Execution Order

**Week 1** (Low risk, high value):
1. **CSS Organization** (Phase 1) - Split into 4 files, test visually
2. **Extract Services** (Phase 2) - Add caching layer

**Week 2** (Medium risk, medium value):
3. **Extract Controllers** (Phase 3) - Separate business logic

**Week 3** (If needed):
4. **Create Views** (Phase 4) - Wrap widgets in view layer
5. **Extract State** (Phase 5) - Only if reactivity proves valuable

**Priority**: Phase 1 (CSS) + Phase 2 (Services) give 80% of benefits with 20% of effort.

---

## Alternative: Minimal Refactor

If full MVC is too heavy:

**Just do**:
1. Split CSS (Phase 1) - Easy win
2. Extract message sending to method - Keep in app.py but organize better
3. Add inline comments marking sections

**Result**: Organized monolith instead of full MVC

---

## Decision Needed

**Option A**: Full MVC refactor (all 5 phases) - Best long-term, most work
**Option B**: CSS + Services only (phases 1-2) - Good balance
**Option C**: CSS only (phase 1) - Quick win, minimal disruption

**Recommendation**: **Option B** - CSS organization + service layer gives 80% of benefits.

Then evaluate if controllers/views are worth the complexity.
