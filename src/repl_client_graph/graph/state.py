"""REPLState TypedDict definition for StateGraph.

This module defines the state schema that flows through the REPL StateGraph.
The state contains all context needed for input processing, command execution,
streaming, rendering, and session management.
"""

from typing import Literal, TypedDict

"""
NOTE:
We can also use state to store things like:
  command history, assistant info, thread info, etc.
  treat state similar to browser localStorage/sessionStorage
"""

# TODO: The below should be built on defined types for each field. Use dataclasses or pydantic models.


class REPLState(TypedDict, total=False):
    """State that flows through the REPL StateGraph.

    This state is propagated automatically through graph nodes and contains
    all context needed for the REPL execution flow.

    Attributes:
        user_input: Raw user input from terminal
        input_type: Classification of input (command/message/empty)

        current_thread_id: Active LangGraph thread ID
        current_assistant_id: Active agent/assistant ID
        current_run_id: Current streaming run ID

        stream_chunks: Accumulated SSE chunks from streaming response
        stream_buffer: Text accumulation and tool call buffers

        render_queue: Parsed chunks waiting to be rendered
        pending_interrupt: HITL interrupt awaiting approval
        interrupt_approved: User's approval decision for interrupt

        session_tokens: Token usage tracking (input, output, total)
        session_start_time: Unix timestamp of session start
        message_count: Number of messages sent in session

        should_exit: Flag to exit the REPL loop
        error: Error message if execution failed

        command_result: Result from command execution
    """

    # Input state
    user_input: str
    input_type: Literal["command", "message", "empty", "exit"] | None

    # Session context
    # TODO: Below should be typed as uuid's and have proper validation/error handling
    current_thread_id: str | None
    current_assistant_id: str
    current_run_id: str | None

    # Streaming state
    stream_chunks: list[dict]  # Accumulate chunks for processing
    stream_buffer: dict  # Text accumulation, tool buffers

    # Rendering queue
    render_queue: list[dict]  # ParsedChunks waiting to render

    # HITL interrupt state
    pending_interrupt: dict | None
    interrupt_approved: bool | None

    # Session stats
    session_tokens: dict  # {input, output, total}
    session_start_time: float
    message_count: int

    # Control flow
    should_exit: bool
    error: str | None

    # Command execution result
    command_result: dict | None
