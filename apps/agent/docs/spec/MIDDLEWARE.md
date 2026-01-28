# Middleware Configuration Guide

This document explains the middleware configurations available in `graph2.py` and how to use them effectively.

## Available Graph Variants

### 1. `graph` (Original - No Middleware)
**File:** `src/agent/graph.py`
**LangGraph name:** `agent`

Basic agent with no middleware. Use for understanding the core agent behavior.

```bash
make dev  # Start server
# In Studio, select "agent" graph
```

### 2. `graph_enhanced` 
**File:** `src/agent/graph2.py:build_graph_with_middleware`
**LangGraph name:** `agent_enhanced`

Full middleware stack for production deployments:

```python
middleware = [
    HumanInTheLoopMiddleware,      # Approve dangerous operations
    ModelCallLimitMiddleware,       # Prevent runaway costs
    ToolCallLimitMiddleware (2x),   # Limit expensive queries
    ModelRetryMiddleware,           # Handle network failures
    SummarizationMiddleware,        # Compress long conversations
    TodoListMiddleware,             # Enable task planning
    ModelFallbackMiddleware,        # Fallback to cheaper models
]
```

### 3. `graph_minimal` (Development)
**File:** `src/agent/graph2.py:build_graph_minimal_middleware`
**LangGraph name:** `agent_minimal`

Minimal middleware for fast iteration:

```python
middleware = [
    ModelCallLimitMiddleware,  # Prevent runaway
    ModelRetryMiddleware,      # Handle failures
]
```

## Middleware Components Explained

### 1. Human-in-the-Loop (Production Only)

**Purpose:** Require human approval before executing potentially dangerous SQL operations.

**Configuration:**
```python
HumanInTheLoopMiddleware(
    interrupt_on={
        "sql_db_query": {
            "allowed_decisions": ["approve", "edit", "reject"],
        },
        "sql_db_schema": False,  # Don't interrupt schema inspection
        "sql_db_list_tables": False,
    }
)
```

**When it triggers:**
- Only when `read_only=False` in context
- Before any `sql_db_query` tool execution
- User can approve, edit the query, or reject

**Requirements:**
- Needs `checkpointer=InMemorySaver()` (automatically configured)
- See [LangChain Human-in-the-Loop docs](https://python.langchain.com/docs/langchain/human-in-the-loop)

**Use case:** Production environments where you want to review queries before execution.

### 2. Model Call Limit

**Purpose:** Prevent runaway agents from making too many API calls.

**Configuration:**
```python
ModelCallLimitMiddleware(
    thread_limit=10,  # Max calls across entire conversation
    run_limit=5,      # Max calls per single invocation
    exit_behavior="end",  # Graceful termination
)
```

**Behavior:**
- `thread_limit`: Tracks calls across the entire conversation (thread)
- `run_limit`: Resets with each new user message
- `exit_behavior="end"`: Stops gracefully when limit reached
- `exit_behavior="error"`: Raises exception when limit reached

**Use case:** Cost control, preventing infinite loops.

### 3. Tool Call Limit

**Purpose:** Control expensive tool usage (SQL queries to Snowflake).

**Configuration:**
```python
# Global limit across all tools
ToolCallLimitMiddleware(
    thread_limit=20,
    run_limit=10,
    exit_behavior="continue",  # Block exceeded calls but continue
)

# Specific limit for sql_db_query (most expensive)
ToolCallLimitMiddleware(
    tool_name="sql_db_query",
    thread_limit=10,  # Max 10 queries per conversation
    run_limit=5,      # Max 5 queries per turn
    exit_behavior="continue",
)
```

**Behavior:**
- Can limit globally or per-tool
- `exit_behavior="continue"`: Returns error message but agent continues
- `exit_behavior="end"`: Stops execution (single-tool scenarios only)
- `exit_behavior="error"`: Raises exception

**Use case:** Preventing excessive Snowflake compute costs, rate limiting.

### 4. Model Retry

**Purpose:** Handle transient network failures with exponential backoff.

**Configuration:**
```python
ModelRetryMiddleware(
    max_retries=3,
    backoff_factor=2.0,  # Exponential: 1s, 2s, 4s
    initial_delay=1.0,
    max_delay=60.0,
    jitter=True,  # Add ±25% randomness
)
```

**Retry schedule:**
- Attempt 1: Immediate
- Attempt 2: Wait 1s
- Attempt 3: Wait 2s
- Attempt 4: Wait 4s

**Retries on:** All exceptions by default. Can customize with `retry_on` parameter.

**Use case:** Handling API rate limits, network blips, temporary outages.

### 5. Summarization

**Purpose:** Compress conversation history when approaching token limits.

**Configuration:**
```python
SummarizationMiddleware(
    model="gpt-4o-mini",  # Use cheaper model for summaries
    trigger=("tokens", 4000),
    keep=("messages", 20),  # Keep last 20 messages unmodified
)
```

**Behavior:**
- Monitors token count in conversation
- When exceeds 4000 tokens, summarizes older messages
- Preserves last 20 messages verbatim
- Summary inserted as single message

**Use case:** Long conversations exploring schemas, iterative query refinement.

### 6. Todo List

**Purpose:** Enable task planning and tracking for complex multi-step analysis.

**Configuration:**
```python
TodoListMiddleware()  # Uses default prompts
```

**What it does:**
- Adds `write_todos` tool to agent
- Provides system prompt encouraging task planning
- Agent can break down complex requests into subtasks
- Useful for: "Analyze sales trends, then segment by region, then forecast Q4"

**Use case:** Complex data analysis requiring multiple queries and transformations.

### 7. Model Fallback

**Purpose:** Automatically switch to backup models when primary fails.

**Configuration:**
```python
ModelFallbackMiddleware("gpt-4o-mini", "claude-3-5-sonnet-20241022")
```

**Behavior:**
- If primary model fails (rate limit, outage), tries first fallback
- If first fallback fails, tries second fallback
- Transparent to caller

**Fallback strategy in graph2.py:**
- Primary: `gpt-4o` → Fallbacks: `gpt-4o-mini`, `claude-3-5-sonnet`
- Primary: `claude-*` → Fallbacks: `gpt-4o`, `gpt-4o-mini`
- Other: Fallback to `gpt-4o-mini`

**Use case:** High availability, handling provider outages.

## Configuration

All middleware parameters are configurable via `EnhancedContextSchema`:

- **LangGraph Studio UI**: Configure when creating assistants (dropdowns, sliders, toggles)
- **Environment variables**: Set `AGENT_*` prefixed variables in `.env`
- **Runtime context**: Pass via `graph.invoke(..., context={...})`

**Complete configuration reference:** See [enhanced-context.md](dev_docs/ai_docs/ai_gen/enhanced-context.md) for all parameters and examples.

**Quick examples:**

```python
# Adjust limits via runtime context
context = {
    "model_call_thread_limit": 20,
    "sql_query_run_limit": 10,
    "enable_hitl": False,
}
result = graph_enhanced.invoke(messages, config={"configurable": context})

# Or via environment variables
# AGENT_MODEL_CALL_THREAD_LIMIT=20
# AGENT_SQL_QUERY_RUN_LIMIT=10
# AGENT_ENABLE_HITL=false
```

## Choosing the Right Graph

### Use `agent` (no middleware) when:
- Learning how the agent works
- Debugging core functionality
- Simplest possible setup

### Use `agent_minimal` when:
- Local development and testing
- Iterating quickly on prompts/tools
- Cost isn't a concern (local SQLite)

### Use `agent_enhanced` when:
- Production deployment
- Connecting to real Snowflake
- Need cost controls and safety
- Long-running conversations
- Complex multi-step analysis

## Testing Middleware

### Test Human-in-the-Loop
```bash
# Set read_only=false to enable HITL
AGENT_READ_ONLY=false uv run langgraph dev

# In Studio:
# 1. Select "agent_enhanced"
# 2. Send: "Delete all rows from CUSTOMER table"
# 3. Agent will interrupt and ask for approval
# 4. You can approve, edit, or reject
```

### Test Call Limits
```bash
# Start with aggressive limits
# Edit graph2.py: run_limit=2

# In Studio:
# 1. Send: "Show me all tables, their schemas, and sample data"
# 2. Agent will hit the 2-call limit
# 3. Should end gracefully with explanation
```

### Test Summarization
```bash
# Lower trigger threshold for testing
# Edit graph2.py: trigger=("tokens", 500)

# In Studio:
# 1. Have a long conversation about schemas
# 2. Check messages - should see summary inserted
# 3. Recent messages preserved verbatim
```

### Test Todo List
```bash
# In Studio with agent_enhanced:
# Send: "Analyze top 10 customers by revenue,
#        then show their order patterns,
#        then identify upsell opportunities"
#
# Agent should:
# 1. Call write_todos to plan steps
# 2. Execute queries sequentially
# 3. Track progress
```

## Customizing Middleware

### Adjust Limits

Edit `graph2.py`:

```python
# More aggressive cost control
ModelCallLimitMiddleware(
    thread_limit=5,   # Reduce from 10
    run_limit=3,      # Reduce from 5
)

# Less aggressive (allow more exploration)
ToolCallLimitMiddleware(
    tool_name="sql_db_query",
    thread_limit=50,  # Increase from 10
    run_limit=20,     # Increase from 5
)
```

### Add Custom Middleware

```python
from langchain.agents.middleware import PIIMiddleware

# Add PII detection for query results
middleware.append(
    PIIMiddleware(
        "email",
        strategy="redact",
        apply_to_input=False,
        apply_to_output=True,
        apply_to_tool_results=True,  # Redact in SQL results
    )
)
```

### Remove Middleware

Comment out any middleware you don't need:

```python
# middleware.append(TodoListMiddleware())  # Disable task planning
```

## Performance Considerations

### Latency Impact

Middleware adds minimal latency:
- **Model/Tool call limits**: ~1ms (just counting)
- **Retries**: Only on failures
- **Summarization**: Only when triggered (~2-3s for summary generation)
- **Human-in-the-loop**: User-dependent (blocks until approval)
- **Todo list**: Adds one tool, minimal overhead
- **Model fallback**: Only on failures

### Cost Impact

- **Summarization**: Uses `gpt-4o-mini` ($0.15/1M tokens) - minimal cost
- **Retries**: May retry failed calls (3x max)
- **Fallback**: May use different model pricing
- **Todo list**: No additional API calls

### Memory Impact

- **Checkpointer**: `InMemorySaver()` stores conversation in memory
  - For production, use `PostgresSaver` or other persistent store
  - See [LangGraph persistence docs](https://python.langchain.com/docs/langgraph/persistence)

## Deployment Patterns

### Pattern 1: Development → Staging → Production

```python
# Development: agent_minimal (fast iteration)
# Staging: agent_enhanced (test middleware)
# Production: agent_enhanced (full safety)
```

### Pattern 2: Per-User Configuration

```python
# Load middleware config from user settings
def build_custom_graph(config: RunnableConfig) -> CompiledStateGraph:
    context = ContextSchema.from_runnable_config(config)

    middleware = []
    if context.environment == "production":
        middleware.extend([...])  # Full stack
    else:
        middleware.extend([...])  # Minimal stack

    return create_agent(model, tools, middleware=middleware)
```

### Pattern 3: Feature Flags

```python
# Enable/disable middleware via environment
ENABLE_HITL = os.getenv("ENABLE_HITL", "true") == "true"
ENABLE_SUMMARIZATION = os.getenv("ENABLE_SUMMARIZATION", "false") == "true"

if ENABLE_HITL and not context.read_only:
    middleware.append(HumanInTheLoopMiddleware(...))
```

## Troubleshooting

### Issue: HITL not triggering
**Cause:** `read_only=true` or checkpointer not configured
**Fix:** Set `AGENT_READ_ONLY=false`, ensure `checkpointer=InMemorySaver()`

### Issue: "Tool call limit exceeded" too quickly
**Cause:** Limits too aggressive for use case
**Fix:** Increase `run_limit` or `thread_limit` in middleware config

### Issue: Summarization not activating
**Cause:** Token threshold too high
**Fix:** Lower `trigger=("tokens", 2000)` for testing

### Issue: Model fallback not working
**Cause:** All fallback models failing
**Fix:** Check API keys for all configured fallback models

## References

- [LangChain Middleware Documentation](https://python.langchain.com/docs/langchain/agents/middleware)
- [LangGraph Persistence](https://python.langchain.com/docs/langgraph/persistence)
- [Human-in-the-Loop Guide](https://python.langchain.com/docs/langchain/human-in-the-loop)
- [Model Profiles](https://python.langchain.com/docs/langchain/models#model-profiles)
