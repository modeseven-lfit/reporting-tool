# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for error handler module.

Tests the error handling infrastructure including:
- ConcurrentErrorHandler for error collection
- ErrorRecord dataclass
- ErrorSeverity classification
- with_retry decorator
- CircuitBreaker pattern
- Thread safety

Phase 7: Concurrency Refinement
"""

import threading
import time
from unittest.mock import patch

import pytest

from concurrency.error_handler import (
    CircuitBreaker,
    CircuitOpenError,
    ConcurrentErrorHandler,
    ErrorRecord,
    ErrorSeverity,
    with_retry,
)


class TestErrorSeverity:
    """Test ErrorSeverity enum."""

    def test_error_severity_values(self):
        """Test ErrorSeverity enum values."""
        assert ErrorSeverity.TRANSIENT.value == "transient"
        assert ErrorSeverity.PERMANENT.value == "permanent"
        assert ErrorSeverity.UNKNOWN.value == "unknown"


class TestErrorRecord:
    """Test ErrorRecord dataclass."""

    def test_error_record_initialization(self):
        """Test ErrorRecord initializes with required fields."""
        record = ErrorRecord(
            context="test_context",
            error_type="ValueError",
            error_message="Test error",
            severity=ErrorSeverity.TRANSIENT,
        )

        assert record.context == "test_context"
        assert record.error_type == "ValueError"
        assert record.error_message == "Test error"
        assert record.severity == ErrorSeverity.TRANSIENT
        assert record.retry_count == 0
        assert record.metadata == {}

    def test_error_record_with_metadata(self):
        """Test ErrorRecord with metadata."""
        metadata = {"repo": "test-repo", "attempt": 1}
        record = ErrorRecord(
            context="repo_analysis",
            error_type="TimeoutError",
            error_message="Connection timeout",
            severity=ErrorSeverity.TRANSIENT,
            retry_count=2,
            metadata=metadata,
        )

        assert record.retry_count == 2
        assert record.metadata == metadata

    def test_error_record_has_timestamp(self):
        """Test ErrorRecord has timestamp."""
        record = ErrorRecord(
            context="test", error_type="Error", error_message="msg", severity=ErrorSeverity.UNKNOWN
        )

        assert record.timestamp is not None


class TestConcurrentErrorHandlerInitialization:
    """Test ConcurrentErrorHandler initialization."""

    def test_default_initialization(self):
        """Test handler initializes with default logger."""
        handler = ConcurrentErrorHandler()

        assert handler.logger is not None
        assert handler._errors == []

    def test_custom_logger_initialization(self):
        """Test handler initializes with custom logger."""
        import logging

        logger = logging.getLogger("test")
        handler = ConcurrentErrorHandler(logger=logger)

        assert handler.logger == logger


class TestConcurrentErrorHandlerErrorRecording:
    """Test error recording functionality."""

    def test_record_simple_error(self):
        """Test recording a simple error."""
        handler = ConcurrentErrorHandler()
        error = ValueError("Test error")

        handler.record_error(context="test_context", error=error)

        errors = handler.get_errors()
        assert len(errors) == 1
        assert errors[0].context == "test_context"
        assert errors[0].error_type == "ValueError"
        assert errors[0].error_message == "Test error"

    def test_record_error_with_severity(self):
        """Test recording error with explicit severity."""
        handler = ConcurrentErrorHandler()
        error = RuntimeError("Runtime issue")

        handler.record_error(context="runtime", error=error, severity=ErrorSeverity.PERMANENT)

        errors = handler.get_errors()
        assert len(errors) == 1
        assert errors[0].severity == ErrorSeverity.PERMANENT

    def test_record_error_with_retry_count(self):
        """Test recording error with retry count."""
        handler = ConcurrentErrorHandler()
        error = ConnectionError("Network error")

        handler.record_error(context="network", error=error, retry_count=3)

        errors = handler.get_errors()
        assert len(errors) == 1
        assert errors[0].retry_count == 3

    def test_record_error_with_metadata(self):
        """Test recording error with metadata."""
        handler = ConcurrentErrorHandler()
        error = TimeoutError("Timeout")
        metadata = {"url": "https://example.com", "timeout": 30}

        handler.record_error(context="api_call", error=error, metadata=metadata)

        errors = handler.get_errors()
        assert len(errors) == 1
        assert errors[0].metadata == metadata

    def test_record_multiple_errors(self):
        """Test recording multiple errors."""
        handler = ConcurrentErrorHandler()

        handler.record_error("ctx1", ValueError("Error 1"))
        handler.record_error("ctx2", RuntimeError("Error 2"))
        handler.record_error("ctx3", TypeError("Error 3"))

        errors = handler.get_errors()
        assert len(errors) == 3


class TestConcurrentErrorHandlerClassification:
    """Test error severity classification."""

    def test_classify_transient_errors(self):
        """Test transient errors are classified correctly."""
        handler = ConcurrentErrorHandler()

        transient_errors = [
            TimeoutError("Timeout"),
            ConnectionError("Connection failed"),
        ]

        for error in transient_errors:
            handler.record_error("test", error)

        errors = handler.get_errors()
        for error_record in errors:
            assert error_record.severity == ErrorSeverity.TRANSIENT

    def test_classify_permanent_errors(self):
        """Test permanent errors are classified correctly."""
        handler = ConcurrentErrorHandler()

        permanent_errors = [
            ValueError("Invalid value"),
            KeyError("Missing key"),
            FileNotFoundError("File not found"),
        ]

        for error in permanent_errors:
            handler.record_error("test", error)

        errors = handler.get_errors()
        for error_record in errors:
            assert error_record.severity == ErrorSeverity.PERMANENT

    def test_classify_unknown_errors(self):
        """Test unknown errors are classified as UNKNOWN."""
        handler = ConcurrentErrorHandler()

        class CustomError(Exception):
            pass

        handler.record_error("test", CustomError("Custom"))

        errors = handler.get_errors()
        assert len(errors) == 1
        assert errors[0].severity == ErrorSeverity.UNKNOWN


class TestConcurrentErrorHandlerSummary:
    """Test error summary generation."""

    def test_summary_empty_handler(self):
        """Test summary for handler with no errors."""
        handler = ConcurrentErrorHandler()
        summary = handler.get_summary()

        assert summary["total_errors"] == 0
        assert summary["errors_by_severity"] == {}
        assert summary["errors_by_type"] == {}
        assert summary["failed_contexts"] == []
        assert summary["transient_errors"] == 0
        assert summary["permanent_errors"] == 0

    def test_summary_with_errors(self):
        """Test summary with recorded errors."""
        handler = ConcurrentErrorHandler()

        handler.record_error("repo1", ValueError("Error 1"))
        handler.record_error("repo2", TimeoutError("Error 2"))
        handler.record_error("repo3", ValueError("Error 3"))

        summary = handler.get_summary()

        assert summary["total_errors"] == 3
        assert summary["errors_by_type"]["ValueError"] == 2
        assert summary["errors_by_type"]["TimeoutError"] == 1
        assert len(summary["failed_contexts"]) == 3

    def test_summary_groups_by_severity(self):
        """Test summary groups errors by severity."""
        handler = ConcurrentErrorHandler()

        handler.record_error("ctx1", TimeoutError("Transient"))
        handler.record_error("ctx2", ValueError("Permanent"))
        handler.record_error("ctx3", ConnectionError("Transient"))

        summary = handler.get_summary()

        assert summary["transient_errors"] == 2
        assert summary["permanent_errors"] == 1

    def test_summary_groups_by_type(self):
        """Test summary groups errors by type."""
        handler = ConcurrentErrorHandler()

        handler.record_error("ctx1", ValueError("Error"))
        handler.record_error("ctx2", ValueError("Error"))
        handler.record_error("ctx3", RuntimeError("Error"))

        summary = handler.get_summary()

        assert summary["errors_by_type"]["ValueError"] == 2
        assert summary["errors_by_type"]["RuntimeError"] == 1


class TestConcurrentErrorHandlerUtilities:
    """Test utility methods."""

    def test_has_errors_initially_false(self):
        """Test has_errors returns False initially."""
        handler = ConcurrentErrorHandler()
        assert handler.has_errors() is False

    def test_has_errors_true_after_recording(self):
        """Test has_errors returns True after recording."""
        handler = ConcurrentErrorHandler()
        handler.record_error("test", ValueError("Error"))
        assert handler.has_errors() is True

    def test_clear_removes_all_errors(self):
        """Test clear removes all errors."""
        handler = ConcurrentErrorHandler()

        handler.record_error("ctx1", ValueError("Error 1"))
        handler.record_error("ctx2", RuntimeError("Error 2"))

        assert len(handler.get_errors()) == 2

        handler.clear()

        assert len(handler.get_errors()) == 0
        assert handler.has_errors() is False


class TestConcurrentErrorHandlerThreadSafety:
    """Test thread safety of error handler."""

    def test_concurrent_error_recording(self):
        """Test recording errors from multiple threads is thread-safe."""
        handler = ConcurrentErrorHandler()

        def record_errors():
            for i in range(10):
                handler.record_error(
                    f"thread_{threading.current_thread().name}_{i}", ValueError(f"Error {i}")
                )

        threads = [threading.Thread(target=record_errors) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        # Should have 50 errors (5 threads * 10 errors each)
        assert len(handler.get_errors()) == 50

    def test_concurrent_summary_access(self):
        """Test accessing summary from multiple threads is thread-safe."""
        handler = ConcurrentErrorHandler()

        # Pre-populate some errors
        for i in range(10):
            handler.record_error(f"ctx{i}", ValueError(f"Error {i}"))

        summaries = []

        def get_summary():
            for _ in range(5):
                summary = handler.get_summary()
                summaries.append(summary)

        threads = [threading.Thread(target=get_summary) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        # Should get 15 summaries without errors
        assert len(summaries) == 15


class TestWithRetryDecorator:
    """Test with_retry decorator."""

    def test_retry_succeeds_on_first_attempt(self):
        """Test function succeeds on first attempt."""
        call_count = [0]

        @with_retry(max_retries=3)
        def successful_function():
            call_count[0] += 1
            return 42

        result = successful_function()

        assert result == 42
        assert call_count[0] == 1

    def test_retry_succeeds_after_failures(self):
        """Test function succeeds after initial failures."""
        call_count = [0]

        @with_retry(max_retries=3, initial_delay=0.01)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("Transient error")
            return 42

        result = flaky_function()

        assert result == 42
        assert call_count[0] == 3

    def test_retry_exhausted_raises_exception(self):
        """Test all retries exhausted raises last exception."""
        call_count = [0]

        @with_retry(max_retries=2, initial_delay=0.01)
        def failing_function():
            call_count[0] += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            failing_function()

        # Should be called 3 times (initial + 2 retries)
        assert call_count[0] == 3

    def test_retry_with_custom_exceptions(self):
        """Test retry only on specific exceptions."""

        @with_retry(max_retries=2, retry_on=(ConnectionError,), initial_delay=0.01)
        def selective_retry():
            raise ValueError("Not retryable")

        # Should not retry ValueError
        with pytest.raises(ValueError):
            selective_retry()

    def test_retry_with_error_handler(self):
        """Test retry integrates with error handler."""
        handler = ConcurrentErrorHandler()
        call_count = [0]

        @with_retry(max_retries=2, error_handler=handler, context="test", initial_delay=0.01)
        def failing_function():
            call_count[0] += 1
            raise ConnectionError("Network error")

        with pytest.raises(ConnectionError):
            failing_function()

        # Should have recorded 3 errors (initial + 2 retries)
        assert len(handler.get_errors()) == 3

    @patch("time.sleep")
    def test_retry_uses_exponential_backoff(self, mock_sleep):
        """Test retry uses exponential backoff."""
        call_count = [0]

        @with_retry(max_retries=3, backoff_factor=2.0, initial_delay=1.0)
        def failing_function():
            call_count[0] += 1
            raise ConnectionError("Error")

        with pytest.raises(ConnectionError):
            failing_function()

        # Should sleep with exponential backoff: 1.0, 2.0, 4.0
        assert mock_sleep.call_count == 3
        sleep_args = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_args == [1.0, 2.0, 4.0]


class TestCircuitBreaker:
    """Test CircuitBreaker pattern."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes correctly."""
        breaker = CircuitBreaker(failure_threshold=5, timeout=60.0)

        assert breaker.failure_threshold == 5
        assert breaker.timeout == 60.0
        assert breaker.get_state() == "CLOSED"

    def test_circuit_closed_allows_calls(self):
        """Test CLOSED circuit allows function calls."""
        breaker = CircuitBreaker()

        def successful_function():
            return 42

        result = breaker.call(successful_function)
        assert result == 42
        assert breaker.get_state() == "CLOSED"

    def test_circuit_opens_after_threshold_failures(self):
        """Test circuit opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=60.0)

        def failing_function():
            raise ValueError("Error")

        # Fail 3 times to reach threshold
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        # Circuit should now be open
        assert breaker.get_state() == "OPEN"

    def test_open_circuit_raises_immediately(self):
        """Test OPEN circuit raises without calling function."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=60.0)
        call_count = [0]

        def failing_function():
            call_count[0] += 1
            raise ValueError("Error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.get_state() == "OPEN"

        # Now calls should fail immediately
        with pytest.raises(CircuitOpenError):
            breaker.call(failing_function)

        # Function should not have been called again
        assert call_count[0] == 2

    def test_circuit_transitions_to_half_open(self):
        """Test circuit transitions to HALF_OPEN after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)

        def failing_function():
            raise ValueError("Error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.get_state() == "OPEN"

        # Wait for timeout
        time.sleep(0.15)

        # Next call should transition to HALF_OPEN
        with pytest.raises(ValueError):
            breaker.call(failing_function)

    def test_half_open_closes_on_success(self):
        """Test HALF_OPEN circuit closes on successful call."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)
        call_count = [0]

        def sometimes_failing():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise ValueError("Error")
            return 42

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(sometimes_failing)

        assert breaker.get_state() == "OPEN"

        # Wait for timeout
        time.sleep(0.15)

        # Successful call should close the circuit
        result = breaker.call(sometimes_failing)
        assert result == 42
        assert breaker.get_state() == "CLOSED"

    def test_circuit_reset(self):
        """Test manual circuit reset."""
        breaker = CircuitBreaker(failure_threshold=2)

        def failing_function():
            raise ValueError("Error")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.get_state() == "OPEN"

        # Reset manually
        breaker.reset()

        assert breaker.get_state() == "CLOSED"
        assert breaker.get_failure_count() == 0

    def test_circuit_tracks_failure_count(self):
        """Test circuit breaker tracks failure count."""
        breaker = CircuitBreaker(failure_threshold=5)

        def failing_function():
            raise ValueError("Error")

        # Fail 3 times (below threshold)
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_function)

        assert breaker.get_failure_count() == 3
        assert breaker.get_state() == "CLOSED"  # Still closed

    def test_successful_call_resets_failure_count(self):
        """Test successful call resets failure count."""
        breaker = CircuitBreaker(failure_threshold=5)
        call_count = [0]

        def sometimes_failing():
            call_count[0] += 1
            if call_count[0] <= 2:
                raise ValueError("Error")
            return 42

        # Fail twice
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(sometimes_failing)

        assert breaker.get_failure_count() == 2

        # Succeed once
        result = breaker.call(sometimes_failing)
        assert result == 42

        # Failure count should be reset
        assert breaker.get_failure_count() == 0
