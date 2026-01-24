#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "langgraph>=0.2.0",
# ]
# ///
"""Standalone script to visualize any LangGraph StateGraph as PNG and Mermaid diagram.

This script can be copied to any project and used to visualize LangGraph StateGraphs.
It generates PNG visualizations and Mermaid diagrams showing all nodes and their
connections including conditional routing.

Requirements:
    - Python 3.11+
    - langgraph package
    - graphviz (system package, for PNG generation only)

Usage Patterns:

    Method 1: Run within your project's environment (recommended)
    -------------------------------------------------------
    This uses your project's dependencies and avoids import issues:

    uv run python visualize_stategraph.py my_module:build_graph --python-path ./src

    Method 2: Run as standalone uv script
    ------------------------------------
    The script runs in its own isolated environment. Your graph builder function
    must not have dependencies beyond langgraph, or add them to the script metadata.

    uv run visualize_stategraph.py my_module:build_graph --python-path ./src

Examples:
    # Visualize a graph (using project environment)
    uv run python visualize_stategraph.py my_module:build_my_graph --python-path ./src

    # Custom output name and directory
    uv run python visualize_stategraph.py my_module:build_graph --python-path ./src --output custom.png --output-dir ./output

    # Multiple Python paths
    uv run python visualize_stategraph.py my_module:build_graph --python-path ./src --python-path ./lib

    # Just generate mermaid without PNG
    uv run python visualize_stategraph.py my_module:build_graph --python-path ./src --no-png

Arguments:
    graph_ref          Import reference in format "module.path:function_name"
                       The function should return a StateGraph or CompiledStateGraph
    --python-path      Add directory to Python import path (repeatable)
    --output           Output filename (default: graph.png)
    --output-dir       Output directory (default: current directory)
    --no-png           Skip PNG generation, only create mermaid diagram
    --ascii            Generate ASCII art visualization (auto-generated if PNG fails)
    --no-open          Don't automatically open PNG after generation
"""

import argparse
import importlib
import subprocess
import sys
from pathlib import Path
from typing import Any


def check_graphviz_installed() -> bool:
    """Check if graphviz is installed on the system.

    Returns:
        True if graphviz is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["dot", "-V"],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def prompt_install_graphviz() -> bool:
    """Prompt user to install graphviz.

    Returns:
        True if user wants to proceed with installation, False otherwise
    """
    print("\n" + "=" * 80)
    print("GRAPHVIZ NOT FOUND")
    print("=" * 80)
    print("\nGraphviz is required for PNG generation.")
    print("\nInstallation instructions:")
    print("  macOS:   brew install graphviz")
    print("  Ubuntu:  sudo apt-get install graphviz")
    print("  Fedora:  sudo dnf install graphviz")
    print("  Windows: choco install graphviz")
    print("\nAlternatively, use --no-png to skip PNG generation.")
    print("=" * 80)

    response = input("\nWould you like to install graphviz now? [y/N]: ").strip().lower()
    return response in ("y", "yes")


def install_graphviz() -> bool:
    """Attempt to install graphviz using system package manager.

    Returns:
        True if installation succeeded, False otherwise
    """
    import platform

    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            print("\nInstalling graphviz using Homebrew...")
            result = subprocess.run(
                ["brew", "install", "graphviz"],
                check=False,
            )
            return result.returncode == 0
        elif system == "Linux":
            # Try to detect package manager
            if subprocess.run(["which", "apt-get"], capture_output=True).returncode == 0:
                print("\nInstalling graphviz using apt-get...")
                result = subprocess.run(
                    ["sudo", "apt-get", "install", "-y", "graphviz"],
                    check=False,
                )
                return result.returncode == 0
            elif subprocess.run(["which", "dnf"], capture_output=True).returncode == 0:
                print("\nInstalling graphviz using dnf...")
                result = subprocess.run(
                    ["sudo", "dnf", "install", "-y", "graphviz"],
                    check=False,
                )
                return result.returncode == 0
        else:
            print(f"\n✗ Automatic installation not supported on {system}")
            print("  Please install graphviz manually and try again.")
            return False
    except Exception as e:
        print(f"\n✗ Installation failed: {e}")
        return False

    return False


def validate_and_compile_graph(graph_obj: Any) -> Any:
    """Validate that the object is a StateGraph or CompiledStateGraph and compile if needed.

    Args:
        graph_obj: The object returned by the graph builder function

    Returns:
        A CompiledStateGraph ready for visualization

    Raises:
        TypeError: If the object is not a StateGraph or CompiledStateGraph
    """
    # Lazy import to avoid import errors when script is loaded
    try:
        from langgraph.graph import StateGraph
        from langgraph.graph.state import CompiledStateGraph
    except ImportError:
        print("\n✗ Error: langgraph not found")
        print("  Install with: uv add langgraph")
        print("  Or run with: uv run python <script> (uses project environment)")
        sys.exit(1)

    # Check if it's already a CompiledStateGraph
    if isinstance(graph_obj, CompiledStateGraph):
        print("✓ Received CompiledStateGraph")
        return graph_obj

    # Check if it's a StateGraph that needs compilation
    if isinstance(graph_obj, StateGraph):
        print("✓ Received StateGraph, compiling...")
        try:
            compiled = graph_obj.compile()
            print("✓ Successfully compiled StateGraph")
            return compiled
        except Exception as e:
            raise RuntimeError(f"Failed to compile StateGraph: {e}")

    # Invalid type
    obj_type = type(graph_obj).__name__
    raise TypeError(
        f"Expected StateGraph or CompiledStateGraph, got {obj_type}\n"
        f"The function must return either:\n"
        f"  - A StateGraph instance (will be compiled automatically)\n"
        f"  - A CompiledStateGraph instance (from StateGraph.compile())"
    )


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


def generate_ascii_graph(analysis: dict[str, Any]) -> str:
    """Generate ASCII art representation of the graph.

    Args:
        analysis: Analysis results from analyze_graph_structure()

    Returns:
        ASCII art string representation of the graph
    """
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append("ASCII GRAPH VISUALIZATION")
    lines.append("=" * 80)
    lines.append("")

    # Build adjacency information
    outgoing = {}  # node -> list of (target, condition)
    incoming = {}  # node -> list of source

    for edge in analysis["edges"]:
        source = edge["source"]
        target = edge["target"]
        condition = edge.get("condition")

        if source not in outgoing:
            outgoing[source] = []
        outgoing[source].append((target, condition))

        if target not in incoming:
            incoming[target] = []
        incoming[target].append(source)

    # Find entry and exit nodes
    entry_nodes = [n for n in analysis["nodes"] if n == "__start__"]
    exit_nodes = [n for n in analysis["nodes"] if n == "__end__"]

    # Do a simple flow representation
    lines.append("FLOW DIAGRAM:")
    lines.append("")

    # Start with entry node
    if entry_nodes:
        lines.append(f"  ┌─────────────────┐")
        lines.append(f"  │   __start__     │")
        lines.append(f"  └─────────────────┘")
        lines.append(f"          │")
        lines.append(f"          ▼")

    # Show all other nodes with their connections
    regular_nodes = [n for n in analysis["nodes"] if n not in ["__start__", "__end__"]]

    for i, node in enumerate(regular_nodes):
        # Node box
        node_display = node[:40]  # Truncate long names
        padding = max(0, 17 - len(node_display))
        lines.append(f"  ┌─────────────────┐")
        lines.append(f"  │ {node_display}{' ' * padding}│")
        lines.append(f"  └─────────────────┘")

        # Show outgoing edges
        if node in outgoing and outgoing[node]:
            targets = outgoing[node]
            if len(targets) == 1:
                target, condition = targets[0]
                if condition:
                    lines.append(f"          │ [{condition}]")
                else:
                    lines.append(f"          │")
                lines.append(f"          ▼")
            else:
                # Multiple targets - show branching
                lines.append(f"          │")
                for j, (target, condition) in enumerate(targets):
                    if j == 0:
                        lines.append(f"     ┌────┴────┐")
                    cond_str = f"[{condition}]" if condition else ""
                    lines.append(f"     │  {cond_str}")
                    lines.append(f"     ▼  to: {target[:30]}")

    # End with exit node
    if exit_nodes:
        lines.append(f"  ┌─────────────────┐")
        lines.append(f"  │    __end__      │")
        lines.append(f"  └─────────────────┘")

    lines.append("")
    lines.append("=" * 80)
    lines.append("NODE CONNECTIONS")
    lines.append("=" * 80)
    lines.append("")

    # List all connections in detail
    for node in analysis["nodes"]:
        lines.append(f"📍 {node}")

        # Incoming edges
        if node in incoming and incoming[node]:
            lines.append(f"   Incoming from:")
            for source in incoming[node]:
                lines.append(f"     ← {source}")

        # Outgoing edges
        if node in outgoing and outgoing[node]:
            lines.append(f"   Outgoing to:")
            for target, condition in outgoing[node]:
                if condition:
                    lines.append(f"     → {target} [{condition}]")
                else:
                    lines.append(f"     → {target}")

        if not (node in incoming and incoming[node]) and not (node in outgoing and outgoing[node]):
            lines.append(f"   (isolated node)")

        lines.append("")

    lines.append("=" * 80)
    lines.append("STATISTICS")
    lines.append("=" * 80)
    lines.append(f"Total nodes: {analysis['node_count']}")
    lines.append(f"Total edges: {analysis['edge_count']}")
    lines.append(f"  - Direct edges: {analysis['direct_count']}")
    lines.append(f"  - Conditional edges: {analysis['conditional_count']}")

    if analysis['conditional_sources']:
        lines.append(f"\nConditional routing points: {len(analysis['conditional_sources'])}")
        for source, targets in analysis['conditional_sources'].items():
            lines.append(f"  • {source} → {len(targets)} branches")

    lines.append("=" * 80)

    return "\n".join(lines)


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
    generate_ascii: bool = False,
    auto_open: bool = True,
    python_paths: list[str] | None = None,
) -> dict[str, Path]:
    """Generate visualization for a StateGraph.

    Args:
        graph_ref: Import reference in format "module.path:function_name"
        output_filename: Name of output file (without extension for base name)
        output_dir: Directory for output files (default: current directory)
        generate_png: Whether to generate PNG (requires graphviz)
        generate_ascii: Whether to generate ASCII art visualization (always generated on PNG failure)
        auto_open: Whether to automatically open PNG after generation
        python_paths: List of paths to add to sys.path for imports

    Returns:
        Dictionary with paths to generated files
    """
    # Add custom Python paths to sys.path
    if python_paths:
        for path in python_paths:
            abs_path = str(Path(path).resolve())
            if abs_path not in sys.path:
                sys.path.insert(0, abs_path)
                print(f"Added to Python path: {abs_path}")

    # Set up output directory
    if output_dir is None:
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate base filename (without extension)
    base_name = Path(output_filename).stem

    png_path = output_dir / f"{base_name}.png"
    mermaid_path = output_dir / f"{base_name}.mmd"
    ascii_path = output_dir / f"{base_name}.txt"

    generated_files = {}

    try:
        # Import and build the graph
        print(f"Importing graph builder from: {graph_ref}")
        builder_func = import_graph_builder(graph_ref)

        print("Building graph...")
        graph_obj = builder_func()
        print("✓ Successfully built graph")

        # Validate and compile if needed
        print("Validating graph type...")
        graph = validate_and_compile_graph(graph_obj)

        # Get the graph structure
        graph_structure = graph.get_graph()
        print(f"✓ Retrieved graph structure with {len(graph_structure.nodes)} nodes")

        # Analyze the graph
        analysis = analyze_graph_structure(graph_structure)
        print_graph_analysis(analysis)

        # Generate PNG if requested
        if generate_png:
            # Check if graphviz is installed
            if not check_graphviz_installed():
                if prompt_install_graphviz():
                    if install_graphviz():
                        print("✓ Graphviz installed successfully!")
                        # Verify installation
                        if not check_graphviz_installed():
                            print("✗ Installation verification failed. PNG generation skipped.")
                            generate_png = False
                    else:
                        print("✗ Installation failed. PNG generation skipped.")
                        generate_png = False
                else:
                    print("\nSkipping PNG generation. Use --no-png to suppress this prompt.")
                    generate_png = False

            if generate_png:
                try:
                    print("\nGenerating PNG visualization...")
                    print("  Trying default API method...")
                    png_data = graph_structure.draw_mermaid_png()

                    with open(png_path, "wb") as f:
                        f.write(png_data)

                    print(f"\n✓ Graph visualization saved to: {png_path}")
                    print(f"  Size: {len(png_data):,} bytes")
                    generated_files["png"] = png_path

                    # Auto-open if requested
                    if auto_open:
                        try:
                            subprocess.run(["open", str(png_path)], check=False)
                            print(f"  Opened: {png_path}")
                        except Exception:
                            print(f"  View with: open {png_path}")

                except Exception as e:
                    error_msg = str(e)
                    print(f"\n✗ Failed to generate PNG: {error_msg}")

                    # Provide helpful suggestions based on error type
                    if "mermaid.ink" in error_msg and "400" in error_msg:
                        print("\n  The mermaid.ink API rejected the diagram (possibly due to complexity).")
                        print(f"  You can still view the diagram at: https://mermaid.live/")
                        print(f"  Mermaid file: {mermaid_path}")
                    elif "graphviz" in error_msg.lower() or "dot" in error_msg.lower():
                        print("  This may indicate a graphviz installation issue.")
                        print("  Install with: brew install graphviz (macOS)")
                    else:
                        print(f"  Unexpected error. You can still use the mermaid file at: {mermaid_path}")

                    # Generate ASCII fallback
                    print("\n  Generating ASCII fallback visualization...")
                    try:
                        ascii_graph = generate_ascii_graph(analysis)

                        # Save to file
                        with open(ascii_path, "w") as f:
                            f.write(ascii_graph)

                        print(f"✓ ASCII visualization saved to: {ascii_path}")
                        generated_files["ascii"] = ascii_path

                        # Display in terminal
                        print("\n" + "─" * 80)
                        print(ascii_graph)
                        print("─" * 80)

                    except Exception as ascii_error:
                        print(f"  ✗ Failed to generate ASCII fallback: {ascii_error}")

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

        # Generate ASCII if requested (or if it wasn't already generated as fallback)
        if generate_ascii and "ascii" not in generated_files:
            print("\nGenerating ASCII visualization...")
            try:
                ascii_graph = generate_ascii_graph(analysis)

                # Save to file
                with open(ascii_path, "w") as f:
                    f.write(ascii_graph)

                print(f"✓ ASCII visualization saved to: {ascii_path}")
                generated_files["ascii"] = ascii_path

                # Display in terminal
                print("\n" + "─" * 80)
                print(ascii_graph)
                print("─" * 80)

            except Exception as ascii_error:
                print(f"✗ Failed to generate ASCII visualization: {ascii_error}")

        return generated_files

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main entry point with argument parsing."""
    # Show help if no arguments provided
    if len(sys.argv) == 1:
        sys.argv.append("--help")

    parser = argparse.ArgumentParser(
        description="Visualize LangGraph StateGraph as PNG and Mermaid diagram",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Visualize a graph from your project (add src to Python path)
  uv run visualize_stategraph.py my_module:build_graph --python-path ./src

  # Multiple Python paths
  uv run visualize_stategraph.py my_module:build_graph --python-path ./src --python-path ./lib

  # Custom output name and directory
  uv run visualize_stategraph.py my_module:build_graph --output my_graph.png --output-dir ./diagrams

  # Just generate mermaid (no graphviz needed)
  uv run visualize_stategraph.py my_module:build_graph --python-path ./src --no-png

  # Don't auto-open the PNG
  uv run visualize_stategraph.py my_module:build_graph --python-path ./src --no-open

  # Generate ASCII art visualization
  uv run visualize_stategraph.py my_module:build_graph --python-path ./src --ascii

Note:
  - The graph_ref must point to a function that returns a StateGraph or CompiledStateGraph
  - StateGraph objects will be automatically compiled before visualization
  - Use --python-path to add directories containing your modules to sys.path
  - For PNG generation, graphviz must be installed (brew install graphviz on macOS)
        """,
    )

    parser.add_argument(
        "graph_ref",
        help="Import reference: 'module.path:function_name' (must return StateGraph or CompiledStateGraph)",
    )
    parser.add_argument(
        "--output",
        default="graph.png",
        help="Output filename (default: graph.png)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "--python-path",
        action="append",
        dest="python_paths",
        help="Add directory to Python import path (can be used multiple times)",
    )
    parser.add_argument(
        "--no-png",
        action="store_true",
        help="Skip PNG generation, only create mermaid diagram",
    )
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="Generate ASCII art visualization (always generated as fallback if PNG fails)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Don't automatically open PNG after generation",
    )

    args = parser.parse_args()

    visualize_stategraph(
        graph_ref=args.graph_ref,
        output_filename=args.output,
        output_dir=args.output_dir,
        generate_png=not args.no_png,
        generate_ascii=args.ascii,
        auto_open=not args.no_open,
        python_paths=args.python_paths,
    )


if __name__ == "__main__":
    main()
