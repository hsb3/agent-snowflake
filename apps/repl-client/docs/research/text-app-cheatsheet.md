# Textual App Class Quick Reference

The `App` class in **Textual** (`textual.app.App`) is the base class for your application. It manages the lifecycle, the main loop, screens, and global state.

Below is a categorized breakdown of the key properties and methods available in the `App` class.


### TL;DR --  Frequently Used Members

| Member | Type | Description |
| --- | --- | --- |
| **`compose`** | Method | Define the UI layout (yield widgets). |
| **`run`** | Method | Start the app loop. |
| **`BINDINGS`** | Attribute | Define keyboard shortcuts. |
| **`CSS_PATH`** | Attribute | Link to external CSS file. |
| **`push_screen`** | Method | Navigate to a new view/modal. |
| **`exit`** | Method | Close the application. |
| **`query_one`** | Method | Find a specific widget by ID or class. |
| **`log`** | Method | Print debug info to the dev console (`textual console`). |



---

### 1. Configuration (Class Attributes)

Define these in your subclass to configure the application before it runs.

* **`CSS`**: `str` — Inline CSS styles for the app.
* **`CSS_PATH`**: `str | Path | list` — Path(s) to `.tcss` files to load.
* **`SCREENS`**: `dict[str, Screen]` — A dictionary mapping names to `Screen` classes or instances for easy navigation.
* **`BINDINGS`**: `list` — A list of key bindings (e.g., `Binding("q", "quit", "Quit")`).
* **`TITLE`**: `str` — The title displayed in the header (if used) and terminal window.
* **`SUB_TITLE`**: `str` — A subtitle displayed in the header.
* **`ENABLE_COMMAND_PALETTE`**: `bool` — Defaults to `True`. Enables the generic command palette (Ctrl+P).
* **`AUTO_FOCUS`**: `str | None` — A CSS selector for the widget to focus automatically on startup.

### 2. Core Lifecycle Methods

You will often override these methods to define your app's logic.

* **`compose()`**: Yields child widgets to build the initial UI (the "root" screen).
* **`on_mount()`**: Called when the app starts and is ready to receive input. Great for loading data.
* **`on_unmount()`**: Called just before the app exits. Cleanup resources here.
* **`run()`**: Starts the application loop. This is usually called on an instance (e.g., `app.run()`).

### 3. Screen Management

Textual apps can have multiple screens (like windows or pages).

* **`push_screen(screen, callback=None)`**: Pushes a new screen onto the stack.
* **`pop_screen()`**: Removes the current screen and goes back to the previous one.
* **`switch_screen(screen)`**: Replaces the current screen with a new one (no stack history).
* **`install_screen(screen, name)`**: Registers a screen instance with a specific name.
* **`uninstall_screen(name)`**: Removes a registered screen.

### 4. Instance Properties (State)

Access these `self.` properties inside your app methods.

* **`title`** / **`sub_title`**: `str` — Reactive properties to update the window title/subtitle dynamically.
* **`dark`**: `bool` — Reactive property to toggle Dark/Light mode (`True` by default).
* **`screen`**: `Screen` — The currently active screen.
* **`console`**: `Console` — The underlying `rich.console.Console` object (useful for debugging).
* **`focused`**: `Widget | None` — The widget that currently holds focus.
* **`mouse_over`**: `Widget | None` — The widget currently under the mouse cursor.
* **`size`**: `Size` — The current terminal dimensions (width, height).

### 5. Utilities & Actions

Methods to interact with the system or control app flow.

* **`exit(return_code=0, message=None)`**: Stops the app. Optional `message` is printed to stdout after exit.
* **`suspend()`**: Context manager to temporarily suspend the app and return to the terminal (e.g., to run a subprocess like `vim`).
* **`bell()`**: Plays a system bell/beep.
* **`copy_to_clipboard(text)`**: Copies text to the system clipboard.
* **`open_url(url)`**: Opens a URL in the default web browser.
* **`refresh()`**: Forces a repaint of the screen (rarely needed manually).
* **`call_from_thread(callable, *args)`**: Thread-safe way to update UI from a background thread.
* **`call_later(callback)`**: Schedules a callback to run on the next iteration of the event loop.

### 6. Event Handling

The `App` class handles specific events globally.

* **`action_{name}()`**: Define methods like `action_quit` to respond to key bindings (e.g., `action_quit` runs when "quit" is triggered).
* **`on_key(event)`**: Global key handler.
* **`on_load()`**: Called very early, before the terminal goes into application mode.

### 7. DOM & Widget Inheritance

Since `App` inherits from `Widget` (and `DOMNode`), it also has standard widget methods:

* **`query(selector)`**: Returns a `DOMQuery` of widgets matching the CSS selector.
* **`query_one(selector)`**: Returns a single matching widget (raises error if 0 or >1 matches).
* **`mount(*widgets)`**: Dynamically adds widgets to the current screen.
* **`notify(message, title=..., severity=...)`**: Shows a "toast" notification.

