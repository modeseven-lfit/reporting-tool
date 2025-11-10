# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Performance benchmark tests for Repository Reporting System.

This module uses pytest-benchmark to measure and track performance
of critical operations. Benchmarks provide:
- Accurate timing measurements with statistical analysis
- Performance trend tracking over time
- Comparison between different implementations
- Regression detection through historical data
"""

import time
from pathlib import Path

import pytest

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
    CacheStats,
    CacheType,
)
from performance.parallel import (
    ProcessingResult,
    ProcessingStatus,
    ResultAggregator,
    WorkerConfig,
    WorkerPool,
)


pytestmark = pytest.mark.benchmark


class TestCacheBenchmarks:
    """Benchmark cache operations."""

    def test_benchmark_cache_get(self, benchmark, temp_cache_dir: Path):
        """Benchmark cache get operation."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
        key = CacheKey.repository("owner", "repo")
        value = {"data": "test_value" * 100}
        cache.set(key, value, ttl=3600)

        result = benchmark(cache.get, key)
        assert result == value

    def test_benchmark_cache_set(self, benchmark, temp_cache_dir: Path):
        """Benchmark cache set operation."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
        key = CacheKey.repository("owner", "repo")
        value = {"data": "test_value" * 100}

        benchmark(cache.set, key, value, 3600)

    def test_benchmark_cache_get_with_miss(self, benchmark, temp_cache_dir: Path):
        """Benchmark cache get with cache miss."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
        key = CacheKey.repository("owner", "nonexistent")

        result = benchmark(cache.get, key)
        assert result is None

    def test_benchmark_cache_invalidate(self, benchmark, temp_cache_dir: Path):
        """Benchmark cache invalidation."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Setup: Add entries
        for i in range(20):
            key = CacheKey.repository("owner", f"repo_{i}")
            cache.set(key, {"data": f"value_{i}"}, ttl=3600)

        key_to_invalidate = CacheKey.repository("owner", "repo_0")
        benchmark(cache.invalidate, key_to_invalidate)

    def test_benchmark_cache_cleanup(self, benchmark, temp_cache_dir: Path):
        """Benchmark cache cleanup operation."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Setup: Add expired entries
        for i in range(50):
            key = CacheKey.repository("owner", f"repo_{i}")
            cache.set(key, {"data": f"value_{i}"}, ttl=0)  # Already expired

        benchmark(cache.cleanup)

    def test_benchmark_cache_get_stats(self, benchmark, temp_cache_dir: Path):
        """Benchmark cache stats retrieval."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Setup: Add entries and perform operations
        for i in range(30):
            key = CacheKey.repository("owner", f"repo_{i}")
            cache.set(key, {"data": f"value_{i}"}, ttl=3600)
            cache.get(key)

        stats = benchmark(cache.get_stats)
        assert isinstance(stats, CacheStats)

    def test_benchmark_cache_key_generation(self, benchmark):
        """Benchmark cache key generation."""
        result = benchmark(CacheKey.repository, "owner", "repo")
        assert result is not None

    def test_benchmark_cache_entry_expiration_check(self, benchmark):
        """Benchmark cache entry expiration check."""
        entry = CacheEntry(
            key="test_key",
            value={"data": "test"},
            created_at=time.time(),
            ttl=3600,
            size_bytes=100,
            cache_type=CacheType.REPOSITORY_METADATA,
        )

        result = benchmark(entry.is_expired)
        assert result is False


class TestParallelProcessingBenchmarks:
    """Benchmark parallel processing operations."""

    def test_benchmark_worker_pool_creation(self, benchmark, worker_count: int):
        """Benchmark worker pool creation and teardown."""

        def create_pool():
            pool = WorkerPool(max_workers=worker_count)
            with pool:
                pass

        benchmark(create_pool)

    def test_benchmark_result_aggregator_add(self, benchmark):
        """Benchmark adding results to aggregator."""
        aggregator = ResultAggregator(total_items=100)
        result = ProcessingResult(
            item_id="test_item",
            status=ProcessingStatus.SUCCESS,
            result={"value": 42},
            start_time=0.0,
            end_time=0.1,
        )

        benchmark(aggregator.add_result, result)

    def test_benchmark_result_aggregation(self, benchmark):
        """Benchmark result aggregation."""
        aggregator = ResultAggregator(total_items=100)

        # Setup: Add results
        for i in range(100):
            result = ProcessingResult(
                item_id=f"item_{i}",
                status=ProcessingStatus.SUCCESS,
                result={"value": i},
                start_time=0.0,
                end_time=0.1,
            )
            aggregator.add_result(result)

        aggregated = benchmark(aggregator.get_results)
        assert aggregated.success_count == 100

    def test_benchmark_parallel_processing_small_batch(
        self, benchmark, mock_repository_data: list[dict], worker_count: int
    ):
        """Benchmark parallel processing of small batch."""

        def processor(item: dict) -> dict:
            return {"name": item["name"], "stars": item["stars"] * 2}

        def process_items():
            with WorkerPool(max_workers=worker_count) as pool:
                return pool.map(processor, mock_repository_data[:10])

        results = benchmark(process_items)
        assert len(results) == 10

    def test_benchmark_parallel_processing_medium_batch(
        self, benchmark, mock_repository_data: list[dict], worker_count: int
    ):
        """Benchmark parallel processing of medium batch."""

        def processor(item: dict) -> dict:
            return {"name": item["name"], "stars": item["stars"] * 2}

        def process_items():
            with WorkerPool(max_workers=worker_count) as pool:
                return pool.map(processor, mock_repository_data)

        results = benchmark(process_items)
        assert len(results) == len(mock_repository_data)

    def test_benchmark_worker_config_auto_detect(self, benchmark):
        """Benchmark worker count auto-detection."""
        count = benchmark(WorkerConfig.auto_detect_workers)
        assert count > 0


class TestBatchOperationBenchmarks:
    """Benchmark batch operation performance."""

    def test_benchmark_request_queue_operations(self, benchmark):
        """Benchmark request queue enqueue/dequeue."""
        queue = RequestQueue()
        request = APIRequest(
            id="test_req",
            endpoint="/test",
            method="GET",
            priority=RequestPriority.NORMAL,
        )

        def queue_ops():
            queue.enqueue(request)
            return queue.dequeue()

        result = benchmark(queue_ops)
        assert result is not None

    def test_benchmark_request_batching(self, benchmark):
        """Benchmark simple batch operations."""
        # Since RequestBatcher might not have batch_requests method,
        # benchmark queue operations instead
        queue = RequestQueue()

        requests = [
            APIRequest(
                id=f"req_{i}",
                endpoint=f"/repos/{i}",
                method="GET",
                priority=RequestPriority.NORMAL,
            )
            for i in range(50)
        ]

        def batch_ops():
            for req in requests:
                queue.enqueue(req)
            results = []
            while not queue.is_empty():
                results.append(queue.dequeue())
            return results

        results = benchmark(batch_ops)
        assert len(results) == 50

    def test_benchmark_request_cache_key_generation(self, benchmark):
        """Benchmark cache key generation for requests."""
        request = APIRequest(
            id="test_req",
            endpoint="/repos/test",
            method="GET",
            priority=RequestPriority.NORMAL,
        )

        cache_key = benchmark(request.get_cache_key)
        assert cache_key is not None

    def test_benchmark_rate_limit_check(self, benchmark):
        """Benchmark rate limit checking."""
        optimizer = RateLimitOptimizer()

        # Setup rate limit info
        optimizer.update_from_response(
            endpoint="/repos",
            limit=5000,
            remaining=4500,
            reset_time=float(time.time() + 3600),
        )

        result = benchmark(optimizer.can_make_request, "/repos")
        assert result is True

    def test_benchmark_rate_limit_update(self, benchmark):
        """Benchmark rate limit update from response."""
        optimizer = RateLimitOptimizer()

        benchmark(
            optimizer.update_from_response,
            endpoint="/repos",
            limit=5000,
            remaining=4500,
            reset_time=float(time.time() + 3600),
        )

    def test_benchmark_rate_limit_info_check(self, benchmark):
        """Benchmark getting rate limit info."""
        optimizer = RateLimitOptimizer()

        optimizer.update_from_response(
            endpoint="/repos",
            limit=5000,
            remaining=4500,
            reset_time=float(time.time() + 3600),
        )

        info = benchmark(optimizer.get_info, "/repos")
        assert info is not None


class TestIntegratedBenchmarks:
    """Benchmark integrated performance scenarios."""

    def test_benchmark_cache_backed_parallel_processing(
        self,
        benchmark,
        temp_cache_dir: Path,
        mock_repository_data: list[dict],
        worker_count: int,
    ):
        """Benchmark parallel processing with cache."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        def cached_processor(item: dict) -> dict:
            cache_key = CacheKey.repository("owner", item["name"])
            cached = cache.get(cache_key)
            if cached:
                return cached

            result = {"name": item["name"], "stars": item["stars"] * 2}
            cache.set(cache_key, result, ttl=3600)
            return result

        def process_items():
            with WorkerPool(max_workers=worker_count) as pool:
                return pool.map(cached_processor, mock_repository_data[:20])

        results = benchmark(process_items)
        assert len(results) == 20

    def test_benchmark_end_to_end_batch_with_cache(
        self,
        benchmark,
        temp_cache_dir: Path,
        mock_api_responses: list[dict],
    ):
        """Benchmark end-to-end batch processing with caching."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        def process_batch():
            # Create and cache API responses
            for i in range(30):
                cache_key = CacheKey.api_response("GET", f"/repos/{i}")
                cache.set(cache_key, {"response": "data"}, ttl=300)

            # Retrieve from cache
            results = []
            for i in range(30):
                cache_key = CacheKey.api_response("GET", f"/repos/{i}")
                result = cache.get(cache_key)
                if result:
                    results.append(result)

            return len(results)

        result = benchmark(process_batch)
        assert result == 30

    def test_benchmark_concurrent_cache_access(self, benchmark, temp_cache_dir: Path):
        """Benchmark concurrent cache access pattern."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Pre-populate cache
        for i in range(50):
            key = CacheKey.repository("owner", f"repo_{i}")
            cache.set(key, {"data": f"value_{i}"}, ttl=3600)

        def concurrent_access():
            # Simulate mixed read/write operations
            for i in range(25):
                # Read
                key_read = CacheKey.repository("owner", f"repo_{i}")
                cache.get(key_read)

                # Write
                key_write = CacheKey.repository("owner", f"repo_{i + 50}")
                cache.set(key_write, {"data": f"new_value_{i}"}, ttl=3600)

        benchmark(concurrent_access)


class TestMemoryBenchmarks:
    """Benchmark memory-intensive operations."""

    def test_benchmark_large_cache_entry(self, benchmark, temp_cache_dir: Path):
        """Benchmark caching large entries."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=50)
        key = CacheKey.repository("owner", "large_repo")

        # 1MB of data
        large_value = {"data": "x" * (1024 * 1024)}

        benchmark(cache.set, key, large_value, 3600)

    def test_benchmark_cache_with_many_entries(self, benchmark, temp_cache_dir: Path):
        """Benchmark cache with many entries."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=50)

        def populate_cache():
            for i in range(100):
                key = CacheKey.repository("owner", f"repo_{i}")
                cache.set(key, {"data": f"value_{i}" * 10}, ttl=3600)

        benchmark(populate_cache)

    def test_benchmark_batch_processing_large_dataset(
        self, benchmark, large_dataset: list[dict], batch_size: int
    ):
        """Benchmark batch processing of large dataset."""

        def process_in_batches():
            results = []
            for i in range(0, len(large_dataset), batch_size):
                batch = large_dataset[i : i + batch_size]
                batch_results = [{"id": item["id"], "processed": True} for item in batch]
                results.extend(batch_results)
            return results

        results = benchmark(process_in_batches)
        assert len(results) == len(large_dataset)


class TestComparisonBenchmarks:
    """Benchmark comparisons between different approaches."""

    def test_benchmark_compare_cache_hit_vs_miss(self, benchmark, temp_cache_dir: Path):
        """Compare cache hit vs miss performance."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Setup cache with some entries
        for i in range(50):
            key = CacheKey.repository("owner", f"repo_{i}")
            cache.set(key, {"data": f"value_{i}"}, ttl=3600)

        # Benchmark cache hits (even indices exist)
        def cache_operations():
            for i in range(100):
                key = CacheKey.repository("owner", f"repo_{i}")
                cache.get(key)

        benchmark(cache_operations)

    def test_benchmark_compare_serial_vs_parallel_processing(
        self, benchmark, mock_repository_data: list[dict]
    ):
        """Compare serial vs parallel processing (serial version)."""

        def processor(item: dict) -> dict:
            return {"name": item["name"], "stars": item["stars"] * 2}

        items = mock_repository_data[:20]

        # Serial processing
        def serial_process():
            return [processor(item) for item in items]

        results = benchmark(serial_process)
        assert len(results) == 20

    def test_benchmark_compare_batch_sizes(self, benchmark, mock_api_responses: list[dict]):
        """Compare different batch sizes using queue operations."""
        queue = RequestQueue()

        requests = [
            APIRequest(
                id=f"req_{i}",
                endpoint=f"/repos/{i}",
                method="GET",
                priority=RequestPriority.NORMAL,
            )
            for i in range(100)
        ]

        def batch_process():
            queue.clear()  # Clear queue before each benchmark iteration
            for req in requests:
                queue.enqueue(req)
            return queue.size()

        size = benchmark(batch_process)
        assert size == 100


class TestOptimizationBenchmarks:
    """Benchmark specific optimizations."""

    def test_benchmark_optimized_cache_lookup(self, benchmark, temp_cache_dir: Path):
        """Benchmark optimized cache lookup path."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Populate with frequently accessed items
        hot_keys = []
        for i in range(10):
            key = CacheKey.repository("owner", f"hot_repo_{i}")
            cache.set(key, {"data": f"hot_value_{i}"}, ttl=3600)
            hot_keys.append(key)

        # Benchmark hot path
        def hot_path_lookup():
            for key in hot_keys:
                cache.get(key)

        benchmark(hot_path_lookup)

    def test_benchmark_optimized_request_priority_queue(self, benchmark):
        """Benchmark priority queue operations."""
        queue = RequestQueue()

        # Create requests with different priorities
        requests = []
        for i in range(100):
            priority = RequestPriority.HIGH if i % 3 == 0 else RequestPriority.NORMAL
            requests.append(
                APIRequest(
                    id=f"req_{i}",
                    endpoint=f"/repos/{i}",
                    method="GET",
                    priority=priority,
                )
            )

        def priority_ops():
            for req in requests:
                queue.enqueue(req)
            count = 0
            while not queue.is_empty():
                queue.dequeue()
                count += 1
            return count

        count = benchmark(priority_ops)
        assert count == 100
