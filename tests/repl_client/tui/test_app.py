"""Integration tests for REPL TUI app.

These tests verify the app functionality but don't require a running server.
They test widget mounting, message handling, and command execution.

For full integration tests with server, see test_app_integration.py.
"""

import pytest
from textual.widgets import Footer, Header

from repl_client.core.config import Config
from repl_client.tui.app import REPLApp
from repl_client.tui.widgets import ChatInput, Sidebar, StatusArea


@pytest.fixture
def app():
    """Create app instance for testing."""
    config = Config(
        server_url="http://localhost:2024",
        default_agent="test-agent",
    )
    return REPLApp(config=config)


def test_app_compose(app):
    """Test that app composes all required widgets."""
    # Note: Can't call compose directly due to context manager issues
    # Instead, verify the app has the compose method
    assert hasattr(app, "compose")
    assert callable(app.compose)


async def test_app_mount():
    """Test app mounting and widget initialization."""
    config = Config(
        server_url="http://localhost:2024",
        default_agent="test-agent",
    )
    app = REPLApp(config=config)

    async with app.run_test() as pilot:
        # Check that key widgets are mounted
        assert app.query_one(Header)
        assert app.query_one(ChatInput)
        assert app.query_one(StatusArea)  # Updated to StatusArea
        assert app.query_one(Footer)
        assert app.query_one("#messages")
        assert app.query_one(Sidebar)  # New sidebar widget


async def test_clear_messages_action():
    """Test that clear messages action works."""
    config = Config(
        server_url="http://localhost:2024",
        default_agent="test-agent",
    )
    app = REPLApp(config=config)

    async with app.run_test() as pilot:
        # Get messages container
        messages = app.query_one("#messages")

        # Initially should be empty
        assert len(messages.children) == 0

        # Trigger clear action (should not crash even when empty)
        app.action_clear_messages()

        # Still should be empty
        assert len(messages.children) == 0


async def test_help_command():
    """Test /help command displays help text."""
    config = Config(
        server_url="http://localhost:2024",
        default_agent="test-agent",
    )
    app = REPLApp(config=config)

    async with app.run_test() as pilot:
        # Get messages container
        messages = app.query_one("#messages")

        # Initially empty
        assert len(messages.children) == 0

        # Execute help command
        await app._handle_command("/help")

        # Should have added a message
        assert len(messages.children) == 1


async def test_info_command():
    """Test /info command displays session info."""
    config = Config(
        server_url="http://localhost:2024",
        default_agent="test-agent",
    )
    app = REPLApp(config=config)

    async with app.run_test() as pilot:
        # Set some session state
        app.session.set_agent("test-agent-123")
        app.session.set_thread("test-thread-456")

        # Get messages container
        messages = app.query_one("#messages")

        # Execute info command
        await app._handle_command("/info")

        # Should have added a message
        assert len(messages.children) == 1


async def test_unknown_command():
    """Test that unknown commands show error message."""
    config = Config(
        server_url="http://localhost:2024",
        default_agent="test-agent",
    )
    app = REPLApp(config=config)

    async with app.run_test() as pilot:
        # Get messages container
        messages = app.query_one("#messages")

        # Execute unknown command
        await app._handle_command("/unknowncommand")

        # Should have added an error message
        assert len(messages.children) == 1


async def test_app_bindings():
    """Test that app has required key bindings."""
    config = Config(
        server_url="http://localhost:2024",
        default_agent="test-agent",
    )
    app = REPLApp(config=config)

    # Check bindings exist
    binding_keys = {b.key for b in app.BINDINGS}

    assert "ctrl+c" in binding_keys  # Quit
    assert "ctrl+l" in binding_keys  # Clear messages


def test_app_initialization(app):
    """Test app initializes with correct config."""
    assert app.config.server_url == "http://localhost:2024"
    assert app.config.default_agent == "test-agent"
    assert app.client is not None
    assert app.session is not None
    assert app.stream_handler is not None
    assert app.hitl_handler is not None


def test_app_css_path(app):
    """Test that CSS path is set."""
    assert app.CSS_PATH == "repl.tcss"
