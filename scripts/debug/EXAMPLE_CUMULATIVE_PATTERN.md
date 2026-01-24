# Example: Cumulative Text Delivery Pattern

This document shows actual captured data demonstrating the cumulative text delivery pattern in LangGraph HTTP "messages" stream mode.

## Raw Chunk Sequence

From actual test run capturing stream events:

```json
[
  {
    "chunk": 3,
    "text": null
  },
  {
    "chunk": 4,
    "text": "1. Starting"
  },
  {
    "chunk": 5,
    "text": "1. Starting the"
  },
  {
    "chunk": 6,
    "text": "1. Starting the count"
  },
  {
    "chunk": 7,
    "text": "1. Starting the count\n2."
  },
  {
    "chunk": 8,
    "text": "1. Starting the count\n2. Halfway"
  },
  {
    "chunk": 9,
    "text": "1. Starting the count\n2. Halfway through"
  },
  {
    "chunk": 10,
    "text": "1. Starting the count\n2. Halfway through\n3. Middle"
  }
]
```

## Visual Breakdown

### Chunk 4
**Full text:** `"1. Starting"`
**Length:** 11 chars
**Delta:** `"1. Starting"` (11 chars)

### Chunk 5
**Full text:** `"1. Starting the"`
**Length:** 15 chars
**Previous:** `"1. Starting"`
**Delta:** `" the"` (4 chars)

```
1. Starting
           ^^^^ new
```

### Chunk 6
**Full text:** `"1. Starting the count"`
**Length:** 21 chars
**Previous:** `"1. Starting the"`
**Delta:** `" count"` (6 chars)

```
1. Starting the
               ^^^^^^ new
```

### Chunk 7
**Full text:** `"1. Starting the count\n2."`
**Length:** 24 chars
**Previous:** `"1. Starting the count"`
**Delta:** `"\n2."` (3 chars)

```
1. Starting the count
                     ^^^^ new
```

### Chunk 8
**Full text:** `"1. Starting the count\n2. Halfway"`
**Length:** 32 chars
**Previous:** `"1. Starting the count\n2."`
**Delta:** `" Halfway"` (8 chars)

```
1. Starting the count
2.
  ^^^^^^^^ new
```

## Key Observation

Each chunk contains **ALL previous text plus new text**:

- Chunk 4: `[-------A-------]`
- Chunk 5: `[-------A-------][--B--]`
- Chunk 6: `[-------A-------][--B--][----C----]`
- Chunk 7: `[-------A-------][--B--][----C----][D]`
- Chunk 8: `[-------A-------][--B--][----C----][D][---E---]`

Without delta extraction, displaying each chunk would repeat all previous text.

## Delta Extraction Algorithm

```python
def extract_delta(current_text: str, previous_text: str) -> str:
    """
    Extract only the new text from a cumulative stream.

    Args:
        current_text: Full cumulative text from current chunk
        previous_text: Full cumulative text from previous chunk

    Returns:
        Only the new text (delta)
    """
    if not current_text:
        return ""

    if not previous_text:
        return current_text

    # Current should always start with previous in cumulative mode
    if current_text.startswith(previous_text):
        return current_text[len(previous_text):]
    else:
        # Edge case: text was replaced or reset
        # This might indicate a new message started
        return current_text
```

## Expected Display Output

With proper delta extraction, the user should see:

```
1. Starting the count
2. Halfway through
3. Middle of the sequence
4. Almost done
5. Finished!
```

Not:

```
1. Starting1. Starting the1. Starting the count1. Starting the count
2.1. Starting the count
2. Halfway...
```

## Implementation Notes

1. **Track previous text per message ID** - If message ID changes, reset previous text
2. **Handle empty/null chunks** - Chunk 3 had null text, skip these
3. **Flush output immediately** - Use `print(delta, end="", flush=True)` for real-time display
4. **Consider partial Unicode** - May need buffering for multi-byte characters at chunk boundaries
