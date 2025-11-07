# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for base API client functionality.

Tests cover:
- Response envelope pattern
- Error classification
- Retry logic with exponential backoff
- Statistics tracking
- Context manager behavior
"""

import logging
from unittest.mock import Mock

import pytest
from src.api.base_client import (
    APIError,
    APIResponse,
    BaseAPIClient,
    ErrorType,
)


# ============================================================================
# Test APIError
# ============================================================================


class TestAPIError:
    """Test APIError data class."""

    def test_error_creation_minimal(self):
        """Test creating error with minimal fields."""
        error = APIError(type=ErrorType.NETWORK, message="Connection failed")
        assert error.type == ErrorType.NETWORK
        assert error.message == "Connection failed"
        assert error.status_code is None
        assert error.details == {}

    def test_error_creation_full(self):
        """Test creating error with all fields."""
        error = APIError(
            type=ErrorType.HTTP_CLIENT,
            message="Bad request",
            status_code=400,
            details={"field": "email", "issue": "invalid"},
        )
        assert error.type == ErrorType.HTTP_CLIENT
        assert error.message == "Bad request"
        assert error.status_code == 400
        assert error.details == {"field": "email", "issue": "invalid"}

    def test_error_str_without_status(self):
        """Test string representation without status code."""
        error = APIError(ErrorType.NETWORK, "Connection timeout")
        assert str(error) == "network: Connection timeout"

    def test_error_str_with_status(self):
        """Test string representation with status code."""
        error = APIError(ErrorType.HTTP_CLIENT, "Not found", status_code=404)
        assert str(error) == "http_client: Not found (HTTP 404)"

    def test_error_to_dict(self):
        """Test conversion to dictionary."""
        error = APIError(
            type=ErrorType.RATE_LIMIT,
            message="Rate limit exceeded",
            status_code=429,
            details={"retry_after": 60},
        )
        result = error.to_dict()
        assert result == {
            "type": "rate_limit",
            "message": "Rate limit exceeded",
            "status_code": 429,
            "details": {"retry_after": 60},
        }

    def test_all_error_types(self):
        """Test all error type variants."""
        types = [
            ErrorType.NETWORK,
            ErrorType.HTTP_CLIENT,
            ErrorType.HTTP_SERVER,
            ErrorType.RATE_LIMIT,
            ErrorType.PARSE,
            ErrorType.VALIDATION,
            ErrorType.TIMEOUT,
            ErrorType.UNKNOWN,
        ]
        for error_type in types:
            error = APIError(error_type, "test message")
            assert error.type == error_type


# ============================================================================
# Test APIResponse
# ============================================================================


class TestAPIResponse:
    """Test APIResponse envelope pattern."""

    def test_success_response_creation(self):
        """Test creating a success response."""
        response = APIResponse(ok=True, data={"result": "success"}, meta={"status_code": 200})
        assert response.ok is True
        assert response.data == {"result": "success"}
        assert response.error is None
        assert response.meta == {"status_code": 200}

    def test_failure_response_creation(self):
        """Test creating a failure response."""
        error = APIError(ErrorType.HTTP_SERVER, "Server error", 500)
        response = APIResponse(ok=False, error=error, meta={"status_code": 500})
        assert response.ok is False
        assert response.data is None
        assert response.error == error
        assert response.meta == {"status_code": 500}

    def test_success_factory_method(self):
        """Test success() factory method."""
        data = {"items": [1, 2, 3]}
        response = APIResponse.success(data, {"count": 3})
        assert response.ok is True
        assert response.data == data
        assert response.error is None
        assert response.meta == {"count": 3}

    def test_success_factory_without_meta(self):
        """Test success() factory without metadata."""
        response = APIResponse.success({"value": 42})
        assert response.ok is True
        assert response.data == {"value": 42}
        assert response.meta == {}

    def test_failure_factory_method(self):
        """Test failure() factory method."""
        error = APIError(ErrorType.TIMEOUT, "Request timeout")
        response = APIResponse.failure(error, {"duration": 30.5})
        assert response.ok is False
        assert response.data is None
        assert response.error == error
        assert response.meta == {"duration": 30.5}

    def test_failure_factory_without_meta(self):
        """Test failure() factory without metadata."""
        error = APIError(ErrorType.NETWORK, "Connection failed")
        response = APIResponse.failure(error)
        assert response.ok is False
        assert response.error == error
        assert response.meta == {}

    def test_validation_success_cannot_have_error(self):
        """Test that success response cannot have error field."""
        error = APIError(ErrorType.UNKNOWN, "test")
        with pytest.raises(ValueError, match="Success response cannot have error"):
            APIResponse(ok=True, data={}, error=error)

    def test_validation_failure_must_have_error(self):
        """Test that failure response must have error field."""
        with pytest.raises(ValueError, match="Error response must have error"):
            APIResponse(ok=False, data={})

    def test_to_dict_success(self):
        """Test to_dict() for success response."""
        response = APIResponse.success({"count": 5}, {"request_id": "abc123"})
        result = response.to_dict()
        assert result == {"ok": True, "data": {"count": 5}, "meta": {"request_id": "abc123"}}

    def test_to_dict_failure(self):
        """Test to_dict() for failure response."""
        error = APIError(ErrorType.HTTP_CLIENT, "Bad request", 400)
        response = APIResponse.failure(error, {"request_id": "xyz789"})
        result = response.to_dict()
        assert result == {
            "ok": False,
            "error": {
                "type": "http_client",
                "message": "Bad request",
                "status_code": 400,
                "details": {},
            },
            "meta": {"request_id": "xyz789"},
        }

    def test_generic_type_hint(self):
        """Test that type hints work correctly."""
        # This is more of a type checker test, but we can verify runtime behavior
        response: APIResponse[list] = APIResponse.success([1, 2, 3])
        assert isinstance(response.data, list)

        response2: APIResponse[dict] = APIResponse.success({"key": "value"})
        assert isinstance(response2.data, dict)


# ============================================================================
# Test BaseAPIClient
# ============================================================================


class TestBaseAPIClientInitialization:
    """Test BaseAPIClient initialization and configuration."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        client = BaseAPIClient()
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.retry_delay == 1.0
        assert client.stats is None
        assert client.logger is not None

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        mock_stats = Mock()
        mock_logger = Mock()
        client = BaseAPIClient(
            timeout=60.0, max_retries=5, retry_delay=2.0, stats=mock_stats, logger=mock_logger
        )
        assert client.timeout == 60.0
        assert client.max_retries == 5
        assert client.retry_delay == 2.0
        assert client.stats == mock_stats
        assert client.logger == mock_logger

    def test_logger_creation(self):
        """Test that logger is created if not provided."""
        client = BaseAPIClient()
        assert isinstance(client.logger, logging.Logger)
        assert "BaseAPIClient" in client.logger.name


class TestErrorClassification:
    """Test HTTP error classification."""

    def test_classify_rate_limit(self):
        """Test classification of rate limit (429)."""
        client = BaseAPIClient()
        error_type = client._classify_http_error(429)
        assert error_type == ErrorType.RATE_LIMIT

    def test_classify_client_errors(self):
        """Test classification of 4xx errors."""
        client = BaseAPIClient()
        for code in [400, 401, 403, 404, 422]:
            error_type = client._classify_http_error(code)
            assert error_type == ErrorType.HTTP_CLIENT

    def test_classify_server_errors(self):
        """Test classification of 5xx errors."""
        client = BaseAPIClient()
        for code in [500, 502, 503, 504]:
            error_type = client._classify_http_error(code)
            assert error_type == ErrorType.HTTP_SERVER

    def test_classify_unknown(self):
        """Test classification of non-standard codes."""
        client = BaseAPIClient()
        for code in [100, 200, 300, 600]:
            error_type = client._classify_http_error(code)
            assert error_type == ErrorType.UNKNOWN


class TestRetryLogic:
    """Test retry decision logic."""

    def test_should_not_retry_client_errors(self):
        """Test that client errors are not retried."""
        client = BaseAPIClient()
        assert not client._should_retry(ErrorType.HTTP_CLIENT, 0)
        assert not client._should_retry(ErrorType.HTTP_CLIENT, 1)
        assert not client._should_retry(ErrorType.HTTP_CLIENT, 2)

    def test_should_retry_rate_limits(self):
        """Test that rate limits are retried."""
        client = BaseAPIClient()
        assert client._should_retry(ErrorType.RATE_LIMIT, 0)
        assert client._should_retry(ErrorType.RATE_LIMIT, 1)
        assert client._should_retry(ErrorType.RATE_LIMIT, 2)

    def test_should_retry_server_errors(self):
        """Test that server errors are retried."""
        client = BaseAPIClient()
        assert client._should_retry(ErrorType.HTTP_SERVER, 0)
        assert client._should_retry(ErrorType.HTTP_SERVER, 1)
        assert client._should_retry(ErrorType.HTTP_SERVER, 2)

    def test_should_retry_network_errors(self):
        """Test that network errors are retried."""
        client = BaseAPIClient()
        assert client._should_retry(ErrorType.NETWORK, 0)
        assert client._should_retry(ErrorType.NETWORK, 1)

    def test_should_retry_timeouts(self):
        """Test that timeouts are retried."""
        client = BaseAPIClient()
        assert client._should_retry(ErrorType.TIMEOUT, 0)
        assert client._should_retry(ErrorType.TIMEOUT, 1)

    def test_should_not_retry_after_max_attempts(self):
        """Test that retries stop after max attempts."""
        client = BaseAPIClient(max_retries=3)
        # Within limit
        assert client._should_retry(ErrorType.HTTP_SERVER, 0)
        assert client._should_retry(ErrorType.HTTP_SERVER, 1)
        assert client._should_retry(ErrorType.HTTP_SERVER, 2)
        # At limit
        assert not client._should_retry(ErrorType.HTTP_SERVER, 3)
        # Beyond limit
        assert not client._should_retry(ErrorType.HTTP_SERVER, 4)

    def test_max_retries_configuration(self):
        """Test different max_retries configurations."""
        client1 = BaseAPIClient(max_retries=1)
        assert client1._should_retry(ErrorType.NETWORK, 0)
        assert not client1._should_retry(ErrorType.NETWORK, 1)

        client2 = BaseAPIClient(max_retries=5)
        assert client2._should_retry(ErrorType.NETWORK, 4)
        assert not client2._should_retry(ErrorType.NETWORK, 5)


class TestRetryDelay:
    """Test exponential backoff calculation."""

    def test_exponential_backoff_default(self):
        """Test exponential backoff with default delay."""
        client = BaseAPIClient(retry_delay=1.0)
        assert client._calculate_retry_delay(0) == 1.0  # 1 * 2^0
        assert client._calculate_retry_delay(1) == 2.0  # 1 * 2^1
        assert client._calculate_retry_delay(2) == 4.0  # 1 * 2^2
        assert client._calculate_retry_delay(3) == 8.0  # 1 * 2^3

    def test_exponential_backoff_custom_delay(self):
        """Test exponential backoff with custom initial delay."""
        client = BaseAPIClient(retry_delay=0.5)
        assert client._calculate_retry_delay(0) == 0.5  # 0.5 * 2^0
        assert client._calculate_retry_delay(1) == 1.0  # 0.5 * 2^1
        assert client._calculate_retry_delay(2) == 2.0  # 0.5 * 2^2

    def test_exponential_backoff_progression(self):
        """Test that delay increases exponentially."""
        client = BaseAPIClient(retry_delay=1.0)
        delays = [client._calculate_retry_delay(i) for i in range(5)]
        # Each delay should be double the previous
        for i in range(1, len(delays)):
            assert delays[i] == delays[i - 1] * 2


class TestStatisticsTracking:
    """Test statistics recording."""

    def test_record_success(self):
        """Test recording successful API call."""
        mock_stats = Mock()
        client = BaseAPIClient(stats=mock_stats)
        client._record_success("test_api")
        mock_stats.record_success.assert_called_once_with("test_api")

    def test_record_success_without_stats(self):
        """Test that recording success without stats doesn't error."""
        client = BaseAPIClient(stats=None)
        # Should not raise
        client._record_success("test_api")

    def test_record_error(self):
        """Test recording API error."""
        mock_stats = Mock()
        client = BaseAPIClient(stats=mock_stats)
        client._record_error("test_api", 500)
        mock_stats.record_error.assert_called_once_with("test_api", 500)

    def test_record_error_without_stats(self):
        """Test that recording error without stats doesn't error."""
        client = BaseAPIClient(stats=None)
        # Should not raise
        client._record_error("test_api", 404)

    def test_record_exception(self):
        """Test recording API exception."""
        mock_stats = Mock()
        client = BaseAPIClient(stats=mock_stats)
        client._record_exception("test_api", "timeout")
        mock_stats.record_exception.assert_called_once_with("test_api", "timeout")

    def test_record_exception_default_type(self):
        """Test recording exception with default type."""
        mock_stats = Mock()
        client = BaseAPIClient(stats=mock_stats)
        client._record_exception("test_api")
        mock_stats.record_exception.assert_called_once_with("test_api", "exception")

    def test_record_exception_without_stats(self):
        """Test that recording exception without stats doesn't error."""
        client = BaseAPIClient(stats=None)
        # Should not raise
        client._record_exception("test_api", "network")


class TestContextManager:
    """Test context manager protocol."""

    def test_context_manager_enter(self):
        """Test __enter__ returns self."""
        client = BaseAPIClient()
        with client as ctx:
            assert ctx is client

    def test_context_manager_exit_calls_close(self):
        """Test __exit__ calls close()."""
        client = BaseAPIClient()
        client.close = Mock()
        with client:
            pass
        client.close.assert_called_once()

    def test_context_manager_exit_with_exception(self):
        """Test __exit__ is called even with exception."""
        client = BaseAPIClient()
        client.close = Mock()
        try:
            with client:
                raise ValueError("test error")
        except ValueError:
            pass
        client.close.assert_called_once()

    def test_close_method_default(self):
        """Test that default close() method doesn't error."""
        client = BaseAPIClient()
        # Should not raise
        client.close()


# ============================================================================
# Integration Tests
# ============================================================================


class TestBaseAPIClientIntegration:
    """Integration tests for complete client behavior."""

    def test_complete_retry_scenario(self):
        """Test complete retry scenario with backoff."""
        mock_stats = Mock()
        client = BaseAPIClient(max_retries=3, retry_delay=0.1, stats=mock_stats)

        # Simulate retryable error
        error_type = ErrorType.HTTP_SERVER

        # Attempt 0 - should retry
        assert client._should_retry(error_type, 0)
        delay0 = client._calculate_retry_delay(0)
        assert delay0 == 0.1

        # Attempt 1 - should retry with increased delay
        assert client._should_retry(error_type, 1)
        delay1 = client._calculate_retry_delay(1)
        assert delay1 == 0.2

        # Attempt 2 - should retry with further increased delay
        assert client._should_retry(error_type, 2)
        delay2 = client._calculate_retry_delay(2)
        assert delay2 == 0.4

        # Attempt 3 - should NOT retry (at max_retries)
        assert not client._should_retry(error_type, 3)

    def test_error_type_to_retry_decision(self):
        """Test mapping from error types to retry decisions."""
        client = BaseAPIClient(max_retries=3)

        # Should retry
        retryable = [
            ErrorType.RATE_LIMIT,
            ErrorType.HTTP_SERVER,
            ErrorType.NETWORK,
            ErrorType.TIMEOUT,
        ]
        for error_type in retryable:
            assert client._should_retry(error_type, 0), f"{error_type} should be retryable"

        # Should NOT retry
        non_retryable = [
            ErrorType.HTTP_CLIENT,
        ]
        for error_type in non_retryable:
            assert not client._should_retry(error_type, 0), f"{error_type} should not be retryable"

    def test_stats_tracking_lifecycle(self):
        """Test stats tracking through a complete request lifecycle."""
        mock_stats = Mock()
        client = BaseAPIClient(stats=mock_stats)

        # Simulate successful request
        client._record_success("api_call")
        assert mock_stats.record_success.call_count == 1

        # Simulate failed request
        client._record_error("api_call", 500)
        assert mock_stats.record_error.call_count == 1

        # Simulate exception
        client._record_exception("api_call", "network")
        assert mock_stats.record_exception.call_count == 1
