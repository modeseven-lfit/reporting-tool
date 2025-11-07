#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Performance Metrics Module

Collects and reports performance metrics for repository analysis operations.
Provides execution summaries, timing breakdowns, resource usage statistics,
and debug-level profiling information.

Features:
- Execution timing and breakdown
- Resource usage tracking (memory, CPU, disk I/O)
- API call statistics
- Operation profiling
- Debug mode detailed metrics
- Beautiful formatted output

Phase 13: CLI & UX Improvements - Step 6
"""

import os
import sys
import time
import psutil
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class TimingMetric:
    """Individual timing measurement."""

    name: str
    duration: float
    start_time: float
    end_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Format timing for display."""
        return f"{self.name}: {format_duration(self.duration)}"


@dataclass
class APIStatistics:
    """API call statistics."""

    api_name: str
    total_calls: int = 0
    cached_calls: int = 0
    failed_calls: int = 0
    total_duration: float = 0.0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        if self.total_calls == 0:
            return 0.0
        return (self.cached_calls / self.total_calls) * 100

    @property
    def average_duration(self) -> float:
        """Calculate average call duration."""
        if self.total_calls == 0:
            return 0.0
        return self.total_duration / self.total_calls

    @property
    def calls_per_second(self) -> float:
        """Calculate calls per second."""
        if self.total_duration == 0:
            return 0.0
        return self.total_calls / self.total_duration


@dataclass
class ResourceUsage:
    """Resource usage statistics."""

    peak_memory_mb: float = 0.0
    avg_memory_mb: float = 0.0
    cpu_time_seconds: float = 0.0
    cpu_utilization: float = 0.0
    disk_read_mb: float = 0.0
    disk_write_mb: float = 0.0


@dataclass
class OperationMetrics:
    """Metrics for a specific operation (e.g., repository analysis)."""

    operation_name: str
    duration: float
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# FORMATTING HELPERS
# =============================================================================


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2m 15s", "1h 23m 45s")
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"

    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {secs}s"

    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {secs}s"


def format_bytes(bytes_count: float) -> str:
    """
    Format bytes in human-readable format.

    Args:
        bytes_count: Number of bytes

    Returns:
        Formatted string (e.g., "1.2 GB", "345 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def format_percentage(value: float, total: float) -> str:
    """
    Format percentage with value.

    Args:
        value: Partial value
        total: Total value

    Returns:
        Formatted string (e.g., "45s (33%)")
    """
    if total == 0:
        return f"{format_duration(value)} (0%)"

    percentage = (value / total) * 100
    return f"{format_duration(value)} ({percentage:.0f}%)"


# =============================================================================
# METRICS COLLECTOR
# =============================================================================


class MetricsCollector:
    """
    Collects performance metrics during execution.

    Thread-safe metrics collection with timing, resource usage,
    and API statistics tracking.

    Example:
        >>> collector = MetricsCollector()
        >>> with collector.time_operation("analysis"):
        ...     # Do work
        ...     pass
        >>> collector.print_summary()
    """

    def __init__(self):
        """Initialize metrics collector."""
        self._start_time = time.time()
        self._end_time: Optional[float] = None
        self._timings: List[TimingMetric] = []
        self._api_stats: Dict[str, APIStatistics] = defaultdict(
            lambda: APIStatistics(api_name="unknown")
        )
        self._operation_metrics: List[OperationMetrics] = []
        self._lock = threading.Lock()

        # Resource tracking
        self._process = psutil.Process()
        self._initial_cpu_times = self._process.cpu_times()
        self._initial_io = self._get_io_counters()
        self._memory_samples: List[float] = []
        self._peak_memory = 0.0

        # Start resource monitoring
        self._monitoring = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_resources,
            daemon=True
        )
        self._monitor_thread.start()

    def _get_io_counters(self) -> Optional[Any]:
        """Get I/O counters if available."""
        try:
            return self._process.io_counters()
        except (AttributeError, psutil.AccessDenied):
            return None

    def _monitor_resources(self):
        """Monitor resource usage in background thread."""
        while self._monitoring:
            try:
                memory_mb = self._process.memory_info().rss / (1024 * 1024)
                with self._lock:
                    self._memory_samples.append(memory_mb)
                    self._peak_memory = max(self._peak_memory, memory_mb)
                time.sleep(0.5)  # Sample every 500ms
            except Exception:
                pass

    def time_operation(self, name: str, **metadata):
        """
        Context manager for timing operations.

        Args:
            name: Operation name
            **metadata: Additional metadata

        Returns:
            Context manager
        """
        return _TimingContext(self, name, metadata)

    def record_timing(
        self,
        name: str,
        duration: float,
        start_time: float,
        end_time: float,
        **metadata
    ):
        """
        Record a timing measurement.

        Args:
            name: Operation name
            duration: Duration in seconds
            start_time: Start timestamp
            end_time: End timestamp
            **metadata: Additional metadata
        """
        metric = TimingMetric(
            name=name,
            duration=duration,
            start_time=start_time,
            end_time=end_time,
            metadata=metadata
        )

        with self._lock:
            self._timings.append(metric)

    def record_api_call(
        self,
        api_name: str,
        duration: float,
        cached: bool = False,
        failed: bool = False
    ):
        """
        Record an API call.

        Args:
            api_name: Name of the API
            duration: Call duration in seconds
            cached: Whether result was cached
            failed: Whether call failed
        """
        with self._lock:
            stats = self._api_stats[api_name]
            stats.api_name = api_name
            stats.total_calls += 1
            stats.total_duration += duration

            if cached:
                stats.cached_calls += 1
            if failed:
                stats.failed_calls += 1

    def record_operation(
        self,
        operation_name: str,
        duration: float,
        success: bool = True,
        error: Optional[str] = None,
        **metadata
    ):
        """
        Record operation metrics.

        Args:
            operation_name: Name of the operation
            duration: Duration in seconds
            success: Whether operation succeeded
            error: Error message if failed
            **metadata: Additional metadata
        """
        metric = OperationMetrics(
            operation_name=operation_name,
            duration=duration,
            success=success,
            error=error,
            metadata=metadata
        )

        with self._lock:
            self._operation_metrics.append(metric)

    def finalize(self):
        """Finalize metrics collection."""
        self._end_time = time.time()
        self._monitoring = False

    def get_total_duration(self) -> float:
        """Get total execution duration."""
        end = self._end_time if self._end_time else time.time()
        return end - self._start_time

    def get_resource_usage(self) -> ResourceUsage:
        """
        Get resource usage statistics.

        Returns:
            ResourceUsage object
        """
        # CPU time
        cpu_times = self._process.cpu_times()
        cpu_user = cpu_times.user - self._initial_cpu_times.user
        cpu_system = cpu_times.system - self._initial_cpu_times.system
        total_cpu = cpu_user + cpu_system

        # CPU utilization
        wall_time = self.get_total_duration()
        cpu_util = (total_cpu / wall_time * 100) if wall_time > 0 else 0

        # Memory
        with self._lock:
            avg_memory = sum(self._memory_samples) / len(self._memory_samples) \
                if self._memory_samples else 0
            peak_memory = self._peak_memory

        # Disk I/O
        current_io = self._get_io_counters()
        disk_read_mb = 0.0
        disk_write_mb = 0.0

        if current_io and self._initial_io:
            try:
                disk_read_mb = (current_io.read_bytes - self._initial_io.read_bytes) / (1024 * 1024)
                disk_write_mb = (current_io.write_bytes - self._initial_io.write_bytes) / (1024 * 1024)
            except AttributeError:
                pass

        return ResourceUsage(
            peak_memory_mb=peak_memory,
            avg_memory_mb=avg_memory,
            cpu_time_seconds=total_cpu,
            cpu_utilization=cpu_util,
            disk_read_mb=disk_read_mb,
            disk_write_mb=disk_write_mb
        )

    def get_timing_breakdown(self) -> Dict[str, float]:
        """
        Get timing breakdown by operation category.

        Returns:
            Dictionary of category -> total duration
        """
        breakdown: defaultdict[str, float] = defaultdict(float)

        with self._lock:
            for timing in self._timings:
                # Extract category from name (e.g., "git:clone" -> "git")
                category = timing.name.split(':')[0] if ':' in timing.name else timing.name
                breakdown[category] += timing.duration

        return dict(breakdown)

    def print_summary(self, verbose: bool = False):
        """
        Print performance summary.

        Args:
            verbose: Include detailed breakdown
        """
        self.finalize()

        print("\n" + "=" * 70)
        print("  Performance Summary")
        print("=" * 70 + "\n")

        # Overall timing
        total_time = self.get_total_duration()
        print(f"Total time: {format_duration(total_time)}")

        # Operation metrics
        if self._operation_metrics:
            total_ops = len(self._operation_metrics)
            successful_ops = sum(1 for op in self._operation_metrics if op.success)
            avg_duration = sum(op.duration for op in self._operation_metrics) / total_ops

            print(f"Operations: {total_ops} total, {successful_ops} successful")
            print(f"Average operation time: {format_duration(avg_duration)}")

        # Timing breakdown
        if verbose:
            breakdown = self.get_timing_breakdown()
            if breakdown:
                print("\nBreakdown:")
                sorted_breakdown = sorted(
                    breakdown.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                for category, duration in sorted_breakdown:
                    print(f"  {category:20} {format_percentage(duration, total_time)}")

        # API statistics
        if self._api_stats:
            print("\nAPI Statistics:")
            for api_name, stats in sorted(self._api_stats.items()):
                print(f"  {api_name}:")
                print(f"    Calls: {stats.total_calls} "
                      f"({stats.calls_per_second:.1f} calls/sec, "
                      f"{stats.cache_hit_rate:.0f}% cache hit)")

        # Resource usage
        resources = self.get_resource_usage()
        print("\nResource Usage:")
        print(f"  Peak memory: {resources.peak_memory_mb:.1f} MB")
        print(f"  CPU time: {format_duration(resources.cpu_time_seconds)} "
              f"({resources.cpu_utilization:.0f}% utilization)")

        if resources.disk_read_mb > 0 or resources.disk_write_mb > 0:
            print(f"  Disk I/O: {resources.disk_read_mb:.1f} MB read, "
                  f"{resources.disk_write_mb:.1f} MB written")

        print("\n" + "=" * 70 + "\n")

    def print_debug_metrics(self):
        """Print detailed debug metrics."""
        self.finalize()

        print("\n" + "=" * 70)
        print("  Debug Metrics")
        print("=" * 70 + "\n")

        # Operation breakdown
        if self._operation_metrics:
            print("Operation Breakdown:")
            sorted_ops = sorted(
                self._operation_metrics,
                key=lambda x: x.duration,
                reverse=True
            )
            for op in sorted_ops[:10]:  # Top 10
                status = "✓" if op.success else "✗"
                warning = " ⚠ SLOW" if op.duration > 5.0 else ""
                print(f"  {status} {op.operation_name}: {format_duration(op.duration)}{warning}")
                if op.error:
                    print(f"      Error: {op.error}")

        # Slowest operations
        with self._lock:
            if self._timings:
                print("\nSlowest Operations:")
                sorted_timings = sorted(
                    self._timings,
                    key=lambda x: x.duration,
                    reverse=True
                )
                for i, timing in enumerate(sorted_timings[:10], 1):
                    print(f"  {i}. {timing.name}: {format_duration(timing.duration)}")

        # API details
        if self._api_stats:
            print("\nAPI Call Details:")
            for api_name, stats in sorted(self._api_stats.items()):
                print(f"  {api_name}:")
                print(f"    Total calls: {stats.total_calls}")
                print(f"    Cached: {stats.cached_calls} ({stats.cache_hit_rate:.1f}%)")
                print(f"    Failed: {stats.failed_calls}")
                print(f"    Avg duration: {format_duration(stats.average_duration)}")

        # Resource usage details
        resources = self.get_resource_usage()
        print("\nResource Usage Details:")
        print(f"  Memory:")
        print(f"    Peak: {resources.peak_memory_mb:.1f} MB")
        print(f"    Average: {resources.avg_memory_mb:.1f} MB")
        print(f"  CPU:")
        print(f"    Time: {format_duration(resources.cpu_time_seconds)}")
        print(f"    Utilization: {resources.cpu_utilization:.1f}%")
        if resources.disk_read_mb > 0 or resources.disk_write_mb > 0:
            print(f"  Disk I/O:")
            print(f"    Read: {resources.disk_read_mb:.1f} MB")
            print(f"    Write: {resources.disk_write_mb:.1f} MB")

        print("\n" + "=" * 70 + "\n")

    def get_output_summary(self, output_files: Dict[str, Path]) -> str:
        """
        Get output files summary.

        Args:
            output_files: Dictionary of format -> file path

        Returns:
            Formatted summary string
        """
        lines = ["Output:"]

        for format_name, file_path in sorted(output_files.items()):
            if file_path.exists():
                size = file_path.stat().st_size
                lines.append(f"  {format_name}: {file_path} ({format_bytes(size)})")
            else:
                lines.append(f"  {format_name}: {file_path} (not created)")

        return "\n".join(lines)


class _TimingContext:
    """Context manager for timing operations."""

    def __init__(self, collector: MetricsCollector, name: str, metadata: Dict[str, Any]):
        """Initialize timing context."""
        self.collector = collector
        self.name = name
        self.metadata = metadata
        self.start_time = 0.0

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and record."""
        end_time = time.time()
        duration = end_time - self.start_time

        self.collector.record_timing(
            self.name,
            duration,
            self.start_time,
            end_time,
            **self.metadata
        )

        return False


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """
    Get global metrics collector instance.

    Returns:
        MetricsCollector instance
    """
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def reset_metrics_collector():
    """Reset global metrics collector."""
    global _global_collector
    if _global_collector:
        _global_collector.finalize()
    _global_collector = MetricsCollector()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def time_operation(name: str, **metadata):
    """
    Time an operation using global collector.

    Args:
        name: Operation name
        **metadata: Additional metadata

    Returns:
        Context manager
    """
    return get_metrics_collector().time_operation(name, **metadata)


def record_api_call(api_name: str, duration: float, cached: bool = False, failed: bool = False):
    """
    Record an API call using global collector.

    Args:
        api_name: Name of the API
        duration: Call duration
        cached: Whether cached
        failed: Whether failed
    """
    get_metrics_collector().record_api_call(api_name, duration, cached, failed)


def print_performance_summary(verbose: bool = False):
    """
    Print performance summary using global collector.

    Args:
        verbose: Include detailed breakdown
    """
    get_metrics_collector().print_summary(verbose)


def print_debug_metrics():
    """Print debug metrics using global collector."""
    get_metrics_collector().print_debug_metrics()


__all__ = [
    # Data structures
    'TimingMetric',
    'APIStatistics',
    'ResourceUsage',
    'OperationMetrics',
    # Main class
    'MetricsCollector',
    # Global instance
    'get_metrics_collector',
    'reset_metrics_collector',
    # Convenience functions
    'time_operation',
    'record_api_call',
    'print_performance_summary',
    'print_debug_metrics',
    # Formatting
    'format_duration',
    'format_bytes',
    'format_percentage',
]
