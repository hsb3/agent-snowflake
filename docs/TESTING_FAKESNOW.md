# Local Snowflake Testing with fakesnow

This document describes how to use **fakesnow** for local Snowflake testing without requiring Docker or Snowflake credentials.

## Overview

[fakesnow](https://github.com/tekumara/fakesnow) is a Python library that provides a fake Snowflake database for local testing. It works by patching the `snowflake-connector-python` library and using DuckDB as the backend database.

### Why fakesnow?

- ✅ **No Docker required** - Pure Python solution
- ✅ **Zero configuration** - Works out of the box
- ✅ **Compatible** - Uses standard `snowflake-connector-python`
- ✅ **Fast** - DuckDB backend provides excellent performance
- ✅ **Easy testing** - Perfect for unit and integration tests
- ✅ **Free and open source** - MIT licensed

## Installation

fakesnow is already included in the project dependencies:

```bash
uv add fakesnow
```

## Quick Start

### Basic Usage with Patching

The simplest way to use fakesnow is with the context manager:

```python
import fakesnow
import snowflake.connector

# Patch snowflake.connector to use fakesnow
with fakesnow.patch():
    conn = snowflake.connector.connect(
        account="test",
        user="test",
        password="test"
    )

    cursor = conn.cursor()
    cursor.execute("SELECT 'Hello from fakesnow!' as message")
    print(cursor.fetchone())
```

### Server Mode

For scenarios where patching doesn't work (subprocesses, non-Python clients):

```python
import fakesnow
import snowflake.connector

# Run fakesnow as an HTTP server
with fakesnow.server() as conn_kwargs:
    conn = snowflake.connector.connect(**conn_kwargs)
    cursor = conn.cursor()
    cursor.execute("SELECT 'Hello from fakesnow server!' as message")
    print(cursor.fetchone())
```

## Testing with Sample Data

### Create Sample Database

```python
import fakesnow
import snowflake.connector

with fakesnow.patch():
    conn = snowflake.connector.connect()
    cursor = conn.cursor()

    # Create database and schema
    cursor.execute("CREATE DATABASE SAMPLE_DB")
    cursor.execute("USE DATABASE SAMPLE_DB")
    cursor.execute("CREATE SCHEMA TPCH_SAMPLE")
    cursor.execute("USE SCHEMA TPCH_SAMPLE")

    # Create tables
    cursor.execute("""
        CREATE TABLE CUSTOMER (
            C_CUSTKEY INTEGER PRIMARY KEY,
            C_NAME VARCHAR(25),
            C_ADDRESS VARCHAR(40),
            C_PHONE VARCHAR(15),
            C_ACCTBAL DECIMAL(15,2)
        )
    """)

    # Insert data
    cursor.execute("""
        INSERT INTO CUSTOMER VALUES
        (1, 'Customer#000000001', '1234 Main St', '555-0001', 1000.00),
        (2, 'Customer#000000002', '5678 Oak Ave', '555-0002', 2000.00),
        (3, 'Customer#000000003', '9012 Pine Rd', '555-0003', 3000.00)
    """)

    # Query data
    cursor.execute("SELECT * FROM CUSTOMER")
    for row in cursor.fetchall():
        print(row)
```

## Running the Test Script

Use the provided test script to verify everything works:

```bash
uv run python test_fakesnow.py
```

This will:
1. Initialize fakesnow
2. Create sample database and tables
3. Load TPC-H inspired sample data
4. Run test queries
5. Verify results

## Using with pytest

fakesnow is designed to work seamlessly with pytest:

```python
import pytest
import fakesnow
import snowflake.connector

@pytest.fixture
def snow_conn():
    """Fixture that provides a fake Snowflake connection."""
    with fakesnow.patch():
        conn = snowflake.connector.connect()
        yield conn
        conn.close()

def test_customer_query(snow_conn):
    """Test querying customer data."""
    cursor = snow_conn.cursor()
    cursor.execute("CREATE TABLE customers (id INT, name VARCHAR)")
    cursor.execute("INSERT INTO customers VALUES (1, 'Alice'), (2, 'Bob')")
    cursor.execute("SELECT COUNT(*) FROM customers")

    assert cursor.fetchone()[0] == 2
```

## Data Persistence

### In-Memory (Default)

By default, fakesnow uses an in-memory database that's cleared when the connection closes:

```python
with fakesnow.patch():
    conn = snowflake.connector.connect()
    # Data exists only within this context
```

### File-Based Persistence

To persist data between runs:

```python
with fakesnow.patch(session_parameters={"FAKESNOW_DB_PATH": "data/"}):
    conn = snowflake.connector.connect()
    # Data is saved to data/ directory
```

### Isolated Databases

For isolated databases per connection:

```python
with fakesnow.patch(session_parameters={"FAKESNOW_DB_PATH": ":isolated:"}):
    conn = snowflake.connector.connect()
    # Each connection gets its own isolated database
```

## Sample Queries

Once you've loaded the sample data (see test_fakesnow.py), you can run:

### Customer Analysis

```python
cursor.execute("""
    SELECT
        c.C_NAME,
        COUNT(o.O_ORDERKEY) as ORDER_COUNT,
        SUM(o.O_TOTALPRICE) as TOTAL_SPENT
    FROM CUSTOMER c
    LEFT JOIN ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
    GROUP BY c.C_NAME
    ORDER BY TOTAL_SPENT DESC
""")
```

### Regional Analysis

```python
cursor.execute("""
    SELECT
        r.R_NAME,
        COUNT(DISTINCT c.C_CUSTKEY) as CUSTOMER_COUNT
    FROM REGION r
    JOIN NATION n ON r.R_REGIONKEY = n.N_REGIONKEY
    JOIN CUSTOMER c ON n.N_NATIONKEY = c.C_NATIONKEY
    GROUP BY r.R_NAME
""")
```

## Supported Features

### What Works ✅

- Standard SQL queries (SELECT, INSERT, UPDATE, DELETE)
- Table and view creation
- Joins (INNER, LEFT, RIGHT, FULL)
- Aggregations (COUNT, SUM, AVG, MIN, MAX)
- Window functions
- CTEs (Common Table Expressions)
- Subqueries
- Most SQL functions
- Transactions

### Known Limitations ⚠️

- No Snowflake stages
- No Snowpark support
- Some Snowflake-specific functions may not work
- No support for stored procedures
- No multi-cluster features
- Performance characteristics differ from real Snowflake

## Environment Variables

For local testing, add these to your `.env`:

```bash
# These work with fakesnow (any values work)
SNOWFLAKE_AGENT_SNOWFLAKE_ACCOUNT=test
SNOWFLAKE_AGENT_SNOWFLAKE_USER=test
SNOWFLAKE_AGENT_SNOWFLAKE_PASSWORD=test
SNOWFLAKE_AGENT_SNOWFLAKE_DATABASE=SAMPLE_DB
SNOWFLAKE_AGENT_SNOWFLAKE_SCHEMA=TPCH_SAMPLE
```

## Integration with Agent Code

To use fakesnow with your agent code:

```python
import fakesnow
import os

# For testing, wrap your agent code
with fakesnow.patch():
    from agent_snowflake import run_agent

    # Agent will use fakesnow instead of real Snowflake
    result = run_agent("Show me top customers by revenue")
```

Or set it up globally in your test suite:

```python
# conftest.py
import pytest
import fakesnow

@pytest.fixture(scope="session", autouse=True)
def fake_snowflake():
    """Automatically use fakesnow for all tests."""
    with fakesnow.patch():
        yield
```

## Troubleshooting

### Import Error

```bash
# Make sure fakesnow is installed
uv add fakesnow
```

### Connection Issues

```python
# Always use the context manager
with fakesnow.patch():
    # Your code here
    pass
```

### SQL Errors

- Check DuckDB documentation for supported syntax
- Simplify complex Snowflake-specific queries
- Use standard SQL instead of Snowflake extensions

## Comparison with Other Options

| Feature | fakesnow | Docker Emulator | Real Snowflake |
|---------|----------|-----------------|----------------|
| Setup | Instant | Docker required | Account needed |
| Cost | Free | Free | Paid |
| Speed | Very Fast | Fast | Varies |
| Snowflake API | ~95% | ~80% | 100% |
| Isolation | Excellent | Good | None |
| CI/CD | Excellent | Good | Possible |

## Additional Resources

- [fakesnow GitHub](https://github.com/tekumara/fakesnow)
- [fakesnow PyPI](https://pypi.org/project/fakesnow/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Snowflake Connector Python](https://docs.snowflake.com/en/user-guide/python-connector)

## Next Steps

1. Install fakesnow: `uv add fakesnow`
2. Run the test script: `uv run python test_fakesnow.py`
3. Load sample data (included in test script)
4. Start building your agent with local testing
5. Switch to real Snowflake for production

## Files

```
agent-snowflake/
├── test_fakesnow.py           # Test script with sample data
├── TESTING_FAKESNOW.md        # This file
└── scripts/
    └── sample_data.py         # Sample data loader
```
