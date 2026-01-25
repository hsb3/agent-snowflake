"""Entry point for REPL TUI application.

Run with:
    python -m repl_client.tui

Or (if installed):
    repl-tui
"""

from repl_client.core.config import Config
from repl_client.core.logging import setup_client_logger
from repl_client.tui.app import REPLApp


def main() -> None:
    """Main entry point for TUI REPL."""
    # Load config
    config = Config.from_env()

    # Setup logging
    log_level = "DEBUG" if config.debug else "INFO"
    setup_client_logger(level=log_level)

    # Create and run app
    app = REPLApp(config=config)
    app.run()


if __name__ == "__main__":
    main()
