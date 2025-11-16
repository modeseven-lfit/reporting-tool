# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Integration test for INFO.yaml reporting feature.

Tests the complete end-to-end flow:
1. INFO.yaml collection from info-master
2. Enrichment with Git metrics
3. Report rendering (Markdown/HTML)
4. Integration with main reporting workflow
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pytest

from domain.info_yaml import CommitterInfo, IssueTracking, PersonInfo, ProjectInfo
from rendering.info_yaml_renderer import InfoYamlRenderer
from reporting_tool.collectors.info_yaml import INFOYamlCollector
from reporting_tool.renderers.report import ReportRenderer
from reporting_tool.reporter import RepositoryReporter


@pytest.fixture
def info_master_structure(tmp_path: Path) -> Path:
    """
    Create a realistic info-master directory structure with sample INFO.yaml files.
    
    Structure:
        info-master/
            gerrit.example.org/
                project-a/
                    INFO.yaml
                project-b/
                    INFO.yaml
            gerrit.other.org/
                project-c/
                    INFO.yaml
    """
    info_master = tmp_path / "info-master"
    
    # Create server directories
    server1 = info_master / "gerrit.example.org"
    server2 = info_master / "gerrit.other.org"
    server1.mkdir(parents=True)
    server2.mkdir(parents=True)
    
    # Project A - Active project with current committers
    project_a = server1 / "project-a"
    project_a.mkdir()
    (project_a / "INFO.yaml").write_text("""---
project: 'Project Alpha'
project_creation_date: '2020-01-15'
lifecycle_state: 'Active'
project_lead:
  name: 'Alice Johnson'
  email: 'alice.johnson@example.com'
  id: 'ajohnson'
  company: 'Example Corp'
  timezone: 'America/Los_Angeles'
committers:
  - name: 'Bob Williams'
    email: 'bob.williams@example.com'
    id: 'bwilliams'
    company: 'Developer Inc'
  - name: 'Carol Smith'
    email: 'carol.smith@example.com'
    id: 'csmith'
    company: 'Code Solutions'
repositories:
  - project-a
issue_tracking:
  type: 'jira'
  url: 'https://jira.example.org/projects/ALPHA'
""")
    
    # Project B - Incubation project
    project_b = server1 / "project-b"
    project_b.mkdir()
    (project_b / "INFO.yaml").write_text("""---
project: 'Project Beta'
project_creation_date: '2022-06-01'
lifecycle_state: 'Incubation'
project_lead:
  name: 'David Brown'
  email: 'david.brown@example.com'
  id: 'dbrown'
  company: 'Tech Solutions'
committers:
  - name: 'Eve Davis'
    email: 'eve.davis@example.com'
    id: 'edavis'
    company: 'Innovation Labs'
repositories:
  - project-b
issue_tracking:
  type: 'github'
  url: 'https://github.com/example/project-b'
""")
    
    # Project C - Archived project
    project_c = server2 / "project-c"
    project_c.mkdir()
    (project_c / "INFO.yaml").write_text("""---
project: 'Project Charlie'
project_creation_date: '2018-03-20'
lifecycle_state: 'Archived'
project_lead:
  name: 'Frank Miller'
  email: 'frank.miller@example.com'
  id: 'fmiller'
  company: 'Old Corp'
committers:
  - name: 'Grace Lee'
    email: 'grace.lee@example.com'
    id: 'glee'
    company: 'Legacy Systems'
repositories:
  - project-c
issue_tracking:
  type: 'jira'
  url: 'https://jira.example.org/projects/CHARLIE'
""")
    
    return info_master


@pytest.fixture
def git_metrics_data() -> List[Dict[str, Any]]:
    """
    Mock Git metrics data for enrichment.
    
    Simulates the output from GitDataCollector with repository metrics
    including author activity data.
    """
    return [
        {
            "repository": {
                "name": "project-a",
                "gerrit_project": "project-a",
                "days_since_last_commit": 30,  # Current activity
                "authors": [
                    {
                        "name": "Alice Johnson",
                        "email": "alice.johnson@example.com",
                        "days_since_last_commit": 30,
                    },
                    {
                        "name": "Bob Williams",
                        "email": "bob.williams@example.com",
                        "days_since_last_commit": 45,
                    },
                    {
                        "name": "Carol Smith",
                        "email": "carol.smith@example.com",
                        "days_since_last_commit": 90,
                    },
                ],
            }
        },
        {
            "repository": {
                "name": "project-b",
                "gerrit_project": "project-b",
                "days_since_last_commit": 500,  # Active but not current
                "authors": [
                    {
                        "name": "David Brown",
                        "email": "david.brown@example.com",
                        "days_since_last_commit": 500,
                    },
                    {
                        "name": "Eve Davis",
                        "email": "eve.davis@example.com",
                        "days_since_last_commit": 600,
                    },
                ],
            }
        },
        {
            "repository": {
                "name": "project-c",
                "gerrit_project": "project-c",
                "days_since_last_commit": 1200,  # Inactive
                "authors": [
                    {
                        "name": "Frank Miller",
                        "email": "frank.miller@example.com",
                        "days_since_last_commit": 1200,
                    },
                    {
                        "name": "Grace Lee",
                        "email": "grace.lee@example.com",
                        "days_since_last_commit": 1300,
                    },
                ],
            }
        },
    ]


@pytest.fixture
def config_with_info_yaml() -> Dict[str, Any]:
    """Configuration with INFO.yaml enabled."""
    return {
        "project": "test-project",
        "info_yaml": {
            "enabled": True,
            "activity_windows": {
                "current": 365,
                "active": 1095,
            },
            "validate_urls": False,  # Disable for testing
            "disable_archived_reports": False,  # Include archived for testing
        },
        "output": {
            "include_sections": {
                "info_yaml": True,
            }
        }
    }


class TestINFOYamlCollectorIntegration:
    """Test INFO.yaml collector in integration scenarios."""
    
    def test_collect_from_info_master_structure(
        self, info_master_structure: Path, config_with_info_yaml: Dict[str, Any]
    ):
        """Test collecting INFO.yaml files from directory structure."""
        collector = INFOYamlCollector(config_with_info_yaml)
        
        result = collector.collect(info_master_structure)
        
        # Verify structure
        assert "projects" in result
        assert "lifecycle_summary" in result
        assert "total_projects" in result
        assert "servers" in result
        
        # Verify project count
        assert result["total_projects"] == 3
        
        # Verify servers
        assert len(result["servers"]) == 2
        assert "gerrit.example.org" in result["servers"]
        assert "gerrit.other.org" in result["servers"]
        
        # Verify lifecycle summary
        lifecycle_summary = result["lifecycle_summary"]
        assert len(lifecycle_summary) == 3  # Active, Incubation, Archived
        
        lifecycle_states = {s["state"] for s in lifecycle_summary}
        assert "Active" in lifecycle_states
        assert "Incubation" in lifecycle_states
        assert "Archived" in lifecycle_states
    
    def test_collect_with_git_enrichment(
        self,
        info_master_structure: Path,
        config_with_info_yaml: Dict[str, Any],
        git_metrics_data: List[Dict[str, Any]],
    ):
        """Test INFO.yaml collection with Git data enrichment."""
        collector = INFOYamlCollector(config_with_info_yaml)
        
        result = collector.collect(
            info_master_structure,
            git_metrics=git_metrics_data,
        )
        
        projects = result["projects"]
        assert len(projects) > 0
        
        # Find project-a (should have current activity)
        project_a = next((p for p in projects if p["project_name"] == "Project Alpha"), None)
        assert project_a is not None
        assert project_a["has_git_data"] is True
        assert project_a["project_days_since_last_commit"] == 30
        
        # Verify committers have activity status
        committers = project_a["committers"]
        assert len(committers) > 0
        
        for committer in committers:
            assert "activity_status" in committer
            assert "activity_color" in committer
            # All committers should be "current" (green) since project has recent activity
            assert committer["activity_status"] == "current"
            assert committer["activity_color"] == "green"
    
    def test_collect_filter_by_server(
        self, info_master_structure: Path, config_with_info_yaml: Dict[str, Any]
    ):
        """Test filtering projects by Gerrit server."""
        collector = INFOYamlCollector(config_with_info_yaml)
        
        result = collector.collect_for_server(
            info_master_structure,
            gerrit_server="gerrit.example.org",
        )
        
        projects = result["projects"]
        
        # Should only have projects from gerrit.example.org
        assert len(projects) == 2
        
        for project in projects:
            assert project["gerrit_server"] == "gerrit.example.org"
    
    def test_collect_exclude_archived(
        self, info_master_structure: Path, config_with_info_yaml: Dict[str, Any]
    ):
        """Test excluding archived projects from collection."""
        # Enable archived filtering
        config = config_with_info_yaml.copy()
        config["info_yaml"]["disable_archived_reports"] = True
        
        collector = INFOYamlCollector(config)
        
        result = collector.collect(info_master_structure)
        
        projects = result["projects"]
        
        # Should not include archived project
        project_names = [p["project_name"] for p in projects]
        assert "Project Charlie" not in project_names
        assert "Project Alpha" in project_names
        assert "Project Beta" in project_names


class TestINFOYamlRendererIntegration:
    """Test INFO.yaml renderer integration."""
    
    def test_render_committer_report(
        self, info_master_structure: Path, config_with_info_yaml: Dict[str, Any]
    ):
        """Test rendering committer report in Markdown."""
        collector = INFOYamlCollector(config_with_info_yaml)
        result = collector.collect(info_master_structure)
        
        # Convert to ProjectInfo objects
        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]
        
        renderer = InfoYamlRenderer()
        markdown = renderer.render_committer_report_markdown(projects)
        
        # Verify structure
        assert "📋 Committer INFO.yaml Report" in markdown
        assert "| Project | Creation Date | Lifecycle State | Project Lead | Committers |" in markdown
        
        # Verify projects are present
        assert "Project Alpha" in markdown
        assert "Project Beta" in markdown
        assert "Project Charlie" in markdown
        
        # Verify committers are present
        assert "Alice Johnson" in markdown
        assert "Bob Williams" in markdown
        assert "David Brown" in markdown
    
    def test_render_lifecycle_summary(
        self, info_master_structure: Path, config_with_info_yaml: Dict[str, Any]
    ):
        """Test rendering lifecycle state summary."""
        collector = INFOYamlCollector(config_with_info_yaml)
        result = collector.collect(info_master_structure)
        
        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]
        
        renderer = InfoYamlRenderer()
        markdown = renderer.render_lifecycle_summary_markdown(projects)
        
        # Verify structure
        assert "Lifecycle State Summary" in markdown
        assert "| Lifecycle State | Gerrit Project Count | Percentage |" in markdown
        
        # Verify states
        assert "Active" in markdown
        assert "Incubation" in markdown
        assert "Archived" in markdown
        
        # Verify total
        assert "**Total Projects:** 3" in markdown
    
    def test_render_with_activity_colors(
        self,
        info_master_structure: Path,
        config_with_info_yaml: Dict[str, Any],
        git_metrics_data: List[Dict[str, Any]],
    ):
        """Test that activity colors are rendered correctly."""
        collector = INFOYamlCollector(config_with_info_yaml)
        result = collector.collect(
            info_master_structure,
            git_metrics=git_metrics_data,
        )
        
        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]
        
        renderer = InfoYamlRenderer()
        markdown = renderer.render_committer_report_markdown(projects)
        
        # Verify color spans are present
        assert 'style="color: green;"' in markdown  # Current
        assert 'style="color: orange;"' in markdown  # Active
        assert 'style="color: red;"' in markdown  # Inactive
        
        # Verify tooltips
        assert "✅ Current - commits within last 365 days" in markdown
        assert "☑️ Active - commits between 365-1095 days" in markdown
        assert "🛑 Inactive - no commits in 1095+ days" in markdown


class TestEndToEndReportingIntegration:
    """Test complete end-to-end reporting with INFO.yaml."""
    
    def test_info_yaml_in_report_data(
        self,
        info_master_structure: Path,
        config_with_info_yaml: Dict[str, Any],
        git_metrics_data: List[Dict[str, Any]],
    ):
        """Test that INFO.yaml data is included in report data structure."""
        collector = INFOYamlCollector(config_with_info_yaml)
        
        info_yaml_data = collector.collect(
            info_master_structure,
            git_metrics=git_metrics_data,
        )
        
        # Simulate report data structure
        report_data = {
            "project": "test-project",
            "repositories": [],
            "info_yaml": info_yaml_data,
        }
        
        # Verify structure
        assert "info_yaml" in report_data
        assert report_data["info_yaml"]["total_projects"] == 3
        assert len(report_data["info_yaml"]["projects"]) == 3
    
    def test_info_yaml_section_in_markdown_report(
        self,
        info_master_structure: Path,
        config_with_info_yaml: Dict[str, Any],
        git_metrics_data: List[Dict[str, Any]],
    ):
        """Test that INFO.yaml section appears in rendered Markdown report."""
        # Collect INFO.yaml data
        collector = INFOYamlCollector(config_with_info_yaml)
        info_yaml_data = collector.collect(
            info_master_structure,
            git_metrics=git_metrics_data,
        )
        
        # Create report data
        report_data = {
            "schema_version": "1.0.0",
            "generated_at": "2025-01-20T00:00:00Z",
            "project": "test-project",
            "repositories": [],
            "authors": [],
            "organizations": [],
            "summaries": {},
            "info_yaml": info_yaml_data,
        }
        
        # Render report
        logger = logging.getLogger(__name__)
        renderer = ReportRenderer(config_with_info_yaml, logger)
        
        markdown = renderer._generate_markdown_content(report_data)
        
        # Verify INFO.yaml section is present
        assert "📋 Committer INFO.yaml Report" in markdown
        assert "Lifecycle State Summary" in markdown
        
        # Verify projects are in the report
        assert "Project Alpha" in markdown
        assert "Project Beta" in markdown
        
        # Verify activity colors are present
        assert 'style="color: green;"' in markdown or 'style="color: orange;"' in markdown
    
    def test_info_yaml_section_disabled_in_config(
        self,
        info_master_structure: Path,
        config_with_info_yaml: Dict[str, Any],
    ):
        """Test that INFO.yaml section is excluded when disabled in config."""
        # Disable INFO.yaml in config
        config = config_with_info_yaml.copy()
        config["output"]["include_sections"]["info_yaml"] = False
        
        # Create report data with INFO.yaml
        report_data = {
            "schema_version": "1.0.0",
            "generated_at": "2025-01-20T00:00:00Z",
            "project": "test-project",
            "repositories": [],
            "authors": [],
            "organizations": [],
            "summaries": {},
            "info_yaml": {
                "projects": [],
                "total_projects": 0,
            },
        }
        
        # Render report
        logger = logging.getLogger(__name__)
        renderer = ReportRenderer(config, logger)
        
        markdown = renderer._generate_markdown_content(report_data)
        
        # Verify INFO.yaml section is NOT present
        assert "📋 Committer INFO.yaml Report" not in markdown


class TestINFOYamlErrorHandling:
    """Test error handling in INFO.yaml integration."""
    
    def test_missing_info_master_directory(self, tmp_path: Path, config_with_info_yaml: Dict[str, Any]):
        """Test handling of missing info-master directory."""
        non_existent = tmp_path / "non-existent"
        
        collector = INFOYamlCollector(config_with_info_yaml)
        
        with pytest.raises(ValueError, match="Invalid source path"):
            collector.collect(non_existent)
    
    def test_malformed_yaml_file(self, tmp_path: Path, config_with_info_yaml: Dict[str, Any]):
        """Test handling of malformed INFO.yaml files."""
        info_master = tmp_path / "info-master"
        server = info_master / "gerrit.example.org"
        project = server / "bad-project"
        project.mkdir(parents=True)
        
        # Create malformed YAML
        (project / "INFO.yaml").write_text("""---
project: 'Bad Project'
  invalid_indentation: true
    worse: false
""")
        
        collector = INFOYamlCollector(config_with_info_yaml)
        result = collector.collect(info_master)
        
        # Should handle gracefully and return empty or partial results
        assert "projects" in result
        # May have 0 projects due to parse error
        assert result["total_projects"] >= 0
    
    def test_report_with_info_yaml_error(self, config_with_info_yaml: Dict[str, Any]):
        """Test report rendering when INFO.yaml collection failed."""
        report_data = {
            "schema_version": "1.0.0",
            "generated_at": "2025-01-20T00:00:00Z",
            "project": "test-project",
            "repositories": [],
            "authors": [],
            "organizations": [],
            "summaries": {},
            "info_yaml": {
                "projects": [],
                "total_projects": 0,
                "error": "Failed to clone info-master: Connection timeout",
            },
        }
        
        logger = logging.getLogger(__name__)
        renderer = ReportRenderer(config_with_info_yaml, logger)
        
        markdown = renderer._generate_markdown_content(report_data)
        
        # Should include error message
        assert "📋 Committer INFO.yaml Report" in markdown
        assert "Error collecting INFO.yaml data" in markdown
        assert "Connection timeout" in markdown


@pytest.mark.slow
class TestINFOYamlPerformance:
    """Performance tests for INFO.yaml integration."""
    
    def test_large_info_master_performance(self, tmp_path: Path, config_with_info_yaml: Dict[str, Any]):
        """Test performance with many INFO.yaml files."""
        info_master = tmp_path / "info-master"
        server = info_master / "gerrit.example.org"
        server.mkdir(parents=True)
        
        # Create 50 projects
        num_projects = 50
        for i in range(num_projects):
            project = server / f"project-{i}"
            project.mkdir()
            (project / "INFO.yaml").write_text(f"""---
project: 'Project {i}'
project_creation_date: '2020-01-01'
lifecycle_state: 'Active'
project_lead:
  name: 'Lead {i}'
  email: 'lead{i}@example.com'
  id: 'lead{i}'
committers:
  - name: 'Committer {i}-1'
    email: 'committer{i}-1@example.com'
    id: 'committer{i}-1'
repositories:
  - project-{i}
""")
        
        import time
        
        collector = INFOYamlCollector(config_with_info_yaml)
        
        start_time = time.time()
        result = collector.collect(info_master)
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time
        assert elapsed < 5.0  # 5 seconds for 50 projects
        assert result["total_projects"] == num_projects
        
        # Rendering should also be fast
        projects = [ProjectInfo.from_dict(p) for p in result["projects"]]
        renderer = InfoYamlRenderer()
        
        start_time = time.time()
        markdown = renderer.render_full_report_markdown(projects)
        elapsed = time.time() - start_time
        
        assert elapsed < 2.0  # 2 seconds for rendering
        assert len(markdown) > 0


class TestReporterIntegration:
    """Test INFO.yaml integration with RepositoryReporter."""
    
    def test_reporter_detects_gerrit_server_from_path(self, tmp_path: Path):
        """Test that reporter correctly detects Gerrit server from repos_path."""
        from reporting_tool.reporter import RepositoryReporter
        
        # Create a repos directory with Gerrit server name
        repos_path = tmp_path / "gerrit.onap.org"
        repos_path.mkdir()
        
        # Create minimal config
        config = {
            "project": "test-project",
            "info_yaml": {"enabled": False},  # Disable to avoid actual collection
        }
        
        # Create reporter
        logger = logging.getLogger(__name__)
        reporter = RepositoryReporter(config, logger)
        
        # Test server detection
        server = reporter._determine_gerrit_server(repos_path)
        assert server == "gerrit.onap.org"
    
    def test_reporter_detects_opendaylight_server(self, tmp_path: Path):
        """Test detection of git.opendaylight.org server."""
        from reporting_tool.reporter import RepositoryReporter
        
        repos_path = tmp_path / "git.opendaylight.org"
        repos_path.mkdir()
        
        config = {"project": "test-project", "info_yaml": {"enabled": False}}
        logger = logging.getLogger(__name__)
        reporter = RepositoryReporter(config, logger)
        
        server = reporter._determine_gerrit_server(repos_path)
        assert server == "git.opendaylight.org"
    
    def test_reporter_detects_o_ran_sc_server(self, tmp_path: Path):
        """Test detection of gerrit.o-ran-sc.org server."""
        from reporting_tool.reporter import RepositoryReporter
        
        repos_path = tmp_path / "gerrit.o-ran-sc.org"
        repos_path.mkdir()
        
        config = {"project": "test-project", "info_yaml": {"enabled": False}}
        logger = logging.getLogger(__name__)
        reporter = RepositoryReporter(config, logger)
        
        server = reporter._determine_gerrit_server(repos_path)
        assert server == "gerrit.o-ran-sc.org"
    
    def test_info_yaml_filtered_by_detected_server(
        self,
        info_master_structure: Path,
        config_with_info_yaml: Dict[str, Any],
    ):
        """Test that INFO.yaml collection is filtered by detected Gerrit server."""
        # Create a repos_path that mimics the expected structure
        repos_path = info_master_structure.parent / "gerrit.example.org"
        repos_path.mkdir(exist_ok=True)
        
        # Collect INFO.yaml with server filtering
        collector = INFOYamlCollector(config_with_info_yaml)
        
        # Simulate what the reporter does - filter by server
        result = collector.collect(
            info_master_structure,
            gerrit_server="gerrit.example.org",
        )
        
        # Verify only projects from gerrit.example.org are included
        projects = result["projects"]
        for project in projects:
            assert project["gerrit_server"] == "gerrit.example.org"
        
        # Should have 2 projects (project-a and project-b)
        assert result["total_projects"] == 2
        project_names = [p["project_name"] for p in projects]
        assert "Project Alpha" in project_names
        assert "Project Beta" in project_names
        # Project Charlie is on gerrit.other.org, so it should NOT be included
        assert "Project Charlie" not in project_names