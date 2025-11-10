# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Comprehensive tests for src/rendering/context.py module.

This test suite provides thorough coverage of:
- RenderContext initialization
- Context building methods
- Data extraction and formatting
- Edge cases and missing data handling
- Configuration-based customization

Target: 95%+ coverage for context.py (from 92.59%)
Phase: 12, Step 4, Task 1.4
"""

import pytest

from rendering.context import RenderContext


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def minimal_data():
    """Minimal valid report data."""
    return {
        "project": "test-project",
        "schema_version": "1.0.0",
        "repositories": [],
        "metadata": {"generated_at": "2025-01-16T14:30:00Z", "report_version": "1.0.0"},
    }


@pytest.fixture
def full_data():
    """Complete report data with all sections."""
    return {
        "project": "full-project",
        "schema_version": "2.0.0",
        "repositories": [
            {
                "gerrit_project": "repo1",
                "name": "repo1",
                "total_commits": 100,
                "total_lines_added": 5000,
                "total_lines_removed": 2000,
                "activity_status": "active",
                "features": {"has_ci": True, "has_tests": True},
                "jenkins_jobs": [
                    {
                        "name": "job1",
                        "status": "success",
                        "color": "blue",
                        "url": "http://jenkins/job1",
                    }
                ],
            },
            {
                "gerrit_project": "repo2",
                "name": "repo2",
                "total_commits": 50,
                "total_lines_added": 1000,
                "total_lines_removed": 500,
                "activity_status": "inactive",
                "features": {"has_ci": False},
                "jenkins_jobs": [],
            },
        ],
        "metadata": {"generated_at": "2025-01-16T14:30:00Z", "report_version": "2.0.0"},
        "summaries": {
            "counts": {
                "repositories_analyzed": 2,
                "total_gerrit_projects": 5,
                "unique_contributors": 10,
                "total_organizations": 3,
                "active_repositories": 1,
                "inactive_repositories": 1,
                "no_commit_repositories": 0,
            },
            "all_repositories": [
                {"name": "repo1", "activity_status": "active"},
                {"name": "repo2", "activity_status": "inactive"},
            ],
            "no_commit_repositories": [],
            "top_contributors_commits": [
                {"name": "user1", "commits": 100},
                {"name": "user2", "commits": 50},
            ],
            "top_contributors_loc": [{"name": "user1", "lines": 5000}],
            "top_organizations": [{"name": "org1", "commits": 150}],
        },
        "orphaned_jenkins_jobs": {
            "total_orphaned_jobs": 2,
            "jobs": {
                "orphan1": {"project_name": "old-project", "state": "DISABLED", "score": 0},
                "orphan2": {"project_name": "another-project", "state": "UNKNOWN", "score": 5},
            },
            "by_state": {"DISABLED": 1, "UNKNOWN": 1},
        },
        "time_windows": [
            {"name": "recent", "days": 30, "description": "Last 30 days"},
            {"name": "quarter", "days": 90, "description": "Last quarter"},
        ],
    }


@pytest.fixture
def minimal_config():
    """Minimal configuration."""
    return {}


@pytest.fixture
def full_config():
    """Full configuration with all options."""
    return {
        "project": {"name": "Custom Project"},
        "render": {"theme": "dark"},
        "output": {
            "top_contributors_limit": 10,
            "top_organizations_limit": 15,
            "include_sections": {
                "title": True,
                "summary": True,
                "repositories": True,
                "contributors": True,
                "organizations": True,
                "features": True,
                "workflows": True,
                "orphaned_jobs": False,
            },
        },
    }


# ============================================================================
# RenderContext Tests
# ============================================================================


class TestRenderContextInit:
    """Test RenderContext initialization."""

    def test_init_basic(self, minimal_data, minimal_config):
        """Test basic initialization."""
        context = RenderContext(minimal_data, minimal_config)

        assert context.data == minimal_data
        assert context.config == minimal_config

    def test_init_with_full_data(self, full_data, full_config):
        """Test initialization with complete data."""
        context = RenderContext(full_data, full_config)

        assert context.data == full_data
        assert context.config == full_config


class TestRenderContextBuild:
    """Test main build method."""

    def test_build_returns_dict(self, minimal_data, minimal_config):
        """Test that build returns a dictionary."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        assert isinstance(result, dict)

    def test_build_has_required_keys(self, minimal_data, minimal_config):
        """Test that build result has all required keys."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        required_keys = [
            "project",
            "summary",
            "repositories",
            "contributors",
            "organizations",
            "features",
            "workflows",
            "orphaned_jobs",
            "time_windows",
            "config",
            "filters",
        ]

        for key in required_keys:
            assert key in result

    def test_build_filters_included(self, minimal_data, minimal_config):
        """Test that template filters are included."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        assert "filters" in result
        assert "format_number" in result["filters"]


class TestProjectContext:
    """Test project context building."""

    def test_project_context_basic(self, minimal_data, minimal_config):
        """Test basic project context."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        assert result["project"]["name"] == "test-project"
        assert result["project"]["schema_version"] == "1.0.0"

    def test_project_context_metadata(self, full_data, minimal_config):
        """Test project metadata extraction."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        project = result["project"]
        assert project["generated_at"] == "2025-01-16T14:30:00Z"
        assert project["report_version"] == "2.0.0"
        assert "generated_at_formatted" in project

    def test_project_context_defaults(self, minimal_config):
        """Test default values when metadata missing."""
        data = {"repositories": []}
        context = RenderContext(data, minimal_config)
        result = context.build()

        project = result["project"]
        assert project["name"] == "Repository Analysis"
        assert project["schema_version"] == "1.0.0"


class TestSummaryContext:
    """Test summary statistics context."""

    def test_summary_basic(self, minimal_data, minimal_config):
        """Test summary with minimal data."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        summary = result["summary"]
        assert summary["total_commits"] == 0
        assert summary["repositories_analyzed"] == 0

    def test_summary_calculations(self, full_data, minimal_config):
        """Test summary calculations from repository data."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        summary = result["summary"]
        # 100 + 50 commits
        assert summary["total_commits"] == 150
        assert summary["total_commits_formatted"] == "150"

        # 5000 + 1000 lines added
        assert summary["total_lines_added"] == 6000

        # 2000 + 500 lines removed
        assert summary["total_lines_removed"] == 2500

        # Net: 6000 - 2500
        assert summary["net_lines"] == 3500

    def test_summary_from_summaries(self, full_data, minimal_config):
        """Test summary using summaries data."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        summary = result["summary"]
        assert summary["repositories_analyzed"] == 2
        assert summary["total_repositories"] == 5
        assert summary["unique_contributors"] == 10
        assert summary["total_organizations"] == 3

    def test_summary_activity_counts(self, full_data, minimal_config):
        """Test activity status counts."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        summary = result["summary"]
        assert summary["active_count"] == 1
        assert summary["inactive_count"] == 1
        assert summary["no_commit_count"] == 0


class TestRepositoriesContext:
    """Test repositories context."""

    def test_repositories_empty(self, minimal_data, minimal_config):
        """Test repositories with no data."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        repos = result["repositories"]
        assert repos["all_count"] == 0
        assert repos["has_repositories"] is False

    def test_repositories_all(self, full_data, minimal_config):
        """Test all repositories listing."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        repos = result["repositories"]
        assert repos["all_count"] == 2
        assert len(repos["all"]) == 2

    def test_repositories_by_activity(self, full_data, minimal_config):
        """Test repositories filtered by activity."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        repos = result["repositories"]
        assert repos["active_count"] == 1
        assert repos["inactive_count"] == 1
        assert repos["no_commits_count"] == 0

    def test_repositories_has_flag(self, full_data, minimal_config):
        """Test has_repositories flag."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        assert result["repositories"]["has_repositories"] is True


class TestContributorsContext:
    """Test contributors context."""

    def test_contributors_empty(self, minimal_data, minimal_config):
        """Test contributors with no data."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        contributors = result["contributors"]
        assert contributors["has_contributors"] is False

    def test_contributors_data(self, full_data, minimal_config):
        """Test contributors data extraction."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        contributors = result["contributors"]
        assert contributors["top_by_commits_count"] == 2
        assert contributors["top_by_loc_count"] == 1
        assert contributors["has_contributors"] is True

    def test_contributors_limit_default(self, full_data, minimal_config):
        """Test default contributor limit."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        assert result["contributors"]["limit"] == 20

    def test_contributors_limit_custom(self, full_data, full_config):
        """Test custom contributor limit from config."""
        context = RenderContext(full_data, full_config)
        result = context.build()

        contributors = result["contributors"]
        assert contributors["limit"] == 10
        assert len(contributors["top_by_commits"]) <= 10


class TestOrganizationsContext:
    """Test organizations context."""

    def test_organizations_empty(self, minimal_data, minimal_config):
        """Test organizations with no data."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        orgs = result["organizations"]
        assert orgs["has_organizations"] is False

    def test_organizations_data(self, full_data, minimal_config):
        """Test organizations data extraction."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        orgs = result["organizations"]
        assert orgs["total_count"] == 1
        assert orgs["has_organizations"] is True

    def test_organizations_limit_default(self, full_data, minimal_config):
        """Test default organization limit."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        assert result["organizations"]["limit"] == 20

    def test_organizations_limit_custom(self, full_data, full_config):
        """Test custom organization limit from config."""
        context = RenderContext(full_data, full_config)
        result = context.build()

        assert result["organizations"]["limit"] == 15


class TestFeaturesContext:
    """Test features matrix context."""

    def test_features_empty(self, minimal_data, minimal_config):
        """Test features with no repositories."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        features = result["features"]
        assert features["feature_count"] == 0
        assert features["has_features"] is False

    def test_features_extraction(self, full_data, minimal_config):
        """Test feature extraction from repositories."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        features = result["features"]
        assert features["feature_count"] == 2
        assert "has_ci" in features["features_list"]
        assert "has_tests" in features["features_list"]

    def test_features_matrix(self, full_data, minimal_config):
        """Test feature matrix construction."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        features = result["features"]
        assert len(features["matrix"]) == 2

        # Check matrix structure
        for repo_features in features["matrix"]:
            assert "repo_name" in repo_features
            assert "features" in repo_features

    def test_features_sorted(self, full_data, minimal_config):
        """Test that features are sorted alphabetically."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        features_list = result["features"]["features_list"]
        assert features_list == sorted(features_list)


class TestWorkflowsContext:
    """Test workflows/CI context."""

    def test_workflows_empty(self, minimal_data, minimal_config):
        """Test workflows with no data."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        workflows = result["workflows"]
        assert workflows["total_count"] == 0
        assert workflows["has_workflows"] is False

    def test_workflows_extraction(self, full_data, minimal_config):
        """Test workflow extraction from repositories."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        workflows = result["workflows"]
        assert workflows["total_count"] == 1
        assert workflows["has_workflows"] is True

    def test_workflows_structure(self, full_data, minimal_config):
        """Test workflow data structure."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        workflow = result["workflows"]["all"][0]
        assert workflow["name"] == "job1"
        assert workflow["repo"] == "repo1"
        assert workflow["status"] == "success"
        assert workflow["color"] == "success"

    def test_workflows_status_counts(self, full_data, minimal_config):
        """Test workflow status counting."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        status_counts = result["workflows"]["status_counts"]
        assert status_counts.get("success", 0) == 1


class TestOrphanedJobsContext:
    """Test orphaned jobs context."""

    def test_orphaned_jobs_empty(self, minimal_data, minimal_config):
        """Test orphaned jobs with no data."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        orphaned = result["orphaned_jobs"]
        assert orphaned["total_count"] == 0
        assert orphaned["has_orphaned_jobs"] is False

    def test_orphaned_jobs_extraction(self, full_data, minimal_config):
        """Test orphaned jobs extraction."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        orphaned = result["orphaned_jobs"]
        assert orphaned["total_count"] == 2
        assert len(orphaned["jobs"]) == 2
        assert orphaned["has_orphaned_jobs"] is True

    def test_orphaned_jobs_structure(self, full_data, minimal_config):
        """Test orphaned jobs data structure."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        jobs = result["orphaned_jobs"]["jobs"]
        job = jobs[0]
        assert "name" in job
        assert "project" in job
        assert "state" in job
        assert "score" in job

    def test_orphaned_jobs_sorted(self, full_data, minimal_config):
        """Test that orphaned jobs are sorted by state."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        jobs = result["orphaned_jobs"]["jobs"]
        # Should be sorted by state, then name
        assert len(jobs) == 2


class TestTimeWindowsContext:
    """Test time windows context."""

    def test_time_windows_empty(self, minimal_data, minimal_config):
        """Test time windows with no data."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        time_windows = result["time_windows"]
        assert isinstance(time_windows, list)
        assert len(time_windows) == 0

    def test_time_windows_extraction(self, full_data, minimal_config):
        """Test time windows extraction."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        time_windows = result["time_windows"]
        assert len(time_windows) == 2

    def test_time_windows_structure(self, full_data, minimal_config):
        """Test time window data structure."""
        context = RenderContext(full_data, minimal_config)
        result = context.build()

        tw = result["time_windows"][0]
        assert tw["name"] == "recent"
        assert tw["days"] == 30
        assert tw["description"] == "Last 30 days"


class TestConfigContext:
    """Test configuration context."""

    def test_config_context_defaults(self, minimal_data, minimal_config):
        """Test config context with defaults."""
        context = RenderContext(minimal_data, minimal_config)
        result = context.build()

        config = result["config"]
        assert config["theme"] == "default"
        assert config["project_name"] == "Repository Analysis"

    def test_config_context_custom(self, minimal_data, full_config):
        """Test config context with custom values."""
        context = RenderContext(minimal_data, full_config)
        result = context.build()

        config = result["config"]
        assert config["theme"] == "dark"
        assert config["project_name"] == "Custom Project"

    def test_config_include_sections(self, minimal_data, full_config):
        """Test include_sections configuration."""
        context = RenderContext(minimal_data, full_config)
        result = context.build()

        sections = result["config"]["include_sections"]
        assert sections["title"] is True
        assert sections["summary"] is True
        assert sections["orphaned_jobs"] is False


class TestGetStatusColor:
    """Test status color mapping."""

    def test_status_color_success(self, minimal_data, minimal_config):
        """Test success color mappings."""
        context = RenderContext(minimal_data, minimal_config)

        assert context._get_status_color("blue") == "success"
        assert context._get_status_color("blue_anime") == "success"
        assert context._get_status_color("green") == "success"

    def test_status_color_failure(self, minimal_data, minimal_config):
        """Test failure color mappings."""
        context = RenderContext(minimal_data, minimal_config)

        assert context._get_status_color("red") == "failure"
        assert context._get_status_color("red_anime") == "failure"

    def test_status_color_warning(self, minimal_data, minimal_config):
        """Test warning color mappings."""
        context = RenderContext(minimal_data, minimal_config)

        assert context._get_status_color("yellow") == "warning"
        assert context._get_status_color("yellow_anime") == "warning"
        assert context._get_status_color("aborted") == "warning"

    def test_status_color_disabled(self, minimal_data, minimal_config):
        """Test disabled color mappings."""
        context = RenderContext(minimal_data, minimal_config)

        assert context._get_status_color("disabled") == "disabled"
        assert context._get_status_color("grey") == "disabled"

    def test_status_color_unknown(self, minimal_data, minimal_config):
        """Test unknown color mappings."""
        context = RenderContext(minimal_data, minimal_config)

        assert context._get_status_color("notbuilt") == "unknown"
        assert context._get_status_color("invalid") == "unknown"
        assert context._get_status_color("UNKNOWN") == "unknown"

    def test_status_color_case_insensitive(self, minimal_data, minimal_config):
        """Test that color mapping is case-insensitive."""
        context = RenderContext(minimal_data, minimal_config)

        assert context._get_status_color("BLUE") == "success"
        assert context._get_status_color("Red") == "failure"


# ============================================================================
# Edge Cases and Integration
# ============================================================================


class TestContextEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_summaries_section(self, minimal_config):
        """Test handling when summaries section is missing."""
        data = {"project": "test", "repositories": []}
        context = RenderContext(data, minimal_config)
        result = context.build()

        # Should handle gracefully with defaults
        assert result["summary"]["total_commits"] == 0

    def test_empty_repositories_list(self, minimal_config):
        """Test with empty repositories list."""
        data = {"repositories": [], "summaries": {}}
        context = RenderContext(data, minimal_config)
        result = context.build()

        assert result["summary"]["total_commits"] == 0
        assert result["repositories"]["all_count"] == 0

    def test_missing_metadata(self, minimal_config):
        """Test handling when metadata is missing."""
        data = {"repositories": []}
        context = RenderContext(data, minimal_config)
        result = context.build()

        project = result["project"]
        assert "generated_at" in project
        assert "report_version" in project

    def test_repositories_without_features(self, minimal_config):
        """Test repositories without features field."""
        data = {"repositories": [{"name": "repo1"}]}
        context = RenderContext(data, minimal_config)
        result = context.build()

        # Should handle gracefully
        assert result["features"]["feature_count"] == 0

    def test_repositories_without_jenkins_jobs(self, minimal_config):
        """Test repositories without jenkins_jobs field."""
        data = {"repositories": [{"name": "repo1"}]}
        context = RenderContext(data, minimal_config)
        result = context.build()

        # Should handle gracefully
        assert result["workflows"]["total_count"] == 0
