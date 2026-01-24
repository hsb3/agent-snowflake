# Debug Scripts - LangGraph HTTP Stream Analysis

This directory contains experimental scripts and analysis for understanding LangGraph HTTP streaming behavior.

## Files

### Scripts
- **`test_stream_modes.py`** - Main test script to analyze different stream modes
  - Tests: messages, updates, values, and dual modes
  - Captures raw SSE events
  - Analyzes text delivery patterns
  - Outputs JSON files with full event data

### Analysis Documents
- **`stream_analysis.md`** - Complete analysis and findings
  - Executive summary
  - Results for each stream mode
  - Key findings and comparisons
  - Recommendations for REPL implementation

- **`EXAMPLE_CUMULATIVE_PATTERN.md`** - Visual breakdown of cumulative text delivery
  - Real captured data examples
  - Step-by-step delta extraction demonstration
  - Implementation notes

- **`STREAM_MODE_COMPARISON.md`** - Side-by-side comparison
  - JSON structure examples for each mode
  - Quick reference table
  - Code examples for each mode

### Output Data
- **`output/`** - Directory containing captured JSON files
  - `stream_messages_*.json` - Messages mode captures
  - `stream_updates_*.json` - Updates mode captures
  - `stream_values_*.json` - Values mode captures
  - `stream_messages+updates_*.json` - Dual mode captures

## Quick Start

Run the test script:

```bash
# Ensure server is running on port 2024
uv run python scripts/debug/test_stream_modes.py
```

This will:
1. Create 4 new threads (one per test)
2. Send test prompt: "Count from 1 to 5, with a brief comment after each number."
3. Capture 20 chunks per stream mode
4. Analyze text delivery patterns
5. Save raw JSON to `output/` directory
6. Print analysis to console

## Key Findings

### Text Delivery Pattern: CUMULATIVE

In "messages" mode, text is delivered cumulatively:

```python
Chunk 4:  "1. Starting"
Chunk 5:  "1. Starting the"      # Contains previous + new
Chunk 6:  "1. Starting the count" # Contains all previous + new
```

### Delta Extraction Required

To display text incrementally without duplication:

```python
previous_text = ""

for chunk in stream:
    current_text = extract_text(chunk)
    delta = current_text[len(previous_text):]
    print(delta, end="", flush=True)
    previous_text = current_text
```

### Recommended Stream Mode

For REPL streaming display:
- Use `stream_mode="messages"`
- Listen for `messages/partial` events
- Extract text from: `data[0]['content'][0]['text']`
- Implement delta extraction

## Usage Examples

### Test Specific Mode

Modify the script to test only one mode:

```python
modes = ["messages"]  # Instead of all 4 modes

for mode in modes:
    thread_id = await get_or_create_thread()
    chunks = await test_stream_mode(mode, assistant_id, thread_id)
```

### Capture More Chunks

Increase capture limit:

```python
max_chunks = 50  # Default is 20
```

### Different Test Prompt

Change the test prompt:

```python
payload = {
    "assistant_id": assistant_id,
    "input": {
        "messages": [
            {
                "role": "user",
                "content": "Write a haiku about streaming data"
            }
        ]
    },
    "stream_mode": mode
}
```

## Inspecting Output Files

View captured JSON:

```bash
# Pretty-print full capture
cat output/stream_messages_*.json | jq '.'

# Show just text chunks
cat output/stream_messages_*.json | jq '[.[] | select(.event == "messages/partial") | {chunk: .chunk_num, text: .data[0].content[0].text}]'

# Count chunks by event type
cat output/stream_messages_*.json | jq '[group_by(.event) | .[] | {event: .[0].event, count: length}]'
```

## Environment

- **Server:** localhost:2024
- **Graph:** agent (from langgraph.json)
- **Python:** 3.12
- **Dependencies:** httpx, asyncio

## Notes

- Each test creates a new thread for clean results
- Tests run sequentially with 2-second delays
- Raw JSON files include timestamps in filenames
- Message IDs are tracked to detect new messages
- Delta extraction handles Unicode properly (each chunk is complete)

## Related Documentation

See also:
- `/Users/henry/Developer/_SANDBOX/agent-snowflake/LANGGRAPH_HTTP_STREAM_FORMAT.md` - Original stream format analysis
- Project root `README.md` - Main project documentation
