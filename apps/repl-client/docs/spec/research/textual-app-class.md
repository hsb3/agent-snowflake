# Textual App Class Reference

Research notes on `textual.app.App` class structure and capabilities.

## Overview

| Category | Count |
|----------|-------|
| Properties | 64 |
| Methods | 245 |
| Class Variables | 61 |

## Multi-Screen Architecture

Textual uses a **stack-based screen model**. An App always has at least one screen, but can manage many.

### Key Concepts

| Concept | Description |
|---------|-------------|
| `screen` | Property returning the currently visible (top of stack) screen |
| `screen_stack` | Full navigation history as a list |
| `SCREENS` | Class variable - dict of pre-registered screens `{"name": ScreenClass}` |
| `MODES` | Class variable - named modes, each with its own screen stack |

### Navigation Patterns

```python
# 1. Push/Pop (modal-style navigation, keeps previous screens in memory)
app.push_screen(SettingsScreen())   # Go to settings
app.pop_screen()                     # Return to previous

# 2. Switch (replaces current screen, no stack buildup)
app.switch_screen(HomeScreen())      # Replace current with home

# 3. Modes (separate screen stacks for different app states)
class MyApp(App):
    MODES = {
        "normal": "main",
        "edit": "editor",
    }
    SCREENS = {
        "main": MainScreen,
        "editor": EditorScreen,
    }
```

### Screen Management Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `push_screen` | `(screen, callback=None, wait_for_dismiss=False)` | Push new screen on stack |
| `pop_screen` | `()` | Pop current screen, return to previous |
| `switch_screen` | `(screen)` | Replace top of stack (no history) |
| `install_screen` | `(screen, name)` | Register a screen for later use |
| `get_screen` | `(screen, screen_class=None)` | Get an installed screen by name |
| `is_screen_installed` | `(screen)` | Check if screen is installed |
| `uninstall_screen` | `(screen)` | Remove an installed screen |

## Key Properties

### Lifecycle & State
- `is_running` - Whether the app is currently running
- `is_headless` - Running without a terminal (testing)
- `is_inline` - Running in inline mode
- `return_code` - Exit code after app closes
- `return_value` - Value returned from app

### UI & Display
- `screen` - Current active screen
- `screen_stack` - Snapshot of screen navigation stack
- `focused` - Currently focused widget
- `size` - Terminal size (width, height)
- `viewport_size` - Viewport dimensions
- `current_theme` - Active theme name
- `colors` - Current color scheme
- `dark` - Whether dark mode is active

### Workers & Async
- `workers` - Worker manager for background tasks
- `animator` - Animation controller

### DOM & Structure
- `children` - Direct child widgets
- `tree` - Full widget tree representation
- `css_tree` - CSS rule tree

## Key Methods by Category

### Lifecycle
- `compose()` - Override to define UI structure
- `on_mount()` - Called after app is mounted
- `run()` - Start the app (blocking)
- `run_async()` - Start the app (async)
- `exit(return_value=None)` - Exit the app

### Widget Management
- `mount(*widgets)` - Add widgets to current screen
- `mount_all(widgets)` - Add multiple widgets
- `query(selector)` - Query widgets by CSS selector
- `query_one(selector)` - Query single widget (raises if not found)
- `query_one_optional(selector)` - Query single widget (returns None)
- `get_widget_by_id(id)` - Get widget by ID

### Focus
- `set_focus(widget)` - Set focus to widget
- `action_focus_next()` - Move focus forward
- `action_focus_previous()` - Move focus backward

### Styling
- `refresh()` - Refresh display
- `refresh_css()` - Reload CSS
- `add_class(class_name)` - Add CSS class
- `remove_class(class_name)` - Remove CSS class
- `toggle_class(class_name)` - Toggle CSS class

### Workers & Timers
- `run_worker(work, ...)` - Run background task
- `call_later(callback)` - Schedule callback
- `set_timer(delay, callback)` - One-shot timer
- `set_interval(interval, callback)` - Repeating timer

### Notifications
- `notify(message, ...)` - Show notification toast
- `clear_notifications()` - Clear all notifications

## Class Variables (Configuration)

| Variable | Type | Description |
|----------|------|-------------|
| `TITLE` | str | App title |
| `SUB_TITLE` | str | App subtitle |
| `CSS` | str | Inline CSS |
| `CSS_PATH` | str/list | Path(s) to CSS files |
| `BINDINGS` | list | Key bindings |
| `SCREENS` | dict | Pre-registered screens |
| `MODES` | dict | App modes with screen stacks |
| `DEFAULT_MODE` | str | Initial mode |
| `COMMANDS` | set | Command palette commands |
| `ENABLE_COMMAND_PALETTE` | bool | Enable Ctrl+P command palette |
| `AUTO_FOCUS` | str | CSS selector for auto-focus |

## Action Methods

Built-in actions (can be bound to keys):

- `action_quit()` - Quit the app
- `action_bell()` - Terminal bell
- `action_focus_next()` / `action_focus_previous()` - Navigate focus
- `action_toggle_dark()` - Toggle dark mode
- `action_screenshot()` - Save screenshot
- `action_command_palette()` - Open command palette
- `action_push_screen(screen)` - Push screen
- `action_pop_screen()` - Pop screen
- `action_switch_screen(screen)` - Switch screen
- `action_switch_mode(mode)` - Switch mode
- `action_add_class(class)` / `action_remove_class(class)` - Modify classes
- `action_toggle_class(class)` - Toggle class

## Reactive Attributes

These trigger watchers when changed:

- `title` - App title (updates terminal title)
- `sub_title` - App subtitle
- `theme` - Current theme
- `ansi_color` - ANSI color mode
- `app_focus` - Whether app has focus

## Default Bindings

```python
BINDINGS = [
    Binding("ctrl+c", "quit", "Quit", show=False, priority=True),
    Binding("ctrl+backslash", "command_palette", show=False),
]
```

## Exploration Commands

```bash
# List all members
uv run python -c "from textual.app import App; print(dir(App))"

# Get help on specific method
uv run python -c "from textual.app import App; help(App.push_screen)"

# Get method signature
uv run python -c "import inspect; from textual.app import App; print(inspect.signature(App.notify))"

# View source code
uv run python -c "import inspect; from textual.app import App; print(inspect.getsource(App.compose))"

# IPython exploration
uv run ipython
>>> from textual.app import App
>>> App.push_screen?      # Quick help
>>> App.push_screen??     # Source code
```

## Related Resources

- Exploration notebook: `scripts/explore_textual_app.py`
- Textual docs: https://textual.textualize.io/
- Screen guide: https://textual.textualize.io/guide/screens/
