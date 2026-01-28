"""System prompts for the Snowflake agent.

Exports the composed system_prompt for use throughout the application.
"""

from .builder import build_system_prompt, system_prompt

__all__ = ["system_prompt", "build_system_prompt"]
