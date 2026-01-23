# agent-snowflake

A LangGraph agent for intelligent Snowflake database interactions.

## Features

- Multi-model support (Anthropic Claude, OpenAI GPT, Google Gemini)
- Runtime configuration via LangGraph Studio
- Schema exploration and SQL query generation
- Built-in guardrails for safe database operations
- Comprehensive test suite with fakesnow

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

```bash
# Create test database with sample TPC-H data
make setup-test-db

# This creates test_snowflake.db (SQLite) with sample tables:
# - REGION (5 rows)
# - CUSTOMER (5 rows)
# - ORDERS (3 rows)

# Update .env with the connection URI shown by setup script
# Then start the dev server:
make dev
```

**⚠️ SQLite Limitations:** SQLite is used for quick local testing but doesn't support Snowflake-specific features like VARIANT types, FLATTEN(), QUALIFY, etc. For production testing with Snowflake-specific SQL, use an actual Snowflake account. See [docs/SQL_COMPATIBILITY.md](docs/SQL_COMPATIBILITY.md) for details.

### Running Tests

```bash
# Run all tests (no Snowflake required)
make test

# Run fast tests only
make test-fast
```

See [docs/README_TESTING.md](docs/README_TESTING.md) for detailed testing documentation.

## Project Structure

```
agent-snowflake/
├── src/
│   └── agent_snowflake/        # Main package
│       ├── config.py           # Settings and defaults
│       ├── context.py          # Runtime context schema
│       ├── graph.py            # Agent graph definition
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
make setup-test-db  # Create test database with sample data
make dev            # Start LangGraph dev server
make test           # Run all tests
make test-fast      # Run tests (skip slow tests)
make format         # Format code with ruff
make lint           # Lint code with ruff
make type-check     # Type check with ty
make clean          # Remove caches and generated files
```

### LangGraph Studio Configuration

After running `make setup-test-db` and `make dev`:

1. Open Studio UI at http://localhost:8123
2. Create a new Assistant
3. Configure with the connection URI:
   ```
   snowflake_uri: sqlite:////absolute/path/to/test_snowflake.db
   ```
4. Try example queries:
   - "Show me all tables"
   - "What regions are in the database?"
   - "Count the number of customers"
   - "Show me all orders"

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

- [README_TESTING.md](README_TESTING.md) - Testing guide
- [TESTING_FAKESNOW.md](TESTING_FAKESNOW.md) - fakesnow documentation
- [LOCAL_TESTING_SUMMARY.md](LOCAL_TESTING_SUMMARY.md) - Testing implementation details

## License

[Add your license here]
