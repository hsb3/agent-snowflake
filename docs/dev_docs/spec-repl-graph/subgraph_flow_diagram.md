# Stream Processor Subgraph Flow Diagram

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     STREAM PROCESSOR SUBGRAPH                        │
│                                                                      │
│  Input: stream_chunks (list of SSE events)                          │
│  Output: render_queue, pending_interrupt, usage                     │
└─────────────────────────────────────────────────────────────────────┘

START
  │
  ▼
┌──────────────┐
│ fetch_chunk  │  Get next chunk from list, increment index
└──────┬───────┘
       │
       ▼
   ╔═══════╗
   ║ Has   ║  Check if current_chunk exists
   ║ chunk?║
   ╚═══╤═══╝
       │
    ┌──┴──┐
    │     │
   NO    YES
    │     │
    ▼     ▼
  END  ┌──────────────┐
       │ parse_chunk  │  Prepare for routing
       └──────┬───────┘
              │
              ▼
         ╔════════╗
         ║ Event  ║  Route by event_type
         ║ type?  ║
         ╚════╤═══╝
              │
     ┌────────┼────────┬───────────┐
     │        │        │           │
  partial  complete  updates    skip
     │        │        │           │
     ▼        ▼        ▼           │
```

## Event-Specific Flows

### 1. messages/partial (Text Streaming)
```
┌────────────────┐
│ extract_text   │  Extract text delta from cumulative
└────────┬───────┘  Add to render_queue
         │          Update prev_text
         ▼
     ╔═══════╗
     ║ More  ║
     ║chunks?║
     ╚═══╤═══╝
         │
     ┌───┴───┐
     │       │
    YES     NO
     │       │
     │       ▼
     │      END
     │
     └──────► (loop back to fetch_chunk)
```

### 2. messages/complete (Tool Calls)
```
┌────────────────┐
│ extract_tools  │  Extract tool_calls array
└────────┬───────┘  Extract usage metadata
         │
         ▼
     ╔═════════╗
     ║  Tool   ║  Route by tool.name
     ║  name?  ║
     ╚═════╤═══╝
           │
    ┌──────┼──────┬────────┬───────┐
    │      │      │        │       │
 sql_db  Ask   generic   none   other
 _query  User             │
    │   Question          │
    │      │      │       │
    ▼      ▼      ▼       │
 ┌─────┐ ┌────┐ ┌─────┐  │
 │ SQL │ │Q&A │ │Gen. │  │
 │tool │ │tool│ │tool │  │
 └──┬──┘ └─┬──┘ └──┬──┘  │
    │      │       │      │
    └──────┴───────┴──────┘
           │
           ▼
       ╔═══════╗
       ║ More  ║
       ║chunks?║
       ╚═══╤═══╝
           │
       ┌───┴───┐
       │       │
      YES     NO
       │       │
       │       ▼
       │      END
       │
       └──────► (loop back to fetch_chunk)
```

### 3. updates (State Updates with Interrupt Detection)
```
┌──────────────────┐
│ process_updates  │  Add state update to render_queue
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ detect_interrupt │  Check for __interrupt__ key
└────────┬─────────┘  Create Interrupt object if found
         │
         ▼
     ╔═══════════╗
     ║Interrupt? ║
     ╚═════╤═════╝
           │
       ┌───┴────┐
       │        │
      YES      NO
       │        │
       ▼        │
      END       └──────► (loop back to fetch_chunk)
    (exit
   subgraph
immediately)
```

## Tool-Specific Rendering

### SQL Tools (sql_db_query, sql_db_schema)
```
┌──────────────────┐
│ render_sql_tool  │
└──────────────────┘
         │
         ▼
   Add to render_queue:
   {
     "type": "tool_call",
     "tool": {
       "name": "sql_db_query",
       "args": {...},
       "display": {
         "format": "sql",
         "query": "SELECT ..."
       }
     }
   }
```

### Question Tool (AskUserQuestion)
```
┌────────────────────────┐
│ render_question_tool   │
└────────────────────────┘
         │
         ▼
   Add to render_queue:
   {
     "type": "tool_call",
     "tool": {
       "name": "AskUserQuestion",
       "display": {
         "format": "question",
         "question": "...",
         "options": [...]
       }
     }
   }
```

### Generic Tool (Fallback)
```
┌────────────────────────┐
│ render_generic_tool    │
└────────────────────────┘
         │
         ▼
   Add to render_queue:
   {
     "type": "tool_call",
     "tool": {
       "name": "unknown_tool",
       "args": {...}
     }
   }
```

## Complete Example: Processing 3 Chunks

### Input
```python
stream_chunks = [
    ("messages/partial", [{"content": [{"type": "text", "text": "Hello"}]}]),
    ("messages/partial", [{"content": [{"type": "text", "text": "Hello, world"}]}]),
    ("messages/complete", [{
        "content": [{"type": "text", "text": "Hello, world"}],
        "tool_calls": [{"name": "sql_db_query", "args": {"query": "SELECT 1"}}],
        "usage_metadata": {"total_tokens": 50}
    }]),
]
```

### Execution Flow
```
1. fetch_chunk (index=0)
   ├─ current_chunk = ("messages/partial", [...])
   └─ chunk_index = 1

2. parse_chunk
   └─ (no transformation)

3. route_by_event_type
   └─ returns "messages/partial"

4. extract_text
   ├─ Extract "Hello" (full text, no prev)
   ├─ render_queue.append({"type": "text", "content": "Hello"})
   └─ prev_text = "Hello"

5. check_has_more
   └─ returns "more" (1 < 3)

6. fetch_chunk (index=1)
   ├─ current_chunk = ("messages/partial", [...])
   └─ chunk_index = 2

7. parse_chunk
   └─ (no transformation)

8. route_by_event_type
   └─ returns "messages/partial"

9. extract_text
   ├─ Extract ", world" (delta from "Hello")
   ├─ render_queue.append({"type": "text", "content": ", world"})
   └─ prev_text = "Hello, world"

10. check_has_more
    └─ returns "more" (2 < 3)

11. fetch_chunk (index=2)
    ├─ current_chunk = ("messages/complete", [...])
    └─ chunk_index = 3

12. parse_chunk
    └─ (no transformation)

13. route_by_event_type
    └─ returns "messages/complete"

14. extract_tools
    ├─ Extract tool_calls
    └─ Extract usage: {total_tokens: 50}

15. route_by_tool_name
    └─ returns "sql_db_query"

16. render_sql_tool
    └─ render_queue.append({"type": "tool_call", "tool": {...}})

17. check_has_more
    └─ returns "done" (3 >= 3)

18. END
```

### Output
```python
{
    "chunk_index": 3,
    "render_queue": [
        {"type": "text", "content": "Hello"},
        {"type": "text", "content": ", world"},
        {"type": "tool_call", "tool": {...}}
    ],
    "pending_interrupt": None,
    "usage": {"total_tokens": 50},
    "is_complete": True
}
```

## State Fields Throughout Execution

| Step | chunk_index | current_chunk | prev_text | render_queue | pending_interrupt | usage |
|------|-------------|---------------|-----------|--------------|-------------------|-------|
| Initial | 0 | None | "" | [] | None | None |
| After fetch 1 | 1 | ("messages/partial", ...) | "" | [] | None | None |
| After extract_text 1 | 1 | (...) | "Hello" | [text: "Hello"] | None | None |
| After fetch 2 | 2 | ("messages/partial", ...) | "Hello" | [...] | None | None |
| After extract_text 2 | 2 | (...) | "Hello, world" | [text: "Hello", text: ", world"] | None | None |
| After fetch 3 | 3 | ("messages/complete", ...) | "Hello, world" | [...] | None | None |
| After extract_tools | 3 | (...) | "Hello, world" | [...] | None | {total: 50} |
| After render_sql | 3 | (...) | "Hello, world" | [text, text, tool] | None | {total: 50} |
| Final | 3 | (...) | "Hello, world" | [text, text, tool] | None | {total: 50} |

## Node Execution Order

For the 3-chunk example above:
```
fetch_chunk → parse_chunk → route_by_event_type → extract_text → check_has_more →
fetch_chunk → parse_chunk → route_by_event_type → extract_text → check_has_more →
fetch_chunk → parse_chunk → route_by_event_type → extract_tools → route_by_tool_name →
render_sql_tool → check_has_more → END
```

Total node executions: 16 nodes for 3 chunks
Average: ~5 nodes per chunk

## Comparison: Single Node Execution

For the same 3-chunk example:
```
process_stream_node (1 execution, processes all 3 chunks internally)
```

This explains the performance difference: Fine-grained executes 16 nodes vs 1 for coarse-grained.
