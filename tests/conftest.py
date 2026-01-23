"""Pytest configuration and shared fixtures for Snowflake testing."""

import fakesnow
import pytest
import snowflake.connector


def pytest_addoption(parser):
    """Add custom pytest options."""
    parser.addoption(
        "--emulator",
        action="store_true",
        default=False,
        help="Run tests against Docker emulator (requires docker-compose up)",
    )


@pytest.fixture
def fakesnow_connection():
    """Provide a fakesnow-patched Snowflake connection."""
    with fakesnow.patch():
        conn = snowflake.connector.connect()
        yield conn
        conn.close()


@pytest.fixture
def sample_database(fakesnow_connection):
    """Create sample database and schema."""
    cursor = fakesnow_connection.cursor()

    cursor.execute("CREATE DATABASE IF NOT EXISTS SAMPLE_DB")
    cursor.execute("USE DATABASE SAMPLE_DB")
    cursor.execute("CREATE SCHEMA IF NOT EXISTS TPCH_SAMPLE")
    cursor.execute("USE SCHEMA TPCH_SAMPLE")

    cursor.close()

    return fakesnow_connection


@pytest.fixture
def tpch_tables(sample_database):
    """Create TPC-H inspired tables."""
    cursor = sample_database.cursor()

    # REGION table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS REGION (
            R_REGIONKEY INTEGER PRIMARY KEY,
            R_NAME VARCHAR(25) NOT NULL,
            R_COMMENT VARCHAR(152)
        )
    """)

    # NATION table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS NATION (
            N_NATIONKEY INTEGER PRIMARY KEY,
            N_NAME VARCHAR(25) NOT NULL,
            N_REGIONKEY INTEGER NOT NULL,
            N_COMMENT VARCHAR(152)
        )
    """)

    # CUSTOMER table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS CUSTOMER (
            C_CUSTKEY INTEGER PRIMARY KEY,
            C_NAME VARCHAR(25) NOT NULL,
            C_ADDRESS VARCHAR(40),
            C_NATIONKEY INTEGER NOT NULL,
            C_PHONE VARCHAR(15),
            C_ACCTBAL DECIMAL(15,2),
            C_MKTSEGMENT VARCHAR(10),
            C_COMMENT VARCHAR(117)
        )
    """)

    # ORDERS table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ORDERS (
            O_ORDERKEY INTEGER PRIMARY KEY,
            O_CUSTKEY INTEGER NOT NULL,
            O_ORDERSTATUS VARCHAR(1),
            O_TOTALPRICE DECIMAL(15,2),
            O_ORDERDATE DATE,
            O_ORDERPRIORITY VARCHAR(15),
            O_CLERK VARCHAR(15),
            O_SHIPPRIORITY INTEGER,
            O_COMMENT VARCHAR(79)
        )
    """)

    # PART table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PART (
            P_PARTKEY INTEGER PRIMARY KEY,
            P_NAME VARCHAR(55) NOT NULL,
            P_MFGR VARCHAR(25),
            P_BRAND VARCHAR(10),
            P_TYPE VARCHAR(25),
            P_SIZE INTEGER,
            P_CONTAINER VARCHAR(10),
            P_RETAILPRICE DECIMAL(15,2),
            P_COMMENT VARCHAR(23)
        )
    """)

    # LINEITEM table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS LINEITEM (
            L_ORDERKEY INTEGER NOT NULL,
            L_PARTKEY INTEGER NOT NULL,
            L_SUPPKEY INTEGER NOT NULL,
            L_LINENUMBER INTEGER NOT NULL,
            L_QUANTITY DECIMAL(15,2),
            L_EXTENDEDPRICE DECIMAL(15,2),
            L_DISCOUNT DECIMAL(15,2),
            L_TAX DECIMAL(15,2),
            L_RETURNFLAG VARCHAR(1),
            L_LINESTATUS VARCHAR(1),
            L_SHIPDATE DATE,
            L_COMMITDATE DATE,
            L_RECEIPTDATE DATE,
            L_SHIPINSTRUCT VARCHAR(25),
            L_SHIPMODE VARCHAR(10),
            L_COMMENT VARCHAR(44)
        )
    """)

    cursor.close()

    return sample_database


@pytest.fixture
def tpch_sample_data(tpch_tables):
    """Load sample data into TPC-H tables."""
    cursor = tpch_tables.cursor()

    # Insert REGION data
    cursor.execute("""
        INSERT INTO REGION VALUES
        (0, 'AFRICA', 'lar deposits. blithely final packages cajole'),
        (1, 'AMERICA', 'hs use ironic, even requests'),
        (2, 'ASIA', 'ges. thinly even pinto beans ca'),
        (3, 'EUROPE', 'ly final courts cajole furiously'),
        (4, 'MIDDLE EAST', 'uickly special accounts cajole')
    """)

    # Insert NATION data
    cursor.execute("""
        INSERT INTO NATION VALUES
        (0, 'ALGERIA', 0, ' haggle. carefully final deposits detect'),
        (1, 'ARGENTINA', 1, 'al foxes promise slyly according to the regular'),
        (2, 'BRAZIL', 1, 'y alongside of the pending deposits'),
        (3, 'CANADA', 1, 'eas hang ironic, silent packages'),
        (4, 'EGYPT', 4, 'y above the carefully unusual theodolites'),
        (5, 'FRANCE', 3, 'refully final requests'),
        (6, 'GERMANY', 3, 'l platelets. regular accounts x-ray'),
        (7, 'INDIA', 2, 'ss excuses cajole slyly across the packages'),
        (8, 'JAPAN', 2, 'ously. final, express gifts cajole a'),
        (9, 'UNITED STATES', 1, 'y final packages. slow foxes cajole quickly')
    """)

    # Insert CUSTOMER data
    cursor.execute("""
        INSERT INTO CUSTOMER VALUES
        (1, 'Customer#000000001', '1234 Main St', 5, '15-989-741-2988', 711.56, 'BUILDING', 'to the even'),
        (2, 'Customer#000000002', '5678 Oak Ave', 9, '25-768-687-3665', 121.65, 'AUTOMOBILE', 'l accounts'),
        (3, 'Customer#000000003', '9012 Pine Rd', 1, '11-719-748-3364', 7498.12, 'AUTOMOBILE', 'deposits eat'),
        (4, 'Customer#000000004', '3456 Elm Blvd', 4, '14-128-190-5944', 2866.83, 'MACHINERY', 'requests'),
        (5, 'Customer#000000005', '7890 Maple Dr', 3, '13-750-942-6364', 794.47, 'HOUSEHOLD', 'n accounts'),
        (6, 'Customer#000000006', '2345 Cedar Ln', 6, '20-114-968-4951', 7638.57, 'AUTOMOBILE', 'tions'),
        (7, 'Customer#000000007', '6789 Birch Way', 8, '29-316-665-2897', 9561.95, 'AUTOMOBILE', 'ainst'),
        (8, 'Customer#000000008', '1357 Walnut St', 2, '17-719-320-3948', 6819.74, 'BUILDING', 'among'),
        (9, 'Customer#000000009', '2468 Ash Ct', 7, '18-338-906-3675', 8324.07, 'FURNITURE', 'r theodolites'),
        (10, 'Customer#000000010', '3579 Spruce Pl', 0, '15-741-346-9870', 2753.54, 'HOUSEHOLD', 'es regular')
    """)

    # Insert ORDERS data
    cursor.execute("""
        INSERT INTO ORDERS VALUES
        (1, 1, 'O', 173665.47, '1996-01-02', '5-LOW', 'Clerk#000000951', 0, 'nstructions'),
        (2, 2, 'O', 46929.18, '1996-12-01', '1-URGENT', 'Clerk#000000880', 0, 'foxes'),
        (3, 3, 'F', 193846.25, '1993-10-14', '5-LOW', 'Clerk#000000955', 0, 'sly final'),
        (4, 4, 'O', 32151.78, '1995-10-11', '5-LOW', 'Clerk#000000124', 0, 'sits'),
        (5, 5, 'F', 144659.20, '1994-07-30', '5-LOW', 'Clerk#000000925', 0, 'quickly'),
        (6, 6, 'F', 58749.59, '1992-02-21', '4-NOT SPECIFIED', 'Clerk#000000058', 0, 'ggle'),
        (7, 7, 'O', 252004.18, '1996-01-10', '2-HIGH', 'Clerk#000000470', 0, 'ly special'),
        (8, 8, 'F', 301629.35, '1995-07-16', '2-HIGH', 'Clerk#000000280', 0, 'r theodolites'),
        (9, 9, 'F', 220111.60, '1998-03-18', '3-MEDIUM', 'Clerk#000000659', 0, 'carefully'),
        (10, 10, 'O', 181876.88, '1998-10-21', '5-LOW', 'Clerk#000000226', 0, 'xpress')
    """)

    # Insert PART data
    cursor.execute("""
        INSERT INTO PART VALUES
        (1, 'goldenrod lavender spring chocolate lace', 'Manufacturer#1', 'Brand#13', 'PROMO BURNISHED COPPER', 7, 'JUMBO PKG', 901.00, 'ly. slyly ironi'),
        (2, 'blush thistle blue yellow saddle', 'Manufacturer#1', 'Brand#13', 'LARGE BRUSHED BRASS', 1, 'LG CASE', 902.00, 'lar accounts amo'),
        (3, 'spring green yellow purple cornsilk', 'Manufacturer#4', 'Brand#42', 'STANDARD POLISHED BRASS', 21, 'WRAP CASE', 903.00, 'egular deposits'),
        (4, 'cornflower chocolate smoke green pink', 'Manufacturer#3', 'Brand#34', 'SMALL PLATED BRASS', 14, 'MED DRUM', 904.00, 'p furiously r'),
        (5, 'forest brown coral puff cream', 'Manufacturer#3', 'Brand#32', 'STANDARD POLISHED TIN', 15, 'SM PKG', 905.00, 'wake carefully')
    """)

    # Insert LINEITEM data
    cursor.execute("""
        INSERT INTO LINEITEM VALUES
        (1, 1, 1, 1, 17, 21168.23, 0.04, 0.02, 'N', 'O', '1996-03-13', '1996-02-12', '1996-03-22', 'DELIVER IN PERSON', 'TRUCK', 'egular courts'),
        (1, 2, 2, 2, 36, 38306.88, 0.09, 0.06, 'N', 'O', '1996-04-12', '1996-02-28', '1996-04-20', 'TAKE BACK RETURN', 'MAIL', 'ly final'),
        (2, 3, 3, 1, 38, 44524.06, 0.00, 0.05, 'N', 'O', '1997-01-28', '1997-01-14', '1997-02-02', 'TAKE BACK RETURN', 'RAIL', 'ven requests'),
        (3, 4, 4, 1, 45, 54058.05, 0.06, 0.00, 'R', 'F', '1994-02-02', '1994-01-04', '1994-02-23', 'NONE', 'AIR', 'ongside'),
        (3, 5, 5, 2, 49, 46796.47, 0.10, 0.00, 'R', 'F', '1993-11-09', '1993-12-20', '1993-11-24', 'TAKE BACK RETURN', 'RAIL', 'unusual')
    """)

    cursor.close()

    return tpch_tables
