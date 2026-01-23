# Testing Guide

This directory contains tests for the Snowflake agent project.

## Quick Start

Run all tests with fakesnow (recommended):

```bash
pytest tests/
```

Run specific test files:

```bash
pytest tests/test_snowflake_fakesnow.py
pytest tests/test_agent.py
```

## Test Organization

### Test Files

- **test_snowflake_fakesnow.py** - Tests using fakesnow (recommended)
  - Pure Python implementation with DuckDB backend
  - Fast, no Docker required
  - Best for local development and CI/CD

- **test_snowflake_emulator.py** - Tests using Docker emulator (alternative)
  - Requires Docker running and `docker-compose up -d`
  - More complete Snowflake environment
  - Run with: `pytest tests/test_snowflake_emulator.py --emulator`

- **test_agent.py** - Agent graph tests
  - Verifies LangGraph agent compiles
  - Requires API keys for full invocation tests

### Fixtures

#### Python Fixtures (conftest.py)

Reusable pytest fixtures for testing:

- `fakesnow_connection` - Provides a fakesnow-patched Snowflake connection
- `sample_database` - Creates SAMPLE_DB database and TPCH_SAMPLE schema
- `tpch_tables` - Creates TPC-H inspired tables (REGION, NATION, CUSTOMER, ORDERS, PART, LINEITEM)
- `tpch_sample_data` - Loads sample data into all tables

#### SQL Fixtures (fixtures/init_data.sql)

Sample SQL data for Docker emulator testing. Contains:
- TPC-H inspired schema
- Sample data for regions, nations, customers, orders, parts, and line items

## Testing Approaches

### Recommended: fakesnow

```python
def test_example(tpch_sample_data):
    """Test with fully populated sample data."""
    cursor = tpch_sample_data.cursor()
    cursor.execute("SELECT COUNT(*) FROM CUSTOMER")
    count = cursor.fetchone()[0]
    assert count == 10
```

**Advantages:**
- No Docker required
- Fast execution
- Easy CI/CD integration
- Pure Python

**Limitations:**
- Not 100% Snowflake feature parity
- May not catch all Snowflake-specific issues

### Alternative: Docker Emulator

```bash
# Start emulator
docker-compose up -d

# Run emulator tests
pytest tests/test_snowflake_emulator.py --emulator

# Stop emulator
docker-compose down
```

**Advantages:**
- More complete Snowflake environment
- Better for testing Snowflake-specific features

**Limitations:**
- Requires Docker
- Slower than fakesnow
- More complex setup

## Writing New Tests

### Using Existing Fixtures

```python
def test_my_query(tpch_sample_data):
    """Test a custom query."""
    cursor = tpch_sample_data.cursor()

    cursor.execute("""
        SELECT c.C_NAME, COUNT(o.O_ORDERKEY)
        FROM CUSTOMER c
        JOIN ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
        GROUP BY c.C_NAME
    """)

    results = cursor.fetchall()
    assert len(results) > 0
```

### Creating Custom Fixtures

Add to `conftest.py`:

```python
@pytest.fixture
def custom_table(sample_database):
    """Create a custom table for testing."""
    cursor = sample_database.cursor()
    cursor.execute("""
        CREATE TABLE MY_TABLE (
            id INTEGER PRIMARY KEY,
            name VARCHAR(100)
        )
    """)
    cursor.close()
    return sample_database
```

## Running Tests in CI/CD

```yaml
# Example GitHub Actions
- name: Install dependencies
  run: uv sync

- name: Run tests
  run: uv run pytest tests/
```

## Troubleshooting

### Missing Dependencies

```bash
uv add fakesnow snowflake-connector-python pytest
```

### Docker Emulator Not Starting

```bash
# Check Docker is running
docker ps

# View emulator logs
docker-compose logs

# Restart emulator
docker-compose down
docker-compose up -d
```

### Test Failures

```bash
# Run with verbose output
pytest tests/ -v

# Run specific test
pytest tests/test_snowflake_fakesnow.py::TestQueries::test_join_query -v

# Show print statements
pytest tests/ -s
```

## Additional Resources

- [fakesnow Documentation](https://github.com/tekumara/fakesnow)
- [Snowflake Python Connector](https://docs.snowflake.com/en/user-guide/python-connector.html)
- [pytest Documentation](https://docs.pytest.org/)
