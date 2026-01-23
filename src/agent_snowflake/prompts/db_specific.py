"""Database-specific SQL guidance for the agent."""

SQLITE_INSTRUCTIONS = """Database-Specific Guidance (SQLite):

IMPORTANT: You are connected to a SQLite database for testing. Use your TOOLS, not raw Snowflake commands.

Tool Usage:
- To list tables: Use the sql_db_list_tables tool (NOT "SHOW TABLES")
- To get schema: Use the sql_db_schema tool with table names
- To query data: Use the sql_db_query tool with SELECT statements
- To validate SQL: Use the sql_db_query_checker tool

SQL Syntax for SQLite:
- Use standard SQL: SELECT, WHERE, JOIN, GROUP BY, ORDER BY
- Use SQLite functions: datetime(), date(), strftime()
- String concat: Use || operator

Example Workflow:
1. User: "Show me all tables"
   → Use sql_db_list_tables tool

2. User: "What's in the CUSTOMER table?"
   → Use sql_db_schema tool with table_names=['CUSTOMER']

3. User: "Count customers"
   → Use sql_db_query tool with: SELECT COUNT(*) FROM CUSTOMER


ANTI-PATTERNS:
- Using commands that only work on specific platforms
   Snowflake:
   - SHOW TABLES, DESCRIBE TABLE, USE DATABASE, FLATTEN(), PARSE_JSON(), QUALIFY
   PostgreSQL:
   - \d, \dt, \c, jsonb functions
   MySQL:
   - DESCRIBE, EXPLAIN, JSON functions

ALWAYS use your tools first before writing raw SQL queries.

"""

SNOWFLAKE_INSTRUCTIONS = """Database-Specific Guidance (Snowflake):

You are connected to Snowflake. Use your TOOLS for exploration, raw SQL for queries.

Tool Usage:
- To list tables: Use the sql_db_list_tables tool
- To get schema: Use the sql_db_schema tool with table names
- To query data: Use the sql_db_query tool with SELECT statements
- To validate SQL: Use the sql_db_query_checker tool before execution

Snowflake-Specific Features Available:
- Semi-structured: VARIANT, OBJECT, ARRAY types
- JSON operations: PARSE_JSON(), GET_PATH(), FLATTEN()
- Window functions: QUALIFY clause
- Time travel: AT, BEFORE clauses
- Advanced functions: TRY_CAST(), IFNULL(), NVL()

SQL Best Practices:
- Use warehouse efficiently (avoid large scans without filters)
- Leverage clustering and partitioning where available
- Use LIMIT for exploratory queries
- Consider query performance impact

ALWAYS use your tools first for schema exploration.
"""
