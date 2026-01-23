"""Test the Snowflake agent graph.

These tests verify that the LangGraph agent compiles correctly and can be invoked.
Note: Some tests require valid API keys in .env file.
"""

from unittest.mock import patch

import pytest
from langchain_community.utilities import SQLDatabase
from sqlalchemy import Column, Integer, MetaData, Table, create_engine

from src.agent_snowflake.graph import build_graph
from src.agent_snowflake.utils import init_model


@pytest.fixture
def mock_sqlite_db():
    """Create mock SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    Table("test_table", metadata, Column("id", Integer, primary_key=True))
    metadata.create_all(engine)
    return SQLDatabase(engine)


def test_build_graph_function(mock_sqlite_db):
    """Test that build_graph() function works with database."""
    with patch("agent_snowflake.tools.sql.create_sql_database") as mock_create_db:
        mock_create_db.return_value = mock_sqlite_db

        config = {
            "configurable": {
                "snowflake_uri": "sqlite:///:memory:",
            }
        }

        graph = build_graph(config)
        assert graph is not None
        assert hasattr(graph, "nodes")


def test_graph_has_nodes(mock_sqlite_db):
    """Test that the graph has expected nodes."""
    with patch("agent_snowflake.tools.sql.create_sql_database") as mock_create_db:
        mock_create_db.return_value = mock_sqlite_db

        config = {
            "configurable": {
                "snowflake_uri": "sqlite:///:memory:",
            }
        }

        graph = build_graph(config)
        nodes = list(graph.nodes.keys())
        assert len(nodes) > 0


def test_init_model_wrapper():
    """Test that init_model wrapper is available."""
    assert init_model is not None
    assert callable(init_model)


@pytest.mark.skip(reason="Requires valid API key and Snowflake connection")
def test_graph_invocation():
    """Test invoking the graph with a simple message.

    This test is skipped by default as it requires:
    - Valid API key in .env file
    - Valid Snowflake connection
    - Makes external API calls
    """
    config = {
        "configurable": {
            "snowflake_uri": "snowflake://...",  # Provide actual URI
        }
    }

    graph = build_graph(config)
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "List the available tables"}]},
    )

    assert "messages" in result
    assert len(result["messages"]) > 0
