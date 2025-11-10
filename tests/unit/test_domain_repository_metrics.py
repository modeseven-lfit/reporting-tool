# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for RepositoryMetrics domain model.

Tests cover:
- Validation (required fields, activity status, non-negative counts, LOC consistency)
- Edge cases (no commits, errors, various activity states)
- Dictionary conversion (to_dict, from_dict)
- Property methods (is_active, is_current, has_errors, window getters)
"""

import pytest

from domain.repository_metrics import RepositoryMetrics


class TestRepositoryMetricsValidation:
    """Test RepositoryMetrics validation rules."""

    def test_empty_gerrit_project_raises_error(self):
        """Empty gerrit_project should raise ValueError."""
        with pytest.raises(ValueError, match="gerrit_project cannot be empty"):
            RepositoryMetrics(
                gerrit_project="",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
            )

    def test_empty_gerrit_host_raises_error(self):
        """Empty gerrit_host should raise ValueError."""
        with pytest.raises(ValueError, match="gerrit_host cannot be empty"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
            )

    def test_empty_gerrit_url_raises_error(self):
        """Empty gerrit_url should raise ValueError."""
        with pytest.raises(ValueError, match="gerrit_url cannot be empty"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="",
                local_path="/tmp/repo",
            )

    def test_empty_local_path_raises_error(self):
        """Empty local_path should raise ValueError."""
        with pytest.raises(ValueError, match="local_path cannot be empty"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="",
            )

    def test_invalid_activity_status_raises_error(self):
        """Invalid activity_status should raise ValueError."""
        with pytest.raises(ValueError, match="activity_status must be one of"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                activity_status="invalid",
            )

    def test_valid_activity_statuses(self):
        """Valid activity statuses: current, active, inactive."""
        for status in ["current", "active", "inactive"]:
            repo = RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                activity_status=status,
            )
            assert repo.activity_status == status

    def test_negative_total_commits_raises_error(self):
        """Negative total_commits_ever should raise ValueError."""
        with pytest.raises(ValueError, match="total_commits_ever must be non-negative"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                total_commits_ever=-5,
            )

    def test_negative_days_since_last_commit_raises_error(self):
        """Negative days_since_last_commit should raise ValueError."""
        with pytest.raises(ValueError, match="days_since_last_commit must be non-negative"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                days_since_last_commit=-10,
            )

    def test_negative_commit_counts_raises_error(self):
        """Negative commit_counts should raise ValueError."""
        with pytest.raises(ValueError, match="commit_counts.*must be non-negative"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                commit_counts={"1y": -10},
            )

    def test_negative_loc_added_raises_error(self):
        """Negative LOC added should raise ValueError."""
        with pytest.raises(ValueError, match="loc_stats.*added.*must be non-negative"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                loc_stats={"1y": {"added": -1000, "removed": 0, "net": -1000}},
            )

    def test_negative_loc_removed_raises_error(self):
        """Negative LOC removed should raise ValueError."""
        with pytest.raises(ValueError, match="loc_stats.*removed.*must be non-negative"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                loc_stats={"1y": {"added": 1000, "removed": -500, "net": 1500}},
            )

    def test_inconsistent_loc_net_raises_error(self):
        """LOC net must equal added - removed."""
        with pytest.raises(ValueError, match="loc_stats.*net.*must equal"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                loc_stats={"1y": {"added": 1000, "removed": 200, "net": 500}},  # Should be 800
            )

    def test_consistent_loc_net_valid(self):
        """Correctly calculated LOC net should be valid."""
        repo = RepositoryMetrics(
            gerrit_project="foo/bar",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/foo/bar",
            local_path="/tmp/repo",
            loc_stats={"1y": {"added": 1000, "removed": 200, "net": 800}},
        )
        assert repo.loc_stats["1y"]["net"] == 800

    def test_negative_loc_net_valid_if_consistent(self):
        """Negative LOC net is valid for net deletions."""
        repo = RepositoryMetrics(
            gerrit_project="foo/bar",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/foo/bar",
            local_path="/tmp/repo",
            loc_stats={"1y": {"added": 100, "removed": 500, "net": -400}},
        )
        assert repo.loc_stats["1y"]["net"] == -400

    def test_negative_unique_contributors_raises_error(self):
        """Negative unique_contributors should raise ValueError."""
        with pytest.raises(ValueError, match="unique_contributors.*must be non-negative"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                unique_contributors={"1y": -5},
            )

    def test_inconsistent_has_commits_and_total_raises_error(self):
        """has_any_commits=False with total_commits_ever>0 should raise error."""
        with pytest.raises(ValueError, match="Inconsistent state"):
            RepositoryMetrics(
                gerrit_project="foo/bar",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/foo/bar",
                local_path="/tmp/repo",
                has_any_commits=False,
                total_commits_ever=100,
            )

    def test_consistent_has_commits_false_with_zero_total(self):
        """has_any_commits=False with total=0 should be valid."""
        repo = RepositoryMetrics(
            gerrit_project="foo/bar",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/foo/bar",
            local_path="/tmp/repo",
            has_any_commits=False,
            total_commits_ever=0,
        )
        assert repo.has_any_commits is False
        assert repo.total_commits_ever == 0


class TestRepositoryMetricsCreation:
    """Test RepositoryMetrics instance creation."""

    def test_minimal_repository(self):
        """Create repository with only required fields."""
        repo = RepositoryMetrics(
            gerrit_project="foo/bar",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/foo/bar",
            local_path="/tmp/repos/foo-bar",
        )

        assert repo.gerrit_project == "foo/bar"
        assert repo.gerrit_host == "gerrit.example.com"
        assert repo.gerrit_url == "https://gerrit.example.com/foo/bar"
        assert repo.local_path == "/tmp/repos/foo-bar"
        assert repo.last_commit_timestamp is None
        assert repo.days_since_last_commit is None
        assert repo.activity_status == "inactive"
        assert repo.has_any_commits is False
        assert repo.total_commits_ever == 0
        assert repo.commit_counts == {}
        assert repo.loc_stats == {}
        assert repo.unique_contributors == {}
        assert repo.features == {}
        assert repo.authors == []
        assert repo.errors == []

    def test_full_repository(self):
        """Create repository with all fields populated."""
        repo = RepositoryMetrics(
            gerrit_project="myproject",
            gerrit_host="gerrit.internal.com",
            gerrit_url="https://gerrit.internal.com/myproject",
            local_path="/var/repos/myproject",
            last_commit_timestamp="2024-01-15T10:30:00Z",
            days_since_last_commit=5,
            activity_status="current",
            has_any_commits=True,
            total_commits_ever=500,
            commit_counts={"1y": 400, "90d": 100, "30d": 30},
            loc_stats={
                "1y": {"added": 20000, "removed": 5000, "net": 15000},
                "90d": {"added": 5000, "removed": 1000, "net": 4000},
            },
            unique_contributors={"1y": 15, "90d": 8, "30d": 5},
            features={"has_ci": True, "has_tests": True},
            authors=[{"email": "dev@example.com", "commits": 50}],
            errors=[],
        )

        assert repo.gerrit_project == "myproject"
        assert repo.activity_status == "current"
        assert repo.has_any_commits is True
        assert repo.total_commits_ever == 500
        assert repo.commit_counts["1y"] == 400
        assert repo.loc_stats["1y"]["net"] == 15000
        assert repo.unique_contributors["90d"] == 8

    def test_repository_with_errors(self):
        """Create repository with error messages."""
        repo = RepositoryMetrics(
            gerrit_project="problem/repo",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/problem/repo",
            local_path="/tmp/problem",
            errors=["Failed to fetch commits", "Git log error"],
        )

        assert len(repo.errors) == 2
        assert "Failed to fetch commits" in repo.errors


class TestRepositoryMetricsDictConversion:
    """Test dictionary serialization and deserialization."""

    def test_to_dict_minimal(self):
        """Convert minimal repository to dictionary."""
        repo = RepositoryMetrics(
            gerrit_project="simple",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/simple",
            local_path="/tmp/simple",
        )
        data = repo.to_dict()

        assert data["gerrit_project"] == "simple"
        assert data["gerrit_host"] == "gerrit.test.com"
        assert data["gerrit_url"] == "https://gerrit.test.com/simple"
        assert data["local_path"] == "/tmp/simple"
        assert data["last_commit_timestamp"] is None
        assert data["activity_status"] == "inactive"
        assert data["has_any_commits"] is False
        assert data["total_commits_ever"] == 0
        assert data["commit_counts"] == {}

    def test_to_dict_full(self):
        """Convert full repository to dictionary."""
        repo = RepositoryMetrics(
            gerrit_project="full",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/full",
            local_path="/tmp/full",
            last_commit_timestamp="2024-01-01T00:00:00Z",
            days_since_last_commit=10,
            activity_status="active",
            has_any_commits=True,
            total_commits_ever=200,
            commit_counts={"1y": 200},
            loc_stats={"1y": {"added": 10000, "removed": 2000, "net": 8000}},
            unique_contributors={"1y": 10},
            features={"ci": True},
            authors=[{"email": "dev@test.com"}],
            errors=["warning"],
        )
        data = repo.to_dict()

        assert data["gerrit_project"] == "full"
        assert data["last_commit_timestamp"] == "2024-01-01T00:00:00Z"
        assert data["days_since_last_commit"] == 10
        assert data["activity_status"] == "active"
        assert data["total_commits_ever"] == 200
        assert data["loc_stats"]["1y"]["net"] == 8000
        assert data["features"] == {"ci": True}
        assert len(data["authors"]) == 1
        assert len(data["errors"]) == 1

    def test_from_dict_minimal(self):
        """Create repository from minimal dictionary."""
        data = {
            "gerrit_project": "test",
            "gerrit_host": "gerrit.test.com",
            "gerrit_url": "https://gerrit.test.com/test",
            "local_path": "/tmp/test",
        }
        repo = RepositoryMetrics.from_dict(data)

        assert repo.gerrit_project == "test"
        assert repo.gerrit_host == "gerrit.test.com"
        assert repo.activity_status == "inactive"
        assert repo.has_any_commits is False

    def test_from_dict_full(self):
        """Create repository from full dictionary."""
        data = {
            "gerrit_project": "complex",
            "gerrit_host": "gerrit.example.com",
            "gerrit_url": "https://gerrit.example.com/complex",
            "local_path": "/var/complex",
            "last_commit_timestamp": "2024-06-01T12:00:00Z",
            "days_since_last_commit": 3,
            "activity_status": "current",
            "has_any_commits": True,
            "total_commits_ever": 1000,
            "commit_counts": {"1y": 800, "90d": 200},
            "loc_stats": {"1y": {"added": 50000, "removed": 10000, "net": 40000}},
            "unique_contributors": {"1y": 25},
            "features": {"workflows": ["ci", "cd"]},
            "authors": [{"email": "a@test.com"}, {"email": "b@test.com"}],
            "errors": [],
        }
        repo = RepositoryMetrics.from_dict(data)

        assert repo.gerrit_project == "complex"
        assert repo.last_commit_timestamp == "2024-06-01T12:00:00Z"
        assert repo.days_since_last_commit == 3
        assert repo.activity_status == "current"
        assert repo.total_commits_ever == 1000
        assert repo.commit_counts["90d"] == 200
        assert len(repo.authors) == 2

    def test_round_trip_conversion(self):
        """Test to_dict -> from_dict preserves data."""
        original = RepositoryMetrics(
            gerrit_project="roundtrip",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/roundtrip",
            local_path="/tmp/roundtrip",
            activity_status="active",
            has_any_commits=True,
            total_commits_ever=150,
            commit_counts={"1y": 150},
            loc_stats={"1y": {"added": 7500, "removed": 1500, "net": 6000}},
            unique_contributors={"1y": 12},
        )

        data = original.to_dict()
        restored = RepositoryMetrics.from_dict(data)

        assert restored.gerrit_project == original.gerrit_project
        assert restored.gerrit_host == original.gerrit_host
        assert restored.activity_status == original.activity_status
        assert restored.total_commits_ever == original.total_commits_ever
        assert restored.commit_counts == original.commit_counts
        assert restored.loc_stats == original.loc_stats


class TestRepositoryMetricsProperties:
    """Test property methods and computed values."""

    def test_is_active_current(self):
        """Repository with 'current' status is active."""
        repo = RepositoryMetrics(
            gerrit_project="test",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test",
            local_path="/tmp/test",
            activity_status="current",
        )
        assert repo.is_active is True

    def test_is_active_active(self):
        """Repository with 'active' status is active."""
        repo = RepositoryMetrics(
            gerrit_project="test",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test",
            local_path="/tmp/test",
            activity_status="active",
        )
        assert repo.is_active is True

    def test_is_active_inactive(self):
        """Repository with 'inactive' status is not active."""
        repo = RepositoryMetrics(
            gerrit_project="test",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test",
            local_path="/tmp/test",
            activity_status="inactive",
        )
        assert repo.is_active is False

    def test_is_current_true(self):
        """Repository with 'current' status is current."""
        repo = RepositoryMetrics(
            gerrit_project="test",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test",
            local_path="/tmp/test",
            activity_status="current",
        )
        assert repo.is_current is True

    def test_is_current_false(self):
        """Repository without 'current' status is not current."""
        for status in ["active", "inactive"]:
            repo = RepositoryMetrics(
                gerrit_project="test",
                gerrit_host="gerrit.test.com",
                gerrit_url="https://gerrit.test.com/test",
                local_path="/tmp/test",
                activity_status=status,
            )
            assert repo.is_current is False

    def test_has_errors_true(self):
        """Repository with errors should report has_errors=True."""
        repo = RepositoryMetrics(
            gerrit_project="test",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test",
            local_path="/tmp/test",
            errors=["Error 1", "Error 2"],
        )
        assert repo.has_errors is True

    def test_has_errors_false(self):
        """Repository without errors should report has_errors=False."""
        repo = RepositoryMetrics(
            gerrit_project="test",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test",
            local_path="/tmp/test",
            errors=[],
        )
        assert repo.has_errors is False

    def test_get_commits_in_window(self):
        """Get commits for specific window."""
        repo = RepositoryMetrics(
            gerrit_project="test",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test",
            local_path="/tmp/test",
            commit_counts={"1y": 100, "90d": 30, "30d": 10},
        )
        assert repo.get_commits_in_window("1y") == 100
        assert repo.get_commits_in_window("90d") == 30
        assert repo.get_commits_in_window("7d") == 0  # Missing

    def test_get_loc_stats_for_window(self):
        """Get LOC stats for specific window."""
        repo = RepositoryMetrics(
            gerrit_project="test",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test",
            local_path="/tmp/test",
            loc_stats={
                "1y": {"added": 5000, "removed": 1000, "net": 4000},
                "90d": {"added": 1500, "removed": 300, "net": 1200},
            },
        )

        stats_1y = repo.get_loc_stats_for_window("1y")
        assert stats_1y["added"] == 5000
        assert stats_1y["removed"] == 1000
        assert stats_1y["net"] == 4000

        stats_missing = repo.get_loc_stats_for_window("30d")
        assert stats_missing == {"added": 0, "removed": 0, "net": 0}

    def test_get_contributor_count_for_window(self):
        """Get contributor count for specific window."""
        repo = RepositoryMetrics(
            gerrit_project="test",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/test",
            local_path="/tmp/test",
            unique_contributors={"1y": 20, "90d": 12},
        )
        assert repo.get_contributor_count_for_window("1y") == 20
        assert repo.get_contributor_count_for_window("90d") == 12
        assert repo.get_contributor_count_for_window("30d") == 0


class TestRepositoryMetricsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_paths(self):
        """Handle unicode in project paths."""
        repo = RepositoryMetrics(
            gerrit_project="проект/тест",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/проект/тест",
            local_path="/tmp/проект-тест",
        )
        assert repo.gerrit_project == "проект/тест"

    def test_very_large_commit_counts(self):
        """Handle very large commit counts."""
        repo = RepositoryMetrics(
            gerrit_project="huge",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/huge",
            local_path="/tmp/huge",
            has_any_commits=True,
            total_commits_ever=10000000,
            commit_counts={"1y": 5000000},
        )
        assert repo.total_commits_ever == 10000000

    def test_very_large_loc_changes(self):
        """Handle very large LOC changes."""
        repo = RepositoryMetrics(
            gerrit_project="massive",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/massive",
            local_path="/tmp/massive",
            loc_stats={"1y": {"added": 100000000, "removed": 50000000, "net": 50000000}},
        )
        assert repo.loc_stats["1y"]["added"] == 100000000

    def test_many_time_windows(self):
        """Handle many different time windows."""
        windows = {f"{i}d": i * 5 for i in range(1, 101)}
        repo = RepositoryMetrics(
            gerrit_project="many-windows",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/many-windows",
            local_path="/tmp/many",
            commit_counts=windows,
        )
        assert len(repo.commit_counts) == 100

    def test_many_errors(self):
        """Handle many error messages."""
        errors = [f"Error {i}" for i in range(100)]
        repo = RepositoryMetrics(
            gerrit_project="buggy",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/buggy",
            local_path="/tmp/buggy",
            errors=errors,
        )
        assert len(repo.errors) == 100
        assert repo.has_errors is True

    def test_empty_repository_no_commits(self):
        """Handle repository with no commits at all."""
        repo = RepositoryMetrics(
            gerrit_project="empty",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/empty",
            local_path="/tmp/empty",
            has_any_commits=False,
            total_commits_ever=0,
        )
        assert repo.has_any_commits is False
        assert repo.total_commits_ever == 0

    def test_complex_nested_features(self):
        """Handle complex nested feature structures."""
        repo = RepositoryMetrics(
            gerrit_project="complex",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/complex",
            local_path="/tmp/complex",
            features={
                "ci": {"github_actions": True, "workflows": ["test.yml", "deploy.yml"]},
                "languages": ["python", "javascript"],
                "metrics": {"coverage": 85.5},
            },
        )
        assert repo.features["ci"]["github_actions"] is True
        assert len(repo.features["ci"]["workflows"]) == 2

    def test_zero_days_since_last_commit(self):
        """Handle repository with commit today (0 days)."""
        repo = RepositoryMetrics(
            gerrit_project="fresh",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/fresh",
            local_path="/tmp/fresh",
            days_since_last_commit=0,
            activity_status="current",
        )
        assert repo.days_since_last_commit == 0

    def test_very_old_last_commit(self):
        """Handle repository with very old last commit."""
        repo = RepositoryMetrics(
            gerrit_project="ancient",
            gerrit_host="gerrit.test.com",
            gerrit_url="https://gerrit.test.com/ancient",
            local_path="/tmp/ancient",
            days_since_last_commit=3650,  # 10 years
            activity_status="inactive",
        )
        assert repo.days_since_last_commit == 3650
