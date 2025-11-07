# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Time window domain models for temporal metrics aggregation.

TimeWindow represents a named time period (e.g., "1y", "90d") with start/end dates.
TimeWindowStats provides a typed container for metrics aggregated over a time window.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from cli.error_helpers import wrap_validation_error


@dataclass(frozen=True)
class TimeWindow:
    """
    Represents a named time period for metrics aggregation.

    Attributes:
        name: Human-readable window name (e.g., "1y", "90d", "30d")
        days: Number of days in the window
        start_date: ISO 8601 timestamp for window start (inclusive)
        end_date: ISO 8601 timestamp for window end (exclusive)
    """

    name: str
    days: int
    start_date: str  # ISO 8601 format
    end_date: str    # ISO 8601 format

    def __post_init__(self) -> None:
        """Validate time window parameters."""
        if self.days <= 0:
            raise wrap_validation_error(
                "must be positive",
                field="TimeWindow.days",
                value=str(self.days),
                expected="integer > 0"
            )

        if not self.name:
            raise wrap_validation_error(
                "cannot be empty",
                field="TimeWindow.name"
            )

        # Validate ISO 8601 format by attempting to parse
        try:
            datetime.fromisoformat(self.start_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            raise wrap_validation_error(
                f"invalid ISO 8601 format: {e}",
                field="TimeWindow.start_date",
                value=self.start_date,
                expected="ISO 8601 timestamp (e.g., '2024-01-01T00:00:00Z')"
            ) from e

        try:
            datetime.fromisoformat(self.end_date.replace('Z', '+00:00'))
        except (ValueError, AttributeError) as e:
            raise wrap_validation_error(
                f"invalid ISO 8601 format: {e}",
                field="TimeWindow.end_date",
                value=self.end_date,
                expected="ISO 8601 timestamp (e.g., '2024-12-31T23:59:59Z')"
            ) from e

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary matching legacy schema format.
        """
        return {
            "days": self.days,
            "start": self.start_date,
            "end": self.end_date,
        }

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "TimeWindow":
        """
        Create TimeWindow from legacy dictionary format.

        Args:
            name: Window name (e.g., "1y")
            data: Dictionary with "days", "start", "end" keys

        Returns:
            TimeWindow instance
        """
        return cls(
            name=name,
            days=data["days"],
            start_date=data["start"],
            end_date=data["end"],
        )


@dataclass
class TimeWindowStats:
    """
    Container for metrics aggregated over a time window.

    This provides a typed alternative to raw dictionaries for per-window metrics
    like commit counts, LOC changes, etc.

    Attributes:
        commits: Number of commits in the window
        lines_added: Lines of code added
        lines_removed: Lines of code removed
        lines_net: Net change in lines (added - removed)
        contributors: Number of unique contributors (optional)
    """

    commits: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    lines_net: int = 0
    contributors: int = 0

    def __post_init__(self) -> None:
        """Validate metrics are non-negative where appropriate."""
        if self.commits < 0:
            raise wrap_validation_error(
                "must be non-negative",
                field="TimeWindowStats.commits",
                value=str(self.commits),
                expected="integer >= 0"
            )
        if self.lines_added < 0:
            raise wrap_validation_error(
                "must be non-negative",
                field="TimeWindowStats.lines_added",
                value=str(self.lines_added),
                expected="integer >= 0"
            )
        if self.lines_removed < 0:
            raise wrap_validation_error(
                "must be non-negative",
                field="TimeWindowStats.lines_removed",
                value=str(self.lines_removed),
                expected="integer >= 0"
            )
        if self.contributors < 0:
            raise wrap_validation_error(
                "must be non-negative",
                field="TimeWindowStats.contributors",
                value=str(self.contributors),
                expected="integer >= 0"
            )

        # lines_net can be negative (net deletion)
        # Validate consistency: net = added - removed
        expected_net = self.lines_added - self.lines_removed
        if self.lines_net != expected_net:
            raise wrap_validation_error(
                f"must equal lines_added - lines_removed ({self.lines_added} - {self.lines_removed} = {expected_net})",
                field="TimeWindowStats.lines_net",
                value=str(self.lines_net),
                expected=f"{expected_net}"
            )

    def to_dict(self) -> Dict[str, int]:
        """
        Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all metrics.
        """
        result = {
            "commits": self.commits,
            "lines_added": self.lines_added,
            "lines_removed": self.lines_removed,
            "lines_net": self.lines_net,
        }

        if self.contributors > 0:
            result["contributors"] = self.contributors

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "TimeWindowStats":
        """
        Create TimeWindowStats from dictionary.

        Args:
            data: Dictionary with metric keys

        Returns:
            TimeWindowStats instance
        """
        return cls(
            commits=data.get("commits", 0),
            lines_added=data.get("lines_added", 0),
            lines_removed=data.get("lines_removed", 0),
            lines_net=data.get("lines_net", 0),
            contributors=data.get("contributors", 0),
        )

    def __add__(self, other: "TimeWindowStats") -> "TimeWindowStats":
        """Add two TimeWindowStats together for aggregation."""
        if not isinstance(other, TimeWindowStats):
            return NotImplemented  # type: ignore[unreachable]

        return TimeWindowStats(
            commits=self.commits + other.commits,
            lines_added=self.lines_added + other.lines_added,
            lines_removed=self.lines_removed + other.lines_removed,
            lines_net=self.lines_net + other.lines_net,
            contributors=self.contributors + other.contributors,
        )
