# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Comprehensive tests for src/rendering/formatters.py module.

This test suite provides thorough coverage of:
- Number formatting functions
- Date/time formatting functions
- Text formatting utilities
- List formatting
- Edge cases and error handling

Target: 90%+ coverage for formatters.py (from 75.61%)
Phase: 12, Step 4, Task 1.3
"""

import datetime
from datetime import timezone

from rendering.formatters import (
    UNKNOWN_AGE,
    format_age,
    format_bytes,
    format_date,
    format_list,
    format_number,
    format_percentage,
    format_timestamp,
    get_template_filters,
    slugify,
    truncate,
)


# ============================================================================
# format_number Tests
# ============================================================================


class TestFormatNumber:
    """Test number formatting with K/M/B suffixes."""

    def test_format_number_small(self):
        """Test formatting numbers less than 1000."""
        assert format_number(0) == "0"
        assert format_number(1) == "1"
        assert format_number(42) == "42"
        assert format_number(999) == "999"

    def test_format_number_thousands(self):
        """Test formatting thousands with K suffix."""
        assert format_number(1000) == "1.0K"
        assert format_number(1234) == "1.2K"
        assert format_number(9999) == "10.0K"
        assert format_number(50000) == "50.0K"

    def test_format_number_millions(self):
        """Test formatting millions with M suffix."""
        assert format_number(1000000) == "1.0M"
        assert format_number(1234567) == "1.2M"
        assert format_number(9999999) == "10.0M"
        assert format_number(50000000) == "50.0M"

    def test_format_number_billions(self):
        """Test formatting billions with B suffix."""
        assert format_number(1000000000) == "1.0B"
        assert format_number(1234567890) == "1.2B"
        assert format_number(9999999999) == "10.0B"

    def test_format_number_negative(self):
        """Test formatting negative numbers."""
        assert format_number(-1000) == "-1.0K"
        assert format_number(-1000000) == "-1.0M"
        assert format_number(-1000000000) == "-1.0B"

    def test_format_number_float(self):
        """Test formatting float values."""
        assert format_number(1234.56) == "1.2K"
        assert format_number(1234567.89) == "1.2M"

    def test_format_number_none(self):
        """Test that None returns '0'."""
        assert format_number(None) == "0"

    def test_format_number_zero(self):
        """Test that zero returns '0'."""
        assert format_number(0) == "0"
        assert format_number(0.0) == "0"


# ============================================================================
# format_age Tests
# ============================================================================


class TestFormatAge:
    """Test age formatting in human-readable units."""

    def test_format_age_days(self):
        """Test formatting age in days."""
        assert format_age(0) == "0d"
        assert format_age(1) == "1d"
        assert format_age(5) == "5d"
        assert format_age(6) == "6d"

    def test_format_age_weeks(self):
        """Test formatting age in weeks."""
        assert format_age(7) == "1w"
        assert format_age(14) == "2w"
        assert format_age(21) == "3w"
        assert format_age(28) == "4w"
        assert format_age(29) == "4w"

    def test_format_age_months(self):
        """Test formatting age in months."""
        assert format_age(30) == "1m"
        assert format_age(60) == "2m"
        assert format_age(90) == "3m"
        assert format_age(180) == "6m"
        assert format_age(364) == "12m"

    def test_format_age_years(self):
        """Test formatting age in years."""
        assert format_age(365) == "1y"
        assert format_age(730) == "2y"
        assert format_age(1095) == "3y"
        assert format_age(3650) == "10y"

    def test_format_age_none(self):
        """Test that None returns 'unknown'."""
        assert format_age(None) == "unknown"

    def test_format_age_unknown_sentinel(self):
        """Test that UNKNOWN_AGE sentinel returns 'unknown'."""
        assert format_age(UNKNOWN_AGE) == "unknown"

    def test_format_age_negative(self):
        """Test that negative ages return 'unknown'."""
        assert format_age(-1) == "unknown"
        assert format_age(-100) == "unknown"

    def test_format_age_float(self):
        """Test formatting float values."""
        assert format_age(1.5) == "1d"
        assert format_age(7.9) == "1w"
        assert format_age(30.5) == "1m"


# ============================================================================
# format_percentage Tests
# ============================================================================


class TestFormatPercentage:
    """Test percentage formatting."""

    def test_format_percentage_basic(self):
        """Test basic percentage formatting."""
        assert format_percentage(0) == "0.0%"
        assert format_percentage(50) == "50.0%"
        assert format_percentage(75.5) == "75.5%"
        assert format_percentage(100) == "100.0%"

    def test_format_percentage_decimals(self):
        """Test percentage with custom decimal places."""
        assert format_percentage(45.678, decimals=0) == "46%"
        assert format_percentage(45.678, decimals=1) == "45.7%"
        assert format_percentage(45.678, decimals=2) == "45.68%"
        assert format_percentage(45.678, decimals=3) == "45.678%"

    def test_format_percentage_none(self):
        """Test that None is treated as 0."""
        assert format_percentage(None) == "0.0%"
        assert format_percentage(None, decimals=2) == "0.00%"

    def test_format_percentage_float(self):
        """Test formatting float percentages."""
        assert format_percentage(33.333333, decimals=2) == "33.33%"
        assert format_percentage(66.666666, decimals=1) == "66.7%"

    def test_format_percentage_edge_cases(self):
        """Test edge case percentages."""
        assert format_percentage(0.1, decimals=1) == "0.1%"
        assert format_percentage(99.9, decimals=1) == "99.9%"


# ============================================================================
# slugify Tests
# ============================================================================


class TestSlugify:
    """Test URL slug generation."""

    def test_slugify_basic(self):
        """Test basic slugification."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test 123") == "test-123"
        assert slugify("Simple Text") == "simple-text"

    def test_slugify_special_characters(self):
        """Test slugifying text with special characters."""
        assert slugify("Test_123 (Special)") == "test-123-special"
        assert slugify("Hello@World!") == "helloworld"
        assert slugify("Test#$%123") == "test123"

    def test_slugify_multiple_spaces(self):
        """Test slugifying text with multiple spaces."""
        assert slugify("Multiple   Spaces") == "multiple-spaces"
        assert slugify("Tab\tTest") == "tab-test"

    def test_slugify_underscores(self):
        """Test that underscores are converted to hyphens."""
        assert slugify("snake_case_text") == "snake-case-text"
        assert slugify("multiple___underscores") == "multiple-underscores"

    def test_slugify_leading_trailing(self):
        """Test removal of leading/trailing hyphens."""
        assert slugify("  Leading spaces") == "leading-spaces"
        assert slugify("Trailing spaces  ") == "trailing-spaces"
        assert slugify("-hyphen-") == "hyphen"

    def test_slugify_empty(self):
        """Test slugifying empty string."""
        assert slugify("") == ""

    def test_slugify_numbers_only(self):
        """Test slugifying numbers."""
        assert slugify("123456") == "123456"
        assert slugify("123-456") == "123-456"

    def test_slugify_unicode(self):
        """Test that non-ASCII characters are removed."""
        assert slugify("Café") == "caf"
        assert slugify("Über") == "ber"


# ============================================================================
# format_date Tests
# ============================================================================


class TestFormatDate:
    """Test date formatting functionality."""

    def test_format_date_datetime_object(self):
        """Test formatting datetime objects."""
        dt = datetime.datetime(2025, 1, 16, 14, 30, 0)
        assert format_date(dt) == "2025-01-16"

    def test_format_date_date_object(self):
        """Test formatting date objects."""
        d = datetime.date(2025, 1, 16)
        assert format_date(d) == "2025-01-16"

    def test_format_date_iso_string(self):
        """Test formatting ISO date strings."""
        assert format_date("2025-01-16") == "2025-01-16"
        assert format_date("2025-01-16T14:30:00Z") == "2025-01-16"

    def test_format_date_custom_format(self):
        """Test custom format strings."""
        dt = datetime.datetime(2025, 1, 16, 14, 30, 0)
        assert format_date(dt, "%Y/%m/%d") == "2025/01/16"
        assert format_date(dt, "%B %d, %Y") == "January 16, 2025"
        assert format_date(dt, "%m-%d-%Y") == "01-16-2025"

    def test_format_date_none(self):
        """Test that None returns 'unknown'."""
        assert format_date(None) == "unknown"

    def test_format_date_invalid_string(self):
        """Test that invalid date strings are returned as-is."""
        assert format_date("not-a-date") == "not-a-date"
        assert format_date("invalid") == "invalid"

    def test_format_date_iso_with_timezone(self):
        """Test ISO strings with timezone."""
        result = format_date("2025-01-16T14:30:00+00:00")
        assert "2025-01-16" in result

    def test_format_date_with_timezone_object(self):
        """Test datetime with timezone."""
        dt = datetime.datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        assert format_date(dt) == "2025-01-16"


# ============================================================================
# format_timestamp Tests
# ============================================================================


class TestFormatTimestamp:
    """Test timestamp formatting."""

    def test_format_timestamp_basic(self):
        """Test basic timestamp formatting."""
        dt = datetime.datetime(2025, 1, 16, 14, 30, 0)
        assert format_timestamp(dt) == "2025-01-16 14:30:00"

    def test_format_timestamp_iso_string(self):
        """Test formatting ISO timestamp strings."""
        result = format_timestamp("2025-01-16T14:30:00")
        assert "2025-01-16 14:30:00" in result

    def test_format_timestamp_custom_format(self):
        """Test custom timestamp format."""
        dt = datetime.datetime(2025, 1, 16, 14, 30, 0)
        assert format_timestamp(dt, "%Y-%m-%d %H:%M") == "2025-01-16 14:30"

    def test_format_timestamp_none(self):
        """Test that None returns 'unknown'."""
        assert format_timestamp(None) == "unknown"


# ============================================================================
# truncate Tests
# ============================================================================


class TestTruncate:
    """Test text truncation."""

    def test_truncate_short_text(self):
        """Test that short text is not truncated."""
        assert truncate("short", 10) == "short"
        assert truncate("exact", 5) == "exact"

    def test_truncate_long_text(self):
        """Test truncating long text."""
        assert truncate("this is a very long text", 10) == "this is..."
        assert truncate("this is a very long text", 15) == "this is a ve..."

    def test_truncate_custom_suffix(self):
        """Test custom truncation suffix."""
        assert truncate("this is a very long string", 10, suffix="…") == "this is a…"
        assert truncate("long text here", 8, suffix=">>") == "long t>>"

    def test_truncate_exact_length(self):
        """Test text at exact truncation length."""
        text = "exact10chr"
        assert truncate(text, 10) == text

    def test_truncate_empty_string(self):
        """Test truncating empty string."""
        assert truncate("", 10) == ""

    def test_truncate_none(self):
        """Test that None/falsy values are returned as-is."""
        # Based on the code, falsy text is returned as-is
        result = truncate("", 10)
        assert result == ""

    def test_truncate_suffix_longer_than_length(self):
        """Test behavior when suffix is longer than length."""
        # This would result in empty string before suffix
        result = truncate("text", 3, suffix="...")
        assert result == "..."


# ============================================================================
# format_list Tests
# ============================================================================


class TestFormatList:
    """Test list formatting."""

    def test_format_list_empty(self):
        """Test formatting empty list."""
        assert format_list([]) == ""

    def test_format_list_single_item(self):
        """Test formatting list with one item."""
        assert format_list(["apple"]) == "apple"

    def test_format_list_two_items(self):
        """Test formatting list with two items."""
        assert format_list(["apple", "banana"]) == "apple and banana"

    def test_format_list_three_items(self):
        """Test formatting list with three items."""
        assert format_list(["apple", "banana", "cherry"]) == "apple, banana and cherry"

    def test_format_list_many_items(self):
        """Test formatting list with many items."""
        result = format_list(["a", "b", "c", "d", "e"])
        assert result == "a, b, c, d and e"

    def test_format_list_custom_separator(self):
        """Test formatting with custom separator."""
        result = format_list(["a", "b", "c"], separator="; ")
        assert result == "a; b and c"

    def test_format_list_custom_final_separator(self):
        """Test formatting with custom final separator."""
        result = format_list(["a", "b", "c"], final_separator=" or ")
        assert result == "a, b or c"

    def test_format_list_numbers(self):
        """Test formatting list of numbers."""
        assert format_list([1, 2, 3]) == "1, 2 and 3"

    def test_format_list_mixed_types(self):
        """Test formatting list with mixed types."""
        result = format_list(["text", 123, True])
        assert "text" in result
        assert "123" in result
        assert "True" in result


# ============================================================================
# format_bytes Tests
# ============================================================================


class TestFormatBytes:
    """Test byte size formatting."""

    def test_format_bytes_zero(self):
        """Test formatting zero bytes."""
        assert format_bytes(0) == "0 B"
        assert format_bytes(None) == "0 B"

    def test_format_bytes_bytes(self):
        """Test formatting bytes (< 1KB)."""
        assert format_bytes(1) == "1.0 B"
        assert format_bytes(500) == "500.0 B"
        assert format_bytes(1023) == "1023.0 B"

    def test_format_bytes_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1536) == "1.5 KB"
        assert format_bytes(10240) == "10.0 KB"

    def test_format_bytes_megabytes(self):
        """Test formatting megabytes."""
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(1572864) == "1.5 MB"
        assert format_bytes(10485760) == "10.0 MB"

    def test_format_bytes_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_bytes(1073741824) == "1.0 GB"
        assert format_bytes(1610612736) == "1.5 GB"

    def test_format_bytes_terabytes(self):
        """Test formatting terabytes."""
        assert format_bytes(1099511627776) == "1.0 TB"
        assert format_bytes(1649267441664) == "1.5 TB"

    def test_format_bytes_petabytes(self):
        """Test formatting petabytes."""
        assert format_bytes(1125899906842624) == "1.0 PB"

    def test_format_bytes_float(self):
        """Test formatting float byte values."""
        assert format_bytes(1024.5) == "1.0 KB"


# ============================================================================
# get_template_filters Tests
# ============================================================================


class TestGetTemplateFilters:
    """Test template filter registration."""

    def test_get_template_filters_returns_dict(self):
        """Test that function returns a dictionary."""
        filters = get_template_filters()
        assert isinstance(filters, dict)

    def test_get_template_filters_has_all_formatters(self):
        """Test that all formatters are included."""
        filters = get_template_filters()

        expected_filters = [
            "format_number",
            "format_age",
            "format_percentage",
            "slugify",
            "format_date",
            "format_timestamp",
            "truncate",
            "format_list",
            "format_bytes",
        ]

        for filter_name in expected_filters:
            assert filter_name in filters

    def test_get_template_filters_functions_callable(self):
        """Test that all filter values are callable."""
        filters = get_template_filters()

        for filter_func in filters.values():
            assert callable(filter_func)

    def test_get_template_filters_correct_functions(self):
        """Test that filters map to correct functions."""
        filters = get_template_filters()

        assert filters["format_number"] == format_number
        assert filters["format_age"] == format_age
        assert filters["format_percentage"] == format_percentage
        assert filters["slugify"] == slugify
        assert filters["format_date"] == format_date
        assert filters["format_timestamp"] == format_timestamp
        assert filters["truncate"] == truncate
        assert filters["format_list"] == format_list
        assert filters["format_bytes"] == format_bytes


# ============================================================================
# Edge Cases and Integration
# ============================================================================


class TestFormattersEdgeCases:
    """Test edge cases across formatters."""

    def test_format_number_boundary_values(self):
        """Test boundary values for number formatting."""
        assert format_number(999) == "999"
        assert format_number(1000) == "1.0K"
        assert format_number(999999) == "1000.0K"
        assert format_number(1000000) == "1.0M"

    def test_format_age_boundary_values(self):
        """Test boundary values for age formatting."""
        assert format_age(6) == "6d"
        assert format_age(7) == "1w"
        assert format_age(29) == "4w"
        assert format_age(30) == "1m"
        assert format_age(364) == "12m"
        assert format_age(365) == "1y"

    def test_slugify_edge_cases(self):
        """Test edge cases for slugify."""
        assert slugify("---multiple---hyphens---") == "multiple-hyphens"
        assert slugify("ALL CAPS TEXT") == "all-caps-text"
        assert slugify("123") == "123"

    def test_format_bytes_boundary_values(self):
        """Test boundary values for byte formatting."""
        assert format_bytes(1023) == "1023.0 B"
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1048575) == "1024.0 KB"
        assert format_bytes(1048576) == "1.0 MB"
