#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
JSON Snapshot Regression Tests

These tests capture snapshots of JSON output to detect unintended changes
in the report structure. When the output format intentionally changes,
snapshots can be updated with pytest --snapshot-update.

Test Categories:
- Domain model serialization snapshots
- Report structure snapshots
- Time window snapshots
- Author metrics snapshots
- Repository metrics snapshots
"""

import json

import pytest

from domain.author_metrics import AuthorMetrics
from domain.repository_metrics import RepositoryMetrics
from domain.time_window import TimeWindow, TimeWindowStats


# =============================================================================
# Domain Model Serialization Snapshots
# =============================================================================


class TestTimeWindowSnapshots:
    """Snapshot tests for TimeWindow serialization."""

    def test_time_window_to_dict_snapshot(self, snapshot):
        """
        Snapshot: TimeWindow.to_dict() output structure

        Captures the expected JSON structure for a time window.
        Any changes to the serialization format will be detected.
        """
        window = TimeWindow(
            name="1y", days=365, start_date="2023-01-01T00:00:00Z", end_date="2024-01-01T00:00:00Z"
        )

        output = window.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="time_window")

    def test_time_window_stats_to_dict_snapshot(self, snapshot):
        """
        Snapshot: TimeWindowStats.to_dict() output structure

        Captures the expected JSON structure for time window statistics.
        """
        stats = TimeWindowStats(
            commits=150, lines_added=5000, lines_removed=2000, lines_net=3000, contributors=25
        )

        output = stats.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="time_window_stats")

    def test_time_window_stats_zero_contributors_snapshot(self, snapshot):
        """
        Snapshot: TimeWindowStats with zero contributors

        Tests how zero values are serialized (may be omitted or included).
        """
        stats = TimeWindowStats(
            commits=10,
            lines_added=100,
            lines_removed=50,
            lines_net=50,
            contributors=0,  # Zero contributors
        )

        output = stats.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(
            name="stats_zero_contributors"
        )


class TestAuthorMetricsSnapshots:
    """Snapshot tests for AuthorMetrics serialization."""

    def test_author_metrics_basic_snapshot(self, snapshot):
        """
        Snapshot: Basic AuthorMetrics.to_dict() output

        Captures the expected structure for author metrics.
        """
        author = AuthorMetrics(
            name="John Doe",
            email="john.doe@example.com",
            username="jdoe",
            domain="example.com",
            commits={"1y": 100, "90d": 30, "30d": 10},
            lines_added={"1y": 5000, "90d": 1500, "30d": 500},
            lines_removed={"1y": 2000, "90d": 600, "30d": 200},
            lines_net={"1y": 3000, "90d": 900, "30d": 300},
            repositories_touched={"1y": 5, "90d": 3, "30d": 1},
        )

        output = author.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="author_basic")

    def test_author_metrics_minimal_snapshot(self, snapshot):
        """
        Snapshot: Minimal AuthorMetrics (only required fields)

        Tests serialization with minimal data.
        """
        author = AuthorMetrics(name="Jane Smith", email="jane@example.com")

        output = author.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="author_minimal")

    def test_author_metrics_empty_name_snapshot(self, snapshot):
        """
        Snapshot: AuthorMetrics with empty name (normalized to email)

        Tests the name normalization behavior.
        """
        author = AuthorMetrics(
            name="",  # Empty, should be normalized
            email="unknown@example.com",
        )

        output = author.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="author_empty_name")

    def test_author_metrics_unicode_snapshot(self, snapshot):
        """
        Snapshot: AuthorMetrics with Unicode characters

        Tests Unicode handling in serialization.
        """
        author = AuthorMetrics(
            name="José García-Pérez (北京)", email="jose@example.com", commits={"1y": 50}
        )

        output = author.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False) == snapshot(
            name="author_unicode"
        )


class TestRepositoryMetricsSnapshots:
    """Snapshot tests for RepositoryMetrics serialization."""

    def test_repository_metrics_active_snapshot(self, snapshot):
        """
        Snapshot: Active repository with commits

        Captures the structure for an active repository.
        """
        repo = RepositoryMetrics(
            gerrit_project="openstack/nova",
            gerrit_host="review.opendev.org",
            gerrit_url="https://review.opendev.org/openstack/nova",
            local_path="/repos/openstack/nova",
            last_commit_timestamp="2024-01-15T14:30:00Z",
            days_since_last_commit=10,
            activity_status="current",
            has_any_commits=True,
            total_commits_ever=50000,
            commit_counts={"1y": 1500, "90d": 400, "30d": 120},
            loc_stats={
                "1y": {"added": 50000, "removed": 30000, "net": 20000},
                "90d": {"added": 15000, "removed": 10000, "net": 5000},
                "30d": {"added": 5000, "removed": 3000, "net": 2000},
            },
            unique_contributors={"1y": 150, "90d": 50, "30d": 20},
            features={"has_github_actions": True, "has_jenkins": False},
            errors=[],
        )

        output = repo.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="repo_active")

    def test_repository_metrics_inactive_snapshot(self, snapshot):
        """
        Snapshot: Inactive repository with no recent commits

        Captures the structure for an inactive repository.
        """
        repo = RepositoryMetrics(
            gerrit_project="archived/old-project",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/archived/old-project",
            local_path="/repos/archived/old-project",
            last_commit_timestamp="2020-06-01T10:00:00Z",
            days_since_last_commit=1300,
            activity_status="inactive",
            has_any_commits=True,
            total_commits_ever=500,
            commit_counts={"1y": 0, "90d": 0, "30d": 0},
            loc_stats={
                "1y": {"added": 0, "removed": 0, "net": 0},
                "90d": {"added": 0, "removed": 0, "net": 0},
                "30d": {"added": 0, "removed": 0, "net": 0},
            },
            unique_contributors={"1y": 0, "90d": 0, "30d": 0},
            errors=[],
        )

        output = repo.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="repo_inactive")

    def test_repository_metrics_empty_snapshot(self, snapshot):
        """
        Snapshot: Empty repository with no commits

        Captures the structure for a repository with no commits.
        """
        repo = RepositoryMetrics(
            gerrit_project="new/empty-repo",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/new/empty-repo",
            local_path="/repos/new/empty-repo",
            last_commit_timestamp=None,
            days_since_last_commit=None,
            activity_status="inactive",
            has_any_commits=False,
            total_commits_ever=0,
            commit_counts={},
            loc_stats={},
            unique_contributors={},
            errors=[],
        )

        output = repo.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="repo_empty")

    def test_repository_metrics_with_errors_snapshot(self, snapshot):
        """
        Snapshot: Repository with processing errors

        Captures how errors are included in the output.
        """
        repo = RepositoryMetrics(
            gerrit_project="problem/repo",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/problem/repo",
            local_path="/repos/problem/repo",
            errors=[
                "Failed to parse commit: abc123",
                "Invalid author email: malformed@",
                "Timeout during git log operation",
            ],
        )

        output = repo.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="repo_with_errors")


# =============================================================================
# Composite Structure Snapshots
# =============================================================================


class TestCompositeStructureSnapshots:
    """Snapshot tests for complex nested structures."""

    def test_multiple_time_windows_snapshot(self, snapshot):
        """
        Snapshot: Multiple time windows dictionary

        Captures how multiple windows are structured together.
        """
        windows = {
            "1y": TimeWindow(
                name="1y",
                days=365,
                start_date="2023-01-01T00:00:00Z",
                end_date="2024-01-01T00:00:00Z",
            ),
            "90d": TimeWindow(
                name="90d",
                days=90,
                start_date="2023-10-03T00:00:00Z",
                end_date="2024-01-01T00:00:00Z",
            ),
            "30d": TimeWindow(
                name="30d",
                days=30,
                start_date="2023-12-02T00:00:00Z",
                end_date="2024-01-01T00:00:00Z",
            ),
        }

        output = {name: window.to_dict() for name, window in windows.items()}
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="multiple_windows")

    def test_author_list_snapshot(self, snapshot):
        """
        Snapshot: List of author metrics

        Captures how a list of authors is structured.
        """
        authors = [
            AuthorMetrics(
                name="Alice Developer",
                email="alice@example.com",
                commits={"1y": 200},
                lines_added={"1y": 10000},
                lines_removed={"1y": 5000},
                lines_net={"1y": 5000},
            ),
            AuthorMetrics(
                name="Bob Engineer",
                email="bob@example.com",
                commits={"1y": 150},
                lines_added={"1y": 7500},
                lines_removed={"1y": 3000},
                lines_net={"1y": 4500},
            ),
        ]

        output = [author.to_dict() for author in authors]
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="author_list")

    def test_repository_list_snapshot(self, snapshot):
        """
        Snapshot: List of repository metrics

        Captures how a list of repositories is structured.
        """
        repos = [
            RepositoryMetrics(
                gerrit_project="project-a",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/project-a",
                local_path="/repos/project-a",
                activity_status="current",
                has_any_commits=True,
                total_commits_ever=1000,
            ),
            RepositoryMetrics(
                gerrit_project="project-b",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/project-b",
                local_path="/repos/project-b",
                activity_status="active",
                has_any_commits=True,
                total_commits_ever=500,
            ),
        ]

        output = [repo.to_dict() for repo in repos]
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="repo_list")


# =============================================================================
# Edge Case Snapshots
# =============================================================================


class TestEdgeCaseSnapshots:
    """Snapshot tests for edge cases in serialization."""

    def test_negative_net_lines_snapshot(self, snapshot):
        """
        Snapshot: Stats with negative net lines (net deletion)

        Tests serialization of negative net values.
        """
        stats = TimeWindowStats(
            commits=50,
            lines_added=1000,
            lines_removed=3000,
            lines_net=-2000,  # Negative (net deletion)
            contributors=10,
        )

        output = stats.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="negative_net_lines")

    def test_zero_everything_snapshot(self, snapshot):
        """
        Snapshot: Stats with all zeros

        Tests serialization of all-zero statistics.
        """
        stats = TimeWindowStats(
            commits=0, lines_added=0, lines_removed=0, lines_net=0, contributors=0
        )

        output = stats.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="zero_everything")

    def test_very_large_numbers_snapshot(self, snapshot):
        """
        Snapshot: Stats with very large numbers

        Tests serialization of large values (integer precision).
        """
        stats = TimeWindowStats(
            commits=1000000,
            lines_added=999999999,
            lines_removed=500000000,
            lines_net=499999999,
            contributors=50000,
        )

        output = stats.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="very_large_numbers")

    def test_special_characters_in_names_snapshot(self, snapshot):
        """
        Snapshot: Author with special characters in name

        Tests handling of special characters.
        """
        author = AuthorMetrics(
            name="O'Brien-Smith & Co. <dev@example.com>", email="obrien@example.com"
        )

        output = author.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="special_characters")

    def test_long_repository_path_snapshot(self, snapshot):
        """
        Snapshot: Repository with very long path

        Tests handling of long path names.
        """
        repo = RepositoryMetrics(
            gerrit_project="org/team/subteam/project/very/deep/nested/repository",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/org/team/subteam/project/very/deep/nested/repository",
            local_path="/very/long/path/to/repositories/org/team/subteam/project/very/deep/nested/repository",
        )

        output = repo.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="long_path")


# =============================================================================
# Regression Prevention Snapshots
# =============================================================================


class TestRegressionPreventionSnapshots:
    """Snapshots that prevent specific regressions."""

    def test_time_window_name_not_in_dict_snapshot(self, snapshot):
        """
        Snapshot: TimeWindow dict doesn't include name (by design)

        Regression: Name was accidentally added to dict, breaking from_dict
        """
        window = TimeWindow(
            name="test_window",
            days=30,
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-01-31T00:00:00Z",
        )

        output = window.to_dict()

        # Verify name is not in output
        assert "name" not in output

        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(
            name="window_name_not_in_dict"
        )

    def test_empty_collections_snapshot(self, snapshot):
        """
        Snapshot: How empty collections are serialized

        Regression: Empty dicts/lists were sometimes omitted
        """
        author = AuthorMetrics(
            name="New Author",
            email="new@example.com",
            commits={},  # Empty
            lines_added={},
            lines_removed={},
            lines_net={},
            repositories_touched={},
        )

        output = author.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="empty_collections")

    def test_field_order_stability_snapshot(self, snapshot):
        """
        Snapshot: Field ordering is stable

        Regression: Field order changed randomly, breaking diffs
        """
        repo = RepositoryMetrics(
            gerrit_project="test-repo",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/test-repo",
            local_path="/tmp/test-repo",
            activity_status="active",
            has_any_commits=True,
            total_commits_ever=100,
        )

        # Sort keys to ensure stable ordering
        output = repo.to_dict()
        assert json.dumps(output, indent=2, sort_keys=True) == snapshot(name="field_order_stable")


# =============================================================================
# Marker for regression tests
# =============================================================================

pytestmark = pytest.mark.regression
