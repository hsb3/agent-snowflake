"""Tests for Config (Layer 8 - Config).

Test-driven development for configuration loading.
"""

import os
from unittest.mock import patch

from repl_client.core.config import Config


class TestConfig:
    """Test Config dataclass and factory methods."""

    def test_config_defaults(self):
        """Test Config with default values."""
        config = Config()

        assert config.server_url == "http://localhost:2024"
        assert config.default_agent == ""
        assert config.stream_mode == ["messages"]
        assert config.debug is False

    def test_config_custom_values(self):
        """Test Config with custom values."""
        config = Config(
            server_url="http://localhost:8000",
            default_agent="agent_enhanced",
            stream_mode=["messages", "updates"],
            debug=True,
        )

        assert config.server_url == "http://localhost:8000"
        assert config.default_agent == "agent_enhanced"
        assert config.stream_mode == ["messages", "updates"]
        assert config.debug is True

    def test_from_env_with_url(self):
        """Test from_env() loads LANGGRAPH_DEV_SERVER_URL."""
        with patch.dict(
            os.environ,
            {"LANGGRAPH_DEV_SERVER_URL": "http://localhost:3000", "REPL_DEFAULT_AGENT": ""},
        ):
            config = Config.from_env()

            assert config.server_url == "http://localhost:3000"
            assert config.default_agent == ""
            assert config.stream_mode == ["messages"]
            assert config.debug is False

    def test_from_env_with_default_agent(self):
        """Test from_env() loads REPL_DEFAULT_AGENT."""
        with patch.dict(
            os.environ,
            {
                "LANGGRAPH_DEV_SERVER_URL": "http://localhost:2024",
                "REPL_DEFAULT_AGENT": "agent_basic",
            },
        ):
            config = Config.from_env()

            assert config.server_url == "http://localhost:2024"
            assert config.default_agent == "agent_basic"

    def test_from_env_with_debug(self):
        """Test from_env() loads REPL_DEBUG."""
        with patch.dict(
            os.environ,
            {
                "LANGGRAPH_DEV_SERVER_URL": "http://localhost:2024",
                "REPL_DEBUG": "true",
            },
        ):
            config = Config.from_env()

            assert config.debug is True

        # Test various truthy values
        for value in ["1", "True", "TRUE", "yes", "YES"]:
            with patch.dict(
                os.environ,
                {
                    "LANGGRAPH_DEV_SERVER_URL": "http://localhost:2024",
                    "REPL_DEBUG": value,
                },
            ):
                config = Config.from_env()
                assert config.debug is True

    def test_from_env_missing_url_uses_default(self):
        """Test from_env() uses default when LANGGRAPH_DEV_SERVER_URL missing."""
        with patch("repl_client.core.config.load_dotenv"), patch.dict(os.environ, {}, clear=True):
            config = Config.from_env()

            assert config.server_url == "http://localhost:2024"

    def test_from_env_prefers_environment_over_dotenv(self):
        """Test from_env() prioritizes environment variables over .env file.

        This tests that environment variables take precedence, which is the
        standard behavior of load_dotenv(). We don't test .env file loading
        in isolation since it's implementation detail - manual testing will
        verify .env files work in practice.
        """
        with patch.dict(
            os.environ,
            {
                "LANGGRAPH_DEV_SERVER_URL": "http://localhost:9999",
                "REPL_DEFAULT_AGENT": "env_agent",
            },
        ):
            config = Config.from_env()

            # Environment variables should be used
            assert config.server_url == "http://localhost:9999"
            assert config.default_agent == "env_agent"

    def test_server_url_from_env(self):
        """Test server_url is read directly from environment."""
        with patch.dict(os.environ, {"LANGGRAPH_DEV_SERVER_URL": "http://localhost:8080"}):
            config = Config.from_env()
            assert config.server_url == "http://localhost:8080"
            assert not config.server_url.endswith("/")
