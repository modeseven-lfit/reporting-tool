# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Jenkins API Client

Client for interacting with Jenkins API to fetch job information
and build status.

Extracted from generate_reports.py as part of Phase 2 refactoring.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import httpx

from .base_client import BaseAPIClient


class JenkinsAPIClient(BaseAPIClient):
    """
    Client for interacting with Jenkins REST API.

    Provides methods to query job information from Jenkins CI/CD servers.
    Handles automatic API endpoint discovery, job matching, and caching.

    Features:
    - Auto-discovery of API base path
    - Job-to-project matching with scoring algorithm
    - Caching of all jobs data for performance
    - Build status and history retrieval
    - Duplicate job allocation prevention
    """

    def __init__(
        self,
        host: str,
        timeout: float = 30.0,
        stats: Optional[Any] = None
    ):
        """
        Initialize Jenkins API client.

        Args:
            host: Jenkins hostname
            timeout: Request timeout in seconds
            stats: Statistics tracker object
        """
        self.host = host
        self.timeout = timeout
        self.base_url = f"https://{host}"
        self.api_base_path: Optional[str] = None  # Will be discovered
        self._jobs_cache: Dict[str, Any] = {}  # Cache for all jobs data
        self._cache_populated = False
        self.stats = stats
        self.logger = logging.getLogger(__name__)

        self.client = httpx.Client(timeout=timeout)

        # Discover the correct API base path
        self._discover_api_base_path()

    def __enter__(self):
        """Enter context manager."""
        return self

    def __exit__(self, *args):
        """Exit context manager and cleanup."""
        self.close()

    def close(self):
        """Close the HTTP client."""
        if hasattr(self, "client"):
            self.client.close()

    def _discover_api_base_path(self):
        """
        Discover the correct API base path for this Jenkins server.

        Jenkins instances can be deployed with different path prefixes.
        This method tests common patterns to find the working API endpoint.
        """
        # Common Jenkins API path patterns to try
        api_patterns = [
            "/api/json",
            "/releng/api/json",
            "/jenkins/api/json",
            "/ci/api/json",
            "/build/api/json",
        ]

        self.logger.info(f"Discovering Jenkins API base path for {self.host}")

        for pattern in api_patterns:
            try:
                test_url = f"{self.base_url}{pattern}?tree=jobs[name]"
                self.logger.debug(f"Testing Jenkins API path: {test_url}")

                response = self.client.get(test_url)
                if response.status_code == 200:
                    if self.stats:
                        self.stats.record_success("jenkins")
                    try:
                        data: Dict[str, Any] = response.json()
                        if "jobs" in data and isinstance(data["jobs"], list):
                            self.api_base_path = pattern
                            job_count = len(data["jobs"])
                            self.logger.info(
                                f"Found working Jenkins API path: {pattern} ({job_count} jobs)"
                            )
                            return
                    except Exception as e:
                        self.logger.debug(f"Invalid JSON response from {pattern}: {e}")
                        continue
                else:
                    self.logger.debug(f"HTTP {response.status_code} for {pattern}")

            except Exception as e:
                self.logger.debug(f"Connection error testing {pattern}: {e}")
                continue

        # If no pattern worked, default to standard path
        self.api_base_path = "/api/json"
        self.logger.warning(
            f"Could not discover Jenkins API path for {self.host}, using default: {self.api_base_path}"
        )

    def get_all_jobs(self) -> Dict[str, Any]:
        """
        Get all jobs from Jenkins with caching.

        Returns:
            Dictionary containing jobs array and metadata.
            Returns empty dict on error.

        Example:
            >>> client = JenkinsAPIClient("jenkins.example.com")
            >>> jobs_data = client.get_all_jobs()
            >>> for job in jobs_data.get('jobs', []):
            ...     print(job['name'])
        """
        # Return cached data if available
        if self._cache_populated and self._jobs_cache:
            self.logger.debug(
                f"Using cached Jenkins jobs data ({len(self._jobs_cache.get('jobs', []))} jobs)"
            )
            return self._jobs_cache

        if not self.api_base_path:
            self.logger.error(f"No valid API base path discovered for {self.host}")
            return {}

        try:
            url = f"{self.base_url}{self.api_base_path}?tree=jobs[name,url,color,buildable,disabled]"
            self.logger.info(f"Fetching Jenkins jobs from: {url}")
            response = self.client.get(url)

            self.logger.info(f"Jenkins API response: {response.status_code}")
            if response.status_code == 200:
                if self.stats:
                    self.stats.record_success("jenkins")
                data = response.json()
                job_count = len(data.get("jobs", []))
                self.logger.info(f"Found {job_count} Jenkins jobs (cached for reuse)")

                # Cache the data
                self._jobs_cache = data
                self._cache_populated = True
                return dict(data)
            else:
                if self.stats:
                    self.stats.record_error("jenkins", response.status_code)
                self.logger.warning(
                    f"❌ Error: Jenkins API query returned error code: {response.status_code} for {url}"
                )
                self.logger.warning(f"Response text: {response.text[:500]}")
                return {}

        except Exception as e:
            if self.stats:
                self.stats.record_exception("jenkins")
            self.logger.error(f"❌ Error: Jenkins API query exception for {self.host}: {e}")
            return {}

    def get_jobs_for_project(
        self,
        project_name: str,
        allocated_jobs: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Get jobs related to a specific Gerrit project with duplicate prevention.

        Uses a scoring algorithm to match Jenkins job names to Gerrit project names.
        Prevents duplicate allocation by tracking allocated jobs.

        Args:
            project_name: Name of the Gerrit project (e.g., "foo/bar")
            allocated_jobs: Set of job names already allocated to other projects

        Returns:
            List of job detail dictionaries for matched jobs

        Example:
            >>> client = JenkinsAPIClient("jenkins.example.com")
            >>> allocated = set()
            >>> jobs = client.get_jobs_for_project("sdc/onap-sdc", allocated)
            >>> print(f"Found {len(jobs)} jobs")
        """
        self.logger.debug(f"Looking for Jenkins jobs for project: {project_name}")
        all_jobs = self.get_all_jobs()
        project_jobs: List[Dict[str, Any]] = []

        if "jobs" not in all_jobs:
            self.logger.debug(
                f"No 'jobs' key found in Jenkins API response for {project_name}"
            )
            return project_jobs

        # Convert project name to job name format (replace / with -)
        project_job_name = project_name.replace("/", "-")
        self.logger.debug(
            f"Searching for Jenkins jobs matching pattern: {project_job_name}"
        )

        total_jobs = len(all_jobs["jobs"])
        self.logger.debug(f"Checking {total_jobs} total Jenkins jobs for matches")

        # Collect potential matches with scoring for better matching
        candidates: List[tuple[Dict[str, Any], int]] = []

        for job in all_jobs["jobs"]:
            job_name = job.get("name", "")

            # Skip already allocated jobs
            if job_name in allocated_jobs:
                self.logger.debug(f"Skipping already allocated Jenkins job: {job_name}")
                continue

            # Calculate match score for better job attribution
            score = self._calculate_job_match_score(
                job_name, project_name, project_job_name
            )
            if score > 0:
                candidates.append((job, score))

        # Sort by score (highest first) to prioritize better matches
        candidates.sort(key=lambda x: x[1], reverse=True)

        for job, score in candidates:
            job_name = job.get("name", "")
            self.logger.debug(f"Processing Jenkins job: {job_name} (score: {score})")

            # Get detailed job info
            job_details = self.get_job_details(job_name)
            if job_details:
                project_jobs.append(job_details)
                # Mark job as allocated
                allocated_jobs.add(job_name)
                self.logger.info(
                    f"Allocated Jenkins job '{job_name}' to project '{project_name}' (score: {score})"
                )
            else:
                self.logger.warning(f"Failed to get details for Jenkins job: {job_name}")

        self.logger.info(
            f"Found {len(project_jobs)} Jenkins jobs for project {project_name}"
        )
        return project_jobs

    def _calculate_job_match_score(
        self,
        job_name: str,
        project_name: str,
        project_job_name: str
    ) -> int:
        """
        Calculate a match score for Jenkins job attribution using STRICT PREFIX MATCHING ONLY.

        This prevents duplicate allocation by ensuring jobs can only match one project.
        Higher scores indicate better matches. Returns 0 for no match.

        Job name must either:
        1. Be exactly equal to project name, OR
        2. Start with project name followed by a dash (-)

        This prevents sdc-tosca-* from matching sdc.

        Args:
            job_name: Jenkins job name
            project_name: Original Gerrit project name (with slashes)
            project_job_name: Project name converted to job format (slashes -> dashes)

        Returns:
            Match score (0 = no match, higher = better match)
        """
        job_name_lower = job_name.lower()
        project_job_name_lower = project_job_name.lower()
        project_name_lower = project_name.lower()

        # STRICT PREFIX MATCHING WITH WORD BOUNDARY ONLY
        if job_name_lower == project_job_name_lower:
            # Exact match - highest priority
            pass
        elif job_name_lower.startswith(project_job_name_lower + "-"):
            # Prefix with dash separator - valid match
            pass
        else:
            # No match - neither exact nor proper prefix
            return 0

        score = 0

        # Higher score for exact match
        if job_name_lower == project_job_name_lower:
            score += 1000
            return score

        # High score for exact prefix match with separator (project-*)
        if job_name_lower.startswith(project_job_name_lower + "-"):
            score += 500
        else:
            score += 100

        # Bonus for longer/more specific project paths (child projects get priority)
        path_parts = project_name.count("/") + 1
        score += path_parts * 50

        # Bonus for containing full project name components in order
        project_parts = project_name_lower.replace("/", "-").split("-")
        consecutive_matches = 0
        job_parts = job_name_lower.split("-")

        for i, project_part in enumerate(project_parts):
            if i < len(job_parts) and job_parts[i] == project_part:
                consecutive_matches += 1
            else:
                break

        score += consecutive_matches * 25

        return score

    def get_job_details(self, job_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific job.

        Args:
            job_name: Name of the Jenkins job

        Returns:
            Dictionary with job details including status, state, color, URLs, and last build info.
            Returns empty dict on error.

        Example:
            >>> client = JenkinsAPIClient("jenkins.example.com")
            >>> details = client.get_job_details("my-project-verify")
            >>> print(details['status'])  # e.g., "success"
        """
        try:
            # Extract base path without /api/json suffix for job URLs
            base_path = (
                self.api_base_path.replace("/api/json", "")
                if self.api_base_path
                else ""
            )
            url = f"{self.base_url}{base_path}/job/{job_name}/api/json"
            response = self.client.get(url)

            if response.status_code == 200:
                job_data = response.json()

                # Get last build info
                last_build_info = self.get_last_build_info(job_name)

                # Compute Jenkins job state from disabled field first
                disabled = job_data.get("disabled", False)
                buildable = job_data.get("buildable", True)
                state = self._compute_jenkins_job_state(disabled, buildable)

                # Get original color from Jenkins
                original_color = job_data.get("color", "")

                # Compute standardized status from color field, considering state
                status = self._compute_job_status_from_color(original_color)

                # Override color if job is disabled (regardless of last build result)
                if state == "disabled":
                    color = "grey"
                    if status not in ("disabled", "not_built"):
                        status = "disabled"
                else:
                    color = original_color

                # Build standardized job data structure
                job_url = job_data.get("url", "")
                if not job_url and base_path:
                    # Fallback: construct URL if not provided by API
                    job_url = f"{self.base_url}{base_path}/job/{job_name}/"

                return {
                    "name": job_name,
                    "status": status,
                    "state": state,
                    "color": color,
                    "urls": {
                        "job_page": job_url,
                        "source": None,
                        "api": url,
                    },
                    "buildable": buildable,
                    "disabled": disabled,
                    "description": job_data.get("description", ""),
                    "last_build": last_build_info,
                }
            else:
                self.logger.debug(
                    f"Jenkins job API returned {response.status_code} for {job_name}"
                )
                return {}

        except Exception as e:
            self.logger.debug(f"Exception fetching job details for {job_name}: {e}")
            return {}

    def _compute_jenkins_job_state(self, disabled: bool, buildable: bool) -> str:
        """
        Convert Jenkins disabled and buildable fields to standardized state.

        Jenkins job states:
        - disabled=True: Job is explicitly disabled
        - disabled=False + buildable=True: Job is active and can be built
        - disabled=False + buildable=False: Job exists but cannot be built (treat as disabled)

        Args:
            disabled: Whether the job is disabled in Jenkins
            buildable: Whether the job is buildable

        Returns:
            State string: "active" or "disabled"
        """
        if disabled:
            return "disabled"
        elif buildable:
            return "active"
        else:
            # If not disabled but not buildable, consider it effectively disabled
            return "disabled"

    def _compute_job_status_from_color(self, color: str) -> str:
        """
        Convert Jenkins color field to standardized status.

        Jenkins color meanings:
        - blue: success
        - red: failure
        - yellow: unstable
        - grey: not built/disabled
        - aborted: aborted
        - *_anime: building (animated versions)

        Args:
            color: Jenkins color code

        Returns:
            Standardized status string
        """
        if not color:
            return "unknown"

        color_lower = color.lower()

        # Handle animated colors (building states)
        if color_lower.endswith("_anime"):
            return "building"

        # Map standard colors
        color_map = {
            "blue": "success",
            "red": "failure",
            "yellow": "unstable",
            "grey": "disabled",
            "gray": "disabled",
            "aborted": "aborted",
            "notbuilt": "not_built",
            "disabled": "disabled",
        }

        return color_map.get(color_lower, "unknown")

    def get_last_build_info(self, job_name: str) -> Dict[str, Any]:
        """
        Get information about the last build of a job.

        Args:
            job_name: Name of the Jenkins job

        Returns:
            Dictionary with last build information (result, duration, timestamp, etc.)
            Returns empty dict if no build exists or on error.
        """
        try:
            # Extract base path without /api/json suffix for job URLs
            base_path = (
                self.api_base_path.replace("/api/json", "")
                if self.api_base_path
                else ""
            )
            url = f"{self.base_url}{base_path}/job/{job_name}/lastBuild/api/json?tree=result,duration,timestamp,building,number"
            response = self.client.get(url)

            if response.status_code == 200:
                build_data = response.json()

                # Convert timestamp to readable format
                timestamp = build_data.get("timestamp", 0)
                if timestamp:
                    build_time = datetime.fromtimestamp(timestamp / 1000)
                    build_data["build_time"] = build_time.isoformat()

                # Convert duration to readable format
                duration_ms = build_data.get("duration", 0)
                if duration_ms:
                    duration_seconds = duration_ms / 1000
                    build_data["duration_seconds"] = duration_seconds

                return dict(build_data)
            else:
                return dict()

        except Exception as e:
            self.logger.debug(f"Exception fetching last build info for {job_name}: {e}")
            return dict()
