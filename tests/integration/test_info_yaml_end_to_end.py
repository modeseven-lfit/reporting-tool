# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
End-to-end integration tests for INFO.yaml feature.

Tests complete workflows from collection through enrichment to rendering,
validating the entire INFO.yaml pipeline.

Phase 5: Comprehensive Testing
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from domain.info_yaml import ProjectInfo
from rendering.info_yaml_renderer import InfoYamlRenderer
from reporting_tool.collectors.info_yaml import INFOYamlCollector, InfoYamlEnricher


@pytest.fixture
def temp_info_master():
    """Create temporary info-master directory structure."""
    temp_dir = tempfile.mkdtemp()
    info_master = Path(temp_dir) / "info-master"
    info_master.mkdir()

    # Create gerrit server directories
    gerrit1 = info_master / "gerrit.example.org"
    gerrit1.mkdir()

    gerrit2 = info_master / "gerrit.other.org"
    gerrit2.mkdir()

    yield info_master

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_info_yaml_content():
    """Sample INFO.yaml content."""
    return """---
project: 'test-project'
project_creation_date: '2020-01-15'
lifecycle_state: 'Active'
project_lead:
    name: 'Alice Lead'
    email: 'alice@example.com'
    company: 'Acme Corp'
    id: 'alice123'
    timezone: 'America/Los_Angeles'
committers:
    - name: 'Alice Lead'
      email: 'alice@example.com'
      company: 'Acme Corp'
      id: 'alice123'
      timezone: 'America/Los_Angeles'
    - name: 'Bob Developer'
      email: 'bob@example.com'
      company: 'Beta Inc'
      id: 'bob456'
      timezone: 'America/New_York'
    - name: 'Charlie Contributor'
      email: 'charlie@example.com'
      company: 'Gamma LLC'
      id: 'charlie789'
      timezone: 'Europe/London'
issue_tracking:
    type: 'jira'
    url: 'https://jira.example.com/projects/TEST'
repositories:
    - 'test-repo-1'
    - 'test-repo-2'
"""


@pytest.fixture
def create_test_projects(temp_info_master, sample_info_yaml_content):
    """Create test INFO.yaml files."""
    # Project 1: Active project
    project1_yaml = sample_info_yaml_content.replace(
        "project: 'test-project'", "project: 'active-project'"
    )
    project1_dir = temp_info_master / "gerrit.example.org" / "active-project"
    project1_dir.mkdir(parents=True)
    (project1_dir / "INFO.yaml").write_text(project1_yaml)

    # Project 2: Incubation project
    project2_yaml = sample_info_yaml_content.replace(
        "project: 'test-project'", "project: 'incubation-project'"
    ).replace("lifecycle_state: 'Active'", "lifecycle_state: 'Incubation'")
    project2_dir = temp_info_master / "gerrit.example.org" / "incubation-project"
    project2_dir.mkdir(parents=True)
    (project2_dir / "INFO.yaml").write_text(project2_yaml)

    # Project 3: Archived project (different server)
    project3_yaml = sample_info_yaml_content.replace(
        "project: 'test-project'", "project: 'archived-project'"
    ).replace("lifecycle_state: 'Active'", "lifecycle_state: 'Archived'")
    project3_dir = temp_info_master / "gerrit.other.org" / "archived-project"
    project3_dir.mkdir(parents=True)
    (project3_dir / "INFO.yaml").write_text(project3_yaml)

    return temp_info_master


@pytest.fixture
def sample_git_metrics():
    """Create sample Git metrics for enrichment."""
    # Create author metrics with varying activity levels using time-windowed metrics
    # Structure matches GitDataCollector output format

    # Repository 1: test-repo-1 (current activity)
    repo1_metrics = {
        "repository": {
            "gerrit_project": "test-repo-1",
            "gerrit_host": "gerrit.example.org",
            "gerrit_url": "https://gerrit.example.org/test-repo-1",
            "local_path": "/tmp/test-repo-1",
            "last_commit_timestamp": "2025-01-01T00:00:00Z",
            "days_since_last_commit": 30,
            "activity_status": "current",
            "has_any_commits": True,
            "total_commits_ever": 250,
            "commit_counts": {"1y": 150, "90d": 50, "30d": 20},
            "loc_stats": {
                "1y": {"added": 5000, "removed": 2000, "net": 3000},
                "90d": {"added": 1500, "removed": 600, "net": 900},
                "30d": {"added": 500, "removed": 200, "net": 300},
            },
            "unique_contributors": {"1y": 3, "90d": 2, "30d": 1},
            "features": {},
        },
        "authors": {
            "alice@example.com": {
                "name": "Alice Lead",
                "email": "alice@example.com",
                "commits": {"1y": 150, "90d": 50, "30d": 20},
                "lines_added": {"1y": 5000, "90d": 1500, "30d": 500},
                "lines_removed": {"1y": 2000, "90d": 600, "30d": 200},
                "lines_net": {"1y": 3000, "90d": 900, "30d": 300},
                "repositories_touched": {"1y": 1, "90d": 1, "30d": 1},
            },
            "bob@example.com": {
                "name": "Bob Developer",
                "email": "bob@example.com",
                "commits": {"1y": 0, "90d": 0, "30d": 0},
                "lines_added": {"1y": 0, "90d": 0, "30d": 0},
                "lines_removed": {"1y": 0, "90d": 0, "30d": 0},
                "lines_net": {"1y": 0, "90d": 0, "30d": 0},
                "repositories_touched": {"1y": 0, "90d": 0, "30d": 0},
            },
        },
        "errors": [],
    }

    # Repository 2: test-repo-2 (active)
    repo2_metrics = {
        "repository": {
            "gerrit_project": "test-repo-2",
            "gerrit_host": "gerrit.example.org",
            "gerrit_url": "https://gerrit.example.org/test-repo-2",
            "local_path": "/tmp/test-repo-2",
            "last_commit_timestamp": "2024-06-01T00:00:00Z",
            "days_since_last_commit": 500,
            "activity_status": "active",
            "has_any_commits": True,
            "total_commits_ever": 100,
            "commit_counts": {"1y": 50, "90d": 10, "30d": 5},
            "loc_stats": {
                "1y": {"added": 2000, "removed": 800, "net": 1200},
                "90d": {"added": 500, "removed": 200, "net": 300},
                "30d": {"added": 200, "removed": 100, "net": 100},
            },
            "unique_contributors": {"1y": 2, "90d": 1, "30d": 1},
            "features": {},
        },
        "authors": {
            "bob@example.com": {
                "name": "Bob Developer",
                "email": "bob@example.com",
                "commits": {"1y": 50, "90d": 10, "30d": 5},
                "lines_added": {"1y": 2000, "90d": 500, "30d": 200},
                "lines_removed": {"1y": 800, "90d": 200, "30d": 100},
                "lines_net": {"1y": 1200, "90d": 300, "30d": 100},
                "repositories_touched": {"1y": 1, "90d": 1, "30d": 1},
            },
        },
        "errors": [],
    }

    return [repo1_metrics, repo2_metrics]


@pytest.fixture
def base_config():
    """Base configuration for tests."""
    return {
        "info_yaml": {
            "enabled": True,
            "cache_enabled": False,  # Disable for testing
            "enrich_with_git_data": True,
            "validate_urls": False,  # Skip URL validation in tests
            "disable_archived_reports": False,  # Include archived for testing
            "activity_windows": {
                "current": 365,
                "active": 1095,
            },
        }
    }


class TestEndToEndBasicWorkflow:
    """Test basic end-to-end workflow."""

    def test_complete_workflow_without_enrichment(self, create_test_projects, base_config):
        """Test complete workflow without enrichment."""
        # Disable enrichment
        config = base_config.copy()
        config["info_yaml"]["enrich_with_git_data"] = False

        # Step 1: Collection
        collector = INFOYamlCollector(config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        assert len(projects) == 3
        assert all(isinstance(p, ProjectInfo) for p in projects)

        # Step 2: Rendering (without enrichment)
        renderer = InfoYamlRenderer()
        markdown = renderer.render_full_report_markdown(projects)

        assert markdown
        assert "## 📋 Committer INFO.yaml Report" in markdown
        assert "### Lifecycle State Summary" in markdown
        assert "test-project" in markdown or "active-project" in markdown

    def test_complete_workflow_with_enrichment(
        self, create_test_projects, base_config, sample_git_metrics
    ):
        """Test complete workflow with Git data enrichment."""
        # Step 1: Collection
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        assert len(projects) == 3

        # Step 2: Enrichment
        enricher = InfoYamlEnricher(
            activity_windows=base_config["info_yaml"]["activity_windows"],
            validate_urls=False,
        )
        enriched_projects = enricher.enrich_projects(projects, sample_git_metrics)

        assert len(enriched_projects) == 3

        # Verify enrichment occurred
        active_project = next(
            (p for p in enriched_projects if "active" in p.project_name.lower()), None
        )
        assert active_project is not None
        assert active_project.has_git_data

        # Check committer activity colors
        committers_with_colors = [
            c for c in active_project.committers if c.activity_color != "gray"
        ]
        assert len(committers_with_colors) > 0

        # Step 3: Rendering
        renderer = InfoYamlRenderer()
        markdown = renderer.render_full_report_markdown(enriched_projects)

        assert markdown
        assert "color: green" in markdown or "color: orange" in markdown

    def test_workflow_with_server_grouping(self, create_test_projects, base_config):
        """Test workflow with Gerrit server grouping."""
        # Collection
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        # Rendering with grouping
        renderer = InfoYamlRenderer()
        markdown = renderer.render_full_report_markdown(projects, group_by_server=True)

        assert markdown
        assert "### gerrit.example.org" in markdown
        assert "### gerrit.other.org" in markdown


class TestEndToEndDataFlow:
    """Test data flow and transformations."""

    def test_data_integrity_through_pipeline(
        self, create_test_projects, base_config, sample_git_metrics
    ):
        """Verify data integrity through entire pipeline."""
        # Collection
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        collected = [ProjectInfo.from_dict(p) for p in result["projects"]]

        # Store original data
        original_names = {p.project_name for p in collected}
        original_states = {p.lifecycle_state for p in collected}

        # Enrichment
        enricher = InfoYamlEnricher(
            activity_windows=base_config["info_yaml"]["activity_windows"],
            validate_urls=False,
        )
        enriched = enricher.enrich_projects(collected, sample_git_metrics)

        # Verify no data loss
        enriched_names = {p.project_name for p in enriched}
        enriched_states = {p.lifecycle_state for p in enriched}

        assert original_names == enriched_names
        assert original_states == enriched_states

        # Verify enrichment added data
        for project in enriched:
            if any(c.email in ["alice@example.com", "bob@example.com"] for c in project.committers):
                assert project.has_git_data

    def test_committer_activity_calculation(
        self, create_test_projects, base_config, sample_git_metrics
    ):
        """Test activity status calculation through pipeline."""
        # Full pipeline
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        enricher = InfoYamlEnricher(
            activity_windows=base_config["info_yaml"]["activity_windows"],
            validate_urls=False,
        )
        enriched = enricher.enrich_projects(projects, sample_git_metrics)

        # Find project with enriched data
        active_project = next((p for p in enriched if p.has_git_data), None)

        assert active_project is not None

        # Check activity colors
        committers = active_project.committers

        # All committers get the same color based on project-level activity
        # (not per-committer activity)
        colors = {c.activity_color for c in committers}
        assert len(colors) == 1  # All committers should have the same color
        assert "green" in colors  # Project has recent activity (< 365 days)


class TestEndToEndErrorHandling:
    """Test error handling through the pipeline."""

    def test_invalid_yaml_handling(self, temp_info_master, base_config):
        """Test handling of invalid YAML files."""
        # Create invalid YAML
        project_dir = temp_info_master / "gerrit.example.org" / "bad-project"
        project_dir.mkdir(parents=True)
        (project_dir / "INFO.yaml").write_text("invalid: yaml: content:")

        # Enable error continuation
        config = base_config.copy()
        config["info_yaml"]["continue_on_error"] = True
        config["info_yaml"]["skip_invalid_projects"] = True

        collector = INFOYamlCollector(config)
        result = collector.collect(temp_info_master)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        # Should not crash, may return empty list
        assert isinstance(projects, list)

    def test_missing_required_fields(self, temp_info_master, base_config):
        """Test handling of INFO.yaml with missing fields."""
        # Create minimal YAML (missing some fields)
        minimal_yaml = """---
project: 'minimal-project'
"""
        project_dir = temp_info_master / "gerrit.example.org" / "minimal-project"
        project_dir.mkdir(parents=True)
        (project_dir / "INFO.yaml").write_text(minimal_yaml)

        config = base_config.copy()
        config["info_yaml"]["skip_invalid_projects"] = True

        collector = INFOYamlCollector(config)
        result = collector.collect(temp_info_master)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        # Should handle gracefully
        assert isinstance(projects, list)

    def test_enrichment_with_no_git_data(self, create_test_projects, base_config):
        """Test enrichment when no Git data is available."""
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        # Enrich with empty Git metrics
        enricher = InfoYamlEnricher(
            activity_windows=base_config["info_yaml"]["activity_windows"],
            validate_urls=False,
        )
        enriched = enricher.enrich_projects(projects, [])

        # Should complete without errors
        assert len(enriched) == len(projects)

        # All committers should be gray (no Git data)
        for project in enriched:
            for committer in project.committers:
                assert committer.activity_color == "gray"


class TestEndToEndPerformance:
    """Test performance characteristics."""

    def test_small_dataset_performance(self, create_test_projects, base_config, sample_git_metrics):
        """Test performance with small dataset (3 projects)."""
        import time

        collector = INFOYamlCollector(base_config)

        start = time.time()
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]
        collection_time = time.time() - start

        enricher = InfoYamlEnricher(
            activity_windows=base_config["info_yaml"]["activity_windows"],
            validate_urls=False,
        )
        start = time.time()
        enriched = enricher.enrich_projects(projects, sample_git_metrics)
        enrichment_time = time.time() - start

        renderer = InfoYamlRenderer()
        start = time.time()
        markdown = renderer.render_full_report_markdown(enriched)
        rendering_time = time.time() - start

        # Verify reasonable performance
        assert collection_time < 5.0  # Should be very fast
        assert enrichment_time < 5.0
        assert rendering_time < 5.0

        # Verify output
        assert len(projects) == 3
        assert len(enriched) == 3
        assert len(markdown) > 0

    def test_repeated_processing(self, create_test_projects, base_config, sample_git_metrics):
        """Test repeated processing of same data."""
        collector = INFOYamlCollector(base_config)
        enricher = InfoYamlEnricher(
            activity_windows=base_config["info_yaml"]["activity_windows"],
            validate_urls=False,
        )
        renderer = InfoYamlRenderer()

        results = []
        for _ in range(3):
            result = collector.collect(create_test_projects)

            projects = [ProjectInfo.from_dict(p) for p in result["projects"]]
            enriched = enricher.enrich_projects(projects, sample_git_metrics)
            markdown = renderer.render_full_report_markdown(enriched)
            results.append((projects, enriched, markdown))

        # Verify consistent results
        assert all(len(r[0]) == 3 for r in results)
        assert all(len(r[1]) == 3 for r in results)
        assert all(len(r[2]) > 0 for r in results)


class TestEndToEndOutputFormats:
    """Test different output formats."""

    def test_markdown_output(self, create_test_projects, base_config):
        """Test Markdown output generation."""
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        renderer = InfoYamlRenderer()
        markdown = renderer.render_full_report_markdown(projects)

        # Verify Markdown structure
        assert "##" in markdown  # Headers
        assert "|" in markdown  # Tables
        assert "**" in markdown  # Bold text

    def test_json_context_output(self, create_test_projects, base_config):
        """Test JSON context building."""
        import json

        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        renderer = InfoYamlRenderer()
        context = renderer.build_template_context(projects)

        # Verify JSON serializable
        json_str = json.dumps(context)
        assert json_str

        # Verify structure
        assert "projects" in context
        assert "total_projects" in context
        assert "lifecycle_summaries" in context

    def test_separate_sections(self, create_test_projects, base_config):
        """Test rendering sections separately."""
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        renderer = InfoYamlRenderer()

        # Render sections separately
        committer_report = renderer.render_committer_report_markdown(projects)
        lifecycle_summary = renderer.render_lifecycle_summary_markdown(projects)

        # Verify both sections
        assert "Committer INFO.yaml Report" in committer_report
        assert "Lifecycle State Summary" in lifecycle_summary

        # Verify they're different
        assert committer_report != lifecycle_summary


class TestEndToEndEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_info_master(self, temp_info_master, base_config):
        """Test with empty info-master directory."""
        collector = INFOYamlCollector(base_config)
        result = collector.collect(temp_info_master)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        assert projects == []

        # Rendering should handle empty list
        renderer = InfoYamlRenderer()
        markdown = renderer.render_full_report_markdown(projects)
        assert markdown == ""

    def test_single_project(self, temp_info_master, sample_info_yaml_content, base_config):
        """Test with single project."""
        project_dir = temp_info_master / "gerrit.example.org" / "single-project"
        project_dir.mkdir(parents=True)
        (project_dir / "INFO.yaml").write_text(sample_info_yaml_content)

        collector = INFOYamlCollector(base_config)
        result = collector.collect(temp_info_master)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        assert len(projects) == 1

        renderer = InfoYamlRenderer()
        markdown = renderer.render_full_report_markdown(projects)

        assert "**Total Projects:** 1" in markdown

    def test_projects_with_no_committers(self, temp_info_master, base_config):
        """Test projects with no committers."""
        yaml_content = """---
project: 'no-committers-project'
project_creation_date: '2020-01-15'
lifecycle_state: 'Active'
project_lead:
    name: 'Lead Only'
    email: 'lead@example.com'
committers: []
"""
        project_dir = temp_info_master / "gerrit.example.org" / "no-committers"
        project_dir.mkdir(parents=True)
        (project_dir / "INFO.yaml").write_text(yaml_content)

        collector = INFOYamlCollector(base_config)
        result = collector.collect(temp_info_master)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        assert len(projects) == 1
        assert len(projects[0].committers) == 0

        renderer = InfoYamlRenderer()
        markdown = renderer.render_full_report_markdown(projects)

        # Should render without errors
        assert markdown
        assert "None" in markdown  # No committers


class TestEndToEndRealWorldScenarios:
    """Test real-world usage scenarios."""

    def test_filtered_by_lifecycle_state(self, create_test_projects, base_config):
        """Test filtering by lifecycle state."""
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        all_projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        # Filter to only active projects
        active_projects = [p for p in all_projects if p.lifecycle_state == "Active"]

        renderer = InfoYamlRenderer()
        markdown = renderer.render_full_report_markdown(active_projects)

        assert markdown
        assert "Archived" not in markdown  # Should not include archived

    def test_multi_server_grouping(self, create_test_projects, base_config):
        """Test grouping across multiple Gerrit servers."""
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        # Group by server
        servers = {}
        for project in projects:
            if project.gerrit_server not in servers:
                servers[project.gerrit_server] = []
            servers[project.gerrit_server].append(project)

        assert len(servers) == 2  # Two different servers
        assert "gerrit.example.org" in servers
        assert "gerrit.other.org" in servers

        # Render with grouping
        renderer = InfoYamlRenderer()
        markdown = renderer.render_full_report_markdown(projects, group_by_server=True)

        # Verify both servers in output
        assert "gerrit.example.org" in markdown
        assert "gerrit.other.org" in markdown

    def test_activity_status_distribution(
        self, create_test_projects, base_config, sample_git_metrics
    ):
        """Test distribution of activity statuses."""
        collector = INFOYamlCollector(base_config)
        result = collector.collect(create_test_projects)

        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]

        enricher = InfoYamlEnricher(
            activity_windows=base_config["info_yaml"]["activity_windows"],
            validate_urls=False,
        )
        enriched = enricher.enrich_projects(projects, sample_git_metrics)

        # Count activity statuses
        status_counts = {
            "current": 0,
            "active": 0,
            "inactive": 0,
            "unknown": 0,
        }

        for project in enriched:
            for committer in project.committers:
                status_counts[committer.activity_status] += 1

        # Should have a distribution
        total_committers = sum(status_counts.values())
        assert total_committers > 0

        # At least some should have activity data
        active_count = status_counts["current"] + status_counts["active"]
        assert active_count > 0 or status_counts["unknown"] > 0
