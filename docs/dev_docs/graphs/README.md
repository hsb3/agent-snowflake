# StateGraph Visualizations

This directory contains visualizations of StateGraph architectures.

## Quick Start

```bash
# Visualize the REPL graph
make visualize-graph

# Or use the script directly
uv run python scripts/visualize_stategraph.py repl_client_graph:build_repl_graph
```

## Visualizing Any StateGraph

The `visualize_stategraph.py` script is a **general-purpose utility** that works with any LangGraph StateGraph:

### Basic Usage

```bash
# Format: module.path:function_name
uv run python scripts/visualize_stategraph.py your_module:build_your_graph
```

### Examples

```bash
# REPL graph (default output: graph.png)
uv run python scripts/visualize_stategraph.py repl_client_graph:build_repl_graph

# Custom output filename
uv run python scripts/visualize_stategraph.py my_module:build_graph --output my_graph.png

# Custom output directory
uv run python scripts/visualize_stategraph.py my_module:build_graph --output-dir /tmp

# Only generate Mermaid (skip PNG)
uv run python scripts/visualize_stategraph.py my_module:build_graph --no-png

# Generate without auto-opening
uv run python scripts/visualize_stategraph.py my_module:build_graph --no-open
```

### Requirements

The script works with any function that returns a **compiled StateGraph**:

```python
# your_module.py
from langgraph.graph import StateGraph

def build_your_graph() -> StateGraph:
    graph = StateGraph(YourState)
    # ... add nodes and edges
    return graph.compile()  # Must return compiled graph
```

Then visualize:
```bash
uv run python scripts/visualize_stategraph.py your_module:build_your_graph
```

## Output Files

For each graph, the script generates:

1. **PNG file** - Visual diagram (requires `graphviz`)
2. **Mermaid file (.mmd)** - Text source for editing/sharing

## What the Script Analyzes

The visualization script provides:

### Graph Structure
- Total nodes and edges
- Entry/exit points
- Conditional vs direct edges

### Edge Analysis
- Routes between nodes
- Conditional routing logic
- Number of possible paths

### Routing Points
- Identifies decision nodes
- Lists all possible targets
- Shows routing conditions

### Example Output
```
================================================================================
GRAPH STRUCTURE
================================================================================
Entry point: __start__
Exit point: __end__

Conditional routing points:
  route_input routes to 4 targets: __end__, execute_command, get_input, send_message
  process_stream routes to 2 targets: handle_interrupt, update_session
  render_output routes to 2 targets: __end__, get_input

================================================================================
SUMMARY
================================================================================
Total nodes: 10
Total edges: 14
Conditional routing points: 3
Graph type: Directed Acyclic Graph (DAG)
```

## Dependencies

### Required
- `langgraph` (already installed)

### Optional (for PNG generation)
- `graphviz` - For better PNG rendering

**Install graphviz:**
```bash
# macOS
brew install graphviz

# Linux
sudo apt-get install graphviz graphviz-dev

# Then optionally install Python bindings
pip install pygraphviz
```

Without `graphviz`, the script will still generate the Mermaid diagram.

## Viewing Online

You can view the Mermaid diagram at [mermaid.live](https://mermaid.live/) by copying the contents of the `.mmd` file.

## Files in This Directory

Generated files (gitignored):
- `*.png` - PNG visualizations
- `*.mmd` - Mermaid diagram source

Tracked files:
- `README.md` - This file
- `.gitignore` - Ignore generated files

## Advanced Usage

### Programmatic Use

You can also use the visualization function in your own scripts:

```python
from scripts.visualize_stategraph import visualize_stategraph

files = visualize_stategraph(
    graph_ref="my_module:build_graph",
    output_filename="my_custom_graph.png",
    output_dir="/custom/path",
    generate_png=True,
    auto_open=False,
)

print(f"PNG: {files['png']}")
print(f"Mermaid: {files['mermaid']}")
```

### Analyzing Graph Structure

```python
from scripts.visualize_stategraph import import_graph_builder, analyze_graph_structure

# Build the graph
builder = import_graph_builder("my_module:build_graph")
graph = builder()
graph_structure = graph.get_graph()

# Analyze it
analysis = analyze_graph_structure(graph_structure)

print(f"Nodes: {analysis['node_count']}")
print(f"Edges: {analysis['edge_count']}")
print(f"Conditional routing points: {len(analysis['conditional_sources'])}")
```

## Troubleshooting

### Import Error
```
Failed to import module 'my_module'
```
**Fix:** Make sure your module is in the Python path. The script adds `src/` automatically.

### Graph Reference Format
```
Invalid graph reference format
```
**Fix:** Use format `module:function_name` (not `module.function_name`)

### PNG Generation Failed
```
Failed to generate PNG
```
**Fix:** Install graphviz (see Dependencies section above)

The Mermaid diagram will still be generated and can be viewed at mermaid.live.
