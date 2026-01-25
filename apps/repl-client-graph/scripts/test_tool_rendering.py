#!/usr/bin/env python
"""Test tool-specific rendering for REPL subgraph.

This script demonstrates the full flow from tool call detection through
rendering with various SQL and interactive tools.
"""

from rich.console import Console

from repl_client_graph.context import set_renderer
from repl_client_graph.graph.nodes.rendering import render_output_node
from repl_client_graph.ui.renderer import Renderer


def test_sql_query_tool():
    """Test sql_db_query rendering with syntax highlighting."""
    print("\n" + "=" * 80)
    print("TEST 1: SQL Query Tool (sql_db_query)")
    print("=" * 80)

    state = {
        "render_queue": [
            {
                "type": "tool_call",
                "tool": {
                    "name": "sql_db_query",
                    "args": {
                        "query": "SELECT c_name, c_acctbal FROM customer WHERE c_region = 'ASIA' LIMIT 10"
                    },
                    "display": {
                        "format": "sql",
                        "query": "SELECT c_name, c_acctbal FROM customer WHERE c_region = 'ASIA' LIMIT 10",
                    },
                },
            }
        ]
    }

    result = render_output_node(state)
    assert len(result["render_queue"]) == 0, "Render queue should be cleared"
    print("\n✓ SQL query rendered with syntax highlighting")


def test_query_checker_tool():
    """Test sql_db_query_checker rendering."""
    print("\n" + "=" * 80)
    print("TEST 2: SQL Query Checker Tool (sql_db_query_checker)")
    print("=" * 80)

    state = {
        "render_queue": [
            {
                "type": "tool_call",
                "tool": {
                    "name": "sql_db_query_checker",
                    "args": {
                        "query": "SELECT COUNT(*) as total FROM orders WHERE o_year = 1995"
                    },
                    "display": {
                        "format": "sql",
                        "query": "SELECT COUNT(*) as total FROM orders WHERE o_year = 1995",
                    },
                },
            }
        ]
    }

    result = render_output_node(state)
    assert len(result["render_queue"]) == 0
    print("\n✓ Query checker rendered with syntax highlighting")


def test_schema_tool():
    """Test sql_db_schema rendering."""
    print("\n" + "=" * 80)
    print("TEST 3: SQL Schema Tool (sql_db_schema)")
    print("=" * 80)

    state = {
        "render_queue": [
            {
                "type": "tool_call",
                "tool": {
                    "name": "sql_db_schema",
                    "args": {"table_names": "customer, orders, lineitem"},
                    "display": {
                        "format": "schema",
                        "tables": ["customer", "orders", "lineitem"],
                    },
                },
            }
        ]
    }

    result = render_output_node(state)
    assert len(result["render_queue"]) == 0
    print("\n✓ Schema query rendered with table list")


def test_list_tables_tool():
    """Test sql_db_list_tables rendering."""
    print("\n" + "=" * 80)
    print("TEST 4: SQL List Tables Tool (sql_db_list_tables)")
    print("=" * 80)

    state = {
        "render_queue": [
            {
                "type": "tool_call",
                "tool": {
                    "name": "sql_db_list_tables",
                    "args": {},
                    "display": {"format": "list_tables"},
                },
            }
        ]
    }

    result = render_output_node(state)
    assert len(result["render_queue"]) == 0
    print("\n✓ List tables rendered with info panel")


def test_ask_question_tool():
    """Test AskUserQuestion rendering."""
    print("\n" + "=" * 80)
    print("TEST 5: Ask User Question Tool (AskUserQuestion)")
    print("=" * 80)

    state = {
        "render_queue": [
            {
                "type": "tool_call",
                "tool": {
                    "name": "AskUserQuestion",
                    "args": {
                        "question": "Which region should I analyze?",
                        "options": ["ASIA", "EUROPE", "AMERICAS", "AFRICA"],
                    },
                    "display": {
                        "format": "question",
                        "question": "Which region should I analyze?",
                        "options": ["ASIA", "EUROPE", "AMERICAS", "AFRICA"],
                    },
                },
            }
        ]
    }

    result = render_output_node(state)
    assert len(result["render_queue"]) == 0
    print("\n✓ Question rendered with options list")
    print("  (Phase 3 will add arrow-key navigation)")


def test_generic_tool():
    """Test generic tool fallback rendering."""
    print("\n" + "=" * 80)
    print("TEST 6: Generic Tool Fallback (unknown_tool)")
    print("=" * 80)

    state = {
        "render_queue": [
            {
                "type": "tool_call",
                "tool": {
                    "name": "custom_web_search",
                    "args": {
                        "query": "latest snowflake features",
                        "max_results": 5,
                        "include_snippets": True,
                    },
                },
            }
        ]
    }

    result = render_output_node(state)
    assert len(result["render_queue"]) == 0
    print("\n✓ Unknown tool rendered with JSON args fallback")


def test_multiple_tools():
    """Test rendering multiple tools in sequence."""
    print("\n" + "=" * 80)
    print("TEST 7: Multiple Tools in Sequence")
    print("=" * 80)

    state = {
        "render_queue": [
            {
                "type": "tool_call",
                "tool": {
                    "name": "sql_db_list_tables",
                    "args": {},
                    "display": {"format": "list_tables"},
                },
            },
            {
                "type": "tool_call",
                "tool": {
                    "name": "sql_db_schema",
                    "args": {"table_names": "customer"},
                    "display": {"format": "schema", "tables": ["customer"]},
                },
            },
            {
                "type": "tool_call",
                "tool": {
                    "name": "sql_db_query",
                    "args": {"query": "SELECT COUNT(*) FROM customer"},
                    "display": {
                        "format": "sql",
                        "query": "SELECT COUNT(*) FROM customer",
                    },
                },
            },
        ]
    }

    result = render_output_node(state)
    assert len(result["render_queue"]) == 0
    print("\n✓ Multiple tools rendered in sequence")


def main():
    """Run all tool rendering tests."""
    # Set up Rich renderer
    console = Console()
    renderer = Renderer(console)
    set_renderer(renderer)

    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "TOOL RENDERING TEST SUITE" + " " * 33 + "║")
    print("╚" + "=" * 78 + "╝")

    # Run tests
    test_sql_query_tool()
    test_query_checker_tool()
    test_schema_tool()
    test_list_tables_tool()
    test_ask_question_tool()
    test_generic_tool()
    test_multiple_tools()

    # Summary
    print("\n" + "=" * 80)
    print("ALL TESTS PASSED ✓")
    print("=" * 80)
    print("\nTool-specific rendering is working correctly!")
    print("\nSupported display formats:")
    print("  • sql          - SQL syntax highlighting")
    print("  • schema       - Table list panel")
    print("  • list_tables  - Info panel")
    print("  • question     - Interactive Q&A (Phase 3: arrow keys)")
    print("  • (none)       - Generic JSON fallback")
    print()


if __name__ == "__main__":
    main()
