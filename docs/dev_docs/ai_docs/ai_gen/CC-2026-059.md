---
doc_id: CC-2026-059
document_type: solution
document_title: "StateGraph Visualization Utility"
document_purpose: "General-purpose utility for visualizing any StateGraph as PNG/Mermaid"
date: 2026-01-24
status: complete
author: docs-cleanup-agent
version: 1.0
tags: [repl, stategraph, visualization, tooling, mermaid]
project: repl_client_graph
focus: graph-based-repl
---

# StateGraph Visualization Utility

## Overview

Created a **general-purpose utility** for visualizing any LangGraph StateGraph as PNG and Mermaid diagrams.

**Script:** `scripts/visualize_stategraph.py`

## Key Features

### ✅ Works with Any StateGraph
Not limited to REPL - can visualize **any** compiled StateGraph:
```bash
uv run python scripts/visualize_stategraph.py your_module:build_your_graph
```

### ✅ Flexible Output Options
```bash
# Custom filename
--output my_graph.png

# Custom directory
--output-dir /tmp

# Skip PNG (only Mermaid)
--no-png

# Don't auto-open
--no-open
```

### ✅ Comprehensive Analysis
The script analyzes and reports:
- Total nodes and edges
- Entry/exit points
- Conditional vs direct edges
- Routing decision points
- All possible paths

### ✅ Multiple Output Formats
1. **PNG** - Visual diagram (requires graphviz)
2. **Mermaid (.mmd)** - Text format for editing/sharing

### ✅ Programmatic API
Can be imported and used in other scripts:
```python
from scripts.visualize_stategraph import visualize_stategraph, analyze_graph_structure

files = visualize_stategraph(
    graph_ref="my_module:build_graph",
    output_filename="custom.png",
)
```

## Usage Examples

### 1. Visualize REPL Graph
```bash
# Quick way (via Makefile)
make visualize-graph

# Direct invocation
uv run python scripts/visualize_stategraph.py repl_client_graph:build_repl_graph
```

### 2. Visualize Custom Graph
```bash
# Your module structure
# src/my_app/graphs.py
from langgraph.graph import StateGraph

def build_workflow_graph() -> StateGraph:
    graph = StateGraph(MyState)
    # ... add nodes and edges
    return graph.compile()

# Visualize it
uv run python scripts/visualize_stategraph.py my_app.graphs:build_workflow_graph
```

### 3. Compare Multiple Graphs
```bash
# Generate multiple visualizations
uv run python scripts/visualize_stategraph.py module1:build_graph1 --output graph1.png --no-open
uv run python scripts/visualize_stategraph.py module2:build_graph2 --output graph2.png --no-open

# View them side by side
open docs/dev_docs/graphs/graph1.png docs/dev_docs/graphs/graph2.png
```

### 4. CI/CD Integration
```bash
# Generate diagram without opening (for automation)
uv run python scripts/visualize_stategraph.py app:build_graph --no-open --no-png

# Check if mermaid file was created
if [ -f docs/dev_docs/graphs/graph.mmd ]; then
    echo "✓ Graph visualization generated"
fi
```

## Output Example

```
Importing graph builder from: repl_client_graph:build_repl_graph
✓ Successfully imported module: repl_client_graph
✓ Successfully imported function: build_repl_graph
Building StateGraph...
✓ Successfully built graph
✓ Retrieved graph structure with 10 nodes

================================================================================
GRAPH NODES
================================================================================
  - __start__
  - get_input
  - route_input
  - execute_command
  - send_message
  - process_stream
  - handle_interrupt
  - update_session
  - render_output
  - __end__

================================================================================
GRAPH EDGES
================================================================================
  __start__ --> get_input
  get_input --> route_input
  route_input --[command]--> execute_command
  route_input --[message]--> send_message
  route_input --[empty]--> get_input
  route_input --[exit]--> __end__
  execute_command --> render_output
  send_message --> process_stream
  process_stream --[interrupt]--> handle_interrupt
  process_stream --[complete]--> update_session
  handle_interrupt --> process_stream
  update_session --> render_output
  render_output --[continue]--> get_input
  render_output --[exit]--> __end__

Total edges: 14
Conditional edges: 8
Direct edges: 6

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

Generating PNG visualization...
✓ Graph visualization saved to: docs/dev_docs/graphs/repl_stategraph.png
  Size: 51,063 bytes

Generating Mermaid diagram...
✓ Mermaid diagram saved to: docs/dev_docs/graphs/repl_stategraph.mmd
```

## Parameters

### Required
- `graph_ref` - Import reference in format `module.path:function_name`

### Optional
- `--output FILENAME` - Output filename (default: `graph.png`)
- `--output-dir DIR` - Output directory (default: `docs/dev_docs/graphs`)
- `--no-png` - Skip PNG, only generate Mermaid
- `--no-open` - Don't auto-open PNG after generation

## Requirements

### For Graph Builder Function
Must return a **compiled** StateGraph:
```python
def build_my_graph() -> StateGraph:
    graph = StateGraph(MyState)
    # ... configure graph
    return graph.compile()  # ← Must compile!
```

### Dependencies
**Required:**
- `langgraph` (already installed)

**Optional (for PNG):**
- `graphviz` system package
```bash
# macOS
brew install graphviz

# Linux
apt-get install graphviz
```

## Programmatic Usage

### Basic Visualization
```python
from scripts.visualize_stategraph import visualize_stategraph

files = visualize_stategraph(
    graph_ref="my_module:build_graph",
    output_filename="my_graph.png",
    output_dir="/custom/path",
    generate_png=True,
    auto_open=False,
)

print(f"Generated PNG: {files['png']}")
print(f"Generated Mermaid: {files['mermaid']}")
```

### Graph Analysis Only
```python
from scripts.visualize_stategraph import (
    import_graph_builder,
    analyze_graph_structure,
    print_graph_analysis,
)

# Import and build
builder = import_graph_builder("my_module:build_graph")
graph = builder()
structure = graph.get_graph()

# Analyze
analysis = analyze_graph_structure(structure)

# Print analysis
print_graph_analysis(analysis)

# Or access programmatically
print(f"Nodes: {analysis['node_count']}")
print(f"Edges: {analysis['edge_count']}")
print(f"Routing points: {len(analysis['conditional_sources'])}")

for source, targets in analysis['conditional_sources'].items():
    print(f"{source} → {targets}")
```

## Comparison to Original

### Before (REPL-specific)
```python
# scripts/visualize_repl_graph.py
from repl_client_graph import build_repl_graph

def save_graph_visualization():
    repl_graph = build_repl_graph()  # Hardcoded
    # ... REPL-specific analysis
```

**Limitations:**
- Only works with REPL graph
- Hardcoded import
- REPL-specific node role analysis

### After (General-purpose)
```python
# scripts/visualize_stategraph.py
def visualize_stategraph(graph_ref: str, ...):
    builder = import_graph_builder(graph_ref)  # Dynamic import
    graph = builder()
    # ... generic analysis
```

**Benefits:**
- ✅ Works with any StateGraph
- ✅ Command-line interface
- ✅ Configurable outputs
- ✅ Programmatic API
- ✅ Generic analysis (no hardcoded knowledge)

## Integration

### Makefile
```makefile
visualize-graph:
	uv run python scripts/visualize_stategraph.py \
		repl_client_graph:build_repl_graph \
		--output repl_stategraph.png
```

### Pre-commit Hook (Optional)
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Auto-generate graph visualization before commit
uv run python scripts/visualize_stategraph.py \
    my_module:build_graph \
    --output current_graph.png \
    --no-open

git add docs/dev_docs/graphs/current_graph.mmd
```

### Documentation Generation
```bash
# Generate diagrams for all graphs
for graph in workflow orchestration pipeline; do
    uv run python scripts/visualize_stategraph.py \
        "app:build_${graph}_graph" \
        --output "${graph}_graph.png" \
        --no-open
done
```

## Future Enhancements

Possible additions:
- [ ] Export to other formats (SVG, PDF)
- [ ] Interactive HTML output
- [ ] Diff two graphs
- [ ] Validate graph structure (detect cycles, unreachable nodes)
- [ ] Generate graph metrics (complexity, depth)
- [ ] Integration with graph testing frameworks

## Related Files

- **Script:** `scripts/visualize_stategraph.py`
- **Documentation:** `docs/dev_docs/graphs/README.md`
- **Makefile target:** `make visualize-graph`
- **Output directory:** `docs/dev_docs/graphs/`
