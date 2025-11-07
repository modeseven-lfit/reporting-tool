# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Concurrency utilities for repository reporting system.

This package provides thread-safe abstractions for concurrent operations:
- JenkinsAllocationContext: Thread-safe Jenkins job allocation
- AdaptiveThreadPool: Dynamic thread pool with adaptive worker scaling
- HybridExecutor: Hybrid executor for CPU/IO-bound task routing
- ConcurrentErrorHandler: Structured error collection and retry logic
- CircuitBreaker: Circuit breaker pattern for fault tolerance

Phase 7: Concurrency Refinement - Enhanced concurrency primitives
"""

from .jenkins_allocation import JenkinsAllocationContext
from .adaptive_pool import AdaptiveThreadPool, PoolMetrics
from .hybrid_executor import (
    HybridExecutor,
    OperationType,
    ExecutorStats,
)
from .error_handler import (
    ConcurrentErrorHandler,
    CircuitBreaker,
    ErrorRecord,
    ErrorSeverity,
    CircuitOpenError,
    with_retry,
)

__all__ = [
    "JenkinsAllocationContext",
    "AdaptiveThreadPool",
    "PoolMetrics",
    "HybridExecutor",
    "OperationType",
    "ExecutorStats",
    "ConcurrentErrorHandler",
    "CircuitBreaker",
    "ErrorRecord",
    "ErrorSeverity",
    "CircuitOpenError",
    "with_retry",
]
