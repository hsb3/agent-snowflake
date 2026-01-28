"""Utility functions for the Snowflake agent."""

import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from langchain.chat_models import init_chat_model
from langchain_community.utilities import SQLDatabase
from langchain_core.language_models import BaseChatModel
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from .context import ContextSchema

if TYPE_CHECKING:
    from .context2 import EnhancedContextSchema

logger = logging.getLogger(__name__)


def init_model(
    model: str,
    temperature: float = 0.0,
    **kwargs: Any,
) -> BaseChatModel:
    """Initialize a chat model with special case handling.

    Wrapper around init_chat_model() that handles provider-specific quirks
    and provides consistent behavior across different LLM providers.

    Args:
        model: Model identifier (e.g., "claude-sonnet-4-5-20250929", "gpt-4o")
        temperature: Temperature for model (0.0=deterministic, 1.0=creative)
        **kwargs: Additional arguments passed to init_chat_model

    Returns:
        Initialized chat model

    Examples:
        >>> llm = init_model("claude-sonnet-4-5-20250929", temperature=0.0)
        >>> llm = init_model("gpt-4o", temperature=0.7)
        >>> llm = init_model("gemini-2.0-flash-exp")

    Notes:
        - Handles model-specific defaults
        - Provides consistent error messages
        - Future: Can add retry logic, fallback models, etc.
    """
    try:
        # Log model initialization
        logger.debug(f"Initializing model: {model} (temperature={temperature})")

        # Special cases can be handled here
        # For now, just pass through to init_chat_model
        llm = init_chat_model(
            model=model,
            temperature=temperature,
            **kwargs,
        )

        logger.debug(f"Successfully initialized: {llm.__class__.__name__}")
        return llm

    except Exception as e:
        logger.error(f"Failed to initialize model '{model}': {e}")
        raise


def is_test_connection(uri: str) -> bool:
    """Check if URI points to a test connection.

    Args:
        uri: Database connection URI

    Returns:
        True if this is a test connection (localhost or test account)
    """
    parsed = urlparse(uri)
    hostname = parsed.hostname or ""

    # Check for localhost or test indicators
    return hostname in ("localhost", "127.0.0.1") or "test" in hostname.lower() or ":8080" in uri


def create_snowflake_engine(context: "ContextSchema | EnhancedContextSchema") -> Engine:
    """Create SQLAlchemy engine from context configuration.

    Supports both URI-based and parameter-based connection methods.
    Automatically detects test connections.

    Args:
        context: Runtime context with connection details

    Returns:
        SQLAlchemy engine configured for Snowflake

    Raises:
        ValueError: If neither URI nor required parameters are provided

    Examples:
        >>> context = ContextSchema(snowflake_uri="snowflake://...")
        >>> engine = create_snowflake_engine(context)
        >>>
        >>> # Or with individual parameters
        >>> context = ContextSchema(
        ...     snowflake_account="myaccount",
        ...     snowflake_user="myuser",
        ...     snowflake_password="mypass",
        ...     snowflake_database="mydb"
        ... )
        >>> engine = create_snowflake_engine(context)
    """
    # Try URI first
    if context.snowflake_uri:
        uri = context.snowflake_uri
        logger.debug(f"Creating engine from URI (test={is_test_connection(uri)})")

        engine_args = {}

        # Add timeout only for Snowflake connections (not SQLite, DuckDB, PostgreSQL, etc.)
        if context.query_timeout and uri.startswith("snowflake://"):
            engine_args["connect_args"] = {"timeout": context.query_timeout}

        return create_engine(uri, **engine_args)

    # Build URI from individual parameters
    if not all([context.snowflake_account, context.snowflake_user, context.snowflake_password]):
        raise ValueError(
            "Either snowflake_uri or all of (snowflake_account, snowflake_user, "
            "snowflake_password) must be provided"
        )

    # Build Snowflake URI: snowflake://user:password@account/database/schema?warehouse=wh&role=role
    uri_parts = [
        "snowflake://",
        f"{context.snowflake_user}:{context.snowflake_password}",
        f"@{context.snowflake_account}",
    ]

    if context.snowflake_database:
        uri_parts.append(f"/{context.snowflake_database}")
        if context.snowflake_schema:
            uri_parts.append(f"/{context.snowflake_schema}")

    uri = "".join(uri_parts)

    # Add query parameters
    query_params = []
    if context.snowflake_warehouse:
        query_params.append(f"warehouse={context.snowflake_warehouse}")
    if context.snowflake_role:
        query_params.append(f"role={context.snowflake_role}")

    if query_params:
        uri += "?" + "&".join(query_params)

    logger.debug(f"Creating engine from parameters (test={is_test_connection(uri)})")

    engine_args = {}
    # Add timeout only for Snowflake connections
    if context.query_timeout and uri.startswith("snowflake://"):
        engine_args["connect_args"] = {"timeout": context.query_timeout}

    return create_engine(uri, **engine_args)


def create_sql_database(
    context: "ContextSchema | EnhancedContextSchema",
    engine: Engine | None = None,
) -> SQLDatabase:
    """Create LangChain SQLDatabase with guardrails from context.

    Applies allowed_schemas and allowed_tables restrictions from context.

    Args:
        context: Runtime context with connection details and guardrails
        engine: Optional pre-created engine (creates new if not provided)

    Returns:
        LangChain SQLDatabase configured with guardrails

    Examples:
        >>> context = ContextSchema(
        ...     snowflake_uri="snowflake://...",
        ...     allowed_schemas="TPCH_SAMPLE",
        ...     allowed_tables="CUSTOMER,ORDERS",
        ...     read_only=True
        ... )
        >>> db = create_sql_database(context)
    """
    if engine is None:
        engine = create_snowflake_engine(context)

    # Parse allowed tables from context
    include_tables = None
    if context.allowed_tables and context.allowed_tables != "*":
        include_tables = [t.strip() for t in context.allowed_tables.split(",")]
        logger.debug(f"Restricting to tables: {include_tables}")

    # Parse allowed schemas from context
    schema = None
    if context.allowed_schemas and context.allowed_schemas != "*":
        schemas = [s.strip() for s in context.allowed_schemas.split(",")]
        if len(schemas) == 1:
            schema = schemas[0]
            logger.debug(f"Using schema: {schema}")
        else:
            logger.warning(
                f"Multiple schemas specified: {schemas}. Using first: {schemas[0]}. "
                "SQLDatabase only supports single schema."
            )
            schema = schemas[0]

    # Create SQLDatabase with restrictions
    db = SQLDatabase(
        engine=engine,
        schema=schema,
        include_tables=include_tables,
        sample_rows_in_table_info=3,
        view_support=True,  # Support views in Snowflake
        max_string_length=300,
    )

    logger.info(
        f"Created SQLDatabase: schema={schema}, tables={include_tables or 'all'}, "
        f"read_only={context.read_only}"
    )

    return db
