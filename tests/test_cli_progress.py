# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for CLI Progress Module

Tests for progress indicators, operation feedback, and time estimation.

Phase 9: CLI & UX Improvements
"""

import io
import unittest
from contextlib import redirect_stderr
from unittest.mock import MagicMock, patch

from cli.progress import (
    TQDM_AVAILABLE,
    OperationFeedback,
    ProgressIndicator,
    estimate_time_remaining,
    format_count,
    progress_bar,
)


class TestProgressIndicator(unittest.TestCase):
    """Test ProgressIndicator class."""

    def test_init_with_defaults(self):
        """Test ProgressIndicator initialization with defaults."""
        progress = ProgressIndicator()
        self.assertIsNone(progress.total)
        self.assertEqual(progress.desc, "Progress")
        self.assertFalse(progress.disable)
        self.assertEqual(progress.unit, "item")
        self.assertTrue(progress.leave)
        self.assertEqual(progress.current, 0)

    def test_init_with_custom_values(self):
        """Test ProgressIndicator initialization with custom values."""
        progress = ProgressIndicator(
            total=100, desc="Processing", disable=True, unit="repo", leave=False
        )
        self.assertEqual(progress.total, 100)
        self.assertEqual(progress.desc, "Processing")
        self.assertTrue(progress.disable)
        self.assertEqual(progress.unit, "repo")
        self.assertFalse(progress.leave)

    def test_context_manager_disabled(self):
        """Test context manager when disabled."""
        stderr = io.StringIO()
        with redirect_stderr(stderr), ProgressIndicator(total=10, disable=True) as progress:
            progress.update(5)
            progress.update(5)

        # No output when disabled
        output = stderr.getvalue()
        self.assertEqual(output, "")

    @patch("cli.progress.TQDM_AVAILABLE", False)
    def test_context_manager_without_tqdm(self):
        """Test context manager without tqdm (simple mode)."""
        stderr = io.StringIO()
        with redirect_stderr(stderr), ProgressIndicator(total=10, desc="Test") as progress:
            progress.update(5)
            progress.update(5)

        output = stderr.getvalue()
        self.assertIn("Test:", output)
        # Should show progress updates
        self.assertTrue(len(output) > 0)

    @patch("cli.progress.TQDM_AVAILABLE", True)
    @patch("cli.progress.tqdm")
    def test_context_manager_with_tqdm(self, mock_tqdm_class):
        """Test context manager with tqdm available."""
        mock_tqdm = MagicMock()
        mock_tqdm_class.return_value = mock_tqdm

        with ProgressIndicator(total=10, desc="Test") as progress:
            progress.update(5)
            progress.update(3)

        # tqdm should be created
        mock_tqdm_class.assert_called_once()

        # Updates should be passed to tqdm
        self.assertEqual(mock_tqdm.update.call_count, 2)
        mock_tqdm.update.assert_any_call(5)
        mock_tqdm.update.assert_any_call(3)

        # Should close tqdm on exit
        mock_tqdm.close.assert_called_once()

    def test_update(self):
        """Test update method."""
        progress = ProgressIndicator(total=100, disable=True)
        progress.current = 0

        progress.update(10)
        self.assertEqual(progress.current, 10)

        progress.update(5)
        self.assertEqual(progress.current, 15)

        progress.update()  # Default increment of 1
        self.assertEqual(progress.current, 16)

    def test_set_description(self):
        """Test set_description method."""
        progress = ProgressIndicator(total=100, desc="Original", disable=True)

        progress.set_description("Updated")
        self.assertEqual(progress.desc, "Updated")

    @patch("cli.progress.TQDM_AVAILABLE", True)
    @patch("cli.progress.tqdm")
    def test_set_description_with_tqdm(self, mock_tqdm_class):
        """Test set_description updates tqdm."""
        mock_tqdm = MagicMock()
        mock_tqdm_class.return_value = mock_tqdm

        with ProgressIndicator(total=10, desc="Test") as progress:
            progress.set_description("Updated")

        mock_tqdm.set_description.assert_called_with("Updated")

    @patch("cli.progress.TQDM_AVAILABLE", True)
    @patch("cli.progress.tqdm")
    def test_write_with_tqdm(self, mock_tqdm_class):
        """Test write method with tqdm."""
        mock_tqdm = MagicMock()
        mock_tqdm_class.return_value = mock_tqdm

        with ProgressIndicator(total=10) as progress:
            progress.write("Test message")

        mock_tqdm.write.assert_called_once()


class TestOperationFeedback(unittest.TestCase):
    """Test OperationFeedback class."""

    def test_init(self):
        """Test OperationFeedback initialization."""
        feedback = OperationFeedback()
        self.assertFalse(feedback.quiet)

        feedback_quiet = OperationFeedback(quiet=True)
        self.assertTrue(feedback_quiet.quiet)

    def test_start_normal_mode(self):
        """Test start message in normal mode."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=False)

        with redirect_stderr(stderr):
            feedback.start("Processing")

        output = stderr.getvalue()
        self.assertIn("🚀", output)
        self.assertIn("Processing", output)

    def test_start_quiet_mode(self):
        """Test start message suppressed in quiet mode."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=True)

        with redirect_stderr(stderr):
            feedback.start("Processing")

        output = stderr.getvalue()
        self.assertEqual(output, "")

    def test_info_normal_mode(self):
        """Test info message in normal mode."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=False)

        with redirect_stderr(stderr):
            feedback.info("Information")

        output = stderr.getvalue()
        self.assertIn("ℹ️", output)
        self.assertIn("Information", output)

    def test_info_quiet_mode(self):
        """Test info message suppressed in quiet mode."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=True)

        with redirect_stderr(stderr):
            feedback.info("Information")

        output = stderr.getvalue()
        self.assertEqual(output, "")

    def test_success_normal_mode(self):
        """Test success message in normal mode."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=False)

        with redirect_stderr(stderr):
            feedback.success("Completed")

        output = stderr.getvalue()
        self.assertIn("✅", output)
        self.assertIn("Completed", output)

    def test_warning_always_shown(self):
        """Test warning shown even in quiet mode."""
        stderr_normal = io.StringIO()
        feedback_normal = OperationFeedback(quiet=False)

        with redirect_stderr(stderr_normal):
            feedback_normal.warning("Warning message")

        stderr_quiet = io.StringIO()
        feedback_quiet = OperationFeedback(quiet=True)

        with redirect_stderr(stderr_quiet):
            feedback_quiet.warning("Warning message")

        # Both should show warning
        self.assertIn("⚠️", stderr_normal.getvalue())
        self.assertIn("⚠️", stderr_quiet.getvalue())

    def test_error_always_shown(self):
        """Test error shown even in quiet mode."""
        stderr_normal = io.StringIO()
        feedback_normal = OperationFeedback(quiet=False)

        with redirect_stderr(stderr_normal):
            feedback_normal.error("Error message")

        stderr_quiet = io.StringIO()
        feedback_quiet = OperationFeedback(quiet=True)

        with redirect_stderr(stderr_quiet):
            feedback_quiet.error("Error message")

        # Both should show error
        self.assertIn("❌", stderr_normal.getvalue())
        self.assertIn("❌", stderr_quiet.getvalue())

    def test_step(self):
        """Test step message."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=False)

        with redirect_stderr(stderr):
            feedback.step(2, 5, "Processing data")

        output = stderr.getvalue()
        self.assertIn("📍", output)
        self.assertIn("Step 2/5", output)
        self.assertIn("Processing data", output)

    def test_discovery(self):
        """Test discovery message."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=False)

        with redirect_stderr(stderr):
            feedback.discovery("Finding repositories")

        output = stderr.getvalue()
        self.assertIn("🔍", output)
        self.assertIn("Finding repositories", output)

    def test_processing(self):
        """Test processing message."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=False)

        with redirect_stderr(stderr):
            feedback.processing("Analyzing")

        output = stderr.getvalue()
        self.assertIn("⚙️", output)
        self.assertIn("Analyzing", output)

    def test_writing(self):
        """Test writing message."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=False)

        with redirect_stderr(stderr):
            feedback.writing("Saving report")

        output = stderr.getvalue()
        self.assertIn("💾", output)
        self.assertIn("Saving report", output)

    def test_analyzing(self):
        """Test analyzing message."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=False)

        with redirect_stderr(stderr):
            feedback.analyzing("Repository metrics")

        output = stderr.getvalue()
        self.assertIn("📊", output)
        self.assertIn("Repository metrics", output)


class TestProgressBarContextManager(unittest.TestCase):
    """Test progress_bar context manager."""

    @patch("cli.progress.TQDM_AVAILABLE", False)
    def test_with_manual_total(self):
        """Test progress_bar with manual total."""
        stderr = io.StringIO()
        with redirect_stderr(stderr), progress_bar(total=5, desc="Test", disable=False) as pbar:
            for _i in range(5):
                pbar.update(1)

        # Should show progress
        output = stderr.getvalue()
        self.assertIn("Test:", output)

    def test_disabled(self):
        """Test progress_bar when disabled."""
        stderr = io.StringIO()
        with redirect_stderr(stderr), progress_bar(total=5, disable=True) as pbar:
            for _i in range(5):
                pbar.update(1)

        # No output when disabled
        self.assertEqual(stderr.getvalue(), "")


class TestEstimateTimeRemaining(unittest.TestCase):
    """Test estimate_time_remaining function."""

    def test_zero_current(self):
        """Test with zero items completed."""
        result = estimate_time_remaining(0, 100, 10.0)
        self.assertEqual(result, "unknown")

    def test_zero_total(self):
        """Test with zero total."""
        result = estimate_time_remaining(50, 0, 10.0)
        self.assertEqual(result, "unknown")

    def test_seconds_only(self):
        """Test estimate in seconds."""
        # 50 items in 10 seconds = 5 items/sec
        # 50 remaining = 10 seconds
        result = estimate_time_remaining(50, 100, 10.0)
        self.assertEqual(result, "10s")

    def test_minutes_and_seconds(self):
        """Test estimate in minutes and seconds."""
        # 10 items in 60 seconds = 0.1667 items/sec
        # 90 remaining = 540 seconds = 9m 0s
        result = estimate_time_remaining(10, 100, 60.0)
        self.assertIn("m", result)
        self.assertIn("s", result)

    def test_hours_and_minutes(self):
        """Test estimate in hours and minutes."""
        # 1 item in 3600 seconds = 0.000278 items/sec
        # 99 remaining = 356400 seconds = 99h 0m
        result = estimate_time_remaining(1, 100, 3600.0)
        self.assertIn("h", result)
        self.assertIn("m", result)


class TestFormatCount(unittest.TestCase):
    """Test format_count function."""

    def test_singular_with_one(self):
        """Test singular form with count of 1."""
        result = format_count(1, "repository")
        self.assertEqual(result, "1 repository")

    def test_plural_with_zero(self):
        """Test plural form with count of 0."""
        result = format_count(0, "repository")
        self.assertEqual(result, "0 repositories")

    def test_plural_with_multiple(self):
        """Test plural form with multiple items."""
        result = format_count(5, "repository")
        self.assertEqual(result, "5 repositories")

    def test_custom_plural(self):
        """Test with custom plural form."""
        result = format_count(1, "entry", "entries")
        self.assertEqual(result, "1 entry")

        result = format_count(2, "entry", "entries")
        self.assertEqual(result, "2 entries")

    def test_irregular_plural(self):
        """Test with irregular plural."""
        result = format_count(1, "person", "people")
        self.assertEqual(result, "1 person")

        result = format_count(3, "person", "people")
        self.assertEqual(result, "3 people")


class TestTqdmAvailability(unittest.TestCase):
    """Test TQDM_AVAILABLE flag."""

    def test_tqdm_available_is_boolean(self):
        """Test that TQDM_AVAILABLE is a boolean."""
        self.assertIsInstance(TQDM_AVAILABLE, bool)

    def test_tqdm_availability_matches_import(self):
        """Test that TQDM_AVAILABLE matches actual import ability."""
        try:
            import tqdm  # noqa: F401

            expected = True
        except ImportError:
            expected = False

        self.assertEqual(TQDM_AVAILABLE, expected)


class TestProgressIntegration(unittest.TestCase):
    """Integration tests for progress indicators."""

    @patch("cli.progress.TQDM_AVAILABLE", False)
    def test_sequential_progress(self):
        """Test progress with sequential operations."""
        items = list(range(10))
        processed = []

        stderr = io.StringIO()
        with (
            redirect_stderr(stderr),
            ProgressIndicator(total=len(items), desc="Sequential") as progress,
        ):
            for item in items:
                processed.append(item * 2)
                progress.update(1)

        self.assertEqual(len(processed), 10)
        output = stderr.getvalue()
        self.assertIn("Sequential:", output)

    def test_nested_feedback(self):
        """Test nested operation feedback."""
        stderr = io.StringIO()
        feedback = OperationFeedback(quiet=False)

        with redirect_stderr(stderr):
            feedback.start("Main operation")
            feedback.step(1, 3, "First step")
            feedback.step(2, 3, "Second step")
            feedback.step(3, 3, "Third step")
            feedback.success("Complete")

        output = stderr.getvalue()
        self.assertIn("Main operation", output)
        self.assertIn("Step 1/3", output)
        self.assertIn("Step 2/3", output)
        self.assertIn("Step 3/3", output)
        self.assertIn("Complete", output)


if __name__ == "__main__":
    unittest.main()
