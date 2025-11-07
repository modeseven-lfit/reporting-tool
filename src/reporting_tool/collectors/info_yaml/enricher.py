# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
INFO.yaml enricher module.

Enriches INFO.yaml project data with Git repository information,
calculating committer activity status and coloring based on recent commits.

Supports both synchronous and asynchronous URL validation for optimal performance.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple

from domain.info_yaml import CommitterInfo, ProjectInfo
from src.reporting_tool.collectors.info_yaml.matcher import CommitterMatcher
from src.reporting_tool.collectors.info_yaml.validator import URLValidator

logger = logging.getLogger(__name__)


class InfoYamlEnricher:
    """
    Enriches INFO.yaml project data with Git repository information.

    Matches projects to Git repositories, determines committer activity status,
    assigns color codes, and validates issue tracker URLs.
    """

    def __init__(
        self,
        activity_windows: Optional[Dict[str, int]] = None,
        validate_urls: bool = True,
        url_timeout: float = 10.0,
        url_retries: int = 2,
    ):
        """
        Initialize the enricher.

        Args:
            activity_windows: Activity thresholds in days
                {
                    "current": 365,  # Green - active within 365 days
                    "active": 1095,  # Orange - active 365-1095 days ago
                    # Red - inactive 1095+ days (implicit)
                }
            validate_urls: Enable URL validation (default: True)
            url_timeout: URL validation timeout in seconds (default: 10.0)
            url_retries: URL validation retry count (default: 2)
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # Activity windows
        self.activity_windows = activity_windows or {
            "current": 365,
            "active": 1095,
        }

        # URL validation settings
        self.validate_urls = validate_urls
        self.url_validator = URLValidator(
            timeout=url_timeout,
            retries=url_retries,
            cache_enabled=True,
        )

        # Committer matcher
        self.matcher = CommitterMatcher()

        self.logger.info("InfoYamlEnricher initialized")
        self.logger.debug(f"Activity windows: {self.activity_windows}")
        self.logger.debug(f"URL validation: {self.validate_urls}")

    def enrich_project(
        self,
        project: ProjectInfo,
        git_metrics: List[Dict[str, Any]],
    ) -> ProjectInfo:
        """
        Enrich a single project with Git data.

        Args:
            project: ProjectInfo object to enrich
            git_metrics: List of repository metrics from Git analysis

        Returns:
            Enriched ProjectInfo object
        """
        # Build repository lookup
        repo_lookup = self._build_repo_lookup(git_metrics)

        # Find matching repositories
        matched_repos = self._find_matching_repos(project, repo_lookup)

        if matched_repos:
            # Enrich with Git data
            project = self._enrich_with_git_data(project, matched_repos)
        else:
            # No Git data - mark as unknown
            project = self._mark_as_unknown(project)

        # Validate issue tracker URL
        if self.validate_urls and project.issue_tracking.url:
            is_valid, error = self.url_validator.validate(project.issue_tracking.url)
            project.issue_tracking.is_valid = is_valid
            project.issue_tracking.validation_error = error

        return project

    def enrich_projects(
        self,
        projects: List[ProjectInfo],
        git_metrics: List[Dict[str, Any]],
        use_async_validation: bool = True,
        max_concurrent_urls: int = 10,
    ) -> List[ProjectInfo]:
        """
        Enrich multiple projects with Git data.

        Args:
            projects: List of ProjectInfo objects to enrich
            git_metrics: List of repository metrics from Git analysis
            use_async_validation: Use async URL validation for better performance
            max_concurrent_urls: Maximum concurrent URL validations

        Returns:
            List of enriched ProjectInfo objects
        """
        # First pass: enrich with Git data (no URL validation yet)
        enriched = []
        for project in projects:
            enriched_project = self._enrich_project_without_url(project, git_metrics)
            enriched.append(enriched_project)

        # Second pass: batch validate URLs if enabled
        if self.validate_urls:
            if use_async_validation:
                self._validate_urls_async_batch(enriched, max_concurrent_urls)
            else:
                self._validate_urls_sync_batch(enriched)

        self.logger.info(f"Enriched {len(enriched)} projects")
        return enriched

    def _enrich_project_without_url(
        self,
        project: ProjectInfo,
        git_metrics: List[Dict[str, Any]],
    ) -> ProjectInfo:
        """
        Enrich a project with Git data without URL validation.

        Args:
            project: ProjectInfo object to enrich
            git_metrics: List of repository metrics from Git analysis

        Returns:
            Enriched ProjectInfo object (URLs not yet validated)
        """
        # Build repository lookup
        repo_lookup = self._build_repo_lookup(git_metrics)

        # Find matching repositories
        matched_repos = self._find_matching_repos(project, repo_lookup)

        if matched_repos:
            # Enrich with Git data
            project = self._enrich_with_git_data(project, matched_repos)
        else:
            # No Git data - mark as unknown
            project = self._mark_as_unknown(project)

        return project

    def _validate_urls_sync_batch(self, projects: List[ProjectInfo]) -> None:
        """
        Validate URLs synchronously for a batch of projects.

        Args:
            projects: List of ProjectInfo objects to validate
        """
        for project in projects:
            if project.issue_tracking.url:
                is_valid, error = self.url_validator.validate(
                    project.issue_tracking.url
                )
                project.issue_tracking.is_valid = is_valid
                project.issue_tracking.validation_error = error

    def _validate_urls_async_batch(
        self, projects: List[ProjectInfo], max_concurrent: int = 10
    ) -> None:
        """
        Validate URLs asynchronously for a batch of projects.

        Args:
            projects: List of ProjectInfo objects to validate
            max_concurrent: Maximum concurrent validations
        """
        # Collect all URLs to validate
        url_to_projects: Dict[str, List[ProjectInfo]] = {}
        for project in projects:
            url = project.issue_tracking.url
            if url:
                if url not in url_to_projects:
                    url_to_projects[url] = []
                url_to_projects[url].append(project)

        if not url_to_projects:
            return

        # Validate all URLs asynchronously
        urls = list(url_to_projects.keys())
        self.logger.info(
            f"Validating {len(urls)} unique URLs asynchronously "
            f"(max_concurrent={max_concurrent})"
        )

        # Always use asyncio.run() in synchronous context
        results = asyncio.run(
            self.url_validator.validate_bulk_async(urls, max_concurrent)
        )

        # Apply results to projects
        for url, (is_valid, error) in results.items():
            for project in url_to_projects[url]:
                project.issue_tracking.is_valid = is_valid
                project.issue_tracking.validation_error = error

    def _build_repo_lookup(
        self, git_metrics: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build a lookup dictionary from Git metrics.

        Args:
            git_metrics: List of repository metrics

        Returns:
            Dictionary mapping Gerrit project path to metrics
        """
        lookup = {}

        for metrics in git_metrics:
            repo_info = metrics.get("repository", {})
            gerrit_project = repo_info.get("gerrit_project", "")

            if gerrit_project:
                lookup[gerrit_project] = metrics

        self.logger.debug(f"Built repo lookup with {len(lookup)} repositories")
        return lookup

    def _find_matching_repos(
        self,
        project: ProjectInfo,
        repo_lookup: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Find Git repositories matching a project.

        Tries:
        1. Exact match on project_path
        2. Match on listed repositories

        Args:
            project: ProjectInfo object
            repo_lookup: Repository lookup dictionary

        Returns:
            List of matching repository metrics
        """
        matched = []

        # Try exact match on project path
        if project.project_path in repo_lookup:
            matched.append(repo_lookup[project.project_path])
            self.logger.debug(
                f"Matched project '{project.project_name}' via project_path"
            )

        # Try matching against listed repositories
        for repo_name in project.repositories:
            if repo_name in repo_lookup:
                # Avoid duplicates
                repo_metrics = repo_lookup[repo_name]
                if repo_metrics not in matched:
                    matched.append(repo_metrics)
                    self.logger.debug(
                        f"Matched project '{project.project_name}' via repository '{repo_name}'"
                    )

        return matched

    def _enrich_with_git_data(
        self,
        project: ProjectInfo,
        matched_repos: List[Dict[str, Any]],
    ) -> ProjectInfo:
        """
        Enrich project with Git data from matched repositories.

        Args:
            project: ProjectInfo object
            matched_repos: List of matching repository metrics

        Returns:
            Enriched ProjectInfo object
        """
        # Find most recent activity across all repos
        most_recent_days = self._find_most_recent_activity(matched_repos)

        # Calculate activity status and color
        status, color = self._calculate_activity_status(most_recent_days)

        # Apply to all committers (project-level coloring)
        enriched_committers = []
        for committer in project.committers:
            enriched_committer = CommitterInfo(
                name=committer.name,
                email=committer.email,
                company=committer.company,
                id=committer.id,
                timezone=committer.timezone,
                activity_status=status,
                activity_color=color,
                days_since_last_commit=most_recent_days,
            )
            enriched_committers.append(enriched_committer)

        # Update project
        project.committers = enriched_committers
        project.has_git_data = True
        project.project_days_since_last_commit = most_recent_days

        self.logger.debug(
            f"Enriched project '{project.project_name}': "
            f"status={status}, color={color}, days={most_recent_days}"
        )

        return project

    def _mark_as_unknown(self, project: ProjectInfo) -> ProjectInfo:
        """
        Mark project committers as unknown activity.

        Args:
            project: ProjectInfo object

        Returns:
            ProjectInfo with committers marked as unknown
        """
        enriched_committers = []
        for committer in project.committers:
            enriched_committer = CommitterInfo(
                name=committer.name,
                email=committer.email,
                company=committer.company,
                id=committer.id,
                timezone=committer.timezone,
                activity_status="unknown",
                activity_color="gray",
                days_since_last_commit=None,
            )
            enriched_committers.append(enriched_committer)

        project.committers = enriched_committers
        project.has_git_data = False
        project.project_days_since_last_commit = None

        self.logger.debug(
            f"No Git data for project '{project.project_name}', marked as unknown"
        )

        return project

    def _find_most_recent_activity(
        self, matched_repos: List[Dict[str, Any]]
    ) -> Optional[int]:
        """
        Find the most recent activity across multiple repositories.

        Args:
            matched_repos: List of repository metrics

        Returns:
            Days since most recent commit, or None if no data
        """
        most_recent = None

        for repo_metrics in matched_repos:
            repo_info = repo_metrics.get("repository", {})
            days_since = repo_info.get("days_since_last_commit")

            if days_since is not None:
                if most_recent is None or days_since < most_recent:
                    most_recent = days_since

        return most_recent

    def _calculate_activity_status(
        self, days_since_commit: Optional[int]
    ) -> Tuple[str, str]:
        """
        Calculate activity status and color based on days since last commit.

        Args:
            days_since_commit: Days since last commit (None if no data)

        Returns:
            Tuple of (status, color):
            - ("current", "green"): Active within current window
            - ("active", "orange"): Active within active window
            - ("inactive", "red"): No activity beyond active window
            - ("unknown", "gray"): No Git data available
        """
        if days_since_commit is None:
            return ("unknown", "gray")

        current_window = self.activity_windows.get("current", 365)
        active_window = self.activity_windows.get("active", 1095)

        if days_since_commit <= current_window:
            return ("current", "green")
        elif days_since_commit <= active_window:
            return ("active", "orange")
        else:
            return ("inactive", "red")

    def get_enrichment_statistics(
        self, projects: List[ProjectInfo]
    ) -> Dict[str, Any]:
        """
        Get statistics about enrichment results.

        Args:
            projects: List of enriched ProjectInfo objects

        Returns:
            Dictionary with enrichment statistics
        """
        stats: Dict[str, Any] = {
            "total_projects": len(projects),
            "with_git_data": 0,
            "without_git_data": 0,
            "status_counts": {
                "current": 0,
                "active": 0,
                "inactive": 0,
                "unknown": 0,
            },
            "color_counts": {
                "green": 0,
                "orange": 0,
                "red": 0,
                "gray": 0,
            },
            "url_validation": {
                "total_urls": 0,
                "valid_urls": 0,
                "invalid_urls": 0,
                "no_url": 0,
            },
        }

        for project in projects:
            # Git data
            if project.has_git_data:
                stats["with_git_data"] += 1
            else:
                stats["without_git_data"] += 1

            # Count committer statuses
            for committer in project.committers:
                status = committer.activity_status
                color = committer.activity_color
                stats["status_counts"][status] = (
                    stats["status_counts"].get(status, 0) + 1
                )
                stats["color_counts"][color] = (
                    stats["color_counts"].get(color, 0) + 1
                )

            # URL validation
            if project.issue_tracking.url:
                stats["url_validation"]["total_urls"] += 1
                if project.issue_tracking.is_valid:
                    stats["url_validation"]["valid_urls"] += 1
                else:
                    stats["url_validation"]["invalid_urls"] += 1
            else:
                stats["url_validation"]["no_url"] += 1

        return stats

    def clear_url_cache(self) -> None:
        """Clear the URL validation cache."""
        self.url_validator.clear_cache()
        self.logger.debug("URL validation cache cleared")

    def get_url_cache_stats(self) -> Dict[str, int]:
        """
        Get URL validation cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return self.url_validator.get_cache_stats()


def enrich_project_with_git_data(
    project: ProjectInfo,
    git_metrics: List[Dict[str, Any]],
    activity_windows: Optional[Dict[str, int]] = None,
) -> ProjectInfo:
    """
    Convenience function to enrich a single project.

    Args:
        project: ProjectInfo object to enrich
        git_metrics: List of repository metrics
        activity_windows: Optional activity thresholds

    Returns:
        Enriched ProjectInfo object
    """
    enricher = InfoYamlEnricher(activity_windows=activity_windows)
    return enricher.enrich_project(project, git_metrics)


def enrich_projects_with_git_data(
    projects: List[ProjectInfo],
    git_metrics: List[Dict[str, Any]],
    activity_windows: Optional[Dict[str, int]] = None,
    use_async_validation: bool = True,
    max_concurrent_urls: int = 10,
) -> List[ProjectInfo]:
    """
    Convenience function to enrich multiple projects.

    Args:
        projects: List of ProjectInfo objects to enrich
        git_metrics: List of repository metrics
        activity_windows: Optional activity thresholds
        use_async_validation: Use async URL validation for better performance
        max_concurrent_urls: Maximum concurrent URL validations

    Returns:
        List of enriched ProjectInfo objects
    """
    enricher = InfoYamlEnricher(activity_windows=activity_windows)
    return enricher.enrich_projects(
        projects,
        git_metrics,
        use_async_validation=use_async_validation,
        max_concurrent_urls=max_concurrent_urls,
    )
