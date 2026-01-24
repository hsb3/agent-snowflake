# LangGraph HTTP Stream Mode Analysis

**Date:** 2026-01-23
**Server:** localhost:2024
**Graph:** agent (Snowflake agent)

## Executive Summary

Testing confirms that **text delivery is CUMULATIVE in "messages" mode** - each chunk contains the full text from the beginning, requiring delta extraction for incremental display. Other modes ("updates", "values") deliver complete responses in single chunks.

## Test Methodology

Created `/Users/henry/Developer/_SANDBOX/agent-snowflake/scripts/debug/test_stream_modes.py` to:
- Test 4 stream modes: "messages", "updates", "values", and dual ["messages", "updates"]
- Capture 20 chunks per test (or until stream completes)
- Analyze text delivery pattern (cumulative vs delta)
- Save raw JSON output for detailed inspection

**Test prompt:** "Count from 1 to 5, with a brief comment after each number."

## Results by Stream Mode

### 1. Messages Mode (`stream_mode="messages"`)

**Event type:** `messages/partial`

**Text location:** `data[0]['content'][0]['text']`

**Delivery pattern:** ✓ **CUMULATIVE**

**Example chunks:**
```
Chunk 4:  "1. Starting"                    (11 chars)
Chunk 5:  "1. Starting the"                (15 chars)
Chunk 6:  "1. Starting the count"          (21 chars)
Chunk 7:  "1. Starting the count\n2."      (24 chars)
Chunk 8:  "1. Starting the count\n2. Halfway" (32 chars)
```

**Delta extraction:**
- Chunk 5 delta = `" the"` (chars 11-15)
- Chunk 6 delta = `" count"` (chars 15-21)
- Chunk 7 delta = `"\n2."` (chars 21-24)

**Conclusion:**
- Each chunk contains the **full text from the beginning**
- To display incrementally, must compute: `delta = current_text[len(previous_text):]`
- This is the **recommended mode for streaming text** as it provides frequent updates

**Data structure:**
```json
{
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
      "type": "ai",
      "id": "lc_run--...",
      "response_metadata": {...}
    }
  ]
}
```

---

### 2. Updates Mode (`stream_mode="updates"`)

**Event type:** `updates`

**Chunks captured:** 2 (metadata + final update)

**Text location:** `data['model']['messages'][-1]['content']` (string)

**Delivery pattern:** **Single complete response**

**Example:**
```json
{
  "event": "updates",
  "data": {
    "model": {
      "messages": [
        {
          "content": "1. Starting the count\n2. Halfway through already\n3. Middle of the sequence\n4. Almost done\n5. Finished!",
          "type": "ai",
          "response_metadata": {
            "id": "msg_01...",
            "model": "claude-haiku-4-5-20251001",
            "stop_reason": "end_turn",
            "usage": {...}
          }
        }
      ]
    }
  }
}
```

**Conclusion:**
- No streaming - receives **complete response in single chunk**
- Only 2 events: metadata + final update with full text
- Not suitable for incremental display
- Useful for state updates but not text streaming

---

### 3. Values Mode (`stream_mode="values"`)

**Event type:** `values`

**Chunks captured:** 3 (metadata + user message + assistant message)

**Text location:** `data['messages'][-1]['content']` (string)

**Delivery pattern:** **Complete messages only**

**Example chunks:**
```
Chunk 2: User message (58 chars)
  "Count from 1 to 5, with a brief comment after each number."

Chunk 3: Assistant complete response (219 chars)
  "1. Starting point - the beginning of our count\n2. Moving forward..."
```

**Conclusion:**
- No streaming - receives **complete messages**
- Chunk 2 = user message
- Chunk 3 = complete assistant response
- Not suitable for incremental display
- Shows full state at each node completion

---

### 4. Dual Mode (`stream_mode=["messages", "updates"]`)

**Events:** Mix of `messages/partial` and `updates`

**Chunks captured:** 18 total

**Delivery pattern:**
- `messages/partial` events: CUMULATIVE (same as messages-only mode)
- `updates` events: Complete updates (same as updates-only mode)

**Conclusion:**
- Combines both stream types
- Can listen to `messages/partial` for incremental text
- Can listen to `updates` for node completions
- More data but provides flexibility

---

## Key Findings

### Text Delivery Comparison

| Mode | Streaming? | Text Pattern | Chunks | Delta Needed? |
|------|-----------|--------------|---------|---------------|
| **messages** | ✓ Yes | Cumulative | 15-20+ | **YES** |
| **updates** | ✗ No | Complete | 2 | No |
| **values** | ✗ No | Complete | 3 | No |
| **messages+updates** | ✓ Yes | Mixed | 18+ | YES (for messages) |

### Recommended Approach

**For streaming text display (REPL):**
1. Use `stream_mode="messages"`
2. Listen for `messages/partial` events
3. Extract text from: `data[0]['content'][0]['text']`
4. Compute delta: `new_text[len(previous_text):]`
5. Display delta incrementally

**Implementation pattern:**
```python
previous_text = ""

for event in stream:
    if event["event"] == "messages/partial":
        data = event["data"]
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

### Why Delta Extraction is Required

The cumulative text delivery in "messages" mode means:
- Chunk 1: "Hello"
- Chunk 2: "Hello world"  ← Contains "Hello" again
- Chunk 3: "Hello world!" ← Contains "Hello world" again

Without delta extraction, we would display:
```
HelloHello worldHello world!
```

With delta extraction, we display:
```
Hello world!
```

## Files Generated

All test outputs saved to: `/Users/henry/Developer/_SANDBOX/agent-snowflake/scripts/debug/output/`

**JSON files** (raw captured events):
- `stream_messages_TIMESTAMP.json` - Messages mode full capture
- `stream_updates_TIMESTAMP.json` - Updates mode full capture
- `stream_values_TIMESTAMP.json` - Values mode full capture
- `stream_messages+updates_TIMESTAMP.json` - Dual mode full capture

**Script:**
- `/Users/henry/Developer/_SANDBOX/agent-snowflake/scripts/debug/test_stream_modes.py` - Reusable test script

## Recommendations

1. **Use "messages" mode** for the REPL client streaming display
2. **Implement delta extraction** to avoid duplicate text
3. **Track previous text** for each message being streamed
4. **Reset previous text** when a new message starts (new message ID)
5. **Consider dual mode** if you need both streaming and state updates

## Next Steps

1. Update REPL client to use "messages" stream mode
2. Implement delta extraction in `StreamManager._extract_text_delta()`
3. Add tests to verify delta extraction works correctly
4. Consider adding option to switch between cumulative and delta display modes
