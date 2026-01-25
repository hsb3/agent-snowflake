"""Compare single-node vs subgraph approaches for process_stream.

This script builds both graph versions and compares:
- Total node count
- Edge count
- Estimated invocations per message
- Graph complexity metrics
- Visualization differences

Usage:
    uv run python scripts/compare_stream_approaches.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from repl_client_graph.graph.builder import build_repl_graph
from repl_client_graph.graph.builder_subgraph import build_repl_graph_with_subgraph


def count_graph_elements(graph) -> dict:
    """Count nodes and edges in a compiled graph.

    Args:
        graph: Compiled StateGraph

    Returns:
        Dictionary with node_count, edge_count, etc.
    """
    try:
        # Access the underlying graph structure
        # LangGraph stores this in graph.graph or similar
        nodes = graph.nodes if hasattr(graph, "nodes") else {}

        # Count nodes
        node_count = len(nodes) if isinstance(nodes, dict) else 0

        # Try to count edges (varies by LangGraph version)
        edge_count = 0
        if hasattr(graph, "edges"):
            edges = graph.edges
            if isinstance(edges, dict):
                edge_count = sum(len(v) if isinstance(v, list) else 1 for v in edges.values())

        return {
            "node_count": node_count,
            "edge_count": edge_count,
        }
    except Exception as e:
        return {
            "node_count": "Unable to count",
            "edge_count": "Unable to count",
            "error": str(e),
        }


def estimate_invocations_single_node(num_chunks: int, num_tools: int) -> dict:
    """Estimate invocations for single-node approach.

    Args:
        num_chunks: Number of SSE chunks in response
        num_tools: Number of tool calls in response

    Returns:
        Dictionary with invocation estimates
    """
    # Single node approach: process_stream runs once
    return {
        "process_stream_node": 1,
        "total": 1,
        "description": "All chunk processing in single node invocation",
    }


def estimate_invocations_subgraph(num_chunks: int, num_tools: int) -> dict:
    """Estimate invocations for subgraph approach.

    Args:
        num_chunks: Number of SSE chunks in response
        num_tools: Number of tool calls in response

    Returns:
        Dictionary with invocation estimates per node type
    """
    # Subgraph approach: multiple nodes per chunk

    # Each chunk: fetch_chunk → parse_chunk
    fetch_chunk_invocations = num_chunks
    parse_chunk_invocations = num_chunks

    # Assume half chunks are text deltas, half are complete messages
    text_chunks = num_chunks // 2
    complete_chunks = num_chunks - text_chunks

    extract_text_delta = text_chunks
    extract_tools = complete_chunks

    # Tool processing
    fetch_next_tool = num_tools
    render_tool = num_tools  # Each tool rendered once

    total = (
        fetch_chunk_invocations +
        parse_chunk_invocations +
        extract_text_delta +
        extract_tools +
        fetch_next_tool +
        render_tool
    )

    return {
        "fetch_chunk": fetch_chunk_invocations,
        "parse_chunk": parse_chunk_invocations,
        "extract_text_delta": extract_text_delta,
        "extract_tools": extract_tools,
        "fetch_next_tool": fetch_next_tool,
        "render_tool": render_tool,
        "total": total,
        "description": f"Fine-grained subgraph with {total} node invocations",
    }


def calculate_complexity_metrics(node_count: int, edge_count: int) -> dict:
    """Calculate graph complexity metrics.

    Args:
        node_count: Number of nodes
        edge_count: Number of edges

    Returns:
        Dictionary with complexity metrics
    """
    # Cyclomatic complexity approximation
    # V(G) = E - N + 2P (where P is number of connected components, assume 1)
    cyclomatic = edge_count - node_count + 2 if isinstance(edge_count, int) and isinstance(node_count, int) else "N/A"

    # Average edges per node
    avg_edges = edge_count / node_count if node_count > 0 and isinstance(edge_count, int) else "N/A"

    return {
        "cyclomatic_complexity": cyclomatic,
        "avg_edges_per_node": f"{avg_edges:.2f}" if isinstance(avg_edges, float) else avg_edges,
    }


def print_comparison():
    """Print side-by-side comparison of both approaches."""

    print("=" * 80)
    print("PROCESS_STREAM APPROACH COMPARISON")
    print("=" * 80)
    print()

    # Build both graphs
    print("Building graphs...")
    single_node_graph = build_repl_graph()
    subgraph_graph = build_repl_graph_with_subgraph()
    print("✓ Both graphs compiled successfully")
    print()

    # Count graph elements
    single_metrics = count_graph_elements(single_node_graph)
    subgraph_metrics = count_graph_elements(subgraph_graph)

    # Print structure comparison
    print("1. GRAPH STRUCTURE")
    print("-" * 80)
    print(f"{'Metric':<30} {'Single Node':<25} {'Subgraph':<25}")
    print("-" * 80)

    print(f"{'Total Nodes':<30} {single_metrics['node_count']:<25} {subgraph_metrics['node_count']:<25}")
    print(f"{'Total Edges':<30} {single_metrics['edge_count']:<25} {subgraph_metrics['edge_count']:<25}")

    # Complexity metrics
    single_complexity = calculate_complexity_metrics(
        single_metrics.get("node_count", 0),
        single_metrics.get("edge_count", 0)
    )
    subgraph_complexity = calculate_complexity_metrics(
        subgraph_metrics.get("node_count", 0),
        subgraph_metrics.get("edge_count", 0)
    )

    print(f"{'Cyclomatic Complexity':<30} {single_complexity['cyclomatic_complexity']:<25} {subgraph_complexity['cyclomatic_complexity']:<25}")
    print(f"{'Avg Edges per Node':<30} {single_complexity['avg_edges_per_node']:<25} {subgraph_complexity['avg_edges_per_node']:<25}")
    print()

    # Invocation estimates
    print("2. ESTIMATED INVOCATIONS PER MESSAGE")
    print("-" * 80)

    # Test scenarios
    scenarios = [
        {"name": "Small (20 chunks, 2 tools)", "chunks": 20, "tools": 2},
        {"name": "Medium (50 chunks, 5 tools)", "chunks": 50, "tools": 5},
        {"name": "Large (100 chunks, 10 tools)", "chunks": 100, "tools": 10},
    ]

    for scenario in scenarios:
        print(f"\nScenario: {scenario['name']}")
        print(f"  Chunks: {scenario['chunks']}, Tools: {scenario['tools']}")

        single_invocations = estimate_invocations_single_node(
            scenario['chunks'], scenario['tools']
        )
        subgraph_invocations = estimate_invocations_subgraph(
            scenario['chunks'], scenario['tools']
        )

        print(f"  Single Node: {single_invocations['total']} invocations")
        print(f"  Subgraph: {subgraph_invocations['total']} invocations")
        print(f"  Overhead: {subgraph_invocations['total'] / single_invocations['total']:.1f}x")

    print()

    # Architecture comparison
    print("3. ARCHITECTURE COMPARISON")
    print("-" * 80)

    print("\nSingle Node Approach (builder.py):")
    print("  ✓ Simple: All logic in one function")
    print("  ✓ Fast: Single invocation per message")
    print("  ✓ Low overhead: Minimal graph traversal")
    print("  ✗ Can grow large: 500+ lines with many tools")
    print("  ✗ Hard to test: Monolithic function")
    print("  ✗ Mixed concerns: Parsing + rendering in one place")

    print("\nSubgraph Approach (builder_subgraph.py):")
    print("  ✓ Modular: Each concern is a separate node")
    print("  ✓ Extensible: Easy to add new tool handlers")
    print("  ✓ Testable: Each node tested in isolation")
    print("  ✓ Clear separation: Parsing vs rendering")
    print("  ✗ Complex: More nodes and edges to understand")
    print("  ✗ Overhead: 50-150x more invocations")
    print("  ✗ Slower: Graph traversal per chunk")

    print()

    # Recommendations
    print("4. RECOMMENDATIONS")
    print("-" * 80)
    print("\nWhen to use Single Node:")
    print("  • Simple tools (< 15 types)")
    print("  • Stateless rendering")
    print("  • Performance is critical")
    print("  • Simple mental model preferred")

    print("\nWhen to use Subgraph:")
    print("  • Complex tools (20+ types)")
    print("  • Multi-step tool rendering")
    print("  • Interactive tools (user input mid-stream)")
    print("  • Detailed observability needed")

    print()

    # File locations
    print("5. FILES")
    print("-" * 80)
    print("\nSingle Node Implementation:")
    print("  • src/repl_client_graph/graph/builder.py")
    print("  • src/repl_client_graph/graph/nodes/streaming.py")

    print("\nSubgraph Implementation:")
    print("  • src/repl_client_graph/graph/builder_subgraph.py")
    print("  • src/repl_client_graph/graph/nodes/streaming_subgraph.py")

    print()
    print("=" * 80)


def generate_visualizations():
    """Generate visual representations of both graphs.

    Note: This requires graphviz or similar tools to be installed.
    For now, we'll print the graph structure as ASCII.
    """
    print("\n6. VISUAL COMPARISON")
    print("-" * 80)

    print("\nSingle Node Flow:")
    print("""
    get_input → route_input → send_message → [process_stream] → update_session → render_output
                     ↓                              ↓
                execute_command                handle_interrupt
                     ↓                              ↓
                render_output                  process_stream (resume)

    [process_stream] = Single node handling all chunks
    """)

    print("\nSubgraph Flow:")
    print("""
    get_input → route_input → send_message → [process_stream_subgraph] → update_session → render_output
                     ↓
                execute_command
                     ↓
                render_output

    [process_stream_subgraph] expanded:
        fetch_chunk → parse_chunk → [route by type]
            → text: extract_text_delta → loop back
            → tools: extract_tools → fetch_next_tool → [route by tool_name]
                → sql/question/code/generic render → loop back
            → updates: detect_interrupt → exit

    Note: Subgraph loops internally for each chunk
    """)

    print()


if __name__ == "__main__":
    try:
        print_comparison()
        generate_visualizations()

        print("\nComparison complete!")
        print("\nNext steps:")
        print("  1. Run test script: uv run python scripts/test_subgraph_stream.py")
        print("  2. Review documentation: docs/dev_docs/stream_subgraph_poc.md")
        print("  3. Make architecture decision based on tradeoffs")

    except Exception as e:
        print(f"\n✗ Error during comparison: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
