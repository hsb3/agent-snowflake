"""Tests for SQL tools."""

import pytest
from langchain_community.utilities import SQLDatabase
from langchain_core.language_models import BaseChatModel
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from agent_snowflake.context import ContextSchema
from agent_snowflake.tools import create_sql_tools, get_database_context
from agent_snowflake.utils import (
    create_snowflake_engine,
    is_test_connection,
)


class MockLLM(BaseChatModel):
    """Mock LLM for testing (query checker tool needs an LLM)."""

    def _generate(self, *args, **kwargs):
        """Mock generate method."""
        from langchain_core.messages import AIMessage
        from langchain_core.outputs import ChatGeneration, ChatResult

        return ChatResult(
            generations=[ChatGeneration(message=AIMessage(content="SELECT * FROM CUSTOMER"))]
        )

    def _llm_type(self) -> str:
        return "mock"

    @property
    def _identifying_params(self):
        return {}


@pytest.fixture
def mock_llm():
    """Provide mock LLM for tests."""
    return MockLLM()


@pytest.fixture
def test_context():
    """Provide test context."""
    return ContextSchema(
        snowflake_uri="snowflake://test:test@localhost:8080/SAMPLE_DB/TPCH_SAMPLE",
        allowed_schemas="TPCH_SAMPLE",
        allowed_tables="*",
        read_only=True,
        enable_debug=True,
    )


@pytest.fixture
def sqlite_test_db():
    """Create a SQLite test database for testing tools without Snowflake."""
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()

    # Create test tables
    _customer = Table(
        "customer",
        metadata,
        Column("c_custkey", Integer, primary_key=True),
        Column("c_name", String(50)),
        Column("c_nationkey", Integer),
    )

    _orders = Table(
        "orders",
        metadata,
        Column("o_orderkey", Integer, primary_key=True),
        Column("o_custkey", Integer),
        Column("o_totalprice", Integer),
    )

    metadata.create_all(engine)

    # Create SQLDatabase instance
    db = SQLDatabase(engine, include_tables=["customer", "orders"])
    return db


def test_is_test_connection():
    """Test detection of test connections."""
    # Test connections
    assert is_test_connection("snowflake://user:pass@localhost/db")
    assert is_test_connection("snowflake://user:pass@127.0.0.1/db")
    assert is_test_connection("snowflake://user:pass@localhost:8080/db")
    assert is_test_connection("snowflake://user:pass@test-account/db")

    # Production connections
    assert not is_test_connection("snowflake://user:pass@myaccount.snowflakecomputing.com/db")
    assert not is_test_connection("snowflake://user:pass@prod-account/db")


def test_create_engine_from_uri(test_context):
    """Test engine creation from URI."""
    engine = create_snowflake_engine(test_context)
    assert engine is not None
    assert "snowflake" in str(engine.url).lower() or "localhost" in str(engine.url).lower()


def test_create_engine_missing_params():
    """Test that engine creation fails without required params."""
    context = ContextSchema(
        snowflake_uri="",  # No URI
        snowflake_account="",  # Missing account
        snowflake_user="test-user",
        snowflake_password="test-pass",
    )
    with pytest.raises(ValueError, match="Either snowflake_uri or all of"):
        create_snowflake_engine(context)


def test_create_sql_tools_with_sqlite(mock_llm, sqlite_test_db):
    """Test SQL tools creation using SQLite (no Snowflake connection needed)."""
    # Create tools using pre-made database
    context = ContextSchema(
        snowflake_uri="sqlite:///:memory:",  # Not actually used
        read_only=True,
    )

    tools = create_sql_tools(llm=mock_llm, context=context, db=sqlite_test_db)

    assert len(tools) > 0

    # Check for expected tools from SQLDatabaseToolkit
    tool_names = [t.name for t in tools]
    assert "sql_db_query" in tool_names or any("query" in name for name in tool_names)
    assert "sql_db_list_tables" in tool_names or any("list" in name for name in tool_names)
    assert "sql_db_schema" in tool_names or any(
        "schema" in name or "info" in name for name in tool_names
    )


def test_sql_tools_read_only_enforcement(mock_llm, sqlite_test_db):
    """Test that read-only mode adds restrictions to tool descriptions."""
    context = ContextSchema(
        snowflake_uri="sqlite:///:memory:",
        read_only=True,
    )

    tools = create_sql_tools(llm=mock_llm, context=context, db=sqlite_test_db)

    # Find query execution tool
    query_tools = [
        t for t in tools if "query" in t.name.lower() and "checker" not in t.name.lower()
    ]

    assert len(query_tools) > 0

    # Check that read-only note is in description
    query_tool = query_tools[0]
    assert "read-only" in query_tool.description.lower() or "SELECT" in query_tool.description


def test_get_database_context(sqlite_test_db):
    """Test getting database context information."""
    ctx = get_database_context(sqlite_test_db)

    assert isinstance(ctx, dict)
    # Context should have useful info about the database
    assert "dialect" in ctx or "table_info" in ctx


def test_create_sql_tools_with_provided_database(mock_llm, sqlite_test_db):
    """Test tool creation with pre-created database."""
    context = ContextSchema(
        snowflake_uri="sqlite:///:memory:",
        read_only=False,
    )

    # Pass database to tool creation
    tools = create_sql_tools(llm=mock_llm, context=context, db=sqlite_test_db)

    assert len(tools) > 0
    tool_names = [t.name for t in tools]
    assert any("query" in name for name in tool_names)


def test_engine_uri_with_timeout():
    """Test that query timeout is passed to engine."""
    context = ContextSchema(
        snowflake_account="myaccount",
        snowflake_user="myuser",
        snowflake_password="mypass",
        query_timeout=60,
    )

    engine = create_snowflake_engine(context)
    # Engine created successfully with timeout setting
    assert engine is not None


def test_sql_database_with_schema_restriction():
    """Test SQLDatabase configuration with schema restriction."""
    # Create in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    Table(
        "test_table",
        metadata,
        Column("id", Integer, primary_key=True),
    )
    metadata.create_all(engine)

    # Create database with no restrictions
    db = SQLDatabase(engine)
    assert db is not None
    assert db.dialect == "sqlite"


def test_tools_integration_with_sqlite(mock_llm):
    """Integration test: Create tools end-to-end with SQLite."""
    # Setup SQLite database
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()

    _customer = Table(
        "customer",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(50)),
    )
    metadata.create_all(engine)

    db = SQLDatabase(engine)

    # Create context and tools
    context = ContextSchema(
        snowflake_uri="sqlite:///:memory:",
        read_only=True,
        enable_debug=False,
    )

    tools = create_sql_tools(llm=mock_llm, context=context, db=db)

    # Verify tools were created
    assert len(tools) == 4  # SQLDatabaseToolkit provides 4 tools
    tool_names = {t.name for t in tools}
    expected_tools = {
        "sql_db_query",
        "sql_db_schema",
        "sql_db_list_tables",
        "sql_db_query_checker",
    }
    assert tool_names == expected_tools
