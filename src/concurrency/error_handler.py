# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Error Handling for Concurrent Operations.

Provides structured error collection, retry logic with exponential backoff,
and circuit breaker pattern for failing operations.

Phase 7: Concurrency Refinement
"""

import logging
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type


class ErrorSeverity(Enum):
    """Severity levels for errors."""

    TRANSIENT = "transient"     # Temporary error, retry may succeed
    PERMANENT = "permanent"     # Permanent error, retry will fail
    UNKNOWN = "unknown"         # Unknown error type


@dataclass
class ErrorRecord:
    """Record of an error that occurred during concurrent execution."""

    context: str                    # Context where error occurred (e.g., repo name)
    error_type: str                 # Error class name
    error_message: str              # Error message
    severity: ErrorSeverity         # Error severity
    timestamp: datetime = field(default_factory=datetime.now)
    traceback: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConcurrentErrorHandler:
    """
    Thread-safe error collection and analysis for concurrent operations.

    Collects errors from multiple workers, classifies severity, and provides
    error summaries for reporting and debugging.

    Example:
        >>> handler = ConcurrentErrorHandler()
        >>>
        >>> # In worker thread:
        >>> try:
        >>>     process_repo(repo)
        >>> except Exception as e:
        >>>     handler.record_error(
        >>>         context=repo.name,
        >>>         error=e,
        >>>         metadata={'repo_path': str(repo.path)}
        >>>     )
        >>>
        >>> # After all workers complete:
        >>> summary = handler.get_summary()
        >>> print(f"Total errors: {summary['total_errors']}")
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize error handler.

        Args:
            logger: Logger for error reporting (default: module logger)
        """
        self.logger = logger or logging.getLogger(__name__)
        self._errors: List[ErrorRecord] = []
        self._lock = threading.Lock()

    def record_error(
        self,
        context: str,
        error: Exception,
        severity: Optional[ErrorSeverity] = None,
        retry_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record an error that occurred during execution.

        Thread-safe: Can be called from multiple threads concurrently.

        Args:
            context: Context identifier (e.g., repository name)
            error: Exception that occurred
            severity: Error severity (auto-detected if None)
            retry_count: Number of retries attempted
            metadata: Additional context information
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Auto-detect severity if not provided
        if severity is None:
            severity = self._classify_severity(error)

        # Capture traceback
        tb = traceback.format_exc()

        record = ErrorRecord(
            context=context,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            traceback=tb,
            retry_count=retry_count,
            metadata=metadata or {}
        )

        with self._lock:
            self._errors.append(record)

        # Log error at appropriate level
        if severity == ErrorSeverity.TRANSIENT:
            self.logger.warning(
                f"Transient error in {context}: {error_type}: {error_message} "
                f"(retries: {retry_count})"
            )
        else:
            self.logger.error(
                f"Error in {context}: {error_type}: {error_message} "
                f"(retries: {retry_count})"
            )

    def _classify_severity(self, error: Exception) -> ErrorSeverity:
        """
        Classify error severity based on exception type.

        Args:
            error: Exception to classify

        Returns:
            Classified severity level
        """
        # Transient errors (network, timeouts)
        transient_types = (
            'TimeoutError', 'ConnectionError', 'HTTPError',
            'NetworkError', 'TemporaryError', 'ServiceUnavailable'
        )

        # Permanent errors (configuration, not found)
        permanent_types = (
            'ValueError', 'KeyError', 'AttributeError',
            'FileNotFoundError', 'PermissionError', 'NotImplementedError'
        )

        error_type = type(error).__name__

        if error_type in transient_types:
            return ErrorSeverity.TRANSIENT
        elif error_type in permanent_types:
            return ErrorSeverity.PERMANENT
        else:
            return ErrorSeverity.UNKNOWN

    def get_errors(self) -> List[ErrorRecord]:
        """
        Get all recorded errors.

        Returns:
            List of all ErrorRecord objects
        """
        with self._lock:
            return list(self._errors)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get error summary for reporting.

        Returns:
            Dictionary with error statistics and groupings:
                - total_errors: Total number of errors
                - errors_by_severity: Count by severity level
                - errors_by_type: Count by exception type
                - failed_contexts: List of contexts that failed
                - transient_errors: Count of transient errors
                - permanent_errors: Count of permanent errors
                - unknown_errors: Count of unknown errors
        """
        with self._lock:
            errors = list(self._errors)

        if not errors:
            return {
                'total_errors': 0,
                'errors_by_severity': {},
                'errors_by_type': {},
                'failed_contexts': [],
                'transient_errors': 0,
                'permanent_errors': 0,
                'unknown_errors': 0
            }

        # Group by severity
        by_severity: dict[str, int] = {}
        for error in errors:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Group by type
        by_type: dict[str, int] = {}
        for error in errors:
            error_type = error.error_type
            by_type[error_type] = by_type.get(error_type, 0) + 1

        # Get failed contexts
        failed_contexts = list(set(e.context for e in errors))

        return {
            'total_errors': len(errors),
            'errors_by_severity': by_severity,
            'errors_by_type': by_type,
            'failed_contexts': failed_contexts,
            'transient_errors': by_severity.get('transient', 0),
            'permanent_errors': by_severity.get('permanent', 0),
            'unknown_errors': by_severity.get('unknown', 0)
        }

    def has_errors(self) -> bool:
        """
        Check if any errors have been recorded.

        Returns:
            True if errors exist, False otherwise
        """
        with self._lock:
            return len(self._errors) > 0

    def clear(self):
        """Clear all recorded errors."""
        with self._lock:
            self._errors.clear()


def with_retry(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    error_handler: Optional[ConcurrentErrorHandler] = None,
    context: str = "unknown",
    retry_on: tuple = (Exception,)
):
    """
    Decorator to add retry logic with exponential backoff to a function.

    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for delay between retries
        initial_delay: Initial delay in seconds before first retry
        error_handler: Error handler to record failures
        context: Context for error reporting
        retry_on: Tuple of exception types to retry on

    Returns:
        Decorator function

    Example:
        >>> @with_retry(max_retries=3, backoff_factor=2.0)
        >>> def fetch_data():
        >>>     return requests.get('https://api.example.com/data')
    """
    def decorator(fn: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    # Record error if handler provided
                    if error_handler:
                        error_handler.record_error(
                            context=context,
                            error=e,
                            retry_count=attempt,
                            metadata={'max_retries': max_retries}
                        )

                    # Don't sleep after last attempt
                    if attempt < max_retries:
                        delay = initial_delay * (backoff_factor ** attempt)
                        time.sleep(delay)

            # All retries exhausted, raise last exception
            if last_exception is not None:
                raise last_exception
            # Should never reach here, but satisfy type checker
            raise RuntimeError("Retry loop completed without exception or return")

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern to prevent cascading failures.

    Opens circuit after threshold failures, preventing further attempts
    until a timeout period expires.

    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Too many failures, requests fail immediately
        - HALF_OPEN: Testing if service recovered

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        >>>
        >>> try:
        >>>     result = breaker.call(risky_operation)
        >>> except CircuitOpenError:
        >>>     # Circuit is open, don't retry
        >>>     return fallback_value
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds before attempting to close circuit
            expected_exception: Exception type to count as failure
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "CLOSED"
        self._lock = threading.Lock()

        # Logger
        self.logger = logging.getLogger(__name__)

    def call(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker.

        Args:
            fn: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result from function call

        Raises:
            CircuitOpenError: If circuit is open
            Exception: Any exception from fn
        """
        with self._lock:
            # Check if circuit should transition from OPEN to HALF_OPEN
            if self._state == "OPEN":
                if self._last_failure_time and time.time() - self._last_failure_time > self.timeout:
                    self._state = "HALF_OPEN"
                    self.logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise CircuitOpenError(
                        f"Circuit breaker is open. "
                        f"Failures: {self._failure_count}, "
                        f"Timeout: {self.timeout}s"
                    )

        try:
            result = fn(*args, **kwargs)

            # Success, reset circuit
            with self._lock:
                if self._state == "HALF_OPEN":
                    self._state = "CLOSED"
                    self.logger.info("Circuit breaker closed after successful test")
                self._failure_count = 0

            return result

        except self.expected_exception as e:
            with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.time()

                if self._failure_count >= self.failure_threshold:
                    if self._state != "OPEN":
                        self._state = "OPEN"
                        self.logger.warning(
                            f"Circuit breaker opened after {self._failure_count} failures"
                        )

            raise

    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        with self._lock:
            self._failure_count = 0
            self._last_failure_time = None
            self._state = "CLOSED"
            self.logger.info("Circuit breaker manually reset to CLOSED")

    def get_state(self) -> str:
        """
        Get current circuit state.

        Returns:
            Current state: "CLOSED", "OPEN", or "HALF_OPEN"
        """
        with self._lock:
            return self._state

    def get_failure_count(self) -> int:
        """
        Get current failure count.

        Returns:
            Number of consecutive failures
        """
        with self._lock:
            return self._failure_count


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass
