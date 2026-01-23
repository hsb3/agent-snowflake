---
title: LangChain SQL Tools Reference
created: 2026-01-23
updated: 2026-01-23
tags: [langchain, sql, tools, reference]
doc_type: reference
---

# LangChain SQL Tools Reference

## Overview

This document describes the SQL tools provided by LangChain's `SQLDatabaseToolkit` that are now available to the Snowflake agent.

## SQLDatabaseToolkit

**Source:** `langchain_community.agent_toolkits.sql.toolkit.SQLDatabaseToolkit`

The toolkit provides 4 pre-built tools for database interaction:

### 1. QuerySQLDatabaseTool (`sql_db_query`)

**Purpose:** Execute SELECT queries against the database

**Description from LangChain:**
```
Input to this tool is a detailed and correct SQL query, output is a
result from the database. If the query is not correct, an error message
will be returned. If an error is returned, rewrite the query, check the
query, and try again. If you encounter an issue with Unknown column
'xxxx' in 'field list', use sql_db_schema to query the correct table fields.
```

**Usage:**
- Agent provides a SQL query string
- Tool executes the query and returns results
- Errors are returned if query is malformed
- Results are formatted for LLM consumption

**Our Enhancements:**
- Read-only warning added when `context.read_only=True`
- Restricted to allowed schemas/tables from context

### 2. InfoSQLDatabaseTool (`sql_db_schema`)

**Purpose:** Get detailed schema information for specific tables

**Description from LangChain:**
```
Input to this tool is a comma-separated list of tables, output is the
schema and sample rows for those tables. Be sure that the tables actually
exist by calling sql_db_list_tables first!
Example Input: table1, table2, table3
```

**Usage:**
- Agent provides comma-separated table names
- Tool returns:
  - Table schema (columns, types, constraints)
  - Sample rows (default: 3 rows)
  - Indexes (if enabled)

**Configuration:**
- Sample rows: 3 (configurable in SQLDatabase)
- Max string length: 300 chars (truncated)
- View support: Enabled

### 3. ListSQLDatabaseTool (`sql_db_list_tables`)

**Purpose:** List all available tables/views in the database

**Description from LangChain:**
```
Input is an empty string, output is a comma-separated list of tables
in the database.
```

**Usage:**
- Agent calls with empty string
- Tool returns list of accessible tables
- Respects schema restrictions from context

**Our Enhancements:**
- Filtered by `allowed_schemas` and `allowed_tables`
- Includes views when accessible

### 4. QuerySQLCheckerTool (`sql_db_query_checker`)

**Purpose:** Validate SQL syntax before execution

**Description from LangChain:**
```
Use this tool to double check if your query is correct before executing
it. Always use this tool before executing a query with sql_db_query!
```

**Usage:**
- Agent provides a SQL query
- Tool uses LLM to check:
  - Syntax validity
  - Table/column existence
  - Common SQL errors
- Returns validated or corrected query

**Requirements:**
- Requires an LLM (passed to SQLDatabaseToolkit)
- Uses LLM to reason about query correctness

## SQLDatabase Configuration

Our implementation configures `langchain_community.utilities.SQLDatabase` with:

```python
SQLDatabase(
    engine=engine,                      # SQLAlchemy engine
    schema=schema,                      # Single schema (from context)
    include_tables=include_tables,      # Allowed tables (from context)
    sample_rows_in_table_info=3,       # Sample rows for schema tool
    view_support=True,                 # Include views in listings
    max_string_length=300,             # Truncate long strings
)
```

### Guardrails Applied

From `ContextSchema`:
- **allowed_schemas**: Restricts to specific schemas (single schema supported)
- **allowed_tables**: Restricts to specific tables (list or `*` for all)
- **read_only**: Adds warnings to tool descriptions
- **query_timeout**: Applied to engine connection args

## Tool Behavior with Restrictions

### Schema Restrictions
```python
allowed_schemas = "PUBLIC"  # Single schema
```
- Only tables in PUBLIC schema are visible
- Multi-schema support: Uses first schema, logs warning

### Table Restrictions
```python
allowed_tables = "CUSTOMERS,ORDERS"  # Specific tables
```
- Only CUSTOMERS and ORDERS are accessible
- Other tables are hidden from list_tables
- Attempts to query other tables fail at DB level

### Read-Only Mode
```python
read_only = True
```
- Adds warning to query tool description
- Note: Actual enforcement is via tool prompting, not SQL parsing
- For strict enforcement, would need SQL parsing to reject DML/DDL

## Example Tool Interactions

### List Tables
```
Agent calls: sql_db_list_tables("")
Tool returns: "CUSTOMER, ORDERS, LINEITEM, PART, NATION, REGION"
```

### Get Schema
```
Agent calls: sql_db_schema("CUSTOMER, ORDERS")
Tool returns:
  CREATE TABLE CUSTOMER (
    C_CUSTKEY INTEGER PRIMARY KEY,
    C_NAME VARCHAR(25),
    C_NATIONKEY INTEGER,
    ...
  )
  Sample rows:
  1, "Customer#000000001", 5, ...
  2, "Customer#000000002", 9, ...
```

### Execute Query
```
Agent calls: sql_db_query("SELECT COUNT(*) FROM CUSTOMER")
Tool returns: "[(10,)]"
```

### Check Query
```
Agent calls: sql_db_query_checker("SELECT * FROM CUSTMER")
Tool returns: "Error: Table CUSTMER does not exist. Did you mean CUSTOMER?"
```

## Implementation Notes

### Why LangChain's Toolkit?

1. **Battle-tested**: Used across thousands of LangChain applications
2. **Well-documented**: Clear descriptions guide LLM behavior
3. **Dialect-aware**: Works with Snowflake SQL via SQLAlchemy
4. **Maintained**: Updates and fixes from LangChain community
5. **Consistent**: Standard interface across databases

### Customization Points

We customize via:
- **Context configuration**: Guardrails, timeouts, restrictions
- **Tool descriptions**: Read-only warnings
- **SQLDatabase config**: Sample rows, views, string truncation
- **Engine config**: Connection parameters, timeouts

### Testing Strategy

- **Unit tests**: Mock SQLDatabase, use SQLite
- **Integration tests**: Use fakesnow or Docker emulator
- **Production**: Real Snowflake connection

## References

- [LangChain SQL Agent Toolkit](https://python.langchain.com/docs/integrations/toolkits/sql_database)
- [SQLDatabase Utility](https://api.python.langchain.com/en/latest/utilities/langchain_community.utilities.sql_database.SQLDatabase.html)
- [SQLAlchemy Snowflake Dialect](https://docs.snowflake.com/en/developer-guide/python-connector/sqlalchemy)
