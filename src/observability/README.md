<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Observability Framework

This package provides structured logging, error classification, and performance tracking for the repository reporting system.

## Overview

The observability framework enhances the standard Python logging system with:

- **Structured Logging**: Context-aware logging with automatic field injection
- **Error Taxonomy**: Comprehensive error classification and tracking
- **Performance Metrics**: Timing and performance monitoring
- **Log Aggregation**: Automatic summarization and reporting
- **Domain Integration**: Seamless integration with domain models

## Features

### Structured Logging

Context-propagating logging system that automatically enriches log entries with contextual information:

```python
from src.observability import create_structured_logger, LogPhase

logger = create_structured_logger("my_app")

# Add context for all subsequent logs
with logger.context(repository="foo/bar", phase=LogPhase.COLLECTION):
    logger.info("Starting collection")

    # Nested contexts merge
    with logger.context(window="1y"):
        logger.info("Processing window")
        # Logs include: repository=foo/bar, phase=collection, window=1y
```

### Error Classification

Comprehensive error taxonomy with automatic severity and category assignment:

```python
from src.observability import ErrorTracker, ErrorType, ErrorContext

tracker = ErrorTracker()

# Add classified error
ctx = ErrorContext(repository="test/repo", operation="git_log")
tracker.add_error(
    ErrorType.GIT_COMMAND_FAILED,
    "Git command failed: exit code 128",
    context=ctx
)

# Get error summary
summary = tracker.get_summary()
print(f"Total errors: {summary['total_errors']}")
print(f"By severity: {summary['by_severity']}")
print(f"By category: {summary['by_category']}")
```

### Performance Tracking

Automatic timing of operations with context-aware metrics:

```python
from src.observability import create_structured_logger

logger = create_structured_logger("my_app")

# Time an operation
with logger.timed("git_clone"):
    # Perform git clone
    pass

# Get performance summary
summary = logger.get_summary()
perf = summary['performance_by_phase']
print(f"Git operations: {perf['git_operation']['avg_ms']}ms average")
```

## Components

### Structured Logging

#### LogPhase

Enumeration of processing phases for context tracking:

- `INITIALIZATION` - System initialization
- `DISCOVERY` - Repository discovery
- `COLLECTION` - Data collection from repositories
- `AGGREGATION` - Data aggregation and rollups
- `RENDERING` - Report rendering
- `FINALIZATION` - Cleanup and finalization
- `API_CALL` - External API calls
- `GIT_OPERATION` - Git operations
- `VALIDATION` - Data validation

#### LogLevel

Standard log levels for classification:

- `DEBUG` - Detailed diagnostic information
- `INFO` - General informational messages
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

#### LogContext

Context information attached to log entries:

```python
from src.observability import LogContext, LogPhase

ctx = LogContext(
    repository="foo/bar",
    phase=LogPhase.COLLECTION,
    operation="git_log",
    window="1y",
    extra={"attempts": 3}
)

# Convert to dict for logging
context_dict = ctx.to_dict()
```

#### StructuredLogger

Main logging interface with context management:

```python
from src.observability import create_structured_logger, LogPhase

logger = create_structured_logger("my_app")

# Basic logging
logger.info("Processing started")
logger.error("Failed to process", error_code=500)

# Context management
with logger.context(repository="test/repo"):
    logger.info("Repository processing")

# Timing operations
with logger.timed("expensive_operation"):
    # Perform operation
    pass

# Get aggregated summary
summary = logger.get_summary()
```

#### LogAggregator

Aggregates log entries for summary reporting:

```python
from src.observability import LogAggregator

aggregator = LogAggregator()

# Aggregator automatically tracks:
# - Counts by log level
# - Errors by repository
# - Warnings by repository
# - Performance metrics by phase

summary = aggregator.get_summary()
partial_failures = aggregator.get_partial_failures()
```

### Error Classification

#### ErrorCategory

High-level error categories:

- `NETWORK` - Network-related errors
- `API` - External API errors
- `GIT` - Git operation errors
- `VALIDATION` - Data validation errors
- `CONFIGURATION` - Configuration errors
- `DATA` - Data processing errors
- `RENDERING` - Report rendering errors
- `SYSTEM` - System-level errors

#### ErrorSeverity

Error severity levels:

- `LOW` - Minor issues, degraded functionality
- `MEDIUM` - Moderate issues, partial failures
- `HIGH` - Major issues, significant impact
- `CRITICAL` - Critical failures, blocks execution

#### ErrorType

Detailed error types (40+ types across all categories):

**Network Errors:**

- `NETWORK_TIMEOUT` - Network timeout
- `NETWORK_CONNECTION` - Connection failure
- `NETWORK_DNS` - DNS resolution failure

**API Errors:**

- `API_HTTP_CLIENT` - HTTP 4xx errors
- `API_HTTP_SERVER` - HTTP 5xx errors
- `API_RATE_LIMIT` - Rate limit exceeded
- `API_AUTHENTICATION` - Authentication failure
- `API_AUTHORIZATION` - Authorization failure
- `API_NOT_FOUND` - Resource not found (404)
- `API_PARSE` - Response parsing error
- `API_TIMEOUT` - API timeout
- `API_UNKNOWN` - Unknown API error

**Git Errors:**

- `GIT_NOT_FOUND` - Repository not found
- `GIT_COMMAND_FAILED` - Git command failed
- `GIT_PARSE_ERROR` - Git output parse error
- `GIT_INVALID_REPO` - Invalid repository
- `GIT_CLONE_FAILED` - Clone operation failed
- `GIT_CHECKOUT_FAILED` - Checkout operation failed

**Validation Errors:**

- `VALIDATION_DOMAIN_MODEL` - Domain model validation
- `VALIDATION_SCHEMA` - Schema validation
- `VALIDATION_CONSTRAINT` - Constraint violation
- `VALIDATION_TYPE` - Type validation
- `VALIDATION_REQUIRED_FIELD` - Required field missing

**Configuration Errors:**

- `CONFIG_MISSING` - Configuration not found
- `CONFIG_INVALID` - Invalid configuration
- `CONFIG_PARSE` - Configuration parse error
- `CONFIG_SCHEMA` - Configuration schema error

**Data Errors:**

- `DATA_MISSING` - Data not found
- `DATA_CORRUPT` - Data corruption
- `DATA_INCONSISTENT` - Data inconsistency
- `DATA_CONVERSION` - Data conversion error

**Rendering Errors:**

- `RENDER_TEMPLATE` - Template rendering error
- `RENDER_FORMAT` - Format error
- `RENDER_OUTPUT` - Output generation error

**System Errors:**

- `SYSTEM_IO` - I/O error
- `SYSTEM_PERMISSION` - Permission denied
- `SYSTEM_RESOURCE` - Resource exhaustion
- `SYSTEM_UNKNOWN` - Unknown system error

#### ErrorContext

Context information for error occurrences:

```python
from src.observability import ErrorContext

ctx = ErrorContext(
    repository="foo/bar",
    operation="git_log",
    phase="collection",
    window="1y",
    extra={"exit_code": 128}
)
```

#### ClassifiedError

A classified error with type, severity, and context:

```python
from src.observability import ClassifiedError, ErrorType, ErrorSeverity, ErrorContext

error = ClassifiedError(
    error_type=ErrorType.GIT_COMMAND_FAILED,
    message="Git command failed: exit code 128",
    severity=ErrorSeverity.HIGH,  # Optional, auto-assigned if not provided
    context=ErrorContext(repository="foo/bar"),
    original_exception=exception  # Optional
)

# Convert to dict for reporting
error_dict = error.to_dict()
```

#### ErrorTracker

Tracks and aggregates errors across the reporting process:

```python
from src.observability import ErrorTracker, ErrorType, ErrorContext

tracker = ErrorTracker()

# Add errors
ctx = ErrorContext(repository="repo1", phase="collection")
tracker.add_error(ErrorType.GIT_COMMAND_FAILED, "Failed", context=ctx)

# Query errors
errors_by_type = tracker.get_errors_by_type(ErrorType.GIT_COMMAND_FAILED)
errors_by_severity = tracker.get_errors_by_severity(ErrorSeverity.HIGH)
errors_by_repo = tracker.get_errors_by_repository("repo1")

# Get summaries
summary = tracker.get_summary()
api_failures = tracker.get_api_failures()
partial_failures = tracker.get_partial_failures()
detailed_report = tracker.get_detailed_report()
```

#### Exception Classification

Automatic classification of Python exceptions:

```python
from src.observability import classify_exception, ErrorContext

try:
    # Some operation
    raise TimeoutError("Connection timed out")
except Exception as e:
    ctx = ErrorContext(repository="test/repo")
    error = classify_exception(e, context=ctx)
    # error.error_type == ErrorType.NETWORK_TIMEOUT
    # error.severity == ErrorSeverity.MEDIUM
```

## Usage Patterns

### Basic Structured Logging

```python
from src.observability import create_structured_logger, LogPhase

logger = create_structured_logger("reporting_system")

# Log with automatic context
with logger.context(phase=LogPhase.INITIALIZATION):
    logger.info("System initializing")

    # Add more context
    with logger.context(repository="foo/bar"):
        logger.info("Processing repository")
        logger.debug("Found 100 commits", commits=100)
```

### Error Tracking and Reporting

```python
from src.observability import ErrorTracker, ErrorType, ErrorContext

tracker = ErrorTracker()

# Track errors during processing
for repo in repositories:
    ctx = ErrorContext(repository=repo.name, phase="collection")

    try:
        process_repository(repo)
    except Exception as e:
        tracker.add_error(
            ErrorType.GIT_COMMAND_FAILED,
            str(e),
            context=ctx,
            exception=e
        )

# Generate error report
summary = tracker.get_summary()
print(f"Total errors: {summary['total_errors']}")
print(f"Repositories affected: {summary['repositories_affected']}")

# Get partial failures (warnings but no critical errors)
partial = tracker.get_partial_failures()
for item in partial:
    print(f"Repository {item['repository']}: {item['error_count']} errors")
```

### Performance Monitoring

```python
from src.observability import create_structured_logger, LogPhase

logger = create_structured_logger("reporting")

# Track phase performance
with logger.context(phase=LogPhase.COLLECTION):
    with logger.timed("clone_repositories"):
        clone_all_repositories()

    with logger.timed("analyze_commits"):
        analyze_all_commits()

# Get performance summary
summary = logger.get_summary()
if 'performance_by_phase' in summary:
    for phase, metrics in summary['performance_by_phase'].items():
        print(f"{phase}: avg={metrics['avg_ms']}ms, total={metrics['total_ms']}ms")
```

### Integrated Logging and Error Tracking

```python
from src.observability import (
    create_structured_logger,
    ErrorTracker,
    ErrorType,
    ErrorContext,
    LogPhase
)

logger = create_structured_logger("reporting")
error_tracker = ErrorTracker()

def process_repository(repo_name):
    with logger.context(repository=repo_name, phase=LogPhase.COLLECTION):
        logger.info("Starting repository processing")

        try:
            with logger.timed("git_operations"):
                # Perform git operations
                pass

            logger.info("Repository processed successfully")

        except Exception as e:
            logger.error(f"Failed to process repository: {e}")

            ctx = ErrorContext(
                repository=repo_name,
                phase="collection",
                operation="git_operations"
            )
            error_tracker.add_error(
                ErrorType.GIT_COMMAND_FAILED,
                str(e),
                context=ctx,
                exception=e
            )

# Generate comprehensive observability report
log_summary = logger.get_summary()
error_summary = error_tracker.get_summary()

report = {
    "observability": {
        "log_summary": log_summary,
        "error_summary": error_summary,
        "api_failures": error_tracker.get_api_failures(),
        "partial_failures": error_tracker.get_partial_failures(),
    }
}
```

## Integration with Report Output

The observability framework is designed to integrate with the JSON report output:

```python
report_data = {
    "schema_version": "1.0.0",
    "generated_at": "2024-01-16T12:00:00Z",
    # ... existing fields ...
    "observability": {
        "log_summary": logger.get_summary(),
        "error_summary": error_tracker.get_summary(),
        "api_failures": error_tracker.get_api_failures(),
        "partial_failures": error_tracker.get_partial_failures(),
        "performance_by_phase": {
            # Performance metrics from logger
        }
    }
}
```

## Testing

Comprehensive unit tests are available:

```bash
# Test structured logging
pytest tests/test_structured_logging.py -v

# Test error taxonomy
pytest tests/test_errors.py -v

# Test both
pytest tests/test_structured_logging.py tests/test_errors.py -v
```

**Test Coverage:**

- 40 tests for structured logging
- 50 tests for error taxonomy
- 90+ total tests, 100% passing

## Design Principles

1. **Context Propagation**: Automatic context inheritance through nested scopes
2. **Fail Safe**: Logging failures don't crash the application
3. **Performance First**: Minimal overhead, <5% runtime impact
4. **Backwards Compatible**: Optional observability section in reports
5. **Extensible**: Easy to add new error types and phases
6. **Type Safe**: Full type hints throughout

## Performance Considerations

- **Log Aggregation**: O(1) append, O(n) summarization
- **Context Management**: Stack-based, minimal overhead
- **Timing**: Uses `time.time()` for microsecond precision
- **Memory**: Log entries stored in memory, use summarization for large runs

## Version

Observability Framework Version: **1.0.0**

See `src/observability/__init__.py` for the current version.

## References

- **Refactoring Plan**: See `REFACTOR_PLAN.md` Phase 4
- **Tests**: `tests/test_structured_logging.py`, `tests/test_errors.py`
- **Domain Models**: `src/domain/` (for context integration)
- **API Error Types**: `src/api/base_client.py` (error type origins)

## Migration from Standard Logging

Replace standard logging calls with structured logging:

```python
# Before
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing {repo_name}")

# After
from src.observability import create_structured_logger

logger = create_structured_logger(__name__)
with logger.context(repository=repo_name):
    logger.info("Processing repository")
```

Benefits:

- Automatic context tracking
- Performance metrics
- Error aggregation
- Structured output
- Better observability
