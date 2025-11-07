# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Gerrit API Client

Client for interacting with Gerrit API to fetch project information
and repository metadata.

Extracted from generate_reports.py as part of Phase 2 refactoring.
"""

import json
import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse

import httpx

from .base_client import APIResponse, APIError, ErrorType, BaseAPIClient


class GerritAPIError(Exception):
    """Base exception for Gerrit API errors."""
    pass


class GerritConnectionError(Exception):
    """Raised when connection to Gerrit server fails."""
    pass


class GerritAPIDiscovery:
    """
    Discovers the correct Gerrit API base URL for a given host.

    Gerrit instances can be deployed with different path prefixes.
    This class tests common patterns to find the working API endpoint.
    """

    # Common Gerrit API path patterns to test
    COMMON_PATHS = [
        "",  # Direct: https://host/
        "/r",  # Standard: https://host/r/
        "/gerrit",  # OpenDaylight style: https://host/gerrit/
        "/infra",  # Linux Foundation style: https://host/infra/
        "/a",  # Authenticated API: https://host/a/
    ]

    def __init__(self, timeout: float = 30.0):
        """
        Initialize discovery client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=10.0),
            follow_redirects=True,
            headers={
                "User-Agent": "repository-reports/1.0.0",
                "Accept": "application/json",
            },
        )

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, *args):
        """Exit context manager and cleanup."""
        self.close()

    def close(self):
        """Close HTTP client."""
        if hasattr(self, "client"):
            self.client.close()

    def discover_base_url(self, host: str) -> str:
        """
        Discover the correct API base URL for a Gerrit host.

        Tries to follow redirects first, then tests common path patterns.

        Args:
            host: Gerrit hostname

        Returns:
            Working API base URL

        Raises:
            GerritAPIError: If no working endpoint is found
        """
        logging.debug(f"Starting API discovery for host: {host}")

        # First, try to follow redirects from the base URL
        redirect_path = self._discover_via_redirect(host)
        if redirect_path:
            test_paths = [redirect_path] + [
                p for p in self.COMMON_PATHS if p != redirect_path
            ]
        else:
            test_paths = self.COMMON_PATHS

        # Test each potential path
        for path in test_paths:
            base_url = f"https://{host}{path}"
            logging.debug(f"Testing API endpoint: {base_url}")

            if self._test_projects_api(base_url):
                logging.debug(f"Discovered working API base URL: {base_url}")
                return base_url

        # If all paths fail, raise an error
        raise GerritAPIError(
            f"Could not discover Gerrit API endpoint for {host}. "
            f"Tested paths: {test_paths}"
        )

    def _discover_via_redirect(self, host: str) -> Optional[str]:
        """
        Attempt to discover the API path by following redirects.

        Args:
            host: Gerrit hostname

        Returns:
            Redirect path if found, None otherwise
        """
        try:
            response = self.client.get(f"https://{host}", follow_redirects=False)
            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if location:
                    parsed = urlparse(location)
                    if parsed.netloc == host or not parsed.netloc:
                        path = parsed.path.rstrip("/")
                        if path and path != "/":
                            return str(path)
        except Exception as e:
            logging.debug(f"Error checking redirects for {host}: {e}")
        return None

    def _test_projects_api(self, base_url: str) -> bool:
        """
        Test if the projects API is available at the given base URL.

        Args:
            base_url: Base URL to test

        Returns:
            True if projects API responds correctly
        """
        try:
            projects_url = urljoin(base_url.rstrip("/") + "/", "projects/?d")
            response = self.client.get(projects_url)

            if response.status_code == 200:
                return self._validate_projects_response(response.text)
            return False
        except Exception as e:
            logging.debug(f"Error testing projects API at {base_url}: {e}")
            return False

    def _validate_projects_response(self, response_text: str) -> bool:
        """
        Validate that the response looks like a valid Gerrit projects API response.

        Args:
            response_text: Raw response text

        Returns:
            True if response is valid Gerrit projects data
        """
        try:
            # Strip Gerrit's security prefix
            if response_text.startswith(")]}'"):
                json_text = response_text[4:]
            else:
                json_text = response_text

            data = json.loads(json_text)
            return isinstance(data, dict)
        except Exception:
            return False


class GerritAPIClient(BaseAPIClient):
    """
    Client for interacting with Gerrit REST API.

    Provides methods to query project information from Gerrit Code Review.
    Handles automatic API endpoint discovery and Gerrit's JSON response format.

    Features:
    - Auto-discovery of API base URL
    - Gerrit magic prefix handling (")]}'")
    - URL encoding for project names with slashes
    - Error tracking and statistics
    """

    def __init__(
        self,
        host: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        stats: Optional[Any] = None
    ):
        """
        Initialize Gerrit API client.

        Args:
            host: Gerrit hostname
            base_url: Optional base URL (auto-discovered if not provided)
            timeout: Request timeout in seconds
            stats: Statistics tracker object
        """
        self.host = host
        self.timeout = timeout
        self.stats = stats
        self.logger = logging.getLogger(__name__)

        if base_url:
            self.base_url = base_url
        else:
            # Auto-discover the base URL
            with GerritAPIDiscovery(timeout) as discovery:
                self.base_url = discovery.discover_base_url(host)

        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout, connect=10.0),
            follow_redirects=True,
            headers={
                "User-Agent": "repository-reports/1.0.0",
                "Accept": "application/json",
            },
        )

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, *args):
        """Exit context manager and cleanup."""
        self.close()

    def close(self):
        """Close HTTP client."""
        if hasattr(self, "client"):
            self.client.close()

    def get_project_info(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific project.

        Args:
            project_name: Name of the Gerrit project (can contain slashes)

        Returns:
            Project information dict, or None if not found

        Example:
            >>> client = GerritAPIClient("gerrit.example.com")
            >>> info = client.get_project_info("foo/bar")
            >>> if info:
            ...     print(f"Project: {info['name']}")
        """
        try:
            # URL-encode the project name and use the projects API with detailed information
            encoded_name = project_name.replace("/", "%2F")
            url = f"/projects/{encoded_name}?d"

            response = self.client.get(url)

            if response.status_code == 200:
                if self.stats:
                    self.stats.record_success("gerrit")
                result = self._parse_json_response(response.text)
                return result
            elif response.status_code == 404:
                if self.stats:
                    self.stats.record_error("gerrit", 404)
                self.logger.debug(f"Project not found in Gerrit: {project_name}")
                return None
            else:
                if self.stats:
                    self.stats.record_error("gerrit", response.status_code)
                self.logger.warning(
                    f"❌ Error: Gerrit API query returned error code: {response.status_code} "
                    f"for project {project_name}"
                )
                return None

        except Exception as e:
            if self.stats:
                self.stats.record_exception("gerrit")
            self.logger.error(f"❌ Error: Gerrit API query exception for {project_name}: {e}")
            return None

    def get_all_projects(self) -> Dict[str, Any]:
        """
        Get all projects with detailed information.

        Returns:
            Dictionary mapping project names to project information.
            Returns empty dict on error.

        Example:
            >>> client = GerritAPIClient("gerrit.example.com")
            >>> projects = client.get_all_projects()
            >>> print(f"Found {len(projects)} projects")
        """
        try:
            response = self.client.get("/projects/?d")

            if response.status_code == 200:
                if self.stats:
                    self.stats.record_success("gerrit")
                result = self._parse_json_response(response.text)
                self.logger.info(f"Fetched {len(result)} projects from Gerrit")
                return result if isinstance(result, dict) else {}
            else:
                if self.stats:
                    self.stats.record_error("gerrit", response.status_code)
                self.logger.error(
                    f"❌ Error: Gerrit API query returned error code: {response.status_code}"
                )
                return {}

        except Exception as e:
            if self.stats:
                self.stats.record_exception("gerrit")
            self.logger.error(f"❌ Error: Gerrit API query exception: {e}")
            return {}

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gerrit JSON response, handling magic prefix.

        Gerrit prepends ")]}" to JSON responses as a security measure
        to prevent XSSI attacks. This method strips it before parsing.

        Args:
            response_text: Raw response text from Gerrit API

        Returns:
            Parsed JSON as dictionary
        """
        # Remove Gerrit's magic prefix if present
        if response_text.startswith(")]}'"):
            clean_text = response_text[4:].lstrip()
        else:
            clean_text = response_text

        try:
            result = json.loads(clean_text)
            return result if isinstance(result, dict) else {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON response: {e}")
            return {}
