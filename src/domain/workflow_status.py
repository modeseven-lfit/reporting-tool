# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Workflow status domain model.

Represents CI/CD workflow status information for repositories,
including detected workflow files and build configurations.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WorkflowStatus:
    """
    CI/CD workflow status for a repository.

    This replaces the ad-hoc dictionary structure used in legacy code with
    a type-safe, validated domain model for workflow detection results.

    Attributes:
        has_github_actions: Whether GitHub Actions workflows were detected
        has_jenkins: Whether Jenkins configuration was detected
        has_circleci: Whether CircleCI configuration was detected
        has_travis: Whether Travis CI configuration was detected
        has_gitlab_ci: Whether GitLab CI configuration was detected
        workflow_files: List of detected workflow/config file paths
        primary_ci_system: Primary CI/CD system identified
        additional_metadata: Extra workflow-related metadata
    """

    # CI/CD system detection
    has_github_actions: bool = False
    has_jenkins: bool = False
    has_circleci: bool = False
    has_travis: bool = False
    has_gitlab_ci: bool = False

    # Detected files
    workflow_files: List[str] = field(default_factory=list)

    # Primary CI system
    primary_ci_system: Optional[str] = None

    # Additional metadata
    additional_metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate workflow status after initialization."""
        # Validate primary_ci_system if set
        valid_ci_systems = {
            "github_actions",
            "jenkins",
            "circleci",
            "travis",
            "gitlab_ci",
            None,
        }

        if self.primary_ci_system not in valid_ci_systems:
            raise ValueError(
                f"primary_ci_system must be one of {valid_ci_systems}, "
                f"got '{self.primary_ci_system}'"
            )

        # Auto-detect primary CI if not set but systems detected
        if self.primary_ci_system is None:
            if self.has_github_actions:
                object.__setattr__(self, 'primary_ci_system', 'github_actions')
            elif self.has_jenkins:
                object.__setattr__(self, 'primary_ci_system', 'jenkins')
            elif self.has_circleci:
                object.__setattr__(self, 'primary_ci_system', 'circleci')
            elif self.has_travis:
                object.__setattr__(self, 'primary_ci_system', 'travis')
            elif self.has_gitlab_ci:
                object.__setattr__(self, 'primary_ci_system', 'gitlab_ci')

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.

        Returns a dictionary matching the legacy schema format for backwards compatibility.

        Returns:
            Dictionary representation of workflow status.
        """
        result: Dict[str, Any] = {
            "has_github_actions": self.has_github_actions,
            "has_jenkins": self.has_jenkins,
            "has_circleci": self.has_circleci,
            "has_travis": self.has_travis,
            "has_gitlab_ci": self.has_gitlab_ci,
        }

        if self.workflow_files:
            result["workflow_files"] = self.workflow_files

        if self.primary_ci_system:
            result["primary_ci_system"] = self.primary_ci_system

        if self.additional_metadata:
            result["additional_metadata"] = self.additional_metadata

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowStatus":
        """
        Create WorkflowStatus from legacy dictionary format.

        This enables gradual migration from dict-based code to domain models.

        Args:
            data: Dictionary with workflow status

        Returns:
            WorkflowStatus instance
        """
        return cls(
            has_github_actions=data.get("has_github_actions", False),
            has_jenkins=data.get("has_jenkins", False),
            has_circleci=data.get("has_circleci", False),
            has_travis=data.get("has_travis", False),
            has_gitlab_ci=data.get("has_gitlab_ci", False),
            workflow_files=data.get("workflow_files", []),
            primary_ci_system=data.get("primary_ci_system"),
            additional_metadata=data.get("additional_metadata", {}),
        )

    @property
    def has_any_ci(self) -> bool:
        """Check if any CI/CD system was detected."""
        return (
            self.has_github_actions
            or self.has_jenkins
            or self.has_circleci
            or self.has_travis
            or self.has_gitlab_ci
        )

    @property
    def ci_system_count(self) -> int:
        """Get count of detected CI/CD systems."""
        return sum([
            self.has_github_actions,
            self.has_jenkins,
            self.has_circleci,
            self.has_travis,
            self.has_gitlab_ci,
        ])

    @property
    def has_multiple_ci_systems(self) -> bool:
        """Check if multiple CI/CD systems are configured."""
        return self.ci_system_count > 1

    def get_detected_systems(self) -> List[str]:
        """
        Get list of all detected CI/CD systems.

        Returns:
            List of system names (e.g., ["github_actions", "jenkins"])
        """
        systems = []
        if self.has_github_actions:
            systems.append("github_actions")
        if self.has_jenkins:
            systems.append("jenkins")
        if self.has_circleci:
            systems.append("circleci")
        if self.has_travis:
            systems.append("travis")
        if self.has_gitlab_ci:
            systems.append("gitlab_ci")
        return systems
