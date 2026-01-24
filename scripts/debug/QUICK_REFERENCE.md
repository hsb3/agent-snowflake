# Quick Reference - LangGraph HTTP Streaming

## TL;DR

✓ Text is **CUMULATIVE** - must extract delta
✓ Use `stream_mode="messages"` for streaming
✓ Delta = `current_text[len(previous_text):]`

## Minimal Working Example

```python
import httpx
import json

def stream_response(thread_id: str, message: str):
    """Stream a response with delta extraction."""
    url = f"http://localhost:2024/threads/{thread_id}/runs/stream"
    payload = {
        "assistant_id": "agent",
        "input": {"messages": [{"role": "user", "content": message}]},
        "stream_mode": "messages"
    }

    previous_text = ""

    with httpx.stream("POST", url, json=payload) as response:
        for line in response.iter_lines():
            if line.startswith("event: "):
                event = line[7:].strip()
            elif line.startswith("data: "):
                data = json.loads(line[6:])

                if event == "messages/partial" and isinstance(data, list):
                    if len(data) > 0 and "content" in data[0]:
                        content = data[0]["content"]
                        if isinstance(content, list) and len(content) > 0:
                            current_text = content[0].get("text", "")

                            # Extract and display delta
                            delta = current_text[len(previous_text):]
                            if delta:
                                print(delta, end="", flush=True)

                            previous_text = current_text

    print()  # Final newline

# Usage
stream_response("your-thread-id", "Count from 1 to 5")
```

## Data Structure

### Messages Mode Chunk

```python
{
  "event": "messages/partial",
  "data": [
    {
      "content": [
        {
          "text": "Hello world",  # ← This is cumulative
          "type": "text",
          "index": 0
        }
      ],
      "type": "ai",
      "id": "msg-123"
    }
  ]
}
```

### Text Extraction Path

```python
text = data[0]["content"][0]["text"]
```

## Delta Extraction Algorithm

```python
def extract_delta(current: str, previous: str) -> str:
    """Extract only new text."""
    if not current:
        return ""
    if not previous:
        return current
    if current.startswith(previous):
        return current[len(previous):]
    return current  # Text was replaced/reset
```

## Stream Mode Cheat Sheet

```python
# Streaming (15-20+ chunks)
stream_mode = "messages"          # ← Use this for REPL

# Non-streaming (2-3 chunks)
stream_mode = "updates"           # State tracking
stream_mode = "values"            # Debugging

# Advanced
stream_mode = ["messages", "updates"]  # Both
```

## Common Patterns

### Pattern 1: Basic Streaming
```python
previous = ""
for chunk in stream:
    current = extract_text(chunk)
    delta = current[len(previous):]
    display(delta)
    previous = current
```

### Pattern 2: Multi-Message Tracking
```python
previous_by_id = {}

for chunk in stream:
    msg_id = extract_id(chunk)
    current = extract_text(chunk)
    previous = previous_by_id.get(msg_id, "")

    delta = current[len(previous):]
    display(delta)

    previous_by_id[msg_id] = current
```

### Pattern 3: Skip Empty Chunks
```python
for chunk in stream:
    current = extract_text(chunk)
    if not current:  # Skip null/empty
        continue

    delta = current[len(previous):]
    if delta:  # Only display if there's new text
        display(delta)

    previous = current
```

## Verification

Run test script:
```bash
uv run python scripts/debug/test_stream_modes.py
```

Check output:
```bash
cat scripts/debug/output/stream_messages_*.json | jq '.[3:6]'
```

## File Locations

- **Test script:** `scripts/debug/test_stream_modes.py`
- **Analysis:** `scripts/debug/stream_analysis.md`
- **Examples:** `scripts/debug/EXAMPLE_CUMULATIVE_PATTERN.md`
- **Comparison:** `scripts/debug/STREAM_MODE_COMPARISON.md`
- **Summary:** `scripts/debug/FINDINGS_SUMMARY.md`

## Key Facts

| Property | Value |
|----------|-------|
| Delivery pattern | Cumulative |
| Delta required? | Yes |
| Recommended mode | `"messages"` |
| Event type | `messages/partial` |
| Text path | `data[0]['content'][0]['text']` |
| Chunk frequency | 15-20+ per response |
| Unicode safe? | Yes |

## Gotchas

1. Don't display `current_text` directly - extract delta first
2. Reset `previous_text` when message ID changes
3. Skip chunks with null/empty text
4. Use `flush=True` for real-time display
5. Text path differs between modes (messages vs updates vs values)

## Testing Your Implementation

```python
# Expected: "Hello world"
# Chunks:   "Hel", "Hello", "Hello w", "Hello world"
# Deltas:   "Hel", "lo",    " w",      "orld"
# Display:  "Hello world"  ✓

# Without delta extraction:
# Display:  "HelHelloHello wHello world"  ✗
```
