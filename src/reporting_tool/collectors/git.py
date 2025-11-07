# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Git repository data collector.

This module provides the GitDataCollector class for analyzing Git repositories
and extracting comprehensive metrics including:
- Commit activity across configurable time windows
- Lines of code changes (additions, deletions, net changes)
- Contributor identification and statistics
- Repository activity status classification
- Integration with external systems (Gerrit, Jenkins)
- Caching support for performance optimization
"""

import datetime
import hashlib
import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.gerrit_client import GerritAPIClient
from api.jenkins_client import JenkinsAPIClient
from concurrency.jenkins_allocation import JenkinsAllocationContext


def safe_git_command(
    cmd: list[str], cwd: Path | None, logger: logging.Logger
) -> tuple[bool, str]:
    """
    Execute a git command safely with error handling.

    Returns:
        (success: bool, output_or_error: str)
    """
    try:
        git_result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        return (
            git_result.returncode == 0,
            git_result.stdout.strip() or git_result.stderr.strip(),
        )
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git command failed in {cwd}: {' '.join(cmd)} - {e.stderr}")
        return False, e.stderr
    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out in {cwd}: {' '.join(cmd)}")
        return False, "Command timed out"
    except Exception as e:
        logger.error(f"Unexpected error running git command in {cwd}: {e}")
        return False, str(e)


class GitDataCollector:
    """Handles Git repository analysis and metric collection.

    Thread Safety:
        This class is designed for concurrent use via ThreadPoolExecutor.
        Jenkins job allocation is protected by instance-level JenkinsAllocationContext.
    """

    def __init__(
        self,
        config: dict[str, Any],
        time_windows: dict[str, dict[str, Any]],
        logger: logging.Logger,
        jenkins_allocation_context: Optional[JenkinsAllocationContext] = None,
    ) -> None:
        self.config = config
        self.time_windows = time_windows
        self.logger = logger
        self.cache_enabled = config.get("performance", {}).get("cache", False)
        self.cache_dir = None
        self.repos_path: Optional[Path] = (
            None  # Will be set later for relative path calculation
        )
        if self.cache_enabled:
            self.cache_dir = Path(tempfile.gettempdir()) / "repo_reporting_cache"
            self.cache_dir.mkdir(exist_ok=True)

        # Initialize Gerrit API client if configured
        self.gerrit_client = None
        self.gerrit_projects_cache: dict[
            str, dict[str, Any]
        ] = {}  # Cache for all Gerrit project data
        gerrit_config = self.config.get("gerrit", {})

        # Initialize Jenkins API client if configured
        self.jenkins_client = None
        # Jenkins allocation context for thread-safe job tracking (Phase 7)
        # If not provided, create a new instance (each collector gets its own context)
        self.jenkins_allocation_context = jenkins_allocation_context or JenkinsAllocationContext()
        self._jenkins_initialized = False

        # Check for Jenkins host from environment variable
        jenkins_host = os.environ.get("JENKINS_HOST")
        jenkins_config = self.config.get("jenkins", {})

        if gerrit_config.get("enabled", False):
            host = gerrit_config.get("host")
            base_url = gerrit_config.get("base_url")
            timeout = gerrit_config.get("timeout", 30.0)

            if host:
                try:
                    self.gerrit_client = GerritAPIClient(host, base_url, timeout)
                    self.logger.info(f"Initialized Gerrit API client for {host}")
                    # Fetch all project data upfront
                    self._fetch_all_gerrit_projects()
                except Exception as e:
                    self.logger.error(
                        f"Failed to initialize Gerrit API client for {host}: {e}"
                    )
            else:
                self.logger.error("Gerrit enabled but no host configured")

        # Initialize Jenkins client
        if jenkins_host:
            # Environment variable takes precedence - enables Jenkins integration
            timeout = jenkins_config.get("timeout", 30.0)
            try:
                self.jenkins_client = JenkinsAPIClient(jenkins_host, timeout)
                self.logger.info(
                    f"Initialized Jenkins API client for {jenkins_host} (from environment)"
                )
                # Test the connection and cache all jobs upfront
                self._initialize_jenkins_cache()
            except Exception as e:
                self.logger.error(
                    f"Failed to initialize Jenkins API client for {jenkins_host}: {e}"
                )
                self.jenkins_client = None
        elif jenkins_config.get("enabled", False):
            # Fallback to config file (for backward compatibility)
            host = jenkins_config.get("host")
            timeout = jenkins_config.get("timeout", 30.0)

            if host:
                try:
                    self.jenkins_client = JenkinsAPIClient(host, timeout)
                    self.logger.info(
                        f"Initialized Jenkins API client for {host} (from config)"
                    )
                    # Initialize cache for config-based Jenkins client too
                    self._initialize_jenkins_cache()
                except Exception as e:
                    self.logger.error(
                        f"Failed to initialize Jenkins API client for {host}: {e}"
                    )
            else:
                self.logger.error("Jenkins enabled but no host configured")

    def _initialize_jenkins_cache(self):
        """Initialize Jenkins jobs cache at startup for better performance."""
        if not self.jenkins_client or self._jenkins_initialized:
            return

        try:
            self.logger.info("Caching all Jenkins jobs for efficient allocation...")
            all_jobs = self.jenkins_client.get_all_jobs()
            self.jenkins_allocation_context.set_all_jobs(all_jobs)
            job_count = len(all_jobs.get("jobs", []))
            self.logger.info(
                f"Jenkins cache initialized: {job_count} total jobs available"
            )
            self._jenkins_initialized = True
        except Exception as e:
            self.logger.error(f"Failed to initialize Jenkins cache: {e}")
            self._jenkins_initialized = False

    def _fetch_all_gerrit_projects(self) -> None:
        """Fetch all Gerrit project data upfront and cache it."""
        if not self.gerrit_client:
            return

        try:
            all_projects = self.gerrit_client.get_all_projects()

            if all_projects:
                self.gerrit_projects_cache = all_projects
                self.logger.info(f"Cached {len(all_projects)} projects from Gerrit")
            else:
                self.logger.warning("No projects returned from Gerrit API")

        except Exception as e:
            self.logger.error(f"Failed to fetch Gerrit projects: {e}")

    def _extract_gerrit_project(self, repo_path: Path) -> str:
        """
        Extract the hierarchical Gerrit project name from the repository path.

        For paths containing hostname patterns like:
        /path/to/gerrit.o-ran-sc.org/aiml-fw/aihp/tps/kserve-adapter
        returns 'aiml-fw/aihp/tps/kserve-adapter' (the full Gerrit project hierarchy).

        Falls back to repository folder name if no hierarchical structure is detected.
        """
        try:
            path_parts = repo_path.parts

            # Strategy 1: Look for gerrit-repos-* directory pattern
            for i, part in enumerate(path_parts):
                if part.startswith("gerrit-repos-"):
                    if i < len(path_parts) - 1:
                        project_path_parts = path_parts[i + 1 :]
                        gerrit_project = "/".join(project_path_parts)
                        self.logger.debug(
                            f"Extracted Gerrit project from gerrit-repos pattern: {gerrit_project}"
                        )
                        return gerrit_project
                    break

            # Strategy 2: Look for hostname pattern (gerrit.domain.tld)
            for i, part in enumerate(path_parts):
                if "." in part and any(
                    tld in part for tld in [".org", ".com", ".net", ".io"]
                ):
                    if i < len(path_parts) - 1:
                        project_path_parts = path_parts[i + 1 :]
                        gerrit_project = "/".join(project_path_parts)
                        self.logger.debug(
                            f"Extracted Gerrit project from hostname pattern: {gerrit_project}"
                        )
                        return gerrit_project
                    break

            # Strategy 3: Look for organization root directories and extract relative path
            # Common organization names in paths
            org_names = ["onap", "o-ran-sc", "opendaylight", "fdio", "opnfv", "agl"]

            for i, part in enumerate(path_parts):
                if part.lower() in org_names:
                    # Found organization root, extract everything after it
                    if i < len(path_parts) - 1:
                        project_path_parts = path_parts[i + 1 :]
                        gerrit_project = "/".join(project_path_parts)
                        self.logger.debug(
                            f"Extracted Gerrit project from organization root '{part}': {gerrit_project}"
                        )
                        return gerrit_project
                    break

            # Strategy 4: Check if any parent directories suggest hierarchical structure
            # Look for common Gerrit project patterns (2+ levels deep)
            # Filter out root directory from path_parts
            meaningful_parts = [part for part in path_parts if part and part != "/"]
            if len(meaningful_parts) >= 3:
                # Take last 2-4 path components as potential project hierarchy
                for depth in range(4, 1, -1):  # Try 4, 3, 2 components
                    if len(meaningful_parts) >= depth:
                        potential_project = "/".join(meaningful_parts[-depth:])
                        # Validate it looks_project

            # Fallback: use just the repository folder name
            self.logger.debug(
                f"No hierarchical structure detected, using folder name: {repo_path.name}"
            )
            return repo_path.name

        except Exception as e:
            self.logger.warning(
                f"Error extracting Gerrit project from {repo_path}: {e}"
            )
            return repo_path.name

    def _derive_gerrit_url(self, repo_path: Path) -> str:
        """
        Derive the full Gerrit URL from the repository path.

        Extracts hostname and project path to create URL like:
        gerrit.o-ran-sc.org/aiml-fw/aihp/tps/kserve-adapter
        """
        try:
            path_parts = repo_path.parts

            # Look for hostname pattern and construct URL-style path
            for i, part in enumerate(path_parts):
                if "." in part and any(
                    tld in part for tld in [".org", ".com", ".net", ".io"]
                ):
                    hostname = part
                    if i < len(path_parts) - 1:
                        project_parts = path_parts[i + 1 :]
                        gerrit_url = f"{hostname}/{'/'.join(project_parts)}"
                        self.logger.debug(f"Derived Gerrit URL: {gerrit_url}")
                        return gerrit_url
                    else:
                        return hostname

            # Fallback: construct generic URL with repo name only (avoid recursive issues)
            repo_name = repo_path.name
            fallback_url = f"unknown-gerrit-host/{repo_name}"
            self.logger.warning(
                f"Could not detect Gerrit hostname, using fallback: {fallback_url}"
            )
            return fallback_url

        except Exception as e:
            self.logger.warning(f"Error deriving Gerrit URL from {repo_path}: {e}")
            return str(repo_path)

    def _extract_gerrit_host(self, repo_path: Path) -> str:
        """Extract the Gerrit hostname from the repository path."""
        try:
            path_parts = repo_path.parts
            for part in path_parts:
                if "." in part and any(
                    tld in part for tld in [".org", ".com", ".net", ".io"]
                ):
                    return part
            return "unknown-gerrit-host"
        except Exception as e:
            self.logger.warning(f"Error extracting Gerrit host from {repo_path}: {e}")
            return "unknown-gerrit-host"

    def __del__(self):
        """Cleanup Gerrit client when GitDataCollector is destroyed."""
        if hasattr(self, "gerrit_client") and self.gerrit_client:
            try:
                self.gerrit_client.close()
            except Exception:
                pass  # Ignore cleanup errors

    def collect_repo_git_metrics(self, repo_path: Path) -> dict[str, Any]:
        """
        Extract Git metrics for a single repository across all time windows.

        Uses git log --numstat --date=iso --pretty=format for unified traversal.
        Single pass filtering commits into all time windows.
        Collects: timestamps, author name/email, added/removed lines.
        Returns structured metrics or error descriptor.
        """
        # Extract Gerrit project information
        if self.repos_path:
            gerrit_project = str(repo_path.relative_to(self.repos_path))
        else:
            gerrit_project = self._extract_gerrit_project(repo_path)
        gerrit_host = self._extract_gerrit_host(repo_path)
        gerrit_url = self._derive_gerrit_url(repo_path)

        self.logger.debug(
            f"Collecting Git metrics for Gerrit project: {gerrit_project}"
        )

        # Initialize metrics structure with Gerrit-centric model
        metrics: Dict[str, Any] = {
            "repository": {
                "gerrit_project": gerrit_project,  # PRIMARY identifier
                "gerrit_host": gerrit_host,
                "gerrit_url": gerrit_url,
                "local_path": str(repo_path),  # Secondary, for internal use
                "last_commit_timestamp": None,
                "days_since_last_commit": None,
                "activity_status": "inactive",  # "current", "active", or "inactive"
                "has_any_commits": False,  # Track if repo has ANY commits (regardless of time windows)
                "total_commits_ever": 0,  # Total commits across all history
                "commit_counts": {window: 0 for window in self.time_windows},
                "loc_stats": {
                    window: {"added": 0, "removed": 0, "net": 0}
                    for window in self.time_windows
                },
                "unique_contributors": {window: set() for window in self.time_windows},
                "features": {},
            },
            "authors": {},  # email -> author metrics
            "errors": [],  # List[str]
        }

        try:
            # Check if this is actually a git repository
            if not (repo_path / ".git").exists():
                errors_list = metrics["errors"]
                assert isinstance(errors_list, list)
                errors_list.append(f"Not a git repository: {repo_path}")
                return metrics

            # Check cache if enabled
            if self.cache_enabled:
                cached_metrics = self._load_from_cache(repo_path)
                if cached_metrics:
                    self.logger.debug(f"Using cached metrics for {gerrit_project}")
                    return cached_metrics

            # Get git log with numstat in a single command
            git_command = [
                "git",
                "log",
                "--numstat",
                "--date=iso",
                "--pretty=format:%H|%ad|%an|%ae|%s",
            ]

            # NOTE: Removed max_history_years filtering to ensure all commit data is captured
            # for accurate total_commits_ever, has_any_commits, and complete contributor data.
            # Time window filtering is applied separately during commit processing.

            success, output = safe_git_command(git_command, repo_path, self.logger)
            if not success:
                metrics["errors"].append(f"Git command failed: {output}")
                return metrics

            # Parse git log output
            commits_data = self._parse_git_log_output(output, gerrit_project)

            # Update total commit count regardless of time windows
            metrics["repository"]["total_commits_ever"] = len(commits_data)
            metrics["repository"]["has_any_commits"] = len(commits_data) > 0

            # Process commits into time windows
            for commit_data in commits_data:
                self._update_commit_metrics(commit_data, metrics)

            # Finalize repository metrics
            self._finalize_repo_metrics(metrics, gerrit_project)

            # Convert sets to counts for JSON serialization
            repo_data = metrics["repository"]

            # Add Jenkins job information if available
            if self.jenkins_client:
                jenkins_jobs = self._get_jenkins_jobs_for_repo(gerrit_project)

                # Store computed status for each job for consistent access
                enriched_jobs = []
                for job in jenkins_jobs:
                    if isinstance(job, dict) and "status" in job:
                        enriched_jobs.append(job)
                    else:
                        # Fallback for jobs missing status (shouldn't happen with new structure)
                        enriched_job = (
                            dict(job) if isinstance(job, dict) else {"name": str(job)}
                        )
                        enriched_job["status"] = "unknown"
                        enriched_jobs.append(enriched_job)

                repo_data["jenkins"] = {
                    "jobs": enriched_jobs,
                    "job_count": len(enriched_jobs),
                    "has_jobs": len(enriched_jobs) > 0,
                }
            unique_contributors = repo_data["unique_contributors"]
            for window in self.time_windows:
                contributor_set = unique_contributors[window]
                assert isinstance(contributor_set, set)
                unique_contributors[window] = len(contributor_set)

            self.logger.debug(
                f"Collected {len(commits_data)} commits for {gerrit_project}"
            )

            # Save to cache if enabled
            if self.cache_enabled:
                self._save_cached_metrics(repo_path, repo_data)

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting Git metrics for {gerrit_project}: {e}")
            errors_list = metrics["errors"]
            assert isinstance(errors_list, list)
            errors_list.append(f"Unexpected error: {str(e)}")
            return metrics

    def _get_jenkins_jobs_for_repo(self, repo_name: str) -> list[dict[str, Any]]:
        """Get Jenkins jobs for a specific repository with duplicate prevention.

        Thread-safe: uses instance-level JenkinsAllocationContext.
        """
        if not self.jenkins_client or not self._jenkins_initialized:
            self.logger.debug(
                f"No Jenkins client available or cache not initialized for {repo_name}"
            )
            return []

        # Use cached data instead of making API calls
        cached = self.jenkins_allocation_context.get_cached_jobs(repo_name)
        if cached is not None:
            self.logger.debug(f"Using cached Jenkins jobs for {repo_name}")
            return list(cached)

        try:
            # Get jobs from Jenkins API (includes allocated jobs set for duplicate prevention)
            jobs = self.jenkins_client.get_jobs_for_project(
                repo_name, self.jenkins_allocation_context.allocated_jobs
            )

            if jobs:
                self.logger.debug(
                    f"Found {len(jobs)} Jenkins jobs for {repo_name}: {[job.get('name') for job in jobs]}"
                )
                # Allocate jobs (thread-safe, prevents duplicates)
                allocated = self.jenkins_allocation_context.allocate_jobs(repo_name, jobs)
                # Cache the allocated results
                self.jenkins_allocation_context.cache_jobs(repo_name, allocated)
                return list(allocated)
            else:
                # Cache empty result
                self.jenkins_allocation_context.cache_jobs(repo_name, [])
                return []
        except Exception as e:
            self.logger.warning(f"Error fetching Jenkins jobs for {repo_name}: {e}")
            self.jenkins_allocation_context.cache_jobs(repo_name, [])
            return []

    def reset_jenkins_allocation_state(self) -> None:
        """Reset Jenkins job allocation state for a fresh start.

        Thread-safe: uses instance-level JenkinsAllocationContext.
        """
        self.jenkins_allocation_context.reset()
        self.logger.info("Reset Jenkins job allocation state")

    def get_jenkins_job_allocation_summary(self) -> dict[str, Any]:
        """Get summary of Jenkins job allocation for auditing purposes.

        Thread-safe: uses instance-level JenkinsAllocationContext.
        """
        if not self.jenkins_client or not self._jenkins_initialized:
            return {"error": "No Jenkins client available or not initialized"}

        # Get summary from allocation context (thread-safe)
        summary = self.jenkins_allocation_context.get_allocation_summary()

        # Add percentage calculation
        total_jobs = summary["total_jobs"]
        allocated_count = summary["allocated_count"]
        unallocated_count = total_jobs - allocated_count
        allocated_names = self.jenkins_allocation_context.get_allocated_job_names()

        return {
            "total_jenkins_jobs": total_jobs,
            "allocated_jobs": allocated_count,
            "unallocated_jobs": unallocated_count,
            "allocated_job_names": sorted(allocated_names),
            "allocation_percentage": round((allocated_count / total_jobs * 100), 2)
            if total_jobs > 0
            else 0,
        }

    def validate_jenkins_job_allocation(self) -> list[str]:
        """Validate Jenkins job allocation and return any issues found."""
        issues = []

        if not self.jenkins_client or not self._jenkins_initialized:
            return ["No Jenkins client available or not initialized for validation"]

        # Check for duplicate allocations (shouldn't happen with new system)
        allocation_summary = self.get_jenkins_job_allocation_summary()

        if "error" in allocation_summary:
            issues.append(allocation_summary["error"])
            return issues

        if allocation_summary["unallocated_jobs"] > 0:
            # Use cached data
            all_jobs = self.jenkins_allocation_context.get_all_jobs()
            all_job_names = {
                job.get("name", "") for job in all_jobs.get("jobs", [])
            }
            allocated_job_names = set(self.jenkins_allocation_context.get_allocated_job_names())
            unallocated_jobs = all_job_names - allocated_job_names

            # Try to match unallocated jobs to archived Gerrit projects
            self._allocate_orphaned_jobs_to_archived_projects(unallocated_jobs)

            # Identify infrastructure jobs that legitimately don't belong to projects
            infrastructure_patterns = [
                "lab-",
                "lf-",
                "openci-",
                "rtdv3-",
                "global-jjb-",
                "ci-management-",
                "releng-",
                "autorelease-",
                "docs-",
                "infra-",
            ]

            # After orphaned job detection, recalculate what's truly unallocated
            orphaned_jobs = self.jenkins_allocation_context.get_orphaned_jobs()
            orphaned_job_names = set(orphaned_jobs.keys())
            remaining_unallocated = unallocated_jobs - orphaned_job_names

            infrastructure_jobs = set()
            project_jobs = set()

            for job in remaining_unallocated:
                job_lower = job.lower()
                is_infrastructure = any(
                    job_lower.startswith(pattern) for pattern in infrastructure_patterns
                )
                if is_infrastructure:
                    infrastructure_jobs.add(job)
                else:
                    project_jobs.add(job)

            # Report orphaned jobs as informational (matched to archived projects)
            if orphaned_job_names:
                orphaned_jobs_list = sorted(list(orphaned_job_names))
                issues.append(
                    f"INFO: Found {len(orphaned_job_names)} Jenkins jobs matched to archived/read-only Gerrit projects"
                )
                issues.append(f"Orphaned jobs: {orphaned_jobs_list}")

                # Group by project state
                by_state: dict[str, list[str]] = {}
                orphaned_jobs = self.jenkins_allocation_context.get_orphaned_jobs()
                for job_name in orphaned_job_names:
                    job_info = orphaned_jobs[job_name]
                    state = job_info.get("state", "UNKNOWN")
                    if state not in by_state:
                        by_state[state] = []
                    by_state[state].append(job_name)

                for state, jobs in by_state.items():
                    issues.append(
                        f"  - {len(jobs)} jobs for {state} projects: {sorted(jobs)}"
                    )

            # Only report remaining project jobs as critical errors
            if project_jobs:
                project_jobs_list = sorted(list(project_jobs))
                issues.append(
                    f"CRITICAL ERROR: Found {len(project_jobs)} unallocated project Jenkins jobs"
                )
                issues.append(f"Unallocated project jobs: {project_jobs_list}")

                # Analyze patterns in project jobs only
                patterns: dict[str, int] = {}
                for job in project_jobs:
                    parts = job.lower().split("-")
                    if parts:
                        first_part = parts[0]
                        patterns[first_part] = patterns.get(first_part, 0) + 1

                if patterns:
                    common_patterns = sorted(
                        patterns.items(), key=lambda x: x[1], reverse=True
                    )[:5]
                    issues.append(
                        f"Common patterns in unallocated project jobs: {common_patterns}"
                    )

                # Generate detailed suggestions for fixing unallocated project jobs
                suggestions = []
                for job in sorted(project_jobs)[:20]:  # Analyze first 20
                    job_parts = job.lower().split("-")
                    if job_parts:
                        suggestions.append(
                            f"  - '{job}' might belong to project containing '{job_parts[0]}'"
                        )

                if suggestions:
                    issues.append("Suggestions for unallocated project jobs:")
                    issues.extend(suggestions)

            # Log infrastructure jobs as informational
            if infrastructure_jobs:
                infrastructure_jobs_list = sorted(list(infrastructure_jobs))
                issues.append(
                    f"INFO: Found {len(infrastructure_jobs)} infrastructure Jenkins jobs (not assigned to projects)"
                )
                issues.append(f"Infrastructure jobs: {infrastructure_jobs_list}")

        return issues

    def _allocate_orphaned_jobs_to_archived_projects(
        self, unallocated_jobs: set[str]
    ) -> None:
        """Try to match unallocated Jenkins jobs to archived/read-only Gerrit projects."""
        if not self.gerrit_projects_cache or not unallocated_jobs:
            return

        self.logger.info(
            f"Attempting to match {len(unallocated_jobs)} unallocated Jenkins jobs to archived Gerrit projects"
        )

        # Get all archived/read-only projects
        archived_projects = {}
        for project_name, project_info in self.gerrit_projects_cache.items():
            state = project_info.get("state", "ACTIVE")
            if state in ["READ_ONLY", "HIDDEN"]:
                archived_projects[project_name] = project_info

        self.logger.debug(
            f"Found {len(archived_projects)} archived/read-only projects in Gerrit"
        )

        # Try to match jobs to archived projects using same logic as active projects
        for job_name in list(
            unallocated_jobs
        ):  # Use list() to avoid modification during iteration
            best_match = None
            best_score = 0

            for project_name, project_info in archived_projects.items():
                project_job_name = project_name.replace("/", "-")
                # Check if jenkins_client is available
                if self.jenkins_client:
                    score = self.jenkins_client._calculate_job_match_score(
                        job_name, project_name, project_job_name
                    )
                else:
                    # Fallback to simple matching if no Jenkins client
                    score = 100 if job_name.startswith(project_job_name) else 0

                if score > best_score:
                    best_score = score
                    best_match = (project_name, project_info)

            if best_match and best_score > 0:
                project_name, project_info = best_match
                # Update orphaned jobs in context
                orphaned = self.jenkins_allocation_context.get_orphaned_jobs()
                orphaned[job_name] = {
                    "project_name": project_name,
                    "state": project_info.get("state", "UNKNOWN"),
                    "score": best_score,
                }
                self.jenkins_allocation_context.set_orphaned_jobs(orphaned)
                self.logger.info(
                    f"Matched orphaned job '{job_name}' to archived project '{project_name}' (state: {project_info.get('state')}, score: {best_score})"
                )

    def get_orphaned_jenkins_jobs_summary(self) -> dict[str, Any]:
        """Get summary of Jenkins jobs matched to archived projects."""
        orphaned_jobs = self.jenkins_allocation_context.get_orphaned_jobs()
        if not orphaned_jobs:
            return {"total_orphaned_jobs": 0, "by_state": {}, "jobs": {}}

        by_state: dict[str, list[str]] = {}
        for job_name, job_info in orphaned_jobs.items():
            state = job_info.get("state", "UNKNOWN")
            if state not in by_state:
                by_state[state] = []
            by_state[state].append(job_name)

        return {
            "total_orphaned_jobs": len(orphaned_jobs),
            "by_state": {state: len(jobs) for state, jobs in by_state.items()},
            "jobs": dict(orphaned_jobs),
        }

    def bucket_commit_into_windows(
        self,
        commit_datetime: datetime.datetime,
        time_windows: dict[str, dict[str, Any]],
    ) -> List[str]:
        """
        Determine which time windows a commit falls into.

        A commit belongs to a window if it occurred after the window's start time.
        """
        matching_windows = []
        commit_timestamp = commit_datetime.timestamp()

        for window_name, window_data in time_windows.items():
            if commit_timestamp >= window_data["start_timestamp"]:
                matching_windows.append(window_name)

        return matching_windows

    def extract_organizational_domain(self, full_domain: str) -> str:
        """
        Extract organizational domain from full domain by taking the last two parts.
        Uses configuration file for exceptions where full domain should be preserved.

        Examples:
        - users.noreply.github.com -> github.com
        - tnap-dev-vm-mangala.tnaplab.telekom.de -> telekom.de
        - contractor.linuxfoundation.org -> linuxfoundation.org
        - zte.com.cn -> zte.com.cn (preserved due to configuration)
        - simple.com -> simple.com (unchanged for 2-part domains)
        - localhost -> localhost (unchanged for single-part domains)
        """
        if not full_domain or full_domain in ["unknown", "localhost", ""]:
            return full_domain

        # Load domain configuration (with caching)
        if not hasattr(self, "_domain_config"):
            self._domain_config = self._load_domain_config()

        # Check if domain should be preserved in full
        if full_domain in self._domain_config.get("preserve_full_domain", []):
            return full_domain

        # Check for custom mappings
        custom_mappings = self._domain_config.get("custom_mappings", {})
        if full_domain in custom_mappings:
            return str(custom_mappings[full_domain])

        # Split domain into parts
        parts = full_domain.split(".")

        # If 2 or fewer parts, return as-is
        if len(parts) <= 2:
            return full_domain

        # Return last two parts
        return ".".join(parts[-2:])

    def _load_domain_config(self) -> dict:
        """Load organizational domain configuration from YAML file."""
        import yaml

        config_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "configuration", "organizational_domains.yaml"
        )

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}
                self.logger.debug(
                    f"Loaded organizational domain config from {config_path}"
                )
                return config
        except FileNotFoundError:
            self.logger.warning(
                f"Organizational domain config file not found: {config_path}"
            )
            return {}
        except Exception as e:
            self.logger.error(f"Error loading organizational domain config: {e}")
            return {}

    def normalize_author_identity(self, name: str, email: str) -> tuple[str, str]:
        """
        Normalize author identity with consistent format.

        - Email lowercase and trimmed
        - Username heuristic from email local part
        - Handle malformed emails gracefully
        - Domain extraction for organization analysis
        """
        # Clean and normalize inputs
        clean_name = name.strip() if name else "Unknown"
        clean_email = email.lower().strip() if email else ""

        # Handle empty or malformed emails
        if not clean_email or "@" not in clean_email:
            unknown_placeholder = self.config.get("data_quality", {}).get(
                "unknown_email_placeholder", "unknown@unknown"
            )
            clean_email = unknown_placeholder

        normalized = {
            "name": clean_name,
            "email": clean_email,
            "username": "",
            "domain": "",
        }

        # Extract username and domain from email
        if "@" in clean_email:
            # Always split on the LAST @ symbol to handle complex email addresses
            parts = clean_email.split("@")
            if len(parts) >= 2:
                normalized["username"] = "@".join(parts[:-1])
                normalized["domain"] = parts[-1].lower()
            else:
                # Shouldn't happen since we checked for @ above, but be safe
                normalized["username"] = clean_email
                normalized["domain"] = ""

        return (normalized["name"], normalized["email"])

    def _parse_git_log_output(
        self, git_output: str, repo_name: str
    ) -> List[Dict[str, Any]]:
        """
        Parse git log output into structured commit data.

        Expected format from git log --numstat --date=iso --pretty=format:%H|%ad|%an|%ae|%s
        """
        commits = []
        lines = git_output.strip().split("\n")
        current_commit = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this is a commit header line (contains |)
            if "|" in line and len(line.split("|")) >= 5:
                # Save previous commit if exists
                if current_commit:
                    commits.append(current_commit)

                # Parse commit header: hash|date|author_name|author_email|subject
                parts = line.split("|", 4)
                try:
                    commit_date = datetime.datetime.fromisoformat(
                        parts[1].replace(" ", "T")
                    )
                    if commit_date.tzinfo is None:
                        commit_date = commit_date.replace(tzinfo=datetime.timezone.utc)
                except (ValueError, IndexError):
                    self.logger.warning(
                        f"Invalid date format in {repo_name}: {parts[1] if len(parts) > 1 else 'unknown'}"
                    )
                    continue

                current_commit = {
                    "hash": parts[0],
                    "date": commit_date,
                    "author_name": parts[2],
                    "author_email": parts[3],
                    "subject": parts[4] if len(parts) > 4 else "",
                    "files_changed": [],
                }
            else:
                # Parse numstat lines (format: added<tab>removed<tab>filename)
                parts = line.split("\t")
                if len(parts) >= 3 and current_commit:
                    try:
                        # Handle binary files (marked with -)
                        added = 0 if parts[0] == "-" else int(parts[0])
                        removed = 0 if parts[1] == "-" else int(parts[1])
                        filename = parts[2]

                        # Skip binary files if configured
                        if self.config.get("data_quality", {}).get(
                            "skip_binary_changes", True
                        ):
                            if parts[0] == "-" or parts[1] == "-":
                                continue

                        files_changed = current_commit["files_changed"]
                        assert isinstance(files_changed, list)
                        files_changed.append(
                            {
                                "filename": filename,
                                "added": added,
                                "removed": removed,
                            }
                        )
                    except (ValueError, IndexError):
                        # Skip malformed lines
                        continue

        # Don't forget the last commit
        if current_commit:
            commits.append(current_commit)

        return commits

    def _update_commit_metrics(
        self, commit: dict[str, Any], metrics: dict[str, Any]
    ) -> None:
        """Process a single commit into the metrics structure."""
        applicable_windows = self.bucket_commit_into_windows(
            commit["date"], self.time_windows
        )

        # Normalize author identity
        norm_name, norm_email = self.normalize_author_identity(
            commit["author_name"], commit["author_email"]
        )
        author_email = norm_email

        # Create author info dict for compatibility
        author_info = {
            "name": norm_name,
            "email": norm_email,
            "username": norm_name.split()[0] if norm_name else "",
            "domain": self.extract_organizational_domain(norm_email.split("@")[-1])
            if "@" in norm_email
            else "",
        }

        # Calculate LOC changes for this commit
        total_added = sum(f["added"] for f in commit["files_changed"])
        total_removed = sum(f["removed"] for f in commit["files_changed"])
        net_lines = total_added - total_removed

        # Update repository metrics for each matching window
        for window in applicable_windows:
            metrics["repository"]["commit_counts"][window] += 1
            metrics["repository"]["loc_stats"][window]["added"] += total_added
            metrics["repository"]["loc_stats"][window]["removed"] += total_removed
            metrics["repository"]["loc_stats"][window]["net"] += net_lines
            metrics["repository"]["unique_contributors"][window].add(author_email)

        # Update author metrics
        if author_email not in metrics["authors"]:
            metrics["authors"][author_email] = {
                "name": author_info["name"],
                "email": author_email,
                "username": author_info["username"],
                "domain": author_info["domain"],
                "commit_counts": {window: 0 for window in self.time_windows},
                "loc_stats": {
                    window: {"added": 0, "removed": 0, "net": 0}
                    for window in self.time_windows
                },
                "repositories": {window: set() for window in self.time_windows},
            }

        # Update author metrics for each matching window
        author_metrics = metrics["authors"][author_email]
        for window in applicable_windows:
            author_metrics["commit_counts"][window] += 1
            author_metrics["loc_stats"][window]["added"] += total_added
            author_metrics["loc_stats"][window]["removed"] += total_removed
            author_metrics["loc_stats"][window]["net"] += net_lines
            author_metrics["repositories"][window].add(
                metrics["repository"]["gerrit_project"]
            )

    def _finalize_repo_metrics(self, metrics: dict[str, Any], repo_name: str) -> None:
        """Finalize repository metrics after processing all commits."""
        repo_metrics = metrics["repository"]

        # Check if repository has any commits at all
        if repo_metrics.get("has_any_commits", False):
            # Repository has commits - find last commit date
            git_command = ["git", "log", "-1", "--date=iso", "--pretty=format:%ad"]
            success, output = safe_git_command(
                git_command, Path(repo_metrics["local_path"]), self.logger
            )

            if success and output.strip():
                try:
                    last_commit_date = datetime.datetime.fromisoformat(
                        output.strip().replace(" ", "T")
                    )
                    if last_commit_date.tzinfo is None:
                        last_commit_date = last_commit_date.replace(
                            tzinfo=datetime.timezone.utc
                        )

                    repo_metrics["last_commit_timestamp"] = last_commit_date.isoformat()

                    # Calculate days since last commit
                    now = datetime.datetime.now(datetime.timezone.utc)
                    days_since = (now - last_commit_date).days
                    repo_metrics["days_since_last_commit"] = days_since

                    # Determine activity status using unified thresholds
                    current_threshold = self.config.get("activity_thresholds", {}).get(
                        "current_days", 365
                    )
                    active_threshold = self.config.get("activity_thresholds", {}).get(
                        "active_days", 1095
                    )

                    has_recent_commits = any(
                        count > 0 for count in repo_metrics["commit_counts"].values()
                    )

                    if has_recent_commits and days_since <= current_threshold:
                        repo_metrics["activity_status"] = "current"
                    elif has_recent_commits and days_since <= active_threshold:
                        repo_metrics["activity_status"] = "active"
                    else:
                        repo_metrics["activity_status"] = "inactive"

                    # Log appropriate message based on activity
                    if any(
                        count > 0 for count in repo_metrics["commit_counts"].values()
                    ):
                        self.logger.debug(
                            f"Repository {repo_name} has {repo_metrics['total_commits_ever']} commits ({sum(repo_metrics['commit_counts'].values())} recent)"
                        )
                    else:
                        self.logger.debug(
                            f"Repository {repo_name} has {repo_metrics['total_commits_ever']} commits (all historical, none recent)"
                        )

                except ValueError as e:
                    self.logger.warning(
                        f"Could not parse last commit date for {repo_name}: {e}"
                    )
        else:
            # Truly no commits - empty repository
            self.logger.info(f"Repository {repo_name} has no commits")

        # Convert author repository sets to counts for JSON serialization
        for author_email, author_data in metrics["authors"].items():
            for window in self.time_windows:
                author_data["repositories"][window] = len(
                    author_data["repositories"][window]
                )

        # Embed authors data in repository record for aggregation
        repo_authors = []
        for author_email, author_data in metrics["authors"].items():
            # Convert author data to expected format for aggregation
            author_record = {
                "name": author_data["name"],
                "email": author_data["email"],
                "username": author_data["username"],
                "domain": author_data["domain"],
                "commits": author_data["commit_counts"],
                "lines_added": {
                    window: author_data["loc_stats"][window]["added"]
                    for window in self.time_windows
                },
                "lines_removed": {
                    window: author_data["loc_stats"][window]["removed"]
                    for window in self.time_windows
                },
                "lines_net": {
                    window: author_data["loc_stats"][window]["net"]
                    for window in self.time_windows
                },
                "repositories": author_data["repositories"],
            }
            repo_authors.append(author_record)

        metrics["repository"]["authors"] = repo_authors

    def _get_repo_cache_key(self, repo_path: Path) -> Optional[str]:
        """Generate a cache key based on the repository's HEAD commit hash."""
        git_command = ["git", "rev-parse", "HEAD"]
        success, output = safe_git_command(git_command, repo_path, self.logger)

        if success and output.strip():
            head_hash = output.strip()
            # Include time windows in cache key to invalidate when windows change
            windows_key = hashlib.sha256(
                json.dumps(self.time_windows, sort_keys=True).encode()
            ).hexdigest()[:8]
            project_name = self._extract_gerrit_project(repo_path)
            # Replace path separators for cache key
            safe_project_name = project_name.replace("/", "_")
            return f"{safe_project_name}_{head_hash}_{windows_key}"

        return None

    def _get_cache_path(self, repo_path: Path) -> Optional[Path]:
        """Get the cache file path for a repository."""
        if not self.cache_dir:
            return None

        cache_key = self._get_repo_cache_key(repo_path)
        if cache_key:
            return self.cache_dir / f"{cache_key}.json"

        return None

    def _load_from_cache(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Load cached metrics for a repository if available and valid."""
        try:
            cache_path = self._get_cache_path(repo_path)
            if not cache_path or not cache_path.exists():
                return None

            with open(cache_path, "r", encoding="utf-8") as f:
                cached_data = json.load(f)

            # Validate cache structure
            if not isinstance(cached_data, dict) or "repository" not in cached_data:
                project_name = self._extract_gerrit_project(repo_path)
                self.logger.warning(f"Invalid cache structure for {project_name}")
                return None

            # Check if cache is compatible with current time windows
            cached_windows = set(
                cached_data.get("repository", {}).get("commit_counts", {}).keys()
            )
            current_windows = set(self.time_windows.keys())

            if cached_windows != current_windows:
                self.logger.debug(
                    f"Cache invalidated for {repo_path.name}: time windows changed"
                )
                return None

            return cached_data

        except (json.JSONDecodeError, IOError, KeyError) as e:
            self.logger.debug(f"Failed to load cache for {repo_path.name}: {e}")
            return None

    def _save_cached_metrics(self, repo_path: Path, metrics: dict[str, Any]) -> None:
        """Save metrics to cache for future use."""
        try:
            cache_path = self._get_cache_path(repo_path)
            if not cache_path:
                return

            # Create a cache-friendly copy (convert sets to lists if any remain)
            cache_data = json.loads(json.dumps(metrics, default=str))

            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, default=str)

            self.logger.debug(f"Saved cache for {repo_path.name}")

        except (IOError, TypeError) as e:
            self.logger.warning(f"Failed to save cache for {repo_path.name}: {e}")
