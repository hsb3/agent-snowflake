# Examples

This directory contains example scripts demonstrating various features of the Snowflake agent.

## Available Examples

### enhanced_context_usage.py

Demonstrates how to use `EnhancedContextSchema` to configure middleware for the enhanced and minimal graph variants.

**What it shows:**
- Basic usage with default configuration
- Customizing middleware limits
- Selectively disabling middleware components
- Aggressive retry configuration
- Custom fallback model chains
- Using minimal graph variant
- Per-user role configuration
- Loading configuration from environment
- Summarization settings
- Production-ready configuration

**How to run:**

```bash
# Make sure you have a database configured
make setup-chinook  # or make setup-test-db

# Update .env with connection URI (printed by setup script)
# Then run the examples:
uv run python examples/enhanced_context_usage.py
```

**Prerequisites:**
- Working database connection (SQLite or Snowflake)
- `SNOWFLAKE_AGENT_SNOWFLAKE_URI` configured in `.env`
- API keys configured (e.g., `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`)

**Examples included:**

1. **Basic usage** - Default configuration
2. **Custom limits** - Adjust model/tool call limits
3. **Disable middleware** - Turn off specific components
4. **Aggressive retry** - Configure retry for flaky networks
5. **Custom fallback** - Specify fallback model chain
6. **Minimal graph** - Use development-friendly minimal middleware
7. **Per-user config** - Different settings for different roles
8. **Load from env** - Read configuration from environment variables
9. **Summarization** - Configure conversation compression
10. **Production config** - Full production-ready setup

## Running Examples

### With Chinook Database

```bash
# Setup
make setup-chinook
export SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///$(pwd)/test_chinook.db

# Run example
uv run python examples/enhanced_context_usage.py
```

### With Custom Configuration

You can override configuration via environment variables:

```bash
# Set custom middleware configuration
export SNOWFLAKE_AGENT_MODEL_CALL_THREAD_LIMIT=20
export SNOWFLAKE_AGENT_SQL_QUERY_RUN_LIMIT=10
export SNOWFLAKE_AGENT_ENABLE_SUMMARIZATION=false

# Run examples with custom config
uv run python examples/enhanced_context_usage.py
```

### Running Individual Examples

If you want to run just one example, modify the script:

```python
if __name__ == "__main__":
    # Comment out examples you don't want to run
    example_1_basic_usage()
    # example_2_custom_limits()
    # example_3_disable_middleware()
    # ...
```

## Tips

- **Start simple**: Run example 1 first to verify basic functionality
- **Check logs**: Set `SNOWFLAKE_AGENT_ENABLE_DEBUG=true` to see detailed logs
- **Experiment**: Modify the examples to test different configurations
- **Error handling**: If examples fail, check database connection and API keys

## Additional Resources

- [ENHANCED_CONTEXT.md](../docs/ENHANCED_CONTEXT.md) - Complete configuration reference
- [MIDDLEWARE.md](../docs/MIDDLEWARE.md) - Middleware guide
- [CHINOOK_QUERIES.md](../docs/CHINOOK_QUERIES.md) - Example queries to try

## Common Issues

### Issue: "No module named 'agent_snowflake'"
**Fix**: Run from project root: `uv run python examples/enhanced_context_usage.py`

### Issue: "Database connection failed"
**Fix**:
1. Run `make setup-chinook` to create database
2. Set `SNOWFLAKE_AGENT_SNOWFLAKE_URI` in `.env`
3. Use absolute path in URI

### Issue: "API key not found"
**Fix**: Set API keys in `.env`:
```bash
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Issue: "Tool call limit exceeded"
**Fix**: This is expected behavior demonstrating middleware! Increase limits in the example or context.
