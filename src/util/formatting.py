# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Formatting Utilities

Pure utility functions for formatting numbers, dates, and other display values.
These functions have no side effects and can be used throughout the application.

Extracted from generate_reports.py as part of Phase 1 refactoring.
"""

from datetime import datetime, timedelta
from typing import Optional, Union


# Sentinel value for unknown age
# Used when age/date cannot be determined
UNKNOWN_AGE = 999999


def format_number(value: Union[int, float], signed: bool = False) -> str:
    """
    Format numbers with K/M/B abbreviation.

    Unified formatting function used throughout the application.
    Converts large numbers to human-readable abbreviated form.

    Args:
        value: Number to format
        signed: If True, add + prefix for positive numbers

    Returns:
        Formatted string with abbreviation (K/M/B) for large numbers

    Examples:
        >>> format_number(1234)
        '1.2K'
        >>> format_number(1234567)
        '1.2M'
        >>> format_number(1234567890)
        '1.2B'
        >>> format_number(100, signed=True)
        '+100'
        >>> format_number(-5000)
        '-5.0K'
    """
    if not isinstance(value, (int, float)):
        return "0"  # type: ignore[unreachable]

    # Handle negative numbers
    is_negative = value < 0
    abs_value = abs(value)

    # Apply abbreviation based on magnitude
    if abs_value >= 1_000_000_000:
        formatted = f"{abs_value / 1_000_000_000:.1f}B"
    elif abs_value >= 1_000_000:
        formatted = f"{abs_value / 1_000_000:.1f}M"
    elif abs_value >= 1_000:
        formatted = f"{abs_value / 1_000:.1f}K"
    else:
        formatted = str(int(abs_value))

    # Add sign prefix
    if is_negative:
        formatted = f"-{formatted}"
    elif signed and value > 0:
        formatted = f"+{formatted}"

    return formatted


def format_age(days: Optional[int]) -> str:
    """
    Format age in days to actual date.

    Unified age formatting function used throughout the application.
    Converts a number of days ago into a calendar date string.

    Args:
        days: Number of days ago (None or UNKNOWN_AGE for unknown)

    Returns:
        Date string in YYYY-MM-DD format, or "Unknown" for sentinel values

    Examples:
        >>> format_age(0)
        '2025-01-15'  # Today's date
        >>> format_age(30)
        '2024-12-16'  # 30 days ago
        >>> format_age(None)
        'Unknown'
        >>> format_age(UNKNOWN_AGE)
        'Unknown'
    """
    # Handle unknown/sentinel values
    if days is None or days == UNKNOWN_AGE:
        return "Unknown"

    # Handle zero or negative (treat as today)
    if days <= 0:
        return datetime.now().strftime("%Y-%m-%d")

    # Calculate actual date (N days ago)
    date = datetime.now() - timedelta(days=days)
    return date.strftime("%Y-%m-%d")


def slugify(text: str) -> str:
    """
    Convert text to URL-friendly slug.

    Removes special characters, converts to lowercase, and replaces
    whitespace with hyphens.

    Args:
        text: Text to convert to slug

    Returns:
        URL-safe slug string

    Examples:
        >>> slugify("Hello World")
        'hello-world'
        >>> slugify("Test  Multiple   Spaces")
        'test-multiple-spaces'
        >>> slugify("Special!@#$%Characters")
        'specialcharacters'
    """
    import re

    # Remove emojis and special chars, convert to lowercase
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    # Normalize whitespace and underscores to single hyphens
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug


# Backwards compatibility aliases
# These can be removed in a future phase once all call sites are updated
def _format_number_legacy(value: Union[int, float], config: dict) -> str:
    """
    Legacy format_number with config parameter.

    Deprecated: Use format_number() directly instead.
    The config parameter is ignored in the new implementation.
    """
    return format_number(value)


def format_age_days(days: int) -> str:
    """
    Legacy format_age_days function.

    Deprecated: Use format_age() instead.
    This alias maintains backwards compatibility.
    """
    return format_age(days)
