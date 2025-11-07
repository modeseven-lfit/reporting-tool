# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Test Fixtures - Repository and Configuration Fixtures

This module provides reusable fixtures for creating synthetic git repositories
and test configurations for the Repository Reporting System tests.
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

# Import test utilities from test_utils (Phase 14: Test Reliability)
from test_utils import run_git_command_safe


# ============================================================================
# Repository Fixtures
# ============================================================================


@pytest.fixture
def temp_git_repo(tmp_path):
    """
    Create a temporary git repository for testing.

    Creates an initialized git repository with an initial commit so that
    HEAD exists and git commands that require a commit history will work.

    Yields:
        Path: Path to the temporary git repository
    """
    repo_path = tmp_path / "test-repo"
    repo_path.mkdir()

    # Initialize git repo
    run_git_command_safe(["git", "init"], cwd=repo_path, check=True, capture_output=True)

    # Configure git user
    run_git_command_safe(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True
    )
    run_git_command_safe(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit so HEAD exists
    readme_file = repo_path / "README.md"
    readme_file.write_text("# Test Repository\n\nInitial commit.\n")

    run_git_command_safe(
        ["git", "add", "README.md"], cwd=repo_path, check=True, capture_output=True
    )

    run_git_command_safe(
        ["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True
    )

    yield repo_path


@pytest.fixture
def synthetic_repo_simple(tmp_path):
    """
    Create a simple synthetic repository with 10 commits.

    Yields:
        Path: Path to the repository
    """
    repo_path = tmp_path / "simple-repo"
    create_synthetic_repository(repo_path, commit_count=10, author_count=1, file_count=5)
    yield repo_path


@pytest.fixture
def synthetic_repo_complex(tmp_path):
    """
    Create a complex synthetic repository with multiple authors and branches.

    Yields:
        Path: Path to the repository
    """
    repo_path = tmp_path / "complex-repo"
    create_synthetic_repository(
        repo_path,
        commit_count=50,
        author_count=5,
        file_count=20,
        branches=["main", "develop", "feature-x"],
    )
    yield repo_path


def create_synthetic_repository(
    repo_path: Path,
    commit_count: int = 10,
    author_count: int = 1,
    file_count: int = 5,
    branches: list[str] | None = None,
    start_date: datetime | None = None,
) -> Path:
    """
    Create a synthetic git repository with specified characteristics.

    Args:
        repo_path: Path where repository should be created
        commit_count: Number of commits to create
        author_count: Number of different authors
        file_count: Number of files to create
        branches: List of branch names to create
        start_date: Starting date for commits (defaults to 90 days ago)

    Returns:
        Path to the created repository
    """
    # Create directory
    repo_path.mkdir(parents=True, exist_ok=True)

    # Initialize git repo
    run_git_command_safe(["git", "init"], cwd=repo_path, check=True, capture_output=True)

    # Configure git to avoid hanging on user input
    run_git_command_safe(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True
    )
    run_git_command_safe(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Default start date is 90 days ago
    if start_date is None:
        start_date = datetime.now() - timedelta(days=90)

    # Generate authors
    authors = []
    for i in range(author_count):
        authors.append({"name": f"Author {i + 1}", "email": f"author{i + 1}@example.com"})

    # Create initial files
    for i in range(file_count):
        file_path = repo_path / f"file{i}.txt"
        file_path.write_text(f"Initial content {i}\n")

    # Create initial commit with all files
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = authors[0]["name"]
    env["GIT_AUTHOR_EMAIL"] = authors[0]["email"]
    env["GIT_COMMITTER_NAME"] = authors[0]["name"]
    env["GIT_COMMITTER_EMAIL"] = authors[0]["email"]

    date_str = start_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
    env["GIT_AUTHOR_DATE"] = date_str
    env["GIT_COMMITTER_DATE"] = date_str

    run_git_command_safe(
        ["git", "add", "."], cwd=repo_path, check=True, capture_output=True, env=env
    )

    run_git_command_safe(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        env=env,
    )

    # Create additional commits
    for commit_num in range(1, commit_count):
        # Rotate through authors
        author = authors[commit_num % len(authors)]

        # Set author for this commit
        env = os.environ.copy()
        env["GIT_AUTHOR_NAME"] = author["name"]
        env["GIT_AUTHOR_EMAIL"] = author["email"]
        env["GIT_COMMITTER_NAME"] = author["name"]
        env["GIT_COMMITTER_EMAIL"] = author["email"]

        # Set commit date
        commit_date = start_date + timedelta(days=commit_num)
        # Use RFC 2822 format for better git compatibility
        date_str = commit_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
        env["GIT_AUTHOR_DATE"] = date_str
        env["GIT_COMMITTER_DATE"] = date_str

        # Modify a random file
        file_index = commit_num % file_count
        file_path = repo_path / f"file{file_index}.txt"

        # Read current content and append
        current_content = file_path.read_text()
        file_path.write_text(current_content + f"Commit {commit_num}\n")

        # Stage changes
        run_git_command_safe(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True, env=env
        )

        # Commit
        run_git_command_safe(
            ["git", "commit", "-m", f"Commit {commit_num}: Update file{file_index}"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            env=env,
        )

    # Create additional branches if specified
    if branches and len(branches) > 1:
        for branch in branches[1:]:  # Skip first (already on main/master)
            run_git_command_safe(
                ["git", "checkout", "-b", branch], cwd=repo_path, check=True, capture_output=True
            )
            # Make a commit on this branch
            file_path = repo_path / f"{branch}.txt"
            file_path.write_text(f"Branch {branch} content\n")
            run_git_command_safe(
                ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
            )
            run_git_command_safe(
                ["git", "commit", "-m", f"Add {branch} branch file"],
                cwd=repo_path,
                check=True,
                capture_output=True,
            )

        # Return to main branch
        run_git_command_safe(
            ["git", "checkout", branches[0]], cwd=repo_path, check=True, capture_output=True
        )

    return repo_path


def create_sparse_time_window_repository(
    repo_path: Path, time_windows: list[tuple], author_count: int = 1, file_count: int = 5
) -> Path:
    """
    Create repository with commits at specific time points.

    Much faster than creating one commit per day - only creates commits
    at strategic time points to test date filtering.

    Args:
        repo_path: Where to create repository
        time_windows: List of (days_ago, commit_count) tuples
        author_count: Number of different authors
        file_count: Number of files to create

    Returns:
        Path to the created repository

    Example:
        # Instead of 730 commits (12 minutes), create 40 strategic commits (5 seconds)
        create_sparse_time_window_repository(
            path,
            time_windows=[
                (730, 10),  # 10 commits from 2 years ago
                (365, 10),  # 10 commits from 1 year ago
                (90, 10),   # 10 commits from 90 days ago
                (30, 10),   # 10 commits from 30 days ago
            ]
        )

    Runtime: ~5-10s vs ~700s for 730 individual commits (140x faster)
    """
    # Create directory
    repo_path.mkdir(parents=True, exist_ok=True)

    # Initialize git repo
    run_git_command_safe(["git", "init"], cwd=repo_path, check=True, capture_output=True)

    # Configure git
    run_git_command_safe(
        ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True, capture_output=True
    )
    run_git_command_safe(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Generate authors
    authors = []
    for i in range(author_count):
        authors.append({"name": f"Author {i + 1}", "email": f"author{i + 1}@example.com"})

    # Create initial files
    for i in range(file_count):
        file_path = repo_path / f"file{i}.txt"
        file_path.write_text(f"Initial content {i}\n")

    commit_num = 0

    # Process time windows from oldest to newest
    for days_ago, commit_count in sorted(time_windows, reverse=True):
        base_date = datetime.now() - timedelta(days=days_ago)

        for i in range(commit_count):
            # Spread commits across the period (hourly distribution)
            commit_date = base_date + timedelta(hours=i * 2)
            author = authors[commit_num % len(authors)]

            # Modify a file
            file_index = commit_num % file_count
            file_path = repo_path / f"file{file_index}.txt"
            current_content = file_path.read_text() if file_path.exists() else ""
            file_path.write_text(current_content + f"Commit {commit_num}\n")

            # Set environment for commit
            env = os.environ.copy()
            env["GIT_AUTHOR_NAME"] = author["name"]
            env["GIT_AUTHOR_EMAIL"] = author["email"]
            env["GIT_COMMITTER_NAME"] = author["name"]
            env["GIT_COMMITTER_EMAIL"] = author["email"]

            # Format date for git
            date_str = commit_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
            env["GIT_AUTHOR_DATE"] = date_str
            env["GIT_COMMITTER_DATE"] = date_str

            # Stage changes
            run_git_command_safe(
                ["git", "add", "."], cwd=repo_path, check=True, capture_output=True, env=env
            )

            # Commit
            run_git_command_safe(
                ["git", "commit", "-m", f"Commit {commit_num}: Update file{file_index}"],
                cwd=repo_path,
                check=True,
                capture_output=True,
                env=env,
            )

            commit_num += 1

    return repo_path


# ============================================================================
# Configuration Fixtures
# ============================================================================


@pytest.fixture
def test_config_minimal():
    """
    Provide a minimal test configuration.

    Returns:
        Dict: Minimal configuration dictionary
    """
    return {
        "project": "TestProject",
        "output_dir": "/tmp/test-output",
        "time_windows": {"days": [7, 30, 90]},
    }


@pytest.fixture
def test_config_complete():
    """
    Provide a complete test configuration with all options.

    Returns:
        Dict: Complete configuration dictionary
    """
    return {
        "project": "TestProject",
        "output_dir": "/tmp/test-output",
        "time_windows": {"days": [7, 30, 90, 365]},
        "output_formats": ["json", "html", "markdown"],
        "github": {"token": "test-token-12345", "api_url": "https://api.github.com"},
        "gerrit": {"url": "https://gerrit.example.com", "username": "test-user"},
        "performance": {
            "parallel_processing": {"enabled": True, "max_workers": 4},
            "caching": {"enabled": True, "ttl": 3600},
        },
        "rendering": {"template_engine": "jinja2", "theme": "default"},
    }


@pytest.fixture
def test_config_with_repos(tmp_path):
    """
    Provide a test configuration with repository paths.

    Args:
        tmp_path: Pytest tmp_path fixture

    Returns:
        Dict: Configuration with repository paths
    """
    repos_dir = tmp_path / "repositories"
    repos_dir.mkdir()

    return {
        "project": "TestProject",
        "output_dir": str(tmp_path / "output"),
        "repos_path": str(repos_dir),
        "time_windows": {"days": [7, 30, 90]},
    }


def create_test_config(**overrides) -> dict[str, Any]:
    """
    Create a test configuration with optional overrides.

    Args:
        **overrides: Configuration values to override

    Returns:
        Configuration dictionary
    """
    config = {
        "project": "TestProject",
        "output_dir": "/tmp/test-output",
        "time_windows": {"days": [7, 30, 90]},
        "output_formats": ["json"],
        "verbose": False,
    }

    # Apply overrides
    config.update(overrides)

    return config


# ============================================================================
# Data Fixtures
# ============================================================================


@pytest.fixture
def sample_commit_data():
    """
    Provide sample commit data for testing.

    Returns:
        List[Dict]: List of commit data dictionaries
    """
    return [
        {
            "sha": "abc123",
            "author": "Alice <alice@example.com>",
            "date": "2025-01-20T10:00:00Z",
            "message": "Add feature X",
            "files_changed": 3,
            "insertions": 50,
            "deletions": 10,
        },
        {
            "sha": "def456",
            "author": "Bob <bob@example.com>",
            "date": "2025-01-21T14:30:00Z",
            "message": "Fix bug Y",
            "files_changed": 1,
            "insertions": 5,
            "deletions": 3,
        },
        {
            "sha": "ghi789",
            "author": "Alice <alice@example.com>",
            "date": "2025-01-22T09:15:00Z",
            "message": "Update documentation",
            "files_changed": 2,
            "insertions": 25,
            "deletions": 0,
        },
    ]


@pytest.fixture
def sample_repository_data():
    """
    Provide sample repository data for testing.

    Returns:
        Dict: Repository data dictionary
    """
    return {
        "name": "test-repo",
        "url": "https://github.com/test-org/test-repo",
        "default_branch": "main",
        "total_commits": 150,
        "total_contributors": 5,
        "last_commit_date": "2025-01-25T12:00:00Z",
        "created_at": "2024-01-01T00:00:00Z",
        "languages": {"Python": 75.0, "JavaScript": 15.0, "Shell": 10.0},
    }


@pytest.fixture
def sample_author_data():
    """
    Provide sample author data for testing.

    Returns:
        List[Dict]: List of author data dictionaries
    """
    return [
        {
            "name": "Alice",
            "email": "alice@example.com",
            "commit_count": 50,
            "organization": "ExampleCorp",
            "first_commit": "2024-01-15",
            "last_commit": "2025-01-25",
        },
        {
            "name": "Bob",
            "email": "bob@example.com",
            "commit_count": 30,
            "organization": "ExampleCorp",
            "first_commit": "2024-03-10",
            "last_commit": "2025-01-20",
        },
        {
            "name": "Charlie",
            "email": "charlie@contractor.com",
            "commit_count": 20,
            "organization": "Contractor",
            "first_commit": "2024-06-01",
            "last_commit": "2024-12-31",
        },
    ]


# ============================================================================
# File Fixtures
# ============================================================================


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Create a temporary output directory.

    Yields:
        Path: Path to the temporary output directory
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    yield output_dir


@pytest.fixture
def sample_json_file(tmp_path):
    """
    Create a sample JSON file for testing.

    Yields:
        Path: Path to the JSON file
    """
    import json

    json_file = tmp_path / "sample.json"
    data = {
        "schema_version": "3.0.0",
        "project": "TestProject",
        "repositories": [],
        "summary": {"total_commits": 0, "total_authors": 0},
    }

    with open(json_file, "w") as f:
        json.dump(data, f, indent=2)

    yield json_file


# ============================================================================
# Environment Fixtures
# ============================================================================


@pytest.fixture
def mock_github_env(monkeypatch):
    """
    Set up mock GitHub environment variables.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    monkeypatch.setenv("GITHUB_TOKEN", "test-token-12345")
    monkeypatch.setenv("GITHUB_API_URL", "https://api.github.com")


@pytest.fixture
def clean_environment(monkeypatch):
    """
    Provide a clean environment by unsetting relevant variables.

    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    env_vars = ["GITHUB_TOKEN", "GERRIT_USERNAME", "GERRIT_PASSWORD", "REPORT_OUTPUT_DIR"]

    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
