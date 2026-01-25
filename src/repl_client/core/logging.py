"""Client-side logging for REPL operations.

This module provides logging configuration for the REPL client.
Logs client operations like connection attempts, thread creation, command execution, etc.
Does NOT log server-side agent execution (that's handled by LangGraph).
"""

import logging
from pathlib import Path

# Root logger for all REPL client components
ROOT_LOGGER_NAME = "repl_client"


def setup_client_logger(log_file: str = ".repl/client.log", level: str = "INFO") -> logging.Logger:
    """Configure client-side logger.

    Args:
        log_file: Path to log file (directory will be created if needed)
        level: Log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Get or create root logger
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setLevel(getattr(logging, level.upper()))

    # Create formatter matching spec: %(asctime)s [%(levelname)s] %(name)s - %(message)s
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(file_handler)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger for specific module.

    Args:
        name: Module name (will be prefixed with 'repl_client.')

    Returns:
        Logger instance for the module
    """
    full_name = f"{ROOT_LOGGER_NAME}.{name}"
    return logging.getLogger(full_name)
