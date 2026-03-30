"""Tests for ChatInput widget with history and completion support."""

from __future__ import annotations

from pathlib import Path

import pytest

from repl_client.tui.widgets.history import HistoryManager
from repl_client.tui.widgets.input import ChatInput, ChatTextArea


class TestHistoryManager:
    """Test the history manager."""

    def test_init_creates_empty_history(self, tmp_path: Path) -> None:
        """Test initialization with non-existent file."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)
        assert manager._entries == []
        assert manager._current_index == -1

    def test_add_entry(self, tmp_path: Path) -> None:
        """Test adding entries to history."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)

        manager.add("first command")
        assert len(manager._entries) == 1
        assert manager._entries[0] == "first command"

        manager.add("second command")
        assert len(manager._entries) == 2
        assert manager._entries[1] == "second command"

    def test_skip_empty_entries(self, tmp_path: Path) -> None:
        """Test that empty entries are skipped."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)

        manager.add("")
        manager.add("   ")
        assert len(manager._entries) == 0

    def test_skip_slash_commands(self, tmp_path: Path) -> None:
        """Test that slash commands are skipped."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)

        manager.add("/help")
        manager.add("/clear")
        assert len(manager._entries) == 0

    def test_skip_duplicate_consecutive(self, tmp_path: Path) -> None:
        """Test that consecutive duplicates are skipped."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)

        manager.add("command")
        manager.add("command")
        assert len(manager._entries) == 1

    def test_get_previous(self, tmp_path: Path) -> None:
        """Test navigating to previous entry."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)

        manager.add("first")
        manager.add("second")
        manager.add("third")

        # First previous should return "third"
        result = manager.get_previous("")
        assert result == "third"

        # Second previous should return "second"
        result = manager.get_previous("")
        assert result == "second"

        # Third previous should return "first"
        result = manager.get_previous("")
        assert result == "first"

        # No more previous
        result = manager.get_previous("")
        assert result is None

    def test_get_next(self, tmp_path: Path) -> None:
        """Test navigating to next entry."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)

        manager.add("first")
        manager.add("second")
        manager.add("third")

        # Navigate to previous entries
        manager.get_previous("")
        manager.get_previous("")

        # Now navigate forward
        result = manager.get_next()
        assert result == "third"

        # Next should return temp input
        result = manager.get_next()
        assert result == ""

    def test_temp_input_saved(self, tmp_path: Path) -> None:
        """Test that current input is saved during navigation."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)

        manager.add("old command")

        # Start navigating with current input
        result = manager.get_previous("my partial input")
        assert result == "old command"

        # Navigate back should restore temp input
        result = manager.get_next()
        assert result == "my partial input"

    def test_prefix_search(self, tmp_path: Path) -> None:
        """Test prefix filtering in history."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)

        manager.add("git status")
        manager.add("ls -la")
        manager.add("git commit")

        # Search for "git" prefix
        result = manager.get_previous("", prefix="git")
        assert result == "git commit"

        result = manager.get_previous("", prefix="git")
        assert result == "git status"

    def test_reset_navigation(self, tmp_path: Path) -> None:
        """Test resetting navigation state."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file)

        manager.add("command")
        manager.get_previous("temp")

        manager.reset_navigation()
        assert manager._current_index == -1
        assert manager._temp_input == ""

    def test_persistence(self, tmp_path: Path) -> None:
        """Test that history is persisted to file."""
        history_file = tmp_path / "history.jsonl"

        # Add entries with first manager
        manager1 = HistoryManager(history_file)
        manager1.add("first")
        manager1.add("second")

        # Load with new manager
        manager2 = HistoryManager(history_file)
        assert len(manager2._entries) == 2
        assert manager2._entries[0] == "first"
        assert manager2._entries[1] == "second"

    def test_max_entries(self, tmp_path: Path) -> None:
        """Test that history respects max entries."""
        history_file = tmp_path / "history.jsonl"
        manager = HistoryManager(history_file, max_entries=3)

        for i in range(10):
            manager.add(f"command {i}")

        # Should only keep last 3
        assert len(manager._entries) <= manager.max_entries * 2


class TestChatInput:
    """Test the ChatInput widget."""

    @pytest.fixture
    def app_with_input(self, tmp_path: Path):
        """Create a test app with ChatInput."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield ChatInput(history_file=tmp_path / "history.jsonl")

        return TestApp()

    async def test_initialization(self, app_with_input) -> None:
        """Test widget initialization."""
        async with app_with_input.run_test():
            chat_input = app_with_input.query_one(ChatInput)
            assert chat_input is not None
            assert chat_input.mode == "normal"

    async def test_submit_message(self, tmp_path: Path) -> None:
        """Test that submitted text emits message."""
        from textual.app import App

        messages = []

        class TestApp(App):
            def compose(self):
                yield ChatInput(history_file=tmp_path / "history.jsonl")

            def on_chat_input_submitted(self, msg: ChatInput.Submitted):
                messages.append(msg)

        app = TestApp()
        async with app.run_test() as pilot:
            chat_input = app.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            # Type text and submit
            text_area.text = "hello world"
            await pilot.press("enter")
            await pilot.pause(0.1)

            assert len(messages) == 1
            assert messages[0].value == "hello world"
            assert messages[0].mode == "normal"

    async def test_command_mode_detection(self, app_with_input) -> None:
        """Test that command mode is detected."""
        async with app_with_input.run_test() as pilot:
            chat_input = app_with_input.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            text_area.text = "/help"
            await pilot.pause(0.1)

            assert chat_input.mode == "command"

    async def test_bash_mode_detection(self, app_with_input) -> None:
        """Test that bash mode is detected."""
        async with app_with_input.run_test() as pilot:
            chat_input = app_with_input.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            text_area.text = "!ls -la"
            await pilot.pause(0.1)

            assert chat_input.mode == "bash"

    async def test_multiline_input(self, app_with_input) -> None:
        """Test multiline input with Ctrl+J."""
        async with app_with_input.run_test() as pilot:
            chat_input = app_with_input.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            # Type text, press ctrl+j for newline, type more
            await pilot.press("l", "i", "n", "e", "1")
            await pilot.press("ctrl+j")
            await pilot.press("l", "i", "n", "e", "2")
            await pilot.pause(0.1)

            assert "line1\nline2" in text_area.text

    async def test_clear_input(self, app_with_input) -> None:
        """Test clearing input after submit."""
        async with app_with_input.run_test() as pilot:
            chat_input = app_with_input.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            text_area.text = "test message"
            await pilot.press("enter")
            await pilot.pause(0.1)

            assert text_area.text == ""

    async def test_history_added_on_submit(self, app_with_input) -> None:
        """Test that submissions are added to history."""
        async with app_with_input.run_test() as pilot:
            chat_input = app_with_input.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            text_area.text = "first command"
            await pilot.press("enter")
            await pilot.pause(0.1)

            assert len(chat_input._history._entries) == 1
            assert chat_input._history._entries[0] == "first command"

    async def test_history_navigation_up(self, app_with_input) -> None:
        """Test navigating history with up arrow."""
        async with app_with_input.run_test() as pilot:
            chat_input = app_with_input.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            # Add some history
            text_area.text = "first"
            await pilot.press("enter")
            await pilot.pause(0.1)

            text_area.text = "second"
            await pilot.press("enter")
            await pilot.pause(0.1)

            # Navigate up (should get "second")
            await pilot.press("up")
            await pilot.pause(0.1)
            assert text_area.text == "second"

            # Navigate up again (should get "first")
            await pilot.press("up")
            await pilot.pause(0.1)
            assert text_area.text == "first"

    async def test_history_navigation_down(self, app_with_input) -> None:
        """Test navigating history with down arrow."""
        async with app_with_input.run_test() as pilot:
            chat_input = app_with_input.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            # Add history
            text_area.text = "command"
            await pilot.press("enter")
            await pilot.pause(0.1)

            # Navigate up
            await pilot.press("up")
            await pilot.pause(0.1)

            # Navigate down (should clear)
            await pilot.press("down")
            await pilot.pause(0.1)
            assert text_area.text == ""

    async def test_focus_input(self, app_with_input) -> None:
        """Test focusing the input widget."""
        async with app_with_input.run_test() as pilot:
            chat_input = app_with_input.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            chat_input.focus_input()
            await pilot.pause(0.1)

            assert text_area.has_focus

    async def test_value_property(self, app_with_input) -> None:
        """Test value property getter/setter."""
        async with app_with_input.run_test():
            chat_input = app_with_input.query_one(ChatInput)

            chat_input.value = "test value"
            assert chat_input.value == "test value"

    async def test_mode_changed_updates_prompt(self, tmp_path: Path) -> None:
        """Test that mode changes update the prompt indicator."""
        from textual.app import App

        class TestApp(App):
            def compose(self):
                yield ChatInput(history_file=tmp_path / "history.jsonl")

        app = TestApp()
        async with app.run_test() as pilot:
            chat_input = app.query_one(ChatInput)
            text_area = chat_input.query_one(ChatTextArea)

            # Default mode is normal
            assert chat_input.mode == "normal"

            # Type a command prefix
            text_area.text = "/command"
            await pilot.pause(0.1)

            # Mode should change to command
            assert chat_input.mode == "command"

            # Switch to bash mode
            text_area.text = "!ls"
            await pilot.pause(0.1)

            assert chat_input.mode == "bash"

            # Back to normal
            text_area.text = "hello"
            await pilot.pause(0.1)

            assert chat_input.mode == "normal"
