# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Performance metrics module for INFO.yaml feature.

Tracks performance metrics, caching statistics, and operational health
of the INFO.yaml reporting feature.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class TimingMetric:
    """
    Represents a single timing measurement.

    Attributes:
        operation: Name of the operation being timed
        duration_ms: Duration in milliseconds
        timestamp: Unix timestamp when operation completed
        metadata: Additional context about the operation
    """

    operation: str
    duration_ms: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollectionMetrics:
    """
    Metrics for INFO.yaml collection operations.

    Tracks performance and statistics for file collection,
    parsing, enrichment, and validation.
    """

    # Collection statistics
    total_files_found: int = 0
    files_parsed_successfully: int = 0
    files_failed_to_parse: int = 0

    # Project statistics
    total_projects: int = 0
    projects_with_git_data: int = 0
    projects_without_git_data: int = 0

    # Committer statistics
    total_committers: int = 0
    committers_by_status: Dict[str, int] = field(default_factory=dict)
    committers_by_color: Dict[str, int] = field(default_factory=dict)

    # URL validation statistics
    total_urls: int = 0
    valid_urls: int = 0
    invalid_urls: int = 0
    urls_from_cache: int = 0

    # Timing metrics
    collection_duration_ms: float = 0.0
    parsing_duration_ms: float = 0.0
    enrichment_duration_ms: float = 0.0
    url_validation_duration_ms: float = 0.0
    total_duration_ms: float = 0.0

    # Error tracking
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize nested dictionaries."""
        if not self.committers_by_status:
            self.committers_by_status = {
                "current": 0,
                "active": 0,
                "inactive": 0,
                "unknown": 0,
            }

        if not self.committers_by_color:
            self.committers_by_color = {
                "green": 0,
                "orange": 0,
                "red": 0,
                "gray": 0,
            }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metrics to a dictionary.

        Returns:
            Dictionary representation of metrics
        """
        return {
            "collection": {
                "total_files_found": self.total_files_found,
                "files_parsed_successfully": self.files_parsed_successfully,
                "files_failed_to_parse": self.files_failed_to_parse,
                "parse_success_rate": self._calculate_percentage(
                    self.files_parsed_successfully, self.total_files_found
                ),
            },
            "projects": {
                "total": self.total_projects,
                "with_git_data": self.projects_with_git_data,
                "without_git_data": self.projects_without_git_data,
                "git_data_coverage": self._calculate_percentage(
                    self.projects_with_git_data, self.total_projects
                ),
            },
            "committers": {
                "total": self.total_committers,
                "by_status": self.committers_by_status.copy(),
                "by_color": self.committers_by_color.copy(),
            },
            "urls": {
                "total": self.total_urls,
                "valid": self.valid_urls,
                "invalid": self.invalid_urls,
                "from_cache": self.urls_from_cache,
                "validation_success_rate": self._calculate_percentage(
                    self.valid_urls, self.total_urls
                ),
                "cache_hit_rate": self._calculate_percentage(
                    self.urls_from_cache, self.total_urls
                ),
            },
            "performance": {
                "collection_ms": round(self.collection_duration_ms, 2),
                "parsing_ms": round(self.parsing_duration_ms, 2),
                "enrichment_ms": round(self.enrichment_duration_ms, 2),
                "url_validation_ms": round(self.url_validation_duration_ms, 2),
                "total_ms": round(self.total_duration_ms, 2),
                "total_seconds": round(self.total_duration_ms / 1000, 2),
            },
            "quality": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "error_list": self.errors[:10],  # First 10 errors
                "warning_list": self.warnings[:10],  # First 10 warnings
            },
        }

    def _calculate_percentage(self, numerator: int, denominator: int) -> float:
        """Calculate percentage with zero-division safety."""
        if denominator == 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    def get_summary(self) -> str:
        """
        Get a human-readable summary of metrics.

        Returns:
            Formatted summary string
        """
        summary_lines = [
            "INFO.yaml Collection Metrics Summary",
            "=" * 50,
            f"Files: {self.files_parsed_successfully}/{self.total_files_found} parsed successfully",
            f"Projects: {self.total_projects} total, {self.projects_with_git_data} with Git data",
            f"Committers: {self.total_committers} total",
            f"  - Current (🟢): {self.committers_by_status.get('current', 0)}",
            f"  - Active (🟠): {self.committers_by_status.get('active', 0)}",
            f"  - Inactive (🔴): {self.committers_by_status.get('inactive', 0)}",
            f"  - Unknown (⚫): {self.committers_by_status.get('unknown', 0)}",
            f"URLs: {self.valid_urls}/{self.total_urls} valid",
            f"Performance: {self.total_duration_ms / 1000:.2f}s total",
            f"  - Collection: {self.collection_duration_ms:.0f}ms",
            f"  - Parsing: {self.parsing_duration_ms:.0f}ms",
            f"  - Enrichment: {self.enrichment_duration_ms:.0f}ms",
            f"  - URL Validation: {self.url_validation_duration_ms:.0f}ms",
        ]

        if self.errors:
            summary_lines.append(f"⚠️  Errors: {len(self.errors)}")

        if self.warnings:
            summary_lines.append(f"⚠️  Warnings: {len(self.warnings)}")

        return "\n".join(summary_lines)


class MetricsCollector:
    """
    Collects and aggregates metrics for INFO.yaml operations.

    Provides context managers for timing operations and methods
    for recording various metrics throughout the collection process.
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self.metrics = CollectionMetrics()
        self._timing_stack: List[TimingMetric] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    def start_timer(self, operation: str, **metadata) -> None:
        """
        Start timing an operation.

        Args:
            operation: Name of the operation
            **metadata: Additional context to store with the timing
        """
        metric = TimingMetric(
            operation=operation,
            duration_ms=0.0,
            timestamp=time.time(),
            metadata=metadata,
        )
        self._timing_stack.append(metric)
        self.logger.debug(f"Started timer for operation: {operation}")

    def stop_timer(self, operation: str) -> float:
        """
        Stop timing an operation and record duration.

        Args:
            operation: Name of the operation (must match start_timer call)

        Returns:
            Duration in milliseconds

        Raises:
            ValueError: If no matching operation is being timed
        """
        if not self._timing_stack:
            raise ValueError(f"No timer started for operation: {operation}")

        metric = self._timing_stack.pop()

        if metric.operation != operation:
            # Put it back and raise error
            self._timing_stack.append(metric)
            raise ValueError(
                f"Timer mismatch: expected '{metric.operation}', got '{operation}'"
            )

        # Calculate duration
        duration_ms = (time.time() - metric.timestamp) * 1000
        metric.duration_ms = duration_ms

        # Record in metrics
        self._record_timing(operation, duration_ms)

        self.logger.debug(
            f"Stopped timer for operation: {operation} ({duration_ms:.2f}ms)"
        )

        return duration_ms

    def _record_timing(self, operation: str, duration_ms: float) -> None:
        """Record a timing metric in the appropriate field."""
        operation_lower = operation.lower()

        if "collect" in operation_lower:
            self.metrics.collection_duration_ms += duration_ms
        elif "pars" in operation_lower:
            self.metrics.parsing_duration_ms += duration_ms
        elif "enrich" in operation_lower:
            self.metrics.enrichment_duration_ms += duration_ms
        elif "validat" in operation_lower or "url" in operation_lower:
            self.metrics.url_validation_duration_ms += duration_ms

        self.metrics.total_duration_ms += duration_ms

    def record_files_found(self, count: int) -> None:
        """Record number of INFO.yaml files found."""
        self.metrics.total_files_found = count
        self.logger.debug(f"Recorded {count} files found")

    def record_file_parsed(self, success: bool = True) -> None:
        """Record result of parsing a single file."""
        if success:
            self.metrics.files_parsed_successfully += 1
        else:
            self.metrics.files_failed_to_parse += 1

    def record_projects(
        self,
        total: int,
        with_git_data: int,
        without_git_data: int,
    ) -> None:
        """
        Record project statistics.

        Args:
            total: Total number of projects
            with_git_data: Number of projects with Git data
            without_git_data: Number of projects without Git data
        """
        self.metrics.total_projects = total
        self.metrics.projects_with_git_data = with_git_data
        self.metrics.projects_without_git_data = without_git_data
        self.logger.debug(f"Recorded project stats: {total} total, {with_git_data} with Git data")

    def record_committers(
        self,
        total: int,
        by_status: Dict[str, int],
        by_color: Dict[str, int],
    ) -> None:
        """
        Record committer statistics.

        Args:
            total: Total number of committers
            by_status: Count by activity status
            by_color: Count by color code
        """
        self.metrics.total_committers = total
        self.metrics.committers_by_status = by_status.copy()
        self.metrics.committers_by_color = by_color.copy()
        self.logger.debug(f"Recorded committer stats: {total} total")

    def record_url_validation(
        self,
        total: int,
        valid: int,
        invalid: int,
        from_cache: int = 0,
    ) -> None:
        """
        Record URL validation statistics.

        Args:
            total: Total number of URLs validated
            valid: Number of valid URLs
            invalid: Number of invalid URLs
            from_cache: Number of results from cache
        """
        self.metrics.total_urls = total
        self.metrics.valid_urls = valid
        self.metrics.invalid_urls = invalid
        self.metrics.urls_from_cache = from_cache
        self.logger.debug(
            f"Recorded URL validation: {valid}/{total} valid, {from_cache} from cache"
        )

    def record_error(self, error: str) -> None:
        """
        Record an error message.

        Args:
            error: Error message
        """
        self.metrics.errors.append(error)
        self.logger.debug(f"Recorded error: {error}")

    def record_warning(self, warning: str) -> None:
        """
        Record a warning message.

        Args:
            warning: Warning message
        """
        self.metrics.warnings.append(warning)
        self.logger.debug(f"Recorded warning: {warning}")

    def get_metrics(self) -> CollectionMetrics:
        """
        Get the current metrics.

        Returns:
            CollectionMetrics object
        """
        return self.metrics

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        self.metrics = CollectionMetrics()
        self._timing_stack.clear()
        self.logger.debug("Metrics reset")

    def timer(self, operation: str, **metadata):
        """
        Context manager for timing operations.

        Args:
            operation: Name of the operation
            **metadata: Additional context

        Yields:
            MetricsCollector instance for chaining

        Example:
            >>> collector = MetricsCollector()
            >>> with collector.timer("parse_yaml"):
            ...     # Do work
            ...     pass
        """
        return TimerContext(self, operation, metadata)


class TimerContext:
    """Context manager for timing operations."""

    def __init__(
        self,
        collector: MetricsCollector,
        operation: str,
        metadata: Dict[str, Any],
    ):
        """
        Initialize timer context.

        Args:
            collector: MetricsCollector instance
            operation: Operation name
            metadata: Additional context
        """
        self.collector = collector
        self.operation = operation
        self.metadata = metadata

    def __enter__(self) -> MetricsCollector:
        """Start the timer."""
        self.collector.start_timer(self.operation, **self.metadata)
        return self.collector

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer."""
        self.collector.stop_timer(self.operation)
        return False  # Don't suppress exceptions


def create_metrics_collector() -> MetricsCollector:
    """
    Factory function to create a new metrics collector.

    Returns:
        MetricsCollector instance
    """
    return MetricsCollector()
