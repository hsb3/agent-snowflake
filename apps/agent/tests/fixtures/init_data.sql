-- Initialize Snowflake Emulator with Sample TPC-H Inspired Data
-- This creates a simplified version of TPC-H schema for testing

-- Create Database and Schema
CREATE DATABASE IF NOT EXISTS SAMPLE_DB;
USE DATABASE SAMPLE_DB;
CREATE SCHEMA IF NOT EXISTS TPCH_SAMPLE;
USE SCHEMA TPCH_SAMPLE;

-- Create Tables

-- REGION table
CREATE TABLE IF NOT EXISTS REGION (
    R_REGIONKEY INTEGER PRIMARY KEY,
    R_NAME VARCHAR(25) NOT NULL,
    R_COMMENT VARCHAR(152)
);

-- NATION table
CREATE TABLE IF NOT EXISTS NATION (
    N_NATIONKEY INTEGER PRIMARY KEY,
    N_NAME VARCHAR(25) NOT NULL,
    N_REGIONKEY INTEGER NOT NULL,
    N_COMMENT VARCHAR(152),
    FOREIGN KEY (N_REGIONKEY) REFERENCES REGION(R_REGIONKEY)
);

-- CUSTOMER table
CREATE TABLE IF NOT EXISTS CUSTOMER (
    C_CUSTKEY INTEGER PRIMARY KEY,
    C_NAME VARCHAR(25) NOT NULL,
    C_ADDRESS VARCHAR(40),
    C_NATIONKEY INTEGER NOT NULL,
    C_PHONE VARCHAR(15),
    C_ACCTBAL DECIMAL(15,2),
    C_MKTSEGMENT VARCHAR(10),
    C_COMMENT VARCHAR(117),
    FOREIGN KEY (C_NATIONKEY) REFERENCES NATION(N_NATIONKEY)
);

-- ORDERS table
CREATE TABLE IF NOT EXISTS ORDERS (
    O_ORDERKEY INTEGER PRIMARY KEY,
    O_CUSTKEY INTEGER NOT NULL,
    O_ORDERSTATUS VARCHAR(1),
    O_TOTALPRICE DECIMAL(15,2),
    O_ORDERDATE DATE,
    O_ORDERPRIORITY VARCHAR(15),
    O_CLERK VARCHAR(15),
    O_SHIPPRIORITY INTEGER,
    O_COMMENT VARCHAR(79),
    FOREIGN KEY (O_CUSTKEY) REFERENCES CUSTOMER(C_CUSTKEY)
);

-- PART table
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
);

-- LINEITEM table
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
    L_COMMENT VARCHAR(44),
    PRIMARY KEY (L_ORDERKEY, L_LINENUMBER),
    FOREIGN KEY (L_ORDERKEY) REFERENCES ORDERS(O_ORDERKEY),
    FOREIGN KEY (L_PARTKEY) REFERENCES PART(P_PARTKEY)
);

-- Insert Sample Data

-- REGION data
INSERT INTO REGION VALUES
(0, 'AFRICA', 'lar deposits. blithely final packages cajole'),
(1, 'AMERICA', 'hs use ironic, even requests'),
(2, 'ASIA', 'ges. thinly even pinto beans ca'),
(3, 'EUROPE', 'ly final courts cajole furiously'),
(4, 'MIDDLE EAST', 'uickly special accounts cajole');

-- NATION data (subset)
INSERT INTO NATION VALUES
(0, 'ALGERIA', 0, ' haggle. carefully final deposits detect slyly agai'),
(1, 'ARGENTINA', 1, 'al foxes promise slyly according to the regular accounts'),
(2, 'BRAZIL', 1, 'y alongside of the pending deposits'),
(3, 'CANADA', 1, 'eas hang ironic, silent packages'),
(4, 'EGYPT', 4, 'y above the carefully unusual theodolites'),
(5, 'ETHIOPIA', 0, 'ven packages wake quickly'),
(6, 'FRANCE', 3, 'refully final requests'),
(7, 'GERMANY', 3, 'l platelets. regular accounts x-ray'),
(8, 'INDIA', 2, 'ss excuses cajole slyly across the packages'),
(9, 'INDONESIA', 2, ' slyly express asymptotes'),
(10, 'IRAN', 4, 'efully alongside of the slyly final dependencies'),
(11, 'IRAQ', 4, 'nic deposits boost atop the quickly final requests'),
(12, 'JAPAN', 2, 'ously. final, express gifts cajole a'),
(13, 'JORDAN', 4, 'ic deposits are blithely about the carefully regular pa'),
(14, 'KENYA', 0, ' pending excuses haggle furiously deposits'),
(15, 'MOROCCO', 0, 'rns. blithely bold courts among the closely regular packages'),
(16, 'MOZAMBIQUE', 0, 's. ironic, unusual asymptotes wake blithely r'),
(17, 'PERU', 1, 'platelets. blithely pending dependencies use fluffily'),
(18, 'CHINA', 2, 'c dependencies. furiously express notornis sleep slyly regular'),
(19, 'ROMANIA', 3, 'ular asymptotes are about the furious multipliers'),
(20, 'SAUDI ARABIA', 4, 'ts. silent requests haggle. closely express packages sleep'),
(21, 'VIETNAM', 2, 'hely enticingly express accounts'),
(22, 'RUSSIA', 3, ' requests against the platelets use never according to the'),
(23, 'UNITED KINGDOM', 3, 'eans boost carefully special requests'),
(24, 'UNITED STATES', 1, 'y final packages. slow foxes cajole quickly');

-- CUSTOMER data (sample)
INSERT INTO CUSTOMER VALUES
(1, 'Customer#000000001', '1234 Main St', 15, '25-989-741-2988', 711.56, 'BUILDING', 'to the even, regular platelets'),
(2, 'Customer#000000002', '5678 Oak Ave', 13, '23-768-687-3665', 121.65, 'AUTOMOBILE', 'l accounts. blithely ironic theodolites'),
(3, 'Customer#000000003', '9012 Pine Rd', 1, '11-719-748-3364', 7498.12, 'AUTOMOBILE', 'deposits eat slyly ironic, even instructions'),
(4, 'Customer#000000004', '3456 Elm Blvd', 4, '14-128-190-5944', 2866.83, 'MACHINERY', ' requests. final, regular ideas sleep final accou'),
(5, 'Customer#000000005', '7890 Maple Dr', 3, '13-750-942-6364', 794.47, 'HOUSEHOLD', 'n accounts will have to unwind'),
(6, 'Customer#000000006', '2345 Cedar Ln', 20, '30-114-968-4951', 7638.57, 'AUTOMOBILE', 'tions. even deposits boost according to the slyly bold packages'),
(7, 'Customer#000000007', '6789 Birch Way', 18, '29-316-665-2897', 9561.95, 'AUTOMOBILE', 'ainst the ironic, express theodolites'),
(8, 'Customer#000000008', '1357 Walnut St', 17, '28-719-320-3948', 6819.74, 'BUILDING', 'among the slyly regular theodolites kindle blithely courts'),
(9, 'Customer#000000009', '2468 Ash Ct', 8, '18-338-906-3675', 8324.07, 'FURNITURE', 'r theodolites according to the requests wake thinly excuses'),
(10, 'Customer#000000010', '3579 Spruce Pl', 5, '15-741-346-9870', 2753.54, 'HOUSEHOLD', 'es regular deposits haggle. fur');

-- ORDERS data (sample)
INSERT INTO ORDERS VALUES
(1, 1, 'O', 173665.47, '1996-01-02', '5-LOW', 'Clerk#000000951', 0, 'nstructions sleep furiously among'),
(2, 2, 'O', 46929.18, '1996-12-01', '1-URGENT', 'Clerk#000000880', 0, ' foxes. pending accounts at the pending, silent asymptot'),
(3, 3, 'F', 193846.25, '1993-10-14', '5-LOW', 'Clerk#000000955', 0, 'sly final accounts boost. carefully regular ideas cajole carefully'),
(4, 4, 'O', 32151.78, '1995-10-11', '5-LOW', 'Clerk#000000124', 0, 'sits. slyly regular warthogs cajole'),
(5, 5, 'F', 144659.20, '1994-07-30', '5-LOW', 'Clerk#000000925', 0, 'quickly. bold deposits sleep slyly'),
(6, 6, 'F', 58749.59, '1992-02-21', '4-NOT SPECIFIED', 'Clerk#000000058', 0, 'ggle. special, final requests are against the furiously'),
(7, 7, 'O', 252004.18, '1996-01-10', '2-HIGH', 'Clerk#000000470', 0, 'ly special requests'),
(8, 8, 'F', 301629.35, '1995-07-16', '2-HIGH', 'Clerk#000000280', 0, 'r theodolites according to the requests wake thinly excuses'),
(9, 9, 'F', 220111.60, '1998-03-18', '3-MEDIUM', 'Clerk#000000659', 0, 'carefully alongside of the bold requests'),
(10, 10, 'O', 181876.88, '1998-10-21', '5-LOW', 'Clerk#000000226', 0, 'xpress packages wake according to the ironic foxes');

-- PART data (sample)
INSERT INTO PART VALUES
(1, 'goldenrod lavender spring chocolate lace', 'Manufacturer#1', 'Brand#13', 'PROMO BURNISHED COPPER', 7, 'JUMBO PKG', 901.00, 'ly. slyly ironi'),
(2, 'blush thistle blue yellow saddle', 'Manufacturer#1', 'Brand#13', 'LARGE BRUSHED BRASS', 1, 'LG CASE', 902.00, 'lar accounts amo'),
(3, 'spring green yellow purple cornsilk', 'Manufacturer#4', 'Brand#42', 'STANDARD POLISHED BRASS', 21, 'WRAP CASE', 903.00, 'egular deposits hag'),
(4, 'cornflower chocolate smoke green pink', 'Manufacturer#3', 'Brand#34', 'SMALL PLATED BRASS', 14, 'MED DRUM', 904.00, 'p furiously r'),
(5, 'forest brown coral puff cream', 'Manufacturer#3', 'Brand#32', 'STANDARD POLISHED TIN', 15, 'SM PKG', 905.00, 'wake carefully'),
(6, 'bisque cornflower lawn forest magenta', 'Manufacturer#2', 'Brand#24', 'PROMO PLATED STEEL', 4, 'MED BAG', 906.00, 'slyly regular pinto be'),
(7, 'moccasin green navajo cream chocolate', 'Manufacturer#1', 'Brand#11', 'SMALL PLATED COPPER', 45, 'SM BAG', 907.00, 'ly alongside of the pending deposits'),
(8, 'misty lemon thistle snow papaya', 'Manufacturer#4', 'Brand#44', 'PROMO BURNISHED TIN', 41, 'LG DRUM', 908.00, 'eplets. blithely pend'),
(9, 'chiffon puff smoke floral orange', 'Manufacturer#4', 'Brand#43', 'SMALL BURNISHED STEEL', 12, 'JUMBO CASE', 909.00, 'ts wake furiously'),
(10, 'linen pink saddle puff powder', 'Manufacturer#5', 'Brand#54', 'LARGE BURNISHED STEEL', 44, 'LG CASE', 910.00, 'ithely final deposits ac');

-- LINEITEM data (sample)
INSERT INTO LINEITEM VALUES
(1, 1, 1, 1, 17, 21168.23, 0.04, 0.02, 'N', 'O', '1996-03-13', '1996-02-12', '1996-03-22', 'DELIVER IN PERSON', 'TRUCK', 'egular courts above the'),
(1, 2, 2, 2, 36, 38306.88, 0.09, 0.06, 'N', 'O', '1996-04-12', '1996-02-28', '1996-04-20', 'TAKE BACK RETURN', 'MAIL', 'ly final dependencies: slyly bold'),
(2, 3, 3, 1, 38, 44524.06, 0.00, 0.05, 'N', 'O', '1997-01-28', '1997-01-14', '1997-02-02', 'TAKE BACK RETURN', 'RAIL', 'ven requests. deposits breach a'),
(3, 4, 4, 1, 45, 54058.05, 0.06, 0.00, 'R', 'F', '1994-02-02', '1994-01-04', '1994-02-23', 'NONE', 'AIR', 'ongside of the furiously brave acco'),
(3, 5, 5, 2, 49, 46796.47, 0.10, 0.00, 'R', 'F', '1993-11-09', '1993-12-20', '1993-11-24', 'TAKE BACK RETURN', 'RAIL', 'unusual accounts. even accounts cajole'),
(4, 6, 6, 1, 30, 30180.60, 0.03, 0.08, 'N', 'O', '1996-01-10', '1995-12-14', '1996-01-18', 'DELIVER IN PERSON', 'REG AIR', '. slyly special requests haggle'),
(5, 7, 7, 1, 15, 17159.55, 0.02, 0.04, 'R', 'F', '1994-10-31', '1994-08-31', '1994-11-20', 'NONE', 'AIR', 'zzle. carefully enticing deposits nag'),
(5, 8, 8, 2, 26, 28739.35, 0.07, 0.08, 'R', 'F', '1994-10-16', '1994-09-25', '1994-10-19', 'NONE', 'FOB', 'hely enticingly bold accounts'),
(5, 9, 9, 3, 50, 48819.00, 0.08, 0.03, 'A', 'F', '1994-10-29', '1994-09-27', '1994-11-04', 'NONE', 'MAIL', 'y. furiously ironic ideas'),
(6, 10, 10, 1, 37, 37925.90, 0.08, 0.03, 'A', 'F', '1992-04-27', '1992-05-15', '1992-05-02', 'TAKE BACK RETURN', 'TRUCK', 'p furiously special foxes');

-- Create some useful views

-- Customer order summary
CREATE VIEW IF NOT EXISTS CUSTOMER_ORDER_SUMMARY AS
SELECT
    c.C_CUSTKEY,
    c.C_NAME,
    c.C_NATIONKEY,
    n.N_NAME AS NATION,
    r.R_NAME AS REGION,
    COUNT(o.O_ORDERKEY) AS ORDER_COUNT,
    SUM(o.O_TOTALPRICE) AS TOTAL_SPENT
FROM CUSTOMER c
JOIN NATION n ON c.C_NATIONKEY = n.N_NATIONKEY
JOIN REGION r ON n.N_REGIONKEY = r.R_REGIONKEY
LEFT JOIN ORDERS o ON c.C_CUSTKEY = o.O_CUSTKEY
GROUP BY c.C_CUSTKEY, c.C_NAME, c.C_NATIONKEY, n.N_NAME, r.R_NAME;

-- Order line items detail
CREATE VIEW IF NOT EXISTS ORDER_DETAILS AS
SELECT
    o.O_ORDERKEY,
    o.O_ORDERDATE,
    c.C_NAME AS CUSTOMER_NAME,
    l.L_LINENUMBER,
    p.P_NAME AS PART_NAME,
    l.L_QUANTITY,
    l.L_EXTENDEDPRICE,
    l.L_DISCOUNT,
    l.L_TAX
FROM ORDERS o
JOIN CUSTOMER c ON o.O_CUSTKEY = c.C_CUSTKEY
JOIN LINEITEM l ON o.O_ORDERKEY = l.L_ORDERKEY
JOIN PART p ON l.L_PARTKEY = p.P_PARTKEY;

-- Summary statistics
CREATE VIEW IF NOT EXISTS DATABASE_SUMMARY AS
SELECT
    'REGION' AS TABLE_NAME,
    COUNT(*) AS ROW_COUNT
FROM REGION
UNION ALL
SELECT 'NATION', COUNT(*) FROM NATION
UNION ALL
SELECT 'CUSTOMER', COUNT(*) FROM CUSTOMER
UNION ALL
SELECT 'ORDERS', COUNT(*) FROM ORDERS
UNION ALL
SELECT 'PART', COUNT(*) FROM PART
UNION ALL
SELECT 'LINEITEM', COUNT(*) FROM LINEITEM;
