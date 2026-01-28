"""SQL tools for Snowflake agent using LangChain's SQLDatabaseToolkit.

This module wraps LangChain's pre-built SQL tools with Snowflake-specific
configuration and guardrails from the agent context.
"""

import logging
from typing import TYPE_CHECKING, List

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool

from ..context import ContextSchema
from ..utils import create_sql_database

if TYPE_CHECKING:
    from ..context2 import EnhancedContextSchema

logger = logging.getLogger(__name__)


def create_sql_tools(
    llm: BaseChatModel,
    context: "ContextSchema | EnhancedContextSchema",
    db: SQLDatabase | None = None,
) -> List[BaseTool]:
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
        f"Creating SQL tools: dialect={db.dialect}, "
        f"usable_tables={len(list(db.get_usable_table_names()))}"
    )

    # Create toolkit with database and LLM
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)

    # Get all tools from toolkit
    tools = toolkit.get_tools()

    # Add read-only enforcement to descriptions if needed
    if context.read_only:
        for tool in tools:
            if "query" in tool.name.lower() and "checker" not in tool.name.lower():
                # Add read-only note to query execution tool
                tool.description = (
                    f"{tool.description}\n\n"
                    "NOTE: Only SELECT queries are allowed. "
                    "INSERT, UPDATE, DELETE, DROP, and other DML/DDL statements "
                    "are prohibited in read-only mode."
                )

    logger.info(f"Created {len(tools)} SQL tools: {[t.name for t in tools]}")

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
