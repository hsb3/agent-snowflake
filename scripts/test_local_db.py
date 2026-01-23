#!/usr/bin/env python3
"""Test script to verify agent tools work with the test database."""

from pathlib import Path

from agent_snowflake.context import ContextSchema
from agent_snowflake.utils import init_model, create_sql_database

# Get database path (in project root, one level up from scripts/)
db_path = (Path(__file__).parent.parent / "test_snowflake.db").resolve()

if not db_path.exists():
    print(f"❌ Database not found: {db_path}")
    print("   Run: make setup-test-db")
    exit(1)

print(f"📦 Using database: {db_path}")

# Create context with test database
context = ContextSchema(
    model="claude-haiku-4-5",
    temperature=0.0,
    snowflake_uri=f"sqlite:///{db_path}",
    allowed_schemas="*",
    allowed_tables="*",
    read_only=True,
    query_timeout=30,
    max_iterations=25,
    enable_debug=False,
)

print(f"✓ Context created")

# Test database connection
try:
    db = create_sql_database(context)
    print(f"✓ Database connection successful")
    print(f"  Dialect: {db.dialect}")

    # List tables
    tables = db.get_usable_table_names()
    print(f"  Tables: {tables}")

    # Get table info
    if tables:
        table_info = db.get_table_info(table_names=tables[:2])
        print(f"\n📋 Sample table info:")
        print(table_info[:500] + "..." if len(table_info) > 500 else table_info)

    # Run a test query
    result = db.run("SELECT COUNT(*) as count FROM CUSTOMER")
    print(f"\n🔍 Test query result:")
    print(f"  Customer count: {result}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
    exit(1)

print("\n All checks passed!")
