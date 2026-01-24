"""Example: Integrating the stream processor subgraph.

This file demonstrates how to use the fine-grained stream processor subgraph
in the main REPL graph as an alternative to the coarse-grained single-node approach.
"""

from langgraph.graph import END, StateGraph

from repl_client_graph.graph.state import REPLState
from repl_client_graph.graph.subgraphs import build_stream_processor_subgraph


def build_repl_graph_with_subgraph() -> StateGraph:
    """Build REPL graph using stream processor subgraph.

    This is an alternative builder that replaces process_stream_node
    with the fine-grained stream_processor subgraph.

    Returns:
        Compiled StateGraph with subgraph integration
    """
    from repl_client_graph.graph.nodes import (
        check_should_exit,
        execute_command_node,
        get_input_node,
        handle_interrupt_node,
        render_output_node,
        route_decision,
        route_input_node,
        send_message_node,
        update_session_node,
    )

    graph = StateGraph(REPLState)  # type: ignore[arg-type]

    # Build stream processor subgraph
    stream_processor = build_stream_processor_subgraph()

    # Add nodes - using subgraph for stream processing
    graph.add_node("get_input", get_input_node)
    graph.add_node("route_input", route_input_node)
    graph.add_node("execute_command", execute_command_node)
    graph.add_node("send_message", send_message_node)

    # Use subgraph instead of process_stream_node
    graph.add_node("process_stream", stream_processor)

    graph.add_node("handle_interrupt", handle_interrupt_node)
    graph.add_node("update_session", update_session_node)
    graph.add_node("render_output", render_output_node)

    # Entry point
    graph.set_entry_point("get_input")

    # Flow (same as coarse-grained version)
    graph.add_edge("get_input", "route_input")

    graph.add_conditional_edges(
        "route_input",
        route_decision,
        {
            "command": "execute_command",
            "message": "send_message",
            "empty": "get_input",
            "exit": END,
        },
    )

    graph.add_edge("execute_command", "render_output")
    graph.add_edge("send_message", "process_stream")

    # After stream processing, check for interrupt
    def check_for_interrupt(state: REPLState) -> str:
        return "interrupt" if state.get("pending_interrupt") else "complete"

    graph.add_conditional_edges(
        "process_stream",
        check_for_interrupt,
        {
            "interrupt": "handle_interrupt",
            "complete": "update_session",
        },
    )

    graph.add_edge("handle_interrupt", "process_stream")
    graph.add_edge("update_session", "render_output")

    graph.add_conditional_edges(
        "render_output",
        check_should_exit,
        {
            "continue": "get_input",
            "exit": END,
        },
    )

    return graph.compile()


# Example usage
if __name__ == "__main__":
    # Build graph with subgraph
    graph = build_repl_graph_with_subgraph()

    # Example state with streaming chunks
    test_state = {
        "user_input": "Tell me a joke",
        "input_type": "message",
        "current_thread_id": "thread_123",
        "current_assistant_id": "asst_abc",
        "stream_chunks": [
            # Partial text chunks
            ("messages/partial", [
                {
                    "id": "msg_1",
                    "type": "ai",
                    "content": [{"type": "text", "text": "Why did"}]
                }
            ]),
            ("messages/partial", [
                {
                    "id": "msg_1",
                    "type": "ai",
                    "content": [{"type": "text", "text": "Why did the chicken"}]
                }
            ]),
            ("messages/partial", [
                {
                    "id": "msg_1",
                    "type": "ai",
                    "content": [{"type": "text", "text": "Why did the chicken cross the road?"}]
                }
            ]),
            # Complete message with tool call
            ("messages/complete", [
                {
                    "id": "msg_1",
                    "type": "ai",
                    "content": [{"type": "text", "text": "Why did the chicken cross the road?"}],
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "name": "sql_db_query",
                            "args": {"query": "SELECT * FROM jokes WHERE type='chicken'"}
                        }
                    ],
                    "usage_metadata": {
                        "input_tokens": 50,
                        "output_tokens": 30,
                        "total_tokens": 80
                    }
                }
            ]),
        ],
        "render_queue": [],
        "pending_interrupt": None,
        "session_tokens": {"input": 0, "output": 0, "total": 0},
        "session_start_time": 1234567890.0,
        "message_count": 0,
        "should_exit": False,
        "error": None,
    }

    # Execute just the stream processing part
    # (In real usage, this would be part of the full graph flow)
    stream_processor = build_stream_processor_subgraph()

    result = stream_processor.invoke({
        "stream_chunks": test_state["stream_chunks"],
        "chunk_index": 0,
        "current_chunk": None,
        "prev_text": "",
        "render_queue": [],
        "pending_interrupt": None,
        "usage": None,
        "is_complete": False,
    })

    print("Stream Processing Result:")
    print(f"Render Queue Items: {len(result['render_queue'])}")
    print(f"Pending Interrupt: {result['pending_interrupt']}")
    print(f"Usage: {result['usage']}")
    print("\nRender Queue:")
    for item in result['render_queue']:
        print(f"  - {item['type']}: {list(item.keys())}")
