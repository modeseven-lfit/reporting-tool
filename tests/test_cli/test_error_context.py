# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for Enhanced Error Context System

Tests all new functionality added in Phase 13, Step 4:
- ErrorContext class and formatting
- Auto-detection of error contexts
- Recovery hints generation
- Context-aware error messages
- Integration with existing error classes

Phase 13, Step 4: Enhanced Error Messages
"""

from pathlib import Path

import pytest

from cli.error_context import (
    ErrorContext,
    auto_detect_error_context,
    detect_disk_space_error,
    detect_github_auth_error,
    detect_invalid_yaml,
    detect_missing_config,
    detect_missing_repos_path,
    detect_network_error,
    detect_permission_error,
    detect_rate_limit_error,
    detect_validation_error,
)
from cli.errors import (
    APIError,
    CLIError,
    ConfigurationError,
    DiskSpaceError,
    NetworkError,
    PermissionError,
    ValidationError,
)


class TestErrorContext:
    """Test ErrorContext class and formatting."""

    def test_error_context_creation(self):
        """Test creating an error context."""
        ctx = ErrorContext(
            error_type="Test Error",
            message="Something went wrong",
            context={"key": "value"},
            recovery_hints=["Fix it"],
            examples=["example code"],
            related_errors=["Related error"],
            doc_links=["docs/test.md"],
        )

        assert ctx.error_type == "Test Error"
        assert ctx.message == "Something went wrong"
        assert ctx.context["key"] == "value"
        assert "Fix it" in ctx.recovery_hints
        assert "example code" in ctx.examples
        assert "Related error" in ctx.related_errors
        assert "docs/test.md" in ctx.doc_links

    def test_error_context_format_basic(self):
        """Test basic error context formatting."""
        ctx = ErrorContext(error_type="Test Error", message="Test message")

        output = ctx.format()
        assert "❌" in output
        assert "Test Error" in output
        assert "Test message" in output

    def test_error_context_format_with_context(self):
        """Test formatting with context information."""
        ctx = ErrorContext(
            error_type="Test Error",
            message="Test message",
            context={"file": "test.yaml", "line": 42},
        )

        output = ctx.format()
        assert "📋 Context:" in output
        assert "file" in output
        assert "test.yaml" in output
        assert "line" in output
        assert "42" in output

    def test_error_context_format_with_recovery_hints(self):
        """Test formatting with recovery hints."""
        ctx = ErrorContext(
            error_type="Test Error",
            message="Test message",
            recovery_hints=["First step", "Second step", "Third step"],
        )

        output = ctx.format()
        assert "🔧 How to fix:" in output
        assert "1. First step" in output
        assert "2. Second step" in output
        assert "3. Third step" in output

    def test_error_context_format_verbose(self):
        """Test verbose formatting includes examples and related errors."""
        ctx = ErrorContext(
            error_type="Test Error",
            message="Test message",
            examples=["example 1", "example 2"],
            related_errors=["Error A", "Error B"],
        )

        # Non-verbose should not include examples/related
        output = ctx.format(verbose=False)
        assert "example 1" not in output
        assert "Error A" not in output

        # Verbose should include them
        output_verbose = ctx.format(verbose=True)
        assert "💡 Examples:" in output_verbose
        assert "example 1" in output_verbose
        assert "🔗 Related issues:" in output_verbose
        assert "Error A" in output_verbose

    def test_error_context_format_with_doc_links(self):
        """Test formatting includes documentation links."""
        ctx = ErrorContext(
            error_type="Test Error",
            message="Test message",
            doc_links=["docs/guide.md", "docs/api.md"],
        )

        output = ctx.format()
        assert "📖 Documentation:" in output
        assert "docs/guide.md" in output
        assert "docs/api.md" in output


class TestDetectMissingConfig:
    """Test missing configuration detection."""

    def test_detect_missing_config(self):
        """Test detecting missing config file."""
        ctx = detect_missing_config()

        assert ctx.error_type == "Configuration Error"
        assert "not found" in ctx.message.lower()
        assert len(ctx.recovery_hints) > 0
        assert any("config.example.yaml" in hint for hint in ctx.recovery_hints)
        assert len(ctx.examples) > 0
        assert len(ctx.doc_links) > 0

    def test_missing_config_has_recovery_steps(self):
        """Test missing config provides step-by-step recovery."""
        ctx = detect_missing_config()

        # Should have concrete steps
        assert any("copy" in hint.lower() for hint in ctx.recovery_hints)
        assert any("edit" in hint.lower() for hint in ctx.recovery_hints)

    def test_missing_config_has_examples(self):
        """Test missing config includes command examples."""
        ctx = detect_missing_config()

        examples_text = " ".join(ctx.examples)
        assert "cp" in examples_text or "copy" in examples_text


class TestDetectInvalidYAML:
    """Test YAML syntax error detection."""

    def test_detect_invalid_yaml(self):
        """Test detecting invalid YAML syntax."""
        ctx = detect_invalid_yaml(Path("config.yaml"))

        assert ctx.error_type == "YAML Syntax Error"
        assert "config.yaml" in ctx.message
        assert "file" in ctx.context
        assert len(ctx.recovery_hints) > 0

    def test_invalid_yaml_with_line_number(self):
        """Test YAML error with line number context."""
        ctx = detect_invalid_yaml(Path("config.yaml"), line=42)

        assert ctx.context["line"] == 42
        assert "config.yaml" in ctx.message

    def test_invalid_yaml_has_common_causes(self):
        """Test YAML error mentions common causes."""
        ctx = detect_invalid_yaml(Path("test.yaml"))

        assert "common_causes" in ctx.context
        recovery_text = " ".join(ctx.recovery_hints).lower()
        assert "indent" in recovery_text or "tab" in recovery_text

    def test_invalid_yaml_has_examples(self):
        """Test YAML error includes correct/wrong examples."""
        ctx = detect_invalid_yaml(Path("test.yaml"))

        examples_text = " ".join(ctx.examples)
        assert "✓" in examples_text  # Correct example marker
        assert "✗" in examples_text  # Wrong example marker


class TestDetectMissingReposPath:
    """Test missing repositories path detection."""

    def test_detect_missing_repos_path(self):
        """Test detecting missing repos directory."""
        ctx = detect_missing_repos_path(Path("/nonexistent/path"))

        assert ctx.error_type == "Invalid Argument"
        assert "does not exist" in ctx.message
        assert "/nonexistent/path" in str(ctx.context["provided_path"])

    def test_missing_repos_has_recovery_hints(self):
        """Test repos path error has recovery hints."""
        ctx = detect_missing_repos_path(Path("~/repos"))

        recovery_text = " ".join(ctx.recovery_hints).lower()
        assert "clone" in recovery_text or "create" in recovery_text
        assert "verify" in recovery_text or "check" in recovery_text

    def test_missing_repos_has_examples(self):
        """Test repos path error includes git clone examples."""
        ctx = detect_missing_repos_path(Path("/path/to/repos"))

        examples_text = " ".join(ctx.examples)
        assert "git clone" in examples_text or "mkdir" in examples_text


class TestDetectGitHubAuthError:
    """Test GitHub authentication error detection."""

    def test_detect_github_auth_401(self):
        """Test detecting 401 unauthorized error."""
        ctx = detect_github_auth_error(status_code=401)

        assert ctx.error_type == "API Authentication Error"
        assert "invalid token" in ctx.message.lower()
        assert ctx.context["status_code"] == 401
        assert any("token" in hint.lower() for hint in ctx.recovery_hints)

    def test_detect_github_auth_403(self):
        """Test detecting 403 forbidden error."""
        ctx = detect_github_auth_error(status_code=403)

        assert ctx.error_type == "API Authentication Error"
        assert "forbidden" in ctx.message.lower()
        assert ctx.context["status_code"] == 403
        assert any(
            "permission" in hint.lower() or "scope" in hint.lower() for hint in ctx.recovery_hints
        )

    def test_detect_github_auth_no_status(self):
        """Test GitHub auth error without status code."""
        ctx = detect_github_auth_error()

        assert ctx.error_type == "API Authentication Error"
        assert "api" in ctx.context
        assert len(ctx.recovery_hints) > 0

    def test_github_auth_has_token_examples(self):
        """Test GitHub auth error includes token setup examples."""
        ctx = detect_github_auth_error()

        examples_text = " ".join(ctx.examples)
        assert "GITHUB_TOKEN" in examples_text
        assert "export" in examples_text or "environment" in examples_text.lower()

    def test_github_auth_has_scope_info(self):
        """Test GitHub auth error mentions required scopes."""
        ctx = detect_github_auth_error()

        recovery_text = " ".join(ctx.recovery_hints)
        assert "scope" in recovery_text.lower()
        assert "repo" in recovery_text or "read:org" in recovery_text


class TestDetectRateLimitError:
    """Test API rate limit error detection."""

    def test_detect_rate_limit_basic(self):
        """Test basic rate limit detection."""
        ctx = detect_rate_limit_error("GitHub")

        assert ctx.error_type == "API Rate Limit"
        assert "rate limit" in ctx.message.lower()
        assert ctx.context["api"] == "GitHub"

    def test_detect_rate_limit_with_reset_time(self):
        """Test rate limit with reset timestamp."""
        import time

        reset_time = int(time.time()) + 3600  # 1 hour from now

        ctx = detect_rate_limit_error("GitHub", reset_time=reset_time)

        assert "rate_limit_reset" in ctx.context
        assert ctx.context["api"] == "GitHub"

    def test_rate_limit_has_recovery_hints(self):
        """Test rate limit error provides recovery strategies."""
        ctx = detect_rate_limit_error("GitHub")

        recovery_text = " ".join(ctx.recovery_hints).lower()
        assert "wait" in recovery_text
        assert "cache" in recovery_text or "token" in recovery_text

    def test_rate_limit_has_workarounds(self):
        """Test rate limit error suggests workarounds."""
        ctx = detect_rate_limit_error("GitHub")

        examples_text = " ".join(ctx.examples).lower()
        assert "cache" in examples_text or "workers" in examples_text


class TestDetectNetworkError:
    """Test network error detection."""

    def test_detect_network_error_basic(self):
        """Test basic network error."""
        ctx = detect_network_error()

        assert ctx.error_type == "Network Error"
        assert "connectivity" in ctx.message.lower()
        assert len(ctx.recovery_hints) > 0

    def test_detect_network_error_with_url(self):
        """Test network error with URL."""
        ctx = detect_network_error(url="https://api.github.com")

        assert "api.github.com" in ctx.message
        assert "url" in ctx.context

    def test_detect_timeout_error(self):
        """Test timeout-specific error."""
        ctx = detect_network_error(error_type="timeout")

        recovery_text = " ".join(ctx.recovery_hints).lower()
        assert "timeout" in recovery_text

    def test_detect_dns_error(self):
        """Test DNS-specific error."""
        ctx = detect_network_error(error_type="dns")

        recovery_text = " ".join(ctx.recovery_hints).lower()
        assert "dns" in recovery_text
        examples_text = " ".join(ctx.examples)
        assert "ping" in examples_text or "nslookup" in examples_text

    def test_detect_ssl_error(self):
        """Test SSL certificate error."""
        ctx = detect_network_error(error_type="ssl")

        recovery_text = " ".join(ctx.recovery_hints).lower()
        assert "ssl" in recovery_text or "certificate" in recovery_text


class TestDetectPermissionError:
    """Test permission error detection."""

    def test_detect_permission_error(self):
        """Test basic permission error."""
        ctx = detect_permission_error(Path("/test/path"))

        assert ctx.error_type == "Permission Error"
        assert "Permission denied" in ctx.message
        assert "/test/path" in str(ctx.context["path"])

    def test_permission_error_with_operation(self):
        """Test permission error with operation context."""
        ctx = detect_permission_error(Path("/test/file"), operation="write")

        assert ctx.context["operation"] == "write"
        assert "write" in ctx.message

    def test_permission_error_has_recovery_hints(self):
        """Test permission error provides recovery steps."""
        ctx = detect_permission_error(Path("/test/path"))

        recovery_text = " ".join(ctx.recovery_hints).lower()
        assert "permission" in recovery_text
        assert "chmod" in recovery_text or "directory" in recovery_text


class TestDetectDiskSpaceError:
    """Test disk space error detection."""

    def test_detect_disk_space_error(self):
        """Test disk space error."""
        ctx = detect_disk_space_error(Path("/tmp"))

        assert ctx.error_type == "Disk Space Error"
        assert "disk space" in ctx.message.lower()
        assert "/tmp" in str(ctx.context["path"])

    def test_disk_space_has_recovery_hints(self):
        """Test disk space error has recovery strategies."""
        ctx = detect_disk_space_error(Path("/"))

        recovery_text = " ".join(ctx.recovery_hints).lower()
        assert "free" in recovery_text or "space" in recovery_text
        assert "cache" in recovery_text or "output" in recovery_text

    def test_disk_space_has_examples(self):
        """Test disk space error includes command examples."""
        ctx = detect_disk_space_error(Path("/tmp"))

        examples_text = " ".join(ctx.examples)
        assert "df" in examples_text or "--no-cache" in examples_text


class TestDetectValidationError:
    """Test validation error detection."""

    def test_detect_validation_error(self):
        """Test basic validation error."""
        ctx = detect_validation_error(field="project", value="", expected="non-empty string")

        assert ctx.error_type == "Validation Error"
        assert "project" in ctx.message
        assert ctx.context["field"] == "project"
        assert ctx.context["expected_format"] == "non-empty string"

    def test_validation_error_with_config_path(self):
        """Test validation error with config file context."""
        ctx = detect_validation_error(
            field="api.github.token",
            value="invalid",
            expected="valid GitHub token",
            config_path=Path("config.yaml"),
        )

        assert "config_file" in ctx.context
        assert "config.yaml" in str(ctx.context["config_file"])

    def test_validation_error_has_recovery_hints(self):
        """Test validation error provides fix instructions."""
        ctx = detect_validation_error(field="workers", value="-1", expected="positive integer")

        recovery_text = " ".join(ctx.recovery_hints).lower()
        assert "update" in recovery_text or "fix" in recovery_text
        assert "validate" in recovery_text or "dry-run" in recovery_text


class TestAutoDetectErrorContext:
    """Test automatic error context detection."""

    def test_auto_detect_file_not_found(self):
        """Test auto-detection of file not found errors."""
        error = FileNotFoundError("config.yaml not found")
        ctx = auto_detect_error_context(error)

        assert "Configuration Error" in ctx.error_type or "config" in ctx.message.lower()
        assert len(ctx.recovery_hints) > 0

    def test_auto_detect_permission_error(self):
        """Test auto-detection of permission errors."""
        error = PermissionError("Permission denied")
        ctx = auto_detect_error_context(error, path="/test/path")

        assert "Permission" in ctx.error_type
        assert len(ctx.recovery_hints) > 0

    def test_auto_detect_yaml_error(self):
        """Test auto-detection of YAML errors."""

        class YAMLError(Exception):
            pass

        error = YAMLError("Invalid YAML syntax")
        ctx = auto_detect_error_context(error, path="config.yaml")

        assert "YAML" in ctx.error_type
        assert len(ctx.recovery_hints) > 0

    def test_auto_detect_network_timeout(self):
        """Test auto-detection of network timeout."""
        error = Exception("Connection timeout")
        ctx = auto_detect_error_context(error, url="https://api.github.com")

        assert "Network" in ctx.error_type
        assert "timeout" in ctx.message.lower()

    def test_auto_detect_401_error(self):
        """Test auto-detection of 401 authentication error."""
        error = Exception("401 Unauthorized")
        ctx = auto_detect_error_context(error)

        assert "Authentication" in ctx.error_type or "401" in ctx.message
        assert any("token" in hint.lower() for hint in ctx.recovery_hints)

    def test_auto_detect_rate_limit(self):
        """Test auto-detection of rate limit errors."""
        error = Exception("403 rate limit exceeded")
        ctx = auto_detect_error_context(error, api_name="GitHub")

        assert "Rate Limit" in ctx.error_type or "rate limit" in ctx.message.lower()

    def test_auto_detect_generic_fallback(self):
        """Test fallback for unknown error types."""
        error = Exception("Some unknown error")
        ctx = auto_detect_error_context(error, custom_key="custom_value")

        assert ctx.error_type == "Exception"
        assert "Some unknown error" in ctx.message
        assert "custom_key" in ctx.context


class TestEnhancedCLIError:
    """Test enhanced CLI error classes with context."""

    def test_cli_error_with_context(self):
        """Test CLIError with context dictionary."""
        error = CLIError("Test error", context={"key": "value", "count": 42})

        output = str(error)
        assert "📋 Context:" in output
        assert "key" in output
        assert "value" in output
        assert "42" in output

    def test_cli_error_with_recovery_hints(self):
        """Test CLIError with recovery hints."""
        error = CLIError("Test error", recovery_hints=["Step 1", "Step 2", "Step 3"])

        output = str(error)
        assert "🔧 How to fix:" in output
        assert "1. Step 1" in output
        assert "2. Step 2" in output
        assert "3. Step 3" in output

    def test_cli_error_backward_compatible(self):
        """Test CLIError is backward compatible with suggestion."""
        error = CLIError("Test error", suggestion="Try this fix")

        output = str(error)
        assert "💡 Suggestion:" in output
        assert "Try this fix" in output

    def test_cli_error_add_context(self):
        """Test adding context to error."""
        error = CLIError("Test error")
        error.add_context("file", "test.txt")
        error.add_context("line", 42)

        assert error.context["file"] == "test.txt"
        assert error.context["line"] == 42

    def test_cli_error_add_recovery_hint(self):
        """Test adding recovery hints to error."""
        error = CLIError("Test error")
        error.add_recovery_hint("First hint")
        error.add_recovery_hint("Second hint")

        assert "First hint" in error.recovery_hints
        assert "Second hint" in error.recovery_hints

    def test_cli_error_chaining(self):
        """Test method chaining for error configuration."""
        error = CLIError("Test error").add_context("key", "value").add_recovery_hint("Fix it")

        assert error.context["key"] == "value"
        assert "Fix it" in error.recovery_hints


class TestEnhancedConfigurationError:
    """Test enhanced ConfigurationError."""

    def test_configuration_error_has_default_hints(self):
        """Test ConfigurationError has default recovery hints."""
        error = ConfigurationError("Invalid config")

        output = str(error)
        assert "🔧 How to fix:" in output
        assert len(error.recovery_hints) > 0

    def test_configuration_error_custom_hints(self):
        """Test ConfigurationError with custom recovery hints."""
        error = ConfigurationError(
            "Invalid config", recovery_hints=["Custom hint 1", "Custom hint 2"]
        )

        assert "Custom hint 1" in error.recovery_hints
        assert "Custom hint 2" in error.recovery_hints

    def test_configuration_error_with_context(self):
        """Test ConfigurationError with context."""
        error = ConfigurationError(
            "Invalid config", context={"file": "config.yaml", "field": "project"}
        )

        output = str(error)
        assert "📋 Context:" in output
        assert "config.yaml" in output


class TestEnhancedAPIError:
    """Test enhanced APIError."""

    def test_api_error_with_status_code(self):
        """Test APIError includes status code in context."""
        error = APIError("Request failed", api_name="GitHub", status_code=401)

        assert error.context["status_code"] == 401
        assert error.context["api"] == "GitHub"

    def test_api_error_401_hints(self):
        """Test APIError provides specific hints for 401."""
        error = APIError("Unauthorized", status_code=401)

        recovery_text = " ".join(error.recovery_hints).lower()
        assert "token" in recovery_text
        assert "expired" in recovery_text or "permissions" in recovery_text

    def test_api_error_403_hints(self):
        """Test APIError provides specific hints for 403."""
        error = APIError("Forbidden", status_code=403)

        recovery_text = " ".join(error.recovery_hints).lower()
        assert "permission" in recovery_text or "scope" in recovery_text

    def test_api_error_404_hints(self):
        """Test APIError provides specific hints for 404."""
        error = APIError("Not found", status_code=404)

        recovery_text = " ".join(error.recovery_hints).lower()
        assert "exists" in recovery_text or "verify" in recovery_text


class TestEnhancedPermissionError:
    """Test enhanced PermissionError."""

    def test_permission_error_has_default_hints(self):
        """Test PermissionError has default recovery hints."""
        error = PermissionError("Permission denied", path="/test/path")

        assert len(error.recovery_hints) > 0
        recovery_text = " ".join(error.recovery_hints).lower()
        assert "permission" in recovery_text
        assert "chmod" in recovery_text or "ls -la" in recovery_text


class TestEnhancedDiskSpaceError:
    """Test enhanced DiskSpaceError."""

    def test_disk_space_error_has_recovery_hints(self):
        """Test DiskSpaceError has recovery strategies."""
        error = DiskSpaceError("Out of space", path="/tmp")

        assert len(error.recovery_hints) > 0
        recovery_text = " ".join(error.recovery_hints).lower()
        assert "space" in recovery_text
        assert "cache" in recovery_text or "df" in recovery_text


class TestEnhancedValidationError:
    """Test enhanced ValidationError."""

    def test_validation_error_has_default_hints(self):
        """Test ValidationError has default recovery hints."""
        error = ValidationError("Invalid value", field="project")

        assert len(error.recovery_hints) > 0
        recovery_text = " ".join(error.recovery_hints).lower()
        assert "check" in recovery_text or "validate" in recovery_text


class TestEnhancedNetworkError:
    """Test enhanced NetworkError."""

    def test_network_error_has_default_hints(self):
        """Test NetworkError has default recovery hints."""
        error = NetworkError("Connection failed")

        assert len(error.recovery_hints) > 0
        recovery_text = " ".join(error.recovery_hints).lower()
        assert "network" in recovery_text or "connectivity" in recovery_text


class TestIntegration:
    """Integration tests for error context system."""

    def test_error_context_flow(self):
        """Test complete error context workflow."""
        # Create error
        error = FileNotFoundError("config.yaml not found")

        # Auto-detect context
        ctx = auto_detect_error_context(error)

        # Format for display
        output = ctx.format(verbose=True)

        # Verify complete output
        assert "❌" in output
        assert len(output) > 100  # Should be substantial
        assert "Context:" in output or "How to fix:" in output

    def test_cli_error_with_auto_context(self):
        """Test integrating auto-detected context with CLI errors."""
        # Simulate catching an error and wrapping it
        try:
            raise FileNotFoundError("config.yaml")
        except FileNotFoundError as e:
            ctx = auto_detect_error_context(e)
            cli_error = ConfigurationError(
                ctx.message, context=ctx.context, recovery_hints=ctx.recovery_hints
            )

            output = str(cli_error)
            assert "🔧 How to fix:" in output
            assert len(cli_error.recovery_hints) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
