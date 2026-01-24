# REPL Client v1 - Specification

Terminal REPL client for agent-snowflake LangGraph server.

## Active Specifications (Use These)

**Main repo root** (driving documents):
- `/repl_spec.json` - Requirements, features, phases, success criteria
- `/repl_components.jsonc` - Layer-by-layer component architecture (Layers 0-8)

## Supporting Research

**`research/`** (reference documentation):
- `LANGGRAPH_HTTP_STREAM_FORMAT.md` - LangGraph HTTP/SSE stream format analysis
- `REPL_FILE_STRUCTURE_ANALYSIS.md` - File structure comparison from 4 existing REPLs

**`scripts/debug/`** (experimental verification):
- Stream mode tests and captured data
- See `scripts/debug/FINDINGS_SUMMARY.md` for results

## Archived Documentation

**`archive/`** (outdated - replaced by JSON specs):
- `PRD_REPL_CLIENT.md` - Verbose prose PRD (replaced by repl_spec.json)
- `REPL_ARCHITECTURE.md` - Verbose architecture (replaced by repl_components.jsonc)
- `REPL_IMPLEMENTATION_CHECKLIST.md` - Task list (replaced by repl_spec.json phases)

## Build Order

Follow layer build order from `/repl_components.jsonc`:

**Phase 1 (Core)**: Layers 0, 1, 2, 3, 4, 6, 8
**Phase 2 (Features)**: Layers 5, 7
**Phase 3 (Polish)**: Enhanced input

See `repl_components.jsonc` → `build_order_summary` for file-level details.
