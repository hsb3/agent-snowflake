"""Enhanced Snowflake agent with middleware for control and capabilities.

This module demonstrates valuable middleware configurations for SQL agents:
- Human-in-the-loop for dangerous operations
- Call limits for cost control
- Retry logic for reliability
- Summarization for long conversations
- Todo list for complex analysis tasks
"""

import logging
from typing import Any, cast

from langchain.agents import create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    ModelFallbackMiddleware,
    ModelRetryMiddleware,
    SummarizationMiddleware,
    TodoListMiddleware,
    ToolCallLimitMiddleware,
)
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from .context2 import EnhancedContextSchema
from .prompts import system_prompt
from .tools import create_sql_tools
from .utils import init_model

logger = logging.getLogger(__name__)


def build_graph_with_middleware(config: RunnableConfig | None = None) -> CompiledStateGraph:
    """Build Snowflake agent with configurable middleware.

    Middleware is configured via EnhancedContextSchema. All middleware
    components can be enabled/disabled and customized through context.

    Available middleware (when enabled):
    1. Human-in-the-loop: Require approval for write operations
    2. Model call limit: Prevent runaway costs
    3. Tool call limit: Limit expensive SQL queries
    4. Model retry: Handle transient network failures
    5. Summarization: Compress conversation history when token limit reached
    6. Todo list: Enable task planning for complex analysis
    7. Model fallback: Fallback to alternative models on failure

    Args:
        config: Optional RunnableConfig from LangGraph runtime

    Returns:
        Compiled agent graph with middleware

    Example:
        >>> # In langgraph.json, reference this function:
        >>> # "graphs": {"agent_enhanced": "src.agent.graph2:build_graph_with_middleware"}
        >>> graph = build_graph_with_middleware()
        >>> result = graph.invoke({"messages": [...]})
    """
    # Load enhanced context from config (or use defaults)
    context = EnhancedContextSchema.from_runnable_config(config, fallback_env=True)

    if context.enable_debug:
        logger.info(f"Building enhanced graph with context: {context}")

    # Initialize LLM
    llm = init_model(
        model=context.model,
        temperature=context.temperature,
    )

    # Create SQL tools with guardrails
    tools = create_sql_tools(llm=llm, context=context)

    if context.enable_debug:
        logger.info(f"Created {len(tools)} tools: {[t.name for t in tools]}")

    # Configure middleware stack based on context settings
    middleware: list[Any] = []

    # 1. Human-in-the-loop: Require approval for sql_db_query tool
    # Only enable if: enable_hitl=True AND read_only=False
    # Note: Requires checkpointer to maintain state across interruptions
    if context.enable_hitl and not context.read_only:
        allowed_decisions = [d.strip() for d in context.hitl_allowed_decisions.split(",")]
        interrupt_config: Any = {
            "sql_db_query": {
                "allowed_decisions": allowed_decisions,
            },
            # Don't interrupt on schema inspection tools
            "sql_db_schema": False,
            "sql_db_list_tables": False,
        }
        middleware.append(HumanInTheLoopMiddleware(interrupt_on=cast(Any, interrupt_config)))
        if context.enable_debug:
            logger.info(f"Added HumanInTheLoopMiddleware with decisions: {allowed_decisions}")

    # 2. Model call limit: Prevent infinite loops
    # Only add if limits are set (> 0)
    if context.model_call_thread_limit > 0 or context.model_call_run_limit > 0:
        middleware.append(
            ModelCallLimitMiddleware(
                thread_limit=context.model_call_thread_limit
                if context.model_call_thread_limit > 0
                else None,
                run_limit=context.model_call_run_limit
                if context.model_call_run_limit > 0
                else None,
                exit_behavior=context.model_call_exit_behavior,
            )
        )
        if context.enable_debug:
            logger.info(
                f"Added ModelCallLimitMiddleware: thread={context.model_call_thread_limit}, "
                f"run={context.model_call_run_limit}, exit={context.model_call_exit_behavior}"
            )

    # 3. Tool call limit: Limit expensive SQL queries
    # Global limit across all tools
    if context.tool_call_thread_limit > 0 or context.tool_call_run_limit > 0:
        middleware.append(
            ToolCallLimitMiddleware(
                thread_limit=context.tool_call_thread_limit
                if context.tool_call_thread_limit > 0
                else None,
                run_limit=context.tool_call_run_limit if context.tool_call_run_limit > 0 else None,
                exit_behavior=context.tool_call_exit_behavior,
            )
        )
        if context.enable_debug:
            logger.info(
                f"Added global ToolCallLimitMiddleware: thread={context.tool_call_thread_limit}, "
                f"run={context.tool_call_run_limit}"
            )

    # Specific limit for sql_db_query (most expensive)
    if context.sql_query_thread_limit > 0 or context.sql_query_run_limit > 0:
        middleware.append(
            ToolCallLimitMiddleware(
                tool_name="sql_db_query",
                thread_limit=context.sql_query_thread_limit
                if context.sql_query_thread_limit > 0
                else None,
                run_limit=context.sql_query_run_limit if context.sql_query_run_limit > 0 else None,
                exit_behavior=context.tool_call_exit_behavior,
            )
        )
        if context.enable_debug:
            logger.info(
                f"Added sql_db_query ToolCallLimitMiddleware: thread={context.sql_query_thread_limit}, "
                f"run={context.sql_query_run_limit}"
            )

    # 4. Model retry: Handle transient failures with exponential backoff
    if context.retry_max_retries > 0:
        middleware.append(
            ModelRetryMiddleware(
                max_retries=context.retry_max_retries,
                backoff_factor=context.retry_backoff_factor,
                initial_delay=context.retry_initial_delay,
                max_delay=context.retry_max_delay,
                jitter=context.retry_jitter,
            )
        )
        if context.enable_debug:
            logger.info(
                f"Added ModelRetryMiddleware: retries={context.retry_max_retries}, "
                f"backoff={context.retry_backoff_factor}x, initial_delay={context.retry_initial_delay}s"
            )

    # 5. Summarization: Compress history when approaching token limits
    if context.enable_summarization:
        middleware.append(
            SummarizationMiddleware(
                model=context.summarization_model,
                trigger=("tokens", context.summarization_trigger_tokens),
                keep=("messages", context.summarization_keep_messages),
            )
        )
        if context.enable_debug:
            logger.info(
                f"Added SummarizationMiddleware: trigger={context.summarization_trigger_tokens} tokens, "
                f"keep={context.summarization_keep_messages} messages, model={context.summarization_model}"
            )

    # 6. Todo list: Enable task planning for complex multi-step analysis
    if context.enable_todo:
        middleware.append(TodoListMiddleware())
        if context.enable_debug:
            logger.info("Added TodoListMiddleware")

    # 7. Model fallback: Fallback to alternative models on failure
    if context.enable_fallback:
        # Use custom fallback models if specified, otherwise auto-detect
        if context.fallback_models:
            fallback_models = [m.strip() for m in context.fallback_models.split(",")]
        else:
            # Auto-detect based on primary model
            primary_model = context.model
            if "gpt-4o" in primary_model:
                fallback_models = ["gpt-4o-mini", "claude-3-5-sonnet-20241022"]
            elif "claude" in primary_model:
                fallback_models = ["gpt-4o", "gpt-4o-mini"]
            else:
                fallback_models = ["gpt-4o-mini"]

        if fallback_models:
            middleware.append(ModelFallbackMiddleware(*fallback_models))
            if context.enable_debug:
                logger.info(f"Added ModelFallbackMiddleware: {fallback_models}")

    if context.enable_debug:
        logger.info(f"Configured {len(middleware)} middleware components")
        if middleware:
            logger.info(f"Middleware stack: {[type(m).__name__ for m in middleware]}")

    # Create agent with middleware
    # Note: HumanInTheLoopMiddleware requires a checkpointer
    checkpointer = InMemorySaver() if (context.enable_hitl and not context.read_only) else None

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        context_schema=EnhancedContextSchema,  # Use enhanced schema for config
        middleware=middleware,
        checkpointer=checkpointer,  # Required for human-in-the-loop
        debug=context.enable_debug,
        name="agent_enhanced",
    )

    if context.enable_debug:
        logger.info(f"Enhanced graph built successfully with nodes: {list(agent.nodes.keys())}")
        logger.info(f"Middleware stack: {[type(m).__name__ for m in middleware]}")

    return agent  # type: ignore


# Alternative: Minimal middleware for development/testing
def build_graph_minimal_middleware(config: RunnableConfig | None = None) -> CompiledStateGraph:
    """Build agent with minimal middleware for faster iteration.

    Only includes essential middleware (configurable via context):
    - Model call limit (prevent runaway)
    - Model retry (handle transient failures)

    Use this for local development and testing.
    """
    context = EnhancedContextSchema.from_runnable_config(config, fallback_env=True)

    if context.enable_debug:
        logger.info(f"Building minimal graph with context: {context}")

    llm = init_model(model=context.model, temperature=context.temperature)
    tools = create_sql_tools(llm=llm, context=context)

    middleware: list[Any] = []

    # Model call limit (if enabled)
    if context.model_call_run_limit > 0:
        middleware.append(
            ModelCallLimitMiddleware(
                run_limit=context.model_call_run_limit,
                exit_behavior=context.model_call_exit_behavior,
            )
        )
        if context.enable_debug:
            logger.info(f"Added ModelCallLimitMiddleware: run_limit={context.model_call_run_limit}")

    # Model retry (if enabled)
    if context.retry_max_retries > 0:
        middleware.append(
            ModelRetryMiddleware(
                max_retries=context.retry_max_retries,
                backoff_factor=context.retry_backoff_factor,
                initial_delay=context.retry_initial_delay,
            )
        )
        if context.enable_debug:
            logger.info(f"Added ModelRetryMiddleware: max_retries={context.retry_max_retries}")

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        context_schema=EnhancedContextSchema,  # Use enhanced schema for config
        middleware=middleware,
        debug=context.enable_debug,
        name="agent_minimal",
    )

    if context.enable_debug:
        logger.info(f"Minimal graph built with {len(middleware)} middleware components")

    return agent  # type: ignore


# Export both versions
graph_enhanced = build_graph_with_middleware
graph_minimal = build_graph_minimal_middleware
