"""Pytest configuration for repl_client_graph tests."""

import pytest


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Run integration tests (require running LangGraph server)",
    )


@pytest.fixture
def server_url():
    """Default server URL for testing."""
    return "http://localhost:2024"
