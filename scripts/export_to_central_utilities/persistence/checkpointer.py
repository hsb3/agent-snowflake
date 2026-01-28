"""Factory function for creating SQLite checkpointer instance."""

import sqlite3
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver


def create_sqlite_checkpointer() -> SqliteSaver:
    """Create a SqliteSaver instance for LangGraph.

    This factory is referenced from langgraph.json as:
    "checkpointer": {"path": "agent_snowflake.persistence.create_sqlite_checkpointer"}

    Note: LangGraph's runtime handles async/sync conversion internally.
    Using the synchronous SqliteSaver is the correct approach for factory functions.

    Returns:
        SqliteSaver: Configured SqliteSaver instance
    """
    # Ensure the directory exists
    checkpoint_path = Path(".langgraph_data/checkpoints.db")
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    # Create SQLite connection
    conn = sqlite3.connect(
        str(checkpoint_path),
        check_same_thread=False,
    )

    # Create and setup the checkpointer
    checkpointer = SqliteSaver(conn)
    checkpointer.setup()  # Run migrations

    return checkpointer
