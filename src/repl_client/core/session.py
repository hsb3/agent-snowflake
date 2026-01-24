"""Session state management for REPL (Layer 3).

This module tracks ephemeral client-side state:
- Current thread, agent, and run IDs
- Token usage for display
- Namespace state for parallel agent support

Design notes:
- State is ephemeral (cleared on REPL exit)
- Server owns persistent state (threads, checkpoints)
- Token tracking is display-only (not authoritative)
- Namespace state prepared for future parallel agents
"""

import time


class SessionState:
    """Track current session state.

    State fields:
    - current_thread_id: Active thread ID or None
    - current_assistant_id: Active agent ID (empty string if not set)
    - current_run_id: Current run ID for HITL resume or None
    - namespace_state: Per-namespace data for parallel agents
    - session_tokens: Token usage tracking {input, output, total}
    - session_start_time: Session start timestamp
    """

    def __init__(self):
        """Initialize empty state."""
        self.current_thread_id: str | None = None
        self.current_assistant_id: str = ""
        self.current_run_id: str | None = None
        self.namespace_state: dict[tuple, dict] = {}
        self.session_tokens: dict[str, int] = {"input": 0, "output": 0, "total": 0}
        self.session_start_time: float = time.time()

    def set_thread(self, thread_id: str) -> None:
        """Set active thread and clear namespace tracking.

        Args:
            thread_id: Thread ID to set as active
        """
        self.current_thread_id = thread_id
        self.namespace_state = {}

    def set_agent(self, assistant_id: str) -> None:
        """Set active agent.

        Args:
            assistant_id: Agent/assistant ID to set as active
        """
        self.current_assistant_id = assistant_id

    def set_run(self, run_id: str) -> None:
        """Track current run ID (for HITL resume).

        Args:
            run_id: Run ID to track
        """
        self.current_run_id = run_id

    def get_namespace_key(self, namespace: list | None) -> tuple:
        """Convert namespace to hashable key.

        Args:
            namespace: Namespace list or None

        Returns:
            Tuple suitable for dict key (empty tuple if None/empty)
        """
        if namespace is None:
            return ()
        return tuple(namespace)

    def track_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Accumulate token usage for display.

        Args:
            input_tokens: Number of input tokens to add
            output_tokens: Number of output tokens to add
        """
        self.session_tokens["input"] += input_tokens
        self.session_tokens["output"] += output_tokens
        self.session_tokens["total"] += input_tokens + output_tokens

    def get_token_summary(self) -> dict:
        """Get token usage stats.

        Returns:
            Dict with input, output, total token counts
        """
        return {
            "input": self.session_tokens["input"],
            "output": self.session_tokens["output"],
            "total": self.session_tokens["total"],
        }

    def get_display_summary(self) -> str:
        """Get summary for prompt (thread/agent/tokens).

        Returns:
            Formatted string showing session state
        """
        thread_info = self.current_thread_id or "No thread"
        agent_info = self.current_assistant_id or "No agent"
        tokens = self.session_tokens

        return (
            f"Thread: {thread_info} | "
            f"Agent: {agent_info} | "
            f"Tokens: {tokens['input']} in / {tokens['output']} out / {tokens['total']} total"
        )

    def reset(self) -> None:
        """Reset all state (new session)."""
        self.current_thread_id = None
        self.current_assistant_id = ""
        self.current_run_id = None
        self.namespace_state = {}
        self.session_tokens = {"input": 0, "output": 0, "total": 0}
        self.session_start_time = time.time()
