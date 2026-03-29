"""Builder for composing system prompts from components."""

from typing import Literal

from .core import CORE_INSTRUCTIONS, SAFETY_INSTRUCTIONS
from .db_specific import SNOWFLAKE_INSTRUCTIONS, SQLITE_INSTRUCTIONS
from .special import SPECIAL_INSTRUCTIONS

DatabaseType = Literal["sqlite", "snowflake"]


def build_system_prompt(
    db_type: DatabaseType = "sqlite",
    include_special: bool = False,
    additional_instructions: str | None = None,
) -> str:
    """Build the complete system prompt from components.

    Args:
        db_type: Database type ("sqlite" or "snowflake") for db-specific guidance
        include_special: Whether to include special instructions
        additional_instructions: Optional additional instructions to append

    Returns:
        Complete system prompt string
    """
    components = [
        CORE_INSTRUCTIONS,
        SAFETY_INSTRUCTIONS,
    ]

    # Add database-specific instructions
    if db_type == "sqlite":
        components.append(SQLITE_INSTRUCTIONS)
    elif db_type == "snowflake":
        components.append(SNOWFLAKE_INSTRUCTIONS)

    if include_special:
        components.append(SPECIAL_INSTRUCTIONS)

    if additional_instructions:
        components.append(additional_instructions)

    return "\n\n".join(components)
