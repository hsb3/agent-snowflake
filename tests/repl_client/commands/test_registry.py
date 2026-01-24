"""Tests for CommandRegistry (Layer 7).

Test-driven development for the command registry system.
"""

import pytest

from repl_client.commands.registry import Command, CommandRegistry


class TestCommandRegistry:
    """Test command registration and execution."""

    def test_register_command(self):
        """Test registering a command."""
        registry = CommandRegistry()

        def test_handler(args: list[str]) -> str:
            return "test result"

        registry.register(
            name="test",
            handler=test_handler,
            description="Test command",
            syntax="test [args]",
        )

        # Verify command is registered
        commands = registry.list_commands()
        assert len(commands) == 1
        assert commands[0].name == "test"
        assert commands[0].description == "Test command"
        assert commands[0].syntax == "test [args]"

    def test_execute_registered_command(self):
        """Test executing a registered command."""
        registry = CommandRegistry()

        def echo_handler(args: list[str]) -> str:
            return " ".join(args)

        registry.register(
            name="echo", handler=echo_handler, description="Echo arguments"
        )

        # Execute command
        result = registry.execute("echo", ["hello", "world"])
        assert result == "hello world"

    def test_command_not_found_raises_error(self):
        """Test that executing unknown command raises error."""
        registry = CommandRegistry()

        with pytest.raises(ValueError, match="Unknown command: unknown"):
            registry.execute("unknown", [])

    def test_list_commands_returns_all(self):
        """Test that list_commands returns all registered commands."""
        registry = CommandRegistry()

        def handler1(args: list[str]) -> None:
            pass

        def handler2(args: list[str]) -> None:
            pass

        registry.register(name="cmd1", handler=handler1, description="First command")
        registry.register(name="cmd2", handler=handler2, description="Second command")

        commands = registry.list_commands()
        assert len(commands) == 2
        names = [cmd.name for cmd in commands]
        assert "cmd1" in names
        assert "cmd2" in names

    def test_get_command(self):
        """Test retrieving a specific command."""
        registry = CommandRegistry()

        def test_handler(args: list[str]) -> None:
            pass

        registry.register(
            name="test",
            handler=test_handler,
            description="Test command",
            syntax="test [args]",
        )

        cmd = registry.get_command("test")
        assert cmd is not None
        assert cmd.name == "test"
        assert cmd.description == "Test command"

    def test_get_command_not_found(self):
        """Test get_command returns None for unknown command."""
        registry = CommandRegistry()
        cmd = registry.get_command("unknown")
        assert cmd is None

    def test_get_help_text_generates_help(self):
        """Test that get_help_text generates formatted help."""
        registry = CommandRegistry()

        def help_handler(args: list[str]) -> None:
            pass

        def exit_handler(args: list[str]) -> None:
            pass

        registry.register(
            name="help",
            handler=help_handler,
            description="Show help message",
            syntax="help [command]",
        )
        registry.register(
            name="exit", handler=exit_handler, description="Exit the REPL"
        )

        help_text = registry.get_help_text()

        # Verify help text contains command info
        assert "help" in help_text
        assert "exit" in help_text
        assert "Show help message" in help_text
        assert "Exit the REPL" in help_text

    def test_command_dataclass(self):
        """Test Command dataclass structure."""

        def dummy_handler(args: list[str]) -> None:
            pass

        cmd = Command(
            name="test",
            handler=dummy_handler,
            description="Test description",
            syntax="test [args]",
        )

        assert cmd.name == "test"
        assert cmd.handler == dummy_handler
        assert cmd.description == "Test description"
        assert cmd.syntax == "test [args]"

    def test_command_dataclass_default_syntax(self):
        """Test Command with default empty syntax."""

        def dummy_handler(args: list[str]) -> None:
            pass

        cmd = Command(name="test", handler=dummy_handler, description="Test description")

        assert cmd.syntax == ""
