# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
INFO.yaml Renderer.

Generates Markdown and HTML reports for INFO.yaml project data,
including committer activity tables and lifecycle state summaries.

Phase 3: Rendering & Report Integration
"""

from typing import Any, Dict, List, Optional
from domain.info_yaml import ProjectInfo, CommitterInfo, LifecycleSummary
import logging


class InfoYamlRenderer:
    """
    Renderer for INFO.yaml project reports.

    Generates formatted tables and summaries for:
    - Project metadata with committer activity
    - Lifecycle state distribution
    - Color-coded activity status

    Features:
        - Markdown table generation
        - HTML-enhanced formatting
        - Activity color coding (green/orange/red/gray)
        - URL validation and error indication
        - Sorting and grouping by Gerrit server

    Example:
        >>> renderer = InfoYamlRenderer(logger=my_logger)
        >>> projects = [project1, project2, ...]
        >>> markdown = renderer.render_committer_report_markdown(projects)
        >>> lifecycle_md = renderer.render_lifecycle_summary_markdown(projects)
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize INFO.yaml renderer.

        Args:
            logger: Logger instance (creates default if not provided)
        """
        self.logger = logger or logging.getLogger(__name__)

    def render_committer_report_markdown(
        self,
        projects: List[ProjectInfo],
        group_by_server: bool = False
    ) -> str:
        """
        Render committer INFO.yaml report as Markdown.

        Generates a table with project metadata, lifecycle state,
        project leads, and committers with activity color coding.

        Args:
            projects: List of ProjectInfo objects
            group_by_server: If True, group projects by Gerrit server

        Returns:
            Markdown-formatted committer report
        """
        if not projects:
            return ""

        lines = ["## 📋 Committer INFO.yaml Report"]
        lines.append("")
        lines.append(
            "This report shows project information from INFO.yaml files, including lifecycle state, "
            "project leads, and committer activity status."
        )
        lines.append("")

        # Sort projects by name
        sorted_projects = sorted(projects, key=lambda p: p.project_name)

        if group_by_server:
            # Group by Gerrit server
            grouped = self._group_projects_by_server(sorted_projects)
            for server, server_projects in sorted(grouped.items()):
                lines.append(f"### {server}")
                lines.append("")
                lines.extend(self._render_committer_table(server_projects))
                lines.append("")
        else:
            # Single table for all projects
            lines.extend(self._render_committer_table(sorted_projects))

        return "\n".join(lines)

    def render_lifecycle_summary_markdown(
        self,
        projects: List[ProjectInfo]
    ) -> str:
        """
        Render lifecycle state summary as Markdown.

        Generates a summary table showing project counts and percentages
        by lifecycle state.

        Args:
            projects: List of ProjectInfo objects

        Returns:
            Markdown-formatted lifecycle summary
        """
        if not projects:
            return ""

        summaries = self._calculate_lifecycle_summaries(projects)

        lines = ["### Lifecycle State Summary"]
        lines.append("")
        lines.append("| Lifecycle State | Gerrit Project Count | Percentage |")
        lines.append("|----------------|---------------------|------------|")

        for summary in summaries:
            lines.append(
                f"| {summary.state} | {summary.count} | {summary.percentage:.1f}% |"
            )

        lines.append("")
        lines.append(f"**Total Projects:** {len(projects)}")

        return "\n".join(lines)

    def _render_committer_table(
        self,
        projects: List[ProjectInfo]
    ) -> List[str]:
        """
        Render committer table for a list of projects.

        Args:
            projects: List of ProjectInfo objects

        Returns:
            List of Markdown table lines
        """
        lines = [
            "| Project | Creation Date | Lifecycle State | Project Lead | Committers |",
            "|---------|---------------|-----------------|--------------|------------|"
        ]

        for project in projects:
            # Format project name with issue tracker link if available
            project_name_display = self._format_project_name(project)

            # Format project lead with activity color
            lead_display = self._format_project_lead(project)

            # Format committers (excluding project lead) with activity colors
            committers_display = self._format_committers(project)

            # Add table row
            lines.append(
                f"| {project_name_display} | {project.creation_date} | "
                f"{project.lifecycle_state} | {lead_display} | {committers_display} |"
            )

        return lines

    def _format_project_name(self, project: ProjectInfo) -> str:
        """
        Format project name with optional issue tracker link.

        Args:
            project: ProjectInfo object

        Returns:
            HTML-formatted project name
        """
        project_name = project.project_name

        if not project.has_issue_tracker:
            return project_name

        issue_url = project.issue_tracking.url

        if project.issue_tracker_valid:
            # Valid URL - make project name a hyperlink
            return f'<a href="{issue_url}" target="_blank">{project_name}</a>'
        else:
            # Invalid URL - show error indicator
            error_msg = project.issue_tracking.validation_error or "Unknown error"
            return (
                f'<span style="color: red;" '
                f'title="⚠️ Broken project issue-tracker link: {error_msg}">'
                f'{project_name}</span>'
            )

    def _format_project_lead(self, project: ProjectInfo) -> str:
        """
        Format project lead with activity color coding.

        Args:
            project: ProjectInfo object

        Returns:
            HTML-formatted project lead name
        """
        if not project.project_lead:
            return '<span style="color: gray;" title="Unknown activity status">Unknown</span>'

        lead_name = project.project_lead.name

        # Find the project lead in committers to get activity status
        lead_committer = None
        for committer in project.committers:
            if committer.name == lead_name:
                lead_committer = committer
                break

        if not lead_committer:
            # Lead not in committers list
            return f'<span style="color: gray;" title="Unknown activity status">{lead_name}</span>'

        return self._format_person_with_color(lead_committer)

    def _format_committers(self, project: ProjectInfo) -> str:
        """
        Format committers list with activity color coding.

        Excludes the project lead from the list to avoid duplication.

        Args:
            project: ProjectInfo object

        Returns:
            HTML-formatted committers list
        """
        lead_name = project.project_lead.name if project.project_lead else None

        # Filter out project lead
        committers = [
            c for c in project.committers
            if c.name != lead_name
        ]

        if not committers:
            return "None"

        # Format each committer with color
        formatted = [
            self._format_person_with_color(c)
            for c in committers
        ]

        return "<br>".join(formatted)

    def _format_person_with_color(self, committer: CommitterInfo) -> str:
        """
        Format a person's name with activity color and tooltip.

        Args:
            committer: CommitterInfo object

        Returns:
            HTML-formatted name with color and tooltip
        """
        name = committer.name
        color = committer.activity_color

        # Create tooltip based on activity status
        if color == "green":
            tooltip = "✅ Current - commits within last 365 days"
        elif color == "orange":
            tooltip = "☑️ Active - commits between 365-1095 days"
        elif color == "red":
            tooltip = "🛑 Inactive - no commits in 1095+ days"
        else:
            tooltip = "Unknown activity status"

        return f'<span style="color: {color};" title="{tooltip}">{name}</span>'

    def _group_projects_by_server(
        self,
        projects: List[ProjectInfo]
    ) -> Dict[str, List[ProjectInfo]]:
        """
        Group projects by Gerrit server.

        Args:
            projects: List of ProjectInfo objects

        Returns:
            Dictionary mapping server names to project lists
        """
        grouped: Dict[str, List[ProjectInfo]] = {}

        for project in projects:
            server = project.gerrit_server
            if server not in grouped:
                grouped[server] = []
            grouped[server].append(project)

        return grouped

    def _calculate_lifecycle_summaries(
        self,
        projects: List[ProjectInfo]
    ) -> List[LifecycleSummary]:
        """
        Calculate lifecycle state summaries from projects.

        Args:
            projects: List of ProjectInfo objects

        Returns:
            List of LifecycleSummary objects, sorted by count (descending)
        """
        if not projects:
            return []

        # Count projects by lifecycle state
        state_counts: Dict[str, int] = {}
        total = len(projects)

        for project in projects:
            state = project.lifecycle_state
            state_counts[state] = state_counts.get(state, 0) + 1

        # Create summary objects
        summaries = []
        for state, count in state_counts.items():
            percentage = (count / total * 100) if total > 0 else 0.0
            summaries.append(
                LifecycleSummary(
                    state=state,
                    count=count,
                    percentage=percentage
                )
            )

        # Sort by count (descending), then by state name
        summaries.sort(key=lambda s: (-s.count, s.state))

        return summaries

    def render_full_report_markdown(
        self,
        projects: List[ProjectInfo],
        group_by_server: bool = False
    ) -> str:
        """
        Render complete INFO.yaml report with committers and lifecycle summary.

        Args:
            projects: List of ProjectInfo objects
            group_by_server: If True, group projects by Gerrit server

        Returns:
            Complete Markdown report
        """
        sections = []

        # Committer report
        committer_report = self.render_committer_report_markdown(
            projects,
            group_by_server=group_by_server
        )
        if committer_report:
            sections.append(committer_report)

        # Lifecycle summary
        lifecycle_summary = self.render_lifecycle_summary_markdown(projects)
        if lifecycle_summary:
            sections.append(lifecycle_summary)

        return "\n\n".join(sections)

    def build_template_context(
        self,
        projects: List[ProjectInfo],
        group_by_server: bool = False
    ) -> Dict[str, Any]:
        """
        Build context dictionary for Jinja2 templates.

        Args:
            projects: List of ProjectInfo objects
            group_by_server: If True, group projects by Gerrit server

        Returns:
            Context dictionary for template rendering
        """
        # Sort projects
        sorted_projects = sorted(projects, key=lambda p: p.project_name)

        # Build context
        context: Dict[str, Any] = {
            "projects": [p.to_dict() for p in sorted_projects],
            "total_projects": len(projects),
            "group_by_server": group_by_server,
        }

        # Add lifecycle summaries
        summaries = self._calculate_lifecycle_summaries(projects)
        context["lifecycle_summaries"] = [s.to_dict() for s in summaries]

        # Add grouped projects if needed
        if group_by_server:
            grouped = self._group_projects_by_server(sorted_projects)
            context["projects_by_server"] = {
                server: [p.to_dict() for p in projs]
                for server, projs in grouped.items()
            }

        return context
