# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Error taxonomy and classification system for the repository reporting system.

This module provides a comprehensive error classification system that extends
the API error types to cover all operations including Git, data collection,
validation, and rendering.

Features:
- Hierarchical error classification
- Error context tracking
- Error aggregation and reporting
- Integration with structured logging
- Domain model validation errors
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict


class ErrorCategory(Enum):
    """High-level error categories."""

    NETWORK = "network"
    API = "api"
    GIT = "git"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    DATA = "data"
    RENDERING = "rendering"
    SYSTEM = "system"


class ErrorSeverity(Enum):
    """Error severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorType(Enum):
    """
    Detailed error types organized by category.

    Extends the API error types to cover all system operations.
    """

    # Network errors
    NETWORK_TIMEOUT = "network_timeout"
    NETWORK_CONNECTION = "network_connection"
    NETWORK_DNS = "network_dns"

    # API errors (from API module)
    API_HTTP_CLIENT = "api_http_client"  # 4xx errors
    API_HTTP_SERVER = "api_http_server"  # 5xx errors
    API_RATE_LIMIT = "api_rate_limit"
    API_AUTHENTICATION = "api_authentication"
    API_AUTHORIZATION = "api_authorization"
    API_NOT_FOUND = "api_not_found"
    API_PARSE = "api_parse"
    API_TIMEOUT = "api_timeout"
    API_UNKNOWN = "api_unknown"

    # Git errors
    GIT_NOT_FOUND = "git_not_found"
    GIT_COMMAND_FAILED = "git_command_failed"
    GIT_PARSE_ERROR = "git_parse_error"
    GIT_INVALID_REPO = "git_invalid_repo"
    GIT_CLONE_FAILED = "git_clone_failed"
    GIT_CHECKOUT_FAILED = "git_checkout_failed"

    # Validation errors
    VALIDATION_DOMAIN_MODEL = "validation_domain_model"
    VALIDATION_SCHEMA = "validation_schema"
    VALIDATION_CONSTRAINT = "validation_constraint"
    VALIDATION_TYPE = "validation_type"
    VALIDATION_REQUIRED_FIELD = "validation_required_field"

    # Configuration errors
    CONFIG_MISSING = "config_missing"
    CONFIG_INVALID = "config_invalid"
    CONFIG_PARSE = "config_parse"
    CONFIG_SCHEMA = "config_schema"

    # Data errors
    DATA_MISSING = "data_missing"
    DATA_CORRUPT = "data_corrupt"
    DATA_INCONSISTENT = "data_inconsistent"
    DATA_CONVERSION = "data_conversion"

    # Rendering errors
    RENDER_TEMPLATE = "render_template"
    RENDER_FORMAT = "render_format"
    RENDER_OUTPUT = "render_output"

    # System errors
    SYSTEM_IO = "system_io"
    SYSTEM_PERMISSION = "system_permission"
    SYSTEM_RESOURCE = "system_resource"
    SYSTEM_UNKNOWN = "system_unknown"


# Mapping of error types to categories
ERROR_TYPE_CATEGORY_MAP: Dict[ErrorType, ErrorCategory] = {
    # Network
    ErrorType.NETWORK_TIMEOUT: ErrorCategory.NETWORK,
    ErrorType.NETWORK_CONNECTION: ErrorCategory.NETWORK,
    ErrorType.NETWORK_DNS: ErrorCategory.NETWORK,

    # API
    ErrorType.API_HTTP_CLIENT: ErrorCategory.API,
    ErrorType.API_HTTP_SERVER: ErrorCategory.API,
    ErrorType.API_RATE_LIMIT: ErrorCategory.API,
    ErrorType.API_AUTHENTICATION: ErrorCategory.API,
    ErrorType.API_AUTHORIZATION: ErrorCategory.API,
    ErrorType.API_NOT_FOUND: ErrorCategory.API,
    ErrorType.API_PARSE: ErrorCategory.API,
    ErrorType.API_TIMEOUT: ErrorCategory.API,
    ErrorType.API_UNKNOWN: ErrorCategory.API,

    # Git
    ErrorType.GIT_NOT_FOUND: ErrorCategory.GIT,
    ErrorType.GIT_COMMAND_FAILED: ErrorCategory.GIT,
    ErrorType.GIT_PARSE_ERROR: ErrorCategory.GIT,
    ErrorType.GIT_INVALID_REPO: ErrorCategory.GIT,
    ErrorType.GIT_CLONE_FAILED: ErrorCategory.GIT,
    ErrorType.GIT_CHECKOUT_FAILED: ErrorCategory.GIT,

    # Validation
    ErrorType.VALIDATION_DOMAIN_MODEL: ErrorCategory.VALIDATION,
    ErrorType.VALIDATION_SCHEMA: ErrorCategory.VALIDATION,
    ErrorType.VALIDATION_CONSTRAINT: ErrorCategory.VALIDATION,
    ErrorType.VALIDATION_TYPE: ErrorCategory.VALIDATION,
    ErrorType.VALIDATION_REQUIRED_FIELD: ErrorCategory.VALIDATION,

    # Configuration
    ErrorType.CONFIG_MISSING: ErrorCategory.CONFIGURATION,
    ErrorType.CONFIG_INVALID: ErrorCategory.CONFIGURATION,
    ErrorType.CONFIG_PARSE: ErrorCategory.CONFIGURATION,
    ErrorType.CONFIG_SCHEMA: ErrorCategory.CONFIGURATION,

    # Data
    ErrorType.DATA_MISSING: ErrorCategory.DATA,
    ErrorType.DATA_CORRUPT: ErrorCategory.DATA,
    ErrorType.DATA_INCONSISTENT: ErrorCategory.DATA,
    ErrorType.DATA_CONVERSION: ErrorCategory.DATA,

    # Rendering
    ErrorType.RENDER_TEMPLATE: ErrorCategory.RENDERING,
    ErrorType.RENDER_FORMAT: ErrorCategory.RENDERING,
    ErrorType.RENDER_OUTPUT: ErrorCategory.RENDERING,

    # System
    ErrorType.SYSTEM_IO: ErrorCategory.SYSTEM,
    ErrorType.SYSTEM_PERMISSION: ErrorCategory.SYSTEM,
    ErrorType.SYSTEM_RESOURCE: ErrorCategory.SYSTEM,
    ErrorType.SYSTEM_UNKNOWN: ErrorCategory.SYSTEM,
}


# Mapping of error types to default severity
ERROR_TYPE_SEVERITY_MAP: Dict[ErrorType, ErrorSeverity] = {
    # Network - generally medium severity
    ErrorType.NETWORK_TIMEOUT: ErrorSeverity.MEDIUM,
    ErrorType.NETWORK_CONNECTION: ErrorSeverity.MEDIUM,
    ErrorType.NETWORK_DNS: ErrorSeverity.MEDIUM,

    # API - varies by type
    ErrorType.API_HTTP_CLIENT: ErrorSeverity.LOW,
    ErrorType.API_HTTP_SERVER: ErrorSeverity.MEDIUM,
    ErrorType.API_RATE_LIMIT: ErrorSeverity.LOW,
    ErrorType.API_AUTHENTICATION: ErrorSeverity.HIGH,
    ErrorType.API_AUTHORIZATION: ErrorSeverity.HIGH,
    ErrorType.API_NOT_FOUND: ErrorSeverity.LOW,
    ErrorType.API_PARSE: ErrorSeverity.MEDIUM,
    ErrorType.API_TIMEOUT: ErrorSeverity.MEDIUM,
    ErrorType.API_UNKNOWN: ErrorSeverity.MEDIUM,

    # Git - generally high severity for repo access
    ErrorType.GIT_NOT_FOUND: ErrorSeverity.HIGH,
    ErrorType.GIT_COMMAND_FAILED: ErrorSeverity.MEDIUM,
    ErrorType.GIT_PARSE_ERROR: ErrorSeverity.MEDIUM,
    ErrorType.GIT_INVALID_REPO: ErrorSeverity.HIGH,
    ErrorType.GIT_CLONE_FAILED: ErrorSeverity.HIGH,
    ErrorType.GIT_CHECKOUT_FAILED: ErrorSeverity.MEDIUM,

    # Validation - medium severity (data quality issue)
    ErrorType.VALIDATION_DOMAIN_MODEL: ErrorSeverity.MEDIUM,
    ErrorType.VALIDATION_SCHEMA: ErrorSeverity.MEDIUM,
    ErrorType.VALIDATION_CONSTRAINT: ErrorSeverity.MEDIUM,
    ErrorType.VALIDATION_TYPE: ErrorSeverity.MEDIUM,
    ErrorType.VALIDATION_REQUIRED_FIELD: ErrorSeverity.MEDIUM,

    # Configuration - critical (blocks execution)
    ErrorType.CONFIG_MISSING: ErrorSeverity.CRITICAL,
    ErrorType.CONFIG_INVALID: ErrorSeverity.CRITICAL,
    ErrorType.CONFIG_PARSE: ErrorSeverity.CRITICAL,
    ErrorType.CONFIG_SCHEMA: ErrorSeverity.CRITICAL,

    # Data - varies by impact
    ErrorType.DATA_MISSING: ErrorSeverity.MEDIUM,
    ErrorType.DATA_CORRUPT: ErrorSeverity.HIGH,
    ErrorType.DATA_INCONSISTENT: ErrorSeverity.MEDIUM,
    ErrorType.DATA_CONVERSION: ErrorSeverity.MEDIUM,

    # Rendering - low to medium (report generation)
    ErrorType.RENDER_TEMPLATE: ErrorSeverity.MEDIUM,
    ErrorType.RENDER_FORMAT: ErrorSeverity.LOW,
    ErrorType.RENDER_OUTPUT: ErrorSeverity.HIGH,

    # System - critical (environment issue)
    ErrorType.SYSTEM_IO: ErrorSeverity.HIGH,
    ErrorType.SYSTEM_PERMISSION: ErrorSeverity.CRITICAL,
    ErrorType.SYSTEM_RESOURCE: ErrorSeverity.CRITICAL,
    ErrorType.SYSTEM_UNKNOWN: ErrorSeverity.MEDIUM,
}


@dataclass
class ErrorContext:
    """
    Context information for an error occurrence.

    Attributes:
        repository: Repository where error occurred
        operation: Operation being performed
        phase: Processing phase
        window: Time window (if applicable)
        extra: Additional context fields
    """

    repository: Optional[str] = None
    operation: Optional[str] = None
    phase: Optional[str] = None
    window: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.repository:
            result["repository"] = self.repository
        if self.operation:
            result["operation"] = self.operation
        if self.phase:
            result["phase"] = self.phase
        if self.window:
            result["window"] = self.window
        if self.extra:
            result.update(self.extra)
        return result


@dataclass
class ClassifiedError:
    """
    A classified error with type, severity, and context.

    Attributes:
        error_type: Type of error
        message: Error message
        severity: Error severity (defaults based on type)
        category: Error category (derived from type)
        context: Error context
        original_exception: Original exception if available
    """

    error_type: ErrorType
    message: str
    severity: Optional[ErrorSeverity] = None
    category: Optional[ErrorCategory] = None
    context: ErrorContext = field(default_factory=ErrorContext)
    original_exception: Optional[Exception] = None

    def __post_init__(self) -> None:
        """Set default severity and category if not provided."""
        if self.severity is None:
            self.severity = ERROR_TYPE_SEVERITY_MAP.get(
                self.error_type, ErrorSeverity.MEDIUM
            )

        if self.category is None:
            self.category = ERROR_TYPE_CATEGORY_MAP.get(
                self.error_type, ErrorCategory.SYSTEM
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for reporting."""
        result: Dict[str, Any] = {
            "error_type": self.error_type.value,
            "category": self.category.value if self.category else None,
            "severity": self.severity.value if self.severity else None,
            "message": self.message,
        }

        context = self.context.to_dict()
        if context:
            result["context"] = context

        if self.original_exception:
            result["exception_type"] = type(self.original_exception).__name__

        return result


class ErrorTracker:
    """
    Tracks and aggregates errors across the reporting process.

    Provides error statistics, grouping, and reporting capabilities.
    """

    def __init__(self) -> None:
        self.errors: List[ClassifiedError] = []
        self.errors_by_type: Dict[ErrorType, List[ClassifiedError]] = defaultdict(list)
        self.errors_by_category: Dict[ErrorCategory, List[ClassifiedError]] = defaultdict(list)
        self.errors_by_severity: Dict[ErrorSeverity, List[ClassifiedError]] = defaultdict(list)
        self.errors_by_repo: Dict[str, List[ClassifiedError]] = defaultdict(list)

    def add_error(
        self,
        error_type: ErrorType,
        message: str,
        severity: Optional[ErrorSeverity] = None,
        context: Optional[ErrorContext] = None,
        exception: Optional[Exception] = None,
    ) -> ClassifiedError:
        """
        Add an error to the tracker.

        Args:
            error_type: Type of error
            message: Error message
            severity: Error severity (optional, defaults based on type)
            context: Error context
            exception: Original exception if available

        Returns:
            The classified error
        """
        error = ClassifiedError(
            error_type=error_type,
            message=message,
            severity=severity,
            context=context or ErrorContext(),
            original_exception=exception,
        )

        self.errors.append(error)
        self.errors_by_type[error.error_type].append(error)
        if error.category:
            self.errors_by_category[error.category].append(error)
        if error.severity:
            self.errors_by_severity[error.severity].append(error)

        if error.context.repository:
            self.errors_by_repo[error.context.repository].append(error)

        return error

    def get_error_count(self) -> int:
        """Get total number of errors."""
        return len(self.errors)

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ClassifiedError]:
        """Get all errors of a specific severity."""
        return self.errors_by_severity[severity]

    def get_errors_by_category(self, category: ErrorCategory) -> List[ClassifiedError]:
        """Get all errors of a specific category."""
        return self.errors_by_category[category]

    def get_errors_by_type(self, error_type: ErrorType) -> List[ClassifiedError]:
        """Get all errors of a specific type."""
        return self.errors_by_type[error_type]

    def get_errors_by_repository(self, repository: str) -> List[ClassifiedError]:
        """Get all errors for a specific repository."""
        return self.errors_by_repo[repository]

    def get_summary(self) -> Dict[str, Any]:
        """
        Get error summary statistics.

        Returns:
            Dictionary with error counts by various dimensions.
        """
        return {
            "total_errors": len(self.errors),
            "by_severity": {
                severity.value: len(errors)
                for severity, errors in self.errors_by_severity.items()
            },
            "by_category": {
                category.value: len(errors)
                for category, errors in self.errors_by_category.items()
            },
            "by_type": {
                error_type.value: len(errors)
                for error_type, errors in self.errors_by_type.items()
            },
            "repositories_affected": len(self.errors_by_repo),
        }

    def get_api_failures(self) -> Dict[str, Any]:
        """
        Get API-specific failure summary.

        Returns:
            Dictionary with API error details.
        """
        api_errors = self.errors_by_category[ErrorCategory.API]

        if not api_errors:
            return {}

        return {
            "total_api_errors": len(api_errors),
            "by_type": {
                error_type.value: len(self.errors_by_type[error_type])
                for error_type in ErrorType
                if error_type in self.errors_by_type
                and ERROR_TYPE_CATEGORY_MAP.get(error_type) == ErrorCategory.API
            },
            "rate_limit_hits": len(self.errors_by_type[ErrorType.API_RATE_LIMIT]),
            "authentication_failures": len(self.errors_by_type[ErrorType.API_AUTHENTICATION]),
        }

    def get_partial_failures(self) -> List[Dict[str, Any]]:
        """
        Get repositories with errors but some successful processing.

        Returns:
            List of repositories with error details.
        """
        partial_failures = []

        for repo, errors in self.errors_by_repo.items():
            # Consider it a partial failure if there are errors but not critical ones
            critical_errors = [
                e for e in errors if e.severity == ErrorSeverity.CRITICAL
            ]

            if errors and not critical_errors:
                partial_failures.append({
                    "repository": repo,
                    "error_count": len(errors),
                    "severity_breakdown": {
                        severity.value: len([e for e in errors if e.severity == severity])
                        for severity in ErrorSeverity
                        if any(e.severity == severity for e in errors)
                    },
                    "sample_errors": [e.message for e in errors[:3]],
                })

        return partial_failures

    def get_detailed_report(self) -> List[Dict[str, Any]]:
        """
        Get detailed list of all errors.

        Returns:
            List of error dictionaries with full details.
        """
        return [error.to_dict() for error in self.errors]


def classify_exception(
    exception: Exception,
    context: Optional[ErrorContext] = None,
) -> ClassifiedError:
    """
    Classify a Python exception into an error type.

    Args:
        exception: Exception to classify
        context: Error context

    Returns:
        Classified error
    """
    error_type = ErrorType.SYSTEM_UNKNOWN
    message = str(exception)

    # Classify based on exception type
    exc_type_name = type(exception).__name__

    if "Timeout" in exc_type_name or "timeout" in message.lower():
        error_type = ErrorType.NETWORK_TIMEOUT
    elif "Connection" in exc_type_name or "connection" in message.lower():
        error_type = ErrorType.NETWORK_CONNECTION
    elif "Permission" in exc_type_name or "permission" in message.lower():
        error_type = ErrorType.SYSTEM_PERMISSION
    elif "IOError" in exc_type_name or "FileNotFoundError" in exc_type_name:
        error_type = ErrorType.SYSTEM_IO
    elif "ValueError" in exc_type_name:
        error_type = ErrorType.VALIDATION_TYPE
    elif "TypeError" in exc_type_name:
        error_type = ErrorType.VALIDATION_TYPE

    return ClassifiedError(
        error_type=error_type,
        message=message,
        context=context or ErrorContext(),
        original_exception=exception,
    )
