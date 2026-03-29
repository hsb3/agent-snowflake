"""Enhanced runtime context schema with middleware configuration.

This module extends the base ContextSchema with middleware-specific parameters
for graph2.py (agent_enhanced and agent_minimal).

Supports the same layered configuration: Runtime -> Environment -> Defaults.
"""

import logging
import os
from dataclasses import dataclass, field, fields
from typing import Annotated, Literal, cast

from langchain_core.runnables import RunnableConfig

from .config import settings
from .context import ContextSchema

logger = logging.getLogger(__name__)


@dataclass(kw_only=True, repr=False)
class EnhancedContextSchema(ContextSchema):
    """Runtime context schema for Snowflake agent with middleware configuration.

    Extends base ContextSchema with middleware-specific parameters for:
    - Human-in-the-loop
    - Model/tool call limits
    - Retry configuration
    - Summarization
    - Model fallback
    - Todo list

    Configuration priority (layered):
    1. Runtime context (via LangGraph API, per-conversation) - highest priority
    2. Environment variables (deployment-time)
    3. Default values (defined below) - lowest priority
    """

    # ========================================================================
    # Middleware Configuration
    # ========================================================================

    # Human-in-the-Loop
    enable_hitl: bool = field(
        default=True,
        metadata={
            "description": "Enable human-in-the-loop for sql_db_query tool (only works if read_only=false)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    hitl_allowed_decisions: str = field(
        default="approve,edit,reject",
        metadata={
            "description": "Comma-separated allowed HITL decisions: approve, edit, reject",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Model Call Limits
    model_call_thread_limit: int = field(
        default=10,
        metadata={
            "description": "Maximum model calls across entire conversation thread (0=unlimited)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    model_call_run_limit: int = field(
        default=5,
        metadata={
            "description": "Maximum model calls per single invocation/run (0=unlimited)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    model_call_exit_behavior: Literal["end", "error"] = field(
        default="end",
        metadata={
            "description": "Behavior when model call limit reached: 'end' (graceful) or 'error' (exception)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Tool Call Limits (Global)
    tool_call_thread_limit: int = field(
        default=20,
        metadata={
            "description": "Maximum tool calls (all tools) across entire thread (0=unlimited)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    tool_call_run_limit: int = field(
        default=10,
        metadata={
            "description": "Maximum tool calls (all tools) per single run (0=unlimited)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    tool_call_exit_behavior: Literal["continue", "error", "end"] = field(
        default="continue",
        metadata={
            "description": "Behavior when tool call limit reached: 'continue' (block with error), 'end', or 'error'",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Tool Call Limits (sql_db_query specific)
    sql_query_thread_limit: int = field(
        default=10,
        metadata={
            "description": "Maximum sql_db_query calls across entire thread (0=unlimited)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    sql_query_run_limit: int = field(
        default=5,
        metadata={
            "description": "Maximum sql_db_query calls per single run (0=unlimited)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Model Retry Configuration
    retry_max_retries: int = field(
        default=3,
        metadata={
            "description": "Maximum retry attempts for failed model calls (after initial attempt)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    retry_backoff_factor: float = field(
        default=2.0,
        metadata={
            "description": "Exponential backoff multiplier for retries (2.0 = double each time)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    retry_initial_delay: float = field(
        default=1.0,
        metadata={
            "description": "Initial delay in seconds before first retry",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    retry_max_delay: float = field(
        default=60.0,
        metadata={
            "description": "Maximum delay in seconds between retries (caps exponential growth)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    retry_jitter: bool = field(
        default=True,
        metadata={
            "description": "Add random jitter (+-25%) to retry delays to avoid thundering herd",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Summarization Configuration
    enable_summarization: bool = field(
        default=True,
        metadata={
            "description": "Enable automatic conversation summarization when token limit reached",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    summarization_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="gpt-4.1-mini",
        metadata={
            "description": "LLM model for generating summaries (use cheaper model)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    summarization_trigger_tokens: int = field(
        default=4000,
        metadata={
            "description": "Token count threshold to trigger summarization",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    summarization_keep_messages: int = field(
        default=20,
        metadata={
            "description": "Number of most recent messages to preserve unmodified after summarization",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Todo List Configuration
    enable_todo: bool = field(
        default=True,
        metadata={
            "description": "Enable todo list middleware for task planning and tracking",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Model Fallback Configuration
    enable_fallback: bool = field(
        default=True,
        metadata={
            "description": "Enable automatic fallback to backup models on primary model failure",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    fallback_models: str = field(
        default="",
        metadata={
            "description": "Comma-separated list of fallback models (empty = auto-detect based on primary model)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    @classmethod
    def from_runnable_config(
        cls, config: RunnableConfig | None = None, fallback_env: bool = True
    ) -> "EnhancedContextSchema":
        """Create EnhancedContextSchema from LangGraph RunnableConfig.

        Called by LangGraph at runtime with user-selected values from the
        Assistant Configuration panel in LangGraph Studio.

        Args:
            config: RunnableConfig from LangGraph API containing user selections
            fallback_env: If True, use environment defaults for missing values (default: True)

        Returns:
            EnhancedContextSchema instance with values from config or environment/defaults

        Example:
            >>> # LangGraph calls this automatically at runtime
            >>> config = RunnableConfig(
            ...     configurable={
            ...         "model": "claude-sonnet-4-5-20250929",
            ...         "model_call_thread_limit": 15,
            ...     }
            ... )
            >>> context = EnhancedContextSchema.from_runnable_config(config)
        """
        configurable = (config.get("configurable") or {}) if config else {}

        # Get environment defaults if fallback enabled
        if fallback_env:
            env_defaults = cls.from_env()
            # Extract configured values, falling back to environment defaults
            kwargs = {}
            for field_info in fields(cls):
                if field_info.name in configurable:
                    kwargs[field_info.name] = configurable[field_info.name]
                else:
                    kwargs[field_info.name] = getattr(env_defaults, field_info.name)
            return cls(**kwargs)

        # Only use values from config (no fallback)
        kwargs = {}
        for field_info in fields(cls):
            if field_info.name in configurable:
                kwargs[field_info.name] = configurable[field_info.name]
        return cls(**kwargs)

    @classmethod
    def from_env(cls) -> "EnhancedContextSchema":
        """Create EnhancedContextSchema from environment variables.

        Reads from environment variables with AGENT_ prefix.
        Falls back to default values if not set.

        Loads base configuration via ContextSchema.from_env(), then adds
        middleware-specific environment variables.

        Returns:
            EnhancedContextSchema instance with values from environment or defaults
        """
        # Get all base fields from parent's from_env()
        base = ContextSchema.from_env()
        base_kwargs = {
            field_info.name: getattr(base, field_info.name) for field_info in fields(ContextSchema)
        }

        return cls(
            # Base configuration from parent
            **base_kwargs,
            # Middleware configuration
            enable_hitl=os.environ.get("AGENT_ENABLE_HITL", "true").lower() == "true",
            hitl_allowed_decisions=os.environ.get(
                "AGENT_HITL_ALLOWED_DECISIONS", "approve,edit,reject"
            ),
            model_call_thread_limit=int(os.environ.get("AGENT_MODEL_CALL_THREAD_LIMIT", "10")),
            model_call_run_limit=int(os.environ.get("AGENT_MODEL_CALL_RUN_LIMIT", "5")),
            model_call_exit_behavior=cast(
                Literal["end", "error"],
                os.environ.get("AGENT_MODEL_CALL_EXIT_BEHAVIOR", "end"),
            ),
            tool_call_thread_limit=int(os.environ.get("AGENT_TOOL_CALL_THREAD_LIMIT", "20")),
            tool_call_run_limit=int(os.environ.get("AGENT_TOOL_CALL_RUN_LIMIT", "10")),
            tool_call_exit_behavior=cast(
                Literal["continue", "error", "end"],
                os.environ.get("AGENT_TOOL_CALL_EXIT_BEHAVIOR", "continue"),
            ),
            sql_query_thread_limit=int(os.environ.get("AGENT_SQL_QUERY_THREAD_LIMIT", "10")),
            sql_query_run_limit=int(os.environ.get("AGENT_SQL_QUERY_RUN_LIMIT", "5")),
            retry_max_retries=int(os.environ.get("AGENT_RETRY_MAX_RETRIES", "3")),
            retry_backoff_factor=float(os.environ.get("AGENT_RETRY_BACKOFF_FACTOR", "2.0")),
            retry_initial_delay=float(os.environ.get("AGENT_RETRY_INITIAL_DELAY", "1.0")),
            retry_max_delay=float(os.environ.get("AGENT_RETRY_MAX_DELAY", "60.0")),
            retry_jitter=os.environ.get("AGENT_RETRY_JITTER", "true").lower() == "true",
            enable_summarization=os.environ.get("AGENT_ENABLE_SUMMARIZATION", "true").lower()
            == "true",
            summarization_model=os.environ.get("AGENT_SUMMARIZATION_MODEL", "gpt-4.1-mini"),
            summarization_trigger_tokens=int(
                os.environ.get("AGENT_SUMMARIZATION_TRIGGER_TOKENS", "4000")
            ),
            summarization_keep_messages=int(
                os.environ.get("AGENT_SUMMARIZATION_KEEP_MESSAGES", "20")
            ),
            enable_todo=os.environ.get("AGENT_ENABLE_TODO", "true").lower() == "true",
            enable_fallback=os.environ.get("AGENT_ENABLE_FALLBACK", "true").lower() == "true",
            fallback_models=os.environ.get("AGENT_FALLBACK_MODELS", ""),
        )

    def get_middleware_config(self) -> dict:
        """Extract middleware-specific configuration as a dictionary.

        Useful for passing to middleware constructors or logging.

        Returns:
            Dictionary of middleware configuration fields only
        """
        # Middleware fields are those defined in EnhancedContextSchema but not in ContextSchema
        base_field_names = {f.name for f in fields(ContextSchema)}
        return {
            field_info.name: getattr(self, field_info.name)
            for field_info in fields(self)
            if field_info.name not in base_field_names
        }
