# agent-snowflake

A LangGraph agent for intelligent Snowflake database interactions.

## Features

- Multi-model support (Anthropic Claude, OpenAI GPT, Google Gemini)
- Runtime configuration via LangGraph Studio
- Schema exploration and SQL query generation
- Built-in guardrails for safe database operations
- Comprehensive test suite with fakesnow
- **Three graph variants with middleware:**
  - `agent` - Basic agent (no middleware)
  - `agent_minimal` - Development mode (limits + retry)
  - `agent_enhanced` - Production mode (7 middleware components)

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd agent-snowflake

# Install dependencies
make install
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Required settings:
- `ANTHROPIC_API_KEY` (or OpenAI/Google API key)
- Snowflake connection details (or use fakesnow for local testing)

### Running the Agent

```bash
# Start LangGraph dev server with Studio UI
make dev

# Or use programmatically
uv run python -c "from agent_snowflake import graph; result = graph.invoke({'messages': [...]})"
```

### Local Testing with Sample Data

**Option 1: Chinook Database (Recommended)**

```bash
# Download Chinook database - realistic digital media store data
make setup-chinook

# This downloads test_chinook.db (SQLite) with 11 tables:
# - Artist, Album, Track (3,500+ tracks)
# - Customer, Invoice, InvoiceLine (sales data)
# - Employee, Playlist, Genre, MediaType
# Total: ~900 KB database with realistic relationships

# Update .env with the connection URI shown by setup script
# Then start the dev server:
make dev
```

**Option 2: Minimal Stub Data**

```bash
# Create minimal test database with TPC-H stub data
make setup-test-db

# This creates test_snowflake.db (SQLite) with 3 tables:
# - REGION (5 rows)
# - CUSTOMER (5 rows)
# - ORDERS (3 rows)

# Update .env and start dev server:
make dev
```

**Additional Resources:**
- 📊 [DATABASE_OPTIONS.md](docs/DATABASE_OPTIONS.md) - Compare Chinook vs stub data in detail
- 🎵 [CHINOOK_QUERIES.md](docs/CHINOOK_QUERIES.md) - 100+ example queries organized by complexity level

**⚠️ SQLite Limitations:**
- SQLite is used for quick local testing but doesn't support Snowflake-specific features like VARIANT types, FLATTEN(), QUALIFY, etc.
- SQLite file operations are **blocking**, so the dev server requires `--allow-blocking` flag (already configured in Makefile)
- **Production Snowflake connections** are network-based and don't have blocking issues - they don't need this flag
- For production testing with Snowflake-specific SQL, use an actual Snowflake account

See [docs/SQL_COMPATIBILITY.md](docs/SQL_COMPATIBILITY.md) for details on SQL syntax differences.

### Running Tests

```bash
# Run all tests (no Snowflake required)
make test

# Run fast tests only
make test-fast
```

See [docs/README_TESTING.md](docs/README_TESTING.md) for detailed testing documentation.

## Middleware & Production Safety

The project provides three graph variants with different middleware configurations:

### Graph Variants

| Graph | Middleware | Use Case |
|-------|------------|----------|
| `agent` | None | Learning, debugging core functionality |
| `agent_minimal` | 2 components | Fast development iteration |
| `agent_enhanced` | 7 components | Production deployment |

### Enhanced Graph Features

The `agent_enhanced` variant includes:

1. **Human-in-the-Loop** - Approve dangerous SQL operations
2. **Model Call Limits** - Prevent runaway costs (10 calls/thread)
3. **Tool Call Limits** - Control expensive queries (global + per-tool)
4. **Model Retry** - Handle network failures (3 retries with backoff)
5. **Summarization** - Compress long conversations (4000 token trigger)
6. **Todo List** - Task planning for complex analysis
7. **Model Fallback** - Switch to backup models on failure

### Using Different Graphs

```bash
# Start server (all graphs available)
make dev

# In LangGraph Studio UI:
# 1. Select graph from dropdown: agent, agent_minimal, or agent_enhanced
# 2. Create assistant with your configuration
# 3. Start chatting
```

**Quick Start:**
- 📘 [Middleware Quick Start](docs/MIDDLEWARE_QUICKSTART.md) - 5-minute overview
- 📖 [Full Middleware Guide](docs/MIDDLEWARE.md) - Detailed configuration and examples
- ⚙️ [Enhanced Context Schema](docs/ENHANCED_CONTEXT.md) - Complete configuration reference

## Project Structure

```
agent-snowflake/
├── src/
│   └── agent_snowflake/        # Main package
│       ├── config.py           # Settings and defaults
│       ├── context.py          # Runtime context schema
│       ├── graph.py            # Basic agent (no middleware)
│       ├── graph2.py           # Enhanced agents with middleware
│       ├── models.py           # Type definitions
│       ├── state.py            # Graph state schema
│       ├── utils.py            # Helper functions
│       ├── prompts/            # System prompts
│       └── tools/              # Agent tools
│           └── sql.py          # SQL toolkit integration
├── scripts/                    # Setup and utility scripts
│   ├── setup_fakesnow_db.py   # Create test database
│   └── test_local_db.py       # Verify database connection
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest fixtures
│   ├── fixtures/              # Test fixtures
│   │   └── init_data.sql      # Sample TPC-H data
│   ├── test_tools.py          # Tool tests
│   ├── test_graph_with_tools.py # Integration tests
│   └── test_snowflake_*.py    # Connection tests
├── docs/                       # Documentation
│   ├── README_TESTING.md      # Testing guide
│   ├── MIDDLEWARE.md          # Full middleware guide
│   ├── MIDDLEWARE_QUICKSTART.md # Quick reference
│   ├── SQL_COMPATIBILITY.md   # SQLite vs Snowflake SQL
│   └── future-template/       # Template scripts
├── Makefile                   # Development commands
├── langgraph.json             # LangGraph configuration
├── pyproject.toml             # Project metadata
└── .env.example               # Environment template
```

## Development

### Makefile Commands

The project includes a Makefile for common tasks:

```bash
make help           # Show all available commands
make install        # Install dependencies
make setup-chinook  # Download Chinook database (recommended)
make setup-test-db  # Create minimal stub database
make dev            # Start LangGraph dev server
make test           # Run all tests
make test-fast      # Run tests (skip slow tests)
make format         # Format code with ruff
make lint           # Lint code with ruff
make type-check     # Type check with ty
make clean          # Remove caches and generated files
```

### LangGraph Studio Configuration

After running `make setup-chinook` (or `make setup-test-db`) and `make dev`:

1. Open Studio UI at http://localhost:8123
2. Create a new Assistant
3. Configure with the connection URI:
   ```
   snowflake_uri: sqlite:////absolute/path/to/test_chinook.db
   ```
4. Try example queries:
   - "Show me all tables"
   - "Who are the top 10 artists by track count?"
   - "What are total sales by country?"
   - "Show me customers who spent the most"
   - "What are the most popular genres?"

**See [CHINOOK_QUERIES.md](docs/CHINOOK_QUERIES.md) for 100+ example queries organized by complexity level.**

### Code Quality

```bash
make format      # Auto-format code
make lint        # Check code quality
make type-check  # Verify types
```

### Adding Tools

Add new tools in `src/agent_snowflake/tools/`:

```python
from langchain_core.tools import tool

@tool
def my_tool(query: str) -> str:
    """Tool description for the LLM."""
    return result
```

Register in `graph.py`:

```python
from .tools import my_tool

tools = [my_tool]
```

## Documentation

### Core Documentation
- [MIDDLEWARE_QUICKSTART.md](docs/MIDDLEWARE_QUICKSTART.md) - Quick reference for middleware (5 min read)
- [MIDDLEWARE.md](docs/MIDDLEWARE.md) - Complete middleware configuration guide
- [ENHANCED_CONTEXT.md](docs/ENHANCED_CONTEXT.md) - Complete configuration reference
- [SQL_COMPATIBILITY.md](docs/SQL_COMPATIBILITY.md) - SQLite vs Snowflake SQL differences

### Database & Testing
- [DATABASE_OPTIONS.md](docs/DATABASE_OPTIONS.md) - Compare Chinook vs stub database
- [CHINOOK_QUERIES.md](docs/CHINOOK_QUERIES.md) - 100+ example queries for testing
- [README_TESTING.md](docs/README_TESTING.md) - Testing guide
- [TESTING_FAKESNOW.md](docs/TESTING_FAKESNOW.md) - fakesnow documentation
- [LOCAL_TESTING_SUMMARY.md](docs/LOCAL_TESTING_SUMMARY.md) - Testing implementation details

## License

[Add your license here]
