# Template Commands - Running List

Commands and patterns to incorporate into template scripts as we build out the agent.

## Project Initialization
- `uv init --no-readme --name <project-name>`
- `uv python install <version>`
- `uv add langchain langgraph langchain-anthropic langchain-openai langchain-google-genai python-dotenv pydantic-settings`
- `uv add --dev langgraph-cli`

## Directory Structure
- Create `src/<module-name>/` with subdirs: `tools/`, `prompts/`
- Create module files: `config.py`, `context.py`, `state.py`, `models.py`, `utils.py`, `graph.py`
- Create prompts: `prompts/core.py`, `prompts/special.py`, `prompts/builder.py`, `prompts/__init__.py`

## Configuration Files
- `.gitignore` - Python, .env, .venv, etc.
- `.env.example` - Template for environment variables
- `langgraph.json` - LangGraph configuration
- `.python-version` - Pin Python version

## Development Commands
- `uv run <script>` - Run scripts in virtual environment
- `langgraph dev` - Start LangGraph dev server with Studio UI
- `langgraph test` - Run tests
- `uv run python -m <module>` - Run modules
- Install with dev server: `uv add --dev 'langgraph-cli[inmem]'`

## Common Patterns to Template
- **config.py**: dataclass Settings with from_env() method, export module-level constants
- **context.py**: dataclass ContextSchema with:
  - `Annotated[str, {"__template_metadata__": {"kind": "llm"}}]` for LLM selector in Studio
  - `field()` with metadata for descriptions and json_schema_extra
  - `from_env()` method for environment loading
  - `from_runnable_config()` method for LangGraph runtime integration
  - `to_dict()` and `__repr__()` helpers
- **state.py**: TypedDict for state schemas (mutable during run)
- **utils.py**: Helper functions including:
  - `init_model()` - Wrapper around `init_chat_model()` for special case handling
- **graph.py**:
  - Single `build_graph()` function (no separate create/build)
  - Use `from langchain.agents import create_agent`
  - Load context via `ContextSchema.from_runnable_config()`
  - Initialize model via `utils.init_model()`
  - Export with `graph = build_graph()` for langgraph.json
  - Document all create_agent parameters (comment out unused ones)
- Prompt composition pattern (core + special + builder)
- Multi-model support (Anthropic/OpenAI/Google)
- Three-layer config: Runtime context → Environment → Defaults

## Database-Specific (as applicable)
- Database connector packages (e.g., `snowflake-connector-python`)
- Connection configuration in BaseSettings
- Guardrails configuration (allowed schemas/tables)

## Notes
- Use `total=False` on TypedDict for optional context fields
- Environment-specific validation (CORS warnings, etc.)
- Helper properties for parsing comma-separated env vars
