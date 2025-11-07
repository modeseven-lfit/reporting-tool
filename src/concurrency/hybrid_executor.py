# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Hybrid Executor for Optimal Workload Distribution.

Automatically routes tasks to ThreadPoolExecutor (for I/O-bound) or
ProcessPoolExecutor (for CPU-bound) based on operation type classification.

Phase 7: Concurrency Refinement
"""

import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Any, Optional, Dict, Union
import threading
import logging


class OperationType(Enum):
    """Classification of operation types for optimal executor selection."""

    CPU_BOUND = "cpu"      # Computation-heavy: use ProcessPoolExecutor
    IO_BOUND = "io"        # I/O-heavy: use ThreadPoolExecutor
    MIXED = "mixed"        # Mixed workload: use adaptive strategy
    AUTO = "auto"          # Automatic detection


@dataclass
class ExecutorStats:
    """Statistics for hybrid executor monitoring."""

    cpu_tasks_submitted: int = 0
    io_tasks_submitted: int = 0
    cpu_tasks_completed: int = 0
    io_tasks_completed: int = 0
    cpu_tasks_failed: int = 0
    io_tasks_failed: int = 0


class HybridExecutor:
    """
    Executor that routes tasks to optimal executor based on operation type.

    Uses ProcessPoolExecutor for CPU-bound tasks (computation-heavy) and
    ThreadPoolExecutor for I/O-bound tasks (network, disk operations).

    Features:
        - Automatic workload routing
        - Separate pools for CPU and I/O
        - Statistics tracking
        - Context manager support

    Example:
        >>> executor = HybridExecutor()
        >>> with executor:
        >>>     # I/O-bound tasks (API calls, file operations)
        >>>     io_future = executor.submit(OperationType.IO_BOUND, fetch_data)
        >>>
        >>>     # CPU-bound tasks (parsing, computation)
        >>>     cpu_future = executor.submit(OperationType.CPU_BOUND, parse_logs)
        >>>
        >>>     results = [io_future.result(), cpu_future.result()]
    """

    def __init__(
        self,
        thread_workers: Optional[int] = None,
        process_workers: Optional[int] = None,
        enable_processes: bool = False
    ):
        """
        Initialize hybrid executor.

        Args:
            thread_workers: Number of threads for I/O-bound tasks
                          (default: CPU count * 2)
            process_workers: Number of processes for CPU-bound tasks
                           (default: CPU count)
            enable_processes: Whether to use ProcessPoolExecutor
                            (set False for debugging/testing, default: False)
        """
        cpu_count = os.cpu_count() or 1

        self.thread_workers = thread_workers or (cpu_count * 2)
        self.process_workers = process_workers or cpu_count
        self.enable_processes = enable_processes

        # Executors (created in __enter__)
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._process_pool: Optional[ProcessPoolExecutor] = None

        # Statistics
        self._stats = ExecutorStats()
        self._stats_lock = threading.Lock()

        # Operation classification cache
        self._operation_types: Dict[str, OperationType] = {}

        # Logger
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        """Start executor pools."""
        self._thread_pool = ThreadPoolExecutor(max_workers=self.thread_workers)

        if self.enable_processes:
            self._process_pool = ProcessPoolExecutor(max_workers=self.process_workers)
            self.logger.info(
                f"Started hybrid executor: "
                f"threads={self.thread_workers}, processes={self.process_workers}"
            )
        else:
            self.logger.info(
                f"Started hybrid executor: "
                f"threads={self.thread_workers}, processes=disabled"
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Shutdown executor pools."""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
        if self._process_pool:
            self._process_pool.shutdown(wait=True)

        # Log final stats
        stats = self.get_stats()
        self.logger.info(
            f"Shutting down hybrid executor: "
            f"io_tasks={stats.io_tasks_completed}/{stats.io_tasks_submitted}, "
            f"cpu_tasks={stats.cpu_tasks_completed}/{stats.cpu_tasks_submitted}"
        )
        return False

    def submit(
        self,
        operation_type: OperationType,
        fn: Callable,
        *args,
        **kwargs
    ) -> Future:
        """
        Submit a task to the appropriate executor.

        Args:
            operation_type: Type of operation (CPU_BOUND, IO_BOUND, AUTO)
            fn: Callable to execute
            *args: Positional arguments for fn
            **kwargs: Keyword arguments for fn

        Returns:
            Future representing the task

        Raises:
            RuntimeError: If executor not started (use with statement)
        """
        if not self._thread_pool:
            raise RuntimeError("Executor not started. Use 'with' statement.")

        # Auto-detect operation type if requested
        actual_op_type = operation_type
        if operation_type == OperationType.AUTO:
            actual_op_type = self._classify_operation(fn)

        # Determine which executor to use and track submission
        executor: Union[ThreadPoolExecutor, ProcessPoolExecutor]
        if actual_op_type == OperationType.CPU_BOUND and self._process_pool:
            executor = self._process_pool
            with self._stats_lock:
                self._stats.cpu_tasks_submitted += 1
        else:
            # Use thread pool for I/O-bound or if processes disabled
            # If it's CPU_BOUND but processes disabled, still count as CPU
            executor = self._thread_pool
            with self._stats_lock:
                if actual_op_type == OperationType.CPU_BOUND:
                    self._stats.cpu_tasks_submitted += 1
                else:
                    self._stats.io_tasks_submitted += 1

        # Wrap task to track completion
        wrapped_fn = self._wrap_task(fn, actual_op_type)
        return executor.submit(wrapped_fn, *args, **kwargs)

    def _wrap_task(self, fn: Callable, op_type: OperationType) -> Callable:
        """Wrap task to track statistics."""
        def wrapper(*args, **kwargs):
            try:
                result = fn(*args, **kwargs)
                with self._stats_lock:
                    if op_type == OperationType.CPU_BOUND:
                        self._stats.cpu_tasks_completed += 1
                    else:
                        self._stats.io_tasks_completed += 1
                return result
            except Exception as e:
                with self._stats_lock:
                    if op_type == OperationType.CPU_BOUND:
                        self._stats.cpu_tasks_failed += 1
                    else:
                        self._stats.io_tasks_failed += 1
                raise

        return wrapper

    def _classify_operation(self, fn: Callable) -> OperationType:
        """
        Classify operation type based on function characteristics.

        This is a heuristic-based classification. For better accuracy,
        explicit classification is recommended.

        Args:
            fn: Function to classify

        Returns:
            Classified operation type
        """
        fn_name = fn.__name__.lower()

        # Check cache
        if fn_name in self._operation_types:
            return self._operation_types[fn_name]

        # Heuristic classification based on function name
        io_keywords = ['fetch', 'request', 'download', 'upload', 'read', 'write',
                       'api', 'http', 'file', 'git', 'clone', 'pull', 'push']
        cpu_keywords = ['parse', 'compute', 'calculate', 'process', 'analyze',
                       'aggregate', 'transform', 'render', 'compile', 'build']

        # Count keyword matches
        io_matches = sum(1 for kw in io_keywords if kw in fn_name)
        cpu_matches = sum(1 for kw in cpu_keywords if kw in fn_name)

        if cpu_matches > io_matches:
            op_type = OperationType.CPU_BOUND
        else:
            # Default to I/O-bound (safer choice for repository analysis)
            op_type = OperationType.IO_BOUND

        # Cache classification
        self._operation_types[fn_name] = op_type
        return op_type

    def submit_io_bound(self, fn: Callable, *args, **kwargs) -> Future:
        """
        Convenience method for I/O-bound tasks.

        Args:
            fn: Callable to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future representing the task
        """
        return self.submit(OperationType.IO_BOUND, fn, *args, **kwargs)

    def submit_cpu_bound(self, fn: Callable, *args, **kwargs) -> Future:
        """
        Convenience method for CPU-bound tasks.

        Args:
            fn: Callable to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Future representing the task
        """
        return self.submit(OperationType.CPU_BOUND, fn, *args, **kwargs)

    def get_stats(self) -> ExecutorStats:
        """
        Get current executor statistics.

        Returns:
            ExecutorStats object with current metrics
        """
        with self._stats_lock:
            return ExecutorStats(
                cpu_tasks_submitted=self._stats.cpu_tasks_submitted,
                io_tasks_submitted=self._stats.io_tasks_submitted,
                cpu_tasks_completed=self._stats.cpu_tasks_completed,
                io_tasks_completed=self._stats.io_tasks_completed,
                cpu_tasks_failed=self._stats.cpu_tasks_failed,
                io_tasks_failed=self._stats.io_tasks_failed
            )
