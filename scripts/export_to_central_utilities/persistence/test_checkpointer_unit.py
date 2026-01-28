"""Unit tests for SQLite checkpointer functionality."""

import os
import tempfile
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

from persistence import create_sqlite_checkpointer


def test_checkpointer_creates_database():
    """Test that checkpointer creates the SQLite database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            checkpointer = create_sqlite_checkpointer()

            # Verify database file was created
            checkpoint_db = Path(".langgraph_data/checkpoints.db")
            assert checkpoint_db.exists(), "Checkpoint database should be created"
            assert checkpoint_db.stat().st_size > 0, "Database should not be empty"

        finally:
            os.chdir(original_cwd)


def test_checkpointer_can_save_and_load_state():
    """Test that checkpointer can save and retrieve checkpoint state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            checkpointer = create_sqlite_checkpointer()

            # Create a simple checkpoint config
            config = {
                "configurable": {
                    "thread_id": "test-thread",
                    "checkpoint_ns": "",
                }
            }

            # Create test state with messages
            test_messages = [
                HumanMessage(content="Hello"),
                AIMessage(content="Hi there!"),
            ]

            checkpoint = {
                "v": 1,
                "ts": "2024-01-01T00:00:00",
                "id": "checkpoint-1",
                "channel_values": {
                    "messages": test_messages,
                },
                "channel_versions": {
                    "messages": 1,
                },
                "versions_seen": {},
                "pending_sends": [],
            }

            # Save checkpoint
            checkpointer.put(config, checkpoint, {}, {})

            # Retrieve checkpoint
            retrieved = checkpointer.get(config)

            # Verify checkpoint was saved and retrieved
            assert retrieved is not None, "Checkpoint should be retrievable"
            assert "channel_values" in retrieved, "Checkpoint should have channel_values"

        finally:
            os.chdir(original_cwd)


def test_checkpointer_maintains_separate_threads():
    """Test that different thread_ids maintain separate checkpoint state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            checkpointer = create_sqlite_checkpointer()

            # Thread 1 config and checkpoint
            config1 = {
                "configurable": {
                    "thread_id": "thread-1",
                    "checkpoint_ns": "",
                }
            }
            checkpoint1 = {
                "v": 1,
                "ts": "2024-01-01T00:00:00",
                "id": "checkpoint-1",
                "channel_values": {
                    "messages": [HumanMessage(content="Thread 1 message")],
                },
                "channel_versions": {"messages": 1},
                "versions_seen": {},
                "pending_sends": [],
            }

            # Thread 2 config and checkpoint
            config2 = {
                "configurable": {
                    "thread_id": "thread-2",
                    "checkpoint_ns": "",
                }
            }
            checkpoint2 = {
                "v": 1,
                "ts": "2024-01-01T00:00:01",
                "id": "checkpoint-2",
                "channel_values": {
                    "messages": [HumanMessage(content="Thread 2 message")],
                },
                "channel_versions": {"messages": 1},
                "versions_seen": {},
                "pending_sends": [],
            }

            # Save both checkpoints
            checkpointer.put(config1, checkpoint1, {}, {})
            checkpointer.put(config2, checkpoint2, {}, {})

            # Retrieve and verify they're separate
            retrieved1 = checkpointer.get(config1)
            retrieved2 = checkpointer.get(config2)

            assert retrieved1 is not None
            assert retrieved2 is not None

            # Verify they contain different data
            msg1 = retrieved1["channel_values"]["messages"][0].content
            msg2 = retrieved2["channel_values"]["messages"][0].content

            assert msg1 == "Thread 1 message"
            assert msg2 == "Thread 2 message"

        finally:
            os.chdir(original_cwd)


def test_checkpointer_persists_across_instances():
    """Test that checkpoint data persists when creating new checkpointer instance."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)

            # First checkpointer instance
            checkpointer1 = create_sqlite_checkpointer()

            config = {
                "configurable": {
                    "thread_id": "persistent-thread",
                    "checkpoint_ns": "",
                }
            }

            checkpoint = {
                "v": 1,
                "ts": "2024-01-01T00:00:00",
                "id": "checkpoint-persist",
                "channel_values": {
                    "messages": [HumanMessage(content="Persistent message")],
                },
                "channel_versions": {"messages": 1},
                "versions_seen": {},
                "pending_sends": [],
            }

            # Save with first instance
            checkpointer1.put(config, checkpoint, {}, {})

            # Create new checkpointer instance (simulates server restart)
            checkpointer2 = create_sqlite_checkpointer()

            # Retrieve with second instance
            retrieved = checkpointer2.get(config)

            # Verify data persisted
            assert retrieved is not None
            assert retrieved["id"] == "checkpoint-persist"
            msg = retrieved["channel_values"]["messages"][0].content
            assert msg == "Persistent message"

        finally:
            os.chdir(original_cwd)
