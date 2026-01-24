"""Test suite for SessionState (Layer 3)."""

import time

import pytest

from repl_client.core.session import SessionState


class TestSessionInit:
    """Test initialization."""

    def test_init(self):
        """Initial state is None/empty, tokens are 0, session_start_time is set."""
        session = SessionState()

        # Thread/agent/run state
        assert session.current_thread_id is None
        assert session.current_assistant_id == ""
        assert session.current_run_id is None

        # Namespace state
        assert session.namespace_state == {}

        # Token tracking
        assert session.session_tokens == {"input": 0, "output": 0, "total": 0}

        # Start time
        assert isinstance(session.session_start_time, float)
        assert session.session_start_time > 0


class TestSetThread:
    """Test set_thread method."""

    def test_set_thread(self):
        """Sets current_thread_id and clears namespace_state."""
        session = SessionState()

        # Add some namespace state
        session.namespace_state[("a", "b")] = {"data": "value"}

        # Set thread
        session.set_thread("thread-123")

        assert session.current_thread_id == "thread-123"
        assert session.namespace_state == {}


class TestSetAgent:
    """Test set_agent method."""

    def test_set_agent(self):
        """Sets current_assistant_id."""
        session = SessionState()

        session.set_agent("agent-456")

        assert session.current_assistant_id == "agent-456"


class TestSetRun:
    """Test set_run method."""

    def test_set_run(self):
        """Sets current_run_id."""
        session = SessionState()

        session.set_run("run-789")

        assert session.current_run_id == "run-789"


class TestGetNamespaceKey:
    """Test get_namespace_key method."""

    def test_get_namespace_key_none(self):
        """None → ()."""
        session = SessionState()

        result = session.get_namespace_key(None)

        assert result == ()

    def test_get_namespace_key_list(self):
        """["a", "b"] → ("a", "b")."""
        session = SessionState()

        result = session.get_namespace_key(["a", "b"])

        assert result == ("a", "b")

    def test_get_namespace_key_empty_list(self):
        """[] → ()."""
        session = SessionState()

        result = session.get_namespace_key([])

        assert result == ()


class TestTrackTokens:
    """Test track_tokens method."""

    def test_track_tokens_accumulates_input(self):
        """Accumulates input_tokens."""
        session = SessionState()

        session.track_tokens(100, 50)
        session.track_tokens(200, 75)

        assert session.session_tokens["input"] == 300

    def test_track_tokens_accumulates_output(self):
        """Accumulates output_tokens."""
        session = SessionState()

        session.track_tokens(100, 50)
        session.track_tokens(200, 75)

        assert session.session_tokens["output"] == 125

    def test_track_tokens_calculates_total(self):
        """Calculates total_tokens."""
        session = SessionState()

        session.track_tokens(100, 50)
        session.track_tokens(200, 75)

        assert session.session_tokens["total"] == 425


class TestGetTokenSummary:
    """Test get_token_summary method."""

    def test_get_token_summary_returns_dict(self):
        """Returns dict with input, output, total."""
        session = SessionState()

        session.track_tokens(150, 75)

        summary = session.get_token_summary()

        assert isinstance(summary, dict)
        assert summary["input"] == 150
        assert summary["output"] == 75
        assert summary["total"] == 225

    def test_get_token_summary_matches_tracked_values(self):
        """Matches tracked values after multiple calls."""
        session = SessionState()

        session.track_tokens(100, 50)
        session.track_tokens(200, 75)
        session.track_tokens(50, 25)

        summary = session.get_token_summary()

        assert summary["input"] == 350
        assert summary["output"] == 150
        assert summary["total"] == 500


class TestGetDisplaySummary:
    """Test get_display_summary method."""

    def test_get_display_summary_shows_thread_agent_tokens(self):
        """Shows thread ID, agent, tokens."""
        session = SessionState()

        session.set_thread("thread-123")
        session.set_agent("agent-456")
        session.track_tokens(100, 50)

        summary = session.get_display_summary()

        assert "thread-123" in summary
        assert "agent-456" in summary
        assert "100" in summary or "50" in summary or "150" in summary

    def test_get_display_summary_handles_none_thread(self):
        """Handles None thread gracefully."""
        session = SessionState()

        session.set_agent("agent-456")
        session.track_tokens(100, 50)

        summary = session.get_display_summary()

        # Should not crash, and should handle missing thread
        assert isinstance(summary, str)
        assert "agent-456" in summary


class TestReset:
    """Test reset method."""

    def test_reset_clears_all_state(self):
        """Clears all state."""
        session = SessionState()

        # Set up some state
        session.set_thread("thread-123")
        session.set_agent("agent-456")
        session.set_run("run-789")
        session.namespace_state[("a", "b")] = {"data": "value"}
        session.track_tokens(100, 50)

        # Reset
        session.reset()

        # Check all state cleared
        assert session.current_thread_id is None
        assert session.current_assistant_id == ""
        assert session.current_run_id is None
        assert session.namespace_state == {}

    def test_reset_resets_tokens_to_zero(self):
        """Resets tokens to 0."""
        session = SessionState()

        session.track_tokens(100, 50)

        session.reset()

        assert session.session_tokens == {"input": 0, "output": 0, "total": 0}

    def test_reset_resets_start_time(self):
        """Resets start time."""
        session = SessionState()

        original_time = session.session_start_time
        time.sleep(0.01)  # Small delay to ensure time changes

        session.reset()

        # Start time should be updated
        assert session.session_start_time > original_time
