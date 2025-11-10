# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for Jenkins API client.

Tests cover:
- API discovery and path detection
- get_all_jobs with caching
- get_jobs_for_project with scoring algorithm
- get_job_details with status computation
- get_last_build_info
- Job matching score calculation
- Error handling and statistics tracking
- Edge cases and integration scenarios
"""

from unittest.mock import Mock, patch

import pytest

from api.jenkins_client import JenkinsAPIClient


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
def jenkins_client(mock_stats):
    """Create a JenkinsAPIClient instance for testing."""
    client = JenkinsAPIClient(host="jenkins.example.com", timeout=30.0, stats=mock_stats)
    # Mock the discovery to avoid network calls
    client.api_base_path = "/api/json"
    client._cache_populated = False
    client._jobs_cache = {}
    yield client
    client.close()


def create_mock_job(name, color="blue", disabled=False, buildable=True, url=None):
    """Helper to create mock job data."""
    return {
        "name": name,
        "url": url or f"https://jenkins.example.com/job/{name}/",
        "color": color,
        "disabled": disabled,
        "buildable": buildable,
    }


def create_mock_job_details(name, color="blue", disabled=False, buildable=True, description=""):
    """Helper to create mock job details."""
    return {
        "name": name,
        "url": f"https://jenkins.example.com/job/{name}/",
        "color": color,
        "disabled": disabled,
        "buildable": buildable,
        "description": description,
    }


# ============================================================================
# Test API Discovery
# ============================================================================


class TestAPIDiscovery:
    """Test Jenkins API discovery mechanism."""

    def test_discovery_finds_standard_path(self, mock_stats):
        """Test discovery finds standard /api/json path."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jobs": [{"name": "test-job"}]}

        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = JenkinsAPIClient(host="jenkins.example.com", stats=mock_stats)

            assert client.api_base_path == "/api/json"
            client.close()

    def test_discovery_tries_multiple_paths(self, mock_stats):
        """Test discovery tries multiple path patterns."""
        call_count = [0]

        def mock_get(url):
            call_count[0] += 1
            response = Mock()
            # First two calls fail, third succeeds
            if call_count[0] < 3:
                response.status_code = 404
            else:
                response.status_code = 200
                response.json.return_value = {"jobs": []}
            return response

        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.get = mock_get
            mock_client_class.return_value = mock_client

            client = JenkinsAPIClient(host="jenkins.example.com", stats=mock_stats)

            # Should have tried at least 3 paths
            assert call_count[0] >= 3
            client.close()

    def test_discovery_falls_back_to_default(self, mock_stats):
        """Test discovery falls back to default path if all fail."""
        mock_response = Mock()
        mock_response.status_code = 404

        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = JenkinsAPIClient(host="jenkins.example.com", stats=mock_stats)

            # Should fall back to default
            assert client.api_base_path == "/api/json"
            client.close()

    def test_discovery_validates_json_structure(self, mock_stats):
        """Test that discovery validates JSON structure has jobs array."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"no_jobs_key": []}

        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = JenkinsAPIClient(host="jenkins.example.com", stats=mock_stats)

            # Invalid JSON should cause fallback
            assert client.api_base_path == "/api/json"
            client.close()


# ============================================================================
# Test get_all_jobs
# ============================================================================


class TestGetAllJobs:
    """Test get_all_jobs method."""

    def test_get_all_jobs_success(self, jenkins_client, mock_stats):
        """Test successfully fetching all jobs."""
        jobs_data = {
            "jobs": [create_mock_job("job1"), create_mock_job("job2"), create_mock_job("job3")]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = jobs_data

        jenkins_client.client.get = Mock(return_value=mock_response)

        result = jenkins_client.get_all_jobs()

        assert result == jobs_data
        assert len(result["jobs"]) == 3
        mock_stats.record_success.assert_called_with("jenkins")

    def test_get_all_jobs_caching(self, jenkins_client):
        """Test that jobs are cached after first fetch."""
        jobs_data = {"jobs": [create_mock_job("job1")]}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = jobs_data

        jenkins_client.client.get = Mock(return_value=mock_response)

        # First call
        result1 = jenkins_client.get_all_jobs()
        assert jenkins_client.client.get.call_count == 1

        # Second call should use cache
        result2 = jenkins_client.get_all_jobs()
        assert jenkins_client.client.get.call_count == 1  # Not called again
        assert result1 == result2

    def test_get_all_jobs_error(self, jenkins_client, mock_stats):
        """Test handling HTTP error when fetching jobs."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        jenkins_client.client.get = Mock(return_value=mock_response)

        result = jenkins_client.get_all_jobs()

        assert result == {}
        mock_stats.record_error.assert_called_with("jenkins", 500)

    def test_get_all_jobs_exception(self, jenkins_client, mock_stats):
        """Test handling exception when fetching jobs."""
        jenkins_client.client.get = Mock(side_effect=Exception("Network error"))

        result = jenkins_client.get_all_jobs()

        assert result == {}
        mock_stats.record_exception.assert_called_with("jenkins")

    def test_get_all_jobs_no_api_path(self, jenkins_client):
        """Test handling missing API path."""
        jenkins_client.api_base_path = None

        result = jenkins_client.get_all_jobs()

        assert result == {}


# ============================================================================
# Test get_jobs_for_project
# ============================================================================


class TestGetJobsForProject:
    """Test get_jobs_for_project method."""

    def test_get_jobs_exact_match(self, jenkins_client):
        """Test finding jobs with exact name match."""
        jobs_data = {"jobs": [create_mock_job("test-project"), create_mock_job("other-job")]}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = jobs_data

        # Mock get_all_jobs
        jenkins_client.get_all_jobs = Mock(return_value=jobs_data)

        # Mock get_job_details
        def mock_job_details(name):
            return {"name": name, "status": "success", "color": "blue"}

        jenkins_client.get_job_details = Mock(side_effect=mock_job_details)

        allocated = set()
        result = jenkins_client.get_jobs_for_project("test/project", allocated)

        assert len(result) == 1
        assert result[0]["name"] == "test-project"
        assert "test-project" in allocated

    def test_get_jobs_prefix_match(self, jenkins_client):
        """Test finding jobs with prefix match."""
        jobs_data = {
            "jobs": [
                create_mock_job("sdc-verify"),
                create_mock_job("sdc-merge"),
                create_mock_job("other-job"),
            ]
        }

        jenkins_client.get_all_jobs = Mock(return_value=jobs_data)

        def mock_job_details(name):
            return {"name": name, "status": "success"}

        jenkins_client.get_job_details = Mock(side_effect=mock_job_details)

        allocated = set()
        result = jenkins_client.get_jobs_for_project("sdc", allocated)

        assert len(result) == 2
        job_names = [j["name"] for j in result]
        assert "sdc-verify" in job_names
        assert "sdc-merge" in job_names

    def test_get_jobs_prevents_duplicates(self, jenkins_client):
        """Test that already allocated jobs are not returned."""
        jobs_data = {"jobs": [create_mock_job("sdc-verify"), create_mock_job("sdc-merge")]}

        jenkins_client.get_all_jobs = Mock(return_value=jobs_data)

        def mock_job_details(name):
            return {"name": name, "status": "success"}

        jenkins_client.get_job_details = Mock(side_effect=mock_job_details)

        # Pre-allocate one job
        allocated = {"sdc-verify"}
        result = jenkins_client.get_jobs_for_project("sdc", allocated)

        assert len(result) == 1
        assert result[0]["name"] == "sdc-merge"

    def test_get_jobs_no_matches(self, jenkins_client):
        """Test handling when no jobs match."""
        jobs_data = {"jobs": [create_mock_job("other-job1"), create_mock_job("other-job2")]}

        jenkins_client.get_all_jobs = Mock(return_value=jobs_data)

        allocated = set()
        result = jenkins_client.get_jobs_for_project("nonexistent", allocated)

        assert len(result) == 0

    def test_get_jobs_no_jobs_key(self, jenkins_client):
        """Test handling when API response has no jobs key."""
        jenkins_client.get_all_jobs = Mock(return_value={})

        allocated = set()
        result = jenkins_client.get_jobs_for_project("test/project", allocated)

        assert len(result) == 0


# ============================================================================
# Test Job Matching Score Calculation
# ============================================================================


class TestJobMatchingScore:
    """Test _calculate_job_match_score method."""

    def test_exact_match_highest_score(self, jenkins_client):
        """Test exact match gets highest score."""
        score = jenkins_client._calculate_job_match_score(
            "test-project", "test/project", "test-project"
        )
        assert score >= 1000

    def test_prefix_match_high_score(self, jenkins_client):
        """Test prefix match gets high score."""
        score = jenkins_client._calculate_job_match_score(
            "test-project-verify", "test/project", "test-project"
        )
        assert score >= 500

    def test_no_match_zero_score(self, jenkins_client):
        """Test non-matching job gets zero score."""
        score = jenkins_client._calculate_job_match_score(
            "other-job", "test/project", "test-project"
        )
        assert score == 0

    def test_partial_match_with_separator(self, jenkins_client):
        """Test partial match with separator does match."""
        # sdc-tosca-verify does match sdc (starts with sdc-)
        score = jenkins_client._calculate_job_match_score("sdc-tosca-verify", "sdc", "sdc")
        assert score > 0  # Should match because it starts with "sdc-"

    def test_nested_project_bonus(self, jenkins_client):
        """Test nested projects get bonus for path depth."""
        score1 = jenkins_client._calculate_job_match_score("foo-verify", "foo", "foo")
        score2 = jenkins_client._calculate_job_match_score("foo-bar-verify", "foo/bar", "foo-bar")
        # Deeper path should have higher score component
        assert score2 > score1

    def test_case_insensitive_matching(self, jenkins_client):
        """Test matching is case-insensitive."""
        score1 = jenkins_client._calculate_job_match_score(
            "Test-Project", "test/project", "test-project"
        )
        score2 = jenkins_client._calculate_job_match_score(
            "test-project", "test/project", "test-project"
        )
        assert score1 == score2


# ============================================================================
# Test get_job_details
# ============================================================================


class TestGetJobDetails:
    """Test get_job_details method."""

    def test_get_job_details_success(self, jenkins_client):
        """Test successfully fetching job details."""
        job_data = create_mock_job_details("test-job", color="blue")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = job_data

        jenkins_client.client.get = Mock(return_value=mock_response)
        jenkins_client.get_last_build_info = Mock(return_value={})

        result = jenkins_client.get_job_details("test-job")

        assert result["name"] == "test-job"
        assert result["status"] == "success"
        assert result["state"] == "active"

    def test_get_job_details_disabled_job(self, jenkins_client):
        """Test job details for disabled job."""
        job_data = create_mock_job_details("test-job", disabled=True)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = job_data

        jenkins_client.client.get = Mock(return_value=mock_response)
        jenkins_client.get_last_build_info = Mock(return_value={})

        result = jenkins_client.get_job_details("test-job")

        assert result["state"] == "disabled"
        assert result["color"] == "grey"

    def test_get_job_details_not_buildable(self, jenkins_client):
        """Test job details for not buildable job."""
        job_data = create_mock_job_details("test-job", buildable=False)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = job_data

        jenkins_client.client.get = Mock(return_value=mock_response)
        jenkins_client.get_last_build_info = Mock(return_value={})

        result = jenkins_client.get_job_details("test-job")

        assert result["state"] == "disabled"

    def test_get_job_details_error(self, jenkins_client):
        """Test handling error when fetching job details."""
        mock_response = Mock()
        mock_response.status_code = 404

        jenkins_client.client.get = Mock(return_value=mock_response)

        result = jenkins_client.get_job_details("nonexistent")

        assert result == {}

    def test_get_job_details_exception(self, jenkins_client):
        """Test handling exception when fetching job details."""
        jenkins_client.client.get = Mock(side_effect=Exception("Network error"))

        result = jenkins_client.get_job_details("test-job")

        assert result == {}


# ============================================================================
# Test Status Computation
# ============================================================================


class TestStatusComputation:
    """Test status and state computation."""

    def test_compute_status_from_blue(self, jenkins_client):
        """Test computing status from blue color."""
        status = jenkins_client._compute_job_status_from_color("blue")
        assert status == "success"

    def test_compute_status_from_red(self, jenkins_client):
        """Test computing status from red color."""
        status = jenkins_client._compute_job_status_from_color("red")
        assert status == "failure"

    def test_compute_status_from_yellow(self, jenkins_client):
        """Test computing status from yellow color."""
        status = jenkins_client._compute_job_status_from_color("yellow")
        assert status == "unstable"

    def test_compute_status_from_grey(self, jenkins_client):
        """Test computing status from grey color."""
        status = jenkins_client._compute_job_status_from_color("grey")
        assert status == "disabled"

    def test_compute_status_from_building(self, jenkins_client):
        """Test computing status from animated color."""
        status = jenkins_client._compute_job_status_from_color("blue_anime")
        assert status == "building"

    def test_compute_status_from_aborted(self, jenkins_client):
        """Test computing status from aborted color."""
        status = jenkins_client._compute_job_status_from_color("aborted")
        assert status == "aborted"

    def test_compute_status_unknown(self, jenkins_client):
        """Test computing status from unknown color."""
        status = jenkins_client._compute_job_status_from_color("unknown_color")
        assert status == "unknown"

    def test_compute_state_disabled(self, jenkins_client):
        """Test computing state for disabled job."""
        state = jenkins_client._compute_jenkins_job_state(disabled=True, buildable=True)
        assert state == "disabled"

    def test_compute_state_active(self, jenkins_client):
        """Test computing state for active job."""
        state = jenkins_client._compute_jenkins_job_state(disabled=False, buildable=True)
        assert state == "active"

    def test_compute_state_not_buildable(self, jenkins_client):
        """Test computing state for not buildable job."""
        state = jenkins_client._compute_jenkins_job_state(disabled=False, buildable=False)
        assert state == "disabled"


# ============================================================================
# Test get_last_build_info
# ============================================================================


class TestGetLastBuildInfo:
    """Test get_last_build_info method."""

    def test_get_last_build_info_success(self, jenkins_client):
        """Test successfully fetching last build info."""
        build_data = {
            "result": "SUCCESS",
            "duration": 120000,
            "timestamp": 1706356800000,
            "building": False,
            "number": 42,
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = build_data

        jenkins_client.client.get = Mock(return_value=mock_response)

        result = jenkins_client.get_last_build_info("test-job")

        assert result["result"] == "SUCCESS"
        assert result["number"] == 42
        assert "build_time" in result
        assert "duration_seconds" in result
        assert result["duration_seconds"] == 120.0

    def test_get_last_build_info_no_build(self, jenkins_client):
        """Test handling when no build exists."""
        mock_response = Mock()
        mock_response.status_code = 404

        jenkins_client.client.get = Mock(return_value=mock_response)

        result = jenkins_client.get_last_build_info("test-job")

        assert result == {}

    def test_get_last_build_info_exception(self, jenkins_client):
        """Test handling exception when fetching build info."""
        jenkins_client.client.get = Mock(side_effect=Exception("Network error"))

        result = jenkins_client.get_last_build_info("test-job")

        assert result == {}

    def test_get_last_build_info_timestamp_conversion(self, jenkins_client):
        """Test timestamp conversion to ISO format."""
        build_data = {"timestamp": 1706356800000, "duration": 60000}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = build_data

        jenkins_client.client.get = Mock(return_value=mock_response)

        result = jenkins_client.get_last_build_info("test-job")

        assert "build_time" in result
        assert isinstance(result["build_time"], str)


# ============================================================================
# Test Context Manager
# ============================================================================


class TestContextManager:
    """Test context manager protocol."""

    def test_context_manager_enter_exit(self, mock_stats):
        """Test using client as context manager."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"jobs": []}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            with JenkinsAPIClient(host="jenkins.example.com", stats=mock_stats) as client:
                assert client is not None

    def test_context_manager_closes_client(self, mock_stats):
        """Test that context manager closes client."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"jobs": []}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = JenkinsAPIClient(host="jenkins.example.com", stats=mock_stats)
            with client:
                pass

            mock_client.close.assert_called()


# ============================================================================
# Test Statistics Integration
# ============================================================================


class TestStatisticsIntegration:
    """Test statistics tracking integration."""

    def test_stats_recorded_on_success(self, jenkins_client, mock_stats):
        """Test that success is recorded in stats."""
        jobs_data = {"jobs": []}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = jobs_data

        jenkins_client.client.get = Mock(return_value=mock_response)
        jenkins_client.get_all_jobs()

        mock_stats.record_success.assert_called_with("jenkins")

    def test_stats_recorded_on_error(self, jenkins_client, mock_stats):
        """Test that errors are recorded in stats."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Error"

        jenkins_client.client.get = Mock(return_value=mock_response)
        jenkins_client.get_all_jobs()

        mock_stats.record_error.assert_called_with("jenkins", 500)

    def test_stats_recorded_on_exception(self, jenkins_client, mock_stats):
        """Test that exceptions are recorded in stats."""
        jenkins_client.client.get = Mock(side_effect=Exception("Network error"))
        jenkins_client.get_all_jobs()

        mock_stats.record_exception.assert_called_with("jenkins")


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_empty_job_name(self, jenkins_client):
        """Test handling empty job name."""
        jenkins_client.client.get = Mock(side_effect=Exception("Invalid URL"))

        result = jenkins_client.get_job_details("")

        assert result == {}

    def test_special_characters_in_job_name(self, jenkins_client):
        """Test job name with special characters."""
        job_data = create_mock_job_details("test-job_123")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = job_data

        jenkins_client.client.get = Mock(return_value=mock_response)
        jenkins_client.get_last_build_info = Mock(return_value={})

        result = jenkins_client.get_job_details("test-job_123")

        assert result["name"] == "test-job_123"

    def test_very_large_job_list(self, jenkins_client):
        """Test handling very large job list."""
        large_jobs = {"jobs": [create_mock_job(f"job-{i}") for i in range(1000)]}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = large_jobs

        jenkins_client.client.get = Mock(return_value=mock_response)

        result = jenkins_client.get_all_jobs()

        assert len(result["jobs"]) == 1000

    def test_unicode_in_job_description(self, jenkins_client):
        """Test Unicode characters in job description."""
        job_data = create_mock_job_details("test", description="テスト")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = job_data

        jenkins_client.client.get = Mock(return_value=mock_response)
        jenkins_client.get_last_build_info = Mock(return_value={})

        result = jenkins_client.get_job_details("test")

        assert result["description"] == "テスト"


# ============================================================================
# Test Integration Scenarios
# ============================================================================


class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    def test_complete_project_job_flow(self, jenkins_client):
        """Test complete flow from fetching jobs to getting details."""
        jobs_data = {
            "jobs": [create_mock_job("test-project-verify"), create_mock_job("test-project-merge")]
        }

        job_details = create_mock_job_details("test-project-verify")

        mock_all_jobs = Mock()
        mock_all_jobs.status_code = 200
        mock_all_jobs.json.return_value = jobs_data

        mock_details = Mock()
        mock_details.status_code = 200
        mock_details.json.return_value = job_details

        def mock_get(url):
            if "/api/json?tree=jobs" in url:
                return mock_all_jobs
            else:
                return mock_details

        jenkins_client.client.get = Mock(side_effect=mock_get)
        jenkins_client.get_last_build_info = Mock(return_value={})

        allocated = set()
        result = jenkins_client.get_jobs_for_project("test/project", allocated)

        assert len(result) >= 1
        assert "test-project-verify" in allocated
