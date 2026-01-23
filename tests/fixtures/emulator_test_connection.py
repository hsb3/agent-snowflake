#!/usr/bin/env python3
"""
Test connection to Snowflake Emulator and verify data loading.
"""

import snowflake.connector
from typing import Optional
import sys


def create_connection(
    account: str = "test",
    user: str = "test",
    password: str = "test",
    host: str = "localhost",
    port: int = 8080,
    database: Optional[str] = None,
    schema: Optional[str] = None,
) -> snowflake.connector.SnowflakeConnection:
    """Create a connection to the Snowflake emulator."""
    conn_params = {
        "account": account,
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "protocol": "http",  # Emulator uses HTTP
        "insecure_mode": True,  # No SSL for local testing
    }

    if database:
        conn_params["database"] = database
    if schema:
        conn_params["schema"] = schema

    return snowflake.connector.connect(**conn_params)


def test_basic_connection():
    """Test basic connection to emulator."""
    print("Testing basic connection...")
    try:
        conn = create_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 'Hello from Snowflake Emulator!' as message")
        result = cursor.fetchone()
        print(f"✓ Connection successful: {result[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_database_creation():
    """Test creating a database and schema."""
    print("\nTesting database and schema creation...")
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Create database
        cursor.execute("CREATE DATABASE IF NOT EXISTS SAMPLE_DB")
        cursor.execute("USE DATABASE SAMPLE_DB")
        print("✓ Database SAMPLE_DB created/selected")

        # Create schema
        cursor.execute("CREATE SCHEMA IF NOT EXISTS TPCH_SAMPLE")
        cursor.execute("USE SCHEMA TPCH_SAMPLE")
        print("✓ Schema TPCH_SAMPLE created/selected")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Database creation failed: {e}")
        return False


def load_sample_data():
    """Load sample data from init_data.sql."""
    print("\nLoading sample data from init_data.sql...")
    try:
        with open("init_data.sql", "r") as f:
            sql_content = f.read()

        conn = create_connection()
        cursor = conn.cursor()

        # Split SQL by semicolons and execute each statement
        statements = [s.strip() for s in sql_content.split(";") if s.strip() and not s.strip().startswith("--")]

        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    cursor.execute(statement)
                    if i % 10 == 0:
                        print(f"  Executed {i}/{len(statements)} statements...")
                except Exception as e:
                    print(f"  Warning: Statement {i} failed: {str(e)[:100]}")

        print(f"✓ Loaded sample data ({len(statements)} statements executed)")

        cursor.close()
        conn.close()
        return True
    except FileNotFoundError:
        print("✗ init_data.sql file not found. Run from scripts/ directory.")
        return False
    except Exception as e:
        print(f"✗ Data loading failed: {e}")
        return False


def verify_data():
    """Verify that sample data was loaded correctly."""
    print("\nVerifying sample data...")
    try:
        conn = create_connection(database="SAMPLE_DB", schema="TPCH_SAMPLE")
        cursor = conn.cursor()

        # Check table counts
        tables = ["REGION", "NATION", "CUSTOMER", "ORDERS", "PART", "LINEITEM"]

        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✓ {table}: {count} rows")

        # Test a sample query
        print("\nTesting sample query (top 5 customers by spending):")
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

        results = cursor.fetchall()
        for i, (name, total) in enumerate(results, 1):
            print(f"  {i}. {name}: ${total:,.2f}")

        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"✗ Data verification failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Snowflake Emulator Connection Test")
    print("=" * 60)

    tests = [
        ("Basic Connection", test_basic_connection),
        ("Database Creation", test_database_creation),
        ("Sample Data Loading", load_sample_data),
        ("Data Verification", verify_data),
    ]

    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
        if not result:
            print(f"\n⚠ Test '{test_name}' failed. Stopping further tests.")
            break

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")

    all_passed = all(result for _, result in results)
    print("=" * 60)

    if all_passed:
        print("\n🎉 All tests passed! Snowflake emulator is ready to use.")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
