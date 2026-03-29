"""Enhanced Snowflake agent with middleware for control and capabilities.

This module demonstrates valuable middleware configurations for SQL agents:
- Human-in-the-loop for dangerous operations
- Call limits for cost control
- Retry logic for reliability
- Summarization for long conversations
- Todo list for complex analysis tasks
"""

import logging
from typing import Any

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
from langgraph.graph.state import CompiledStateGraph

from .context2 import EnhancedContextSchema
from .prompts import build_system_prompt
from .tools import create_sql_tools
from .utils import init_model

logger = logging.getLogger(__name__)


def _detect_db_type(uri: str) -> str:
    """Detect database type from connection URI.

    Args:
        uri: Database connection URI

    Returns:
        "snowflake" if URI starts with snowflake://, otherwise "sqlite"
    """
    if uri.startswith("snowflake://"):
        return "snowflake"
    return "sqlite"


def build_graph_with_middleware(config: RunnableConfig | None = None) -> CompiledStateGraph:
    """Build Snowflake agent with configurable middleware.

    Middleware is configured via EnhancedContextSchema. All middleware
    components can be enabled/disabled and customized through context.

    Middleware ordering (innermost to outermost):
    1. ModelRetryMiddleware - retry transient failures closest to model
    2. ModelFallbackMiddleware - fall back to other models on failure
    3. ModelCallLimitMiddleware - enforce model call limits
    4. ToolCallLimitMiddleware(s) - enforce tool call limits
    5. HumanInTheLoopMiddleware - approval flow for dangerous operations
    6. SummarizationMiddleware - context window management
    7. TodoListMiddleware - task planning

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
        logger.info("Building enhanced graph with context: %s", context)

    # Initialize LLM
    llm = init_model(
        model=context.model,
        temperature=context.temperature,
    )

    # Create SQL tools with guardrails
    tools = create_sql_tools(llm=llm, context=context)

    if context.enable_debug:
        logger.info("Created %d tools: %s", len(tools), [t.name for t in tools])

    # Build system prompt based on detected database type
    db_type = _detect_db_type(context.snowflake_uri)
    prompt = build_system_prompt(db_type=db_type)

    if context.enable_debug:
        logger.info("Using db_type=%s for system prompt", db_type)

    # Configure middleware stack based on context settings.
    # Order: error handling closest to model, flow control further out.
    middleware: list[Any] = []

    # 1. Model retry: Handle transient failures with exponential backoff
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
                "Added ModelRetryMiddleware: retries=%s, backoff=%sx, initial_delay=%ss",
                context.retry_max_retries,
                context.retry_backoff_factor,
                context.retry_initial_delay,
            )

    # 2. Model fallback: Fallback to alternative models on failure
    if context.enable_fallback:
        # Use custom fallback models if specified, otherwise auto-detect
        if context.fallback_models:
            fallback_models = [m.strip() for m in context.fallback_models.split(",")]
        else:
            # Auto-detect based on primary model
            primary_model = context.model
            if "gpt-4" in primary_model:
                fallback_models = ["gpt-4.1-mini", "claude-haiku-4-5-20251001"]
            elif "claude" in primary_model:
                fallback_models = ["gpt-4.1", "gpt-4.1-mini"]
            else:
                fallback_models = ["gpt-4.1-mini"]

        if fallback_models:
            middleware.append(ModelFallbackMiddleware(*fallback_models))
            if context.enable_debug:
                logger.info("Added ModelFallbackMiddleware: %s", fallback_models)

    # 3. Model call limit: Prevent infinite loops
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
                "Added ModelCallLimitMiddleware: thread=%s, run=%s, exit=%s",
                context.model_call_thread_limit,
                context.model_call_run_limit,
                context.model_call_exit_behavior,
            )

    # 4. Tool call limits
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
                "Added global ToolCallLimitMiddleware: thread=%s, run=%s",
                context.tool_call_thread_limit,
                context.tool_call_run_limit,
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
                "Added sql_db_query ToolCallLimitMiddleware: thread=%s, run=%s",
                context.sql_query_thread_limit,
                context.sql_query_run_limit,
            )

    # 5. Human-in-the-loop: Require approval for sql_db_query tool
    # Only enable if: enable_hitl=True AND read_only=False
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
        middleware.append(HumanInTheLoopMiddleware(interrupt_on=interrupt_config))
        if context.enable_debug:
            logger.info("Added HumanInTheLoopMiddleware with decisions: %s", allowed_decisions)

    # 6. Summarization: Compress history when approaching token limits
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
                "Added SummarizationMiddleware: trigger=%s tokens, keep=%s messages, model=%s",
                context.summarization_trigger_tokens,
                context.summarization_keep_messages,
                context.summarization_model,
            )

    # 7. Todo list: Enable task planning for complex multi-step analysis
    if context.enable_todo:
        middleware.append(TodoListMiddleware())
        if context.enable_debug:
            logger.info("Added TodoListMiddleware")

    if context.enable_debug:
        logger.info("Configured %d middleware components", len(middleware))
        if middleware:
            logger.info("Middleware stack: %s", [type(m).__name__ for m in middleware])

    # Create agent with middleware
    # Server provides its own checkpointer -- do not create one here
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt,
        context_schema=EnhancedContextSchema,
        middleware=middleware,
        debug=context.enable_debug,
        name="agent_enhanced",
    )

    if context.enable_debug:
        logger.info("Enhanced graph built successfully with nodes: %s", list(agent.nodes.keys()))
        logger.info("Middleware stack: %s", [type(m).__name__ for m in middleware])

    return agent  # type: ignore


# Alternative: Minimal middleware for development/testing
def build_graph_minimal_middleware(config: RunnableConfig | None = None) -> CompiledStateGraph:
    """Build agent with minimal middleware for faster iteration.

    Only includes essential middleware (configurable via context):
    - Model retry (handle transient failures)
    - Model call limit (prevent runaway)

    Use this for local development and testing.
    """
    context = EnhancedContextSchema.from_runnable_config(config, fallback_env=True)

    if context.enable_debug:
        logger.info("Building minimal graph with context: %s", context)

    llm = init_model(model=context.model, temperature=context.temperature)
    tools = create_sql_tools(llm=llm, context=context)

    # Build system prompt based on detected database type
    db_type = _detect_db_type(context.snowflake_uri)
    prompt = build_system_prompt(db_type=db_type)

    middleware: list[Any] = []

    # Model retry first (closest to model)
    if context.retry_max_retries > 0:
        middleware.append(
            ModelRetryMiddleware(
                max_retries=context.retry_max_retries,
                backoff_factor=context.retry_backoff_factor,
                initial_delay=context.retry_initial_delay,
            )
        )
        if context.enable_debug:
            logger.info("Added ModelRetryMiddleware: max_retries=%s", context.retry_max_retries)

    # Model call limit (after retry)
    if context.model_call_run_limit > 0:
        middleware.append(
            ModelCallLimitMiddleware(
                run_limit=context.model_call_run_limit,
                exit_behavior=context.model_call_exit_behavior,
            )
        )
        if context.enable_debug:
            logger.info(
                "Added ModelCallLimitMiddleware: run_limit=%s", context.model_call_run_limit
            )

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt,
        context_schema=EnhancedContextSchema,
        middleware=middleware,
        debug=context.enable_debug,
        name="agent_minimal",
    )

    if context.enable_debug:
        logger.info("Minimal graph built with %d middleware components", len(middleware))

    return agent  # type: ignore


# Export both versions
graph_enhanced = build_graph_with_middleware
graph_minimal = build_graph_minimal_middleware
