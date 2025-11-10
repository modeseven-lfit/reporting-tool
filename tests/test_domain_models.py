# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for domain models.

Tests validation, serialization, and convenience methods for all domain models:
- TimeWindow and TimeWindowStats
- RepositoryMetrics
- AuthorMetrics
- OrganizationMetrics
- WorkflowStatus
"""

import pytest

from cli.errors import ValidationError
from domain import (
    AuthorMetrics,
    OrganizationMetrics,
    RepositoryMetrics,
    TimeWindow,
    TimeWindowStats,
    WorkflowStatus,
)


class TestTimeWindow:
    """Test TimeWindow domain model."""

    def test_valid_time_window(self):
        """Test creating a valid time window."""
        window = TimeWindow(
            name="1y",
            days=365,
            start_date="2023-01-01T00:00:00Z",
            end_date="2024-01-01T00:00:00Z",
        )

        assert window.name == "1y"
        assert window.days == 365
        assert window.start_date == "2023-01-01T00:00:00Z"
        assert window.end_date == "2024-01-01T00:00:00Z"

    def test_to_dict(self):
        """Test TimeWindow serialization."""
        window = TimeWindow(
            name="90d",
            days=90,
            start_date="2023-10-01T00:00:00Z",
            end_date="2023-12-30T00:00:00Z",
        )

        result = window.to_dict()
        assert result == {
            "days": 90,
            "start": "2023-10-01T00:00:00Z",
            "end": "2023-12-30T00:00:00Z",
        }

    def test_from_dict(self):
        """Test TimeWindow deserialization."""
        data = {
            "days": 30,
            "start": "2023-12-01T00:00:00Z",
            "end": "2023-12-31T00:00:00Z",
        }

        window = TimeWindow.from_dict("30d", data)
        assert window.name == "30d"
        assert window.days == 30
        assert window.start_date == "2023-12-01T00:00:00Z"
        assert window.end_date == "2023-12-31T00:00:00Z"

    def test_invalid_days(self):
        """Test that negative or zero days raise ValidationError."""
        with pytest.raises(ValidationError, match="days.*must be positive"):
            TimeWindow(
                name="invalid",
                days=0,
                start_date="2023-01-01T00:00:00Z",
                end_date="2023-12-31T00:00:00Z",
            )

        with pytest.raises(ValidationError, match="days.*must be positive"):
            TimeWindow(
                name="invalid",
                days=-10,
                start_date="2023-01-01T00:00:00Z",
                end_date="2023-12-31T00:00:00Z",
            )

    def test_empty_name(self):
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError, match="name.*cannot be empty"):
            TimeWindow(
                name="",
                days=30,
                start_date="2023-01-01T00:00:00Z",
                end_date="2023-01-31T00:00:00Z",
            )

    def test_invalid_date_format(self):
        """Test that invalid date formats raise ValidationError."""
        with pytest.raises(ValidationError, match="start_date.*invalid ISO 8601 format"):
            TimeWindow(
                name="1y",
                days=365,
                start_date="not-a-date",
                end_date="2023-12-31T00:00:00Z",
            )


class TestTimeWindowStats:
    """Test TimeWindowStats domain model."""

    def test_valid_stats(self):
        """Test creating valid time window stats."""
        stats = TimeWindowStats(
            commits=42,
            lines_added=1000,
            lines_removed=200,
            lines_net=800,
            contributors=5,
        )

        assert stats.commits == 42
        assert stats.lines_added == 1000
        assert stats.lines_removed == 200
        assert stats.lines_net == 800
        assert stats.contributors == 5

    def test_default_values(self):
        """Test default zero values."""
        stats = TimeWindowStats()

        assert stats.commits == 0
        assert stats.lines_added == 0
        assert stats.lines_removed == 0
        assert stats.lines_net == 0
        assert stats.contributors == 0

    def test_negative_commits_invalid(self):
        """Test that negative commits raise ValidationError."""
        with pytest.raises(ValidationError, match="commits.*must be non-negative"):
            TimeWindowStats(commits=-1)

    def test_negative_lines_added_invalid(self):
        """Test that negative lines_added raises ValidationError."""
        with pytest.raises(ValidationError, match="lines_added.*must be non-negative"):
            TimeWindowStats(lines_added=-100)

    def test_negative_lines_removed_invalid(self):
        """Test that negative lines_removed raises ValidationError."""
        with pytest.raises(ValidationError, match="lines_removed.*must be non-negative"):
            TimeWindowStats(lines_removed=-50)

    def test_inconsistent_net_invalid(self):
        """Test that inconsistent lines_net raises ValidationError."""
        with pytest.raises(ValidationError, match="lines_net.*must equal"):
            TimeWindowStats(
                lines_added=1000,
                lines_removed=200,
                lines_net=500,  # Should be 800
            )

    def test_negative_net_allowed(self):
        """Test that negative net (deletion) is allowed."""
        stats = TimeWindowStats(
            lines_added=100,
            lines_removed=200,
            lines_net=-100,
        )
        assert stats.lines_net == -100

    def test_to_dict(self):
        """Test stats serialization."""
        stats = TimeWindowStats(
            commits=10,
            lines_added=500,
            lines_removed=100,
            lines_net=400,
            contributors=3,
        )

        result = stats.to_dict()
        assert result == {
            "commits": 10,
            "lines_added": 500,
            "lines_removed": 100,
            "lines_net": 400,
            "contributors": 3,
        }

    def test_to_dict_no_contributors(self):
        """Test serialization excludes zero contributors."""
        stats = TimeWindowStats(commits=5, lines_added=100, lines_removed=10, lines_net=90)
        result = stats.to_dict()
        assert "contributors" not in result

    def test_from_dict(self):
        """Test stats deserialization."""
        data = {
            "commits": 20,
            "lines_added": 800,
            "lines_removed": 300,
            "lines_net": 500,
            "contributors": 7,
        }

        stats = TimeWindowStats.from_dict(data)
        assert stats.commits == 20
        assert stats.lines_added == 800
        assert stats.lines_removed == 300
        assert stats.lines_net == 500
        assert stats.contributors == 7

    def test_addition(self):
        """Test adding two TimeWindowStats together."""
        stats1 = TimeWindowStats(
            commits=10, lines_added=100, lines_removed=20, lines_net=80, contributors=2
        )
        stats2 = TimeWindowStats(
            commits=5, lines_added=50, lines_removed=10, lines_net=40, contributors=1
        )

        result = stats1 + stats2
        assert result.commits == 15
        assert result.lines_added == 150
        assert result.lines_removed == 30
        assert result.lines_net == 120
        assert result.contributors == 3


class TestRepositoryMetrics:
    """Test RepositoryMetrics domain model."""

    def test_valid_repository_metrics(self):
        """Test creating valid repository metrics."""
        metrics = RepositoryMetrics(
            gerrit_project="foo/bar",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/foo/bar",
            local_path="/tmp/repos/foo-bar",
            activity_status="active",
            has_any_commits=True,
            total_commits_ever=100,
        )

        assert metrics.gerrit_project == "foo/bar"
        assert metrics.gerrit_host == "gerrit.example.com"
        assert metrics.is_active is True
        assert metrics.has_any_commits is True

    def test_empty_gerrit_project_invalid(self):
        """Test that empty gerrit_project raises ValueError."""
        with pytest.raises(ValueError, match="gerrit_project cannot be empty"):
            RepositoryMetrics(
                gerrit_project="",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/",
                local_path="/tmp/repos",
            )

    def test_invalid_activity_status(self):
        """Test that invalid activity_status raises ValueError."""
        with pytest.raises(ValueError, match="activity_status must be one of"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repos",
                activity_status="bogus",
            )

    def test_negative_total_commits_invalid(self):
        """Test that negative total_commits_ever raises ValueError."""
        with pytest.raises(ValueError, match="total_commits_ever must be non-negative"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repos",
                total_commits_ever=-10,
            )

    def test_inconsistent_commit_state_invalid(self):
        """Test that inconsistent has_any_commits/total raises ValueError."""
        with pytest.raises(ValueError, match="Inconsistent state"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repos",
                has_any_commits=False,
                total_commits_ever=10,
            )

    def test_negative_commit_counts_invalid(self):
        """Test that negative commit counts raise ValueError."""
        with pytest.raises(ValueError, match="commit_counts"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repos",
                commit_counts={"1y": -5},
            )

    def test_invalid_loc_stats(self):
        """Test that invalid LOC stats raise ValueError."""
        with pytest.raises(ValueError, match="loc_stats"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repos",
                loc_stats={"1y": {"added": 100, "removed": 50, "net": 0}},  # Should be 50
            )

    def test_to_dict(self):
        """Test repository metrics serialization."""
        metrics = RepositoryMetrics(
            gerrit_project="test/repo",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test/repo",
            local_path="/tmp/test-repo",
            has_any_commits=True,
            total_commits_ever=50,
            commit_counts={"1y": 25},
            loc_stats={"1y": {"added": 500, "removed": 100, "net": 400}},
        )

        result = metrics.to_dict()
        assert result["gerrit_project"] == "test/repo"
        assert result["total_commits_ever"] == 50
        assert result["commit_counts"] == {"1y": 25}

    def test_from_dict(self):
        """Test repository metrics deserialization."""
        data = {
            "gerrit_project": "test/repo",
            "gerrit_host": "gerrit.test.com",
            "gerrit_url": "https://gerrit.test.com/test/repo",
            "local_path": "/tmp/test-repo",
            "has_any_commits": True,
            "total_commits_ever": 75,
            "commit_counts": {"1y": 30},
            "errors": ["test error"],
        }

        metrics = RepositoryMetrics.from_dict(data)
        assert metrics.gerrit_project == "test/repo"
        assert metrics.total_commits_ever == 75
        assert metrics.has_errors is True

    def test_property_is_current(self):
        """Test is_current property."""
        metrics = RepositoryMetrics(
            gerrit_project="test/repo",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test/repo",
            local_path="/tmp/test-repo",
            activity_status="current",
        )
        assert metrics.is_current is True
        assert metrics.is_active is True

    def test_get_commits_in_window(self):
        """Test getting commits for a specific window."""
        metrics = RepositoryMetrics(
            gerrit_project="test/repo",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test/repo",
            local_path="/tmp/test-repo",
            commit_counts={"1y": 100, "90d": 50},
        )

        assert metrics.get_commits_in_window("1y") == 100
        assert metrics.get_commits_in_window("90d") == 50
        assert metrics.get_commits_in_window("30d") == 0


class TestAuthorMetrics:
    """Test AuthorMetrics domain model."""

    def test_valid_author_metrics(self):
        """Test creating valid author metrics."""
        metrics = AuthorMetrics(
            name="John Doe",
            email="john@example.com",
            username="johndoe",
            domain="example.com",
            commits={"1y": 42},
            lines_added={"1y": 1000},
            lines_removed={"1y": 200},
            lines_net={"1y": 800},
        )

        assert metrics.name == "John Doe"
        assert metrics.email == "john@example.com"
        assert metrics.domain == "example.com"
        assert metrics.is_affiliated is True

    def test_empty_email_invalid(self):
        """Test that empty email raises ValueError."""
        with pytest.raises(ValueError, match="email cannot be empty"):
            AuthorMetrics(name="John Doe", email="")

    def test_empty_name_uses_email(self):
        """Test that empty name defaults to email."""
        metrics = AuthorMetrics(name="", email="john@example.com")
        assert metrics.name == "john@example.com"

    def test_unknown_domain_not_affiliated(self):
        """Test that unknown domain means not affiliated."""
        metrics = AuthorMetrics(
            name="Jane Doe",
            email="jane@example.com",
            domain="unknown",
        )
        assert metrics.is_affiliated is False

    def test_negative_commits_invalid(self):
        """Test that negative commits raise ValueError."""
        with pytest.raises(ValueError, match="commits"):
            AuthorMetrics(
                name="John Doe",
                email="john@example.com",
                commits={"1y": -5},
                lines_added={"1y": 0},
                lines_removed={"1y": 0},
                lines_net={"1y": 0},
            )

    def test_inconsistent_net_invalid(self):
        """Test that inconsistent net lines raise ValueError."""
        with pytest.raises(ValueError, match="lines_net"):
            AuthorMetrics(
                name="John Doe",
                email="john@example.com",
                commits={"1y": 10},
                lines_added={"1y": 100},
                lines_removed={"1y": 50},
                lines_net={"1y": 0},  # Should be 50
            )

    def test_to_dict(self):
        """Test author metrics serialization."""
        metrics = AuthorMetrics(
            name="Jane Smith",
            email="jane@example.com",
            username="jsmith",
            domain="example.com",
            commits={"1y": 20},
            lines_added={"1y": 500},
            lines_removed={"1y": 100},
            lines_net={"1y": 400},
            repositories_touched={"1y": 3},
        )

        result = metrics.to_dict()
        assert result["name"] == "Jane Smith"
        assert result["email"] == "jane@example.com"
        assert result["commits"] == {"1y": 20}

    def test_from_dict(self):
        """Test author metrics deserialization."""
        data = {
            "name": "Bob Jones",
            "email": "bob@test.com",
            "username": "bjones",
            "domain": "test.com",
            "commits": {"1y": 15},
            "lines_added": {"1y": 300},
            "lines_removed": {"1y": 50},
            "lines_net": {"1y": 250},
            "repositories_touched": {"1y": 2},
        }

        metrics = AuthorMetrics.from_dict(data)
        assert metrics.name == "Bob Jones"
        assert metrics.total_commits == 15

    def test_from_dict_with_set_repositories(self):
        """Test deserialization converts repository sets to counts."""
        data = {
            "email": "alice@test.com",
            "repositories_touched": {"1y": {"repo1", "repo2", "repo3"}},
            "commits": {"1y": 10},
            "lines_added": {"1y": 100},
            "lines_removed": {"1y": 20},
            "lines_net": {"1y": 80},
        }

        metrics = AuthorMetrics.from_dict(data)
        assert metrics.repositories_touched == {"1y": 3}

    def test_total_properties(self):
        """Test total aggregation properties."""
        metrics = AuthorMetrics(
            name="Test User",
            email="test@example.com",
            commits={"1y": 10, "90d": 5, "30d": 2},
            lines_added={"1y": 100, "90d": 50, "30d": 20},
            lines_removed={"1y": 20, "90d": 10, "30d": 5},
            lines_net={"1y": 80, "90d": 40, "30d": 15},
        )

        assert metrics.total_commits == 17
        assert metrics.total_lines_added == 170
        assert metrics.total_lines_removed == 35
        assert metrics.total_lines_net == 135

    def test_get_window_methods(self):
        """Test window-specific getter methods."""
        metrics = AuthorMetrics(
            name="Test User",
            email="test@example.com",
            commits={"1y": 100},
            lines_added={"1y": 1000},
            lines_removed={"1y": 200},
            lines_net={"1y": 800},
            repositories_touched={"1y": 5},
        )

        assert metrics.get_commits_in_window("1y") == 100
        assert metrics.get_lines_added_in_window("1y") == 1000
        assert metrics.get_lines_removed_in_window("1y") == 200
        assert metrics.get_lines_net_in_window("1y") == 800
        assert metrics.get_repositories_in_window("1y") == 5
        assert metrics.get_commits_in_window("90d") == 0


class TestOrganizationMetrics:
    """Test OrganizationMetrics domain model."""

    def test_valid_organization_metrics(self):
        """Test creating valid organization metrics."""
        metrics = OrganizationMetrics(
            domain="example.com",
            contributor_count=10,
            commits={"1y": 500},
            lines_added={"1y": 10000},
            lines_removed={"1y": 2000},
            lines_net={"1y": 8000},
            repositories_count={"1y": 15},
        )

        assert metrics.domain == "example.com"
        assert metrics.contributor_count == 10
        assert metrics.is_known_org is True

    def test_empty_domain_invalid(self):
        """Test that empty domain raises ValueError."""
        with pytest.raises(ValueError, match="domain cannot be empty"):
            OrganizationMetrics(domain="")

    def test_unknown_domain_not_known(self):
        """Test that 'unknown' domain is not a known org."""
        metrics = OrganizationMetrics(domain="unknown")
        assert metrics.is_known_org is False

    def test_negative_contributor_count_invalid(self):
        """Test that negative contributor count raises ValueError."""
        with pytest.raises(ValueError, match="contributor_count must be non-negative"):
            OrganizationMetrics(domain="test.com", contributor_count=-1)

    def test_negative_commits_invalid(self):
        """Test that negative commits raise ValueError."""
        with pytest.raises(ValueError, match="commits"):
            OrganizationMetrics(
                domain="test.com",
                commits={"1y": -10},
                lines_added={"1y": 0},
                lines_removed={"1y": 0},
                lines_net={"1y": 0},
            )

    def test_inconsistent_net_invalid(self):
        """Test that inconsistent net lines raise ValueError."""
        with pytest.raises(ValueError, match="lines_net"):
            OrganizationMetrics(
                domain="test.com",
                commits={"1y": 100},
                lines_added={"1y": 1000},
                lines_removed={"1y": 200},
                lines_net={"1y": 500},  # Should be 800
            )

    def test_to_dict(self):
        """Test organization metrics serialization."""
        metrics = OrganizationMetrics(
            domain="acme.com",
            contributor_count=25,
            commits={"1y": 1000},
            lines_added={"1y": 20000},
            lines_removed={"1y": 5000},
            lines_net={"1y": 15000},
            repositories_count={"1y": 20},
        )

        result = metrics.to_dict()
        assert result["domain"] == "acme.com"
        assert result["contributor_count"] == 25
        assert result["commits"] == {"1y": 1000}

    def test_from_dict(self):
        """Test organization metrics deserialization."""
        data = {
            "domain": "bigcorp.com",
            "contributor_count": 50,
            "commits": {"1y": 2000},
            "lines_added": {"1y": 50000},
            "lines_removed": {"1y": 10000},
            "lines_net": {"1y": 40000},
            "repositories_count": {"1y": 30},
        }

        metrics = OrganizationMetrics.from_dict(data)
        assert metrics.domain == "bigcorp.com"
        assert metrics.contributor_count == 50

    def test_total_properties(self):
        """Test total aggregation properties."""
        metrics = OrganizationMetrics(
            domain="test.com",
            commits={"1y": 100, "90d": 50, "30d": 20},
            lines_added={"1y": 1000, "90d": 500, "30d": 200},
            lines_removed={"1y": 200, "90d": 100, "30d": 40},
            lines_net={"1y": 800, "90d": 400, "30d": 160},
        )

        assert metrics.total_commits == 170
        assert metrics.total_lines_added == 1700
        assert metrics.total_lines_removed == 340
        assert metrics.total_lines_net == 1360

    def test_get_window_methods(self):
        """Test window-specific getter methods."""
        metrics = OrganizationMetrics(
            domain="test.com",
            commits={"1y": 500},
            lines_added={"1y": 5000},
            lines_removed={"1y": 1000},
            lines_net={"1y": 4000},
            repositories_count={"1y": 10},
        )

        assert metrics.get_commits_in_window("1y") == 500
        assert metrics.get_lines_added_in_window("1y") == 5000
        assert metrics.get_lines_removed_in_window("1y") == 1000
        assert metrics.get_lines_net_in_window("1y") == 4000
        assert metrics.get_repositories_in_window("1y") == 10
        assert metrics.get_commits_in_window("90d") == 0


class TestWorkflowStatus:
    """Test WorkflowStatus domain model."""

    def test_valid_workflow_status(self):
        """Test creating valid workflow status."""
        status = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=False,
            workflow_files=[".github/workflows/ci.yml"],
            primary_ci_system="github_actions",
        )

        assert status.has_github_actions is True
        assert status.has_any_ci is True
        assert status.primary_ci_system == "github_actions"

    def test_no_ci_detected(self):
        """Test workflow status with no CI systems."""
        status = WorkflowStatus()
        assert status.has_any_ci is False
        assert status.ci_system_count == 0
        assert status.primary_ci_system is None

    def test_auto_detect_primary_ci(self):
        """Test automatic primary CI detection."""
        status = WorkflowStatus(has_github_actions=True, has_jenkins=True)
        # Should auto-detect github_actions as primary (first in priority)
        assert status.primary_ci_system == "github_actions"

    def test_multiple_ci_systems(self):
        """Test detection of multiple CI systems."""
        status = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=True,
            has_circleci=True,
        )

        assert status.has_multiple_ci_systems is True
        assert status.ci_system_count == 3
        assert len(status.get_detected_systems()) == 3

    def test_invalid_primary_ci_system(self):
        """Test that invalid primary CI system raises ValueError."""
        with pytest.raises(ValueError, match="primary_ci_system must be one of"):
            WorkflowStatus(primary_ci_system="invalid_ci")

    def test_to_dict(self):
        """Test workflow status serialization."""
        status = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=True,
            workflow_files=[".github/workflows/test.yml", "Jenkinsfile"],
            primary_ci_system="github_actions",
            additional_metadata={"custom": "data"},
        )

        result = status.to_dict()
        assert result["has_github_actions"] is True
        assert result["has_jenkins"] is True
        assert "workflow_files" in result
        assert "primary_ci_system" in result
        assert "additional_metadata" in result

    def test_to_dict_minimal(self):
        """Test serialization with minimal data."""
        status = WorkflowStatus(has_github_actions=True)
        result = status.to_dict()

        # Should include all boolean flags
        assert "has_github_actions" in result
        assert "has_jenkins" in result
        # Should include primary_ci_system when auto-detected
        assert result.get("primary_ci_system") == "github_actions"

    def test_from_dict(self):
        """Test workflow status deserialization."""
        data = {
            "has_github_actions": True,
            "has_jenkins": False,
            "has_circleci": True,
            "has_travis": False,
            "has_gitlab_ci": False,
            "workflow_files": [".github/workflows/ci.yml", ".circleci/config.yml"],
            "primary_ci_system": "github_actions",
        }

        status = WorkflowStatus.from_dict(data)
        assert status.has_github_actions is True
        assert status.has_circleci is True
        assert len(status.workflow_files) == 2

    def test_get_detected_systems(self):
        """Test getting list of detected systems."""
        status = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=True,
            has_travis=True,
        )

        systems = status.get_detected_systems()
        assert "github_actions" in systems
        assert "jenkins" in systems
        assert "travis" in systems
        assert len(systems) == 3


# Integration tests for combined usage
class TestDomainModelsIntegration:
    """Integration tests for using domain models together."""

    def test_repository_with_authors(self):
        """Test repository metrics with embedded author metrics."""
        author1 = AuthorMetrics(
            name="Alice",
            email="alice@example.com",
            commits={"1y": 50},
            lines_added={"1y": 500},
            lines_removed={"1y": 100},
            lines_net={"1y": 400},
        )

        author2 = AuthorMetrics(
            name="Bob",
            email="bob@example.com",
            commits={"1y": 30},
            lines_added={"1y": 300},
            lines_removed={"1y": 50},
            lines_net={"1y": 250},
        )

        repo = RepositoryMetrics(
            gerrit_project="test/project",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test/project",
            local_path="/tmp/test-project",
            total_commits_ever=80,
            has_any_commits=True,
            authors=[author1.to_dict(), author2.to_dict()],
        )

        assert len(repo.authors) == 2
        assert repo.total_commits_ever == 80

    def test_round_trip_serialization(self):
        """Test that models can round-trip through dict serialization."""
        original = AuthorMetrics(
            name="Test User",
            email="test@example.com",
            commits={"1y": 100, "90d": 50},
            lines_added={"1y": 1000, "90d": 500},
            lines_removed={"1y": 200, "90d": 100},
            lines_net={"1y": 800, "90d": 400},
            repositories_touched={"1y": 5, "90d": 3},
        )

        # Serialize to dict
        as_dict = original.to_dict()

        # Deserialize back
        restored = AuthorMetrics.from_dict(as_dict)

        # Should be equal
        assert restored.name == original.name
        assert restored.email == original.email
        assert restored.commits == original.commits
        assert restored.lines_net == original.lines_net
