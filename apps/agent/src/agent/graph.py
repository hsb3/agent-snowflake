"""Snowflake agent graph definition.

This module creates and compiles the LangGraph agent for Snowflake database interactions.
"""

import logging

from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

from .context import ContextSchema

# from .state import AgentState # default agent state for langchain v1 agent
from .prompts import system_prompt
from .tools import create_sql_tools
from .utils import init_model

logger = logging.getLogger(__name__)


def build_graph(config: RunnableConfig | None = None) -> CompiledStateGraph:
    """Build and compile the Snowflake agent graph.

    This is the entry point called by LangGraph. It loads context from
    RunnableConfig and creates the agent with appropriate tools.

    Args:
        config: Optional RunnableConfig from LangGraph runtime

    Returns:
        Compiled agent graph ready for invocation

    Example:
        >>> # Called automatically by LangGraph
        >>> graph = build_graph()
        >>> result = graph.invoke({"messages": [...]})
    """
    # Load context from config (or use defaults)
    context = ContextSchema.from_runnable_config(config, fallback_env=True)

    if context.enable_debug:
        logger.info(f"Building graph with context: {context}")

    # Initialize LLM from context
    llm = init_model(
        model=context.model,
        temperature=context.temperature,
    )

    # Create SQL tools with guardrails from context
    tools = create_sql_tools(llm=llm, context=context)

    if context.enable_debug:
        logger.info(f"Created {len(tools)} tools: {[t.name for t in tools]}")

    # Create agent with system prompt and context schema
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        # state_schema=AgentState,          # Optional: only needed if customizing beyond default
        context_schema=ContextSchema,
        debug=context.enable_debug,
        name="agent",
        # middleware=(),                    # For custom pre/post model hooks
        # response_format=None,             # For structured output
        # checkpointer=None,                # For conversation persistence
        # store=None,                       # For long-term memory (BaseStore)
        # interrupt_before=None,            # For human-in-the-loop before nodes
        # interrupt_after=None,             # For human-in-the-loop after nodes
        # cache=None,                       # For LLM response caching
    )

    if context.enable_debug:
        logger.info(f"Graph built successfully with nodes: {list(agent.nodes.keys())}")

    return agent  # type: ignore


# Export for langgraph.json
# graph = build_graph(). # not sure we need this.
