# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
CLI Error Classes

Enhanced error classes for better user experience with actionable suggestions
and documentation links.

Phase 9: CLI & UX Improvements
Phase 13, Step 4: Enhanced Error Messages with Context
"""

from typing import Optional, Dict, Any, List


class CLIError(Exception):
    """
    Base CLI error with helpful context.

    This error class provides structured error information including:
    - Clear error message
    - Actionable suggestions for resolution
    - Links to relevant documentation

    Example:
        >>> raise CLIError(
        ...     "Configuration file not found: config.yaml",
        ...     suggestion="Create a config.yaml file or specify path with --config",
        ...     doc_link="https://docs.example.com/configuration"
        ... )
    """

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        doc_link: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_hints: Optional[List[str]] = None
    ):
        """
        Initialize CLI error.

        Args:
            message: Error message describing what went wrong
            suggestion: Optional suggestion for how to fix the error
            doc_link: Optional link to relevant documentation
            context: Optional context information dictionary
            recovery_hints: Optional list of step-by-step recovery instructions
        """
        self.message = message
        self.suggestion = suggestion
        self.doc_link = doc_link
        self.context = context or {}
        self.recovery_hints = recovery_hints or []
        super().__init__(message)

    def __str__(self) -> str:
        """Format error with suggestions and documentation."""
        parts = [f"❌ Error: {self.message}"]

        # Context information
        if self.context:
            parts.append("\n📋 Context:")
            for key, value in self.context.items():
                parts.append(f"  • {key}: {value}")

        # Recovery hints (step-by-step)
        if self.recovery_hints:
            parts.append("\n🔧 How to fix:")
            for i, hint in enumerate(self.recovery_hints, 1):
                parts.append(f"  {i}. {hint}")

        # Simple suggestion (backward compatible)
        elif self.suggestion:
            parts.append(f"\n💡 Suggestion: {self.suggestion}")

        # Documentation link
        if self.doc_link:
            parts.append(f"\n📖 Documentation: {self.doc_link}")

        return '\n'.join(parts)

    def add_context(self, key: str, value: Any) -> 'CLIError':
        """
        Add context information to error.

        Args:
            key: Context key
            value: Context value

        Returns:
            Self for chaining
        """
        self.context[key] = value
        return self

    def add_recovery_hint(self, hint: str) -> 'CLIError':
        """
        Add a recovery hint.

        Args:
            hint: Recovery instruction

        Returns:
            Self for chaining
        """
        self.recovery_hints.append(hint)
        return self


class ConfigurationError(CLIError):
    """
    Configuration-related error.

    Raised when configuration file is missing, invalid, or contains errors.
    """

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_hints: Optional[List[str]] = None
    ):
        """Initialize configuration error."""
        default_suggestion = (
            "Check your configuration file syntax and required fields. "
            "See config.example.yaml for a template."
        )
        default_hints = [
            "Verify YAML syntax is correct (no tabs, proper indentation)",
            "Check for required fields in configuration",
            "Compare with config.example.yaml template",
            "Validate with: python generate_reports.py --dry-run"
        ]
        super().__init__(
            message,
            suggestion=suggestion or default_suggestion,
            doc_link="docs/configuration.md",
            context=context,
            recovery_hints=recovery_hints or default_hints
        )


class InvalidArgumentError(CLIError):
    """
    Invalid command-line argument error.

    Raised when user provides invalid or conflicting arguments.
    """

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_hints: Optional[List[str]] = None
    ):
        """Initialize invalid argument error."""
        default_suggestion = "Run with --help to see valid arguments and usage examples."
        default_hints = [
            "Check the command-line arguments for typos",
            "Run with --help to see all available options",
            "See docs/CLI_REFERENCE.md for detailed usage",
            "Use --list-features to see available features"
        ]
        super().__init__(
            message,
            suggestion=suggestion or default_suggestion,
            doc_link="docs/CLI_REFERENCE.md",
            context=context,
            recovery_hints=recovery_hints or default_hints
        )


class APIError(CLIError):
    """
    API-related error.

    Raised when external API calls fail (GitHub, Gerrit, Jenkins).
    """

    def __init__(
        self,
        message: str,
        api_name: Optional[str] = None,
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_hints: Optional[List[str]] = None,
        status_code: Optional[int] = None
    ):
        """Initialize API error."""
        ctx = context or {}
        if api_name:
            message = f"{api_name} API error: {message}"
            ctx["api"] = api_name
        if status_code:
            ctx["status_code"] = status_code

        default_suggestion = (
            "Check network connectivity and API credentials. "
            "Verify that API endpoints are accessible."
        )

        # Specific hints based on status code (only used if no custom hints/suggestion provided)
        default_hints = []
        if not suggestion and not recovery_hints:
            if status_code == 401:
                default_hints = [
                    "Verify API token is set in environment or config",
                    "Check that the token hasn't expired",
                    "Regenerate token if needed",
                    "Ensure token has required permissions"
                ]
            elif status_code == 403:
                default_hints = [
                    "Check API token permissions/scopes",
                    "Verify access to the resource",
                    "Check for rate limiting",
                    "Ensure organization membership if applicable"
                ]
            elif status_code == 404:
                default_hints = [
                    "Verify the resource exists",
                    "Check the resource URL/path",
                    "Ensure you have access to the resource",
                    "Verify repository/organization name spelling"
                ]
            else:
                default_hints = [
                    "Check network connectivity",
                    "Verify API credentials are correct",
                    "Check API endpoint is accessible",
                    "Review API documentation for requirements"
                ]

        super().__init__(
            message,
            suggestion=suggestion or default_suggestion,
            doc_link="docs/troubleshooting.md#api-errors",
            context=ctx,
            recovery_hints=recovery_hints or (default_hints if default_hints else None)
        )


class PermissionError(CLIError):
    """
    Permission-related error.

    Raised when operations fail due to insufficient permissions.
    """

    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize permission error."""
        ctx = context or {}
        if path:
            message = f"Permission denied: {path}"
            ctx["path"] = path

        suggestion = (
            "Check file/directory permissions. "
            "You may need to run with appropriate privileges or "
            "choose a different output directory."
        )

        recovery_hints = [
            "Check file/directory permissions with: ls -la",
            "Ensure your user has necessary access rights",
            "Try using a different output directory",
            "Fix permissions with: chmod u+rw <path> (if you own it)"
        ]

        super().__init__(
            message,
            suggestion=suggestion,
            context=ctx,
            recovery_hints=recovery_hints
        )


class DiskSpaceError(CLIError):
    """
    Disk space error.

    Raised when operations fail due to insufficient disk space.
    """

    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize disk space error."""
        ctx = context or {}
        if path:
            ctx["path"] = path

        suggestion = (
            "Free up disk space or choose a different output directory. "
            "Consider using --no-cache to reduce disk usage."
        )

        recovery_hints = [
            "Check available disk space with: df -h",
            "Free up space by removing unnecessary files",
            "Use a different output directory with more space",
            "Use --no-cache to reduce disk usage",
            "Use --output-format json to skip HTML generation"
        ]

        super().__init__(
            message,
            suggestion=suggestion,
            context=ctx,
            recovery_hints=recovery_hints
        )


class ValidationError(CLIError):
    """
    Validation error.

    Raised when data validation fails.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_hints: Optional[List[str]] = None
    ):
        """Initialize validation error."""
        ctx = context or {}
        if field:
            message = f"Validation failed for '{field}': {message}"
            ctx["field"] = field

        default_hints = [
            "Check the value format and type",
            "Compare with config.example.yaml for valid examples",
            "Validate configuration with: --dry-run",
            "See docs/configuration.md for field requirements"
        ]

        super().__init__(
            message,
            context=ctx,
            recovery_hints=recovery_hints or default_hints
        )


class NetworkError(CLIError):
    """
    Network connectivity error.

    Raised when network operations fail.
    """

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        recovery_hints: Optional[List[str]] = None
    ):
        """Initialize network error."""
        default_suggestion = (
            "Check your network connection. "
            "Verify that you can reach the required endpoints. "
            "You may need to configure proxy settings."
        )

        default_hints = [
            "Check internet connectivity",
            "Test endpoint reachability (e.g., ping api.github.com)",
            "Verify firewall/proxy settings",
            "Check for DNS resolution issues",
            "Try again after a few moments"
        ]

        super().__init__(
            message,
            suggestion=suggestion or default_suggestion,
            doc_link="docs/troubleshooting.md#network-issues",
            context=context,
            recovery_hints=recovery_hints or default_hints
        )


def format_validation_errors(errors: list[dict]) -> str:
    """
    Format multiple validation errors into readable message.

    Args:
        errors: List of validation error dictionaries with 'path' and 'message'

    Returns:
        Formatted error message

    Example:
        >>> errors = [
        ...     {'path': 'project', 'message': 'Required field missing'},
        ...     {'path': 'api.github.token', 'message': 'Invalid token format'}
        ... ]
        >>> print(format_validation_errors(errors))
        Configuration validation failed with 2 error(s):
          - project: Required field missing
          - api.github.token: Invalid token format
    """
    if not errors:
        return "Validation passed"

    lines = [f"Configuration validation failed with {len(errors)} error(s):"]
    for error in errors:
        path = error.get('path', 'unknown')
        message = error.get('message', 'Unknown error')
        lines.append(f"  - {path}: {message}")

    return '\n'.join(lines)


def suggest_common_fixes(error: Exception) -> Optional[str]:
    """
    Suggest common fixes based on error type and message.

    Args:
        error: The exception that was raised

    Returns:
        Suggestion string or None if no common fix available

    Example:
        >>> error = FileNotFoundError("config.yaml")
        >>> print(suggest_common_fixes(error))
        Create a config.yaml file using config.example.yaml as template
    """
    error_str = str(error).lower()

    # Check error type first
    if isinstance(error, FileNotFoundError):
        if "config" in error_str:
            return "Create a config.yaml file using config.example.yaml as template"
        return "Verify the file path exists and is accessible"

    # Common error patterns and suggestions
    if "config.yaml" in error_str and "not found" in error_str:
        return "Create a config.yaml file using config.example.yaml as template"

    if "permission denied" in error_str:
        return "Check file permissions or run with appropriate privileges"

    if "connection" in error_str or "network" in error_str:
        return "Check network connectivity and firewall settings"

    if "authentication" in error_str or "401" in error_str:
        return "Verify API credentials and tokens are correct"

    if "not found" in error_str and "repository" in error_str:
        return "Verify repository path exists and is accessible"

    if "disk" in error_str or "space" in error_str:
        return "Free up disk space or use --no-cache flag"

    if "yaml" in error_str and ("invalid" in error_str or "parse" in error_str):
        return "Check YAML syntax - ensure proper indentation and no tabs"

    return None


__all__ = [
    "CLIError",
    "ConfigurationError",
    "InvalidArgumentError",
    "APIError",
    "PermissionError",
    "DiskSpaceError",
    "ValidationError",
    "NetworkError",
    "format_validation_errors",
    "suggest_common_fixes",
]
