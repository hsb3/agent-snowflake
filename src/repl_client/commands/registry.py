"""Command registry for REPL (Layer 7).

Provides command registration and routing using the registry pattern.
Similar to agent0's command system.
"""

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Command:
    """Command definition.

    Attributes:
        name: Command name (e.g., "help", "exit")
        handler: Callable that handles the command
        description: Human-readable description
        syntax: Optional syntax help (e.g., "help [command]")
    """

    name: str
    handler: Callable[[list[str]], Any]
    description: str
    syntax: str = ""


class CommandRegistry:
    """Registry for REPL commands.

    Manages command registration, lookup, and execution.
    Uses eager registration pattern - all commands registered at startup.
    """

    def __init__(self):
        """Initialize empty registry."""
        self._commands: dict[str, Command] = {}

    def register(
        self,
        name: str,
        handler: Callable[[list[str]], Any],
        description: str,
        syntax: str = "",
    ) -> None:
        """Register a command handler.

        Args:
            name: Command name (without leading /)
            handler: Function to handle command
            description: Human-readable description
            syntax: Optional syntax help
        """
        cmd = Command(name=name, handler=handler, description=description, syntax=syntax)
        self._commands[name] = cmd

    def execute(self, name: str, args: list[str]) -> Any:
        """Execute a registered command.

        Args:
            name: Command name (without leading /)
            args: Command arguments

        Returns:
            Command handler return value

        Raises:
            ValueError: If command not found
        """
        cmd = self._commands.get(name)
        if cmd is None:
            raise ValueError(f"Unknown command: {name}")
        return cmd.handler(args)

    def get_command(self, name: str) -> Command | None:
        """Get command by name.

        Args:
            name: Command name

        Returns:
            Command if found, None otherwise
        """
        return self._commands.get(name)

    def list_commands(self) -> list[Command]:
        """Get all registered commands.

        Returns:
            List of all Command objects
        """
        return list(self._commands.values())

    def get_help_text(self) -> str:
        """Generate help text for all commands.

        Returns:
            Formatted help text showing all commands
        """
        if not self._commands:
            return "No commands registered."

        lines = ["Available commands:", ""]
        for cmd in sorted(self._commands.values(), key=lambda c: c.name):
            syntax = cmd.syntax if cmd.syntax else cmd.name
            lines.append(f"  /{syntax}")
            lines.append(f"    {cmd.description}")
            lines.append("")

        return "\n".join(lines)
