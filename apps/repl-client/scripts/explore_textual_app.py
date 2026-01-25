# %% [markdown]
# # Exploring Textual App Class
#
# Interactive notebook to explore the `textual.app.App` class.
# Run with: `uv run python -m jupytext --to notebook scripts/explore_textual_app.py`
# Or use VS Code's interactive Python feature (Ctrl+Enter on cells)

# %%
from textual.app import App
import inspect
from rich import print as rprint
from rich.table import Table
from rich.console import Console

console = Console()

# %% [markdown]
# ## Basic Inspection

# %%
# Module location
print(f"Module: {inspect.getfile(App)}")
print(f"Base classes: {[c.__name__ for c in App.__mro__]}")

# %% [markdown]
# ## Properties
# Properties are computed attributes accessed like regular attributes

# %%
def get_properties(cls):
    """Get all properties of a class."""
    props = []
    for name in dir(cls):
        if not name.startswith('_'):
            obj = getattr(cls, name, None)
            if isinstance(obj, property):
                doc = obj.fget.__doc__ if obj.fget else None
                props.append((name, doc))
    return sorted(props, key=lambda x: x[0])

props = get_properties(App)
table = Table(title="App Properties (Public)", show_lines=True)
table.add_column("Property", style="cyan")
table.add_column("Description", style="green")

for name, doc in props[:20]:  # First 20
    doc_preview = (doc.split('\n')[0][:80] + '...') if doc and len(doc) > 80 else (doc.split('\n')[0] if doc else 'No docs')
    table.add_row(name, doc_preview)

console.print(table)
print(f"\n... and {len(props) - 20} more properties")

# %% [markdown]
# ## Key Properties in Detail

# %%
import random

core_properties = ['screen', 'focused', 'is_running', 'current_theme', 'workers', 'children']

# get 10 random properties from props list after removing core_properties
additional_properties = [name for name, _ in props if name not in core_properties]
random_properties = random.sample(additional_properties, 4)
key_properties = core_properties + random_properties


# key_properties = [name for name, _ in props[:10]]  # First 10 properties for detail


for prop_name in key_properties:
    prop = getattr(App, prop_name, None)
    if isinstance(prop, property) and prop.fget:
        print(f"\n{'='*60}")
        print(f"App.{prop_name}")
        print(f"{'='*60}")
        sig = inspect.signature(prop.fget)
        print(f"Returns: {sig.return_annotation if sig.return_annotation != inspect.Parameter.empty else 'Unknown'}")
        if prop.fget.__doc__:
            print(f"\nDocstring:\n{prop.fget.__doc__}")
        else:
            print("No docstring available.")
            # print(f"Doc: {prop.fget.__doc__[:200]}...")

# %% [markdown]
# ## Methods - Lifecycle

# %%
lifecycle_methods = [
    'compose', 'on_mount', 'run', 'run_async', 'exit',
    'refresh', 'recompose', 'mount', 'mount_all'
]

table = Table(title="Lifecycle Methods")
table.add_column("Method", style="cyan")
table.add_column("Signature", style="yellow")
table.add_column("Description", style="green")

for method_name in lifecycle_methods:
    method = getattr(App, method_name, None)
    if method and callable(method):
        try:
            sig = str(inspect.signature(method))[:50]
        except:
            sig = "(...)"
        doc = method.__doc__
        doc_preview = doc.split('\n')[0][:60] if doc else 'No docs'
        table.add_row(method_name, sig, doc_preview)

console.print(table)

# %% [markdown]
# ## Methods - Screen Management

# %%
screen_methods = [
    'push_screen', 'pop_screen', 'switch_screen', 'install_screen',
    'uninstall_screen', 'get_screen', 'is_screen_installed'
]

print("Screen Management Methods:")
print("=" * 60)
for method_name in screen_methods:
    method = getattr(App, method_name, None)
    if method:
        try:
            sig = inspect.signature(method)
            print(f"\nApp.{method_name}{sig}")
            if method.__doc__:
                first_line = method.__doc__.strip().split('\n')[0]
                print(f"  → {first_line}")
        except Exception as e:
            print(f"\nApp.{method_name}: {e}")

# %% [markdown]
# ## Methods - Actions

# %%
action_methods = [name for name in dir(App) if name.startswith('action_') and callable(getattr(App, name))]

print(f"Found {len(action_methods)} action methods:\n")
for method_name in sorted(action_methods):
    method = getattr(App, method_name)
    try:
        sig = inspect.signature(method)
        print(f"  {method_name}{sig}")
    except:
        print(f"  {method_name}(...)")

# %% [markdown]
# ## Methods - Focus & Input

# %%
focus_methods = [
    'set_focus', 'action_focus', 'action_focus_next', 'action_focus_previous',
    'capture_mouse', 'check_consume_key', 'simulate_key'
]

for method_name in focus_methods:
    method = getattr(App, method_name, None)
    if method:
        print(f"\n{method_name}:")
        help_text = method.__doc__
        if help_text:
            # First paragraph
            para = help_text.split('\n\n')[0].strip()
            print(f"  {para[:200]}")

# %% [markdown]
# ## Class Variables (Configuration)

# %%
class_vars = [
    'TITLE', 'SUB_TITLE', 'CSS', 'CSS_PATH', 'BINDINGS',
    'SCREENS', 'MODES', 'DEFAULT_MODE', 'COMMANDS',
    'ENABLE_COMMAND_PALETTE', 'AUTO_FOCUS'
]

table = Table(title="Key Class Variables")
table.add_column("Variable", style="cyan")
table.add_column("Default Value", style="yellow")
table.add_column("Type", style="green")

for var_name in class_vars:
    val = getattr(App, var_name, None)
    val_str = repr(val)[:40] + '...' if len(repr(val)) > 40 else repr(val)
    table.add_row(var_name, val_str, type(val).__name__)

console.print(table)

# %% [markdown]
# ## Reactive Attributes

# %%
# Reactive attributes are special - they trigger watchers when changed
print("Reactive Attributes (trigger watchers on change):")
print("=" * 60)

reactives = getattr(App, '_reactives', {})
for name, reactive in reactives.items():
    print(f"  {name}: {type(reactive).__name__}")

# %% [markdown]
# ## Exploring a Specific Method in Detail

# %%
def explore_method(cls, method_name):
    """Deep dive into a specific method."""
    method = getattr(cls, method_name, None)
    if not method:
        print(f"Method {method_name} not found")
        return

    print(f"{'='*60}")
    print(f"{cls.__name__}.{method_name}")
    print(f"{'='*60}")

    try:
        sig = inspect.signature(method)
        print(f"\nSignature: {sig}")

        # Parameter details
        print("\nParameters:")
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            default = f" = {param.default}" if param.default != inspect.Parameter.empty else ""
            annotation = f": {param.annotation.__name__}" if param.annotation != inspect.Parameter.empty else ""
            print(f"  {param_name}{annotation}{default}")

        # Return type
        if sig.return_annotation != inspect.Signature.empty:
            print(f"\nReturns: {sig.return_annotation}")
    except Exception as e:
        print(f"Could not get signature: {e}")

    print(f"\nDocstring:\n{method.__doc__}")

# Example: explore push_screen
explore_method(App, 'push_screen')

# %% [markdown]
# ## Try It: Explore Any Method
# Change the method name below to explore others

# %%
# Uncomment and modify to explore other methods:
# explore_method(App, 'run')
# explore_method(App, 'compose')
# explore_method(App, 'switch_mode')
# explore_method(App, 'notify')

# %% [markdown]
# ## Quick Reference: Most Used Methods

# %%
most_used = {
    "Lifecycle": ['compose', 'on_mount', 'run', 'exit'],
    "Screens": ['push_screen', 'pop_screen', 'switch_screen'],
    "Widgets": ['mount', 'query', 'query_one', 'get_widget_by_id'],
    "Focus": ['set_focus', 'action_focus_next'],
    "Styling": ['refresh', 'refresh_css', 'add_class', 'remove_class'],
    "Workers": ['run_worker', 'call_later', 'set_timer'],
    "Notifications": ['notify', 'clear_notifications'],
}

for category, methods in most_used.items():
    print(f"\n{category}:")
    for m in methods:
        print(f"  - App.{m}()")

# %% [markdown]
# ## View Source Code

# %%
def view_source(cls, method_name, max_lines=30):
    """View the source code of a method."""
    method = getattr(cls, method_name, None)
    if not method:
        print(f"Method {method_name} not found")
        return

    try:
        source = inspect.getsource(method)
        lines = source.split('\n')
        if len(lines) > max_lines:
            print('\n'.join(lines[:max_lines]))
            print(f"\n... ({len(lines) - max_lines} more lines)")
        else:
            print(source)
    except Exception as e:
        print(f"Could not get source: {e}")

# Example: view compose method source
# view_source(App, 'compose')

# %% [markdown]
# ## Bindings Reference

# %%
print("Default App Bindings:")
print("=" * 40)
for binding in App.BINDINGS:
    print(f"  {binding}")

# %%
# Interactive: Get full help on App
# Uncomment to see complete documentation:
# help(App)

# %%
