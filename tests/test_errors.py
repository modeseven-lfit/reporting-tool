# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for error taxonomy and classification system.

Tests error types, classification, tracking, and aggregation.
"""

from observability.errors import (
    ERROR_TYPE_CATEGORY_MAP,
    ERROR_TYPE_SEVERITY_MAP,
    ClassifiedError,
    ErrorCategory,
    ErrorContext,
    ErrorSeverity,
    ErrorTracker,
    ErrorType,
    classify_exception,
)


class TestErrorContext:
    """Test ErrorContext functionality."""

    def test_empty_context(self):
        """Test creating an empty context."""
        ctx = ErrorContext()
        assert ctx.repository is None
        assert ctx.operation is None
        assert ctx.phase is None
        assert ctx.window is None
        assert ctx.extra == {}

    def test_context_with_values(self):
        """Test creating context with values."""
        ctx = ErrorContext(
            repository="foo/bar",
            operation="git_log",
            phase="collection",
            window="1y",
            extra={"attempts": 3},
        )
        assert ctx.repository == "foo/bar"
        assert ctx.operation == "git_log"
        assert ctx.phase == "collection"
        assert ctx.window == "1y"
        assert ctx.extra == {"attempts": 3}

    def test_to_dict_empty(self):
        """Test converting empty context to dict."""
        ctx = ErrorContext()
        result = ctx.to_dict()
        assert result == {}

    def test_to_dict_with_values(self):
        """Test converting populated context to dict."""
        ctx = ErrorContext(
            repository="test/repo",
            operation="test_op",
            phase="rendering",
        )
        result = ctx.to_dict()
        assert result == {
            "repository": "test/repo",
            "operation": "test_op",
            "phase": "rendering",
        }

    def test_to_dict_includes_extra(self):
        """Test that extra fields are included in dict."""
        ctx = ErrorContext(
            repository="repo",
            extra={"foo": "bar", "count": 42},
        )
        result = ctx.to_dict()
        assert result["repository"] == "repo"
        assert result["foo"] == "bar"
        assert result["count"] == 42


class TestClassifiedError:
    """Test ClassifiedError functionality."""

    def test_create_error(self):
        """Test creating a classified error."""
        error = ClassifiedError(
            error_type=ErrorType.GIT_COMMAND_FAILED,
            message="Git command failed",
        )
        assert error.error_type == ErrorType.GIT_COMMAND_FAILED
        assert error.message == "Git command failed"
        assert error.severity is not None  # Auto-assigned
        assert error.category is not None  # Auto-assigned

    def test_auto_assign_severity(self):
        """Test that severity is auto-assigned based on type."""
        error = ClassifiedError(
            error_type=ErrorType.CONFIG_MISSING,
            message="Config not found",
        )
        assert error.severity == ErrorSeverity.CRITICAL

    def test_auto_assign_category(self):
        """Test that category is auto-assigned based on type."""
        error = ClassifiedError(
            error_type=ErrorType.GIT_NOT_FOUND,
            message="Repository not found",
        )
        assert error.category == ErrorCategory.GIT

    def test_explicit_severity(self):
        """Test providing explicit severity."""
        error = ClassifiedError(
            error_type=ErrorType.API_TIMEOUT,
            message="Timeout",
            severity=ErrorSeverity.HIGH,
        )
        assert error.severity == ErrorSeverity.HIGH

    def test_with_context(self):
        """Test error with context."""
        ctx = ErrorContext(repository="test/repo", operation="fetch")
        error = ClassifiedError(
            error_type=ErrorType.API_TIMEOUT,
            message="Timeout",
            context=ctx,
        )
        assert error.context.repository == "test/repo"
        assert error.context.operation == "fetch"

    def test_with_original_exception(self):
        """Test storing original exception."""
        exc = ValueError("Invalid value")
        error = ClassifiedError(
            error_type=ErrorType.VALIDATION_TYPE,
            message="Validation failed",
            original_exception=exc,
        )
        assert error.original_exception is exc

    def test_to_dict_basic(self):
        """Test converting error to dict."""
        error = ClassifiedError(
            error_type=ErrorType.GIT_PARSE_ERROR,
            message="Parse failed",
        )
        result = error.to_dict()
        assert result["error_type"] == "git_parse_error"
        assert result["category"] == "git"
        assert result["severity"] == "medium"
        assert result["message"] == "Parse failed"

    def test_to_dict_with_context(self):
        """Test dict includes context."""
        ctx = ErrorContext(repository="foo/bar")
        error = ClassifiedError(
            error_type=ErrorType.GIT_COMMAND_FAILED,
            message="Failed",
            context=ctx,
        )
        result = error.to_dict()
        assert "context" in result
        assert result["context"]["repository"] == "foo/bar"

    def test_to_dict_with_exception(self):
        """Test dict includes exception type."""
        exc = OSError("File not found")
        error = ClassifiedError(
            error_type=ErrorType.SYSTEM_IO,
            message="IO error",
            original_exception=exc,
        )
        result = error.to_dict()
        assert result["exception_type"] == "OSError"


class TestErrorTracker:
    """Test ErrorTracker functionality."""

    def test_empty_tracker(self):
        """Test newly created tracker is empty."""
        tracker = ErrorTracker()
        assert tracker.get_error_count() == 0
        assert len(tracker.errors) == 0

    def test_add_error(self):
        """Test adding an error."""
        tracker = ErrorTracker()
        error = tracker.add_error(
            ErrorType.GIT_COMMAND_FAILED,
            "Command failed",
        )
        assert isinstance(error, ClassifiedError)
        assert tracker.get_error_count() == 1

    def test_add_error_with_context(self):
        """Test adding error with context."""
        tracker = ErrorTracker()
        ctx = ErrorContext(repository="test/repo")
        tracker.add_error(
            ErrorType.GIT_NOT_FOUND,
            "Not found",
            context=ctx,
        )
        assert len(tracker.errors_by_repo["test/repo"]) == 1

    def test_errors_by_type(self):
        """Test grouping errors by type."""
        tracker = ErrorTracker()
        tracker.add_error(ErrorType.API_TIMEOUT, "Timeout 1")
        tracker.add_error(ErrorType.API_TIMEOUT, "Timeout 2")
        tracker.add_error(ErrorType.GIT_NOT_FOUND, "Not found")

        api_timeouts = tracker.get_errors_by_type(ErrorType.API_TIMEOUT)
        assert len(api_timeouts) == 2

    def test_errors_by_category(self):
        """Test grouping errors by category."""
        tracker = ErrorTracker()
        tracker.add_error(ErrorType.GIT_COMMAND_FAILED, "Git error 1")
        tracker.add_error(ErrorType.GIT_PARSE_ERROR, "Git error 2")
        tracker.add_error(ErrorType.API_TIMEOUT, "API error")

        git_errors = tracker.get_errors_by_category(ErrorCategory.GIT)
        assert len(git_errors) == 2

    def test_errors_by_severity(self):
        """Test grouping errors by severity."""
        tracker = ErrorTracker()
        tracker.add_error(ErrorType.CONFIG_MISSING, "Critical")
        tracker.add_error(ErrorType.API_TIMEOUT, "Medium")

        critical = tracker.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical) == 1
        assert critical[0].error_type == ErrorType.CONFIG_MISSING

    def test_errors_by_repository(self):
        """Test grouping errors by repository."""
        tracker = ErrorTracker()
        ctx1 = ErrorContext(repository="repo1")
        ctx2 = ErrorContext(repository="repo2")

        tracker.add_error(ErrorType.GIT_NOT_FOUND, "Error 1", context=ctx1)
        tracker.add_error(ErrorType.GIT_COMMAND_FAILED, "Error 2", context=ctx1)
        tracker.add_error(ErrorType.API_TIMEOUT, "Error 3", context=ctx2)

        repo1_errors = tracker.get_errors_by_repository("repo1")
        assert len(repo1_errors) == 2

    def test_get_summary(self):
        """Test getting error summary."""
        tracker = ErrorTracker()
        tracker.add_error(ErrorType.CONFIG_MISSING, "Config error")
        tracker.add_error(ErrorType.API_TIMEOUT, "API error")
        tracker.add_error(ErrorType.GIT_COMMAND_FAILED, "Git error")

        summary = tracker.get_summary()
        assert summary["total_errors"] == 3
        assert "by_severity" in summary
        assert "by_category" in summary
        assert "by_type" in summary

    def test_get_summary_severity_counts(self):
        """Test summary includes severity counts."""
        tracker = ErrorTracker()
        tracker.add_error(ErrorType.CONFIG_MISSING, "Critical 1")
        tracker.add_error(ErrorType.CONFIG_INVALID, "Critical 2")
        tracker.add_error(ErrorType.API_TIMEOUT, "Medium")

        summary = tracker.get_summary()
        assert summary["by_severity"]["critical"] == 2
        assert summary["by_severity"]["medium"] == 1

    def test_get_summary_category_counts(self):
        """Test summary includes category counts."""
        tracker = ErrorTracker()
        tracker.add_error(ErrorType.GIT_COMMAND_FAILED, "Git 1")
        tracker.add_error(ErrorType.GIT_PARSE_ERROR, "Git 2")
        tracker.add_error(ErrorType.API_TIMEOUT, "API")

        summary = tracker.get_summary()
        assert summary["by_category"]["git"] == 2
        assert summary["by_category"]["api"] == 1

    def test_get_summary_type_counts(self):
        """Test summary includes type counts."""
        tracker = ErrorTracker()
        tracker.add_error(ErrorType.API_TIMEOUT, "Timeout 1")
        tracker.add_error(ErrorType.API_TIMEOUT, "Timeout 2")

        summary = tracker.get_summary()
        assert summary["by_type"]["api_timeout"] == 2

    def test_get_summary_repositories_affected(self):
        """Test summary counts affected repositories."""
        tracker = ErrorTracker()
        ctx1 = ErrorContext(repository="repo1")
        ctx2 = ErrorContext(repository="repo2")

        tracker.add_error(ErrorType.GIT_NOT_FOUND, "Error", context=ctx1)
        tracker.add_error(ErrorType.API_TIMEOUT, "Error", context=ctx2)

        summary = tracker.get_summary()
        assert summary["repositories_affected"] == 2

    def test_get_api_failures_empty(self):
        """Test API failures when no API errors."""
        tracker = ErrorTracker()
        tracker.add_error(ErrorType.GIT_COMMAND_FAILED, "Git error")

        api_failures = tracker.get_api_failures()
        assert api_failures == {}

    def test_get_api_failures(self):
        """Test getting API failure summary."""
        tracker = ErrorTracker()
        tracker.add_error(ErrorType.API_TIMEOUT, "Timeout")
        tracker.add_error(ErrorType.API_RATE_LIMIT, "Rate limit")
        tracker.add_error(ErrorType.API_AUTHENTICATION, "Auth failed")

        api_failures = tracker.get_api_failures()
        assert api_failures["total_api_errors"] == 3
        assert api_failures["rate_limit_hits"] == 1
        assert api_failures["authentication_failures"] == 1

    def test_get_partial_failures(self):
        """Test identifying partial failures."""
        tracker = ErrorTracker()

        # Repo with only low/medium severity errors
        ctx1 = ErrorContext(repository="repo1")
        tracker.add_error(ErrorType.API_TIMEOUT, "Timeout", context=ctx1)
        tracker.add_error(ErrorType.GIT_PARSE_ERROR, "Parse", context=ctx1)

        # Repo with critical error
        ctx2 = ErrorContext(repository="repo2")
        tracker.add_error(ErrorType.CONFIG_MISSING, "Critical", context=ctx2)

        partial = tracker.get_partial_failures()
        assert len(partial) == 1
        assert partial[0]["repository"] == "repo1"
        assert partial[0]["error_count"] == 2

    def test_partial_failures_severity_breakdown(self):
        """Test partial failures include severity breakdown."""
        tracker = ErrorTracker()
        ctx = ErrorContext(repository="test/repo")

        tracker.add_error(ErrorType.API_TIMEOUT, "Medium 1", context=ctx)
        tracker.add_error(ErrorType.API_PARSE, "Medium 2", context=ctx)
        tracker.add_error(ErrorType.API_NOT_FOUND, "Low", context=ctx)

        partial = tracker.get_partial_failures()
        assert len(partial) == 1
        breakdown = partial[0]["severity_breakdown"]
        assert breakdown["medium"] == 2
        assert breakdown["low"] == 1

    def test_partial_failures_sample_errors(self):
        """Test partial failures include sample error messages."""
        tracker = ErrorTracker()
        ctx = ErrorContext(repository="test/repo")

        tracker.add_error(ErrorType.GIT_PARSE_ERROR, "Error 1", context=ctx)
        tracker.add_error(ErrorType.GIT_COMMAND_FAILED, "Error 2", context=ctx)

        partial = tracker.get_partial_failures()
        assert len(partial[0]["sample_errors"]) == 2
        assert "Error 1" in partial[0]["sample_errors"]
        assert "Error 2" in partial[0]["sample_errors"]

    def test_partial_failures_limits_samples(self):
        """Test that sample errors are limited to 3."""
        tracker = ErrorTracker()
        ctx = ErrorContext(repository="test/repo")

        for i in range(10):
            tracker.add_error(ErrorType.GIT_PARSE_ERROR, f"Error {i}", context=ctx)

        partial = tracker.get_partial_failures()
        assert len(partial[0]["sample_errors"]) == 3

    def test_get_detailed_report(self):
        """Test getting detailed error report."""
        tracker = ErrorTracker()
        ctx = ErrorContext(repository="test/repo")
        tracker.add_error(ErrorType.GIT_COMMAND_FAILED, "Error", context=ctx)

        report = tracker.get_detailed_report()
        assert len(report) == 1
        assert report[0]["error_type"] == "git_command_failed"
        assert report[0]["message"] == "Error"


class TestClassifyException:
    """Test exception classification."""

    def test_classify_timeout_exception(self):
        """Test classifying timeout exceptions."""
        exc = TimeoutError("Connection timed out")
        error = classify_exception(exc)
        assert error.error_type == ErrorType.NETWORK_TIMEOUT

    def test_classify_connection_exception(self):
        """Test classifying connection exceptions."""
        exc = ConnectionError("Failed to connect")
        error = classify_exception(exc)
        assert error.error_type == ErrorType.NETWORK_CONNECTION

    def test_classify_permission_exception(self):
        """Test classifying permission exceptions."""
        exc = PermissionError("Access denied")
        error = classify_exception(exc)
        assert error.error_type == ErrorType.SYSTEM_PERMISSION

    def test_classify_io_exception(self):
        """Test classifying IO exceptions."""
        exc = FileNotFoundError("File not found")
        error = classify_exception(exc)
        assert error.error_type == ErrorType.SYSTEM_IO

    def test_classify_value_exception(self):
        """Test classifying ValueError."""
        exc = ValueError("Invalid value")
        error = classify_exception(exc)
        assert error.error_type == ErrorType.VALIDATION_TYPE

    def test_classify_type_exception(self):
        """Test classifying TypeError."""
        exc = TypeError("Wrong type")
        error = classify_exception(exc)
        assert error.error_type == ErrorType.VALIDATION_TYPE

    def test_classify_unknown_exception(self):
        """Test classifying unknown exception types."""
        exc = RuntimeError("Unknown error")
        error = classify_exception(exc)
        assert error.error_type == ErrorType.SYSTEM_UNKNOWN

    def test_classify_with_context(self):
        """Test classifying exception with context."""
        ctx = ErrorContext(repository="test/repo", operation="git_log")
        exc = ValueError("Invalid")
        error = classify_exception(exc, context=ctx)
        assert error.context.repository == "test/repo"
        assert error.context.operation == "git_log"

    def test_classified_stores_original(self):
        """Test that original exception is stored."""
        exc = ValueError("Test")
        error = classify_exception(exc)
        assert error.original_exception is exc


class TestErrorTypeMappings:
    """Test error type mapping dictionaries."""

    def test_all_types_have_category(self):
        """Test that all error types have a category mapping."""
        for error_type in ErrorType:
            assert error_type in ERROR_TYPE_CATEGORY_MAP

    def test_all_types_have_severity(self):
        """Test that all error types have a severity mapping."""
        for error_type in ErrorType:
            assert error_type in ERROR_TYPE_SEVERITY_MAP

    def test_network_errors_mapped_correctly(self):
        """Test network errors map to NETWORK category."""
        network_types = [
            ErrorType.NETWORK_TIMEOUT,
            ErrorType.NETWORK_CONNECTION,
            ErrorType.NETWORK_DNS,
        ]
        for error_type in network_types:
            assert ERROR_TYPE_CATEGORY_MAP[error_type] == ErrorCategory.NETWORK

    def test_git_errors_mapped_correctly(self):
        """Test git errors map to GIT category."""
        git_types = [
            ErrorType.GIT_NOT_FOUND,
            ErrorType.GIT_COMMAND_FAILED,
            ErrorType.GIT_PARSE_ERROR,
        ]
        for error_type in git_types:
            assert ERROR_TYPE_CATEGORY_MAP[error_type] == ErrorCategory.GIT

    def test_critical_config_errors(self):
        """Test config errors are marked as critical."""
        config_types = [
            ErrorType.CONFIG_MISSING,
            ErrorType.CONFIG_INVALID,
            ErrorType.CONFIG_PARSE,
        ]
        for error_type in config_types:
            assert ERROR_TYPE_SEVERITY_MAP[error_type] == ErrorSeverity.CRITICAL


class TestIntegration:
    """Integration tests for error taxonomy."""

    def test_full_error_tracking_workflow(self):
        """Test complete error tracking workflow."""
        tracker = ErrorTracker()

        # Simulate processing multiple repositories
        repos = ["repo1", "repo2", "repo3"]

        for repo in repos:
            ctx = ErrorContext(repository=repo, phase="collection")

            # Different error types for different repos
            if repo == "repo1":
                tracker.add_error(ErrorType.GIT_COMMAND_FAILED, "Git failed", context=ctx)
            elif repo == "repo2":
                tracker.add_error(ErrorType.API_TIMEOUT, "Timeout 1", context=ctx)
                tracker.add_error(ErrorType.API_TIMEOUT, "Timeout 2", context=ctx)
            else:
                tracker.add_error(ErrorType.CONFIG_MISSING, "No config", context=ctx)

        # Verify tracking
        assert tracker.get_error_count() == 4
        assert len(tracker.errors_by_repo) == 3

        # Get summary
        summary = tracker.get_summary()
        assert summary["total_errors"] == 4
        assert summary["repositories_affected"] == 3
        assert summary["by_category"]["git"] == 1
        assert summary["by_category"]["api"] == 2
        assert summary["by_category"]["configuration"] == 1

    def test_error_severity_escalation(self):
        """Test tracking errors across severity levels."""
        tracker = ErrorTracker()
        ctx = ErrorContext(repository="test/repo")

        # Add errors of different severities
        tracker.add_error(ErrorType.API_NOT_FOUND, "Not found", context=ctx)  # LOW
        tracker.add_error(ErrorType.GIT_PARSE_ERROR, "Parse error", context=ctx)  # MEDIUM
        tracker.add_error(ErrorType.SYSTEM_IO, "IO error", context=ctx)  # HIGH
        tracker.add_error(ErrorType.CONFIG_MISSING, "Config missing", context=ctx)  # CRITICAL

        # Check severity counts
        summary = tracker.get_summary()
        assert summary["by_severity"]["low"] == 1
        assert summary["by_severity"]["medium"] == 1
        assert summary["by_severity"]["high"] == 1
        assert summary["by_severity"]["critical"] == 1

        # Verify critical errors
        critical = tracker.get_errors_by_severity(ErrorSeverity.CRITICAL)
        assert len(critical) == 1
        assert critical[0].error_type == ErrorType.CONFIG_MISSING
