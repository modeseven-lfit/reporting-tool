# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""Configuration management and validation package.

This package provides configuration loading, validation, and management
for the repository reporting system.

Features:
- JSON Schema-based configuration validation
- Semantic validation (ordering, dependencies, etc.)
- Detailed error messages with suggestions
- Security and performance warnings
- Schema version compatibility checking

Example:
    >>> from src.config import ConfigValidator, validate_config_file
    >>> result = validate_config_file(Path("config/myproject.config"))
    >>> if not result.is_valid:
    ...     for error in result.errors:
    ...         print(error)
"""

from .validator import (
    ConfigValidator,
    ValidationCategory,
    ValidationIssue,
    ValidationLevel,
    ValidationResult,
    print_validation_result,
    validate_config_file,
)

__all__ = [
    "ConfigValidator",
    "ValidationCategory",
    "ValidationIssue",
    "ValidationLevel",
    "ValidationResult",
    "print_validation_result",
    "validate_config_file",
]

__version__ = "1.0.0"
