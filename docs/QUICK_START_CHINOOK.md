# Quick Start with Chinook Database

The fastest way to get started with realistic test data.

## 1. Setup (2 minutes)

```bash
# Install dependencies
make install

# Download Chinook database
make setup-chinook
```

This downloads a ~900 KB SQLite database with:
- 11 tables (Artist, Album, Track, Customer, Invoice, etc.)
- 15,000+ rows of realistic music store data
- Proper foreign key relationships

## 2. Configure (30 seconds)

The setup script prints a connection URI. Copy it to your `.env` file:

```bash
# .env
SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:////absolute/path/to/test_chinook.db
ANTHROPIC_API_KEY=your_key_here  # or OPENAI_API_KEY
```

## 3. Start Server (10 seconds)

```bash
make dev
```

Opens LangGraph Studio at http://localhost:8123

## 4. Try It Out (1 minute)

1. Open Studio UI
2. Select a graph: `agent_enhanced` (recommended)
3. Create an Assistant
4. Start chatting!

### Example Queries to Try

**Simple:**
```
"Show me all tables"
"How many tracks are in the database?"
"List all music genres"
```

**Moderate:**
```
"Who are the top 5 artists by track count?"
"What are total sales by country?"
"Show me the most expensive tracks"
```

**Advanced:**
```
"Create a customer segmentation based on spending levels"
"Analyze sales trends by genre over time"
"Find the most profitable artist and their top markets"
```

**Test Middleware:**
```
"Show me everything about all tables, their schemas, sample data, and statistics"
(Tests call limits)

"Analyze the entire music business: customers, products, sales, trends, and recommendations"
(Tests todo list and multi-step planning)
```

## What Makes Chinook Good for Testing?

✅ **Realistic data**: Actual artist names, album titles, real sales data
✅ **Complex queries**: Multiple tables with proper relationships
✅ **Good size**: Large enough to be interesting, small enough to be fast
✅ **Well-documented**: Established sample database with known structure
✅ **Middleware testing**: Complex enough to hit call limits and trigger features

## Next Steps

### Explore the Data

See [chinook-queries.md](dev_docs/ai_docs/ai_gen/chinook-queries.md) for 100+ example queries organized by complexity.

### Test Middleware

Try different graph variants:
- `agent` - No middleware (baseline)
- `agent_minimal` - Basic limits + retry (development)
- `agent_enhanced` - Full middleware stack (production)

Configure middleware settings in the Studio UI to test:
- Human-in-the-loop approval
- Call limits (model and tool)
- Retry logic
- Summarization
- Todo list planning
- Model fallback

### Customize Configuration

Adjust middleware settings:
```bash
# In Studio UI "Assistant Configuration" panel:
- model_call_thread_limit: 20 (increase from 10)
- sql_query_run_limit: 8 (increase from 5)
- enable_hitl: false (disable human approval)
- enable_summarization: true (test long conversations)
```

### Compare Databases

See [DATABASE_OPTIONS.md](DATABASE_OPTIONS.md) to compare Chinook vs stub data.

## Troubleshooting

### "Download failed"
- Check internet connection
- Try again: `make setup-chinook`
- Manual download: Visit https://github.com/lerocha/chinook-database

### "Connection error"
- Use **absolute path** in URI: `sqlite:////full/path/to/test_chinook.db`
- Check file exists: `ls -lh test_chinook.db`
- Verify permissions: `chmod 644 test_chinook.db`

### "Agent not responding"
- Check API key is set in `.env`
- Verify model is available
- Check logs for errors: `SNOWFLAKE_AGENT_ENABLE_DEBUG=true make dev`

### "Blocking I/O error"
- Already handled! Makefile uses `--allow-blocking` flag
- This is normal for SQLite file operations

## That's It!

You now have:
- ✅ Realistic test database
- ✅ Working agent
- ✅ Studio UI running
- ✅ 100+ example queries to try

Start chatting with your agent and explore the database! 🎵
