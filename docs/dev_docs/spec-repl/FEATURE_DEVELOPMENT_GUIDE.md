# Feature Development Guide - REPL Client TUI

## Architecture Quick Reference

**5 Layers** (bottom to top):
1. **Models** - Application state (AppState)
2. **Services** - External API wrappers (LangGraph, streaming)
3. **Controllers** - Business logic and coordination
4. **Views** - Presentational components
5. **App** - Event routing shell

**Data Flow**: User Input → App → Controller → Service → AppState → View → Widget

**Core Principle**: State in AppState, logic in Controllers, presentation in Views, routing in App.

---

## Where Does My Feature Go?

**Quick Decision Matrix**:

| I want to... | Modify Layer | Also Update |
|-------------|--------------|-------------|
| Add slash command | CommandController | - |
| Add message type | Widget + MessageAreaView | StreamService (if streamed) |
| Add API operation | Service + Controller | AppState (if new state) |
| Add UI panel | Widget + View | LayoutView + CSS |
| Add keybinding | App (BINDINGS) | Controller (action logic) |
| Add setting/preference | AppState | Controller (mutation) + CSS |
| Change styling | CSS (appropriate section) | - |
| Change business logic | Controller | Service (if API changes) |

---

## Common Feature Patterns

### Adding a Slash Command

**Layers**: CommandController → App (auto-routes)

**Process**:
1. Add handler method to CommandController
2. Add case to execute_command() switch
3. Return success/error message string
4. App displays automatically

**When to involve services**: If command needs agent/thread API calls

---

### Adding a Message or Stream Event Type

**Layers**: Widget → View → StreamService → Controller

**Process**:
1. Create widget class (e.g., ImageMessage)
2. Add mounting method to MessageAreaView
3. Add callback to StreamService (e.g., on_image)
4. Wire callback in MessageController
5. Add component styles to CSS

**Pattern**: Stream → Service callback → Controller → View → Widget

---

### Adding Agent/Thread Operation

**Layers**: Service → Controller → View

**Process**:
1. Add API wrapper to LangGraphService
2. Add coordination method to SessionController
3. Update view if display changes
4. Update AppState if tracking new data

**Pattern**: Service handles API, Controller handles logic, View handles display

---

### Adding UI Section

**Layers**: Widget → View → LayoutView → CSS → App

**Process**:
1. Create widget component
2. Create view wrapper with semantic methods
3. Add to LayoutView composition
4. Add layout rules (layout.tcss) and styles (components.tcss)
5. Add visibility state to AppState
6. Wire toggle action in App

---

### Adding State or Setting

**Layers**: AppState → Controller → View/App

**Process**:
1. Add field to AppState with type annotation
2. Add update method (e.g., set_dark_mode())
3. Controller calls update when triggered
4. Views/App read state for display
5. CSS handles visual changes via states.tcss

**Rule**: Controllers mutate, Views/App read

---

## Modifying Existing Features

| Change | Primary File | Secondary Files |
|--------|-------------|-----------------|
| Message appearance | styles/components.tcss | Widget (if structure) |
| Agent switching logic | SessionController | LangGraphService (if API) |
| Streaming behavior | StreamService, MessageController | Widget (if display) |
| Screen layout | styles/layout.tcss, LayoutView | - |
| Command behavior | CommandController | Service (if new API) |
| Theme/colors | styles/theme.tcss | - |
| State transitions | styles/states.tcss | Widget (if behavior) |

---

## CSS Organization

**4 Sections** (in index.tcss):
- **Theme** - Colors, spacing, typography (design tokens)
- **Layout** - Screen structure, grids, containers, positioning
- **Components** - Widget-specific styles (messages, inputs, sidebar)
- **States** - Interaction states (focus, hover, connected, error)

**When to use which**:
- Changing colors/fonts → theme.tcss
- Changing screen layout → layout.tcss
- Changing widget appearance → components.tcss
- Changing interactive states → states.tcss

---

## Testing Strategy

**Test by layer with mocked dependencies**:

1. **Services** - Mock API client, test caching/retries
2. **Controllers** - Mock services and views, test logic
3. **Views** - Mock widgets, test mounting
4. **Integration** - Test full flow with real components

**Pattern**: Isolated unit tests per layer + integration tests for wiring

---

## Development Workflow

**Bottom-up approach**:
1. **Service** (if external API needed) → Add wrapper method
2. **Controller** → Add business logic
3. **AppState** (if new state) → Add field + update method
4. **View** → Add presentation method
5. **Widget** (if new UI) → Create component
6. **CSS** → Add styles in appropriate section
7. **App** → Wire keybinding/action
8. **Tests** → Unit tests per layer + integration test

---

## State Management Rules

**AppState is single source of truth**:
- ✅ Controllers mutate via update methods
- ✅ Views/App read for display
- ❌ Never mutate from Views or Widgets
- ❌ Never bypass update methods

**Flow**: Controller → AppState.set_*() → View reads → Widget displays

---

## Service Integration Rules

**Services wrap external APIs**:
- ✅ Add caching in Service
- ✅ Add retry logic in Service
- ✅ Format errors in Service
- ❌ No business logic in Service
- ❌ Never call clients directly from Controllers

**Pattern**: Controller → Service → External API

---

## Best Practices

1. **Separation of concerns** - Logic in Controllers, presentation in Views, state in AppState
2. **Semantic methods** - View methods describe intent (add_user_message vs mount_widget)
3. **Mock at boundaries** - Test each layer independently
4. **Unidirectional flow** - Data flows down (Controller → State → View), events flow up (Widget → App → Controller)
5. **CSS modularity** - Use correct section for each concern
6. **Explicit state** - All state in AppState, not scattered

---

## Common Anti-Patterns to Avoid

| ❌ Don't | ✅ Do |
|---------|-------|
| Put logic in App event handlers | Delegate to Controllers |
| Call API clients directly | Go through Services |
| Store state in Controllers/Views | Use AppState |
| Mount widgets from App | Use View methods |
| Mix CSS concerns | Use appropriate section |
| Mutate state directly | Use AppState update methods |
| Skip View layer | Always use View semantic API |

---

## Quick Reference: File Locations

```
tui/
├── app.py                     # Event routing only
├── models/app_state.py        # All application state
├── services/
│   ├── langgraph_service.py  # Agent/thread API
│   └── stream_service.py     # Streaming events
├── controllers/
│   ├── message_controller.py # Send/stream messages
│   ├── session_controller.py # Switch agent/thread
│   ├── command_controller.py # Process commands
│   └── interrupt_controller.py # HITL interrupts
├── views/
│   ├── layout_view.py        # Screen composition
│   ├── message_area_view.py  # Message mounting
│   ├── sidebar_view.py       # Sidebar wrapper
│   └── status_area_view.py   # Status display
├── widgets/                   # Atomic UI components
└── styles/index.tcss          # All CSS (4 sections)
```

---

## Example Walkthrough: Adding Thread Deletion

1. **Service**: Add delete_thread(thread_id) to LangGraphService
2. **Controller**: Add delete_current_thread() to SessionController
   - Calls service.delete_thread()
   - Updates app_state (removes from threads list)
   - Returns success message
3. **View**: Add refresh_threads() to SidebarView (may already exist)
4. **App**: Add keybinding → action_delete_thread() → controller method
5. **Test**: Mock service in controller test, verify state update

**Total changes**: 1 service method, 1 controller method, 1 app action, 1 test

---

**See TUI_REFACTOR_PLAN.md for architectural rationale and detailed layer descriptions.**
