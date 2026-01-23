"""Snowflake agent for LangGraph.

A LangGraph agent that provides intelligent database interactions with Snowflake.
"""

from .graph import build_graph as graph
from .graph2 import (
    build_graph_with_middleware as graph_enhanced,
    build_graph_minimal_middleware as graph_minimal,
)
from .context import ContextSchema
from .context2 import EnhancedContextSchema
from .config import settings

__version__ = "0.1.0"
__all__ = [
    "graph",
    "graph_enhanced",
    "graph_minimal",
    "ContextSchema",
    "EnhancedContextSchema",
    "settings",
]
