# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Test Examples - Retry Decorator Usage

This module demonstrates and tests the retry decorator functionality
for handling flaky tests.

Phase 14: Test Reliability - Retry Logic Implementation
"""

import time
from unittest.mock import Mock

import pytest
from tests.test_utils import mark_flaky, retry_on_failure


class TestRetryDecorator:
    """Test the retry_on_failure decorator."""

    def test_retry_decorator_success_first_try(self):
        """Test that retry decorator doesn't interfere with passing tests."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.1)
        def always_passes():
            nonlocal call_count
            call_count += 1
            return "success"

        result = always_passes()

        assert result == "success"
        assert call_count == 1  # Should only be called once

    def test_retry_decorator_eventually_succeeds(self):
        """Test that retry decorator retries and eventually succeeds."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.1, backoff=1.5)
        def fails_twice_then_succeeds():
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise AssertionError(f"Attempt {call_count} failed")

            return "success"

        result = fails_twice_then_succeeds()

        assert result == "success"
        assert call_count == 3  # Should be called 3 times

    def test_retry_decorator_all_attempts_fail(self):
        """Test that retry decorator raises after max attempts."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.05)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise AssertionError(f"Attempt {call_count} failed")

        with pytest.raises(AssertionError, match="Attempt 3 failed"):
            always_fails()

        assert call_count == 3  # Should try all 3 attempts

    def test_retry_decorator_with_specific_exception(self):
        """Test retry decorator with specific exception types."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.05, exceptions=(ValueError,))
        def raises_value_error_then_succeeds():
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                raise ValueError("Transient error")

            return "success"

        result = raises_value_error_then_succeeds()

        assert result == "success"
        assert call_count == 2

    def test_retry_decorator_doesnt_catch_other_exceptions(self):
        """Test that retry decorator doesn't catch unspecified exceptions."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.05, exceptions=(ValueError,))
        def raises_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("This should not be retried")

        with pytest.raises(TypeError, match="This should not be retried"):
            raises_type_error()

        assert call_count == 1  # Should not retry on TypeError


class TestMarkFlaky:
    """Test the mark_flaky convenience decorator."""

    def test_mark_flaky_basic_usage(self):
        """Test basic usage of mark_flaky decorator."""
        call_count = 0

        @mark_flaky(reason="Test is timing-dependent")
        def flaky_test():
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                raise AssertionError("Flaky failure")

            return "success"

        result = flaky_test()

        assert result == "success"
        assert call_count == 2
        assert hasattr(flaky_test, "_is_flaky")
        assert flaky_test._is_flaky is True
        assert flaky_test._flaky_reason == "Test is timing-dependent"

    def test_mark_flaky_catches_all_exceptions(self):
        """Test that mark_flaky catches all exception types."""
        call_count = 0

        @mark_flaky(reason="Catches all exceptions")
        def raises_different_exceptions():
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                raise ValueError("First failure")
            elif call_count == 2:
                raise KeyError("Second failure")

            return "success"

        result = raises_different_exceptions()

        assert result == "success"
        assert call_count == 3


class TestRealisticScenarios:
    """Test realistic scenarios where retry logic helps."""

    @mark_flaky(reason="Race condition in concurrent operations")
    def test_concurrent_resource_access(self):
        """Test accessing shared resource with potential race condition."""
        # Simulate a resource that might be locked
        resource = Mock()
        resource.is_locked = Mock(side_effect=[True, True, False])
        resource.acquire = Mock(return_value=True)

        # Try to acquire resource (might be locked initially)
        while resource.is_locked():
            time.sleep(0.01)

        result = resource.acquire()
        assert result is True

    @retry_on_failure(max_attempts=3, delay=0.1, backoff=2.0)
    def test_api_call_with_transient_errors(self):
        """Test API call that might have transient failures."""
        # Simulate API client that occasionally fails
        api_client = Mock()

        # First call fails, second succeeds
        api_client.get_data.side_effect = [
            Exception("503 Service Unavailable"),
            {"status": "ok", "data": "result"},
        ]

        try:
            result = api_client.get_data()
        except Exception:
            # Retry
            time.sleep(0.1)
            result = api_client.get_data()

        assert result["status"] == "ok"

    @mark_flaky(reason="Timing-sensitive assertion")
    def test_eventual_consistency(self):
        """Test operation that might need time to reach consistent state."""
        # Simulate eventually consistent data store
        store = Mock()
        store.read_count = 0

        def get_value():
            store.read_count += 1
            # Value becomes consistent after 2 reads
            if store.read_count >= 2:
                return "consistent_value"
            return None

        store.get.side_effect = get_value

        # Might need multiple reads to get consistent value
        value = None
        for _ in range(5):
            value = store.get()
            if value is not None:
                break
            time.sleep(0.01)

        assert value == "consistent_value"


class TestRetryLogging:
    """Test that retry attempts are logged for monitoring."""

    def test_retry_attempts_are_visible(self, capsys):
        """Test that retry attempts print helpful messages."""
        call_count = 0

        @retry_on_failure(max_attempts=2, delay=0.05)
        def fails_once():
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                raise AssertionError("First attempt fails")

            return "success"

        result = fails_once()

        # Check that retry message was printed
        captured = capsys.readouterr()
        assert "⚠️  Test 'fails_once' failed (attempt 1/2)" in captured.out
        assert "Retrying in" in captured.out
        assert result == "success"

    def test_final_failure_is_logged(self, capsys):
        """Test that final failure prints appropriate message."""

        @retry_on_failure(max_attempts=2, delay=0.05)
        def always_fails():
            raise AssertionError("Always fails")

        with pytest.raises(AssertionError):
            always_fails()

        # Check that final failure message was printed
        captured = capsys.readouterr()
        assert "❌ Test 'always_fails' failed after 2 attempts" in captured.out


class TestBackoffBehavior:
    """Test exponential backoff behavior."""

    def test_exponential_backoff_timing(self):
        """Test that delay increases exponentially."""
        delays = []

        @retry_on_failure(max_attempts=4, delay=0.1, backoff=2.0)
        def track_delays():
            delays.append(time.time())
            if len(delays) < 4:
                raise AssertionError("Force retry")
            return "success"

        time.time()
        result = track_delays()

        assert result == "success"
        assert len(delays) == 4

        # Check that delays roughly follow exponential pattern
        # Delay 1: ~0.1s, Delay 2: ~0.2s, Delay 3: ~0.4s
        # (with some tolerance for timing variations)
        if len(delays) >= 3:
            gap1 = delays[1] - delays[0]
            gap2 = delays[2] - delays[1]
            # Second gap should be roughly 2x first gap (with tolerance)
            assert 1.5 < gap2 / gap1 < 2.5


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_max_attempts_one(self):
        """Test with max_attempts=1 (no retries)."""
        call_count = 0

        @retry_on_failure(max_attempts=1, delay=0.05)
        def single_attempt():
            nonlocal call_count
            call_count += 1
            raise AssertionError("Fails")

        with pytest.raises(AssertionError):
            single_attempt()

        assert call_count == 1

    def test_zero_delay(self):
        """Test with zero delay between retries."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.0)
        def zero_delay_retry():
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                raise AssertionError("Retry")

            return "success"

        start = time.time()
        result = zero_delay_retry()
        duration = time.time() - start

        assert result == "success"
        assert duration < 0.5  # Should be very fast with no delays

    def test_large_backoff_factor(self):
        """Test with large backoff factor."""
        call_count = 0

        @retry_on_failure(max_attempts=3, delay=0.01, backoff=10.0)
        def large_backoff():
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                raise AssertionError("Retry")

            return "success"

        result = large_backoff()
        assert result == "success"

    def test_with_function_that_returns_none(self):
        """Test that retry works with functions returning None."""
        call_count = 0

        @retry_on_failure(max_attempts=2, delay=0.05)
        def returns_none():
            nonlocal call_count
            call_count += 1

            if call_count < 2:
                raise AssertionError("Retry")

            return None

        result = returns_none()
        assert result is None
        assert call_count == 2
