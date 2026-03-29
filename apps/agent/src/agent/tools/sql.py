"""SQL tools for Snowflake agent using LangChain's SQLDatabaseToolkit.

This module wraps LangChain's pre-built SQL tools with Snowflake-specific
configuration and guardrails from the agent context.
"""

import logging
from typing import TYPE_CHECKING

import sqlparse
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from ..context import ContextSchema
from ..utils import create_sql_database

if TYPE_CHECKING:
    from ..context2 import EnhancedContextSchema

logger = logging.getLogger(__name__)

# SQL statement types that are allowed in read-only mode
_ALLOWED_READONLY_TYPES = {"SELECT", "WITH"}

# SQL statement types that are explicitly forbidden in read-only mode
_FORBIDDEN_READONLY_TYPES = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "REPLACE",
    "MERGE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "CALL",
}


def validate_read_only_query(sql: str) -> str | None:
    """Validate that a SQL query is read-only (SELECT or WITH/CTE only).

    Uses sqlparse to determine the statement type. Returns None if the query
    is allowed, or an error message string if it is not.

    Args:
        sql: The SQL query string to validate.

    Returns:
        None if the query is safe, or an error message string if it is rejected.
    """
    stripped = sql.strip()
    if not stripped:
        return "Error: Empty query is not allowed."

    try:
        parsed = sqlparse.parse(stripped)
    except Exception as e:
        return f"Error: Could not parse SQL query: {e}"

    if not parsed:
        return "Error: Could not parse SQL query."

    for statement in parsed:
        # Skip empty statements (e.g. trailing semicolons)
        if not str(statement).strip():
            continue

        stmt_type = statement.get_type()

        # sqlparse returns None for some statements; fall back to first keyword
        if stmt_type is None:
            first_token = statement.token_first(skip_cm=True, skip_ws=True)
            if first_token is not None:
                stmt_type = first_token.ttype and first_token.normalized
                # If ttype is a keyword, use the normalized value
                if first_token.ttype in (
                    sqlparse.tokens.Keyword,
                    sqlparse.tokens.Keyword.DDL,
                    sqlparse.tokens.Keyword.DML,
                ):
                    stmt_type = first_token.normalized

        if stmt_type is None:
            return (
                "Error: Could not determine statement type. "
                "Only SELECT queries are allowed in read-only mode."
            )

        stmt_type_upper = str(stmt_type).upper()

        if stmt_type_upper in _FORBIDDEN_READONLY_TYPES:
            return (
                f"Error: {stmt_type_upper} statements are not allowed in read-only mode. "
                "Only SELECT queries are permitted."
            )

        if stmt_type_upper not in _ALLOWED_READONLY_TYPES:
            return (
                f"Error: {stmt_type_upper} statements are not allowed in read-only mode. "
                "Only SELECT queries are permitted."
            )

    return None


class ReadOnlyQueryTool(BaseTool):
    """Wrapper around sql_db_query that enforces read-only validation.

    Validates each query using sqlparse before delegating to the wrapped tool.
    Non-SELECT queries are rejected with an error message (returned as a string
    so the LLM can self-correct).
    """

    name: str = "sql_db_query"
    description: str = ""
    _wrapped_tool: BaseTool

    def __init__(self, wrapped_tool: BaseTool, **kwargs):
        super().__init__(
            name=wrapped_tool.name,
            description=wrapped_tool.description,
            **kwargs,
        )
        # Use object.__setattr__ to bypass Pydantic field validation
        object.__setattr__(self, "_wrapped_tool", wrapped_tool)

    def _run(self, query: str, **kwargs) -> str:
        """Validate query then delegate to the wrapped tool."""
        error = validate_read_only_query(query)
        if error is not None:
            logger.warning("Read-only enforcement blocked query: %s", query[:200])
            return error
        return self._wrapped_tool._run(query, **kwargs)

    async def _arun(self, query: str, **kwargs) -> str:
        """Validate query then delegate to the wrapped tool (async)."""
        error = validate_read_only_query(query)
        if error is not None:
            logger.warning("Read-only enforcement blocked query: %s", query[:200])
            return error
        return await self._wrapped_tool._arun(query, **kwargs)


def create_sql_tools(
    llm: BaseChatModel,
    context: "ContextSchema | EnhancedContextSchema",
    db: SQLDatabase | None = None,
) -> list[BaseTool]:
    """Create SQL database tools with context-based guardrails.

    Uses LangChain's SQLDatabaseToolkit and applies restrictions from context:
    - allowed_schemas: Limit to specific schemas
    - allowed_tables: Limit to specific tables
    - read_only: Enforce read-only access (via toolkit configuration)

    Args:
        llm: Language model for query checking
        context: Runtime context with connection and guardrail settings
        db: Optional pre-created SQLDatabase (creates new if not provided)

    Returns:
        List of SQL tools:
        - sql_db_query: Execute SELECT queries
        - sql_db_schema: Get schema info for tables
        - sql_db_list_tables: List available tables
        - sql_db_query_checker: Validate SQL queries

    Examples:
        >>> from agent.utils import init_model
        >>> from agent.context import ContextSchema
        >>>
        >>> llm = init_model("claude-sonnet-4-5-20250929")
        >>> context = ContextSchema(
        ...     snowflake_uri="snowflake://...",
        ...     allowed_schemas="TPCH_SAMPLE",
        ...     read_only=True
        ... )
        >>> tools = create_sql_tools(llm, context)

    Notes:
        - Read-only enforcement: Toolkit naturally provides read-only tools
          (query checker can be instructed to reject DML/DDL via prompts)
        - Schema/table restrictions: Applied via SQLDatabase configuration
        - Query timeout: Applied via engine connection args
    """
    # Create or use provided database
    if db is None:
        db = create_sql_database(context)

    # Log connection info
    logger.info(
        "Creating SQL tools: dialect=%s, usable_tables=%d",
        db.dialect,
        len(list(db.get_usable_table_names())),
    )

    # Create toolkit with database and LLM
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # Get all tools from toolkit
    tools = toolkit.get_tools()

    # Add read-only enforcement if needed
    if context.read_only:
        wrapped_tools = []
        for tool in tools:
            if "query" in tool.name.lower() and "checker" not in tool.name.lower():
                # Replace with a read-only wrapper that validates queries
                read_only_note = (
                    f"{tool.description}\n\n"
                    "NOTE: Only SELECT queries are allowed. "
                    "INSERT, UPDATE, DELETE, DROP, and other DML/DDL statements "
                    "are prohibited in read-only mode."
                )
                wrapped = ReadOnlyQueryTool(wrapped_tool=tool)
                wrapped.description = read_only_note
                wrapped_tools.append(wrapped)
            else:
                wrapped_tools.append(tool)
        tools = wrapped_tools

    logger.info("Created %d SQL tools: %s", len(tools), [t.name for t in tools])

    return tools


def get_database_context(db: SQLDatabase) -> dict:
    """Get database context information for agent prompts.

    Provides useful context about the database structure that can be
    included in system prompts.

    Args:
        db: SQLDatabase instance

    Returns:
        Dictionary with database context:
        - dialect: SQL dialect (e.g., "snowflake")
        - usable_tables: List of accessible tables
        - table_info: Schema information for tables

    Examples:
        >>> db = create_sql_database(context)
        >>> ctx = get_database_context(db)
        >>> print(ctx["dialect"])
        snowflake
        >>> print(ctx["usable_tables"])
        ['CUSTOMER', 'ORDERS', 'LINEITEM']
    """
    return db.get_context()
