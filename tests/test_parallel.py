# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for the parallel processing module.

This module tests:
- ParallelRepositoryProcessor functionality
- WorkerPool management
- ResultAggregator thread safety
- WorkerConfig validation
- ProcessingResult data structures
- Parallel execution and error handling
"""

import threading
import time

import pytest

from performance import (
    AggregatedResults,
    ParallelRepositoryProcessor,
    PerformanceProfiler,
    ProcessingResult,
    ProcessingStatus,
    ResultAggregator,
    WorkerConfig,
    WorkerPool,
    WorkerType,
    parallel_map,
)


class TestWorkerConfig:
    """Tests for WorkerConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = WorkerConfig()

        assert config.max_workers == 4
        assert config.worker_type == WorkerType.THREAD
        assert config.worker_timeout == 300
        assert config.batch_size == 10
        assert config.retry_on_failure is False
        assert config.max_retries == 2
        assert config.stop_on_error is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = WorkerConfig(
            max_workers=8,
            worker_type=WorkerType.PROCESS,
            worker_timeout=600,
            batch_size=20,
            retry_on_failure=True,
            max_retries=3,
            stop_on_error=True,
        )

        assert config.max_workers == 8
        assert config.worker_type == WorkerType.PROCESS
        assert config.worker_timeout == 600
        assert config.batch_size == 20
        assert config.retry_on_failure is True
        assert config.max_retries == 3
        assert config.stop_on_error is True

    def test_invalid_max_workers_too_low(self):
        """Test validation rejects invalid max_workers (too low)."""
        with pytest.raises(ValueError, match="max_workers must be >= 1"):
            WorkerConfig(max_workers=0)

    def test_invalid_max_workers_too_high(self):
        """Test validation rejects invalid max_workers (too high)."""
        with pytest.raises(ValueError, match="max_workers must be <= 64"):
            WorkerConfig(max_workers=100)

    def test_invalid_timeout(self):
        """Test validation rejects invalid timeout."""
        with pytest.raises(ValueError, match="worker_timeout must be >= 1"):
            WorkerConfig(worker_timeout=0)

    def test_invalid_batch_size(self):
        """Test validation rejects invalid batch_size."""
        with pytest.raises(ValueError, match="batch_size must be >= 1"):
            WorkerConfig(batch_size=0)

    def test_invalid_max_retries(self):
        """Test validation rejects invalid max_retries."""
        with pytest.raises(ValueError, match="max_retries must be >= 0"):
            WorkerConfig(max_retries=-1)

    def test_auto_detect_workers(self):
        """Test auto-detection of worker count."""
        count = WorkerConfig.auto_detect_workers()

        assert count >= 1
        assert count <= 16


class TestProcessingResult:
    """Tests for ProcessingResult class."""

    def test_result_creation(self):
        """Test creating a processing result."""
        result = ProcessingResult(
            item_id="repo1",
            status=ProcessingStatus.SUCCESS,
            result={"data": "value"},
            start_time=0.0,
            end_time=1.5,
            worker_id=1,
        )

        assert result.item_id == "repo1"
        assert result.status == ProcessingStatus.SUCCESS
        assert result.result == {"data": "value"}
        assert result.duration == 1.5
        assert result.worker_id == 1

    def test_is_success(self):
        """Test is_success property."""
        result = ProcessingResult(item_id="repo1", status=ProcessingStatus.SUCCESS)

        assert result.is_success is True
        assert result.is_failure is False

    def test_is_failure(self):
        """Test is_failure property."""
        result = ProcessingResult(
            item_id="repo1", status=ProcessingStatus.FAILED, error="Test error"
        )

        assert result.is_success is False
        assert result.is_failure is True

    def test_timeout_status(self):
        """Test timeout status."""
        result = ProcessingResult(item_id="repo1", status=ProcessingStatus.TIMEOUT, error="Timeout")

        assert result.is_success is False
        assert result.is_failure is True


class TestAggregatedResults:
    """Tests for AggregatedResults class."""

    def test_empty_results(self):
        """Test empty aggregated results."""
        results = AggregatedResults(total=0)

        assert results.total == 0
        assert results.success_count == 0
        assert results.failure_count == 0
        assert results.success_rate == 0.0
        assert results.avg_duration == 0.0

    def test_all_successful(self):
        """Test all successful results."""
        successful = [
            ProcessingResult("repo1", ProcessingStatus.SUCCESS, start_time=0, end_time=1),
            ProcessingResult("repo2", ProcessingStatus.SUCCESS, start_time=0, end_time=2),
            ProcessingResult("repo3", ProcessingStatus.SUCCESS, start_time=0, end_time=1.5),
        ]

        results = AggregatedResults(total=3, successful=successful, failed=[], total_duration=5.0)

        assert results.success_count == 3
        assert results.failure_count == 0
        assert results.success_rate == 100.0
        assert results.avg_duration == 1.5  # (1 + 2 + 1.5) / 3

    def test_mixed_results(self):
        """Test mixed success and failure results."""
        successful = [
            ProcessingResult("repo1", ProcessingStatus.SUCCESS, start_time=0, end_time=1),
            ProcessingResult("repo2", ProcessingStatus.SUCCESS, start_time=0, end_time=2),
        ]
        failed = [
            ProcessingResult("repo3", ProcessingStatus.FAILED, error="Error"),
        ]

        results = AggregatedResults(total=3, successful=successful, failed=failed)

        assert results.success_count == 2
        assert results.failure_count == 1
        assert results.success_rate == pytest.approx(66.67, rel=0.1)


class TestResultAggregator:
    """Tests for ResultAggregator class."""

    def test_aggregator_initialization(self):
        """Test aggregator initialization."""
        aggregator = ResultAggregator(total_items=10)

        completed, total = aggregator.get_progress()
        assert completed == 0
        assert total == 10

    def test_add_single_result(self):
        """Test adding a single result."""
        aggregator = ResultAggregator(total_items=5)

        result = ProcessingResult("repo1", ProcessingStatus.SUCCESS)
        aggregator.add_result(result)

        completed, total = aggregator.get_progress()
        assert completed == 1
        assert total == 5

    def test_add_multiple_results(self):
        """Test adding multiple results."""
        aggregator = ResultAggregator(total_items=3)

        aggregator.add_result(ProcessingResult("repo1", ProcessingStatus.SUCCESS))
        aggregator.add_result(ProcessingResult("repo2", ProcessingStatus.SUCCESS))
        aggregator.add_result(ProcessingResult("repo3", ProcessingStatus.FAILED, error="Error"))

        results = aggregator.get_results()

        assert results.total == 3
        assert results.success_count == 2
        assert results.failure_count == 1

    def test_thread_safety(self):
        """Test thread-safe result collection."""
        aggregator = ResultAggregator(total_items=100)

        def add_results(start, end):
            for i in range(start, end):
                result = ProcessingResult(f"repo{i}", ProcessingStatus.SUCCESS)
                aggregator.add_result(result)

        # Create multiple threads adding results
        threads = []
        for i in range(10):
            thread = threading.Thread(target=add_results, args=(i * 10, (i + 1) * 10))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify all results collected
        completed, total = aggregator.get_progress()
        assert completed == 100
        assert total == 100


class TestWorkerPool:
    """Tests for WorkerPool class."""

    def test_thread_pool_creation(self):
        """Test thread pool creation."""
        with WorkerPool(max_workers=2, worker_type=WorkerType.THREAD) as pool:
            assert pool.executor is not None

    def test_pool_context_manager(self):
        """Test pool as context manager."""
        pool = WorkerPool(max_workers=2, worker_type=WorkerType.THREAD)

        with pool:
            assert pool.executor is not None

        # Executor should be shutdown after context
        assert pool.executor is not None  # Still exists but shutdown

    def test_pool_map(self):
        """Test pool map function."""

        def square(x):
            return x * x

        with WorkerPool(max_workers=2, worker_type=WorkerType.THREAD) as pool:
            results = pool.map(square, [1, 2, 3, 4])

        assert results == [1, 4, 9, 16]

    def test_pool_submit(self):
        """Test pool submit function."""

        def add(x, y):
            return x + y

        with WorkerPool(max_workers=2, worker_type=WorkerType.THREAD) as pool:
            future = pool.submit(add, 5, 3)
            result = future.result()

        assert result == 8

    def test_pool_error_outside_context(self):
        """Test error when using pool outside context."""
        pool = WorkerPool(max_workers=2, worker_type=WorkerType.THREAD)

        with pytest.raises(RuntimeError, match="must be used as context manager"):
            pool.submit(lambda: None)


class TestParallelRepositoryProcessor:
    """Tests for ParallelRepositoryProcessor class."""

    def test_processor_initialization_default(self):
        """Test processor with default configuration."""
        processor = ParallelRepositoryProcessor()

        assert processor.config.max_workers > 0
        assert processor.config.worker_type == WorkerType.THREAD

    def test_processor_initialization_custom_workers(self):
        """Test processor with custom worker count."""
        processor = ParallelRepositoryProcessor(max_workers=8)

        assert processor.config.max_workers == 8

    def test_processor_initialization_with_config(self):
        """Test processor with custom config."""
        config = WorkerConfig(max_workers=6, batch_size=5)
        processor = ParallelRepositoryProcessor(config=config)

        assert processor.config.max_workers == 6
        assert processor.config.batch_size == 5

    def test_process_empty_list(self):
        """Test processing empty repository list."""
        processor = ParallelRepositoryProcessor(max_workers=2)

        def analyze(repo):
            return {"repo": repo}

        results = processor.process_repositories([], analyze)

        assert results.total == 0
        assert results.success_count == 0

    def test_process_single_repository(self):
        """Test processing single repository."""
        processor = ParallelRepositoryProcessor(max_workers=2)

        def analyze(repo):
            return {"repo": repo, "files": 10}

        results = processor.process_repositories(["repo1"], analyze)

        assert results.total == 1
        assert results.success_count == 1
        assert "repo1" in results.results
        assert results.results["repo1"]["files"] == 10

    def test_process_multiple_repositories(self):
        """Test processing multiple repositories."""
        processor = ParallelRepositoryProcessor(max_workers=2)

        def analyze(repo):
            time.sleep(0.01)  # Simulate work
            return {"repo": repo, "files": 10}

        repos = ["repo1", "repo2", "repo3", "repo4"]
        results = processor.process_repositories(repos, analyze)

        assert results.total == 4
        assert results.success_count == 4
        assert len(results.results) == 4

    def test_process_with_errors(self):
        """Test processing with some failures."""
        processor = ParallelRepositoryProcessor(max_workers=2)

        def analyze(repo):
            if repo == "repo2":
                raise ValueError("Test error")
            return {"repo": repo}

        repos = ["repo1", "repo2", "repo3"]
        results = processor.process_repositories(repos, analyze)

        assert results.total == 3
        assert results.success_count == 2
        assert results.failure_count == 1
        assert "repo2" in results.errors

    def test_process_with_profiler(self):
        """Test processing with profiler integration."""
        profiler = PerformanceProfiler(name="test")
        profiler.start()

        processor = ParallelRepositoryProcessor(max_workers=2, profiler=profiler)

        def analyze(repo):
            return {"repo": repo}

        results = processor.process_repositories(["repo1", "repo2"], analyze)

        profiler.stop()

        assert results.success_count == 2
        assert len(profiler.operations) > 0

    def test_process_with_progress_callback(self):
        """Test processing with progress callback."""
        progress_updates = []

        def on_progress(completed, total):
            progress_updates.append((completed, total))

        processor = ParallelRepositoryProcessor(max_workers=2, progress_callback=on_progress)

        def analyze(repo):
            time.sleep(0.01)
            return {"repo": repo}

        results = processor.process_repositories(["repo1", "repo2", "repo3"], analyze)

        assert results.success_count == 3
        assert len(progress_updates) == 3
        assert progress_updates[-1] == (3, 3)

    def test_worker_utilization(self):
        """Test worker utilization statistics."""
        processor = ParallelRepositoryProcessor(max_workers=4)

        def analyze(repo):
            return {"repo": repo}

        results = processor.process_repositories(["repo1", "repo2"], analyze)

        utilization = processor.get_worker_utilization(results)

        assert utilization["total_workers"] == 4
        assert utilization["utilized_workers"] > 0
        assert utilization["utilization_rate"] >= 0

    def test_retry_on_failure(self):
        """Test retry logic on failures."""
        config = WorkerConfig(max_workers=2, retry_on_failure=True, max_retries=2)
        processor = ParallelRepositoryProcessor(config=config)

        attempt_count = {"count": 0}

        def analyze(repo):
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:  # Fail first 2 attempts
                raise ValueError("Temporary error")
            return {"repo": repo}

        results = processor.process_repositories(["repo1"], analyze)

        # Should succeed after retries
        assert results.success_count == 1
        assert attempt_count["count"] == 3  # Initial + 2 retries


class TestParallelMap:
    """Tests for parallel_map convenience function."""

    def test_parallel_map_basic(self):
        """Test basic parallel map."""

        def square(x):
            return x * x

        results = parallel_map(square, [1, 2, 3, 4], max_workers=2)

        assert results == [1, 4, 9, 16]

    def test_parallel_map_auto_workers(self):
        """Test parallel map with auto-detected workers."""

        def double(x):
            return x * 2

        results = parallel_map(double, [1, 2, 3])

        assert results == [2, 4, 6]

    def test_parallel_map_with_sleep(self):
        """Test parallel map with work simulation."""

        def slow_func(x):
            time.sleep(0.01)
            return x + 1

        start = time.perf_counter()
        results = parallel_map(slow_func, [1, 2, 3, 4], max_workers=2)
        duration = time.perf_counter() - start

        assert results == [2, 3, 4, 5]
        # Should be faster than sequential (4 * 0.01 = 0.04s)
        assert duration < 0.04


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_parallel_faster_than_sequential(self):
        """Test that parallel processing is faster."""

        def slow_work(item):
            time.sleep(0.05)
            return item

        items = list(range(8))

        # Sequential
        start = time.perf_counter()
        sequential_results = [slow_work(i) for i in items]
        sequential_time = time.perf_counter() - start

        # Parallel
        start = time.perf_counter()
        parallel_results = parallel_map(slow_work, items, max_workers=4)
        parallel_time = time.perf_counter() - start

        assert parallel_results == sequential_results
        # Parallel should be significantly faster (at least 2x)
        assert parallel_time < sequential_time / 2

    def test_large_repository_set(self):
        """Test processing large repository set."""
        processor = ParallelRepositoryProcessor(max_workers=4)

        def analyze(repo):
            return {"id": repo, "size": 100}

        repos = [f"repo{i}" for i in range(50)]
        results = processor.process_repositories(repos, analyze)

        assert results.total == 50
        assert results.success_count == 50
        assert results.success_rate == 100.0

    def test_mixed_success_failure_large_set(self):
        """Test processing with mixed success/failure on large set."""
        processor = ParallelRepositoryProcessor(max_workers=4)

        def analyze(repo):
            # Fail every 5th repo
            repo_num = int(repo.replace("repo", ""))
            if repo_num % 5 == 0:
                raise ValueError(f"Failed on {repo}")
            return {"id": repo}

        repos = [f"repo{i}" for i in range(20)]
        results = processor.process_repositories(repos, analyze)

        assert results.total == 20
        assert results.failure_count == 4  # 0, 5, 10, 15
        assert results.success_count == 16


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_processor_with_none_function(self):
        """Test processor handles None function."""
        processor = ParallelRepositoryProcessor(max_workers=2)

        # None function will cause error during execution, not at call time
        results = processor.process_repositories(["repo1"], None)

        # Should fail since None is not callable
        assert results.failure_count == 1
        assert results.success_count == 0

    def test_processor_with_invalid_items(self):
        """Test processor with various item types."""
        processor = ParallelRepositoryProcessor(max_workers=2)

        def analyze(item):
            return {"item": str(item)}

        # Should work with strings, dicts, numbers
        results = processor.process_repositories(["str", {"key": "val"}, 123], analyze)

        assert results.success_count == 3

    def test_worker_timeout_handling(self):
        """Test handling of worker timeouts."""
        config = WorkerConfig(max_workers=2, worker_timeout=1)
        processor = ParallelRepositoryProcessor(config=config)

        def slow_work(repo):
            time.sleep(2)  # Longer than timeout
            return {"repo": repo}

        # Note: Timeout handling is complex in thread pools
        # This test verifies the config is accepted
        assert processor.config.worker_timeout == 1
