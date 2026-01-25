"""Command palette widget for master command navigation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import Input, Label, OptionList
from textual.widgets.option_list import Option

if TYPE_CHECKING:
    from textual.app import ComposeResult


@dataclass
class Command:
    """Represents a command in the palette."""

    id: str
    label: str
    category: str
    description: str
    action: Callable


class CommandPalette(ModalScreen[Command | None]):
    """Modal command palette with hierarchical navigation.

    Features:
    - Searchable command list with fuzzy filtering
    - Hierarchical categories (Agents, Threads, Navigation, Commands)
    - Keyboard navigation (up/down, Enter, Esc)
    - Visual grouping with separators
    """

    DEFAULT_CSS = """
    CommandPalette {
        align: center middle;
    }

    CommandPalette > Container {
        width: 80;
        height: auto;
        max-height: 30;
        background: $panel;
        border: thick $primary;
        padding: 1;
    }

    CommandPalette Input {
        width: 100%;
        margin-bottom: 1;
        border: solid $primary;
    }

    CommandPalette Label {
        width: 100%;
        margin-bottom: 1;
        text-align: center;
        color: $text-muted;
        text-style: italic;
    }

    CommandPalette OptionList {
        width: 100%;
        height: auto;
        max-height: 20;
        border: none;
        background: $surface;
    }

    CommandPalette OptionList > .option-list--option {
        padding: 0 1;
    }

    CommandPalette OptionList > .option-list--option-highlighted {
        background: $primary;
    }

    CommandPalette .command-category {
        color: $primary;
        text-style: bold;
        padding: 1 0 0 0;
    }

    CommandPalette .command-label {
        text-style: bold;
    }

    CommandPalette .command-description {
        color: $text-muted;
        text-style: italic;
    }
    """

    def __init__(self, commands: list[Command]):
        """Initialize command palette.

        Args:
            commands: List of Command objects to display
        """
        super().__init__()
        self.commands = commands
        self.filtered_commands = commands.copy()

    def compose(self) -> ComposeResult:
        """Compose the palette layout."""
        with Container():
            yield Label("Command Palette (Esc to close)")
            yield Input(placeholder="Search commands...", id="search-input")
            yield OptionList(id="command-list")

    def on_mount(self) -> None:
        """Initialize palette on mount."""
        self._update_command_list()
        search_input = self.query_one("#search-input", Input)
        search_input.focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter commands as user types.

        Args:
            event: Input change event
        """
        if event.input.id != "search-input":
            return

        query = event.value.lower().strip()

        if not query:
            self.filtered_commands = self.commands.copy()
        else:
            # Fuzzy filter: match query substring in label or description
            self.filtered_commands = [
                cmd
                for cmd in self.commands
                if query in cmd.label.lower() or query in cmd.description.lower()
            ]

        self._update_command_list()

    def _update_command_list(self) -> None:
        """Update option list with filtered commands grouped by category."""
        option_list = self.query_one("#command-list", OptionList)
        option_list.clear_options()

        if not self.filtered_commands:
            option_list.add_option(Option("No commands found", disabled=True))
            return

        # Group commands by category
        categories: dict[str, list[Command]] = {}
        for cmd in self.filtered_commands:
            if cmd.category not in categories:
                categories[cmd.category] = []
            categories[cmd.category].append(cmd)

        # Add commands grouped by category
        category_order = ["Agents", "Threads", "Navigation", "Commands", "System"]

        first_category = True
        for category in category_order:
            if category not in categories:
                continue

            # Add separator between categories (except first)
            if not first_category:
                # Use disabled option as separator since Separator is not available
                option_list.add_option(Option("---", id=f"sep-{category}", disabled=True))
            first_category = False

            # Add category header
            option_list.add_option(
                Option(f"[{category}]", id=f"category-{category}", disabled=True)
            )

            # Add commands in category
            for cmd in categories[category]:
                label = f"  {cmd.label}"
                if cmd.description:
                    label += f" - {cmd.description}"
                option_list.add_option(Option(label, id=cmd.id))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle command selection.

        Args:
            event: Option selected event
        """
        if event.option.disabled:
            return

        # Find selected command
        selected_cmd = None
        for cmd in self.filtered_commands:
            if cmd.id == event.option.id:
                selected_cmd = cmd
                break

        self.dismiss(selected_cmd)

    def on_key(self, event) -> None:
        """Handle keyboard shortcuts.

        Args:
            event: Key event
        """
        if event.key == "escape":
            self.dismiss(None)
        elif event.key == "down":
            # Focus option list if on search input
            if self.focused == self.query_one("#search-input"):
                self.query_one("#command-list", OptionList).focus()
                event.prevent_default()
        elif event.key == "up":
            # Focus search input if at top of option list
            option_list = self.query_one("#command-list", OptionList)
            if self.focused == option_list and option_list.highlighted == 0:
                self.query_one("#search-input", Input).focus()
                event.prevent_default()
