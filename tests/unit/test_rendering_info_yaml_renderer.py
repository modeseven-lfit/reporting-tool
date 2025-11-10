# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for INFO.yaml renderer.

Tests the InfoYamlRenderer class for generating Markdown reports
from INFO.yaml project data.

Phase 3: Rendering & Report Integration
"""

import pytest

from domain.info_yaml import (
    CommitterInfo,
    IssueTracking,
    LifecycleSummary,
    PersonInfo,
    ProjectInfo,
)
from rendering.info_yaml_renderer import InfoYamlRenderer


@pytest.fixture
def renderer():
    """Create InfoYamlRenderer instance."""
    return InfoYamlRenderer()


@pytest.fixture
def sample_committers():
    """Create sample committers with different activity statuses."""
    return [
        CommitterInfo(
            name="Alice Active",
            email="alice@example.com",
            company="Acme Corp",
            id="alice123",
            activity_status="current",
            activity_color="green",
            days_since_last_commit=30,
        ),
        CommitterInfo(
            name="Bob Moderate",
            email="bob@example.com",
            company="Beta Inc",
            id="bob456",
            activity_status="active",
            activity_color="orange",
            days_since_last_commit=500,
        ),
        CommitterInfo(
            name="Charlie Inactive",
            email="charlie@example.com",
            company="Gamma LLC",
            id="charlie789",
            activity_status="inactive",
            activity_color="red",
            days_since_last_commit=1200,
        ),
    ]


@pytest.fixture
def sample_project(sample_committers):
    """Create a sample ProjectInfo object."""
    return ProjectInfo(
        project_name="Test Project",
        gerrit_server="gerrit.example.org",
        project_path="testorg/testproject",
        full_path="gerrit.example.org/testorg/testproject",
        creation_date="2020-01-01",
        lifecycle_state="Active",
        project_lead=PersonInfo(
            name="Alice Active",
            email="alice@example.com",
            company="Acme Corp",
            id="alice123",
        ),
        committers=sample_committers,
        issue_tracking=IssueTracking(
            type="jira",
            url="https://jira.example.com/projects/TEST",
            is_valid=True,
        ),
        repositories=["repo1", "repo2"],
        has_git_data=True,
        project_days_since_last_commit=30,
    )


@pytest.fixture
def sample_projects(sample_project):
    """Create a list of sample projects."""
    # Create additional projects with different states
    project2 = ProjectInfo(
        project_name="Another Project",
        gerrit_server="gerrit.example.org",
        project_path="testorg/another",
        full_path="gerrit.example.org/testorg/another",
        creation_date="2021-06-15",
        lifecycle_state="Incubation",
        project_lead=PersonInfo(
            name="Bob Moderate",
            email="bob@example.com",
            company="Beta Inc",
            id="bob456",
        ),
        committers=[
            CommitterInfo(
                name="Bob Moderate",
                email="bob@example.com",
                company="Beta Inc",
                id="bob456",
                activity_status="active",
                activity_color="orange",
                days_since_last_commit=400,
            ),
        ],
        has_git_data=True,
    )

    project3 = ProjectInfo(
        project_name="Archived Project",
        gerrit_server="gerrit.other.org",
        project_path="oldorg/archived",
        full_path="gerrit.other.org/oldorg/archived",
        creation_date="2018-03-20",
        lifecycle_state="Archived",
        project_lead=PersonInfo(
            name="Charlie Inactive",
            email="charlie@example.com",
            company="Gamma LLC",
            id="charlie789",
        ),
        committers=[],
        has_git_data=False,
    )

    return [sample_project, project2, project3]


class TestInfoYamlRendererBasic:
    """Test basic renderer functionality."""

    def test_init(self):
        """Test renderer initialization."""
        renderer = InfoYamlRenderer()
        assert renderer is not None
        assert renderer.logger is not None

    def test_init_with_logger(self):
        """Test renderer initialization with custom logger."""
        import logging

        logger = logging.getLogger("test")
        renderer = InfoYamlRenderer(logger=logger)
        assert renderer.logger == logger


class TestFormatProjectName:
    """Test project name formatting with issue tracker links."""

    def test_format_project_name_no_issue_tracker(self, renderer, sample_project):
        """Test formatting when no issue tracker is configured."""
        sample_project.issue_tracking = IssueTracking()
        result = renderer._format_project_name(sample_project)
        assert result == "Test Project"
        assert "<a href=" not in result

    def test_format_project_name_valid_url(self, renderer, sample_project):
        """Test formatting with valid issue tracker URL."""
        result = renderer._format_project_name(sample_project)
        assert '<a href="https://jira.example.com/projects/TEST"' in result
        assert 'target="_blank"' in result
        assert "Test Project" in result

    def test_format_project_name_invalid_url(self, renderer, sample_project):
        """Test formatting with invalid issue tracker URL."""
        sample_project.issue_tracking = IssueTracking(
            type="jira",
            url="https://broken.example.com",
            is_valid=False,
            validation_error="Connection timeout",
        )
        result = renderer._format_project_name(sample_project)
        assert 'style="color: red;"' in result
        assert "Connection timeout" in result
        assert "Test Project" in result


class TestFormatProjectLead:
    """Test project lead formatting with activity colors."""

    def test_format_project_lead_not_in_committers(self, renderer, sample_project):
        """Test formatting when project lead is not in committers list."""
        sample_project.project_lead = PersonInfo(
            name="David Unknown",
            email="david@example.com",
            company="Delta Corp",
        )
        result = renderer._format_project_lead(sample_project)
        assert "David Unknown" in result
        assert "color: gray" in result
        assert "Unknown activity status" in result

    def test_format_project_lead_green(self, renderer, sample_project):
        """Test formatting for currently active project lead."""
        result = renderer._format_project_lead(sample_project)
        assert "Alice Active" in result
        assert "color: green" in result
        assert "✅ Current" in result

    def test_format_project_lead_no_lead(self, renderer, sample_project):
        """Test formatting when no project lead is set."""
        sample_project.project_lead = None
        result = renderer._format_project_lead(sample_project)
        assert "Unknown" in result
        assert "color: gray" in result


class TestFormatCommitters:
    """Test committers list formatting."""

    def test_format_committers_excludes_lead(self, renderer, sample_project):
        """Test that project lead is excluded from committers list."""
        result = renderer._format_committers(sample_project)
        assert "Alice Active" not in result
        assert "Bob Moderate" in result
        assert "Charlie Inactive" in result

    def test_format_committers_color_coding(self, renderer, sample_project):
        """Test that committers are color-coded correctly."""
        result = renderer._format_committers(sample_project)
        assert "color: orange" in result  # Bob
        assert "color: red" in result  # Charlie
        assert "<br>" in result  # Multiple committers separated

    def test_format_committers_none(self, renderer, sample_project):
        """Test formatting when no committers besides lead."""
        sample_project.committers = [sample_project.committers[0]]  # Only Alice (lead)
        result = renderer._format_committers(sample_project)
        assert result == "None"

    def test_format_committers_no_lead(self, renderer, sample_project):
        """Test formatting when no project lead is set."""
        sample_project.project_lead = None
        result = renderer._format_committers(sample_project)
        assert "Alice Active" in result
        assert "Bob Moderate" in result
        assert "Charlie Inactive" in result


class TestFormatPersonWithColor:
    """Test person formatting with activity colors."""

    def test_format_person_green(self, renderer, sample_committers):
        """Test formatting for green (current) activity."""
        result = renderer._format_person_with_color(sample_committers[0])
        assert "Alice Active" in result
        assert "color: green" in result
        assert "✅ Current" in result
        assert "365 days" in result

    def test_format_person_orange(self, renderer, sample_committers):
        """Test formatting for orange (active) activity."""
        result = renderer._format_person_with_color(sample_committers[1])
        assert "Bob Moderate" in result
        assert "color: orange" in result
        assert "☑️ Active" in result
        assert "365-1095 days" in result

    def test_format_person_red(self, renderer, sample_committers):
        """Test formatting for red (inactive) activity."""
        result = renderer._format_person_with_color(sample_committers[2])
        assert "Charlie Inactive" in result
        assert "color: red" in result
        assert "🛑 Inactive" in result
        assert "1095+ days" in result

    def test_format_person_gray(self, renderer):
        """Test formatting for gray (unknown) activity."""
        committer = CommitterInfo(
            name="Unknown User",
            email="unknown@example.com",
            activity_status="unknown",
            activity_color="gray",
        )
        result = renderer._format_person_with_color(committer)
        assert "Unknown User" in result
        assert "color: gray" in result
        assert "Unknown activity status" in result


class TestGroupProjectsByServer:
    """Test project grouping by Gerrit server."""

    def test_group_projects_single_server(self, renderer, sample_project):
        """Test grouping with single server."""
        projects = [sample_project]
        grouped = renderer._group_projects_by_server(projects)
        assert len(grouped) == 1
        assert "gerrit.example.org" in grouped
        assert len(grouped["gerrit.example.org"]) == 1

    def test_group_projects_multiple_servers(self, renderer, sample_projects):
        """Test grouping with multiple servers."""
        grouped = renderer._group_projects_by_server(sample_projects)
        assert len(grouped) == 2
        assert "gerrit.example.org" in grouped
        assert "gerrit.other.org" in grouped
        assert len(grouped["gerrit.example.org"]) == 2
        assert len(grouped["gerrit.other.org"]) == 1

    def test_group_projects_empty_list(self, renderer):
        """Test grouping with empty project list."""
        grouped = renderer._group_projects_by_server([])
        assert grouped == {}


class TestCalculateLifecycleSummaries:
    """Test lifecycle summary calculation."""

    def test_calculate_summaries(self, renderer, sample_projects):
        """Test calculation with multiple lifecycle states."""
        summaries = renderer._calculate_lifecycle_summaries(sample_projects)
        assert len(summaries) == 3

        # Check sorting (by count descending)
        assert summaries[0].count >= summaries[1].count
        assert summaries[1].count >= summaries[2].count

        # Check percentages
        total_percentage = sum(s.percentage for s in summaries)
        assert abs(total_percentage - 100.0) < 0.1  # Allow for rounding

    def test_calculate_summaries_single_state(self, renderer, sample_project):
        """Test calculation with single lifecycle state."""
        projects = [sample_project]
        summaries = renderer._calculate_lifecycle_summaries(projects)
        assert len(summaries) == 1
        assert summaries[0].state == "Active"
        assert summaries[0].count == 1
        assert summaries[0].percentage == 100.0

    def test_calculate_summaries_empty_list(self, renderer):
        """Test calculation with empty project list."""
        summaries = renderer._calculate_lifecycle_summaries([])
        assert summaries == []

    def test_calculate_summaries_validation(self, renderer, sample_projects):
        """Test that LifecycleSummary objects are valid."""
        summaries = renderer._calculate_lifecycle_summaries(sample_projects)
        for summary in summaries:
            assert isinstance(summary, LifecycleSummary)
            assert summary.count >= 0
            assert 0 <= summary.percentage <= 100


class TestRenderCommitterTable:
    """Test committer table rendering."""

    def test_render_committer_table(self, renderer, sample_projects):
        """Test rendering committer table with multiple projects."""
        lines = renderer._render_committer_table(sample_projects)
        assert len(lines) > 2  # Header + separator + data rows

        # Check header
        assert "| Project |" in lines[0]
        assert "| Creation Date |" in lines[0]
        assert "| Lifecycle State |" in lines[0]
        assert "| Project Lead |" in lines[0]
        assert "| Committers |" in lines[0]

        # Check separator
        assert "|------" in lines[1]

        # Check that all projects are included
        table_content = "\n".join(lines)
        assert "Test Project" in table_content
        assert "Another Project" in table_content
        assert "Archived Project" in table_content

    def test_render_committer_table_empty(self, renderer):
        """Test rendering with empty project list."""
        lines = renderer._render_committer_table([])
        assert len(lines) == 2  # Only header and separator


class TestRenderCommitterReportMarkdown:
    """Test full committer report rendering."""

    def test_render_report_basic(self, renderer, sample_projects):
        """Test basic report rendering."""
        result = renderer.render_committer_report_markdown(sample_projects)
        assert result
        assert "## 📋 Committer INFO.yaml Report" in result
        assert "This report shows project information" in result
        assert "Test Project" in result
        assert "Another Project" in result

    def test_render_report_empty(self, renderer):
        """Test rendering with empty project list."""
        result = renderer.render_committer_report_markdown([])
        assert result == ""

    def test_render_report_sorted(self, renderer, sample_projects):
        """Test that projects are sorted by name."""
        result = renderer.render_committer_report_markdown(sample_projects)
        # Find positions of project names
        pos_another = result.find("Another Project")
        pos_archived = result.find("Archived Project")
        pos_test = result.find("Test Project")

        # Check alphabetical order
        assert pos_another < pos_archived < pos_test

    def test_render_report_grouped_by_server(self, renderer, sample_projects):
        """Test report rendering grouped by server."""
        result = renderer.render_committer_report_markdown(sample_projects, group_by_server=True)
        assert result
        assert "### gerrit.example.org" in result
        assert "### gerrit.other.org" in result


class TestRenderLifecycleSummaryMarkdown:
    """Test lifecycle summary rendering."""

    def test_render_summary_basic(self, renderer, sample_projects):
        """Test basic summary rendering."""
        result = renderer.render_lifecycle_summary_markdown(sample_projects)
        assert result
        assert "### Lifecycle State Summary" in result
        assert "| Lifecycle State |" in result
        assert "**Total Projects:** 3" in result

    def test_render_summary_empty(self, renderer):
        """Test rendering with empty project list."""
        result = renderer.render_lifecycle_summary_markdown([])
        assert result == ""

    def test_render_summary_percentages(self, renderer, sample_projects):
        """Test that percentages are calculated correctly."""
        result = renderer.render_lifecycle_summary_markdown(sample_projects)
        # Each state should appear once with 33.3%
        assert "33.3%" in result or "33.4%" in result


class TestRenderFullReportMarkdown:
    """Test full report rendering with both sections."""

    def test_render_full_report(self, renderer, sample_projects):
        """Test rendering complete report."""
        result = renderer.render_full_report_markdown(sample_projects)
        assert result
        assert "## 📋 Committer INFO.yaml Report" in result
        assert "### Lifecycle State Summary" in result
        assert "Test Project" in result
        assert "**Total Projects:**" in result

    def test_render_full_report_empty(self, renderer):
        """Test rendering with empty project list."""
        result = renderer.render_full_report_markdown([])
        assert result == ""

    def test_render_full_report_grouped(self, renderer, sample_projects):
        """Test full report with server grouping."""
        result = renderer.render_full_report_markdown(sample_projects, group_by_server=True)
        assert result
        assert "### gerrit.example.org" in result
        assert "### gerrit.other.org" in result
        assert "### Lifecycle State Summary" in result


class TestBuildTemplateContext:
    """Test template context building."""

    def test_build_context_basic(self, renderer, sample_projects):
        """Test basic context building."""
        context = renderer.build_template_context(sample_projects)
        assert context is not None
        assert "projects" in context
        assert "total_projects" in context
        assert "lifecycle_summaries" in context
        assert context["total_projects"] == 3
        assert len(context["projects"]) == 3
        assert len(context["lifecycle_summaries"]) == 3

    def test_build_context_empty(self, renderer):
        """Test context building with empty project list."""
        context = renderer.build_template_context([])
        assert context["total_projects"] == 0
        assert context["projects"] == []
        assert context["lifecycle_summaries"] == []

    def test_build_context_grouped(self, renderer, sample_projects):
        """Test context building with server grouping."""
        context = renderer.build_template_context(sample_projects, group_by_server=True)
        assert context["group_by_server"] is True
        assert "projects_by_server" in context
        assert len(context["projects_by_server"]) == 2
        assert "gerrit.example.org" in context["projects_by_server"]
        assert "gerrit.other.org" in context["projects_by_server"]

    def test_build_context_not_grouped(self, renderer, sample_projects):
        """Test context building without server grouping."""
        context = renderer.build_template_context(sample_projects, group_by_server=False)
        assert context["group_by_server"] is False
        assert "projects_by_server" not in context

    def test_build_context_serializable(self, renderer, sample_projects):
        """Test that context is JSON-serializable."""
        import json

        context = renderer.build_template_context(sample_projects)
        # Should not raise exception
        json_str = json.dumps(context)
        assert json_str


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_project_with_no_committers(self, renderer):
        """Test rendering project with no committers."""
        project = ProjectInfo(
            project_name="Empty Project",
            gerrit_server="gerrit.example.org",
            project_path="testorg/empty",
            full_path="gerrit.example.org/testorg/empty",
            creation_date="2023-01-01",
            lifecycle_state="Active",
            project_lead=PersonInfo(name="Lead Person", email="lead@example.com"),
            committers=[],
        )
        result = renderer.render_committer_report_markdown([project])
        assert "Empty Project" in result
        assert "None" in result  # No committers

    def test_project_with_many_committers(self, renderer):
        """Test rendering project with many committers."""
        committers = [
            CommitterInfo(
                name=f"Committer {i}",
                email=f"committer{i}@example.com",
                activity_status="current",
                activity_color="green",
            )
            for i in range(50)
        ]
        project = ProjectInfo(
            project_name="Large Project",
            gerrit_server="gerrit.example.org",
            project_path="testorg/large",
            full_path="gerrit.example.org/testorg/large",
            creation_date="2023-01-01",
            lifecycle_state="Active",
            project_lead=PersonInfo(name="Lead Person", email="lead@example.com"),
            committers=committers,
        )
        result = renderer.render_committer_report_markdown([project])
        assert "Large Project" in result
        # Check that multiple committers are joined with <br>
        assert result.count("<br>") >= 40

    def test_special_characters_in_names(self, renderer):
        """Test handling of special characters in names."""
        project = ProjectInfo(
            project_name="Test & Project <Special>",
            gerrit_server="gerrit.example.org",
            project_path="testorg/special",
            full_path="gerrit.example.org/testorg/special",
            creation_date="2023-01-01",
            lifecycle_state="Active",
            project_lead=PersonInfo(name="O'Brien & Associates", email="obrien@example.com"),
            committers=[
                CommitterInfo(
                    name="O'Brien & Associates",
                    email="obrien@example.com",
                    activity_status="current",
                    activity_color="green",
                )
            ],
        )
        result = renderer.render_committer_report_markdown([project])
        assert "Test & Project <Special>" in result
        assert "O'Brien & Associates" in result
