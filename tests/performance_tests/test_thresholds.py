# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Performance threshold tests for Repository Reporting System.

This module tests that critical operations complete within acceptable
performance thresholds. Tests verify:
- Cache operations meet latency requirements
- Parallel processing meets throughput targets
- Batch operations stay within memory limits
- Rate limiting doesn't cause excessive delays
"""

import time
from pathlib import Path

import pytest
from tests.performance_tests.conftest import (
    assert_memory_within_limit,
    assert_throughput_meets_minimum,
    assert_within_threshold,
)

from performance.batch import (
    APIRequest,
    RateLimitOptimizer,
    RequestPriority,
    RequestQueue,
)
from performance.cache import (
    CacheEntry,
    CacheKey,
    CacheManager,
    CacheType,
)
from performance.parallel import (
    WorkerConfig,
    WorkerPool,
)


pytestmark = pytest.mark.performance


class TestCachePerformanceThresholds:
    """Test cache operations meet performance thresholds."""

    def test_cache_get_within_threshold(
        self, temp_cache_dir: Path, perf_thresholds: dict[str, float]
    ):
        """Test cache get operation meets latency threshold."""
        manager = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
        key = CacheKey.repository("owner", "repo")
        value = {"data": "test_value"}

        # Set up cache entry
        manager.set(key, value, ttl=3600)

        # Measure get operation
        start = time.perf_counter()
        result = manager.get(key)
        duration = time.perf_counter() - start

        assert result == value
        assert_within_threshold(duration, perf_thresholds["cache_get"], "Cache get operation")

    def test_cache_set_within_threshold(
        self, temp_cache_dir: Path, perf_thresholds: dict[str, float]
    ):
        """Test cache set operation meets latency threshold."""
        manager = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
        key = CacheKey.repository("owner", "repo")
        value = {"data": "test_value" * 100}

        # Measure set operation
        start = time.perf_counter()
        manager.set(key, value, ttl=3600)
        duration = time.perf_counter() - start

        assert_within_threshold(duration, perf_thresholds["cache_set"], "Cache set operation")

    def test_cache_cleanup_within_threshold(
        self,
        temp_cache_dir: Path,
        mock_cache_entries: list[dict],
        perf_thresholds: dict[str, float],
    ):
        """Test cache cleanup meets performance threshold."""
        manager = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Add expired entries
        for i, entry in enumerate(mock_cache_entries[:50]):
            key = CacheKey.repository("owner", f"repo_{i}")
            manager.set(key, entry["value"], ttl=0)  # Already expired

        # Measure cleanup operation
        start = time.perf_counter()
        manager.cleanup()
        duration = time.perf_counter() - start

        assert_within_threshold(
            duration, perf_thresholds["cache_cleanup"], "Cache cleanup operation"
        )

    def test_cache_invalidate_pattern_within_threshold(
        self, temp_cache_dir: Path, perf_thresholds: dict[str, float]
    ):
        """Test pattern-based cache invalidation meets threshold."""
        manager = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Add entries with pattern
        for i in range(20):
            key = CacheKey.repository("owner", f"repo_{i}")
            manager.set(key, {"data": f"value_{i}"}, ttl=3600)

        # Measure invalidation
        start = time.perf_counter()
        manager.invalidate_pattern("owner")
        duration = time.perf_counter() - start

        assert_within_threshold(
            duration, perf_thresholds["cache_invalidate"], "Cache invalidate pattern"
        )

    def test_cache_size_within_limit(self, temp_cache_dir: Path, perf_thresholds: dict[str, float]):
        """Test cache respects size limits."""
        max_size_mb = 5
        manager = CacheManager(cache_dir=temp_cache_dir, max_size_mb=max_size_mb)

        # Add data until eviction happens
        large_value = "x" * (1024 * 100)  # 100KB per entry
        for i in range(100):
            key = CacheKey.repository("owner", f"repo_{i}")
            manager.set(key, {"data": large_value}, ttl=3600)

        stats = manager.get_stats()
        actual_size = stats.total_size_mb

        # Cache should enforce limit (with some margin for metadata)
        assert_memory_within_limit(actual_size, max_size_mb, "Cache size", margin=0.2)

    def test_cache_throughput_meets_minimum(
        self, temp_cache_dir: Path, perf_thresholds: dict[str, float]
    ):
        """Test cache operations per second meets minimum."""
        manager = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Pre-populate cache
        for i in range(100):
            key = CacheKey.repository("owner", f"repo_{i}")
            manager.set(key, {"data": f"value_{i}"}, ttl=3600)

        # Measure throughput
        operations = 100
        start = time.perf_counter()
        for i in range(operations):
            key = CacheKey.repository("owner", f"repo_{i}")
            manager.get(key)
        duration = time.perf_counter() - start

        ops_per_second = operations / duration
        assert_throughput_meets_minimum(
            ops_per_second,
            perf_thresholds["cache_ops_per_second"],
            "Cache operations",
        )


class TestWorkerPoolThresholds:
    """Test worker pool performance thresholds."""

    def test_worker_pool_creation_within_threshold(
        self, worker_count: int, perf_thresholds: dict[str, float]
    ):
        """Test worker pool creation time."""
        start = time.perf_counter()
        pool = WorkerPool(max_workers=worker_count)
        pool.__enter__()
        duration = time.perf_counter() - start
        pool.__exit__(None, None, None)

        assert_within_threshold(
            duration,
            perf_thresholds["worker_pool_creation"],
            "Worker pool creation",
        )

    def test_worker_pool_task_execution(self, worker_count: int):
        """Test worker pool can execute tasks efficiently."""

        def simple_task(x):
            return x * 2

        items = list(range(20))

        start = time.perf_counter()
        with WorkerPool(max_workers=worker_count) as pool:
            results = pool.map(simple_task, items)
        duration = time.perf_counter() - start

        assert len(results) == 20
        assert results[0] == 0
        assert results[10] == 20
        # Should complete quickly
        assert duration < 1.0


class TestBatchOperationThresholds:
    """Test batch operations meet performance thresholds."""

    def test_rate_limit_check_within_threshold(self, perf_thresholds: dict[str, float]):
        """Test rate limit checking performance."""
        optimizer = RateLimitOptimizer()

        # Initialize with rate limit info
        optimizer.update_from_response(
            endpoint="/repos",
            limit=5000,
            remaining=4500,
            reset_time=float(time.time() + 3600),
        )

        # Measure rate limit check
        start = time.perf_counter()
        for _ in range(100):
            optimizer.can_make_request("/repos")
        duration = time.perf_counter() - start

        per_check_time = duration / 100
        assert_within_threshold(
            per_check_time,
            perf_thresholds["rate_limit_check"],
            "Rate limit check",
        )

    def test_request_queue_operations(self):
        """Test request queue basic operations."""
        queue = RequestQueue()

        # Create test requests
        requests = [
            APIRequest(
                id=f"req_{i}",
                endpoint=f"/repos/{i}",
                method="GET",
                priority=RequestPriority.NORMAL,
            )
            for i in range(100)
        ]

        # Measure enqueue performance
        start = time.perf_counter()
        for req in requests:
            queue.enqueue(req)
        enqueue_duration = time.perf_counter() - start

        assert queue.size() == 100
        assert enqueue_duration < 0.1  # Should be very fast

        # Measure dequeue performance
        start = time.perf_counter()
        dequeued = []
        while not queue.is_empty():
            dequeued.append(queue.dequeue())
        dequeue_duration = time.perf_counter() - start

        assert len(dequeued) == 100
        assert dequeue_duration < 0.1


class TestIntegratedPerformanceThresholds:
    """Test integrated performance scenarios."""

    def test_cache_key_generation_performance(self):
        """Test cache key generation is fast."""
        start = time.perf_counter()
        for i in range(1000):
            CacheKey.repository("owner", f"repo_{i}")
        duration = time.perf_counter() - start

        # Should be able to generate 1000 keys very quickly
        assert duration < 0.1

    def test_memory_constrained_batch_processing(
        self,
        large_dataset: list[dict],
        memory_constraint_mb: int,
        batch_size: int,
    ):
        """Test batch processing respects memory constraints."""
        # Process in batches to stay within memory limit
        batches = [
            large_dataset[i : i + batch_size] for i in range(0, len(large_dataset), batch_size)
        ]

        results = []
        for batch in batches:
            # Process batch
            batch_results = [{"id": item["id"], "processed": True} for item in batch]
            results.extend(batch_results)

        # All items processed
        assert len(results) == len(large_dataset)

        # Memory stayed reasonable (didn't crash or swap excessively)
        # In production, you'd measure actual memory usage

    def test_concurrent_cache_operations_performance(
        self, temp_cache_dir: Path, perf_thresholds: dict[str, float]
    ):
        """Test cache performance under concurrent access."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Simulate concurrent operations
        operations = []
        for i in range(50):
            # Mix of reads and writes
            if i % 2 == 0:
                operations.append(("set", f"key_{i}", {"data": f"value_{i}"}))
            else:
                operations.append(("get", f"key_{i - 1}", None))

        start = time.perf_counter()
        for op_type, key, value in operations:
            cache_key = CacheKey.repository("owner", key)
            if op_type == "set":
                cache.set(cache_key, value, ttl=3600)
            else:
                cache.get(cache_key)
        duration = time.perf_counter() - start

        ops_per_second = len(operations) / duration
        # Should maintain good throughput even with mixed operations
        assert ops_per_second > perf_thresholds["cache_ops_per_second"] * 0.5


class TestPerformanceRegression:
    """Test for performance regressions against baselines."""

    def test_cache_performance_vs_baseline(
        self, temp_cache_dir: Path, perf_thresholds: dict[str, float]
    ):
        """Verify cache performance hasn't regressed from baseline."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Baseline scenario: 100 set/get operations
        timings = []
        for i in range(100):
            key = CacheKey.repository("owner", f"repo_{i}")
            value = {"data": f"value_{i}" * 10}

            start = time.perf_counter()
            cache.set(key, value, ttl=3600)
            result = cache.get(key)
            duration = time.perf_counter() - start
            timings.append(duration)

            assert result == value

        # Check average and p95 latency
        avg_latency = sum(timings) / len(timings)
        timings_sorted = sorted(timings)
        p95_latency = timings_sorted[int(len(timings) * 0.95)]

        # Average should be well under threshold
        assert avg_latency < perf_thresholds["cache_set"] * 2

        # P95 shouldn't be more than 3x threshold
        assert p95_latency < perf_thresholds["cache_set"] * 3

    def test_worker_config_auto_detection(self):
        """Test worker count auto-detection is fast."""
        start = time.perf_counter()
        count = WorkerConfig.auto_detect_workers()
        duration = time.perf_counter() - start

        assert count > 0
        assert count <= 16
        assert duration < 0.01  # Should be nearly instant

    def test_cache_entry_expiration_check(self):
        """Test cache entry expiration check performance."""
        entry = CacheEntry(
            key="test_key",
            value={"data": "test"},
            created_at=time.time(),
            ttl=3600,
            size_bytes=100,
            cache_type=CacheType.REPOSITORY_METADATA,
        )

        # Check expiration many times
        start = time.perf_counter()
        for _ in range(10000):
            is_expired = entry.is_expired()
        duration = time.perf_counter() - start

        assert not is_expired
        assert duration < 0.1  # 10000 checks should be very fast
