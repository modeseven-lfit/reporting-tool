# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Structured logging framework for the repository reporting system.

This module provides a context-aware logging system that enhances standard
Python logging with structured fields, performance tracking, and integration
with domain models.

Features:
- Context propagation (repository, phase, operation)
- Performance timing
- Structured field injection
- Domain model integration
- Log aggregation and summarization
- JSON-compatible output
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict


class LogPhase(Enum):
    """Enumeration of processing phases for context tracking."""

    INITIALIZATION = "initialization"
    DISCOVERY = "discovery"
    COLLECTION = "collection"
    AGGREGATION = "aggregation"
    RENDERING = "rendering"
    FINALIZATION = "finalization"
    API_CALL = "api_call"
    GIT_OPERATION = "git_operation"
    VALIDATION = "validation"


class LogLevel(Enum):
    """Log level enumeration for aggregation."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """
    Context information for structured logging.

    Attributes:
        repository: Current repository being processed
        phase: Current processing phase
        operation: Specific operation being performed
        window: Time window being processed
        extra: Additional context fields
    """

    repository: Optional[str] = None
    phase: Optional[LogPhase] = None
    operation: Optional[str] = None
    window: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging."""
        context = {}

        if self.repository:
            context["repository"] = self.repository
        if self.phase:
            context["phase"] = self.phase.value
        if self.operation:
            context["operation"] = self.operation
        if self.window:
            context["window"] = self.window
        if self.extra:
            context.update(self.extra)

        return context

    def merge(self, other: "LogContext") -> "LogContext":
        """Merge with another context, preferring other's non-None values."""
        return LogContext(
            repository=other.repository or self.repository,
            phase=other.phase or self.phase,
            operation=other.operation or self.operation,
            window=other.window or self.window,
            extra={**self.extra, **other.extra},
        )


@dataclass
class LogEntry:
    """
    Structured log entry for aggregation and analysis.

    Attributes:
        level: Log level
        message: Log message
        context: Logging context
        timestamp: When the log was created
        duration_ms: Optional duration for performance tracking
    """

    level: LogLevel
    message: str
    context: LogContext
    timestamp: float = field(default_factory=time.time)
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary."""
        entry: Dict[str, Any] = {
            "level": self.level.value,
            "message": self.message,
            "timestamp": self.timestamp,
        }

        if self.duration_ms is not None:
            entry["duration_ms"] = self.duration_ms

        context = self.context.to_dict()
        if context:
            entry["context"] = context

        return entry


class LogAggregator:
    """
    Aggregates log entries for summary reporting.

    Tracks counts by level, errors by repository, and performance metrics.
    """

    def __init__(self) -> None:
        self.entries: List[LogEntry] = []
        self.counts_by_level: Dict[str, int] = defaultdict(int)
        self.errors_by_repo: Dict[str, List[str]] = defaultdict(list)
        self.warnings_by_repo: Dict[str, List[str]] = defaultdict(list)
        self.performance_by_phase: Dict[str, List[float]] = defaultdict(list)

    def add_entry(self, entry: LogEntry) -> None:
        """Add a log entry to the aggregator."""
        self.entries.append(entry)
        self.counts_by_level[entry.level.value] += 1

        # Track errors and warnings by repository
        if entry.context.repository:
            if entry.level == LogLevel.ERROR:
                self.errors_by_repo[entry.context.repository].append(entry.message)
            elif entry.level == LogLevel.WARNING:
                self.warnings_by_repo[entry.context.repository].append(entry.message)

        # Track performance by phase
        if entry.duration_ms is not None and entry.context.phase:
            self.performance_by_phase[entry.context.phase.value].append(entry.duration_ms)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of aggregated logs.

        Returns:
            Dictionary with log counts, errors, and performance metrics.
        """
        summary = {
            "log_summary": dict(self.counts_by_level),
            "total_entries": len(self.entries),
        }

        # Add error details if present
        if self.errors_by_repo:
            summary["errors_by_repository"] = {
                repo: {
                    "count": len(errors),
                    "messages": errors[:5],  # First 5 errors
                }
                for repo, errors in self.errors_by_repo.items()
            }

        # Add warning details if present
        if self.warnings_by_repo:
            summary["warnings_by_repository"] = {
                repo: {
                    "count": len(warnings),
                    "messages": warnings[:5],  # First 5 warnings
                }
                for repo, warnings in self.warnings_by_repo.items()
            }

        # Add performance metrics if present
        if self.performance_by_phase:
            summary["performance_by_phase"] = {
                phase: {
                    "count": len(durations),
                    "total_ms": sum(durations),
                    "avg_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations),
                }
                for phase, durations in self.performance_by_phase.items()
            }

        return summary

    def get_partial_failures(self) -> List[Dict[str, Any]]:
        """
        Get list of repositories with partial failures (warnings but not errors).

        Returns:
            List of repositories with warning counts.
        """
        partial_failures = []

        for repo, warnings in self.warnings_by_repo.items():
            if repo not in self.errors_by_repo:  # No errors, only warnings
                partial_failures.append({
                    "repository": repo,
                    "warning_count": len(warnings),
                    "sample_warnings": warnings[:3],
                })

        return partial_failures


class StructuredLogger:
    """
    Wrapper around standard Python logger with structured logging support.

    Provides context management, performance tracking, and log aggregation.
    """

    def __init__(self, logger: logging.Logger, aggregator: Optional[LogAggregator] = None):
        """
        Initialize structured logger.

        Args:
            logger: Underlying Python logger
            aggregator: Optional log aggregator for summary reporting
        """
        self.logger = logger
        self.aggregator = aggregator or LogAggregator()
        self._context_stack: List[LogContext] = [LogContext()]

    @property
    def current_context(self) -> LogContext:
        """Get current logging context."""
        # Merge all contexts in the stack
        result = LogContext()
        for ctx in self._context_stack:
            result = result.merge(ctx)
        return result

    def _log(
        self,
        level: LogLevel,
        message: str,
        duration_ms: Optional[float] = None,
        **extra_context: Any
    ) -> None:
        """
        Internal logging method.

        Args:
            level: Log level
            message: Log message
            duration_ms: Optional duration for performance tracking
            extra_context: Additional context fields
        """
        # Create log entry
        context = self.current_context
        if extra_context:
            context = LogContext(
                repository=context.repository,
                phase=context.phase,
                operation=context.operation,
                window=context.window,
                extra={**context.extra, **extra_context},
            )

        entry = LogEntry(
            level=level,
            message=message,
            context=context,
            duration_ms=duration_ms,
        )

        # Add to aggregator
        self.aggregator.add_entry(entry)

        # Log to underlying logger
        log_level = getattr(logging, level.value)
        context_dict = context.to_dict()

        # Format message with context
        if context_dict or duration_ms is not None:
            extra_parts = []
            if duration_ms is not None:
                extra_parts.append(f"duration_ms={duration_ms:.2f}")
            for key, value in context_dict.items():
                extra_parts.append(f"{key}={value}")

            formatted_message = f"{message} [{', '.join(extra_parts)}]"
        else:
            formatted_message = message

        self.logger.log(log_level, formatted_message)

    def debug(self, message: str, **extra: Any) -> None:
        """Log debug message with context."""
        self._log(LogLevel.DEBUG, message, **extra)

    def info(self, message: str, **extra: Any) -> None:
        """Log info message with context."""
        self._log(LogLevel.INFO, message, **extra)

    def warning(self, message: str, **extra: Any) -> None:
        """Log warning message with context."""
        self._log(LogLevel.WARNING, message, **extra)

    def error(self, message: str, **extra: Any) -> None:
        """Log error message with context."""
        self._log(LogLevel.ERROR, message, **extra)

    def critical(self, message: str, **extra: Any) -> None:
        """Log critical message with context."""
        self._log(LogLevel.CRITICAL, message, **extra)

    @contextmanager
    def context(
        self,
        repository: Optional[str] = None,
        phase: Optional[LogPhase] = None,
        operation: Optional[str] = None,
        window: Optional[str] = None,
        **extra: Any
    ):
        """
        Context manager for adding logging context.

        Args:
            repository: Repository name
            phase: Processing phase
            operation: Operation name
            window: Time window
            extra: Additional context fields

        Example:
            with logger.context(repository="foo/bar", phase=LogPhase.COLLECTION):
                logger.info("Processing repository")
        """
        ctx = LogContext(
            repository=repository,
            phase=phase,
            operation=operation,
            window=window,
            extra=extra,
        )

        self._context_stack.append(ctx)
        try:
            yield
        finally:
            self._context_stack.pop()

    @contextmanager
    def timed(self, operation: str):
        """
        Context manager for timing operations.

        Args:
            operation: Name of the operation being timed

        Example:
            with logger.timed("git_log"):
                # perform git operation
                pass
        """
        start_time = time.time()

        with self.context(operation=operation):
            try:
                yield
            finally:
                duration_ms = (time.time() - start_time) * 1000
                self._log(
                    LogLevel.DEBUG,
                    f"Operation completed: {operation}",
                    duration_ms=duration_ms,
                )

    def get_summary(self) -> Dict[str, Any]:
        """Get aggregated log summary."""
        return self.aggregator.get_summary()

    def get_partial_failures(self) -> List[Dict[str, Any]]:
        """Get list of repositories with partial failures."""
        return self.aggregator.get_partial_failures()


def create_structured_logger(
    name: str,
    level: int = logging.INFO,
    aggregator: Optional[LogAggregator] = None
) -> StructuredLogger:
    """
    Create a structured logger instance.

    Args:
        name: Logger name
        level: Logging level
        aggregator: Optional log aggregator (creates new one if not provided)

    Returns:
        StructuredLogger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    return StructuredLogger(logger, aggregator)


def log_with_context(
    logger: StructuredLogger,
    level: str,
    message: str,
    **context: Any
) -> None:
    """
    Helper function to log with context fields.

    Args:
        logger: Structured logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        context: Context fields

    Example:
        log_with_context(
            logger,
            "INFO",
            "Repository processed",
            repository="foo/bar",
            commits=100
        )
    """
    log_method = getattr(logger, level.lower())
    log_method(message, **context)
