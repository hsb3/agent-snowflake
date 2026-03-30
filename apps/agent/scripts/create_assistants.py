"""Create assistant variants for testing different agent configurations.

Creates 5 assistants on the LangGraph Dev Server, each with a different
middleware/model configuration. Verifies each by sending a test message.

Usage:
    uv run python scripts/create_assistants.py [--server-url URL]
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv
from langgraph_sdk import get_client

load_dotenv()

DEFAULT_URL = f"http://localhost:{os.environ.get('LANGGRAPH_DEV_SERVER_PORT', '2024')}"
GRAPH_ID = "agent"
TEST_MESSAGE = "List the tables in this database."

# 5 assistant configurations to create
ASSISTANTS = [
    {
        "name": "baseline",
        "metadata": {"description": "Default config — all middleware enabled"},
        "config": {
            "configurable": {
                "model": "claude-haiku-4-5-20251001",
                "temperature": 0.0,
                "enable_hitl": False,
                "enable_summarization": True,
                "enable_todo": True,
                "enable_fallback": True,
                "retry_max_retries": 3,
                "model_call_run_limit": 5,
            }
        },
    },
    {
        "name": "minimal",
        "metadata": {"description": "No middleware — raw agent, fastest"},
        "config": {
            "configurable": {
                "model": "claude-haiku-4-5-20251001",
                "temperature": 0.0,
                "enable_hitl": False,
                "enable_summarization": False,
                "enable_todo": False,
                "enable_fallback": False,
                "retry_max_retries": 0,
                "model_call_thread_limit": 0,
                "model_call_run_limit": 0,
                "tool_call_thread_limit": 0,
                "tool_call_run_limit": 0,
                "sql_query_thread_limit": 0,
                "sql_query_run_limit": 0,
            }
        },
    },
    {
        "name": "strict-limits",
        "metadata": {"description": "Tight call limits — cost control testing"},
        "config": {
            "configurable": {
                "model": "claude-haiku-4-5-20251001",
                "temperature": 0.0,
                "enable_hitl": False,
                "enable_summarization": False,
                "enable_todo": False,
                "enable_fallback": False,
                "retry_max_retries": 1,
                "model_call_thread_limit": 3,
                "model_call_run_limit": 2,
                "tool_call_run_limit": 3,
                "sql_query_run_limit": 1,
                "model_call_exit_behavior": "end",
            }
        },
    },
    {
        "name": "creative",
        "metadata": {"description": "Higher temperature, OpenAI model"},
        "config": {
            "configurable": {
                "model": "gpt-4.1-mini",
                "temperature": 0.7,
                "enable_hitl": False,
                "enable_summarization": True,
                "enable_todo": False,
                "enable_fallback": False,
                "retry_max_retries": 2,
                "model_call_run_limit": 8,
            }
        },
    },
    {
        "name": "write-mode",
        "metadata": {"description": "Read-write with HITL approval required"},
        "config": {
            "configurable": {
                "model": "claude-haiku-4-5-20251001",
                "temperature": 0.0,
                "read_only": False,
                "enable_hitl": True,
                "hitl_allowed_decisions": "approve,edit,reject",
                "enable_summarization": True,
                "enable_todo": True,
                "enable_fallback": True,
                "retry_max_retries": 3,
                "model_call_run_limit": 5,
            }
        },
    },
]


async def create_assistants(server_url: str, verify: bool = True) -> None:
    """Create all assistant variants and optionally verify them."""
    client = get_client(url=server_url)

    # Check server health
    print(f"Connecting to {server_url}...")
    try:
        existing = await client.assistants.search(limit=1)
        print(f"Server OK — {len(existing)} existing assistant(s)\n")
    except Exception as e:
        print(f"Failed to connect: {e}")
        sys.exit(1)

    created = []

    for spec in ASSISTANTS:
        name = spec["name"]
        print(f"Creating '{name}'...")
        try:
            assistant = await client.assistants.create(
                graph_id=GRAPH_ID,
                name=name,
                config=spec["config"],
                metadata=spec["metadata"],
            )
            aid = assistant["assistant_id"]
            print(f"  -> {aid}")
            created.append({"name": name, "id": aid, "config": spec["config"]})
        except Exception as e:
            print(f"  FAILED: {e}")

    print(f"\nCreated {len(created)}/{len(ASSISTANTS)} assistants.")

    if not verify or not created:
        _print_summary(created)
        return

    # Verify each by sending a test message
    print(f"\nVerifying with: \"{TEST_MESSAGE}\"\n")

    for entry in created:
        name, aid = entry["name"], entry["id"]
        print(f"Testing '{name}'...", end=" ", flush=True)
        try:
            thread = await client.threads.create()
            response = await client.runs.wait(
                thread_id=thread["thread_id"],
                assistant_id=aid,
                input={"messages": [{"role": "user", "content": TEST_MESSAGE}]},
            )
            messages = response.get("messages", [])
            ai_msgs = [m for m in messages if m.get("type") == "ai"]
            if ai_msgs:
                text = ai_msgs[-1].get("content", "")
                preview = text[:80].replace("\n", " ") if isinstance(text, str) else str(text)[:80]
                print(f"OK — {preview}...")
            else:
                print("OK — (no AI message in response)")
        except Exception as e:
            print(f"FAILED — {e}")

    _print_summary(created)


def _print_summary(created: list[dict]) -> None:
    """Print final summary table."""
    print("\n" + "=" * 60)
    print("ASSISTANTS")
    print("=" * 60)
    for entry in created:
        config = entry["config"]["configurable"]
        model = config.get("model", "default")
        print(f"\n  {entry['name']}")
        print(f"    ID:    {entry['id']}")
        print(f"    Model: {model}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Create assistant variants for testing")
    parser.add_argument(
        "--server-url",
        default=DEFAULT_URL,
        help=f"LangGraph server URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip verification (don't send test messages)",
    )
    args = parser.parse_args()
    asyncio.run(create_assistants(args.server_url, verify=not args.no_verify))


if __name__ == "__main__":
    main()
