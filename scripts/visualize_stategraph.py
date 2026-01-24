"""Script to visualize any LangGraph StateGraph as PNG.

This script generates a PNG visualization of a LangGraph StateGraph,
showing all nodes and their connections including conditional routing.

Usage:
    # Visualize REPL graph
    uv run python scripts/visualize_stategraph.py repl_client_graph:build_repl_graph

    # Visualize custom graph with custom output
    uv run python scripts/visualize_stategraph.py my_module:build_my_graph --output my_graph.png

    # Just generate mermaid without PNG
    uv run python scripts/visualize_stategraph.py my_module:build_graph --no-png

Arguments:
    graph_ref       Import reference in format "module.path:function_name"
                    The function should return a compiled StateGraph
    --output        Output filename (default: graph.png)
    --output-dir    Output directory (default: docs/dev_docs/graphs)
    --no-png        Skip PNG generation, only create mermaid diagram
    --open          Automatically open the PNG after generation (default: True)
    --no-open       Don't open the PNG after generation
"""

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def import_graph_builder(graph_ref: str) -> Any:
    """Import a graph builder function from a module reference.

    Args:
        graph_ref: Reference in format "module.path:function_name"
                  e.g., "repl_client_graph:build_repl_graph"

    Returns:
        The imported function that builds/returns a StateGraph

    Raises:
        ImportError: If module or function cannot be imported
        ValueError: If graph_ref format is invalid
    """
    if ":" not in graph_ref:
        raise ValueError(
            f"Invalid graph reference format: {graph_ref}\n"
            "Expected format: 'module.path:function_name'"
        )

    module_path, function_name = graph_ref.split(":", 1)

    try:
        module = importlib.import_module(module_path)
        print(f"✓ Successfully imported module: {module_path}")
    except ImportError as e:
        raise ImportError(f"Failed to import module '{module_path}': {e}")

    if not hasattr(module, function_name):
        raise AttributeError(
            f"Module '{module_path}' has no function '{function_name}'\n"
            f"Available: {', '.join(dir(module))}"
        )

    builder_func = getattr(module, function_name)
    print(f"✓ Successfully imported function: {function_name}")

    return builder_func


def analyze_graph_structure(graph_structure: Any) -> dict[str, Any]:
    """Analyze a graph structure and extract metadata.

    Args:
        graph_structure: The graph structure from graph.get_graph()

    Returns:
        Dictionary with analysis results
    """
    nodes = list(graph_structure.nodes.keys())
    edges = graph_structure.edges

    # Analyze edges
    edge_info = []
    conditional_count = 0

    for edge in edges:
        source = edge.source if hasattr(edge, "source") else "unknown"
        target = edge.target if hasattr(edge, "target") else "unknown"
        is_conditional = hasattr(edge, "data") and edge.data

        if is_conditional:
            conditional_count += 1
            condition = edge.data if isinstance(edge.data, str) else "conditional"
            edge_info.append({
                "source": source,
                "target": target,
                "type": "conditional",
                "condition": condition,
            })
        else:
            edge_info.append({
                "source": source,
                "target": target,
                "type": "direct",
                "condition": None,
            })

    # Find conditional routing points
    conditional_sources = {}
    for edge in edge_info:
        if edge["type"] == "conditional":
            source = edge["source"]
            if source not in conditional_sources:
                conditional_sources[source] = []
            conditional_sources[source].append(edge["target"])

    # Find entry and exit points
    entry_nodes = [n for n in nodes if n == "__start__"]
    exit_nodes = [n for n in nodes if n == "__end__"]

    return {
        "nodes": nodes,
        "node_count": len(nodes),
        "edges": edge_info,
        "edge_count": len(edges),
        "conditional_count": conditional_count,
        "direct_count": len(edges) - conditional_count,
        "conditional_sources": conditional_sources,
        "entry_nodes": entry_nodes,
        "exit_nodes": exit_nodes,
    }


def print_graph_analysis(analysis: dict[str, Any]) -> None:
    """Print detailed graph analysis to console.

    Args:
        analysis: Analysis results from analyze_graph_structure()
    """
    print("\n" + "=" * 80)
    print("GRAPH NODES")
    print("=" * 80)
    for node_id in analysis["nodes"]:
        print(f"  - {node_id}")

    print("\n" + "=" * 80)
    print("GRAPH EDGES")
    print("=" * 80)
    for edge in analysis["edges"]:
        if edge["type"] == "conditional":
            print(f"  {edge['source']} --[{edge['condition']}]--> {edge['target']}")
        else:
            print(f"  {edge['source']} --> {edge['target']}")

    print(f"\nTotal edges: {analysis['edge_count']}")
    print(f"Conditional edges: {analysis['conditional_count']}")
    print(f"Direct edges: {analysis['direct_count']}")

    print("\n" + "=" * 80)
    print("GRAPH STRUCTURE")
    print("=" * 80)

    if analysis["entry_nodes"]:
        print(f"Entry point: {', '.join(analysis['entry_nodes'])}")
    if analysis["exit_nodes"]:
        print(f"Exit point: {', '.join(analysis['exit_nodes'])}")

    if analysis["conditional_sources"]:
        print("\nConditional routing points:")
        for source, targets in analysis["conditional_sources"].items():
            print(f"  {source} routes to {len(targets)} targets: {', '.join(targets)}")

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total nodes: {analysis['node_count']}")
    print(f"Total edges: {analysis['edge_count']}")
    print(f"Conditional routing points: {len(analysis['conditional_sources'])}")
    print(f"Graph type: Directed Acyclic Graph (DAG)")


def visualize_stategraph(
    graph_ref: str,
    output_filename: str = "graph.png",
    output_dir: str | Path = None,
    generate_png: bool = True,
    auto_open: bool = True,
) -> dict[str, Path]:
    """Generate visualization for a StateGraph.

    Args:
        graph_ref: Import reference in format "module.path:function_name"
        output_filename: Name of output file (without extension for base name)
        output_dir: Directory for output files (default: docs/dev_docs/graphs)
        generate_png: Whether to generate PNG (requires graphviz)
        auto_open: Whether to automatically open PNG after generation

    Returns:
        Dictionary with paths to generated files
    """
    # Set up output directory
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "docs" / "dev_docs" / "graphs"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate base filename (without extension)
    base_name = Path(output_filename).stem

    png_path = output_dir / f"{base_name}.png"
    mermaid_path = output_dir / f"{base_name}.mmd"

    generated_files = {}

    try:
        # Import and build the graph
        print(f"Importing graph builder from: {graph_ref}")
        builder_func = import_graph_builder(graph_ref)

        print("Building StateGraph...")
        graph = builder_func()
        print("✓ Successfully built graph")

        # Get the graph structure
        graph_structure = graph.get_graph()
        print(f"✓ Retrieved graph structure with {len(graph_structure.nodes)} nodes")

        # Analyze the graph
        analysis = analyze_graph_structure(graph_structure)
        print_graph_analysis(analysis)

        # Generate PNG if requested
        if generate_png:
            try:
                print("\nGenerating PNG visualization...")
                png_data = graph_structure.draw_mermaid_png()

                with open(png_path, "wb") as f:
                    f.write(png_data)

                print(f"\n✓ Graph visualization saved to: {png_path}")
                print(f"  Size: {len(png_data):,} bytes")
                generated_files["png"] = png_path

                # Auto-open if requested
                if auto_open:
                    try:
                        import subprocess
                        subprocess.run(["open", str(png_path)], check=False)
                        print(f"  Opened: {png_path}")
                    except Exception:
                        print(f"  View with: open {png_path}")

            except Exception as e:
                print(f"\n✗ Failed to generate PNG: {e}")
                print("  Install graphviz: brew install graphviz (macOS)")
                print("                    apt-get install graphviz (Linux)")

        # Always generate Mermaid diagram
        try:
            print("\nGenerating Mermaid diagram...")
            mermaid_text = graph_structure.draw_mermaid()

            with open(mermaid_path, "w") as f:
                f.write(mermaid_text)

            print(f"✓ Mermaid diagram saved to: {mermaid_path}")
            print("  You can visualize this at: https://mermaid.live/")
            generated_files["mermaid"] = mermaid_path

            print("\nMermaid diagram:")
            print("-" * 80)
            print(mermaid_text)
            print("-" * 80)

        except Exception as e:
            print(f"\n✗ Failed to generate mermaid diagram: {e}")

        return generated_files

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Visualize LangGraph StateGraph as PNG and Mermaid diagram",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize REPL graph
  python scripts/visualize_stategraph.py repl_client_graph:build_repl_graph

  # Custom output name
  python scripts/visualize_stategraph.py my_module:build_graph --output my_graph.png

  # Just generate mermaid
  python scripts/visualize_stategraph.py my_module:build_graph --no-png

  # Custom output directory
  python scripts/visualize_stategraph.py my_module:build_graph --output-dir /tmp
        """,
    )

    parser.add_argument(
        "graph_ref",
        help="Import reference: 'module.path:function_name'",
    )
    parser.add_argument(
        "--output",
        default="graph.png",
        help="Output filename (default: graph.png)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: docs/dev_docs/graphs)",
    )
    parser.add_argument(
        "--no-png",
        action="store_true",
        help="Skip PNG generation, only create mermaid",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't automatically open PNG",
    )

    args = parser.parse_args()

    visualize_stategraph(
        graph_ref=args.graph_ref,
        output_filename=args.output,
        output_dir=args.output_dir,
        generate_png=not args.no_png,
        auto_open=not args.no_open,
    )


if __name__ == "__main__":
    main()
