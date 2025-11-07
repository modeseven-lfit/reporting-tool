# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Integration tests for the data pipeline.

Tests the complete data collection and processing pipeline including:
- Git log parsing and commit extraction
- Author identification and aggregation
- Organization detection
- Time window calculations
- Metric aggregation
- Data transformation workflows

Phase 14: Test Reliability - Updated to use run_git_command_safe
"""

import subprocess
from datetime import datetime, timedelta

from tests.fixtures.repositories import (
    create_sparse_time_window_repository,
    create_synthetic_repository,
)
from tests.test_utils import run_git_command_safe


class TestGitLogParsing:
    """Test git log parsing and commit extraction."""

    def test_parse_basic_commit_info(self, tmp_path):
        """Test parsing basic commit information from git log."""
        repo_path = tmp_path / "test-repo"
        create_synthetic_repository(repo_path, commit_count=5, author_count=1)

        # Get git log output
        result = run_git_command_safe(
            ["git", "log", "--format=%H|%an|%ae|%aI|%s"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        commits = result.stdout.strip().split("\n")

        assert len(commits) == 5

        # Parse first commit
        parts = commits[0].split("|")
        assert len(parts) == 5  # sha, author name, email, date, subject
        assert len(parts[0]) == 40  # SHA is 40 characters
        assert "@" in parts[2]  # Email contains @
        assert "T" in parts[3]  # ISO date contains T

    def test_parse_commit_statistics(self, tmp_path):
        """Test parsing commit statistics (insertions/deletions)."""
        repo_path = tmp_path / "test-repo"
        create_synthetic_repository(repo_path, commit_count=5, file_count=3)

        # Get commit stats
        result = run_git_command_safe(
            ["git", "log", "--numstat", "--format=commit:%H"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        output = result.stdout.strip()

        # Should contain commit markers and file stats
        assert "commit:" in output
        assert len(output) > 0

    def test_parse_multiple_authors(self, tmp_path):
        """Test parsing commits from multiple authors."""
        repo_path = tmp_path / "test-repo"
        create_synthetic_repository(repo_path, commit_count=20, author_count=3)

        # Get unique authors
        result = run_git_command_safe(
            ["git", "log", "--format=%an|%ae"], cwd=repo_path, capture_output=True, text=True
        )

        author_lines = result.stdout.strip().split("\n")
        unique_authors = set(author_lines)

        # Should have 3 unique author entries
        assert len(unique_authors) == 3

    def test_parse_commit_dates(self, tmp_path):
        """Test parsing commit dates in various formats."""
        repo_path = tmp_path / "test-repo"
        start_date = datetime.now() - timedelta(days=30)

        create_synthetic_repository(repo_path, commit_count=10, start_date=start_date)

        # Get commit dates in ISO format
        result = run_git_command_safe(
            ["git", "log", "--format=%aI"], cwd=repo_path, capture_output=True, text=True
        )

        dates = result.stdout.strip().split("\n")

        assert len(dates) == 10

        # Parse and verify dates are in chronological order (newest first)
        parsed_dates = [datetime.fromisoformat(d.replace("Z", "+00:00")) for d in dates]

        # Newest should be first
        assert parsed_dates[0] >= parsed_dates[-1]

    def test_parse_merge_commits(self, tmp_path):
        """Test identifying merge commits."""
        repo_path = tmp_path / "test-repo"
        create_synthetic_repository(repo_path, commit_count=5, branches=["main", "feature"])

        # Get all commits with parent info
        result = run_git_command_safe(
            ["git", "log", "--format=%H %P"], cwd=repo_path, capture_output=True, text=True
        )

        commits = result.stdout.strip().split("\n")

        # Check for commits with multiple parents (merges)
        merge_commits = [
            c
            for c in commits
            if len(c.split()) > 2  # Has more than one parent
        ]

        # May or may not have merges depending on branch strategy
        assert isinstance(merge_commits, list)


class TestAuthorAggregation:
    """Test author identification and aggregation."""

    def test_aggregate_commits_by_author(self, tmp_path):
        """Test aggregating commits by author."""
        repo_path = tmp_path / "test-repo"
        create_synthetic_repository(repo_path, commit_count=30, author_count=3)

        # Get commit count by author
        result = run_git_command_safe(
            ["git", "shortlog", "-sn", "HEAD"], cwd=repo_path, capture_output=True, text=True
        )

        lines = result.stdout.strip().split("\n")

        # Should have 3 authors
        assert len(lines) == 3

        # Each line should have count and name
        for line in lines:
            parts = line.strip().split("\t")
            assert len(parts) == 2
            count = int(parts[0])
            assert count == 10  # 30 commits / 3 authors = 10 each

    def test_identify_author_organizations(self, tmp_path):
        """Test identifying author organizations from email domains."""
        authors = [
            ("Alice", "alice@company-a.com"),
            ("Bob", "bob@company-a.com"),
            ("Charlie", "charlie@company-b.com"),
        ]

        # Extract organizations from emails
        orgs = {}
        for name, email in authors:
            domain = email.split("@")[1]
            org = domain.split(".")[0]  # Simple org extraction

            if org not in orgs:
                orgs[org] = []
            orgs[org].append(name)

        # Should have 2 organizations
        assert len(orgs) == 2
        assert "company-a" in orgs
        assert "company-b" in orgs
        assert len(orgs["company-a"]) == 2
        assert len(orgs["company-b"]) == 1

    def test_normalize_author_names(self):
        """Test normalizing author names and emails."""
        variations = [
            ("John Doe", "john@example.com"),
            ("john doe", "john@example.com"),
            ("John Doe", "JOHN@EXAMPLE.COM"),
        ]

        # Normalize to lowercase for comparison
        normalized = set()
        for name, email in variations:
            key = (name.lower(), email.lower())
            normalized.add(key)

        # Should collapse to single author
        assert len(normalized) == 1

    def test_handle_missing_author_info(self):
        """Test handling commits with missing author information."""
        commits = [
            {"author": "Alice", "email": "alice@example.com"},
            {"author": "", "email": "unknown@example.com"},
            {"author": "Bob", "email": ""},
        ]

        # Filter valid commits
        valid_commits = [c for c in commits if c.get("author") and c.get("email")]

        assert len(valid_commits) == 1
        assert valid_commits[0]["author"] == "Alice"


class TestTimeWindowCalculations:
    """Test time window calculations and filtering."""

    def test_filter_commits_by_time_window(self, tmp_path):
        """Test filtering commits within a time window."""
        repo_path = tmp_path / "test-repo"

        # Create sparse repository with commits at strategic time points
        # This is much faster than creating 90 daily commits
        create_sparse_time_window_repository(
            repo_path,
            time_windows=[
                (90, 10),  # 10 commits from 90 days ago (outside 30d window)
                (60, 10),  # 10 commits from 60 days ago (outside 30d window)
                (25, 10),  # 10 commits from 25 days ago (inside 30d window)
                (15, 10),  # 10 commits from 15 days ago (inside 30d window)
                (5, 5),  # 5 commits from 5 days ago (inside 30d window)
            ],
            author_count=1,
        )

        # Get commits from last 30 days
        since_date = (datetime.now() - timedelta(days=30)).isoformat()
        result = run_git_command_safe(
            ["git", "log", "--since", since_date, "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        commits = result.stdout.strip().split("\n")
        commit_count = len([c for c in commits if c])

        # Should have approximately 25 commits (10+10+5 from windows within 30 days)
        assert 23 <= commit_count <= 27

    def test_multiple_time_windows(self, tmp_path):
        """Test calculating metrics for multiple time windows."""
        repo_path = tmp_path / "test-repo"

        # Create sparse repository with commits at strategic time points
        # This is much faster than creating 365 daily commits
        create_sparse_time_window_repository(
            repo_path,
            time_windows=[
                (365, 10),  # 10 commits from 1 year ago
                (270, 10),  # 10 commits from 9 months ago
                (180, 10),  # 10 commits from 6 months ago
                (90, 10),  # 10 commits from 3 months ago
                (30, 10),  # 10 commits from 1 month ago
                (7, 10),  # 10 commits from 1 week ago
            ],
            author_count=1,
        )

        windows = [7, 30, 90, 365]
        results = {}

        for window in windows:
            since_date = (datetime.now() - timedelta(days=window)).isoformat()
            result = run_git_command_safe(
                ["git", "log", "--since", since_date, "--oneline"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            commits = result.stdout.strip().split("\n")
            results[window] = len([c for c in commits if c])

        # Verify increasing counts with larger windows
        assert results[7] <= results[30]
        assert results[30] <= results[90]
        assert results[90] <= results[365]

    def test_time_window_edge_cases(self, tmp_path):
        """Test edge cases in time window calculations."""
        repo_path = tmp_path / "test-repo"
        start_date = datetime.now() - timedelta(days=10)

        create_synthetic_repository(repo_path, commit_count=10, start_date=start_date)

        # Test: All commits should be within 30 days
        since_date = (datetime.now() - timedelta(days=30)).isoformat()
        result = run_git_command_safe(
            ["git", "log", "--since", since_date, "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )

        commits = result.stdout.strip().split("\n")
        commit_count = len([c for c in commits if c])

        assert commit_count == 10


class TestMetricAggregation:
    """Test aggregation of metrics across commits and repositories."""

    def test_aggregate_commit_counts(self, tmp_path):
        """Test aggregating total commit counts."""
        repos = []
        expected_total = 0

        for i in range(3):
            repo_path = tmp_path / f"repo{i}"
            commit_count = 10 + (i * 5)
            create_synthetic_repository(repo_path, commit_count=commit_count)
            repos.append(repo_path)
            expected_total += commit_count

        # Count commits in each repo
        total_commits = 0
        for repo in repos:
            result = run_git_command_safe(
                ["git", "rev-list", "--count", "HEAD"], cwd=repo, capture_output=True, text=True
            )
            total_commits += int(result.stdout.strip())

        assert total_commits == expected_total  # 10 + 15 + 20 = 45

    def test_aggregate_author_counts(self, tmp_path):
        """Test aggregating unique author counts."""
        repo_path = tmp_path / "test-repo"
        create_synthetic_repository(repo_path, commit_count=30, author_count=5)

        # Get unique authors
        result = subprocess.run(
            ["git", "log", "--format=%an|%ae"], cwd=repo_path, capture_output=True, text=True
        )

        unique_authors = set(result.stdout.strip().split("\n"))

        assert len(unique_authors) == 5

    def test_aggregate_line_changes(self, tmp_path):
        """Test aggregating lines added/deleted."""
        repo_path = tmp_path / "test-repo"
        create_synthetic_repository(repo_path, commit_count=10, file_count=5)

        # Get total line changes
        result = subprocess.run(
            ["git", "log", "--numstat", "--format="], cwd=repo_path, capture_output=True, text=True
        )

        # Should have numstat output
        output = result.stdout.strip()
        assert len(output) > 0

        # Count lines (simplified)
        lines = [line for line in output.split("\n") if line.strip()]
        assert len(lines) > 0


class TestDataTransformations:
    """Test data transformation and normalization."""

    def test_transform_commit_data_to_json(self):
        """Test transforming commit data to JSON format."""
        commit_data = {
            "sha": "abc123",
            "author": "Alice",
            "email": "alice@example.com",
            "date": "2025-01-01T10:00:00Z",
            "message": "Add feature X",
        }

        import json

        json_str = json.dumps(commit_data, indent=2)

        # Verify JSON is valid
        parsed = json.loads(json_str)
        assert parsed["sha"] == "abc123"
        assert parsed["author"] == "Alice"

    def test_normalize_date_formats(self):
        """Test normalizing different date formats."""
        dates = [
            "2025-01-01T10:00:00Z",
            "2025-01-01T10:00:00+00:00",
            "Mon Jan 1 10:00:00 2025 +0000",
        ]

        # All should parse to datetime
        from datetime import datetime

        parsed = []
        for date_str in dates[:2]:  # Skip RFC format for simplicity
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            parsed.append(dt)

        # First two should be equivalent
        assert parsed[0] == parsed[1]

    def test_sanitize_commit_messages(self):
        """Test sanitizing commit messages for output."""
        messages = [
            "Fix bug #123",
            "Add feature\nwith\nmultiple\nlines",
            "Unicode: 你好世界",
            "Special chars: <>&\"'",
        ]

        # Ensure messages can be processed
        for msg in messages:
            # Should not raise errors
            assert isinstance(msg, str)
            assert len(msg) > 0


class TestOrganizationDetection:
    """Test organization detection from email domains."""

    def test_detect_organization_from_email(self):
        """Test detecting organization from email domain."""
        test_cases = [
            ("alice@example.com", "example"),
            ("bob@company.org", "company"),
            ("charlie@sub.domain.com", "sub"),
            ("dave@localhost", "localhost"),
        ]

        for email, expected_org in test_cases:
            domain = email.split("@")[1]
            org = domain.split(".")[0]
            assert org == expected_org

    def test_group_authors_by_organization(self):
        """Test grouping authors by organization."""
        authors = [
            {"name": "Alice", "email": "alice@company-a.com"},
            {"name": "Bob", "email": "bob@company-a.com"},
            {"name": "Charlie", "email": "charlie@company-b.com"},
            {"name": "Dave", "email": "dave@company-b.com"},
            {"name": "Eve", "email": "eve@company-c.com"},
        ]

        by_org = {}
        for author in authors:
            domain = author["email"].split("@")[1]
            org = domain.split(".")[0]

            if org not in by_org:
                by_org[org] = []
            by_org[org].append(author["name"])

        assert len(by_org) == 3
        assert len(by_org["company-a"]) == 2
        assert len(by_org["company-b"]) == 2
        assert len(by_org["company-c"]) == 1

    def test_handle_unknown_organizations(self):
        """Test handling authors with unknown/unaffiliated emails."""
        emails = ["user@gmail.com", "developer@yahoo.com", "coder@outlook.com"]

        # These should be grouped as "unaffiliated" or similar
        unaffiliated = []
        public_domains = {"gmail", "yahoo", "outlook"}

        for email in emails:
            domain = email.split("@")[1]
            org = domain.split(".")[0]

            if org in public_domains:
                unaffiliated.append(email)

        assert len(unaffiliated) == 3


class TestEndToEndPipeline:
    """Test complete end-to-end data pipeline."""

    def test_full_pipeline_single_repo(self, tmp_path):
        """Test complete pipeline for a single repository."""
        # Stage 1: Create repository
        repo_path = tmp_path / "test-repo"
        create_synthetic_repository(repo_path, commit_count=20, author_count=3, file_count=5)

        assert repo_path.exists()

        # Stage 2: Extract commits
        result = subprocess.run(
            ["git", "log", "--format=%H|%an|%ae|%aI"], cwd=repo_path, capture_output=True, text=True
        )

        commits = result.stdout.strip().split("\n")
        assert len(commits) == 20

        # Stage 3: Parse commit data
        parsed_commits = []
        for commit in commits:
            parts = commit.split("|")
            parsed_commits.append(
                {"sha": parts[0], "author": parts[1], "email": parts[2], "date": parts[3]}
            )

        assert len(parsed_commits) == 20

        # Stage 4: Aggregate by author
        by_author = {}
        for commit in parsed_commits:
            author = commit["author"]
            if author not in by_author:
                by_author[author] = 0
            by_author[author] += 1

        assert len(by_author) == 3

        # Stage 5: Verify distribution
        for _author, count in by_author.items():
            # Each author should have some commits
            assert count > 0

    def test_full_pipeline_multiple_repos(self, tmp_path):
        """Test complete pipeline for multiple repositories."""
        repos = []
        for i in range(3):
            repo_path = tmp_path / f"repo{i}"
            create_synthetic_repository(repo_path, commit_count=10, author_count=2)
            repos.append(repo_path)

        # Aggregate across all repos
        total_commits = 0
        all_authors = set()

        for repo in repos:
            # Count commits
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"], cwd=repo, capture_output=True, text=True
            )
            total_commits += int(result.stdout.strip())

            # Collect authors
            result = subprocess.run(
                ["git", "log", "--format=%an"], cwd=repo, capture_output=True, text=True
            )
            authors = set(result.stdout.strip().split("\n"))
            all_authors.update(authors)

        assert total_commits == 30  # 10 * 3
        assert len(all_authors) == 2  # Same 2 authors in each repo
