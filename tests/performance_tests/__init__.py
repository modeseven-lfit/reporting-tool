# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Performance tests package for Repository Reporting System.

This package contains performance threshold tests and benchmarks to ensure
critical operations meet latency, throughput, and memory requirements.

Modules:
    conftest: Shared fixtures and performance thresholds
    test_thresholds: Performance threshold validation tests
    test_benchmarks: Statistical benchmark tests using pytest-benchmark

Usage:
    # Run all performance tests
    pytest tests/performance/ -v

    # Run threshold tests only
    pytest tests/performance/test_thresholds.py -v -m performance

    # Run benchmarks only
    pytest tests/performance/test_benchmarks.py --benchmark-only
"""

__all__ = [
    "PERFORMANCE_THRESHOLDS",
    "BENCHMARK_CONFIG",
]

from .conftest import BENCHMARK_CONFIG, PERFORMANCE_THRESHOLDS
