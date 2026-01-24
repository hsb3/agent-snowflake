# LangGraph HTTP Stream Analysis - Executive Summary

**Date:** 2026-01-23
**Objective:** Determine if text in LangGraph HTTP streams is cumulative or delta
**Result:** ✓ CUMULATIVE - Delta extraction required

---

## The Question

When streaming text from LangGraph HTTP API using `stream_mode="messages"`, is the text delivered as:
- **Cumulative:** Each chunk contains full text from start (requires delta extraction)
- **Delta:** Each chunk contains only new text (ready to display)

## The Answer

**CUMULATIVE** - Each chunk contains the complete text from the beginning.

### Proof

Actual captured chunks from test run:

```
Chunk 4:  "1. Starting"                    (11 chars)
Chunk 5:  "1. Starting the"                (15 chars)  ← contains "1. Starting" again
Chunk 6:  "1. Starting the count"          (21 chars)  ← contains all previous again
Chunk 7:  "1. Starting the count\n2."      (24 chars)  ← contains all previous again
```

Each chunk includes ALL previous text plus new text.

## What This Means

### Without Delta Extraction
```python
for chunk in stream:
    print(chunk.text)  # Wrong!

# Output:
# 1. Starting
# 1. Starting the
# 1. Starting the count
# ...
```

Displays duplicate text.

### With Delta Extraction
```python
previous = ""
for chunk in stream:
    delta = chunk.text[len(previous):]
    print(delta, end="", flush=True)
    previous = chunk.text

# Output:
# 1. Starting the count
# 2. Next number
# ...
```

Displays text correctly.

## Implementation Required

For the REPL client:

1. **Track previous text** for each message
2. **Extract delta** before displaying: `delta = current[len(previous):]`
3. **Reset on new message** when message ID changes
4. **Use "messages" mode** for streaming: `stream_mode="messages"`

## Test Evidence

- **Script:** `/Users/henry/Developer/_SANDBOX/agent-snowflake/scripts/debug/test_stream_modes.py`
- **Raw data:** `/Users/henry/Developer/_SANDBOX/agent-snowflake/scripts/debug/output/*.json`
- **Total tests:** 4 modes × 3 runs = 12 test captures
- **Chunks analyzed:** 100+ chunks across all tests
- **Pattern confirmed:** 100% cumulative in all "messages" mode tests

## Stream Mode Comparison

| Mode | Streaming? | Pattern | Use Case |
|------|-----------|---------|----------|
| **messages** | ✓ Yes (15-20+ chunks) | **Cumulative** ← | **REPL display** ← |
| updates | ✗ No (2 chunks) | Complete | State tracking |
| values | ✗ No (3 chunks) | Complete | Debugging |
| messages+updates | ✓ Yes (18+ chunks) | Mixed | Advanced |

## Recommendation

**Use `stream_mode="messages"` with delta extraction for REPL streaming.**

### Reference Implementation

```python
class StreamManager:
    def __init__(self):
        self._previous_text = {}  # message_id -> text

    def process_chunk(self, chunk):
        if chunk["event"] == "messages/partial":
            data = chunk["data"][0]
            message_id = data["id"]
            current_text = data["content"][0]["text"]

            # Get previous text for this message
            previous = self._previous_text.get(message_id, "")

            # Extract delta
            delta = current_text[len(previous):]

            # Update previous
            self._previous_text[message_id] = current_text

            return delta
```

## Files Created

### Documentation
1. `README.md` - Overview and usage guide
2. `stream_analysis.md` - Complete detailed analysis
3. `EXAMPLE_CUMULATIVE_PATTERN.md` - Visual examples with real data
4. `STREAM_MODE_COMPARISON.md` - Side-by-side mode comparison
5. `FINDINGS_SUMMARY.md` - This executive summary

### Code
1. `test_stream_modes.py` - Reusable test script

### Data
1. `output/*.json` - 12 raw capture files (100+ chunks total)

## Next Steps

1. ✓ Confirmed cumulative delivery pattern
2. → Implement delta extraction in REPL client
3. → Add tests for delta extraction logic
4. → Update REPL documentation

## Questions Answered

- ✓ Is text cumulative or delta? **Cumulative**
- ✓ Do we need delta extraction? **Yes**
- ✓ Which stream mode to use? **"messages"**
- ✓ Where is text located? **`data[0]['content'][0]['text']`**
- ✓ How frequent are updates? **15-20+ chunks per response**

## Additional Notes

- Text chunks are always complete (not mid-Unicode character)
- Empty/null content chunks should be skipped
- Message ID changes indicate a new message started
- Previous text should be reset when message ID changes
- Dual mode provides both streaming and state, but higher bandwidth
