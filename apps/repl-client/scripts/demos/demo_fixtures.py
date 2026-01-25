"""Centralized fixtures for TUI demos.

This module provides shared demo data used across multiple demo scripts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from repl_client.tui.widgets import Sidebar, StatusArea

# Thread fixtures
DEMO_THREADS = [
    {"thread_id": "thread-abc123456789", "created_at": "2026-01-24T10:00:00"},
    {"thread_id": "thread-def987654321", "created_at": "2026-01-23T15:30:00"},
    {"thread_id": "thread-ghi111222333", "created_at": "2026-01-22T09:15:00"},
]

# Agent fixtures
DEMO_AGENTS = [
    {"assistant_id": "agent-enhanced-123", "graph_id": "agent_enhanced"},
    {"assistant_id": "agent-basic-456", "graph_id": "agent_basic"},
    {"assistant_id": "agent-research-789", "graph_id": "agent_research"},
]

# Tool fixtures
DEMO_TOOLS = [
    {
        "name": "sql_db_query",
        "args": {"query": "SELECT * FROM users LIMIT 10"},
        "result": "[10 rows returned]",
        "status": "success",
    },
    {
        "name": "search_web",
        "args": {"query": "LangGraph documentation"},
        "result": "Found 5 results",
        "status": "success",
    },
    {
        "name": "code_interpreter",
        "args": {"code": "print('hello')"},
        "result": "",
        "status": "pending",
    },
]

# URL fixtures for connection demos
DEMO_URLS = [
    "http://localhost:2024",
    "http://localhost:3000",
    "https://api.example.com:8080",
    "http://192.168.1.100:5000",
]

# Status state fixtures for cycling through demo states
DEMO_STATUS_STATES = [
    {"agent": "agent_basic", "thread": "", "tokens": 0, "connected": True},
    {"agent": "agent_enhanced", "thread": "thread_abc123", "tokens": 456, "connected": True},
    {"agent": "agent_enhanced", "thread": "thread_abc123", "tokens": 1234, "connected": True},
    {"agent": "agent_enhanced", "thread": "thread_abc123", "tokens": 5678, "connected": False},
    {"agent": "", "thread": "", "tokens": 0, "connected": True},
]

# Loading operation labels
DEMO_LOADING_OPERATIONS = [
    "Processing",
    "Analyzing",
    "Generating",
    "Streaming response",
]


def setup_status_area(
    status_area: StatusArea,
    *,
    agent: str = "demo_agent",
    thread: str = "demo-1234",
    tokens: int = 1500,
    connected: bool = True,
    url: str | None = None,
    status: str = "Ready",
    last_update: str | None = None,
) -> None:
    """Configure a StatusArea with demo defaults.

    Args:
        status_area: The StatusArea widget to configure.
        agent: Agent ID to display.
        thread: Thread ID to display.
        tokens: Token count to display.
        connected: Connection state.
        url: Server URL (optional).
        status: Status message to display.
        last_update: Last update timestamp (optional).
    """
    status_area.set_agent(agent)
    status_area.set_thread(thread)
    status_area.set_tokens(tokens)
    status_area.set_connected(connected, url)
    status_area.set_status(status)
    if last_update:
        status_area.set_last_update(last_update)


def populate_sidebar(
    sidebar: Sidebar,
    *,
    threads: list[dict] | None = None,
    agents: list[dict] | None = None,
    tools: list[dict] | None = None,
    selected_thread: str | None = None,
    selected_agent: str | None = None,
    tokens: dict[str, int] | None = None,
    model: str = "claude-sonnet-4-5-20250929",
) -> None:
    """Populate a Sidebar with demo data.

    Args:
        sidebar: The Sidebar widget to populate.
        threads: Thread list (defaults to DEMO_THREADS).
        agents: Agent list (defaults to DEMO_AGENTS).
        tools: Tool list (defaults to DEMO_TOOLS).
        selected_thread: Currently selected thread ID.
        selected_agent: Currently selected agent ID.
        tokens: Token usage dict with 'total', 'input', 'output' keys.
        model: Model name to display.
    """
    threads = threads or DEMO_THREADS
    agents = agents or DEMO_AGENTS
    tools = tools or DEMO_TOOLS

    # Use first items as defaults if not specified
    if selected_thread is None and threads:
        selected_thread = threads[0]["thread_id"]
    if selected_agent is None and agents:
        selected_agent = agents[0]["assistant_id"]

    sidebar.populate_threads(threads, selected_thread)
    sidebar.populate_agents(agents, selected_agent)
    sidebar.populate_tools(tools)

    if selected_thread and selected_agent:
        sidebar.populate_session_info(
            thread_id=selected_thread,
            agent_id=selected_agent,
            tokens=tokens or {"total": 2345, "input": 1200, "output": 1145},
            model=model,
        )
