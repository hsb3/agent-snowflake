"""Tests for LoadingWidget."""

import asyncio

import pytest
from textual.app import App
from textual.widgets import Static

from repl_client.tui.widgets import LoadingWidget


class LoadingTestApp(App):
    """Test app for LoadingWidget."""

    def compose(self):
        yield LoadingWidget("Processing")


@pytest.fixture
async def loading_widget():
    """Create a LoadingWidget for testing."""
    app = LoadingTestApp()
    async with app.run_test() as pilot:
        yield pilot.app.query_one(LoadingWidget)


class TestLoadingWidgetAnimation:
    """Test LoadingWidget animation behavior."""

    async def test_spinner_frames_cycle(self, loading_widget):
        """Test spinner cycles through braille frames."""
        # Get spinner widget
        spinner = loading_widget.query_one(".loading-spinner", Static)

        # Store initial frame
        initial_frame = spinner.content

        # Wait for animation to update (100ms interval)
        await asyncio.sleep(0.15)

        # Frame should have changed
        new_frame = spinner.content
        assert new_frame != initial_frame

    async def test_spinner_has_braille_characters(self, loading_widget):
        """Test spinner uses braille characters."""
        spinner = loading_widget.query_one(".loading-spinner", Static)

        # Check that spinner contains braille (unicode range U+2800-U+28FF)
        # The frames are wrapped in rich markup, so we check the raw content
        await asyncio.sleep(0.05)
        frame_text = str(spinner.content)
        has_braille = any(
            "\u2800" <= char <= "\u28ff" for char in frame_text if isinstance(char, str)
        )
        assert has_braille or "⠋" in frame_text or "⠙" in frame_text

    async def test_elapsed_time_updates(self, loading_widget):
        """Test elapsed time increments."""
        hint = loading_widget.query_one(".loading-hint", Static)

        # Initial time should be 0s
        initial_text = hint.content
        assert "0s" in str(initial_text)

        # Wait for at least 1 second
        await asyncio.sleep(1.1)

        # Time should have incremented
        updated_text = hint.content
        assert "1s" in str(updated_text) or "2s" in str(updated_text)

    async def test_animation_interval_is_100ms(self, loading_widget):
        """Test animation updates approximately every 100ms."""
        spinner = loading_widget.query_one(".loading-spinner", Static)

        frames_seen = []
        for _ in range(3):
            await asyncio.sleep(0.11)
            frames_seen.append(str(spinner.content))

        # Should have at least 2 different frames in 3 checks
        unique_frames = len(set(frames_seen))
        assert unique_frames >= 2


class TestLoadingWidgetStatus:
    """Test LoadingWidget status text."""

    async def test_initial_status_displayed(self, loading_widget):
        """Test initial status message is displayed."""
        status = loading_widget.query_one(".loading-status", Static)
        assert "Processing" in status.content

    async def test_set_status_updates_text(self, loading_widget):
        """Test set_status method updates displayed text."""
        loading_widget.set_status("Analyzing")
        await asyncio.sleep(0.05)

        status = loading_widget.query_one(".loading-status", Static)
        assert "Analyzing" in status.content

    async def test_status_has_ellipsis(self, loading_widget):
        """Test status text includes ellipsis."""
        status = loading_widget.query_one(".loading-status", Static)
        assert "..." in status.content


class TestLoadingWidgetPauseResume:
    """Test LoadingWidget pause/resume functionality."""

    async def test_pause_stops_spinner_animation(self, loading_widget):
        """Test pause stops the spinner from animating."""
        loading_widget.pause("Waiting")
        await asyncio.sleep(0.05)

        spinner = loading_widget.query_one(".loading-spinner", Static)
        paused_frame = str(spinner.content)

        # Wait for what would be several animation frames
        await asyncio.sleep(0.3)

        # Frame should not have changed (paused shows ⏸)
        assert str(spinner.content) == paused_frame
        assert "⏸" in paused_frame

    async def test_pause_updates_status_text(self, loading_widget):
        """Test pause updates status message."""
        loading_widget.pause("Awaiting decision")
        await asyncio.sleep(0.05)

        status = loading_widget.query_one(".loading-status", Static)
        assert "Awaiting decision" in status.content

    async def test_pause_shows_paused_elapsed_time(self, loading_widget):
        """Test pause shows elapsed time when paused."""
        # Wait a bit before pausing
        await asyncio.sleep(1.1)

        loading_widget.pause("Waiting")
        await asyncio.sleep(0.05)

        hint = loading_widget.query_one(".loading-hint", Static)
        hint_text = str(hint.content)
        assert "paused" in hint_text.lower()
        assert "s)" in hint_text

    async def test_resume_restarts_animation(self, loading_widget):
        """Test resume restarts spinner animation."""
        loading_widget.pause("Waiting")
        await asyncio.sleep(0.15)

        loading_widget.resume()
        await asyncio.sleep(0.05)

        spinner = loading_widget.query_one(".loading-spinner", Static)
        str(spinner.content)

        # Wait for animation
        await asyncio.sleep(0.15)

        frame_after = str(spinner.content)
        # Should be animating again (not showing pause symbol)
        assert "⏸" not in frame_after

    async def test_resume_resets_status(self, loading_widget):
        """Test resume resets status to default."""
        loading_widget.pause("Custom status")
        await asyncio.sleep(0.05)

        loading_widget.resume()
        await asyncio.sleep(0.05)

        status = loading_widget.query_one(".loading-status", Static)
        assert "Thinking" in status.content


class TestLoadingWidgetLayout:
    """Test LoadingWidget layout and composition."""

    async def test_all_components_present(self, loading_widget):
        """Test all widget components are present."""
        assert loading_widget.query_one(".loading-spinner")
        assert loading_widget.query_one(".loading-status")
        assert loading_widget.query_one(".loading-hint")

    async def test_hint_shows_interrupt_text(self, loading_widget):
        """Test hint shows interrupt instruction."""
        hint = loading_widget.query_one(".loading-hint", Static)
        assert "esc" in str(hint.content).lower() or "interrupt" in str(hint.content).lower()
