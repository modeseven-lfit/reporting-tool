# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Test Mocks - API Response Mock Factories

This module provides mock factories for GitHub and Gerrit API responses,
enabling comprehensive testing of API clients without making real network calls.
"""

from datetime import datetime, timedelta
from typing import Any
from unittest.mock import Mock

import responses


# ============================================================================
# GitHub API Mocks
# ============================================================================


class MockGitHubAPI:
    """Mock factory for GitHub API responses."""

    def __init__(self, base_url: str = "https://api.github.com"):
        """
        Initialize the GitHub API mock factory.

        Args:
            base_url: Base URL for the GitHub API
        """
        self.base_url = base_url
        self.responses = responses.RequestsMock()

    def mock_repository(
        self, owner: str = "test-owner", repo: str = "test-repo", **overrides
    ) -> dict[str, Any]:
        """
        Create a mock repository response.

        Args:
            owner: Repository owner
            repo: Repository name
            **overrides: Fields to override in the response

        Returns:
            Mock repository data dictionary
        """
        data = {
            "id": 123456,
            "name": repo,
            "full_name": f"{owner}/{repo}",
            "owner": {"login": owner, "id": 789, "type": "Organization"},
            "private": False,
            "description": f"Test repository {repo}",
            "fork": False,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2025-01-25T12:00:00Z",
            "pushed_at": "2025-01-25T12:00:00Z",
            "size": 1024,
            "stargazers_count": 42,
            "watchers_count": 42,
            "language": "Python",
            "forks_count": 10,
            "open_issues_count": 5,
            "default_branch": "main",
            "topics": ["python", "testing"],
            "visibility": "public",
            "has_issues": True,
            "has_projects": True,
            "has_wiki": True,
            "archived": False,
            "disabled": False,
        }
        data.update(overrides)
        return data

    def mock_commit(
        self,
        sha: str = "abc123def456",
        author_name: str = "Test Author",
        author_email: str = "test@example.com",
        message: str = "Test commit",
        date: str | None = None,
        **overrides,
    ) -> dict[str, Any]:
        """
        Create a mock commit response.

        Args:
            sha: Commit SHA
            author_name: Author name
            author_email: Author email
            message: Commit message
            date: Commit date (ISO format)
            **overrides: Fields to override

        Returns:
            Mock commit data dictionary
        """
        if date is None:
            date = datetime.now().isoformat() + "Z"

        data = {
            "sha": sha,
            "commit": {
                "author": {"name": author_name, "email": author_email, "date": date},
                "committer": {"name": author_name, "email": author_email, "date": date},
                "message": message,
                "tree": {
                    "sha": "tree123",
                    "url": "https://api.github.com/repos/test/test/git/trees/tree123",
                },
                "comment_count": 0,
            },
            "author": {"login": author_name.lower().replace(" ", ""), "id": 12345, "type": "User"},
            "committer": {
                "login": author_name.lower().replace(" ", ""),
                "id": 12345,
                "type": "User",
            },
            "parents": [
                {
                    "sha": "parent123",
                    "url": "https://api.github.com/repos/test/test/commits/parent123",
                }
            ],
            "stats": {"additions": 10, "deletions": 5, "total": 15},
            "files": [
                {
                    "filename": "test.py",
                    "additions": 10,
                    "deletions": 5,
                    "changes": 15,
                    "status": "modified",
                }
            ],
        }
        data.update(overrides)
        return data

    def mock_commits_list(
        self, count: int = 10, start_date: datetime | None = None
    ) -> list[dict[str, Any]]:
        """
        Create a list of mock commits.

        Args:
            count: Number of commits to generate
            start_date: Starting date for commits

        Returns:
            List of mock commit dictionaries
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)

        commits = []
        for i in range(count):
            commit_date = start_date + timedelta(days=i)
            commit = self.mock_commit(
                sha=f"commit{i:03d}", message=f"Commit {i}", date=commit_date.isoformat() + "Z"
            )
            commits.append(commit)

        return commits

    def mock_contributor(
        self, login: str = "testuser", contributions: int = 42, **overrides
    ) -> dict[str, Any]:
        """
        Create a mock contributor response.

        Args:
            login: User login name
            contributions: Number of contributions
            **overrides: Fields to override

        Returns:
            Mock contributor data dictionary
        """
        data = {
            "login": login,
            "id": 12345,
            "avatar_url": "https://avatars.githubusercontent.com/u/12345",
            "type": "User",
            "contributions": contributions,
        }
        data.update(overrides)
        return data

    def mock_rate_limit(
        self, remaining: int = 5000, limit: int = 5000, reset_time: int | None = None
    ) -> dict[str, Any]:
        """
        Create a mock rate limit response.

        Args:
            remaining: Remaining API calls
            limit: Total API limit
            reset_time: Unix timestamp when limit resets

        Returns:
            Mock rate limit data dictionary
        """
        if reset_time is None:
            reset_time = int((datetime.now() + timedelta(hours=1)).timestamp())

        return {
            "resources": {
                "core": {
                    "limit": limit,
                    "remaining": remaining,
                    "reset": reset_time,
                    "used": limit - remaining,
                }
            }
        }

    def add_repository_response(
        self, owner: str = "test-owner", repo: str = "test-repo", status: int = 200, **overrides
    ):
        """
        Add a mocked repository API response.

        Args:
            owner: Repository owner
            repo: Repository name
            status: HTTP status code
            **overrides: Response data overrides
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        data = self.mock_repository(owner=owner, repo=repo, **overrides)
        self.responses.add(responses.GET, url, json=data, status=status)

    def add_commits_response(
        self, owner: str = "test-owner", repo: str = "test-repo", count: int = 10, status: int = 200
    ):
        """
        Add a mocked commits list API response.

        Args:
            owner: Repository owner
            repo: Repository name
            count: Number of commits
            status: HTTP status code
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        data = self.mock_commits_list(count=count)
        self.responses.add(responses.GET, url, json=data, status=status)

    def add_error_response(self, url: str, status: int = 404, message: str = "Not Found"):
        """
        Add a mocked error response.

        Args:
            url: API endpoint URL
            status: HTTP status code
            message: Error message
        """
        self.responses.add(responses.GET, url, json={"message": message}, status=status)


# ============================================================================
# Gerrit API Mocks
# ============================================================================


class MockGerritAPI:
    """Mock factory for Gerrit API responses."""

    def __init__(self, base_url: str = "https://gerrit.example.com"):
        """
        Initialize the Gerrit API mock factory.

        Args:
            base_url: Base URL for the Gerrit API
        """
        self.base_url = base_url
        self.responses = responses.RequestsMock()

    def mock_project(self, name: str = "test-project", **overrides) -> dict[str, Any]:
        """
        Create a mock Gerrit project response.

        Args:
            name: Project name
            **overrides: Fields to override

        Returns:
            Mock project data dictionary
        """
        data = {
            "id": name,
            "name": name,
            "parent": "All-Projects",
            "description": f"Test project {name}",
            "state": "ACTIVE",
            "web_links": [
                {"name": "browse", "url": f"https://gerrit.example.com/admin/projects/{name}"}
            ],
        }
        data.update(overrides)
        return data

    def mock_projects_list(self, count: int = 5) -> dict[str, dict[str, Any]]:
        """
        Create a mock Gerrit projects list response.

        Args:
            count: Number of projects

        Returns:
            Dictionary of project name to project data
        """
        projects = {}
        for i in range(count):
            name = f"project-{i}"
            projects[name] = self.mock_project(name=name)
        return projects

    def mock_change(
        self,
        change_id: str = "I1234567890abcdef",
        project: str = "test-project",
        subject: str = "Test change",
        status: str = "MERGED",
        **overrides,
    ) -> dict[str, Any]:
        """
        Create a mock Gerrit change response.

        Args:
            change_id: Change ID
            project: Project name
            subject: Change subject
            status: Change status
            **overrides: Fields to override

        Returns:
            Mock change data dictionary
        """
        data = {
            "id": change_id,
            "project": project,
            "branch": "main",
            "topic": "test-topic",
            "change_id": change_id,
            "subject": subject,
            "status": status,
            "created": "2025-01-20 10:00:00.000000000",
            "updated": "2025-01-25 12:00:00.000000000",
            "submitted": "2025-01-25 11:00:00.000000000",
            "insertions": 10,
            "deletions": 5,
            "owner": {"name": "Test Author", "email": "test@example.com"},
        }
        data.update(overrides)
        return data

    def add_projects_response(self, count: int = 5, status: int = 200):
        """
        Add a mocked projects list API response.

        Args:
            count: Number of projects
            status: HTTP status code
        """
        url = f"{self.base_url}/projects/"
        # Gerrit returns )]}' prefix for security
        data = self.mock_projects_list(count=count)
        response_text = ")]}'\n" + str(data)
        self.responses.add(responses.GET, url, body=response_text, status=status)


# ============================================================================
# Mock Git Repository
# ============================================================================


class MockGitRepository:
    """Mock factory for git repository operations."""

    def __init__(self, repo_path: str = "/tmp/test-repo"):
        """
        Initialize the git repository mock.

        Args:
            repo_path: Path to the mock repository
        """
        self.repo_path = repo_path
        self.commits = []
        self.branches = ["main"]
        self.tags = []

    def add_commit(self, sha: str, author: str, date: str, message: str, files_changed: int = 1):
        """
        Add a mock commit to the repository.

        Args:
            sha: Commit SHA
            author: Author name and email
            date: Commit date
            message: Commit message
            files_changed: Number of files changed
        """
        self.commits.append(
            {
                "sha": sha,
                "author": author,
                "date": date,
                "message": message,
                "files_changed": files_changed,
            }
        )

    def add_branch(self, name: str):
        """Add a branch to the repository."""
        if name not in self.branches:
            self.branches.append(name)

    def add_tag(self, name: str, sha: str):
        """Add a tag to the repository."""
        self.tags.append({"name": name, "sha": sha})

    def get_log(self, **kwargs) -> list[dict[str, Any]]:
        """Get mock git log."""
        return self.commits

    def get_branches(self) -> list[str]:
        """Get mock branch list."""
        return self.branches

    def get_tags(self) -> list[dict[str, str]]:
        """Get mock tag list."""
        return self.tags


# ============================================================================
# Helper Functions
# ============================================================================


def create_mock_response(
    status_code: int = 200,
    json_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Mock:
    """
    Create a mock HTTP response object.

    Args:
        status_code: HTTP status code
        json_data: JSON response data
        headers: Response headers

    Returns:
        Mock response object
    """
    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.json = Mock(return_value=json_data or {})
    mock_response.headers = headers or {}
    mock_response.text = str(json_data) if json_data else ""
    mock_response.ok = 200 <= status_code < 300
    return mock_response


def create_mock_api_error(
    status_code: int = 404, message: str = "Not Found", error_type: str = "NotFoundError"
) -> Mock:
    """
    Create a mock API error response.

    Args:
        status_code: HTTP status code
        message: Error message
        error_type: Error type

    Returns:
        Mock error response
    """
    mock_response = create_mock_response(
        status_code=status_code,
        json_data={
            "message": message,
            "documentation_url": "https://docs.example.com/api",
            "type": error_type,
        },
    )
    mock_response.raise_for_status = Mock(side_effect=Exception(message))
    return mock_response


def mock_github_rate_limit_headers(
    remaining: int = 5000, limit: int = 5000, reset_time: int | None = None
) -> dict[str, str]:
    """
    Create mock GitHub rate limit headers.

    Args:
        remaining: Remaining API calls
        limit: Total API limit
        reset_time: Unix timestamp when limit resets

    Returns:
        Dictionary of rate limit headers
    """
    if reset_time is None:
        reset_time = int((datetime.now() + timedelta(hours=1)).timestamp())

    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_time),
        "X-RateLimit-Used": str(limit - remaining),
    }
