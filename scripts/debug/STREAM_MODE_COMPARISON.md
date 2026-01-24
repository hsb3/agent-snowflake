# Stream Mode Comparison: Side-by-Side

Quick reference showing the structure and content of each stream mode.

## Messages Mode - Streaming Text

**Purpose:** Real-time streaming of text as it's generated
**Event type:** `messages/partial`
**Chunks:** 15-20+ per response
**Text delivery:** Cumulative (requires delta extraction)

### Example Chunk (Chunk 6)

```json
{
  "chunk_num": 6,
  "event": "messages/partial",
  "data": [
    {
      "content": [
        {
          "text": "1. Starting the count",
          "type": "text",
          "index": 0
        }
      ],
      "additional_kwargs": {},
      "response_metadata": {
        "model_name": "claude-haiku-4-5-20251001",
        "model_provider": "anthropic"
      },
      "type": "ai",
      "name": null,
      "id": "lc_run--019bedb7-048a-7691-8b30-dc3419326984",
      "tool_calls": [],
      "invalid_tool_calls": [],
      "usage_metadata": null
    }
  ]
}
```

**Text extraction:**
```python
text = data[0]["content"][0]["text"]
```

**Use case:** REPL streaming display, chat interfaces

---

## Updates Mode - Node Completions

**Purpose:** Receive updates when graph nodes complete
**Event type:** `updates`
**Chunks:** 2 total (metadata + final)
**Text delivery:** Complete response only

### Example Chunk (Final Update)

```json
{
  "chunk_num": 2,
  "event": "updates",
  "data": {
    "model": {
      "messages": [
        {
          "content": "1. Starting the count\n2. Halfway through already\n3. Middle of the sequence\n4. Almost done\n5. Finished!",
          "additional_kwargs": {},
          "response_metadata": {
            "id": "msg_01KcRdAbYE7P5NrKxrQ8qadh",
            "model": "claude-haiku-4-5-20251001",
            "stop_reason": "end_turn",
            "stop_sequence": null,
            "usage": {
              "input_tokens": 123,
              "output_tokens": 45,
              "cache_creation_input_tokens": 0,
              "cache_read_input_tokens": 0
            }
          },
          "type": "ai",
          "name": null,
          "id": "abc123",
          "tool_calls": [],
          "invalid_tool_calls": [],
          "usage_metadata": {...}
        }
      ]
    }
  }
}
```

**Text extraction:**
```python
text = data["model"]["messages"][-1]["content"]
```

**Use case:** Monitoring node state, collecting final results, usage tracking

---

## Values Mode - Full State Snapshots

**Purpose:** Get complete state at each checkpoint
**Event type:** `values`
**Chunks:** 3 total (metadata + user message + assistant message)
**Text delivery:** Complete messages

### Example Chunk 2 (User Message)

```json
{
  "chunk_num": 2,
  "event": "values",
  "data": {
    "messages": [
      {
        "content": "Count from 1 to 5, with a brief comment after each number.",
        "additional_kwargs": {},
        "response_metadata": {},
        "type": "human",
        "name": null,
        "id": "a66e4b27-f49f-4edb-9688-4a1905231a57"
      }
    ]
  }
}
```

### Example Chunk 3 (Assistant Response)

```json
{
  "chunk_num": 3,
  "event": "values",
  "data": {
    "messages": [
      {
        "content": "Count from 1 to 5, with a brief comment after each number.",
        "type": "human",
        "id": "a66e4b27-..."
      },
      {
        "content": "1. Starting point - the beginning of our count\n2. Moving forward - halfway to the middle\n3. The middle - right at the center of our range\n4. Approaching the end - almost there\n5. Complete - we've reached our goal!",
        "type": "ai",
        "id": "b77f5c38-...",
        "response_metadata": {...}
      }
    ]
  }
}
```

**Text extraction:**
```python
text = data["messages"][-1]["content"]
```

**Use case:** State inspection, debugging, full conversation history

---

## Dual Mode - Combined Streaming

**Purpose:** Get both streaming updates AND state changes
**Event types:** `messages/partial` + `updates`
**Chunks:** 18+ total (mixed)
**Text delivery:** Cumulative for messages/partial, complete for updates

### Messages/Partial Events
Same as messages mode (see above)

### Updates Events
Same as updates mode (see above)

**Use case:** Advanced applications needing both real-time text and state tracking

---

## Quick Reference Table

| Feature | messages | updates | values | messages+updates |
|---------|----------|---------|---------|------------------|
| **Streaming?** | ✓ Yes | ✗ No | ✗ No | ✓ Yes |
| **Chunk count** | 15-20+ | 2 | 3 | 18+ |
| **Event types** | `messages/partial` | `updates` | `values` | Both |
| **Text format** | Cumulative | Complete | Complete | Mixed |
| **Delta needed?** | YES | No | No | YES (for messages) |
| **Update frequency** | Very high | Low | Low | High |
| **Best for** | Streaming UI | State tracking | Debugging | Advanced apps |
| **Latency** | Lowest | Highest | High | Low |
| **Bandwidth** | Higher | Lower | Lower | Highest |

---

## Code Examples

### Streaming with Messages Mode

```python
import httpx
import json

previous_text = ""

with httpx.stream(
    "POST",
    "http://localhost:2024/threads/{thread_id}/runs/stream",
    json={
        "assistant_id": "agent",
        "input": {"messages": [{"role": "user", "content": "Hello"}]},
        "stream_mode": "messages"
    }
) as response:
    for line in response.iter_lines():
        if line.startswith("event: "):
            event_type = line[7:].strip()
        elif line.startswith("data: "):
            data = json.loads(line[6:])

            if event_type == "messages/partial":
                # Extract text
                if isinstance(data, list) and len(data) > 0:
                    content = data[0].get("content", [])
                    if isinstance(content, list) and len(content) > 0:
                        current_text = content[0].get("text", "")

                        # Extract delta
                        delta = current_text[len(previous_text):]
                        if delta:
                            print(delta, end="", flush=True)

                        previous_text = current_text
```

### Non-Streaming with Updates Mode

```python
import httpx
import json

with httpx.stream(
    "POST",
    "http://localhost:2024/threads/{thread_id}/runs/stream",
    json={
        "assistant_id": "agent",
        "input": {"messages": [{"role": "user", "content": "Hello"}]},
        "stream_mode": "updates"
    }
) as response:
    for line in response.iter_lines():
        if line.startswith("event: "):
            event_type = line[7:].strip()
        elif line.startswith("data: "):
            data = json.loads(line[6:])

            if event_type == "updates":
                # Get complete response
                if "model" in data and "messages" in data["model"]:
                    messages = data["model"]["messages"]
                    if messages:
                        final_text = messages[-1]["content"]
                        print(final_text)
```

---

## Summary

- **Use "messages" mode** for streaming text display (REPL, chat UI)
- **Use "updates" mode** for state tracking without streaming
- **Use "values" mode** for debugging and state inspection
- **Use dual mode** only if you need both streaming and state updates
- **Always extract delta** when using messages mode to avoid duplicate text
