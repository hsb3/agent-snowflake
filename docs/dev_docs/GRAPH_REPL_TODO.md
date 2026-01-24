# Graph-Based REPL (StateGraph) - Remaining Work

**Project:** `repl_client_graph` - LangGraph StateGraph-based Terminal REPL

**Status:** Phase 1 & 2 Complete, Phase 3 & Optimizations Needed

**Current State:** Functional with single-node stream processing. All commands working, dual streaming operational, HITL infrastructure in place.

---

## 🐛 Critical Bugs

- [ ] **Fix token tracking** - Session summary shows `Tokens Used: 0` despite usage_metadata in stream
  - Investigate usage extraction in `process_stream_node`
  - Verify flow through `update_session_node`
  - Check if usage_metadata structure matches expectations
  - Related: `src/repl_client_graph/graph/nodes/streaming.py:110-117`

- [ ] **Debug subgraph integration** - Subgraph PoC produces 0 render items when integrated
  - Works standalone with mock data ✅
  - Produces empty render_queue when called from main graph ❌
  - State transformation may be issue (`transform_to_subgraph_input/output`)
  - Chunk data structure differences between mock and live
  - Related: `src/repl_client_graph/graph/builder_subgraph.py`
  - Related: `src/repl_client_graph/graph/subgraphs/stream_processor.py`

## 🔨 Phase 2 Completion

- [ ] **Test HITL flow end-to-end**
  - Configure agent with `interrupt_before: ["*"]` or specific tools
  - Trigger tool call that requires approval
  - Test approval flow (y/n prompts)
  - Test rejection flow
  - Verify resume streaming works correctly
  - Related: `src/repl_client_graph/graph/nodes/hitl.py`

- [ ] **Fix state update verbosity** - Too many `[State Update: X keys changed]` messages
  - Add config flag: `REPL_SHOW_STATE_UPDATES=false` (default)
  - Only show in verbose/debug mode
  - Or make dimmer/less prominent
  - Related: `src/repl_client_graph/graph/nodes/rendering.py:77-84`

## ✨ Phase 3 Features

- [ ] **Enhanced input with prompt-toolkit**
  - Replace `input()` with `prompt_toolkit.prompt()`
  - Multi-line input support (Ctrl+Enter to send)
  - Input history (up/down arrows)
  - Command completion (Tab key)
  - Syntax highlighting in input
  - Related: `src/repl_client_graph/graph/nodes/input.py`

- [ ] **Command completion system**
  - Tab completion for commands (`/ag<Tab>` → `/agents`)
  - Tab completion for agent names
  - Tab completion for thread IDs
  - Context-aware completions

- [ ] **Status bar** (bottom line)
  - Show when streaming (typing indicator)
  - Live token count during responses
  - Connection status
  - Current agent/thread info
  - Hidden when idle

- [ ] **Session persistence and replay**
  - Save conversation history to `.repl/sessions/`
  - `/replay <session_id>` command
  - Checkpoint support for debugging
  - Export sessions to markdown

## 🎨 UX Improvements

- [ ] **Add command aliases**
  - `/a` → `/agents`
  - `/t` → `/threads`
  - `/n` → `/new`
  - `/i` → `/info`
  - `/c` → `/clear`
  - `/s` → `/session`

- [ ] **Auto-clear mode** (toggle)
  - `/auto-clear on` - Clear screen before each agent response
  - Helps with long conversations
  - Persistent preference in config

- [ ] **Improve table rendering**
  - Add pagination for large lists (>20 items)
  - Add sorting options
  - Color-code current items

- [ ] **Better error messages**
  - Friendly error formatting
  - Suggestions for common mistakes
  - Connection troubleshooting guide

## 🏗️ Subgraph Migration (When Ready)

- [ ] **Debug and fix subgraph integration**
  - Identify why render_queue stays empty
  - Fix state transformation issues
  - Verify chunk data structure handling
  - Test with live server data
  - Compare output byte-for-byte with single-node

- [ ] **Switch to subgraph in production**
  - Change `graph/__init__.py` to import `builder_subgraph`
  - Verify all features still work
  - Monitor performance impact
  - Update documentation

- [ ] **Add more tool-specific renderers**
  - `python_repl` → Code execution display
  - `search_tool` → Search results formatting
  - `file_operations` → File tree or diff display
  - `chart_generator` → ASCII charts or data tables
  - `web_scraper` → Formatted web content

## 🧪 Testing

- [ ] **Unit tests for StateGraph nodes**
  - Test each node function with mock state
  - Test conditional edge functions
  - Test state transformations
  - Related: `tests/repl_client_graph/`

- [ ] **Integration tests**
  - Test complete workflows (agent switch + query)
  - Test thread management flows
  - Test command sequences
  - Test error recovery

- [ ] **Performance benchmarking**
  - Compare single-node vs subgraph with real workloads
  - Measure latency impact on user experience
  - Profile graph execution
  - Identify bottlenecks

## 📖 Documentation

- [ ] **Update QUICKSTART_REPL_GRAPH.md**
  - Add Phase 2 command examples
  - Add workflow examples
  - Add troubleshooting section

- [ ] **Create HITL testing guide**
  - How to configure agents for interrupts
  - How to test approval flows
  - Example agent configurations

- [ ] **Command reference card**
  - Quick reference for all commands
  - Usage examples
  - Tips and tricks

- [ ] **Architecture decision records**
  - Why StateGraph over traditional loop
  - Why single-node vs subgraph (for now)
  - State management approach
  - Dependency injection via context vars

## 🔧 Technical Debt

- [ ] **Remove debug print statements**
  - Clean up `[DEBUG]` prints in production code
  - Use proper logging instead
  - Keep debug mode available via flag

- [ ] **Type checking cleanup**
  - Fix `type: ignore` comments
  - Add proper type annotations
  - Ensure `ty` passes without warnings

- [ ] **Code organization**
  - Consider splitting large command handler into modules
  - Refactor common patterns
  - Add more comprehensive docstrings

## 🎯 Nice to Have

- [ ] **/debug command** - Toggle verbose mode
  - Show state updates
  - Show full chunk details
  - Show graph execution traces

- [ ] **/export command** - Export conversation
  - Export to markdown
  - Export to JSON
  - Export with metadata

- [ ] **/config command** - Runtime configuration
  - Toggle auto-clear
  - Toggle state updates
  - Change prompt style

- [ ] **Graph visualization in REPL**
  - `/graph` command to show current workflow
  - Display execution path for last message
  - Show node timing

## 📊 Metrics & Observability

- [ ] **Add execution tracing**
  - Leverage StateGraph's built-in traces
  - Log node execution times
  - Track state transitions

- [ ] **Performance monitoring**
  - Track average response times
  - Monitor graph overhead
  - Alert on slow operations

- [ ] **Usage analytics** (optional)
  - Track command usage
  - Track agent preferences
  - Track common workflows

---

## Current Blockers

1. **Subgraph integration bug** - Needs debugging before migration
2. **Token tracking broken** - Usage metadata not flowing through
3. **HITL not fully tested** - Need agent with interrupt config

## Migration Path

1. ✅ Phase 1: Basic REPL with streaming (Complete)
2. ✅ Phase 2: Commands and HITL infrastructure (Complete)
3. 🔄 Fix bugs: Token tracking, state updates (In Progress)
4. ⏳ Phase 3: Enhanced input, completion, status bar (Planned)
5. ⏳ Subgraph migration: Fix integration, switch over (Blocked)

## References

- **Quickstart:** `docs/QUICKSTART_REPL_GRAPH.md`
- **Architecture:** `docs/dev_docs/repl_data_flow.md`
- **Subgraph PoC:** `docs/dev_docs/stream_subgraph_poc.md`
- **Phase 2 Report:** `docs/dev_docs/phase2_implementation_complete.md`
- **Main code:** `src/repl_client_graph/`

---

**Labels:** `enhancement`, `graph-based-repl`, `stategraph`, `phase-3`
**Priority:** Medium (functional but needs polish)
**Effort:** ~40-60 hours remaining
