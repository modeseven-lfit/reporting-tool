#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Main entry point for reporting-tool.

This module provides the core orchestration logic for report generation,
coordinating configuration loading, repository analysis, and output generation.
"""

import copy
import datetime
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import yaml
except ImportError:
    print(
        "ERROR: PyYAML is required. Install with: pip install PyYAML", file=sys.stderr
    )
    sys.exit(1)

# Import utility modules
from util.zip_bundle import create_report_bundle
from util.github_org import determine_github_org

# Import configuration utilities
from reporting_tool.config import save_resolved_config

# Import main orchestration
from reporting_tool.reporter import RepositoryReporter


# =============================================================================
# CONSTANTS AND SCHEMA DEFINITIONS
# =============================================================================

SCRIPT_VERSION = "1.0.0"
SCHEMA_VERSION = "1.0.0"
DEFAULT_CONFIG_DIR = "configuration"
DEFAULT_OUTPUT_DIR = "reports"

# Default time windows (can be overridden in config)
DEFAULT_TIME_WINDOWS = {
    "last_30_days": 30,
    "last_90_days": 90,
    "last_365_days": 365,
    "last_3_years": 1095,
}


# =============================================================================
# API STATISTICS TRACKING
# =============================================================================


class APIStatistics:
    """Track statistics for external API calls (GitHub, Gerrit, Jenkins)."""

    def __init__(self):
        """Initialize statistics tracker."""
        self.stats: Dict[str, Dict[str, Any]] = {
            "github": {"success": 0, "errors": {}},
            "gerrit": {"success": 0, "errors": {}},
            "jenkins": {"success": 0, "errors": {}},
            "info_master": {"success": False, "error": None},
        }

    def record_success(self, api_type: str) -> None:
        """Record a successful API call."""
        if api_type in self.stats and isinstance(self.stats[api_type]["success"], int):
            self.stats[api_type]["success"] += 1

    def record_error(self, api_type: str, status_code: int) -> None:
        """Record an API error by status code."""
        if api_type in self.stats:
            errors: Dict[Union[int, str], int] = self.stats[api_type]["errors"]
            errors[status_code] = errors.get(status_code, 0) + 1

    def record_exception(self, api_type: str, error_type: str = "exception") -> None:
        """Record an API exception (non-HTTP error)."""
        if api_type in self.stats:
            errors: Dict[Union[int, str], int] = self.stats[api_type]["errors"]
            errors[error_type] = errors.get(error_type, 0) + 1

    def record_info_master(self, success: bool, error: Optional[str] = None) -> None:
        """Record info-master clone status."""
        self.stats["info_master"]["success"] = success
        if error:
            self.stats["info_master"]["error"] = error

    def get_total_calls(self, api_type: str) -> int:
        """Get total number of API calls (success + errors)."""
        if api_type not in self.stats:
            return 0
        success = self.stats[api_type]["success"]
        if not isinstance(success, int):
            return 0
        errors_dict: Dict[Union[int, str], int] = self.stats[api_type]["errors"]
        errors = sum(errors_dict.values())
        return success + errors

    def get_total_errors(self, api_type: str) -> int:
        """Get total number of errors for an API."""
        if api_type not in self.stats:
            return 0
        errors_dict: Dict[Union[int, str], int] = self.stats[api_type]["errors"]
        return sum(errors_dict.values())

    def has_errors(self) -> bool:
        """Check if any API has errors."""
        for api_type in ["github", "gerrit", "jenkins"]:
            if self.get_total_errors(api_type) > 0:
                return True
        if not self.stats["info_master"]["success"] and self.stats["info_master"]["error"]:
            return True
        return False

    def format_console_output(self) -> str:
        """Format statistics for console output."""
        lines = []

        # GitHub API stats
        if self.get_total_calls("github") > 0:
            lines.append("\n📊 GitHub API Statistics:")
            lines.append(f"   ✅ Successful calls: {self.stats['github']['success']}")
            total_errors = self.get_total_errors("github")
            if total_errors > 0:
                lines.append(f"   ❌ Failed calls: {total_errors}")
                errors_dict: Dict[Union[int, str], int] = self.stats["github"]["errors"]
                for code, count in sorted(errors_dict.items(), key=lambda x: str(x[0])):
                    lines.append(f"      • Error {code}: {count}")

        # Gerrit API stats
        if self.get_total_calls("gerrit") > 0:
            lines.append("\n📊 Gerrit API Statistics:")
            lines.append(f"   ✅ Successful calls: {self.stats['gerrit']['success']}")
            total_errors = self.get_total_errors("gerrit")
            if total_errors > 0:
                lines.append(f"   ❌ Failed calls: {total_errors}")
                gerrit_errors: Dict[Union[int, str], int] = self.stats["gerrit"]["errors"]
                for code, count in sorted(gerrit_errors.items(), key=lambda x: str(x[0])):
                    lines.append(f"      • Error {code}: {count}")

        # Jenkins API stats
        if self.get_total_calls("jenkins") > 0:
            lines.append("\n📊 Jenkins API Statistics:")
            lines.append(f"   ✅ Successful calls: {self.stats['jenkins']['success']}")
            total_errors = self.get_total_errors("jenkins")
            if total_errors > 0:
                lines.append(f"   ❌ Failed calls: {total_errors}")
                jenkins_errors: Dict[Union[int, str], int] = self.stats["jenkins"]["errors"]
                for code, count in sorted(jenkins_errors.items(), key=lambda x: str(x[0])):
                    lines.append(f"      • Error {code}: {count}")

        # Info-master clone status
        if self.stats["info_master"]["success"]:
            lines.append("\n📊 Info-Master Clone:")
            lines.append("   ✅ Successfully cloned")
        elif self.stats["info_master"]["error"]:
            lines.append("\n📊 Info-Master Clone:")
            lines.append(f"   ❌ {self.stats['info_master']['error']}")

        return "\n".join(lines) if lines else ""

    def write_to_step_summary(self) -> None:
        """Write API statistics to GitHub Step Summary."""
        step_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if not step_summary_file:
            return

        try:
            with open(step_summary_file, "a") as f:
                f.write("\n## 📊 API Statistics\n\n")

                # GitHub API
                if self.get_total_calls("github") > 0:
                    f.write("### GitHub API\n")
                    f.write(f"- ✅ Successful calls: {self.stats['github']['success']}\n")
                    total_errors = self.get_total_errors("github")
                    if total_errors > 0:
                        f.write(f"- ❌ Failed calls: {total_errors}\n")
                        for code, count in sorted(self.stats["github"]["errors"].items()):
                            f.write(f"  - Error {code}: {count}\n")
                    f.write("\n")

                # Gerrit API
                if self.get_total_calls("gerrit") > 0:
                    f.write("### Gerrit API\n")
                    f.write(f"- ✅ Successful calls: {self.stats['gerrit']['success']}\n")
                    total_errors = self.get_total_errors("gerrit")
                    if total_errors > 0:
                        f.write(f"- ❌ Failed calls: {total_errors}\n")
                        for code, count in sorted(self.stats["gerrit"]["errors"].items()):
                            f.write(f"  - Error {code}: {count}\n")
                    f.write("\n")

                # Jenkins API
                if self.get_total_calls("jenkins") > 0:
                    f.write("### Jenkins API\n")
                    f.write(f"- ✅ Successful calls: {self.stats['jenkins']['success']}\n")
                    total_errors = self.get_total_errors("jenkins")
                    if total_errors > 0:
                        f.write(f"- ❌ Failed calls: {total_errors}\n")
                        for code, count in sorted(self.stats["jenkins"]["errors"].items()):
                            f.write(f"  - Error {code}: {count}\n")
                    f.write("\n")

                # Info-master
                if self.stats["info_master"]["success"] or self.stats["info_master"]["error"]:
                    f.write("### Info-Master Clone\n")
                    if self.stats["info_master"]["success"]:
                        f.write("- ✅ Successfully cloned\n")
                    elif self.stats["info_master"]["error"]:
                        f.write(f"- ❌ {self.stats['info_master']['error']}\n")
                    f.write("\n")

        except Exception as e:
            print(f"Warning: Could not write API stats to step summary: {e}", file=sys.stderr)


# Global API statistics instance
api_stats = APIStatistics()


# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================


def setup_logging(
    level: str = "INFO", include_timestamps: bool = True
) -> logging.Logger:
    """Configure logging with structured format."""
    log_format = "[%(levelname)s]"
    if include_timestamps:
        log_format = "[%(asctime)s] " + log_format
    log_format += " %(message)s"

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )

    return logging.getLogger(__name__)


def deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two dictionaries, with override taking precedence."""
    result = copy.deepcopy(base)

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = copy.deepcopy(value)

    return result


def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML configuration file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {config_path}: {e}")


def load_configuration(config_dir: Path, project: str) -> dict[str, Any]:
    """
    Load configuration with template + project override merge strategy.

    Args:
        config_dir: Directory containing configuration files
        project: Project name for override file

    Returns:
        Merged configuration dictionary
    """
    # Load template configuration
    template_path = config_dir / "template.config"
    template_config = load_yaml_config(template_path)

    # Load project-specific configuration
    project_config_path = config_dir / f"{project}.config"
    project_config = load_yaml_config(project_config_path)

    # Merge configurations (project overrides template)
    if template_config and project_config:
        merged = deep_merge_dicts(template_config, project_config)
    elif project_config:
        merged = project_config
    else:
        merged = template_config

    # Ensure required fields
    merged.setdefault("project", project)
    merged.setdefault("schema_version", SCHEMA_VERSION)
    merged.setdefault("time_windows", DEFAULT_TIME_WINDOWS)

    # Validate time_windows
    if "time_windows" in merged:
        for window_name, days in merged["time_windows"].items():
            if not isinstance(days, int) or days < 0:
                raise ValueError(
                    f"Invalid time window '{window_name}': must be a positive integer"
                )

    return merged


def compute_config_digest(config: Dict[str, Any]) -> str:
    """Compute SHA256 digest of configuration for reproducibility tracking."""
    config_json = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(config_json.encode("utf-8")).hexdigest()


def write_config_to_step_summary(config: dict[str, Any], project: str) -> None:
    """Write configuration information to GitHub Step Summary."""
    step_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not step_summary_file:
        return

    try:
        current_days = config.get("activity_thresholds", {}).get("current_days", "N/A")
        active_days = config.get("activity_thresholds", {}).get("active_days", "N/A")

        with open(step_summary_file, "a") as f:
            f.write(f"## 🔧 Configuration for {project}\n\n")
            f.write("| Setting | Value |\n")
            f.write("|---------|-------|\n")
            f.write(f"| Schema Version | {config.get('schema_version', 'N/A')} |\n")
            f.write(f"| Current Threshold | {current_days} days |\n")
            f.write(f"| Active Threshold | {active_days} days |\n")
            f.write(f"| Time Windows | {len(config.get('time_windows', {}))} |\n")
            f.write(
                f"| Features Enabled | {len(config.get('features', {}).get('enabled', []))} |\n"
            )
            f.write("\n")

    except Exception as e:
        print(f"Warning: Could not write config to step summary: {e}", file=sys.stderr)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main(args=None) -> int:
    """
    Main entry point for report generation.

    Args:
        args: Parsed arguments namespace (from argparse or CLI)

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    try:
        # If args not provided, parse from command line
        if args is None:
            from cli import parse_arguments
            args = parse_arguments()

        # Load configuration
        try:
            config = load_configuration(args.config_dir, args.project)
        except Exception as e:
            print(f"ERROR: Failed to load configuration: {e}", file=sys.stderr)
            return 1

        # Determine GitHub organization once - centralized
        github_org, github_org_source = determine_github_org(args.repos_path)

        if github_org:
            # Store in config for all components to use
            config["github"] = github_org
            config["_github_org_source"] = github_org_source

            # Log what we determined
            if github_org_source == "auto_derived":
                print(f"ℹ️  Derived GitHub organization '{github_org}' from repository path", file=sys.stderr)
            elif github_org_source == "environment_variable":
                print(f"ℹ️  GitHub organization '{github_org}' from PROJECTS_JSON", file=sys.stderr)

        # Inject script and schema versions into config for reporter
        config["_script_version"] = SCRIPT_VERSION
        config["_schema_version"] = SCHEMA_VERSION

        # Override log level if specified
        if hasattr(args, 'log_level') and args.log_level:
            config.setdefault("logging", {})["level"] = args.log_level
        elif hasattr(args, 'verbose') and args.verbose:
            config.setdefault("logging", {})["level"] = "DEBUG"

        # Setup logging
        log_config = config.get("logging", {})
        logger = setup_logging(
            level=log_config.get("level", "INFO"),
            include_timestamps=log_config.get("include_timestamps", True),
        )

        logger.info(f"Repository Reporting System v{SCRIPT_VERSION}")
        logger.info(f"Project: {args.project}")
        logger.info(f"Configuration digest: {compute_config_digest(config)[:12]}...")

        # Write configuration to GitHub Step Summary
        write_config_to_step_summary(config, args.project)

        # Validate-only mode
        if hasattr(args, 'validate_only') and args.validate_only:
            logger.info("Configuration validation successful")
            print(f"✅ Configuration valid for project '{args.project}'")
            print(f"   - Schema version: {config.get('schema_version', 'Unknown')}")
            print(f"   - Time windows: {list(config.get('time_windows', {}).keys())}")
            print(
                f"   - Features enabled: {len(config.get('features', {}).get('enabled', []))}"
            )
            return 0

        # Create output directory
        args.output_dir.mkdir(parents=True, exist_ok=True)
        project_output_dir = args.output_dir / args.project
        project_output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize reporter
        reporter = RepositoryReporter(config, logger)

        # Analyze repositories
        report_data = reporter.analyze_repositories(args.repos_path)

        # Generate outputs
        json_path = project_output_dir / "report_raw.json"
        md_path = project_output_dir / "report.md"
        html_path = project_output_dir / "report.html"
        config_path = project_output_dir / "config_resolved.json"

        # Write JSON report
        reporter.renderer.render_json_report(report_data, json_path)

        # Generate Markdown report
        markdown_content = reporter.renderer.render_markdown_report(
            report_data, md_path
        )

        # Generate HTML report (unless disabled)
        if not (hasattr(args, 'no_html') and args.no_html):
            reporter.renderer.render_html_report(markdown_content, html_path)

        # Write resolved configuration
        save_resolved_config(config, config_path)

        # Create ZIP bundle (unless disabled)
        if not (hasattr(args, 'no_zip') and args.no_zip):
            zip_path = create_report_bundle(project_output_dir, args.project, logger)

        # Print summary
        repo_count = len(report_data["repositories"])
        error_count = len(report_data["errors"])

        print(f"\n✅ Report generation completed successfully!")
        print(f"   - Analyzed: {repo_count} repositories")
        print(f"   - Errors: {error_count}")
        print(f"   - Output directory: {project_output_dir}")

        if error_count > 0:
            print(f"   - Check {json_path} for error details")

        # Print API statistics
        api_stats_output = api_stats.format_console_output()
        if api_stats_output:
            print(api_stats_output)

        # Write API statistics to GitHub Step Summary
        api_stats.write_to_step_summary()

        return 0

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
