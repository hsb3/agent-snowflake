"""SQL agent graph definition.

This module creates and compiles the LangGraph agent for database interactions.
Middleware is conditionally assembled based on ContextSchema configuration.
"""

import logging
from typing import Any, Literal

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

from .context import ContextSchema
from .prompts import build_system_prompt
from .tools import create_sql_tools
from .utils import init_model

logger = logging.getLogger(__name__)


def _detect_db_type(context: ContextSchema) -> Literal["sqlite", "snowflake"]:
    """Detect database type from context configuration.

    Checks the URI first, then falls back to checking whether individual
    Snowflake connection parameters are set.

    Args:
        context: Agent context with database configuration

    Returns:
        "snowflake" if URI or individual params indicate Snowflake, otherwise "sqlite"
    """
    if context.database_uri.startswith("snowflake://"):
        return "snowflake"
    if context.snowflake_account:
        return "snowflake"
    return "sqlite"


def _build_middleware(context: ContextSchema) -> list[Any]:
    """Assemble middleware stack based on context configuration.

    Middleware ordering (innermost to outermost):
    1. ModelRetryMiddleware - retry transient failures closest to model
    2. ModelFallbackMiddleware - fall back to other models on failure
    3. ModelCallLimitMiddleware - enforce model call limits
    4. ToolCallLimitMiddleware(s) - enforce tool call limits
    5. HumanInTheLoopMiddleware - approval flow for dangerous operations
    6. SummarizationMiddleware - context window management
    7. TodoListMiddleware - task planning

    Args:
        context: Agent configuration with middleware flags

    Returns:
        List of middleware instances (may be empty)
    """
    middleware: list[Any] = []

    # 1. Model retry
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

    # 2. Model fallback
    if context.enable_fallback:
        if context.fallback_models:
            fallback_models = [m.strip() for m in context.fallback_models.split(",")]
        else:
            primary_model = context.model
            if "gpt-4" in primary_model:
                fallback_models = ["gpt-4.1-mini", "claude-haiku-4-5-20251001"]
            elif "claude" in primary_model:
                fallback_models = ["gpt-4.1", "gpt-4.1-mini"]
            else:
                fallback_models = ["gpt-4.1-mini"]

        if fallback_models:
            middleware.append(ModelFallbackMiddleware(*fallback_models))

    # 3. Model call limit
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

    # 4. Tool call limits — global
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

    # Tool call limits — sql_db_query specific
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

    # 5. Human-in-the-loop (only when not read-only)
    if context.enable_hitl and not context.read_only:
        allowed_decisions = [d.strip() for d in context.hitl_allowed_decisions.split(",")]
        interrupt_config: dict[str, bool | dict[str, list[str]]] = {
            "sql_db_query": {"allowed_decisions": allowed_decisions},
            "sql_db_schema": False,
            "sql_db_list_tables": False,
        }
        middleware.append(HumanInTheLoopMiddleware(interrupt_on=interrupt_config))  # type: ignore[arg-type]

    # 6. Summarization
    if context.enable_summarization:
        middleware.append(
            SummarizationMiddleware(
                model=context.summarization_model,
                trigger=("tokens", context.summarization_trigger_tokens),
                keep=("messages", context.summarization_keep_messages),
            )
        )

    # 7. Todo list
    if context.enable_todo:
        middleware.append(TodoListMiddleware())

    return middleware


def build_graph(config: RunnableConfig | None = None) -> CompiledStateGraph:
    """Build and compile the SQL agent graph.

    This is the single entry point called by LangGraph. It loads context from
    RunnableConfig, creates tools, and conditionally assembles middleware
    based on configuration flags.

    Args:
        config: Optional RunnableConfig from LangGraph runtime

    Returns:
        Compiled agent graph ready for invocation
    """
    context = ContextSchema.from_runnable_config(config, fallback_env=True)

    if context.enable_debug:
        logger.info("Building graph with context: %s", context)

    # Initialize LLM
    llm = init_model(model=context.model, temperature=context.temperature)

    # Create SQL tools with guardrails
    tools = create_sql_tools(llm=llm, context=context)

    if context.enable_debug:
        logger.info("Created %d tools: %s", len(tools), [t.name for t in tools])

    # Build system prompt based on detected database type
    db_type = _detect_db_type(context)
    prompt = build_system_prompt(db_type=db_type)

    # Assemble middleware
    middleware = _build_middleware(context)

    if context.enable_debug:
        logger.info("Using db_type=%s for system prompt", db_type)
        logger.info(
            "Configured %d middleware: %s",
            len(middleware),
            [type(m).__name__ for m in middleware],
        )

    # Create agent
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=prompt,
        context_schema=ContextSchema,
        middleware=middleware,
        debug=context.enable_debug,
        name="agent",
    )

    if context.enable_debug:
        logger.info("Graph built successfully with nodes: %s", list(agent.nodes.keys()))

    return agent  # type: ignore
