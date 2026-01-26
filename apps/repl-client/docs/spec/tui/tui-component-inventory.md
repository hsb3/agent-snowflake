# TUI Component Inventory & Planning

Planning document for the REPL Client TUI design system and component architecture.

## Current State Summary

The TUI has grown organically with:
- 1 main screen + 4 modal screens
- 12+ custom widgets
- ~15 built-in Textual widgets used
- 1073 lines of CSS (Carbon Design System based)
- MVC-ish architecture (Controllers, Views, Services)

---

## Part 1: Macro UI Components

### Screens (Full-page views)

| Screen | Status | Purpose | Notes |
|--------|--------|---------|-------|
| **MainScreen** | Implicit | Chat interface | Currently just App.compose(), could extract |
| **AgentSelectionScreen** | ✅ Exists | Modal - pick agent | ModalScreen with OptionList |
| **ThreadSelectionScreen** | ✅ Exists | Modal - pick/create thread | ModalScreen with OptionList |
| **AgentConfigScreen** | ✅ Exists | Modal - view agent schema | Tabbed layout |
| **SettingsScreen** | ❌ Needed | App preferences | Theme, keybindings, server URL |
| **HelpScreen** | ❌ Needed | Keyboard shortcuts, commands | Markdown-based help content |
| **DebugScreen** | 🔄 Optional | Dev debugging | State inspector, event log |

### Modals (Overlay dialogs)

| Modal | Status | Purpose | Pattern |
|-------|--------|---------|---------|
| **ConfirmDialog** | ❌ Needed | Yes/No confirmations | "Delete thread?", "Disconnect?" |
| **InputDialog** | ❌ Needed | Single-field input | "Thread name:", "Server URL:" |
| **NotificationToast** | ❌ Needed | Transient messages | Use Textual's `notify()` system |
| **CommandPalette** | ✅ Exists | Master command navigator | Custom implementation |
| **ErrorModal** | ❌ Needed | Display error details | Full stacktrace view |

### Sidebars / Panels

| Panel | Status | Purpose | Notes |
|-------|--------|---------|-------|
| **Sidebar** | ✅ Exists | Threads/Agents/Session/Tools tabs | Toggleable, expandable |
| **ToolOutputPanel** | 🔄 Consider | Dedicated tool output viewer | Alternative to inline collapse |
| **HistoryPanel** | 🔄 Consider | Conversation history browser | Search past messages |

### Persistent UI Zones

| Zone | Status | Purpose | Notes |
|------|--------|---------|-------|
| **Header** | ✅ Built-in | App title, clock | Could customize |
| **Footer** | ✅ Built-in | Key bindings | Auto-generated from BINDINGS |
| **StatusArea** | ✅ Exists | Agent/Thread/Tokens + Connection | Two-line custom status |
| **ChatInput** | ✅ Exists | User input area | Multi-line with history |
| **MessageArea** | ✅ Exists | Scrollable message display | Dynamic widget mounting |

---

## Part 2: Widget Inventory

### Built-in Widgets Currently Used

| Widget | Where Used | Notes |
|--------|------------|-------|
| `Header` | LayoutView | Standard header |
| `Footer` | LayoutView | Shows BINDINGS |
| `Static` | Multiple | Text display, containers |
| `Label` | Sidebar items, status | Styled text |
| `TextArea` | ChatTextArea base | Multi-line input |
| `Markdown` | AssistantMessage | Rendered markdown |
| `OptionList` | Modals, CommandPalette | Selection lists |
| `TabbedContent` | Sidebar, AgentConfig | Tab containers |
| `TabPane` | Sidebar, AgentConfig | Individual tabs |
| `Button` | Modals | Actions |
| `Input` | CommandPalette search | Single-line input |
| `Container` | Multiple | Layout container |
| `Vertical` | Multiple | Vertical layout |
| `Horizontal` | Multiple | Horizontal layout |
| `ScrollableContainer` | MessageArea | Scrolling content |
| `VerticalScroll` | Sidebar tabs | Scrollable lists |

### Built-in Widgets to Consider Adding

| Widget | Use Case | Priority |
|--------|----------|----------|
| `Collapsible` | Tool output expand/collapse | High |
| `DataTable` | Token stats, session info | Medium |
| `LoadingIndicator` | Built-in spinner | Low (have custom) |
| `ProgressBar` | Long operations | Low |
| `RadioSet` | Settings options | Medium |
| `Switch` | Toggle settings | Medium |
| `Tree` | Thread hierarchy, tool tree | Medium |
| `RichLog` | Debug output | Low |
| `Rule` | Visual separators | Low |
| `Link` | Clickable URLs in messages | Medium |
| `Select` | Dropdown selections | Medium |
| `Placeholder` | Empty states | Low |

### Custom Widgets - Current

| Widget | File | Base Class | Purpose |
|--------|------|------------|---------|
| `ChatInput` | input.py | Vertical | Input container with mode detection |
| `ChatTextArea` | input.py | TextArea | Custom keybindings, history |
| `UserMessage` | messages.py | Static | User message display |
| `AssistantMessage` | messages.py | Static | Assistant message with streaming |
| `ToolCallMessage` | messages.py | Static | Tool calls with collapsible output |
| `LoadingWidget` | loading.py | Static | Animated spinner |
| `CommandPalette` | command_palette.py | Container | Master command navigator |
| `Sidebar` | sidebar.py | Container | Tabbed sidebar |
| `StatusArea` | status_area.py | Horizontal | Two-line status (deprecated?) |
| `UserStatusLine` | status_area.py | Horizontal | Agent/Thread/Tokens |
| `ClientInfoLine` | status_area.py | Horizontal | Connection/Status |
| `StatusBar` | status.py | Horizontal | Legacy single-line |
| `HistoryManager` | history.py | (non-widget) | Command history |
| `SchemaFieldWidget` | agent_config.py | Horizontal | Schema field display |
| `SchemaViewer` | agent_config.py | VerticalScroll | Schema container |

### Custom Widgets - Needed

| Widget | Base Class | Purpose | Priority |
|--------|------------|---------|----------|
| `ConfirmDialog` | ModalScreen | Yes/No prompts | High |
| `InputDialog` | ModalScreen | Single input prompts | High |
| `SystemMessage` | Static | Welcome, info, warnings | Medium |
| `ToolApprovalWidget` | Container | HITL approval UI | High |
| `ErrorDisplay` | Static | Formatted error messages | Medium |
| `EmptyState` | Static | "No messages", "No threads" | Low |
| `ThreadListItem` | Static | Richer thread display | Medium |
| `AgentListItem` | Static | Richer agent display | Medium |
| `TokenCounter` | Static | Visual token display | Low |
| `ConnectionIndicator` | Static | Visual connection status | Medium |

---

## Part 3: Design System Foundation

### Color Tokens (Carbon-based, already defined)

```
/* Surfaces */
--surface-primary:    gray-90 (dark) / gray-30 (light)
--surface-secondary:  gray-80 (dark) / gray-20 (light)
--surface-tertiary:   gray-70 (dark) / gray-10 (light)

/* Text */
--text-primary:       gray-10 (dark) / black (light)
--text-secondary:     gray-40 (dark) / gray-70 (light)
--text-muted:         gray-50 (dark) / gray-60 (light)

/* Interactive */
--interactive-primary: blue-60
--interactive-hover:   blue-70
--interactive-focus:   blue-40 (outline)

/* Status */
--status-success:     green-40
--status-error:       red-60
--status-warning:     yellow-30
--status-info:        blue-40

/* Borders */
--border-subtle:      gray-70 (dark) / gray-40 (light)
--border-strong:      gray-60 (dark) / gray-50 (light)
```

### Spacing Scale (to formalize)

```
/* Spacing tokens */
--space-1: 1    /* 4px equivalent */
--space-2: 2    /* 8px */
--space-3: 3    /* 12px */
--space-4: 4    /* 16px */
--space-6: 6    /* 24px */
--space-8: 8    /* 32px */

/* Component spacing */
--padding-widget:     1 2      /* vertical horizontal */
--padding-container:  1 2
--padding-modal:      2 4
--margin-between:     1        /* between stacked items */
```

### Typography (terminal constraints)

```
/* Text styles (via classes) */
.text-title     { text-style: bold; }
.text-subtitle  { text-style: italic; }
.text-muted     { color: $text-secondary; }
.text-code      { /* monospace by default */ }
.text-error     { color: $error; text-style: bold; }
.text-success   { color: $success; }
```

### Semantic CSS Classes (to create)

```css
/* Layout utilities */
.full-width     { width: 100%; }
.full-height    { height: 100%; }
.hidden         { display: none; }
.flex-grow      { width: 1fr; }

/* State classes */
.is-active      { /* active state styles */ }
.is-disabled    { opacity: 0.5; }
.is-loading     { /* loading state */ }
.is-error       { border: thick $error; }
.is-success     { border: thick $success; }

/* Message types */
.msg-user       { border-left: thick $blue-60; }
.msg-assistant  { /* default styling */ }
.msg-system     { color: $text-secondary; text-style: italic; }
.msg-error      { border-left: thick $error; background: $error-bg; }

/* Interactive states */
.focusable:focus { border: thick $interactive-focus; }
.hoverable:hover { background: $surface-secondary; }
.clickable       { /* cursor indicator in terminals? */ }
```

---

## Part 4: Component Hierarchy

```
App (REPLApp)
│
├── Screens
│   ├── MainScreen (implicit)
│   │   └── LayoutView
│   │       ├── Header
│   │       ├── #main-content (Horizontal)
│   │       │   ├── MessageAreaView
│   │       │   │   ├── SystemMessage (welcome)
│   │       │   │   ├── UserMessage *
│   │       │   │   ├── AssistantMessage *
│   │       │   │   ├── ToolCallMessage *
│   │       │   │   └── LoadingWidget
│   │       │   └── SidebarView (toggleable)
│   │       │       └── Sidebar
│   │       │           └── TabbedContent
│   │       │               ├── ThreadsTab
│   │       │               ├── AgentsTab
│   │       │               ├── SessionTab
│   │       │               └── ToolsTab
│   │       ├── ChatInput
│   │       │   └── ChatTextArea
│   │       ├── StatusAreaView
│   │       │   ├── UserStatusLine
│   │       │   └── ClientInfoLine
│   │       └── Footer
│   │
│   ├── AgentSelectionScreen (modal)
│   ├── ThreadSelectionScreen (modal)
│   ├── AgentConfigScreen (modal)
│   ├── SettingsScreen (modal) [TODO]
│   └── HelpScreen (modal) [TODO]
│
├── Dialogs (overlay)
│   ├── CommandPalette
│   ├── ConfirmDialog [TODO]
│   └── InputDialog [TODO]
│
└── Services (non-UI)
    ├── LangGraphService
    └── StreamService
```

---

## Part 5: Implementation Priorities

### Phase 1: Foundation (stabilize current)
1. Extract semantic CSS classes from inline styles
2. Create design token variables file
3. Standardize widget base classes
4. Document existing component API

### Phase 2: Missing Essentials
1. `ConfirmDialog` - for destructive actions
2. `InputDialog` - for user prompts
3. `SystemMessage` widget - consistent system messages
4. Improve `ToolCallMessage` with proper `Collapsible`

### Phase 3: Polish
1. `SettingsScreen` - theme, keybindings
2. `HelpScreen` - keyboard shortcuts reference
3. `EmptyState` widgets - better empty states
4. `ConnectionIndicator` - visual connection status

### Phase 4: Advanced
1. `HistoryPanel` - search past conversations
2. `DebugScreen` - state inspector
3. Thread/Agent list item enhancements
4. Animation polish

---

## Part 6: File Organization

### Recommended Structure

```
tui/
├── __main__.py
├── app.py                    # REPLApp class
│
├── screens/                  # Full-page views
│   ├── __init__.py
│   ├── main_screen.py        # Extract from app.py
│   ├── agent_config.py       # ✅ Exists
│   ├── agent_selection.py    # Extract from app.py
│   ├── thread_selection.py   # Extract from app.py
│   ├── settings.py           # TODO
│   └── help.py               # TODO
│
├── widgets/                  # Reusable components
│   ├── __init__.py
│   ├── input.py              # ✅ ChatInput, ChatTextArea
│   ├── messages.py           # ✅ UserMessage, AssistantMessage, ToolCallMessage
│   ├── sidebar.py            # ✅ Sidebar
│   ├── status_area.py        # ✅ StatusArea components
│   ├── command_palette.py    # ✅ CommandPalette
│   ├── loading.py            # ✅ LoadingWidget
│   ├── dialogs.py            # TODO: ConfirmDialog, InputDialog
│   └── common.py             # TODO: EmptyState, ErrorDisplay, SystemMessage
│
├── views/                    # Presentational containers
│   ├── __init__.py
│   ├── layout_view.py        # ✅
│   ├── message_area_view.py  # ✅
│   ├── sidebar_view.py       # ✅
│   └── status_area_view.py   # ✅
│
├── controllers/              # Business logic
│   ├── __init__.py
│   ├── message_controller.py # ✅
│   ├── session_controller.py # ✅
│   ├── command_controller.py # ✅
│   └── interrupt_controller.py # ✅
│
├── services/                 # Backend integration
│   ├── __init__.py
│   ├── langgraph_service.py  # ✅
│   └── stream_service.py     # ✅
│
├── models/                   # Data models
│   ├── __init__.py
│   └── app_state.py          # ✅
│
└── styles/                   # CSS
    ├── index.tcss            # ✅ Master file
    ├── _tokens.tcss          # TODO: Design tokens only
    ├── _layout.tcss          # Reference
    ├── _components.tcss      # Reference
    └── _states.tcss          # Reference
```

---

## References

- Textual App Class: [textual-app-class.md](./textual-app-class.md)
- Anatomy of Textual UI: https://textual.textualize.io/blog/2024/09/15/anatomy-of-a-textual-user-interface/
- Textual Widgets: https://textual.textualize.io/widgets/
- Textual CSS: https://textual.textualize.io/guide/CSS/
