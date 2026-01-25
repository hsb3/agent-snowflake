#!/usr/bin/env python3
"""Setup script for test SQLite database.

Creates a persistent SQLite database with TPC-H sample data for testing
the Snowflake agent via LangGraph Studio.

⚠️ LIMITATIONS: SQLite != Snowflake
- No VARIANT/OBJECT/ARRAY types
- No FLATTEN(), QUALIFY, or Snowflake-specific functions
- Different date/time handling
- For production testing, use actual Snowflake or Snowflake trial account

Usage:
    uv run python scripts/setup_fakesnow_db.py

This will create:
    - test_snowflake.db - SQLite database with sample data
    - Connection URI to use in LangGraph Studio
"""

import sys
from pathlib import Path

try:
    from sqlalchemy import create_engine, text
except ImportError:
    print("❌ sqlalchemy not installed")
    print("   Run: make install")
    sys.exit(1)


def setup_database():
    """Create and populate test database with TPC-H sample data."""

    db_path = Path("test_snowflake.db")

    # Remove existing database
    if db_path.exists():
        print(f"🗑️  Removing existing database: {db_path}")
        db_path.unlink()

    print(f"📦 Creating new SQLite database: {db_path}")
    print("   ⚠️  Note: SQLite has limited Snowflake compatibility")
    print("   For Snowflake-specific features, test with actual Snowflake")

    # Create SQLite engine
    engine = create_engine(f"sqlite:///{db_path}")

    print("✓ Database created")

    with engine.connect() as conn:
        # Create REGION table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS REGION (
                R_REGIONKEY INTEGER PRIMARY KEY,
                R_NAME VARCHAR(25),
                R_COMMENT VARCHAR(152)
            )
        """)
        )
        print("✓ REGION table created")

        # Insert region data
        regions = [
            (
                0,
                "AFRICA",
                "lar deposits. blithely final packages cajole. regular waters are final requests.",
            ),
            (1, "AMERICA", "hs use ironic, even requests. s"),
            (2, "ASIA", "ges. thinly even pinto beans ca"),
            (3, "EUROPE", "ly final courts cajole furiously final excuse"),
            (4, "MIDDLE EAST", "uickly special accounts cajole carefully blithely close requests."),
        ]

        for region in regions:
            conn.execute(
                text(
                    "INSERT INTO REGION (R_REGIONKEY, R_NAME, R_COMMENT) VALUES (:key, :name, :comment)"
                ),
                {"key": region[0], "name": region[1], "comment": region[2]},
            )
        print(f"✓ Inserted {len(regions)} regions")

        # Create CUSTOMER table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS CUSTOMER (
                C_CUSTKEY INTEGER PRIMARY KEY,
                C_NAME VARCHAR(25),
                C_ADDRESS VARCHAR(40),
                C_NATIONKEY INTEGER,
                C_PHONE VARCHAR(15),
                C_ACCTBAL DECIMAL(15,2),
                C_MKTSEGMENT VARCHAR(10),
                C_COMMENT VARCHAR(117)
            )
        """)
        )
        print("✓ CUSTOMER table created")

        # Insert customer data
        customers = [
            (
                1,
                "Customer#000000001",
                "IVhzIApeRb ot,c,E",
                15,
                "25-989-741-2988",
                711.56,
                "BUILDING",
                "to the even, regular platelets.",
            ),
            (
                2,
                "Customer#000000002",
                "XSTf4,NCwDVaWNe6tEgvwfmRchLXak",
                13,
                "23-768-687-3665",
                121.65,
                "AUTOMOBILE",
                "l accounts. blithely ironic theodolites integrate",
            ),
            (
                3,
                "Customer#000000003",
                "MG9kdTD2WBHm",
                1,
                "11-719-748-3364",
                7498.12,
                "AUTOMOBILE",
                " deposits eat slyly ironic, even instructions.",
            ),
            (
                4,
                "Customer#000000004",
                "XxVSJsLAGtn",
                4,
                "14-128-190-5944",
                2866.83,
                "MACHINERY",
                " requests. final, regular ideas sleep final accou",
            ),
            (
                5,
                "Customer#000000005",
                "KvpyuHCplrB84WgAiGV6sYpZq7Tj",
                3,
                "13-750-942-6364",
                794.47,
                "HOUSEHOLD",
                "n accounts will have to unwind. foxes cajole accor",
            ),
        ]

        for customer in customers:
            conn.execute(
                text(
                    "INSERT INTO CUSTOMER VALUES (:key, :name, :address, :nation, :phone, :bal, :segment, :comment)"
                ),
                {
                    "key": customer[0],
                    "name": customer[1],
                    "address": customer[2],
                    "nation": customer[3],
                    "phone": customer[4],
                    "bal": customer[5],
                    "segment": customer[6],
                    "comment": customer[7],
                },
            )
        print(f"✓ Inserted {len(customers)} customers")

        # Create ORDERS table
        conn.execute(
            text("""
            CREATE TABLE IF NOT EXISTS ORDERS (
                O_ORDERKEY INTEGER PRIMARY KEY,
                O_CUSTKEY INTEGER,
                O_ORDERSTATUS CHAR(1),
                O_TOTALPRICE DECIMAL(15,2),
                O_ORDERDATE DATE,
                O_ORDERPRIORITY VARCHAR(15),
                O_CLERK VARCHAR(15),
                O_SHIPPRIORITY INTEGER,
                O_COMMENT VARCHAR(79)
            )
        """)
        )
        print("✓ ORDERS table created")

        # Insert order data
        orders = [
            (
                1,
                1,
                "O",
                173665.47,
                "1996-01-02",
                "5-LOW",
                "Clerk#000000951",
                0,
                "nstructions sleep furiously among",
            ),
            (
                2,
                2,
                "O",
                46929.18,
                "1996-12-01",
                "1-URGENT",
                "Clerk#000000880",
                0,
                " foxes. pending accounts at the pending",
            ),
            (
                3,
                3,
                "F",
                193846.25,
                "1993-10-14",
                "5-LOW",
                "Clerk#000000955",
                0,
                "sly final accounts boost. carefully",
            ),
        ]

        for order in orders:
            conn.execute(
                text(
                    "INSERT INTO ORDERS VALUES (:key, :cust, :status, :price, :date, :priority, :clerk, :ship, :comment)"
                ),
                {
                    "key": order[0],
                    "cust": order[1],
                    "status": order[2],
                    "price": order[3],
                    "date": order[4],
                    "priority": order[5],
                    "clerk": order[6],
                    "ship": order[7],
                    "comment": order[8],
                },
            )
        print(f"✓ Inserted {len(orders)} orders")

        # Commit all changes
        conn.commit()

        # Verify data
        region_count = conn.execute(text("SELECT COUNT(*) FROM REGION")).scalar()
        customer_count = conn.execute(text("SELECT COUNT(*) FROM CUSTOMER")).scalar()
        order_count = conn.execute(text("SELECT COUNT(*) FROM ORDERS")).scalar()

        print(f"\n📊 Database summary:")
        print(f"   REGION: {region_count} rows")
        print(f"   CUSTOMER: {customer_count} rows")
        print(f"   ORDERS: {order_count} rows")

    return db_path


def main():
    """Setup fakesnow database and print connection instructions."""

    print("=" * 60)
    print("Fakesnow Test Database Setup")
    print("=" * 60)
    print()

    db_path = setup_database()

    # Get absolute path
    abs_path = db_path.absolute()

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print(f"\nDatabase file: {abs_path}")
    print(f"\n📝 To use with LangGraph Studio:")
    print(f"\n1. Add to your .env file:")
    print(f"   SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///{abs_path}")
    print(f"\n2. Or set in Studio UI Assistant Config:")
    print(f"   snowflake_uri: sqlite:///{abs_path}")
    print(f"\n3. Start the dev server:")
    print(f"   make dev")
    print(f"\n4. Try these queries in Studio:")
    print(f"   - 'Show me all tables'")
    print(f"   - 'What regions are available?'")
    print(f"   - 'Count the number of customers'")
    print(f"   - 'Show me all orders'")
    print()


if __name__ == "__main__":
    main()
