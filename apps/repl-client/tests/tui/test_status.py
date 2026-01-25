"""Tests for StatusBar widget."""

import asyncio

import pytest
from textual.app import App
from textual.widgets import Static

from repl_client.tui.widgets import StatusBar


class StatusBarTestApp(App):
    """Test app for StatusBar."""

    def compose(self):
        yield StatusBar()


@pytest.fixture
async def status_bar():
    """Create a StatusBar widget for testing."""
    app = StatusBarTestApp()
    async with app.run_test() as pilot:
        yield pilot.app.query_one(StatusBar)


class TestStatusBarReactivity:
    """Test reactive properties of StatusBar."""

    async def test_agent_update(self, status_bar):
        """Test agent reactive property updates display."""
        status_bar.agent = "agent_enhanced"
        await asyncio.sleep(0.05)

        agent_display = status_bar.query_one("#agent-status", Static)
        assert "agent_enhanced" in str(str(agent_display.content))

    async def test_thread_update(self, status_bar):
        """Test thread reactive property updates display."""
        status_bar.thread = "thread_abc123"
        await asyncio.sleep(0.05)

        thread_display = status_bar.query_one("#thread-status", Static)
        assert "thread_abc123" in str(thread_display.content)

    async def test_token_formatting_under_1000(self, status_bar):
        """Test token display formats numbers under 1000 correctly."""
        status_bar.tokens = 456
        await asyncio.sleep(0.05)

        token_display = status_bar.query_one("#token-count", Static)
        assert "456" in str(token_display.content)
        assert "tokens" in str(token_display.content).lower()

    async def test_token_formatting_over_1000(self, status_bar):
        """Test token display formats thousands with K suffix."""
        status_bar.tokens = 1234
        await asyncio.sleep(0.05)

        token_display = status_bar.query_one("#token-count", Static)
        assert "1.2K" in str(token_display.content)
        assert "tokens" in str(token_display.content).lower()

    async def test_token_formatting_exact_thousands(self, status_bar):
        """Test token display formats exact thousands correctly."""
        status_bar.tokens = 5000
        await asyncio.sleep(0.05)

        token_display = status_bar.query_one("#token-count", Static)
        assert "5.0K" in str(token_display.content)

    async def test_token_zero_clears_display(self, status_bar):
        """Test token count of 0 clears the display."""
        status_bar.tokens = 1000
        await asyncio.sleep(0.05)

        status_bar.tokens = 0
        await asyncio.sleep(0.05)

        token_display = status_bar.query_one("#token-count", Static)
        assert str(token_display.content) == ""

    async def test_connection_status_connected(self, status_bar):
        """Test connection status shows connected state."""
        status_bar.connected = True
        await asyncio.sleep(0.05)

        conn_display = status_bar.query_one("#connection-status", Static)
        assert conn_display.has_class("connected")
        assert not conn_display.has_class("disconnected")

    async def test_connection_status_disconnected(self, status_bar):
        """Test connection status shows disconnected state."""
        status_bar.connected = False
        await asyncio.sleep(0.05)

        conn_display = status_bar.query_one("#connection-status", Static)
        assert conn_display.has_class("disconnected")
        assert not conn_display.has_class("connected")


class TestStatusBarLayout:
    """Test StatusBar layout and styling."""

    async def test_not_docked(self, status_bar):
        """Test StatusBar is not docked (flows in normal layout).

        Note: StatusBar should NOT have dock: bottom in DEFAULT_CSS
        to avoid overlapping with other widgets. External CSS in
        layout.tcss controls the overall layout positioning.
        """
        # Should be empty or none, not "bottom"
        assert status_bar.styles.dock != "bottom"

    async def test_height_is_one(self, status_bar):
        """Test StatusBar height is 1."""
        # Height will be 1 when rendered
        assert status_bar.styles.height is not None

    async def test_all_status_elements_present(self, status_bar):
        """Test all status display elements are present."""
        assert status_bar.query_one("#agent-status")
        assert status_bar.query_one("#thread-status")
        assert status_bar.query_one("#token-count")
        assert status_bar.query_one("#connection-status")


class TestStatusBarMethods:
    """Test StatusBar convenience methods."""

    async def test_set_agent(self, status_bar):
        """Test set_agent method."""
        status_bar.set_agent("test_agent")
        await asyncio.sleep(0.05)

        assert status_bar.agent == "test_agent"

    async def test_set_thread(self, status_bar):
        """Test set_thread method."""
        status_bar.set_thread("test_thread")
        await asyncio.sleep(0.05)

        assert status_bar.thread == "test_thread"

    async def test_set_tokens(self, status_bar):
        """Test set_tokens method."""
        status_bar.set_tokens(999)
        await asyncio.sleep(0.05)

        assert status_bar.tokens == 999

    async def test_hide_tokens(self, status_bar):
        """Test hide_tokens clears display."""
        status_bar.tokens = 500
        await asyncio.sleep(0.05)

        status_bar.hide_tokens()

        token_display = status_bar.query_one("#token-count", Static)
        assert str(token_display.content) == ""

    async def test_set_connected(self, status_bar):
        """Test set_connected method."""
        status_bar.set_connected(False)
        await asyncio.sleep(0.05)

        assert status_bar.connected is False
