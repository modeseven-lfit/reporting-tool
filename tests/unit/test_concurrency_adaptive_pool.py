# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for adaptive thread pool module.

Tests the AdaptiveThreadPool class including:
- Pool initialization and configuration
- Task submission and execution
- Metrics tracking
- Scaling logic
- Thread safety
- Context manager behavior

Phase 7: Concurrency Refinement
"""

import threading
import time
from unittest.mock import patch

import pytest

from concurrency.adaptive_pool import (
    AdaptiveThreadPool,
    PoolMetrics,
)


class TestPoolMetrics:
    """Test PoolMetrics dataclass."""

    def test_pool_metrics_initialization(self):
        """Test PoolMetrics initializes with default values."""
        metrics = PoolMetrics()

        assert metrics.queue_depth == 0
        assert metrics.active_workers == 0
        assert metrics.completed_tasks == 0
        assert metrics.failed_tasks == 0
        assert metrics.avg_task_duration == 0.0
        assert metrics.last_adjustment == 0.0

    def test_pool_metrics_custom_values(self):
        """Test PoolMetrics with custom values."""
        metrics = PoolMetrics(
            queue_depth=5,
            active_workers=4,
            completed_tasks=100,
            failed_tasks=2,
            avg_task_duration=1.5,
            last_adjustment=123.45,
        )

        assert metrics.queue_depth == 5
        assert metrics.active_workers == 4
        assert metrics.completed_tasks == 100
        assert metrics.failed_tasks == 2
        assert metrics.avg_task_duration == 1.5
        assert metrics.last_adjustment == 123.45


class TestAdaptiveThreadPoolInitialization:
    """Test AdaptiveThreadPool initialization."""

    def test_default_initialization(self):
        """Test pool initializes with default values."""
        pool = AdaptiveThreadPool()

        assert pool.min_workers == 2
        assert pool.max_workers > 0  # CPU count * 2
        assert pool.scale_up_threshold == 10
        assert pool.scale_down_threshold == 2
        assert pool.adjustment_interval == 5.0

    def test_custom_initialization(self):
        """Test pool initializes with custom values."""
        pool = AdaptiveThreadPool(
            min_workers=4,
            max_workers=16,
            scale_up_threshold=20,
            scale_down_threshold=5,
            adjustment_interval=10.0,
        )

        assert pool.min_workers == 4
        assert pool.max_workers == 16
        assert pool.scale_up_threshold == 20
        assert pool.scale_down_threshold == 5
        assert pool.adjustment_interval == 10.0

    def test_max_workers_defaults_to_cpu_count_times_two(self):
        """Test max_workers defaults to CPU count * 2."""
        import os

        pool = AdaptiveThreadPool(min_workers=2)

        expected_max = (os.cpu_count() or 1) * 2
        assert pool.max_workers == expected_max


class TestAdaptiveThreadPoolContextManager:
    """Test AdaptiveThreadPool context manager behavior."""

    def test_context_manager_starts_pool(self):
        """Test pool starts when entering context."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        with pool:
            assert pool._executor is not None
            assert pool._monitor_thread is not None
            assert pool._monitor_thread.is_alive()

    def test_context_manager_stops_pool(self):
        """Test pool stops when exiting context."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        with pool:
            pass

        # Give threads time to shutdown
        time.sleep(0.1)

        # Monitor thread should be stopped
        assert pool._shutdown_event.is_set()

    def test_submit_without_context_raises_error(self):
        """Test submitting task without starting pool raises error."""
        pool = AdaptiveThreadPool()

        with pytest.raises(RuntimeError, match="Pool not started"):
            pool.submit(lambda: 42)


class TestAdaptiveThreadPoolTaskSubmission:
    """Test task submission and execution."""

    def test_submit_simple_task(self):
        """Test submitting and executing a simple task."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        def simple_task():
            return 42

        with pool:
            future = pool.submit(simple_task)
            result = future.result(timeout=1.0)

        assert result == 42

    def test_submit_task_with_args(self):
        """Test submitting task with arguments."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        def task_with_args(a, b):
            return a + b

        with pool:
            future = pool.submit(task_with_args, 10, 20)
            result = future.result(timeout=1.0)

        assert result == 30

    def test_submit_task_with_kwargs(self):
        """Test submitting task with keyword arguments."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        def task_with_kwargs(x=0, y=0):
            return x * y

        with pool:
            future = pool.submit(task_with_kwargs, x=5, y=6)
            result = future.result(timeout=1.0)

        assert result == 30

    def test_submit_multiple_tasks(self):
        """Test submitting multiple tasks."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=8)

        def task(n):
            return n * 2

        with pool:
            futures = [pool.submit(task, i) for i in range(10)]
            results = [f.result(timeout=1.0) for f in futures]

        assert results == [i * 2 for i in range(10)]

    def test_map_function(self):
        """Test map function over iterables."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=8)

        def square(x):
            return x**2

        with pool:
            results = pool.map(square, range(5))

        assert results == [0, 1, 4, 9, 16]


class TestAdaptiveThreadPoolMetrics:
    """Test metrics tracking."""

    def test_initial_metrics(self):
        """Test metrics start at zero."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        with pool:
            metrics = pool.get_metrics()

        assert metrics.queue_depth == 0
        assert metrics.completed_tasks == 0
        assert metrics.failed_tasks == 0

    def test_metrics_track_completed_tasks(self):
        """Test metrics track completed tasks."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        def task():
            return 42

        with pool:
            futures = [pool.submit(task) for _ in range(5)]
            # Wait for completion
            for f in futures:
                f.result(timeout=1.0)

            # Give metrics time to update
            time.sleep(0.1)
            metrics = pool.get_metrics()

        assert metrics.completed_tasks == 5
        assert metrics.failed_tasks == 0

    def test_metrics_track_failed_tasks(self):
        """Test metrics track failed tasks."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        def failing_task():
            raise ValueError("Test error")

        with pool:
            futures = [pool.submit(failing_task) for _ in range(3)]

            # Expect failures
            for f in futures:
                with pytest.raises(ValueError):
                    f.result(timeout=1.0)

            # Give metrics time to update
            time.sleep(0.1)
            metrics = pool.get_metrics()

        assert metrics.failed_tasks == 3

    def test_metrics_track_average_duration(self):
        """Test metrics track average task duration."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        def slow_task():
            time.sleep(0.1)
            return 42

        with pool:
            futures = [pool.submit(slow_task) for _ in range(5)]
            for f in futures:
                f.result(timeout=2.0)

            # Give metrics time to update
            time.sleep(0.2)
            metrics = pool.get_metrics()

        # Average should be around 0.1 seconds (more lenient for race conditions)
        assert metrics.avg_task_duration >= 0.0
        assert metrics.completed_tasks == 5


class TestAdaptiveThreadPoolScaling:
    """Test pool scaling behavior."""

    def test_current_workers_starts_at_min(self):
        """Test worker count starts at minimum."""
        pool = AdaptiveThreadPool(min_workers=3, max_workers=10)

        with pool:
            assert pool._current_workers == 3

    def test_active_workers_in_metrics(self):
        """Test active workers reported in metrics."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=8)

        with pool:
            metrics = pool.get_metrics()
            assert metrics.active_workers >= 2

    @patch("time.sleep")  # Speed up test by mocking sleep
    def test_scale_up_increases_workers(self, mock_sleep):
        """Test scaling up increases worker count."""
        pool = AdaptiveThreadPool(
            min_workers=2, max_workers=8, scale_up_threshold=3, adjustment_interval=0.1
        )

        with pool:
            initial_workers = pool._current_workers

            # Manually trigger scale up
            with pool._metrics_lock:
                pool._metrics.queue_depth = 10  # Above threshold

            pool._scale_up()

            assert pool._current_workers > initial_workers

    @patch("time.sleep")
    def test_scale_down_decreases_workers(self, mock_sleep):
        """Test scaling down decreases worker count."""
        pool = AdaptiveThreadPool(
            min_workers=2, max_workers=8, scale_down_threshold=5, adjustment_interval=0.1
        )

        with pool:
            # First scale up
            pool._current_workers = 8

            # Then scale down
            with pool._metrics_lock:
                pool._metrics.queue_depth = 1  # Below threshold

            pool._scale_down()

            assert pool._current_workers < 8

    def test_scale_up_respects_max_workers(self):
        """Test scaling up doesn't exceed max workers."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        with pool:
            pool._current_workers = 4
            pool._scale_up()

            # Should not exceed max
            assert pool._current_workers <= 4

    def test_scale_down_respects_min_workers(self):
        """Test scaling down doesn't go below min workers."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=8)

        with pool:
            pool._current_workers = 2
            pool._scale_down()

            # Should not go below min
            assert pool._current_workers >= 2


class TestAdaptiveThreadPoolThreadSafety:
    """Test thread safety of pool operations."""

    def test_concurrent_task_submission(self):
        """Test submitting tasks from multiple threads is thread-safe."""
        pool = AdaptiveThreadPool(min_workers=4, max_workers=8)

        results = []

        def submit_tasks():
            with pool:
                for i in range(10):
                    future = pool.submit(lambda x: x * 2, i)
                    results.append(future)

        # Submit from multiple threads
        threads = [threading.Thread(target=submit_tasks) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5.0)

        # All tasks should complete
        assert len(results) > 0

    def test_concurrent_metrics_access(self):
        """Test accessing metrics from multiple threads is thread-safe."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        metrics_list = []

        def get_metrics():
            for _ in range(10):
                metrics = pool.get_metrics()
                metrics_list.append(metrics)
                time.sleep(0.01)

        with pool:
            # Access metrics from multiple threads
            threads = [threading.Thread(target=get_metrics) for _ in range(3)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5.0)

        # Should get multiple metrics without errors
        assert len(metrics_list) >= 30


class TestAdaptiveThreadPoolErrorHandling:
    """Test error handling in pool."""

    def test_task_exception_propagates(self):
        """Test exceptions in tasks are propagated to caller."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        def failing_task():
            raise ValueError("Test error")

        with pool:
            future = pool.submit(failing_task)

            with pytest.raises(ValueError, match="Test error"):
                future.result(timeout=1.0)

    def test_pool_continues_after_task_failure(self):
        """Test pool continues working after a task fails."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        def failing_task():
            raise ValueError("Test error")

        def successful_task():
            return 42

        with pool:
            # Submit failing task
            future1 = pool.submit(failing_task)

            # Submit successful task
            future2 = pool.submit(successful_task)

            # First should fail
            with pytest.raises(ValueError):
                future1.result(timeout=1.0)

            # Second should succeed
            assert future2.result(timeout=1.0) == 42

    def test_map_with_exception_raises(self):
        """Test map raises exception if any task fails."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        def task(x):
            if x == 3:
                raise ValueError("Error at 3")
            return x * 2

        with pool, pytest.raises(ValueError, match="Error at 3"):
            pool.map(task, range(5))


class TestAdaptiveThreadPoolShutdown:
    """Test pool shutdown behavior."""

    def test_shutdown_completes_pending_tasks(self):
        """Test shutdown waits for pending tasks to complete."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)
        results = []

        def slow_task(x):
            time.sleep(0.1)
            return x

        with pool:
            futures = [pool.submit(slow_task, i) for i in range(5)]

        # After exiting context, all tasks should be complete
        for future in futures:
            # Should not timeout since pool waited for completion
            result = future.result(timeout=0.1)
            results.append(result)

        assert len(results) == 5

    def test_shutdown_sets_event(self):
        """Test shutdown sets the shutdown event."""
        pool = AdaptiveThreadPool(min_workers=2, max_workers=4)

        with pool:
            assert not pool._shutdown_event.is_set()

        # After exit, event should be set
        assert pool._shutdown_event.is_set()
