# LangGraph SDK Reference

Quick reference for `langgraph-sdk` methods relevant to the REPL client.

## Setup

```python
from langgraph_sdk import get_client  # async
from langgraph_sdk import get_sync_client  # sync
from langgraph_sdk.schema import Command

client = get_client(url="http://localhost:2024")
```

---

## Client Namespaces

| Namespace | Purpose |
|-----------|---------|
| `client.assistants` | Manage agents |
| `client.threads` | Manage conversations |
| `client.runs` | Manage executions |
| `client.store` | Key-value storage |
| `client.crons` | Scheduled jobs |

---

## Assistants (Agents)

| Method | Use Case |
|--------|----------|
| `assistants.search()` | List all agents |
| `assistants.get(id)` | Get agent details |
| `assistants.get_schemas(id)` | Get config_schema, context_schema |
| `assistants.create(...)` | Create custom agent |
| `assistants.update(id, ...)` | Modify agent config |
| `assistants.delete(id)` | Remove agent |

---

## Threads

| Method | Use Case |
|--------|----------|
| `threads.create()` | Start new conversation |
| `threads.get(id)` | Check thread exists/status |
| `threads.search()` | List all threads |
| `threads.delete(id)` | Remove thread |
| `threads.update(id, metadata=...)` | Rename thread |
| **`threads.get_state(id)`** | Get current state + interrupts |
| **`threads.update_state(id, values)`** | Inject state |
| **`threads.get_history(id)`** | Get checkpoint history |
| **`threads.join_stream(id)`** | Reconnect to thread stream |

---

## Runs

| Method | Use Case |
|--------|----------|
| **`runs.stream(thread_id, assistant_id, input=...)`** | Send message, stream response |
| `runs.create(...)` | Background run (no stream) |
| `runs.wait(...)` | Sync execution |
| `runs.get(thread_id, run_id)` | Check run status |
| `runs.list(thread_id)` | Get run history |
| **`runs.cancel(thread_id, run_id)`** | Stop running agent |
| `runs.join(thread_id, run_id)` | Wait for background run |
| **`runs.join_stream(thread_id, run_id)`** | Reconnect to run stream |

---

## Error Recovery Methods

### Check Status

```python
# Check if thread is available
thread = await client.threads.get(thread_id)
# thread.status: "idle" | "busy" | "interrupted" | "error"

# Check if run is still going
run = await client.runs.get(thread_id, run_id)
# run.status: "pending" | "running" | "error" | "success" | "timeout" | "interrupted"
```

### Reconnect After Disconnect

```python
# Reconnect to a running stream
async for event in client.runs.join_stream(
    thread_id,
    run_id,
    last_event_id=last_received_event_id  # Resume from where we left off
):
    process(event)
```

### Cancel Stuck Run

```python
# If user presses Escape during HITL or agent is stuck
await client.runs.cancel(
    thread_id,
    run_id,
    action="interrupt"  # or "rollback"
)
```

### Resume After HITL

```python
from langgraph_sdk.schema import Command

# Accept tool call
await client.runs.stream(
    thread_id,
    assistant_id,
    command=Command(resume={"action": "approve"})
)

# Reject tool call
await client.runs.stream(
    thread_id,
    assistant_id,
    command=Command(resume={"action": "reject", "reason": "User declined"})
)

# Modify tool args
await client.runs.stream(
    thread_id,
    assistant_id,
    command=Command(resume={"action": "approve", "args": modified_args})
)
```

### Get Thread State (for debugging)

```python
state = await client.threads.get_state(thread_id)
# state.values - current state
# state.next - next nodes to execute
# state.interrupts - pending interrupts
# state.tasks - pending tasks
```

### Time Travel

```python
# Get history
history = await client.threads.get_history(thread_id, limit=20)

# Resume from a checkpoint
await client.runs.stream(
    thread_id,
    assistant_id,
    checkpoint_id=some_checkpoint_id,
    input=...
)
```

---

## Key Types

### ThreadStatus
```python
"idle" | "busy" | "interrupted" | "error"
```

### RunStatus
```python
"pending" | "running" | "error" | "success" | "timeout" | "interrupted"
```

### StreamMode
```python
"values" | "messages" | "updates" | "events" | "tasks" | "checkpoints" | "debug"
```

### Command (for HITL)
```python
Command(
    resume=...,     # Resume from interrupt
    update=...,     # Update state
    goto=...        # Jump to node
)
```

---

## References

- SDK Docs: https://langchain-ai.github.io/langgraph/cloud/reference/sdk/python_sdk_ref/
- PyPI: https://pypi.org/project/langgraph-sdk/
