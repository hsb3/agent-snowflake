"""Tests for AgentDetailItem, AgentDetailList, and AgentSelector widgets."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Label

from repl_client.tui.widgets.agent_detail import (
    AgentDetailItem,
    AgentDetailList,
    AgentSelector,
)

# Sample test data
SAMPLE_AGENTS = [
    {
        "assistant_id": "fe096781-5601-53d2-b2f6-0d3403f7e9ca",
        "graph_id": "agent",
        "name": "agent",
        "created_at": "2026-01-25T12:00:00Z",
    },
    {
        "assistant_id": "abc12345-6789-0def-ghij-klmnopqrstuv",
        "graph_id": "agent_enhanced",
        "name": "agent_enhanced",
        "created_at": "2026-01-24T10:30:00Z",
    },
]


# ============================================================================
# Test Apps
# ============================================================================


class AgentDetailItemTestApp(App[None]):
    """Test app for AgentDetailItem widget."""

    def __init__(self, agent: dict, is_current: bool = False) -> None:
        super().__init__()
        self._agent = agent
        self._is_current = is_current

    def compose(self) -> ComposeResult:
        yield AgentDetailItem(self._agent, is_current=self._is_current)


class AgentDetailListTestApp(App[None]):
    """Test app for AgentDetailList widget."""

    def __init__(self, agents: list[dict] | None = None, current_id: str = "") -> None:
        super().__init__()
        self._agents = agents
        self._current_id = current_id

    def compose(self) -> ComposeResult:
        yield AgentDetailList(self._agents, self._current_id)


class AgentSelectorTestApp(App[None]):
    """Test app for AgentSelector widget."""

    def __init__(self, agents: list[dict] | None = None, current_id: str = "") -> None:
        super().__init__()
        self._agents = agents
        self._current_id = current_id
        self.selected_agent: dict | None = None

    def compose(self) -> ComposeResult:
        yield AgentSelector(self._agents, self._current_id)

    def on_agent_selector_agent_selected(self, message: AgentSelector.AgentSelected) -> None:
        """Handle agent selection message."""
        self.selected_agent = message.agent


def get_label_text(label: Label) -> str:
    """Helper to extract text from a Label widget."""
    rendered = label.render()
    return str(rendered)


# ============================================================================
# AgentDetailItem Tests
# ============================================================================


class TestAgentDetailItem:
    """Tests for AgentDetailItem widget."""

    async def test_agent_detail_item_renders(self):
        """Test that AgentDetailItem renders correctly with agent data."""
        agent = SAMPLE_AGENTS[0]
        app = AgentDetailItemTestApp(agent, is_current=False)

        async with app.run_test() as pilot:
            await pilot.pause()
            item = pilot.app.query_one(AgentDetailItem)

            # Check that item exists
            assert item is not None

            # Check agent name label
            name_label = item.query_one(".agent-name", Label)
            name_text = get_label_text(name_label)
            assert agent["graph_id"] in name_text

            # Check assistant_id label
            id_label = item.query_one(".agent-id", Label)
            id_text = get_label_text(id_label)
            assert agent["assistant_id"] in id_text

            # Check created date label
            meta_label = item.query_one(".agent-meta", Label)
            meta_text = get_label_text(meta_label)
            assert "2026-01-25" in meta_text

    async def test_agent_detail_item_current_marker(self):
        """Test the checkmark appears when is_current=True."""
        agent = SAMPLE_AGENTS[0]
        app = AgentDetailItemTestApp(agent, is_current=True)

        async with app.run_test() as pilot:
            await pilot.pause()
            item = pilot.app.query_one(AgentDetailItem)

            # Check that checkmark is in name
            name_label = item.query_one(".agent-name", Label)
            name_text = get_label_text(name_label)
            assert agent["graph_id"] in name_text
            assert "\u2713" in name_text  # Unicode checkmark

    async def test_agent_detail_item_no_marker_when_not_current(self):
        """Test that no checkmark appears when is_current=False."""
        agent = SAMPLE_AGENTS[0]
        app = AgentDetailItemTestApp(agent, is_current=False)

        async with app.run_test() as pilot:
            await pilot.pause()
            item = pilot.app.query_one(AgentDetailItem)

            # Check that checkmark is NOT in name
            name_label = item.query_one(".agent-name", Label)
            name_text = get_label_text(name_label)
            assert "\u2713" not in name_text

    async def test_agent_detail_item_current_class(self):
        """Test 'current' class is added when is_current=True."""
        agent = SAMPLE_AGENTS[0]
        app = AgentDetailItemTestApp(agent, is_current=True)

        async with app.run_test() as pilot:
            await pilot.pause()
            item = pilot.app.query_one(AgentDetailItem)
            assert item.has_class("current")

    async def test_agent_detail_item_no_current_class_when_not_current(self):
        """Test 'current' class is NOT added when is_current=False."""
        agent = SAMPLE_AGENTS[0]
        app = AgentDetailItemTestApp(agent, is_current=False)

        async with app.run_test() as pilot:
            await pilot.pause()
            item = pilot.app.query_one(AgentDetailItem)
            assert not item.has_class("current")

    async def test_agent_detail_item_handles_missing_fields(self):
        """Test widget handles missing agent fields gracefully."""
        minimal_agent = {"assistant_id": "test-id"}
        app = AgentDetailItemTestApp(minimal_agent, is_current=False)

        async with app.run_test() as pilot:
            await pilot.pause()
            item = pilot.app.query_one(AgentDetailItem)

            # Should render without errors
            assert item is not None

            # Name should be "unknown"
            name_label = item.query_one(".agent-name", Label)
            name_text = get_label_text(name_label)
            assert "unknown" in name_text

            # Meta should show "unknown" for date
            meta_label = item.query_one(".agent-meta", Label)
            meta_text = get_label_text(meta_label)
            assert "unknown" in meta_text


# ============================================================================
# AgentDetailList Tests
# ============================================================================


class TestAgentDetailList:
    """Tests for AgentDetailList widget."""

    async def test_agent_detail_list_populate(self):
        """Test AgentDetailList.populate() creates correct number of items."""
        app = AgentDetailListTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            agent_list = pilot.app.query_one(AgentDetailList)

            items = agent_list.query(AgentDetailItem)
            assert len(list(items)) == len(SAMPLE_AGENTS)

    async def test_agent_detail_list_empty_message(self):
        """Test empty list shows 'No agents available' message when populate() is called."""
        app = AgentDetailListTestApp(agents=None, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            agent_list = pilot.app.query_one(AgentDetailList)

            # Explicitly call populate with empty list
            # (on_mount doesn't call populate for empty lists)
            agent_list.populate([], "")
            await pilot.pause()

            # Should have label with "No agents available"
            labels = agent_list.query(Label)
            label_texts = [get_label_text(label) for label in labels]
            assert any("No agents available" in text for text in label_texts)

            # Should not have any AgentDetailItem
            items = agent_list.query(AgentDetailItem)
            assert len(list(items)) == 0

    async def test_agent_detail_list_marks_current(self):
        """Test that the current agent is marked correctly."""
        current_id = SAMPLE_AGENTS[0]["assistant_id"]
        app = AgentDetailListTestApp(SAMPLE_AGENTS, current_id=current_id)

        async with app.run_test() as pilot:
            await pilot.pause()
            agent_list = pilot.app.query_one(AgentDetailList)

            items = list(agent_list.query(AgentDetailItem))
            current_items = [item for item in items if item.has_class("current")]

            assert len(current_items) == 1
            assert current_items[0].agent["assistant_id"] == current_id

    async def test_agent_detail_list_repopulate(self):
        """Test repopulating list clears previous items."""
        app = AgentDetailListTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            agent_list = pilot.app.query_one(AgentDetailList)

            # Initial count
            items = list(agent_list.query(AgentDetailItem))
            assert len(items) == 2

            # Repopulate with different data
            new_agents = [SAMPLE_AGENTS[0]]  # Only one agent
            agent_list.populate(new_agents, current_id="")
            await pilot.pause()

            items = list(agent_list.query(AgentDetailItem))
            assert len(items) == 1


# ============================================================================
# AgentSelector Tests
# ============================================================================


class TestAgentSelector:
    """Tests for AgentSelector widget with keyboard navigation."""

    async def test_agent_selector_keyboard_navigation_down(self):
        """Test down arrow navigation moves focus."""
        app = AgentSelectorTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            selector = pilot.app.query_one(AgentSelector)

            # Focus the selector
            selector.focus()
            await pilot.pause()

            # Initial focus should be on first item (index 0)
            # Note: focus class is applied via _update_focus() which may need a key event
            items = list(selector.query(AgentDetailItem))

            # Press down arrow - this will set focus on second item
            await pilot.press("down")
            await pilot.pause()

            # Focus should now be on second item
            items = list(selector.query(AgentDetailItem))
            assert not items[0].has_class("focused")
            assert items[1].has_class("focused")

    async def test_agent_selector_keyboard_navigation_up(self):
        """Test up arrow navigation moves focus."""
        app = AgentSelectorTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            selector = pilot.app.query_one(AgentSelector)

            # Focus the selector
            selector.focus()
            await pilot.pause()

            # Move down first
            await pilot.press("down")
            await pilot.pause()

            items = list(selector.query(AgentDetailItem))
            assert items[1].has_class("focused")

            # Now move back up
            await pilot.press("up")
            await pilot.pause()

            items = list(selector.query(AgentDetailItem))
            assert items[0].has_class("focused")
            assert not items[1].has_class("focused")

    async def test_agent_selector_navigation_bounds_top(self):
        """Test navigation doesn't go above first item."""
        app = AgentSelectorTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            selector = pilot.app.query_one(AgentSelector)

            selector.focus()
            await pilot.pause()

            # Navigate down first to apply focus class
            await pilot.press("down")
            await pilot.pause()

            # Then back up
            await pilot.press("up")
            await pilot.pause()

            # Try to go up when at top
            await pilot.press("up")
            await pilot.pause()

            # Should still be at index 0
            items = list(selector.query(AgentDetailItem))
            assert items[0].has_class("focused")

    async def test_agent_selector_navigation_bounds_bottom(self):
        """Test navigation doesn't go below last item."""
        app = AgentSelectorTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            selector = pilot.app.query_one(AgentSelector)

            selector.focus()
            await pilot.pause()

            # Go to last item
            await pilot.press("down")
            await pilot.pause()

            # Try to go further down
            await pilot.press("down")
            await pilot.pause()

            # Should still be at last index (1)
            items = list(selector.query(AgentDetailItem))
            assert not items[0].has_class("focused")
            assert items[1].has_class("focused")

    async def test_agent_selector_selection_message(self):
        """Test that pressing Enter posts AgentSelected message."""
        app = AgentSelectorTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            selector = pilot.app.query_one(AgentSelector)

            selector.focus()
            await pilot.pause()

            # Press enter to select first item
            await pilot.press("enter")
            await pilot.pause()

            # Check that app received the selection
            assert app.selected_agent is not None
            assert app.selected_agent["assistant_id"] == SAMPLE_AGENTS[0]["assistant_id"]

    async def test_agent_selector_selection_message_after_navigation(self):
        """Test selecting an item after navigating down."""
        app = AgentSelectorTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            selector = pilot.app.query_one(AgentSelector)

            selector.focus()
            await pilot.pause()

            # Navigate to second item
            await pilot.press("down")
            await pilot.pause()

            # Select it
            await pilot.press("enter")
            await pilot.pause()

            # Should have selected second agent
            assert app.selected_agent is not None
            assert app.selected_agent["assistant_id"] == SAMPLE_AGENTS[1]["assistant_id"]

    async def test_agent_selector_focus_class_after_navigation(self):
        """Test that 'focused' class is applied after navigation."""
        app = AgentSelectorTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            selector = pilot.app.query_one(AgentSelector)

            selector.focus()
            await pilot.pause()

            # Navigate to trigger focus class update
            await pilot.press("down")
            await pilot.pause()

            items = list(selector.query(AgentDetailItem))

            # Second item should have focused class after down
            assert items[1].has_class("focused")

            # First item should not
            assert not items[0].has_class("focused")

    async def test_agent_selector_empty_list_navigation(self):
        """Test navigation with empty list doesn't crash."""
        app = AgentSelectorTestApp(agents=[], current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            selector = pilot.app.query_one(AgentSelector)

            selector.focus()
            await pilot.pause()

            # Pressing keys on empty list should not crash
            await pilot.press("down")
            await pilot.press("up")
            await pilot.press("enter")
            await pilot.pause()

            # No selection should have been made
            assert app.selected_agent is None

    async def test_agent_selector_populate_updates_internal_state(self):
        """Test that populate() updates internal state correctly."""
        app = AgentSelectorTestApp(SAMPLE_AGENTS, current_id="")

        async with app.run_test() as pilot:
            await pilot.pause()
            selector = pilot.app.query_one(AgentSelector)

            # Verify initial state
            assert selector._agents == SAMPLE_AGENTS
            assert selector._focus_index == 0

            # Navigate to second item
            selector.focus()
            await pilot.press("down")
            await pilot.pause()

            assert selector._focus_index == 1

            # Repopulate
            new_agents = [SAMPLE_AGENTS[0]]
            selector.populate(new_agents, "")
            await pilot.pause()

            # Focus index should be reset to 0
            assert selector._focus_index == 0
            assert selector._agents == new_agents


class TestAgentSelectedMessage:
    """Tests for AgentSelected message properties."""

    async def test_agent_selected_message_agent_property(self):
        """Test AgentSelected.agent property returns full agent dict."""
        agent = SAMPLE_AGENTS[0]
        message = AgentSelector.AgentSelected(agent)

        assert message.agent == agent
        assert message.agent["graph_id"] == "agent"

    async def test_agent_selected_message_assistant_id_property(self):
        """Test AgentSelected.assistant_id property."""
        agent = SAMPLE_AGENTS[0]
        message = AgentSelector.AgentSelected(agent)

        assert message.assistant_id == agent["assistant_id"]

    async def test_agent_selected_message_missing_id(self):
        """Test AgentSelected.assistant_id handles missing ID."""
        agent = {"graph_id": "test"}
        message = AgentSelector.AgentSelected(agent)

        assert message.assistant_id == ""
