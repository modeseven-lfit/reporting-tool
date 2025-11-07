# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Extended unit tests for GitHub API client.

Tests cover:
- Workflow runs status fetching
- Workflow status computation logic
- Color computation from status/state
- Summary generation
- Error handling edge cases
- Pagination scenarios
"""

from unittest.mock import Mock, patch

import httpx
import pytest
from src.api.github_client import GitHubAPIClient


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_stats():
    """Mock statistics tracker."""
    stats = Mock()
    stats.record_success = Mock()
    stats.record_error = Mock()
    stats.record_exception = Mock()
    return stats


@pytest.fixture
def github_client(mock_stats):
    """Create a GitHubAPIClient instance for testing."""
    client = GitHubAPIClient(token="test_token_12345", timeout=30.0, stats=mock_stats)
    yield client
    client.close()


def create_mock_workflow_run(
    run_id=123,
    run_number=456,
    conclusion="success",
    status="completed",
    created_at="2025-01-27T10:00:00Z",
    updated_at="2025-01-27T10:30:00Z",
    html_url="https://github.com/test/repo/actions/runs/123",
    head_branch="main",
    head_sha="abc123def456",
):
    """Helper to create mock workflow run data."""
    return {
        "id": run_id,
        "run_number": run_number,
        "conclusion": conclusion,
        "status": status,
        "created_at": created_at,
        "updated_at": updated_at,
        "html_url": html_url,
        "head_branch": head_branch,
        "head_sha": head_sha,
    }


# ============================================================================
# Test get_workflow_runs_status
# ============================================================================


class TestGetWorkflowRunsStatus:
    """Test workflow runs status fetching."""

    def test_successful_runs_fetch(self, github_client, mock_stats):
        """Test successfully fetching workflow runs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "workflow_runs": [
                create_mock_workflow_run(run_id=100, conclusion="success", status="completed"),
                create_mock_workflow_run(run_id=99, conclusion="failure", status="completed"),
            ]
        }

        github_client.client.get = Mock(return_value=mock_response)

        result = github_client.get_workflow_runs_status("test-owner", "test-repo", workflow_id=42)

        assert result["status"] == "success"
        assert result["conclusion"] == "success"
        assert result["run_status"] == "completed"
        assert result["last_run"]["id"] == 100
        assert result["last_run"]["number"] == 456
        mock_stats.record_success.assert_called_once_with("github")

    def test_no_workflow_runs(self, github_client, mock_stats):
        """Test handling when workflow has no runs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"workflow_runs": []}

        github_client.client.get = Mock(return_value=mock_response)

        result = github_client.get_workflow_runs_status("test-owner", "test-repo", workflow_id=42)

        assert result["status"] == "no_runs"
        assert result["last_run"] is None
        mock_stats.record_success.assert_called_once()

    def test_workflow_runs_401_unauthorized(self, github_client, mock_stats):
        """Test 401 unauthorized error."""
        mock_response = Mock()
        mock_response.status_code = 401

        github_client.client.get = Mock(return_value=mock_response)

        result = github_client.get_workflow_runs_status("test-owner", "test-repo", workflow_id=42)

        assert result["status"] == "auth_error"
        assert result["last_run"] is None
        mock_stats.record_error.assert_called_once_with("github", 401)

    def test_workflow_runs_403_forbidden(self, github_client, mock_stats):
        """Test 403 forbidden error."""
        mock_response = Mock()
        mock_response.status_code = 403

        github_client.client.get = Mock(return_value=mock_response)

        result = github_client.get_workflow_runs_status("test-owner", "test-repo", workflow_id=42)

        assert result["status"] == "permission_error"
        assert result["last_run"] is None
        mock_stats.record_error.assert_called_once_with("github", 403)

    def test_workflow_runs_other_error(self, github_client, mock_stats):
        """Test other HTTP error codes."""
        mock_response = Mock()
        mock_response.status_code = 500

        github_client.client.get = Mock(return_value=mock_response)

        result = github_client.get_workflow_runs_status("test-owner", "test-repo", workflow_id=42)

        assert result["status"] == "api_error"
        assert result["last_run"] is None
        mock_stats.record_error.assert_called_once_with("github", 500)

    def test_workflow_runs_exception(self, github_client, mock_stats):
        """Test exception handling during runs fetch."""
        github_client.client.get = Mock(side_effect=Exception("Network error"))

        result = github_client.get_workflow_runs_status("test-owner", "test-repo", workflow_id=42)

        assert result["status"] == "error"
        assert result["last_run"] is None
        mock_stats.record_exception.assert_called_once_with("github", "exception")

    def test_workflow_runs_custom_limit(self, github_client):
        """Test custom limit parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"workflow_runs": []}

        github_client.client.get = Mock(return_value=mock_response)

        github_client.get_workflow_runs_status("test-owner", "test-repo", workflow_id=42, limit=25)

        # Verify params were passed correctly
        call_args = github_client.client.get.call_args
        assert call_args[1]["params"]["per_page"] == 25

    def test_workflow_runs_sha_truncation(self, github_client):
        """Test that SHA is truncated to 7 characters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "workflow_runs": [
                create_mock_workflow_run(head_sha="abc123def456789012345678901234567890")
            ]
        }

        github_client.client.get = Mock(return_value=mock_response)

        result = github_client.get_workflow_runs_status("test-owner", "test-repo", workflow_id=42)

        assert result["last_run"]["head_sha"] == "abc123d"

    def test_workflow_runs_no_sha(self, github_client):
        """Test handling when SHA is missing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "workflow_runs": [
                {
                    "id": 123,
                    "run_number": 456,
                    "conclusion": "success",
                    "status": "completed",
                    "created_at": "2025-01-27T10:00:00Z",
                    "updated_at": "2025-01-27T10:30:00Z",
                    "html_url": "https://github.com/test/repo/actions/runs/123",
                    "head_branch": "main",
                    # No head_sha field
                }
            ]
        }

        github_client.client.get = Mock(return_value=mock_response)

        result = github_client.get_workflow_runs_status("test-owner", "test-repo", workflow_id=42)

        assert result["last_run"]["head_sha"] is None


# ============================================================================
# Test Status Computation
# ============================================================================


class TestWorkflowStatusComputation:
    """Test workflow status computation logic."""

    def test_compute_status_success(self, github_client):
        """Test computing success status."""
        status = github_client._compute_workflow_status("success", "completed")
        assert status == "success"

    def test_compute_status_failure(self, github_client):
        """Test computing failure status."""
        status = github_client._compute_workflow_status("failure", "completed")
        assert status == "failure"

    def test_compute_status_cancelled(self, github_client):
        """Test computing cancelled status."""
        status = github_client._compute_workflow_status("cancelled", "completed")
        assert status == "cancelled"

    def test_compute_status_skipped(self, github_client):
        """Test computing skipped status."""
        status = github_client._compute_workflow_status("skipped", "completed")
        assert status == "skipped"

    def test_compute_status_timed_out(self, github_client):
        """Test computing timed out status."""
        status = github_client._compute_workflow_status("timed_out", "completed")
        assert status == "failure"

    def test_compute_status_action_required(self, github_client):
        """Test computing action_required status."""
        status = github_client._compute_workflow_status("action_required", "completed")
        assert status == "failure"

    def test_compute_status_neutral(self, github_client):
        """Test computing neutral status."""
        status = github_client._compute_workflow_status("neutral", "completed")
        assert status == "success"

    def test_compute_status_stale(self, github_client):
        """Test computing stale status."""
        status = github_client._compute_workflow_status("stale", "completed")
        assert status == "unknown"

    def test_compute_status_in_progress(self, github_client):
        """Test computing in_progress status."""
        status = github_client._compute_workflow_status("unknown", "in_progress")
        assert status == "building"

    def test_compute_status_queued(self, github_client):
        """Test computing queued status."""
        status = github_client._compute_workflow_status("unknown", "queued")
        assert status == "building"

    def test_compute_status_waiting(self, github_client):
        """Test computing waiting status."""
        status = github_client._compute_workflow_status("unknown", "waiting")
        assert status == "unknown"

    def test_compute_status_requested(self, github_client):
        """Test computing requested status."""
        status = github_client._compute_workflow_status("unknown", "requested")
        assert status == "unknown"

    def test_compute_status_pending(self, github_client):
        """Test computing pending status."""
        status = github_client._compute_workflow_status("unknown", "pending")
        assert status == "unknown"

    def test_compute_status_unknown_defaults_to_unknown(self, github_client):
        """Test that unknown conclusion/status defaults to unknown."""
        status = github_client._compute_workflow_status("unknown", "unknown")
        assert status == "unknown"

    def test_compute_status_empty_strings(self, github_client):
        """Test handling empty strings."""
        status = github_client._compute_workflow_status("", "")
        assert status == "unknown"


# ============================================================================
# Test Color Computation from Runtime Status
# ============================================================================


class TestColorComputationFromRuntimeStatus:
    """Test color computation from runtime status."""

    def test_color_success(self, github_client):
        """Test blue color for success."""
        color = github_client._compute_workflow_color_from_runtime_status("success")
        assert color == "blue"

    def test_color_failure(self, github_client):
        """Test red color for failure."""
        color = github_client._compute_workflow_color_from_runtime_status("failure")
        assert color == "red"

    def test_color_in_progress(self, github_client):
        """Test blue_anime color for in_progress."""
        color = github_client._compute_workflow_color_from_runtime_status("in_progress")
        assert color == "blue_anime"

    def test_color_aborted(self, github_client):
        """Test grey color for aborted."""
        color = github_client._compute_workflow_color_from_runtime_status("aborted")
        assert color == "grey"

    def test_color_not_built(self, github_client):
        """Test grey color for not_built."""
        color = github_client._compute_workflow_color_from_runtime_status("not_built")
        assert color == "grey"

    def test_color_unknown(self, github_client):
        """Test grey color for unknown."""
        color = github_client._compute_workflow_color_from_runtime_status("unknown")
        assert color == "grey"

    def test_color_case_insensitive(self, github_client):
        """Test that color computation is case-insensitive."""
        color = github_client._compute_workflow_color_from_runtime_status("SUCCESS")
        assert color == "blue"

        color = github_client._compute_workflow_color_from_runtime_status("Failure")
        assert color == "red"


# ============================================================================
# Test Color Computation from State
# ============================================================================


class TestColorComputationFromState:
    """Test color computation from workflow state."""

    def test_color_active_state(self, github_client):
        """Test blue color for active state."""
        color = github_client._compute_workflow_color_from_state("active")
        assert color == "blue"

    def test_color_disabled_state(self, github_client):
        """Test grey color for disabled state."""
        color = github_client._compute_workflow_color_from_state("disabled")
        assert color == "grey"

    def test_color_disabled_fork(self, github_client):
        """Test grey color for disabled_fork state."""
        color = github_client._compute_workflow_color_from_state("disabled_fork")
        assert color == "grey"

    def test_color_disabled_manually(self, github_client):
        """Test grey color for disabled_manually state."""
        color = github_client._compute_workflow_color_from_state("disabled_manually")
        assert color == "grey"

    def test_color_disabled_inactivity(self, github_client):
        """Test grey color for disabled_inactivity state."""
        color = github_client._compute_workflow_color_from_state("disabled_inactivity")
        assert color == "grey"

    def test_color_unknown_state(self, github_client):
        """Test grey color for unknown state."""
        color = github_client._compute_workflow_color_from_state("unknown")
        assert color == "grey"


# ============================================================================
# Test get_repository_workflow_status_summary
# ============================================================================


class TestWorkflowStatusSummary:
    """Test workflow status summary generation."""

    def test_successful_summary_generation(self, github_client, mock_stats):
        """Test successfully generating workflow status summary."""
        # Mock get_repository_workflows
        workflows = [
            {
                "id": 1,
                "name": "CI",
                "path": ".github/workflows/ci.yml",
                "state": "active",
                "status": "unknown",
                "color": "green",
                "urls": {
                    "workflow_page": "https://github.com/owner/repo/actions/workflows/ci.yml",
                    "source": "https://github.com/owner/repo/blob/master/.github/workflows/ci.yml",
                    "badge": "https://github.com/owner/repo/workflows/CI/badge.svg",
                },
            },
            {
                "id": 2,
                "name": "Tests",
                "path": ".github/workflows/tests.yml",
                "state": "active",
                "status": "unknown",
                "color": "green",
                "urls": {
                    "workflow_page": "https://github.com/owner/repo/actions/workflows/tests.yml",
                    "source": "https://github.com/owner/repo/blob/master/.github/workflows/tests.yml",
                    "badge": "https://github.com/owner/repo/workflows/Tests/badge.svg",
                },
            },
        ]

        github_client.get_repository_workflows = Mock(return_value=workflows)

        # Mock get_workflow_runs_status
        def mock_runs_status(owner, repo, workflow_id):
            if workflow_id == 1:
                return {
                    "status": "success",
                    "conclusion": "success",
                    "run_status": "completed",
                    "last_run": {"id": 100, "number": 10},
                }
            else:
                return {
                    "status": "failure",
                    "conclusion": "failure",
                    "run_status": "completed",
                    "last_run": {"id": 200, "number": 20},
                }

        github_client.get_workflow_runs_status = Mock(side_effect=mock_runs_status)

        result = github_client.get_repository_workflow_status_summary("test-owner", "test-repo")

        assert result["has_workflows"] is True
        assert result["total_workflows"] == 2
        assert result["active_workflows"] == 2
        assert len(result["workflows"]) == 2
        assert result["workflows"][0]["name"] == "CI"
        assert result["workflows"][0]["status"] == "success"
        assert result["workflows"][0]["color"] == "blue"
        assert result["workflows"][1]["name"] == "Tests"
        assert result["workflows"][1]["status"] == "failure"
        assert result["workflows"][1]["color"] == "red"
        assert result["overall_status"] == "has_failures"

    def test_summary_with_no_workflows(self, github_client):
        """Test summary generation when there are no workflows."""
        github_client.get_repository_workflows = Mock(return_value=[])

        result = github_client.get_repository_workflow_status_summary("test-owner", "test-repo")

        assert isinstance(result, dict)
        assert result["has_workflows"] is False
        assert result["workflows"] == []
        assert result["overall_status"] == "no_workflows"

    def test_summary_preserves_workflow_metadata(self, github_client):
        """Test that summary preserves all workflow metadata."""
        workflows = [
            {
                "id": 1,
                "name": "CI",
                "path": ".github/workflows/ci.yml",
                "state": "active",
                "status": "unknown",
                "color": "green",
                "urls": {
                    "workflow_page": "https://github.com/owner/repo/actions/workflows/ci.yml",
                    "source": "https://github.com/owner/repo/blob/master/.github/workflows/ci.yml",
                    "badge": "https://github.com/owner/repo/workflows/CI/badge.svg",
                },
            },
        ]

        github_client.get_repository_workflows = Mock(return_value=workflows)
        github_client.get_workflow_runs_status = Mock(
            return_value={
                "status": "success",
                "conclusion": "success",
                "run_status": "completed",
                "last_run": {"id": 100},
            }
        )

        result = github_client.get_repository_workflow_status_summary("test-owner", "test-repo")

        assert result["has_workflows"] is True
        assert result["total_workflows"] == 1
        assert result["active_workflows"] == 1
        assert len(result["workflows"]) == 1
        assert result["workflows"][0]["id"] == 1
        assert result["workflows"][0]["name"] == "CI"
        assert result["workflows"][0]["path"] == ".github/workflows/ci.yml"
        assert result["workflows"][0]["state"] == "active"
        assert result["workflows"][0]["status"] == "success"
        assert (
            result["workflows"][0]["urls"]["workflow_page"]
            == "https://github.com/owner/repo/actions/workflows/ci.yml"
        )


# ============================================================================
# Test Edge Cases and Error Scenarios
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_workflow_with_missing_fields(self, github_client):
        """Test handling workflows with missing fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "workflows": [
                {
                    "id": 1,
                    # Missing name, path, state
                }
            ]
        }

        github_client.client.get = Mock(return_value=mock_response)

        workflows = github_client.get_repository_workflows("owner", "repo")

        assert len(workflows) == 1
        assert workflows[0]["id"] == 1
        assert workflows[0]["name"] is None
        assert workflows[0]["path"] == ""
        assert workflows[0]["state"] == "unknown"

    def test_workflow_run_with_missing_fields(self, github_client):
        """Test handling workflow run with missing fields."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "workflow_runs": [
                {
                    "id": 123,
                    # Missing other fields
                }
            ]
        }

        github_client.client.get = Mock(return_value=mock_response)

        result = github_client.get_workflow_runs_status("owner", "repo", 1)

        assert result["last_run"]["id"] == 123
        assert result["last_run"]["number"] is None
        assert result["last_run"]["head_sha"] is None

    def test_empty_workflow_path(self, github_client):
        """Test handling empty workflow path."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "workflows": [
                {
                    "id": 1,
                    "name": "Test",
                    "path": "",
                    "state": "active",
                }
            ]
        }

        github_client.client.get = Mock(return_value=mock_response)

        workflows = github_client.get_repository_workflows("owner", "repo")

        assert workflows[0]["urls"]["source"] is None

    def test_workflow_with_null_badge_url(self, github_client):
        """Test handling workflow with null badge URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "workflows": [
                {
                    "id": 1,
                    "name": "Test",
                    "path": ".github/workflows/test.yml",
                    "state": "active",
                    "badge_url": None,
                }
            ]
        }

        github_client.client.get = Mock(return_value=mock_response)

        workflows = github_client.get_repository_workflows("owner", "repo")

        assert workflows[0]["urls"]["badge"] is None


# ============================================================================
# Test Client Lifecycle
# ============================================================================


class TestClientLifecycle:
    """Test client lifecycle management."""

    def test_client_initialization_creates_httpx_client(self):
        """Test that initialization creates httpx client."""
        client = GitHubAPIClient(token="test_token")
        assert client.client is not None
        assert isinstance(client.client, httpx.Client)
        assert client.base_url == "https://api.github.com"
        client.close()

    def test_client_headers_include_token(self):
        """Test that headers include authorization token."""
        client = GitHubAPIClient(token="test_secret_token")
        assert "Authorization" in client.client.headers
        assert client.client.headers["Authorization"] == "Bearer test_secret_token"
        client.close()

    def test_client_headers_include_user_agent(self):
        """Test that headers include user agent."""
        client = GitHubAPIClient(token="test_token")
        assert "User-Agent" in client.client.headers
        assert "repository-reports" in client.client.headers["User-Agent"]
        client.close()

    def test_client_headers_include_api_version(self):
        """Test that headers include GitHub API version."""
        client = GitHubAPIClient(token="test_token")
        assert "X-GitHub-Api-Version" in client.client.headers
        assert client.client.headers["X-GitHub-Api-Version"] == "2022-11-28"
        client.close()

    def test_client_close_cleanup(self):
        """Test that close() cleans up resources."""
        client = GitHubAPIClient(token="test_token")
        client.close()
        # After close, client should still exist but be closed
        assert hasattr(client, "client")

    def test_client_custom_timeout(self):
        """Test client with custom timeout."""
        client = GitHubAPIClient(token="test_token", timeout=60.0)
        assert client.timeout == 60.0
        client.close()


# ============================================================================
# Test Write to Step Summary
# ============================================================================


class TestWriteToStepSummary:
    """Test GitHub step summary writing."""

    def test_write_with_env_var_set(self, github_client, tmp_path):
        """Test writing to step summary when env var is set."""
        summary_file = tmp_path / "summary.md"
        with patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": str(summary_file)}):
            github_client._write_to_step_summary("Test message")
            assert summary_file.exists()
            assert summary_file.read_text() == "Test message\n"

    def test_write_without_env_var(self, github_client):
        """Test that writing without env var doesn't error."""
        with patch.dict("os.environ", {}, clear=True):
            # Should not raise
            github_client._write_to_step_summary("Test message")

    def test_write_handles_file_error(self, github_client):
        """Test that file errors are handled gracefully."""
        with patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": "/invalid/path/file.md"}):
            # Should not raise
            github_client._write_to_step_summary("Test message")

    def test_write_appends_to_existing_file(self, github_client, tmp_path):
        """Test that messages are appended to existing summary file."""
        summary_file = tmp_path / "summary.md"
        summary_file.write_text("Existing content\n")

        with patch.dict("os.environ", {"GITHUB_STEP_SUMMARY": str(summary_file)}):
            github_client._write_to_step_summary("New message")
            content = summary_file.read_text()
            assert "Existing content\n" in content
            assert "New message\n" in content
