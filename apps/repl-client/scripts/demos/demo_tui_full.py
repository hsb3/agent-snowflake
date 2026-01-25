"""Demo of full TUI app integration.

This script demonstrates the complete REPL TUI with all widgets:
- Connection to server
- Streaming messages
- User/AI/Tool messages
- HITL flow (if triggered)

Prerequisites:
    - LangGraph server running (make dev-server)
    - Environment configured (.env with LANGGRAPH_DEV_SERVER_PORT)

Run:
    uv run python scripts/demos/demo_tui_full.py
"""

from repl_client.core.config import Config
from repl_client.core.logging import setup_client_logger
from repl_client.tui.app import REPLApp


def main():
    """Run the full TUI demo."""
    # Setup logging
    setup_client_logger(level="DEBUG")

    # Load config
    config = Config.from_env()

    print("=" * 60)
    print("REPL TUI Full Demo")
    print("=" * 60)
    print(f"Server: {config.server_url}")
    print(f"Default agent: {config.default_agent or '(first available)'}")
    print()
    print("Features demonstrated:")
    print("  - Connection to LangGraph server")
    print("  - Agent and thread management")
    print("  - Streaming messages with live updates")
    print("  - User/AI/Tool message widgets")
    print("  - Status bar with connection/agent/thread info")
    print("  - Command system (/help, /agents, /new, /info, /clear)")
    print("  - HITL interrupts (if triggered)")
    print()
    print("Key bindings:")
    print("  - Enter: Send message")
    print("  - Ctrl+J: New line in input")
    print("  - Up/Down: History navigation (on first/last line)")
    print("  - Ctrl+L: Clear messages")
    print("  - Ctrl+C: Quit")
    print()
    print("Commands:")
    print("  /help          - Show help")
    print("  /agents        - List available agents")
    print("  /agents <id>   - Switch to agent")
    print("  /new           - Create new thread")
    print("  /info          - Show session info")
    print("  /clear         - Clear message history")
    print()
    print("Starting TUI...")
    print("=" * 60)
    print()

    # Create and run app
    app = REPLApp(config=config)
    app.run()


if __name__ == "__main__":
    main()
