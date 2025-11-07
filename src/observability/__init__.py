# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Observability package for the repository reporting system.

This package provides structured logging, error classification, and
performance tracking capabilities.

Features:
- Structured logging with context propagation
- Error taxonomy and classification
- Performance metrics and timing
- Log aggregation and summarization
- Integration with domain models
"""

from .errors import (
    ClassifiedError,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    ErrorTracker,
    ErrorType,
    classify_exception,
)
from .structured_logging import (
    LogAggregator,
    LogContext,
    LogEntry,
    LogLevel,
    LogPhase,
    StructuredLogger,
    create_structured_logger,
    log_with_context,
)

__all__ = [
    # Error taxonomy
    "ClassifiedError",
    "ErrorCategory",
    "ErrorContext",
    "ErrorSeverity",
    "ErrorTracker",
    "ErrorType",
    "classify_exception",
    # Structured logging
    "LogAggregator",
    "LogContext",
    "LogEntry",
    "LogLevel",
    "LogPhase",
    "StructuredLogger",
    "create_structured_logger",
    "log_with_context",
]

# Version for observability framework
OBSERVABILITY_VERSION = "1.0.0"
