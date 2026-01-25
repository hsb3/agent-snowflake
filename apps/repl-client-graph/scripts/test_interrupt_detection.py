#!/usr/bin/env python3
"""Manual verification script for interrupt detection in process_stream_node."""

import sys
sys.path.insert(0, "src")

from repl_client_graph.graph.nodes.streaming import process_stream_node
from repl_client_graph.graph.state import REPLState


def test_interrupt_detection():
    """Test that process_stream_node detects __interrupt__ correctly."""
    print("Testing interrupt detection in process_stream_node...")
    print("=" * 70)

    # Test 1: Detect interrupt
    print("\n1. Test with interrupt present:")
    state: REPLState = {
        "stream_chunks": [
            (
                "updates",
                {
                    "__interrupt__": [
                        {
                            "value": {
                                "tool": "execute_sql",
                                "args": {"query": "SELECT * FROM users"},
                            },
                            "when": "during",
                        }
                    ]
                },
            )
        ],
    }

    result = process_stream_node(state)

    if result["pending_interrupt"] is not None:
        print("  ✓ Interrupt detected")
        print(f"  ✓ Interrupt ID: {result['pending_interrupt']['id']}")
        print(f"  ✓ Tool name: {result['pending_interrupt']['value']['tool']}")
        print(f"  ✓ Tool args: {result['pending_interrupt']['value']['args']}")
    else:
        print("  ✗ FAIL: Interrupt not detected")
        return False

    # Test 2: No interrupt
    print("\n2. Test with no interrupt:")
    state2: REPLState = {
        "stream_chunks": [
            (
                "updates",
                {
                    "some_state_key": "some_value",
                },
            )
        ],
    }

    result2 = process_stream_node(state2)

    if result2["pending_interrupt"] is None:
        print("  ✓ No interrupt detected (as expected)")
    else:
        print("  ✗ FAIL: Interrupt detected when it shouldn't be")
        return False

    # Test 3: Interrupt stops processing
    print("\n3. Test that interrupt stops processing remaining chunks:")
    state3: REPLState = {
        "stream_chunks": [
            (
                "updates",
                {
                    "before_interrupt": "value1",
                },
            ),
            (
                "updates",
                {
                    "__interrupt__": [
                        {
                            "value": {
                                "tool": "dangerous_operation",
                                "args": {},
                            },
                            "when": "during",
                        }
                    ],
                },
            ),
            (
                "updates",
                {
                    "after_interrupt": "value3",
                },
            ),
        ],
    }

    result3 = process_stream_node(state3)

    if result3["pending_interrupt"] is not None:
        print("  ✓ Interrupt detected")

        # Check that updates after interrupt were not processed
        state_updates = [item for item in result3["render_queue"] if item["type"] == "state_update"]
        print(f"  ✓ Number of state updates processed: {len(state_updates)}")

        # Should only have the update before interrupt
        if len(state_updates) == 1:
            print("  ✓ Processing stopped after interrupt (only 1 update before interrupt)")
        else:
            print(f"  ✗ FAIL: Expected 1 state update, got {len(state_updates)}")
            return False
    else:
        print("  ✗ FAIL: Interrupt not detected")
        return False

    # Test 4: Empty interrupt list
    print("\n4. Test with empty interrupt list:")
    state4: REPLState = {
        "stream_chunks": [
            (
                "updates",
                {
                    "__interrupt__": [],
                },
            )
        ],
    }

    result4 = process_stream_node(state4)

    if result4["pending_interrupt"] is None:
        print("  ✓ No interrupt detected with empty list (as expected)")
    else:
        print("  ✗ FAIL: Interrupt detected with empty list")
        return False

    print("\n" + "=" * 70)
    print("All tests passed! Interrupt detection is working correctly.")
    return True


if __name__ == "__main__":
    success = test_interrupt_detection()
    sys.exit(0 if success else 1)
