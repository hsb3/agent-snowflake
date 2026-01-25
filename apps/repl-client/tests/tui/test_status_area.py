"""Tests for status area widget."""

from __future__ import annotations

import pytest
from textual.app import App, ComposeResult

from repl_client.tui.widgets import StatusArea


class StatusAreaTestApp(App[None]):
    """Test app for status area."""

    def compose(self) -> ComposeResult:
        """Compose with status area."""
        yield StatusArea()


@pytest.fixture
async def app():
    """Create test app."""
    app = StatusAreaTestApp()
    async with app.run_test() as pilot:
        yield pilot


async def test_status_area_initial_state(app):
    """Test status area initial state."""
    status_area = app.app.query_one(StatusArea)
    assert status_area is not None

    # Should have both lines
    user_line = status_area.query_one("#user-status-line")
    client_line = status_area.query_one("#client-info-line")
    assert user_line is not None
    assert client_line is not None


async def test_status_area_set_agent(app):
    """Test setting agent."""
    status_area = app.app.query_one(StatusArea)

    status_area.set_agent("test_agent")

    user_line = status_area.query_one("#user-status-line")
    assert user_line.agent == "test_agent"


async def test_status_area_set_thread(app):
    """Test setting thread."""
    status_area = app.app.query_one(StatusArea)

    status_area.set_thread("thread-123")

    user_line = status_area.query_one("#user-status-line")
    assert user_line.thread == "thread-123"


async def test_status_area_set_tokens(app):
    """Test setting tokens."""
    status_area = app.app.query_one(StatusArea)

    status_area.set_tokens(1234)

    user_line = status_area.query_one("#user-status-line")
    assert user_line.tokens == 1234


async def test_status_area_set_connected(app):
    """Test setting connection status."""
    status_area = app.app.query_one(StatusArea)

    status_area.set_connected(True)

    client_line = status_area.query_one("#client-info-line")
    assert client_line.connected is True

    status_area.set_connected(False)
    assert client_line.connected is False


async def test_status_area_set_connected_with_url(app):
    """Test setting connection status with server URL."""
    status_area = app.app.query_one(StatusArea)

    # Set connected with custom URL
    status_area.set_connected(True, "http://localhost:3000")

    client_line = status_area.query_one("#client-info-line")
    assert client_line.connected is True
    assert client_line.server_url == "http://localhost:3000"

    # Set disconnected with URL
    status_area.set_connected(False, "http://localhost:3000")
    assert client_line.connected is False
    assert client_line.server_url == "http://localhost:3000"


async def test_status_area_connection_display_text(app):
    """Test connection indicator displays correct text with URL."""
    status_area = app.app.query_one(StatusArea)

    # Test connected state
    status_area.set_connected(True, "http://localhost:2024")
    await app.pause()

    connection_display = status_area.query_one("#connection-status")
    # Get the text content from the widget
    display_text = connection_display.render()
    assert "●" in str(display_text)
    assert "http://localhost:2024" in str(display_text)

    # Test disconnected state
    status_area.set_connected(False, "http://localhost:2024")
    await app.pause()

    display_text = connection_display.render()
    assert "○" in str(display_text)
    assert "http://localhost:2024" in str(display_text)


async def test_status_area_set_last_update(app):
    """Test setting last update time."""
    status_area = app.app.query_one(StatusArea)

    status_area.set_last_update("5s ago")

    client_line = status_area.query_one("#client-info-line")
    assert client_line.last_update == "5s ago"


async def test_status_area_set_status_info(app):
    """Test setting status message (info level)."""
    status_area = app.app.query_one(StatusArea)

    status_area.set_status("Ready")

    client_line = status_area.query_one("#client-info-line")
    assert client_line.status_message == "Ready"
    assert client_line.status_level == "info"


async def test_status_area_set_status_error(app):
    """Test setting status message (error level)."""
    status_area = app.app.query_one(StatusArea)

    status_area.set_status("Connection failed", error=True)

    client_line = status_area.query_one("#client-info-line")
    assert client_line.status_message == "Connection failed"
    assert client_line.status_level == "error"


async def test_status_area_set_status_warning(app):
    """Test setting status message (warning level)."""
    status_area = app.app.query_one(StatusArea)

    status_area.set_status("Slow response", warning=True)

    client_line = status_area.query_one("#client-info-line")
    assert client_line.status_message == "Slow response"
    assert client_line.status_level == "warning"


async def test_token_formatting(app):
    """Test token count formatting."""
    status_area = app.app.query_one(StatusArea)

    # Small numbers
    status_area.set_tokens(456)
    await app.pause()
    user_line = status_area.query_one("#user-status-line")
    user_line.query_one("#token-count")
    # Just verify it doesn't crash and updates
    assert user_line.tokens == 456

    # Thousands
    status_area.set_tokens(1234)
    await app.pause()
    assert user_line.tokens == 1234
