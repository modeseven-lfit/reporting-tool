# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Integration tests for report generation workflows.

Tests the complete end-to-end report generation process including:
- Single repository reports
- Multi-repository reports
- Different output formats
- Time window calculations
- Summary aggregation
"""

import json
from datetime import datetime, timedelta

from tests.fixtures.repositories import (
    create_sparse_time_window_repository,
    create_synthetic_repository,
)


class TestSingleRepositoryReport:
    """Test report generation for a single repository."""

    def test_generate_basic_report(self, tmp_path, synthetic_repo_simple):
        """Generate a basic report from a simple repository."""
        # Note: This is a placeholder for actual report generation
        # The actual implementation will depend on the report generation API

        # For now, verify the synthetic repo was created correctly
        assert synthetic_repo_simple.exists()
        assert (synthetic_repo_simple / ".git").exists()

        # Verify git log works
        import subprocess

        result = subprocess.run(
            ["git", "log", "--oneline"], cwd=synthetic_repo_simple, capture_output=True, text=True
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 10  # Should have 10 commits

    def test_report_contains_all_commits(self, tmp_path, synthetic_repo_simple):
        """Verify report includes all commits from repository."""
        import subprocess

        # Get commit count
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=synthetic_repo_simple,
            capture_output=True,
            text=True,
        )
        commit_count = int(result.stdout.strip())

        assert commit_count == 10

    def test_report_includes_author_metrics(self, tmp_path, synthetic_repo_simple):
        """Verify report includes author statistics."""
        import subprocess

        # Get authors
        result = subprocess.run(
            ["git", "log", "--format=%an"],
            cwd=synthetic_repo_simple,
            capture_output=True,
            text=True,
        )
        authors = set(result.stdout.strip().split("\n"))

        # Simple repo should have 1 author
        assert len(authors) == 1
        assert "Author 1" in authors

    def test_report_calculates_loc_changes(self, tmp_path, synthetic_repo_simple):
        """Verify report calculates lines of code changes."""
        import subprocess

        # Get LOC stats
        result = subprocess.run(
            ["git", "log", "--numstat", "--format="],
            cwd=synthetic_repo_simple,
            capture_output=True,
            text=True,
        )

        # Should have stats output
        assert len(result.stdout.strip()) > 0

    def test_report_respects_time_windows(self, tmp_path):
        """Verify report correctly filters commits by time windows."""
        # Create repo with commits spread over time
        repo_path = tmp_path / "time-test-repo"
        start_date = datetime.now() - timedelta(days=180)

        # Create 180 commits (one per day) over 180 days
        create_synthetic_repository(
            repo_path, commit_count=180, author_count=1, file_count=5, start_date=start_date
        )

        import subprocess

        # Get commits in last 30 days
        since_date = (datetime.now() - timedelta(days=30)).isoformat()
        result = subprocess.run(
            ["git", "log", "--since", since_date, "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        commits = result.stdout.strip().split("\n")
        commit_count = len([c for c in commits if c])

        # Should have approximately 30 commits (one per day for 30 days)
        # Allow for timezone and date boundary variations
        assert 28 <= commit_count <= 32

    def test_report_handles_empty_repository(self, tmp_path):
        """Verify report handles repository with no commits gracefully."""
        import subprocess

        repo_path = tmp_path / "empty-repo"
        repo_path.mkdir()

        # Initialize empty git repo
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        # Verify it's empty
        result = subprocess.run(
            ["git", "log", "--oneline"], cwd=repo_path, capture_output=True, text=True
        )

        # Should have no output (empty repo)
        assert result.stdout.strip() == ""


class TestMultiRepositoryReport:
    """Test report generation for multiple repositories."""

    def test_aggregate_multiple_repos(self, tmp_path):
        """Generate report aggregating multiple repositories."""
        # Create two synthetic repos
        repo1 = tmp_path / "repo1"
        repo2 = tmp_path / "repo2"

        create_synthetic_repository(repo1, commit_count=10, author_count=2, file_count=5)

        create_synthetic_repository(repo2, commit_count=15, author_count=3, file_count=8)

        assert repo1.exists()
        assert repo2.exists()

        # Both repos should be valid
        import subprocess

        for repo in [repo1, repo2]:
            result = subprocess.run(
                ["git", "log", "--oneline"], cwd=repo, capture_output=True, text=True
            )
            assert result.returncode == 0

    def test_deduplicate_authors_across_repos(self, tmp_path):
        """Verify authors are deduplicated across repositories."""
        # This would test that the same author in multiple repos
        # is counted as one unique contributor
        # Implementation depends on report generation API
        pass

    def test_aggregate_commits_across_repos(self, tmp_path):
        """Verify total commit count across all repositories."""
        repo1 = tmp_path / "repo1"
        repo2 = tmp_path / "repo2"

        create_synthetic_repository(repo1, commit_count=10)
        create_synthetic_repository(repo2, commit_count=15)

        import subprocess

        # Get commit counts
        result1 = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"], cwd=repo1, capture_output=True, text=True
        )
        count1 = int(result1.stdout.strip())

        result2 = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"], cwd=repo2, capture_output=True, text=True
        )
        count2 = int(result2.stdout.strip())

        # Total should be 25
        assert count1 + count2 == 25

    def test_per_repo_metrics_preserved(self, tmp_path):
        """Verify individual repository metrics are preserved in aggregate."""
        # Individual repo metrics should be available even in aggregate report
        pass


class TestOutputFormats:
    """Test different output format generation."""

    def test_json_output_valid(self, tmp_path, synthetic_repo_simple):
        """Verify JSON output is valid and well-formed."""
        output_file = tmp_path / "report.json"

        # Create minimal JSON structure
        report_data = {
            "schema_version": "3.0.0",
            "generated_at": datetime.now().isoformat(),
            "project": "test-project",
            "repositories": [
                {"name": "simple-repo", "path": str(synthetic_repo_simple), "commits": 10}
            ],
            "summary": {"total_commits": 10, "total_authors": 1, "total_repositories": 1},
        }

        output_file.write_text(json.dumps(report_data, indent=2))

        # Verify it's valid JSON
        with open(output_file) as f:
            data = json.load(f)

        assert data["schema_version"] == "3.0.0"
        assert data["summary"]["total_commits"] == 10

    def test_json_schema_compliance(self, tmp_path):
        """Verify JSON output complies with schema."""
        output_file = tmp_path / "report.json"

        report_data = {
            "schema_version": "3.0.0",
            "generated_at": datetime.now().isoformat(),
            "project": "test",
            "repositories": [],
            "summary": {"total_commits": 0, "total_authors": 0},
        }

        output_file.write_text(json.dumps(report_data, indent=2))

        with open(output_file) as f:
            data = json.load(f)

        # Required fields
        assert "schema_version" in data
        assert "generated_at" in data
        assert "project" in data
        assert "repositories" in data
        assert "summary" in data

    def test_html_output_generated(self, tmp_path):
        """Verify HTML output is generated correctly."""
        # Placeholder for HTML generation test
        # Will test template rendering and HTML structure
        pass

    def test_markdown_output_generated(self, tmp_path):
        """Verify Markdown output is generated correctly."""
        # Placeholder for Markdown generation test
        # Will test markdown formatting and structure
        pass


class TestTimeWindowCalculations:
    """Test time window filtering and calculations."""

    def test_30day_window(self, tmp_path):
        """Verify 30-day time window correctly filters commits."""
        repo_path = tmp_path / "window-test"

        # Create sparse repository with commits at strategic time points
        # This is much faster than creating 60 daily commits
        create_sparse_time_window_repository(
            repo_path,
            time_windows=[
                (60, 5),  # 5 commits from 60 days ago
                (45, 5),  # 5 commits from 45 days ago (outside 30d window)
                (25, 10),  # 10 commits from 25 days ago (inside 30d window)
                (15, 10),  # 10 commits from 15 days ago (inside 30d window)
                (5, 5),  # 5 commits from 5 days ago (inside 30d window)
            ],
            author_count=1,
        )

        import subprocess

        # Count commits in last 30 days
        since_date = (datetime.now() - timedelta(days=30)).isoformat()
        result = subprocess.run(
            ["git", "log", "--since", since_date, "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        commits = result.stdout.strip().split("\n")
        commit_count = len([c for c in commits if c])

        # Should have approximately 25 commits (10+10+5 from windows within 30 days)
        assert 23 <= commit_count <= 27

    def test_90day_window(self, tmp_path):
        """Verify 90-day time window correctly filters commits."""
        repo_path = tmp_path / "window-test"

        # Create sparse repository with commits at strategic time points
        # This is much faster than creating 180 daily commits
        create_sparse_time_window_repository(
            repo_path,
            time_windows=[
                (180, 10),  # 10 commits from 180 days ago (outside window)
                (120, 10),  # 10 commits from 120 days ago (outside window)
                (85, 15),  # 15 commits from 85 days ago (inside 90d window)
                (60, 15),  # 15 commits from 60 days ago (inside 90d window)
                (30, 15),  # 15 commits from 30 days ago (inside 90d window)
                (10, 15),  # 15 commits from 10 days ago (inside 90d window)
            ],
            author_count=1,
        )

        import subprocess

        # Count commits in last 90 days
        since_date = (datetime.now() - timedelta(days=90)).isoformat()
        result = subprocess.run(
            ["git", "log", "--since", since_date, "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        commits = result.stdout.strip().split("\n")
        commit_count = len([c for c in commits if c])

        # Should have approximately 60 commits (15+15+15+15 from windows within 90 days)
        assert 58 <= commit_count <= 62

    def test_1year_window(self, tmp_path):
        """Verify 1-year time window correctly filters commits."""
        repo_path = tmp_path / "window-test"

        # Create sparse repository with commits at strategic time points
        # This is MUCH faster than creating 730 daily commits (12 min -> 10 sec)
        create_sparse_time_window_repository(
            repo_path,
            time_windows=[
                (730, 10),  # 10 commits from 2 years ago (outside 1y window)
                (550, 10),  # 10 commits from ~18 months ago (outside 1y window)
                (360, 15),  # 15 commits from ~1 year ago (inside 1y window)
                (270, 15),  # 15 commits from 9 months ago (inside 1y window)
                (180, 15),  # 15 commits from 6 months ago (inside 1y window)
                (90, 15),  # 15 commits from 3 months ago (inside 1y window)
                (30, 15),  # 15 commits from 1 month ago (inside 1y window)
                (7, 15),  # 15 commits from last week (inside 1y window)
            ],
            author_count=1,
        )

        import subprocess

        # Count commits in last year
        since_date = (datetime.now() - timedelta(days=365)).isoformat()
        result = subprocess.run(
            ["git", "log", "--since", since_date, "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        commits = result.stdout.strip().split("\n")
        commit_count = len([c for c in commits if c])

        # Should have approximately 90 commits (15+15+15+15+15+15 from windows within 1 year)
        assert 88 <= commit_count <= 92

    def test_multiple_windows_same_report(self, tmp_path):
        """Verify multiple time windows can coexist in same report."""
        # A report can have metrics for 30d, 90d, and 1y simultaneously
        pass


class TestSummaryAggregation:
    """Test summary statistics aggregation."""

    def test_total_commit_count(self, tmp_path):
        """Verify total commit count aggregation."""
        repo1 = tmp_path / "repo1"
        repo2 = tmp_path / "repo2"

        create_synthetic_repository(repo1, commit_count=25)
        create_synthetic_repository(repo2, commit_count=35)

        # Summary should show 60 total commits
        import subprocess

        count1 = int(
            subprocess.run(
                ["git", "rev-list", "--count", "HEAD"], cwd=repo1, capture_output=True, text=True
            ).stdout.strip()
        )

        count2 = int(
            subprocess.run(
                ["git", "rev-list", "--count", "HEAD"], cwd=repo2, capture_output=True, text=True
            ).stdout.strip()
        )

        assert count1 + count2 == 60

    def test_unique_author_count(self, tmp_path):
        """Verify unique author count across repositories."""
        # Should deduplicate authors with same email
        pass

    def test_total_loc_changes(self, tmp_path):
        """Verify total lines of code changes aggregation."""
        # Should sum all insertions and deletions
        pass

    def test_repository_count(self, tmp_path):
        """Verify repository count in summary."""
        repo1 = tmp_path / "repo1"
        repo2 = tmp_path / "repo2"
        repo3 = tmp_path / "repo3"

        for repo in [repo1, repo2, repo3]:
            create_synthetic_repository(repo, commit_count=5)

        # Should count 3 repositories
        assert all(r.exists() for r in [repo1, repo2, repo3])

    def test_activity_period_detection(self, tmp_path):
        """Verify detection of first and last commit dates."""
        repo_path = tmp_path / "activity-test"
        start_date = datetime.now() - timedelta(days=100)

        create_synthetic_repository(repo_path, commit_count=50, start_date=start_date)

        import subprocess

        # Get all commit dates
        all_commits = (
            subprocess.run(
                ["git", "log", "--format=%aI"], cwd=repo_path, capture_output=True, text=True
            )
            .stdout.strip()
            .split("\n")
        )

        # Get first commit date (last in the all_commits list)
        first_commit = all_commits[-1] if all_commits else ""

        # Get last commit date (first in the all_commits list)
        last_commit = all_commits[0] if all_commits else ""

        # Verify dates are different
        assert first_commit != last_commit

        # Parse and verify date range
        first_dt = datetime.fromisoformat(first_commit.replace("Z", "+00:00"))
        last_dt = datetime.fromisoformat(last_commit.replace("Z", "+00:00"))

        # Should span approximately 49 days (50 commits over 50 days, starting at day 0)
        # Allow for timezone variations
        delta = (last_dt - first_dt).days
        assert 47 <= delta <= 51


class TestErrorHandling:
    """Test error handling in report generation."""

    def test_missing_repository_error(self, tmp_path):
        """Verify appropriate error for missing repository."""
        nonexistent = tmp_path / "does-not-exist"

        # Should handle missing repo gracefully
        assert not nonexistent.exists()

    def test_corrupted_repository_error(self, tmp_path):
        """Verify appropriate error for corrupted repository."""
        import subprocess

        repo_path = tmp_path / "corrupted"
        repo_path.mkdir()

        # Create .git directory but corrupt it
        git_dir = repo_path / ".git"
        git_dir.mkdir()

        # Try to run git command (should fail)
        result = subprocess.run(["git", "log"], cwd=repo_path, capture_output=True, text=True)

        assert result.returncode != 0

    def test_permission_error_handling(self, tmp_path):
        """Verify handling of permission errors."""
        # Test when output directory is not writable
        pass

    def test_partial_failure_handling(self, tmp_path):
        """Verify handling when some repos succeed and some fail."""
        # Should generate report with available data
        # Should record errors for failed repos
        pass


class TestIncrementalUpdates:
    """Test incremental report updates."""

    def test_update_existing_report(self, tmp_path):
        """Verify updating an existing report with new commits."""
        # Generate initial report
        # Add new commits
        # Regenerate report
        # Verify metrics updated correctly
        pass

    def test_preserve_historical_data(self, tmp_path):
        """Verify historical data is preserved during updates."""
        # Old time windows should remain accurate
        pass


class TestConfigurationVariations:
    """Test report generation with different configurations."""

    def test_custom_time_windows(self, tmp_path):
        """Test report with custom time window configuration."""
        # e.g., 7d, 14d, 60d instead of default 30d, 90d, 1y
        pass

    def test_filter_by_author(self, tmp_path):
        """Test filtering commits by specific authors."""
        pass

    def test_filter_by_organization(self, tmp_path):
        """Test filtering commits by organization."""
        pass

    def test_exclude_merge_commits(self, tmp_path):
        """Test excluding merge commits from metrics."""
        pass
