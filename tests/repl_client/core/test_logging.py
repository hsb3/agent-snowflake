"""Tests for REPL client logging system."""

import logging
import os
from pathlib import Path

import pytest

from repl_client.core.logging import get_logger, setup_client_logger


@pytest.fixture
def temp_log_file(tmp_path):
    """Create a temporary log file path."""
    return str(tmp_path / "test_client.log")


def test_setup_client_logger_creates_file(temp_log_file):
    """Test that setup_client_logger creates log file and configures logger."""
    logger = setup_client_logger(temp_log_file, level="INFO")

    # Logger should be configured
    assert logger is not None
    assert logger.name == "repl_client"
    assert logger.level == logging.INFO

    # Write a log message
    logger.info("Test message")

    # Log file should exist and contain the message
    assert os.path.exists(temp_log_file)
    with open(temp_log_file) as f:
        content = f.read()
        assert "Test message" in content
        assert "[INFO]" in content


def test_setup_client_logger_custom_level(temp_log_file):
    """Test that setup_client_logger respects custom log level."""
    logger = setup_client_logger(temp_log_file, level="DEBUG")

    assert logger.level == logging.DEBUG

    # DEBUG messages should be logged
    logger.debug("Debug message")

    with open(temp_log_file) as f:
        content = f.read()
        assert "Debug message" in content
        assert "[DEBUG]" in content


def test_setup_client_logger_warning_level(temp_log_file):
    """Test that WARNING level filters out INFO and DEBUG."""
    logger = setup_client_logger(temp_log_file, level="WARNING")

    assert logger.level == logging.WARNING

    # Write messages at different levels
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    with open(temp_log_file) as f:
        content = f.read()
        # DEBUG and INFO should not appear
        assert "Debug message" not in content
        assert "Info message" not in content
        # WARNING and ERROR should appear
        assert "Warning message" in content
        assert "Error message" in content


def test_get_logger_returns_configured_logger(temp_log_file):
    """Test that get_logger returns a logger with the correct configuration."""
    # Setup main logger first
    setup_client_logger(temp_log_file, level="INFO")

    # Get module-specific logger
    module_logger = get_logger("test_module")

    assert module_logger is not None
    assert module_logger.name == "repl_client.test_module"

    # Should inherit configuration from parent
    module_logger.info("Module test message")

    with open(temp_log_file) as f:
        content = f.read()
        assert "Module test message" in content
        assert "repl_client.test_module" in content


def test_log_format_matches_spec(temp_log_file):
    """Test that log format matches specification."""
    logger = setup_client_logger(temp_log_file, level="INFO")
    logger.info("Test message")

    with open(temp_log_file) as f:
        content = f.read().strip()
        # Format: %(asctime)s [%(levelname)s] %(name)s - %(message)s
        # Should contain timestamp, level in brackets, logger name, dash, message
        assert "[INFO]" in content
        assert "repl_client" in content
        assert " - " in content
        assert "Test message" in content


def test_multiple_log_levels(temp_log_file):
    """Test logging at different levels."""
    logger = setup_client_logger(temp_log_file, level="DEBUG")

    logger.debug("Debug level")
    logger.info("Info level")
    logger.warning("Warning level")
    logger.error("Error level")

    with open(temp_log_file) as f:
        content = f.read()
        assert "[DEBUG]" in content and "Debug level" in content
        assert "[INFO]" in content and "Info level" in content
        assert "[WARNING]" in content and "Warning level" in content
        assert "[ERROR]" in content and "Error level" in content


def test_setup_creates_log_directory(tmp_path):
    """Test that setup creates log directory if it doesn't exist."""
    log_file = str(tmp_path / "nested" / "dir" / "client.log")

    logger = setup_client_logger(log_file, level="INFO")
    logger.info("Test")

    # Directory should be created
    assert os.path.exists(os.path.dirname(log_file))
    assert os.path.exists(log_file)


def test_get_logger_before_setup():
    """Test that get_logger works even if setup not called (uses default config)."""
    # Get logger without setup
    logger = get_logger("standalone_module")

    # Should not raise exception
    assert logger is not None
    assert logger.name == "repl_client.standalone_module"
