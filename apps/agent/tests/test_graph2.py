"""Tests for graph2.py — enhanced/minimal middleware graph builders.

Covers:
- Middleware stack composition (HITL, model call limits, etc.)
- Dynamic system prompt (SQLite vs Snowflake detection)
- _detect_db_type() helper
- EnhancedContextSchema inheritance, from_env, from_runnable_config, to_dict, get_middleware_config
"""

from dataclasses import fields
from unittest.mock import patch

import pytest
from langchain_community.utilities import SQLDatabase
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

from agent.context import ContextSchema
from agent.context2 import EnhancedContextSchema
from agent.graph2 import (
    _detect_db_type,
    build_graph_minimal_middleware,
    build_graph_with_middleware,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_sqlite_db():
    """Create an in-memory SQLite database with a test table."""
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    Table(
        "customer",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(50)),
    )
    metadata.create_all(engine)
    return SQLDatabase(engine)


@pytest.fixture
def _patch_sql_db(mock_sqlite_db):
    """Patch create_sql_database so no real Snowflake connection is needed."""
    with patch("agent.tools.sql.create_sql_database", return_value=mock_sqlite_db):
        yield


@pytest.fixture
def base_config():
    """Minimal RunnableConfig pointing at an in-memory SQLite URI."""
    return {
        "configurable": {
            "snowflake_uri": "sqlite:///:memory:",
            "read_only": True,
        }
    }


# ---------------------------------------------------------------------------
# _detect_db_type helper
# ---------------------------------------------------------------------------


class TestDetectDbType:
    def test_sqlite_uri(self):
        assert _detect_db_type("sqlite:///:memory:") == "sqlite"

    def test_sqlite_file_uri(self):
        assert _detect_db_type("sqlite:///path/to/chinook.db") == "sqlite"

    def test_snowflake_uri(self):
        assert _detect_db_type("snowflake://user:pass@account/db/schema") == "snowflake"

    def test_empty_string_defaults_to_sqlite(self):
        assert _detect_db_type("") == "sqlite"

    def test_postgres_defaults_to_sqlite(self):
        """Any non-snowflake URI falls back to sqlite."""
        assert _detect_db_type("postgresql://localhost/mydb") == "sqlite"


# ---------------------------------------------------------------------------
# Middleware stack composition — build_graph_with_middleware
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_sql_db")
class TestBuildGraphWithMiddleware:
    """Tests for build_graph_with_middleware()."""

    def test_compiles_with_default_context(self, base_config):
        """Default context produces a compiled graph."""
        graph = build_graph_with_middleware(base_config)
        assert graph is not None
        assert hasattr(graph, "nodes")
        assert hasattr(graph, "invoke")

    def test_hitl_added_when_enabled_and_not_read_only(self, base_config):
        """HITL middleware is added when enable_hitl=True and read_only=False."""
        base_config["configurable"]["enable_hitl"] = True
        base_config["configurable"]["read_only"] = False

        with (
            patch("agent.graph2.HumanInTheLoopMiddleware") as mock_hitl,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_hitl.assert_called_once()

    def test_hitl_not_added_when_read_only(self, base_config):
        """HITL is NOT added when read_only=True, regardless of enable_hitl."""
        base_config["configurable"]["enable_hitl"] = True
        base_config["configurable"]["read_only"] = True

        with (
            patch("agent.graph2.HumanInTheLoopMiddleware") as mock_hitl,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_hitl.assert_not_called()

    def test_hitl_not_added_when_enable_hitl_false(self, base_config):
        """HITL is NOT added when enable_hitl=False."""
        base_config["configurable"]["enable_hitl"] = False
        base_config["configurable"]["read_only"] = False

        with (
            patch("agent.graph2.HumanInTheLoopMiddleware") as mock_hitl,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_hitl.assert_not_called()

    def test_model_call_limit_configured_from_context(self, base_config):
        """ModelCallLimitMiddleware receives limits from context."""
        base_config["configurable"]["model_call_thread_limit"] = 15
        base_config["configurable"]["model_call_run_limit"] = 7

        with (
            patch("agent.graph2.ModelCallLimitMiddleware") as mock_limit,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_limit.assert_called_once_with(
                thread_limit=15,
                run_limit=7,
                exit_behavior="end",
            )

    def test_model_call_limit_skipped_when_zero(self, base_config):
        """ModelCallLimitMiddleware is NOT added when both limits are 0."""
        base_config["configurable"]["model_call_thread_limit"] = 0
        base_config["configurable"]["model_call_run_limit"] = 0

        with (
            patch("agent.graph2.ModelCallLimitMiddleware") as mock_limit,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_limit.assert_not_called()

    def test_retry_middleware_added_by_default(self, base_config):
        """ModelRetryMiddleware is added when retry_max_retries > 0 (default=3)."""
        with (
            patch("agent.graph2.ModelRetryMiddleware") as mock_retry,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_retry.assert_called_once()

    def test_retry_middleware_skipped_when_zero(self, base_config):
        """ModelRetryMiddleware is NOT added when retry_max_retries=0."""
        base_config["configurable"]["retry_max_retries"] = 0

        with (
            patch("agent.graph2.ModelRetryMiddleware") as mock_retry,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_retry.assert_not_called()

    def test_summarization_middleware_added_by_default(self, base_config):
        """SummarizationMiddleware is added when enable_summarization=True (default)."""
        with (
            patch("agent.graph2.SummarizationMiddleware") as mock_summ,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_summ.assert_called_once()

    def test_summarization_middleware_skipped_when_disabled(self, base_config):
        """SummarizationMiddleware is NOT added when enable_summarization=False."""
        base_config["configurable"]["enable_summarization"] = False

        with (
            patch("agent.graph2.SummarizationMiddleware") as mock_summ,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_summ.assert_not_called()

    def test_todo_middleware_added_by_default(self, base_config):
        """TodoListMiddleware is added when enable_todo=True (default)."""
        with (
            patch("agent.graph2.TodoListMiddleware") as mock_todo,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_todo.assert_called_once()

    def test_todo_middleware_skipped_when_disabled(self, base_config):
        """TodoListMiddleware is NOT added when enable_todo=False."""
        base_config["configurable"]["enable_todo"] = False

        with (
            patch("agent.graph2.TodoListMiddleware") as mock_todo,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_todo.assert_not_called()

    def test_fallback_middleware_added_by_default(self, base_config):
        """ModelFallbackMiddleware is added when enable_fallback=True (default)."""
        with (
            patch("agent.graph2.ModelFallbackMiddleware") as mock_fb,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_fb.assert_called_once()

    def test_fallback_middleware_skipped_when_disabled(self, base_config):
        """ModelFallbackMiddleware is NOT added when enable_fallback=False."""
        base_config["configurable"]["enable_fallback"] = False

        with (
            patch("agent.graph2.ModelFallbackMiddleware") as mock_fb,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            mock_fb.assert_not_called()

    def test_middleware_list_passed_to_create_agent(self, base_config):
        """The assembled middleware list is passed to create_agent()."""
        with patch("agent.graph2.create_agent") as mock_create:
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            _, kwargs = mock_create.call_args
            assert "middleware" in kwargs
            assert isinstance(kwargs["middleware"], list)

    def test_context_schema_passed_to_create_agent(self, base_config):
        """EnhancedContextSchema is passed as context_schema to create_agent."""
        with patch("agent.graph2.create_agent") as mock_create:
            mock_create.return_value = _stub_graph()
            build_graph_with_middleware(base_config)
            _, kwargs = mock_create.call_args
            assert kwargs["context_schema"] is EnhancedContextSchema


# ---------------------------------------------------------------------------
# Middleware stack composition — build_graph_minimal_middleware
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_sql_db")
class TestBuildGraphMinimalMiddleware:
    """Tests for build_graph_minimal_middleware()."""

    def test_compiles_successfully(self, base_config):
        """Minimal variant compiles to a graph."""
        graph = build_graph_minimal_middleware(base_config)
        assert graph is not None
        assert hasattr(graph, "nodes")
        assert hasattr(graph, "invoke")

    def test_only_retry_and_limit_middleware(self, base_config):
        """Minimal graph only includes retry + model call limit middleware."""
        with patch("agent.graph2.create_agent") as mock_create:
            mock_create.return_value = _stub_graph()
            build_graph_minimal_middleware(base_config)
            _, kwargs = mock_create.call_args
            mw = kwargs["middleware"]
            type_names = [type(m).__name__ for m in mw]
            # Should not contain HITL, Summarization, Todo, Fallback, ToolCallLimit
            for excluded in [
                "HumanInTheLoopMiddleware",
                "SummarizationMiddleware",
                "TodoListMiddleware",
                "ModelFallbackMiddleware",
                "ToolCallLimitMiddleware",
            ]:
                assert excluded not in type_names

    def test_named_agent_minimal(self, base_config):
        """Minimal graph is named 'agent_minimal'."""
        with patch("agent.graph2.create_agent") as mock_create:
            mock_create.return_value = _stub_graph()
            build_graph_minimal_middleware(base_config)
            _, kwargs = mock_create.call_args
            assert kwargs["name"] == "agent_minimal"


# ---------------------------------------------------------------------------
# Dynamic system prompt — database type detection in graph builders
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("_patch_sql_db")
class TestDynamicSystemPrompt:
    """Verify that the correct system prompt is chosen based on URI."""

    def test_sqlite_uri_uses_sqlite_prompt(self):
        config = {"configurable": {"snowflake_uri": "sqlite:///chinook.db"}}
        with (
            patch("agent.graph2.build_system_prompt") as mock_prompt,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            mock_prompt.return_value = "prompt"
            build_graph_with_middleware(config)
            mock_prompt.assert_called_once_with(db_type="sqlite")

    def test_snowflake_uri_uses_snowflake_prompt(self):
        config = {"configurable": {"snowflake_uri": "snowflake://user:pass@acct/db/schema"}}
        with (
            patch("agent.graph2.build_system_prompt") as mock_prompt,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            mock_prompt.return_value = "prompt"
            build_graph_with_middleware(config)
            mock_prompt.assert_called_once_with(db_type="snowflake")

    def test_minimal_graph_also_detects_db_type(self):
        config = {"configurable": {"snowflake_uri": "snowflake://user:pass@acct/db"}}
        with (
            patch("agent.graph2.build_system_prompt") as mock_prompt,
            patch("agent.graph2.create_agent") as mock_create,
        ):
            mock_create.return_value = _stub_graph()
            mock_prompt.return_value = "prompt"
            build_graph_minimal_middleware(config)
            mock_prompt.assert_called_once_with(db_type="snowflake")


# ---------------------------------------------------------------------------
# EnhancedContextSchema
# ---------------------------------------------------------------------------


class TestEnhancedContextSchemaInheritance:
    """Verify inheritance from ContextSchema."""

    def test_base_fields_present(self):
        """All base ContextSchema fields exist on EnhancedContextSchema."""
        base_names = {f.name for f in fields(ContextSchema)}
        enhanced_names = {f.name for f in fields(EnhancedContextSchema)}
        assert base_names.issubset(enhanced_names)

    def test_has_middleware_fields(self):
        """Enhanced schema adds middleware-specific fields."""
        enhanced_names = {f.name for f in fields(EnhancedContextSchema)}
        expected_middleware_fields = {
            "enable_hitl",
            "hitl_allowed_decisions",
            "model_call_thread_limit",
            "model_call_run_limit",
            "retry_max_retries",
            "enable_summarization",
            "enable_todo",
            "enable_fallback",
        }
        assert expected_middleware_fields.issubset(enhanced_names)

    def test_is_subclass_of_context_schema(self):
        assert issubclass(EnhancedContextSchema, ContextSchema)

    def test_default_construction(self):
        """Can construct with all defaults (no arguments)."""
        ctx = EnhancedContextSchema()
        assert ctx.enable_hitl is True
        assert ctx.model_call_run_limit == 5
        assert ctx.retry_max_retries == 3


class TestEnhancedContextFromEnv:
    """Test from_env() populates both base and enhanced fields."""

    def test_from_env_populates_base_fields(self):
        with patch.dict(
            "os.environ",
            {"AGENT_MODEL": "test-model", "AGENT_READ_ONLY": "false"},
            clear=False,
        ):
            ctx = EnhancedContextSchema.from_env()
            assert ctx.model == "test-model"
            assert ctx.read_only is False

    def test_from_env_populates_enhanced_fields(self):
        with patch.dict(
            "os.environ",
            {
                "AGENT_ENABLE_HITL": "false",
                "AGENT_MODEL_CALL_RUN_LIMIT": "99",
                "AGENT_RETRY_MAX_RETRIES": "7",
            },
            clear=False,
        ):
            ctx = EnhancedContextSchema.from_env()
            assert ctx.enable_hitl is False
            assert ctx.model_call_run_limit == 99
            assert ctx.retry_max_retries == 7

    def test_from_env_defaults_when_env_not_set(self):
        """Without env vars, from_env() uses default values."""
        ctx = EnhancedContextSchema.from_env()
        assert ctx.enable_hitl is True
        assert ctx.enable_summarization is True
        assert ctx.enable_todo is True


class TestEnhancedContextFromRunnableConfig:
    """Test from_runnable_config() handles both base and enhanced fields."""

    def test_with_base_fields_in_config(self):
        config = {"configurable": {"model": "override-model", "temperature": 0.5}}
        ctx = EnhancedContextSchema.from_runnable_config(config)
        assert ctx.model == "override-model"
        assert ctx.temperature == 0.5

    def test_with_enhanced_fields_in_config(self):
        config = {
            "configurable": {
                "enable_hitl": False,
                "model_call_thread_limit": 42,
            }
        }
        ctx = EnhancedContextSchema.from_runnable_config(config)
        assert ctx.enable_hitl is False
        assert ctx.model_call_thread_limit == 42

    def test_with_mixed_fields(self):
        config = {
            "configurable": {
                "model": "gpt-4.1-mini",
                "retry_max_retries": 10,
            }
        }
        ctx = EnhancedContextSchema.from_runnable_config(config)
        assert ctx.model == "gpt-4.1-mini"
        assert ctx.retry_max_retries == 10

    def test_with_none_config(self):
        """None config falls back to env/defaults."""
        ctx = EnhancedContextSchema.from_runnable_config(None)
        assert ctx is not None
        assert isinstance(ctx, EnhancedContextSchema)

    def test_without_fallback_env(self):
        config = {"configurable": {"enable_hitl": False}}
        ctx = EnhancedContextSchema.from_runnable_config(config, fallback_env=False)
        assert ctx.enable_hitl is False
        # Fields not in config use dataclass defaults
        assert ctx.model_call_run_limit == 5


class TestEnhancedContextToDict:
    """Test to_dict() includes all fields."""

    def test_includes_base_fields(self):
        ctx = EnhancedContextSchema()
        d = ctx.to_dict()
        assert "model" in d
        assert "snowflake_uri" in d
        assert "read_only" in d

    def test_includes_enhanced_fields(self):
        ctx = EnhancedContextSchema()
        d = ctx.to_dict()
        assert "enable_hitl" in d
        assert "model_call_thread_limit" in d
        assert "retry_max_retries" in d
        assert "enable_summarization" in d

    def test_roundtrip_values(self):
        ctx = EnhancedContextSchema(model_call_run_limit=99, enable_hitl=False)
        d = ctx.to_dict()
        assert d["model_call_run_limit"] == 99
        assert d["enable_hitl"] is False


class TestGetMiddlewareConfig:
    """Test get_middleware_config() returns only middleware-specific fields."""

    def test_returns_only_middleware_fields(self):
        ctx = EnhancedContextSchema()
        mw = ctx.get_middleware_config()
        base_names = {f.name for f in fields(ContextSchema)}
        for key in mw:
            assert key not in base_names, (
                f"{key} is a base field, should not be in middleware config"
            )

    def test_includes_all_enhanced_fields(self):
        ctx = EnhancedContextSchema()
        mw = ctx.get_middleware_config()
        enhanced_only_names = {f.name for f in fields(EnhancedContextSchema)} - {
            f.name for f in fields(ContextSchema)
        }
        assert set(mw.keys()) == enhanced_only_names

    def test_values_match_instance(self):
        ctx = EnhancedContextSchema(enable_hitl=False, retry_max_retries=1)
        mw = ctx.get_middleware_config()
        assert mw["enable_hitl"] is False
        assert mw["retry_max_retries"] == 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _StubGraph:
    """Minimal stand-in for CompiledStateGraph when we only need create_agent to return something."""

    nodes = {"agent": None, "tools": None}

    def invoke(self, *args, **kwargs):
        return {}


def _stub_graph():
    return _StubGraph()
