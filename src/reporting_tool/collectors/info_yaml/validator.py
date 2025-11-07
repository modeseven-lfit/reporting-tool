# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
URL validator module.

Provides HTTP URL validation with caching, retries, and exponential backoff
for validating issue tracker URLs from INFO.yaml files.

Supports both synchronous and asynchronous validation for optimal performance.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


class URLValidator:
    """
    Validates HTTP/HTTPS URLs with caching and retry logic.

    Features:
    - Caching to avoid repeated requests to the same URL
    - Configurable timeout and retry count
    - Exponential backoff for transient failures
    - Follows redirects
    - HEAD requests for efficiency
    """

    def __init__(
        self,
        timeout: float = 10.0,
        retries: int = 2,
        cache_enabled: bool = True,
    ):
        """
        Initialize the URL validator.

        Args:
            timeout: Request timeout in seconds (default: 10.0)
            retries: Number of retry attempts (default: 2)
            cache_enabled: Enable response caching (default: True)
        """
        self.timeout = timeout
        self.retries = retries
        self.cache_enabled = cache_enabled

        # Cache for validation results: {url: (is_valid, error_message)}
        self._cache: Dict[str, Tuple[bool, str]] = {}

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(
            f"URLValidator initialized: timeout={timeout}s, retries={retries}, "
            f"cache={cache_enabled}"
        )

    def validate(self, url: str) -> Tuple[bool, str]:
        """
        Validate a URL by making an HTTP HEAD request.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if URL is accessible, False otherwise
            - error_message: Empty string if valid, error description if invalid
        """
        if not url:
            return (False, "No URL provided")

        # Check cache first
        if self.cache_enabled and url in self._cache:
            self.logger.debug(f"Cache hit for URL: {url}")
            return self._cache[url]

        # Validate the URL
        result = self._validate_with_retry(url)

        # Cache the result
        if self.cache_enabled:
            self._cache[url] = result

        return result

    def _validate_with_retry(self, url: str) -> Tuple[bool, str]:
        """
        Validate URL with retry logic and exponential backoff.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        last_error = "Unknown error"

        for attempt in range(self.retries + 1):  # +1 for initial attempt
            try:
                # Use httpx to check URL
                with httpx.Client(
                    follow_redirects=True, timeout=self.timeout
                ) as client:
                    # Use HEAD request for efficiency
                    response = client.head(url)

                    # Check status code
                    if response.status_code < 400:
                        self.logger.debug(
                            f"URL validation succeeded for {url}: "
                            f"HTTP {response.status_code}"
                        )
                        return (True, "")
                    else:
                        # HTTP error - don't retry
                        error_msg = f"HTTP {response.status_code}"
                        self.logger.debug(
                            f"URL validation failed for {url}: {error_msg}"
                        )
                        return (False, error_msg)

            except httpx.ConnectError as e:
                last_error = "Connection failed"
                self.logger.debug(
                    f"Connection error for {url} (attempt {attempt + 1}/"
                    f"{self.retries + 1}): {e}"
                )

            except httpx.TimeoutException as e:
                last_error = f"Timeout after {self.timeout}s"
                self.logger.debug(
                    f"Timeout for {url} (attempt {attempt + 1}/"
                    f"{self.retries + 1}): {e}"
                )

            except httpx.UnsupportedProtocol as e:
                # Don't retry protocol errors
                last_error = "Unsupported protocol"
                self.logger.debug(f"Protocol error for {url}: {e}")
                return (False, last_error)

            except httpx.InvalidURL as e:
                # Don't retry invalid URL errors
                last_error = "Invalid URL"
                self.logger.debug(f"Invalid URL {url}: {e}")
                return (False, last_error)

            except Exception as e:
                # Unexpected error - don't retry
                last_error = f"Unexpected error: {type(e).__name__}"
                self.logger.warning(f"Unexpected error validating {url}: {e}")
                return (False, last_error)

            # If we haven't returned yet, we need to retry
            if attempt < self.retries:
                # Exponential backoff: 1s, 2s, 4s, etc.
                retry_delay = 1.0 * (2**attempt)
                self.logger.debug(
                    f"Retrying {url} in {retry_delay}s "
                    f"(attempt {attempt + 1}/{self.retries + 1})"
                )
                time.sleep(retry_delay)

        # All retries exhausted
        error_msg = f"{last_error} (after {self.retries + 1} attempts)"
        self.logger.debug(f"URL validation failed for {url}: {error_msg}")
        return (False, error_msg)

    def validate_bulk(self, urls: list[str]) -> Dict[str, Tuple[bool, str]]:
        """
        Validate multiple URLs sequentially.

        Args:
            urls: List of URLs to validate

        Returns:
            Dictionary mapping URL to (is_valid, error_message) tuple
        """
        results = {}

        for url in urls:
            if not url:
                continue

            results[url] = self.validate(url)

        return results

    async def validate_async(self, url: str) -> Tuple[bool, str]:
        """
        Validate a URL asynchronously by making an HTTP HEAD request.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if URL is accessible, False otherwise
            - error_message: Empty string if valid, error description if invalid
        """
        if not url:
            return (False, "No URL provided")

        # Check cache first
        if self.cache_enabled and url in self._cache:
            self.logger.debug(f"Cache hit for URL: {url}")
            return self._cache[url]

        # Validate the URL
        result = await self._validate_with_retry_async(url)

        # Cache the result
        if self.cache_enabled:
            self._cache[url] = result

        return result

    async def _validate_with_retry_async(self, url: str) -> Tuple[bool, str]:
        """
        Validate URL asynchronously with retry logic and exponential backoff.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        last_error = "Unknown error"

        for attempt in range(self.retries + 1):  # +1 for initial attempt
            try:
                # Use httpx async client to check URL
                async with httpx.AsyncClient(
                    follow_redirects=True, timeout=self.timeout
                ) as client:
                    # Use HEAD request for efficiency
                    response = await client.head(url)

                    # Check status code
                    if response.status_code < 400:
                        self.logger.debug(
                            f"URL validation succeeded for {url}: "
                            f"HTTP {response.status_code}"
                        )
                        return (True, "")
                    else:
                        # HTTP error - don't retry
                        error_msg = f"HTTP {response.status_code}"
                        self.logger.debug(
                            f"URL validation failed for {url}: {error_msg}"
                        )
                        return (False, error_msg)

            except httpx.ConnectError as e:
                last_error = "Connection failed"
                self.logger.debug(
                    f"Connection error for {url} (attempt {attempt + 1}/"
                    f"{self.retries + 1}): {e}"
                )

            except httpx.TimeoutException as e:
                last_error = f"Timeout after {self.timeout}s"
                self.logger.debug(
                    f"Timeout for {url} (attempt {attempt + 1}/"
                    f"{self.retries + 1}): {e}"
                )

            except httpx.UnsupportedProtocol as e:
                # Don't retry protocol errors
                last_error = "Unsupported protocol"
                self.logger.debug(f"Protocol error for {url}: {e}")
                return (False, last_error)

            except httpx.InvalidURL as e:
                # Don't retry invalid URL errors
                last_error = "Invalid URL"
                self.logger.debug(f"Invalid URL {url}: {e}")
                return (False, last_error)

            except Exception as e:
                # Unexpected error - don't retry
                last_error = f"Unexpected error: {type(e).__name__}"
                self.logger.warning(f"Unexpected error validating {url}: {e}")
                return (False, last_error)

            # If we haven't returned yet, we need to retry
            if attempt < self.retries:
                # Exponential backoff: 1s, 2s, 4s, etc.
                retry_delay = 1.0 * (2**attempt)
                self.logger.debug(
                    f"Retrying {url} in {retry_delay}s "
                    f"(attempt {attempt + 1}/{self.retries + 1})"
                )
                await asyncio.sleep(retry_delay)

        # All retries exhausted
        error_msg = f"{last_error} (after {self.retries + 1} attempts)"
        self.logger.debug(f"URL validation failed for {url}: {error_msg}")
        return (False, error_msg)

    async def validate_bulk_async(
        self, urls: List[str], max_concurrent: int = 10
    ) -> Dict[str, Tuple[bool, str]]:
        """
        Validate multiple URLs concurrently using async HTTP requests.

        This method provides significant performance improvements over sequential
        validation when checking many URLs.

        Args:
            urls: List of URLs to validate
            max_concurrent: Maximum number of concurrent requests (default: 10)

        Returns:
            Dictionary mapping URL to (is_valid, error_message) tuple
        """
        # Filter out empty URLs
        valid_urls = [url for url in urls if url]

        if not valid_urls:
            return {}

        # Create semaphore to limit concurrent connections
        semaphore = asyncio.Semaphore(max_concurrent)

        async def validate_with_semaphore(url: str) -> Tuple[str, Tuple[bool, str]]:
            """Validate a single URL with semaphore control."""
            async with semaphore:
                result = await self.validate_async(url)
                return (url, result)

        # Create tasks for all URLs
        tasks = [validate_with_semaphore(url) for url in valid_urls]

        # Execute all tasks concurrently
        self.logger.info(
            f"Starting concurrent validation of {len(valid_urls)} URLs "
            f"(max_concurrent={max_concurrent})"
        )
        start_time = time.time()

        results_list = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        self.logger.info(
            f"Completed validation of {len(valid_urls)} URLs in {elapsed:.2f}s "
            f"({len(valid_urls)/elapsed:.1f} URLs/s)"
        )

        # Convert results to dictionary
        results = {}
        for item in results_list:
            if isinstance(item, Exception):
                self.logger.error(f"Task failed with exception: {item}")
                continue
            if isinstance(item, tuple) and len(item) == 2:
                url, result = item
                results[url] = result

        return results

    def clear_cache(self) -> None:
        """Clear the validation cache."""
        self._cache.clear()
        self.logger.debug("Validation cache cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics:
            - total_entries: Total number of cached entries
            - valid_entries: Number of valid URLs in cache
            - invalid_entries: Number of invalid URLs in cache
        """
        stats = {
            "total_entries": len(self._cache),
            "valid_entries": sum(1 for is_valid, _ in self._cache.values() if is_valid),
            "invalid_entries": sum(
                1 for is_valid, _ in self._cache.values() if not is_valid
            ),
        }
        return stats

    def get_cached_result(self, url: str) -> Optional[Tuple[bool, str]]:
        """
        Get cached validation result for a URL.

        Args:
            url: URL to look up

        Returns:
            Cached result tuple or None if not in cache
        """
        return self._cache.get(url)

    def is_url_cached(self, url: str) -> bool:
        """
        Check if a URL is in the cache.

        Args:
            url: URL to check

        Returns:
            True if URL is cached, False otherwise
        """
        return url in self._cache


def validate_url(url: str, timeout: float = 10.0, retries: int = 2) -> Tuple[bool, str]:
    """
    Convenience function to validate a single URL.

    Args:
        url: URL to validate
        timeout: Request timeout in seconds
        retries: Number of retry attempts

    Returns:
        Tuple of (is_valid, error_message)
    """
    validator = URLValidator(timeout=timeout, retries=retries, cache_enabled=False)
    return validator.validate(url)


def validate_urls(
    urls: list[str], timeout: float = 10.0, retries: int = 2
) -> Dict[str, Tuple[bool, str]]:
    """
    Convenience function to validate multiple URLs sequentially.

    Args:
        urls: List of URLs to validate
        timeout: Request timeout in seconds
        retries: Number of retry attempts

    Returns:
        Dictionary mapping URL to (is_valid, error_message) tuple
    """
    validator = URLValidator(timeout=timeout, retries=retries, cache_enabled=True)
    return validator.validate_bulk(urls)


async def validate_urls_async(
    urls: List[str],
    timeout: float = 10.0,
    retries: int = 2,
    max_concurrent: int = 10,
) -> Dict[str, Tuple[bool, str]]:
    """
    Convenience function to validate multiple URLs concurrently.

    This async function provides significant performance improvements when
    validating many URLs by making concurrent HTTP requests.

    Args:
        urls: List of URLs to validate
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        max_concurrent: Maximum number of concurrent requests (default: 10)

    Returns:
        Dictionary mapping URL to (is_valid, error_message) tuple

    Example:
        >>> urls = ["https://example.com", "https://github.com"]
        >>> results = await validate_urls_async(urls, max_concurrent=5)
        >>> print(results)
        {'https://example.com': (True, ''), 'https://github.com': (True, '')}
    """
    validator = URLValidator(timeout=timeout, retries=retries, cache_enabled=True)
    return await validator.validate_bulk_async(urls, max_concurrent=max_concurrent)


def validate_urls_sync(
    urls: List[str],
    timeout: float = 10.0,
    retries: int = 2,
    max_concurrent: int = 10,
    use_async: bool = True,
) -> Dict[str, Tuple[bool, str]]:
    """
    Convenience function to validate multiple URLs with automatic async/sync selection.

    This function automatically uses async validation for better performance when
    validating multiple URLs, but can fall back to synchronous validation if needed.

    Args:
        urls: List of URLs to validate
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        max_concurrent: Maximum number of concurrent requests (default: 10)
        use_async: Use async validation for better performance (default: True)

    Returns:
        Dictionary mapping URL to (is_valid, error_message) tuple

    Example:
        >>> urls = ["https://example.com", "https://github.com"]
        >>> results = validate_urls_sync(urls, max_concurrent=5)
        >>> print(results)
        {'https://example.com': (True, ''), 'https://github.com': (True, '')}
    """
    if use_async and len(urls) > 1:
        # Use async validation for multiple URLs
        try:
            # Try to get existing event loop
            try:
                loop = asyncio.get_running_loop()
                # We're already in an async context, can't use asyncio.run()
                # Fall back to sync validation
                logger.debug(
                    "Event loop already running, falling back to sync validation"
                )
                return validate_urls(urls, timeout=timeout, retries=retries)
            except RuntimeError:
                # No event loop exists, create one with asyncio.run()
                pass

            # Use asyncio.run() which properly cleans up the event loop
            return asyncio.run(
                validate_urls_async(
                    urls, timeout=timeout, retries=retries, max_concurrent=max_concurrent
                )
            )
        except Exception as e:
            # If async fails for any reason, fall back to sync
            logger.warning(f"Async validation failed, falling back to sync: {e}")
            return validate_urls(urls, timeout=timeout, retries=retries)
    else:
        # Use synchronous validation for single URL or when async is disabled
        return validate_urls(urls, timeout=timeout, retries=retries)
