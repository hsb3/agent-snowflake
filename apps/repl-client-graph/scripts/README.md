# REPL Client Graph Scripts

Test and debugging scripts for the `repl_client_graph` package (StateGraph-based REPL).

## Scripts

### Test Scripts

#### `test_subgraph_stream.py`
Comprehensive test script for the subgraph stream processing implementation.

**Purpose:**
- Tests subgraph version with mock streaming data
- Measures performance vs single-node approach
- Verifies output correctness

**Usage:**
```bash
uv run python scripts/repl_client_graph/test_subgraph_stream.py
```

**Tests:**
- Small messages (10 text chunks, no tools)
- Medium messages (20 text chunks, 5 tools)
- Large messages (50 text chunks, 10 tools)
- Messages with interrupts
- Individual chunk type handling

**Output:**
- Performance metrics for both approaches
- Render queue comparison
- Interrupt detection validation
- Detailed inspection of render items

---

#### `test_tool_rendering.py`
Tests tool-specific rendering for various SQL and interactive tools.

**Purpose:**
- Verify tool call rendering with syntax highlighting
- Test all tool types (SQL, schema, questions, generic)
- Validate render queue processing

**Usage:**
```bash
uv run python scripts/repl_client_graph/test_tool_rendering.py
```

**Tool Types Tested:**
- `sql_db_query` - SQL with syntax highlighting
- `sql_db_query_checker` - Query validation
- `sql_db_schema` - Schema information
- `sql_db_list_tables` - Table listing
- `AskUserQuestion` - Interactive prompts
- Generic fallback for unknown tools

---

#### `test_interrupt_detection.py`
Manual verification script for interrupt detection in `process_stream_node`.

**Purpose:**
- Verify `__interrupt__` detection in updates stream
- Test interrupt stops further chunk processing
- Validate empty interrupt list handling

**Usage:**
```bash
uv run python scripts/repl_client_graph/test_interrupt_detection.py
```

**Test Cases:**
1. Interrupt present - should detect and set `pending_interrupt`
2. No interrupt - should remain None
3. Interrupt stops processing - remaining chunks ignored
4. Empty interrupt list - treated as no interrupt

---

### Comparison Scripts

#### `compare_stream_approaches.py`
Side-by-side comparison of single-node vs subgraph stream processing approaches.

**Purpose:**
- Compare graph structure (nodes, edges, complexity)
- Estimate invocations per message
- Show architectural tradeoffs
- Generate visual flow diagrams

**Usage:**
```bash
uv run python scripts/repl_client_graph/compare_stream_approaches.py
```

**Output:**
1. Graph structure metrics (nodes, edges, cyclomatic complexity)
2. Invocation estimates for different message sizes
3. Architecture pros/cons for each approach
4. Recommendations for when to use each
5. Visual ASCII flow diagrams

**Scenarios Tested:**
- Small: 20 chunks, 2 tools
- Medium: 50 chunks, 5 tools
- Large: 100 chunks, 10 tools

---

## Architecture Context

These scripts support the **repl_client_graph** package, which implements a REPL client using LangGraph's StateGraph for control flow.

### Two Approaches

**Single-Node Approach** (Current):
- All stream processing in one `process_stream_node` function
- Fast: ~0.01ms per message
- Simple: ~300 lines, easy to understand
- File: `src/repl_client_graph/graph/nodes/streaming.py`

**Subgraph Approach** (PoC):
- Fine-grained nodes for each processing step
- Slower: ~30-45ms per message (still fast enough)
- Modular: ~450 lines across 7 files
- Better testability and observability
- File: `src/repl_client_graph/graph/nodes/streaming_subgraph.py`

### When to Use Each

Use **Single-Node** if:
- Tool count < 15
- Performance is critical
- Simple mental model preferred
- Current implementation is manageable

Use **Subgraph** if:
- Tool count > 20
- Need multi-step tool rendering
- Interactive tools with rich UI
- Detailed observability required

## Related Documentation

**Architecture:**
- `docs/dev_docs/stream_subgraph_poc.md` - Full PoC analysis
- `docs/dev_docs/ai_docs/ai_gen/stream_subgraph_poc_summary.md` - Executive summary
- `docs/dev_docs/ai_docs/ai_gen/subgraph_migration_complete.md` - Migration guide

**Code:**
- `src/repl_client_graph/graph/builder.py` - Single-node builder (active)
- `src/repl_client_graph/graph/builder_subgraph.py` - Subgraph builder (PoC)
- `src/repl_client_graph/graph/subgraphs/` - Subgraph node implementations

## Development Workflow

1. **Make changes** to streaming nodes or subgraph
2. **Run tests** to verify correctness:
   ```bash
   uv run python scripts/repl_client_graph/test_subgraph_stream.py
   uv run python scripts/repl_client_graph/test_tool_rendering.py
   ```
3. **Compare performance** if needed:
   ```bash
   uv run python scripts/repl_client_graph/compare_stream_approaches.py
   ```
4. **Check interrupt handling**:
   ```bash
   uv run python scripts/repl_client_graph/test_interrupt_detection.py
   ```

## Notes

- All scripts are **standalone** - no server required
- Use **mock data** for consistent, repeatable testing
- Scripts are **reference implementations** for how to use the graph nodes
- Keep scripts up-to-date when streaming logic changes
