# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Parallel repository processing module for the Repository Reporting System.

This module provides utilities for processing multiple repositories in parallel
using a worker pool architecture. It handles result aggregation, error management,
and progress tracking across workers.

Classes:
    ParallelRepositoryProcessor: Main coordinator for parallel processing
    WorkerPool: Worker lifecycle management
    ResultAggregator: Thread-safe result collection
    WorkerConfig: Configuration for parallel processing
    ProcessingResult: Result from processing a repository

Example:
    >>> from src.performance import ParallelRepositoryProcessor
    >>>
    >>> processor = ParallelRepositoryProcessor(max_workers=4)
    >>> repos = ['repo1', 'repo2', 'repo3']
    >>> results = processor.process_repositories(repos, analyze_function)
    >>> print(f"Processed {len(results.successful)} repositories")
"""

import multiprocessing
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any, Optional, Tuple, Union
from enum import Enum
import traceback
import os


class WorkerType(Enum):
    """Type of worker pool to use."""
    THREAD = "thread"
    PROCESS = "process"


class ProcessingStatus(Enum):
    """Status of a processing task."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class WorkerConfig:
    """Configuration for parallel processing."""
    max_workers: int = 4
    worker_type: WorkerType = WorkerType.THREAD
    worker_timeout: int = 300  # seconds
    batch_size: int = 10
    retry_on_failure: bool = False
    max_retries: int = 2
    stop_on_error: bool = False

    def __post_init__(self):
        """Validate configuration."""
        if self.max_workers < 1:
            raise ValueError(f"max_workers must be >= 1, got {self.max_workers}")
        if self.max_workers > 64:
            raise ValueError(f"max_workers must be <= 64, got {self.max_workers}")
        if self.worker_timeout < 1:
            raise ValueError(f"worker_timeout must be >= 1, got {self.worker_timeout}")
        if self.batch_size < 1:
            raise ValueError(f"batch_size must be >= 1, got {self.batch_size}")
        if self.max_retries < 0:
            raise ValueError(f"max_retries must be >= 0, got {self.max_retries}")

    @staticmethod
    def auto_detect_workers() -> int:
        """
        Auto-detect optimal number of workers.

        Returns:
            Recommended worker count
        """
        cpu_count = multiprocessing.cpu_count()
        # Use CPU count for I/O-bound tasks (repository analysis is I/O heavy)
        # Cap at 16 to avoid overwhelming system
        return min(cpu_count, 16)


@dataclass
class ProcessingResult:
    """Result from processing a single repository."""
    item_id: str
    status: ProcessingStatus
    result: Any = None
    error: Optional[str] = None
    error_traceback: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    worker_id: Optional[int] = None
    retry_count: int = 0

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return self.end_time - self.start_time if self.end_time > 0 else 0.0

    @property
    def is_success(self) -> bool:
        """Check if processing was successful."""
        return self.status == ProcessingStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """Check if processing failed."""
        return self.status in (ProcessingStatus.FAILED, ProcessingStatus.TIMEOUT)


@dataclass
class AggregatedResults:
    """Aggregated results from parallel processing."""
    total: int
    successful: List[ProcessingResult] = field(default_factory=list)
    failed: List[ProcessingResult] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    total_duration: float = 0.0

    @property
    def success_count(self) -> int:
        """Number of successful results."""
        return len(self.successful)

    @property
    def failure_count(self) -> int:
        """Number of failed results."""
        return len(self.failed)

    @property
    def success_rate(self) -> float:
        """Success rate as percentage."""
        return (self.success_count / self.total * 100) if self.total > 0 else 0.0

    @property
    def avg_duration(self) -> float:
        """Average processing duration."""
        if not self.successful:
            return 0.0
        return sum(r.duration for r in self.successful) / len(self.successful)


class ResultAggregator:
    """
    Thread-safe result aggregator for collecting results from workers.

    Example:
        >>> aggregator = ResultAggregator(total_items=10)
        >>> aggregator.add_result(ProcessingResult(...))
        >>> results = aggregator.get_results()
    """

    def __init__(self, total_items: int):
        """
        Initialize result aggregator.

        Args:
            total_items: Total number of items to process
        """
        self.total_items = total_items
        self.lock = threading.Lock()
        self.results: List[ProcessingResult] = []
        self.completed_count = 0
        self.start_time = time.perf_counter()

    def add_result(self, result: ProcessingResult):
        """
        Add a result (thread-safe).

        Args:
            result: Processing result to add
        """
        with self.lock:
            self.results.append(result)
            self.completed_count += 1

    def get_progress(self) -> Tuple[int, int]:
        """
        Get current progress.

        Returns:
            Tuple of (completed, total)
        """
        with self.lock:
            return (self.completed_count, self.total_items)

    def get_results(self) -> AggregatedResults:
        """
        Get aggregated results.

        Returns:
            AggregatedResults with all data
        """
        with self.lock:
            end_time = time.perf_counter()

            successful = [r for r in self.results if r.is_success]
            failed = [r for r in self.results if r.is_failure]

            results_dict = {r.item_id: r.result for r in successful if r.result is not None}
            errors_dict = {r.item_id: r.error for r in failed if r.error is not None}

            return AggregatedResults(
                total=self.total_items,
                successful=successful,
                failed=failed,
                results=results_dict,
                errors=errors_dict,
                total_duration=end_time - self.start_time
            )


class WorkerPool:
    """
    Worker pool for managing parallel execution.

    Example:
        >>> with WorkerPool(max_workers=4, worker_type=WorkerType.THREAD) as pool:
        ...     results = pool.map(func, items)
    """

    def __init__(
        self,
        max_workers: int = 4,
        worker_type: WorkerType = WorkerType.THREAD,
        worker_timeout: int = 300
    ):
        """
        Initialize worker pool.

        Args:
            max_workers: Maximum number of workers
            worker_type: Type of workers (thread or process)
            worker_timeout: Timeout per task in seconds
        """
        self.max_workers = max_workers
        self.worker_type = worker_type
        self.worker_timeout = worker_timeout
        self.executor: Optional[Union[ThreadPoolExecutor, ProcessPoolExecutor]] = None

    def __enter__(self):
        """Enter context manager."""
        if self.worker_type == WorkerType.THREAD:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self.executor:
            self.executor.shutdown(wait=True)
        return False

    def submit(self, func: Callable, *args, **kwargs) -> Future:
        """
        Submit a task to the pool.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future object
        """
        if not self.executor:
            raise RuntimeError("WorkerPool must be used as context manager")
        return self.executor.submit(func, *args, **kwargs)

    def map(self, func: Callable, items: List[Any]) -> List[Any]:
        """
        Map function over items in parallel.

        Args:
            func: Function to apply
            items: Items to process

        Returns:
            List of results
        """
        if not self.executor:
            raise RuntimeError("WorkerPool must be used as context manager")
        return list(self.executor.map(func, items, timeout=self.worker_timeout))


class ParallelRepositoryProcessor:
    """
    Main coordinator for parallel repository processing.

    This class manages the parallel execution of repository analysis,
    handles result aggregation, error management, and progress tracking.

    Example:
        >>> processor = ParallelRepositoryProcessor(max_workers=4)
        >>>
        >>> def analyze(repo_path):
        ...     return {"path": repo_path, "files": 100}
        >>>
        >>> results = processor.process_repositories(
        ...     repositories=['repo1', 'repo2', 'repo3'],
        ...     processor_func=analyze
        ... )
        >>>
        >>> print(f"Success: {results.success_count}/{results.total}")
    """

    def __init__(
        self,
        max_workers: Optional[int] = None,
        config: Optional[WorkerConfig] = None,
        profiler: Optional[Any] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """
        Initialize parallel processor.

        Args:
            max_workers: Maximum number of workers (auto-detect if None)
            config: Worker configuration (creates default if None)
            profiler: Optional performance profiler
            progress_callback: Optional callback for progress updates (completed, total)
        """
        if config:
            self.config = config
        else:
            workers = max_workers if max_workers else WorkerConfig.auto_detect_workers()
            self.config = WorkerConfig(max_workers=workers)

        self.profiler = profiler
        self.progress_callback = progress_callback
        self._worker_counter = 0
        self._lock = threading.Lock()

    def _get_worker_id(self) -> int:
        """Get next worker ID (thread-safe)."""
        with self._lock:
            self._worker_counter += 1
            return self._worker_counter

    def _process_item(
        self,
        item: Any,
        processor_func: Callable,
        worker_id: int,
        retry_count: int = 0
    ) -> ProcessingResult:
        """
        Process a single item.

        Args:
            item: Item to process
            processor_func: Function to process the item
            worker_id: ID of the worker
            retry_count: Current retry count

        Returns:
            ProcessingResult
        """
        item_id = str(item) if not isinstance(item, dict) else item.get('id', str(item))

        result = ProcessingResult(
            item_id=item_id,
            status=ProcessingStatus.RUNNING,
            start_time=time.perf_counter(),
            worker_id=worker_id,
            retry_count=retry_count
        )

        try:
            # Track with profiler if available
            if self.profiler:
                with self.profiler.track_operation(
                    f"process_item_{item_id}",
                    category="analysis",
                    metadata={"worker_id": worker_id, "retry": retry_count}
                ):
                    output = processor_func(item)
            else:
                output = processor_func(item)

            result.result = output
            result.status = ProcessingStatus.SUCCESS

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.error = str(e)
            result.error_traceback = traceback.format_exc()

            # Retry logic
            if self.config.retry_on_failure and retry_count < self.config.max_retries:
                # Recursive retry
                return self._process_item(item, processor_func, worker_id, retry_count + 1)

        finally:
            result.end_time = time.perf_counter()

        return result

    def _batch_items(self, items: List[Any]) -> List[List[Any]]:
        """
        Batch items for processing.

        Args:
            items: Items to batch

        Returns:
            List of batches
        """
        batch_size = self.config.batch_size
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

    def process_repositories(
        self,
        repositories: List[Any],
        processor_func: Callable[[Any], Any],
        batch_mode: bool = False
    ) -> AggregatedResults:
        """
        Process multiple repositories in parallel.

        Args:
            repositories: List of repositories to process
            processor_func: Function to process each repository
            batch_mode: If True, process in batches

        Returns:
            AggregatedResults with all processing results

        Example:
            >>> def analyze_repo(repo_path):
            ...     return {"path": repo_path, "size": 1000}
            >>>
            >>> processor = ParallelRepositoryProcessor(max_workers=4)
            >>> results = processor.process_repositories(
            ...     repositories=['repo1', 'repo2', 'repo3'],
            ...     processor_func=analyze_repo
            ... )
        """
        if not repositories:
            return AggregatedResults(total=0)

        # Initialize aggregator
        aggregator = ResultAggregator(total_items=len(repositories))

        # Track overall operation
        if self.profiler:
            self.profiler.memory_snapshot("before_parallel_processing")

        # Create worker pool
        with WorkerPool(
            max_workers=self.config.max_workers,
            worker_type=self.config.worker_type,
            worker_timeout=self.config.worker_timeout
        ) as pool:

            # Submit all tasks
            futures: Dict[Future, Tuple[Any, int]] = {}

            for item in repositories:
                worker_id = self._get_worker_id()
                future = pool.submit(
                    self._process_item,
                    item,
                    processor_func,
                    worker_id
                )
                futures[future] = (item, worker_id)

            # Collect results as they complete
            for future in as_completed(futures, timeout=self.config.worker_timeout):
                item, worker_id = futures[future]

                try:
                    result = future.result(timeout=1.0)
                    aggregator.add_result(result)

                    # Progress callback
                    if self.progress_callback:
                        completed, total = aggregator.get_progress()
                        self.progress_callback(completed, total)

                    # Stop on error if configured
                    if self.config.stop_on_error and result.is_failure:
                        # Cancel remaining futures
                        for f in futures:
                            if not f.done():
                                f.cancel()
                        break

                except TimeoutError:
                    # Task timed out
                    item_id = str(item)
                    timeout_result = ProcessingResult(
                        item_id=item_id,
                        status=ProcessingStatus.TIMEOUT,
                        error=f"Task timed out after {self.config.worker_timeout}s",
                        worker_id=worker_id
                    )
                    aggregator.add_result(timeout_result)

                except Exception as e:
                    # Unexpected error
                    item_id = str(item)
                    error_result = ProcessingResult(
                        item_id=item_id,
                        status=ProcessingStatus.FAILED,
                        error=f"Unexpected error: {str(e)}",
                        error_traceback=traceback.format_exc(),
                        worker_id=worker_id
                    )
                    aggregator.add_result(error_result)

        # Track memory after processing
        if self.profiler:
            self.profiler.memory_snapshot("after_parallel_processing")

        return aggregator.get_results()

    def get_worker_utilization(self, results: AggregatedResults) -> Dict[str, Any]:
        """
        Calculate worker utilization statistics.

        Args:
            results: Aggregated results

        Returns:
            Dictionary with utilization stats
        """
        if not results.successful:
            return {
                "total_workers": self.config.max_workers,
                "utilized_workers": 0,
                "utilization_rate": 0.0,
                "avg_items_per_worker": 0.0
            }

        # Count unique workers
        worker_ids = set()
        worker_counts: Dict[int, int] = {}

        for result in results.successful + results.failed:
            if result.worker_id:
                worker_ids.add(result.worker_id)
                worker_counts[result.worker_id] = worker_counts.get(result.worker_id, 0) + 1

        utilized_workers = len(worker_ids)

        return {
            "total_workers": self.config.max_workers,
            "utilized_workers": utilized_workers,
            "utilization_rate": (utilized_workers / self.config.max_workers * 100),
            "avg_items_per_worker": results.total / utilized_workers if utilized_workers > 0 else 0,
            "items_per_worker": worker_counts
        }


# Convenience function for simple parallel mapping
def parallel_map(
    func: Callable,
    items: List[Any],
    max_workers: Optional[int] = None,
    timeout: int = 300
) -> List[Any]:
    """
    Simple parallel map function.

    Args:
        func: Function to apply
        items: Items to process
        max_workers: Number of workers (auto-detect if None)
        timeout: Timeout per item in seconds

    Returns:
        List of results in same order as items

    Example:
        >>> def square(x):
        ...     return x * x
        >>> results = parallel_map(square, [1, 2, 3, 4], max_workers=2)
        >>> print(results)  # [1, 4, 9, 16]
    """
    workers = max_workers if max_workers else WorkerConfig.auto_detect_workers()

    with WorkerPool(max_workers=workers, worker_timeout=timeout) as pool:
        return list(pool.map(func, items))
