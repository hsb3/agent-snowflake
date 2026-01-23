"""Builder for composing system prompts from components."""

from .core import CORE_INSTRUCTIONS, SAFETY_INSTRUCTIONS
from .special import SPECIAL_INSTRUCTIONS


def build_system_prompt(
    include_special: bool = False,
    additional_instructions: str | None = None,
) -> str:
    """Build the complete system prompt from components.

    Args:
        include_special: Whether to include special instructions
        additional_instructions: Optional additional instructions to append

    Returns:
        Complete system prompt string
    """
    components = [
        CORE_INSTRUCTIONS,
        SAFETY_INSTRUCTIONS,
    ]

    if include_special:
        components.append(SPECIAL_INSTRUCTIONS)

    if additional_instructions:
        components.append(additional_instructions)

    return "\n\n".join(components)


# Default system prompt
system_prompt = build_system_prompt()
