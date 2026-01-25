# Feature Development Guide - REPL Client TUI (DRAFT)

## Architecture Overview

The TUI follows a webapp-style MVC architecture with clear separation of concerns:

**Layers (bottom to top)**:
1. **Models** (`models/`) - Application state (AppState class)
2. **Services** (`services/`) - External API wrappers (LangGraph client, streaming)
3. **Controllers** (`controllers/`) - Business logic coordination
4. **Views** (`views/`) - Presentational components that mount widgets
5. **Widgets** (`widgets/`) - Atomic UI components (messages, inputs, etc.)
6. **App** (`app.py`) - Event routing and orchestration shell

**Data Flow**:
```
User Input → App → Controller → Service → AppState → View → Widget
```

**Key Principles**:
- State lives in AppState (single source of truth)
- Business logic lives in Controllers
- External calls go through Services
- Presentation logic lives in Views
- App is thin - just routes events to controllers

---

## Adding New Features

### 1. New Slash Command

**Example**: Add `/history` command to show conversation history

**What to modify**:
- **CommandController**: Add `_handle_history()` method
- **CommandController**: Add case to `execute_command()` switch
- **App**: Command routing already handles it automatically

**Pattern**:
- Controller method processes command
- Returns success/error message string
- App displays the message

**When to add service**: If command needs API calls (agents, threads, etc.)

---

### 2. New Message Type or Streaming Event

**Example**: Add support for image messages or file attachments

**What to modify**:
- **Widget**: Create new widget class (e.g., `ImageMessage` in `widgets/messages.py`)
- **MessageAreaView**: Add method like `add_image_message(image_data)`
- **StreamService**: Add callback for new event type (e.g., `on_image`)
- **MessageController**: Wire callback to view method
- **CSS**: Add styles in `styles/components.tcss`

**Pattern**:
- Stream event → StreamService callback → Controller → View → Widget
- Service handles event detection
- Controller handles coordination
- View handles mounting
- Widget handles rendering

---

### 3. New Agent/Thread Operation

**Example**: Add thread deletion or agent favoriting

**What to modify**:
- **LangGraphService**: Add method like `delete_thread(thread_id)`
- **SessionController**: Add coordination method like `delete_current_thread()`
- **SidebarView**: Add UI method to refresh thread list
- **App**: Add action/keybinding if needed

**Pattern**:
- Service wraps API call
- Controller coordinates logic + state updates
- View updates UI
- App wires keybinding to controller

---

### 4. New UI Section or Panel

**Example**: Add a debug panel showing token usage graphs

**What to modify**:
- **Widget**: Create `DebugPanel` widget in `widgets/debug.py`
- **View**: Create `DebugPanelView` in `views/debug_panel_view.py`
- **LayoutView**: Add panel to compose() and layout
- **CSS**: Add layout rules in `styles/layout.tcss`, component styles in `styles/components.tcss`
- **AppState**: Add relevant state fields (e.g., `debug_panel_visible`)
- **App**: Add action to toggle panel visibility

**Pattern**:
- Widget defines the UI component
- View wraps widget with semantic methods
- LayoutView integrates into screen
- CSS handles visual layout
- AppState tracks visibility/state
- App provides toggle action

---

### 5. New State or Setting

**Example**: Add "dark mode" or "compact view" preference

**What to modify**:
- **AppState**: Add field like `dark_mode: bool = False`
- **AppState**: Add update method like `set_dark_mode(enabled: bool)`
- **App or Controller**: Call `app_state.set_dark_mode()` when toggled
- **CSS**: Add conditional styles in `styles/states.tcss` or theme variants
- **Views/Widgets**: Update based on state if needed

**Pattern**:
- State lives in AppState
- Controllers mutate state through update methods
- Views/App read state to adjust behavior
- CSS handles visual changes via class toggles

---

### 6. New Service Integration

**Example**: Add filesystem browsing or clipboard support

**What to modify**:
- **Service**: Create new service class like `FilesystemService` in `services/filesystem_service.py`
- **Controller**: Create or update controller to use service
- **App**: Instantiate service in `__init__`, pass to controller
- **Widget/View**: Add UI for displaying/interacting with data

**Pattern**:
- Service wraps external API/library
- Service handles caching, retries, error formatting
- Controller coordinates service calls with state/views
- App wires service to controller

---

## Modifying Existing Features

### Change Message Display Style

**Modify**:
- **CSS**: `styles/components.tcss` for base styles, `styles/states.tcss` for states
- **Widget**: `widgets/messages.py` only if structure changes
- **View**: `MessageAreaView` only if mounting logic changes

### Change Agent Switching Behavior

**Modify**:
- **SessionController**: Update `switch_agent()` logic
- **LangGraphService**: If API call changes
- **AppState**: If new state tracking needed

### Change Streaming Display

**Modify**:
- **StreamService**: Callback dispatching logic
- **MessageController**: Coordination between callbacks
- **Widget**: Update streaming widget if display changes

### Add New Keybinding

**Modify**:
- **App**: Add to `BINDINGS` list
- **App**: Add `action_*` method
- **Controller**: Delegate to appropriate controller method

---

## Testing Strategy

**Test by Layer**:

1. **Services**: Mock API clients, test caching/retries/errors
   - No UI needed
   - Fast unit tests

2. **Controllers**: Mock services and views, test business logic
   - No UI needed
   - Test coordination flow

3. **Views**: Mock widgets, test mounting/unmounting logic
   - Minimal UI (can test methods directly)
   - Test semantic API

4. **App Integration**: Test full flow with test harness
   - Full UI environment
   - Test event routing and coordination

**Pattern**:
- Test each layer in isolation with mocked dependencies
- Integration tests verify wiring between layers
- Widget tests verify rendering (existing widget test suite)

---

## Common Patterns

### Adding a Feature Checklist

1. **Identify the layer**: Where does this feature belong?
   - New data source? → Service
   - Business logic? → Controller
   - UI component? → Widget/View
   - User action? → App keybinding + Controller

2. **Work bottom-up**:
   - Service (if needed) → Controller → View → Widget → CSS → App wiring

3. **Update state if needed**:
   - Add fields to AppState
   - Add update methods to AppState
   - Controllers mutate, Views/App read

4. **Write tests at each layer**:
   - Service tests (mock client)
   - Controller tests (mock service + view)
   - View tests (mock widgets)
   - Integration test (full flow)

5. **Update CSS**:
   - Layout changes → `styles/layout.tcss`
   - Component styles → `styles/components.tcss`
   - Theme changes → `styles/theme.tcss`
   - State styles → `styles/states.tcss`

### State Mutation Pattern

- **Controllers** mutate state via AppState methods
- **Views/App** read state for display
- **Never** mutate state directly from Views or Widgets
- State flows unidirectionally: Controller → AppState → View

### Service Call Pattern

- Always go through Services, never call LangGraphClient directly
- Services handle caching, so check cache before API calls
- Services return data, Controllers decide what to do with it
- Controllers update AppState based on service responses

### UI Update Pattern

- Controller calls View methods (semantic API)
- View mounts/updates Widgets
- Widgets handle their own rendering
- CSS handles styling, not inline styles

---

## File Organization Reference

```
tui/
├── app.py                  # Event routing, orchestration shell
├── models/
│   └── app_state.py       # Centralized state
├── services/
│   ├── langgraph_service.py   # LangGraph API wrapper
│   └── stream_service.py      # Streaming wrapper
├── controllers/
│   ├── message_controller.py  # Message/streaming logic
│   ├── session_controller.py  # Agent/thread logic
│   ├── command_controller.py  # Command processing
│   └── interrupt_controller.py # HITL logic
├── views/
│   ├── layout_view.py         # Main layout
│   ├── message_area_view.py   # Message display
│   ├── sidebar_view.py        # Sidebar wrapper
│   └── status_area_view.py    # Status display
├── widgets/                # Atomic UI components
│   ├── messages.py        # Message widgets
│   ├── input.py          # Input widgets
│   ├── status_area.py    # Status widgets
│   └── sidebar.py        # Sidebar widget
└── styles/
    ├── index.tcss        # Master CSS (all sections)
    ├── layout.tcss       # Layout reference
    ├── components.tcss   # Components reference
    ├── theme.tcss        # Theme reference
    └── states.tcss       # States reference
```

---

## Quick Decision Tree

**I want to add...**

- **A new command** → CommandController
- **A new message type** → Widget + MessageAreaView + StreamService
- **A new API call** → LangGraphService (or new service)
- **A new UI section** → Widget + View + LayoutView + CSS
- **A new keybinding** → App BINDINGS + action method + Controller
- **A new setting** → AppState + Controller update + UI trigger
- **A new external integration** → New Service + Controller + View

**I want to change...**

- **How messages look** → CSS (components.tcss)
- **Screen layout** → CSS (layout.tcss) + LayoutView
- **Agent switching logic** → SessionController
- **Streaming behavior** → StreamService + MessageController
- **Command behavior** → CommandController
- **Colors/theme** → CSS (theme.tcss)
- **State management** → AppState methods

---

## Best Practices

1. **Keep layers separated** - Don't let business logic leak into Views or Widgets
2. **Use semantic methods** - View methods should describe intent, not implementation
3. **Mock at boundaries** - Test each layer with mocked dependencies
4. **State flows one way** - Controllers → AppState → Views (never backwards)
5. **Services are thin wrappers** - Just add caching/retries/error handling, not business logic
6. **CSS is modular** - Put styles in the right section (layout vs components vs theme vs states)
7. **Controllers coordinate** - They orchestrate Services and Views, but don't do UI or API calls directly

---

## Examples of Good vs Bad

### Good: Adding a new command
- ✅ Add method to CommandController
- ✅ Controller calls SessionController/Service if needed
- ✅ Controller returns message string
- ✅ App displays message

### Bad: Adding a new command
- ❌ Put logic in App event handler
- ❌ Call LangGraphClient directly from App
- ❌ Update UI widgets directly from App

### Good: Adding new state
- ✅ Add field to AppState with type annotation
- ✅ Add update method to AppState
- ✅ Controller calls update method
- ✅ View reads state to update display

### Bad: Adding new state
- ❌ Store state in Controller
- ❌ Store state in View
- ❌ Mutate state directly without method

### Good: Adding new UI
- ✅ Create Widget for atomic component
- ✅ Create View to wrap widget with semantic API
- ✅ Update LayoutView to compose new view
- ✅ Add CSS in appropriate section

### Bad: Adding new UI
- ❌ Put all UI logic in App
- ❌ Skip View layer, mount widgets directly
- ❌ Mix layout and styling in one CSS section

---

## Getting Help

**Understand the codebase**:
- Read `tui-refactor-plan.md` for architecture rationale
- Read `app.py` to see orchestration pattern
- Read a Controller to see business logic pattern
- Read a View to see presentation pattern

**Common mistakes**:
- Business logic in App → Move to Controller
- State scattered across files → Move to AppState
- Direct API calls → Go through Service
- Direct widget mounting in App → Use View methods
- Mixing CSS concerns → Use correct section file

**Architecture questions**:
- "Where does X belong?" → See Quick Decision Tree above
- "How do I test X?" → See Testing Strategy above
- "How do layers communicate?" → See Data Flow diagram
