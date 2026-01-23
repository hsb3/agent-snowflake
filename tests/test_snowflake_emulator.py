#!/usr/bin/env python3
"""Tests for Snowflake using Docker emulator (alternative testing approach).

The Docker emulator provides a more complete Snowflake environment but requires
Docker to be running. Use fakesnow for faster, simpler testing.

Prerequisites:
    - Docker installed and running
    - Start emulator with: docker-compose up -d
    - Run with: pytest tests/test_snowflake_emulator.py --emulator
"""

import pytest
import snowflake.connector


# Skip all emulator tests by default unless --emulator flag is used
pytestmark = pytest.mark.skipif(
    "not config.getoption('--emulator', default=False)",
    reason="Need --emulator option to run (requires docker-compose up)",
)


@pytest.fixture
def emulator_connection():
    """Provide a connection to the Docker emulator."""
    try:
        conn = snowflake.connector.connect(
            account="test",
            user="test",
            password="test",
            host="localhost",
            port=8080,
            protocol="http",
            insecure_mode=True,
        )
        yield conn
        conn.close()
    except Exception as e:
        pytest.skip(f"Cannot connect to emulator: {e}")


class TestEmulatorConnection:
    """Test basic connection to emulator."""

    def test_basic_connection(self, emulator_connection):
        """Test that we can establish a connection."""
        cursor = emulator_connection.cursor()
        cursor.execute("SELECT 'Hello from Snowflake Emulator!' as message")
        result = cursor.fetchone()
        assert "Emulator" in result[0]
        cursor.close()


class TestEmulatorDatabaseOperations:
    """Test database operations on emulator."""

    def test_create_database_and_schema(self, emulator_connection):
        """Test creating database and schema."""
        cursor = emulator_connection.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS TEST_DB")
        cursor.execute("USE DATABASE TEST_DB")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS TEST_SCHEMA")
        cursor.execute("USE SCHEMA TEST_SCHEMA")

        cursor.close()

    def test_create_table(self, emulator_connection):
        """Test creating a table."""
        cursor = emulator_connection.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS TEST_DB")
        cursor.execute("USE DATABASE TEST_DB")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS TEST_SCHEMA")
        cursor.execute("USE SCHEMA TEST_SCHEMA")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SAMPLE_TABLE (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100),
                value DECIMAL(10,2)
            )
        """)

        cursor.close()

    def test_insert_and_query_data(self, emulator_connection):
        """Test inserting and querying data."""
        cursor = emulator_connection.cursor()

        # Setup
        cursor.execute("CREATE DATABASE IF NOT EXISTS TEST_DB")
        cursor.execute("USE DATABASE TEST_DB")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS TEST_SCHEMA")
        cursor.execute("USE SCHEMA TEST_SCHEMA")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SAMPLE_TABLE (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100),
                value DECIMAL(10,2)
            )
        """)

        # Insert data
        cursor.execute(
            "INSERT INTO SAMPLE_TABLE VALUES (1, 'Test Item 1', 100.50)"
        )
        cursor.execute(
            "INSERT INTO SAMPLE_TABLE VALUES (2, 'Test Item 2', 250.75)"
        )
        cursor.execute(
            "INSERT INTO SAMPLE_TABLE VALUES (3, 'Test Item 3', 500.00)"
        )

        # Query data
        cursor.execute("SELECT * FROM SAMPLE_TABLE ORDER BY id")
        rows = cursor.fetchall()

        assert len(rows) == 3
        assert rows[0][0] == 1
        assert rows[1][0] == 2
        assert rows[2][0] == 3

        cursor.close()

    def test_aggregate_query(self, emulator_connection):
        """Test aggregate functions on emulator."""
        cursor = emulator_connection.cursor()

        # Setup
        cursor.execute("CREATE DATABASE IF NOT EXISTS TEST_DB")
        cursor.execute("USE DATABASE TEST_DB")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS TEST_SCHEMA")
        cursor.execute("USE SCHEMA TEST_SCHEMA")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS SAMPLE_TABLE (
                id INTEGER PRIMARY KEY,
                name VARCHAR(100),
                value DECIMAL(10,2)
            )
        """)

        cursor.execute(
            "INSERT INTO SAMPLE_TABLE VALUES (1, 'Test Item 1', 100.50)"
        )
        cursor.execute(
            "INSERT INTO SAMPLE_TABLE VALUES (2, 'Test Item 2', 250.75)"
        )
        cursor.execute(
            "INSERT INTO SAMPLE_TABLE VALUES (3, 'Test Item 3', 500.00)"
        )

        # Test aggregate
        cursor.execute(
            "SELECT COUNT(*) as count, SUM(value) as total FROM SAMPLE_TABLE"
        )
        result = cursor.fetchone()

        assert result[0] == 3  # count
        assert result[1] == 851.25  # total

        cursor.close()
