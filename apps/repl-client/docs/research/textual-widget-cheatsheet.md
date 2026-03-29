# Text Pre-build widgets Cheat Sheet

Here is a cheatsheet for the pre-built widgets available in `textual.widgets`. 
These are the building blocks you will use inside your `compose()` methods.

### 1. Essentials & Structure

These standard widgets provide the basic framework and text display for your application.

| Widget | Description | Common Usage |
| --- | --- | --- |
| **`Header`** | Displays the `App.TITLE` and a clock at the top. | `yield Header()` (usually first). |
| **`Footer`** | Displays current key bindings at the bottom. | `yield Footer()` (usually last). |
| **`Label`** | Simple text display. Can be styled easily. | `Label("Hello World")` |
| **`Static`** | Base class for simple content. Can render text or Markup. | `Static("Click me", id="status")` |
| **`Rule`** | A horizontal or vertical line separator. | `Rule(orientation="horizontal")` |

### 2. Input & Controls

Widgets that accept user input or trigger actions.

| Widget | Description | Key Events / Attributes |
| --- | --- | --- |
| **`Button`** | A clickable button with variants (primary, error, etc.). | `on_button_pressed` <br>

<br> `variant="primary"` |
| **`Input`** | Single-line text entry. Supports placeholders and masking. | `on_input_submitted` <br>

<br> `on_input_changed` |
| **`TextArea`** | Multi-line text editor with syntax highlighting support. | `language="python"` <br>

<br> `text` property |
| **`Checkbox`** | A binary toggle with a label. | `on_checkbox_changed` <br>

<br> `value` (bool) |
| **`Switch`** | A sliding toggle switch (like iOS/Android). | `on_switch_changed` <br>

<br> `value` (bool) |
| **`Select`** | A dropdown menu to choose one option from a list. | `on_select_changed` <br>

<br> `options=[(label, value), ...]` |
| **`RadioButton`** | A selectable option, usually inside a `RadioSet`. | `value` (bool) |
| **`RadioSet`** | Container for RadioButtons; ensures mutually exclusive selection. | `on_radio_set_changed` |

### 3. Data Presentation

Widgets designed to handle structured data, logs, or formatted content.

| Widget | Description | Key Methods |
| --- | --- | --- |
| **`DataTable`** | A scrollable grid/spreadsheet. Supports sorting and row/cell selection. | `add_columns()`, `add_row()` <br>

<br> `on_data_table_row_selected` |
| **`Tree`** | A hierarchical tree view (like a file explorer). | `root.add()`, `root.expand()` <br>

<br> `on_tree_node_selected` |
| **`RichLog`** | A scrollable log window. Can render Rich renderables (colors/tables). | `write(content)` <br>

<br> `clear()` |
| **`Markdown`** | Renders Markdown content with headers, lists, and code blocks. | `load(path)`, `update(str)` |
| **`Digits`** | Displays large, seven-segment style numbers. | `update(str)` |
| **`Sparkline`** | A simple line chart for visualizing a list of numbers. | `data` (list of nums) |

### 4. Lists & Navigation

Widgets for handling lists of items or tabbed navigation.

| Widget | Description | Usage Notes |
| --- | --- | --- |
| **`ListView`** | A vertical list of `ListItem` widgets. Keyboard navigable. | Used with `ListItem`. <br>

<br> `on_list_view_selected` |
| **`OptionList`** | A more performant list for simple text items (replaces ListView for simple data). | `add_option(Option("Text"))` <br>

<br> `on_option_list_option_selected` |
| **`Tabs`** | A row of clickable tabs. | `add_tab("Tab 1")` <br>

<br> `on_tabs_changed` |
| **`TabbedContent`** | A container that automatically swaps content based on the selected tab. | Wrap children in `TabPane`. |

### 5. Status & Feedback

Visual indicators for background processes or loading states.

| Widget | Description |
| --- | --- |
| **`ProgressBar`** | Shows completion percentage. Properties: `total`, `progress`, `advance()`. |
| **`LoadingIndicator`** | An animated spinner/dots to indicate work in progress. |

### 6. Helpful Containers

While `textual.containers` handles layout (Grid, Vertical, Horizontal), these widgets act as specialized containers.

* **`Collapsible`**: A box that can expand or collapse its content when the title is clicked.
* **`ContentSwitcher`**: Holds multiple widgets but only displays one at a time (controlled by `current` ID).

---

### Quick Example: Form Layout

Here is how you might combine **Input**, **Controls**, and **Structure** widgets in a simple form.

```python
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Header, Footer, Label, Input, Button, Checkbox

class CheatsheetApp(App):
    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            Label("User Settings", classes="heading"),
            Input(placeholder="Enter your name"),
            Horizontal(
                Checkbox("Enable Notifications"),
                Checkbox("Dark Mode", value=True),
                classes="checkbox-row"
            ),
            Button("Save Settings", variant="primary", id="save_btn"),
            classes="form_container"
        )
        yield Footer()

if __name__ == "__main__":
    CheatsheetApp().run()

```

--
## Appendix - DataTAble and Tree examples

Here are concrete examples for the `DataTable` and `Tree` widgets. These are two of the most common "data presentation" widgets in Textual.

### 1. DataTable Example

The `DataTable` is used for rows and columns. It supports scrolling, sorting, and row/cell selection.

**Key features used below:**

* **`add_columns`**: Sets up headers.
* **`add_rows`**: Populates data efficiently.
* **`cursor_type`**: Sets selection to "row" mode (instead of single cell).
* **`zebra_stripes`**: Adds alternating colors for readability.

```python
from textual.app import App, ComposeResult
from textual.widgets import DataTable, Header, Footer

class TableApp(App):
    CSS = """
    DataTable {
        height: 1fr;
        border: solid green;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable()
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        
        # 1. Define Structure
        table.add_columns("ID", "Name", "Role", "Status")

        # 2. Add Data
        # Rows are tuples/lists matching the column count
        ROWS = [
            ("101", "Alice Smith", "Engineer", "Active"),
            ("102", "Bob Jones", "Designer", "Remote"),
            ("103", "Charlie Day", "Manager", "On Leave"),
            ("104", "Dana White", "Engineer", "Active"),
        ]
        table.add_rows(ROWS)

        # 3. Configure Appearance
        table.cursor_type = "row"  # Highlight full row
        table.zebra_stripes = True 

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Event fired when user presses Enter on a row."""
        # Get the row key from the event
        row_key = event.row_key
        
        # Retrieve the data for that row using the key
        table = self.query_one(DataTable)
        row_data = table.get_row(row_key)
        
        # Show a notification
        self.notify(f"Selected: {row_data[1]} ({row_data[2]})")

if __name__ == "__main__":
    TableApp().run()

```

---

### 2. Tree Example

The `Tree` widget displays hierarchical data. You start with a `root` node and attach children (branches) or leaves (endpoints).

**Key features used below:**

* **`tree.root`**: The starting node.
* **`add(label)`**: Adds a branch (can have children).
* **`add_leaf(label)`**: Adds a leaf (cannot have children).
* **`expand=True`**: Opens the folder by default.

```python
from textual.app import App, ComposeResult
from textual.widgets import Tree, Header, Footer, Label

class TreeApp(App):
    CSS = """
    Tree {
        width: 30%;
        dock: left;
        border-right: solid $primary;
    }
    #details {
        padding: 2;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        # Initialize tree with a root label
        yield Tree("Project Root")
        yield Label("Select a file...", id="details")
        yield Footer()

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        tree.root.expand() # Open root immediately

        # 1. Add Branch Nodes (Folders)
        # We add these to the 'root' node
        src = tree.root.add("src", expand=True)
        tests = tree.root.add("tests", expand=True)
        docs = tree.root.add("docs")

        # 2. Add Leaf Nodes (Files)
        # We add these to the variable returned by the .add() call above
        src.add_leaf("main.py")
        src.add_leaf("utils.py")
        
        # You can nest deeper
        models = src.add("models", expand=False)
        models.add_leaf("user.py")
        models.add_leaf("product.py")

        tests.add_leaf("test_main.py")
        docs.add_leaf("readme.md")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Event fired when user presses Enter on a node."""
        node = event.node
        details_label = self.query_one("#details", Label)
        
        if node.allow_expand:
            # It is a folder/branch
            details_label.update(f"📂 Folder: {node.label}")
            node.toggle() # Expand/Collapse on select
        else:
            # It is a leaf/file
            details_label.update(f"📄 File: {node.label}")

if __name__ == "__main__":
    TreeApp().run()

```

