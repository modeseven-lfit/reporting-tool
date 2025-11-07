# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Render context builder for preparing data for template rendering.

This module provides the RenderContext class which transforms raw report data
into a structured context suitable for Jinja2 templates. It handles data
extraction, formatting, and organization.

Phase: 8 - Renderer Modernization
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from .formatters import (
    format_number,
    format_age,
    format_percentage,
    format_date,
    get_template_filters,
)


class RenderContext:
    """
    Builds rendering context from report data.

    This class prepares data for template rendering by:
    - Extracting relevant data from raw report structure
    - Formatting values for display
    - Organizing data into logical sections
    - Providing template-friendly data structures

    Thread Safety:
        This class is stateless and thread-safe. Each render operation
        creates a new context instance.

    Example:
        >>> data = load_report_data()
        >>> config = load_config()
        >>> context = RenderContext(data, config)
        >>> template_vars = context.build()
        >>> # Use template_vars in Jinja2 templates
    """

    def __init__(self, data: Dict[str, Any], config: Dict[str, Any]):
        """
        Initialize render context.

        Args:
            data: Raw report data (from JSON)
            config: Configuration dictionary
        """
        self.data = data
        self.config = config

    def build(self) -> Dict[str, Any]:
        """
        Build complete rendering context.

        Returns:
            Dictionary with all context data for templates
        """
        return {
            "project": self._build_project_context(),
            "summary": self._build_summary_context(),
            "repositories": self._build_repositories_context(),
            "contributors": self._build_contributors_context(),
            "organizations": self._build_organizations_context(),
            "features": self._build_features_context(),
            "workflows": self._build_workflows_context(),
            "orphaned_jobs": self._build_orphaned_jobs_context(),
            "time_windows": self._build_time_windows_context(),
            "config": self._build_config_context(),
            "filters": get_template_filters(),
        }

    def _build_project_context(self) -> Dict[str, Any]:
        """Build project-level metadata context."""
        metadata = self.data.get("metadata", {})

        return {
            "name": self.data.get("project", "Repository Analysis"),
            "schema_version": self.data.get("schema_version", "1.0.0"),
            "generated_at": metadata.get("generated_at", datetime.now().isoformat()),
            "generated_at_formatted": format_date(
                metadata.get("generated_at"),
                "%B %d, %Y at %H:%M:%S UTC"
            ),
            "report_version": metadata.get("report_version", "1.0.0"),
        }

    def _build_summary_context(self) -> Dict[str, Any]:
        """Build summary statistics context."""
        summaries = self.data.get("summaries", {})
        counts = summaries.get("counts", {})

        # Calculate totals
        total_commits = sum(
            repo.get("total_commits", 0)
            for repo in self.data.get("repositories", [])
        )

        total_lines_added = sum(
            repo.get("total_lines_added", 0)
            for repo in self.data.get("repositories", [])
        )

        total_lines_removed = sum(
            repo.get("total_lines_removed", 0)
            for repo in self.data.get("repositories", [])
        )

        repositories_analyzed = counts.get("repositories_analyzed", 0)
        total_repositories = counts.get("total_gerrit_projects", repositories_analyzed)

        return {
            "repositories_analyzed": repositories_analyzed,
            "total_repositories": total_repositories,
            "unique_contributors": counts.get("unique_contributors", 0),
            "total_commits": total_commits,
            "total_commits_formatted": format_number(total_commits),
            "total_organizations": counts.get("total_organizations", 0),
            "active_count": counts.get("active_repositories", 0),
            "inactive_count": counts.get("inactive_repositories", 0),
            "no_commit_count": counts.get("no_commit_repositories", 0),
            "total_lines_added": total_lines_added,
            "total_lines_added_formatted": format_number(total_lines_added),
            "total_lines_removed": total_lines_removed,
            "total_lines_removed_formatted": format_number(total_lines_removed),
            "net_lines": total_lines_added - total_lines_removed,
            "net_lines_formatted": format_number(total_lines_added - total_lines_removed),
        }

    def _build_repositories_context(self) -> Dict[str, Any]:
        """Build repositories section context."""
        summaries = self.data.get("summaries", {})

        all_repos = summaries.get("all_repositories", [])
        no_commit_repos = summaries.get("no_commit_repositories", [])

        # Sort repositories by activity
        active_repos = [r for r in all_repos if r.get("activity_status") == "active"]
        inactive_repos = [r for r in all_repos if r.get("activity_status") == "inactive"]

        return {
            "all": all_repos,
            "all_count": len(all_repos),
            "active": active_repos,
            "active_count": len(active_repos),
            "inactive": inactive_repos,
            "inactive_count": len(inactive_repos),
            "no_commits": no_commit_repos,
            "no_commits_count": len(no_commit_repos),
            "has_repositories": len(all_repos) > 0,
        }

    def _build_contributors_context(self) -> Dict[str, Any]:
        """Build contributors leaderboard context."""
        summaries = self.data.get("summaries", {})

        top_commits = summaries.get("top_contributors_commits", [])
        top_loc = summaries.get("top_contributors_loc", [])

        # Limit to top N (from config or default 20)
        limit = self.config.get("output", {}).get("top_contributors_limit", 20)

        return {
            "top_by_commits": top_commits[:limit],
            "top_by_commits_count": len(top_commits),
            "top_by_loc": top_loc[:limit],
            "top_by_loc_count": len(top_loc),
            "limit": limit,
            "has_contributors": len(top_commits) > 0 or len(top_loc) > 0,
        }

    def _build_organizations_context(self) -> Dict[str, Any]:
        """Build organizations leaderboard context."""
        summaries = self.data.get("summaries", {})

        top_orgs = summaries.get("top_organizations", [])

        # Limit to top N
        limit = self.config.get("output", {}).get("top_organizations_limit", 20)

        return {
            "top": top_orgs[:limit],
            "total_count": len(top_orgs),
            "limit": limit,
            "has_organizations": len(top_orgs) > 0,
        }

    def _build_features_context(self) -> Dict[str, Any]:
        """Build feature matrix context."""
        repositories = self.data.get("repositories", [])

        # Extract unique features
        all_features = set()
        for repo in repositories:
            features = repo.get("features", {})
            all_features.update(features.keys())

        # Sort features alphabetically
        features_list = sorted(all_features)

        # Build feature matrix
        feature_matrix = []
        for repo in repositories:
            repo_features = repo.get("features", {})
            feature_matrix.append({
                "repo_name": repo.get("gerrit_project", repo.get("name", "Unknown")),
                "features": {
                    feature: repo_features.get(feature, False)
                    for feature in features_list
                }
            })

        return {
            "features_list": features_list,
            "feature_count": len(features_list),
            "matrix": feature_matrix,
            "repositories_count": len(repositories),
            "has_features": len(features_list) > 0,
        }

    def _build_workflows_context(self) -> Dict[str, Any]:
        """Build CI/CD workflows/jobs context."""
        repositories = self.data.get("repositories", [])

        # Collect all workflows with status
        workflows = []
        for repo in repositories:
            jenkins_jobs = repo.get("jenkins_jobs", [])
            for job in jenkins_jobs:
                workflows.append({
                    "name": job.get("name", "Unknown"),
                    "repo": repo.get("gerrit_project", "Unknown"),
                    "status": job.get("status", "unknown"),
                    "url": job.get("url", ""),
                    "color": self._get_status_color(job.get("color", "notbuilt")),
                })

        # Count by status
        status_counts: Dict[str, int] = {}
        for workflow in workflows:
            status = workflow["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "all": workflows,
            "total_count": len(workflows),
            "status_counts": status_counts,
            "has_workflows": len(workflows) > 0,
        }

    def _build_orphaned_jobs_context(self) -> Dict[str, Any]:
        """Build orphaned Jenkins jobs context."""
        orphaned_data = self.data.get("orphaned_jenkins_jobs", {})

        jobs = orphaned_data.get("jobs", {})
        by_state = orphaned_data.get("by_state", {})

        # Convert to list for template
        jobs_list = [
            {
                "name": name,
                "project": info.get("project_name", "Unknown"),
                "state": info.get("state", "UNKNOWN"),
                "score": info.get("score", 0),
            }
            for name, info in jobs.items()
        ]

        # Sort by state, then by name
        jobs_list.sort(key=lambda x: (x["state"], x["name"]))

        return {
            "jobs": jobs_list,
            "total_count": orphaned_data.get("total_orphaned_jobs", 0),
            "by_state": by_state,
            "has_orphaned_jobs": len(jobs_list) > 0,
        }

    def _build_time_windows_context(self) -> List[Dict[str, Any]]:
        """Build time windows context."""
        time_windows = self.data.get("time_windows", [])

        return [
            {
                "name": tw.get("name", "Unknown"),
                "days": tw.get("days", 0),
                "description": tw.get("description", ""),
            }
            for tw in time_windows
        ]

    def _build_config_context(self) -> Dict[str, Any]:
        """Build configuration context for templates."""
        output_config = self.config.get("output", {})
        include_sections = output_config.get("include_sections", {})

        return {
            "theme": self.config.get("render", {}).get("theme", "default"),
            "include_sections": {
                "title": include_sections.get("title", True),
                "summary": include_sections.get("summary", True),
                "repositories": include_sections.get("repositories", True),
                "contributors": include_sections.get("contributors", True),
                "organizations": include_sections.get("organizations", True),
                "features": include_sections.get("features", True),
                "workflows": include_sections.get("workflows", True),
                "orphaned_jobs": include_sections.get("orphaned_jobs", True),
            },
            "project_name": self.config.get("project", {}).get("name", "Repository Analysis"),
        }

    def _get_status_color(self, jenkins_color: str) -> str:
        """
        Map Jenkins color to semantic status.

        Args:
            jenkins_color: Jenkins job color (e.g., 'blue', 'red', 'yellow')

        Returns:
            Semantic color name (success, failure, warning, disabled, unknown)
        """
        color_map = {
            "blue": "success",
            "blue_anime": "success",
            "green": "success",
            "red": "failure",
            "red_anime": "failure",
            "yellow": "warning",
            "yellow_anime": "warning",
            "aborted": "warning",
            "disabled": "disabled",
            "grey": "disabled",
            "notbuilt": "unknown",
        }

        return color_map.get(jenkins_color.lower(), "unknown")
