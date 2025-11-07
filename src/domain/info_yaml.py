# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
INFO.yaml domain model.

Represents project metadata and committer information from INFO.yaml files
in the LF info-master repository.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PersonInfo:
    """
    Information about a person (project lead or committer).

    Attributes:
        name: Full name of the person
        email: Email address
        company: Company affiliation
        id: LF ID or other identifier
        timezone: Timezone (optional)
    """

    name: str
    email: str = ""
    company: str = ""
    id: str = ""
    timezone: str = ""

    def __post_init__(self) -> None:
        """Validate person information."""
        if not self.name or self.name == "Unknown":
            raise ValueError("Person name cannot be empty or 'Unknown'")

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "id": self.id,
            "timezone": self.timezone,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PersonInfo":
        """Create PersonInfo from dictionary."""
        if not data or not isinstance(data, dict):
            raise ValueError("Invalid person data")

        return cls(
            name=data.get("name", "Unknown"),
            email=data.get("email", ""),
            company=data.get("company", ""),
            id=data.get("id", ""),
            timezone=data.get("timezone", ""),
        )


@dataclass
class CommitterInfo:
    """
    Information about a project committer with activity enrichment.

    Extends PersonInfo with activity status and color coding for reporting.

    Attributes:
        name: Full name of the committer
        email: Email address
        company: Company affiliation
        id: LF ID or other identifier
        timezone: Timezone (optional)
        activity_status: Activity classification ("current", "active", "inactive", "unknown")
        activity_color: Color code for display ("green", "orange", "red", "gray")
        days_since_last_commit: Days since committer's last commit (optional)
    """

    name: str
    email: str = ""
    company: str = ""
    id: str = ""
    timezone: str = ""
    activity_status: str = "unknown"
    activity_color: str = "gray"
    days_since_last_commit: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate committer information."""
        if not self.name or self.name == "Unknown":
            raise ValueError("Committer name cannot be empty or 'Unknown'")

        # Validate activity status
        valid_statuses = {"current", "active", "inactive", "unknown"}
        if self.activity_status not in valid_statuses:
            raise ValueError(
                f"activity_status must be one of {valid_statuses}, "
                f"got '{self.activity_status}'"
            )

        # Validate activity color
        valid_colors = {"green", "orange", "red", "gray"}
        if self.activity_color not in valid_colors:
            raise ValueError(
                f"activity_color must be one of {valid_colors}, "
                f"got '{self.activity_color}'"
            )

        # Validate days_since_last_commit if present
        if self.days_since_last_commit is not None and self.days_since_last_commit < 0:
            raise ValueError(
                f"days_since_last_commit must be non-negative, "
                f"got {self.days_since_last_commit}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "email": self.email,
            "company": self.company,
            "id": self.id,
            "timezone": self.timezone,
            "activity_status": self.activity_status,
            "activity_color": self.activity_color,
            "days_since_last_commit": self.days_since_last_commit,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommitterInfo":
        """Create CommitterInfo from dictionary."""
        if not data or not isinstance(data, dict):
            raise ValueError("Invalid committer data")

        return cls(
            name=data.get("name", "Unknown"),
            email=data.get("email", ""),
            company=data.get("company", ""),
            id=data.get("id", ""),
            timezone=data.get("timezone", ""),
            activity_status=data.get("activity_status", "unknown"),
            activity_color=data.get("activity_color", "gray"),
            days_since_last_commit=data.get("days_since_last_commit"),
        )

    @property
    def is_active(self) -> bool:
        """Check if committer is currently active or recently active."""
        return self.activity_status in ("current", "active")

    @property
    def is_current(self) -> bool:
        """Check if committer has very recent activity."""
        return self.activity_status == "current"


@dataclass
class IssueTracking:
    """
    Issue tracking information for a project.

    Attributes:
        type: Type of issue tracker (e.g., "jira", "github")
        url: URL to the issue tracker
        is_valid: Whether the URL has been validated
        validation_error: Error message if URL validation failed
    """

    type: str = ""
    url: str = ""
    is_valid: bool = False
    validation_error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type,
            "url": self.url,
            "is_valid": self.is_valid,
            "validation_error": self.validation_error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IssueTracking":
        """Create IssueTracking from dictionary."""
        if not data or not isinstance(data, dict):
            return cls()

        return cls(
            type=data.get("type", ""),
            url=data.get("url", ""),
            is_valid=data.get("is_valid", False),
            validation_error=data.get("validation_error", ""),
        )

    @property
    def has_url(self) -> bool:
        """Check if a URL is configured."""
        return bool(self.url)


@dataclass
class ProjectInfo:
    """
    Complete project information from INFO.yaml.

    This is the primary domain model representing a project's metadata,
    committers, and organizational information.

    Attributes:
        project_name: Name of the project
        gerrit_server: Gerrit server hostname (e.g., "gerrit.onap.org")
        project_path: Path to project in Gerrit (e.g., "foo/bar")
        full_path: Complete path including server
        creation_date: Project creation date (ISO 8601 or human-readable)
        lifecycle_state: Project lifecycle state (e.g., "Incubation", "Active", "Archived")
        project_lead: Project lead information
        committers: List of project committers
        issue_tracking: Issue tracking configuration
        repositories: List of repository names
        yaml_file_path: Path to the INFO.yaml file
        has_git_data: Whether Git data enrichment was performed
        project_days_since_last_commit: Days since project's last commit (any repo)
        errors: List of errors encountered during processing
    """

    project_name: str
    gerrit_server: str
    project_path: str
    full_path: str
    creation_date: str = "Unknown"
    lifecycle_state: str = "Unknown"
    project_lead: Optional[PersonInfo] = None
    committers: List[CommitterInfo] = field(default_factory=list)
    issue_tracking: IssueTracking = field(default_factory=IssueTracking)
    repositories: List[str] = field(default_factory=list)
    yaml_file_path: str = ""
    has_git_data: bool = False
    project_days_since_last_commit: Optional[int] = None
    errors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate project information."""
        if not self.project_name:
            raise ValueError("project_name cannot be empty")
        if not self.gerrit_server:
            raise ValueError("gerrit_server cannot be empty")
        if not self.project_path:
            raise ValueError("project_path cannot be empty")
        if not self.full_path:
            raise ValueError("full_path cannot be empty")

        # Validate project_days_since_last_commit if present
        if (
            self.project_days_since_last_commit is not None
            and self.project_days_since_last_commit < 0
        ):
            raise ValueError(
                f"project_days_since_last_commit must be non-negative, "
                f"got {self.project_days_since_last_commit}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "project_name": self.project_name,
            "gerrit_server": self.gerrit_server,
            "project_path": self.project_path,
            "full_path": self.full_path,
            "creation_date": self.creation_date,
            "lifecycle_state": self.lifecycle_state,
            "project_lead": self.project_lead.to_dict() if self.project_lead else None,
            "committers": [c.to_dict() for c in self.committers],
            "issue_tracking": self.issue_tracking.to_dict(),
            "repositories": self.repositories,
            "yaml_file_path": self.yaml_file_path,
            "has_git_data": self.has_git_data,
            "project_days_since_last_commit": self.project_days_since_last_commit,
            "errors": self.errors,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectInfo":
        """Create ProjectInfo from dictionary."""
        if not data or not isinstance(data, dict):
            raise ValueError("Invalid project data")

        # Parse project lead
        project_lead = None
        lead_data = data.get("project_lead")
        if lead_data:
            try:
                project_lead = PersonInfo.from_dict(lead_data)
            except ValueError:
                # Invalid lead data, skip
                pass

        # Parse committers
        committers = []
        for committer_data in data.get("committers", []):
            try:
                committers.append(CommitterInfo.from_dict(committer_data))
            except ValueError:
                # Skip invalid committer data
                continue

        # Parse issue tracking
        issue_tracking = IssueTracking.from_dict(data.get("issue_tracking", {}))

        return cls(
            project_name=data.get("project_name", "Unknown"),
            gerrit_server=data.get("gerrit_server", "unknown"),
            project_path=data.get("project_path", ""),
            full_path=data.get("full_path", ""),
            creation_date=data.get("creation_date", "Unknown"),
            lifecycle_state=data.get("lifecycle_state", "Unknown"),
            project_lead=project_lead,
            committers=committers,
            issue_tracking=issue_tracking,
            repositories=data.get("repositories", []),
            yaml_file_path=data.get("yaml_file_path", ""),
            has_git_data=data.get("has_git_data", False),
            project_days_since_last_commit=data.get("project_days_since_last_commit"),
            errors=data.get("errors", []),
        )

    @property
    def has_errors(self) -> bool:
        """Check if any errors occurred during processing."""
        return len(self.errors) > 0

    @property
    def is_archived(self) -> bool:
        """Check if project is in an archived lifecycle state."""
        archived_states = {"archived", "end of life", "eol", "deprecated"}
        return self.lifecycle_state.lower() in archived_states

    @property
    def committer_count(self) -> int:
        """Get the number of committers."""
        return len(self.committers)

    @property
    def active_committer_count(self) -> int:
        """Get the number of active committers."""
        return sum(1 for c in self.committers if c.is_active)

    @property
    def has_issue_tracker(self) -> bool:
        """Check if project has a configured issue tracker."""
        return self.issue_tracking.has_url

    @property
    def issue_tracker_valid(self) -> bool:
        """Check if issue tracker URL is valid."""
        return self.issue_tracking.is_valid

    def get_committers_by_status(self, status: str) -> List[CommitterInfo]:
        """
        Get committers filtered by activity status.

        Args:
            status: Activity status to filter by ("current", "active", "inactive", "unknown")

        Returns:
            List of committers with matching status
        """
        return [c for c in self.committers if c.activity_status == status]

    def get_committers_by_color(self, color: str) -> List[CommitterInfo]:
        """
        Get committers filtered by activity color.

        Args:
            color: Activity color to filter by ("green", "orange", "red", "gray")

        Returns:
            List of committers with matching color
        """
        return [c for c in self.committers if c.activity_color == color]


@dataclass
class LifecycleSummary:
    """
    Summary statistics for projects grouped by lifecycle state.

    Attributes:
        state: Lifecycle state name
        count: Number of projects in this state
        percentage: Percentage of total projects
    """

    state: str
    count: int
    percentage: float

    def __post_init__(self) -> None:
        """Validate lifecycle summary."""
        if self.count < 0:
            raise ValueError(f"count must be non-negative, got {self.count}")
        if not 0 <= self.percentage <= 100:
            raise ValueError(f"percentage must be 0-100, got {self.percentage}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "state": self.state,
            "count": self.count,
            "percentage": self.percentage,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LifecycleSummary":
        """Create LifecycleSummary from dictionary."""
        return cls(
            state=data.get("state", "Unknown"),
            count=data.get("count", 0),
            percentage=data.get("percentage", 0.0),
        )
