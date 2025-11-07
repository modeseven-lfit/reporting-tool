#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit Tests for Formatting Utilities

Tests for the formatting utility functions extracted in Phase 1 refactoring.
"""

import sys
from pathlib import Path

import pytest


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from util.formatting import (
    UNKNOWN_AGE,
    format_age,
    format_number,
    slugify,
)


class TestFormatNumber:
    """Tests for format_number function."""

    def test_format_small_numbers(self):
        """Test formatting of numbers less than 1000."""
        assert format_number(0) == "0"
        assert format_number(1) == "1"
        assert format_number(42) == "42"
        assert format_number(999) == "999"

    def test_format_thousands(self):
        """Test formatting of numbers in thousands."""
        assert format_number(1000) == "1.0K"
        assert format_number(1234) == "1.2K"
        assert format_number(9999) == "10.0K"
        assert format_number(50000) == "50.0K"

    def test_format_millions(self):
        """Test formatting of numbers in millions."""
        assert format_number(1_000_000) == "1.0M"
        assert format_number(1_234_567) == "1.2M"
        assert format_number(999_999_999) == "1000.0M"

    def test_format_billions(self):
        """Test formatting of numbers in billions."""
        assert format_number(1_000_000_000) == "1.0B"
        assert format_number(1_234_567_890) == "1.2B"
        assert format_number(9_876_543_210) == "9.9B"

    def test_format_negative_numbers(self):
        """Test formatting of negative numbers."""
        assert format_number(-100) == "-100"
        assert format_number(-1234) == "-1.2K"
        assert format_number(-1_000_000) == "-1.0M"
        assert format_number(-1_000_000_000) == "-1.0B"

    def test_format_with_sign(self):
        """Test formatting with explicit sign for positive numbers."""
        assert format_number(100, signed=True) == "+100"
        assert format_number(1234, signed=True) == "+1.2K"
        assert format_number(0, signed=True) == "0"
        assert format_number(-100, signed=True) == "-100"

    def test_format_floats(self):
        """Test formatting of float values."""
        assert format_number(1234.56) == "1.2K"
        assert format_number(1_234_567.89) == "1.2M"

    def test_format_invalid_input(self):
        """Test formatting of invalid input types."""
        assert format_number("invalid") == "0"
        assert format_number(None) == "0"
        assert format_number([]) == "0"


class TestFormatAge:
    """Tests for format_age function."""

    def test_format_zero_days(self):
        """Test formatting of zero days (today)."""
        result = format_age(0)
        # Should return today's date in YYYY-MM-DD format
        assert len(result) == 10
        assert result.count("-") == 2
        # Just check format, not exact date (time-dependent test)

    def test_format_positive_days(self):
        """Test formatting of positive day counts."""
        result = format_age(30)
        # Should return a date string
        assert len(result) == 10
        assert result.count("-") == 2
        # Format: YYYY-MM-DD
        parts = result.split("-")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_format_unknown_age_none(self):
        """Test formatting when age is None."""
        assert format_age(None) == "Unknown"

    def test_format_unknown_age_sentinel(self):
        """Test formatting when age is sentinel value."""
        assert format_age(UNKNOWN_AGE) == "Unknown"

    def test_format_negative_days(self):
        """Test formatting of negative days (treated as today)."""
        result = format_age(-5)
        # Should treat as today
        assert len(result) == 10
        assert result.count("-") == 2

    def test_format_large_days(self):
        """Test formatting of large day counts."""
        result = format_age(3650)  # ~10 years
        assert len(result) == 10
        assert result.count("-") == 2


class TestSlugify:
    """Tests for slugify function."""

    def test_slugify_simple(self):
        """Test simple text slugification."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test") == "test"

    def test_slugify_multiple_spaces(self):
        """Test slugifying text with multiple spaces."""
        assert slugify("Test  Multiple   Spaces") == "test-multiple-spaces"

    def test_slugify_special_characters(self):
        """Test removing special characters."""
        assert slugify("Special!@#$%Characters") == "specialcharacters"
        assert slugify("Test & Example") == "test-example"

    def test_slugify_with_hyphens(self):
        """Test text already containing hyphens."""
        assert slugify("already-hyphenated") == "already-hyphenated"
        assert slugify("multiple---hyphens") == "multiple-hyphens"

    def test_slugify_with_underscores(self):
        """Test converting underscores to hyphens."""
        assert slugify("with_underscores") == "with-underscores"
        assert slugify("mixed_and-separated") == "mixed-and-separated"

    def test_slugify_leading_trailing_whitespace(self):
        """Test trimming leading/trailing whitespace."""
        assert slugify("  trimmed  ") == "trimmed"
        assert slugify("\ttabbed\t") == "tabbed"

    def test_slugify_empty_string(self):
        """Test slugifying empty string."""
        assert slugify("") == ""

    def test_slugify_numbers(self):
        """Test slugifying text with numbers."""
        assert slugify("Version 1.2.3") == "version-123"
        assert slugify("Test123") == "test123"

    def test_slugify_unicode(self):
        """Test slugifying unicode characters (should be removed)."""
        # Emoji and special unicode should be stripped
        result = slugify("Test 👍 Example")
        assert result == "test-example"


class TestUnknownAgeSentinel:
    """Tests for UNKNOWN_AGE sentinel value."""

    def test_unknown_age_constant(self):
        """Test that UNKNOWN_AGE is the expected sentinel value."""
        assert UNKNOWN_AGE == 999999

    def test_unknown_age_in_format_age(self):
        """Test that UNKNOWN_AGE is properly handled by format_age."""
        assert format_age(UNKNOWN_AGE) == "Unknown"


class TestEdgeCases:
    """Edge case tests for formatting utilities."""

    def test_format_number_boundary_values(self):
        """Test boundary values for number formatting."""
        assert format_number(999) == "999"
        assert format_number(1000) == "1.0K"
        assert format_number(999_999) == "1000.0K"
        assert format_number(1_000_000) == "1.0M"
        assert format_number(999_999_999) == "1000.0M"
        assert format_number(1_000_000_000) == "1.0B"

    def test_format_number_rounding(self):
        """Test rounding behavior."""
        assert format_number(1449) == "1.4K"
        assert format_number(1450) == "1.4K"  # Python's default rounding
        assert format_number(1_449_999) == "1.4M"
        assert format_number(1_500_000) == "1.5M"

    def test_slugify_only_special_chars(self):
        """Test slugifying string with only special characters."""
        assert slugify("!@#$%^&*()") == ""
        assert slugify("---") == "-"  # Hyphens are valid, just normalized

    def test_format_age_year_boundaries(self):
        """Test format_age around year boundaries."""
        # Just verify it returns valid date format
        result = format_age(365)
        assert len(result) == 10
        assert result.count("-") == 2


# Pytest markers for categorization
pytestmark = pytest.mark.unit
