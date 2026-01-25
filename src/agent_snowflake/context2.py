"""Enhanced runtime context schema with middleware configuration.

This module extends the base ContextSchema with middleware-specific parameters
for graph2.py (agent_enhanced and agent_minimal).

Supports the same layered configuration: Runtime → Environment → Defaults.
"""

import logging
import os
from dataclasses import dataclass, field, fields
from typing import Annotated, Literal, cast

from langchain_core.runnables import RunnableConfig

from .config import settings

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class EnhancedContextSchema:
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
    # Base Configuration (from original ContextSchema)
    # ========================================================================

    # Model Configuration
    model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default=settings.model,
        metadata={
            "description": "LLM model for the agent",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    temperature: float = field(
        default=settings.temperature,
        metadata={
            "description": "Model temperature (0.0=deterministic, 1.0=creative)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Snowflake Connection - Primary configurable
    snowflake_uri: str = field(
        default=settings.snowflake_uri,
        metadata={
            "description": "Snowflake connection URI: snowflake://user:password@account/database/schema?warehouse=wh&role=role",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Snowflake Connection - Individual components
    snowflake_account: str = field(
        default=settings.snowflake_account,
        metadata={
            "description": "Snowflake account identifier",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    snowflake_user: str = field(
        default=settings.snowflake_user,
        metadata={
            "description": "Snowflake username",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    snowflake_password: str = field(
        default=settings.snowflake_password,
        metadata={
            "description": "Snowflake password",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    snowflake_database: str = field(
        default=settings.snowflake_database,
        metadata={
            "description": "Snowflake database name",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    snowflake_schema: str = field(
        default=settings.snowflake_schema,
        metadata={
            "description": "Snowflake schema name",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    snowflake_warehouse: str = field(
        default=settings.snowflake_warehouse,
        metadata={
            "description": "Snowflake warehouse name",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    snowflake_role: str = field(
        default=settings.snowflake_role,
        metadata={
            "description": "Snowflake role name",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Agent Configuration - Guardrails
    allowed_schemas: str = field(
        default=settings.allowed_schemas,
        metadata={
            "description": "Comma-separated list of allowed schemas (* for all)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    allowed_tables: str = field(
        default=settings.allowed_tables,
        metadata={
            "description": "Comma-separated list of allowed tables (* for all)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    read_only: bool = field(
        default=settings.read_only,
        metadata={
            "description": "Enforce read-only database access (disables human-in-the-loop)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    query_timeout: int = field(
        default=settings.query_timeout,
        metadata={
            "description": "Query execution timeout in seconds",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # Execution Settings
    max_iterations: int = field(
        default=settings.max_iterations,
        metadata={
            "description": "Maximum agent iterations before stopping",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    enable_debug: bool = field(
        default=settings.enable_debug,
        metadata={
            "description": "Enable debug mode with verbose logging",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

    # ========================================================================
    # Middleware Configuration (NEW)
    # ========================================================================

    # Middleware Mode Selection
    middleware_mode: str = field(
        default="enhanced",
        metadata={
            "description": "Middleware mode: 'enhanced' (all middleware), 'minimal' (limits+retry only), 'none' (no middleware)",
            "json_schema_extra": {"langgraph_nodes": settings.langgraph_node_names},
        },
    )

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
            "description": "Add random jitter (±25%) to retry delays to avoid thundering herd",
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
        default="gpt-4o-mini",
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
            ...         "middleware_mode": "enhanced",
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

        Reads from environment variables with SNOWFLAKE_AGENT_ prefix.
        Falls back to default values if not set.

        Environment variables (base configuration):
        - SNOWFLAKE_AGENT_MODEL: LLM model
        - SNOWFLAKE_AGENT_TEMPERATURE: Model temperature
        - SNOWFLAKE_AGENT_SNOWFLAKE_URI: Snowflake connection URI
        - SNOWFLAKE_AGENT_SNOWFLAKE_*: Individual Snowflake connection params
        - SNOWFLAKE_AGENT_ALLOWED_SCHEMAS: Comma-separated allowed schemas
        - SNOWFLAKE_AGENT_ALLOWED_TABLES: Comma-separated allowed tables
        - SNOWFLAKE_AGENT_READ_ONLY: Enforce read-only (true/false)
        - SNOWFLAKE_AGENT_QUERY_TIMEOUT: Query timeout in seconds
        - SNOWFLAKE_AGENT_MAX_ITERATIONS: Max iterations
        - SNOWFLAKE_AGENT_ENABLE_DEBUG: Enable debug mode (true/false)

        Environment variables (middleware configuration):
        - SNOWFLAKE_AGENT_MIDDLEWARE_MODE: Middleware mode (enhanced/minimal/none)
        - SNOWFLAKE_AGENT_ENABLE_HITL: Enable human-in-the-loop (true/false)
        - SNOWFLAKE_AGENT_MODEL_CALL_THREAD_LIMIT: Model call thread limit
        - SNOWFLAKE_AGENT_MODEL_CALL_RUN_LIMIT: Model call run limit
        - SNOWFLAKE_AGENT_TOOL_CALL_THREAD_LIMIT: Tool call thread limit
        - SNOWFLAKE_AGENT_TOOL_CALL_RUN_LIMIT: Tool call run limit
        - SNOWFLAKE_AGENT_SQL_QUERY_THREAD_LIMIT: SQL query thread limit
        - SNOWFLAKE_AGENT_SQL_QUERY_RUN_LIMIT: SQL query run limit
        - SNOWFLAKE_AGENT_RETRY_MAX_RETRIES: Max retry attempts
        - SNOWFLAKE_AGENT_RETRY_BACKOFF_FACTOR: Retry backoff multiplier
        - SNOWFLAKE_AGENT_RETRY_INITIAL_DELAY: Initial retry delay (seconds)
        - SNOWFLAKE_AGENT_ENABLE_SUMMARIZATION: Enable summarization (true/false)
        - SNOWFLAKE_AGENT_SUMMARIZATION_MODEL: Model for summaries
        - SNOWFLAKE_AGENT_SUMMARIZATION_TRIGGER_TOKENS: Token trigger threshold
        - SNOWFLAKE_AGENT_SUMMARIZATION_KEEP_MESSAGES: Messages to preserve
        - SNOWFLAKE_AGENT_ENABLE_TODO: Enable todo list (true/false)
        - SNOWFLAKE_AGENT_ENABLE_FALLBACK: Enable model fallback (true/false)
        - SNOWFLAKE_AGENT_FALLBACK_MODELS: Comma-separated fallback models

        Returns:
            EnhancedContextSchema instance with values from environment or defaults
        """
        return cls(
            # Base configuration
            model=os.environ.get("SNOWFLAKE_AGENT_MODEL", settings.model),
            temperature=float(
                os.environ.get("SNOWFLAKE_AGENT_TEMPERATURE", str(settings.temperature))
            ),
            snowflake_uri=os.environ.get("SNOWFLAKE_AGENT_SNOWFLAKE_URI", settings.snowflake_uri),
            snowflake_account=os.environ.get(
                "SNOWFLAKE_AGENT_SNOWFLAKE_ACCOUNT", settings.snowflake_account
            ),
            snowflake_user=os.environ.get(
                "SNOWFLAKE_AGENT_SNOWFLAKE_USER", settings.snowflake_user
            ),
            snowflake_password=os.environ.get(
                "SNOWFLAKE_AGENT_SNOWFLAKE_PASSWORD", settings.snowflake_password
            ),
            snowflake_database=os.environ.get(
                "SNOWFLAKE_AGENT_SNOWFLAKE_DATABASE", settings.snowflake_database
            ),
            snowflake_schema=os.environ.get(
                "SNOWFLAKE_AGENT_SNOWFLAKE_SCHEMA", settings.snowflake_schema
            ),
            snowflake_warehouse=os.environ.get(
                "SNOWFLAKE_AGENT_SNOWFLAKE_WAREHOUSE", settings.snowflake_warehouse
            ),
            snowflake_role=os.environ.get(
                "SNOWFLAKE_AGENT_SNOWFLAKE_ROLE", settings.snowflake_role
            ),
            allowed_schemas=os.environ.get(
                "SNOWFLAKE_AGENT_ALLOWED_SCHEMAS", settings.allowed_schemas
            ),
            allowed_tables=os.environ.get(
                "SNOWFLAKE_AGENT_ALLOWED_TABLES", settings.allowed_tables
            ),
            read_only=os.environ.get(
                "SNOWFLAKE_AGENT_READ_ONLY", str(settings.read_only).lower()
            ).lower()
            == "true",
            query_timeout=int(
                os.environ.get("SNOWFLAKE_AGENT_QUERY_TIMEOUT", str(settings.query_timeout))
            ),
            max_iterations=int(
                os.environ.get("SNOWFLAKE_AGENT_MAX_ITERATIONS", str(settings.max_iterations))
            ),
            enable_debug=os.environ.get(
                "SNOWFLAKE_AGENT_ENABLE_DEBUG", str(settings.enable_debug).lower()
            ).lower()
            == "true",
            # Middleware configuration
            middleware_mode=os.environ.get("SNOWFLAKE_AGENT_MIDDLEWARE_MODE", "enhanced"),
            enable_hitl=os.environ.get("SNOWFLAKE_AGENT_ENABLE_HITL", "true").lower() == "true",
            hitl_allowed_decisions=os.environ.get(
                "SNOWFLAKE_AGENT_HITL_ALLOWED_DECISIONS", "approve,edit,reject"
            ),
            model_call_thread_limit=int(
                os.environ.get("SNOWFLAKE_AGENT_MODEL_CALL_THREAD_LIMIT", "10")
            ),
            model_call_run_limit=int(os.environ.get("SNOWFLAKE_AGENT_MODEL_CALL_RUN_LIMIT", "5")),
            model_call_exit_behavior=cast(
                Literal["end", "error"],
                os.environ.get("SNOWFLAKE_AGENT_MODEL_CALL_EXIT_BEHAVIOR", "end"),
            ),
            tool_call_thread_limit=int(
                os.environ.get("SNOWFLAKE_AGENT_TOOL_CALL_THREAD_LIMIT", "20")
            ),
            tool_call_run_limit=int(os.environ.get("SNOWFLAKE_AGENT_TOOL_CALL_RUN_LIMIT", "10")),
            tool_call_exit_behavior=cast(
                Literal["continue", "error", "end"],
                os.environ.get("SNOWFLAKE_AGENT_TOOL_CALL_EXIT_BEHAVIOR", "continue"),
            ),
            sql_query_thread_limit=int(
                os.environ.get("SNOWFLAKE_AGENT_SQL_QUERY_THREAD_LIMIT", "10")
            ),
            sql_query_run_limit=int(os.environ.get("SNOWFLAKE_AGENT_SQL_QUERY_RUN_LIMIT", "5")),
            retry_max_retries=int(os.environ.get("SNOWFLAKE_AGENT_RETRY_MAX_RETRIES", "3")),
            retry_backoff_factor=float(
                os.environ.get("SNOWFLAKE_AGENT_RETRY_BACKOFF_FACTOR", "2.0")
            ),
            retry_initial_delay=float(os.environ.get("SNOWFLAKE_AGENT_RETRY_INITIAL_DELAY", "1.0")),
            retry_max_delay=float(os.environ.get("SNOWFLAKE_AGENT_RETRY_MAX_DELAY", "60.0")),
            retry_jitter=os.environ.get("SNOWFLAKE_AGENT_RETRY_JITTER", "true").lower() == "true",
            enable_summarization=os.environ.get(
                "SNOWFLAKE_AGENT_ENABLE_SUMMARIZATION", "true"
            ).lower()
            == "true",
            summarization_model=os.environ.get(
                "SNOWFLAKE_AGENT_SUMMARIZATION_MODEL", "gpt-4o-mini"
            ),
            summarization_trigger_tokens=int(
                os.environ.get("SNOWFLAKE_AGENT_SUMMARIZATION_TRIGGER_TOKENS", "4000")
            ),
            summarization_keep_messages=int(
                os.environ.get("SNOWFLAKE_AGENT_SUMMARIZATION_KEEP_MESSAGES", "20")
            ),
            enable_todo=os.environ.get("SNOWFLAKE_AGENT_ENABLE_TODO", "true").lower() == "true",
            enable_fallback=os.environ.get("SNOWFLAKE_AGENT_ENABLE_FALLBACK", "true").lower()
            == "true",
            fallback_models=os.environ.get("SNOWFLAKE_AGENT_FALLBACK_MODELS", ""),
        )

    def get_middleware_config(self) -> dict:
        """Extract middleware-specific configuration as a dictionary.

        Useful for passing to middleware constructors or logging.

        Returns:
            Dictionary of middleware configuration fields only
        """
        middleware_fields = {
            "middleware_mode",
            "enable_hitl",
            "hitl_allowed_decisions",
            "model_call_thread_limit",
            "model_call_run_limit",
            "model_call_exit_behavior",
            "tool_call_thread_limit",
            "tool_call_run_limit",
            "tool_call_exit_behavior",
            "sql_query_thread_limit",
            "sql_query_run_limit",
            "retry_max_retries",
            "retry_backoff_factor",
            "retry_initial_delay",
            "retry_max_delay",
            "retry_jitter",
            "enable_summarization",
            "summarization_model",
            "summarization_trigger_tokens",
            "summarization_keep_messages",
            "enable_todo",
            "enable_fallback",
            "fallback_models",
        }
        return {
            field_info.name: getattr(self, field_info.name)
            for field_info in fields(self)
            if field_info.name in middleware_fields
        }

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Useful for serialization, logging, or passing to functions.

        Returns:
            Dictionary representation of all configuration fields
        """
        return {field_info.name: getattr(self, field_info.name) for field_info in fields(self)}

    def __repr__(self) -> str:
        """String representation showing key configuration values."""
        field_strs = [
            f"{field_info.name}={getattr(self, field_info.name)!r}" for field_info in fields(self)
        ]
        return f"{self.__class__.__name__}({', '.join(field_strs)})"
