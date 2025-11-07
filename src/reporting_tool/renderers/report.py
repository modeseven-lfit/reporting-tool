# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Report renderer for generating output in multiple formats.

This module provides the ReportRenderer class for rendering repository
metrics and aggregated data into various output formats including:
- JSON (canonical data format)
- Markdown (human-readable tables and summaries)
- HTML (styled web-viewable reports)
- ZIP (bundled report package)
"""

import json
import logging
from pathlib import Path
from typing import Any, Union

from util.formatting import format_number, format_age, UNKNOWN_AGE
from util.zip_bundle import create_report_bundle


class ReportRenderer:
    """Handles rendering of aggregated data into various output formats."""

    def __init__(self, config: dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    def render_json_report(self, data: dict[str, Any], output_path: Path) -> None:
        """
        Write the canonical JSON report.

        TODO: Implement in Phase 5
        """
        self.logger.info(f"Writing JSON report to {output_path}")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def render_markdown_report(self, data: dict[str, Any], output_path: Path) -> str:
        """
        Generate Markdown report from JSON data.

        Creates structured Markdown with tables, emoji indicators, and formatted numbers.
        """
        self.logger.info(f"Generating Markdown report to {output_path}")

        markdown_content = self._generate_markdown_content(data)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        return markdown_content

    def render_html_report(self, markdown_content: str, output_path: Path) -> None:
        """
        Convert Markdown to HTML with embedded styling.

        Converts Markdown tables and formatting to proper HTML with CSS styling.
        """
        self.logger.info(f"Converting to HTML report at {output_path}")

        html_content = self._convert_markdown_to_html(markdown_content)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def package_zip_report(self, output_dir: Path, project: str) -> Path:
        """
        Package all report outputs into a ZIP file.

        Creates a ZIP containing JSON, Markdown, HTML, and configuration files.

        This now delegates to create_report_bundle for unified implementation.
        """
        result: Path = create_report_bundle(output_dir, project, self.logger)
        return result

    def _generate_markdown_content(self, data: dict[str, Any]) -> str:
        """Generate complete Markdown content from JSON data."""
        include_sections = self.config.get("output", {}).get("include_sections", {})

        sections = []

        # Title and metadata
        sections.append(self._generate_title_section(data))

        # Global summary
        sections.append(self._generate_summary_section(data))

        # Organizations (moved up)
        if include_sections.get("organizations", True):
            sections.append(self._generate_organizations_section(data))

        # Contributors (moved up)
        if include_sections.get("contributors", True):
            sections.append(self._generate_contributors_section(data))

        # Repository activity distribution (renamed)
        if include_sections.get("inactive_distributions", True):
            sections.append(self._generate_activity_distribution_section(data))

        # Combined repositories table (replaces separate active/inactive tables)
        sections.append(self._generate_all_repositories_section(data))

        # Repositories with no commits
        sections.append(self._generate_no_commit_repositories_section(data))

        # Repository feature matrix
        if include_sections.get("repo_feature_matrix", True):
            sections.append(self._generate_feature_matrix_section(data))

        # Deployed CI/CD jobs telemetry
        sections.append(self._generate_deployed_workflows_section(data))

        # Orphaned Jenkins jobs from archived projects
        sections.append(self._generate_orphaned_jobs_section(data))

        # Footer
        sections.append("Generated with ❤️ by Release Engineering")

        # Filter out empty sections to avoid unnecessary whitespace
        non_empty_sections = [section for section in sections if section.strip()]
        return "\n\n".join(non_empty_sections)

    def _generate_title_section(self, data: dict[str, Any]) -> str:
        """Generate title and metadata section."""
        project = data.get("project", "Repository Analysis")
        generated_at = data.get("generated_at", "")
        total_repos = (
            data.get("summaries", {}).get("counts", {}).get("total_repositories", 0)
        )
        current_repos = (
            data.get("summaries", {}).get("counts", {}).get("current_repositories", 0)
        )
        active_repos = (
            data.get("summaries", {}).get("counts", {}).get("active_repositories", 0)
        )
        total_authors = (
            data.get("summaries", {}).get("counts", {}).get("total_authors", 0)
        )

        # Format timestamp
        if generated_at:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                formatted_time = dt.strftime("%B %d, %Y at %H:%M UTC")
            except:
                formatted_time = generated_at
        else:
            formatted_time = "Unknown"

        return f"""# 📊 Gerrit Project Analysis Report: {project}

**Generated:** {formatted_time}
**Schema Version:** {data.get("schema_version", "1.0.0")}"""

    def _generate_summary_section(self, data: dict[str, Any]) -> str:
        """Generate global summary statistics section."""
        counts = data.get("summaries", {}).get("counts", {})

        total_repos = counts.get("total_repositories", 0)
        current_repos = counts.get("current_repositories", 0)
        active_repos = counts.get("active_repositories", 0)
        inactive_repos = counts.get("inactive_repositories", 0)
        no_commit_repos = counts.get("no_commit_repositories", 0)
        total_commits = counts.get("total_commits", 0)
        total_lines_added = counts.get("total_lines_added", 0)
        total_authors = counts.get("total_authors", 0)
        total_orgs = counts.get("total_organizations", 0)

        # Calculate percentages
        current_pct = (current_repos / total_repos * 100) if total_repos > 0 else 0
        active_pct = (active_repos / total_repos * 100) if total_repos > 0 else 0
        inactive_pct = (inactive_repos / total_repos * 100) if total_repos > 0 else 0
        no_commit_pct = (no_commit_repos / total_repos * 100) if total_repos > 0 else 0

        # Get configuration thresholds for definitions
        current_threshold = self.config.get("activity_thresholds", {}).get(
            "current_days", 365
        )
        active_threshold = self.config.get("activity_thresholds", {}).get(
            "active_days", 1095
        )

        return f"""## 📈 Global Summary

**✅ Current** commits within last {current_threshold} days
**☑️ Active** commits between {current_threshold}-{active_threshold} days
**🛑 Inactive** no commits in {active_threshold}+ days

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Gerrit Projects | {self._format_number(total_repos)} | 100% |
| Current Gerrit Projects | {self._format_number(current_repos)} | {current_pct:.1f}% |
| Active Gerrit Projects | {self._format_number(active_repos)} | {active_pct:.1f}% |
| Inactive Gerrit Projects | {self._format_number(inactive_repos)} | {inactive_pct:.1f}% |
| No Apparent Commits | {self._format_number(no_commit_repos)} | {no_commit_pct:.1f}% |
| Total Commits | {self._format_number(total_commits)} | - |
| Total Lines of Code | {self._format_number(total_lines_added)} | - |"""

    def _generate_activity_distribution_section(self, data: dict[str, Any]) -> str:
        """Generate repository activity distribution section."""
        return ""  # This section is now disabled

    def _generate_activity_table(self, repos: list[dict[str, Any]]) -> str:
        """Generate activity table for inactive repositories."""
        if not repos:
            return "No repositories in this category."

        # Sort by days since last commit (descending)
        def sort_key(x):
            days = x.get("days_since_last_commit")
            return days if days is not None else 999999

        sorted_repos = sorted(repos, key=sort_key, reverse=True)

        lines = [
            "| Repository | Days Inactive | Last Commit Date |",
            "|------------|---------------|-------------------|",
        ]

        from datetime import datetime, timedelta

        for repo in sorted_repos:  # Show all repositories, not just top 20
            name = repo.get("gerrit_project", "Unknown")
            days = repo.get("days_since_last_commit")
            if days is None:
                days = 999999  # Very large number for repos with no commits
                date_str = "Unknown"
            else:
                # Calculate actual date
                last_activity_date = datetime.now() - timedelta(days=days)
                date_str = last_activity_date.strftime("%Y-%m-%d")
            lines.append(f"| {name} | {days:,} | {date_str} |")

        return "\n".join(lines)

    def _match_workflow_file_to_github_name(
        self, github_name: str, file_names: list[str]
    ) -> str:
        """
        Match GitHub workflow name to workflow file name.

        Args:
            github_name: Name from GitHub API
            file_names: List of workflow file names

        Returns:
            Matching file name or empty string if no match
        """
        # Direct match
        if github_name in file_names:
            return github_name

        # Try matching without extension
        github_base = github_name.lower().replace(" ", "-").replace("_", "-")

        for file_name in file_names:
            file_base = file_name.lower()
            # Remove .yml/.yaml extension
            if file_base.endswith(".yml"):
                file_base = file_base[:-4]
            elif file_base.endswith(".yaml"):
                file_base = file_base[:-5]

            # Try various matching strategies
            if (
                file_base == github_base
                or github_base in file_base
                or file_base in github_base
                or file_base.replace("-", "") == github_base.replace("-", "")
            ):
                return file_name

        # If no match found, return the first file name as fallback
        return file_names[0] if file_names else ""

    def _generate_all_repositories_section(self, data: dict[str, Any]) -> str:
        """Generate combined repositories table showing all Gerrit projects."""
        all_repos = data.get("summaries", {}).get("all_repositories", [])

        if not all_repos:
            return "## 📊 All Gerrit Repositories\n\nNo repositories found."

        # Get configuration for definitions
        current_threshold = self.config.get("activity_thresholds", {}).get(
            "current_days", 365
        )
        active_threshold = self.config.get("activity_thresholds", {}).get(
            "active_days", 1095
        )

        lines = [
            "## 📊 Gerrit Projects",
            "",
            "| Gerrit Project | Commits | LOC | Contributors | Days Inactive | Last Commit Date | Status |",
            "|----------------|---------|---------|--------------|---------------|------------------|--------|",
        ]

        for repo in all_repos:
            name = repo.get("gerrit_project", "Unknown")
            commits_1y = repo.get("commit_counts", {}).get("last_365_days", 0)
            loc_1y = repo.get("loc_stats", {}).get("last_365_days", {}).get("net", 0)
            contributors_1y = repo.get("unique_contributors", {}).get(
                "last_365_days", 0
            )
            days_since = repo.get("days_since_last_commit")
            if days_since is None:
                days_since = 999999  # Very large number for repos with no commits
            activity_status = repo.get("activity_status", "inactive")

            age_str = self._format_age(days_since)

            # Map activity status to display format (emoji only)
            status_map = {"current": "✅", "active": "☑️", "inactive": "🛑"}
            status = status_map.get(activity_status, "🛑")

            # Format days inactive
            days_inactive_str = f"{days_since:,}" if days_since < 999999 else "N/A"

            lines.append(
                f"| {name} | {commits_1y} | {int(loc_1y):+d} | {contributors_1y} | {days_inactive_str} | {age_str} | {status} |"
            )

        lines.extend(["", f"**Total:** {len(all_repos)} repositories"])
        return "\n".join(lines)

    def _generate_no_commit_repositories_section(self, data: dict[str, Any]) -> str:
        """Generate repositories with no commits section."""
        no_commit_repos = data.get("summaries", {}).get("no_commit_repositories", [])

        if not no_commit_repos:
            return ""  # Skip output entirely if no data

        lines = [
            "## 📝 Gerrit Projects with No Apparent Commits",
            "",
            "**WARNING:** All Gerrit projects/repositories should contain at least one commit, due to the initial repository creation automation writing initial template and configuration files. The report generation and parsing logic may need checking/debugging for the projects/repositories below.",
            "",
            "| Gerrit Project |",
            "|------------|",
        ]

        for repo in no_commit_repos:
            name = repo.get("gerrit_project", "Unknown")
            lines.append(f"| {name} |")

        lines.extend(
            [
                "",
                f"**Total:** {len(no_commit_repos)} Gerrit projects with no apparent commits",
            ]
        )
        return "\n".join(lines)

    def _determine_jenkins_job_status(self, job_data: dict[str, Any]) -> str:
        """
        Determine Jenkins job status for color coding.

        Now uses the standardized status and state fields if available, falls back to color/build interpretation.

        Args:
            job_data: Jenkins job data containing status, state, color and last_build info

        Returns:
            Status string: "success", "failure", "unstable", "building", "disabled", "unknown"
        """
        # Use standardized status if available
        if "status" in job_data and job_data["status"]:
            status: str = str(job_data["status"])
            # Check state for disabled jobs
            if "state" in job_data and job_data["state"] == "disabled":
                return "disabled"
            return status

        # Fallback to original color-based logic for compatibility
        color = job_data.get("color", "").lower()
        last_build = job_data.get("last_build", {})
        last_result = (last_build.get("result") or "").upper()

        # Handle animated colors (building)
        if color.endswith("_anime"):
            return "building"

        # Map Jenkins colors to status
        color_map = {
            "blue": "success",
            "green": "success",
            "red": "failure",
            "yellow": "unstable",
            "grey": "disabled",
            "disabled": "disabled",
            "aborted": "aborted",
        }

        # Try color first
        if color in color_map:
            return color_map[color]

        # Fallback to last build result
        result_map = {
            "SUCCESS": "success",
            "FAILURE": "failure",
            "UNSTABLE": "unstable",
            "ABORTED": "aborted",
        }

        if last_result in result_map:
            return result_map[last_result]

        return "unknown"

    def _determine_github_workflow_status(self, workflow_data: dict[str, Any]) -> str:
        """
        Determine GitHub workflow status for color coding.

        Now uses the standardized status field if available, falls back to conclusion/run_status interpretation.

        Args:
            workflow_data: Workflow data from GitHub API

        Returns:
            Status string: "success", "failure", "building", "no_runs", "unknown"
        """
        # Use standardized status if available (from workflow runs)
        # Note: "status" contains run results (success/failure), different from "state" (active/disabled)
        if (
            "status" in workflow_data
            and workflow_data["status"]
            and workflow_data["status"] != "unknown"
        ):
            status: str = str(workflow_data["status"])
            # Map building to in_progress for display compatibility
            if status == "building":
                return "in_progress"
            return status

        # Fallback to original logic for compatibility
        # Get the conclusion (final result) and run status (current execution state)
        conclusion = workflow_data.get("conclusion", "unknown")
        run_status = workflow_data.get("run_status", "unknown")

        # Handle in-progress workflows first
        if run_status in ("queued", "in_progress"):
            return "in_progress"

        # Handle completed workflows - map conclusion to our status
        if run_status == "completed":
            conclusion_map = {
                "success": "success",
                "failure": "failure",
                "neutral": "success",  # Treat neutral as success for display
                "cancelled": "cancelled",
                "skipped": "skipped",
                "timed_out": "failure",
                "action_required": "failure",
            }
            return conclusion_map.get(conclusion, "unknown")

        # Special case for no runs
        if conclusion == "no_runs":
            return "no_runs"

        return "unknown"

    def _apply_status_color_classes(
        self, item_name: str, status: str, item_type: str = "workflow"
    ) -> str:
        """
        Apply CSS classes for status color coding.

        Args:
            item_name: Name of the job/workflow
            status: Status string from determine_*_status functions
            item_type: "workflow" or "jenkins" for different styling if needed

        Returns:
            HTML string with appropriate CSS classes
        """
        # CSS class mapping for different statuses
        class_map = {
            "success": "status-success",
            "failure": "status-failure",
            "unstable": "status-warning",
            "building": "status-building",
            "in_progress": "status-in-progress",
            "disabled": "status-disabled",
            "aborted": "status-cancelled",
            "cancelled": "status-cancelled",
            "neutral": "status-neutral",
            "skipped": "status-skipped",
            "no_runs": "status-no-runs",
            "active": "status-success",
            "unknown": "status-unknown",
        }

        css_class = class_map.get(status, "status-unknown")
        return f'<span class="{css_class} {item_type}-status">{item_name}</span>'

    def _construct_github_workflow_url(
        self, gerrit_project: str, workflow_name: str
    ) -> str:
        """
        Construct GitHub source URL for a workflow file based on Gerrit project.

        Args:
            gerrit_project: Gerrit project name (e.g., "portal-ng/bff", "doc")
            workflow_name: Workflow file name (e.g., "ci.yaml")

        Returns:
            GitHub source URL for the workflow file
        """
        if not gerrit_project or not workflow_name:
            return ""

        # Convert Gerrit project name to GitHub repository name
        github_repo_name = self._gerrit_to_github_repo_name(gerrit_project)
        return f"https://github.com/onap/{github_repo_name}/blob/master/.github/workflows/{workflow_name}"

    def _construct_github_workflow_actions_url(
        self, gerrit_project: str, workflow_name: str
    ) -> str:
        """
        Construct GitHub Actions URL for a workflow based on Gerrit project.

        Args:
            gerrit_project: Gerrit project name (e.g., "portal-ng/bff", "doc")
            workflow_name: Workflow file name (e.g., "ci.yaml")

        Returns:
            GitHub Actions URL for the workflow
        """
        if not gerrit_project or not workflow_name:
            return ""

        # Convert Gerrit project name to GitHub repository name
        github_repo_name = self._gerrit_to_github_repo_name(gerrit_project)
        return f"https://github.com/onap/{github_repo_name}/actions/workflows/{workflow_name}"

    def _gerrit_to_github_repo_name(self, gerrit_project: str) -> str:
        """
        Convert Gerrit project name to GitHub repository name using ONAP naming conventions.

        Args:
            gerrit_project: Gerrit project name (e.g., "ccsdk/parent", "aai/babel")

        Returns:
            GitHub repository name (e.g., "ccsdk-parent", "aai-babel")
        """
        if not gerrit_project:
            return ""

        # Convert slashes to dashes for ONAP GitHub mirrors
        # e.g., "ccsdk/parent" -> "ccsdk-parent"
        #       "aai/babel" -> "aai-babel"
        #       "policy/apex-pdp" -> "policy-apex-pdp"
        return gerrit_project.replace("/", "-")

    def _generate_deployed_workflows_section(self, data: dict[str, Any]) -> str:
        """Generate deployed CI/CD jobs telemetry section with status color-coding."""
        repositories = data.get("repositories", [])

        if not repositories:
            return "## 🏁 Deployed CI/CD Jobs\n\nNo repositories found."

        # Collect repositories that have workflows or Jenkins jobs
        repos_with_cicd = []
        has_any_jenkins = False

        for repo in repositories:
            workflow_names = (
                repo.get("features", {}).get("workflows", {}).get("workflow_names", [])
            )
            jenkins_jobs = repo.get("jenkins", {}).get("jobs", [])
            jenkins_job_names = [
                job.get("name", "") for job in jenkins_jobs if job.get("name")
            ]

            if workflow_names or jenkins_job_names:
                repos_with_cicd.append(
                    {
                        "gerrit_project": repo.get("gerrit_project", "Unknown"),
                        "workflow_names": workflow_names,
                        "workflows_data": repo.get("features", {}).get(
                            "workflows", {}
                        ),  # Include workflow data for status
                        "features": repo.get(
                            "features", {}
                        ),  # Include full features data for github_mirror check
                        "jenkins_jobs": jenkins_jobs,  # Store full job data for status
                        "jenkins_job_names": jenkins_job_names,
                        "workflow_count": len(workflow_names),
                        "job_count": len(jenkins_job_names),
                    }
                )
                if jenkins_job_names:
                    has_any_jenkins = True

        if not repos_with_cicd:
            return "## 🏁 Deployed CI/CD Jobs\n\nNo CI/CD jobs detected in any repositories."

        # Calculate totals
        total_workflows = sum(repo["workflow_count"] for repo in repos_with_cicd)
        total_jenkins_jobs = sum(repo["job_count"] for repo in repos_with_cicd)

        # Build table header based on whether Jenkins jobs exist
        if has_any_jenkins:
            lines = [
                "## 🏁 Deployed CI/CD Jobs",
                "",
                f"**Total GitHub workflows:** {total_workflows}",
                f"**Total Jenkins jobs:** {total_jenkins_jobs}",
                "",
                "| Gerrit Project | GitHub Workflows | Workflow Count | Jenkins Jobs | Job Count |",
                "|----------------|-------------------|----------------|--------------|-----------|",
            ]
        else:
            lines = [
                "## 🏁 Deployed CI/CD Jobs",
                "",
                f"**Total GitHub workflows:** {total_workflows}",
                f"**Total Jenkins jobs:** {total_jenkins_jobs}",
                "",
                "| Gerrit Project | GitHub Workflows | Workflow Count | Job Count |",
                "|----------------|-------------------|----------------|-----------|",
            ]

        for repo in sorted(repos_with_cicd, key=lambda x: x["gerrit_project"]):
            name = repo["gerrit_project"]

            # Check if GitHub mirror exists for this repository
            github_mirror_info = repo.get("features", {}).get("github_mirror", {})

            # Add warning indicator if:
            # 1. Repository has GitHub workflows (so we'd be generating broken links)
            # 2. The mirror was explicitly checked on GitHub and not found (reason: "not_found_on_github")
            # Don't flag repos with "no_github_indicators" - they simply don't use GitHub at all
            has_workflows = len(repo.get("workflow_names", [])) > 0
            mirror_not_found = (
                github_mirror_info.get("exists") is False
                and github_mirror_info.get("reason") == "not_found_on_github"
            )

            if has_workflows and mirror_not_found:
                # Add warning symbol with CSS tooltip, but keep text normal color
                project_name = f'<span class="mirror-warning">⚠️<span class="tooltip-text">Not mirrored to GitHub</span></span> {name}'
                has_github_mirror = False
            else:
                project_name = name
                has_github_mirror = True

            # Build workflow names with color coding
            workflow_items = []
            workflows_data = repo.get("workflows_data", {})
            self.logger.debug(
                f"[workflows] Processing repo {name}: workflows_data keys={list(workflows_data.keys())}, has_runtime_status={workflows_data.get('has_runtime_status', 'MISSING')}, has_github_mirror={has_github_mirror}"
            )

            # Check if we have valid GitHub API data or should fall back to failure status
            has_github_api_data = workflows_data.get(
                "has_runtime_status", False
            ) and workflows_data.get("github_api_data", {}).get("workflows")

            if has_github_api_data:
                # Use GitHub API data for status-aware rendering
                github_workflows = workflows_data.get("github_api_data", {}).get(
                    "workflows", []
                )

                # Create a map of workflow file names to their execution status using path field
                workflow_status_map = {}
                import os

                for workflow in github_workflows:
                    workflow_path = workflow.get("path", "")
                    # Extract filename from path (e.g., ".github/workflows/ci.yaml" -> "ci.yaml")
                    if workflow_path:
                        file_name = os.path.basename(workflow_path)
                        if file_name in repo["workflow_names"]:
                            # Only process workflows that are enabled/active
                            if workflow.get("state") == "active":
                                status = self._determine_github_workflow_status(
                                    workflow
                                )
                                workflow_status_map[file_name] = status
                                self.logger.debug(
                                    f"[workflows] Path match status mapped: path={workflow_path} file={file_name} status={status}"
                                )
                            else:
                                # Disabled workflows get disabled status
                                workflow_status_map[file_name] = "disabled"
                                self.logger.debug(
                                    f"[workflows] Disabled workflow: path={workflow_path} file={file_name}"
                                )
                        else:
                            self.logger.debug(
                                f"[workflows] Path basename '{file_name}' not in local workflow_names {repo['workflow_names']} (repo={name})"
                            )

                # Fallback: attempt to map remaining workflows by GitHub display name when path-based mapping
                # did not cover all locally discovered workflow files (common with mirrored or renamed workflows)
                if github_workflows and len(workflow_status_map) < len(
                    repo["workflow_names"]
                ):
                    remaining = set(repo["workflow_names"]) - set(
                        workflow_status_map.keys()
                    )
                    if remaining:
                        self.logger.debug(
                            f"[workflows] Attempting name-based fallback mapping; unmapped local files: {sorted(remaining)} (repo={name})"
                        )
                        for workflow in github_workflows:
                            gh_name = workflow.get("name")
                            if not gh_name:
                                continue
                            matched_file = self._match_workflow_file_to_github_name(
                                gh_name, repo["workflow_names"]
                            )
                            if matched_file and matched_file not in workflow_status_map:
                                status = self._determine_github_workflow_status(
                                    workflow
                                )
                                workflow_status_map[matched_file] = status
                                self.logger.debug(
                                    f"[workflows] Fallback name match: github_name='{gh_name}' -> file='{matched_file}' status={status} (repo={name})"
                                )

                # If still nothing mapped, emit a single debug to aid diagnosis
                if (
                    github_workflows
                    and not workflow_status_map
                    and repo["workflow_names"]
                ):
                    self.logger.debug(
                        f"[workflows] No workflow runtime statuses mapped (possible API auth/visibility issue) repo={name} github_workflows={len(github_workflows)} local_files={repo['workflow_names']}"
                    )

                # If GitHub API returned no workflows but local files exist, assume API failure
                elif (
                    not github_workflows
                    and repo["workflow_names"]
                    and workflows_data.get("has_runtime_status", False)
                ):
                    self.logger.debug(
                        f"[workflows] GitHub API returned no workflows for {name}, defaulting to unknown status for local workflow files"
                    )
                    for workflow_name in repo["workflow_names"]:
                        workflow_status_map[workflow_name] = "unknown"

                # Build the list with status information and hyperlinks
                for workflow_name in sorted(repo["workflow_names"]):
                    status = workflow_status_map.get(workflow_name, "unknown")
                    colored_name = self._apply_status_color_classes(
                        workflow_name, status, "workflow"
                    )
                    self.logger.debug(
                        f"[workflows] Applied color to {workflow_name}: status={status}, colored_name={colored_name[:100]}..."
                    )

                    # Find the corresponding workflow data to get URLs
                    workflow_url = None
                    for workflow in github_workflows:
                        workflow_path = workflow.get("path", "")
                        if (
                            workflow_path
                            and os.path.basename(workflow_path) == workflow_name
                        ):
                            # Prefer workflow page URL for runs/status over source code URL
                            urls = workflow.get("urls", {})
                            workflow_url = urls.get("workflow_page")
                            break

                    # If no workflow URL found in GitHub API data, construct one using GitHub owner/repo info
                    if not workflow_url:
                        workflows_data = repo.get("workflows_data", {})
                        github_api_data = workflows_data.get("github_api_data", {})
                        github_owner = github_api_data.get("github_owner")
                        github_repo = github_api_data.get("github_repo")

                        if github_owner and github_repo:
                            # Use actual GitHub owner/repo from API data
                            workflow_url = f"https://github.com/{github_owner}/{github_repo}/actions/workflows/{workflow_name}"
                        elif repo.get("gerrit_project"):
                            # Fallback to constructed URL from Gerrit project
                            workflow_url = self._construct_github_workflow_actions_url(
                                repo["gerrit_project"], workflow_name
                            )

                    if workflow_url:
                        linked_name = f'<a href="{workflow_url}" target="_blank">{colored_name}</a>'
                        workflow_items.append(linked_name)
                    else:
                        workflow_items.append(colored_name)
            else:
                # Fallback when no GitHub API data is available
                workflows_data_workflows = workflows_data.get(
                    "github_api_data", {}
                ).get("workflows", [])
                for workflow_name in sorted(repo["workflow_names"]):
                    # For workflows that are expected to have status but GitHub API failed,
                    # default to unknown to indicate the monitoring is not working
                    default_status = "unknown"
                    colored_name = self._apply_status_color_classes(
                        workflow_name, default_status, "workflow"
                    )
                    self.logger.debug(
                        f"[workflows] Fallback color applied to {workflow_name}: status={default_status}, colored_name={colored_name[:100]}..."
                    )

                    # Try to find URL from workflows data even without runtime status
                    workflow_url = None
                    for workflow in workflows_data_workflows:
                        workflow_path = workflow.get("path", "")
                        if (
                            workflow_path
                            and os.path.basename(workflow_path) == workflow_name
                        ):
                            # Prefer workflow page URL for runs/status over source code URL
                            urls = workflow.get("urls", {})
                            workflow_url = urls.get("workflow_page")
                            break

                    # If no API URL, try to construct GitHub Actions URL using stored GitHub info
                    if not workflow_url:
                        workflows_data = repo.get("workflows_data", {})
                        github_api_data = workflows_data.get("github_api_data", {})
                        github_owner = github_api_data.get("github_owner")
                        github_repo = github_api_data.get("github_repo")

                        if github_owner and github_repo:
                            # Use actual GitHub owner/repo from API data
                            workflow_url = f"https://github.com/{github_owner}/{github_repo}/actions/workflows/{workflow_name}"
                        elif repo.get("gerrit_project"):
                            # Fallback to constructed URL from Gerrit project
                            workflow_url = self._construct_github_workflow_actions_url(
                                repo["gerrit_project"], workflow_name
                            )

                    # Only skip links/colors if the repo has workflows but mirror was not found on GitHub
                    if has_workflows and mirror_not_found:
                        # No GitHub mirror - just add plain text without links or color coding
                        workflow_items.append(workflow_name)
                    elif workflow_url:
                        linked_name = f'<a href="{workflow_url}" target="_blank">{colored_name}</a>'
                        workflow_items.append(linked_name)
                    else:
                        workflow_items.append(colored_name)

            workflow_names_str = "<br>".join(workflow_items) if workflow_items else ""

            # Build Jenkins job names with color coding based on status and hyperlinks
            jenkins_items = []
            for job in repo["jenkins_jobs"]:
                job_name = job.get("name", "Unknown")
                status = self._determine_jenkins_job_status(job)
                colored_name = self._apply_status_color_classes(
                    job_name, status, "jenkins"
                )

                # Get Jenkins job URL from URLs structure
                urls = job.get("urls", {})
                job_url = urls.get("job_page")

                if job_url:
                    linked_name = (
                        f'<a href="{job_url}" target="_blank">{colored_name}</a>'
                    )
                    jenkins_items.append(linked_name)
                else:
                    jenkins_items.append(colored_name)
            jenkins_names_str = "<br>".join(jenkins_items) if jenkins_items else ""

            workflow_count = repo["workflow_count"]
            job_count = repo["job_count"]

            if has_any_jenkins:
                lines.append(
                    f"| {project_name} | {workflow_names_str} | {workflow_count} | {jenkins_names_str} | {job_count} |"
                )
            else:
                lines.append(
                    f"| {project_name} | {workflow_names_str} | {workflow_count} | {job_count} |"
                )

        lines.extend(
            ["", f"**Total:** {len(repos_with_cicd)} repositories with CI/CD jobs"]
        )
        return "\n".join(lines)

    def _generate_contributors_section(self, data: dict[str, Any]) -> str:
        """Generate consolidated contributors table section."""
        top_commits = data.get("summaries", {}).get("top_contributors_commits", [])
        top_loc = data.get("summaries", {}).get("top_contributors_loc", [])
        total_authors = (
            data.get("summaries", {}).get("counts", {}).get("total_authors", 0)
        )

        sections = ["## 👥 Top Contributors (Last Year)"]
        sections.append(f"**Contributors Found:** {total_authors:,}")

        # Generate consolidated table with all contributors
        if top_commits or top_loc:
            sections.append(
                self._generate_consolidated_contributors_table(top_commits, top_loc)
            )
        else:
            sections.append("No contributor data available.")

        return "\n\n".join(sections)

    def _generate_consolidated_contributors_table(
        self, top_commits: list[dict[str, Any]], top_loc: list[dict[str, Any]]
    ) -> str:
        """Generate consolidated contributors table with commits, LOC, and average LOC per commit."""
        # Create a comprehensive list of all contributors from both lists
        contributors_dict = {}

        # Add contributors from commits list
        for contributor in top_commits:
            email = contributor.get("email", "")
            contributors_dict[email] = contributor.copy()

        # Merge data from LOC list
        for contributor in top_loc:
            email = contributor.get("email", "")
            if email in contributors_dict:
                # Update existing entry with LOC data
                contributors_dict[email].update(contributor)
            else:
                # Add new entry
                contributors_dict[email] = contributor.copy()

        # Convert back to list and sort by total activity (commits + normalized LOC)
        all_contributors = list(contributors_dict.values())

        # Sort by commits first, then by LOC as secondary sort
        all_contributors.sort(
            key=lambda x: (
                x.get("commits", {}).get("last_365_days", 0),
                x.get("lines_net", {}).get("last_365_days", 0),
            ),
            reverse=True,
        )

        if not all_contributors:
            return "No contributors found."

        # Create table headers
        lines = [
            "| Rank | Contributor | Commits | LOC | Δ LOC | Avg LOC/Commit | Repositories | Organization |",
            "|------|-------------|---------|-----|-------|----------------|--------------|--------------|",
        ]

        for i, contributor in enumerate(all_contributors, 1):
            name = contributor.get("name", "Unknown")
            email = contributor.get("email", "")
            domain = contributor.get("domain", "")
            commits_1y = contributor.get("commits", {}).get("last_365_days", 0)
            loc_1y = contributor.get("lines_net", {}).get("last_365_days", 0)
            lines_added_1y = contributor.get("lines_added", {}).get("last_365_days", 0)
            lines_removed_1y = contributor.get("lines_removed", {}).get(
                "last_365_days", 0
            )
            delta_loc_1y = abs(lines_added_1y) + abs(lines_removed_1y)
            repos_1y = contributor.get("repositories_count", {}).get("last_365_days", 0)

            # Calculate average LOC per commit
            if commits_1y > 0:
                avg_loc_per_commit = loc_1y / commits_1y
                avg_display = f"{avg_loc_per_commit:+.1f}"
            else:
                avg_display = "-"

            # Use just the name without email for privacy
            display_name = name

            org_display = domain if domain and domain != "unknown" else "-"

            lines.append(
                f"| {i} | {display_name} | {commits_1y} | {int(loc_1y):+d} | {delta_loc_1y} | {avg_display} | {repos_1y} | {org_display} |"
            )

        return "\n".join(lines)

    def _generate_contributors_table(
        self, contributors: list[dict[str, Any]], metric_type: str
    ) -> str:
        """Generate contributors table for commits or LOC."""
        if not contributors:
            return "No contributors found."

        if metric_type == "commits":
            lines = [
                "| Rank | Contributor | Commits | Repositories | Organization |",
                "|------|-------------|---------|--------------|--------------|",
            ]
        else:
            lines = [
                "| Rank | Contributor | LOC | Commits | Repositories | Organization |",
                "|------|-------------|---------|---------|--------------|--------------|",
            ]

        for i, contributor in enumerate(contributors, 1):
            name = contributor.get("name", "Unknown")
            email = contributor.get("email", "")
            domain = contributor.get("domain", "")
            commits_1y = contributor.get("commits", {}).get("last_365_days", 0)
            loc_1y = contributor.get("lines_net", {}).get("last_365_days", 0)
            repos_1y = contributor.get("repositories_count", {}).get("last_365_days", 0)

            # Use just the name without email for privacy
            display_name = name

            org_display = domain if domain and domain != "unknown" else "-"

            if metric_type == "commits":
                lines.append(
                    f"| {i} | {display_name} | {commits_1y} | {repos_1y} | {org_display} |"
                )
            else:
                lines.append(
                    f"| {i} | {display_name} | {int(loc_1y):+d} | {commits_1y} | {repos_1y} | {org_display} |"
                )

        return "\n".join(lines)

    def _generate_organizations_section(self, data: dict[str, Any]) -> str:
        """Generate organizations leaderboard section."""
        top_orgs = data.get("summaries", {}).get("top_organizations", [])

        if not top_orgs:
            return "## 🏢 Organizations\n\nNo organization data available."

        total_orgs = (
            data.get("summaries", {}).get("counts", {}).get("total_organizations", 0)
        )

        lines = ["## 🏢 Top Organizations (Last Year)"]
        lines.append(f"**Organizations Found:** {total_orgs:,}")
        lines.append("")
        lines.append(
            "| Rank | Organization | Contributors | Commits | LOC | Δ LOC | Avg LOC/Commit | Unique Repositories |"
        )
        lines.append(
            "|------|--------------|--------------|---------|-----|-------|----------------|---------------------|"
        )

        for i, org in enumerate(top_orgs, 1):
            domain = org.get("domain", "Unknown")
            contributors = org.get("contributor_count", 0)
            commits_1y = org.get("commits", {}).get("last_365_days", 0)
            loc_1y = org.get("lines_net", {}).get("last_365_days", 0)
            lines_added_1y = org.get("lines_added", {}).get("last_365_days", 0)
            lines_removed_1y = org.get("lines_removed", {}).get("last_365_days", 0)
            delta_loc_1y = abs(lines_added_1y) + abs(lines_removed_1y)
            repos_1y = org.get("repositories_count", {}).get("last_365_days", 0)

            # Calculate average LOC per commit
            if commits_1y > 0:
                avg_loc_per_commit = loc_1y / commits_1y
                avg_display = f"{avg_loc_per_commit:+.1f}"
            else:
                avg_display = "-"

            lines.append(
                f"| {i} | {domain} | {contributors} | {commits_1y} | {int(loc_1y):+d} | {delta_loc_1y} | {avg_display} | {repos_1y} |"
            )

        return "\n".join(lines)

    def _generate_feature_matrix_section(self, data: dict[str, Any]) -> str:
        """Generate repository feature matrix section."""
        repositories = data.get("repositories", [])

        if not repositories:
            return "## 🔧 Gerrit Project Feature Matrix\n\nNo projects analyzed."

        # Sort repositories by primary metric (commits in last year)
        sorted_repos = sorted(
            repositories,
            key=lambda r: r.get("commit_counts", {}).get("last_365_days", 0),
            reverse=True,
        )

        # Get activity thresholds for definition
        current_threshold = self.config.get("activity_thresholds", {}).get(
            "current_days", 365
        )
        active_threshold = self.config.get("activity_thresholds", {}).get(
            "active_days", 1095
        )

        lines = [
            "## 🔧 Gerrit Project Feature Matrix",
            "",
            "| Gerrit Project | Type | Dependabot | Pre-commit | ReadTheDocs | .gitreview | G2G | Status |",
            "|------------|------|------------|------------|-------------|------------|-----|--------|",
        ]

        for repo in sorted_repos:
            name = repo.get("gerrit_project", "Unknown")
            features = repo.get("features", {})
            activity_status = repo.get("activity_status", "inactive")

            # Extract feature status
            project_types = features.get("project_types", {})
            primary_type = project_types.get("primary_type", "unknown")

            dependabot = (
                "✅" if features.get("dependabot", {}).get("present", False) else "❌"
            )
            pre_commit = (
                "✅" if features.get("pre_commit", {}).get("present", False) else "❌"
            )
            readthedocs = (
                "✅" if features.get("readthedocs", {}).get("present", False) else "❌"
            )
            gitreview = (
                "✅" if features.get("gitreview", {}).get("present", False) else "❌"
            )
            g2g = "✅" if features.get("g2g", {}).get("present", False) else "❌"

            # Map activity status to display format (emoji only)
            status_map = {"current": "✅", "active": "☑️", "inactive": "🛑"}
            status = status_map.get(activity_status, "🛑")

            lines.append(
                f"| {name} | {primary_type} | {dependabot} | {pre_commit} | {readthedocs} | {gitreview} | {g2g} | {status} |"
            )

        return "\n".join(lines)

    def _generate_orphaned_jobs_section(self, data: dict[str, Any]) -> str:
        """Generate section for Jenkins jobs matched to archived/read-only Gerrit projects."""
        orphaned_data = data.get("orphaned_jenkins_jobs", {})

        if not orphaned_data or orphaned_data.get("total_orphaned_jobs", 0) == 0:
            return ""  # Don't show section if no orphaned jobs

        total_orphaned = orphaned_data.get("total_orphaned_jobs", 0)
        by_state = orphaned_data.get("by_state", {})
        jobs = orphaned_data.get("jobs", {})

        lines = [
            "## 🏚️ Orphaned Jenkins Jobs (Archived Projects)",
            "",
            f"**Total Orphaned Jobs:** {total_orphaned}",
            "",
            "These Jenkins jobs belong to archived or read-only Gerrit projects and should likely be removed:",
            "",
        ]

        # Summary by project state
        if by_state:
            lines.append("### Summary by Project State")
            lines.append("")
            for state, count in sorted(by_state.items()):
                lines.append(f"- **{state}:** {count} jobs")
            lines.append("")

        # Detailed table
        lines.extend(
            [
                "### Detailed Job Listing",
                "",
                "| Job Name | Gerrit Project | Project State | Match Score |",
                "|----------|----------------|---------------|-------------|",
            ]
        )

        # Sort jobs by project name for better organization
        sorted_jobs = sorted(jobs.items(), key=lambda x: x[1].get("project_name", ""))

        for job_name, job_info in sorted_jobs:
            project_name = job_info.get("project_name", "Unknown")
            state = job_info.get("state", "UNKNOWN")
            score = job_info.get("score", 0)

            # Color-code based on state
            if state == "READ_ONLY":
                state_display = f"🔒 {state}"
            elif state == "HIDDEN":
                state_display = f"👻 {state}"
            else:
                state_display = f"❓ {state}"

            lines.append(
                f"| `{job_name}` | `{project_name}` | {state_display} | {score} |"
            )

        lines.extend(
            [
                "",
                "**Recommendation:** Review these jobs and remove them if they are no longer needed, ",
                "since their associated Gerrit projects are archived or read-only.",
                "",
            ]
        )

        return "\n".join(lines)

    def _generate_appendix_section(self, data: dict[str, Any]) -> str:
        """Generate appendix with metadata and configuration."""
        # This method is no longer used - metadata section has been removed
        return ""

    def _convert_markdown_to_html(self, markdown_content: str) -> str:
        """Convert Markdown content to HTML with embedded CSS."""

        # Simple Markdown to HTML conversion
        html_body = self._simple_markdown_to_html(markdown_content)

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gerrit Project Analysis Report</title>
    {self._get_datatable_css()}
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #ffffff;
            color: #333333;
        }}

        h1, h2, h3 {{
            color: #2c3e50;
            margin-top: 2em;
            margin-bottom: 0.5em;
        }}

        h1 {{
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}

        h2 {{
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1em 0;
            font-size: 0.9em;
        }}

        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}

        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }}

        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}

        tr:hover {{
            background-color: #e8f4f8;
        }}

        code {{
            background-color: #f1f2f6;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}

        .emoji {{
            font-size: 1.1em;
        }}

        .number {{
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-weight: 500;
        }}

        .metadata {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 1em 0;
            border-left: 4px solid #3498db;
        }}

        .footer {{
            text-align: center;
            margin-top: 3em;
            padding-top: 2em;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
        }}

        /* CI/CD Job Status Styling */
        .status-success {{
            color: #28a745;
            font-weight: 500;
        }}

        .status-failure {{
            color: #dc3545;
            font-weight: 500;
        }}

        .status-warning {{
            color: #ffc107;
            font-weight: 500;
        }}

        .status-building {{
            color: #007bff;
            font-weight: 500;
        }}

        .status-disabled {{
            color: #6c757d;
            font-style: italic;
        }}

        .status-cancelled {{
            color: #fd7e14;
            font-weight: 500;
        }}

        .status-unknown {{
            color: #6c757d;
        }}

        .status-in-progress {{
            color: #007bff;
            font-weight: 500;
        }}

        .status-neutral {{
            color: #6c757d;
            font-weight: 500;
        }}

        .status-skipped {{
            color: #6c757d;
            font-style: italic;
        }}

        .status-no-runs {{
            color: #6c757d;
            font-style: italic;
        }}

        /* Hover effects for better UX */
        .workflow-status:hover, .jenkins-status:hover {{
            text-decoration: underline;
            cursor: default;
        }}

        /* Tooltip for non-mirrored repositories */
        .mirror-warning {{
            cursor: help;
            position: relative;
            display: inline-block;
        }}

        .mirror-warning .tooltip-text {{
            visibility: hidden;
            width: 180px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 8px;
            position: absolute;
            z-index: 1000;
            bottom: 125%;
            left: 50%;
            margin-left: -90px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 13px;
            font-weight: normal;
            white-space: nowrap;
        }}

        .mirror-warning .tooltip-text::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #333 transparent transparent transparent;
        }}

        .mirror-warning:hover .tooltip-text {{
            visibility: visible;
            opacity: 1;
        }}

        /* Custom styles for Simple-DataTables integration */
        .dataTable-wrapper {{
            margin: 1em 0;
        }}

        .dataTable-top, .dataTable-bottom {{
            padding: 8px 0;
        }}

        .dataTable-search {{
            margin-bottom: 1em;
        }}

        .dataTable-search input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            width: 250px;
        }}

        .dataTable-selector select {{
            padding: 6px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}

        .dataTable-info {{
            color: #666;
            font-size: 14px;
        }}

        .dataTable-pagination a {{
            padding: 6px 12px;
            margin: 0 2px;
            border: 1px solid #ddd;
            border-radius: 4px;
            text-decoration: none;
            color: #2c3e50;
        }}

        .dataTable-pagination a:hover {{
            background-color: #e8f4f8;
        }}

        .dataTable-pagination a.active {{
            background-color: #3498db;
            color: white;
            border-color: #3498db;
        }}

        /* Custom column widths for specific tables */
        .feature-matrix-table th:nth-child(1) {{ width: 30%; }} /* Gerrit Project */
        .feature-matrix-table th:nth-child(2) {{ width: 12%; }} /* Type */
        .feature-matrix-table th:nth-child(3) {{ width: 12%; }} /* Dependabot */
        .feature-matrix-table th:nth-child(4) {{ width: 12%; }} /* Pre-commit */
        .feature-matrix-table th:nth-child(5) {{ width: 12%; }} /* ReadTheDocs */
        .feature-matrix-table th:nth-child(6) {{ width: 12%; }} /* .gitreview */
        .feature-matrix-table th:nth-child(7) {{ width: 10%; }} /* Status */

        /* CI/CD Jobs table - handles both 4 and 5 column layouts */
        .cicd-jobs-table th:nth-child(1) {{ width: 20%; }} /* Gerrit Project */
        .cicd-jobs-table th:nth-child(2) {{ width: 30%; }} /* GitHub Workflows */
        .cicd-jobs-table th:nth-child(3) {{ width: 15%; }} /* Workflow Count */
        .cicd-jobs-table th:nth-child(4) {{ width: 35%; }} /* Job Count (4-col) or Jenkins Jobs (5-col) */
        .cicd-jobs-table th:nth-child(5) {{ width: 15%; }} /* Job Count (5-col only) */
    </style>
</head>
<body>
    {html_body}
    {self._get_datatable_js()}
</body>
</html>"""

        return html_template

    def _simple_markdown_to_html(self, markdown: str) -> str:
        """Simple Markdown to HTML conversion for tables and headers."""
        import re

        html_lines = []
        lines = markdown.split("\n")
        in_table = False

        i = 0
        while i < len(lines):
            line = lines[i]

            # Headers
            if line.startswith("# "):
                content = line[2:].strip()
                html_lines.append(f'<h1 id="{self._slugify(content)}">{content}</h1>')
            elif line.startswith("## "):
                content = line[3:].strip()
                html_lines.append(f'<h2 id="{self._slugify(content)}">{content}</h2>')
            elif line.startswith("### "):
                content = line[4:].strip()
                html_lines.append(f'<h3 id="{self._slugify(content)}">{content}</h3>')

            # Tables
            elif "|" in line and line.strip():
                if not in_table:
                    # Check if this table will have headers by looking ahead
                    has_headers = i + 1 < len(lines) and re.match(
                        r"^\|[\s\-\|]+\|$", lines[i + 1].strip()
                    )
                    # Only add sortable class if feature is enabled and table has headers
                    sortable_enabled = self.config.get("html_tables", {}).get(
                        "sortable", True
                    )

                    # Check if this is the feature matrix table or combined repositories table by looking for specific headers
                    is_feature_matrix = False
                    is_cicd_jobs = False
                    is_all_repositories = False
                    is_global_summary = False
                    if has_headers and i < len(lines):
                        table_header = line.lower()
                        if (
                            "gerrit project" in table_header
                            and "dependabot" in table_header
                            and "pre-commit" in table_header
                        ):
                            is_feature_matrix = True
                        elif "gerrit project" in table_header and (
                            "github workflows" in table_header
                            or "jenkins jobs" in table_header
                        ):
                            is_cicd_jobs = True
                        elif (
                            "gerrit project" in table_header
                            and "commits" in table_header
                            and "status" in table_header
                        ):
                            is_all_repositories = True
                        elif (
                            "metric" in table_header
                            and "count" in table_header
                            and "percentage" in table_header
                        ):
                            is_global_summary = True

                    table_class = (
                        ' class="sortable"'
                        if (has_headers and sortable_enabled)
                        else ""
                    )
                    if is_feature_matrix:
                        table_class = (
                            ' class="sortable no-pagination feature-matrix-table"'
                        )
                    elif is_cicd_jobs:
                        table_class = ' class="sortable no-pagination cicd-jobs-table"'
                    elif is_all_repositories:
                        table_class = ' class="sortable"'
                    elif is_global_summary:
                        table_class = ' class="no-search no-pagination"'

                    html_lines.append(f"<table{table_class}>")
                    in_table = True

                # Check if this is a header separator line
                if re.match(r"^\|[\s\-\|]+\|$", line.strip()):
                    # Skip separator line
                    pass
                else:
                    # Regular table row
                    cells = [
                        cell.strip() for cell in line.split("|")[1:-1]
                    ]  # Remove empty first/last

                    # Determine if this is likely a header row (check next line)
                    is_header = i + 1 < len(lines) and re.match(
                        r"^\|[\s\-\|]+\|$", lines[i + 1].strip()
                    )

                    if is_header:
                        html_lines.append("<thead><tr>")
                        for cell in cells:
                            html_lines.append(f"<th>{cell}</th>")
                        html_lines.append("</tr></thead><tbody>")
                    else:
                        html_lines.append("<tr>")
                        for cell in cells:
                            html_lines.append(f"<td>{cell}</td>")
                        html_lines.append("</tr>")

            # End table when we hit a non-table line
            elif in_table and not ("|" in line and line.strip()):
                html_lines.append("</tbody></table>")
                in_table = False
                # Process this line normally
                if line.strip():
                    html_lines.append(f"<p>{line}</p>")
                else:
                    html_lines.append("")

            # Regular paragraphs
            elif line.strip() and not in_table:
                # Bold text
                line = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", line)
                # Code blocks
                line = re.sub(r"`(.*?)`", r"<code>\1</code>", line)
                html_lines.append(f"<p>{line}</p>")

            # Empty lines
            else:
                if not in_table:
                    html_lines.append("")

            i += 1

        # Close table if still open
        if in_table:
            html_lines.append("</tbody></table>")

        return "\n".join(html_lines)

    def _get_datatable_css(self) -> str:
        """Get Simple-DataTables CSS if sorting is enabled."""
        if not self.config.get("html_tables", {}).get("sortable", True):
            return ""

        return """
    <!-- Simple-DataTables CSS -->
    <link href="https://cdn.jsdelivr.net/npm/simple-datatables@latest/dist/style.css" rel="stylesheet" type="text/css">
    """

    def _get_datatable_js(self) -> str:
        """Get Simple-DataTables JavaScript if sorting is enabled."""
        if not self.config.get("html_tables", {}).get("sortable", True):
            return ""

        min_rows = self.config.get("html_tables", {}).get("min_rows_for_sorting", 3)
        searchable = str(
            self.config.get("html_tables", {}).get("searchable", True)
        ).lower()
        sortable = str(self.config.get("html_tables", {}).get("sortable", True)).lower()
        pagination = str(
            self.config.get("html_tables", {}).get("pagination", True)
        ).lower()
        per_page = self.config.get("html_tables", {}).get("entries_per_page", 50)
        page_options = self.config.get("html_tables", {}).get(
            "page_size_options", [20, 50, 100, 200]
        )

        return f"""
    <!-- Simple-DataTables JavaScript -->
    <script src="https://cdn.jsdelivr.net/npm/simple-datatables@latest" type="text/javascript"></script>
    <script>
        // Initialize Simple-DataTables on all tables with the sortable class
        document.addEventListener('DOMContentLoaded', function() {{
            const tables = document.querySelectorAll('table.sortable');
            tables.forEach(function(table) {{
                // Skip tables that are too small to benefit from sorting
                const rows = table.querySelectorAll('tbody tr');
                if (rows.length < {min_rows}) {{
                    return;
                }}

                // Check if this table should have pagination disabled
                const noPagination = table.classList.contains('no-pagination');
                const noSearch = table.classList.contains('no-search');
                const usePagination = noPagination ? false : {pagination};
                const useSearch = noSearch ? false : {searchable};

                new simpleDatatables.DataTable(table, {{
                    searchable: useSearch,
                    sortable: {sortable},
                    paging: usePagination,
                    perPage: {per_page},
                    perPageSelect: {page_options},
                    classes: {{
                        active: "active",
                        disabled: "disabled"
                    }},
                    labels: {{
                        placeholder: "Search repositories, contributors, etc...",
                        perPage: "entries per page",
                        noRows: "No entries found",
                        info: "Showing {{start}} to {{end}} of {{rows}} entries"
                    }}
                }});
            }});
        }});
    </script>"""

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug."""
        from util.formatting import slugify
        result: str = slugify(text)
        return result

    def _format_number(self, num: Union[int, float], signed: bool = False) -> str:
        """Format number with K/M/B abbreviation.

        Delegates to unified format_number utility.
        """
        result: str = format_number(num, signed=signed)
        return result

    def _format_age(self, days: int) -> str:
        """Format age in days to actual date.

        Delegates to unified format_age utility.
        """
        result: str = format_age(days)
        return result
