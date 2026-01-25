"""Runtime context schema for per-invocation configuration.

This module defines the ContextSchema following LangGraph's convention.
Supports layered configuration: Runtime → Environment → Defaults.

Context is read-only and not persisted between invocations.

## Purpose & LangGraph Integration

The ContextSchema serves two purposes:

1. **Assistant Configuration (Dev Server/API)**
   - The entire schema is used by the dev server to expose configurable fields
   - When creating assistants via LangGraph API/Studio, these fields become available
   - Runtime values are passed via `graph.invoke(..., context={...})`

2. **LangGraph Studio UI Enhancement** (optional but recommended)
   The following metadata elements enhance the Studio UI but are not functionally required:

   - `Annotated[str, {"__template_metadata__": {"kind": "llm"}}]`
     → Shows LLM selector dropdown instead of text input (Studio UI only)

   - `metadata={"description": "..."}`
     → Displays as tooltips/help text in Studio UI forms

   - `metadata={"json_schema_extra": {"langgraph_nodes": [...]}}`
     → Ties configuration to specific graph nodes (for scoped configs)

Without these Studio UI enhancements, fields still work but appear as generic text inputs.
"""

import logging
import os
from dataclasses import dataclass, field, fields
from typing import Annotated

from langchain_core.runnables import RunnableConfig

from .config import settings

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class ContextSchema:
    """Runtime context schema for Snowflake agent.

    Configuration priority (layered):
    1. Runtime context (via LangGraph API, per-conversation) - highest priority
    2. Environment variables (deployment-time)
    3. Default values (defined in config.py) - lowest priority
    """

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

    # Snowflake Connection - Individual components (for granular override)
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
            "description": "Enforce read-only database access",
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

    @classmethod
    def from_runnable_config(
        cls, config: RunnableConfig | None = None, fallback_env: bool = True
    ) -> "ContextSchema":
        """Create ContextSchema from LangGraph RunnableConfig.

        Called by LangGraph at runtime with user-selected values from the
        Assistant Configuration panel in LangGraph Studio.

        Args:
            config: RunnableConfig from LangGraph API containing user selections
            fallback_env: If True, use environment defaults for missing values (default: True)

        Returns:
            ContextSchema instance with values from config or environment/defaults

        Example:
            >>> # LangGraph calls this automatically at runtime
            >>> config = RunnableConfig(
            ...     configurable={
            ...         "model": "claude-sonnet-4-5-20250929",
            ...         "snowflake_uri": "snowflake://..."
            ...     }
            ... )
            >>> context = ContextSchema.from_runnable_config(config)
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
    def from_env(cls) -> "ContextSchema":
        """Create ContextSchema from environment variables.

        Reads from environment variables with SNOWFLAKE_AGENT_ prefix.
        Falls back to default values from config.py if not set.

        Environment variables:
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

        Returns:
            ContextSchema instance with values from environment or defaults
        """
        return cls(
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
        )

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
