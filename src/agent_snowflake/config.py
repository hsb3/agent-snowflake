"""Base configuration settings with defaults and environment variable loading.

This module provides default values for the agent. Environment-based overrides
are handled via Settings.from_env() and exposed at runtime via ContextSchema.
"""

import os
from dataclasses import dataclass
from typing import Literal


ModelProvider = Literal["anthropic", "openai", "google"]


@dataclass
class Settings:
    """Default settings for Snowflake agent.

    Provides default values and environment variable loading.
    Configuration priority: Runtime context > Environment > Defaults
    """

    # Model Configuration
    model: str = "claude-haiku-4-5"
    temperature: float = 0.0

    # Snowflake Connection
    snowflake_uri: str = ""
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_database: str = ""
    snowflake_schema: str = ""
    snowflake_warehouse: str = ""
    snowflake_role: str = ""

    # Agent Configuration - Guardrails
    allowed_schemas: str = "*"
    allowed_tables: str = "*"
    read_only: bool = True
    query_timeout: int = 30

    # Execution Settings
    max_iterations: int = 25
    enable_debug: bool = False

    # Development Settings
    cors_origins: str = "*"
    environment: str = "development"

    # LangGraph node names for configuration
    langgraph_node_names: list[str] | None = None

    def __post_init__(self):
        """Initialize langgraph_node_names if not provided."""
        if self.langgraph_node_names is None:
            self.langgraph_node_names = ["agent"]

        # Validate CORS in production
        if self.environment != "development" and self.cors_origins == "*":
            import warnings

            warnings.warn(
                f"CORS_ORIGINS is set to '*' but ENVIRONMENT is '{self.environment}'. "
                "This is a security risk in production!",
                RuntimeWarning,
                stacklevel=2,
            )

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables.

        Environment variables:
        - SNOWFLAKE_AGENT_MODEL: Main model
        - SNOWFLAKE_AGENT_TEMPERATURE: Model temperature (float)
        - SNOWFLAKE_AGENT_SNOWFLAKE_URI: Snowflake connection URI
        - SNOWFLAKE_AGENT_SNOWFLAKE_ACCOUNT: Snowflake account
        - SNOWFLAKE_AGENT_SNOWFLAKE_USER: Snowflake user
        - SNOWFLAKE_AGENT_SNOWFLAKE_PASSWORD: Snowflake password
        - SNOWFLAKE_AGENT_SNOWFLAKE_DATABASE: Snowflake database
        - SNOWFLAKE_AGENT_SNOWFLAKE_SCHEMA: Snowflake schema
        - SNOWFLAKE_AGENT_SNOWFLAKE_WAREHOUSE: Snowflake warehouse
        - SNOWFLAKE_AGENT_SNOWFLAKE_ROLE: Snowflake role
        - SNOWFLAKE_AGENT_ALLOWED_SCHEMAS: Comma-separated allowed schemas
        - SNOWFLAKE_AGENT_ALLOWED_TABLES: Comma-separated allowed tables
        - SNOWFLAKE_AGENT_READ_ONLY: Enforce read-only (true/false)
        - SNOWFLAKE_AGENT_QUERY_TIMEOUT: Query timeout in seconds
        - SNOWFLAKE_AGENT_MAX_ITERATIONS: Max agent iterations
        - SNOWFLAKE_AGENT_ENABLE_DEBUG: Enable debug mode (true/false)
        - SNOWFLAKE_AGENT_CORS_ORIGINS: Comma-separated CORS origins
        - SNOWFLAKE_AGENT_ENVIRONMENT: Environment (development/staging/production)

        Returns:
            Settings instance with values from environment or defaults
        """
        return cls(
            model=os.environ.get("SNOWFLAKE_AGENT_MODEL", "claude-sonnet-4-5-20250929"),
            temperature=float(os.environ.get("SNOWFLAKE_AGENT_TEMPERATURE", "0.0")),
            snowflake_uri=os.environ.get("SNOWFLAKE_AGENT_SNOWFLAKE_URI", ""),
            snowflake_account=os.environ.get("SNOWFLAKE_AGENT_SNOWFLAKE_ACCOUNT", ""),
            snowflake_user=os.environ.get("SNOWFLAKE_AGENT_SNOWFLAKE_USER", ""),
            snowflake_password=os.environ.get("SNOWFLAKE_AGENT_SNOWFLAKE_PASSWORD", ""),
            snowflake_database=os.environ.get("SNOWFLAKE_AGENT_SNOWFLAKE_DATABASE", ""),
            snowflake_schema=os.environ.get("SNOWFLAKE_AGENT_SNOWFLAKE_SCHEMA", ""),
            snowflake_warehouse=os.environ.get(
                "SNOWFLAKE_AGENT_SNOWFLAKE_WAREHOUSE", ""
            ),
            snowflake_role=os.environ.get("SNOWFLAKE_AGENT_SNOWFLAKE_ROLE", ""),
            allowed_schemas=os.environ.get("SNOWFLAKE_AGENT_ALLOWED_SCHEMAS", "*"),
            allowed_tables=os.environ.get("SNOWFLAKE_AGENT_ALLOWED_TABLES", "*"),
            read_only=os.environ.get("SNOWFLAKE_AGENT_READ_ONLY", "true").lower()
            == "true",
            query_timeout=int(os.environ.get("SNOWFLAKE_AGENT_QUERY_TIMEOUT", "30")),
            max_iterations=int(os.environ.get("SNOWFLAKE_AGENT_MAX_ITERATIONS", "25")),
            enable_debug=os.environ.get("SNOWFLAKE_AGENT_ENABLE_DEBUG", "false").lower()
            == "true",
            cors_origins=os.environ.get("SNOWFLAKE_AGENT_CORS_ORIGINS", "*"),
            environment=os.environ.get("SNOWFLAKE_AGENT_ENVIRONMENT", "development"),
        )


# Module-level instance for easy access
settings = Settings.from_env()
