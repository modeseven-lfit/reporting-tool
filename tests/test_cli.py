# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for CLI Module

Tests for exit codes, error classes, and CLI utilities.

Phase 9: CLI & UX Improvements
"""

import pytest

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
from cli.exit_codes import (
    EXIT_CONFIG_ERROR,
    EXIT_INVALID_ARGS,
    EXIT_SUCCESS,
    ExitCode,
    format_exit_message,
    get_exit_code_description,
    should_retry,
)


class TestExitCodes:
    """Tests for exit code constants and utilities."""

    def test_exit_code_values(self):
        """Test that exit codes have expected values."""
        assert ExitCode.SUCCESS == 0
        assert ExitCode.ERROR == 1
        assert ExitCode.PARTIAL == 2
        assert ExitCode.USAGE_ERROR == 3
        assert ExitCode.SYSTEM_ERROR == 4

    def test_convenience_constants(self):
        """Test convenience constants match their base codes."""
        assert EXIT_SUCCESS == ExitCode.SUCCESS
        assert EXIT_CONFIG_ERROR == ExitCode.ERROR
        assert EXIT_INVALID_ARGS == ExitCode.USAGE_ERROR

    def test_get_exit_code_description(self):
        """Test exit code descriptions."""
        desc = get_exit_code_description(ExitCode.SUCCESS)
        assert "SUCCESS" in desc
        assert "completed successfully" in desc

        desc = get_exit_code_description(ExitCode.ERROR)
        assert "ERROR" in desc
        assert "General error" in desc

    def test_get_exit_code_description_unknown(self):
        """Test description for unknown exit code."""
        desc = get_exit_code_description(99)
        assert "UNKNOWN" in desc
        assert "99" in desc

    def test_format_exit_message_without_details(self):
        """Test formatting exit message without additional details."""
        message = format_exit_message(ExitCode.SUCCESS)
        assert "SUCCESS" in message
        assert "completed successfully" in message

    def test_format_exit_message_with_details(self):
        """Test formatting exit message with additional details."""
        message = format_exit_message(ExitCode.ERROR, "Configuration file not found")
        assert "ERROR" in message
        assert "Configuration file not found" in message
        assert "Details:" in message

    def test_should_retry_for_transient_errors(self):
        """Test that transient errors are marked as retryable."""
        assert should_retry(ExitCode.ERROR) is True
        assert should_retry(ExitCode.PARTIAL) is True
        assert should_retry(ExitCode.SYSTEM_ERROR) is True

    def test_should_not_retry_for_permanent_errors(self):
        """Test that permanent errors are not marked as retryable."""
        assert should_retry(ExitCode.USAGE_ERROR) is False


class TestCLIError:
    """Tests for CLIError base class."""

    def test_cli_error_basic(self):
        """Test basic CLI error creation."""
        error = CLIError("Something went wrong")
        assert error.message == "Something went wrong"
        assert error.suggestion is None
        assert error.doc_link is None

    def test_cli_error_with_suggestion(self):
        """Test CLI error with suggestion."""
        error = CLIError("Config not found", suggestion="Create a config.yaml file")
        assert error.message == "Config not found"
        assert error.suggestion == "Create a config.yaml file"

        error_str = str(error)
        assert "Error: Config not found" in error_str
        assert "Suggestion: Create a config.yaml file" in error_str

    def test_cli_error_with_doc_link(self):
        """Test CLI error with documentation link."""
        error = CLIError("Invalid configuration", doc_link="https://docs.example.com/config")

        error_str = str(error)
        assert "Invalid configuration" in error_str
        assert "Documentation: https://docs.example.com/config" in error_str

    def test_cli_error_complete(self):
        """Test CLI error with all fields."""
        error = CLIError(
            "Config validation failed",
            suggestion="Check YAML syntax",
            doc_link="https://docs.example.com/validation",
        )

        error_str = str(error)
        assert "Config validation failed" in error_str
        assert "Check YAML syntax" in error_str
        assert "https://docs.example.com/validation" in error_str


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_configuration_error_default_suggestion(self):
        """Test that ConfigurationError has default suggestion."""
        error = ConfigurationError("Invalid YAML")

        assert error.message == "Invalid YAML"
        assert error.suggestion is not None
        assert "config.example.yaml" in error.suggestion
        assert error.doc_link == "docs/configuration.md"

    def test_configuration_error_custom_suggestion(self):
        """Test ConfigurationError with custom suggestion."""
        error = ConfigurationError(
            "Missing required field", suggestion="Add the 'project' field to config"
        )

        assert error.suggestion == "Add the 'project' field to config"


class TestInvalidArgumentError:
    """Tests for InvalidArgumentError."""

    def test_invalid_argument_error_default(self):
        """Test InvalidArgumentError with defaults."""
        error = InvalidArgumentError("Unknown flag: --xyz")

        assert error.message == "Unknown flag: --xyz"
        assert "--help" in error.suggestion
        assert error.doc_link == "docs/CLI_REFERENCE.md"


class TestAPIError:
    """Tests for APIError."""

    def test_api_error_without_name(self):
        """Test API error without API name."""
        error = APIError("Connection timeout")

        assert error.message == "Connection timeout"
        assert "network connectivity" in error.suggestion

    def test_api_error_with_name(self):
        """Test API error with API name."""
        error = APIError("Authentication failed", api_name="GitHub")

        assert "GitHub API error" in error.message
        assert "Authentication failed" in error.message


class TestPermissionError:
    """Tests for PermissionError."""

    def test_permission_error_basic(self):
        """Test basic permission error."""
        error = PermissionError("Access denied")

        assert "Access denied" in error.message
        assert "permissions" in error.suggestion

    def test_permission_error_with_path(self):
        """Test permission error with path."""
        error = PermissionError("Cannot write", path="/var/logs/report.log")

        assert "Permission denied: /var/logs/report.log" in error.message


class TestDiskSpaceError:
    """Tests for DiskSpaceError."""

    def test_disk_space_error(self):
        """Test disk space error."""
        error = DiskSpaceError("Out of space")

        assert "Out of space" in error.message
        assert "disk space" in error.suggestion
        assert "--no-cache" in error.suggestion


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error_basic(self):
        """Test basic validation error."""
        error = ValidationError("Invalid value")

        assert "Invalid value" in error.message

    def test_validation_error_with_field(self):
        """Test validation error with field name."""
        error = ValidationError("Must be positive", field="reporting_window_days")

        assert "Validation failed for 'reporting_window_days'" in error.message
        assert "Must be positive" in error.message


class TestNetworkError:
    """Tests for NetworkError."""

    def test_network_error_default(self):
        """Test network error with defaults."""
        error = NetworkError("Connection refused")

        assert "Connection refused" in error.message
        assert "network connection" in error.suggestion
        assert error.doc_link is not None


class TestFormatValidationErrors:
    """Tests for format_validation_errors function."""

    def test_format_no_errors(self):
        """Test formatting with no errors."""
        result = format_validation_errors([])
        assert "passed" in result.lower()

    def test_format_single_error(self):
        """Test formatting single validation error."""
        errors = [{"path": "project", "message": "Required field missing"}]
        result = format_validation_errors(errors)

        assert "1 error(s)" in result
        assert "project" in result
        assert "Required field missing" in result

    def test_format_multiple_errors(self):
        """Test formatting multiple validation errors."""
        errors = [
            {"path": "project", "message": "Required field missing"},
            {"path": "api.github.token", "message": "Invalid token format"},
            {"path": "time_windows.days", "message": "Must be positive"},
        ]
        result = format_validation_errors(errors)

        assert "3 error(s)" in result
        assert "project" in result
        assert "api.github.token" in result
        assert "time_windows.days" in result


class TestSuggestCommonFixes:
    """Tests for suggest_common_fixes function."""

    def test_suggest_config_not_found(self):
        """Test suggestion for missing config file."""
        error = FileNotFoundError("config.yaml not found")
        suggestion = suggest_common_fixes(error)

        assert suggestion is not None
        assert "config.example.yaml" in suggestion

    def test_suggest_permission_denied(self):
        """Test suggestion for permission errors."""
        error = PermissionError("Permission denied: /root/output")
        suggestion = suggest_common_fixes(error)

        assert suggestion is not None
        assert "permission" in suggestion.lower()

    def test_suggest_network_error(self):
        """Test suggestion for network errors."""
        error = Exception("Connection timeout")
        suggestion = suggest_common_fixes(error)

        assert suggestion is not None
        assert "network" in suggestion.lower()

    def test_suggest_auth_error(self):
        """Test suggestion for authentication errors."""
        error = Exception("401 Authentication failed")
        suggestion = suggest_common_fixes(error)

        assert suggestion is not None
        assert "credentials" in suggestion.lower() or "token" in suggestion.lower()

    def test_suggest_disk_space(self):
        """Test suggestion for disk space errors."""
        error = Exception("No space left on disk")
        suggestion = suggest_common_fixes(error)

        assert suggestion is not None
        assert "disk space" in suggestion.lower()

    def test_suggest_yaml_parse_error(self):
        """Test suggestion for YAML parsing errors."""
        error = Exception("Invalid YAML syntax")
        suggestion = suggest_common_fixes(error)

        assert suggestion is not None
        assert "YAML" in suggestion or "yaml" in suggestion

    def test_suggest_unknown_error(self):
        """Test suggestion for unknown error returns None."""
        error = Exception("Something completely unexpected")
        suggestion = suggest_common_fixes(error)

        assert suggestion is None


class TestErrorIntegration:
    """Integration tests for error handling."""

    def test_error_chain_with_suggestions(self):
        """Test that errors can be chained with suggestions."""
        try:
            raise ConfigurationError("Invalid config")
        except ConfigurationError as e:
            assert isinstance(e, CLIError)
            assert e.suggestion is not None
            assert e.doc_link is not None

    def test_error_string_representation(self):
        """Test complete error string representation."""
        error = APIError(
            "Rate limit exceeded",
            api_name="GitHub",
            suggestion="Wait before retrying or use a different token",
        )

        error_str = str(error)
        assert "GitHub API error" in error_str
        assert "Rate limit exceeded" in error_str
        assert "Wait before retrying" in error_str
        assert "Documentation:" in error_str


class TestArgumentParser:
    """Tests for enhanced argument parser."""

    def test_create_argument_parser(self):
        """Test that argument parser is created successfully."""
        from cli.arguments import create_argument_parser

        parser = create_argument_parser()
        assert parser is not None
        assert parser.prog == "generate_reports.py"

    def test_parse_basic_arguments(self):
        """Test parsing basic required arguments."""
        import tempfile
        from pathlib import Path

        from cli.arguments import parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            args = parse_arguments(["--project", "test-project", "--repos-path", tmpdir])

            assert args.project == "test-project"
            assert args.repos_path == Path(tmpdir)

    def test_parse_output_format(self):
        """Test parsing output format argument."""
        import tempfile

        from cli.arguments import parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            args = parse_arguments(
                ["--project", "test", "--repos-path", tmpdir, "--output-format", "html"]
            )

            assert args.output_format == "html"

    def test_parse_verbosity_flags(self):
        """Test parsing verbosity flags."""
        import tempfile

        from cli.arguments import parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            # Single verbose
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "-v"])
            assert args.verbose == 1

            # Double verbose
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "-vv"])
            assert args.verbose == 2

    def test_parse_quiet_flag(self):
        """Test parsing quiet flag."""
        import tempfile

        from cli.arguments import parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "--quiet"])
            assert args.quiet is True

    def test_parse_dry_run_flag(self):
        """Test parsing dry-run flag."""
        import tempfile

        from cli.arguments import parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "--dry-run"])
            assert args.dry_run is True

    def test_parse_list_features_flag(self):
        """Test parsing list-features flag."""
        import tempfile

        from cli.arguments import parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "--list-features"])
            assert args.list_features is True

    def test_parse_show_feature_flag(self):
        """Test parsing show-feature flag."""
        import tempfile

        from cli.arguments import parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            args = parse_arguments(
                ["--project", "test", "--repos-path", tmpdir, "--show-feature", "dependabot"]
            )
            assert args.show_feature == "dependabot"

    def test_validate_nonexistent_path(self):
        """Test validation fails for nonexistent path."""
        from cli.arguments import parse_arguments

        with pytest.raises(InvalidArgumentError) as exc_info:
            parse_arguments(
                ["--project", "test", "--repos-path", "/nonexistent/path/that/does/not/exist"]
            )

        assert "does not exist" in str(exc_info.value)

    def test_get_verbosity_level(self):
        """Test getting verbosity level from arguments."""
        import tempfile

        from cli.arguments import VerbosityLevel, get_verbosity_level, parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            # Normal
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir])
            assert get_verbosity_level(args) == VerbosityLevel.NORMAL

            # Verbose
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "-v"])
            assert get_verbosity_level(args) == VerbosityLevel.VERBOSE

            # Debug
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "-vv"])
            assert get_verbosity_level(args) == VerbosityLevel.DEBUG

            # Quiet
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "--quiet"])
            assert get_verbosity_level(args) == VerbosityLevel.QUIET

    def test_get_log_level(self):
        """Test getting log level from arguments."""
        import tempfile

        from cli.arguments import get_log_level, parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            # Default
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir])
            assert get_log_level(args) == "INFO"

            # Verbose
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "-vv"])
            assert get_log_level(args) == "DEBUG"

            # Explicit
            args = parse_arguments(
                ["--project", "test", "--repos-path", tmpdir, "--log-level", "ERROR"]
            )
            assert get_log_level(args) == "ERROR"

    def test_get_output_formats(self):
        """Test getting output formats from arguments."""
        import tempfile

        from cli.arguments import OutputFormat, get_output_formats, parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            # Default (all)
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir])
            formats = get_output_formats(args)
            assert OutputFormat.JSON in formats
            assert OutputFormat.MARKDOWN in formats
            assert OutputFormat.HTML in formats

            # HTML only
            args = parse_arguments(
                ["--project", "test", "--repos-path", tmpdir, "--output-format", "html"]
            )
            formats = get_output_formats(args)
            assert formats == [OutputFormat.HTML]

    def test_is_special_mode(self):
        """Test detection of special modes."""
        import tempfile

        from cli.arguments import is_special_mode, parse_arguments

        with tempfile.TemporaryDirectory() as tmpdir:
            # Normal mode
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir])
            assert is_special_mode(args) is False

            # Dry run mode
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "--dry-run"])
            assert is_special_mode(args) is True

            # List features mode
            args = parse_arguments(["--project", "test", "--repos-path", tmpdir, "--list-features"])
            assert is_special_mode(args) is True

            # Show feature mode
            args = parse_arguments(
                ["--project", "test", "--repos-path", tmpdir, "--show-feature", "docker"]
            )
            assert is_special_mode(args) is True


class TestFeatureDiscovery:
    """Tests for feature discovery module."""

    def test_list_all_features(self):
        """Test listing all available features."""
        from cli.features import list_all_features

        output = list_all_features()
        assert "Available Feature Checks" in output
        assert "dependabot" in output
        assert "CI/CD" in output
        assert "Total:" in output

    def test_get_features_by_category(self):
        """Test getting features organized by category."""
        from cli.features import get_features_by_category

        features = get_features_by_category()
        assert "CI/CD" in features
        assert isinstance(features["CI/CD"], list)
        assert len(features["CI/CD"]) > 0

    def test_get_feature_description(self):
        """Test getting description for a feature."""
        from cli.features import get_feature_description

        desc = get_feature_description("dependabot")
        assert "Dependabot" in desc

        # Unknown feature
        desc = get_feature_description("nonexistent-feature")
        assert "Unknown" in desc

    def test_get_feature_category(self):
        """Test getting category for a feature."""
        from cli.features import get_feature_category

        category = get_feature_category("dependabot")
        assert category == "CI/CD"

        # Unknown feature
        category = get_feature_category("nonexistent")
        assert category == "Unknown"

    def test_get_features_in_category(self):
        """Test getting all features in a category."""
        from cli.features import get_features_in_category

        features = get_features_in_category("CI/CD")
        assert "dependabot" in features
        assert isinstance(features, list)

    def test_get_all_categories(self):
        """Test getting all categories."""
        from cli.features import get_all_categories

        categories = get_all_categories()
        assert "CI/CD" in categories
        assert "Documentation" in categories
        assert isinstance(categories, list)

    def test_search_features(self):
        """Test searching for features."""
        from cli.features import search_features

        results = search_features("github")
        assert len(results) > 0
        assert any("github" in name.lower() for name, _, _ in results)

    def test_format_feature_list_compact(self):
        """Test compact feature list formatting."""
        from cli.features import format_feature_list_compact

        output = format_feature_list_compact()
        assert "dependabot" in output
        assert "," in output

    def test_get_feature_count(self):
        """Test getting total feature count."""
        from cli.features import get_feature_count

        count = get_feature_count()
        assert count > 0
        assert isinstance(count, int)

    def test_get_category_count(self):
        """Test getting total category count."""
        from cli.features import get_category_count

        count = get_category_count()
        assert count > 0
        assert isinstance(count, int)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
