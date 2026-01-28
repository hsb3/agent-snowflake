# SQLite Persistence Module for LangGraph

Factory functions for creating SQLite-based checkpointers and stores for LangGraph applications.

## Files

- `checkpointer.py` - Creates `SqliteSaver` for checkpoint persistence
- `store.py` - Creates `SqliteStore` for long-term memory
- `test_checkpointer_unit.py` - Unit tests (7/7 passing)
- `test_checkpointer_integration.py` - Integration tests with LLM (6/7 passing)

## Usage

### Direct Usage

```python
from persistence import create_sqlite_checkpointer, create_sqlite_store

# Create checkpointer (stores conversation state)
checkpointer = create_sqlite_checkpointer()

# Create store (long-term memory with TTL)
store = create_sqlite_store()

# Use with LangGraph
graph_with_persistence = graph.with_config({
    "checkpointer": checkpointer,
    "store": store
})
```

## Database Locations

- Checkpointer: `.langgraph_data/checkpoints.db`
- Store: `.langgraph_data/store.db`

## Notes

- Uses synchronous SQLite (LangGraph runtime handles async conversion)
- Checkpointer DB: ~20KB typical size
- Store DB: ~24KB typical size
- TTL: 7 days for store items with refresh on read
- Thread-safe with `check_same_thread=False`

## Why Not Used in agent-snowflake

The default `langgraph dev` in-memory persistence (pickle-based) works fine for development.
This module was extracted for potential use in custom servers or production deployments.

## Future Improvements

### 1. Configurable Factory Functions

Update factories to accept a `config_dict` parameter for runtime configuration:

**Checkpointer options:**
- `db_path`: Custom database file path (default: `.langgraph_data/checkpoints.db`)
- `serde`: Custom serialization/deserialization protocol
- `check_same_thread`: Thread safety settings (default: `False`)

**Store options:**
- `db_path`: Custom database file path (default: `.langgraph_data/store.db`)
- `ttl_default`: Default TTL in seconds (currently hardcoded to 7 days)
- `ttl_refresh_on_read`: Whether to refresh TTL on read (currently `True`)
- `index_config`: Vector search configuration (`SqliteIndexConfig`)
- `deserializer`: Custom deserialization function
- `isolation_level`: SQLite isolation level (currently `None` for autocommit)

Example:
```python
def create_sqlite_checkpointer(config_dict: dict | None = None) -> SqliteSaver:
    config = config_dict or {}
    db_path = config.get("db_path", ".langgraph_data/checkpoints.db")
    # ... use config options
```

### 2. Async/Sync Variants

Either add selection parameter or create separate factory functions:

**Option A: Selection parameter**
```python
def create_sqlite_checkpointer(use_async: bool = False) -> SqliteSaver | AsyncSqliteSaver:
    if use_async:
        # Return AsyncSqliteSaver with aiosqlite connection
    else:
        # Return SqliteSaver with sqlite3 connection
```

**Option B: Separate factory functions (recommended)**
```python
def create_sqlite_checkpointer() -> SqliteSaver:
    # Synchronous version (current implementation)

def create_async_sqlite_checkpointer() -> AsyncSqliteSaver:
    # Async version with aiosqlite
```

**Note:** AsyncSqliteSaver requires:
- `aiosqlite` connection instead of `sqlite3`
- Async setup: `await checkpointer.setup()`
- Cannot use `asyncio.run()` in factory (conflicts with running event loops)
