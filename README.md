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
uv sync
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
# Start LangGraph dev server
langgraph dev

# Or use programmatically
uv run python -c "from agent_snowflake import build_graph; graph = build_graph()"
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with fakesnow (no Snowflake required)
pytest tests/test_snowflake_fakesnow.py -v
```

See [README_TESTING.md](README_TESTING.md) for detailed testing documentation.

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
├── tests/                      # Test suite
│   ├── conftest.py            # Pytest fixtures
│   └── fixtures/              # Sample data
├── langgraph.json             # LangGraph configuration
├── pyproject.toml             # Project metadata
└── .env.example               # Environment template
```

## Development

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Lint
ruff check src/ tests/

# Type check
ty check src/
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
