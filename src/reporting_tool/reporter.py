#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Repository Reporter - Main Orchestration Module

This module contains the RepositoryReporter class which orchestrates the entire
repository analysis workflow, including:
- Repository discovery and scanning
- Git data collection coordination
- Feature detection coordination
- Data aggregation
- Report rendering and output generation

The RepositoryReporter acts as the main controller that ties together all the
subsystems (collectors, aggregators, renderers) to produce comprehensive
repository analysis reports.
"""

import atexit
import concurrent.futures
import datetime
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Optional, cast

from reporting_tool.aggregators import DataAggregator
from reporting_tool.collectors import GitDataCollector
from reporting_tool.features import FeatureRegistry
from reporting_tool.renderers import ReportRenderer
from util.git import safe_git_command
from util.zip_bundle import create_report_bundle
from reporting_tool.config import save_resolved_config

# Global API statistics (imported from main module)
try:
    from generate_reports import api_stats
except ImportError:
    # Fallback for testing or standalone usage
    api_stats = None


class RepositoryReporter:
    """Main orchestrator for repository reporting."""

    def __init__(self, config: dict[str, Any], logger: logging.Logger) -> None:
        """
        Initialize the repository reporter.

        Args:
            config: Merged configuration dictionary
            logger: Logger instance for reporting progress and issues
        """
        self.config = config
        self.logger = logger
        self.git_collector = GitDataCollector(config, {}, logger)
        self.feature_registry = FeatureRegistry(config, logger)
        self.aggregator = DataAggregator(config, logger)
        self.renderer = ReportRenderer(config, logger)
        self.info_master_temp_dir: Optional[str] = None

    def _cleanup_info_master_repo(self) -> None:
        """Clean up the temporary info-master repository directory."""
        if self.info_master_temp_dir and os.path.exists(self.info_master_temp_dir):
            try:
                self.logger.info(
                    f"Cleaning up info-master repository at {self.info_master_temp_dir}"
                )
                shutil.rmtree(self.info_master_temp_dir)
                self.logger.info("Successfully cleaned up info-master repository")
            except Exception as e:
                self.logger.warning(f"Failed to clean up info-master repository: {e}")

    def _clone_info_master_repo(self) -> Optional[Path]:
        """
        Clone the info-master repository for additional context data.

        Returns the path to the cloned repository in a temporary directory,
        or None if cloning failed.
        """
        # Create a temporary directory for info-master
        self.info_master_temp_dir = tempfile.mkdtemp(prefix="info-master-")
        info_master_path = Path(self.info_master_temp_dir) / "info-master"
        info_master_url = "ssh://modesevenindustrialsolutions@gerrit.linuxfoundation.org:29418/releng/info-master"

        self.logger.info(
            f"Cloning info-master repository to temporary location: {info_master_path}"
        )
        success, output = safe_git_command(
            ["git", "clone", info_master_url, str(info_master_path)],
            Path(self.info_master_temp_dir),
            self.logger,
        )

        if success:
            if api_stats:
                api_stats.record_info_master(True)
            self.logger.info("✅ Successfully cloned info-master repository")
            # Register cleanup handler
            atexit.register(self._cleanup_info_master_repo)
            return info_master_path
        else:
            error_msg = f"Clone failed: {output[:200]}" if output else "Clone failed"
            if api_stats:
                api_stats.record_info_master(False, error_msg)
            self.logger.error(f"❌ Failed to clone info-master repository: {output}")
            # Clean up the temp directory if clone failed
            if os.path.exists(self.info_master_temp_dir):
                shutil.rmtree(self.info_master_temp_dir)
            self.info_master_temp_dir = None
            return None

    def analyze_repositories(self, repos_path: Path) -> dict[str, Any]:
        """
        Main analysis workflow.

        Coordinates all phases of repository analysis:
        1. Clone info-master for additional context
        2. Initialize report data structure
        3. Discover all repositories
        4. Analyze repositories in parallel
        5. Aggregate data across repositories
        6. Generate Jenkins allocation summary

        Args:
            repos_path: Path to directory containing repositories to analyze

        Returns:
            Complete report data dictionary with all analysis results
        """
        # Resolve to absolute path for consistent handling
        repos_path_abs = repos_path.resolve()
        self.logger.info(f"Starting repository analysis in {repos_path_abs}")

        # Clone info-master repository for additional context
        # This is cloned to a temporary directory to avoid it appearing in the report
        info_master_path = self._clone_info_master_repo()
        if info_master_path:
            self.logger.info(f"Info-master repository available at: {info_master_path}")
        else:
            self.logger.warning(
                "Info-master repository not available - continuing without it"
            )

        # Initialize data structure
        # Pass schema_version and script_version from constants in main module
        report_data = {
            "schema_version": self.config.get("_schema_version", "1.0.0"),
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "project": self.config["project"],
            "config_digest": self._compute_config_digest(self.config),
            "script_version": self.config.get("_script_version", "1.0.0"),
            "time_windows": self._setup_time_windows(self.config),
            "repositories": [],
            "authors": [],
            "organizations": [],
            "summaries": {},
            "errors": [],
        }

        # Update git collector with time windows
        self.git_collector.time_windows = cast(
            dict[str, dict[str, Any]], report_data["time_windows"]
        )

        # Update git collector with repos_path for relative path calculation
        self.git_collector.repos_path = repos_path_abs

        # Find all repository directories
        repo_dirs = self._discover_repositories(repos_path_abs)
        self.logger.info(f"Found {len(repo_dirs)} repositories to analyze")

        # Analyze repositories (with concurrency)
        repo_metrics = self._analyze_repositories_parallel(repo_dirs)

        # Extract successful metrics and errors
        successful_repos = []
        for metrics in repo_metrics:
            if "error" in metrics:
                cast(list[dict[str, Any]], report_data["errors"]).append(metrics)
            else:
                # Extract the repository record with embedded author data
                successful_repos.append(metrics["repository"])

        report_data["repositories"] = successful_repos

        # Aggregate data (pass repository records directly)
        report_data["authors"] = self.aggregator.compute_author_rollups(
            successful_repos
        )
        report_data["organizations"] = self.aggregator.compute_org_rollups(
            report_data["authors"]
        )
        report_data["summaries"] = self.aggregator.aggregate_global_data(
            successful_repos
        )

        # Log comprehensive Jenkins job allocation summary for auditing
        if (
            self.git_collector.jenkins_client
            and self.git_collector._jenkins_initialized
        ):
            allocation_summary = self.git_collector.get_jenkins_job_allocation_summary()

            self.logger.info(f"Jenkins job allocation summary:")
            self.logger.info(
                f"  Total jobs: {allocation_summary['total_jenkins_jobs']}"
            )
            self.logger.info(f"  Allocated: {allocation_summary['allocated_jobs']}")
            self.logger.info(f"  Unallocated: {allocation_summary['unallocated_jobs']}")
            self.logger.info(
                f"  Allocation rate: {allocation_summary['allocation_percentage']}%"
            )

            # Validate allocation and report any issues
            validation_issues = self.git_collector.validate_jenkins_job_allocation()
            if validation_issues:
                self.logger.error("CRITICAL: Jenkins job allocation issues detected:")
                for issue in validation_issues:
                    self.logger.error(f"  - {issue}")

                # Infrastructure jobs are not fatal - only log as warning
                self.logger.warning(
                    "Some Jenkins jobs could not be allocated, but continuing with report generation"
                )

                # Get final counts for reporting
                allocation_summary = (
                    self.git_collector.get_jenkins_job_allocation_summary()
                )
                orphaned_summary = (
                    self.git_collector.get_orphaned_jenkins_jobs_summary()
                )

                total_jobs = allocation_summary.get("total_jenkins_jobs", 0)
                allocated_jobs = allocation_summary.get("allocated_jobs", 0)
                orphaned_jobs = orphaned_summary.get("total_orphaned_jobs", 0)

                self.logger.info(
                    f"Final Jenkins job allocation: {allocated_jobs}/{total_jobs} active, {orphaned_jobs} orphaned"
                )
            else:
                self.logger.info("Jenkins job allocation validation: No issues found")

            # Add allocation data to report for debugging
            report_data["jenkins_allocation"] = allocation_summary

            # Add orphaned jobs data to report
            orphaned_summary = self.git_collector.get_orphaned_jenkins_jobs_summary()
            report_data["orphaned_jenkins_jobs"] = orphaned_summary
            if orphaned_summary["total_orphaned_jobs"] > 0:
                self.logger.info(
                    f"Found {orphaned_summary['total_orphaned_jobs']} Jenkins jobs belonging to archived Gerrit projects"
                )
                for state, count in orphaned_summary["by_state"].items():
                    self.logger.info(f"  - {count} jobs for {state} projects")

        self.logger.info(
            f"Analysis complete: {len(report_data['repositories'])} repositories, {len(report_data['errors'])} errors"
        )

        return report_data

    def generate_reports(self, repos_path: Path, output_dir: Path) -> dict[str, Path]:
        """
        Generate complete reports (JSON, Markdown, HTML, ZIP).

        This is a convenience method that combines analysis and rendering into
        a single call. It:
        1. Analyzes all repositories
        2. Generates JSON report
        3. Generates Markdown report
        4. Generates HTML report (if enabled)
        5. Saves resolved configuration
        6. Creates ZIP bundle (if enabled)

        Args:
            repos_path: Path to directory containing repositories
            output_dir: Path to output directory for generated reports

        Returns:
            Dictionary mapping output type to file path for all generated files
        """
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Analyze repositories
        report_data = self.analyze_repositories(repos_path)

        # Define output paths
        project = self.config["project"]
        json_path = output_dir / "report_raw.json"
        markdown_path = output_dir / "report.md"
        html_path = output_dir / "report.html"
        config_path = output_dir / "config_resolved.json"

        generated_files = {}

        # Generate JSON report
        self.renderer.render_json_report(report_data, json_path)
        generated_files["json"] = json_path

        # Generate Markdown report
        markdown_content = self.renderer.render_markdown_report(
            report_data, markdown_path
        )
        generated_files["markdown"] = markdown_path

        # Generate HTML report (if not disabled)
        if not self.config.get("output", {}).get("no_html", False):
            self.renderer.render_html_report(markdown_content, html_path)
            generated_files["html"] = html_path

        # Save resolved configuration
        save_resolved_config(self.config, config_path)
        generated_files["config"] = config_path

        # Create ZIP bundle (if not disabled)
        if not self.config.get("output", {}).get("no_zip", False):
            zip_path = create_report_bundle(output_dir, project, self.logger)
            generated_files["zip"] = zip_path

        return generated_files

    def _discover_repositories(self, repos_path: Path) -> list[Path]:
        """
        Find all repository directories recursively with no artificial depth limit.

        Args:
            repos_path: Root path to search for repositories

        Returns:
            List of paths to discovered Git repositories, sorted by depth
            (deepest first) to ensure child projects get processed before parents

        Raises:
            FileNotFoundError: If repos_path does not exist
        """
        if not repos_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {repos_path}")

        self.logger.info(f"Discovering repositories recursively under: {repos_path}")

        repo_dirs: list[Path] = []
        access_errors = 0

        # Use rglob to discover all .git directories without a depth limit
        try:
            for git_dir in repos_path.rglob(".git"):
                try:
                    if git_dir.exists():
                        repo_dir = git_dir.parent

                        # Use relative path from repos_path for clean logging (fallback to absolute)
                        try:
                            rel_path = str(repo_dir.relative_to(repos_path))
                        except ValueError:
                            rel_path = str(repo_dir)

                        self.logger.debug(f"Found git repository: {rel_path}")

                        # Validate against Gerrit API cache if available
                        if getattr(self.git_collector, "gerrit_projects_cache", None):
                            if rel_path in self.git_collector.gerrit_projects_cache:
                                self.logger.debug(
                                    f"Verified {rel_path} exists in Gerrit"
                                )
                            else:
                                self.logger.warning(
                                    f"Repository {rel_path} not found in Gerrit API cache"
                                )

                        repo_dirs.append(repo_dir)
                except (PermissionError, OSError) as e:
                    access_errors += 1
                    self.logger.debug(
                        f"Cannot access potential repository at {git_dir}: {e}"
                    )
        except (PermissionError, OSError) as e:
            self.logger.warning(f"Error during repository discovery: {e}")

        # Deduplicate and sort results by path depth (deepest first) to ensure
        # child projects get processed before parent projects for Jenkins job allocation
        unique_repos = list({p.resolve() for p in repo_dirs})
        unique_repos.sort(key=lambda p: (-len(p.parts), str(p)))

        self.logger.info(f"Discovered {len(unique_repos)} git repositories")
        if access_errors:
            self.logger.debug(
                f"Encountered {access_errors} access errors during discovery"
            )

        return unique_repos

    def _analyze_repositories_parallel(
        self, repo_dirs: list[Path]
    ) -> list[dict[str, Any]]:
        """
        Analyze repositories with optional concurrency.

        Args:
            repo_dirs: List of repository paths to analyze

        Returns:
            List of analysis results (metrics or error records)
        """
        max_workers = self.config.get("performance", {}).get("max_workers", 8)

        if max_workers == 1:
            # Sequential processing
            return [self._analyze_single_repository(repo_dir) for repo_dir in repo_dirs]

        # Concurrent processing
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_repo = {
                executor.submit(self._analyze_single_repository, repo_dir): repo_dir
                for repo_dir in repo_dirs
            }

            for future in concurrent.futures.as_completed(future_to_repo):
                repo_dir = future_to_repo[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to analyze {repo_dir.name}: {e}")
                    results.append(
                        {
                            "error": str(e),
                            "repo": repo_dir.name,
                            "category": "analysis_failure",
                        }
                    )

        return results

    def _analyze_single_repository(self, repo_path: Path) -> dict[str, Any]:
        """
        Analyze a single repository.

        Args:
            repo_path: Path to repository to analyze

        Returns:
            Repository metrics dictionary or error record
        """
        try:
            self.logger.debug(f"Analyzing repository: {repo_path.name}")

            # Collect Git metrics
            repo_metrics = self.git_collector.collect_repo_git_metrics(repo_path)

            # Scan features
            repo_features = self.feature_registry.detect_features(repo_path)
            repo_metrics["repository"]["features"] = repo_features

            return dict(repo_metrics)

        except Exception as e:
            self.logger.error(f"Error analyzing {repo_path.name}: {e}")
            return {
                "error": str(e),
                "repo": repo_path.name,
                "category": "repository_analysis",
            }

    def _compute_config_digest(self, config: dict[str, Any]) -> str:
        """
        Compute SHA256 digest of configuration for reproducibility tracking.

        Args:
            config: Configuration dictionary

        Returns:
            Hexadecimal SHA256 digest string
        """
        import hashlib
        import json

        config_json = json.dumps(config, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(config_json.encode("utf-8")).hexdigest()

    def _setup_time_windows(self, config: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """
        Compute time window boundaries based on configuration.

        Args:
            config: Configuration dictionary with time_windows settings

        Returns:
            Dictionary with window definitions including start/end timestamps
        """
        from datetime import timedelta

        now = datetime.datetime.now(datetime.timezone.utc)
        windows = {}

        # Default time windows if not specified
        default_windows = {
            "last_30_days": 30,
            "last_90_days": 90,
            "last_365_days": 365,
            "last_3_years": 1095,
        }

        time_window_config = config.get("time_windows", default_windows)

        for window_name, days in time_window_config.items():
            start_date = now - timedelta(days=days)
            windows[window_name] = {
                "days": days,
                "start": start_date.isoformat(),
                "end": now.isoformat(),
                "start_timestamp": start_date.timestamp(),
                "end_timestamp": now.timestamp(),
            }

        return windows
