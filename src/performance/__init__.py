# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Performance optimization module for the Repository Reporting System.

This package provides utilities for profiling, parallel processing, caching,
memory optimization, and performance monitoring.

Modules:
    profiler: Performance profiling and metrics tracking
    parallel: Parallel repository processing
    git_optimizer: Git operation optimization
    cache: Enhanced caching system
    memory: Memory optimization and monitoring
    batch: Batch processing and API optimization
    reporter: Performance monitoring and reporting

Classes:
    PerformanceProfiler: Main profiling coordinator
    OperationTimer: Context manager for timing operations
    MemoryTracker: Memory usage monitoring
    ProfileReport: Performance report generation
    OperationCategory: Enum for operation categories

    ParallelRepositoryProcessor: Parallel processing coordinator
    WorkerPool: Worker pool management
    ResultAggregator: Result aggregation

    GitOptimizer: Git operation optimizer
    ReferenceRepository: Reference repository manager
    ShallowCloneStrategy: Shallow clone strategy

    CacheManager: Main cache coordinator
    RepositoryCache: Repository metadata caching
    GitOperationCache: Git operation result caching
    APIResponseCache: API response caching
    AnalysisResultCache: Analysis result caching

    MemoryOptimizer: Main memory optimization coordinator
    LazyLoader: Lazy loading for deferred data access
    StreamProcessor: Stream processing for large files
    MemoryMonitor: Memory usage tracking and alerting

    BatchProcessor: Batch processing coordinator
    RateLimitOptimizer: Smart rate limit tracking
    RequestBatcher: Request grouping and parallel execution

    PerformanceReporter: Performance monitoring and reporting
    MetricsCollector: Metrics collection from components
    MetricsVisualizer: Performance metrics visualization

Example:
    >>> from src.performance import PerformanceProfiler, CacheManager, MemoryOptimizer
    >>> profiler = PerformanceProfiler()
    >>> cache = CacheManager(cache_dir=".cache", ttl=3600)
    >>> optimizer = MemoryOptimizer(max_memory_mb=500)
    >>> optimizer.optimize_environment()
    >>> profiler.start()
    >>> with profiler.track_operation("analyze_repo", category="analysis"):
    ...     with optimizer.track_memory("analyze"):
    ...         # Check cache first
    ...         cached = cache.get("repo:owner/name")
    ...         if not cached:
    ...             # Do analysis work
    ...             result = analyze()
    ...             cache.set("repo:owner/name", result)
    ...     pass
    >>> profiler.stop()
    >>> report = profiler.get_report()
    >>> print(report.format())
"""

from .profiler import (
    PerformanceProfiler,
    OperationTimer,
    MemoryTracker,
    ProfileReport,
    OperationCategory,
    OperationMetric,
    AggregatedMetrics,
    profile_operation,
)

from .parallel import (
    ParallelRepositoryProcessor,
    WorkerPool,
    ResultAggregator,
    WorkerConfig,
    ProcessingResult,
    AggregatedResults,
    WorkerType,
    ProcessingStatus,
    parallel_map,
)

from .git_optimizer import (
    GitOptimizer,
    ReferenceRepository,
    ShallowCloneStrategy,
    GitConfig,
    GitOperationResult,
    CloneStrategy,
    GitOperationType,
    optimize_git_config_global,
    estimate_clone_time,
)

from .cache import (
    CacheManager,
    RepositoryCache,
    GitOperationCache,
    APIResponseCache,
    AnalysisResultCache,
    CacheEntry,
    CacheStats,
    CacheType,
    CacheKey,
    create_cache_manager,
)

from .memory import (
    MemoryOptimizer,
    LazyLoader,
    StreamProcessor,
    MemoryMonitor,
    MemoryStats,
    MemorySnapshot,
    LazyProxy,
    MemoryContext,
    MemoryUnit,
    create_memory_optimizer,
)

from .batch import (
    BatchProcessor,
    RateLimitOptimizer,
    RequestBatcher,
    RequestQueue,
    RateLimitInfo,
    APIRequest,
    BatchResult,
    RequestPriority,
    RetryStrategy,
    batch_api_calls,
    create_batch_processor,
)

from .reporter import (
    PerformanceReporter,
    MetricsCollector,
    MetricsVisualizer,
    PerformanceReport,
    Metric,
    MetricTrend,
    Alert,
    AlertRule,
    MetricType,
    AlertSeverity,
    create_performance_reporter,
)

__all__ = [
    # Profiling classes
    "PerformanceProfiler",
    "OperationTimer",
    "MemoryTracker",
    "ProfileReport",

    # Profiling data classes
    "OperationCategory",
    "OperationMetric",
    "AggregatedMetrics",

    # Parallel processing classes
    "ParallelRepositoryProcessor",
    "WorkerPool",
    "ResultAggregator",

    # Parallel processing data classes
    "WorkerConfig",
    "ProcessingResult",
    "AggregatedResults",
    "WorkerType",
    "ProcessingStatus",

    # Git optimization classes
    "GitOptimizer",
    "ReferenceRepository",
    "ShallowCloneStrategy",
    "GitConfig",
    "GitOperationResult",
    "CloneStrategy",
    "GitOperationType",

    # Caching classes
    "CacheManager",
    "RepositoryCache",
    "GitOperationCache",
    "APIResponseCache",
    "AnalysisResultCache",

    # Caching data classes
    "CacheEntry",
    "CacheStats",
    "CacheType",
    "CacheKey",

    # Memory optimization classes
    "MemoryOptimizer",
    "LazyLoader",
    "StreamProcessor",
    "MemoryMonitor",

    # Memory optimization data classes
    "MemoryStats",
    "MemorySnapshot",
    "LazyProxy",
    "MemoryContext",
    "MemoryUnit",

    # Batch processing classes
    "BatchProcessor",
    "RateLimitOptimizer",
    "RequestBatcher",
    "RequestQueue",

    # Batch processing data classes
    "RateLimitInfo",
    "APIRequest",
    "BatchResult",
    "RequestPriority",
    "RetryStrategy",

    # Reporting classes
    "PerformanceReporter",
    "MetricsCollector",
    "MetricsVisualizer",

    # Reporting data classes
    "PerformanceReport",
    "Metric",
    "MetricTrend",
    "Alert",
    "AlertRule",
    "MetricType",
    "AlertSeverity",

    # Utility functions
    "profile_operation",
    "parallel_map",
    "optimize_git_config_global",
    "estimate_clone_time",
    "create_cache_manager",
    "create_memory_optimizer",
    "batch_api_calls",
    "create_batch_processor",
    "create_performance_reporter",
]

__version__ = "1.0.0"
