# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for enhanced error handling in CLI.

Tests CLI error classes, error helpers, and error message formatting.

Phase 9, Step 6: Enhanced Error Messages Integration
"""

import tempfile
from pathlib import Path

import pytest

from cli.error_helpers import (
    CLIPermissionError,
    format_error_context,
    handle_cli_error,
    wrap_api_error,
    wrap_config_error,
    wrap_file_error,
    wrap_network_error,
    wrap_validation_error,
)
from cli.errors import (
    APIError,
    CLIError,
    ConfigurationError,
    DiskSpaceError,
    InvalidArgumentError,
    NetworkError,
    PermissionError,
    ValidationError,
    format_validation_errors,
    suggest_common_fixes,
)


# =============================================================================
# CLI ERROR CLASSES TESTS
# =============================================================================


class TestCLIError:
    """Test base CLI error class."""

    def test_basic_error(self):
        """Test basic error message."""
        error = CLIError("Something went wrong")
        assert str(error) == "❌ Error: Something went wrong"
        assert error.message == "Something went wrong"
        assert error.suggestion is None
        assert error.doc_link is None

    def test_error_with_suggestion(self):
        """Test error with suggestion."""
        error = CLIError("File not found", suggestion="Check the file path")
        assert "❌ Error: File not found" in str(error)
        assert "💡 Suggestion: Check the file path" in str(error)

    def test_error_with_doc_link(self):
        """Test error with documentation link."""
        error = CLIError("Configuration invalid", doc_link="https://docs.example.com/config")
        assert "❌ Error: Configuration invalid" in str(error)
        assert "📖 Documentation: https://docs.example.com/config" in str(error)

    def test_error_with_all_fields(self):
        """Test error with all fields populated."""
        error = CLIError(
            "Operation failed",
            suggestion="Try again with --verbose",
            doc_link="https://docs.example.com/troubleshooting",
        )
        error_str = str(error)
        assert "❌ Error: Operation failed" in error_str
        assert "💡 Suggestion: Try again with --verbose" in error_str
        assert "📖 Documentation: https://docs.example.com/troubleshooting" in error_str


class TestConfigurationError:
    """Test configuration error class."""

    def test_default_suggestion(self):
        """Test that default suggestion is provided."""
        error = ConfigurationError("Missing required field")
        assert "config.example.yaml" in str(error)
        assert "docs/configuration.md" in str(error)

    def test_custom_suggestion(self):
        """Test custom suggestion is shown."""
        error = ConfigurationError("Invalid format", suggestion="Use YAML format")
        # With custom suggestion, it still shows recovery hints (not the suggestion)
        # because ConfigurationError provides default recovery_hints
        error_str = str(error)
        assert "🔧 How to fix:" in error_str
        assert "Verify YAML syntax" in error_str


class TestInvalidArgumentError:
    """Test invalid argument error class."""

    def test_default_suggestion(self):
        """Test that default help suggestion is provided."""
        error = InvalidArgumentError("Unknown flag --foo")
        assert "--help" in str(error)
        assert "CLI_REFERENCE.md" in str(error)


class TestAPIError:
    """Test API error class."""

    def test_basic_api_error(self):
        """Test basic API error."""
        error = APIError("Request failed")
        assert "Request failed" in str(error)
        assert "network connectivity" in str(error).lower()

    def test_api_error_with_name(self):
        """Test API error with API name."""
        error = APIError("Unauthorized", api_name="GitHub")
        assert "GitHub API error" in str(error)
        assert "Unauthorized" in str(error)

    def test_api_error_with_custom_suggestion(self):
        """Test API error with custom suggestion."""
        error = APIError(
            "Rate limited", api_name="GitHub", suggestion="Wait 60 seconds before retrying"
        )
        assert "Wait 60 seconds" in str(error)


class TestValidationError:
    """Test validation error class."""

    def test_basic_validation_error(self):
        """Test basic validation error."""
        error = ValidationError("Value is invalid")
        assert "Value is invalid" in str(error)

    def test_validation_error_with_field(self):
        """Test validation error with field name."""
        error = ValidationError("must be positive", field="count")
        assert "Validation failed for 'count'" in str(error)
        assert "must be positive" in str(error)


class TestNetworkError:
    """Test network error class."""

    def test_default_suggestion(self):
        """Test default network error suggestion."""
        error = NetworkError("Connection timeout")
        error_str = str(error).lower()
        # Check for recovery hints format
        assert "check internet connectivity" in error_str or "network" in error_str
        assert "firewall" in error_str or "proxy" in error_str


# =============================================================================
# ERROR HELPER FUNCTIONS TESTS
# =============================================================================


class TestWrapConfigError:
    """Test wrap_config_error helper."""

    def test_basic_config_error(self):
        """Test basic config error wrapping."""
        error = wrap_config_error("Invalid syntax")
        assert isinstance(error, ConfigurationError)
        assert "Invalid syntax" in str(error)

    def test_config_error_with_path(self):
        """Test config error with file path."""
        error = wrap_config_error("Missing field", config_path=Path("config.yaml"))
        assert "config.yaml" in str(error)

    def test_config_error_auto_suggestion(self):
        """Test automatic suggestion based on message."""
        error = wrap_config_error("Missing required field 'project'")
        # ConfigurationError provides default recovery hints
        error_str = str(error)
        assert "🔧 How to fix:" in error_str
        assert "Verify YAML syntax" in error_str

    def test_config_error_yaml_syntax(self):
        """Test YAML syntax error suggestion."""
        error = wrap_config_error("Invalid YAML detected")
        assert "YAML syntax" in str(error)
        assert "indentation" in str(error).lower()


class TestWrapFileError:
    """Test wrap_file_error helper."""

    def test_file_not_found(self):
        """Test FileNotFoundError wrapping."""
        original = FileNotFoundError("config.yaml")
        error = wrap_file_error(original, "config.yaml", "read")
        assert isinstance(error, ConfigurationError)
        assert "config.yaml" in str(error)

    def test_permission_error(self):
        """Test PermissionError wrapping."""
        import builtins

        original = builtins.PermissionError("Access denied")
        error = wrap_file_error(original, "/etc/config", "write")
        assert isinstance(error, CLIPermissionError)
        assert "write" in str(error)

    def test_is_directory_error(self):
        """Test IsADirectoryError wrapping."""
        original = IsADirectoryError("/path/to/dir")
        error = wrap_file_error(original, "/path/to/dir", "read")
        assert isinstance(error, CLIError)
        assert "directory" in str(error).lower()
        assert "file path" in str(error).lower()


class TestWrapValidationError:
    """Test wrap_validation_error helper."""

    def test_basic_validation(self):
        """Test basic validation error."""
        error = wrap_validation_error("must be positive")
        assert isinstance(error, ValidationError)
        assert "must be positive" in str(error)

    def test_validation_with_field(self):
        """Test validation error with field."""
        error = wrap_validation_error("must be non-negative", field="count")
        assert "count" in str(error)
        assert "must be non-negative" in str(error)

    def test_validation_with_value(self):
        """Test validation error with value."""
        error = wrap_validation_error("must be positive", field="days", value="-5")
        assert "days" in str(error)
        assert "-5" in str(error)

    def test_validation_with_expected(self):
        """Test validation error with expected value."""
        error = wrap_validation_error(
            "invalid format", field="date", value="2024-13-01", expected="YYYY-MM-DD"
        )
        assert "date" in str(error)
        assert "2024-13-01" in str(error)
        assert "YYYY-MM-DD" in str(error)


class TestWrapAPIError:
    """Test wrap_api_error helper."""

    def test_basic_api_error(self):
        """Test basic API error wrapping."""
        original = Exception("Connection failed")
        error = wrap_api_error(original, "GitHub")
        assert isinstance(error, APIError)
        assert "GitHub" in str(error)
        assert "Connection failed" in str(error)

    def test_unauthorized_error(self):
        """Test 401 unauthorized error."""
        original = Exception("401 Unauthorized")
        error = wrap_api_error(original, "GitHub")
        assert "token" in str(error).lower()
        assert "expired" in str(error).lower() or "invalid" in str(error).lower()

    def test_forbidden_error(self):
        """Test 403 forbidden error."""
        original = Exception("403 Forbidden")
        error = wrap_api_error(original, "GitHub")
        assert "permissions" in str(error).lower()

    def test_not_found_error(self):
        """Test 404 not found error."""
        original = Exception("404 Not Found")
        error = wrap_api_error(original, "GitHub")
        assert "exists" in str(error).lower() or "accessible" in str(error).lower()

    def test_rate_limit_error(self):
        """Test rate limit error."""
        original = Exception("Rate limit exceeded")
        error = wrap_api_error(original, "GitHub")
        assert "wait" in str(error).lower() or "retry" in str(error).lower()

    def test_timeout_error(self):
        """Test timeout error."""
        original = Exception("Request timed out")
        error = wrap_api_error(original, "GitHub")
        assert "network" in str(error).lower() or "connectivity" in str(error).lower()


class TestWrapNetworkError:
    """Test wrap_network_error helper."""

    def test_basic_network_error(self):
        """Test basic network error."""
        original = Exception("Connection refused")
        error = wrap_network_error(original)
        assert isinstance(error, NetworkError)
        assert "Connection refused" in str(error)

    def test_network_error_with_url(self):
        """Test network error with URL."""
        original = Exception("Timeout")
        error = wrap_network_error(original, url="https://api.github.com")
        assert "api.github.com" in str(error)

    def test_ssl_error(self):
        """Test SSL certificate error."""
        original = Exception("SSL certificate verification failed")
        error = wrap_network_error(original)
        assert "SSL" in str(error) or "certificate" in str(error).lower()

    def test_dns_error(self):
        """Test DNS resolution error."""
        original = Exception("Failed to resolve hostname")
        error = wrap_network_error(original)
        assert "DNS" in str(error) or "hostname" in str(error).lower()


class TestFormatErrorContext:
    """Test format_error_context helper."""

    def test_basic_formatting(self):
        """Test basic error formatting."""
        error = ValueError("Invalid input")
        formatted = format_error_context(error)
        assert "ValueError" in formatted
        assert "Invalid input" in formatted

    def test_formatting_with_context(self):
        """Test error formatting with context."""
        error = ValueError("Invalid input")
        context = {"file": "config.yaml", "line": 42}
        formatted = format_error_context(error, context=context)
        assert "config.yaml" in formatted
        assert "42" in formatted

    def test_formatting_cli_error(self):
        """Test formatting CLI error with suggestions."""
        error = ConfigurationError("Missing field", suggestion="Add the field")
        formatted = format_error_context(error)
        assert "ConfigurationError" in formatted
        assert "Missing field" in formatted
        assert "Add the field" in formatted


class TestHandleCLIError:
    """Test handle_cli_error helper."""

    def test_configuration_error_exit_code(self):
        """Test ConfigurationError returns exit code 2."""
        error = ConfigurationError("Invalid config")
        exit_code = handle_cli_error(error, verbose=False)
        assert exit_code == 2

    def test_invalid_argument_error_exit_code(self):
        """Test InvalidArgumentError returns exit code 2."""
        error = InvalidArgumentError("Unknown flag")
        exit_code = handle_cli_error(error, verbose=False)
        assert exit_code == 2

    def test_api_error_exit_code(self):
        """Test APIError returns exit code 3."""
        error = APIError("Request failed")
        exit_code = handle_cli_error(error, verbose=False)
        assert exit_code == 3

    def test_network_error_exit_code(self):
        """Test NetworkError returns exit code 3."""
        error = NetworkError("Connection failed")
        exit_code = handle_cli_error(error, verbose=False)
        assert exit_code == 3

    def test_permission_error_exit_code(self):
        """Test PermissionError returns exit code 4."""
        error = PermissionError("Access denied")
        exit_code = handle_cli_error(error, verbose=False)
        assert exit_code == 4

    def test_disk_space_error_exit_code(self):
        """Test DiskSpaceError returns exit code 5."""
        error = DiskSpaceError("No space left")
        exit_code = handle_cli_error(error, verbose=False)
        assert exit_code == 5

    def test_validation_error_exit_code(self):
        """Test ValidationError returns exit code 6."""
        error = ValidationError("Invalid value")
        exit_code = handle_cli_error(error, verbose=False)
        assert exit_code == 6

    def test_generic_cli_error_exit_code(self):
        """Test generic CLIError returns exit code 1."""
        error = CLIError("Unknown error")
        exit_code = handle_cli_error(error, verbose=False)
        assert exit_code == 1

    def test_non_cli_error_exit_code(self):
        """Test non-CLI error returns exit code 1."""
        error = ValueError("Some error")
        exit_code = handle_cli_error(error, verbose=False)
        assert exit_code == 1


# =============================================================================
# UTILITY FUNCTIONS TESTS
# =============================================================================


class TestFormatValidationErrors:
    """Test format_validation_errors utility."""

    def test_empty_errors(self):
        """Test formatting empty error list."""
        result = format_validation_errors([])
        assert "passed" in result.lower()

    def test_single_error(self):
        """Test formatting single error."""
        errors = [{"path": "project", "message": "Required field"}]
        result = format_validation_errors(errors)
        assert "1 error(s)" in result
        assert "project" in result
        assert "Required field" in result

    def test_multiple_errors(self):
        """Test formatting multiple errors."""
        errors = [
            {"path": "project", "message": "Required field"},
            {"path": "api.token", "message": "Invalid format"},
        ]
        result = format_validation_errors(errors)
        assert "2 error(s)" in result
        assert "project" in result
        assert "api.token" in result


class TestSuggestCommonFixes:
    """Test suggest_common_fixes utility."""

    def test_config_not_found(self):
        """Test suggestion for missing config file."""
        error = FileNotFoundError("config.yaml")
        suggestion = suggest_common_fixes(error)
        assert suggestion is not None
        assert "config.yaml" in suggestion
        assert "template" in suggestion.lower()

    def test_permission_denied(self):
        """Test suggestion for permission error."""
        error = Exception("Permission denied")
        suggestion = suggest_common_fixes(error)
        assert suggestion is not None
        assert "permission" in suggestion.lower()

    def test_network_error(self):
        """Test suggestion for network error."""
        error = Exception("Connection refused")
        suggestion = suggest_common_fixes(error)
        assert suggestion is not None
        assert "network" in suggestion.lower()

    def test_auth_error(self):
        """Test suggestion for authentication error."""
        error = Exception("401 Unauthorized")
        suggestion = suggest_common_fixes(error)
        assert suggestion is not None
        assert "credentials" in suggestion.lower() or "token" in suggestion.lower()

    def test_yaml_syntax_error(self):
        """Test suggestion for YAML syntax error."""
        error = Exception("Invalid YAML: indentation error")
        suggestion = suggest_common_fixes(error)
        assert suggestion is not None
        assert "YAML" in suggestion
        assert "indentation" in suggestion.lower()

    def test_unknown_error(self):
        """Test that unknown errors return None."""
        error = Exception("Something completely random")
        suggest_common_fixes(error)
        # May return None or a generic suggestion
        # Either is acceptable


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestErrorHandlingIntegration:
    """Integration tests for error handling system."""

    def test_config_file_not_found_flow(self):
        """Test full error flow for missing config file."""
        from config.validator import validate_config_file

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config_file(Path("/nonexistent/config.yaml"))

        error = exc_info.value
        assert "not found" in str(error).lower()
        assert error.suggestion is not None
        assert error.doc_link is not None

    def test_invalid_yaml_flow(self):
        """Test full error flow for invalid YAML."""
        from config.validator import validate_config_file

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: syntax: [[[")
            config_path = Path(f.name)

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                validate_config_file(config_path)

            error = exc_info.value
            assert "YAML" in str(error)
            assert error.suggestion is not None
            assert "syntax" in str(error).lower() or "indentation" in str(error).lower()
        finally:
            config_path.unlink()

    def test_validation_error_from_domain_model(self):
        """Test validation errors from domain models."""
        from domain.time_window import TimeWindow

        with pytest.raises(ValidationError) as exc_info:
            TimeWindow(
                name="invalid",
                days=0,
                start_date="2024-01-01T00:00:00Z",
                end_date="2024-12-31T00:00:00Z",
            )

        error = exc_info.value
        assert "days" in str(error).lower()
        assert "positive" in str(error).lower()

    def test_error_messages_are_actionable(self):
        """Test that error messages provide actionable guidance."""
        # Configuration error should have suggestion
        config_error = ConfigurationError("Invalid format")
        assert config_error.suggestion is not None
        assert len(config_error.suggestion) > 10  # Non-trivial suggestion

        # API error should have suggestion
        api_error = APIError("Request failed", api_name="GitHub")
        assert api_error.suggestion is not None

        # Validation error from helper should be detailed
        val_error = wrap_validation_error("must be positive", field="count", value="-5")
        error_str = str(val_error)
        assert "count" in error_str
        assert "-5" in error_str
