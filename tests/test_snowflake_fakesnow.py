"""Tests for Snowflake using fakesnow (recommended testing approach).

fakesnow provides a pure Python implementation using DuckDB as the backend,
allowing fast local testing without Docker or real Snowflake credentials.
"""



class TestBasicConnection:
    """Test basic Snowflake connection with fakesnow."""

    def test_connection_establishes(self, fakesnow_connection):
        """Test that we can establish a connection."""
        assert fakesnow_connection is not None
        cursor = fakesnow_connection.cursor()
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        assert result[0] == 1
        cursor.close()


class TestDatabaseOperations:
    """Test database and schema operations."""

    def test_database_creation(self, sample_database):
        """Test database and schema are created."""
        cursor = sample_database.cursor()
        cursor.execute("SELECT CURRENT_DATABASE()")
        db_name = cursor.fetchone()[0]
        assert db_name == "SAMPLE_DB"
        cursor.close()

    def test_schema_creation(self, sample_database):
        """Test schema is created and accessible."""
        cursor = sample_database.cursor()
        cursor.execute("SELECT CURRENT_SCHEMA()")
        schema_name = cursor.fetchone()[0]
        assert schema_name == "TPCH_SAMPLE"
        cursor.close()


class TestTableOperations:
    """Test table creation and operations."""

    def test_tables_exist(self, tpch_tables):
        """Test that all TPC-H tables are created."""
        cursor = tpch_tables.cursor()

        expected_tables = ["REGION", "NATION", "CUSTOMER", "ORDERS", "PART", "LINEITEM"]

        for table in expected_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            # Just verify the query doesn't fail
            cursor.fetchone()

        cursor.close()

    def test_table_structure(self, tpch_tables):
        """Test that tables have expected structure."""
        cursor = tpch_tables.cursor()

        # Test REGION table structure
        cursor.execute("DESCRIBE TABLE REGION")
        columns = cursor.fetchall()
        column_names = [col[0] for col in columns]

        assert "R_REGIONKEY" in column_names
        assert "R_NAME" in column_names
        assert "R_COMMENT" in column_names

        cursor.close()


class TestDataLoading:
    """Test data loading into tables."""

    def test_data_counts(self, tpch_sample_data):
        """Test that expected number of rows are loaded."""
        cursor = tpch_sample_data.cursor()

        expected_counts = {
            "REGION": 5,
            "NATION": 10,
            "CUSTOMER": 10,
            "ORDERS": 10,
            "PART": 5,
            "LINEITEM": 5,
        }

        for table, expected_count in expected_counts.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            actual_count = cursor.fetchone()[0]
            assert (
                actual_count == expected_count
            ), f"{table} has {actual_count} rows, expected {expected_count}"

        cursor.close()

    def test_region_data(self, tpch_sample_data):
        """Test REGION table contains expected data."""
        cursor = tpch_sample_data.cursor()

        cursor.execute("SELECT R_NAME FROM REGION ORDER BY R_REGIONKEY")
        regions = [row[0] for row in cursor.fetchall()]

        expected_regions = ["AFRICA", "AMERICA", "ASIA", "EUROPE", "MIDDLE EAST"]
        assert regions == expected_regions

        cursor.close()

    def test_nation_data(self, tpch_sample_data):
        """Test NATION table contains expected data."""
        cursor = tpch_sample_data.cursor()

        cursor.execute("SELECT COUNT(DISTINCT N_NAME) FROM NATION")
        nation_count = cursor.fetchone()[0]
        assert nation_count == 10

        cursor.close()


class TestQueries:
    """Test SQL queries against sample data."""

    def test_simple_select(self, tpch_sample_data):
        """Test simple SELECT query."""
        cursor = tpch_sample_data.cursor()

        cursor.execute("SELECT COUNT(*) FROM CUSTOMER")
        count = cursor.fetchone()[0]
        assert count == 10

        cursor.close()

    def test_join_query(self, tpch_sample_data):
        """Test JOIN between CUSTOMER and ORDERS."""
        cursor = tpch_sample_data.cursor()

        cursor.execute("""
            SELECT c.C_NAME, COUNT(o.O_ORDERKEY) as order_count
            FROM CUSTOMER c
            JOIN ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
            GROUP BY c.C_NAME
            ORDER BY order_count DESC
            LIMIT 1
        """)

        result = cursor.fetchone()
        assert result is not None
        assert result[1] == 1  # Each customer has 1 order in sample data

        cursor.close()

    def test_aggregate_query(self, tpch_sample_data):
        """Test aggregate functions."""
        cursor = tpch_sample_data.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_orders,
                SUM(O_TOTALPRICE) as total_revenue,
                AVG(O_TOTALPRICE) as avg_order_value
            FROM ORDERS
        """)

        result = cursor.fetchone()
        assert result[0] == 10  # total_orders
        assert result[1] > 0  # total_revenue
        assert result[2] > 0  # avg_order_value

        cursor.close()

    def test_multi_table_join(self, tpch_sample_data):
        """Test multi-table JOIN query."""
        cursor = tpch_sample_data.cursor()

        cursor.execute("""
            SELECT
                r.R_NAME as region,
                COUNT(DISTINCT c.C_CUSTKEY) as customer_count
            FROM REGION r
            JOIN NATION n ON r.R_REGIONKEY = n.N_REGIONKEY
            JOIN CUSTOMER c ON n.N_NATIONKEY = c.C_NATIONKEY
            GROUP BY r.R_NAME
            ORDER BY customer_count DESC
        """)

        results = cursor.fetchall()
        assert len(results) > 0

        # Verify we have customers in some regions
        total_customers = sum(row[1] for row in results)
        assert total_customers == 10  # Total customers in sample data

        cursor.close()

    def test_filtering_and_sorting(self, tpch_sample_data):
        """Test WHERE clause and ORDER BY."""
        cursor = tpch_sample_data.cursor()

        cursor.execute("""
            SELECT C_NAME, C_ACCTBAL
            FROM CUSTOMER
            WHERE C_ACCTBAL > 5000
            ORDER BY C_ACCTBAL DESC
        """)

        results = cursor.fetchall()
        assert len(results) > 0

        # Verify results are sorted descending
        balances = [row[1] for row in results]
        assert balances == sorted(balances, reverse=True)

        cursor.close()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_table_query(self, tpch_tables):
        """Test querying empty tables."""
        cursor = tpch_tables.cursor()

        # Tables are created but not yet populated
        cursor.execute("SELECT COUNT(*) FROM CUSTOMER")
        count = cursor.fetchone()[0]
        assert count == 0

        cursor.close()

    def test_duplicate_database_creation(self, sample_database):
        """Test creating database that already exists."""
        cursor = sample_database.cursor()

        # Should not raise error with IF NOT EXISTS
        cursor.execute("CREATE DATABASE IF NOT EXISTS SAMPLE_DB")

        cursor.close()
