# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for structured logging framework.

Tests context management, log aggregation, performance tracking,
and integration with the logging system.
"""

import logging
import time

from observability.structured_logging import (
    LogAggregator,
    LogContext,
    LogEntry,
    LogLevel,
    LogPhase,
    StructuredLogger,
    create_structured_logger,
    log_with_context,
)


class TestLogContext:
    """Test LogContext functionality."""

    def test_empty_context(self):
        """Test creating an empty context."""
        ctx = LogContext()
        assert ctx.repository is None
        assert ctx.phase is None
        assert ctx.operation is None
        assert ctx.window is None
        assert ctx.extra == {}

    def test_context_with_values(self):
        """Test creating context with values."""
        ctx = LogContext(
            repository="foo/bar",
            phase=LogPhase.COLLECTION,
            operation="git_log",
            window="1y",
            extra={"commits": 100},
        )
        assert ctx.repository == "foo/bar"
        assert ctx.phase == LogPhase.COLLECTION
        assert ctx.operation == "git_log"
        assert ctx.window == "1y"
        assert ctx.extra == {"commits": 100}

    def test_to_dict_empty(self):
        """Test converting empty context to dict."""
        ctx = LogContext()
        result = ctx.to_dict()
        assert result == {}

    def test_to_dict_with_values(self):
        """Test converting populated context to dict."""
        ctx = LogContext(
            repository="test/repo",
            phase=LogPhase.AGGREGATION,
            operation="compute_totals",
        )
        result = ctx.to_dict()
        assert result == {
            "repository": "test/repo",
            "phase": "aggregation",
            "operation": "compute_totals",
        }

    def test_to_dict_with_extra(self):
        """Test that extra fields are included."""
        ctx = LogContext(
            repository="test/repo",
            extra={"foo": "bar", "count": 42},
        )
        result = ctx.to_dict()
        assert result["repository"] == "test/repo"
        assert result["foo"] == "bar"
        assert result["count"] == 42

    def test_merge_contexts(self):
        """Test merging two contexts."""
        ctx1 = LogContext(
            repository="repo1",
            phase=LogPhase.COLLECTION,
            extra={"a": 1},
        )
        ctx2 = LogContext(
            repository="repo2",
            operation="test_op",
            extra={"b": 2},
        )

        merged = ctx1.merge(ctx2)
        assert merged.repository == "repo2"  # Prefer ctx2
        assert merged.phase == LogPhase.COLLECTION  # From ctx1
        assert merged.operation == "test_op"  # From ctx2
        assert merged.extra == {"a": 1, "b": 2}  # Combined

    def test_merge_preserves_none(self):
        """Test that merge doesn't overwrite with None."""
        ctx1 = LogContext(repository="repo1", phase=LogPhase.COLLECTION)
        ctx2 = LogContext(operation="op1")

        merged = ctx1.merge(ctx2)
        assert merged.repository == "repo1"  # Not overwritten
        assert merged.phase == LogPhase.COLLECTION  # Not overwritten
        assert merged.operation == "op1"


class TestLogEntry:
    """Test LogEntry functionality."""

    def test_create_log_entry(self):
        """Test creating a log entry."""
        ctx = LogContext(repository="test/repo")
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test message",
            context=ctx,
        )
        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"
        assert entry.context == ctx
        assert entry.duration_ms is None
        assert entry.timestamp > 0

    def test_log_entry_with_duration(self):
        """Test log entry with duration."""
        entry = LogEntry(
            level=LogLevel.DEBUG,
            message="Operation complete",
            context=LogContext(),
            duration_ms=123.45,
        )
        assert entry.duration_ms == 123.45

    def test_to_dict_basic(self):
        """Test converting basic entry to dict."""
        entry = LogEntry(
            level=LogLevel.WARNING,
            message="Warning message",
            context=LogContext(),
        )
        result = entry.to_dict()
        assert result["level"] == "WARNING"
        assert result["message"] == "Warning message"
        assert "timestamp" in result

    def test_to_dict_with_duration(self):
        """Test dict includes duration when present."""
        entry = LogEntry(
            level=LogLevel.INFO,
            message="Test",
            context=LogContext(),
            duration_ms=100.0,
        )
        result = entry.to_dict()
        assert result["duration_ms"] == 100.0

    def test_to_dict_with_context(self):
        """Test dict includes context when present."""
        ctx = LogContext(repository="foo/bar", phase=LogPhase.RENDERING)
        entry = LogEntry(
            level=LogLevel.ERROR,
            message="Error",
            context=ctx,
        )
        result = entry.to_dict()
        assert "context" in result
        assert result["context"]["repository"] == "foo/bar"
        assert result["context"]["phase"] == "rendering"


class TestLogAggregator:
    """Test LogAggregator functionality."""

    def test_empty_aggregator(self):
        """Test newly created aggregator is empty."""
        agg = LogAggregator()
        assert len(agg.entries) == 0
        assert len(agg.counts_by_level) == 0
        assert len(agg.errors_by_repo) == 0

    def test_add_entry_updates_counts(self):
        """Test that adding entries updates counts."""
        agg = LogAggregator()
        entry1 = LogEntry(LogLevel.INFO, "Info", LogContext())
        entry2 = LogEntry(LogLevel.INFO, "Info2", LogContext())
        entry3 = LogEntry(LogLevel.ERROR, "Error", LogContext())

        agg.add_entry(entry1)
        agg.add_entry(entry2)
        agg.add_entry(entry3)

        assert len(agg.entries) == 3
        assert agg.counts_by_level["INFO"] == 2
        assert agg.counts_by_level["ERROR"] == 1

    def test_track_errors_by_repo(self):
        """Test that errors are tracked by repository."""
        agg = LogAggregator()
        ctx = LogContext(repository="test/repo")
        entry = LogEntry(LogLevel.ERROR, "Test error", ctx)

        agg.add_entry(entry)

        assert "test/repo" in agg.errors_by_repo
        assert len(agg.errors_by_repo["test/repo"]) == 1
        assert agg.errors_by_repo["test/repo"][0] == "Test error"

    def test_track_warnings_by_repo(self):
        """Test that warnings are tracked by repository."""
        agg = LogAggregator()
        ctx = LogContext(repository="test/repo")
        entry = LogEntry(LogLevel.WARNING, "Test warning", ctx)

        agg.add_entry(entry)

        assert "test/repo" in agg.warnings_by_repo
        assert len(agg.warnings_by_repo["test/repo"]) == 1
        assert agg.warnings_by_repo["test/repo"][0] == "Test warning"

    def test_track_performance_by_phase(self):
        """Test that performance metrics are tracked by phase."""
        agg = LogAggregator()
        ctx = LogContext(phase=LogPhase.COLLECTION)
        entry = LogEntry(LogLevel.DEBUG, "Op done", ctx, duration_ms=100.0)

        agg.add_entry(entry)

        assert "collection" in agg.performance_by_phase
        assert agg.performance_by_phase["collection"] == [100.0]

    def test_get_summary_basic(self):
        """Test basic summary generation."""
        agg = LogAggregator()
        agg.add_entry(LogEntry(LogLevel.INFO, "Info", LogContext()))
        agg.add_entry(LogEntry(LogLevel.ERROR, "Error", LogContext()))

        summary = agg.get_summary()
        assert summary["total_entries"] == 2
        assert summary["log_summary"]["INFO"] == 1
        assert summary["log_summary"]["ERROR"] == 1

    def test_get_summary_with_errors(self):
        """Test summary includes error details."""
        agg = LogAggregator()
        ctx = LogContext(repository="test/repo")
        agg.add_entry(LogEntry(LogLevel.ERROR, "Error 1", ctx))
        agg.add_entry(LogEntry(LogLevel.ERROR, "Error 2", ctx))

        summary = agg.get_summary()
        assert "errors_by_repository" in summary
        assert summary["errors_by_repository"]["test/repo"]["count"] == 2
        assert len(summary["errors_by_repository"]["test/repo"]["messages"]) == 2

    def test_get_summary_limits_error_messages(self):
        """Test that summary limits error messages to first 5."""
        agg = LogAggregator()
        ctx = LogContext(repository="test/repo")
        for i in range(10):
            agg.add_entry(LogEntry(LogLevel.ERROR, f"Error {i}", ctx))

        summary = agg.get_summary()
        messages = summary["errors_by_repository"]["test/repo"]["messages"]
        assert len(messages) == 5  # Only first 5

    def test_get_summary_with_performance(self):
        """Test summary includes performance metrics."""
        agg = LogAggregator()
        ctx = LogContext(phase=LogPhase.COLLECTION)
        agg.add_entry(LogEntry(LogLevel.DEBUG, "Op1", ctx, duration_ms=100.0))
        agg.add_entry(LogEntry(LogLevel.DEBUG, "Op2", ctx, duration_ms=200.0))

        summary = agg.get_summary()
        assert "performance_by_phase" in summary
        perf = summary["performance_by_phase"]["collection"]
        assert perf["count"] == 2
        assert perf["total_ms"] == 300.0
        assert perf["avg_ms"] == 150.0
        assert perf["min_ms"] == 100.0
        assert perf["max_ms"] == 200.0

    def test_get_partial_failures(self):
        """Test identifying partial failures (warnings but no errors)."""
        agg = LogAggregator()

        # Repo with warnings only
        ctx1 = LogContext(repository="repo1")
        agg.add_entry(LogEntry(LogLevel.WARNING, "Warning", ctx1))

        # Repo with errors
        ctx2 = LogContext(repository="repo2")
        agg.add_entry(LogEntry(LogLevel.ERROR, "Error", ctx2))

        partial = agg.get_partial_failures()
        assert len(partial) == 1
        assert partial[0]["repository"] == "repo1"
        assert partial[0]["warning_count"] == 1


class TestStructuredLogger:
    """Test StructuredLogger functionality."""

    def test_create_logger(self):
        """Test creating a structured logger."""
        logger = logging.getLogger("test")
        s_logger = StructuredLogger(logger)
        assert s_logger.logger == logger
        assert isinstance(s_logger.aggregator, LogAggregator)

    def test_current_context_empty(self):
        """Test current context starts empty."""
        logger = StructuredLogger(logging.getLogger("test"))
        ctx = logger.current_context
        assert ctx.repository is None
        assert ctx.phase is None

    def test_log_info(self):
        """Test logging info message."""
        logger = StructuredLogger(logging.getLogger("test"))
        logger.info("Test message")

        assert len(logger.aggregator.entries) == 1
        assert logger.aggregator.entries[0].level == LogLevel.INFO
        assert logger.aggregator.entries[0].message == "Test message"

    def test_log_with_extra_context(self):
        """Test logging with extra context."""
        logger = StructuredLogger(logging.getLogger("test"))
        logger.info("Test", custom_field="value")

        entry = logger.aggregator.entries[0]
        assert entry.context.extra["custom_field"] == "value"

    def test_context_manager(self):
        """Test context manager adds context."""
        logger = StructuredLogger(logging.getLogger("test"))

        with logger.context(repository="test/repo", phase=LogPhase.COLLECTION):
            logger.info("Inside context")

        entry = logger.aggregator.entries[0]
        assert entry.context.repository == "test/repo"
        assert entry.context.phase == LogPhase.COLLECTION

    def test_context_manager_nesting(self):
        """Test nested context managers."""
        logger = StructuredLogger(logging.getLogger("test"))

        with logger.context(repository="repo1"), logger.context(phase=LogPhase.COLLECTION):
            logger.info("Nested")

        entry = logger.aggregator.entries[0]
        assert entry.context.repository == "repo1"
        assert entry.context.phase == LogPhase.COLLECTION

    def test_context_manager_cleanup(self):
        """Test context is cleaned up after exiting."""
        logger = StructuredLogger(logging.getLogger("test"))

        with logger.context(repository="repo1"):
            pass

        logger.info("After context")
        entry = logger.aggregator.entries[0]
        assert entry.context.repository is None

    def test_timed_operation(self):
        """Test timed operation tracking."""
        logger = StructuredLogger(logging.getLogger("test"))

        with logger.timed("test_operation"):
            time.sleep(0.01)  # Sleep 10ms

        # Should have one debug log with duration
        entries = logger.aggregator.entries
        assert len(entries) == 1
        assert entries[0].duration_ms is not None
        assert entries[0].duration_ms >= 10.0  # At least 10ms
        assert entries[0].context.operation == "test_operation"

    def test_timed_sets_operation_context(self):
        """Test that timed() sets operation in context."""
        logger = StructuredLogger(logging.getLogger("test"))

        with logger.timed("my_op"):
            logger.info("Inside")

        # First entry is our info log
        assert logger.aggregator.entries[0].context.operation == "my_op"

    def test_get_summary(self):
        """Test getting summary from logger."""
        logger = StructuredLogger(logging.getLogger("test"))
        logger.info("Info 1")
        logger.error("Error 1")

        summary = logger.get_summary()
        assert summary["total_entries"] == 2
        assert summary["log_summary"]["INFO"] == 1
        assert summary["log_summary"]["ERROR"] == 1

    def test_get_partial_failures(self):
        """Test getting partial failures from logger."""
        logger = StructuredLogger(logging.getLogger("test"))

        with logger.context(repository="repo1"):
            logger.warning("Warning")

        partial = logger.get_partial_failures()
        assert len(partial) == 1
        assert partial[0]["repository"] == "repo1"


class TestHelperFunctions:
    """Test module-level helper functions."""

    def test_create_structured_logger(self):
        """Test create_structured_logger function."""
        logger = create_structured_logger("test_logger")
        assert isinstance(logger, StructuredLogger)
        assert logger.logger.name == "test_logger"

    def test_create_structured_logger_with_level(self):
        """Test creating logger with specific level."""
        logger = create_structured_logger("test", level=logging.DEBUG)
        assert logger.logger.level == logging.DEBUG

    def test_create_structured_logger_with_aggregator(self):
        """Test creating logger with custom aggregator."""
        agg = LogAggregator()
        logger = create_structured_logger("test", aggregator=agg)
        assert logger.aggregator is agg

    def test_log_with_context_helper(self):
        """Test log_with_context helper function."""
        logger = create_structured_logger("test")
        log_with_context(
            logger,
            "INFO",
            "Test message",
            repository="test/repo",
            commits=100,
        )

        entry = logger.aggregator.entries[0]
        assert entry.level == LogLevel.INFO
        assert entry.message == "Test message"
        assert entry.context.extra["repository"] == "test/repo"
        assert entry.context.extra["commits"] == 100


class TestLogPhaseEnum:
    """Test LogPhase enumeration."""

    def test_phase_values(self):
        """Test that all expected phases exist."""
        phases = [
            LogPhase.INITIALIZATION,
            LogPhase.DISCOVERY,
            LogPhase.COLLECTION,
            LogPhase.AGGREGATION,
            LogPhase.RENDERING,
            LogPhase.FINALIZATION,
            LogPhase.API_CALL,
            LogPhase.GIT_OPERATION,
            LogPhase.VALIDATION,
        ]
        for phase in phases:
            assert isinstance(phase.value, str)
            assert phase.value  # Non-empty

    def test_phase_in_context(self):
        """Test using phase in context."""
        ctx = LogContext(phase=LogPhase.COLLECTION)
        assert ctx.phase == LogPhase.COLLECTION
        assert ctx.to_dict()["phase"] == "collection"


class TestIntegration:
    """Integration tests for structured logging."""

    def test_full_workflow(self):
        """Test complete logging workflow."""
        logger = create_structured_logger("test")

        # Simulate repository processing
        with logger.context(repository="foo/bar", phase=LogPhase.COLLECTION):
            logger.info("Starting collection")

            with logger.timed("git_log"):
                time.sleep(0.01)

            logger.debug("Collection complete", commits=100)

            with logger.context(window="1y"):
                logger.info("Processing window")

        # Verify aggregation
        summary = logger.get_summary()
        assert summary["total_entries"] == 4  # info, debug (timed), debug, info
        assert "performance_by_phase" in summary

        # Check that all entries have correct repository
        for entry in logger.aggregator.entries[:3]:  # Except last one
            assert entry.context.repository == "foo/bar"

    def test_error_tracking_workflow(self):
        """Test error tracking across multiple repositories."""
        logger = create_structured_logger("test")

        # Repo 1: Success
        with logger.context(repository="repo1"):
            logger.info("Success")

        # Repo 2: Warnings
        with logger.context(repository="repo2"):
            logger.warning("Minor issue 1")
            logger.warning("Minor issue 2")

        # Repo 3: Errors
        with logger.context(repository="repo3"):
            logger.error("Critical failure")

        summary = logger.get_summary()
        assert summary["log_summary"]["WARNING"] == 2
        assert summary["log_summary"]["ERROR"] == 1

        partial = logger.get_partial_failures()
        assert len(partial) == 1
        assert partial[0]["repository"] == "repo2"
