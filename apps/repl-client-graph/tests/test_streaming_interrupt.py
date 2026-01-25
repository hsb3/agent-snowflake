"""Test interrupt detection in process_stream_node."""

import pytest
from repl_client_graph.graph.nodes.streaming import process_stream_node
from repl_client_graph.graph.state import REPLState


def test_process_stream_detects_interrupt():
    """Test that process_stream_node detects __interrupt__ in updates events."""
    # Arrange: Create state with chunks containing an interrupt
    state: REPLState = {
        "stream_chunks": [
            (
                "updates",
                {
                    "__interrupt__": [
                        {
                            "value": {
                                "tool": "execute_sql",
                                "args": {"query": "SELECT * FROM users"},
                            },
                            "when": "during",
                        }
                    ]
                },
            )
        ],
    }

    # Act: Process the stream
    result = process_stream_node(state)

    # Assert: Check that interrupt was detected
    assert result["pending_interrupt"] is not None
    assert result["pending_interrupt"]["id"].startswith("interrupt_execute_sql_")
    assert result["pending_interrupt"]["value"]["tool"] == "execute_sql"
    assert result["pending_interrupt"]["value"]["args"]["query"] == "SELECT * FROM users"


def test_process_stream_no_interrupt():
    """Test that process_stream_node works normally without interrupts."""
    # Arrange: Create state with regular updates (no interrupt)
    state: REPLState = {
        "stream_chunks": [
            (
                "updates",
                {
                    "some_state_key": "some_value",
                },
            )
        ],
    }

    # Act: Process the stream
    result = process_stream_node(state)

    # Assert: Check that no interrupt was detected
    assert result["pending_interrupt"] is None


def test_process_stream_interrupt_stops_processing():
    """Test that interrupt detection stops processing remaining chunks."""
    # Arrange: Create state with interrupt followed by more chunks
    state: REPLState = {
        "stream_chunks": [
            (
                "updates",
                {
                    "before_interrupt": "value1",
                },
            ),
            (
                "updates",
                {
                    "__interrupt__": [
                        {
                            "value": {
                                "tool": "dangerous_operation",
                                "args": {},
                            },
                            "when": "during",
                        }
                    ],
                    "this_should_not_be_rendered": "value2",
                },
            ),
            (
                "updates",
                {
                    "after_interrupt": "value3",
                },
            ),
        ],
    }

    # Act: Process the stream
    result = process_stream_node(state)

    # Assert: Check that interrupt was detected
    assert result["pending_interrupt"] is not None
    assert result["pending_interrupt"]["value"]["tool"] == "dangerous_operation"

    # Check that state updates before interrupt were added to render queue
    state_updates = [item for item in result["render_queue"] if item["type"] == "state_update"]
    assert len(state_updates) == 1  # Only the first update before interrupt

    # Check that updates after interrupt were not processed
    assert not any(
        item.get("content", {}).get("after_interrupt") for item in result["render_queue"]
    )


def test_process_stream_empty_interrupt_list():
    """Test that empty __interrupt__ list doesn't trigger interrupt handling."""
    # Arrange: Create state with empty interrupt list
    state: REPLState = {
        "stream_chunks": [
            (
                "updates",
                {
                    "__interrupt__": [],
                },
            )
        ],
    }

    # Act: Process the stream
    result = process_stream_node(state)

    # Assert: Check that no interrupt was detected
    assert result["pending_interrupt"] is None


def test_process_stream_malformed_interrupt():
    """Test that malformed interrupt data is handled gracefully."""
    # Arrange: Create state with malformed interrupt (not a list)
    state: REPLState = {
        "stream_chunks": [
            (
                "updates",
                {
                    "__interrupt__": "not a list",
                },
            )
        ],
    }

    # Act: Process the stream
    result = process_stream_node(state)

    # Assert: Check that no interrupt was detected (graceful handling)
    assert result["pending_interrupt"] is None
