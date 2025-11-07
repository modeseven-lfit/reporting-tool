# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Repository metrics domain model.

Represents metrics for a single repository including commit counts,
LOC statistics, contributor counts, and activity status.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RepositoryMetrics:
    """
    Metrics for a single repository.

    This replaces the ad-hoc dictionary structure used in legacy code with
    a type-safe, validated domain model.

    Attributes:
        gerrit_project: Primary identifier - Gerrit project path (e.g., "foo/bar")
        gerrit_host: Gerrit server hostname
        gerrit_url: Full URL to Gerrit project
        local_path: Local filesystem path to cloned repository
        last_commit_timestamp: ISO 8601 timestamp of most recent commit
        days_since_last_commit: Days elapsed since last commit
        activity_status: Activity classification ("current", "active", "inactive")
        has_any_commits: Whether repository has any commits at all
        total_commits_ever: Total number of commits across all history
        commit_counts: Commits per time window (e.g., {"1y": 42, "90d": 10})
        loc_stats: Lines of code statistics per window
        unique_contributors: Number of unique contributors per window
        features: Feature detection results (workflow files, etc.)
        authors: Per-repository author metrics
        errors: List of errors encountered during collection
    """

    # Primary identifiers
    gerrit_project: str
    gerrit_host: str
    gerrit_url: str
    local_path: str

    # Activity metrics
    last_commit_timestamp: Optional[str] = None
    days_since_last_commit: Optional[int] = None
    activity_status: str = "inactive"
    has_any_commits: bool = False
    total_commits_ever: int = 0

    # Time-windowed metrics
    commit_counts: Dict[str, int] = field(default_factory=dict)
    loc_stats: Dict[str, Dict[str, int]] = field(default_factory=dict)
    unique_contributors: Dict[str, int] = field(default_factory=dict)

    # Additional data
    features: Dict[str, Any] = field(default_factory=dict)
    authors: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate repository metrics after initialization."""
        # Validate required fields
        if not self.gerrit_project:
            raise ValueError("gerrit_project cannot be empty")
        if not self.gerrit_host:
            raise ValueError("gerrit_host cannot be empty")
        if not self.gerrit_url:
            raise ValueError("gerrit_url cannot be empty")
        if not self.local_path:
            raise ValueError("local_path cannot be empty")

        # Validate activity status
        valid_statuses = {"current", "active", "inactive"}
        if self.activity_status not in valid_statuses:
            raise ValueError(
                f"activity_status must be one of {valid_statuses}, "
                f"got '{self.activity_status}'"
            )

        # Validate non-negative counts
        if self.total_commits_ever < 0:
            raise ValueError(
                f"total_commits_ever must be non-negative, got {self.total_commits_ever}"
            )

        if self.days_since_last_commit is not None and self.days_since_last_commit < 0:
            raise ValueError(
                f"days_since_last_commit must be non-negative, got {self.days_since_last_commit}"
            )

        # Validate commit counts are non-negative
        for window, count in self.commit_counts.items():
            if count < 0:
                raise ValueError(
                    f"commit_counts['{window}'] must be non-negative, got {count}"
                )

        # Validate LOC stats are non-negative (except net which can be negative)
        for window, stats in self.loc_stats.items():
            if stats.get("added", 0) < 0:
                raise ValueError(
                    f"loc_stats['{window}']['added'] must be non-negative"
                )
            if stats.get("removed", 0) < 0:
                raise ValueError(
                    f"loc_stats['{window}']['removed'] must be non-negative"
                )
            # Validate net = added - removed
            added = stats.get("added", 0)
            removed = stats.get("removed", 0)
            net = stats.get("net", 0)
            expected_net = added - removed
            if net != expected_net:
                raise ValueError(
                    f"loc_stats['{window}']['net'] ({net}) must equal "
                    f"added ({added}) - removed ({removed}) = {expected_net}"
                )

        # Validate unique contributors are non-negative
        for window, count in self.unique_contributors.items():
            if count < 0:
                raise ValueError(
                    f"unique_contributors['{window}'] must be non-negative, got {count}"
                )

        # Consistency check: if has_any_commits is False, total should be 0
        if not self.has_any_commits and self.total_commits_ever > 0:
            raise ValueError(
                "Inconsistent state: has_any_commits is False but total_commits_ever > 0"
            )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns a dictionary matching the legacy schema format for backwards compatibility.

        Returns:
            Dictionary representation of repository metrics.
        """
        return {
            "gerrit_project": self.gerrit_project,
            "gerrit_host": self.gerrit_host,
            "gerrit_url": self.gerrit_url,
            "local_path": self.local_path,
            "last_commit_timestamp": self.last_commit_timestamp,
            "days_since_last_commit": self.days_since_last_commit,
            "activity_status": self.activity_status,
            "has_any_commits": self.has_any_commits,
            "total_commits_ever": self.total_commits_ever,
            "commit_counts": self.commit_counts,
            "loc_stats": self.loc_stats,
            "unique_contributors": self.unique_contributors,
            "features": self.features,
            "authors": self.authors,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RepositoryMetrics":
        """
        Create RepositoryMetrics from legacy dictionary format.

        This enables gradual migration from dict-based code to domain models.

        Args:
            data: Dictionary with repository metrics

        Returns:
            RepositoryMetrics instance
        """
        return cls(
            gerrit_project=data["gerrit_project"],
            gerrit_host=data["gerrit_host"],
            gerrit_url=data["gerrit_url"],
            local_path=data["local_path"],
            last_commit_timestamp=data.get("last_commit_timestamp"),
            days_since_last_commit=data.get("days_since_last_commit"),
            activity_status=data.get("activity_status", "inactive"),
            has_any_commits=data.get("has_any_commits", False),
            total_commits_ever=data.get("total_commits_ever", 0),
            commit_counts=data.get("commit_counts", {}),
            loc_stats=data.get("loc_stats", {}),
            unique_contributors=data.get("unique_contributors", {}),
            features=data.get("features", {}),
            authors=data.get("authors", []),
            errors=data.get("errors", []),
        )

    @property
    def is_active(self) -> bool:
        """Check if repository is currently active or recently active."""
        return self.activity_status in ("current", "active")

    @property
    def is_current(self) -> bool:
        """Check if repository has very recent activity (current)."""
        return self.activity_status == "current"

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred during metrics collection."""
        return len(self.errors) > 0

    def get_commits_in_window(self, window: str) -> int:
        """
        Get commit count for a specific time window.

        Args:
            window: Time window name (e.g., "1y", "90d")

        Returns:
            Commit count, or 0 if window not found
        """
        return self.commit_counts.get(window, 0)

    def get_loc_stats_for_window(self, window: str) -> Dict[str, int]:
        """
        Get LOC statistics for a specific time window.

        Args:
            window: Time window name (e.g., "1y", "90d")

        Returns:
            Dictionary with "added", "removed", "net" keys, or zeros if not found
        """
        return self.loc_stats.get(window, {"added": 0, "removed": 0, "net": 0})

    def get_contributor_count_for_window(self, window: str) -> int:
        """
        Get unique contributor count for a specific time window.

        Args:
            window: Time window name (e.g., "1y", "90d")

        Returns:
            Contributor count, or 0 if window not found
        """
        return self.unique_contributors.get(window, 0)
