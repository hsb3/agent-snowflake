# Local Snowflake Testing Environment

This document describes the local Snowflake testing environment for the agent-snowflake project.

## Overview

Since Snowflake doesn't provide an official local emulator, we use **snowflake-emulator** by nnnkkk7, which provides a Snowflake-compatible SQL interface backed by DuckDB. This allows for local development and testing without requiring Snowflake credentials or incurring cloud costs.

## Architecture

- **Emulator**: [snowflake-emulator](https://github.com/nnnkkk7/snowflake-emulator) - Go-based Snowflake emulator with DuckDB backend
- **Container**: Docker container running on port 8080
- **Data**: TPC-H inspired sample dataset with realistic business data
- **Connector**: Uses standard `snowflake-connector-python` package

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.12+ with uv
- Project dependencies installed (`uv sync`)

### Start the Emulator

```bash
# Start the emulator in detached mode
docker-compose up -d

# Check that it's running
docker-compose ps

# View logs if needed
docker-compose logs -f snowflake-emulator
```

### Test the Connection

```bash
# Run the quick test script
uv run python test_emulator.py
```

This will:
1. Connect to the emulator
2. Create a test database and schema
3. Create a sample table
4. Insert and query test data
5. Verify everything works

## Sample Data

The emulator includes a TPC-H inspired dataset with the following tables:

### Tables

| Table | Description | Rows |
|-------|-------------|------|
| `REGION` | Geographic regions | 5 |
| `NATION` | Countries/nations | 25 |
| `CUSTOMER` | Customer information | 10 |
| `ORDERS` | Customer orders | 10 |
| `PART` | Parts/products | 10 |
| `LINEITEM` | Order line items | 10 |

### Views

- `CUSTOMER_ORDER_SUMMARY` - Customer spending summary by region
- `ORDER_DETAILS` - Detailed order line items with customer and part info
- `DATABASE_SUMMARY` - Row counts for all tables

### Access the Sample Data

```python
import snowflake.connector

conn = snowflake.connector.connect(
    account="test",
    user="test",
    password="test",
    host="localhost",
    port=8080,
    protocol="http",
    insecure_mode=True,
    database="SAMPLE_DB",
    schema="TPCH_SAMPLE"
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM CUSTOMER_ORDER_SUMMARY")
for row in cursor.fetchall():
    print(row)
```

## Connection Configuration

### Environment Variables

Update your `.env` file with these test connection parameters:

```bash
# For local testing with emulator
SNOWFLAKE_AGENT_SNOWFLAKE_ACCOUNT=test
SNOWFLAKE_AGENT_SNOWFLAKE_USER=test
SNOWFLAKE_AGENT_SNOWFLAKE_PASSWORD=test
SNOWFLAKE_AGENT_SNOWFLAKE_HOST=localhost
SNOWFLAKE_AGENT_SNOWFLAKE_PORT=8080
SNOWFLAKE_AGENT_SNOWFLAKE_DATABASE=SAMPLE_DB
SNOWFLAKE_AGENT_SNOWFLAKE_SCHEMA=TPCH_SAMPLE
```

### Python Connection

```python
import snowflake.connector

# Basic connection
conn = snowflake.connector.connect(
    account="test",
    user="test",
    password="test",
    host="localhost",
    port=8080,
    protocol="http",
    insecure_mode=True,
)

# Connection with database/schema
conn = snowflake.connector.connect(
    account="test",
    user="test",
    password="test",
    host="localhost",
    port=8080,
    protocol="http",
    insecure_mode=True,
    database="SAMPLE_DB",
    schema="TPCH_SAMPLE"
)
```

## Sample Queries

### Customer Analysis

```sql
-- Top customers by total spending
SELECT
    c.C_NAME,
    SUM(o.O_TOTALPRICE) as TOTAL_SPENT,
    COUNT(o.O_ORDERKEY) as ORDER_COUNT
FROM CUSTOMER c
JOIN ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
GROUP BY c.C_NAME
ORDER BY TOTAL_SPENT DESC
LIMIT 5;
```

### Regional Analysis

```sql
-- Orders by region
SELECT
    r.R_NAME as REGION,
    COUNT(o.O_ORDERKEY) as ORDER_COUNT,
    SUM(o.O_TOTALPRICE) as TOTAL_REVENUE
FROM REGION r
JOIN NATION n ON r.R_REGIONKEY = n.N_REGIONKEY
JOIN CUSTOMER c ON n.N_NATIONKEY = c.C_NATIONKEY
JOIN ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
GROUP BY r.R_NAME
ORDER BY TOTAL_REVENUE DESC;
```

### Product Analysis

```sql
-- Most popular parts
SELECT
    p.P_NAME,
    COUNT(l.L_ORDERKEY) as TIMES_ORDERED,
    SUM(l.L_QUANTITY) as TOTAL_QUANTITY,
    SUM(l.L_EXTENDEDPRICE) as TOTAL_REVENUE
FROM PART p
JOIN LINEITEM l ON p.P_PARTKEY = l.L_PARTKEY
GROUP BY p.P_NAME
ORDER BY TOTAL_REVENUE DESC;
```

## Managing the Emulator

### Common Commands

```bash
# Start emulator
docker-compose up -d

# Stop emulator (keeps data)
docker-compose stop

# Stop and remove emulator (removes data)
docker-compose down

# Stop and remove including volumes (clean slate)
docker-compose down -v

# View logs
docker-compose logs -f

# Restart emulator
docker-compose restart

# Check status
docker-compose ps
```

### Data Persistence

Data is persisted in a Docker volume named `snowflake-data`. This means:
- Data survives `docker-compose stop` and `docker-compose restart`
- Data is removed with `docker-compose down -v`
- Each fresh start without `-v` keeps existing data

To reset to a clean state:
```bash
docker-compose down -v
docker-compose up -d
```

## Limitations

### What Works
- Standard SQL queries (SELECT, INSERT, UPDATE, DELETE)
- Table and view creation
- Basic joins and aggregations
- WHERE clauses, GROUP BY, ORDER BY
- Common SQL functions
- snowflake-connector-python compatibility

### Known Limitations
- Not all Snowflake-specific functions are supported
- No support for Snowflake stages (file loading)
- No support for Snowpark
- No support for stored procedures/UDFs
- Performance characteristics differ from real Snowflake
- Some advanced features may not work

### When to Use Real Snowflake
- Testing Snowflake-specific features (stages, Snowpark, etc.)
- Performance testing and optimization
- Testing with large datasets
- Integration testing with other Snowflake services
- Production-like testing

## Troubleshooting

### Emulator won't start
```bash
# Check if port 8080 is already in use
lsof -i :8080

# Check Docker logs
docker-compose logs snowflake-emulator

# Try restarting Docker
# (macOS: Docker Desktop → Restart)
```

### Connection refused
```bash
# Make sure emulator is running
docker-compose ps

# Check emulator health
curl http://localhost:8080/health

# Try restarting emulator
docker-compose restart
```

### SQL query fails
- Check the error message - some Snowflake features aren't supported
- Try simplifying the query
- Check DuckDB documentation for supported syntax
- Consider using real Snowflake for unsupported features

### Data not persisting
```bash
# Check if volume exists
docker volume ls | grep snowflake

# Make sure you're not using `down -v` which removes volumes
docker-compose down  # Good: keeps data
docker-compose down -v  # Removes all data
```

## Alternative Testing Approaches

If the emulator doesn't meet your needs, consider:

1. **fakesnow** - Python-only mock with in-memory DuckDB
   ```bash
   uv add fakesnow
   ```

2. **Snowflake Trial Account** - Free 30-day trial with $400 credits
   - Sign up at https://signup.snowflake.com/

3. **Mocking** - Use Python's `unittest.mock` for unit tests
   - Good for testing application logic without database

4. **PostgreSQL** - For basic SQL testing (not Snowflake-compatible)

## Additional Resources

- [snowflake-emulator GitHub](https://github.com/nnnkkk7/snowflake-emulator)
- [Snowflake Documentation](https://docs.snowflake.com/)
- [TPC-H Benchmark](http://www.tpc.org/tpch/)
- [DuckDB Documentation](https://duckdb.org/docs/)

## Files in This Setup

```
agent-snowflake/
├── docs/
│   └── TESTING.md             # This file
├── docker-compose.yml          # Emulator container configuration
├── test_emulator.py           # Quick connection test script
└── scripts/
    ├── init_data.sql          # Sample TPC-H data initialization
    └── test_connection.py     # Detailed test script
```
