# REPL Client Usage Guide

Quick reference for using Layer 0 (Logging) and Layer 1 (HTTP Client).

## Layer 0: Logging

### Setup Logger

```python
from agent_snowflake.repl_client.core.logging import setup_client_logger, get_logger

# Setup main logger (do this once at startup)
setup_client_logger(".repl/client.log", level="INFO")

# Get module-specific logger
logger = get_logger("my_module")

# Use logger
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Log Levels

- **DEBUG**: Parsing details, chunk inspection
- **INFO**: Connection events, thread/agent switches
- **WARNING**: Unknown tools, fallback rendering, parse errors
- **ERROR**: Connection failures, critical errors

## Layer 1: HTTP Client

### Basic Setup

```python
import asyncio
from agent_snowflake.repl_client.core.client import LangGraphClient

async def main():
    # Create client
    client = LangGraphClient("http://localhost:2024", timeout=30)

    # Test connection
    connected = await client.connect()
    if not connected:
        print("Server not running")
        return

    # Your code here...

asyncio.run(main())
```

### List Agents

```python
# Get available agents
agents = await client.list_agents(limit=10)

for agent in agents:
    print(f"Agent: {agent['name']} ({agent['assistant_id']})")

# Get specific agent
agent = await client.get_agent(assistant_id)
```

### Thread Management

```python
# Create new thread
thread_id = await client.create_thread(metadata={"session": "my_session"})

# Get thread details
thread = await client.get_thread(thread_id)
print(f"Thread status: {thread['status']}")

# List threads
threads = await client.list_threads(limit=10)
```

### Stream Messages

```python
# Stream a message to agent
async for event_type, data in client.stream_message(
    thread_id=thread_id,
    message="What is 2 + 2?",
    assistant_id=assistant_id
):
    if event_type == "messages/partial":
        # Handle streaming text chunk
        print(f"Chunk: {data}")
    elif event_type == "messages/complete":
        # Handle complete message
        print(f"Complete: {data}")
    elif event_type == "metadata":
        # Handle metadata
        run_id = data.get("run_id")
```

### Resume After Interrupt (HITL)

```python
# Resume execution after tool approval
async for event_type, data in client.resume_after_interrupt(
    thread_id=thread_id,
    assistant_id=assistant_id,
    approved=True  # or False to reject
):
    # Handle events same as stream_message
    print(f"{event_type}: {data}")
```

## Common SSE Event Types

From LangGraph streaming API:

- **metadata**: Run metadata (run_id, attempt)
- **messages/metadata**: Message metadata (model info, checkpoint info)
- **messages/partial**: Partial message chunk (streaming text/tool calls)
- **messages/complete**: Complete message with final state

## Example: Complete Flow

```python
import asyncio
from agent_snowflake.repl_client.core.client import LangGraphClient
from agent_snowflake.repl_client.core.logging import setup_client_logger

async def chat_example():
    # Setup
    setup_client_logger(".repl/client.log", level="INFO")
    client = LangGraphClient("http://localhost:2024")

    # Connect
    if not await client.connect():
        print("Failed to connect")
        return

    # Get first agent
    agents = await client.list_agents(limit=1)
    if not agents:
        print("No agents available")
        return

    assistant_id = agents[0]["assistant_id"]

    # Create thread
    thread_id = await client.create_thread()

    # Send message and stream response
    print("User: Hello!")
    print("Agent: ", end="", flush=True)

    async for event_type, data in client.stream_message(
        thread_id=thread_id,
        message="Hello! Introduce yourself briefly.",
        assistant_id=assistant_id
    ):
        if event_type == "messages/partial":
            # Extract text from data and print
            # (In Layer 2, parser will do this)
            if data and len(data) > 0:
                content = data[0].get("content", [])
                if content and len(content) > 0:
                    text = content[0].get("text", "")
                    print(text, end="", flush=True)

    print()  # newline

asyncio.run(chat_example())
```

## Error Handling

```python
try:
    agents = await client.list_agents()
except Exception as e:
    logger.error(f"Failed to list agents: {e}")
    # Handle error
```

## Running Tests

```bash
# Run logging tests
uv run pytest tests/repl_client/core/test_logging.py -v

# Run client tests (unit tests only, no server needed)
uv run pytest tests/repl_client/core/test_client.py -v

# Run client tests with server (integration tests)
langgraph dev  # in separate terminal
uv run pytest tests/repl_client/core/test_client.py -v

# Run quick test script
langgraph dev  # in separate terminal
uv run python scripts/test_repl_client.py
```

## Next Steps

Layer 2 (Parsers) will handle:
- Parsing SSE events into typed structures
- Extracting text deltas from cumulative updates
- Detecting tool calls and interrupts
- Structured data models (ParsedChunk, ContentBlock, etc.)
