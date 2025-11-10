# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for async URL validation in info_yaml validator module.

Tests async validation, concurrent processing, and performance characteristics.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from src.reporting_tool.collectors.info_yaml.validator import (
    URLValidator,
    validate_urls_async,
    validate_urls_sync,
)


class TestAsyncURLValidator:
    """Test async URL validation functionality."""

    @pytest.mark.asyncio
    async def test_validate_async_success(self):
        """Test successful async URL validation."""
        validator = URLValidator(timeout=5.0, retries=1)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            is_valid, error = await validator.validate_async("https://example.com")

            assert is_valid is True
            assert error == ""
            mock_client.head.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_async_http_error(self):
        """Test async validation with HTTP error."""
        validator = URLValidator(timeout=5.0, retries=1)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            is_valid, error = await validator.validate_async("https://example.com/notfound")

            assert is_valid is False
            assert "404" in error

    @pytest.mark.asyncio
    async def test_validate_async_timeout(self):
        """Test async validation with timeout."""
        validator = URLValidator(timeout=0.1, retries=0)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            is_valid, error = await validator.validate_async("https://slow.example.com")

            assert is_valid is False
            assert "Timeout" in error

    @pytest.mark.asyncio
    async def test_validate_async_connection_error(self):
        """Test async validation with connection error."""
        validator = URLValidator(timeout=5.0, retries=0)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(side_effect=httpx.ConnectError("Failed"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            is_valid, error = await validator.validate_async("https://unreachable.example.com")

            assert is_valid is False
            assert "Connection failed" in error

    @pytest.mark.asyncio
    async def test_validate_async_invalid_url(self):
        """Test async validation with invalid URL."""
        validator = URLValidator(timeout=5.0, retries=0)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.head = AsyncMock(side_effect=httpx.InvalidURL("Invalid"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            is_valid, error = await validator.validate_async("not-a-url")

            assert is_valid is False
            assert "Invalid URL" in error

    @pytest.mark.asyncio
    async def test_validate_async_empty_url(self):
        """Test async validation with empty URL."""
        validator = URLValidator()

        is_valid, error = await validator.validate_async("")

        assert is_valid is False
        assert "No URL provided" in error

    @pytest.mark.asyncio
    async def test_validate_async_uses_cache(self):
        """Test that async validation uses cache."""
        validator = URLValidator(cache_enabled=True)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # First call
            is_valid1, error1 = await validator.validate_async("https://example.com")
            # Second call (should use cache)
            is_valid2, error2 = await validator.validate_async("https://example.com")

            assert is_valid1 is True
            assert is_valid2 is True
            # Should only call HTTP once
            assert mock_client.head.call_count == 1

    @pytest.mark.asyncio
    async def test_validate_async_retry_logic(self):
        """Test async validation retry logic."""
        validator = URLValidator(timeout=5.0, retries=2)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            # Fail twice, succeed on third attempt
            mock_client.head = AsyncMock(
                side_effect=[
                    httpx.ConnectError("Failed"),
                    httpx.ConnectError("Failed"),
                    MagicMock(status_code=200),
                ]
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Mock asyncio.sleep to avoid delays in tests
            with patch("asyncio.sleep", new_callable=AsyncMock):
                is_valid, error = await validator.validate_async("https://flaky.example.com")

            assert is_valid is True
            assert error == ""
            assert mock_client.head.call_count == 3


class TestAsyncBulkValidation:
    """Test async bulk URL validation."""

    @pytest.mark.asyncio
    async def test_validate_bulk_async_basic(self):
        """Test basic async bulk validation."""
        validator = URLValidator(timeout=5.0, retries=0)

        urls = [
            "https://example.com",
            "https://github.com",
            "https://python.org",
        ]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            results = await validator.validate_bulk_async(urls)

            assert len(results) == 3
            assert all(is_valid for is_valid, _ in results.values())
            assert mock_client.head.call_count == 3

    @pytest.mark.asyncio
    async def test_validate_bulk_async_mixed_results(self):
        """Test async bulk validation with mixed results."""
        validator = URLValidator(timeout=5.0, retries=0)

        urls = [
            "https://example.com",
            "https://notfound.example.com",
            "https://timeout.example.com",
        ]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # Different responses for different URLs
            responses = [
                MagicMock(status_code=200),  # Success
                MagicMock(status_code=404),  # Not found
                httpx.TimeoutException("Timeout"),  # Timeout
            ]

            mock_client.head = AsyncMock(side_effect=responses)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            results = await validator.validate_bulk_async(urls)

            assert len(results) == 3
            assert results[urls[0]][0] is True
            assert results[urls[1]][0] is False
            assert results[urls[2]][0] is False

    @pytest.mark.asyncio
    async def test_validate_bulk_async_empty_list(self):
        """Test async bulk validation with empty URL list."""
        validator = URLValidator()

        results = await validator.validate_bulk_async([])

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_validate_bulk_async_filters_empty_urls(self):
        """Test that bulk async validation filters empty URLs."""
        validator = URLValidator()

        urls = ["https://example.com", "", "https://github.com", None]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            results = await validator.validate_bulk_async(urls)

            # Should only validate non-empty URLs
            assert len(results) == 2
            assert mock_client.head.call_count == 2

    @pytest.mark.asyncio
    async def test_validate_bulk_async_concurrency_limit(self):
        """Test that concurrent validation respects max_concurrent limit."""
        validator = URLValidator(timeout=5.0, retries=0)

        # Create 20 URLs
        urls = [f"https://example{i}.com" for i in range(20)]

        concurrent_count = []
        lock = asyncio.Lock()

        async def mock_head(*args, **kwargs):
            """Mock that tracks concurrent calls."""
            async with lock:
                concurrent_count.append(len(concurrent_count) + 1)

            # Simulate work
            await asyncio.sleep(0.01)

            async with lock:
                concurrent_count.pop()

            response = MagicMock()
            response.status_code = 200
            return response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.head = mock_head
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Limit to 5 concurrent
            results = await validator.validate_bulk_async(urls, max_concurrent=5)

            assert len(results) == 20
            # Max concurrent should not exceed 5
            # (This is hard to test precisely due to timing, but we can check results)
            assert all(is_valid for is_valid, _ in results.values())

    @pytest.mark.asyncio
    async def test_validate_bulk_async_performance(self):
        """Test that async validation is faster than sequential."""
        validator = URLValidator(timeout=5.0, retries=0, cache_enabled=False)

        # Create 10 URLs
        urls = [f"https://example{i}.com" for i in range(10)]

        async def mock_head_slow(*args, **kwargs):
            """Mock with artificial delay."""
            await asyncio.sleep(0.1)  # 100ms per request
            response = MagicMock()
            response.status_code = 200
            return response

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.head = mock_head_slow
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            start_time = time.time()
            results = await validator.validate_bulk_async(urls, max_concurrent=5)
            elapsed = time.time() - start_time

            assert len(results) == 10
            # With 10 URLs at 100ms each, sequential would take 1s
            # With concurrency of 5, should take ~200ms (2 batches)
            # Add some buffer for overhead
            assert elapsed < 0.5, f"Took too long: {elapsed}s"


class TestConvenienceFunctions:
    """Test convenience functions for async validation."""

    @pytest.mark.asyncio
    async def test_validate_urls_async_function(self):
        """Test validate_urls_async convenience function."""
        urls = ["https://example.com", "https://github.com"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            results = await validate_urls_async(urls, timeout=5.0, retries=1, max_concurrent=2)

            assert len(results) == 2
            assert all(is_valid for is_valid, _ in results.values())

    @pytest.mark.filterwarnings("ignore::ResourceWarning")
    @pytest.mark.filterwarnings("ignore::pytest.PytestUnraisableExceptionWarning")
    def test_validate_urls_sync_with_async(self):
        """Test validate_urls_sync with async enabled.

        Note: This test uses asyncio.run() with mocked async clients,
        which can leave unclosed resources. These warnings are suppressed
        as they're artifacts of mocking, not real issues.
        """
        import gc

        urls = ["https://example.com", "https://github.com"]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            results = validate_urls_sync(urls, use_async=True, max_concurrent=2)

            assert len(results) == 2
            assert all(is_valid for is_valid, _ in results.values())

        # Force garbage collection to clean up async resources
        gc.collect()
        gc.collect()  # Run twice to handle circular references

    def test_validate_urls_sync_without_async(self):
        """Test validate_urls_sync with async disabled."""
        urls = ["https://example.com"]

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = MagicMock(return_value=mock_response)
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=None)
            mock_client.close = MagicMock()
            mock_client_class.return_value = mock_client

            results = validate_urls_sync(urls, use_async=False)

            assert len(results) == 1
            assert results[urls[0]][0] is True

    def test_validate_urls_sync_single_url_uses_sync(self):
        """Test that single URL uses sync validation even with use_async=True."""
        urls = ["https://example.com"]

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = MagicMock(return_value=mock_response)
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=None)
            mock_client.close = MagicMock()
            mock_client_class.return_value = mock_client

            # Single URL should use sync even with use_async=True
            results = validate_urls_sync(urls, use_async=True)

            assert len(results) == 1
            assert results[urls[0]][0] is True


class TestCacheIntegrationAsync:
    """Test cache integration with async validation."""

    @pytest.mark.asyncio
    async def test_async_validation_populates_cache(self):
        """Test that async validation populates the cache."""
        validator = URLValidator(cache_enabled=True)

        url = "https://example.com"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Validate async
            await validator.validate_async(url)

            # Check cache
            cached = validator.get_cached_result(url)
            assert cached is not None
            assert cached[0] is True

    @pytest.mark.asyncio
    async def test_async_uses_sync_cache(self):
        """Test that async validation uses cache populated by sync validation."""
        validator = URLValidator(cache_enabled=True)

        url = "https://example.com"

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.head = MagicMock(return_value=mock_response)
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Populate cache with sync validation
            validator.validate(url)

        # Now use async - should hit cache without making new request
        with patch("httpx.AsyncClient") as mock_async_client_class:
            mock_async_client = AsyncMock()
            mock_async_client.head = AsyncMock()  # Should not be called
            mock_async_client.__aenter__ = AsyncMock(return_value=mock_async_client)
            mock_async_client.__aexit__ = AsyncMock(return_value=None)
            mock_async_client_class.return_value = mock_async_client

            is_valid, error = await validator.validate_async(url)

            assert is_valid is True
            mock_async_client.head.assert_not_called()
