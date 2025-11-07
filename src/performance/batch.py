# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Batch processing and API optimization module.

This module provides utilities for batching API requests, intelligent rate limiting,
request deduplication, and retry logic with exponential backoff.

Classes:
    BatchProcessor: Main batch processing coordinator
    RateLimitOptimizer: Smart rate limit tracking and optimization
    RequestBatcher: Request grouping and parallel execution
    RequestQueue: Priority queue for API requests
    RateLimitInfo: Rate limit information tracking
    BatchResult: Batch execution results

Example:
    >>> from src.performance.batch import BatchProcessor
    >>> processor = BatchProcessor(batch_size=10, parallel_requests=5)
    >>> results = processor.batch_requests(api_calls)
    >>> print(f"Success rate: {results.success_rate:.1%}")
"""

import asyncio
import logging
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from functools import wraps
import hashlib
import json

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Request priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class RetryStrategy(Enum):
    """Retry strategies."""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


@dataclass
class RateLimitInfo:
    """Rate limit information."""
    limit: int = 5000
    remaining: int = 5000
    reset_time: float = 0.0

    @property
    def reset_in_seconds(self) -> float:
        """Time until rate limit resets."""
        return max(0, self.reset_time - time.time())

    @property
    def usage_percentage(self) -> float:
        """Percentage of rate limit used."""
        if self.limit == 0:
            return 0.0
        return (self.limit - self.remaining) / self.limit

    def can_make_request(self, cost: int = 1) -> bool:
        """Check if request can be made."""
        if self.remaining <= 0:
            return time.time() >= self.reset_time
        return self.remaining >= cost

    def consume(self, cost: int = 1) -> None:
        """Consume rate limit budget."""
        self.remaining = max(0, self.remaining - cost)

    def update(self, limit: int, remaining: int, reset_time: float) -> None:
        """Update rate limit info."""
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time


@dataclass
class APIRequest:
    """API request metadata."""
    id: str
    endpoint: str
    method: str = "GET"
    params: Dict[str, Any] = field(default_factory=dict)
    priority: RequestPriority = RequestPriority.NORMAL
    cost: int = 1
    created_at: float = field(default_factory=time.time)
    retries: int = 0
    max_retries: int = 3

    def get_cache_key(self) -> str:
        """Generate cache key for request."""
        key_parts = [self.method, self.endpoint]
        if self.params:
            param_str = json.dumps(self.params, sort_keys=True)
            key_parts.append(param_str)
        key_str = ":".join(key_parts)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def can_retry(self) -> bool:
        """Check if request can be retried."""
        return self.retries < self.max_retries


@dataclass
class BatchResult:
    """Batch execution result."""
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    retried: int = 0
    deduplicated: int = 0
    execution_time: float = 0.0
    results: List[Any] = field(default_factory=list)
    errors: List[Exception] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful / self.total_requests

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        return 1.0 - self.success_rate

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requests": self.total_requests,
            "successful": self.successful,
            "failed": self.failed,
            "retried": self.retried,
            "deduplicated": self.deduplicated,
            "execution_time": self.execution_time,
            "success_rate": self.success_rate,
            "failure_rate": self.failure_rate,
        }

    def format(self) -> str:
        """Format result as string."""
        return f"""Batch Result:
  Total Requests: {self.total_requests:,}
  Successful: {self.successful:,} ({self.success_rate:.1%})
  Failed: {self.failed:,} ({self.failure_rate:.1%})
  Retried: {self.retried:,}
  Deduplicated: {self.deduplicated:,}
  Execution Time: {self.execution_time:.2f}s
  Throughput: {self.total_requests / self.execution_time if self.execution_time > 0 else 0:.1f} req/s"""


class RequestQueue:
    """Priority queue for API requests."""

    def __init__(self):
        """Initialize request queue."""
        self._queues: Dict[RequestPriority, deque] = {
            priority: deque() for priority in RequestPriority
        }
        self._lock = threading.Lock()

    def enqueue(self, request: APIRequest) -> None:
        """Add request to queue."""
        with self._lock:
            self._queues[request.priority].append(request)

    def dequeue(self) -> Optional[APIRequest]:
        """Get next request from queue (highest priority first)."""
        with self._lock:
            # Check priorities from highest to lowest
            for priority in sorted(RequestPriority, key=lambda p: p.value, reverse=True):
                if self._queues[priority]:
                    request: APIRequest = self._queues[priority].popleft()
                    return request
            return None

    def peek(self) -> Optional[APIRequest]:
        """Peek at next request without removing."""
        with self._lock:
            for priority in sorted(RequestPriority, key=lambda p: p.value, reverse=True):
                if self._queues[priority]:
                    request: APIRequest = self._queues[priority][0]
                    return request
            return None

    def size(self) -> int:
        """Get total queue size."""
        with self._lock:
            return sum(len(q) for q in self._queues.values())

    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return self.size() == 0

    def clear(self) -> None:
        """Clear all queues."""
        with self._lock:
            for queue in self._queues.values():
                queue.clear()


class RateLimitOptimizer:
    """Smart rate limit tracking and optimization."""

    def __init__(
        self,
        initial_limit: int = 5000,
        buffer_percentage: float = 0.1,
        adaptive: bool = True,
    ):
        """
        Initialize rate limit optimizer.

        Args:
            initial_limit: Initial rate limit
            buffer_percentage: Reserve buffer (0.1 = 10%)
            adaptive: Adapt to actual rate limits
        """
        self.rate_limits: Dict[str, RateLimitInfo] = defaultdict(
            lambda: RateLimitInfo(limit=initial_limit, remaining=initial_limit)
        )
        self.buffer_percentage = buffer_percentage
        self.adaptive = adaptive
        self._lock = threading.Lock()

        logger.info(f"Rate limit optimizer initialized: limit={initial_limit}, buffer={buffer_percentage:.1%}")

    def can_make_request(
        self,
        endpoint: str = "default",
        cost: int = 1,
    ) -> bool:
        """
        Check if request can be made.

        Args:
            endpoint: API endpoint
            cost: Request cost

        Returns:
            True if request can be made
        """
        with self._lock:
            rate_limit = self.rate_limits[endpoint]

            # Check if reset time has passed and reset if needed
            if rate_limit.remaining <= 0 and time.time() >= rate_limit.reset_time:
                rate_limit.remaining = rate_limit.limit

            # Apply buffer
            buffer_amount = int(rate_limit.limit * self.buffer_percentage)
            effective_remaining = rate_limit.remaining - buffer_amount

            # Check if we have enough remaining for this request
            return effective_remaining >= cost

    def wait_if_needed(
        self,
        endpoint: str = "default",
        cost: int = 1,
    ) -> float:
        """
        Wait if rate limit would be exceeded.

        Args:
            endpoint: API endpoint
            cost: Request cost

        Returns:
            Time waited in seconds
        """
        if self.can_make_request(endpoint, cost):
            return 0.0

        rate_limit = self.rate_limits[endpoint]
        wait_time = rate_limit.reset_in_seconds

        if wait_time > 0:
            logger.info(f"Rate limit approaching, waiting {wait_time:.1f}s for reset")
            time.sleep(wait_time)
            return wait_time

        return 0.0

    def record_request(
        self,
        endpoint: str = "default",
        cost: int = 1,
    ) -> None:
        """
        Record a request.

        Args:
            endpoint: API endpoint
            cost: Request cost
        """
        with self._lock:
            self.rate_limits[endpoint].consume(cost)

    def update_from_response(
        self,
        endpoint: str = "default",
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        reset_time: Optional[float] = None,
    ) -> None:
        """
        Update rate limit from API response.

        Args:
            endpoint: API endpoint
            limit: Rate limit
            remaining: Remaining requests
            reset_time: Reset timestamp
        """
        if not self.adaptive:
            return

        with self._lock:
            rate_limit = self.rate_limits[endpoint]

            if limit is not None:
                rate_limit.limit = limit
            if remaining is not None:
                rate_limit.remaining = remaining
            if reset_time is not None:
                rate_limit.reset_time = reset_time

    def get_info(self, endpoint: str = "default") -> RateLimitInfo:
        """Get rate limit info for endpoint."""
        with self._lock:
            return self.rate_limits[endpoint]

    def get_all_info(self) -> Dict[str, RateLimitInfo]:
        """Get all rate limit info."""
        with self._lock:
            return dict(self.rate_limits)


class RequestBatcher:
    """Request grouping and parallel execution."""

    def __init__(
        self,
        batch_size: int = 10,
        parallel_requests: int = 5,
        deduplicate: bool = True,
    ):
        """
        Initialize request batcher.

        Args:
            batch_size: Number of requests per batch
            parallel_requests: Number of parallel requests
            deduplicate: Remove duplicate requests
        """
        self.batch_size = batch_size
        self.parallel_requests = parallel_requests
        self.deduplicate = deduplicate

        self._request_cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()

        logger.info(
            f"Request batcher initialized: batch_size={batch_size}, "
            f"parallel={parallel_requests}, deduplicate={deduplicate}"
        )

    def batch_requests(
        self,
        requests: List[APIRequest],
    ) -> List[List[APIRequest]]:
        """
        Group requests into batches.

        Args:
            requests: List of API requests

        Returns:
            List of request batches
        """
        if self.deduplicate:
            requests = self._deduplicate_requests(requests)

        batches = []
        for i in range(0, len(requests), self.batch_size):
            batch = requests[i:i + self.batch_size]
            batches.append(batch)

        return batches

    def _deduplicate_requests(
        self,
        requests: List[APIRequest],
    ) -> List[APIRequest]:
        """Remove duplicate requests."""
        seen_keys = set()
        unique_requests = []

        for request in requests:
            cache_key = request.get_cache_key()
            if cache_key not in seen_keys:
                seen_keys.add(cache_key)
                unique_requests.append(request)

        if len(unique_requests) < len(requests):
            deduped = len(requests) - len(unique_requests)
            logger.debug(f"Deduplicated {deduped} requests")

        return unique_requests

    def get_cached_result(self, request: APIRequest) -> Optional[Any]:
        """Get cached result for request."""
        if not self.deduplicate:
            return None

        cache_key = request.get_cache_key()
        with self._cache_lock:
            return self._request_cache.get(cache_key)

    def cache_result(self, request: APIRequest, result: Any) -> None:
        """Cache request result."""
        if not self.deduplicate:
            return

        cache_key = request.get_cache_key()
        with self._cache_lock:
            self._request_cache[cache_key] = result

    def clear_cache(self) -> None:
        """Clear request cache."""
        with self._cache_lock:
            self._request_cache.clear()


class BatchProcessor:
    """Main batch processing coordinator."""

    def __init__(
        self,
        batch_size: int = 10,
        parallel_requests: int = 5,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0,
        rate_limit_buffer: float = 0.1,
    ):
        """
        Initialize batch processor.

        Args:
            batch_size: Number of requests per batch
            parallel_requests: Number of parallel requests
            retry_strategy: Retry strategy
            max_retries: Maximum retry attempts
            initial_backoff: Initial backoff time in seconds
            max_backoff: Maximum backoff time in seconds
            rate_limit_buffer: Rate limit buffer percentage
        """
        self.batch_size = batch_size
        self.parallel_requests = parallel_requests
        self.retry_strategy = retry_strategy
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff

        # Components
        self.rate_limiter = RateLimitOptimizer(buffer_percentage=rate_limit_buffer)
        self.batcher = RequestBatcher(batch_size=batch_size, parallel_requests=parallel_requests)
        self.queue = RequestQueue()

        logger.info(
            f"Batch processor initialized: batch_size={batch_size}, "
            f"parallel={parallel_requests}, retry={retry_strategy.value}"
        )

    def calculate_backoff(self, retry_count: int) -> float:
        """
        Calculate backoff time for retry.

        Args:
            retry_count: Number of retries already attempted

        Returns:
            Backoff time in seconds
        """
        if self.retry_strategy == RetryStrategy.EXPONENTIAL:
            backoff = self.initial_backoff * (2 ** retry_count)
        elif self.retry_strategy == RetryStrategy.LINEAR:
            backoff = self.initial_backoff * (retry_count + 1)
        else:  # FIXED
            backoff = self.initial_backoff

        return float(min(backoff, self.max_backoff))

    def execute_request(
        self,
        request: APIRequest,
        executor: Callable[[APIRequest], Any],
    ) -> Tuple[Optional[Any], Optional[Exception]]:
        """
        Execute a single request with retry logic.

        Args:
            request: API request
            executor: Function to execute request

        Returns:
            Tuple of (result, error)
        """
        # Check cache first
        cached = self.batcher.get_cached_result(request)
        if cached is not None:
            return cached, None

        last_error = None

        while request.can_retry():
            try:
                # Check rate limit
                wait_time = self.rate_limiter.wait_if_needed(request.endpoint, request.cost)

                # Execute request
                result = executor(request)

                # Record success
                self.rate_limiter.record_request(request.endpoint, request.cost)

                # Cache result
                self.batcher.cache_result(request, result)

                return result, None

            except Exception as e:
                last_error = e
                request.retries += 1

                if request.can_retry():
                    backoff = self.calculate_backoff(request.retries)
                    logger.warning(
                        f"Request failed (attempt {request.retries}/{request.max_retries}), "
                        f"retrying in {backoff:.1f}s: {e}"
                    )
                    time.sleep(backoff)
                else:
                    logger.error(f"Request failed after {request.retries} retries: {e}")

        return None, last_error

    def process_batch(
        self,
        requests: List[APIRequest],
        executor: Callable[[APIRequest], Any],
    ) -> BatchResult:
        """
        Process a batch of requests.

        Args:
            requests: List of API requests
            executor: Function to execute requests

        Returns:
            Batch result
        """
        start_time = time.time()
        result = BatchResult(total_requests=len(requests))

        # Group into batches
        batches = self.batcher.batch_requests(requests)
        result.deduplicated = len(requests) - sum(len(b) for b in batches)

        for batch in batches:
            # Execute batch (limited parallelism)
            batch_results = []
            batch_errors = []

            # Simple parallel execution with thread pool
            from concurrent.futures import ThreadPoolExecutor, as_completed

            with ThreadPoolExecutor(max_workers=self.parallel_requests) as pool:
                futures = {
                    pool.submit(self.execute_request, req, executor): req
                    for req in batch
                }

                for future in as_completed(futures):
                    request = futures[future]
                    try:
                        res, err = future.result()

                        if err is None:
                            batch_results.append(res)
                            result.successful += 1
                        else:
                            batch_errors.append(err)
                            result.failed += 1

                        if request.retries > 0:
                            result.retried += 1

                    except Exception as e:
                        batch_errors.append(e)
                        result.failed += 1

            result.results.extend(batch_results)
            result.errors.extend(batch_errors)

        result.execution_time = time.time() - start_time

        logger.info(
            f"Processed {result.total_requests} requests: "
            f"{result.successful} successful, {result.failed} failed, "
            f"{result.retried} retried, {result.deduplicated} deduplicated "
            f"in {result.execution_time:.2f}s"
        )

        return result

    def update_rate_limit(
        self,
        endpoint: str = "default",
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        reset_time: Optional[float] = None,
    ) -> None:
        """Update rate limit information from API response."""
        self.rate_limiter.update_from_response(endpoint, limit, remaining, reset_time)

    def get_rate_limit_info(self, endpoint: str = "default") -> RateLimitInfo:
        """Get rate limit info for endpoint."""
        return self.rate_limiter.get_info(endpoint)


def batch_api_calls(
    batch_size: int = 10,
    parallel_requests: int = 5,
    max_retries: int = 3,
):
    """
    Decorator for batching API calls.

    Args:
        batch_size: Number of requests per batch
        parallel_requests: Number of parallel requests
        max_retries: Maximum retry attempts

    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        processor = BatchProcessor(
            batch_size=batch_size,
            parallel_requests=parallel_requests,
            max_retries=max_retries,
        )

        @wraps(func)
        def wrapper(requests: List[APIRequest], *args, **kwargs):
            def executor(request: APIRequest):
                return func(request, *args, **kwargs)

            return processor.process_batch(requests, executor)

        return wrapper

    return decorator


def create_batch_processor(
    batch_size: int = 10,
    parallel_requests: int = 5,
    retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    max_backoff: float = 60.0,
    rate_limit_buffer: float = 0.1,
) -> BatchProcessor:
    """
    Create batch processor with default settings.

    Args:
        batch_size: Number of requests per batch
        parallel_requests: Number of parallel requests
        retry_strategy: Retry strategy
        max_retries: Maximum retry attempts
        initial_backoff: Initial backoff time
        max_backoff: Maximum backoff time
        rate_limit_buffer: Rate limit buffer percentage

    Returns:
        Configured batch processor
    """
    return BatchProcessor(
        batch_size=batch_size,
        parallel_requests=parallel_requests,
        retry_strategy=retry_strategy,
        max_retries=max_retries,
        initial_backoff=initial_backoff,
        max_backoff=max_backoff,
        rate_limit_buffer=rate_limit_buffer,
    )
