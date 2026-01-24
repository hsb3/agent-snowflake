"""Dependency injection using context vars for StateGraph REPL.

This module provides context variables for injecting dependencies into graph nodes:
- LangGraphClient for API communication
- Renderer for terminal output
- SessionState for tracking session data

Context vars allow nodes to access dependencies without explicit parameter passing.
"""

from contextvars import ContextVar

from repl_client_graph.core.client import LangGraphClient
from repl_client_graph.core.session import SessionState
from repl_client_graph.ui.renderer import Renderer

# Context variables for dependency injection
_client_ctx: ContextVar[LangGraphClient | None] = ContextVar("client", default=None)
_renderer_ctx: ContextVar[Renderer | None] = ContextVar("renderer", default=None)
_session_ctx: ContextVar[SessionState | None] = ContextVar("session", default=None)


def set_client(client: LangGraphClient) -> None:
    """Set the LangGraphClient in context.

    Args:
        client: LangGraphClient instance to make available to nodes
    """
    _client_ctx.set(client)


def get_client() -> LangGraphClient:
    """Get the LangGraphClient from context.

    Returns:
        LangGraphClient instance

    Raises:
        RuntimeError: If client not set in context
    """
    client = _client_ctx.get()
    if client is None:
        raise RuntimeError("LangGraphClient not set in context. Call set_client() first.")
    return client


def set_renderer(renderer: Renderer) -> None:
    """Set the Renderer in context.

    Args:
        renderer: Renderer instance to make available to nodes
    """
    _renderer_ctx.set(renderer)


def get_renderer() -> Renderer:
    """Get the Renderer from context.

    Returns:
        Renderer instance

    Raises:
        RuntimeError: If renderer not set in context
    """
    renderer = _renderer_ctx.get()
    if renderer is None:
        raise RuntimeError("Renderer not set in context. Call set_renderer() first.")
    return renderer


def set_session(session: SessionState) -> None:
    """Set the SessionState in context.

    Args:
        session: SessionState instance to make available to nodes
    """
    _session_ctx.set(session)


def get_session() -> SessionState:
    """Get the SessionState from context.

    Returns:
        SessionState instance

    Raises:
        RuntimeError: If session not set in context
    """
    session = _session_ctx.get()
    if session is None:
        raise RuntimeError("SessionState not set in context. Call set_session() first.")
    return session
