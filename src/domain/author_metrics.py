# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Author metrics domain model.

Represents statistics for a single contributor across repositories,
including commit counts, LOC changes, and organizational affiliation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Set


@dataclass
class AuthorMetrics:
    """
    Metrics for a single contributor/author.

    This replaces the ad-hoc dictionary structure used in legacy code with
    a type-safe, validated domain model.

    Attributes:
        name: Author's display name
        email: Author's email address (primary identifier)
        username: Version control username (if available)
        domain: Email domain for organization affiliation
        commits: Commit counts per time window (e.g., {"1y": 42, "90d": 10})
        lines_added: Lines added per time window
        lines_removed: Lines removed per time window
        lines_net: Net line changes per time window (added - removed)
        repositories_touched: Number of repositories contributed to per window
    """

    # Identity fields
    name: str
    email: str
    username: str = ""
    domain: str = "unknown"

    # Time-windowed metrics
    commits: Dict[str, int] = field(default_factory=dict)
    lines_added: Dict[str, int] = field(default_factory=dict)
    lines_removed: Dict[str, int] = field(default_factory=dict)
    lines_net: Dict[str, int] = field(default_factory=dict)
    repositories_touched: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate author metrics after initialization."""
        # Validate required fields
        if not self.email:
            raise ValueError("email cannot be empty")

        # Name can be empty (some commits don't have names)
        # but normalize to email if empty
        if not self.name:
            object.__setattr__(self, 'name', self.email)

        # Validate non-negative counts
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

        for window, count in self.repositories_touched.items():
            if count < 0:
                raise ValueError(
                    f"repositories_touched['{window}'] must be non-negative, got {count}"
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
            Dictionary representation of author metrics.
        """
        return {
            "name": self.name,
            "email": self.email,
            "username": self.username,
            "domain": self.domain,
            "commits": self.commits,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "lines_net": self.lines_net,
            "repositories_touched": self.repositories_touched,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuthorMetrics":
        """
        Create AuthorMetrics from legacy dictionary format.

        This enables gradual migration from dict-based code to domain models.

        Args:
            data: Dictionary with author metrics

        Returns:
            AuthorMetrics instance
        """
        # Handle repositories_touched which might be sets in legacy code
        repos_touched = data.get("repositories_touched", {})
        if repos_touched and isinstance(next(iter(repos_touched.values()), None), set):
            # Convert sets to counts
            repos_touched = {
                window: len(repos) if isinstance(repos, set) else repos
                for window, repos in repos_touched.items()
            }

        return cls(
            name=data.get("name", ""),
            email=data["email"],
            username=data.get("username", ""),
            domain=data.get("domain", "unknown"),
            commits=data.get("commits", {}),
            lines_added=data.get("lines_added", {}),
            lines_removed=data.get("lines_removed", {}),
            lines_net=data.get("lines_net", {}),
            repositories_touched=repos_touched,
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
    def is_affiliated(self) -> bool:
        """Check if author has a known organizational affiliation."""
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
        return self.repositories_touched.get(window, 0)
