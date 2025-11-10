# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for INFO.yaml domain models.

Tests the validation, serialization, and business logic of:
- PersonInfo
- CommitterInfo
- IssueTracking
- ProjectInfo
- LifecycleSummary
"""

import pytest

from domain.info_yaml import (
    CommitterInfo,
    IssueTracking,
    LifecycleSummary,
    PersonInfo,
    ProjectInfo,
)


class TestPersonInfo:
    """Tests for PersonInfo domain model."""

    def test_create_valid_person(self):
        """Test creating a valid PersonInfo object."""
        person = PersonInfo(
            name="John Doe",
            email="john.doe@example.com",
            company="Example Corp",
            id="jdoe",
            timezone="America/Los_Angeles",
        )

        assert person.name == "John Doe"
        assert person.email == "john.doe@example.com"
        assert person.company == "Example Corp"
        assert person.id == "jdoe"
        assert person.timezone == "America/Los_Angeles"

    def test_create_person_with_defaults(self):
        """Test creating PersonInfo with minimal required fields."""
        person = PersonInfo(name="Jane Smith")

        assert person.name == "Jane Smith"
        assert person.email == ""
        assert person.company == ""
        assert person.id == ""
        assert person.timezone == ""

    def test_reject_empty_name(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            PersonInfo(name="")

    def test_reject_unknown_name(self):
        """Test that 'Unknown' name is rejected."""
        with pytest.raises(ValueError, match="name cannot be empty"):
            PersonInfo(name="Unknown")

    def test_to_dict(self):
        """Test serialization to dictionary."""
        person = PersonInfo(
            name="Alice Johnson",
            email="alice@example.com",
            company="Tech Inc",
            id="ajohnson",
        )

        result = person.to_dict()

        assert result == {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "company": "Tech Inc",
            "id": "ajohnson",
            "timezone": "",
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "Bob Williams",
            "email": "bob@example.com",
            "company": "Code Solutions",
            "id": "bwilliams",
            "timezone": "Asia/Tokyo",
        }

        person = PersonInfo.from_dict(data)

        assert person.name == "Bob Williams"
        assert person.email == "bob@example.com"
        assert person.company == "Code Solutions"
        assert person.id == "bwilliams"
        assert person.timezone == "Asia/Tokyo"

    def test_from_dict_with_missing_fields(self):
        """Test deserialization with missing optional fields."""
        data = {"name": "Carol Martinez"}

        person = PersonInfo.from_dict(data)

        assert person.name == "Carol Martinez"
        assert person.email == ""
        assert person.company == ""

    def test_from_dict_invalid_data(self):
        """Test that invalid data raises ValueError."""
        with pytest.raises(ValueError, match="Invalid person data"):
            PersonInfo.from_dict(None)

        with pytest.raises(ValueError, match="Invalid person data"):
            PersonInfo.from_dict([])


class TestCommitterInfo:
    """Tests for CommitterInfo domain model."""

    def test_create_valid_committer(self):
        """Test creating a valid CommitterInfo object."""
        committer = CommitterInfo(
            name="Alice Johnson",
            email="alice@example.com",
            company="Developer Inc",
            id="ajohnson",
            timezone="Europe/London",
            activity_status="current",
            activity_color="green",
            days_since_last_commit=10,
        )

        assert committer.name == "Alice Johnson"
        assert committer.activity_status == "current"
        assert committer.activity_color == "green"
        assert committer.days_since_last_commit == 10

    def test_create_committer_with_defaults(self):
        """Test creating CommitterInfo with default activity status."""
        committer = CommitterInfo(name="Bob Williams")

        assert committer.name == "Bob Williams"
        assert committer.activity_status == "unknown"
        assert committer.activity_color == "gray"
        assert committer.days_since_last_commit is None

    def test_reject_invalid_activity_status(self):
        """Test that invalid activity status is rejected."""
        with pytest.raises(ValueError, match="activity_status must be one of"):
            CommitterInfo(name="Test User", activity_status="invalid")

    def test_reject_invalid_activity_color(self):
        """Test that invalid activity color is rejected."""
        with pytest.raises(ValueError, match="activity_color must be one of"):
            CommitterInfo(name="Test User", activity_color="blue")

    def test_reject_negative_days_since_commit(self):
        """Test that negative days_since_last_commit is rejected."""
        with pytest.raises(ValueError, match="must be non-negative"):
            CommitterInfo(name="Test User", days_since_last_commit=-5)

    def test_is_active_property(self):
        """Test is_active property for different statuses."""
        current = CommitterInfo(name="Current User", activity_status="current")
        active = CommitterInfo(name="Active User", activity_status="active")
        inactive = CommitterInfo(name="Inactive User", activity_status="inactive")
        unknown = CommitterInfo(name="Unknown User", activity_status="unknown")

        assert current.is_active is True
        assert active.is_active is True
        assert inactive.is_active is False
        assert unknown.is_active is False

    def test_is_current_property(self):
        """Test is_current property."""
        current = CommitterInfo(name="Current User", activity_status="current")
        active = CommitterInfo(name="Active User", activity_status="active")

        assert current.is_current is True
        assert active.is_current is False

    def test_to_dict(self):
        """Test serialization to dictionary."""
        committer = CommitterInfo(
            name="Test User",
            email="test@example.com",
            activity_status="active",
            activity_color="orange",
            days_since_last_commit=500,
        )

        result = committer.to_dict()

        assert result["name"] == "Test User"
        assert result["email"] == "test@example.com"
        assert result["activity_status"] == "active"
        assert result["activity_color"] == "orange"
        assert result["days_since_last_commit"] == 500

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "company": "Test Corp",
            "activity_status": "inactive",
            "activity_color": "red",
            "days_since_last_commit": 1500,
        }

        committer = CommitterInfo.from_dict(data)

        assert committer.name == "Test User"
        assert committer.activity_status == "inactive"
        assert committer.activity_color == "red"
        assert committer.days_since_last_commit == 1500


class TestIssueTracking:
    """Tests for IssueTracking domain model."""

    def test_create_valid_issue_tracking(self):
        """Test creating a valid IssueTracking object."""
        tracker = IssueTracking(
            type="jira",
            url="https://jira.example.org/projects/TEST",
            is_valid=True,
            validation_error="",
        )

        assert tracker.type == "jira"
        assert tracker.url == "https://jira.example.org/projects/TEST"
        assert tracker.is_valid is True
        assert tracker.validation_error == ""

    def test_create_empty_issue_tracking(self):
        """Test creating an empty IssueTracking object."""
        tracker = IssueTracking()

        assert tracker.type == ""
        assert tracker.url == ""
        assert tracker.is_valid is False
        assert tracker.validation_error == ""

    def test_has_url_property(self):
        """Test has_url property."""
        with_url = IssueTracking(url="https://example.com")
        without_url = IssueTracking()

        assert with_url.has_url is True
        assert without_url.has_url is False

    def test_to_dict(self):
        """Test serialization to dictionary."""
        tracker = IssueTracking(
            type="github",
            url="https://github.com/org/repo/issues",
            is_valid=True,
        )

        result = tracker.to_dict()

        assert result == {
            "type": "github",
            "url": "https://github.com/org/repo/issues",
            "is_valid": True,
            "validation_error": "",
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "type": "jira",
            "url": "https://jira.example.org",
            "is_valid": False,
            "validation_error": "Connection timeout",
        }

        tracker = IssueTracking.from_dict(data)

        assert tracker.type == "jira"
        assert tracker.url == "https://jira.example.org"
        assert tracker.is_valid is False
        assert tracker.validation_error == "Connection timeout"

    def test_from_dict_invalid_data(self):
        """Test deserialization with invalid data returns empty object."""
        tracker1 = IssueTracking.from_dict(None)
        tracker2 = IssueTracking.from_dict([])

        assert tracker1.url == ""
        assert tracker2.url == ""


class TestProjectInfo:
    """Tests for ProjectInfo domain model."""

    def test_create_valid_project(self):
        """Test creating a valid ProjectInfo object."""
        lead = PersonInfo(name="John Doe", email="john@example.com")
        committers = [
            CommitterInfo(name="Alice Johnson", email="alice@example.com"),
            CommitterInfo(name="Bob Williams", email="bob@example.com"),
        ]
        issue_tracking = IssueTracking(type="jira", url="https://jira.example.org/projects/TEST")

        project = ProjectInfo(
            project_name="Test Project",
            gerrit_server="gerrit.example.org",
            project_path="test/project",
            full_path="gerrit.example.org/test/project",
            creation_date="2020-01-15",
            lifecycle_state="Active",
            project_lead=lead,
            committers=committers,
            issue_tracking=issue_tracking,
            repositories=["test/repo1", "test/repo2"],
            yaml_file_path="/path/to/INFO.yaml",
        )

        assert project.project_name == "Test Project"
        assert project.gerrit_server == "gerrit.example.org"
        assert project.project_path == "test/project"
        assert project.lifecycle_state == "Active"
        assert project.committer_count == 2
        assert len(project.repositories) == 2

    def test_create_minimal_project(self):
        """Test creating ProjectInfo with minimal required fields."""
        project = ProjectInfo(
            project_name="Minimal Project",
            gerrit_server="gerrit.example.org",
            project_path="minimal",
            full_path="gerrit.example.org/minimal",
        )

        assert project.project_name == "Minimal Project"
        assert project.creation_date == "Unknown"
        assert project.lifecycle_state == "Unknown"
        assert project.project_lead is None
        assert project.committer_count == 0
        assert len(project.repositories) == 0

    def test_reject_empty_required_fields(self):
        """Test that empty required fields are rejected."""
        with pytest.raises(ValueError, match="project_name cannot be empty"):
            ProjectInfo(
                project_name="",
                gerrit_server="gerrit.example.org",
                project_path="test",
                full_path="gerrit.example.org/test",
            )

        with pytest.raises(ValueError, match="gerrit_server cannot be empty"):
            ProjectInfo(
                project_name="Test",
                gerrit_server="",
                project_path="test",
                full_path="gerrit.example.org/test",
            )

    def test_reject_negative_days_since_commit(self):
        """Test that negative project_days_since_last_commit is rejected."""
        with pytest.raises(ValueError, match="must be non-negative"):
            ProjectInfo(
                project_name="Test",
                gerrit_server="gerrit.example.org",
                project_path="test",
                full_path="gerrit.example.org/test",
                project_days_since_last_commit=-10,
            )

    def test_is_archived_property(self):
        """Test is_archived property for different lifecycle states."""
        active = ProjectInfo(
            project_name="Active",
            gerrit_server="gerrit.example.org",
            project_path="active",
            full_path="gerrit.example.org/active",
            lifecycle_state="Active",
        )

        archived = ProjectInfo(
            project_name="Archived",
            gerrit_server="gerrit.example.org",
            project_path="archived",
            full_path="gerrit.example.org/archived",
            lifecycle_state="Archived",
        )

        eol = ProjectInfo(
            project_name="EOL",
            gerrit_server="gerrit.example.org",
            project_path="eol",
            full_path="gerrit.example.org/eol",
            lifecycle_state="End of Life",
        )

        assert active.is_archived is False
        assert archived.is_archived is True
        assert eol.is_archived is True

    def test_committer_count_property(self):
        """Test committer_count property."""
        project = ProjectInfo(
            project_name="Test",
            gerrit_server="gerrit.example.org",
            project_path="test",
            full_path="gerrit.example.org/test",
            committers=[
                CommitterInfo(name="User1"),
                CommitterInfo(name="User2"),
                CommitterInfo(name="User3"),
            ],
        )

        assert project.committer_count == 3

    def test_active_committer_count_property(self):
        """Test active_committer_count property."""
        project = ProjectInfo(
            project_name="Test",
            gerrit_server="gerrit.example.org",
            project_path="test",
            full_path="gerrit.example.org/test",
            committers=[
                CommitterInfo(name="Current User", activity_status="current"),
                CommitterInfo(name="Active User", activity_status="active"),
                CommitterInfo(name="Inactive User", activity_status="inactive"),
                CommitterInfo(name="Unknown User", activity_status="unknown"),
            ],
        )

        assert project.active_committer_count == 2  # current + active

    def test_has_issue_tracker_property(self):
        """Test has_issue_tracker property."""
        with_tracker = ProjectInfo(
            project_name="Test",
            gerrit_server="gerrit.example.org",
            project_path="test",
            full_path="gerrit.example.org/test",
            issue_tracking=IssueTracking(url="https://example.com"),
        )

        without_tracker = ProjectInfo(
            project_name="Test",
            gerrit_server="gerrit.example.org",
            project_path="test",
            full_path="gerrit.example.org/test",
        )

        assert with_tracker.has_issue_tracker is True
        assert without_tracker.has_issue_tracker is False

    def test_get_committers_by_status(self):
        """Test filtering committers by status."""
        project = ProjectInfo(
            project_name="Test",
            gerrit_server="gerrit.example.org",
            project_path="test",
            full_path="gerrit.example.org/test",
            committers=[
                CommitterInfo(name="Current1", activity_status="current"),
                CommitterInfo(name="Current2", activity_status="current"),
                CommitterInfo(name="Active1", activity_status="active"),
                CommitterInfo(name="Inactive1", activity_status="inactive"),
            ],
        )

        current = project.get_committers_by_status("current")
        active = project.get_committers_by_status("active")
        inactive = project.get_committers_by_status("inactive")

        assert len(current) == 2
        assert len(active) == 1
        assert len(inactive) == 1

    def test_get_committers_by_color(self):
        """Test filtering committers by color."""
        project = ProjectInfo(
            project_name="Test",
            gerrit_server="gerrit.example.org",
            project_path="test",
            full_path="gerrit.example.org/test",
            committers=[
                CommitterInfo(name="Green1", activity_color="green"),
                CommitterInfo(name="Green2", activity_color="green"),
                CommitterInfo(name="Orange1", activity_color="orange"),
                CommitterInfo(name="Red1", activity_color="red"),
                CommitterInfo(name="Gray1", activity_color="gray"),
            ],
        )

        green = project.get_committers_by_color("green")
        orange = project.get_committers_by_color("orange")
        red = project.get_committers_by_color("red")
        gray = project.get_committers_by_color("gray")

        assert len(green) == 2
        assert len(orange) == 1
        assert len(red) == 1
        assert len(gray) == 1

    def test_to_dict(self):
        """Test serialization to dictionary."""
        project = ProjectInfo(
            project_name="Test Project",
            gerrit_server="gerrit.example.org",
            project_path="test/project",
            full_path="gerrit.example.org/test/project",
            lifecycle_state="Active",
            committers=[CommitterInfo(name="Test User")],
        )

        result = project.to_dict()

        assert result["project_name"] == "Test Project"
        assert result["gerrit_server"] == "gerrit.example.org"
        assert result["project_path"] == "test/project"
        assert result["lifecycle_state"] == "Active"
        assert len(result["committers"]) == 1
        assert isinstance(result["committers"][0], dict)

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "project_name": "Test Project",
            "gerrit_server": "gerrit.example.org",
            "project_path": "test/project",
            "full_path": "gerrit.example.org/test/project",
            "creation_date": "2020-01-15",
            "lifecycle_state": "Active",
            "project_lead": {
                "name": "John Doe",
                "email": "john@example.com",
            },
            "committers": [
                {"name": "Alice Johnson", "email": "alice@example.com"},
                {"name": "Bob Williams", "email": "bob@example.com"},
            ],
            "issue_tracking": {
                "type": "jira",
                "url": "https://jira.example.org",
            },
            "repositories": ["test/repo1", "test/repo2"],
        }

        project = ProjectInfo.from_dict(data)

        assert project.project_name == "Test Project"
        assert project.gerrit_server == "gerrit.example.org"
        assert project.lifecycle_state == "Active"
        assert project.project_lead is not None
        assert project.project_lead.name == "John Doe"
        assert len(project.committers) == 2
        assert len(project.repositories) == 2


class TestLifecycleSummary:
    """Tests for LifecycleSummary domain model."""

    def test_create_valid_summary(self):
        """Test creating a valid LifecycleSummary object."""
        summary = LifecycleSummary(
            state="Active",
            count=42,
            percentage=65.5,
        )

        assert summary.state == "Active"
        assert summary.count == 42
        assert summary.percentage == 65.5

    def test_reject_negative_count(self):
        """Test that negative count is rejected."""
        with pytest.raises(ValueError, match="count must be non-negative"):
            LifecycleSummary(state="Active", count=-5, percentage=0.0)

    def test_reject_invalid_percentage(self):
        """Test that invalid percentage is rejected."""
        with pytest.raises(ValueError, match="percentage must be 0-100"):
            LifecycleSummary(state="Active", count=10, percentage=150.0)

        with pytest.raises(ValueError, match="percentage must be 0-100"):
            LifecycleSummary(state="Active", count=10, percentage=-5.0)

    def test_to_dict(self):
        """Test serialization to dictionary."""
        summary = LifecycleSummary(
            state="Incubation",
            count=15,
            percentage=23.4,
        )

        result = summary.to_dict()

        assert result == {
            "state": "Incubation",
            "count": 15,
            "percentage": 23.4,
        }

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "state": "Archived",
            "count": 8,
            "percentage": 12.5,
        }

        summary = LifecycleSummary.from_dict(data)

        assert summary.state == "Archived"
        assert summary.count == 8
        assert summary.percentage == 12.5

    def test_from_dict_with_defaults(self):
        """Test deserialization with missing fields."""
        data = {"state": "Unknown"}

        summary = LifecycleSummary.from_dict(data)

        assert summary.state == "Unknown"
        assert summary.count == 0
        assert summary.percentage == 0.0
