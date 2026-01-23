# Local Snowflake Testing Guide

This guide covers multiple approaches for testing Snowflake locally without requiring cloud credentials or incurring costs.

## Table of Contents

1. [Overview](#overview)
2. [Option 1: fakesnow (Recommended)](#option-1-fakesnow-recommended)
3. [Option 2: snowflake-emulator (Docker)](#option-2-snowflake-emulator-docker)
4. [Option 3: Real Snowflake Trial](#option-3-real-snowflake-trial)
5. [Comparison](#comparison)
6. [Sample Data](#sample-data)

## Overview

Since Snowflake is a cloud-native data warehouse, there's no official local version. However, several community solutions provide local testing capabilities:

| Solution | Pros | Cons |
|----------|------|------|
| **fakesnow** | Easy setup, no Docker, fast | ~95% Snowflake compatibility |
| **snowflake-emulator** | Good compatibility, persistent storage | Requires Docker |
| **Snowflake Trial** | 100% compatible, real features | Requires signup, limited time |

## Option 1: fakesnow (Recommended)

**Best for:** Unit testing, CI/CD, local development without Docker

**Quick summary:** Pure Python mocking library using DuckDB backend. No Docker required, fast test execution, perfect for pytest and CI/CD pipelines.

**For complete details:** See [TESTING_FAKESNOW.md](./TESTING_FAKESNOW.md)

**Quick start:**
```bash
uv add fakesnow
uv run python test_fakesnow.py
```

## Option 2: snowflake-emulator (Docker)

**Best for:** Integration testing, team environments, persistent test data

**Quick summary:** Docker-based HTTP API emulator with DuckDB backend. Provides persistent storage and good Snowflake compatibility for integration testing.

**For complete details:** See [TESTING.md](./TESTING.md)

**Quick start:**
```bash
docker-compose up -d
uv run python test_emulator.py
```

## Option 3: Real Snowflake Trial

**Best for:** Feature testing, performance testing, production-like environments

**Quick summary:** 100% compatible real Snowflake environment with $400 free credits and 30-day trial. Required for testing Snowflake-specific features like Stages, Snowpark, and UDFs.

**Sign up:** https://signup.snowflake.com/

## Comparison

### Performance

| Solution | Speed | Startup Time | Data Size |
|----------|-------|--------------|-----------|
| fakesnow | Very Fast | Instant | Small-Medium |
| snowflake-emulator | Fast | ~5 seconds | Medium |
| Snowflake Trial | Varies | ~30 seconds | Large |

### Compatibility

| Feature | fakesnow | snowflake-emulator | Snowflake Trial |
|---------|----------|-------------------|-----------------|
| SQL Queries | ✅ 95% | ✅ 85% | ✅ 100% |
| Joins | ✅ | ✅ | ✅ |
| Aggregations | ✅ | ✅ | ✅ |
| Window Functions | ✅ | ✅ | ✅ |
| CTEs | ✅ | ✅ | ✅ |
| Stages | ❌ | ❌ | ✅ |
| Snowpark | ❌ | ❌ | ✅ |
| Stored Procs | ❌ | ❌ | ✅ |
| UDFs | ⚠️ Limited | ⚠️ Limited | ✅ |

### Use Cases

| Use Case | Recommended Solution |
|----------|---------------------|
| Unit testing | fakesnow |
| CI/CD pipelines | fakesnow |
| Local development | fakesnow or snowflake-emulator |
| Integration testing | snowflake-emulator |
| Feature testing | Snowflake Trial |
| Performance testing | Snowflake Trial |
| Team environments | snowflake-emulator |
| Production-like testing | Snowflake Trial |

## Sample Data

All testing solutions include a TPC-H inspired sample dataset with 6 tables (REGION, NATION, CUSTOMER, ORDERS, PART, LINEITEM) containing realistic business data.

**For sample queries and detailed schema:** See [TESTING_FAKESNOW.md](./TESTING_FAKESNOW.md#sample-queries) or [TESTING.md](./TESTING.md#sample-queries)

## Environment Configuration

See `.env.example` for environment variable templates for all three testing options.

**For detailed configuration:** See [TESTING_FAKESNOW.md](./TESTING_FAKESNOW.md#environment-variables) or [TESTING.md](./TESTING.md#environment-variables)

## Getting Started

**Recommended approach (fakesnow):**
```bash
uv add fakesnow
uv run python test_fakesnow.py
```

**Alternative (Docker emulator):**
```bash
docker-compose up -d
uv run python test_emulator.py
```

Then start building your agent!

## Troubleshooting

**For detailed troubleshooting:** See [TESTING_FAKESNOW.md](./TESTING_FAKESNOW.md#troubleshooting) or [TESTING.md](./TESTING.md#troubleshooting)

**Quick fixes:**
- fakesnow: Ensure installed (`uv add fakesnow`) and use context manager
- Docker: Ensure Docker running (`docker ps`) and emulator started (`docker-compose up -d`)

## Additional Resources

### fakesnow
- [GitHub Repository](https://github.com/tekumara/fakesnow)
- [PyPI Package](https://pypi.org/project/fakesnow/)

### snowflake-emulator
- [GitHub Repository](https://github.com/nnnkkk7/snowflake-emulator)
- [DEV Community Article](https://dev.to/kurorr/stop-burning-snowflake-credits-build-a-local-emulator-with-go-and-duckdb-44lk)

### Snowflake
- [Official Documentation](https://docs.snowflake.com/)
- [Free Trial Signup](https://signup.snowflake.com/)
- [Sample Data Documentation](https://docs.snowflake.com/en/user-guide/sample-data)

### DuckDB
- [Official Documentation](https://duckdb.org/docs/)
- [SQL Introduction](https://duckdb.org/docs/sql/introduction)

## Files in This Project

```
agent-snowflake/
├── docs/
│   ├── README_TESTING.md        # This file
│   ├── TESTING_FAKESNOW.md     # fakesnow detailed docs
│   └── TESTING.md              # Docker emulator detailed docs
├── docker-compose.yml            # Docker emulator config
├── test_fakesnow.py              # fakesnow test script
├── test_emulator.py              # Docker emulator test script
├── .env.example                  # Environment variables template
└── scripts/
    ├── init_data.sql             # Sample data for Docker emulator
    └── test_connection.py        # Detailed emulator test
```

## Next Steps

1. Choose your testing approach (fakesnow recommended)
2. Install dependencies and run test scripts
3. Review the sample data and queries
4. Start building your Snowflake agent
5. Switch to real Snowflake for production

## Support

- For fakesnow issues: https://github.com/tekumara/fakesnow/issues
- For snowflake-emulator issues: https://github.com/nnnkkk7/snowflake-emulator/issues
- For Snowflake issues: https://community.snowflake.com/
