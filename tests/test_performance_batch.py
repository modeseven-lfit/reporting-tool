# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for the batch processing and API optimization module.

This module tests all aspects of batch processing including:
- Batch processor operations
- Rate limit tracking and optimization
- Request batching and deduplication
- Retry logic with backoff
- Priority queue management
- Request execution
"""

import time

from performance.batch import (
    APIRequest,
    BatchProcessor,
    BatchResult,
    RateLimitInfo,
    RateLimitOptimizer,
    RequestBatcher,
    RequestPriority,
    RequestQueue,
    RetryStrategy,
    batch_api_calls,
    create_batch_processor,
)


class TestRequestPriority:
    """Test RequestPriority enum."""

    def test_priority_values(self):
        """Test priority level values."""
        assert RequestPriority.LOW.value == 1
        assert RequestPriority.NORMAL.value == 2
        assert RequestPriority.HIGH.value == 3
        assert RequestPriority.CRITICAL.value == 4


class TestRetryStrategy:
    """Test RetryStrategy enum."""

    def test_retry_strategies(self):
        """Test retry strategy values."""
        assert RetryStrategy.EXPONENTIAL.value == "exponential"
        assert RetryStrategy.LINEAR.value == "linear"
        assert RetryStrategy.FIXED.value == "fixed"


class TestRateLimitInfo:
    """Test RateLimitInfo dataclass."""

    def test_create_rate_limit_info(self):
        """Test creating rate limit info."""
        info = RateLimitInfo(
            limit=5000,
            remaining=3000,
            reset_time=time.time() + 3600,
        )

        assert info.limit == 5000
        assert info.remaining == 3000
        assert info.reset_in_seconds > 0

    def test_usage_percentage(self):
        """Test usage percentage calculation."""
        info = RateLimitInfo(limit=1000, remaining=250)

        assert info.usage_percentage == 0.75

    def test_can_make_request(self):
        """Test request permission check."""
        info = RateLimitInfo(limit=100, remaining=10)

        assert info.can_make_request(cost=5)
        assert info.can_make_request(cost=10)
        assert not info.can_make_request(cost=20)

    def test_can_make_request_after_reset(self):
        """Test request permission after reset."""
        info = RateLimitInfo(
            limit=100,
            remaining=0,
            reset_time=time.time() - 1,  # Already reset
        )

        assert info.can_make_request()

    def test_consume(self):
        """Test consuming rate limit."""
        info = RateLimitInfo(limit=100, remaining=50)

        info.consume(10)
        assert info.remaining == 40

        info.consume(40)
        assert info.remaining == 0

        info.consume(10)
        assert info.remaining == 0  # Can't go negative

    def test_update(self):
        """Test updating rate limit info."""
        info = RateLimitInfo()

        new_reset = time.time() + 3600
        info.update(limit=6000, remaining=5500, reset_time=new_reset)

        assert info.limit == 6000
        assert info.remaining == 5500
        assert info.reset_time == new_reset


class TestAPIRequest:
    """Test APIRequest dataclass."""

    def test_create_request(self):
        """Test creating API request."""
        request = APIRequest(
            id="req1",
            endpoint="/repos/owner/repo",
            method="GET",
            params={"page": 1},
            priority=RequestPriority.HIGH,
        )

        assert request.id == "req1"
        assert request.endpoint == "/repos/owner/repo"
        assert request.method == "GET"
        assert request.priority == RequestPriority.HIGH

    def test_cache_key_generation(self):
        """Test cache key generation."""
        request1 = APIRequest(
            id="req1",
            endpoint="/test",
            method="GET",
            params={"a": 1, "b": 2},
        )

        request2 = APIRequest(
            id="req2",
            endpoint="/test",
            method="GET",
            params={"b": 2, "a": 1},  # Different order
        )

        # Same params should generate same key
        assert request1.get_cache_key() == request2.get_cache_key()

    def test_cache_key_different_params(self):
        """Test cache key with different params."""
        request1 = APIRequest(
            id="req1",
            endpoint="/test",
            params={"a": 1},
        )

        request2 = APIRequest(
            id="req2",
            endpoint="/test",
            params={"a": 2},
        )

        assert request1.get_cache_key() != request2.get_cache_key()

    def test_can_retry(self):
        """Test retry check."""
        request = APIRequest(
            id="req1",
            endpoint="/test",
            max_retries=3,
        )

        assert request.can_retry()

        request.retries = 3
        assert not request.can_retry()

        request.retries = 5
        assert not request.can_retry()


class TestBatchResult:
    """Test BatchResult dataclass."""

    def test_create_result(self):
        """Test creating batch result."""
        result = BatchResult(
            total_requests=100,
            successful=80,
            failed=20,
        )

        assert result.total_requests == 100
        assert result.successful == 80
        assert result.failed == 20

    def test_success_rate(self):
        """Test success rate calculation."""
        result = BatchResult(
            total_requests=100,
            successful=75,
            failed=25,
        )

        assert result.success_rate == 0.75
        assert result.failure_rate == 0.25

    def test_empty_result(self):
        """Test empty result."""
        result = BatchResult()

        assert result.success_rate == 0.0
        assert result.failure_rate == 1.0

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = BatchResult(
            total_requests=50,
            successful=40,
            failed=10,
        )

        data = result.to_dict()

        assert data["total_requests"] == 50
        assert data["successful"] == 40
        assert data["failed"] == 10
        assert data["success_rate"] == 0.8

    def test_format(self):
        """Test formatting result."""
        result = BatchResult(
            total_requests=100,
            successful=90,
            failed=10,
            execution_time=10.0,
        )

        formatted = result.format()

        assert "100" in formatted
        assert "90" in formatted
        assert "90.0%" in formatted


class TestRequestQueue:
    """Test RequestQueue class."""

    def test_enqueue_dequeue(self):
        """Test basic enqueue and dequeue."""
        queue = RequestQueue()

        request = APIRequest(id="req1", endpoint="/test")
        queue.enqueue(request)

        assert queue.size() == 1

        dequeued = queue.dequeue()
        assert dequeued.id == "req1"
        assert queue.size() == 0

    def test_priority_ordering(self):
        """Test priority-based ordering."""
        queue = RequestQueue()

        # Add requests with different priorities
        queue.enqueue(APIRequest(id="low", endpoint="/test", priority=RequestPriority.LOW))
        queue.enqueue(
            APIRequest(id="critical", endpoint="/test", priority=RequestPriority.CRITICAL)
        )
        queue.enqueue(APIRequest(id="normal", endpoint="/test", priority=RequestPriority.NORMAL))
        queue.enqueue(APIRequest(id="high", endpoint="/test", priority=RequestPriority.HIGH))

        # Should dequeue in priority order
        assert queue.dequeue().id == "critical"
        assert queue.dequeue().id == "high"
        assert queue.dequeue().id == "normal"
        assert queue.dequeue().id == "low"

    def test_peek(self):
        """Test peeking at next request."""
        queue = RequestQueue()

        request = APIRequest(id="req1", endpoint="/test")
        queue.enqueue(request)

        # Peek should not remove
        peeked = queue.peek()
        assert peeked.id == "req1"
        assert queue.size() == 1

        # Dequeue should remove
        dequeued = queue.dequeue()
        assert dequeued.id == "req1"
        assert queue.size() == 0

    def test_is_empty(self):
        """Test empty check."""
        queue = RequestQueue()

        assert queue.is_empty()

        queue.enqueue(APIRequest(id="req1", endpoint="/test"))
        assert not queue.is_empty()

        queue.dequeue()
        assert queue.is_empty()

    def test_clear(self):
        """Test clearing queue."""
        queue = RequestQueue()

        for i in range(10):
            queue.enqueue(APIRequest(id=f"req{i}", endpoint="/test"))

        assert queue.size() == 10

        queue.clear()
        assert queue.size() == 0
        assert queue.is_empty()


class TestRateLimitOptimizer:
    """Test RateLimitOptimizer class."""

    def test_initialization(self):
        """Test optimizer initialization."""
        optimizer = RateLimitOptimizer(
            initial_limit=5000,
            buffer_percentage=0.1,
        )

        assert optimizer.buffer_percentage == 0.1

    def test_can_make_request(self):
        """Test request permission check."""
        optimizer = RateLimitOptimizer(initial_limit=100, buffer_percentage=0.0)

        # First request should be allowed (initial limit = 100)
        assert optimizer.can_make_request("test", cost=10)
        assert optimizer.can_make_request("test", cost=100)

        # After recording a request, check remaining
        optimizer.record_request("test", cost=50)
        assert optimizer.can_make_request("test", cost=50)
        assert not optimizer.can_make_request("test", cost=60)

    def test_buffer_application(self):
        """Test buffer percentage application."""
        optimizer = RateLimitOptimizer(initial_limit=100, buffer_percentage=0.1)

        # With 10% buffer, effective remaining is 90 (100 - 10)
        # Should allow requests up to 90
        assert optimizer.can_make_request("test", cost=90)

        # After recording, remaining = 100, effective = 90
        # Cost of 91 should fail
        assert not optimizer.can_make_request("test", cost=91)

    def test_record_request(self):
        """Test recording requests."""
        optimizer = RateLimitOptimizer(initial_limit=100, buffer_percentage=0.0)

        optimizer.record_request("test", cost=30)
        info = optimizer.get_info("test")
        assert info.remaining == 70

        optimizer.record_request("test", cost=40)
        info = optimizer.get_info("test")
        assert info.remaining == 30

    def test_update_from_response(self):
        """Test updating from API response."""
        optimizer = RateLimitOptimizer(initial_limit=5000)

        reset_time = time.time() + 3600
        optimizer.update_from_response(
            "test",
            limit=6000,
            remaining=5500,
            reset_time=reset_time,
        )

        info = optimizer.get_info("test")
        assert info.limit == 6000
        assert info.remaining == 5500
        assert info.reset_time == reset_time

    def test_multiple_endpoints(self):
        """Test tracking multiple endpoints."""
        optimizer = RateLimitOptimizer(initial_limit=100)

        optimizer.record_request("endpoint1", cost=10)
        optimizer.record_request("endpoint2", cost=20)

        info1 = optimizer.get_info("endpoint1")
        info2 = optimizer.get_info("endpoint2")

        assert info1.remaining == 90
        assert info2.remaining == 80

    def test_get_all_info(self):
        """Test getting all rate limit info."""
        optimizer = RateLimitOptimizer(initial_limit=100)

        optimizer.record_request("ep1", cost=10)
        optimizer.record_request("ep2", cost=20)

        all_info = optimizer.get_all_info()

        assert "ep1" in all_info
        assert "ep2" in all_info


class TestRequestBatcher:
    """Test RequestBatcher class."""

    def test_initialization(self):
        """Test batcher initialization."""
        batcher = RequestBatcher(
            batch_size=10,
            parallel_requests=5,
            deduplicate=True,
        )

        assert batcher.batch_size == 10
        assert batcher.parallel_requests == 5
        assert batcher.deduplicate is True

    def test_batch_requests(self):
        """Test batching requests."""
        batcher = RequestBatcher(batch_size=5, deduplicate=False)

        requests = [APIRequest(id=f"req{i}", endpoint="/test") for i in range(12)]

        batches = batcher.batch_requests(requests)

        assert len(batches) == 3
        assert len(batches[0]) == 5
        assert len(batches[1]) == 5
        assert len(batches[2]) == 2

    def test_deduplication(self):
        """Test request deduplication."""
        batcher = RequestBatcher(batch_size=10, deduplicate=True)

        requests = [
            APIRequest(id="req1", endpoint="/test", params={"a": 1}),
            APIRequest(id="req2", endpoint="/test", params={"a": 1}),  # Duplicate
            APIRequest(id="req3", endpoint="/test", params={"a": 2}),
        ]

        batches = batcher.batch_requests(requests)

        # Should deduplicate to 2 requests
        total_requests = sum(len(b) for b in batches)
        assert total_requests == 2

    def test_caching(self):
        """Test result caching."""
        batcher = RequestBatcher(deduplicate=True)

        request = APIRequest(id="req1", endpoint="/test")
        result = {"data": "value"}

        # Cache result
        batcher.cache_result(request, result)

        # Retrieve cached result
        cached = batcher.get_cached_result(request)
        assert cached == result

    def test_clear_cache(self):
        """Test clearing cache."""
        batcher = RequestBatcher(deduplicate=True)

        request = APIRequest(id="req1", endpoint="/test")
        batcher.cache_result(request, {"data": "value"})

        assert batcher.get_cached_result(request) is not None

        batcher.clear_cache()

        assert batcher.get_cached_result(request) is None


class TestBatchProcessor:
    """Test BatchProcessor class."""

    def test_initialization(self):
        """Test processor initialization."""
        processor = BatchProcessor(
            batch_size=10,
            parallel_requests=5,
            retry_strategy=RetryStrategy.EXPONENTIAL,
            max_retries=3,
        )

        assert processor.batch_size == 10
        assert processor.parallel_requests == 5
        assert processor.retry_strategy == RetryStrategy.EXPONENTIAL
        assert processor.max_retries == 3

    def test_calculate_backoff_exponential(self):
        """Test exponential backoff calculation."""
        processor = BatchProcessor(
            retry_strategy=RetryStrategy.EXPONENTIAL,
            initial_backoff=1.0,
        )

        assert processor.calculate_backoff(0) == 1.0
        assert processor.calculate_backoff(1) == 2.0
        assert processor.calculate_backoff(2) == 4.0
        assert processor.calculate_backoff(3) == 8.0

    def test_calculate_backoff_linear(self):
        """Test linear backoff calculation."""
        processor = BatchProcessor(
            retry_strategy=RetryStrategy.LINEAR,
            initial_backoff=2.0,
        )

        assert processor.calculate_backoff(0) == 2.0
        assert processor.calculate_backoff(1) == 4.0
        assert processor.calculate_backoff(2) == 6.0

    def test_calculate_backoff_fixed(self):
        """Test fixed backoff calculation."""
        processor = BatchProcessor(
            retry_strategy=RetryStrategy.FIXED,
            initial_backoff=5.0,
        )

        assert processor.calculate_backoff(0) == 5.0
        assert processor.calculate_backoff(1) == 5.0
        assert processor.calculate_backoff(10) == 5.0

    def test_calculate_backoff_max(self):
        """Test maximum backoff limit."""
        processor = BatchProcessor(
            retry_strategy=RetryStrategy.EXPONENTIAL,
            initial_backoff=10.0,
            max_backoff=30.0,
        )

        # Should cap at max_backoff
        assert processor.calculate_backoff(0) == 10.0
        assert processor.calculate_backoff(1) == 20.0
        assert processor.calculate_backoff(2) == 30.0  # Capped
        assert processor.calculate_backoff(10) == 30.0  # Still capped

    def test_execute_request_success(self):
        """Test successful request execution."""
        processor = BatchProcessor(max_retries=3)

        request = APIRequest(id="req1", endpoint="/test")

        def mock_executor(req):
            return {"success": True}

        result, error = processor.execute_request(request, mock_executor)

        assert result == {"success": True}
        assert error is None
        assert request.retries == 0

    def test_execute_request_with_retry(self):
        """Test request execution with retry."""
        processor = BatchProcessor(max_retries=3, initial_backoff=0.01)

        request = APIRequest(id="req1", endpoint="/test", max_retries=3)

        call_count = [0]

        def mock_executor(req):
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Temporary failure")
            return {"success": True}

        result, error = processor.execute_request(request, mock_executor)

        assert result == {"success": True}
        assert error is None
        assert request.retries == 1
        assert call_count[0] == 2

    def test_execute_request_max_retries(self):
        """Test request execution reaching max retries."""
        processor = BatchProcessor(max_retries=2, initial_backoff=0.01)

        request = APIRequest(id="req1", endpoint="/test", max_retries=2)

        def mock_executor(req):
            raise Exception("Persistent failure")

        result, error = processor.execute_request(request, mock_executor)

        assert result is None
        assert error is not None
        assert request.retries == 2

    def test_process_batch(self):
        """Test batch processing."""
        processor = BatchProcessor(batch_size=5, parallel_requests=2)

        requests = [
            APIRequest(id=f"req{i}", endpoint="/test", params={"unique": i}) for i in range(10)
        ]

        def mock_executor(req):
            return {"id": req.id, "success": True}

        result = processor.process_batch(requests, mock_executor)

        assert result.total_requests == 10
        assert result.successful == 10
        assert result.failed == 0

    def test_process_batch_with_failures(self):
        """Test batch processing with some failures."""
        processor = BatchProcessor(batch_size=5, max_retries=1, initial_backoff=0.01)

        requests = [
            APIRequest(id=f"req{i}", endpoint="/test", max_retries=1, params={"unique": i})
            for i in range(10)
        ]

        def mock_executor(req):
            # Fail odd-numbered requests
            req_num = int(req.id.replace("req", ""))
            if req_num % 2 == 1:
                raise Exception("Failure")
            return {"id": req.id, "success": True}

        result = processor.process_batch(requests, mock_executor)

        assert result.total_requests == 10
        assert result.successful == 5
        assert result.failed == 5

    def test_update_rate_limit(self):
        """Test updating rate limit from response."""
        processor = BatchProcessor()

        reset_time = time.time() + 3600
        processor.update_rate_limit(
            "test",
            limit=5000,
            remaining=4500,
            reset_time=reset_time,
        )

        info = processor.get_rate_limit_info("test")
        assert info.limit == 5000
        assert info.remaining == 4500


class TestIntegration:
    """Test batch processing integration."""

    def test_end_to_end_batch_processing(self):
        """Test complete batch processing workflow."""
        processor = BatchProcessor(
            batch_size=3,
            parallel_requests=2,
            max_retries=2,
            initial_backoff=0.01,
        )

        # Create mixed priority requests with unique IDs
        requests = [
            APIRequest(
                id=f"req{i}",
                endpoint="/test",
                priority=RequestPriority.NORMAL,
                params={"unique": i},
            )
            for i in range(10)
        ]

        # Add some high priority with unique params
        requests.extend(
            [
                APIRequest(
                    id="urgent1",
                    endpoint="/test",
                    priority=RequestPriority.HIGH,
                    params={"unique": "u1"},
                ),
                APIRequest(
                    id="urgent2",
                    endpoint="/test",
                    priority=RequestPriority.HIGH,
                    params={"unique": "u2"},
                ),
            ]
        )

        call_count = [0]

        def mock_executor(req):
            call_count[0] += 1
            time.sleep(0.01)  # Simulate API delay
            return {"id": req.id, "data": f"result_{req.id}"}

        result = processor.process_batch(requests, mock_executor)

        assert result.total_requests == 12
        assert result.successful == 12
        assert result.failed == 0
        assert call_count[0] == 12


def test_batch_api_calls_decorator():
    """Test batch API calls decorator."""

    @batch_api_calls(batch_size=5, parallel_requests=2, max_retries=2)
    def fetch_data(request: APIRequest):
        return {"id": request.id, "data": "value"}

    requests = [APIRequest(id=f"req{i}", endpoint="/test", params={"unique": i}) for i in range(10)]

    result = fetch_data(requests)

    assert isinstance(result, BatchResult)
    assert result.total_requests == 10
    assert result.successful == 10


def test_create_batch_processor():
    """Test batch processor factory function."""
    processor = create_batch_processor(
        batch_size=20,
        parallel_requests=10,
        retry_strategy=RetryStrategy.LINEAR,
        max_retries=5,
        initial_backoff=2.0,
        max_backoff=120.0,
        rate_limit_buffer=0.15,
    )

    assert processor.batch_size == 20
    assert processor.parallel_requests == 10
    assert processor.retry_strategy == RetryStrategy.LINEAR
    assert processor.max_retries == 5
    assert processor.initial_backoff == 2.0
    assert processor.max_backoff == 120.0
    assert processor.rate_limiter.buffer_percentage == 0.15


class TestPerformance:
    """Test batch processing performance."""

    def test_parallel_speedup(self):
        """Test parallel processing provides speedup."""
        requests = [
            APIRequest(id=f"req{i}", endpoint="/test", params={"unique": i}) for i in range(20)
        ]

        def slow_executor(req):
            time.sleep(0.01)
            return {"id": req.id}

        # Sequential (parallel_requests=1)
        processor_seq = BatchProcessor(batch_size=20, parallel_requests=1)
        start = time.time()
        result_seq = processor_seq.process_batch(requests, slow_executor)
        time_seq = time.time() - start

        # Parallel (parallel_requests=4)
        processor_par = BatchProcessor(batch_size=20, parallel_requests=4)
        start = time.time()
        result_par = processor_par.process_batch(requests, slow_executor)
        time_par = time.time() - start

        # Parallel should be faster
        assert time_par < time_seq
        assert result_seq.successful == result_par.successful == 20

    def test_deduplication_efficiency(self):
        """Test deduplication reduces API calls."""
        # Create many duplicate requests
        requests = []
        for i in range(100):
            # Only 10 unique requests
            requests.append(APIRequest(id=f"req{i}", endpoint="/test", params={"id": i % 10}))

        call_count = [0]

        def counting_executor(req):
            call_count[0] += 1
            return {"data": "value"}

        processor = BatchProcessor(batch_size=50, parallel_requests=5)
        result = processor.process_batch(requests, counting_executor)

        # Should only make 10 actual API calls due to deduplication
        assert result.deduplicated == 90
        assert call_count[0] == 10
