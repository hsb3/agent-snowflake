"""Test the Snowflake agent graph.

These tests verify that the LangGraph agent compiles correctly and can be invoked.
Note: These tests require valid API keys in .env file.
"""

import pytest
from src.agent_snowflake.graph import build_graph
from src.agent_snowflake.utils import init_model


def test_build_graph_function():
    """Test that build_graph() function works."""
    graph = build_graph()
    assert graph is not None
    assert hasattr(graph, "nodes")


def test_graph_has_nodes():
    """Test that the graph has expected nodes."""
    graph = build_graph()
    nodes = list(graph.nodes.keys())
    assert len(nodes) > 0


def test_init_model_wrapper():
    """Test that init_model wrapper is available."""
    assert init_model is not None
    assert callable(init_model)


@pytest.mark.skip(reason="Requires valid API key and makes external API calls")
def test_graph_invocation():
    """Test invoking the graph with a simple message.

    This test is skipped by default as it requires:
    - Valid API key in .env file
    - Makes external API calls
    """
    graph = build_graph()
    result = graph.invoke(
        {"messages": [{"role": "user", "content": "Hello! Can you help me with Snowflake?"}]},
    )

    assert "messages" in result
    assert len(result["messages"]) > 0
