---
title: Chinook Database - Example Queries
created: 2026-01-23
updated: 2026-01-23
tags: [testing, uat, database, queries, examples]
doc_type: reference
---

# Chinook Database - Example Queries

The Chinook database represents a digital media store with realistic data. Here are interesting queries to test your Snowflake agent.

## Database Schema

### Tables Overview

| Table | Rows | Description |
|-------|------|-------------|
| **Artist** | 275 | Music artists |
| **Album** | 347 | Albums by artists |
| **Track** | 3,503 | Individual songs/tracks |
| **MediaType** | 5 | Audio/video formats (MP3, AAC, etc.) |
| **Genre** | 25 | Music genres (Rock, Jazz, Metal, etc.) |
| **Playlist** | 18 | User-created playlists |
| **PlaylistTrack** | 8,715 | Many-to-many: tracks in playlists |
| **Customer** | 59 | Store customers |
| **Employee** | 8 | Store employees |
| **Invoice** | 412 | Customer purchases |
| **InvoiceLine** | 2,240 | Line items on invoices |

### Entity Relationships

```
Artist ──< Album ──< Track ──< InvoiceLine >── Invoice >── Customer
                      │                                      │
                      │                                    Employee (SupportRep)
                      └──< PlaylistTrack >── Playlist
                      │
                    Genre, MediaType
```

## Example Queries for Testing

### Schema Exploration

```
"Show me all tables in the database"
"What's the schema of the Track table?"
"Describe the relationships between Artist, Album, and Track"
"How many rows are in each table?"
```

### Artist & Album Analysis

```
"Who are the top 10 artists by number of tracks?"
"Which artist has the most albums?"
"List all albums by Iron Maiden"
"Show me artists with only one album"
"What are the longest albums (most tracks)?"
```

### Track Analysis

```
"What are the 10 longest tracks by duration?"
"List the most expensive tracks"
"Show me all tracks in the Rock genre"
"What track appears in the most playlists?"
"Find tracks that are over 10 minutes long"
"What's the average track length by genre?"
```

### Genre Analysis

```
"What are all the available genres?"
"Which genre has the most tracks?"
"Show me the distribution of tracks across genres"
"What genres does Led Zeppelin appear in?"
"List genres with fewer than 10 tracks"
```

### Sales Analysis

```
"What are total sales by country?"
"Who are the top 10 customers by total spending?"
"What were the sales in 2013?"
"Show me monthly sales trends for 2012"
"Which country generates the most revenue?"
"What's the average invoice total?"
"List customers who have spent more than $40"
```

### Employee & Customer Analysis

```
"List all employees and their titles"
"Which support representative has the most customers?"
"Show me customers from Brazil"
"How many customers does each employee support?"
"What countries have the most customers?"
```

### Playlist Analysis

```
"What are all the playlists?"
"Which playlist has the most tracks?"
"Show me all tracks in the 'Music' playlist"
"What's the total duration of the 'Classical' playlist?"
"List playlists with Rock tracks"
```

### Complex Analytical Queries

```
"What's the revenue per customer by country?"
"Show me the top 5 genres by total sales"
"Which artists generate the most revenue?"
"What's the customer lifetime value for customers from USA?"
"Find customers who have purchased tracks from multiple genres"
"Calculate the average invoice total by country, sorted by average"
"Show me year-over-year sales growth"
"Which tracks have never been purchased?"
```

### Multi-Step Analysis (Good for Todo List Middleware)

```
"Analyze music sales: First show me top 5 countries by revenue,
then for each country show the top genre, then identify which
artists are most popular in those genres"

"Create a customer segmentation: group customers by spending level
(low/medium/high), show count in each segment, then identify the
most popular genres for each segment"

"Find the most profitable artist: calculate revenue by artist,
show their top albums, then show which countries buy their music most"
```

### Aggregation and Statistics

```
"What's the total revenue for all time?"
"How many tracks does each media type have?"
"Calculate the average album price (sum of track prices per album)"
"Show me the distribution of track lengths"
"What percentage of total sales comes from each country?"
```

### Time-Based Analysis

```
"Show me sales by month for 2012"
"Which quarter had the highest sales?"
"What's the sales trend over time?"
"Compare sales between 2010 and 2013"
"Show me invoice counts by day of week"
```

### Edge Cases and Data Quality

```
"Are there any tracks without a genre?"
"Find albums with no tracks"
"Show me tracks that appear in zero playlists"
"List customers with no purchases"
"Find any duplicate track names"
```

### Testing Guardrails

If you configure `allowed_schemas` or `allowed_tables`:

```
"Only show me data from the Customer and Invoice tables"
"I should only be able to see Artist, Album, and Track tables"
```

If you set `read_only=false` and enable human-in-the-loop:

```
"Delete all tracks by Nickelback"  (should trigger HITL approval)
"Update all prices to $0.99"       (should trigger HITL approval)
```

## Testing Middleware Features

### Human-in-the-Loop Testing

```
# Set read_only=false and enable_hitl=true
"Delete all playlists"
"Update customer emails"
"Insert a new artist"
```

### Call Limit Testing

```
# Set sql_query_run_limit=3
"Show me all tables, their schemas, sample data from each,
and statistics about each table"
(should hit limit after 3 queries)
```

### Summarization Testing

```
# Set summarization_trigger_tokens=1000
Ask many questions in sequence to build up conversation history:
1. "List all genres"
2. "For each genre, show top 3 artists"
3. "For those artists, show their albums"
4. "For those albums, show sales data"
... etc until summarization triggers
```

### Todo List Testing

```
"Analyze the music store business: identify top products,
best customers, seasonal trends, and provide recommendations
for inventory and marketing"
(should create a task plan with multiple steps)
```

### Fallback Testing

```
# Use primary model that might fail
# Should automatically fallback to cheaper model
"Analyze all sales data and create detailed report"
```

## Query Complexity Levels

### Level 1: Simple (Single table, no joins)
- "List all genres"
- "Show me the first 10 customers"
- "How many tracks are there?"

### Level 2: Moderate (Single join, basic aggregation)
- "Show albums by 'AC/DC'"
- "Count tracks per genre"
- "List customers from Canada"

### Level 3: Intermediate (Multiple joins, aggregation)
- "Top 5 artists by track count"
- "Total sales by country"
- "Customers with most purchases"

### Level 4: Advanced (Complex joins, subqueries, analytics)
- "Revenue per customer by country"
- "Year-over-year sales growth"
- "Customer segmentation by spending"

### Level 5: Expert (Multi-step analysis, complex logic)
- "Complete business analysis with customer segmentation, product analysis, and trend forecasting"
- "Identify underperforming products and suggest pricing changes"
- "Find correlation between genres, geographies, and purchasing patterns"

## Useful Context for the Agent

When chatting with the agent, you can provide business context:

```
"I'm a store manager looking to increase sales. Help me understand
which products and customers are most valuable."

"I need to plan inventory for next quarter. Show me what genres
and artists are trending."

"I want to create a customer loyalty program. Help me segment
customers and identify high-value targets."

"Help me analyze employee performance based on their customer
portfolio and sales."
```

## Expected Agent Behaviors

The agent should:
1. ✅ Use `sql_db_list_tables` before querying
2. ✅ Use `sql_db_schema` to understand table structure
3. ✅ Build queries incrementally for complex questions
4. ✅ Use proper JOINs based on foreign key relationships
5. ✅ Aggregate data appropriately (COUNT, SUM, AVG)
6. ✅ Handle NULL values gracefully
7. ✅ Format output clearly (currency, numbers, dates)
8. ✅ Explain query results in business terms

The agent should NOT:
1. ❌ Use `SHOW TABLES` (should use sql_db_list_tables tool)
2. ❌ Use `DESCRIBE TABLE` (should use sql_db_schema tool)
3. ❌ Make assumptions without checking schema
4. ❌ Return raw query results without interpretation

## Database Source

- **Source**: [Chinook Database on GitHub](https://github.com/lerocha/chinook-database)
- **License**: MIT License
- **Format**: SQLite
- **Size**: ~900 KB
- **Last Updated**: Regularly maintained

## Additional Resources

- Schema diagram: Available in the GitHub repository
- Data dictionary: Column descriptions in repository
- Sample queries: More examples in repository documentation
