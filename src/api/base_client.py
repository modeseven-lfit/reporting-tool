# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Base API Client

Provides base classes and response envelope pattern for all API clients.
This standardizes error handling, retries, and observability across all
external API integrations.

Extracted from generate_reports.py as part of Phase 2 refactoring.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, TypeVar, Generic
from enum import Enum


class ErrorType(Enum):
    """Classification of API errors."""

    NETWORK = "network"              # Connection/timeout errors
    HTTP_CLIENT = "http_client"      # 4xx errors (bad request, auth, etc.)
    HTTP_SERVER = "http_server"      # 5xx errors (server errors)
    RATE_LIMIT = "rate_limit"        # Rate limiting (429)
    PARSE = "parse"                  # Response parsing errors
    VALIDATION = "validation"        # Response validation errors
    TIMEOUT = "timeout"              # Request timeout
    UNKNOWN = "unknown"              # Uncategorized errors


@dataclass
class APIError:
    """
    Structured API error information.

    Provides detailed error context for debugging and observability.
    """

    type: ErrorType
    message: str
    status_code: Optional[int] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Human-readable error description."""
        parts = [f"{self.type.value}: {self.message}"]
        if self.status_code:
            parts.append(f"(HTTP {self.status_code})")
        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details
        }


T = TypeVar('T')


@dataclass
class APIResponse(Generic[T]):
    """
    Standardized API response envelope.

    Wraps all API responses in a consistent structure that clearly
    distinguishes success from failure and provides rich error context.

    Type Parameters:
        T: The type of the response data payload

    Attributes:
        ok: True if the request succeeded, False otherwise
        data: The response payload (None if error)
        error: Error information (None if success)
        meta: Additional metadata (status code, timing, etc.)

    Examples:
        >>> # Success response
        >>> response = APIResponse(ok=True, data={"repo": "test"}, meta={"status_code": 200})
        >>> if response.ok:
        ...     print(response.data)

        >>> # Error response
        >>> error = APIError(ErrorType.HTTP_CLIENT, "Not found", status_code=404)
        >>> response = APIResponse(ok=False, error=error, meta={"status_code": 404})
        >>> if not response.ok:
        ...     print(response.error.message)
    """

    ok: bool
    data: Optional[T] = None
    error: Optional[APIError] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate response envelope invariants."""
        if self.ok and self.error is not None:
            raise ValueError("Success response cannot have error")
        if not self.ok and self.error is None:
            raise ValueError("Error response must have error")

    @classmethod
    def success(cls, data: T, meta: Optional[Dict[str, Any]] = None) -> 'APIResponse[T]':
        """
        Create a success response.

        Args:
            data: Response payload
            meta: Optional metadata

        Returns:
            Success APIResponse
        """
        return cls(ok=True, data=data, meta=meta or {})

    @classmethod
    def failure(cls, error: APIError, meta: Optional[Dict[str, Any]] = None) -> 'APIResponse[T]':
        """
        Create a failure response.

        Args:
            error: Error information
            meta: Optional metadata

        Returns:
            Failure APIResponse
        """
        return cls(ok=False, error=error, meta=meta or {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "ok": self.ok,
            "meta": self.meta
        }
        if self.ok:
            result["data"] = self.data
        else:
            result["error"] = self.error.to_dict() if self.error else None
        return result


class BaseAPIClient:
    """
    Base class for all API clients.

    Provides common functionality:
    - Timeout handling
    - Retry logic with exponential backoff
    - Statistics tracking
    - Logging
    - Response envelope wrapping

    Subclasses should override specific API methods and use the helper
    methods provided here for consistent behavior.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        stats: Any = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize base API client.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (exponential backoff)
            stats: Statistics tracker object
            logger: Logger instance (creates one if not provided)
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.stats = stats
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def _classify_http_error(self, status_code: int) -> ErrorType:
        """
        Classify HTTP status code into error type.

        Args:
            status_code: HTTP status code

        Returns:
            Appropriate ErrorType
        """
        if status_code == 429:
            return ErrorType.RATE_LIMIT
        elif 400 <= status_code < 500:
            return ErrorType.HTTP_CLIENT
        elif 500 <= status_code < 600:
            return ErrorType.HTTP_SERVER
        else:
            return ErrorType.UNKNOWN

    def _should_retry(self, error_type: ErrorType, attempt: int) -> bool:
        """
        Determine if a request should be retried.

        Args:
            error_type: Type of error encountered
            attempt: Current attempt number (0-based)

        Returns:
            True if should retry, False otherwise
        """
        # Don't retry client errors (except rate limits)
        if error_type == ErrorType.HTTP_CLIENT:
            return False

        # Retry rate limits, server errors, network errors, timeouts
        if error_type in (ErrorType.RATE_LIMIT, ErrorType.HTTP_SERVER,
                         ErrorType.NETWORK, ErrorType.TIMEOUT):
            return attempt < self.max_retries

        return False

    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        # Exponential backoff: delay * 2^attempt
        # e.g., 1s, 2s, 4s, 8s...
        return float(self.retry_delay * (2 ** attempt))

    def _record_success(self, api_name: str):
        """Record successful API call in statistics."""
        if self.stats:
            self.stats.record_success(api_name)

    def _record_error(self, api_name: str, status_code: int):
        """Record API error in statistics."""
        if self.stats:
            self.stats.record_error(api_name, status_code)

    def _record_exception(self, api_name: str, error_type: str = "exception"):
        """Record API exception in statistics."""
        if self.stats:
            self.stats.record_exception(api_name, error_type)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False

    def close(self):
        """
        Close the API client and clean up resources.

        Subclasses should override if they have resources to clean up.
        """
        pass
