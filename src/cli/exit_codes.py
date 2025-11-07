# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
CLI Exit Codes

Standardized exit codes for the repository reporting system CLI.
This module defines exit codes that follow Unix conventions and provide
clear signals for both interactive and automated (CI/CD) usage.

Exit Codes:
    0 - SUCCESS: Operation completed successfully
    1 - ERROR: General error (configuration, API failure, etc.)
    2 - PARTIAL: Partial success (warnings, incomplete data)
    3 - USAGE_ERROR: Invalid arguments or usage
    4 - SYSTEM_ERROR: System-level error (permissions, disk space)

Phase 9: CLI & UX Improvements
"""

from enum import IntEnum
from typing import Dict, Optional


class ExitCode(IntEnum):
    """
    Standardized exit codes for CLI operations.

    These codes follow common Unix conventions and provide clear
    signals for both interactive users and automation systems.

    Usage:
        >>> import sys
        >>> from src.cli.exit_codes import ExitCode
        >>>
        >>> # Success case
        >>> sys.exit(ExitCode.SUCCESS)
        >>>
        >>> # Error case
        >>> sys.exit(ExitCode.ERROR)
    """

    SUCCESS = 0
    """Operation completed successfully with no errors or warnings."""

    ERROR = 1
    """
    General error occurred.

    This includes:
    - Configuration errors (invalid YAML, missing required fields)
    - API failures (network errors, authentication failures)
    - Data processing errors
    - Unexpected exceptions
    """

    PARTIAL = 2
    """
    Partial success - operation completed but with warnings.

    This includes:
    - Some repositories failed to process
    - Incomplete data collected
    - Non-fatal errors occurred
    - Results may be incomplete
    """

    USAGE_ERROR = 3
    """
    Invalid usage or arguments.

    This includes:
    - Missing required arguments
    - Invalid argument values
    - Conflicting options
    - Incorrect command syntax
    """

    SYSTEM_ERROR = 4
    """
    System-level error.

    This includes:
    - Permission denied (filesystem, network)
    - Out of disk space
    - Missing system dependencies
    - Resource exhaustion
    """


def get_exit_code_description(code: int) -> str:
    """
    Get human-readable description of exit code.

    Args:
        code: Exit code value (0-4)

    Returns:
        Description of the exit code

    Example:
        >>> get_exit_code_description(0)
        'SUCCESS: Operation completed successfully with no errors or warnings.'
    """
    descriptions: Dict[ExitCode, str] = {
        ExitCode.SUCCESS: "SUCCESS: Operation completed successfully with no errors or warnings.",
        ExitCode.ERROR: "ERROR: General error occurred (configuration, API, or processing failure).",
        ExitCode.PARTIAL: "PARTIAL: Operation completed but with warnings or incomplete data.",
        ExitCode.USAGE_ERROR: "USAGE_ERROR: Invalid arguments or command syntax.",
        ExitCode.SYSTEM_ERROR: "SYSTEM_ERROR: System-level error (permissions, disk space, dependencies).",
    }
    exit_code = ExitCode(code) if code in [e.value for e in ExitCode] else None
    if exit_code is None:
        return f"UNKNOWN: Unknown exit code {code}"
    return descriptions.get(exit_code, f"UNKNOWN: Unknown exit code {code}")


def format_exit_message(code: int, message: Optional[str] = None) -> str:
    """
    Format a complete exit message with code description.

    Args:
        code: Exit code
        message: Optional additional context message

    Returns:
        Formatted exit message

    Example:
        >>> print(format_exit_message(ExitCode.ERROR, "Configuration file not found"))
        ERROR: General error occurred (configuration, API, or processing failure).
        Details: Configuration file not found
    """
    base = get_exit_code_description(code)
    if message:
        return f"{base}\nDetails: {message}"
    return base


def should_retry(code: int) -> bool:
    """
    Determine if operation should be retried based on exit code.

    Args:
        code: Exit code from previous attempt

    Returns:
        True if operation might succeed on retry, False otherwise

    Example:
        >>> should_retry(ExitCode.ERROR)  # Network error might be transient
        True
        >>> should_retry(ExitCode.USAGE_ERROR)  # Invalid args won't improve
        False
    """
    # Transient errors that might resolve on retry
    retry_codes = {ExitCode.ERROR, ExitCode.PARTIAL, ExitCode.SYSTEM_ERROR}

    # Permanent errors that won't resolve on retry
    # no_retry_codes = {ExitCode.USAGE_ERROR}

    return code in retry_codes


# Convenience constants for common exit scenarios
EXIT_SUCCESS = ExitCode.SUCCESS
EXIT_CONFIG_ERROR = ExitCode.ERROR
EXIT_API_ERROR = ExitCode.ERROR
EXIT_PROCESSING_ERROR = ExitCode.ERROR
EXIT_PARTIAL_SUCCESS = ExitCode.PARTIAL
EXIT_INVALID_ARGS = ExitCode.USAGE_ERROR
EXIT_PERMISSION_DENIED = ExitCode.SYSTEM_ERROR
EXIT_DISK_FULL = ExitCode.SYSTEM_ERROR


__all__ = [
    "ExitCode",
    "get_exit_code_description",
    "format_exit_message",
    "should_retry",
    # Convenience constants
    "EXIT_SUCCESS",
    "EXIT_CONFIG_ERROR",
    "EXIT_API_ERROR",
    "EXIT_PROCESSING_ERROR",
    "EXIT_PARTIAL_SUCCESS",
    "EXIT_INVALID_ARGS",
    "EXIT_PERMISSION_DENIED",
    "EXIT_DISK_FULL",
]
