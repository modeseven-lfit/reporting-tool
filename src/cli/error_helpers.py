# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Error Handling Helpers

Utilities for creating enhanced error messages with context and suggestions.
Helps migrate legacy errors to CLI error classes.

Phase 9, Step 6: Enhanced Error Messages Integration
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any
import traceback
import sys
import builtins

from .errors import (
    CLIError,
    ConfigurationError,
    InvalidArgumentError,
    APIError,
    PermissionError as CLIPermissionError,
    DiskSpaceError,
    ValidationError,
    NetworkError,
    suggest_common_fixes,
)


def wrap_config_error(
    message: str,
    config_path: Optional[Path] = None,
    suggestion: Optional[str] = None
) -> ConfigurationError:
    """
    Create configuration error with context.

    Args:
        message: Error message
        config_path: Path to configuration file
        suggestion: Optional custom suggestion

    Returns:
        ConfigurationError with helpful context

    Example:
        >>> raise wrap_config_error(
        ...     "Missing required field 'project'",
        ...     config_path=Path("config.yaml")
        ... )
    """
    if config_path:
        message = f"{message} in {config_path}"

    if not suggestion:
        # Try to suggest based on message content
        if "required field" in message.lower():
            suggestion = "Add the required field to your configuration file"
        elif "invalid yaml" in message.lower():
            suggestion = "Check YAML syntax - ensure proper indentation and no tabs"
        elif "not found" in message.lower():
            suggestion = "Create a config.yaml file using config.example.yaml as template"

    return ConfigurationError(message, suggestion=suggestion)


def wrap_file_error(
    error: Exception,
    file_path: Union[str, Path],
    operation: str = "access"
) -> CLIError:
    """
    Create appropriate error for file operation failures.

    Args:
        error: Original exception
        file_path: Path that caused the error
        operation: Operation being performed (read, write, access, etc.)

    Returns:
        Appropriate CLI error based on exception type

    Example:
        >>> try:
        ...     with open("config.yaml") as f:
        ...         config = f.read()
        ... except Exception as e:
        ...     raise wrap_file_error(e, "config.yaml", "read")
    """
    path_str = str(file_path)

    if isinstance(error, FileNotFoundError):
        message = f"File not found: {path_str}"

        if "config" in path_str.lower():
            return ConfigurationError(
                message,
                suggestion="Create the configuration file or specify a different path with --config"
            )
        elif "template" in path_str.lower():
            return ConfigurationError(
                message,
                suggestion="Ensure template files are present in the templates directory"
            )
        else:
            return CLIError(
                message,
                suggestion=f"Verify the path exists and is accessible"
            )

    elif isinstance(error, builtins.PermissionError):
        return CLIPermissionError(
            f"Cannot {operation} file: {path_str}",
            path=None  # Don't use path parameter to avoid message override
        )

    elif isinstance(error, IsADirectoryError):
        return CLIError(
            f"Expected file but found directory: {path_str}",
            suggestion="Specify a file path, not a directory"
        )

    elif "disk" in str(error).lower() or "space" in str(error).lower():
        return DiskSpaceError(
            f"Disk space error while trying to {operation} {path_str}",
            path=path_str
        )

    else:
        # Generic file error
        return CLIError(
            f"Failed to {operation} {path_str}: {error}",
            suggestion=suggest_common_fixes(error)
        )


def wrap_validation_error(
    message: str,
    field: Optional[str] = None,
    value: Optional[str] = None,
    expected: Optional[str] = None
) -> ValidationError:
    """
    Create validation error with context.

    Args:
        message: Error message
        field: Field that failed validation
        value: Invalid value
        expected: Expected value or format

    Returns:
        ValidationError with helpful context

    Example:
        >>> raise wrap_validation_error(
        ...     "must be non-negative",
        ...     field="commit_count",
        ...     value="-5",
        ...     expected="integer >= 0"
        ... )
    """
    parts = []

    if field:
        parts.append(f"Field '{field}'")

    parts.append(message)

    if value is not None:
        parts.append(f"(got: {value})")

    if expected:
        parts.append(f"Expected: {expected}")

    full_message = " ".join(parts)

    return ValidationError(full_message, field=field)


def wrap_api_error(
    error: Exception,
    api_name: str,
    endpoint: Optional[str] = None,
    suggestion: Optional[str] = None
) -> APIError:
    """
    Create API error with context.

    Args:
        error: Original exception
        api_name: Name of the API (GitHub, Gerrit, Jenkins)
        endpoint: API endpoint that failed
        suggestion: Optional custom suggestion

    Returns:
        APIError with helpful context

    Example:
        >>> try:
        ...     response = github_client.get("/user")
        ... except Exception as e:
        ...     raise wrap_api_error(e, "GitHub", "/user")
    """
    error_str = str(error)

    message = error_str
    if endpoint:
        message = f"{endpoint}: {error_str}"

    # Provide specific suggestions based on error type
    if not suggestion:
        if "401" in error_str or "unauthorized" in error_str.lower():
            suggestion = f"Check {api_name} API token - it may be expired or invalid"
        elif "403" in error_str or "forbidden" in error_str.lower():
            suggestion = f"Verify {api_name} API token has required permissions"
        elif "404" in error_str or "not found" in error_str.lower():
            suggestion = f"Verify the {api_name} resource exists and is accessible"
        elif "rate limit" in error_str.lower():
            suggestion = f"Wait before retrying or use a different {api_name} API token"
        elif "timeout" in error_str.lower() or "timed out" in error_str.lower():
            suggestion = f"Check network connectivity to {api_name} API servers"
        elif "connection" in error_str.lower():
            suggestion = f"Verify network connectivity to {api_name} API servers"

    return APIError(message, api_name=api_name, suggestion=suggestion)


def wrap_network_error(
    error: Exception,
    url: Optional[str] = None,
    suggestion: Optional[str] = None
) -> NetworkError:
    """
    Create network error with context.

    Args:
        error: Original exception
        url: URL that failed
        suggestion: Optional custom suggestion

    Returns:
        NetworkError with helpful context

    Example:
        >>> try:
        ...     response = requests.get("https://api.github.com")
        ... except Exception as e:
        ...     raise wrap_network_error(e, "https://api.github.com")
    """
    message = str(error)
    if url:
        message = f"Failed to connect to {url}: {message}"

    if not suggestion:
        error_str = str(error).lower()
        if "ssl" in error_str or "certificate" in error_str:
            suggestion = "Verify SSL/TLS certificates or use --no-verify-ssl if appropriate"
        elif "proxy" in error_str:
            suggestion = "Check proxy configuration and credentials"
        elif "dns" in error_str or "resolve" in error_str:
            suggestion = "Verify DNS settings and that the hostname is correct"
        elif "timeout" in error_str:
            suggestion = "Check network connectivity and firewall settings"

    return NetworkError(message, suggestion=suggestion)


def format_error_context(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    include_traceback: bool = False
) -> str:
    """
    Format error with contextual information.

    Args:
        error: Exception to format
        context: Additional context information
        include_traceback: Whether to include full traceback

    Returns:
        Formatted error message with context

    Example:
        >>> try:
        ...     process_data(data)
        ... except Exception as e:
        ...     print(format_error_context(
        ...         e,
        ...         context={'data_size': len(data), 'step': 'validation'}
        ...     ))
    """
    lines = []

    # Error type and message
    error_type = type(error).__name__
    lines.append(f"{error_type}: {error}")

    # Context information
    if context:
        lines.append("\nContext:")
        for key, value in context.items():
            lines.append(f"  {key}: {value}")

    # Suggestions
    if isinstance(error, CLIError):
        if error.suggestion:
            lines.append(f"\nSuggestion: {error.suggestion}")
        if error.doc_link:
            lines.append(f"Documentation: {error.doc_link}")
    else:
        suggestion = suggest_common_fixes(error)
        if suggestion:
            lines.append(f"\nSuggestion: {suggestion}")

    # Traceback
    if include_traceback:
        lines.append("\nTraceback:")
        lines.append(''.join(traceback.format_tb(error.__traceback__)))

    return '\n'.join(lines)


def safe_operation(operation_name: str, verbose: bool = False):
    """
    Decorator to wrap operations with enhanced error handling.

    Args:
        operation_name: Name of the operation for error messages
        verbose: Whether to include verbose error information

    Returns:
        Decorator function

    Example:
        >>> @safe_operation("Loading configuration")
        ... def load_config(path):
        ...     with open(path) as f:
        ...         return yaml.safe_load(f)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except CLIError:
                # Already a CLI error, just re-raise
                raise
            except FileNotFoundError as e:
                # Convert to appropriate CLI error
                path = args[0] if args else "unknown"
                raise wrap_file_error(e, path, operation_name.lower())
            except PermissionError as e:
                path = args[0] if args else "unknown"
                raise wrap_file_error(e, path, operation_name.lower())
            except Exception as e:
                # Generic error with context
                context: Dict[str, Any] = {"operation": operation_name}
                if args:
                    context["args"] = tuple(args)
                if kwargs:
                    context["kwargs"] = dict(kwargs)

                if verbose:
                    sys.stderr.write(format_error_context(e, context, include_traceback=True))

                raise CLIError(
                    f"{operation_name} failed: {e}",
                    suggestion=suggest_common_fixes(e)
                )

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


def handle_cli_error(error: Exception, verbose: bool = False) -> int:
    """
    Handle CLI error and return appropriate exit code.

    Args:
        error: Exception that was raised
        verbose: Whether to show verbose error information

    Returns:
        Exit code (0-255)

    Example:
        >>> try:
        ...     run_cli()
        ... except Exception as e:
        ...     sys.exit(handle_cli_error(e, verbose=args.verbose))
    """
    if isinstance(error, CLIError):
        # CLI error with structured information
        print(f"\n❌ {error}", file=sys.stderr)

        if verbose and hasattr(error, '__traceback__'):
            print("\nTraceback:", file=sys.stderr)
            traceback.print_tb(error.__traceback__, file=sys.stderr)

        # Return specific exit codes based on error type
        if isinstance(error, ConfigurationError):
            return 2
        elif isinstance(error, InvalidArgumentError):
            return 2
        elif isinstance(error, APIError):
            return 3
        elif isinstance(error, NetworkError):
            return 3
        elif isinstance(error, CLIPermissionError):
            return 4
        elif isinstance(error, DiskSpaceError):
            return 5
        elif isinstance(error, ValidationError):
            return 6
        else:
            return 1

    else:
        # Non-CLI error - convert and handle
        print(f"\n❌ Error: {error}", file=sys.stderr)

        suggestion = suggest_common_fixes(error)
        if suggestion:
            print(f"💡 Suggestion: {suggestion}", file=sys.stderr)

        if verbose:
            print("\nTraceback:", file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        return 1


__all__ = [
    "wrap_config_error",
    "wrap_file_error",
    "wrap_validation_error",
    "wrap_api_error",
    "wrap_network_error",
    "format_error_context",
    "safe_operation",
    "handle_cli_error",
    "CLIPermissionError",
]
