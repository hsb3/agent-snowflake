---
doc_id: CC-2026-065
title: "TUI Layout Specification"
date: 2026-01-24
type: planning
project: repl_client
focus: tui
status: complete
tags: [tui, layout, specification, design, textual]
---

# TUI Layout Specification

Based on provided design mockup.

## Layout Modes

### Mode 1: Full Width (Default)
```
┌─ Header ────────────────────────────── 🔔 🔄 ─┐
│ LangGraph REPL                               │
├──────────────────────────────────────────────┤
│                                              │
│  Chat History (scrollable)                   │
│  > User: hello                               │
│  Agent: response...                          │
│                                              │
├──────────────────────────────────────────────┤
│  > [Text Input Area - multi-line]            │
├──────────────────────────────────────────────┤
│  Agent: agent_enhanced │ Thread: abc │ 2.3K  │ ← Status Line (customizable)
│  ● Connected │ Last update: 2s ago           │ ← Client Info/Updates
└──────────────────────────────────────────────┘
```

### Mode 2: With Sidebar (Togglable)
```
┌─ Header ──────────────── 🔔 🔄 ─┬─ Sidebar ──────┐
│ LangGraph REPL               │                 │
├──────────────────────────────┤                 │
│                              │  [Context]      │
│  Chat History (narrower)     │  - Threads      │
│  > User: hello               │  - Agents       │
│  Agent: response...          │  - Session Info │
│                              │  - Tool Outputs │
│                              │                 │
├──────────────────────────────┤                 │
│  > [Input]                   │                 │
├──────────────────────────────┴─────────────────┤
│  Agent: agent │ Thread: abc │ 2.3K             │
│  ● Connected │ Last update: 2s ago            │
└─────────────────────────────────────────────────┘
```

### Mode 3: Sidebar Expanded (F4 key)
```
┌─ Header ─────── 🔔 🔄 ─┬─ Sidebar Expanded ────────┐
│ LangGraph REPL        │                            │
├───────────────────────┤  Artifact Palette:         │
│                       │                            │
│  Chat                 │  Tool Output:              │
│  (narrow)             │  ┌──────────────────────┐  │
│                       │  │ sql_db_query result  │  │
│                       │  │ ...                  │  │
│                       │  │ ...                  │  │
│                       │  └──────────────────────┘  │
│                       │                            │
├───────────────────────┤                            │
│  > [Input]            │                            │
├───────────────────────┴────────────────────────────┤
│  Agent: agent │ Thread: abc │ 2.3K                 │
│  ● Connected │ Last update: 2s ago                │
└───────────────────────────────────────────────────┘
```

## Components

### Header
- Title: "LangGraph REPL"
- Right side icons:
  - 🔔 Notifications (errors, warnings)
  - 🔄 Agent/Thread switcher (quick access)

### Chat History
- Scrollable container
- User/Assistant/Tool messages
- Resizes width when sidebar open

### Sidebar (Optional)
- Toggleable with F4 or hamburger icon
- Tabs: Threads, Agents, Session, Tools
- Expandable to full "artifact palette" mode

### Status Area (2 lines)
**Line 1 - User Status**:
- Agent: <current_agent>
- Thread: <thread_id_short>
- Tokens: <formatted_count>

**Line 2 - Client Info**:
- Connection: ● Connected / ○ Disconnected
- Last update: <time_ago>
- Errors/warnings if any

### Footer
- Key bindings help
- Updates dynamically based on context

## Key Bindings

- **F2** - Select Agent (modal)
- **F3** - Select Thread (modal)
- **F4** - Toggle Sidebar
- **F5** - Expand Sidebar (artifact mode)
- **Ctrl+L** - Clear messages
- **Ctrl+C** - Quit
- **Ctrl+P** - Command palette

## Implementation Plan

1. Create Sidebar widget with tabs
2. Add two-line status area
3. Header with action buttons
4. CSS for responsive layout
5. Toggle logic for sidebar modes
