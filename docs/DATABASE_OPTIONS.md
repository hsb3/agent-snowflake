# Test Database Options

This document compares the two SQLite database options for local testing.

## Quick Comparison

| Feature | Chinook (Recommended) | TPC-H Stub Data |
|---------|----------------------|-----------------|
| **Setup Command** | `make setup-chinook` | `make setup-test-db` |
| **Database File** | `test_chinook.db` | `test_snowflake.db` |
| **File Size** | ~900 KB | ~20 KB |
| **Tables** | 11 tables | 3 tables |
| **Total Rows** | ~15,000 rows | 13 rows |
| **Relationships** | ✅ Full FK relationships | ⚠️ Minimal |
| **Realistic Data** | ✅ Yes | ❌ Stub data only |
| **Query Complexity** | ✅ Simple to expert level | ⚠️ Basic only |
| **Use Case** | Testing, demos, development | Quick unit tests |

## Chinook Database (Recommended)

### Overview
- **Source**: [GitHub - lerocha/chinook-database](https://github.com/lerocha/chinook-database)
- **Domain**: Digital media store (like iTunes)
- **License**: MIT

### Schema

```
Artist (275 rows)
  └─ Album (347 rows)
      └─ Track (3,503 rows)
          ├─ Genre (25 genres)
          ├─ MediaType (5 types)
          └─ InvoiceLine (2,240 rows)
              └─ Invoice (412 rows)
                  └─ Customer (59 rows)
                      └─ Employee (8 employees)

Playlist (18 playlists)
  └─ PlaylistTrack (8,715 relationships)
      └─ Track
```

### Key Features
- **Foreign keys**: Proper relationships between all tables
- **Indexes**: Performance-optimized for queries
- **Data types**: Variety of INTEGER, TEXT, NUMERIC, DATETIME
- **Constraints**: NOT NULL, CHECK constraints
- **Real data**: Actual artist names, albums, tracks from music industry

### Example Queries

**Simple:**
```sql
SELECT * FROM Genre;
SELECT Name FROM Artist WHERE ArtistId = 1;
SELECT COUNT(*) FROM Track;
```

**Moderate:**
```sql
-- Albums by AC/DC
SELECT Album.Title
FROM Album
JOIN Artist ON Album.ArtistId = Artist.ArtistId
WHERE Artist.Name = 'AC/DC';

-- Track count by genre
SELECT Genre.Name, COUNT(Track.TrackId) as TrackCount
FROM Genre
LEFT JOIN Track ON Genre.GenreId = Track.GenreId
GROUP BY Genre.GenreId;
```

**Advanced:**
```sql
-- Top 5 customers by spending
SELECT
    Customer.FirstName || ' ' || Customer.LastName as CustomerName,
    SUM(Invoice.Total) as TotalSpent
FROM Customer
JOIN Invoice ON Customer.CustomerId = Invoice.CustomerId
GROUP BY Customer.CustomerId
ORDER BY TotalSpent DESC
LIMIT 5;

-- Revenue per genre
SELECT
    Genre.Name,
    COUNT(InvoiceLine.InvoiceLineId) as ItemsSold,
    SUM(InvoiceLine.UnitPrice * InvoiceLine.Quantity) as Revenue
FROM Genre
JOIN Track ON Genre.GenreId = Track.GenreId
JOIN InvoiceLine ON Track.TrackId = InvoiceLine.TrackId
GROUP BY Genre.GenreId
ORDER BY Revenue DESC;
```

### Testing Capabilities

✅ **Schema exploration**: Many tables to discover
✅ **Joins**: Complex multi-table joins
✅ **Aggregations**: COUNT, SUM, AVG across real data
✅ **Subqueries**: Nested queries for analysis
✅ **Analytics**: Sales trends, customer segmentation
✅ **Data quality**: Missing values, duplicates
✅ **Middleware testing**: Complex enough to hit call limits
✅ **Performance**: Large enough to test optimization

### Setup

```bash
# Download and setup
make setup-chinook

# This will:
# 1. Download from GitHub
# 2. Save as test_chinook.db
# 3. Show schema and sample data
# 4. Print connection string

# Then update .env:
SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///absolute/path/to/test_chinook.db

# Start server
make dev
```

### Example Agent Interactions

```
User: "Show me all tables"
Agent: Lists 11 tables with descriptions

User: "Who are the top 5 artists by track count?"
Agent: Uses joins to aggregate and rank artists

User: "What are total sales by country?"
Agent: Joins Invoice → Customer, aggregates by Country

User: "Create a customer segmentation analysis"
Agent: Multi-step analysis using todo list middleware
```

## TPC-H Stub Database

### Overview
- **Source**: Custom script (`scripts/setup_fakesnow_db.py`)
- **Domain**: Business data (TPC-H inspired)
- **Purpose**: Minimal testing, unit tests

### Schema

```
REGION (5 rows)
  └─ No foreign keys

CUSTOMER (5 rows)
  └─ No foreign keys

ORDERS (3 rows)
  └─ No foreign keys
```

### Key Features
- **Simple**: Only 3 tables
- **Minimal**: Handful of rows each
- **Lightweight**: Perfect for quick tests
- **Custom**: Can modify script to add more data

### Example Queries

**Simple:**
```sql
SELECT * FROM REGION;
SELECT COUNT(*) FROM CUSTOMER;
SELECT * FROM ORDERS WHERE ORDERKEY = 1;
```

**Limited:**
```sql
-- No meaningful joins (no FKs defined)
-- No complex analytics (not enough data)
-- Basic aggregations only
```

### Testing Capabilities

⚠️ **Schema exploration**: Only 3 tables
⚠️ **Joins**: No foreign keys defined
⚠️ **Aggregations**: Limited by row count
⚠️ **Subqueries**: Not meaningful with stub data
⚠️ **Analytics**: Not enough data for trends
❌ **Data quality**: Too clean (no realistic issues)
⚠️ **Middleware testing**: May not hit call limits
✅ **Performance**: Fast for unit tests

### Setup

```bash
# Create minimal database
make setup-test-db

# This will:
# 1. Create empty SQLite database
# 2. Run SQL script to create tables and insert data
# 3. Print connection string

# Then update .env:
SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///absolute/path/to/test_snowflake.db

# Start server
make dev
```

### Example Agent Interactions

```
User: "Show me all tables"
Agent: Lists REGION, CUSTOMER, ORDERS

User: "What regions are available?"
Agent: Lists 5 regions

User: "Analyze customer data"
Agent: Limited analysis (only 5 customers)
```

## When to Use Each

### Use Chinook When:
- ✅ Testing agent capabilities with realistic data
- ✅ Demonstrating to stakeholders
- ✅ Developing complex query logic
- ✅ Testing middleware (call limits, summarization)
- ✅ Training yourself on SQL agent behavior
- ✅ Creating demos or videos
- ✅ Testing multi-step analytical workflows

### Use TPC-H Stub When:
- ✅ Running unit tests (fast, minimal)
- ✅ Testing basic functionality
- ✅ CI/CD pipelines (quick setup)
- ✅ Learning basic agent setup
- ✅ Debugging connection issues

## Migration Between Databases

You can easily switch between databases:

```bash
# Try Chinook
make setup-chinook
export SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///$(pwd)/test_chinook.db
make dev

# Later, switch to stub data
make setup-test-db
export SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///$(pwd)/test_snowflake.db
make dev
```

Or use both simultaneously by changing the URI in LangGraph Studio's assistant configuration.

## Other Database Options

If you want even more data, consider:

### Northwind Database
- Classic Microsoft sample database
- Orders, products, customers, employees
- Available in SQLite format
- Similar complexity to Chinook

### Stack Overflow Data Dumps
- Real Stack Overflow data
- Very large (GBs)
- Good for testing performance limits
- Requires download and ETL

### Custom Domain Data
- Create your own with realistic domain data
- Use `scripts/setup_fakesnow_db.py` as template
- Tailor to your specific use case

## Example Query Files

For Chinook database, see:
- **[CHINOOK_QUERIES.md](CHINOOK_QUERIES.md)** - 100+ example queries organized by complexity

For TPC-H stub, queries are limited to basic operations on the 3 tables.

## Recommendation

**For most users**: Use `make setup-chinook`

It provides:
- Realistic testing scenarios
- Interesting queries to explore
- Good middleware testing
- Demonstration-ready examples
- Enough complexity to find issues
- Still fast enough for development

Only use the stub database when you specifically need minimal, fast tests (like in CI/CD).
