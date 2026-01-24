# Testing Strategy

## Database Usage Pattern

**test_snowflake.db** - Unit/Integration tests (pytest)
- Minimal stub data (13 rows across 3 tables)
- Fast test execution
- Used by CI/CD pipeline
- Setup: `make setup-test-db`

**test_chinook.db** - UAT (User Acceptance Testing)
- Realistic data (15,000+ rows, 11 tables)
- Manual testing and demos
- Middleware behavior validation
- Setup: `make setup-chinook`

## Test Execution

```bash
# Unit/Integration tests (uses test_snowflake.db via fixtures)
make test

# UAT (manual testing in Studio)
make setup-chinook
export SNOWFLAKE_AGENT_SNOWFLAKE_URI=sqlite:///$(pwd)/test_chinook.db
make dev
```

## Test Fixtures

Pytest fixtures in `tests/conftest.py` use test_snowflake.db:
- `sample_database` - SQLite connection with stub data
- `fakesnow_connection` - FakeSnow mock
- Tests don't require Chinook database

## UAT Focus Areas

- Schema exploration with realistic tables
- Complex multi-table joins
- Aggregation queries on real data
- Middleware behavior (call limits, HITL, summarization)
- Multi-step analytical workflows
- Agent response quality

## CI/CD

Pipeline uses test_snowflake.db only:
```bash
make setup-test-db
make test
```

No need to download Chinook in CI (slower, unnecessary for unit tests).
