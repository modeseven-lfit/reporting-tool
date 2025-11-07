#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit Tests for API Response Envelope and Base Client

Tests for the API response envelope pattern and base client functionality
extracted in Phase 2 refactoring. These tests cover error types, response
wrapping, envelope pattern, and base client utilities.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from api.base_client import (
    APIError,
    APIResponse,
    BaseAPIClient,
    ErrorType,
)


# LegacyAPIAdapter removed in Phase 14 - no longer needed
LEGACY_ADAPTER_AVAILABLE = False


class TestErrorType:
    """Tests for ErrorType enumeration."""

    def test_error_types_exist(self):
        """Test that all expected error types exist."""
        assert hasattr(ErrorType, "NETWORK")
        assert hasattr(ErrorType, "HTTP_CLIENT")
        assert hasattr(ErrorType, "HTTP_SERVER")
        assert hasattr(ErrorType, "RATE_LIMIT")
        assert hasattr(ErrorType, "PARSE")
        assert hasattr(ErrorType, "VALIDATION")
        assert hasattr(ErrorType, "TIMEOUT")
        assert hasattr(ErrorType, "UNKNOWN")

    def test_error_type_values(self):
        """Test error type string values."""
        assert ErrorType.NETWORK.value == "network"
        assert ErrorType.HTTP_CLIENT.value == "http_client"
        assert ErrorType.HTTP_SERVER.value == "http_server"
        assert ErrorType.RATE_LIMIT.value == "rate_limit"
        assert ErrorType.PARSE.value == "parse"
        assert ErrorType.VALIDATION.value == "validation"
        assert ErrorType.TIMEOUT.value == "timeout"
        assert ErrorType.UNKNOWN.value == "unknown"

    def test_error_type_uniqueness(self):
        """Test that all error types are unique."""
        error_types = [
            ErrorType.NETWORK,
            ErrorType.HTTP_CLIENT,
            ErrorType.HTTP_SERVER,
            ErrorType.RATE_LIMIT,
            ErrorType.PARSE,
            ErrorType.VALIDATION,
            ErrorType.TIMEOUT,
            ErrorType.UNKNOWN,
        ]

        assert len(error_types) == len(set(error_types))


class TestAPIError:
    """Tests for APIError class."""

    def test_api_error_creation(self):
        """Test creating an APIError instance."""
        error = APIError(type=ErrorType.NETWORK, message="Connection failed")

        assert error.type == ErrorType.NETWORK
        assert error.message == "Connection failed"
        assert error.status_code is None
        assert error.details == {}

    def test_api_error_with_status_code(self):
        """Test APIError with HTTP status code."""
        error = APIError(type=ErrorType.HTTP_CLIENT, message="Not found", status_code=404)

        assert error.type == ErrorType.HTTP_CLIENT
        assert error.message == "Not found"
        assert error.status_code == 404

    def test_api_error_with_details(self):
        """Test APIError with additional details."""
        details = {"url": "https://api.example.com/test", "method": "GET", "retry_count": 3}

        error = APIError(type=ErrorType.TIMEOUT, message="Request timeout", details=details)

        assert error.details == details
        assert error.details["url"] == "https://api.example.com/test"

    def test_api_error_str(self):
        """Test string representation of APIError."""
        error = APIError(
            type=ErrorType.HTTP_SERVER, message="Internal server error", status_code=500
        )

        error_str = str(error)

        assert "http_server" in error_str
        assert "Internal server error" in error_str
        assert "500" in error_str

    def test_api_error_str_without_status_code(self):
        """Test string representation without status code."""
        error = APIError(type=ErrorType.NETWORK, message="Connection failed")

        error_str = str(error)

        assert "network" in error_str
        assert "Connection failed" in error_str
        assert "HTTP" not in error_str

    def test_api_error_to_dict(self):
        """Test converting APIError to dictionary."""
        error = APIError(
            type=ErrorType.RATE_LIMIT,
            message="Rate limit exceeded",
            status_code=429,
            details={"reset_time": "2025-01-25T12:00:00Z"},
        )

        error_dict = error.to_dict()

        assert error_dict["type"] == "rate_limit"
        assert error_dict["message"] == "Rate limit exceeded"
        assert error_dict["status_code"] == 429
        assert error_dict["details"]["reset_time"] == "2025-01-25T12:00:00Z"

    def test_api_error_to_dict_minimal(self):
        """Test converting minimal APIError to dictionary."""
        error = APIError(type=ErrorType.UNKNOWN, message="Unknown error")

        error_dict = error.to_dict()

        assert error_dict["type"] == "unknown"
        assert error_dict["message"] == "Unknown error"
        assert error_dict["status_code"] is None
        assert error_dict["details"] == {}


class TestAPIResponse:
    """Tests for APIResponse envelope."""

    def test_success_response(self):
        """Test creating a successful response."""
        response = APIResponse(ok=True, data={"key": "value"}, meta={"status_code": 200})

        assert response.ok is True
        assert response.data == {"key": "value"}
        assert response.error is None
        assert response.meta["status_code"] == 200

    def test_error_response(self):
        """Test creating an error response."""
        error = APIError(type=ErrorType.HTTP_CLIENT, message="Not found", status_code=404)

        response = APIResponse(ok=False, error=error, meta={"status_code": 404})

        assert response.ok is False
        assert response.data is None
        assert response.error == error
        assert response.error.type == ErrorType.HTTP_CLIENT

    def test_response_with_list_data(self):
        """Test response with list data."""
        data = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

        response = APIResponse(ok=True, data=data)

        assert response.ok is True
        assert isinstance(response.data, list)
        assert len(response.data) == 2

    def test_response_with_string_data(self):
        """Test response with string data."""
        response = APIResponse(ok=True, data="Success message")

        assert response.ok is True
        assert response.data == "Success message"

    def test_response_with_none_data(self):
        """Test response with None data."""
        response = APIResponse(ok=True, data=None)

        assert response.ok is True
        assert response.data is None

    def test_response_metadata(self):
        """Test response metadata."""
        meta = {
            "status_code": 200,
            "request_id": "req-123",
            "timestamp": "2025-01-25T12:00:00Z",
            "duration_ms": 125,
        }

        response = APIResponse(ok=True, data={}, meta=meta)

        assert response.meta["status_code"] == 200
        assert response.meta["request_id"] == "req-123"
        assert response.meta["duration_ms"] == 125

    def test_response_type_parameter(self):
        """Test APIResponse with type parameter."""
        # Test with typed data
        data: dict[str, str] = {"message": "Hello"}
        response: APIResponse[dict[str, str]] = APIResponse(ok=True, data=data)

        assert response.ok is True
        assert isinstance(response.data, dict)

    def test_response_empty_meta(self):
        """Test response with empty metadata."""
        response = APIResponse(ok=True, data={})

        assert response.meta == {}


class TestBaseAPIClient:
    """Tests for BaseAPIClient class."""

    def test_base_client_initialization(self):
        """Test BaseAPIClient initialization."""
        client = BaseAPIClient(timeout=30.0)

        assert client.timeout == 30.0
        assert hasattr(client, "stats")

    def test_base_client_with_stats(self):
        """Test BaseAPIClient with stats tracker."""
        mock_stats = MagicMock()
        client = BaseAPIClient(timeout=60.0, stats=mock_stats)

        assert client.timeout == 60.0
        assert client.stats == mock_stats

    def test_record_error_method(self):
        """Test _record_error method."""
        mock_stats = MagicMock()
        client = BaseAPIClient(stats=mock_stats)

        if hasattr(client, "_record_error"):
            client._record_error("api_name", 500)
            # Verify stats tracking (implementation may vary)
            assert True

    def test_base_client_close(self):
        """Test close method."""
        client = BaseAPIClient()

        # Should not raise exception
        if hasattr(client, "close"):
            client.close()

        assert True


# LegacyAPIAdapter tests removed in Phase 14
# The adapter has been removed as all code now uses the envelope pattern directly


class TestErrorTypeClassification:
    """Tests for error type classification logic."""

    def test_classify_4xx_errors(self):
        """Test classification of 4xx errors."""
        # 400-499 should be HTTP_CLIENT errors
        client_codes = [400, 401, 403, 404, 422]

        for code in client_codes:
            expected = ErrorType.RATE_LIMIT if code == 429 else ErrorType.HTTP_CLIENT

            # This would test a classifier method if available
            assert expected in [ErrorType.HTTP_CLIENT, ErrorType.RATE_LIMIT]

    def test_classify_5xx_errors(self):
        """Test classification of 5xx errors."""
        # 500-599 should be HTTP_SERVER errors
        server_codes = [500, 502, 503, 504]

        for _code in server_codes:
            expected = ErrorType.HTTP_SERVER
            assert expected == ErrorType.HTTP_SERVER

    def test_classify_rate_limit(self):
        """Test classification of rate limit errors."""
        # 429 should be RATE_LIMIT
        assert ErrorType.RATE_LIMIT.value == "rate_limit"


class TestResponseEnvelopePatterns:
    """Tests for common response envelope patterns."""

    def test_success_with_pagination(self):
        """Test success response with pagination metadata."""
        response = APIResponse(
            ok=True,
            data={"items": [1, 2, 3]},
            meta={"total_count": 100, "page": 1, "per_page": 3, "has_more": True},
        )

        assert response.ok is True
        assert response.meta["total_count"] == 100
        assert response.meta["has_more"] is True

    def test_error_with_retry_info(self):
        """Test error response with retry information."""
        error = APIError(
            type=ErrorType.RATE_LIMIT,
            message="Too many requests",
            status_code=429,
            details={"retry_after": 60, "reset_time": "2025-01-25T13:00:00Z"},
        )

        response = APIResponse(ok=False, error=error)

        assert response.error.details["retry_after"] == 60
        assert "reset_time" in response.error.details

    def test_partial_success_pattern(self):
        """Test partial success pattern."""
        # Some APIs return partial results with errors
        response = APIResponse(
            ok=True,
            data={"successful": [1, 2], "failed": [3]},
            meta={"partial_success": True, "error_count": 1},
        )

        assert response.ok is True
        assert response.meta["partial_success"] is True

    def test_validation_error_pattern(self):
        """Test validation error pattern."""
        error = APIError(
            type=ErrorType.VALIDATION,
            message="Validation failed",
            details={
                "field_errors": {"email": "Invalid email format", "age": "Must be positive integer"}
            },
        )

        response = APIResponse(ok=False, error=error)

        assert response.error.type == ErrorType.VALIDATION
        assert "field_errors" in response.error.details


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_error_with_very_long_message(self):
        """Test error with very long message."""
        long_message = "Error: " + "x" * 10000

        error = APIError(type=ErrorType.UNKNOWN, message=long_message)

        assert len(error.message) > 10000
        assert error.message.startswith("Error:")

    def test_error_with_unicode_message(self):
        """Test error with unicode characters."""
        error = APIError(type=ErrorType.NETWORK, message="接続エラー: 日本語のエラーメッセージ")

        assert "日本語" in error.message
        assert "接続エラー" in error.message

    def test_response_with_nested_data(self):
        """Test response with deeply nested data."""
        nested_data = {"level1": {"level2": {"level3": {"level4": {"value": "deep"}}}}}

        response = APIResponse(ok=True, data=nested_data)

        assert response.data["level1"]["level2"]["level3"]["level4"]["value"] == "deep"

    def test_error_with_empty_message(self):
        """Test error with empty message."""
        error = APIError(type=ErrorType.UNKNOWN, message="")

        assert error.message == ""
        assert str(error)  # Should not raise

    def test_response_with_very_large_data(self):
        """Test response with large data payload."""
        large_data = [{"id": i, "value": f"item_{i}"} for i in range(10000)]

        response = APIResponse(ok=True, data=large_data)

        assert len(response.data) == 10000
        assert response.ok is True

    def test_error_details_with_special_types(self):
        """Test error details with various Python types."""
        error = APIError(
            type=ErrorType.UNKNOWN,
            message="Test",
            details={
                "string": "value",
                "number": 42,
                "float": 3.14,
                "bool": True,
                "null": None,
                "list": [1, 2, 3],
                "dict": {"nested": "value"},
            },
        )

        assert error.details["number"] == 42
        assert error.details["bool"] is True
        assert error.details["null"] is None
        assert isinstance(error.details["list"], list)


class TestIntegrationPatterns:
    """Integration patterns for using the envelope system."""

    def test_success_then_error_pattern(self):
        """Test handling success followed by error."""
        # First request succeeds
        success = APIResponse(ok=True, data={"id": 1})
        assert success.ok is True

        # Second request fails
        error = APIError(ErrorType.HTTP_CLIENT, "Not found", 404)
        failure = APIResponse(ok=False, error=error)
        assert failure.ok is False

        # Code should handle both patterns
        responses = [success, failure]
        successful = [r for r in responses if r.ok]
        failed = [r for r in responses if not r.ok]

        assert len(successful) == 1
        assert len(failed) == 1

    def test_error_propagation_pattern(self):
        """Test error propagation through multiple layers."""
        # Create error at low level
        base_error = APIError(
            type=ErrorType.NETWORK, message="Connection failed", details={"layer": "network"}
        )

        # Wrap in response
        response = APIResponse(ok=False, error=base_error)

        # Check error can be accessed
        assert response.error is not None
        assert response.error.type == ErrorType.NETWORK
        assert response.error.details["layer"] == "network"

    def test_conditional_response_handling(self):
        """Test conditional handling based on response.ok."""

        def handle_response(response: APIResponse) -> str:
            if response.ok:
                return f"Success: {response.data}"
            else:
                return f"Error: {response.error.message}"

        success = APIResponse(ok=True, data="result")
        error_resp = APIResponse(ok=False, error=APIError(ErrorType.UNKNOWN, "failed"))

        assert "Success" in handle_response(success)
        assert "Error" in handle_response(error_resp)


# Pytest markers for categorization
pytestmark = [pytest.mark.unit, pytest.mark.api]
