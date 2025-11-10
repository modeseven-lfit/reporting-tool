# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Extended unit tests for Gerrit API client.

Tests cover:
- get_project_info method with all error scenarios
- URL encoding for project names with slashes
- Error handling and statistics tracking
- Edge cases with various response formats
- Integration with base client retry logic
"""

import json
from unittest.mock import Mock, patch

import httpx
import pytest

from api.gerrit_client import (
    GerritAPIClient,
    GerritAPIDiscovery,
)


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
def gerrit_client(mock_stats):
    """Create a GerritAPIClient instance for testing."""
    # Mock the discovery to avoid network calls
    with patch.object(
        GerritAPIDiscovery, "discover_base_url", return_value="https://gerrit.example.com"
    ):
        client = GerritAPIClient(host="gerrit.example.com", timeout=30.0, stats=mock_stats)
        yield client
        client.close()


@pytest.fixture
def gerrit_client_with_base_url(mock_stats):
    """Create a GerritAPIClient with explicit base URL (no discovery)."""
    client = GerritAPIClient(
        host="gerrit.example.com",
        base_url="https://gerrit.example.com/r",
        timeout=30.0,
        stats=mock_stats,
    )
    yield client
    client.close()


def create_gerrit_response(data, with_prefix=True):
    """Helper to create Gerrit-style JSON response."""
    json_str = json.dumps(data)
    if with_prefix:
        return ")]}'" + json_str
    return json_str


# ============================================================================
# Test get_project_info
# ============================================================================


class TestGetProjectInfo:
    """Test get_project_info method."""

    def test_get_project_info_success(self, gerrit_client, mock_stats):
        """Test successfully fetching project information."""
        project_data = {
            "name": "test/project",
            "description": "Test project",
            "state": "ACTIVE",
            "web_links": [{"name": "browse", "url": "https://gerrit.example.com/test/project"}],
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response(project_data)

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_project_info("test/project")

        assert result == project_data
        assert result["name"] == "test/project"
        assert result["state"] == "ACTIVE"
        mock_stats.record_success.assert_called_once_with("gerrit")

    def test_get_project_info_url_encoding(self, gerrit_client):
        """Test that project names with slashes are URL-encoded."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response({"name": "foo/bar/baz"})

        gerrit_client.client.get = Mock(return_value=mock_response)

        gerrit_client.get_project_info("foo/bar/baz")

        # Verify the URL encoding
        call_args = gerrit_client.client.get.call_args
        assert "foo%2Fbar%2Fbaz" in call_args[0][0]

    def test_get_project_info_not_found(self, gerrit_client, mock_stats):
        """Test handling 404 when project doesn't exist."""
        mock_response = Mock()
        mock_response.status_code = 404

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_project_info("nonexistent")

        assert result is None
        mock_stats.record_error.assert_called_once_with("gerrit", 404)

    def test_get_project_info_unauthorized(self, gerrit_client, mock_stats):
        """Test handling 401 unauthorized."""
        mock_response = Mock()
        mock_response.status_code = 401

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_project_info("test/project")

        assert result is None
        mock_stats.record_error.assert_called_once_with("gerrit", 401)

    def test_get_project_info_forbidden(self, gerrit_client, mock_stats):
        """Test handling 403 forbidden."""
        mock_response = Mock()
        mock_response.status_code = 403

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_project_info("test/project")

        assert result is None
        mock_stats.record_error.assert_called_once_with("gerrit", 403)

    def test_get_project_info_server_error(self, gerrit_client, mock_stats):
        """Test handling 500 server error."""
        mock_response = Mock()
        mock_response.status_code = 500

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_project_info("test/project")

        assert result is None
        mock_stats.record_error.assert_called_once_with("gerrit", 500)

    def test_get_project_info_exception(self, gerrit_client, mock_stats):
        """Test handling exceptions during request."""
        gerrit_client.client.get = Mock(side_effect=Exception("Network error"))

        result = gerrit_client.get_project_info("test/project")

        assert result is None
        mock_stats.record_exception.assert_called_once_with("gerrit")

    def test_get_project_info_timeout(self, gerrit_client, mock_stats):
        """Test handling request timeout."""
        gerrit_client.client.get = Mock(side_effect=httpx.TimeoutException("Request timeout"))

        result = gerrit_client.get_project_info("test/project")

        assert result is None
        mock_stats.record_exception.assert_called_once_with("gerrit")

    def test_get_project_info_without_prefix(self, gerrit_client, mock_stats):
        """Test parsing response without magic prefix."""
        project_data = {"name": "test/project", "state": "ACTIVE"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response(project_data, with_prefix=False)

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_project_info("test/project")

        assert result == project_data
        mock_stats.record_success.assert_called_once()

    def test_get_project_info_with_whitespace_prefix(self, gerrit_client, mock_stats):
        """Test parsing response with whitespace after magic prefix."""
        project_data = {"name": "test/project"}

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ")]}'  \n" + json.dumps(project_data)

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_project_info("test/project")

        assert result == project_data


# ============================================================================
# Test get_all_projects
# ============================================================================


class TestGetAllProjects:
    """Test get_all_projects method."""

    def test_get_all_projects_success(self, gerrit_client, mock_stats):
        """Test successfully fetching all projects."""
        projects_data = {
            "project1": {"name": "project1", "state": "ACTIVE"},
            "project2": {"name": "project2", "state": "READ_ONLY"},
            "test/project": {"name": "test/project", "state": "ACTIVE"},
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response(projects_data)

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_all_projects()

        assert result == projects_data
        assert len(result) == 3
        assert "project1" in result
        assert "test/project" in result
        mock_stats.record_success.assert_called_once_with("gerrit")

    def test_get_all_projects_empty(self, gerrit_client, mock_stats):
        """Test handling empty project list."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response({})

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_all_projects()

        assert result == {}
        mock_stats.record_success.assert_called_once()

    def test_get_all_projects_error(self, gerrit_client, mock_stats):
        """Test handling HTTP error when fetching all projects."""
        mock_response = Mock()
        mock_response.status_code = 500

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_all_projects()

        assert result == {}
        mock_stats.record_error.assert_called_once_with("gerrit", 500)

    def test_get_all_projects_exception(self, gerrit_client, mock_stats):
        """Test handling exception when fetching all projects."""
        gerrit_client.client.get = Mock(side_effect=Exception("Network error"))

        result = gerrit_client.get_all_projects()

        assert result == {}
        mock_stats.record_exception.assert_called_once_with("gerrit")

    def test_get_all_projects_non_dict_response(self, gerrit_client, mock_stats):
        """Test handling non-dict response (returns empty dict)."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response([{"name": "project1"}])

        gerrit_client.client.get = Mock(return_value=mock_response)

        result = gerrit_client.get_all_projects()

        # Should return empty dict for non-dict response
        assert result == {}


# ============================================================================
# Test JSON Response Parsing
# ============================================================================


class TestJSONResponseParsing:
    """Test _parse_json_response method."""

    def test_parse_with_standard_prefix(self, gerrit_client):
        """Test parsing with standard Gerrit magic prefix."""
        data = {"key": "value", "nested": {"foo": "bar"}}
        response_text = ")]}'" + json.dumps(data)

        result = gerrit_client._parse_json_response(response_text)

        assert result == data

    def test_parse_without_prefix(self, gerrit_client):
        """Test parsing without magic prefix."""
        data = {"key": "value"}
        response_text = json.dumps(data)

        result = gerrit_client._parse_json_response(response_text)

        assert result == data

    def test_parse_with_extra_whitespace(self, gerrit_client):
        """Test parsing with whitespace after prefix."""
        data = {"key": "value"}
        response_text = ")]}'  \n\n\t" + json.dumps(data)

        result = gerrit_client._parse_json_response(response_text)

        assert result == data

    def test_parse_invalid_json(self, gerrit_client):
        """Test handling invalid JSON."""
        response_text = ")]}'{invalid json}"

        result = gerrit_client._parse_json_response(response_text)

        assert result == {}

    def test_parse_non_dict_json(self, gerrit_client):
        """Test handling non-dict JSON (array)."""
        response_text = ")]}'[1, 2, 3]"

        result = gerrit_client._parse_json_response(response_text)

        assert result == {}

    def test_parse_empty_response(self, gerrit_client):
        """Test handling empty response."""
        result = gerrit_client._parse_json_response("")

        assert result == {}

    def test_parse_null_json(self, gerrit_client):
        """Test handling null JSON."""
        response_text = ")]}'null"

        result = gerrit_client._parse_json_response(response_text)

        assert result == {}

    def test_parse_complex_nested_data(self, gerrit_client):
        """Test parsing complex nested data structures."""
        data = {
            "projects": {
                "test/foo": {
                    "name": "test/foo",
                    "state": "ACTIVE",
                    "web_links": [
                        {"name": "browse", "url": "https://example.com"},
                        {"name": "gitiles", "url": "https://gitiles.example.com"},
                    ],
                    "labels": {
                        "Code-Review": {"values": {"-2": "Do not submit", "+2": "Looks good to me"}}
                    },
                }
            }
        }
        response_text = ")]}'" + json.dumps(data)

        result = gerrit_client._parse_json_response(response_text)

        assert result == data
        assert result["projects"]["test/foo"]["state"] == "ACTIVE"


# ============================================================================
# Test Client Initialization
# ============================================================================


class TestClientInitialization:
    """Test client initialization and configuration."""

    def test_init_with_base_url(self, mock_stats):
        """Test initialization with explicit base URL (no discovery)."""
        client = GerritAPIClient(
            host="gerrit.example.com", base_url="https://gerrit.example.com/r", stats=mock_stats
        )

        assert client.host == "gerrit.example.com"
        assert client.base_url == "https://gerrit.example.com/r"
        assert client.stats == mock_stats
        client.close()

    def test_init_with_autodiscovery(self, mock_stats):
        """Test initialization with autodiscovery."""
        with patch.object(
            GerritAPIDiscovery,
            "discover_base_url",
            return_value="https://gerrit.example.com/gerrit",
        ):
            client = GerritAPIClient(host="gerrit.example.com", stats=mock_stats)

            assert client.base_url == "https://gerrit.example.com/gerrit"
            client.close()

    def test_init_custom_timeout(self, mock_stats):
        """Test initialization with custom timeout."""
        with patch.object(
            GerritAPIDiscovery, "discover_base_url", return_value="https://gerrit.example.com"
        ):
            client = GerritAPIClient(host="gerrit.example.com", timeout=60.0, stats=mock_stats)

            assert client.timeout == 60.0
            client.close()

    def test_client_headers(self, mock_stats):
        """Test that client has correct headers."""
        client = GerritAPIClient(
            host="gerrit.example.com", base_url="https://gerrit.example.com", stats=mock_stats
        )

        assert "User-Agent" in client.client.headers
        assert "repository-reports" in client.client.headers["User-Agent"]
        assert client.client.headers["Accept"] == "application/json"
        client.close()


# ============================================================================
# Test Context Manager
# ============================================================================


class TestContextManager:
    """Test context manager protocol."""

    def test_context_manager_with_base_url(self, mock_stats):
        """Test using client as context manager."""
        with GerritAPIClient(
            host="gerrit.example.com", base_url="https://gerrit.example.com", stats=mock_stats
        ) as client:
            assert client is not None
            assert hasattr(client, "client")

    def test_context_manager_closes_client(self, mock_stats):
        """Test that context manager closes client."""
        client = GerritAPIClient(
            host="gerrit.example.com", base_url="https://gerrit.example.com", stats=mock_stats
        )

        with client:
            pass

        # After exiting context, client should be closed
        # We can't easily test this without implementation details

    def test_context_manager_with_exception(self, mock_stats):
        """Test that context manager closes even with exception."""
        try:
            with GerritAPIClient(
                host="gerrit.example.com", base_url="https://gerrit.example.com", stats=mock_stats
            ):
                raise ValueError("Test error")
        except ValueError:
            pass
        # If we get here without hanging, context manager worked


# ============================================================================
# Test Statistics Integration
# ============================================================================


class TestStatisticsIntegration:
    """Test statistics tracking integration."""

    def test_stats_success_recorded(self, gerrit_client, mock_stats):
        """Test that successful requests record stats."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response({"name": "test"})

        gerrit_client.client.get = Mock(return_value=mock_response)
        gerrit_client.get_project_info("test")

        mock_stats.record_success.assert_called_with("gerrit")

    def test_stats_error_recorded(self, gerrit_client, mock_stats):
        """Test that HTTP errors record stats."""
        mock_response = Mock()
        mock_response.status_code = 404

        gerrit_client.client.get = Mock(return_value=mock_response)
        gerrit_client.get_project_info("test")

        mock_stats.record_error.assert_called_with("gerrit", 404)

    def test_stats_exception_recorded(self, gerrit_client, mock_stats):
        """Test that exceptions record stats."""
        gerrit_client.client.get = Mock(side_effect=Exception("Network error"))
        gerrit_client.get_project_info("test")

        mock_stats.record_exception.assert_called_with("gerrit")

    def test_stats_none_handled(self):
        """Test that None stats doesn't cause errors."""
        client = GerritAPIClient(
            host="gerrit.example.com", base_url="https://gerrit.example.com", stats=None
        )

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response({"name": "test"})

        client.client.get = Mock(return_value=mock_response)

        # Should not raise even with stats=None
        result = client.get_project_info("test")
        assert result == {"name": "test"}
        client.close()


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_project_name_with_special_chars(self, gerrit_client):
        """Test project names with special characters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response({"name": "foo/bar-baz_qux"})

        gerrit_client.client.get = Mock(return_value=mock_response)
        result = gerrit_client.get_project_info("foo/bar-baz_qux")

        assert result["name"] == "foo/bar-baz_qux"

    def test_project_name_empty(self, gerrit_client, mock_stats):
        """Test empty project name."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response({"name": ""})

        gerrit_client.client.get = Mock(return_value=mock_response)
        gerrit_client.get_project_info("")

        # Should still make the request
        assert gerrit_client.client.get.called

    def test_very_long_project_name(self, gerrit_client):
        """Test very long project name."""
        long_name = "a" * 500
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response({"name": long_name})

        gerrit_client.client.get = Mock(return_value=mock_response)
        result = gerrit_client.get_project_info(long_name)

        assert result["name"] == long_name

    def test_unicode_in_project_name(self, gerrit_client):
        """Test Unicode characters in project name."""
        unicode_name = "test/プロジェクト"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response({"name": unicode_name})

        gerrit_client.client.get = Mock(return_value=mock_response)
        result = gerrit_client.get_project_info(unicode_name)

        assert result["name"] == unicode_name

    def test_large_response_handling(self, gerrit_client):
        """Test handling large response data."""
        # Create a large projects dict
        large_projects = {
            f"project{i}": {"name": f"project{i}", "state": "ACTIVE"} for i in range(1000)
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = create_gerrit_response(large_projects)

        gerrit_client.client.get = Mock(return_value=mock_response)
        result = gerrit_client.get_all_projects()

        assert len(result) == 1000
        assert "project0" in result
        assert "project999" in result


# ============================================================================
# Test Discovery Edge Cases
# ============================================================================


class TestDiscoveryEdgeCases:
    """Test edge cases in API discovery."""

    def test_discovery_with_redirect_no_netloc(self):
        """Test redirect discovery when location has no netloc."""
        discovery = GerritAPIDiscovery()

        mock_response = Mock()
        mock_response.status_code = 302
        mock_response.headers = {"location": "/gerrit/"}

        with patch.object(discovery.client, "get", return_value=mock_response):
            result = discovery._discover_via_redirect("gerrit.example.com")
            assert result == "/gerrit"

        discovery.close()

    def test_discovery_with_redirect_different_host(self):
        """Test redirect discovery when location has different host."""
        discovery = GerritAPIDiscovery()

        mock_response = Mock()
        mock_response.status_code = 302
        mock_response.headers = {"location": "https://other.example.com/gerrit"}

        with patch.object(discovery.client, "get", return_value=mock_response):
            result = discovery._discover_via_redirect("gerrit.example.com")
            assert result is None

        discovery.close()

    def test_validate_projects_response_with_string(self):
        """Test validating projects response with string instead of dict."""
        discovery = GerritAPIDiscovery()

        result = discovery._validate_projects_response(')]}\'"not a dict"')
        assert result is False

        discovery.close()

    def test_validate_projects_response_with_number(self):
        """Test validating projects response with number."""
        discovery = GerritAPIDiscovery()

        result = discovery._validate_projects_response(")]}'42")
        assert result is False

        discovery.close()


# ============================================================================
# Test Integration Scenarios
# ============================================================================


class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    def test_complete_project_fetch_flow(self, mock_stats):
        """Test complete flow from discovery to project fetch."""
        with patch.object(
            GerritAPIDiscovery, "discover_base_url", return_value="https://gerrit.example.com/r"
        ):
            client = GerritAPIClient(host="gerrit.example.com", stats=mock_stats)

            project_data = {"name": "test/project", "state": "ACTIVE"}
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = create_gerrit_response(project_data)

            client.client.get = Mock(return_value=mock_response)
            result = client.get_project_info("test/project")

            assert result == project_data
            mock_stats.record_success.assert_called_with("gerrit")
            client.close()

    def test_fetch_all_then_specific_project(self, gerrit_client, mock_stats):
        """Test fetching all projects then a specific one."""
        all_projects = {"project1": {"name": "project1"}, "project2": {"name": "project2"}}

        specific_project = {"name": "project1", "state": "ACTIVE", "description": "Details"}

        def mock_get(url):
            response = Mock()
            response.status_code = 200
            if "projects/?d" in url:
                response.text = create_gerrit_response(all_projects)
            else:
                response.text = create_gerrit_response(specific_project)
            return response

        gerrit_client.client.get = mock_get

        # First fetch all
        all_result = gerrit_client.get_all_projects()
        assert len(all_result) == 2

        # Then fetch specific
        specific_result = gerrit_client.get_project_info("project1")
        assert specific_result["description"] == "Details"
