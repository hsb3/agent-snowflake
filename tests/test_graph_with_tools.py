"""Test graph integration with SQL tools."""

from unittest.mock import patch

from langchain_community.utilities import SQLDatabase
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from agent_snowflake.graph import build_graph


def test_build_graph_with_sqlite():
    """Test that graph builds successfully with SQLite (no Snowflake needed)."""
    # Create SQLite database
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    Table(
        "customer",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(50)),
    )
    metadata.create_all(engine)

    # Mock the create_sql_database to use SQLite instead of Snowflake
    with patch("agent_snowflake.tools.sql.create_sql_database") as mock_create_db:
        mock_create_db.return_value = SQLDatabase(engine)

        config = {
            "configurable": {
                "snowflake_uri": "sqlite:///:memory:",
                "read_only": True,
                "model": "claude-sonnet-4-5-20250929",
            }
        }

        # Build graph with mocked database
        graph = build_graph(config)

        assert graph is not None
        assert hasattr(graph, "invoke")
        # Verify create_sql_database was called
        assert mock_create_db.called


def test_graph_structure():
    """Test that graph has expected structure from create_agent."""
    # Create SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    Table("test", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)

    with patch("agent_snowflake.tools.sql.create_sql_database") as mock_create_db:
        mock_create_db.return_value = SQLDatabase(engine)

        config = {
            "configurable": {
                "snowflake_uri": "sqlite:///:memory:",
                "model": "claude-sonnet-4-5-20250929",
            }
        }

        graph = build_graph(config)

        # Verify graph structure
        assert graph is not None
        assert hasattr(graph, "nodes")
        assert len(graph.nodes) > 0  # Should have nodes from create_agent
