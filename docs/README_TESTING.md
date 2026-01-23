# Local Snowflake Testing Guide

This guide covers multiple approaches for testing Snowflake locally without requiring cloud credentials or incurring costs.

## Table of Contents

1. [Overview](#overview)
2. [Option 1: fakesnow (Recommended)](#option-1-fakesnow-recommended)
3. [Option 2: snowflake-emulator (Docker)](#option-2-snowflake-emulator-docker)
4. [Option 3: Real Snowflake Trial](#option-3-real-snowflake-trial)
5. [Comparison](#comparison)
6. [Sample Data](#sample-data)

## Overview

Since Snowflake is a cloud-native data warehouse, there's no official local version. However, several community solutions provide local testing capabilities:

| Solution | Pros | Cons |
|----------|------|------|
| **fakesnow** | Easy setup, no Docker, fast | ~95% Snowflake compatibility |
| **snowflake-emulator** | Good compatibility, persistent storage | Requires Docker |
| **Snowflake Trial** | 100% compatible, real features | Requires signup, limited time |

## Option 1: fakesnow (Recommended)

**Best for:** Unit testing, CI/CD, local development without Docker

### Installation

```bash
uv add fakesnow
```

### Quick Start

```python
import fakesnow
import snowflake.connector

# Use as context manager
with fakesnow.patch():
    conn = snowflake.connector.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT 'Hello from fakesnow!' as message")
    print(cursor.fetchone())
```

### Run Test Script

```bash
uv run python test_fakesnow.py
```

### Features

- ✅ Pure Python (no Docker needed)
- ✅ DuckDB backend (fast, SQL-compatible)
- ✅ Works with snowflake-connector-python
- ✅ Supports most SQL operations
- ✅ Perfect for pytest
- ✅ In-memory or file-based persistence

### Limitations

- ❌ No Snowflake stages
- ❌ No Snowpark support
- ❌ Some Snowflake-specific functions missing
- ❌ No stored procedures

### Documentation

See [TESTING_FAKESNOW.md](./TESTING_FAKESNOW.md) for detailed documentation.

## Option 2: snowflake-emulator (Docker)

**Best for:** Integration testing, team environments, persistent test data

### Prerequisites

- Docker and Docker Compose
- macOS, Linux, or Windows with WSL

### Quick Start

```bash
# Start the emulator
docker-compose up -d

# Test connection
uv run python test_emulator.py

# Stop emulator (keeps data)
docker-compose stop

# Stop and remove (deletes data)
docker-compose down -v
```

### Connection

```python
import snowflake.connector

conn = snowflake.connector.connect(
    account="test",
    user="test",
    password="test",
    host="localhost",
    port=8080,
    protocol="http",
    insecure_mode=True
)
```

### Features

- ✅ Good Snowflake compatibility
- ✅ HTTP API endpoint
- ✅ Persistent storage via Docker volumes
- ✅ Runs in container
- ✅ DuckDB backend

### Limitations

- ❌ Requires Docker
- ❌ Platform-specific (Linux x86_64 preferred)
- ❌ No Snowpark or stages
- ❌ Limited Snowflake-specific features

### Documentation

See [TESTING.md](./TESTING.md) for detailed documentation.

## Option 3: Real Snowflake Trial

**Best for:** Feature testing, performance testing, production-like environments

### Setup

1. Sign up at https://signup.snowflake.com/
2. Get $400 in free credits
3. 30-day trial period
4. Access to all Snowflake features

### Features

- ✅ 100% Snowflake compatibility
- ✅ All features available
- ✅ Real performance characteristics
- ✅ Production-like environment
- ✅ Stages, Snowpark, UDFs, etc.

### Limitations

- ❌ Requires signup
- ❌ Time-limited trial
- ❌ Costs money after trial
- ❌ Requires internet connection
- ❌ Slower than local testing

### Sample Datasets

Snowflake provides free sample datasets including TPC-H and TPC-DS in the `SNOWFLAKE_SAMPLE_DATA` database.

## Comparison

### Performance

| Solution | Speed | Startup Time | Data Size |
|----------|-------|--------------|-----------|
| fakesnow | Very Fast | Instant | Small-Medium |
| snowflake-emulator | Fast | ~5 seconds | Medium |
| Snowflake Trial | Varies | ~30 seconds | Large |

### Compatibility

| Feature | fakesnow | snowflake-emulator | Snowflake Trial |
|---------|----------|-------------------|-----------------|
| SQL Queries | ✅ 95% | ✅ 85% | ✅ 100% |
| Joins | ✅ | ✅ | ✅ |
| Aggregations | ✅ | ✅ | ✅ |
| Window Functions | ✅ | ✅ | ✅ |
| CTEs | ✅ | ✅ | ✅ |
| Stages | ❌ | ❌ | ✅ |
| Snowpark | ❌ | ❌ | ✅ |
| Stored Procs | ❌ | ❌ | ✅ |
| UDFs | ⚠️ Limited | ⚠️ Limited | ✅ |

### Use Cases

| Use Case | Recommended Solution |
|----------|---------------------|
| Unit testing | fakesnow |
| CI/CD pipelines | fakesnow |
| Local development | fakesnow or snowflake-emulator |
| Integration testing | snowflake-emulator |
| Feature testing | Snowflake Trial |
| Performance testing | Snowflake Trial |
| Team environments | snowflake-emulator |
| Production-like testing | Snowflake Trial |

## Sample Data

All testing solutions include a TPC-H inspired sample dataset with:

### Tables

- **REGION** - 5 geographic regions
- **NATION** - 25 countries
- **CUSTOMER** - 10 sample customers
- **ORDERS** - 10 sample orders
- **PART** - 5 sample products
- **LINEITEM** - 5 order line items

### Sample Queries

```python
import snowflake.connector

# Connect (example with fakesnow)
import fakesnow
with fakesnow.patch():
    conn = snowflake.connector.connect(
        database="SAMPLE_DB",
        schema="TPCH_SAMPLE"
    )
    cursor = conn.cursor()

    # Top customers by spending
    cursor.execute("""
        SELECT
            c.C_NAME,
            SUM(o.O_TOTALPRICE) as TOTAL_SPENT
        FROM CUSTOMER c
        JOIN ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
        GROUP BY c.C_NAME
        ORDER BY TOTAL_SPENT DESC
        LIMIT 5
    """)

    for row in cursor.fetchall():
        print(f"{row[0]}: ${row[1]:,.2f}")
```

## Environment Configuration

### For fakesnow

```bash
# .env file
SNOWFLAKE_AGENT_SNOWFLAKE_ACCOUNT=test
SNOWFLAKE_AGENT_SNOWFLAKE_USER=test
SNOWFLAKE_AGENT_SNOWFLAKE_PASSWORD=test
SNOWFLAKE_AGENT_SNOWFLAKE_DATABASE=SAMPLE_DB
SNOWFLAKE_AGENT_SNOWFLAKE_SCHEMA=TPCH_SAMPLE
```

### For snowflake-emulator

```bash
# .env file
SNOWFLAKE_AGENT_SNOWFLAKE_ACCOUNT=test
SNOWFLAKE_AGENT_SNOWFLAKE_USER=test
SNOWFLAKE_AGENT_SNOWFLAKE_PASSWORD=test
SNOWFLAKE_AGENT_SNOWFLAKE_HOST=localhost
SNOWFLAKE_AGENT_SNOWFLAKE_PORT=8080
SNOWFLAKE_AGENT_SNOWFLAKE_DATABASE=SAMPLE_DB
SNOWFLAKE_AGENT_SNOWFLAKE_SCHEMA=TPCH_SAMPLE
```

### For Snowflake Trial

```bash
# .env file
SNOWFLAKE_AGENT_SNOWFLAKE_ACCOUNT=your_account_identifier
SNOWFLAKE_AGENT_SNOWFLAKE_USER=your_username
SNOWFLAKE_AGENT_SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_AGENT_SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_AGENT_SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_AGENT_SNOWFLAKE_SCHEMA=your_schema
SNOWFLAKE_AGENT_SNOWFLAKE_ROLE=your_role
```

## Getting Started

### Quick Start (Recommended)

1. Install fakesnow:
   ```bash
   uv add fakesnow
   ```

2. Run test script:
   ```bash
   uv run python test_fakesnow.py
   ```

3. Start building your agent!

### Alternative: Docker Emulator

1. Start emulator:
   ```bash
   docker-compose up -d
   ```

2. Run test script:
   ```bash
   uv run python test_emulator.py
   ```

3. Start building your agent!

## Troubleshooting

### fakesnow Issues

```bash
# Make sure it's installed
uv add fakesnow

# Check Python version (requires 3.10+)
python --version
```

### Docker Issues

```bash
# Check if Docker is running
docker ps

# Restart Docker Desktop (macOS)
# Applications → Docker → Restart

# Check emulator logs
docker-compose logs -f
```

### Connection Issues

```python
# Always use context manager with fakesnow
with fakesnow.patch():
    # Your code here
    pass

# For emulator, ensure it's running
docker-compose ps
```

## Additional Resources

### fakesnow
- [GitHub Repository](https://github.com/tekumara/fakesnow)
- [PyPI Package](https://pypi.org/project/fakesnow/)

### snowflake-emulator
- [GitHub Repository](https://github.com/nnnkkk7/snowflake-emulator)
- [DEV Community Article](https://dev.to/kurorr/stop-burning-snowflake-credits-build-a-local-emulator-with-go-and-duckdb-44lk)

### Snowflake
- [Official Documentation](https://docs.snowflake.com/)
- [Free Trial Signup](https://signup.snowflake.com/)
- [Sample Data Documentation](https://docs.snowflake.com/en/user-guide/sample-data)

### DuckDB
- [Official Documentation](https://duckdb.org/docs/)
- [SQL Introduction](https://duckdb.org/docs/sql/introduction)

## Files in This Project

```
agent-snowflake/
├── README_TESTING.md              # This file
├── TESTING_FAKESNOW.md           # fakesnow detailed docs
├── TESTING.md                    # Docker emulator detailed docs
├── docker-compose.yml            # Docker emulator config
├── test_fakesnow.py              # fakesnow test script
├── test_emulator.py              # Docker emulator test script
├── .env.example                  # Environment variables template
└── scripts/
    ├── init_data.sql             # Sample data for Docker emulator
    └── test_connection.py        # Detailed emulator test
```

## Next Steps

1. Choose your testing approach (fakesnow recommended)
2. Install dependencies and run test scripts
3. Review the sample data and queries
4. Start building your Snowflake agent
5. Switch to real Snowflake for production

## Support

- For fakesnow issues: https://github.com/tekumara/fakesnow/issues
- For snowflake-emulator issues: https://github.com/nnnkkk7/snowflake-emulator/issues
- For Snowflake issues: https://community.snowflake.com/
