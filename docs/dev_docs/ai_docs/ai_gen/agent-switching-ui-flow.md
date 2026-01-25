# Agent Switching UI Flow Diagram

## Visual Flow

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                           REPL TUI Interface                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Status Bar (Top):                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Agent: agent_minimal │ Thread: e4f2a1b3... │ Tokens: 1.2K              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│           ↑ UPDATES IMMEDIATELY                                              │
│                                                                              │
│  [User presses F2]                                                           │
│           ↓                                                                  │
│                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                     Agent Selection Modal                              │ │
│  │                                                                        │ │
│  │  Select Agent (Enter to confirm, Esc to cancel)                       │ │
│  │                                                                        │ │
│  │  → agent_minimal ✓                                                     │ │
│  │    agent_enhanced                                                      │ │
│  │    agent                                                               │ │
│  │                                                                        │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  [User selects agent_enhanced → Enter]                                      │
│           ↓                                                                  │
│                                                                              │
│  Status Bar (UPDATED):                                                       │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │ Agent: agent_enhanced │ Thread: e4f2a1b3... │ Tokens: 1.2K             │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│           ↑ Changed from agent_minimal to agent_enhanced                     │
│                                                                              │
│  [User presses F4 to open sidebar]                                           │
│           ↓                                                                  │
│                                                                              │
│  Sidebar (Right):                                                            │
│  ┌──────────────────────┐                                                   │
│  │ [Threads] [Agents]   │                                                   │
│  │                      │                                                   │
│  │  agent_minimal       │                                                   │
│  │  3f239ca8...         │                                                   │
│  │                      │                                                   │
│  │  agent_enhanced      │ ← Background highlighted (cyan)                   │
│  │  1ee80259...     ✓   │ ← Checkmark shows current agent                   │
│  │                      │                                                   │
│  │  agent               │                                                   │
│  │  fe096781...         │                                                   │
│  │                      │                                                   │
│  └──────────────────────┘                                                   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Code Flow

```
User Action: Press F2
    │
    ▼
REPLApp.action_select_agent()  (app.py:408)
    │
    ├─→ Get agents from service (force_refresh=True)
    │
    ├─→ Show AgentSelectionScreen modal
    │       │
    │       ▼
    │   User selects agent_id
    │
    ▼
SessionController.switch_agent(agent_id)  (session_controller.py:53)
    │
    ├─→ Resolve agent name to UUID
    │
    ├─→ Update session.current_assistant_id
    │
    ├─→ Update app_state.current_agent_id
    │
    ├─→ Update app_state.current_agent_name
    │
    └─→ Return {success: True, display_name: "agent_enhanced"}
    │
    ▼
UI Updates:
    │
    ├─→ StatusArea.set_agent(display_name)  (app.py:429)
    │       │
    │       └─→ user_line.agent = display_name  (reactive property)
    │               │
    │               └─→ watch_agent() triggered automatically
    │                       │
    │                       └─→ display.update("Agent: agent_enhanced")
    │
    └─→ _update_sidebar_content()  (app.py:432)
            │
            └─→ sidebar.populate_agents(agents, current_agent_id)
                    │
                    ├─→ Clear agent list
                    │
                    ├─→ For each agent:
                    │   ├─→ Check if agent_id == current_agent_id
                    │   ├─→ Add "✓" if current
                    │   └─→ Add "current" CSS class if current
                    │
                    └─→ Mount new widgets
```

## State Flow

```
Before Switch:
    session.current_assistant_id = "3f239ca8-..."  (agent_minimal)
    app_state.current_agent_id = "3f239ca8-..."
    app_state.current_agent_name = "agent_minimal"

    Status Bar: "Agent: agent_minimal"
    Sidebar: agent_minimal ✓

    ↓ [User selects agent_enhanced]

During Switch:
    SessionController.switch_agent("1ee80259-...")
        ├─→ session.set_agent("1ee80259-...")
        ├─→ app_state.set_agent("1ee80259-...", "agent_enhanced")
        └─→ Return display_name = "agent_enhanced"

After Switch:
    session.current_assistant_id = "1ee80259-..."  (agent_enhanced)
    app_state.current_agent_id = "1ee80259-..."
    app_state.current_agent_name = "agent_enhanced"

    Status Bar: "Agent: agent_enhanced"  ← Updated immediately
    Sidebar: agent_enhanced ✓            ← Updated immediately
```

## Reactive Update Mechanism

```
Textual Reactive Properties:

1. Setting reactive property:
   user_line.agent = "agent_enhanced"

2. Textual framework automatically calls watcher:
   watch_agent(old_value="agent_minimal", new_value="agent_enhanced")

3. Watcher updates UI:
   display.update("Agent: agent_enhanced")

4. Screen re-renders:
   Status bar shows new agent name

Total time: < 1ms (synchronous)
```

## Multiple Entry Points

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Agent Switching Entry Points                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. F2 Keyboard Shortcut                                            │
│     → action_select_agent()                                         │
│     → Show modal → switch_agent()                                   │
│                                                                     │
│  2. Sidebar Click                                                   │
│     → on_sidebar_agent_selected()                                   │
│     → switch_agent()                                                │
│                                                                     │
│  3. Command Palette                                                 │
│     → "Switch Agent" command                                        │
│     → action_select_agent()                                         │
│     → Show modal → switch_agent()                                   │
│                                                                     │
│  ALL PATHS:                                                         │
│  ├─→ Call SessionController.switch_agent()                          │
│  ├─→ Update status bar                                              │
│  └─→ Update sidebar                                                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Visual Indicators Summary

| UI Element | Before Switch | After Switch | Update Method |
|------------|---------------|--------------|---------------|
| Status Bar | `Agent: agent_minimal` | `Agent: agent_enhanced` | Reactive property |
| Sidebar Checkmark | `agent_minimal ✓` | `agent_enhanced ✓` | Imperative rebuild |
| Sidebar Background | Cyan highlight on minimal | Cyan highlight on enhanced | CSS class `current` |
| Sidebar Text | All agents listed | All agents listed | Same |

## User Experience Timeline

```
Time  Event                           User Sees
────────────────────────────────────────────────────────────────────
0ms   User presses F2                 Status bar shows "agent_minimal"

50ms  Modal appears                   Agent list with agent_minimal ✓

1s    User navigates to agent_enhanced Arrow keys to highlight desired agent

1.5s  User presses Enter              Modal closes

1.51s Status bar updates              "Agent: agent_enhanced" appears
      Sidebar updates (if open)       agent_enhanced ✓ highlighted

      ✓ Clear visual confirmation that switch succeeded
      ✓ No confusion about which agent is active
```

## Acceptance Criteria ✓

- [x] Status bar immediately shows new agent name
- [x] Sidebar updates to show current agent with ✓
- [x] Sidebar highlights current agent with background color
- [x] User gets clear visual feedback that switch succeeded
- [x] No confusion about which agent is active
- [x] Multiple entry points all work consistently
- [x] Reactive updates work without explicit refresh() calls
- [x] State management is consistent across all components
