"""Utility functions for the Snowflake agent."""

import logging
from typing import Any

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)


def init_model(
    model: str,
    temperature: float = 0.0,
    **kwargs: Any,
) -> BaseChatModel:
    """Initialize a chat model with special case handling.

    Wrapper around init_chat_model() that handles provider-specific quirks
    and provides consistent behavior across different LLM providers.

    Args:
        model: Model identifier (e.g., "claude-sonnet-4-5-20250929", "gpt-4o")
        temperature: Temperature for model (0.0=deterministic, 1.0=creative)
        **kwargs: Additional arguments passed to init_chat_model

    Returns:
        Initialized chat model

    Examples:
        >>> llm = init_model("claude-sonnet-4-5-20250929", temperature=0.0)
        >>> llm = init_model("gpt-4o", temperature=0.7)
        >>> llm = init_model("gemini-2.0-flash-exp")

    Notes:
        - Handles model-specific defaults
        - Provides consistent error messages
        - Future: Can add retry logic, fallback models, etc.
    """
    try:
        # Log model initialization
        logger.debug(f"Initializing model: {model} (temperature={temperature})")

        # Special cases can be handled here
        # For now, just pass through to init_chat_model
        llm = init_chat_model(
            model=model,
            temperature=temperature,
            **kwargs,
        )

        logger.debug(f"Successfully initialized: {llm.__class__.__name__}")
        return llm

    except Exception as e:
        logger.error(f"Failed to initialize model '{model}': {e}")
        raise
