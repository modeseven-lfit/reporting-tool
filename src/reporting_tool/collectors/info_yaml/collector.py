# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
INFO.yaml collector module.

Collects and processes INFO.yaml files from the LF info-master repository,
providing project metadata and committer information for reporting.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain.info_yaml import LifecycleSummary, ProjectInfo
from src.reporting_tool.collectors.base import BaseCollector
from src.reporting_tool.collectors.info_yaml.enricher import InfoYamlEnricher
from src.reporting_tool.collectors.info_yaml.parser import INFOYamlParser

logger = logging.getLogger(__name__)


class INFOYamlCollector(BaseCollector):
    """
    Collector for INFO.yaml project metadata.

    Scans the info-master repository for INFO.yaml files, parses them,
    and provides structured project information for reporting.

    Configuration:
        enabled: Whether INFO.yaml collection is enabled (default: True)
        local_path: Path to local info-master repository
        clone_url: URL to clone info-master if local_path doesn't exist
        activity_windows: Activity thresholds for committer coloring
        validate_urls: Whether to validate issue tracker URLs (default: True)
        url_timeout: Timeout for URL validation in seconds (default: 10.0)
        url_retries: Number of retries for URL validation (default: 2)
        disable_archived_reports: Exclude archived projects (default: True)
        filter_by_gerrit_server: Only include specific Gerrit server (optional)
        cache_parsed_data: Enable caching of parsed data (default: True)
        cache_ttl: Cache time-to-live in seconds (default: 3600)
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the INFO.yaml collector.

        Args:
            config: Configuration dictionary with 'info_yaml' section
        """
        super().__init__(config)

        # Extract INFO.yaml-specific config
        self.info_config = self.config.get("info_yaml", {})

        # Repository path configuration
        self.local_path = self.info_config.get("local_path")
        self.clone_url = self.info_config.get("clone_url")

        # Activity window thresholds (in days)
        self.activity_windows = {
            "current": 365,  # Green - commits within last 365 days
            "active": 1095,  # Orange - commits between 365-1095 days
            # Red - no commits in 1095+ days
        }

        # Allow configuration overrides
        config_windows = self.info_config.get("activity_windows", {})
        self.activity_windows.update(config_windows)

        # URL validation settings
        self.validate_urls = self.info_config.get("validate_urls", True)
        self.url_timeout = self.info_config.get("url_timeout", 10.0)
        self.url_retries = self.info_config.get("url_retries", 2)

        # Filtering options
        self.disable_archived = self.info_config.get("disable_archived_reports", True)
        self.filter_gerrit_server = self.info_config.get("filter_by_gerrit_server")

        # Caching settings
        self.cache_enabled = self.info_config.get("cache_parsed_data", True)
        self.cache_ttl = self.info_config.get("cache_ttl", 3600)

        # Internal state
        self.info_master_path: Optional[Path] = None
        self.parser: Optional[INFOYamlParser] = None
        self.enricher: Optional[InfoYamlEnricher] = None
        self.projects: List[ProjectInfo] = []
        self._cache: Dict[str, Any] = {}

        self.logger.info("INFOYamlCollector initialized")
        self.logger.debug(f"Activity windows: {self.activity_windows}")
        self.logger.debug(f"URL validation: {self.validate_urls}")
        self.logger.debug(f"Disable archived: {self.disable_archived}")

    def collect(self, source: Path, **kwargs) -> Dict[str, Any]:
        """
        Collect INFO.yaml data from the info-master repository.

        Args:
            source: Path to the info-master repository (or parent directory)
            **kwargs: Additional arguments:
                - gerrit_server: Filter by specific Gerrit server
                - include_archived: Override disable_archived setting
                - git_metrics: Optional Git repository metrics for enrichment

        Returns:
            Dictionary with collected INFO.yaml data:
                {
                    "projects": List of ProjectInfo dictionaries,
                    "lifecycle_summary": Lifecycle state statistics,
                    "total_projects": Total number of projects,
                    "servers": List of unique Gerrit servers,
                }

        Raises:
            ValueError: If source is invalid or collection fails
        """
        # Validate source
        if not self.validate_source(source):
            raise ValueError(f"Invalid source path: {source}")

        # Set info-master path
        self._set_info_master_path(source)

        if not self.info_master_path:
            raise ValueError("Failed to determine info-master path")

        # Initialize parser
        self.parser = INFOYamlParser(self.info_master_path)

        # Initialize enricher
        self.enricher = InfoYamlEnricher(
            activity_windows=self.activity_windows,
            validate_urls=self.validate_urls,
            url_timeout=self.url_timeout,
            url_retries=self.url_retries,
        )

        # Parse all INFO.yaml files
        self.logger.info(f"Collecting INFO.yaml files from: {self.info_master_path}")
        self.projects = self.parser.parse_directory(self.info_master_path)

        if not self.projects:
            self.logger.warning("No INFO.yaml files found or parsed")
            return self._empty_result()

        self.logger.info(f"Collected {len(self.projects)} projects")

        # Apply filters
        filtered_projects = self._apply_filters(
            self.projects,
            gerrit_server=kwargs.get("gerrit_server", self.filter_gerrit_server),
            include_archived=kwargs.get("include_archived", not self.disable_archived),
        )

        self.logger.info(
            f"After filtering: {len(filtered_projects)} projects "
            f"(excluded {len(self.projects) - len(filtered_projects)})"
        )

        # Enrich with Git data if provided
        git_metrics = kwargs.get("git_metrics", [])
        if git_metrics and self.enricher:
            self.logger.info(f"Enriching projects with Git data from {len(git_metrics)} repositories")
            filtered_projects = self.enricher.enrich_projects(filtered_projects, git_metrics)

            # Get enrichment statistics
            stats = self.enricher.get_enrichment_statistics(filtered_projects)
            self.logger.info(
                f"Enrichment complete: {stats['with_git_data']} projects with Git data, "
                f"{stats['without_git_data']} without"
            )

        # Generate lifecycle summary
        lifecycle_summary = self._generate_lifecycle_summary(filtered_projects)

        # Get unique servers
        servers = sorted(set(p.gerrit_server for p in filtered_projects))

        # Build result
        result = {
            "projects": [p.to_dict() for p in filtered_projects],
            "lifecycle_summary": [s.to_dict() for s in lifecycle_summary],
            "total_projects": len(filtered_projects),
            "servers": servers,
            "activity_windows": self.activity_windows,
        }

        return result

    def collect_for_server(
        self, source: Path, gerrit_server: str, **kwargs
    ) -> Dict[str, Any]:
        """
        Collect INFO.yaml data for a specific Gerrit server.

        Args:
            source: Path to the info-master repository
            gerrit_server: Gerrit server to filter by (e.g., "gerrit.onap.org")

        Returns:
            Dictionary with filtered project data
        """
        return self.collect(source, gerrit_server=gerrit_server, **kwargs)

    def get_project_by_path(self, project_path: str) -> Optional[ProjectInfo]:
        """
        Get a specific project by its path.

        Args:
            project_path: Project path (e.g., "foo/bar")

        Returns:
            ProjectInfo object or None if not found
        """
        for project in self.projects:
            if project.project_path == project_path:
                return project
        return None

    def get_projects_by_server(self, gerrit_server: str) -> List[ProjectInfo]:
        """
        Get all projects for a specific Gerrit server.

        Args:
            gerrit_server: Gerrit server name

        Returns:
            List of ProjectInfo objects
        """
        return [p for p in self.projects if p.gerrit_server == gerrit_server]

    def get_lifecycle_summary(
        self, projects: Optional[List[ProjectInfo]] = None
    ) -> List[LifecycleSummary]:
        """
        Generate lifecycle state summary statistics.

        Args:
            projects: List of projects to summarize (defaults to all collected)

        Returns:
            List of LifecycleSummary objects
        """
        if projects is None:
            projects = self.projects

        return self._generate_lifecycle_summary(projects)

    def _set_info_master_path(self, source: Path) -> None:
        """
        Determine the info-master repository path.

        Args:
            source: Source path (may be info-master root or parent)
        """
        # If local_path is configured, use it
        if self.local_path:
            path = Path(self.local_path)
            if path.exists():
                self.info_master_path = path
                self.logger.info(f"Using configured info-master path: {path}")
                return

        # Check if source is info-master directory
        if source.name == "info-master" and source.exists():
            self.info_master_path = source
            self.logger.info(f"Using source as info-master path: {source}")
            return

        # Check if info-master is a subdirectory of source
        info_master_subdir = source / "info-master"
        if info_master_subdir.exists():
            self.info_master_path = info_master_subdir
            self.logger.info(f"Found info-master subdirectory: {info_master_subdir}")
            return

        # Fall back to source
        self.info_master_path = source
        self.logger.warning(
            f"Could not determine info-master path, using source: {source}"
        )

    def _apply_filters(
        self,
        projects: List[ProjectInfo],
        gerrit_server: Optional[str] = None,
        include_archived: bool = False,
    ) -> List[ProjectInfo]:
        """
        Apply filters to project list.

        Args:
            projects: List of projects to filter
            gerrit_server: Filter by specific Gerrit server (optional)
            include_archived: Include archived projects (default: False)

        Returns:
            Filtered list of projects
        """
        filtered = projects

        # Filter by Gerrit server
        if gerrit_server:
            filtered = [p for p in filtered if p.gerrit_server == gerrit_server]
            self.logger.debug(
                f"Filtered by server '{gerrit_server}': {len(filtered)} projects"
            )

        # Filter out archived projects
        if not include_archived:
            initial_count = len(filtered)
            filtered = [p for p in filtered if not p.is_archived]
            excluded = initial_count - len(filtered)
            if excluded > 0:
                self.logger.debug(f"Excluded {excluded} archived projects")

        return filtered

    def _generate_lifecycle_summary(
        self, projects: List[ProjectInfo]
    ) -> List[LifecycleSummary]:
        """
        Generate lifecycle state summary statistics.

        Args:
            projects: List of projects to summarize

        Returns:
            List of LifecycleSummary objects sorted by count (descending)
        """
        if not projects:
            return []

        # Count projects by lifecycle state
        state_counts: Dict[str, int] = {}
        for project in projects:
            state = project.lifecycle_state
            state_counts[state] = state_counts.get(state, 0) + 1

        # Calculate percentages and create summary objects
        total = len(projects)
        summaries = []

        for state, count in state_counts.items():
            percentage = (count / total * 100) if total > 0 else 0.0
            summary = LifecycleSummary(
                state=state,
                count=count,
                percentage=round(percentage, 1),
            )
            summaries.append(summary)

        # Sort by count (descending)
        summaries.sort(key=lambda s: s.count, reverse=True)

        return summaries

    def _empty_result(self) -> Dict[str, Any]:
        """
        Return empty result structure.

        Returns:
            Empty result dictionary
        """
        return {
            "projects": [],
            "lifecycle_summary": [],
            "total_projects": 0,
            "servers": [],
            "activity_windows": self.activity_windows,
        }

    def is_enabled(self) -> bool:
        """
        Check if INFO.yaml collection is enabled.

        Returns:
            True if enabled in configuration
        """
        return bool(self.info_config.get("enabled", True))

    def get_enrichment_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Get enrichment statistics for the last collection.

        Returns:
            Dictionary with enrichment statistics or None if no enricher
        """
        if not self.enricher or not self.projects:
            return None

        return self.enricher.get_enrichment_statistics(self.projects)

    def clear_url_cache(self) -> None:
        """Clear the URL validation cache."""
        if self.enricher:
            self.enricher.clear_url_cache()
            self.logger.debug("URL validation cache cleared")

    def get_url_cache_stats(self) -> Optional[Dict[str, int]]:
        """
        Get URL validation cache statistics.

        Returns:
            Dictionary with cache statistics or None if no enricher
        """
        if not self.enricher:
            return None

        return self.enricher.get_url_cache_stats()
