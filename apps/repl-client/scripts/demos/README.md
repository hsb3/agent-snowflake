# TUI Widget Demos

Interactive demos for testing and showcasing REPL TUI widgets.

## Quick Start

```bash
cd apps/repl-client

# List available demos
uv run python scripts/demos/run_demo.py --list

# Run a specific demo
uv run python scripts/demos/run_demo.py messages
uv run python scripts/demos/run_demo.py sidebar

# Partial matching works
uv run python scripts/demos/run_demo.py side    # matches "sidebar"
uv run python scripts/demos/run_demo.py conn    # matches "connection"
```

## Available Demos

| Demo | Description | Server Required |
|------|-------------|-----------------|
| `messages` | Message widgets (User/AI/Tool) | No |
| `sidebar` | Sidebar panel with threads/agents/tools | No |
| `status` | Status bar and loading indicators | No |
| `input` | Chat input with history and completion | No |
| `connection` | Connection health indicator | No |
| `full` | Full TUI integration | Yes |

## Files

| File | Purpose |
|------|---------|
| `run_demo.py` | CLI launcher for all demos |
| `demo_fixtures.py` | Shared demo data and helper functions |
| `demo_tui_*.py` | Individual widget demos |
| `demo_connection_indicator.py` | Connection status demo |

## Fixtures

`demo_fixtures.py` provides centralized test data:

- `DEMO_THREADS` - Sample thread data
- `DEMO_AGENTS` - Sample agent data
- `DEMO_TOOLS` - Sample tool call data
- `DEMO_URLS` - Sample server URLs
- `DEMO_STATUS_STATES` - Status bar state cycles
- `DEMO_LOADING_OPERATIONS` - Loading indicator labels

Helper functions:
- `setup_status_area()` - Configure a StatusArea widget
- `populate_sidebar()` - Populate a Sidebar with demo data
