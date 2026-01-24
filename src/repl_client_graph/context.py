"""Dependency injection using context vars for StateGraph REPL.

This module provides context variables for injecting dependencies into graph nodes:
- LangGraphClient for API communication
- Renderer for terminal output
- SessionState for tracking session data
- HITLHandler for interrupt handling
- ToolRenderRegistry for tool rendering customization

Context vars allow nodes to access dependencies without explicit parameter passing.
"""

from contextvars import ContextVar

from repl_client_graph.core.client import LangGraphClient
from repl_client_graph.core.session import SessionState
from repl_client_graph.ui.renderer import Renderer

# Forward reference for HITLHandler and ToolRenderRegistry to avoid circular import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from repl_client_graph.streaming.hitl import HITLHandler
    from repl_client_graph.ui.content_blocks import ToolRenderRegistry

# Context variables for dependency injection
_client_ctx: ContextVar[LangGraphClient | None] = ContextVar("client", default=None)
_renderer_ctx: ContextVar[Renderer | None] = ContextVar("renderer", default=None)
_session_ctx: ContextVar[SessionState | None] = ContextVar("session", default=None)
_hitl_handler_ctx: ContextVar["HITLHandler | None"] = ContextVar("hitl_handler", default=None)
_tool_registry_ctx: ContextVar["ToolRenderRegistry | None"] = ContextVar("tool_registry", default=None)


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


def set_hitl_handler(hitl_handler: "HITLHandler") -> None:
    """Set the HITLHandler in context.

    Args:
        hitl_handler: HITLHandler instance to make available to nodes
    """
    _hitl_handler_ctx.set(hitl_handler)


def get_hitl_handler() -> "HITLHandler":
    """Get the HITLHandler from context.

    Returns:
        HITLHandler instance

    Raises:
        RuntimeError: If HITLHandler not set in context
    """
    hitl_handler = _hitl_handler_ctx.get()
    if hitl_handler is None:
        raise RuntimeError("HITLHandler not set in context. Call set_hitl_handler() first.")
    return hitl_handler


def set_tool_registry(registry: "ToolRenderRegistry") -> None:
    """Set the ToolRenderRegistry in context.

    Args:
        registry: ToolRenderRegistry instance to make available to nodes
    """
    _tool_registry_ctx.set(registry)


def get_tool_registry() -> "ToolRenderRegistry":
    """Get the ToolRenderRegistry from context.

    Returns:
        ToolRenderRegistry instance

    Raises:
        RuntimeError: If tool registry not set in context
    """
    registry = _tool_registry_ctx.get()
    if registry is None:
        raise RuntimeError("ToolRenderRegistry not set in context. Call set_tool_registry() first.")
    return registry
