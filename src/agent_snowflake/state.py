"""State definitions for the Snowflake agent.

Defines the graph state schema using TypedDict for LangGraph compatibility.
"""

from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    """State schema for the Snowflake agent graph.

    This is the mutable state that evolves during agent execution.
    Use for conversation history, intermediate results, and outputs.
    """

    # Messages - conversation history
    messages: list[AnyMessage]
