# LangGraph HTTP Stream Format Analysis

## API Endpoints (POST only)

```
POST /assistants/search        # List assistants
POST /threads                  # Create thread
POST /runs/stream              # Stream agent response (SSE)
```

## SSE Event Structure

All events follow Server-Sent Events format:
```
event: <event_type>
data: <json_payload>

event: <next_event>
data: <next_json>
```

## Event Types Observed

### 1. `metadata` (Run Start)
```json
{
  "run_id": "019bed1e-bf92-7311-914d-885e731a9499",
  "attempt": 1
}
```

### 2. `messages/metadata` (LangChain Run Context)
```json
{
  "lc_run--<id>": {
    "metadata": {
      "run_id": "...",
      "thread_id": "...",
      "graph_id": "agent",
      "assistant_id": "...",
      "langgraph_node": "model",
      "ls_provider": "anthropic",
      "ls_model_name": "claude-haiku-4-5",
      ...
    }
  }
}
```

### 3. `messages/partial` (Streaming Message Updates)
**Format**: Array with single AIMessage object
```json
[{
  "content": [
    {"text": "Hello! 👋 I'm...", "type": "text", "index": 0}
  ],
  "type": "ai",
  "id": "lc_run--019bed1e-c283-7782-84fc-5afedc7a072c",
  "tool_calls": [],
  "usage_metadata": null,
  "response_metadata": {
    "model_name": "claude-haiku-4-5-20251001",
    "model_provider": "anthropic"
  }
}]
```

**Key Observation**: Text is CUMULATIVE, not delta!
- Each chunk contains the full text so far
- To display incrementally: extract text, compare to previous, show diff

### 4. `messages/partial` with Tool Call
**Content blocks array includes tool_use block**:
```json
[{
  "content": [
    {"text": "I'll list all tables...", "type": "text", "index": 0},
    {
      "id": "toolu_01GYEoZ4PXE1pA8UgBbqi8z7",
      "input": {},
      "name": "sql_db_list_tables",
      "type": "tool_use",
      "index": 1,
      "partial_json": "{\"tool_input\": \"\"}"
    }
  ],
  "type": "ai",
  "tool_calls": [{
    "name": "sql_db_list_tables",
    "args": {"tool_input": ""},
    "id": "toolu_01GYEoZ4PXE1pA8UgBbqi8z7",
    "type": "tool_call"
  }],
  "response_metadata": {
    "stop_reason": "tool_use"
  },
  "usage_metadata": {
    "input_tokens": 1528,
    "output_tokens": 71,
    "total_tokens": 1599
  }
}]
```

**Tool Call Streaming**:
- `partial_json` field shows incremental JSON assembly
- `input` field has final parsed args when complete
- `tool_calls` array duplicates info from content blocks

### 5. `messages/complete` (Tool Result)
```json
[{
  "content": "Album, Artist, Customer, Employee, Genre, ...",
  "type": "tool",
  "name": "sql_db_list_tables",
  "id": "81b2fa66-89ca-46bf-ac5f-8f990f884401",
  "tool_call_id": "toolu_01GYEoZ4PXE1pA8UgBbqi8z7",
  "status": "success"
}]
```

## Content Block Types

### Text Block
```json
{
  "text": "Hello! ...",
  "type": "text",
  "index": 0
}
```

### Tool Use Block
```json
{
  "id": "toolu_01...",
  "input": {"query": "SELECT ..."},
  "name": "sql_db_query",
  "type": "tool_use",
  "index": 1,
  "partial_json": "{\"query\": \"SELECT ...\"}"
}
```

## Message Types

### AIMessage
```json
{
  "type": "ai",
  "content": [<content_blocks>],
  "tool_calls": [<tool_call_objects>],
  "usage_metadata": {
    "input_tokens": 1528,
    "output_tokens": 71,
    "total_tokens": 1599
  }
}
```

### ToolMessage
```json
{
  "type": "tool",
  "content": "<tool_result_string>",
  "name": "sql_db_query",
  "tool_call_id": "toolu_01...",
  "status": "success"
}
```

### HumanMessage (in input)
```json
{
  "role": "user",
  "content": "what tables are available?"
}
```

## Streaming Patterns

### Pattern 1: Text Streaming
```
messages/partial: content=[{text: "Hello"}]
messages/partial: content=[{text: "Hello!"}]
messages/partial: content=[{text: "Hello! 👋"}]
...
```
**Each chunk contains full text so far.**

### Pattern 2: Tool Call Streaming
```
messages/partial: content=[{text: "..."}, {tool_use, partial_json: ""}]
messages/partial: content=[{text: "..."}, {tool_use, partial_json: "{\""}]
messages/partial: content=[{text: "..."}, {tool_use, partial_json: "{\"query\""}]
messages/partial: content=[{text: "..."}, {tool_use, partial_json: "{\"query\": \"SELECT"}]
messages/partial: content=[{text: "..."}, {tool_use, input: {...}, stop_reason: "tool_use"}]
```
**Final chunk has `stop_reason: "tool_use"` and complete `input`.**

### Pattern 3: Tool Execution & Response
```
messages/partial: AIMessage with tool_calls + stop_reason="tool_use"
  (execution happens on server)
messages/complete: ToolMessage with result
messages/partial: New AIMessage with response to tool result
```

## What We Need to Parse

### Layer 2: Parsers

**Key Functions**:

1. **parse_sse_line(line: str) -> tuple[str, str] | None**
   - Extract `event:` and `data:` from SSE format
   - Returns `(event_type, json_string)` or None

2. **extract_delta_text(prev_text: str, curr_text: str) -> str**
   - Compare cumulative texts, return new portion
   - For incremental display

3. **parse_message_chunk(data: dict) -> ParsedChunk**
   - Extract message type, content blocks, metadata
   - Detect tool calls, usage, stop_reason

4. **extract_content_blocks(message: dict) -> list[ContentBlock]**
   - Parse content array into structured blocks
   - Handle text, tool_use, tool_result types

5. **detect_interrupt(chunk: dict) -> bool**
   - Check for HITL interrupt signals
   - Look for `__interrupt__` or specific event types

**Data Structures**:

```python
@dataclass
class ParsedChunk:
    event_type: str                    # "messages/partial", "messages/complete", etc.
    message_type: str                  # "ai", "tool", "human"
    message_id: str
    content_blocks: list[ContentBlock]
    tool_calls: list[dict] | None
    usage: dict | None
    stop_reason: str | None
    metadata: dict

@dataclass
class ContentBlock:
    type: str                          # "text", "tool_use", "tool_result"
    text: str | None = None            # For text blocks
    tool_name: str | None = None       # For tool blocks
    tool_id: str | None = None
    tool_input: dict | None = None
    tool_output: str | None = None
    index: int = 0
```

## Critical Insights

1. **Cumulative Text**: Don't append chunks - extract delta from cumulative
2. **Content Blocks**: Messages contain array of typed blocks (text, tool_use)
3. **Tool Calls Duplicated**: In both `content[]` and `tool_calls[]` arrays
4. **Stop Reason**: `"tool_use"` indicates tool call complete, execution pending
5. **Usage Metadata**: Only in final chunk of each message
6. **No Explicit End Event**: Stream just stops after final `messages/partial`

## Next: Lock Down Parser Interface

Based on this, here's what Layer 2 needs:

```python
# core/parsers.py

def parse_sse_line(line: str) -> tuple[str, str] | None:
    """Parse SSE 'event:' or 'data:' line."""

def extract_text_delta(prev: str, curr: str) -> str:
    """Get new text from cumulative update."""

def parse_chunk(event_type: str, data: dict) -> ParsedChunk:
    """Parse SSE event into structured chunk."""

def extract_content_blocks(content: list[dict]) -> list[ContentBlock]:
    """Parse content array into typed blocks."""
```

Ready to lock this in?
