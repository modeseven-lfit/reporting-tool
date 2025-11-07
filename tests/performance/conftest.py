# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Shared fixtures and configuration for performance tests.

This module provides common fixtures, constants, and utilities
for performance threshold tests and benchmarks.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


# Performance thresholds (adjust based on baseline measurements)
PERFORMANCE_THRESHOLDS = {
    # Cache operations (seconds)
    "cache_get": 0.001,  # 1ms
    "cache_set": 0.002,  # 2ms
    "cache_cleanup": 0.1,  # 100ms
    "cache_invalidate": 0.005,  # 5ms
    # Parallel processing (seconds)
    "worker_pool_creation": 0.1,  # 100ms
    "batch_processing_per_item": 0.05,  # 50ms per item
    "result_aggregation": 0.01,  # 10ms
    # Batch operations (seconds)
    "request_batching": 0.01,  # 10ms
    "rate_limit_check": 0.001,  # 1ms
    "request_deduplication": 0.005,  # 5ms
    # Memory limits (MB)
    "cache_max_size": 100,  # 100MB
    "worker_memory_per_item": 10,  # 10MB per item
    "batch_memory_overhead": 50,  # 50MB overhead
    # Throughput (items/second)
    "cache_ops_per_second": 1000,
    "batch_requests_per_second": 100,
    "parallel_items_per_second": 50,
}

# Benchmark configuration
BENCHMARK_CONFIG = {
    "min_rounds": 5,
    "max_time": 1.0,  # 1 second max per benchmark
    "warmup": True,
    "warmup_iterations": 2,
}


@pytest.fixture
def perf_thresholds() -> dict[str, float]:
    """Return performance thresholds for validation."""
    return PERFORMANCE_THRESHOLDS.copy()


@pytest.fixture
def benchmark_config() -> dict[str, Any]:
    """Return benchmark configuration."""
    return BENCHMARK_CONFIG.copy()


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temporary cache directory for tests."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


@pytest.fixture
def mock_cache_entries(temp_cache_dir: Path) -> list[dict[str, Any]]:
    """Create mock cache entries for testing."""
    entries = []
    for i in range(100):
        entry = {
            "key": f"test_key_{i}",
            "value": {"data": f"test_value_{i}" * 10},
            "timestamp": 1609459200.0 + i,
            "ttl": 3600,
        }
        entries.append(entry)

        # Write to cache file
        cache_file = temp_cache_dir / f"entry_{i}.json"
        with open(cache_file, "w") as f:
            json.dump(entry, f)

    return entries


@pytest.fixture
def mock_repository_data() -> list[dict[str, Any]]:
    """Generate mock repository data for batch processing."""
    repositories = []
    for i in range(50):
        repo = {
            "name": f"repo_{i}",
            "owner": f"owner_{i % 10}",
            "stars": i * 10,
            "forks": i * 5,
            "size": i * 1000,
            "commits": i * 100,
        }
        repositories.append(repo)
    return repositories


@pytest.fixture
def mock_api_responses() -> list[dict[str, Any]]:
    """Generate mock API responses for testing."""
    responses = []
    for i in range(100):
        response = {
            "id": i,
            "status": 200 if i % 10 != 0 else 429,  # Some rate limited
            "data": {"result": f"data_{i}" * 20},
            "headers": {
                "X-RateLimit-Remaining": str(5000 - i),
                "X-RateLimit-Limit": "5000",
                "X-RateLimit-Reset": "1609459200",
            },
        }
        responses.append(response)
    return responses


@pytest.fixture
def performance_logger():
    """Create a mock logger for performance tracking."""
    logger = MagicMock()
    logger.timings = []
    logger.memory_samples = []

    def log_timing(operation: str, duration: float):
        logger.timings.append({"operation": operation, "duration": duration})

    def log_memory(operation: str, memory_mb: float):
        logger.memory_samples.append({"operation": operation, "memory_mb": memory_mb})

    logger.log_timing = log_timing
    logger.log_memory = log_memory

    return logger


@pytest.fixture
def large_dataset() -> list[dict[str, Any]]:
    """Generate a large dataset for stress testing."""
    return [
        {
            "id": i,
            "data": "x" * 1000,  # 1KB per item
            "nested": {"values": list(range(100))},
        }
        for i in range(1000)
    ]


@pytest.fixture
def memory_constraint_mb() -> int:
    """Return memory constraint for testing (MB)."""
    return 50  # 50MB limit for tests


@pytest.fixture
def worker_count() -> int:
    """Return optimal worker count for testing."""
    import multiprocessing

    return min(multiprocessing.cpu_count(), 4)


@pytest.fixture
def batch_size() -> int:
    """Return optimal batch size for testing."""
    return 10


def assert_within_threshold(
    actual: float,
    threshold: float,
    operation: str,
    margin: float = 0.1,
) -> None:
    """
    Assert that an actual value is within threshold with margin.

    Args:
        actual: Actual measured value
        threshold: Expected threshold
        operation: Name of operation being tested
        margin: Acceptable margin as percentage (default 10%)

    Raises:
        AssertionError: If actual exceeds threshold + margin
    """
    max_allowed = threshold * (1 + margin)
    assert actual <= max_allowed, (
        f"{operation} exceeded threshold: "
        f"{actual:.6f}s > {max_allowed:.6f}s "
        f"(threshold: {threshold:.6f}s + {margin * 100}% margin)"
    )


def assert_memory_within_limit(
    actual_mb: float,
    limit_mb: float,
    operation: str,
    margin: float = 0.1,
) -> None:
    """
    Assert that memory usage is within limit with margin.

    Args:
        actual_mb: Actual memory usage in MB
        limit_mb: Memory limit in MB
        operation: Name of operation being tested
        margin: Acceptable margin as percentage (default 10%)

    Raises:
        AssertionError: If memory exceeds limit + margin
    """
    max_allowed = limit_mb * (1 + margin)
    assert actual_mb <= max_allowed, (
        f"{operation} exceeded memory limit: "
        f"{actual_mb:.2f}MB > {max_allowed:.2f}MB "
        f"(limit: {limit_mb:.2f}MB + {margin * 100}% margin)"
    )


def assert_throughput_meets_minimum(
    actual_ops_per_sec: float,
    minimum_ops_per_sec: float,
    operation: str,
    margin: float = 0.1,
) -> None:
    """
    Assert that throughput meets minimum requirement.

    Args:
        actual_ops_per_sec: Actual operations per second
        minimum_ops_per_sec: Minimum required ops/sec
        operation: Name of operation being tested
        margin: Acceptable margin as percentage (default 10%)

    Raises:
        AssertionError: If throughput is below minimum - margin
    """
    min_allowed = minimum_ops_per_sec * (1 - margin)
    assert actual_ops_per_sec >= min_allowed, (
        f"{operation} below throughput requirement: "
        f"{actual_ops_per_sec:.2f} ops/sec < {min_allowed:.2f} ops/sec "
        f"(minimum: {minimum_ops_per_sec:.2f} ops/sec - {margin * 100}% margin)"
    )


# Export helper functions for use in tests
__all__ = [
    "PERFORMANCE_THRESHOLDS",
    "BENCHMARK_CONFIG",
    "assert_within_threshold",
    "assert_memory_within_limit",
    "assert_throughput_meets_minimum",
]
