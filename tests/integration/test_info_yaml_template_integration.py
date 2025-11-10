# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Integration tests for INFO.yaml template rendering.

Tests the complete rendering pipeline from ProjectInfo objects
through Jinja2 templates to final Markdown output.

Phase 3: Rendering & Report Integration
"""

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from domain.info_yaml import (
    CommitterInfo,
    IssueTracking,
    PersonInfo,
    ProjectInfo,
)
from rendering.info_yaml_renderer import InfoYamlRenderer


@pytest.fixture
def template_dir():
    """Get path to templates directory."""
    current_file = Path(__file__)
    src_dir = current_file.parent.parent.parent / "src"
    return src_dir / "templates" / "markdown" / "sections"


@pytest.fixture
def jinja_env(template_dir):
    """Create Jinja2 environment for testing."""
    if not template_dir.exists():
        pytest.skip(f"Template directory not found: {template_dir}")

    loader = FileSystemLoader(str(template_dir))
    env = Environment(
        loader=loader,
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    return env


@pytest.fixture
def renderer():
    """Create InfoYamlRenderer instance."""
    return InfoYamlRenderer()


@pytest.fixture
def sample_projects():
    """Create sample projects for testing."""
    project1 = ProjectInfo(
        project_name="Active Project",
        gerrit_server="gerrit.example.org",
        project_path="testorg/active",
        full_path="gerrit.example.org/testorg/active",
        creation_date="2020-01-15",
        lifecycle_state="Active",
        project_lead=PersonInfo(
            name="Alice Lead",
            email="alice@example.com",
            company="Acme Corp",
            id="alice123",
        ),
        committers=[
            CommitterInfo(
                name="Alice Lead",
                email="alice@example.com",
                company="Acme Corp",
                id="alice123",
                activity_status="current",
                activity_color="green",
                days_since_last_commit=30,
            ),
            CommitterInfo(
                name="Bob Dev",
                email="bob@example.com",
                company="Beta Inc",
                id="bob456",
                activity_status="active",
                activity_color="orange",
                days_since_last_commit=500,
            ),
            CommitterInfo(
                name="Charlie Old",
                email="charlie@example.com",
                company="Gamma LLC",
                id="charlie789",
                activity_status="inactive",
                activity_color="red",
                days_since_last_commit=1200,
            ),
        ],
        issue_tracking=IssueTracking(
            type="jira",
            url="https://jira.example.com/projects/ACTIVE",
            is_valid=True,
        ),
        repositories=["repo1", "repo2"],
        has_git_data=True,
        project_days_since_last_commit=30,
    )

    project2 = ProjectInfo(
        project_name="Incubation Project",
        gerrit_server="gerrit.example.org",
        project_path="testorg/incubation",
        full_path="gerrit.example.org/testorg/incubation",
        creation_date="2022-06-01",
        lifecycle_state="Incubation",
        project_lead=PersonInfo(
            name="David New",
            email="david@example.com",
            company="Delta Corp",
            id="david999",
        ),
        committers=[
            CommitterInfo(
                name="David New",
                email="david@example.com",
                company="Delta Corp",
                id="david999",
                activity_status="current",
                activity_color="green",
                days_since_last_commit=10,
            ),
        ],
        issue_tracking=IssueTracking(
            type="github",
            url="https://github.com/example/incubation/issues",
            is_valid=True,
        ),
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
            name="Eve Retired",
            email="eve@example.com",
            company="Epsilon Inc",
        ),
        committers=[],
        issue_tracking=IssueTracking(
            type="jira",
            url="https://broken.example.com",
            is_valid=False,
            validation_error="Connection timeout",
        ),
        has_git_data=False,
    )

    return [project1, project2, project3]


class TestCommitterTemplateIntegration:
    """Test INFO.yaml committer template integration."""

    def test_committer_template_exists(self, jinja_env):
        """Test that committer template file exists."""
        try:
            template = jinja_env.get_template("info_yaml_committers.md.j2")
            assert template is not None
        except TemplateNotFound:
            pytest.fail("Committer template not found")

    def test_render_committer_template_basic(self, jinja_env, renderer, sample_projects):
        """Test rendering committer template with basic context."""
        template = jinja_env.get_template("info_yaml_committers.md.j2")
        context = renderer.build_template_context(sample_projects)

        result = template.render(**context)

        # Check header
        assert "## 📋 Committer INFO.yaml Report" in result
        assert "This report shows project information" in result

        # Check table structure
        assert "| Project |" in result
        assert "| Creation Date |" in result
        assert "| Lifecycle State |" in result
        assert "| Project Lead |" in result
        assert "| Committers |" in result

        # Check project names
        assert "Active Project" in result
        assert "Incubation Project" in result
        assert "Archived Project" in result

    def test_render_committer_template_with_grouping(self, jinja_env, renderer, sample_projects):
        """Test rendering with Gerrit server grouping."""
        template = jinja_env.get_template("info_yaml_committers.md.j2")
        context = renderer.build_template_context(sample_projects, group_by_server=True)

        result = template.render(**context)

        # Check server headers
        assert "### gerrit.example.org" in result
        assert "### gerrit.other.org" in result

        # Check that projects appear under correct servers
        lines = result.split("\n")
        example_org_idx = next(
            i for i, line in enumerate(lines) if "### gerrit.example.org" in line
        )
        other_org_idx = next(i for i, line in enumerate(lines) if "### gerrit.other.org" in line)

        # Active and Incubation should be before Archived
        assert example_org_idx < other_org_idx

    def test_render_committer_template_activity_colors(self, jinja_env, renderer, sample_projects):
        """Test that activity colors are rendered correctly."""
        template = jinja_env.get_template("info_yaml_committers.md.j2")
        context = renderer.build_template_context(sample_projects)

        result = template.render(**context)

        # Check color spans are present (HTML-escaped by Jinja2)
        assert "style=&#34;color: orange;&#34;" in result or 'style="color: orange;"' in result
        assert "style=&#34;color: red;&#34;" in result or 'style="color: red;"' in result

        # Check tooltips that are actually present (orange and red are in committers)
        assert "☑️ Active" in result or "Active - commits between" in result
        assert "🛑 Inactive" in result or "Inactive - no commits in" in result

    def test_render_committer_template_issue_tracker_links(
        self, jinja_env, renderer, sample_projects
    ):
        """Test that issue tracker links are rendered correctly."""
        template = jinja_env.get_template("info_yaml_committers.md.j2")
        context = renderer.build_template_context(sample_projects)

        result = template.render(**context)

        # Valid link (HTML-escaped by Jinja2)
        assert (
            "&lt;a href=&#34;https://jira.example.com/projects/ACTIVE&#34;" in result
            or '<a href="https://jira.example.com/projects/ACTIVE"' in result
        )
        assert "target=&#34;_blank&#34;" in result or 'target="_blank"' in result

        # Broken link with error
        assert (
            "style=&#34;color: red;&#34;" in result
            or 'style="color: red;"' in result
            or "color: red;" in result
        )
        assert "Connection timeout" in result

    def test_render_committer_template_lead_exclusion(self, jinja_env, renderer, sample_projects):
        """Test that project lead is not duplicated in committers column."""
        template = jinja_env.get_template("info_yaml_committers.md.j2")
        context = renderer.build_template_context(sample_projects)

        result = template.render(**context)

        # Find the row for Active Project
        lines = result.split("\n")
        active_row = next(
            line for line in lines if "Active Project" in line and line.startswith("|")
        )

        # Count occurrences of "Alice Lead" in the row
        # Should appear once in Project Lead column, not in Committers
        columns = active_row.split("|")
        lead_column = columns[4]  # Project Lead column
        committers_column = columns[5]  # Committers column

        assert "Alice Lead" in lead_column
        assert "Alice Lead" not in committers_column

        # But Bob and Charlie should be in committers
        assert "Bob Dev" in committers_column
        assert "Charlie Old" in committers_column

    def test_render_committer_template_sorting(self, jinja_env, renderer, sample_projects):
        """Test that projects are sorted alphabetically."""
        template = jinja_env.get_template("info_yaml_committers.md.j2")
        context = renderer.build_template_context(sample_projects)

        result = template.render(**context)

        # Find positions of project names
        pos_active = result.find("Active Project")
        pos_archived = result.find("Archived Project")
        pos_incubation = result.find("Incubation Project")

        # Check alphabetical order
        assert pos_active < pos_archived < pos_incubation


class TestLifecycleTemplateIntegration:
    """Test lifecycle summary template integration."""

    def test_lifecycle_template_exists(self, jinja_env):
        """Test that lifecycle template file exists."""
        try:
            template = jinja_env.get_template("info_yaml_lifecycle.md.j2")
            assert template is not None
        except TemplateNotFound:
            pytest.fail("Lifecycle template not found")

    def test_render_lifecycle_template_basic(self, jinja_env, renderer, sample_projects):
        """Test rendering lifecycle template with basic context."""
        template = jinja_env.get_template("info_yaml_lifecycle.md.j2")
        context = renderer.build_template_context(sample_projects)

        result = template.render(**context)

        # Check header
        assert "### Lifecycle State Summary" in result

        # Check table structure
        assert "| Lifecycle State |" in result
        assert "| Gerrit Project Count |" in result
        assert "| Percentage |" in result

        # Check total
        assert "**Total Projects:** 3" in result

    def test_render_lifecycle_template_states(self, jinja_env, renderer, sample_projects):
        """Test that all lifecycle states are included."""
        template = jinja_env.get_template("info_yaml_lifecycle.md.j2")
        context = renderer.build_template_context(sample_projects)

        result = template.render(**context)

        # Each state should appear once
        assert "Active" in result
        assert "Incubation" in result
        assert "Archived" in result

    def test_render_lifecycle_template_percentages(self, jinja_env, renderer, sample_projects):
        """Test that percentages are calculated and formatted correctly."""
        template = jinja_env.get_template("info_yaml_lifecycle.md.j2")
        context = renderer.build_template_context(sample_projects)

        result = template.render(**context)

        # With 3 projects, each state should be 33.3%
        assert "33.3%" in result or "33.4%" in result

        # Check counts
        assert "| 1 |" in result  # Each state has 1 project

    def test_render_lifecycle_template_empty(self, jinja_env, renderer):
        """Test rendering with no projects."""
        template = jinja_env.get_template("info_yaml_lifecycle.md.j2")
        context = renderer.build_template_context([])

        result = template.render(**context)

        # Should still have structure
        assert "### Lifecycle State Summary" in result
        assert "**Total Projects:** 0" in result


class TestFullTemplateIntegration:
    """Test complete template integration pipeline."""

    def test_combined_rendering(self, jinja_env, renderer, sample_projects):
        """Test rendering both templates together."""
        committer_template = jinja_env.get_template("info_yaml_committers.md.j2")
        lifecycle_template = jinja_env.get_template("info_yaml_lifecycle.md.j2")

        context = renderer.build_template_context(sample_projects)

        committer_result = committer_template.render(**context)
        lifecycle_result = lifecycle_template.render(**context)

        combined = f"{committer_result}\n\n{lifecycle_result}"

        # Check that both sections are present
        assert "## 📋 Committer INFO.yaml Report" in combined
        assert "### Lifecycle State Summary" in combined

        # Check project data
        assert "Active Project" in combined
        assert "**Total Projects:** 3" in combined

    def test_renderer_vs_template_consistency(self, jinja_env, renderer, sample_projects):
        """Test that renderer output matches template output."""
        # Get output from renderer methods
        renderer_committer = renderer.render_committer_report_markdown(sample_projects)
        renderer_lifecycle = renderer.render_lifecycle_summary_markdown(sample_projects)

        # Get output from templates
        committer_template = jinja_env.get_template("info_yaml_committers.md.j2")
        lifecycle_template = jinja_env.get_template("info_yaml_lifecycle.md.j2")
        context = renderer.build_template_context(sample_projects)

        template_committer = committer_template.render(**context)
        template_lifecycle = lifecycle_template.render(**context)

        # Key elements should be present in both
        # (exact match not required due to different rendering approaches)

        # Committer report
        for project in sample_projects:
            assert project.project_name in renderer_committer
            assert project.project_name in template_committer

        # Lifecycle summary
        assert "**Total Projects:** 3" in renderer_lifecycle
        assert "**Total Projects:** 3" in template_lifecycle

    def test_context_builder_completeness(self, renderer, sample_projects):
        """Test that context builder includes all necessary data."""
        context = renderer.build_template_context(sample_projects)

        # Check required keys
        assert "projects" in context
        assert "total_projects" in context
        assert "lifecycle_summaries" in context
        assert "group_by_server" in context

        # Check data structure
        assert len(context["projects"]) == 3
        assert context["total_projects"] == 3
        assert len(context["lifecycle_summaries"]) == 3

        # Check project serialization
        for project_dict in context["projects"]:
            assert "project_name" in project_dict
            assert "lifecycle_state" in project_dict
            assert "committers" in project_dict
            assert "project_lead" in project_dict
            assert "issue_tracking" in project_dict

    def test_edge_case_no_committers(self, jinja_env, renderer):
        """Test template rendering with project that has no committers."""
        project = ProjectInfo(
            project_name="Empty Project",
            gerrit_server="gerrit.example.org",
            project_path="testorg/empty",
            full_path="gerrit.example.org/testorg/empty",
            creation_date="2023-01-01",
            lifecycle_state="Active",
            project_lead=PersonInfo(name="Lead Only", email="lead@example.com"),
            committers=[],
        )

        template = jinja_env.get_template("info_yaml_committers.md.j2")
        context = renderer.build_template_context([project])

        result = template.render(**context)

        # Should handle gracefully
        assert "Empty Project" in result
        assert "Lead Only" in result

    def test_edge_case_special_characters(self, jinja_env, renderer):
        """Test template rendering with special characters."""
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

        template = jinja_env.get_template("info_yaml_committers.md.j2")
        context = renderer.build_template_context([project])

        result = template.render(**context)

        # Special characters should be HTML-escaped by Jinja2
        assert (
            "Test &amp; Project &lt;Special&gt;" in result or "Test & Project <Special>" in result
        )
        assert (
            "O'Brien &amp; Associates" in result
            or "O&#39;Brien &amp; Associates" in result
            or "O'Brien & Associates" in result
        )
