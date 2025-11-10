# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for INFO.yaml parser.

Tests the parsing logic for INFO.yaml files, including:
- Valid YAML parsing
- Invalid/malformed YAML handling
- Field extraction
- Path resolution
- Error handling
"""

from pathlib import Path

import pytest

from domain.info_yaml import CommitterInfo, ProjectInfo
from reporting_tool.collectors.info_yaml.parser import (
    INFOYamlParser,
    parse_info_yaml_directory,
    parse_info_yaml_file,
)


@pytest.fixture
def info_master_path(tmp_path: Path) -> Path:
    """Create a temporary info-master directory structure."""
    info_master = tmp_path / "info-master"
    info_master.mkdir()
    return info_master


@pytest.fixture
def gerrit_server_dir(info_master_path: Path) -> Path:
    """Create a Gerrit server directory."""
    server_dir = info_master_path / "gerrit.example.org"
    server_dir.mkdir()
    return server_dir


@pytest.fixture
def valid_info_yaml_content() -> str:
    """Return valid INFO.yaml content for testing."""
    return """---
project: 'Test Project'
project_creation_date: '2020-01-15'
lifecycle_state: 'Active'
project_lead:
  name: 'John Doe'
  email: 'john.doe@example.com'
  id: 'jdoe'
  company: 'Example Corp'
  timezone: 'America/Los_Angeles'
committers:
  - name: 'Alice Johnson'
    email: 'alice.johnson@example.com'
    id: 'ajohnson'
    company: 'Developer Inc'
  - name: 'Bob Williams'
    email: 'bob.williams@example.com'
    id: 'bwilliams'
    company: 'Code Solutions'
repositories:
  - test/repo1
  - test/repo2
issue_tracking:
  type: 'jira'
  url: 'https://jira.example.org/projects/TEST'
"""


@pytest.fixture
def minimal_info_yaml_content() -> str:
    """Return minimal valid INFO.yaml content."""
    return """---
project: 'Minimal Project'
project_creation_date: '2021-06-01'
lifecycle_state: 'Incubation'
"""


@pytest.fixture
def invalid_yaml_content() -> str:
    """Return invalid YAML content for testing error handling."""
    return """---
project: 'Invalid YAML'
  bad_indentation: true
    worse_indentation: false
"""


class TestINFOYamlParser:
    """Tests for INFOYamlParser class."""

    def test_create_parser(self, info_master_path: Path):
        """Test creating a parser instance."""
        parser = INFOYamlParser(info_master_path)

        assert parser.info_master_path == info_master_path
        assert parser.logger is not None

    def test_parse_valid_file(
        self, info_master_path: Path, gerrit_server_dir: Path, valid_info_yaml_content: str
    ):
        """Test parsing a valid INFO.yaml file."""
        # Create project directory and INFO.yaml file
        project_dir = gerrit_server_dir / "test" / "project"
        project_dir.mkdir(parents=True)
        yaml_file = project_dir / "INFO.yaml"
        yaml_file.write_text(valid_info_yaml_content)

        # Parse the file
        parser = INFOYamlParser(info_master_path)
        result = parser.parse_file(yaml_file)

        # Verify result
        assert result is not None
        assert isinstance(result, ProjectInfo)
        assert result.project_name == "Test Project"
        assert result.gerrit_server == "gerrit.example.org"
        assert result.project_path == "test/project"
        assert result.creation_date == "2020-01-15"
        assert result.lifecycle_state == "Active"
        assert result.project_lead is not None
        assert result.project_lead.name == "John Doe"
        assert len(result.committers) == 2
        assert result.committers[0].name == "Alice Johnson"
        assert len(result.repositories) == 2
        assert result.issue_tracking.type == "jira"
        assert result.issue_tracking.url == "https://jira.example.org/projects/TEST"

    def test_parse_minimal_file(
        self, info_master_path: Path, gerrit_server_dir: Path, minimal_info_yaml_content: str
    ):
        """Test parsing a minimal INFO.yaml file."""
        project_dir = gerrit_server_dir / "minimal"
        project_dir.mkdir(parents=True)
        yaml_file = project_dir / "INFO.yaml"
        yaml_file.write_text(minimal_info_yaml_content)

        parser = INFOYamlParser(info_master_path)
        result = parser.parse_file(yaml_file)

        assert result is not None
        assert result.project_name == "Minimal Project"
        assert result.gerrit_server == "gerrit.example.org"
        assert result.project_path == "minimal"
        assert result.lifecycle_state == "Incubation"
        assert result.project_lead is None
        assert len(result.committers) == 0
        assert len(result.repositories) == 0

    def test_parse_nonexistent_file(self, info_master_path: Path):
        """Test parsing a file that doesn't exist."""
        parser = INFOYamlParser(info_master_path)
        yaml_file = info_master_path / "nonexistent" / "INFO.yaml"

        result = parser.parse_file(yaml_file)

        assert result is None

    def test_parse_invalid_yaml(
        self, info_master_path: Path, gerrit_server_dir: Path, invalid_yaml_content: str
    ):
        """Test parsing invalid YAML content."""
        project_dir = gerrit_server_dir / "invalid"
        project_dir.mkdir(parents=True)
        yaml_file = project_dir / "INFO.yaml"
        yaml_file.write_text(invalid_yaml_content)

        parser = INFOYamlParser(info_master_path)
        result = parser.parse_file(yaml_file)

        # Should return None for invalid YAML
        assert result is None

    def test_parse_empty_file(self, info_master_path: Path, gerrit_server_dir: Path):
        """Test parsing an empty file."""
        project_dir = gerrit_server_dir / "empty"
        project_dir.mkdir(parents=True)
        yaml_file = project_dir / "INFO.yaml"
        yaml_file.write_text("")

        parser = INFOYamlParser(info_master_path)
        result = parser.parse_file(yaml_file)

        assert result is None

    def test_parse_directory(
        self,
        info_master_path: Path,
        gerrit_server_dir: Path,
        valid_info_yaml_content: str,
        minimal_info_yaml_content: str,
    ):
        """Test parsing all INFO.yaml files in a directory."""
        # Create multiple projects
        project1_dir = gerrit_server_dir / "project1"
        project1_dir.mkdir(parents=True)
        (project1_dir / "INFO.yaml").write_text(valid_info_yaml_content)

        project2_dir = gerrit_server_dir / "project2"
        project2_dir.mkdir(parents=True)
        (project2_dir / "INFO.yaml").write_text(minimal_info_yaml_content)

        # Parse directory
        parser = INFOYamlParser(info_master_path)
        results = parser.parse_directory(info_master_path)

        # Verify results
        assert len(results) == 2
        assert all(isinstance(r, ProjectInfo) for r in results)
        project_names = {r.project_name for r in results}
        assert "Test Project" in project_names
        assert "Minimal Project" in project_names

    def test_parse_directory_nonexistent(self, tmp_path: Path):
        """Test parsing a nonexistent directory."""
        parser = INFOYamlParser(tmp_path / "info-master")
        nonexistent_dir = tmp_path / "nonexistent"

        results = parser.parse_directory(nonexistent_dir)

        assert results == []

    def test_parse_directory_is_file(self, tmp_path: Path):
        """Test parsing when path is a file, not a directory."""
        file_path = tmp_path / "not_a_directory.txt"
        file_path.write_text("content")

        parser = INFOYamlParser(tmp_path)
        results = parser.parse_directory(file_path)

        assert results == []

    def test_extract_person_valid(self, info_master_path: Path):
        """Test extracting person information."""
        parser = INFOYamlParser(info_master_path)
        person_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Example Corp",
            "id": "jdoe",
            "timezone": "America/Los_Angeles",
        }

        result = parser._extract_person(person_data)

        assert result is not None
        assert result.name == "John Doe"
        assert result.email == "john@example.com"
        assert result.company == "Example Corp"
        assert result.id == "jdoe"

    def test_extract_person_missing_name(self, info_master_path: Path):
        """Test extracting person with missing name."""
        parser = INFOYamlParser(info_master_path)
        person_data = {"email": "test@example.com"}

        result = parser._extract_person(person_data)

        assert result is None

    def test_extract_person_unknown_name(self, info_master_path: Path):
        """Test extracting person with 'Unknown' name."""
        parser = INFOYamlParser(info_master_path)
        person_data = {"name": "Unknown"}

        result = parser._extract_person(person_data)

        assert result is None

    def test_extract_person_invalid_data(self, info_master_path: Path):
        """Test extracting person with invalid data."""
        parser = INFOYamlParser(info_master_path)

        assert parser._extract_person(None) is None
        assert parser._extract_person([]) is None
        assert parser._extract_person("string") is None

    def test_extract_committers_valid(self, info_master_path: Path):
        """Test extracting committers list."""
        parser = INFOYamlParser(info_master_path)
        committers_data = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
            {"name": "Carol", "email": "carol@example.com"},
        ]

        result = parser._extract_committers(committers_data)

        assert len(result) == 3
        assert all(isinstance(c, CommitterInfo) for c in result)
        assert result[0].name == "Alice"
        assert result[1].name == "Bob"
        assert result[2].name == "Carol"
        # All should have default activity status
        assert all(c.activity_status == "unknown" for c in result)
        assert all(c.activity_color == "gray" for c in result)

    def test_extract_committers_empty_list(self, info_master_path: Path):
        """Test extracting empty committers list."""
        parser = INFOYamlParser(info_master_path)

        result = parser._extract_committers([])

        assert result == []

    def test_extract_committers_invalid_data(self, info_master_path: Path):
        """Test extracting committers with invalid data."""
        parser = INFOYamlParser(info_master_path)

        assert parser._extract_committers(None) == []
        assert parser._extract_committers("string") == []
        assert parser._extract_committers({}) == []

    def test_extract_committers_skip_invalid_entries(self, info_master_path: Path):
        """Test that invalid committer entries are skipped."""
        parser = INFOYamlParser(info_master_path)
        committers_data = [
            {"name": "Valid User", "email": "valid@example.com"},
            {"name": "Unknown"},  # Should be skipped
            {"email": "no-name@example.com"},  # Missing name, should be skipped
            "invalid",  # Not a dict, should be skipped
            {"name": "Another Valid", "email": "another@example.com"},
        ]

        result = parser._extract_committers(committers_data)

        assert len(result) == 2
        assert result[0].name == "Valid User"
        assert result[1].name == "Another Valid"

    def test_extract_issue_tracking_valid(self, info_master_path: Path):
        """Test extracting issue tracking information."""
        parser = INFOYamlParser(info_master_path)
        issue_data = {
            "type": "jira",
            "url": "https://jira.example.org/projects/TEST",
            "key": "TEST",
        }

        result = parser._extract_issue_tracking(issue_data)

        assert result.type == "jira"
        assert result.url == "https://jira.example.org/projects/TEST"
        assert result.is_valid is False  # Not validated yet
        assert result.validation_error == ""

    def test_extract_issue_tracking_empty(self, info_master_path: Path):
        """Test extracting empty issue tracking."""
        parser = INFOYamlParser(info_master_path)

        result = parser._extract_issue_tracking({})

        assert result.type == ""
        assert result.url == ""
        assert result.is_valid is False

    def test_extract_issue_tracking_invalid_data(self, info_master_path: Path):
        """Test extracting issue tracking with invalid data."""
        parser = INFOYamlParser(info_master_path)

        result1 = parser._extract_issue_tracking(None)
        result2 = parser._extract_issue_tracking([])

        assert result1.url == ""
        assert result2.url == ""

    def test_extract_repositories_list(self, info_master_path: Path):
        """Test extracting repositories as list of strings."""
        parser = INFOYamlParser(info_master_path)
        repos_data = ["repo1", "repo2", "repo3"]

        result = parser._extract_repositories(repos_data)

        assert result == ["repo1", "repo2", "repo3"]

    def test_extract_repositories_dict_list(self, info_master_path: Path):
        """Test extracting repositories as list of dicts with 'name' key."""
        parser = INFOYamlParser(info_master_path)
        repos_data = [
            {"name": "repo1", "url": "https://example.com/repo1"},
            {"name": "repo2", "url": "https://example.com/repo2"},
        ]

        result = parser._extract_repositories(repos_data)

        assert result == ["repo1", "repo2"]

    def test_extract_repositories_mixed(self, info_master_path: Path):
        """Test extracting repositories with mixed string and dict entries."""
        parser = INFOYamlParser(info_master_path)
        repos_data = [
            "repo1",
            {"name": "repo2"},
            "repo3",
            {"name": "repo4", "url": "https://example.com"},
        ]

        result = parser._extract_repositories(repos_data)

        assert result == ["repo1", "repo2", "repo3", "repo4"]

    def test_extract_repositories_empty(self, info_master_path: Path):
        """Test extracting empty repositories list."""
        parser = INFOYamlParser(info_master_path)

        result = parser._extract_repositories([])

        assert result == []

    def test_extract_repositories_invalid_data(self, info_master_path: Path):
        """Test extracting repositories with invalid data."""
        parser = INFOYamlParser(info_master_path)

        assert parser._extract_repositories(None) == []
        assert parser._extract_repositories("string") == []
        assert parser._extract_repositories({}) == []

    def test_path_resolution_nested_project(
        self, info_master_path: Path, valid_info_yaml_content: str
    ):
        """Test path resolution for nested project structure."""
        # Create deeply nested project
        server_dir = info_master_path / "gerrit.example.org"
        project_dir = server_dir / "category" / "subcategory" / "project"
        project_dir.mkdir(parents=True)
        yaml_file = project_dir / "INFO.yaml"
        yaml_file.write_text(valid_info_yaml_content)

        parser = INFOYamlParser(info_master_path)
        result = parser.parse_file(yaml_file)

        assert result is not None
        assert result.gerrit_server == "gerrit.example.org"
        assert result.project_path == "category/subcategory/project"
        assert result.full_path == "gerrit.example.org/category/subcategory/project"

    def test_path_resolution_single_level(
        self, info_master_path: Path, valid_info_yaml_content: str
    ):
        """Test path resolution for single-level project."""
        server_dir = info_master_path / "gerrit.example.org"
        project_dir = server_dir / "simple"
        project_dir.mkdir(parents=True)
        yaml_file = project_dir / "INFO.yaml"
        yaml_file.write_text(valid_info_yaml_content)

        parser = INFOYamlParser(info_master_path)
        result = parser.parse_file(yaml_file)

        assert result is not None
        assert result.gerrit_server == "gerrit.example.org"
        assert result.project_path == "simple"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_parse_info_yaml_file(
        self, info_master_path: Path, gerrit_server_dir: Path, valid_info_yaml_content: str
    ):
        """Test parse_info_yaml_file convenience function."""
        project_dir = gerrit_server_dir / "test"
        project_dir.mkdir(parents=True)
        yaml_file = project_dir / "INFO.yaml"
        yaml_file.write_text(valid_info_yaml_content)

        result = parse_info_yaml_file(yaml_file, info_master_path)

        assert result is not None
        assert isinstance(result, ProjectInfo)
        assert result.project_name == "Test Project"

    def test_parse_info_yaml_directory(
        self, info_master_path: Path, gerrit_server_dir: Path, valid_info_yaml_content: str
    ):
        """Test parse_info_yaml_directory convenience function."""
        project_dir = gerrit_server_dir / "test"
        project_dir.mkdir(parents=True)
        yaml_file = project_dir / "INFO.yaml"
        yaml_file.write_text(valid_info_yaml_content)

        results = parse_info_yaml_directory(info_master_path)

        assert len(results) == 1
        assert isinstance(results[0], ProjectInfo)
        assert results[0].project_name == "Test Project"
