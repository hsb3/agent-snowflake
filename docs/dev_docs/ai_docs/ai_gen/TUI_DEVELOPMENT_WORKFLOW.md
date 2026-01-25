# TUI Development Workflow - Hot Reload & Decoupled Server

## New Development Commands

### Decoupled TUI Launch

**Standalone TUI** (server must be running separately):
```bash
make tui              # Start TUI only (production mode)
make tui-dev          # Start TUI with hot reload (development mode)
```

**Combined** (convenience - starts both):
```bash
make repl-tui         # Start server + TUI together
```

---

## Development Workflow (Recommended)

### Terminal Setup (2 terminals)

**Terminal 1 - Server** (leave running):
```bash
make dev-server
```

**Terminal 2 - TUI Development**:
```bash
make tui-dev
```

### Hot Reload Features

When you run `make tui-dev`, Textual's dev mode provides:

1. **Hot Reload** - File changes trigger automatic reload
   - Changes to `src/repl_client/tui/**/*.py`
   - Changes to `src/repl_client/tui/styles/index.tcss`
   - Instant visual feedback without restarting

2. **Textual DevTools** - Press **Ctrl+T** to open
   - Live DOM tree inspection
   - CSS inspector
   - Widget hierarchy viewer
   - Console output

3. **Dev Console** - Additional debugging information
   - Widget lifecycle events
   - Reactive property changes
   - DOM updates

---

## Workflow Examples

### Example 1: Color Tweaking

**Goal**: Adjust message border colors

**Steps**:
1. Terminal 1: `make dev-server` (leave running)
2. Terminal 2: `make tui-dev`
3. Edit `src/repl_client/tui/styles/index.tcss`
   - Change `border-left: thick #42be65;` to `thick #24a148;`
4. **Save file** → TUI automatically reloads with new color
5. Iterate until satisfied
6. No manual restarts needed!

---

### Example 2: Widget Development

**Goal**: Modify StatusArea layout

**Steps**:
1. Terminal 1: `make dev-server`
2. Terminal 2: `make tui-dev`
3. Edit `src/repl_client/tui/widgets/status_area.py`
   - Modify `UserStatusLine` compose method
4. **Save file** → TUI reloads automatically
5. Press **Ctrl+T** → Open DevTools to inspect DOM
6. Iterate on changes with instant feedback

---

### Example 3: Controller Logic Changes

**Goal**: Modify message sending flow

**Steps**:
1. Terminal 1: `make dev-server`
2. Terminal 2: `make tui-dev`
3. Edit `src/repl_client/tui/controllers/message_controller.py`
   - Modify `send_message()` logic
4. **Save file** → TUI reloads
5. Test in TUI → Send a message
6. Check logs: `tail -f .repl/client.log`

---

## Quality Check Workflow

**Before committing**:
```bash
# 1. Format code
make format-repl

# 2. Run all quality checks
make check-repl

# 3. If all pass, commit
git add src/repl_client/ tests/repl_client/
git commit -m "feat: your change"
```

---

## Command Reference

### Server Commands

| Command | Description | Use Case |
|---------|-------------|----------|
| `make dev` | Server + Studio UI | Agent development, debugging |
| `make dev-server` | Server only, no browser | REPL/TUI development |

### TUI Commands

| Command | Description | Use Case |
|---------|-------------|----------|
| `make tui` | TUI only | Quick testing with running server |
| `make tui-dev` | TUI + hot reload | **Active TUI development** ⭐ |
| `make repl-tui` | Server + TUI | One-command startup, demos |

### Development Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `make format-repl` | Auto-format | Before committing |
| `make lint-repl` | Check code quality | After changes |
| `make type-check-repl` | Type safety | After changes |
| `make test-repl` | Run tests | After changes |
| `make check-repl` | All of the above | **Before every commit** ⭐ |

---

## Hot Reload Scope

### ✅ What Triggers Reload

- **Python files**: Any `.py` file in `src/repl_client/tui/`
  - Widgets, views, controllers, services, models
  - app.py changes
- **CSS files**: `src/repl_client/tui/styles/index.tcss`
- **Configuration**: Changes to reactive properties

### ❌ What Doesn't Trigger Reload

- **Core modules**: `src/repl_client/core/` (client, parsers, session)
- **Streaming**: `src/repl_client/streaming/` (handler, types)
- **Commands**: `src/repl_client/commands/`
- **UI renderers**: `src/repl_client/ui/`

**Note**: For core module changes, restart both server and TUI

---

## DevTools Usage (Ctrl+T in dev mode)

### DOM Inspector
- Navigate widget hierarchy
- See widget IDs and classes
- View widget properties

### CSS Inspector
- See computed styles for selected widget
- Debug CSS specificity
- Find style conflicts

### Console
- View log messages
- See reactive property changes
- Debug event handlers

---

## Typical Development Session

### Scenario: Implementing a New Feature

```bash
# 1. Start server (Terminal 1)
make dev-server

# 2. Start TUI in dev mode (Terminal 2)
make tui-dev

# 3. Make changes to TUI code
# Files auto-reload on save

# 4. Test interactively in TUI
# - Send messages
# - Switch agents
# - Use command palette

# 5. Check logs if needed (Terminal 3)
tail -f .repl/client.log

# 6. Before committing
make check-repl

# 7. Commit if all checks pass
git commit -m "feat: add new feature"
```

---

## Tips for Efficient Development

### 1. Keep Server Running
- Start `make dev-server` once at beginning of session
- Leave it running across multiple TUI restarts
- Only restart server if you change graph/agent code

### 2. Use Hot Reload
- `make tui-dev` for all UI development
- CSS changes are instant
- Widget changes reload in <1 second
- No need to manually restart

### 3. Use DevTools
- **Ctrl+T** to inspect DOM structure
- Useful for debugging layout issues
- See exact CSS being applied

### 4. Check Logs
- Client logs: `.repl/client.log`
- Server logs: `.repl/server.log` (when using combined commands)
- Use `tail -f` to watch live

### 5. Run Quality Checks Early
- Run `make check-repl` frequently
- Catch type errors and lint issues before they compound
- Would have caught the `get_container()` bug

---

## Comparison: Old vs New Workflow

### Old Workflow (Pre-Decoupling)

```bash
# Every change required full restart
make repl-tui
# Edit code
# Ctrl+C to stop
# make repl-tui again
# Wait for server to start (3-5 seconds)
# Test change
```

**Cycle time**: ~10 seconds per iteration

---

### New Workflow (Decoupled + Hot Reload)

```bash
# Terminal 1 (once)
make dev-server

# Terminal 2
make tui-dev
# Edit code
# Save file → auto-reload (instant)
# Test change immediately
```

**Cycle time**: <1 second per iteration ⚡

**10x faster iteration!**

---

## Server Requirements

The TUI requires a running LangGraph dev server. If you see:
```
Connection failed
```

**Fix**: Start server in another terminal
```bash
make dev-server
```

---

## Advanced: Custom Dev Server Port

If your server uses a non-default port:

**Option 1**: Environment variable
```bash
export LANGGRAPH_DEV_SERVER_PORT=3000
make tui-dev
```

**Option 2**: Update `.env` file
```env
LANGGRAPH_DEV_SERVER_PORT=3000
```

The TUI reads from `Config.from_env()` which checks environment variables and `.env` file.

---

## Summary

**For TUI Development**:
- Use `make tui-dev` with a running `make dev-server`
- Hot reload gives instant feedback on code changes
- Run `make check-repl` before committing
- 10x faster development cycle

**For Quick Testing**:
- Use `make repl-tui` for one-command startup
- Good for demos and user testing
- Not ideal for active development (slower restarts)

**For Agent Development**:
- Use `make dev` for LangGraph Studio
- TUI and classic REPL are clients only
- Server changes require server restart (not TUI restart)
