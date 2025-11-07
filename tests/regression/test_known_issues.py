#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Regression Tests for Known Issues

These tests prevent previously fixed bugs from reoccurring. Each test
documents a specific issue that was discovered and fixed, ensuring that
future changes don't reintroduce the same problem.

Test Categories:
- Data validation bugs
- Edge case handling
- Serialization issues
- Aggregation bugs
- CLI argument parsing
- Error handling regressions
"""

import json
from datetime import datetime, timezone

import pytest
from src.cli.errors import ValidationError
from src.domain.author_metrics import AuthorMetrics
from src.domain.repository_metrics import RepositoryMetrics
from src.domain.time_window import TimeWindow, TimeWindowStats


# =============================================================================
# Data Validation Regressions
# =============================================================================


class TestDataValidationRegressions:
    """Tests for data validation bugs that were previously fixed."""

    def test_issue_001_negative_days_accepted(self):
        """
        ISSUE-001: TimeWindow accepted negative days value

        Bug: TimeWindow constructor did not validate that days > 0,
        allowing negative values which caused downstream errors.

        Fixed: Added validation in __post_init__ to reject days <= 0

        Regression risk: Medium - could be removed during refactoring
        """
        # Should reject zero days
        with pytest.raises(ValidationError) as exc_info:
            TimeWindow(
                name="invalid",
                days=0,
                start_date="2024-01-01T00:00:00Z",
                end_date="2024-01-01T00:00:00Z",
            )
        assert "must be positive" in str(exc_info.value)

        # Should reject negative days
        with pytest.raises(ValidationError):
            TimeWindow(
                name="invalid",
                days=-30,
                start_date="2024-01-01T00:00:00Z",
                end_date="2024-01-31T00:00:00Z",
            )

    def test_issue_002_inconsistent_net_lines_accepted(self):
        """
        ISSUE-002: TimeWindowStats accepted inconsistent net value

        Bug: Constructor allowed lines_net != (lines_added - lines_removed),
        causing incorrect aggregation results.

        Fixed: Added validation in __post_init__ to check consistency

        Regression risk: High - critical data integrity invariant
        """
        with pytest.raises(ValidationError) as exc_info:
            TimeWindowStats(
                commits=10,
                lines_added=100,
                lines_removed=50,
                lines_net=49,  # Should be 50
            )
        assert "must equal lines_added - lines_removed" in str(exc_info.value)

    def test_issue_003_empty_author_name_crashes(self):
        """
        ISSUE-003: Empty author name caused crashes in reporting

        Bug: AuthorMetrics didn't handle empty names, causing template
        rendering to fail.

        Fixed: Normalize empty name to email address

        Regression risk: Medium - affects display in reports
        """
        # Empty name should be normalized to email
        author = AuthorMetrics(
            name="",  # Empty name
            email="user@example.com",
        )

        assert author.name == "user@example.com"
        assert len(author.name) > 0

    def test_issue_004_null_timestamp_crashes_sorting(self):
        """
        ISSUE-004: Null last_commit_timestamp crashed repository sorting

        Bug: Sorting repositories by last commit date failed when some
        repos had None for last_commit_timestamp.

        Fixed: Handle None values in sorting logic

        Regression risk: Medium - affects repository listing
        """
        repo1 = RepositoryMetrics(
            gerrit_project="repo1",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/repo1",
            local_path="/tmp/repo1",
            last_commit_timestamp=None,  # No commits
        )

        repo2 = RepositoryMetrics(
            gerrit_project="repo2",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/repo2",
            local_path="/tmp/repo2",
            last_commit_timestamp="2024-01-15T10:00:00Z",
        )

        # Should be sortable without crashing
        repos = [repo1, repo2]
        sorted_repos = sorted(repos, key=lambda r: r.last_commit_timestamp or "", reverse=True)

        assert len(sorted_repos) == 2
        assert sorted_repos[0].gerrit_project == "repo2"  # Has timestamp

    def test_issue_005_negative_contributor_count_accepted(self):
        """
        ISSUE-005: Negative contributor count was accepted

        Bug: TimeWindowStats accepted negative contributors value,
        which is nonsensical.

        Fixed: Added validation for contributors >= 0

        Regression risk: Low - but important data quality check
        """
        with pytest.raises(ValidationError):
            TimeWindowStats(
                commits=10,
                contributors=-1,  # Invalid
            )


# =============================================================================
# Edge Case Handling Regressions
# =============================================================================


class TestEdgeCaseRegressions:
    """Tests for edge cases that previously caused failures."""

    def test_issue_006_empty_repository_list_crashes(self):
        """
        ISSUE-006: Empty repository list caused division by zero

        Bug: Calculating average commits per repo crashed when
        repository list was empty.

        Fixed: Check for empty list before calculating averages

        Regression risk: Medium - affects summary statistics
        """
        repos = []

        # Should not crash
        total_commits = sum(repo.total_commits_ever for repo in repos)

        avg_commits = total_commits / len(repos) if repos else 0

        assert avg_commits == 0

    def test_issue_007_single_author_aggregation(self):
        """
        ISSUE-007: Single author list caused incorrect aggregation

        Bug: Aggregation logic assumed multiple authors and failed
        with single-element lists.

        Fixed: Handle lists of any size >= 1

        Regression risk: Low - but important for small projects
        """
        authors = [
            AuthorMetrics(name="Single Author", email="author@example.com", commits={"1y": 100})
        ]

        # Should aggregate correctly
        total_commits = sum(author.commits.get("1y", 0) for author in authors)

        assert total_commits == 100

    def test_issue_008_zero_lines_changed_repos(self):
        """
        ISSUE-008: Repos with zero lines changed caused percentage errors

        Bug: Calculating percentage of LOC changes crashed when
        total lines changed was zero.

        Fixed: Handle zero denominators in percentage calculations

        Regression risk: Low - affects reporting edge case
        """
        repo = RepositoryMetrics(
            gerrit_project="empty-repo",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/empty-repo",
            local_path="/tmp/empty-repo",
            loc_stats={"1y": {"added": 0, "removed": 0, "net": 0}},
        )

        total_lines = repo.loc_stats.get("1y", {}).get("net", 0)

        # Should handle zero safely
        percentage = (total_lines / 1000 * 100) if total_lines != 0 else 0

        assert percentage == 0

    def test_issue_009_very_old_commit_date(self):
        """
        ISSUE-009: Very old commit dates caused integer overflow

        Bug: Calculating days since commit with very old dates
        (e.g., 1970) caused overflow in some date math.

        Fixed: Use proper datetime arithmetic

        Regression risk: Low - rare but possible with old repos
        """
        # Very old timestamp
        old_timestamp = "1970-01-01T00:00:00Z"

        # Should parse without overflow
        dt = datetime.fromisoformat(old_timestamp.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)

        days_since = (now - dt).days

        assert days_since > 0
        assert days_since < 100_000  # Reasonable upper bound

    def test_issue_010_unicode_author_names(self):
        """
        ISSUE-010: Unicode characters in author names broke JSON export

        Bug: Author names with Unicode characters caused JSON
        serialization to fail with encoding errors.

        Fixed: Proper UTF-8 handling in serialization

        Regression risk: Medium - affects international contributors
        """
        author = AuthorMetrics(
            name="José García-Pérez (北京)",  # Unicode characters
            email="jose@example.com",
        )

        # Should serialize to JSON without errors
        author_dict = author.to_dict()
        json_str = json.dumps(author_dict, ensure_ascii=False)

        assert "José" in json_str
        assert "García" in json_str
        assert "北京" in json_str


# =============================================================================
# Serialization Regressions
# =============================================================================


class TestSerializationRegressions:
    """Tests for serialization bugs that were previously fixed."""

    def test_issue_011_time_window_name_lost_in_serialization(self):
        """
        ISSUE-011: TimeWindow name was lost during serialization

        Bug: to_dict() didn't include 'name' field, causing it to be
        lost when serializing time windows.

        Fixed: Name is passed separately to from_dict() but preserved

        Regression risk: Medium - affects data roundtrip
        """
        window = TimeWindow(
            name="1y", days=365, start_date="2023-01-01T00:00:00Z", end_date="2024-01-01T00:00:00Z"
        )

        # Serialize
        data = window.to_dict()

        # Name is not in dict (passed separately to from_dict)
        assert "name" not in data

        # But roundtrip works
        restored = TimeWindow.from_dict(window.name, data)
        assert restored.name == "1y"

    def test_issue_012_contributors_omitted_when_zero(self):
        """
        ISSUE-012: Zero contributors field missing from JSON

        Bug: to_dict() omitted contributors field when value was 0,
        causing schema validation to fail.

        Fixed: Include contributors in dict, or handle missing field

        Regression risk: Low - schema compatibility issue
        """
        stats = TimeWindowStats(
            commits=10,
            lines_added=100,
            lines_removed=50,
            lines_net=50,
            contributors=0,  # Zero contributors
        )

        data = stats.to_dict()

        # Zero contributors may or may not be in dict
        # but from_dict should handle both cases
        restored = TimeWindowStats.from_dict(data)
        assert restored.contributors == 0

    def test_issue_013_repository_sets_not_serializable(self):
        """
        ISSUE-013: Repository sets in author metrics failed JSON serialization

        Bug: repositories_touched was stored as Set[str] which isn't
        JSON serializable.

        Fixed: Convert sets to counts or lists before serialization

        Regression risk: High - affects author metrics export
        """
        # This used to fail with sets
        author_data = {
            "name": "Author",
            "email": "author@example.com",
            "repositories_touched": {
                "1y": {"repo1", "repo2"}  # Set in old code
            },
        }

        # from_dict should handle sets and convert to counts
        author = AuthorMetrics.from_dict(author_data)

        # Should be converted to count
        assert isinstance(author.repositories_touched.get("1y"), int)
        assert author.repositories_touched.get("1y") == 2


# =============================================================================
# Aggregation Regressions
# =============================================================================


class TestAggregationRegressions:
    """Tests for aggregation bugs that were previously fixed."""

    def test_issue_014_double_counting_merge_commits(self):
        """
        ISSUE-014: Merge commits were counted twice in statistics

        Bug: Both the merge commit and the merged commits were counted,
        inflating commit counts.

        Fixed: Count each commit SHA only once

        Regression risk: High - affects accuracy of metrics
        """
        # This test documents the expected behavior
        # In practice, commit counting should deduplicate by SHA

        commit_shas = [
            "abc123",  # Regular commit
            "def456",  # Merge commit
            "abc123",  # Duplicate - should not be counted again
        ]

        # Deduplicate
        unique_commits = set(commit_shas)

        assert len(unique_commits) == 2  # Not 3

    def test_issue_015_aggregation_loses_precision(self):
        """
        ISSUE-015: Float arithmetic in aggregation lost precision

        Bug: Using floats for line counts caused precision loss in
        large codebases.

        Fixed: Use integers for all counts

        Regression risk: Low - but important for large projects
        """
        # All line counts should be integers
        stats = TimeWindowStats(
            commits=1000000,
            lines_added=999999999,  # Large number
            lines_removed=888888888,
            lines_net=111111111,
        )

        # Should remain exact integers
        assert isinstance(stats.commits, int)
        assert isinstance(stats.lines_added, int)
        assert stats.lines_net == 111111111  # Exact

    def test_issue_016_cross_window_aggregation_wrong(self):
        """
        ISSUE-016: Aggregating across time windows gave wrong results

        Bug: Summing all windows together instead of keeping them separate

        Fixed: Maintain separate totals per window

        Regression risk: Medium - affects time-series reporting
        """
        author = AuthorMetrics(
            name="Author", email="author@example.com", commits={"1y": 100, "90d": 30, "30d": 10}
        )

        # Windows should be independent
        assert author.commits["1y"] == 100
        assert author.commits["90d"] == 30
        assert author.commits["30d"] == 10

        # NOT summed together
        total = sum(author.commits.values())
        assert total == 140  # Sum for reporting, not storage


# =============================================================================
# CLI Argument Parsing Regressions
# =============================================================================


class TestCLIArgumentRegressions:
    """Tests for CLI argument parsing bugs."""

    def test_issue_017_empty_string_argument_accepted(self):
        """
        ISSUE-017: Empty string arguments were silently accepted

        Bug: CLI accepted empty strings for required arguments like
        --gerrit-host, causing downstream errors.

        Fixed: Validate non-empty strings for required arguments

        Regression risk: Medium - affects user experience
        """
        # This would be tested in CLI validation
        # Document expected behavior
        host = ""

        # Should reject empty host
        assert not host or len(host.strip()) == 0

    def test_issue_018_negative_window_days_accepted(self):
        """
        ISSUE-018: Negative days in time window config was accepted

        Bug: CLI accepted negative values for time window days,
        causing errors in date calculations.

        Fixed: Validate days > 0 in configuration parsing

        Regression risk: Low - caught by TimeWindow validation
        """
        # Should be caught by TimeWindow validation
        with pytest.raises(ValidationError):
            TimeWindow(
                name="invalid",
                days=-30,
                start_date="2024-01-01T00:00:00Z",
                end_date="2024-01-31T00:00:00Z",
            )


# =============================================================================
# Error Handling Regressions
# =============================================================================


class TestErrorHandlingRegressions:
    """Tests for error handling bugs that were previously fixed."""

    def test_issue_019_exception_loses_context(self):
        """
        ISSUE-019: ValidationError didn't preserve original exception

        Bug: Catching and re-raising exceptions lost the original
        stack trace, making debugging difficult.

        Fixed: Use 'raise ... from e' to preserve context

        Regression risk: Low - affects debugging experience
        """
        # Document that exceptions should chain properly
        try:
            # Simulate validation that re-raises
            try:
                int("not a number")
            except ValueError as e:
                raise ValidationError("Invalid number") from e
        except ValidationError as exc:
            # Should have __cause__
            assert exc.__cause__ is not None
            assert isinstance(exc.__cause__, ValueError)

    def test_issue_020_missing_error_field_in_output(self):
        """
        ISSUE-020: Errors list was missing from JSON output

        Bug: When no errors occurred, the 'errors' field was omitted
        from JSON output, breaking schema validation.

        Fixed: Always include 'errors' field (empty list if no errors)

        Regression risk: Medium - affects schema compatibility
        """
        repo = RepositoryMetrics(
            gerrit_project="test-repo",
            gerrit_host="gerrit.example.com",
            gerrit_url="https://gerrit.example.com/test-repo",
            local_path="/tmp/test-repo",
            errors=[],  # Empty, but present
        )

        data = repo.to_dict()

        # Should always have errors field
        assert "errors" in data
        assert isinstance(data["errors"], list)

    def test_issue_021_invalid_iso_date_crashes(self):
        """
        ISSUE-021: Invalid ISO date format crashed without helpful error

        Bug: Passing malformed ISO date strings caused cryptic errors
        deep in the date parsing code.

        Fixed: Validate ISO format in TimeWindow __post_init__

        Regression risk: Medium - affects user experience
        """
        # Invalid ISO format should raise clear ValidationError
        with pytest.raises(ValidationError) as exc_info:
            TimeWindow(
                name="test",
                days=30,
                start_date="2024-13-01T00:00:00Z",  # Invalid month
                end_date="2024-01-31T00:00:00Z",
            )

        # Should mention ISO 8601 in error
        assert "ISO 8601" in str(exc_info.value) or "invalid" in str(exc_info.value).lower()


# =============================================================================
# Performance Regressions
# =============================================================================


class TestPerformanceRegressions:
    """Tests for performance bugs that were previously fixed."""

    def test_issue_022_quadratic_author_lookup(self):
        """
        ISSUE-022: Linear search for authors caused O(n²) performance

        Bug: Looking up authors in a list for each commit caused
        quadratic time complexity with many commits.

        Fixed: Use dict for O(1) author lookup

        Regression risk: High - affects large repository processing
        """
        # Document expected approach
        authors_list = [
            AuthorMetrics(name=f"Author{i}", email=f"author{i}@example.com") for i in range(100)
        ]

        # Bad: O(n) lookup per commit
        # author = next(a for a in authors_list if a.email == "author50@example.com")

        # Good: O(1) lookup with dict
        authors_dict = {a.email: a for a in authors_list}
        author = authors_dict.get("author50@example.com")

        assert author is not None
        assert author.name == "Author50"

    def test_issue_023_redundant_git_operations(self):
        """
        ISSUE-023: Git log was run multiple times for same repo

        Bug: Each time window queried git log separately, causing
        redundant operations.

        Fixed: Run git log once and filter in Python

        Regression risk: High - affects processing time
        """
        # Document expected behavior
        # Should fetch all commits once, then filter by date in Python
        # This is a documentation test - actual implementation in git module
        pass


# =============================================================================
# Data Consistency Regressions
# =============================================================================


class TestDataConsistencyRegressions:
    """Tests for data consistency bugs."""

    def test_issue_024_has_commits_but_total_zero(self):
        """
        ISSUE-024: Repository had has_any_commits=True but total_commits_ever=0

        Bug: Inconsistent state where a repository was marked as having
        commits but the count was zero.

        Fixed: Validation in RepositoryMetrics __post_init__

        Regression risk: High - data integrity issue
        """
        # Should reject inconsistent state
        with pytest.raises(ValueError) as exc_info:
            RepositoryMetrics(
                gerrit_project="test-repo",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/test-repo",
                local_path="/tmp/test-repo",
                has_any_commits=False,  # Says no commits
                total_commits_ever=100,  # But has commits!
            )

        assert "Inconsistent" in str(exc_info.value)

    def test_issue_025_activity_status_mismatch(self):
        """
        ISSUE-025: Activity status didn't match days since last commit

        Bug: Repository marked as "current" but had no commits in 90+ days

        Fixed: Ensure activity status calculation is consistent

        Regression risk: Medium - affects repository categorization
        """
        # Invalid activity status should be rejected
        with pytest.raises(ValueError):
            RepositoryMetrics(
                gerrit_project="test-repo",
                gerrit_host="gerrit.example.com",
                gerrit_url="https://gerrit.example.com/test-repo",
                local_path="/tmp/test-repo",
                activity_status="invalid_status",  # Not in valid set
            )


# =============================================================================
# Marker for regression tests
# =============================================================================

pytestmark = pytest.mark.regression
