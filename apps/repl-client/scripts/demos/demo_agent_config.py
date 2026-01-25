"""Demo of Agent Config Screen with schema viewer.

This script demonstrates the AgentConfigScreen modal with two tabs:
- Schema Viewer: Displays context_schema fields with descriptions
- Create Assistant: Placeholder for future assistant creation form

Can run in two modes:
1. Mock mode (default): Uses sample schema data
2. Live mode (--live): Connects to running LangGraph server

Run:
    # Mock mode - no server required
    uv run python scripts/demos/demo_agent_config.py

    # Live mode - requires running server
    uv run python scripts/demos/demo_agent_config.py --live
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Label

from repl_client.tui.screens.agent_config import AgentConfigScreen

# Get the path to the main stylesheet
_STYLES_DIR = Path(__file__).parent.parent.parent / "src" / "repl_client" / "tui" / "styles"
_STYLESHEET_PATH = _STYLES_DIR / "index.tcss"

# Sample schema data matching the structure from /assistants/{id}/schemas
SAMPLE_SCHEMA = {
    "graph_id": "agent",
    "context_schema": {
        "title": "ContextSchema",
        "type": "object",
        "properties": {
            "model": {
                "default": "claude-haiku-4-5",
                "description": "LLM model for the agent",
                "langgraph_nodes": ["agent"],
                "title": "Model",
                "type": "string",
            },
            "temperature": {
                "default": 0.2,
                "description": "Model temperature (0.0=deterministic, 1.0=creative)",
                "langgraph_nodes": ["agent"],
                "title": "Temperature",
                "type": "number",
            },
            "snowflake_uri": {
                "default": "sqlite:///test_chinook.db",
                "description": "Snowflake connection URI: snowflake://user:password@account/database/schema?warehouse=wh&role=role",
                "langgraph_nodes": ["agent"],
                "title": "Snowflake Uri",
                "type": "string",
            },
            "snowflake_account": {
                "default": "",
                "description": "Snowflake account identifier",
                "langgraph_nodes": ["agent"],
                "title": "Snowflake Account",
                "type": "string",
            },
            "allowed_schemas": {
                "default": "*",
                "description": "Comma-separated list of allowed schemas (* for all)",
                "langgraph_nodes": ["agent"],
                "title": "Allowed Schemas",
                "type": "string",
            },
            "allowed_tables": {
                "default": "*",
                "description": "Comma-separated list of allowed tables (* for all)",
                "langgraph_nodes": ["agent"],
                "title": "Allowed Tables",
                "type": "string",
            },
            "read_only": {
                "default": True,
                "description": "Enforce read-only database access",
                "langgraph_nodes": ["agent"],
                "title": "Read Only",
                "type": "boolean",
            },
            "query_timeout": {
                "default": 30,
                "description": "Query execution timeout in seconds",
                "langgraph_nodes": ["agent"],
                "title": "Query Timeout",
                "type": "integer",
            },
            "max_iterations": {
                "default": 50,
                "description": "Maximum agent iterations before stopping",
                "langgraph_nodes": ["agent"],
                "title": "Max Iterations",
                "type": "integer",
            },
            "enable_debug": {
                "default": True,
                "description": "Enable debug mode with verbose logging",
                "langgraph_nodes": ["agent"],
                "title": "Enable Debug",
                "type": "boolean",
            },
        },
    },
}

SAMPLE_AGENT_INFO = {
    "assistant_id": "fe096781-5601-53d2-b2f6-0d3403f7e9ca",
    "graph_id": "agent",
    "name": "agent",
    "description": None,
    "config": {},
    "context": {},
    "metadata": {"created_by": "system"},
    "created_at": "2026-01-25T17:37:42.053169+00:00",
    "updated_at": "2026-01-25T17:37:42.053169+00:00",
    "version": 1,
}


class AgentConfigDemoApp(App[None]):
    """Demo app for testing AgentConfigScreen.

    Uses the main repl_client stylesheet for consistent styling.
    """

    # Use the main stylesheet from repl_client.tui
    CSS_PATH = _STYLESHEET_PATH

    CSS = """
    .demo-label {
        text-align: center;
        padding: 2;
    }
    """

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("escape", "quit", "Quit", show=True),
        Binding("f6", "show_config", "Agent Config", show=True),
    ]

    def __init__(self, live_mode: bool = False):
        super().__init__()
        self.live_mode = live_mode
        self.agent_info: dict | None = None
        self.schemas: dict | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        mode = "Live" if self.live_mode else "Mock"
        yield Label(
            f"Agent Config Demo ({mode} Mode)\n\n"
            "Press F6 to open Agent Config screen\n"
            "Press Escape to quit",
            classes="demo-label",
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Load data and show config screen on mount."""
        if self.live_mode:
            await self._load_live_data()
        else:
            self._load_mock_data()

        # Automatically show the config screen
        self.call_after_refresh(self.action_show_config)

    def _load_mock_data(self) -> None:
        """Load mock data for demo."""
        self.agent_info = SAMPLE_AGENT_INFO.copy()
        self.schemas = SAMPLE_SCHEMA.copy()

    async def _load_live_data(self) -> None:
        """Load data from running LangGraph server."""
        from repl_client.core.client import LangGraphClient
        from repl_client.core.config import Config
        from repl_client.core.logging import get_logger

        logger = get_logger("demo.agent_config")

        try:
            config = Config.from_env()
            logger.info(f"Connecting to server: {config.server_url}")
            client = LangGraphClient(config.server_url)

            # Get first agent
            agents = await client.list_agents()
            logger.info(f"Found {len(agents)} agents")

            if not agents:
                self.notify("No agents available", severity="error")
                self._load_mock_data()
                return

            self.agent_info = agents[0]
            agent_id = self.agent_info["assistant_id"]
            graph_id = self.agent_info.get("graph_id", "unknown")
            logger.info(f"Selected agent: graph_id={graph_id}, assistant_id={agent_id}")

            # Get schemas using the UUID
            logger.info(f"Fetching schemas for assistant_id: {agent_id}")
            self.schemas = await client.get_agent_schemas(agent_id)

            if self.schemas:
                context_schema = self.schemas.get("context_schema", {})
                properties = context_schema.get("properties", {})
                logger.info(f"Loaded schemas with {len(properties)} context properties")
            else:
                logger.warning("No schemas returned")

            self.notify(f"Loaded: {graph_id} ({agent_id[:8]}...)")

        except Exception as e:
            logger.exception(f"Failed to connect: {e}")
            self.notify(f"Failed to connect: {e}", severity="error")
            self._load_mock_data()

    async def action_show_config(self) -> None:
        """Show the agent config screen."""
        if not self.agent_info:
            self.notify("No agent data loaded", severity="error")
            return

        result = await self.push_screen(
            AgentConfigScreen(self.agent_info, self.schemas)
        )

        if result:
            self.notify(f"Config result: {result}")


def main():
    """Run the agent config demo."""
    live_mode = "--live" in sys.argv

    print("=" * 60)
    print("Agent Config Screen Demo")
    print("=" * 60)
    print()

    if live_mode:
        print("Mode: LIVE (connecting to LangGraph server)")
        print()
        print("Prerequisites:")
        print("  - LangGraph server running (make dev-server)")
        print("  - Environment configured (.env)")
    else:
        print("Mode: MOCK (using sample data)")
        print()
        print("Use --live flag to connect to actual server:")
        print("  uv run python scripts/demos/demo_agent_config.py --live")

    print()
    print("Controls:")
    print("  - F6: Open Agent Config screen")
    print("  - Tab: Navigate between tabs")
    print("  - Escape: Close modal / Quit")
    print()
    print("Starting demo...")
    print("=" * 60)
    print()

    app = AgentConfigDemoApp(live_mode=live_mode)
    app.run()


if __name__ == "__main__":
    main()
