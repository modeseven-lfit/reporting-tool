# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Organization metrics domain model.

Represents aggregated statistics for an organization (identified by email domain),
including contributor counts, commit totals, and LOC changes across repositories.
"""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class OrganizationMetrics:
    """
    Metrics for a single organization (identified by email domain).

    This replaces the ad-hoc dictionary structure used in legacy code with
    a type-safe, validated domain model.

    Attributes:
        domain: Organization email domain (e.g., "example.com")
        contributor_count: Total number of unique contributors from this org
        commits: Commit counts per time window (e.g., {"1y": 100, "90d": 25})
        lines_added: Lines added per time window
        lines_removed: Lines removed per time window
        lines_net: Net line changes per time window (added - removed)
        repositories_count: Number of repositories touched per window
    """

    # Identity field
    domain: str

    # Contributor metrics
    contributor_count: int = 0

    # Time-windowed metrics
    commits: Dict[str, int] = field(default_factory=dict)
    lines_added: Dict[str, int] = field(default_factory=dict)
    lines_removed: Dict[str, int] = field(default_factory=dict)
    lines_net: Dict[str, int] = field(default_factory=dict)
    repositories_count: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate organization metrics after initialization."""
        # Validate required fields
        if not self.domain:
            raise ValueError("domain cannot be empty")

        # Validate non-negative counts
        if self.contributor_count < 0:
            raise ValueError(
                f"contributor_count must be non-negative, got {self.contributor_count}"
            )

        for window, count in self.commits.items():
            if count < 0:
                raise ValueError(
                    f"commits['{window}'] must be non-negative, got {count}"
                )

        for window, count in self.lines_added.items():
            if count < 0:
                raise ValueError(
                    f"lines_added['{window}'] must be non-negative, got {count}"
                )

        for window, count in self.lines_removed.items():
            if count < 0:
                raise ValueError(
                    f"lines_removed['{window}'] must be non-negative, got {count}"
                )

        for window, count in self.repositories_count.items():
            if count < 0:
                raise ValueError(
                    f"repositories_count['{window}'] must be non-negative, got {count}"
                )

        # Validate consistency: for each window, net = added - removed
        for window in self.commits.keys():
            added = self.lines_added.get(window, 0)
            removed = self.lines_removed.get(window, 0)
            net = self.lines_net.get(window, 0)
            expected_net = added - removed

            if net != expected_net:
                raise ValueError(
                    f"lines_net['{window}'] ({net}) must equal "
                    f"lines_added ({added}) - lines_removed ({removed}) = {expected_net}"
                )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns a dictionary matching the legacy schema format for backwards compatibility.

        Returns:
            Dictionary representation of organization metrics.
        """
        return {
            "domain": self.domain,
            "contributor_count": self.contributor_count,
            "commits": self.commits,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "lines_net": self.lines_net,
            "repositories_count": self.repositories_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrganizationMetrics":
        """
        Create OrganizationMetrics from legacy dictionary format.

        This enables gradual migration from dict-based code to domain models.

        Args:
            data: Dictionary with organization metrics

        Returns:
            OrganizationMetrics instance
        """
        return cls(
            domain=data["domain"],
            contributor_count=data.get("contributor_count", 0),
            commits=data.get("commits", {}),
            lines_added=data.get("lines_added", {}),
            lines_removed=data.get("lines_removed", {}),
            lines_net=data.get("lines_net", {}),
            repositories_count=data.get("repositories_count", {}),
        )

    @property
    def total_commits(self) -> int:
        """Get total commits across all time windows."""
        return sum(self.commits.values())

    @property
    def total_lines_added(self) -> int:
        """Get total lines added across all time windows."""
        return sum(self.lines_added.values())

    @property
    def total_lines_removed(self) -> int:
        """Get total lines removed across all time windows."""
        return sum(self.lines_removed.values())

    @property
    def total_lines_net(self) -> int:
        """Get total net line changes across all time windows."""
        return sum(self.lines_net.values())

    @property
    def is_known_org(self) -> bool:
        """Check if this is a known organization (not 'unknown' domain)."""
        return self.domain != "unknown" and bool(self.domain)

    def get_commits_in_window(self, window: str) -> int:
        """
        Get commit count for a specific time window.

        Args:
            window: Time window name (e.g., "1y", "90d")

        Returns:
            Commit count, or 0 if window not found
        """
        return self.commits.get(window, 0)

    def get_lines_added_in_window(self, window: str) -> int:
        """
        Get lines added for a specific time window.

        Args:
            window: Time window name (e.g., "1y", "90d")

        Returns:
            Lines added, or 0 if window not found
        """
        return self.lines_added.get(window, 0)

    def get_lines_removed_in_window(self, window: str) -> int:
        """
        Get lines removed for a specific time window.

        Args:
            window: Time window name (e.g., "1y", "90d")

        Returns:
            Lines removed, or 0 if window not found
        """
        return self.lines_removed.get(window, 0)

    def get_lines_net_in_window(self, window: str) -> int:
        """
        Get net line changes for a specific time window.

        Args:
            window: Time window name (e.g., "1y", "90d")

        Returns:
            Net lines, or 0 if window not found
        """
        return self.lines_net.get(window, 0)

    def get_repositories_in_window(self, window: str) -> int:
        """
        Get repository count for a specific time window.

        Args:
            window: Time window name (e.g., "1y", "90d")

        Returns:
            Repository count, or 0 if window not found
        """
        return self.repositories_count.get(window, 0)
