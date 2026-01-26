# TUI User Journeys & UI Requirements

Deriving UI component requirements from user journey analysis.

**Status:** All 5 journeys analyzed. Ready for implementation planning.

---

## Table of Contents

1. [Core UX Principles](#core-ux-principles)
2. [User Journeys](#user-journeys)
3. [Component Inventory](#component-inventory)
4. [Layout Specifications](#layout-specifications)
5. [Open Questions](#open-questions)
6. [Next Steps](#next-steps)

---

## Core UX Principles

### 1. Keyboard Navigation (Universal)

**Rule: All focusable elements must support Tab cycling and Enter activation.**

| Key | Action | Scope |
|-----|--------|-------|
| `Tab` | Next focusable element | Global |
| `Shift+Tab` | Previous focusable element | Global |
| `Enter` | Activate/select | Global |
| `Escape` | Return to previous focus region | Global |

**Focusable elements:** Buttons, inputs, list items, tabs, collapsible sections.

**Implementation:**
- `can_focus=True` on interactive widgets
- Visual focus indicator (border/outline change)
- ChatInput = default focus on main screen

### 2. Focus Region Stack

`Escape` navigates back through **focus regions** (large UI areas), not individual elements.

**Focus regions:** Main chat, Sidebar, Modals, Command Palette

```
Modal open       → Esc → Close modal, return to previous
Sidebar focused  → Esc → Return to ChatInput
Command Palette  → Esc → Close, return to ChatInput
ChatInput        → Esc → No-op (base level)
```

**Consideration:** Alternative pattern using `Ctrl+[` / `Ctrl+]` for region navigation (matches browser nav). Decision pending.

### 3. Shortcut System (Needs Redesign)

**Problem:** Current shortcuts are inconsistent and hard to remember.

**Current (scattered):**
```
F2→Agents, F3→Threads, F4→Sidebar, F5→Expand, F6→Config
Ctrl+L→Clear, Ctrl+P→Palette, Ctrl+D→Dark, Ctrl+B→Sidebar
```

**Recommended: Hybrid approach**
```
Universal:
  Ctrl+P / Ctrl+K  → Command Palette (discover everything)
  Ctrl+C           → Quit
  Escape           → Back/Cancel
  Tab / Enter      → Navigate/Select

Quick access (mnemonic):
  Ctrl+/           → Help
  Ctrl+L           → Clear
  Ctrl+B           → Sidebar

F-keys as backup:
  F1→Help, F2→Agents, F3→Threads
```

**Key principle:** Command Palette is the "forgot the shortcut" escape hatch.

---

## User Journeys

### Journey 1: First Launch & Setup ✅

**Narrative:** User opens app, connects to server, selects agent, sends first message.

**Key UI elements identified:**
- WelcomeScreen (modal with OK/Help/Quit)
- NavFooter + InfoFooter (two stacked footers)
- ConnectionIndicator (visual state)
- ErrorDisplay (actionable errors)
- SettingsScreen, HelpScreen, InputDialog

**Design decision:** Bottom layout has 3 stacked zones:
1. ChatInput (bordered)
2. NavFooter (shortcuts)
3. InfoFooter (status)

---

### Journey 2: Multi-turn Conversation with Tools ✅

**Narrative:** User chats, agent uses tools, user approves/rejects via HITL.

**Key UI elements identified:**
- ToolApprovalPrompt (Accept/Modify/Reject pattern)
- ToolStatusBadge (pending/running/success/error/rejected)
- StreamingIndicator
- Collapsible tool args/results
- FeedbackInput (for rejection reason or modification)

**Design decision:** HITL pattern is Accept/Modify/Reject with TextArea for human input:
```
┌─ Tool: sql_query ─────────────────── ⏳ Pending ┐
│  Agent proposes: [SQL shown]                    │
│  Your input: [TextArea]                         │
│  [Accept Y] [Modify M] [Reject N]               │
└─────────────────────────────────────────────────┘
```

---

### Journey 3: Thread Management ✅

**Narrative:** User creates/switches/renames/deletes threads, views history.

**Key UI elements identified:**
- ThreadListItem (name, date, count, active indicator)
- ThreadSearchInput
- ConfirmDialog (generic reusable)
- HistoryPlaceholder
- ThreadContextMenu
- ExportDialog

**Design decision:** Thread list shows metadata (date, message count, agent used).

---

### Journey 4: Agent & Thread Switching ✅

**Narrative:** User switches agents, chooses to keep or start new thread.

**Key UI elements identified:**
- AgentListItem (name, description, tools)
- AgentSwitchDialog (keep/new thread choice)
- AgentInfoPanel (expanded details)
- AgentQuickSwitch (dropdown from InfoFooter)
- SystemMessage ("Switched to...")

**Design decision:** Agent switch offers "Keep current thread" vs "Start new thread".

---

### Journey 5: Error Recovery ✅

**Narrative:** User is mid-conversation when connection drops. They need to reconnect, check thread status, and resume where they left off.

**Key UI elements identified:**
- ConnectionLostBanner (prominent reconnection UI)
- ReconnectButton (manual retry)
- ThreadStatusIndicator (idle/busy/interrupted/error)
- RunStatusBadge (pending/running/success/error/timeout)
- RecoveryDialog (options when reconnecting)

**Design decision:** Use `langgraph-sdk` for all server communication. SDK provides:
- `runs.join_stream(thread_id, run_id, last_event_id=...)` for reconnection
- `threads.get(thread_id)` to check thread status
- `runs.cancel(thread_id, run_id)` to cancel stuck runs

**State to persist in memory for recovery:**
- `assistant_id` (current agent)
- `thread_id` (current conversation)
- `run_id` (current execution, if streaming)
- `last_event_id` (for stream reconnection)

See: [langgraph-sdk-reference.md](./langgraph-sdk-reference.md)

---

## Component Inventory

### Modals & Screens (8)

| Component | Base Widgets | Journey | Priority |
|-----------|--------------|---------|----------|
| WelcomeScreen | `ModalScreen` + `Button` | J1 | High |
| SettingsScreen | `ModalScreen` + `Input` + `Switch` | J1 | High |
| HelpScreen | `ModalScreen` + `Markdown` | J1 | Medium |
| InputDialog | `ModalScreen` + `Input` + `Button` | J1 | High |
| ConfirmDialog | `ModalScreen` + `Button` | J3 | High |
| ExportDialog | `ModalScreen` + `RadioSet` | J3 | Low |
| AgentSwitchDialog | `ModalScreen` + `RadioSet` + `Input` | J4 | High |
| RecoveryDialog | `ModalScreen` + `Button` + `Static` | J5 | High |

### New Widgets (20)

| Component | Base Widgets | Journey | Priority |
|-----------|--------------|---------|----------|
| NavFooter | `Horizontal` + `Label` | J1 | High |
| InfoFooter | `Horizontal` + `Static` | J1 | High |
| ConnectionIndicator | `Static` + CSS | J1 | High |
| ErrorDisplay | `Container` + `Static` + `Button` | J1 | High |
| ToolApprovalPrompt | `Container` + `Button` + `TextArea` | J2 | High |
| ToolStatusBadge | `Static` or `Label` | J2 | High |
| StreamingIndicator | `Static` + CSS animation | J2 | Medium |
| ToolResultDisplay | `Static` or `DataTable` | J2 | Medium |
| FeedbackInput | `TextArea` or `Input` | J2 | High |
| ThreadListItem | `Static` or `ListItem` | J3 | High |
| ThreadSearchInput | `Input` | J3 | Medium |
| HistoryPlaceholder | `Static` | J3 | Low |
| ThreadContextMenu | `OptionList` (overlay) | J3 | Medium |
| AgentListItem | `Static` or `ListItem` | J4 | High |
| AgentInfoPanel | `Container` + `Static` | J4 | Medium |
| AgentQuickSwitch | `OptionList` (dropdown) | J4 | Medium |
| SystemMessage | `Static` | J4 | Medium |
| ConnectionLostBanner | `Static` + `Button` | J5 | High |
| ReconnectButton | `Button` | J5 | High |
| ThreadStatusIndicator | `Static` + CSS | J5 | Medium |

### Refactors (10)

| Component | Change | Journey |
|-----------|--------|---------|
| ChatInput | Add border | J1 |
| StatusArea | Split → InfoFooter | J1 |
| Footer | Replace with NavFooter | J1 |
| ToolCallMessage | Add approval UI, status badges | J2 |
| Sidebar ToolsTab | Tool history display | J2 |
| Sidebar ThreadsTab | Enhanced list items, search | J3 |
| MessageArea | Support history loading/prepend | J3 |
| Sidebar AgentsTab | Enhanced list items | J4 |
| AgentSelectionScreen | Add keep/new thread options | J4 |
| core/client.py | Migrate to `langgraph-sdk` | J5 |

### Reused Built-ins

| Component | Usage |
|-----------|-------|
| `ModalScreen` | All modals |
| `Button` | All modals, approval prompts |
| `Collapsible` | Tool args/results |
| `DataTable` | Tool results (tabular) |
| `RadioSet` | Export format, switch options |
| `OptionList` | Context menus, quick switch |
| `App.notify()` | Toast notifications |

### States

| Category | States |
|----------|--------|
| Connection | `disconnected`, `connecting`, `connected`, `error`, `reconnecting` |
| Tool | `pending`, `approved`, `running`, `success`, `error`, `rejected` |
| Streaming | `idle`, `streaming`, `interrupted` |
| Thread | `loading`, `active`, `selected`, `empty`, `idle`, `busy`, `interrupted`, `error` |
| Run | `pending`, `running`, `success`, `error`, `timeout`, `interrupted` |
| Agent | `active`, `selected`, `switching` |
| Recovery | `checking_status`, `resuming_stream`, `cancelling_run` |

### Keybindings by Context

**Tool Approval (J2)**
| Key | Action |
|-----|--------|
| `Y` / `Enter` | Accept |
| `M` | Modify |
| `N` / `R` | Reject |
| `Tab` | Cycle elements |
| `Escape` | Cancel run (API call needed) |

**Thread List (J3)**
| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate |
| `Enter` | Switch to thread |
| `N` | New thread |
| `R` | Rename |
| `D` | Delete (with confirm) |
| `/` | Focus search |

**Agent List (J4)**
| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate |
| `Enter` | Select (open switch dialog) |
| `I` | View info |
| `K` | Quick: keep thread |
| `N` | Quick: new thread |

---

## Layout Specifications

### Bottom Screen Layout

```
┌─────────────────────────────────────────────────────────────┐
│                      Message Area                           │
│                      (scrollable)                           │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ > [Multi-line chat input]                               │ │ ← ChatInput (bordered)
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ F2 Agents │ F3 Threads │ F4 Sidebar │ Ctrl+P Commands │ ?  │ ← NavFooter
├─────────────────────────────────────────────────────────────┤
│ Agent: agent_enhanced │ Thread: abc123 │ Tokens: 1.2k │ ●  │ ← InfoFooter
└─────────────────────────────────────────────────────────────┘
```

### Welcome Modal

```
┌─────────────────────────────────────────┐
│        Welcome to REPL Client           │
│                                         │
│  Connect to a LangGraph server and      │
│  start chatting with AI agents.         │
│                                         │
│   [OK]    [Help]    [Quit]              │
└─────────────────────────────────────────┘
```

### HITL Approval Pattern

```
┌─ Tool: sql_query ─────────────────── ⏳ Pending ┐
│  Agent proposes:                                │
│  ┌────────────────────────────────────────┐    │
│  │ SELECT * FROM customers LIMIT 10       │    │
│  └────────────────────────────────────────┘    │
│  Your input (optional):                         │
│  ┌────────────────────────────────────────┐    │
│  │ [TextArea for override/feedback]       │    │
│  └────────────────────────────────────────┘    │
│  [Accept Y]  [Modify M]  [Reject N]            │
└─────────────────────────────────────────────────┘
```

### Agent Switch Dialog

```
┌─────────────────────────────────────────────────┐
│  Switch to agent_enhanced?                      │
│                                                 │
│  ○ Keep current thread                          │
│  ○ Start new thread                             │
│                                                 │
│  [Switch]  [Cancel]                             │
└─────────────────────────────────────────────────┘
```

---

## Open Questions

### UX Decisions Needed

| Question | Context | Options |
|----------|---------|---------|
| Region navigation keys | Core UX | `Esc` only vs `Ctrl+[`/`Ctrl+]` |
| Shortcut system | Core UX | Hybrid recommended, needs final decision |
| Default agent switch | J4 | Keep thread by default, or always ask? |
| Auto-name threads | J3 | Use first message? AI summary? Manual only? |
| History pagination | J3 | Load all vs progressive load |
| Bulk tool approval | J2 | Approve multiple tools at once? |
| Auto-approve setting | J2 | Per-tool/agent trust via config_schema |

### Technical Decisions Needed

| Question | Context | Notes |
|----------|---------|-------|
| Escape during HITL | J2 | Needs `POST /runs/{id}/cancel` API call |
| Export formats | J3 | JSON, Markdown, plain text? |
| Search scope | J3 | Current thread only, or all threads? |
| Agent comparison | J4 | Side-by-side view? |

---

## Next Steps

1. ✅ Journey 1: First Launch & Setup
2. ✅ Journey 2: Multi-turn Conversation with Tools
3. ✅ Journey 3: Thread Management
4. ✅ Journey 4: Agent & Thread Switching
5. ✅ Journey 5: Error Recovery
6. ☐ Resolve open questions
7. ☐ Prioritize components for implementation
8. ☐ Create implementation plan

---

## Appendix: Journey Details

*Full step-by-step breakdowns preserved below for reference.*

<details>
<summary>Journey 1: First Launch & Setup (Full)</summary>

### Steps

| Step | User Action | System Response | UI Element |
|------|-------------|-----------------|------------|
| 1.1 | Launches app | Shows welcome modal | WelcomeScreen |
| 1.2 | Clicks "OK" | Main chat visible | - |
| 1.3 | Sees info footer | "Disconnected" or "Connecting..." | InfoFooter |
| 1.4 | (Auto) Connection attempt | Loading state | ConnectionIndicator |
| 1.5a | Connection succeeds | Toast notification | `App.notify()` |
| 1.5b | Connection fails | Error with retry | ErrorDisplay |
| 1.6 | Change server URL | Settings dialog | SettingsScreen |
| 1.7 | View agents | Agent list | AgentList |
| 1.8 | Select agent | Thread created | AgentSelectionScreen |
| 1.9 | Types message | Input captured | ChatInput |
| 1.10 | Sends message | Response streams | Messages |
| 1.11 | Learn keybindings | Help screen | HelpScreen |

### States

| State | Visual |
|-------|--------|
| `disconnected` | Red indicator |
| `connecting` | Spinner |
| `connected` | Green indicator |
| `connection_error` | Red + retry button |
| `no_agent_selected` | Prompt to select |
| `ready` | Input focused |

</details>

<details>
<summary>Journey 2: Multi-turn Conversation with Tools (Full)</summary>

### Steps

| Step | User Action | System Response | UI Element |
|------|-------------|-----------------|------------|
| 2.1 | Types query | Message sent | UserMessage |
| 2.2 | Waits | Streaming starts | StreamingIndicator |
| 2.3 | Sees response | Text streams | AssistantMessage |
| 2.4 | Agent uses tool | Tool call appears | ToolCallWidget |
| 2.5 | Sees approval | HITL prompt | ToolApprovalPrompt |
| 2.6a | Approves | Tool executes | ToolStatus: running |
| 2.6b | Rejects | Tool skipped | ToolStatus: rejected |
| 2.7 | Tool completes | Result shown | ToolResultWidget |
| 2.8 | Agent continues | More text | AssistantMessage |
| 2.9 | Another tool | Second approval | Same flow |
| 2.10 | Rejects | Agent adapts | Rejection feedback |
| 2.11 | Final answer | Complete | StreamingIndicator stops |

### Tool Status States

| State | Visual |
|-------|--------|
| `pending` | Yellow border, "Awaiting approval" |
| `approved` | Blue border |
| `running` | Blue + spinner |
| `success` | Green border, "✓ Completed" |
| `error` | Red border, error message |
| `rejected` | Gray border, "Rejected" |

### HITL Data Flow

| Action | Server Request |
|--------|----------------|
| Accept | `resume: {action: "approve"}` |
| Modify | `resume: {action: "approve", args: {...}}` |
| Reject | `resume: {action: "reject", reason: "..."}` |
| Escape | `POST /runs/{id}/cancel` |

</details>

<details>
<summary>Journey 3: Thread Management (Full)</summary>

### Steps

| Step | User Action | System Response | UI Element |
|------|-------------|-----------------|------------|
| 3.1 | View threads | Opens sidebar | ThreadList |
| 3.2 | Sees list | Metadata shown | ThreadListItem |
| 3.3 | Create new | Clicks "+ New" | InputDialog |
| 3.4 | Name thread | Optional input | InputDialog |
| 3.5 | New active | UI clears | MessageArea |
| 3.6 | Switch thread | Click in list | ThreadListItem |
| 3.7 | Load history | Messages appear | HistoryLoader |
| 3.8 | Loading state | Placeholder | HistoryPlaceholder |
| 3.9 | Rename | Context menu | ThreadContextMenu |
| 3.10 | Delete | Confirm dialog | ConfirmDialog |
| 3.11 | Search | Filter input | ThreadSearchInput |
| 3.12 | Export | Format dialog | ExportDialog |

### Thread List Item

```
┌─────────────────────────────────────────────────┐
│ ● Thread Name                                   │
│   Jan 25, 2:34 PM · 12 messages · agent_name    │
└─────────────────────────────────────────────────┘
```

</details>

<details>
<summary>Journey 4: Agent & Thread Switching (Full)</summary>

### Steps

| Step | User Action | System Response | UI Element |
|------|-------------|-----------------|------------|
| 4.1 | View agents | Opens list | AgentList |
| 4.2 | Sees agents | Metadata shown | AgentListItem |
| 4.3 | View details | Expand/info | AgentInfoPanel |
| 4.4 | Select agent | Switch prompt | AgentSwitchDialog |
| 4.5 | Keep thread | Same thread | - |
| 4.6 | Switched | Status updates | SystemMessage |
| 4.7 | Send message | New agent responds | - |
| 4.8 | New thread | Fresh start | - |
| 4.9 | Quick switch | Dropdown | AgentQuickSwitch |

### Switch Matrix

| Action | Result |
|--------|--------|
| Switch agent, keep thread | Continue with context |
| Switch agent, new thread | Fresh start |
| Switch thread, same agent | Resume conversation |
| Switch thread + agent | Load thread with new agent |

</details>

<details>
<summary>Journey 5: Error Recovery (Full)</summary>

### Steps

| Step | User Action | System Response | UI Element |
|------|-------------|-----------------|------------|
| 5.1 | Mid-conversation | Connection drops | ConnectionLostBanner |
| 5.2 | Sees banner | "Connection lost. Reconnecting..." | ConnectionIndicator |
| 5.3 | (Auto) Retry | Attempting reconnection | Spinner |
| 5.4a | Reconnect succeeds | Check thread status | ThreadStatusIndicator |
| 5.4b | Reconnect fails | Manual retry option | ReconnectButton |
| 5.5 | Thread was busy | Resume stream | `runs.join_stream()` |
| 5.6 | Stream resumes | Continue where left off | Messages |
| 5.7 | Thread interrupted | Show recovery options | RecoveryDialog |
| 5.8 | Cancel run | User presses Escape | `runs.cancel()` |
| 5.9 | Check status | Verify thread idle | `threads.get()` |
| 5.10 | Ready | Can send new message | ChatInput |

### Recovery States

| State | Visual | Action Available |
|-------|--------|------------------|
| `connection_lost` | Red banner, no spinner | Wait for auto-retry |
| `reconnecting` | Yellow banner, spinner | Cancel reconnection |
| `checking_status` | "Checking thread status..." | None |
| `resuming_stream` | "Resuming conversation..." | Cancel |
| `recovery_needed` | Dialog with options | Choose action |
| `recovered` | Toast notification | Continue |

### SDK Methods Used

| Scenario | SDK Method | Purpose |
|----------|------------|---------|
| Check thread status | `threads.get(thread_id)` | Get `status`: idle/busy/interrupted/error |
| Check run status | `runs.get(thread_id, run_id)` | Get `status`: pending/running/success/error/timeout |
| Resume stream | `runs.join_stream(thread_id, run_id, last_event_id=...)` | Continue from last event |
| Cancel stuck run | `runs.cancel(thread_id, run_id, action="interrupt")` | Stop running agent |
| Resume from interrupt | `runs.stream(thread_id, assistant_id, command=Command(resume=...))` | Continue after HITL |

### State to Track for Recovery

```python
# Minimum state needed in SessionState for recovery
session_state = {
    "assistant_id": "current-agent-uuid",
    "thread_id": "current-thread-uuid",
    "run_id": "current-run-uuid",      # Only while streaming
    "last_event_id": "evt-123",        # For stream resumption
}
```

### Connection Lost Banner

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠ Connection lost. Attempting to reconnect...  [Retry] [Cancel] │
└─────────────────────────────────────────────────────────────────┘
```

### Recovery Dialog

```
┌─────────────────────────────────────────────────────────────────┐
│  Connection Restored                                             │
│                                                                  │
│  Thread status: interrupted                                      │
│  A run was in progress when connection was lost.                 │
│                                                                  │
│  ○ Resume where we left off                                      │
│  ○ Cancel the interrupted run                                    │
│  ○ Start fresh (new message)                                     │
│                                                                  │
│  [Continue]  [Cancel]                                            │
└─────────────────────────────────────────────────────────────────┘
```

</details>
