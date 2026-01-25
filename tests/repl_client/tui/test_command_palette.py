"""Tests for command palette widget."""

from unittest.mock import AsyncMock

import pytest
from textual.widgets import Input, OptionList

from repl_client.tui.widgets import Command, CommandPalette


@pytest.fixture
def sample_commands():
    """Create sample commands for testing."""
    return [
        Command(
            id="agent-switch",
            label="Switch Agent",
            category="Agents",
            description="Change current agent",
            action=AsyncMock(),
        ),
        Command(
            id="thread-new",
            label="New Thread",
            category="Threads",
            description="Create new thread",
            action=AsyncMock(),
        ),
        Command(
            id="nav-sidebar",
            label="Toggle Sidebar",
            category="Navigation",
            description="Show/hide sidebar",
            action=AsyncMock(),
        ),
        Command(
            id="cmd-help",
            label="/help",
            category="Commands",
            description="Show help",
            action=AsyncMock(),
        ),
    ]


@pytest.mark.asyncio
async def test_command_palette_mount(sample_commands):
    """Test command palette can mount."""
    palette = CommandPalette(sample_commands)

    # Check initialization
    assert palette.commands == sample_commands
    assert palette.filtered_commands == sample_commands


@pytest.mark.asyncio
async def test_command_palette_renders_all_commands(sample_commands):
    """Test command palette displays all commands grouped by category."""
    from textual.app import App

    class TestApp(App):
        def on_mount(self):
            self.push_screen(CommandPalette(sample_commands))

    async with TestApp().run_test() as pilot:
        # Wait for screen to mount
        await pilot.pause()

        # Check that option list exists
        option_list = pilot.app.screen.query_one("#command-list", OptionList)
        assert option_list is not None

        # Check that we have options (commands + categories + separators)
        assert len(option_list._options) > len(sample_commands)


@pytest.mark.asyncio
async def test_command_palette_search_filter(sample_commands):
    """Test search filtering."""
    from textual.app import App

    class TestApp(App):
        def on_mount(self):
            self.push_screen(CommandPalette(sample_commands))

    async with TestApp().run_test() as pilot:
        await pilot.pause()

        palette = pilot.app.screen
        search_input = palette.query_one("#search-input", Input)

        # Type search query
        search_input.value = "thread"
        await pilot.pause()

        # Check filtered commands
        assert len(palette.filtered_commands) == 1
        assert palette.filtered_commands[0].id == "thread-new"


@pytest.mark.asyncio
async def test_command_palette_fuzzy_search(sample_commands):
    """Test fuzzy search matches both label and description."""
    from textual.app import App

    class TestApp(App):
        def on_mount(self):
            self.push_screen(CommandPalette(sample_commands))

    async with TestApp().run_test() as pilot:
        await pilot.pause()

        palette = pilot.app.screen
        search_input = palette.query_one("#search-input", Input)

        # Search by description word
        search_input.value = "sidebar"
        await pilot.pause()

        # Should match "Toggle Sidebar" in description
        assert len(palette.filtered_commands) == 1
        assert palette.filtered_commands[0].id == "nav-sidebar"


@pytest.mark.asyncio
async def test_command_palette_escape_dismisses(sample_commands):
    """Test pressing escape dismisses palette."""
    from textual.app import App

    class TestApp(App):
        def on_mount(self):
            self.push_screen(CommandPalette(sample_commands))

    async with TestApp().run_test() as pilot:
        await pilot.pause()

        # Press escape
        await pilot.press("escape")
        await pilot.pause()

        # Screen should be dismissed (back to main app)
        assert not isinstance(pilot.app.screen, CommandPalette)


@pytest.mark.asyncio
async def test_command_palette_empty_search(sample_commands):
    """Test empty search query shows all commands."""
    from textual.app import App

    class TestApp(App):
        def on_mount(self):
            self.push_screen(CommandPalette(sample_commands))

    async with TestApp().run_test() as pilot:
        await pilot.pause()

        palette = pilot.app.screen
        search_input = palette.query_one("#search-input", Input)

        # Type then clear
        search_input.value = "test"
        await pilot.pause()
        search_input.value = ""
        await pilot.pause()

        # Should show all commands again
        assert palette.filtered_commands == sample_commands


@pytest.mark.asyncio
async def test_command_palette_no_results(sample_commands):
    """Test search with no matching commands."""
    from textual.app import App

    class TestApp(App):
        def on_mount(self):
            self.push_screen(CommandPalette(sample_commands))

    async with TestApp().run_test() as pilot:
        await pilot.pause()

        palette = pilot.app.screen
        search_input = palette.query_one("#search-input", Input)

        # Search for something that doesn't exist
        search_input.value = "zzz-nonexistent"
        await pilot.pause()

        # Should have no filtered commands
        assert len(palette.filtered_commands) == 0

        # Option list should show "No commands found"
        option_list = palette.query_one("#command-list", OptionList)
        assert len(option_list._options) == 1
        # Check the prompt string (it could be a RenderableType)
        option_prompt = option_list._options[0].prompt
        assert "No commands found" in str(option_prompt)


@pytest.mark.asyncio
async def test_command_palette_category_grouping(sample_commands):
    """Test commands are properly grouped by category."""
    from textual.app import App

    class TestApp(App):
        def on_mount(self):
            self.push_screen(CommandPalette(sample_commands))

    async with TestApp().run_test() as pilot:
        await pilot.pause()

        palette = pilot.app.screen
        option_list = palette.query_one("#command-list", OptionList)

        # Check that category headers exist
        option_ids = [opt.id for opt in option_list._options if opt.id]
        category_ids = [opt_id for opt_id in option_ids if opt_id.startswith("category-")]

        # Should have categories for: Agents, Threads, Navigation, Commands
        assert len(category_ids) == 4
        assert "category-Agents" in category_ids
        assert "category-Threads" in category_ids
        assert "category-Navigation" in category_ids
        assert "category-Commands" in category_ids
