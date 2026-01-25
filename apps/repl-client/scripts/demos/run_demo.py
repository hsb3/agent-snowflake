#!/usr/bin/env python
"""Demo launcher for TUI widget demos.

Usage:
    uv run python scripts/demos/run_demo.py --list      # List all demos
    uv run python scripts/demos/run_demo.py messages    # Run messages demo
    uv run python scripts/demos/run_demo.py side        # Partial match
    uv run python scripts/demos/run_demo.py sidebar     # Run sidebar demo
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any

DEMOS: dict[str, dict[str, Any]] = {
    "messages": {
        "module": "demo_tui_messages",
        "class": "MessageDemo",
        "desc": "Message widgets (User/AI/Tool)",
        "server": False,
    },
    "sidebar": {
        "module": "demo_tui_sidebar",
        "class": "SidebarDemo",
        "desc": "Sidebar panel with threads/agents/tools",
        "server": False,
    },
    "status": {
        "module": "demo_tui_status",
        "class": "StatusDemo",
        "desc": "Status bar and loading indicators",
        "server": False,
    },
    "input": {
        "module": "demo_tui_input",
        "class": "InputDemo",
        "desc": "Chat input with history and completion",
        "server": False,
    },
    "connection": {
        "module": "demo_connection_indicator",
        "class": "ConnectionIndicatorDemo",
        "desc": "Connection health indicator",
        "server": False,
    },
    "full": {
        "module": "demo_tui_full",
        "entry": "main",
        "desc": "Full TUI integration (requires server)",
        "server": True,
    },
}


def list_demos() -> None:
    """Print available demos."""
    print("Available demos:")
    print()
    for name, info in DEMOS.items():
        server_note = " [requires server]" if info.get("server") else ""
        print(f"  {name:<12} - {info['desc']}{server_note}")
    print()
    print("Usage: uv run python scripts/demos/run_demo.py <demo_name>")


def find_demo(query: str) -> str | None:
    """Find demo by name or partial match."""
    if query in DEMOS:
        return query

    matches = [name for name in DEMOS if name.startswith(query)]
    if len(matches) == 1:
        return matches[0]

    if not matches:
        matches = [name for name in DEMOS if query in name]
        if len(matches) == 1:
            return matches[0]

    if len(matches) > 1:
        print(f"Ambiguous query '{query}'. Matches: {', '.join(matches)}")
        return None

    return None


def run_demo(name: str) -> None:
    """Run a demo by name."""
    info = DEMOS[name]
    module_name = info["module"]

    module = importlib.import_module(module_name)

    if "entry" in info:
        entry_fn = getattr(module, info["entry"])
        entry_fn()
    else:
        app_class = getattr(module, info["class"])
        app = app_class()
        app.run()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TUI Demo Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "demo",
        nargs="?",
        help="Demo name (or partial match)",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available demos",
    )

    args = parser.parse_args()

    if args.list or not args.demo:
        list_demos()
        return

    demo_name = find_demo(args.demo)
    if not demo_name:
        print(f"Demo '{args.demo}' not found.")
        print()
        list_demos()
        sys.exit(1)

    print(f"Running demo: {demo_name}")
    print(f"  {DEMOS[demo_name]['desc']}")
    if DEMOS[demo_name].get("server"):
        print("  Note: This demo requires a running LangGraph server")
    print()

    run_demo(demo_name)


if __name__ == "__main__":
    main()
