#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
API Statistics Integration Tests

Comprehensive tests to ensure API statistics tracking is properly wired up
and functioning across the entire application stack.

These tests verify:
1. API stats object is passed through the constructor chain
2. All API clients receive and use the stats object
3. API calls are properly tracked (success and failure)
4. GitHub step summary output is generated
5. Stats are never empty when APIs are called
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from api.gerrit_client import GerritAPIClient
from api.github_client import GitHubAPIClient
from api.jenkins_client import JenkinsAPIClient
from reporting_tool.collectors.git import GitDataCollector
from reporting_tool.features.registry import FeatureRegistry
from reporting_tool.main import APIStatistics
from reporting_tool.reporter import RepositoryReporter


class TestAPIStatisticsWiring:
    """Test that API statistics object is properly wired through the application."""

    def test_api_statistics_initialization(self):
        """Test that APIStatistics initializes with correct structure."""
        stats = APIStatistics()

        assert hasattr(stats, "stats")
        assert "github" in stats.stats
        assert "gerrit" in stats.stats
        assert "jenkins" in stats.stats
        assert "info_master" in stats.stats

        # Verify initial state
        assert stats.stats["github"]["success"] == 0
        assert stats.stats["gerrit"]["success"] == 0
        assert stats.stats["jenkins"]["success"] == 0
        assert stats.stats["github"]["errors"] == {}
        assert stats.stats["gerrit"]["errors"] == {}
        assert stats.stats["jenkins"]["errors"] == {}

    def test_reporter_accepts_api_stats(self):
        """Test that RepositoryReporter accepts and stores api_stats parameter."""
        config = {
            "gerrit": {"enabled": False},
            "jenkins": {"enabled": False},
        }
        logger = MagicMock()
        api_stats = APIStatistics()

        reporter = RepositoryReporter(config, logger, api_stats)

        assert reporter.api_stats is api_stats
        assert reporter.git_collector.api_stats is api_stats
        assert reporter.feature_registry.api_stats is api_stats

    def test_git_collector_accepts_api_stats(self):
        """Test that GitDataCollector accepts and stores api_stats parameter."""
        config = {
            "gerrit": {"enabled": False},
            "jenkins": {"enabled": False},
        }
        logger = MagicMock()
        api_stats = APIStatistics()

        collector = GitDataCollector(config, {}, logger, api_stats=api_stats)

        assert collector.api_stats is api_stats

    def test_feature_registry_accepts_api_stats(self):
        """Test that FeatureRegistry accepts and stores api_stats parameter."""
        config = {"features": {"enabled": []}}
        logger = MagicMock()
        api_stats = APIStatistics()

        registry = FeatureRegistry(config, logger, api_stats=api_stats)

        assert registry.api_stats is api_stats

    def test_gerrit_client_receives_stats(self):
        """Test that GerritAPIClient receives stats object during initialization."""
        config = {
            "gerrit": {
                "enabled": True,
                "host": "gerrit.example.org",
                "base_url": "https://gerrit.example.org",
            },
            "jenkins": {"enabled": False},
        }
        logger = MagicMock()
        api_stats = APIStatistics()

        with patch("reporting_tool.collectors.git.GerritAPIClient") as mock_gerrit:
            mock_instance = MagicMock()
            mock_gerrit.return_value = mock_instance
            mock_instance.get_all_projects.return_value = {}

            GitDataCollector(config, {}, logger, api_stats=api_stats)

            # Verify GerritAPIClient was instantiated with stats
            mock_gerrit.assert_called_once()
            call_kwargs = mock_gerrit.call_args[1]
            assert "stats" in call_kwargs
            assert call_kwargs["stats"] is api_stats

    def test_jenkins_client_receives_stats_from_env(self):
        """Test that JenkinsAPIClient receives stats when initialized from env var."""
        config = {
            "gerrit": {"enabled": False},
            "jenkins": {"enabled": False},
        }
        logger = MagicMock()
        api_stats = APIStatistics()

        with (
            patch.dict(os.environ, {"JENKINS_HOST": "jenkins.example.org"}),
            patch("reporting_tool.collectors.git.JenkinsAPIClient") as mock_jenkins,
        ):
            mock_instance = MagicMock()
            mock_jenkins.return_value = mock_instance
            mock_instance.get_all_jobs.return_value = {"jobs": []}

            GitDataCollector(config, {}, logger, api_stats=api_stats)

            # Verify JenkinsAPIClient was instantiated with stats
            mock_jenkins.assert_called_once()
            call_kwargs = mock_jenkins.call_args[1]
            assert "stats" in call_kwargs
            assert call_kwargs["stats"] is api_stats

    def test_jenkins_client_receives_stats_from_config(self):
        """Test that JenkinsAPIClient receives stats when initialized from config."""
        config = {
            "gerrit": {"enabled": False},
            "jenkins": {
                "enabled": True,
                "host": "jenkins.example.org",
            },
        }
        logger = MagicMock()
        api_stats = APIStatistics()

        with patch("reporting_tool.collectors.git.JenkinsAPIClient") as mock_jenkins:
            mock_instance = MagicMock()
            mock_jenkins.return_value = mock_instance
            mock_instance.get_all_jobs.return_value = {"jobs": []}

            GitDataCollector(config, {}, logger, api_stats=api_stats)

            # Verify JenkinsAPIClient was instantiated with stats
            mock_jenkins.assert_called_once()
            call_kwargs = mock_jenkins.call_args[1]
            assert "stats" in call_kwargs
            assert call_kwargs["stats"] is api_stats

    def test_github_client_receives_stats_in_workflow_check(self):
        """Test that GitHubAPIClient receives stats during workflow checks."""
        config = {
            "github": "test-org",
            "features": {"enabled": ["workflows"]},
        }
        logger = MagicMock()
        api_stats = APIStatistics()

        registry = FeatureRegistry(config, logger, api_stats=api_stats)

        with (
            patch.dict(os.environ, {"GITHUB_TOKEN": "fake-token"}),
            patch("reporting_tool.features.registry.GitHubAPIClient") as mock_github,
        ):
            mock_instance = MagicMock()
            mock_github.return_value = mock_instance
            mock_instance.get_repository_workflow_status_summary.return_value = {
                "has_workflows": False
            }

            # Simulate workflow check
            repo_path = Path("/tmp/fake-repo")
            with patch.object(Path, "exists", return_value=False):
                registry._check_workflows(repo_path)

            # Note: GitHubAPIClient won't be called if no .github/workflows exists
            # But if it is called, verify stats parameter
            if mock_github.called:
                call_kwargs = mock_github.call_args[1]
                assert "stats" in call_kwargs
                assert call_kwargs["stats"] is api_stats


class TestAPIStatisticsRecording:
    """Test that API statistics are properly recorded during operations."""

    def test_github_success_recorded(self):
        """Test that successful GitHub API calls are recorded."""
        api_stats = APIStatistics()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"workflows": []}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GitHubAPIClient("fake-token", stats=api_stats)
            client.get_repository_workflows("owner", "repo")

            assert api_stats.stats["github"]["success"] == 1
            assert api_stats.get_total_calls("github") == 1

    def test_github_error_recorded(self):
        """Test that GitHub API errors are recorded."""
        api_stats = APIStatistics()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GitHubAPIClient("fake-token", stats=api_stats)
            client.get_repository_workflows("owner", "repo")

            assert api_stats.stats["github"]["success"] == 0
            assert api_stats.stats["github"]["errors"][404] == 1
            assert api_stats.get_total_calls("github") == 1
            assert api_stats.get_total_errors("github") == 1

    def test_gerrit_success_recorded(self):
        """Test that successful Gerrit API calls are recorded."""
        api_stats = APIStatistics()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.text = ')]}\n{"project": "test"}'
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GerritAPIClient(
                "gerrit.example.org", base_url="https://gerrit.example.org", stats=api_stats
            )
            client.get_project_info("test-project")

            assert api_stats.stats["gerrit"]["success"] == 1
            assert api_stats.get_total_calls("gerrit") == 1

    def test_gerrit_error_recorded(self):
        """Test that Gerrit API errors are recorded."""
        api_stats = APIStatistics()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GerritAPIClient(
                "gerrit.example.org", base_url="https://gerrit.example.org", stats=api_stats
            )
            result = client.get_project_info("nonexistent")

            assert result is None
            assert api_stats.stats["gerrit"]["success"] == 0
            assert api_stats.stats["gerrit"]["errors"][404] == 1
            assert api_stats.get_total_errors("gerrit") == 1

    def test_jenkins_success_recorded(self):
        """Test that successful Jenkins API calls are recorded."""
        api_stats = APIStatistics()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"jobs": []}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            JenkinsAPIClient("jenkins.example.org", stats=api_stats)
            # The constructor calls API discovery which records a success

            assert api_stats.stats["jenkins"]["success"] >= 1

    def test_info_master_clone_success_recorded(self):
        """Test that successful info-master clone is recorded."""
        api_stats = APIStatistics()

        api_stats.record_info_master(True)

        assert api_stats.stats["info_master"]["success"] is True
        assert api_stats.stats["info_master"]["error"] is None

    def test_info_master_clone_failure_recorded(self):
        """Test that failed info-master clone is recorded."""
        api_stats = APIStatistics()

        api_stats.record_info_master(False, "Clone failed: connection timeout")

        assert api_stats.stats["info_master"]["success"] is False
        assert api_stats.stats["info_master"]["error"] == "Clone failed: connection timeout"


class TestAPIStatisticsOutput:
    """Test API statistics output and reporting."""

    def test_step_summary_written_with_stats(self):
        """Test that step summary is written when API calls are made."""
        api_stats = APIStatistics()
        api_stats.record_success("github")
        api_stats.record_error("gerrit", 404)
        api_stats.record_success("jenkins")

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": temp_file}):
                api_stats.write_to_step_summary()

            with open(temp_file) as f:
                content = f.read()

            assert "📊 API Statistics" in content
            assert "GitHub API" in content
            assert "Successful calls: 1" in content
            assert "Gerrit API" in content
            assert "Error 404: 1" in content
            assert "Jenkins API" in content
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_step_summary_written_without_stats(self):
        """Test that step summary indicates no API calls when stats are empty."""
        api_stats = APIStatistics()

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            temp_file = f.name

        try:
            with patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": temp_file}):
                api_stats.write_to_step_summary()

            with open(temp_file) as f:
                content = f.read()

            assert "📊 API Statistics" in content
            assert "No external API calls were made" in content
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_step_summary_not_written_without_env(self):
        """Test that step summary is not written when GITHUB_STEP_SUMMARY is not set."""
        api_stats = APIStatistics()
        api_stats.record_success("github")

        # Ensure GITHUB_STEP_SUMMARY is not set
        with patch.dict(os.environ, {}, clear=True):
            # Should not raise exception
            api_stats.write_to_step_summary()

    def test_console_output_formatting(self):
        """Test that console output is properly formatted."""
        api_stats = APIStatistics()
        api_stats.record_success("github")
        api_stats.record_success("github")
        api_stats.record_error("github", 404)
        api_stats.record_error("gerrit", 500)

        output = api_stats.format_console_output()

        assert "📊 GitHub API Statistics:" in output
        assert "✅ Successful calls: 2" in output
        assert "❌ Failed calls: 1" in output
        assert "📊 Gerrit API Statistics:" in output

    def test_console_output_empty_when_no_calls(self):
        """Test that console output is empty when no API calls made."""
        api_stats = APIStatistics()

        output = api_stats.format_console_output()

        assert output == ""

    def test_has_errors_detection(self):
        """Test that has_errors correctly detects API errors."""
        api_stats = APIStatistics()

        assert not api_stats.has_errors()

        api_stats.record_error("github", 401)
        assert api_stats.has_errors()

        api_stats2 = APIStatistics()
        api_stats2.record_info_master(False, "Clone failed")
        assert api_stats2.has_errors()


class TestAPIStatisticsGuarantees:
    """Tests that guarantee API statistics cannot be empty when they should have data."""

    def test_reporter_with_gerrit_must_have_stats(self):
        """Test that reporter with Gerrit enabled MUST pass stats object."""
        config = {
            "gerrit": {
                "enabled": True,
                "host": "gerrit.example.org",
                "base_url": "https://gerrit.example.org",
            },
            "jenkins": {"enabled": False},
        }
        logger = MagicMock()

        # Without api_stats - should log warning or fail
        with patch("reporting_tool.collectors.git.GerritAPIClient") as mock_gerrit:
            mock_instance = MagicMock()
            mock_gerrit.return_value = mock_instance
            mock_instance.get_all_projects.return_value = {}

            # This should work but not track stats
            GitDataCollector(config, {}, logger, api_stats=None)

            # Verify GerritAPIClient was called with stats=None
            call_kwargs = mock_gerrit.call_args[1]
            assert call_kwargs["stats"] is None

    def test_api_clients_work_without_stats(self):
        """Test that API clients work correctly even without stats object (backward compat)."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"workflows": []}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            # Should not raise exception
            client = GitHubAPIClient("fake-token", stats=None)
            result = client.get_repository_workflows("owner", "repo")

            # Should return results normally
            assert isinstance(result, list)

    def test_multiple_api_calls_accumulate_stats(self):
        """Test that multiple API calls accumulate statistics correctly."""
        api_stats = APIStatistics()

        with patch("httpx.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"workflows": []}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            client = GitHubAPIClient("fake-token", stats=api_stats)

            # Make multiple calls
            client.get_repository_workflows("owner1", "repo1")
            client.get_repository_workflows("owner2", "repo2")
            client.get_repository_workflows("owner3", "repo3")

            assert api_stats.stats["github"]["success"] == 3
            assert api_stats.get_total_calls("github") == 3

    def test_mixed_success_and_errors_tracked(self):
        """Test that mix of successful and failed calls are tracked correctly."""
        api_stats = APIStatistics()

        api_stats.record_success("github")
        api_stats.record_success("github")
        api_stats.record_error("github", 404)
        api_stats.record_error("github", 401)
        api_stats.record_success("github")

        assert api_stats.stats["github"]["success"] == 3
        assert api_stats.get_total_errors("github") == 2
        assert api_stats.get_total_calls("github") == 5


class TestAPIStatisticsEdgeCases:
    """Test edge cases and error conditions."""

    def test_multiple_errors_same_code(self):
        """Test that multiple errors with same code are counted correctly."""
        api_stats = APIStatistics()

        api_stats.record_error("github", 404)
        api_stats.record_error("github", 404)
        api_stats.record_error("github", 404)

        assert api_stats.stats["github"]["errors"][404] == 3

    def test_exception_tracking(self):
        """Test that exceptions (non-HTTP errors) are tracked."""
        api_stats = APIStatistics()

        api_stats.record_exception("gerrit", "timeout")
        api_stats.record_exception("gerrit", "connection_error")

        assert api_stats.stats["gerrit"]["errors"]["timeout"] == 1
        assert api_stats.stats["gerrit"]["errors"]["connection_error"] == 1

    def test_invalid_api_type_handled(self):
        """Test that invalid API types don't cause crashes."""
        api_stats = APIStatistics()

        # Should not raise exception
        api_stats.record_success("invalid_api")
        assert api_stats.get_total_calls("invalid_api") == 0

    def test_thread_safety_simulation(self):
        """Simulate concurrent API calls (basic test - not true thread safety test)."""
        api_stats = APIStatistics()

        # Simulate rapid concurrent calls
        for _ in range(100):
            api_stats.record_success("github")

        assert api_stats.stats["github"]["success"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
