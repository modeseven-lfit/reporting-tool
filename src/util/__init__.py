# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Utility modules for the Repository Reporting System.

This package contains pure utility functions that have no side effects
and can be used throughout the application.
"""

from .formatting import (
    format_number,
    format_age,
    UNKNOWN_AGE,
)

from .zip_bundle import create_report_bundle

from .github_org import determine_github_org

__all__ = [
    # Formatting utilities
    'format_number',
    'format_age',
    'UNKNOWN_AGE',

    # ZIP bundling
    'create_report_bundle',

    # GitHub organization detection
    'determine_github_org',
]

__version__ = '1.0.0'
