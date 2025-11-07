# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Test Utilities - Common Assertions and Helpers

This module provides reusable assertion helpers and utilities for testing
the Repository Reporting System. These utilities help standardize test
assertions and reduce code duplication across test files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
import pytest


# ============================================================================
# JSON Schema Validation
# ============================================================================


def assert_valid_json_schema(data: dict[str, Any], schema: dict[str, Any]) -> None:
    """
    Assert that data conforms to the provided JSON schema.

    Args:
        data: The data to validate
        schema: The JSON schema to validate against

    Raises:
        AssertionError: If validation fails
    """
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"JSON schema validation failed: {e.message}\nPath: {e.path}")
    except jsonschema.SchemaError as e:
        pytest.fail(f"Invalid JSON schema: {e.message}")


def assert_has_required_fields(data: dict[str, Any], required_fields: list[str]) -> None:
    """
    Assert that data contains all required fields.

    Args:
        data: The dictionary to check
        required_fields: List of field names that must be present

    Raises:
        AssertionError: If any required field is missing
    """
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        pytest.fail(f"Missing required fields: {', '.join(missing_fields)}")


def assert_field_type(data: dict[str, Any], field: str, expected_type: type) -> None:
    """
    Assert that a field has the expected type.

    Args:
        data: The dictionary containing the field
        field: The field name to check
        expected_type: The expected type

    Raises:
        AssertionError: If the field doesn't exist or has wrong type
    """
    if field not in data:
        pytest.fail(f"Field '{field}' not found in data")

    if not isinstance(data[field], expected_type):
        actual_type = type(data[field]).__name__
        expected_name = expected_type.__name__
        pytest.fail(f"Field '{field}' has type {actual_type}, expected {expected_name}")


def assert_no_unexpected_fields(
    data: dict[str, Any], allowed_fields: list[str], strict: bool = False
) -> None:
    """
    Assert that data contains no unexpected fields.

    Args:
        data: The dictionary to check
        allowed_fields: List of allowed field names
        strict: If True, fail on any unexpected field. If False, just warn.

    Raises:
        AssertionError: If strict=True and unexpected fields found
    """
    unexpected_fields = [field for field in data if field not in allowed_fields]
    if unexpected_fields:
        message = f"Unexpected fields found: {', '.join(unexpected_fields)}"
        if strict:
            pytest.fail(message)
        else:
            pytest.warns(UserWarning, match=message)


# ============================================================================
# Performance Assertions
# ============================================================================


def assert_performance_threshold(
    actual_time: float, max_time: float, operation: str = "Operation"
) -> None:
    """
    Assert that an operation completed within a time threshold.

    Args:
        actual_time: The actual execution time in seconds
        max_time: The maximum allowed time in seconds
        operation: Description of the operation being timed

    Raises:
        AssertionError: If actual time exceeds max time
    """
    if actual_time > max_time:
        pytest.fail(f"{operation} took {actual_time:.2f}s, exceeding threshold of {max_time:.2f}s")


def assert_memory_threshold(
    actual_memory_mb: float, max_memory_mb: float, operation: str = "Operation"
) -> None:
    """
    Assert that an operation used memory within a threshold.

    Args:
        actual_memory_mb: The actual memory usage in MB
        max_memory_mb: The maximum allowed memory in MB
        operation: Description of the operation

    Raises:
        AssertionError: If actual memory exceeds max memory
    """
    if actual_memory_mb > max_memory_mb:
        pytest.fail(
            f"{operation} used {actual_memory_mb:.1f}MB, "
            f"exceeding threshold of {max_memory_mb:.1f}MB"
        )


def assert_speedup(baseline_time: float, optimized_time: float, min_speedup: float = 2.0) -> None:
    """
    Assert that an optimization achieved minimum speedup.

    Args:
        baseline_time: Time before optimization in seconds
        optimized_time: Time after optimization in seconds
        min_speedup: Minimum required speedup factor

    Raises:
        AssertionError: If speedup is less than minimum
    """
    if optimized_time <= 0:
        pytest.fail("Optimized time must be greater than 0")

    actual_speedup = baseline_time / optimized_time
    if actual_speedup < min_speedup:
        pytest.fail(
            f"Speedup of {actual_speedup:.2f}x is less than minimum required {min_speedup:.2f}x"
        )


# ============================================================================
# Regression Assertions
# ============================================================================


def assert_no_regression(
    current_value: int | float,
    baseline_value: int | float,
    tolerance_percent: float = 10.0,
    metric_name: str = "Metric",
) -> None:
    """
    Assert that a metric hasn't regressed beyond tolerance.

    Args:
        current_value: The current metric value
        baseline_value: The baseline metric value
        tolerance_percent: Allowed regression percentage
        metric_name: Name of the metric being checked

    Raises:
        AssertionError: If regression exceeds tolerance
    """
    if baseline_value == 0:
        pytest.fail("Baseline value cannot be zero")

    change_percent = ((current_value - baseline_value) / baseline_value) * 100

    if change_percent > tolerance_percent:
        pytest.fail(
            f"{metric_name} regressed by {change_percent:.1f}%, "
            f"exceeding tolerance of {tolerance_percent:.1f}%"
        )


def assert_output_stable(
    current_output: dict[str, Any],
    baseline_output: dict[str, Any],
    ignore_fields: list[str] | None = None,
) -> None:
    """
    Assert that output is stable compared to baseline.

    Args:
        current_output: Current output dictionary
        baseline_output: Baseline output dictionary
        ignore_fields: Fields to ignore in comparison

    Raises:
        AssertionError: If outputs differ unexpectedly
    """
    ignore_fields = ignore_fields or []

    def _filter_dict(d: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in d.items() if k not in ignore_fields}

    current = _filter_dict(current_output)
    baseline = _filter_dict(baseline_output)

    if current != baseline:
        # Find differences
        all_keys = set(current.keys()) | set(baseline.keys())
        differences = []

        for key in all_keys:
            if key not in current:
                differences.append(f"Missing in current: {key}")
            elif key not in baseline:
                differences.append(f"New in current: {key}")
            elif current[key] != baseline[key]:
                differences.append(
                    f"Changed: {key} (baseline: {baseline[key]}, current: {current[key]})"
                )

        pytest.fail(
            "Output has changed unexpectedly:\n" + "\n".join(f"  - {diff}" for diff in differences)
        )


# ============================================================================
# File Assertions
# ============================================================================


def assert_file_exists(file_path: str | Path, message: str = None) -> None:
    """
    Assert that a file exists.

    Args:
        file_path: Path to the file
        message: Optional custom error message

    Raises:
        AssertionError: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        msg = message or f"File does not exist: {path}"
        pytest.fail(msg)


def assert_file_contains(file_path: str | Path, expected_content: str, message: str = None) -> None:
    """
    Assert that a file contains expected content.

    Args:
        file_path: Path to the file
        expected_content: Content that should be in the file
        message: Optional custom error message

    Raises:
        AssertionError: If file doesn't contain expected content
    """
    path = Path(file_path)
    assert_file_exists(path)

    actual_content = path.read_text()
    if expected_content not in actual_content:
        msg = message or f"File {path} does not contain expected content"
        pytest.fail(msg)


def assert_valid_json_file(file_path: str | Path) -> dict[str, Any]:
    """
    Assert that a file contains valid JSON and return the parsed data.

    Args:
        file_path: Path to the JSON file

    Returns:
        Parsed JSON data

    Raises:
        AssertionError: If file doesn't exist or contains invalid JSON
    """
    path = Path(file_path)
    assert_file_exists(path)

    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        pytest.fail(f"File {path} contains invalid JSON: {e}")


# ============================================================================
# Data Assertions
# ============================================================================


def assert_list_contains_all(
    actual_list: list[Any], expected_items: list[Any], message: str = None
) -> None:
    """
    Assert that a list contains all expected items.

    Args:
        actual_list: The list to check
        expected_items: Items that must be in the list
        message: Optional custom error message

    Raises:
        AssertionError: If any expected item is missing
    """
    missing_items = [item for item in expected_items if item not in actual_list]
    if missing_items:
        msg = message or f"List is missing items: {missing_items}"
        pytest.fail(msg)


def assert_list_unique(actual_list: list[Any], message: str = None) -> None:
    """
    Assert that all items in a list are unique.

    Args:
        actual_list: The list to check
        message: Optional custom error message

    Raises:
        AssertionError: If duplicate items found
    """
    seen = set()
    duplicates = []

    for item in actual_list:
        if item in seen:
            duplicates.append(item)
        seen.add(item)

    if duplicates:
        msg = message or f"List contains duplicates: {duplicates}"
        pytest.fail(msg)


def assert_dict_subset(
    actual_dict: dict[str, Any], expected_subset: dict[str, Any], message: str = None
) -> None:
    """
    Assert that a dictionary contains all key-value pairs from expected subset.

    Args:
        actual_dict: The dictionary to check
        expected_subset: Key-value pairs that must be in actual_dict
        message: Optional custom error message

    Raises:
        AssertionError: If any expected key-value pair is missing or different
    """
    differences = []

    for key, expected_value in expected_subset.items():
        if key not in actual_dict:
            differences.append(f"Missing key: {key}")
        elif actual_dict[key] != expected_value:
            differences.append(
                f"Different value for {key}: expected {expected_value}, got {actual_dict[key]}"
            )

    if differences:
        msg = message or "Dictionary subset mismatch:\n" + "\n".join(
            f"  - {diff}" for diff in differences
        )
        pytest.fail(msg)


# ============================================================================
# String Assertions
# ============================================================================


def assert_string_matches_pattern(actual_string: str, pattern: str, message: str = None) -> None:
    """
    Assert that a string matches a regex pattern.

    Args:
        actual_string: The string to check
        pattern: The regex pattern to match
        message: Optional custom error message

    Raises:
        AssertionError: If string doesn't match pattern
    """
    import re

    if not re.search(pattern, actual_string):
        msg = message or f"String '{actual_string}' doesn't match pattern '{pattern}'"
        pytest.fail(msg)


def assert_string_length(
    actual_string: str, min_length: int = None, max_length: int = None, message: str = None
) -> None:
    """
    Assert that a string length is within bounds.

    Args:
        actual_string: The string to check
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        message: Optional custom error message

    Raises:
        AssertionError: If string length is out of bounds
    """
    actual_length = len(actual_string)

    if min_length is not None and actual_length < min_length:
        msg = message or f"String length {actual_length} is less than minimum {min_length}"
        pytest.fail(msg)

    if max_length is not None and actual_length > max_length:
        msg = message or f"String length {actual_length} exceeds maximum {max_length}"
        pytest.fail(msg)


# ============================================================================
# Datetime Assertions
# ============================================================================


def assert_datetime_recent(
    dt: datetime, max_age_seconds: float = 60.0, message: str = None
) -> None:
    """
    Assert that a datetime is recent (within max_age_seconds of now).

    Args:
        dt: The datetime to check
        max_age_seconds: Maximum age in seconds
        message: Optional custom error message

    Raises:
        AssertionError: If datetime is too old
    """
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    age_seconds = (now - dt).total_seconds()

    if age_seconds > max_age_seconds:
        msg = message or (
            f"Datetime is {age_seconds:.1f}s old, exceeding maximum {max_age_seconds:.1f}s"
        )
        pytest.fail(msg)


def assert_datetime_in_range(
    dt: datetime, start: datetime, end: datetime, message: str = None
) -> None:
    """
    Assert that a datetime is within a range.

    Args:
        dt: The datetime to check
        start: Start of the range (inclusive)
        end: End of the range (inclusive)
        message: Optional custom error message

    Raises:
        AssertionError: If datetime is outside the range
    """
    if not (start <= dt <= end):
        msg = message or f"Datetime {dt} is not in range [{start}, {end}]"
        pytest.fail(msg)


# ============================================================================
# Error Assertions
# ============================================================================


def assert_raises_with_message(
    exception_class: type, expected_message: str, callable_func, *args, **kwargs
) -> None:
    """
    Assert that a function raises an exception with a specific message.

    Args:
        exception_class: The expected exception class
        expected_message: The expected error message (substring match)
        callable_func: The function to call
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Raises:
        AssertionError: If exception not raised or message doesn't match
    """
    with pytest.raises(exception_class) as exc_info:
        callable_func(*args, **kwargs)

    actual_message = str(exc_info.value)
    if expected_message not in actual_message:
        pytest.fail(f"Exception message '{actual_message}' doesn't contain '{expected_message}'")


# ============================================================================
# Coverage Assertions
# ============================================================================


def assert_coverage_threshold(
    coverage_percent: float, min_coverage: float = 85.0, module_name: str = "Module"
) -> None:
    """
    Assert that code coverage meets minimum threshold.

    Args:
        coverage_percent: The actual coverage percentage
        min_coverage: The minimum required coverage percentage
        module_name: Name of the module being checked

    Raises:
        AssertionError: If coverage is below threshold
    """
    if coverage_percent < min_coverage:
        pytest.fail(
            f"{module_name} coverage of {coverage_percent:.1f}% "
            f"is below minimum {min_coverage:.1f}%"
        )
