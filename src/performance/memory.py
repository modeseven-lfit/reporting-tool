# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Memory optimization module for repository analysis.

This module provides utilities for reducing memory usage, lazy loading,
streaming large files, and monitoring memory consumption.

Classes:
    MemoryOptimizer: Main memory optimization coordinator
    LazyLoader: Lazy loading for deferred data access
    StreamProcessor: Stream processing for large files
    MemoryMonitor: Memory usage tracking and alerting
    MemoryStats: Memory usage statistics
    LazyProxy: Proxy for lazy-loaded objects

Example:
    >>> from src.performance.memory import MemoryOptimizer
    >>> optimizer = MemoryOptimizer(max_memory_mb=500)
    >>> optimizer.optimize_environment()
    >>> with optimizer.track_memory("analyze_repo"):
    ...     # Analysis code
    ...     pass
    >>> stats = optimizer.get_stats()
    >>> print(f"Peak memory: {stats.peak_mb:.1f} MB")
"""

import gc
import logging
import os
import sys
import threading
import time
import weakref
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterator, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class MemoryUnit(Enum):
    """Memory size units."""
    BYTES = 1
    KB = 1024
    MB = 1024 * 1024
    GB = 1024 * 1024 * 1024


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    current_mb: float = 0.0
    peak_mb: float = 0.0
    allocated_mb: float = 0.0
    gc_collections: int = 0
    gc_collected: int = 0
    tracked_objects: int = 0
    lazy_loads: int = 0
    stream_reads: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "current_mb": self.current_mb,
            "peak_mb": self.peak_mb,
            "allocated_mb": self.allocated_mb,
            "gc_collections": self.gc_collections,
            "gc_collected": self.gc_collected,
            "tracked_objects": self.tracked_objects,
            "lazy_loads": self.lazy_loads,
            "stream_reads": self.stream_reads,
        }

    def format(self) -> str:
        """Format statistics as string."""
        return f"""Memory Statistics:
  Current: {self.current_mb:.1f} MB
  Peak: {self.peak_mb:.1f} MB
  Allocated: {self.allocated_mb:.1f} MB
  GC Collections: {self.gc_collections:,}
  GC Objects Collected: {self.gc_collected:,}
  Tracked Objects: {self.tracked_objects:,}
  Lazy Loads: {self.lazy_loads:,}
  Stream Reads: {self.stream_reads:,}"""


@dataclass
class MemorySnapshot:
    """Memory snapshot at a point in time."""
    timestamp: float
    memory_mb: float
    operation: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class LazyProxy:
    """Proxy object for lazy-loaded data."""

    def __init__(self, loader: Callable[[], Any], name: str = ""):
        """
        Initialize lazy proxy.

        Args:
            loader: Function to load the actual object
            name: Name for debugging
        """
        self._loader = loader
        self._name = name
        self._loaded = False
        self._value = None
        self._lock = threading.Lock()

    def _load(self) -> Any:
        """Load the actual value."""
        with self._lock:
            if not self._loaded:
                logger.debug(f"Lazy loading: {self._name}")
                self._value = self._loader()
                self._loaded = True
            return self._value

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to loaded object."""
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return getattr(self._load(), name)

    def __getitem__(self, key: Any) -> Any:
        """Proxy item access to loaded object."""
        return self._load()[key]

    def __len__(self) -> int:
        """Proxy length to loaded object."""
        return len(self._load())

    def __iter__(self) -> Iterator:
        """Proxy iteration to loaded object."""
        return iter(self._load())

    def __repr__(self) -> str:
        """String representation."""
        if self._loaded:
            return f"LazyProxy({self._name}, loaded)"
        return f"LazyProxy({self._name}, not loaded)"


class LazyLoader:
    """Lazy loading manager for deferred data access."""

    def __init__(self):
        """Initialize lazy loader."""
        self._proxies: Dict[str, LazyProxy] = {}
        self._load_count = 0
        self._lock = threading.Lock()

    def create_lazy(
        self,
        loader: Callable[[], Any],
        name: str = "",
    ) -> LazyProxy:
        """
        Create a lazy-loaded proxy.

        Args:
            loader: Function to load the data
            name: Name for debugging

        Returns:
            Lazy proxy object
        """
        with self._lock:
            if not name:
                name = f"lazy_{len(self._proxies)}"

            proxy = LazyProxy(loader, name)
            self._proxies[name] = proxy

            logger.debug(f"Created lazy proxy: {name}")
            return proxy

    def load_all(self) -> int:
        """
        Force load all lazy proxies.

        Returns:
            Number of proxies loaded
        """
        loaded = 0
        for proxy in self._proxies.values():
            if not proxy._loaded:
                proxy._load()
                loaded += 1

        return loaded

    def clear(self) -> None:
        """Clear all lazy proxies."""
        with self._lock:
            self._proxies.clear()
            self._load_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get lazy loading statistics."""
        loaded = sum(1 for p in self._proxies.values() if p._loaded)
        return {
            "total_proxies": len(self._proxies),
            "loaded_proxies": loaded,
            "unloaded_proxies": len(self._proxies) - loaded,
            "load_ratio": loaded / len(self._proxies) if self._proxies else 0,
        }


class StreamProcessor:
    """Stream processor for handling large files."""

    def __init__(
        self,
        chunk_size: int = 8192,
        buffer_size: int = 65536,
    ):
        """
        Initialize stream processor.

        Args:
            chunk_size: Size of each read chunk in bytes
            buffer_size: Buffer size for buffered reading
        """
        self.chunk_size = chunk_size
        self.buffer_size = buffer_size
        self._read_count = 0
        self._bytes_read = 0

    def read_file_chunks(
        self,
        file_path: Union[str, Path],
        encoding: str = 'utf-8',
    ) -> Generator[str, None, None]:
        """
        Read file in chunks.

        Args:
            file_path: Path to file
            encoding: Text encoding

        Yields:
            File chunks
        """
        file_path = Path(file_path)

        with open(file_path, 'r', encoding=encoding, buffering=self.buffer_size) as f:
            while True:
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break

                self._read_count += 1
                self._bytes_read += len(chunk.encode(encoding))
                yield chunk

    def read_lines(
        self,
        file_path: Union[str, Path],
        encoding: str = 'utf-8',
    ) -> Generator[str, None, None]:
        """
        Read file line by line.

        Args:
            file_path: Path to file
            encoding: Text encoding

        Yields:
            File lines
        """
        file_path = Path(file_path)

        with open(file_path, 'r', encoding=encoding, buffering=self.buffer_size) as f:
            for line in f:
                self._read_count += 1
                self._bytes_read += len(line.encode(encoding))
                yield line

    def process_large_file(
        self,
        file_path: Union[str, Path],
        processor: Callable[[str], Any],
        encoding: str = 'utf-8',
        line_mode: bool = True,
    ) -> List[Any]:
        """
        Process large file without loading entirely into memory.

        Args:
            file_path: Path to file
            processor: Function to process each chunk/line
            encoding: Text encoding
            line_mode: Process line-by-line vs chunk-by-chunk

        Returns:
            List of processed results
        """
        results = []

        if line_mode:
            for line in self.read_lines(file_path, encoding):
                result = processor(line)
                if result is not None:
                    results.append(result)
        else:
            for chunk in self.read_file_chunks(file_path, encoding):
                result = processor(chunk)
                if result is not None:
                    results.append(result)

        return results

    def should_stream(self, file_path: Union[str, Path], threshold_mb: float = 10) -> bool:
        """
        Check if file should be streamed.

        Args:
            file_path: Path to file
            threshold_mb: Size threshold in MB

        Returns:
            True if file should be streamed
        """
        file_path = Path(file_path)
        if not file_path.exists():
            return False

        size_mb = file_path.stat().st_size / (1024 * 1024)
        return size_mb >= threshold_mb

    def get_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        return {
            "read_count": self._read_count,
            "bytes_read": self._bytes_read,
            "mb_read": self._bytes_read / (1024 * 1024),
        }


class MemoryMonitor:
    """Memory usage monitoring and tracking."""

    def __init__(
        self,
        alert_threshold_mb: float = 1000,
        sample_interval: float = 1.0,
    ):
        """
        Initialize memory monitor.

        Args:
            alert_threshold_mb: Alert when memory exceeds this
            sample_interval: Sampling interval in seconds
        """
        self.alert_threshold_mb = alert_threshold_mb
        self.sample_interval = sample_interval

        self._snapshots: List[MemorySnapshot] = []
        self._peak_mb = 0.0
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def get_current_memory(self) -> float:
        """
        Get current process memory usage in MB.

        Returns:
            Memory usage in MB
        """
        try:
            import psutil
            process = psutil.Process()
            return float(process.memory_info().rss / (1024 * 1024))
        except ImportError:
            # Fallback to gc stats if psutil not available
            import gc
            gc.collect()

            # Rough estimate from gc stats
            stats = gc.get_stats()
            if stats:
                # Very rough estimate
                collected = sum(s.get('collected', 0) for s in stats)
                return float(collected / 1000)  # Very approximate
            return 0.0

    def snapshot(self, operation: str = "", metadata: Optional[Dict] = None) -> MemorySnapshot:
        """
        Take a memory snapshot.

        Args:
            operation: Current operation name
            metadata: Additional metadata

        Returns:
            Memory snapshot
        """
        current_mb = self.get_current_memory()

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            memory_mb=current_mb,
            operation=operation,
            metadata=metadata or {},
        )

        with self._lock:
            self._snapshots.append(snapshot)
            if current_mb > self._peak_mb:
                self._peak_mb = current_mb

            # Alert if threshold exceeded
            if current_mb > self.alert_threshold_mb:
                logger.warning(
                    f"Memory alert: {current_mb:.1f} MB "
                    f"(threshold: {self.alert_threshold_mb:.1f} MB) "
                    f"during operation: {operation}"
                )

        return snapshot

    def start_monitoring(self) -> None:
        """Start continuous memory monitoring."""
        if self._monitoring:
            return

        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        logger.info(f"Started memory monitoring (interval: {self.sample_interval}s)")

    def stop_monitoring(self) -> None:
        """Stop continuous memory monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)

        logger.info("Stopped memory monitoring")

    def _monitor_loop(self) -> None:
        """Monitoring loop (runs in thread)."""
        while self._monitoring:
            self.snapshot(operation="background_monitor")
            time.sleep(self.sample_interval)

    def get_snapshots(
        self,
        operation: Optional[str] = None,
        since: Optional[float] = None,
    ) -> List[MemorySnapshot]:
        """
        Get memory snapshots.

        Args:
            operation: Filter by operation name
            since: Filter by timestamp (Unix time)

        Returns:
            List of snapshots
        """
        with self._lock:
            snapshots = self._snapshots

            if operation:
                snapshots = [s for s in snapshots if s.operation == operation]

            if since:
                snapshots = [s for s in snapshots if s.timestamp >= since]

            return snapshots

    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        return self._peak_mb

    def reset(self) -> None:
        """Reset monitoring data."""
        with self._lock:
            self._snapshots.clear()
            self._peak_mb = 0.0


class MemoryOptimizer:
    """Main memory optimizer coordinator."""

    def __init__(
        self,
        max_memory_mb: float = 500,
        lazy_loading: bool = True,
        stream_threshold_mb: float = 10,
        gc_interval: int = 10,
        auto_gc: bool = True,
    ):
        """
        Initialize memory optimizer.

        Args:
            max_memory_mb: Maximum memory per repository
            lazy_loading: Enable lazy loading
            stream_threshold_mb: Stream files larger than this
            gc_interval: Run GC every N operations
            auto_gc: Automatically run garbage collection
        """
        self.max_memory_mb = max_memory_mb
        self.lazy_loading = lazy_loading
        self.stream_threshold_mb = stream_threshold_mb
        self.gc_interval = gc_interval
        self.auto_gc = auto_gc

        # Components
        self.lazy_loader = LazyLoader()
        self.stream_processor = StreamProcessor()
        self.monitor = MemoryMonitor(alert_threshold_mb=max_memory_mb)

        # Statistics
        self._operations = 0
        self._gc_runs = 0
        self._gc_collected = 0

        # Environment optimized
        self._env_optimized = False

        logger.info(
            f"Memory optimizer initialized: max={max_memory_mb}MB, "
            f"lazy={lazy_loading}, stream_threshold={stream_threshold_mb}MB"
        )

    def optimize_environment(self) -> None:
        """Optimize Python environment for memory efficiency."""
        if self._env_optimized:
            return

        # Configure garbage collector
        gc.set_threshold(700, 10, 10)  # More aggressive GC

        # Enable GC debug stats (development only)
        if logger.isEnabledFor(logging.DEBUG):
            gc.set_debug(gc.DEBUG_STATS)

        # Set recursion limit (prevent stack overflow)
        sys.setrecursionlimit(10000)

        self._env_optimized = True
        logger.info("Environment optimized for memory efficiency")

    def optimize_git_config(self) -> Dict[str, str]:
        """
        Get git configuration for memory optimization.

        Returns:
            Git config dictionary
        """
        return {
            'core.packedGitLimit': '256m',
            'core.packedGitWindowSize': '256m',
            'pack.windowMemory': '256m',
            'pack.packSizeLimit': '256m',
            'pack.threads': '1',
            'core.preloadIndex': 'true',
            'core.fscache': 'true',
        }

    def create_lazy(
        self,
        loader: Callable[[], Any],
        name: str = "",
    ) -> Union[LazyProxy, Any]:
        """
        Create lazy-loaded object.

        Args:
            loader: Function to load data
            name: Name for debugging

        Returns:
            Lazy proxy if lazy loading enabled, else loaded object
        """
        if not self.lazy_loading:
            return loader()

        return self.lazy_loader.create_lazy(loader, name)

    def should_stream(self, file_path: Union[str, Path]) -> bool:
        """
        Check if file should be streamed.

        Args:
            file_path: Path to file

        Returns:
            True if file should be streamed
        """
        return self.stream_processor.should_stream(file_path, self.stream_threshold_mb)

    def stream_file(
        self,
        file_path: Union[str, Path],
        processor: Callable[[str], Any],
        line_mode: bool = True,
    ) -> List[Any]:
        """
        Stream and process large file.

        Args:
            file_path: Path to file
            processor: Function to process each line/chunk
            line_mode: Process line-by-line

        Returns:
            List of processed results
        """
        return self.stream_processor.process_large_file(
            file_path,
            processor,
            line_mode=line_mode,
        )

    def track_memory(self, operation: str) -> 'MemoryContext':
        """
        Context manager for tracking memory during operation.

        Args:
            operation: Operation name

        Returns:
            Memory tracking context manager
        """
        return MemoryContext(self, operation)

    def run_gc(self, force: bool = False) -> int:
        """
        Run garbage collection.

        Args:
            force: Force GC even if not at interval

        Returns:
            Number of objects collected
        """
        if not force and not self.auto_gc:
            return 0

        if not force:
            self._operations += 1
            if self._operations % self.gc_interval != 0:
                return 0

        logger.debug("Running garbage collection")
        collected = gc.collect()

        self._gc_runs += 1
        self._gc_collected += collected

        if collected > 0:
            logger.debug(f"GC collected {collected} objects")

        return collected

    def get_stats(self) -> MemoryStats:
        """Get memory statistics."""
        current_mb = self.monitor.get_current_memory()
        peak_mb = self.monitor.get_peak_memory()

        lazy_stats = self.lazy_loader.get_stats()
        stream_stats = self.stream_processor.get_stats()

        return MemoryStats(
            current_mb=current_mb,
            peak_mb=peak_mb,
            allocated_mb=current_mb,  # Approximate
            gc_collections=self._gc_runs,
            gc_collected=self._gc_collected,
            tracked_objects=lazy_stats['total_proxies'],
            lazy_loads=lazy_stats['loaded_proxies'],
            stream_reads=stream_stats['read_count'],
        )

    def reset(self) -> None:
        """Reset optimizer state."""
        self.lazy_loader.clear()
        self.monitor.reset()
        self._operations = 0
        self._gc_runs = 0
        self._gc_collected = 0


class MemoryContext:
    """Context manager for memory tracking."""

    def __init__(self, optimizer: MemoryOptimizer, operation: str):
        """
        Initialize memory context.

        Args:
            optimizer: Memory optimizer
            operation: Operation name
        """
        self.optimizer = optimizer
        self.operation = operation
        self._start_snapshot: Optional[MemorySnapshot] = None
        self._end_snapshot: Optional[MemorySnapshot] = None

    def __enter__(self) -> 'MemoryContext':
        """Enter context."""
        self._start_snapshot = self.optimizer.monitor.snapshot(
            operation=f"{self.operation}_start"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context."""
        self._end_snapshot = self.optimizer.monitor.snapshot(
            operation=f"{self.operation}_end"
        )

        # Run GC if needed
        self.optimizer.run_gc()

        # Log memory usage
        if self._start_snapshot and self._end_snapshot:
            delta = self._end_snapshot.memory_mb - self._start_snapshot.memory_mb
            logger.debug(
                f"Memory for {self.operation}: "
                f"{self._start_snapshot.memory_mb:.1f} MB -> "
                f"{self._end_snapshot.memory_mb:.1f} MB "
                f"(delta: {delta:+.1f} MB)"
            )

    def get_delta(self) -> float:
        """Get memory delta in MB."""
        if self._start_snapshot and self._end_snapshot:
            return self._end_snapshot.memory_mb - self._start_snapshot.memory_mb
        return 0.0


def create_memory_optimizer(
    max_memory_mb: float = 500,
    lazy_loading: bool = True,
    stream_threshold_mb: float = 10,
    gc_interval: int = 10,
    auto_gc: bool = True,
) -> MemoryOptimizer:
    """
    Create memory optimizer with default settings.

    Args:
        max_memory_mb: Maximum memory per repository
        lazy_loading: Enable lazy loading
        stream_threshold_mb: Stream files larger than this
        gc_interval: Run GC every N operations
        auto_gc: Automatically run garbage collection

    Returns:
        Configured memory optimizer
    """
    optimizer = MemoryOptimizer(
        max_memory_mb=max_memory_mb,
        lazy_loading=lazy_loading,
        stream_threshold_mb=stream_threshold_mb,
        gc_interval=gc_interval,
        auto_gc=auto_gc,
    )
    optimizer.optimize_environment()
    return optimizer
