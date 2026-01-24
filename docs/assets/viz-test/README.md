# Graph Visualizations

Generated visualizations for agent_snowflake graphs using [visualize_stategraph.py](../../../scripts/shared/visualize_stategraph.py).

## Files

### agent_minimal
- **PNG**: [agent_minimal.png](agent_minimal.png) ✓
- **Mermaid**: [agent_minimal.mmd](agent_minimal.mmd) ✓
- **Nodes**: 6 (minimal middleware stack)

### agent_enhanced
- **PNG**: ⚠️ Failed to generate (mermaid.ink API error)
- **ASCII**: [agent_enhanced.txt](agent_enhanced.txt) ✓ (auto-generated as fallback)
- **Mermaid**: [agent_enhanced.mmd](agent_enhanced.mmd) ✓
- **Nodes**: 10 (full middleware stack)

## Viewing agent_enhanced

The agent_enhanced diagram is more complex and the mermaid.ink API returned a 400 error when trying to generate the PNG. This is likely due to escaped characters in node IDs (e.g., `\2e` for `.`, `\5b\5d` for `[]`).

**To view the diagram:**

1. **ASCII visualization (immediately viewable)** ✓:
   - View [agent_enhanced.txt](agent_enhanced.txt) directly in your terminal or editor
   - Auto-generated as fallback when PNG fails
   - Shows flow diagram and all node connections
   - Example: `cat docs/assets/viz-test/agent_enhanced.txt`

2. **Online viewer (best visual quality)**:
   - Go to [mermaid.live](https://mermaid.live/)
   - Copy the contents of [agent_enhanced.mmd](agent_enhanced.mmd)
   - Paste into the editor
   - The diagram will render in the preview pane

3. **VS Code**:
   - Install the "Markdown Preview Mermaid Support" extension
   - Open this README and view the diagram below

## agent_enhanced ASCII Visualization

<details>
<summary>Click to expand ASCII diagram (immediately viewable)</summary>

```
================================================================================
ASCII GRAPH VISUALIZATION
================================================================================

FLOW DIAGRAM:

  ┌─────────────────┐
  │   __start__     │
  └─────────────────┘
          │
          ▼
  ┌─────────────────┐
  │ model            │
  └─────────────────┘
          │
          ▼
  ┌─────────────────┐
  │ tools            │
  └─────────────────┘
          │
          ▼
  ┌─────────────────┐
  │ ModelCallLimitMiddleware.before_model│
  └─────────────────┘
          │
     ┌────┴────┐
     │
     ▼  to: SummarizationMiddleware.before
     │
     ▼  to: __end__

  ... (see agent_enhanced.txt for full diagram)

================================================================================
NODE CONNECTIONS
================================================================================

📍 __start__
   Outgoing to:
     → ModelCallLimitMiddleware.before_model

📍 model
   Incoming from:
     ← SummarizationMiddleware.before_model
   Outgoing to:
     → TodoListMiddleware.after_model

  ... (see agent_enhanced.txt for full connections)
```

Full ASCII diagram: [agent_enhanced.txt](agent_enhanced.txt)

</details>

## agent_enhanced Mermaid Diagram

<details>
<summary>Click to expand Mermaid diagram (requires viewer)</summary>

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	model(model)
	tools(tools)
	ModelCallLimitMiddleware\2ebefore_model(ModelCallLimitMiddleware.before_model)
	ModelCallLimitMiddleware\2eafter_model(ModelCallLimitMiddleware.after_model)
	ToolCallLimitMiddleware\2eafter_model(ToolCallLimitMiddleware.after_model)
	ToolCallLimitMiddleware\5bsql_db_query\5d\2eafter_model(ToolCallLimitMiddleware[sql_db_query].after_model)
	SummarizationMiddleware\2ebefore_model(SummarizationMiddleware.before_model)
	TodoListMiddleware\2eafter_model(TodoListMiddleware.after_model)
	__end__([<p>__end__</p>]):::last
	ModelCallLimitMiddleware\2eafter_model -.-> ModelCallLimitMiddleware\2ebefore_model;
	ModelCallLimitMiddleware\2eafter_model -.-> __end__;
	ModelCallLimitMiddleware\2eafter_model -.-> tools;
	ModelCallLimitMiddleware\2ebefore_model -.-> SummarizationMiddleware\2ebefore_model;
	ModelCallLimitMiddleware\2ebefore_model -.-> __end__;
	SummarizationMiddleware\2ebefore_model --> model;
	TodoListMiddleware\2eafter_model --> ToolCallLimitMiddleware\5bsql_db_query\5d\2eafter_model;
	ToolCallLimitMiddleware\2eafter_model -.-> ModelCallLimitMiddleware\2eafter_model;
	ToolCallLimitMiddleware\2eafter_model -.-> __end__;
	ToolCallLimitMiddleware\5bsql_db_query\5d\2eafter_model -.-> ToolCallLimitMiddleware\2eafter_model;
	ToolCallLimitMiddleware\5bsql_db_query\5d\2eafter_model -.-> __end__;
	__start__ --> ModelCallLimitMiddleware\2ebefore_model;
	model --> TodoListMiddleware\2eafter_model;
	tools -.-> ModelCallLimitMiddleware\2ebefore_model;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

</details>

## Troubleshooting

### Why did agent_enhanced PNG generation fail?

The mermaid.ink API (used by LangGraph's `draw_mermaid_png()`) returned a 400 error. This happens when:
- The diagram is too complex
- Node IDs contain special characters that need escaping
- The API service is having issues

### Alternative rendering methods:

1. **mermaid.ink API** (default): ✗ Failed with 400 error
2. **ASCII fallback** (auto-generated): ✓ Generated successfully
   - Immediately viewable in terminal
   - Shows flow diagram and node connections
   - No external dependencies required
3. **PYPPETEER** (local browser): ✗ Not viable (dependency conflicts with unmaintained package)
4. **Mermaid file**: ✓ Generated successfully

### Regenerating with fixes:

To regenerate with the updated script:

```bash
# Visualize both graphs (ASCII auto-generated on PNG failure)
uv run python scripts/shared/visualize_stategraph.py agent_snowflake:graph_enhanced \
  --python-path ./src --output agent_enhanced.png --output-dir docs/assets/viz-test --no-open

uv run python scripts/shared/visualize_stategraph.py agent_snowflake:graph_minimal \
  --python-path ./src --output agent_minimal.png --output-dir docs/assets/viz-test --no-open

# Generate ASCII visualization explicitly (even if PNG succeeds)
uv run python scripts/shared/visualize_stategraph.py agent_snowflake:graph_minimal \
  --python-path ./src --output agent_minimal.png --output-dir docs/assets/viz-test --ascii --no-open
```

## Graph Structure Analysis

### agent_minimal (6 nodes)
Simple middleware configuration with just model call limits:
- Entry: `__start__`
- Middleware: `ModelCallLimitMiddleware` (before/after)
- Core: `model`, `tools`
- Exit: `__end__`

### agent_enhanced (10 nodes)
Full middleware stack with multiple layers:
- Entry: `__start__`
- Middleware layers:
  - `ModelCallLimitMiddleware` (before/after)
  - `ToolCallLimitMiddleware` (global + sql_db_query specific)
  - `SummarizationMiddleware` (before)
  - `TodoListMiddleware` (after)
- Core: `model`, `tools`
- Exit: `__end__`
