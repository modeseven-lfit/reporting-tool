# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Data aggregator for repository metrics.

This module provides the DataAggregator class for aggregating repository
metrics into global summaries including:
- Repository classification (current/active/inactive)
- Author and organization rollups
- Top/least active repository identification
- Contributor leaderboards
- Activity status distribution analysis
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, cast


class DataAggregator:
    """Handles aggregation of repository data into global summaries."""

    def __init__(self, config: dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    def aggregate_global_data(
        self, repo_metrics: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Aggregate all repository metrics into global summaries.

        Performs comprehensive aggregation including:
        - Active/inactive classification
        - Author and organization rollups
        - Top/least active repository identification
        - Contributor leaderboards
        - Age distribution analysis
        """
        self.logger.info("Starting global data aggregation")

        # Debug: Analyze repository commit status
        self._analyze_repository_commit_status(repo_metrics)

        # Configuration values for unified activity status
        current_threshold = self.config.get("activity_thresholds", {}).get(
            "current_days", 365
        )
        active_threshold = self.config.get("activity_thresholds", {}).get(
            "active_days", 1095
        )

        # Primary time window for rankings (usually last_365_days)
        primary_window = "last_365_days"

        # Classify repositories by unified activity status
        current_repos = []
        active_repos = []
        inactive_repos = []

        total_commits = 0
        total_lines_added = 0
        no_commit_repos = []  # Separate list for repositories with no commits

        for repo in repo_metrics:
            days_since_last = repo.get("days_since_last_commit")

            # Count total commits and lines of code
            total_commits += repo.get("commit_counts", {}).get(primary_window, 0)
            total_lines_added += (
                repo.get("loc_stats", {}).get(primary_window, {}).get("added", 0)
            )

            # Check if repository has no commits at all (use the explicit flag)
            has_any_commits = repo.get("has_any_commits", False)

            if not has_any_commits:
                # Repository with no commits - separate category
                no_commit_repos.append(repo)
            else:
                # Repository has commits - categorize by unified activity status
                # Handle case where days_since_last_commit might be None
                if days_since_last is None:
                    # If we have commits but no days_since_last, treat as inactive
                    inactive_repos.append(repo)
                else:
                    activity_status = repo.get("activity_status", "inactive")

                    if activity_status == "current":
                        current_repos.append(repo)
                    elif activity_status == "active":
                        active_repos.append(repo)
                    else:
                        inactive_repos.append(repo)

        # Aggregate author and organization data
        self.logger.info("Computing author rollups")
        authors = self.compute_author_rollups(repo_metrics)

        self.logger.info("Computing organization rollups")
        organizations = self.compute_org_rollups(authors)

        # Build complete repository list (all repositories sorted by activity)
        # Combine all activity status repositories for comprehensive view
        all_repos = current_repos + active_repos + inactive_repos

        # Sort all repositories by commits in primary window (descending)
        all_repositories_by_activity = self.rank_entities(
            all_repos,
            f"commit_counts.{primary_window}",
            reverse=True,
            limit=None,  # No limit - show all repositories
        )

        # Keep separate lists for different activity statuses
        top_current = self.rank_entities(
            current_repos, f"commit_counts.{primary_window}", reverse=True, limit=None
        )

        top_active = self.rank_entities(
            active_repos, f"commit_counts.{primary_window}", reverse=True, limit=None
        )

        least_active = self.rank_entities(
            inactive_repos, "days_since_last_commit", reverse=True, limit=None
        )

        # Build contributor leaderboards
        top_contributors_commits = self.rank_entities(
            authors, f"commits.{primary_window}", reverse=True, limit=None
        )

        top_contributors_loc = self.rank_entities(
            authors, f"lines_net.{primary_window}", reverse=True, limit=None
        )

        # Build organization leaderboard
        top_organizations = self.rank_entities(
            organizations, f"commits.{primary_window}", reverse=True, limit=None
        )

        # Build comprehensive summaries
        summaries = {
            "counts": {
                "total_repositories": len(repo_metrics),
                "current_repositories": len(current_repos),
                "active_repositories": len(active_repos),
                "inactive_repositories": len(inactive_repos),
                "no_commit_repositories": len(no_commit_repos),
                "total_commits": total_commits,
                "total_lines_added": total_lines_added,
                "total_authors": len(authors),
                "total_organizations": len(organizations),
            },
            "activity_status_distribution": {
                "current": [
                    {
                        "gerrit_project": r.get("gerrit_project", "Unknown"),
                        "days_since_last_commit": r.get("days_since_last_commit")
                        if r.get("days_since_last_commit") is not None
                        else 999999,
                    }
                    for r in current_repos
                ],
                "active": [
                    {
                        "gerrit_project": r.get("gerrit_project", "Unknown"),
                        "days_since_last_commit": r.get("days_since_last_commit")
                        if r.get("days_since_last_commit") is not None
                        else 999999,
                    }
                    for r in active_repos
                ],
                "inactive": [
                    {
                        "gerrit_project": r.get("gerrit_project", "Unknown"),
                        "days_since_last_commit": r.get("days_since_last_commit")
                        if r.get("days_since_last_commit") is not None
                        else 999999,
                    }
                    for r in inactive_repos
                ],
            },
            "top_current_repositories": top_current,
            "top_active_repositories": top_active,
            "least_active_repositories": least_active,
            "all_repositories": all_repositories_by_activity,
            "no_commit_repositories": no_commit_repos,
            "top_contributors_commits": top_contributors_commits,
            "top_contributors_loc": top_contributors_loc,
            "top_organizations": top_organizations,
        }

        self.logger.info(
            f"Aggregation complete: {len(current_repos)} current, {len(active_repos)} active, {len(inactive_repos)} inactive, {len(no_commit_repos)} no-commit repositories"
        )
        self.logger.info(
            f"Found {len(authors)} authors across {len(organizations)} organizations"
        )

        return summaries

    def _analyze_repository_commit_status(
        self, repo_metrics: list[dict[str, Any]]
    ) -> None:
        """Diagnostic function to analyze repository commit status."""
        self.logger.info("=== Repository Analysis ===")

        total_repos = len(repo_metrics)
        repos_with_commits = 0
        repos_no_commits = 0

        sample_no_commit_repos: list[dict[str, Any]] = []

        for repo in repo_metrics:
            repo_name = repo.get("gerrit_project", "Unknown")
            commit_counts = repo.get("commit_counts", {})

            # Check if repository has any commits across all time windows
            has_commits = any(count > 0 for count in commit_counts.values())

            if has_commits:
                repos_with_commits += 1
            else:
                repos_no_commits += 1
                if (
                    len(sample_no_commit_repos) < 3
                ):  # Collect sample for detailed analysis
                    sample_no_commit_repos.append(
                        {"gerrit_project": repo_name, "commit_counts": commit_counts}
                    )

        self.logger.info(f"Total repositories: {total_repos}")
        self.logger.info(f"Repositories with commits: {repos_with_commits}")
        self.logger.info(f"Repositories with NO commits: {repos_no_commits}")

        if sample_no_commit_repos:
            self.logger.info("Sample repositories with NO commits:")
            for repo in sample_no_commit_repos:
                self.logger.info(f"  - {repo['gerrit_project']}")

    def compute_author_rollups(
        self, repo_metrics: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Aggregate author metrics across all repositories.

        Merges author data by email address, summing metrics across all repos
        and tracking unique repositories touched per time window.
        """
        author_aggregates: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "name": "",
                "email": "",
                "username": "",
                "domain": "",
                "repositories_touched": defaultdict(set),
                "commits": defaultdict(int),
                "lines_added": defaultdict(int),
                "lines_removed": defaultdict(int),
                "lines_net": defaultdict(int),
            }
        )

        # Aggregate across all repositories
        for repo in repo_metrics:
            repo_name = repo.get("gerrit_project", "unknown")

            # Process each author in this repository
            for author in repo.get("authors", []):
                email = author.get("email", "").lower().strip()
                if not email or email == "unknown@unknown":
                    continue

                # Initialize author info (first occurrence wins for name/username)
                if not author_aggregates[email]["name"]:
                    author_aggregates[email]["name"] = author.get("name", "")
                    author_aggregates[email]["email"] = email
                    author_aggregates[email]["username"] = author.get("username", "")
                    author_aggregates[email]["domain"] = author.get("domain", "")

                # Aggregate metrics for each time window
                for window_name in author.get("commits", {}):
                    repos_set = cast(
                        set[str],
                        author_aggregates[email]["repositories_touched"][window_name],
                    )
                    repos_set.add(repo_name)
                    author_aggregates[email]["commits"][window_name] += author.get(
                        "commits", {}
                    ).get(window_name, 0)
                    author_aggregates[email]["lines_added"][window_name] += author.get(
                        "lines_added", {}
                    ).get(window_name, 0)
                    author_aggregates[email]["lines_removed"][window_name] += (
                        author.get("lines_removed", {}).get(window_name, 0)
                    )
                    author_aggregates[email]["lines_net"][window_name] += author.get(
                        "lines_net", {}
                    ).get(window_name, 0)

        # Convert to list format and finalize repository counts
        authors: List[Dict[str, Any]] = []
        for email, data in author_aggregates.items():
            author_record = {
                "name": data["name"],
                "email": email,
                "username": data["username"],
                "domain": data["domain"],
                "commits": dict(data["commits"]),
                "lines_added": dict(data["lines_added"]),
                "lines_removed": dict(data["lines_removed"]),
                "lines_net": dict(data["lines_net"]),
                "repositories_touched": {
                    window: set(repos)
                    for window, repos in data["repositories_touched"].items()
                },
                "repositories_count": {
                    window: len(repos)
                    for window, repos in data["repositories_touched"].items()
                },
            }
            authors.append(author_record)

        self.logger.info(
            f"Aggregated {len(authors)} unique authors across repositories"
        )
        return authors

    def compute_org_rollups(
        self, authors: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Aggregate organization metrics from author data.

        Groups authors by email domain and aggregates their contributions.
        """
        org_aggregates: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "domain": "",
                "contributor_count": 0,
                "contributors": set(),
                "commits": defaultdict(int),
                "lines_added": defaultdict(int),
                "lines_removed": defaultdict(int),
                "lines_net": defaultdict(int),
                "repositories_count": defaultdict(set),
            }
        )

        # Aggregate by domain
        for author in authors:
            domain = author.get("domain", "").strip().lower()
            if not domain or domain in ["unknown", "localhost", ""]:
                continue

            org_aggregates[domain]["domain"] = domain
            contributors_set = cast(set[str], org_aggregates[domain]["contributors"])
            contributors_set.add(author.get("email", ""))

            # Sum metrics across all time windows
            for window_name in author.get("commits", {}):
                org_aggregates[domain]["commits"][window_name] += author.get(
                    "commits", {}
                ).get(window_name, 0)
                org_aggregates[domain]["lines_added"][window_name] += author.get(
                    "lines_added", {}
                ).get(window_name, 0)
                org_aggregates[domain]["lines_removed"][window_name] += author.get(
                    "lines_removed", {}
                ).get(window_name, 0)
                org_aggregates[domain]["lines_net"][window_name] += author.get(
                    "lines_net", {}
                ).get(window_name, 0)

                # Track unique repositories per organization
                author_repos = author.get("repositories_touched", {}).get(
                    window_name, set()
                )
                if author_repos:
                    repos_set = cast(
                        set[str],
                        org_aggregates[domain]["repositories_count"][window_name],
                    )
                    repos_set.update(author_repos)

        # Convert to list format
        organizations = []
        for domain, data in org_aggregates.items():
            org_record = {
                "domain": domain,
                "contributor_count": len(data["contributors"]),
                "commits": dict(data["commits"]),
                "lines_added": dict(data["lines_added"]),
                "lines_removed": dict(data["lines_removed"]),
                "lines_net": dict(data["lines_net"]),
                "repositories_count": {
                    window: len(repos)
                    for window, repos in data["repositories_count"].items()
                },
            }
            organizations.append(org_record)

        self.logger.info(
            f"Aggregated {len(organizations)} organizations from author domains"
        )
        return organizations

    def rank_entities(
        self,
        entities: list[dict[str, Any]],
        sort_key: str,
        reverse: bool = False,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Sort entities by a metric with deterministic tie-breaking.

        Primary sort by the specified metric, secondary sort by name for stability.
        Handles nested dictionary keys (e.g., "commits.last_365_days").
        """

        def get_sort_value(entity):
            """Extract sort value, handling nested keys."""
            if "." in sort_key:
                keys = sort_key.split(".")
                value = entity
                for key in keys:
                    value = value.get(key, 0) if isinstance(value, dict) else 0
            else:
                value = entity.get(sort_key, 0)

            # Handle None values with appropriate defaults based on the metric
            if value is None:
                if sort_key == "days_since_last_commit":
                    return 999999  # Very large number for very old/no commits
                else:
                    return 0  # Default for other metrics

            # Ensure numeric return value
            if not isinstance(value, (int, float)):
                return 0
            return value

        def get_name(entity):
            """Extract name for tie-breaking."""
            return (
                entity.get("name")
                or entity.get("gerrit_project")
                or entity.get("domain")
                or entity.get("email")
                or ""
            )

        # Sort with primary metric (reverse if specified) and secondary name (always ascending)
        if reverse:
            sorted_entities = sorted(
                entities, key=lambda x: (-get_sort_value(x), get_name(x))
            )
        else:
            sorted_entities = sorted(
                entities, key=lambda x: (get_sort_value(x), get_name(x))
            )

        if limit and limit > 0:
            return sorted_entities[:limit]

        return sorted_entities
