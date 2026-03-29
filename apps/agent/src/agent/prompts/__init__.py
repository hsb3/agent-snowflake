"""System prompts for the Snowflake agent.

Exports build_system_prompt for dynamic prompt generation based on db_type.
"""

from .builder import build_system_prompt

__all__ = ["build_system_prompt"]
