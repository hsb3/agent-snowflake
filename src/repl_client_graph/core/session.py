"""Session state management for REPL.

Tracks current thread, assistant, tokens, and session metadata.
"""

import time
from typing import Any


class SessionState:
    """Manages session state for the REPL.

    Tracks:
    - Current thread and assistant
    - Token usage
    - Session metadata (start time, message count)
    """

    def __init__(self) -> None:
        """Initialize session state."""
        self.current_thread_id: str | None = None
        self.current_assistant_id: str | None = None
        self.session_start_time: float = time.time()
        self.session_tokens: dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }
        self.message_count: int = 0

    def set_thread(self, thread_id: str) -> None:
        """Set the current thread ID.

        Args:
            thread_id: Thread ID to set
        """
        self.current_thread_id = thread_id

    def set_agent(self, agent_id: str) -> None:
        """Set the current assistant/agent ID.

        Args:
            agent_id: Assistant ID to set
        """
        self.current_assistant_id = agent_id

    def track_tokens(self, input_tokens: int, output_tokens: int) -> None:
        """Track token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        self.session_tokens["input_tokens"] += input_tokens
        self.session_tokens["output_tokens"] += output_tokens
        self.session_tokens["total_tokens"] += input_tokens + output_tokens

    def get_token_summary(self) -> dict[str, Any]:
        """Get token usage summary.

        Returns:
            Dictionary with token counts
        """
        return {
            "input_tokens": self.session_tokens["input_tokens"],
            "output_tokens": self.session_tokens["output_tokens"],
            "total_tokens": self.session_tokens["total_tokens"],
        }
