"""Factory function for creating SQLite store instance."""

import sqlite3
from pathlib import Path

from langgraph.store.base import BaseStore, TTLConfig
from langgraph.store.sqlite import SqliteStore


def create_sqlite_store() -> BaseStore:
    """Create a SqliteStore instance for LangGraph.

    This factory is referenced from langgraph.json as:
    "store": {"path": "agent_snowflake.persistence.create_sqlite_store"}

    Note: LangGraph's runtime handles async/sync conversion internally.
    Using the synchronous SqliteStore is the correct approach for factory functions.

    Returns:
        BaseStore: Configured SqliteStore instance
    """
    # Ensure the directory exists
    store_path = Path(".langgraph_data/store.db")
    store_path.parent.mkdir(parents=True, exist_ok=True)

    # Create SQLite connection
    conn = sqlite3.connect(
        str(store_path),
        check_same_thread=False,
        isolation_level=None,  # autocommit mode
    )

    # Configure TTL (10080 minutes = 7 days)
    ttl_config = TTLConfig(
        default_ttl=10080 * 60,  # Convert minutes to seconds
        refresh_on_read=True,
    )

    # Create and setup the store
    store = SqliteStore(conn, ttl=ttl_config)
    store.setup()  # Run migrations

    return store
