#!/usr/bin/env python3
"""
Test LangGraph HTTP stream modes to understand text delivery patterns.

This script tests different stream modes (messages, updates, values, dual) to determine
if text content is delivered as:
- Cumulative: Each chunk contains full text from start
- Delta: Each chunk contains only new text since last chunk
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import httpx


BASE_URL = "http://localhost:2024"
OUTPUT_DIR = Path(__file__).parent / "output"


async def get_or_create_assistant():
    """Get assistant ID from server (using default graph_id)."""
    # For LangGraph, we use the graph_id directly as the assistant_id
    # The default graph from langgraph.json is "agent"
    return "agent"


async def get_or_create_thread():
    """Get or create a thread for testing."""
    async with httpx.AsyncClient() as client:
        # Create new thread with empty json body
        response = await client.post(f"{BASE_URL}/threads", json={})
        response.raise_for_status()
        thread_data = response.json()
        return thread_data["thread_id"]


async def test_stream_mode(mode: str | list[str], assistant_id: str, thread_id: str):
    """Test a specific stream mode and capture chunks."""
    mode_name = mode if isinstance(mode, str) else "+".join(mode)
    print(f"\n{'='*80}")
    print(f"Testing stream mode: {mode_name}")
    print(f"{'='*80}\n")

    # Prepare request
    url = f"{BASE_URL}/threads/{thread_id}/runs/stream"
    payload = {
        "assistant_id": assistant_id,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": "Count from 1 to 5, with a brief comment after each number."
                }
            ]
        },
        "stream_mode": mode
    }

    chunks = []
    chunk_count = 0
    max_chunks = 20  # Capture first 20 chunks

    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()

            current_event = None
            async for line in response.aiter_lines():
                if not line.strip():
                    continue

                if line.startswith("event: "):
                    current_event = line[7:].strip()
                elif line.startswith("data: "):
                    data_str = line[6:].strip()

                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    chunk_count += 1

                    # Store chunk info
                    chunk_info = {
                        "chunk_num": chunk_count,
                        "event": current_event,
                        "data": data
                    }
                    chunks.append(chunk_info)

                    # Print chunk for first few
                    if chunk_count <= 10:
                        print(f"\n--- Chunk {chunk_count} (event: {current_event}) ---")
                        print(json.dumps(data, indent=2)[:500])  # First 500 chars

    # Save raw output
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"stream_{mode_name}_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(chunks, f, indent=2)

    print(f"\n✓ Saved {chunk_count} chunks to: {output_file}")

    # Analyze text patterns
    analyze_text_pattern(chunks, mode_name)

    return chunks


def analyze_text_pattern(chunks: list[dict], mode_name: str):
    """Analyze how text is delivered across chunks."""
    print(f"\n{'='*80}")
    print(f"ANALYSIS: {mode_name}")
    print(f"{'='*80}\n")

    # Look for text content in different locations
    text_chunks = []

    for chunk in chunks:
        data = chunk["data"]
        event = chunk["event"]

        # Check different possible locations for text
        text = None
        location = None

        # For messages mode - data is a list of message objects
        if isinstance(data, list) and len(data) > 0:
            msg = data[0]
            if "content" in msg:
                content = msg["content"]
                # Content can be a string or a list of content blocks
                if isinstance(content, str):
                    text = content
                    location = "data[0]['content'] (string)"
                elif isinstance(content, list) and len(content) > 0:
                    # Look for text blocks
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            text = block.get("text", "")
                            location = "data[0]['content'][0]['text']"
                            break

        # For updates/values mode - data is a dict with state
        if isinstance(data, dict):
            # Check for messages at root level
            if "messages" in data and isinstance(data["messages"], list) and len(data["messages"]) > 0:
                # Get last message (usually the assistant response)
                last_msg = data["messages"][-1]
                if "content" in last_msg:
                    content = last_msg["content"]
                    if isinstance(content, str):
                        text = content
                        location = "data['messages'][-1]['content'] (string)"
                    elif isinstance(content, list) and len(content) > 0:
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text = block.get("text", "")
                                location = "data['messages'][-1]['content'][0]['text']"
                                break

            # Check for model/agent nested structure
            if "model" in data and "messages" in data["model"]:
                model_msgs = data["model"]["messages"]
                if isinstance(model_msgs, list) and len(model_msgs) > 0:
                    last_msg = model_msgs[-1]
                    if "content" in last_msg:
                        content = last_msg["content"]
                        if isinstance(content, str):
                            text = content
                            location = "data['model']['messages'][-1]['content'] (string)"

        if text and isinstance(text, str) and len(text) > 0:
            text_chunks.append({
                "chunk_num": chunk["chunk_num"],
                "event": event,
                "location": location,
                "text": text,
                "text_length": len(text)
            })

    if not text_chunks:
        print("⚠ No text content found in chunks")
        return

    print(f"Found {len(text_chunks)} chunks with text content:\n")

    # Show first few text chunks
    for i, tc in enumerate(text_chunks[:5]):
        print(f"Chunk {tc['chunk_num']} (event: {tc['event']}):")
        print(f"  Location: {tc['location']}")
        print(f"  Length: {tc['text_length']}")
        preview = tc['text'][:100].replace('\n', ' ')
        print(f"  Preview: {preview}...")
        print()

    # Determine if cumulative or delta
    if len(text_chunks) >= 2:
        print("Text delivery pattern analysis:")

        is_cumulative = True
        is_delta = True

        for i in range(min(3, len(text_chunks) - 1)):
            curr_text = text_chunks[i]['text']
            next_text = text_chunks[i + 1]['text']

            if next_text.startswith(curr_text):
                pattern = "CUMULATIVE"
                is_delta = False
            else:
                pattern = "DELTA"
                is_cumulative = False

            print(f"  Chunks {i+1}→{i+2}: {pattern}")
            print(f"    Prev length: {len(curr_text)}")
            print(f"    Next length: {len(next_text)}")

            if pattern == "CUMULATIVE" and len(next_text) > len(curr_text):
                delta = next_text[len(curr_text):]
                print(f"    Delta: {repr(delta[:50])}...")
            print()

        # Final determination
        print("\nCONCLUSION:")
        if is_cumulative:
            print("  ✓ Text delivery is CUMULATIVE")
            print("  → Each chunk contains full text from the beginning")
            print("  → Need to extract delta by comparing with previous chunk")
        elif is_delta:
            print("  ✓ Text delivery is DELTA")
            print("  → Each chunk contains only new text")
            print("  → Can use text directly without delta extraction")
        else:
            print("  ⚠ Mixed pattern detected - needs further investigation")


async def main():
    """Run all stream mode tests."""
    print("LangGraph HTTP Stream Mode Testing")
    print("="*80)

    # Get assistant and thread
    print("\nInitializing...")
    assistant_id = await get_or_create_assistant()
    print(f"Assistant ID: {assistant_id}")

    # Test each mode with a fresh thread
    modes = [
        "messages",
        "updates",
        "values",
        ["messages", "updates"]
    ]

    results = {}

    for mode in modes:
        thread_id = await get_or_create_thread()
        print(f"Thread ID: {thread_id}")

        try:
            chunks = await test_stream_mode(mode, assistant_id, thread_id)
            mode_name = mode if isinstance(mode, str) else "+".join(mode)
            results[mode_name] = {
                "success": True,
                "chunk_count": len(chunks)
            }
        except Exception as e:
            mode_name = mode if isinstance(mode, str) else "+".join(mode)
            print(f"\n❌ Error testing {mode_name}: {e}")
            results[mode_name] = {
                "success": False,
                "error": str(e)
            }

        # Wait between tests
        await asyncio.sleep(2)

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}\n")

    for mode_name, result in results.items():
        status = "✓" if result["success"] else "❌"
        print(f"{status} {mode_name}: ", end="")
        if result["success"]:
            print(f"{result['chunk_count']} chunks captured")
        else:
            print(f"Failed - {result['error']}")

    print(f"\nOutput saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
