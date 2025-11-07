# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
CLI Package

Command-line interface utilities for the repository reporting system.

This package provides:
- Standardized exit codes
- Enhanced error classes with suggestions
- Argument parsing with improved help text
- Feature discovery
- Progress indicators

Phase 9: CLI & UX Improvements
"""

from .exit_codes import (
    ExitCode,
    get_exit_code_description,
    format_exit_message,
    should_retry,
    EXIT_SUCCESS,
    EXIT_CONFIG_ERROR,
    EXIT_API_ERROR,
    EXIT_PROCESSING_ERROR,
    EXIT_PARTIAL_SUCCESS,
    EXIT_INVALID_ARGS,
    EXIT_PERMISSION_DENIED,
    EXIT_DISK_FULL,
)

from .errors import (
    CLIError,
    ConfigurationError,
    InvalidArgumentError,
    APIError,
    PermissionError,
    DiskSpaceError,
    ValidationError,
    NetworkError,
    format_validation_errors,
    suggest_common_fixes,
)

from .arguments import (
    create_argument_parser,
    parse_arguments,
    validate_arguments,
    get_verbosity_level,
    get_log_level,
    get_output_formats,
    should_generate_zip,
    is_special_mode,
    is_wizard_mode,
    OutputFormat,
    VerbosityLevel,
)

from .features import (
    AVAILABLE_FEATURES,
    get_features_by_category,
    list_all_features,
    get_feature_description,
    get_feature_category,
    get_features_in_category,
    get_all_categories,
    search_features,
    format_feature_list_compact,
    get_feature_count,
    get_category_count,
)

from .validation import (
    ValidationResult,
    DryRunValidator,
    dry_run,
)

from .progress import (
    ProgressIndicator,
    OperationFeedback,
    progress_bar,
    estimate_time_remaining,
    format_count,
    TQDM_AVAILABLE,
)

from .wizard import (
    run_wizard,
    create_config_from_template,
    ConfigurationWizard,
    MINIMAL_TEMPLATE,
    STANDARD_TEMPLATE,
    FULL_TEMPLATE,
)

from .metrics import (
    MetricsCollector,
    get_metrics_collector,
    reset_metrics_collector,
    time_operation,
    record_api_call,
    print_performance_summary,
    print_debug_metrics,
    format_duration,
    format_bytes,
    format_percentage,
    TimingMetric,
    APIStatistics,
    ResourceUsage,
    OperationMetrics,
)

__all__ = [
    # Exit codes
    "ExitCode",
    "get_exit_code_description",
    "format_exit_message",
    "should_retry",
    "EXIT_SUCCESS",
    "EXIT_CONFIG_ERROR",
    "EXIT_API_ERROR",
    "EXIT_PROCESSING_ERROR",
    "EXIT_PARTIAL_SUCCESS",
    "EXIT_INVALID_ARGS",
    "EXIT_PERMISSION_DENIED",
    "EXIT_DISK_FULL",
    # Errors
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
    # Arguments
    "create_argument_parser",
    "parse_arguments",
    "validate_arguments",
    "get_verbosity_level",
    "get_log_level",
    "get_output_formats",
    "should_generate_zip",
    "is_special_mode",
    "is_wizard_mode",
    "OutputFormat",
    "VerbosityLevel",
    # Features
    "AVAILABLE_FEATURES",
    "get_features_by_category",
    "list_all_features",
    "get_feature_description",
    "get_feature_category",
    "get_features_in_category",
    "get_all_categories",
    "search_features",
    "format_feature_list_compact",
    "get_feature_count",
    "get_category_count",
    # Validation
    "ValidationResult",
    "DryRunValidator",
    "dry_run",
    # Progress
    "ProgressIndicator",
    "OperationFeedback",
    "progress_bar",
    "estimate_time_remaining",
    "format_count",
    "TQDM_AVAILABLE",
    # Wizard
    "run_wizard",
    "create_config_from_template",
    "ConfigurationWizard",
    "MINIMAL_TEMPLATE",
    "STANDARD_TEMPLATE",
    "FULL_TEMPLATE",
    # Metrics
    "MetricsCollector",
    "get_metrics_collector",
    "reset_metrics_collector",
    "time_operation",
    "record_api_call",
    "print_performance_summary",
    "print_debug_metrics",
    "format_duration",
    "format_bytes",
    "format_percentage",
    "TimingMetric",
    "APIStatistics",
    "ResourceUsage",
    "OperationMetrics",
]

__version__ = "1.0.0"
