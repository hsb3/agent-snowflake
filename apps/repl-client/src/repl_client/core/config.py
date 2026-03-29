"""Configuration for REPL client (Layer 8).

Loads configuration from environment variables and .env file.
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass
class Config:
    """REPL configuration.

    Attributes:
        server_url: LangGraph server URL (e.g., http://localhost:2024)
        default_agent: Default agent/assistant ID (empty string if not set)
        stream_mode: List of stream modes for server (default: ["messages"])
        debug: Enable debug logging (default: False)
    """

    server_url: str = "http://localhost:2024"
    default_agent: str = ""
    stream_mode: list[str] = field(default_factory=lambda: ["messages"])
    debug: bool = False

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Loads .env file if present, then reads:
        - LANGGRAPH_DEV_SERVER_URL: Full server URL (default: http://localhost:2024)
        - REPL_DEFAULT_AGENT: Default agent ID (default: "")
        - REPL_DEBUG: Enable debug mode (default: False)

        Returns:
            Config instance with values from environment
        """
        # Load .env file if present
        load_dotenv()

        # Get server URL from environment
        server_url = os.getenv("LANGGRAPH_DEV_SERVER_URL", "http://localhost:2024")

        # Get default agent
        default_agent = os.getenv("REPL_DEFAULT_AGENT", "")

        # Get debug mode
        debug_str = os.getenv("REPL_DEBUG", "false").lower()
        debug = debug_str in ("true", "1", "yes")

        # Stream mode is always ["messages"] for Phase 1
        stream_mode = ["messages"]

        return cls(
            server_url=server_url,
            default_agent=default_agent,
            stream_mode=stream_mode,
            debug=debug,
        )
