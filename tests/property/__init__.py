# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Property-based tests using Hypothesis.

This package contains property-based tests that validate invariants,
mathematical properties, and edge cases across the domain models and
core logic.

Property-based testing generates random inputs according to strategies
and verifies that certain properties always hold, helping discover edge
cases that traditional example-based tests might miss.
"""

__all__ = [
    "test_time_windows",
    "test_aggregations",
    "test_transformations",
]
