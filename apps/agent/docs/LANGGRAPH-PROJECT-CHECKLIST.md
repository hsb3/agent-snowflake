# LangGraph Project Checklist

Questions to ask and things to verify for any project that implements LangChain agents / LangGraph graphs targeting the LangGraph API Server.

Derived from real issues found during code review of a production LangGraph agent.

---

## 1. Checkpointing: Who Owns It?

The LangGraph Dev Server and LangGraph Cloud both inject their own checkpointer at runtime. If your graph code also creates one (e.g., `InMemorySaver`), you get two competing checkpointers.

**Ask:**
- Does any `build_graph()` function create its own checkpointer?
- Is `InMemorySaver` used anywhere outside of standalone script testing?

**Rule:** Never pass `checkpointer=` when the graph will run under the LangGraph server. The server handles it. If you need a checkpointer for local script invocation, make that a separate code path, not the default.

**Exception:** If you're compiling a subgraph that needs its own checkpoint scope, that's intentional — but document why.

---

## 2. Context Schema: What Gets Exposed?

Any field in your `context_schema` dataclass becomes visible and configurable through the LangGraph API (`GET /assistants/{id}`) and Studio UI. This includes default values.

**Ask:**
- Are there passwords, API keys, or secrets in the context schema?
- Does `__repr__` dump sensitive fields? (It will get called in debug logs.)
- Does the connection URI contain embedded credentials?

**Rule:** Credentials must come from environment variables only, never from the context schema. Mask sensitive fields in `__repr__`. Redact credentials from URIs before logging.

---

## 3. Read-Only / Safety Enforcement: Prompt vs Code

Telling the LLM "don't run destructive queries" via the system prompt or tool description is not enforcement. The LLM can and will ignore it.

**Ask:**
- Is read-only mode enforced at the code level (pre-execution validation)?
- Is there a query validator that parses SQL before execution?
- Are `allowed_tables` restrictions enforced at query time, or only at schema-exploration time?
- Is there a default `LIMIT` to prevent full-table scans?

**Rule:** Any safety constraint that matters must be enforced programmatically. Use `sqlparse` or similar to validate queries. Wrap tools with pre-execution hooks. Prompt-level hints are belt-and-suspenders, not primary enforcement.

---

## 4. Middleware Ordering

Middleware wraps the agent execution. Order matters — inner middleware runs closest to the model/tool call, outer middleware runs first on the way in and last on the way out.

**Correct ordering (inner to outer):**
1. `ModelRetryMiddleware` — retry transient failures
2. `ModelFallbackMiddleware` — fall back to other models
3. `ModelCallLimitMiddleware` — enforce call limits
4. `ToolCallLimitMiddleware` — enforce tool limits
5. `HumanInTheLoopMiddleware` — approval flow
6. `SummarizationMiddleware` — context management
7. `TodoListMiddleware` — planning

**Common mistake:** Putting limits before retry/fallback. If the call limit fires first, the retry middleware never gets a chance to handle transient errors.

**Ask:**
- What order is middleware assembled?
- If a model call fails transiently, does it retry before counting against the limit?

---

## 5. System Prompt: Static vs Dynamic

A module-level `system_prompt = build_prompt(db_type="sqlite")` means every graph invocation gets the same prompt, regardless of runtime context.

**Ask:**
- Is the system prompt computed at import time or at graph-build time?
- Does it reflect the actual runtime context (database dialect, available tools, user role)?
- If the agent supports multiple database types, does it get the right dialect-specific instructions?

**Rule:** Build the prompt inside the graph builder function where you have access to the context. Detect the database type from the connection URI.

---

## 6. Model Configuration Consistency

Projects often have multiple places where model identifiers appear: config class defaults, `from_env()` fallbacks, fallback model lists, summarization model defaults.

**Ask:**
- Do the class-level defaults match the `from_env()` defaults?
- Are fallback model IDs current? (Model IDs go stale fast — `gpt-4o` is already outdated.)
- Is the summarization model the same vintage as the primary model?

**Rule:** Have one source of truth for model defaults. If `from_env()` is the real constructor, make class-level defaults match or remove them.

---

## 7. Code Duplication in Context Schemas

If you have multiple graph variants (e.g., basic, enhanced, minimal), you likely have multiple context schemas. These tend to duplicate fields and methods.

**Ask:**
- Does `EnhancedContextSchema` copy-paste fields from `ContextSchema`?
- Are `from_env()`, `from_runnable_config()`, and `to_dict()` duplicated?
- If you change a field in the base, do you have to change it in N other files?

**Rule:** Use dataclass inheritance. The enhanced schema should extend the base, adding only its new fields. Override methods to call `super()` for base field handling.

---

## 8. langgraph.json Configuration

This file defines which graphs the server exposes and how.

**Ask:**
- Does `python_version` match the actual runtime?
- Are all graph entry points valid and importable?
- Are there graph entries for variants that no longer exist?
- Is the `dependencies` list (pip packages) complete?

**Gotcha:** The server imports your graph module at startup. If the import fails (missing dependency, broken import chain), you get a cryptic error. Test with `python -c "from your_module.graph import build_graph"` locally first.

---

## 9. Tool Error Handling

When a tool fails (SQL syntax error, connection timeout, permission denied), the raw Python traceback goes back to the LLM. Long tracebacks waste tokens and confuse the model.

**Ask:**
- Are tool execution errors caught and formatted as helpful messages?
- Does the error message help the LLM self-correct? (e.g., "SQL syntax error near 'SELCT' — did you mean 'SELECT'?")
- Are transient errors (network, rate limits) retried at the tool level?

**Rule:** Wrap tool execution with error handling that returns structured, actionable error strings. Don't raise exceptions that produce full tracebacks.

---

## 10. HITL: Interrupt Configuration

Human-in-the-loop requires both middleware configuration AND the client sending the right stream mode.

**Ask:**
- Is `HumanInTheLoopMiddleware` added to the middleware stack?
- Does the client use `stream_mode=["messages", "updates"]`? (Interrupts only appear in the `updates` stream.)
- Is HITL disabled when `read_only=True`? (If the agent can't do anything dangerous, approval is friction.)
- Does the resume command use the correct format? (`Command(resume={"approve": True})`)

**Gotcha:** If the client only uses `stream_mode=["messages"]`, it will never see interrupt signals. The agent will appear to hang.

---

## 11. Test Coverage Gaps

Certain parts of LangGraph projects are chronically under-tested.

**Commonly untested:**
- Middleware stack composition (which middleware is active under which config)
- Context schema `from_runnable_config()` (the runtime config path)
- Graph compilation with different context configurations
- HITL interrupt/resume flow
- Error paths (invalid model, connection failure, malformed SQL)
- Dynamic prompt generation

**Commonly over-tested:**
- Basic graph compilation (a single happy-path test is enough)
- Static configuration values

**Rule:** Test conditional behavior. If middleware is only added when `enable_hitl=True`, test both `True` and `False`. If the prompt changes based on `db_type`, test both dialects.

---

## 12. Dependency Hygiene

LangChain/LangGraph projects accumulate dependencies fast.

**Ask:**
- Are all declared dependencies actually imported somewhere?
- Is `pydantic-settings` declared but unused (common when config uses plain dataclasses)?
- Are there experimental/alternative database drivers (duckdb, etc.) left over from exploration?
- Is the project using `langgraph-sdk` (client) vs `langgraph-cli` (server) correctly? They serve different purposes.

**Rule:** Grep for each dependency's import before declaring it. Unused deps slow installs and can cause version conflicts.

---

## 13. Streaming: Cumulative vs Delta Text

The LangGraph streaming API sends **cumulative text**, not deltas. Each chunk contains the full text so far.

**Ask:**
- Does the client extract deltas correctly? (`new_text[len(prev_text):]`)
- Is there a bug where the same text is displayed multiple times?
- Does the client handle both `messages` and `updates` stream types?

**Gotcha:** If you treat each chunk as a delta, you'll display the entire message again with every chunk.

---

## 14. Graph Variant Naming

`langgraph.json` maps graph names to entry points. The name is what clients use.

**Ask:**
- Are graph names stable? Renaming breaks existing client configurations.
- Do graph names match what users expect? (`agent` vs `agent_enhanced` vs `agent_minimal`)
- Is the default graph (the one Studio opens) the right one for most users?

---

## Quick Pre-Deploy Checklist

```
[ ] No secrets in context schema or logs
[ ] Read-only enforcement is code-level, not just prompt
[ ] No self-created checkpointer (server provides one)
[ ] Middleware in correct order (retry/fallback innermost)
[ ] System prompt is dynamic (correct dialect for actual database)
[ ] Model IDs are current
[ ] All declared dependencies are actually used
[ ] Integration tests exist for HITL flow
[ ] `python -c "from my_module.graph import build_graph"` succeeds
[ ] Client uses `stream_mode=["messages", "updates"]` for HITL
```
