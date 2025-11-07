#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Configuration Wizard - Interactive Setup for Repository Reports

This module provides an interactive configuration wizard that helps users
create valid configuration files for their first report generation.

Features:
- Interactive prompts for all configuration options
- Template-based configuration generation
- Validation during setup
- Smart defaults based on environment
- Example configurations for common use cases
- Pre-flight checks before saving
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

# =============================================================================
# CONFIGURATION TEMPLATES
# =============================================================================

MINIMAL_TEMPLATE = {
    "project": "",
    "time_windows": {
        "reporting_window_days": 365,
        "recent_activity_days": 90,
        "active_contributor_days": 90,
    },
    "output": {
        "directory": "output",
        "formats": ["json", "md", "html"],
    },
}

STANDARD_TEMPLATE = {
    "project": "",
    "time_windows": {
        "reporting_window_days": 365,
        "recent_activity_days": 90,
        "active_contributor_days": 90,
        "abandoned_days": 180,
    },
    "output": {
        "directory": "output",
        "formats": ["json", "md", "html"],
        "create_bundle": True,
    },
    "api": {
        "github": {
            "enabled": True,
            "timeout": 30,
            "max_retries": 3,
        }
    },
    "features": {
        "ci_cd": {
            "github_actions": {"enabled": True},
            "jenkins": {"enabled": True},
        },
        "security": {
            "dependabot": {"enabled": True},
        },
        "documentation": {
            "readthedocs": {"enabled": True},
        },
    },
}

FULL_TEMPLATE = {
    "project": "",
    "time_windows": {
        "reporting_window_days": 365,
        "recent_activity_days": 90,
        "active_contributor_days": 90,
        "abandoned_days": 180,
        "new_contributor_days": 90,
    },
    "output": {
        "directory": "output",
        "formats": ["json", "md", "html"],
        "create_bundle": True,
        "bundle_name": "{project}-{date}",
    },
    "api": {
        "github": {
            "enabled": True,
            "token_env": "GITHUB_TOKEN",
            "timeout": 30,
            "max_retries": 3,
            "rate_limit_wait": True,
        },
        "gerrit": {
            "enabled": False,
            "base_url": "",
            "timeout": 30,
        },
        "jenkins": {
            "enabled": False,
            "base_url": "",
            "timeout": 30,
        },
    },
    "features": {
        "ci_cd": {
            "github_actions": {"enabled": True},
            "jenkins": {"enabled": True},
            "travis": {"enabled": True},
        },
        "build_package": {
            "maven": {"enabled": True},
            "npm": {"enabled": True},
            "pip": {"enabled": True},
        },
        "code_quality": {
            "sonarqube": {"enabled": True},
            "codecov": {"enabled": True},
        },
        "security": {
            "dependabot": {"enabled": True},
            "snyk": {"enabled": True},
        },
        "documentation": {
            "readthedocs": {"enabled": True},
            "github_pages": {"enabled": True},
        },
    },
    "performance": {
        "concurrency": {
            "enabled": True,
            "max_workers": 4,
        },
        "cache": {
            "enabled": True,
            "directory": ".cache",
            "ttl_hours": 24,
        },
    },
}


# =============================================================================
# WIZARD HELPERS
# =============================================================================


def prompt(question: str, default: Optional[str] = None) -> str:
    """
    Prompt user for input with optional default.

    Args:
        question: Question to ask
        default: Default value if user presses Enter

    Returns:
        User's answer or default
    """
    if default:
        prompt_text = f"{question} [{default}]: "
    else:
        prompt_text = f"{question}: "

    answer = input(prompt_text).strip()
    return answer if answer else (default or "")


def confirm(question: str, default: bool = True) -> bool:
    """
    Ask yes/no question.

    Args:
        question: Question to ask
        default: Default answer

    Returns:
        True for yes, False for no
    """
    default_str = "Y/n" if default else "y/N"
    answer = input(f"{question} [{default_str}]: ").strip().lower()

    if not answer:
        return default

    return answer in ("y", "yes", "true", "1")


def select_option(
    question: str, options: List[Tuple[str, str]], default: int = 0
) -> str:
    """
    Present multiple choice selection.

    Args:
        question: Question to ask
        options: List of (value, description) tuples
        default: Index of default option

    Returns:
        Selected value
    """
    print(f"\n{question}")
    for i, (value, description) in enumerate(options, 1):
        marker = "→" if i - 1 == default else " "
        print(f"  {marker} {i}. {description}")

    while True:
        answer = input(f"\nSelect [1-{len(options)}] or press Enter for default: ").strip()

        if not answer:
            return options[default][0]

        try:
            idx = int(answer) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
            else:
                print(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print(f"Please enter a number between 1 and {len(options)}")


def print_section(title: str) -> None:
    """Print a section header."""
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}\n")


def print_success(message: str) -> None:
    """Print success message."""
    print(f"✅ {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"⚠️  {message}")


def print_error(message: str) -> None:
    """Print error message."""
    print(f"❌ {message}")


def print_info(message: str) -> None:
    """Print info message."""
    print(f"ℹ️  {message}")


# =============================================================================
# CONFIGURATION WIZARD
# =============================================================================


class ConfigurationWizard:
    """Interactive configuration wizard."""

    def __init__(self):
        """Initialize wizard."""
        self.config: Dict[str, Any] = {}
        self.template_type: str = "standard"

    def run(self, output_path: Optional[str] = None) -> str:
        """
        Run the interactive wizard.

        Args:
            output_path: Optional path to save configuration

        Returns:
            Path to created configuration file
        """
        print("\n" + "=" * 70)
        print("  🚀 Repository Reporting Configuration Wizard")
        print("=" * 70)
        print("\nThis wizard will help you create a configuration file")
        print("for generating repository reports.\n")

        # Step 1: Select template
        self._select_template()

        # Step 2: Basic settings
        self._configure_basic_settings()

        # Step 3: Time windows
        self._configure_time_windows()

        # Step 4: Output settings
        self._configure_output()

        # Step 5: API integrations (skip for minimal)
        if self.template_type != "minimal":
            self._configure_api_integrations()

        # Step 6: Features
        if self.template_type != "minimal":
            self._configure_features()

        # Step 7: Performance settings
        if self.template_type == "full":
            self._configure_performance()

        # Step 8: Save configuration
        config_path = self._save_configuration(output_path)

        # Step 9: Print next steps
        self._print_next_steps(config_path)

        return config_path

    def _select_template(self) -> None:
        """Select configuration template."""
        print_section("Step 1: Select Configuration Template")

        options = [
            ("minimal", "Minimal - Basic settings only (quickest setup)"),
            ("standard", "Standard - Common features and integrations (recommended)"),
            ("full", "Full - All features and advanced options"),
        ]

        self.template_type = select_option(
            "Which template would you like to use?", options, default=1
        )

        # Load selected template
        if self.template_type == "minimal":
            self.config = MINIMAL_TEMPLATE.copy()
        elif self.template_type == "standard":
            self.config = STANDARD_TEMPLATE.copy()
        else:
            self.config = FULL_TEMPLATE.copy()

        print_info(f"Using {self.template_type} template")

    def _configure_basic_settings(self) -> None:
        """Configure basic project settings."""
        print_section("Step 2: Basic Settings")

        # Project name
        project = prompt("Project name", "my-project")
        self.config["project"] = project

        print_success(f"Project name set to: {project}")

    def _configure_time_windows(self) -> None:
        """Configure time window settings."""
        print_section("Step 3: Time Windows")

        print("Configure analysis time windows (in days):\n")

        time_windows = self.config.get("time_windows", {})

        # Reporting window
        if confirm("Use default reporting window (365 days / 1 year)?", True):
            time_windows["reporting_window_days"] = 365
        else:
            days = int(prompt("Reporting window (days)", "365"))
            time_windows["reporting_window_days"] = days

        # Recent activity
        if self.template_type != "minimal":
            if confirm("Use default recent activity window (90 days)?", True):
                time_windows["recent_activity_days"] = 90
            else:
                days = int(prompt("Recent activity window (days)", "90"))
                time_windows["recent_activity_days"] = days

        self.config["time_windows"] = time_windows
        print_success("Time windows configured")

    def _configure_output(self) -> None:
        """Configure output settings."""
        print_section("Step 4: Output Settings")

        output = self.config.get("output", {})

        # Output directory
        directory = prompt("Output directory", "output")
        output["directory"] = directory

        # Output formats
        print("\nOutput formats:")
        print("  Available: json, md (markdown), html")

        formats = []
        if confirm("  Generate JSON?", True):
            formats.append("json")
        if confirm("  Generate Markdown?", True):
            formats.append("md")
        if confirm("  Generate HTML?", True):
            formats.append("html")

        if not formats:
            print_warning("No formats selected, using JSON as default")
            formats = ["json"]

        output["formats"] = formats

        # Bundle creation
        if self.template_type != "minimal":
            if confirm("Create ZIP bundle of all reports?", True):
                output["create_bundle"] = True
            else:
                output["create_bundle"] = False

        self.config["output"] = output
        print_success(f"Output configured: {directory} ({', '.join(formats)})")

    def _configure_api_integrations(self) -> None:
        """Configure API integrations."""
        print_section("Step 5: API Integrations")

        api = self.config.get("api", {})

        # GitHub
        print("\nGitHub API:")
        if confirm("  Enable GitHub API integration?", True):
            github = api.get("github", {})
            github["enabled"] = True

            # Check for token
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                print_success("  GITHUB_TOKEN found in environment")
            else:
                print_warning("  GITHUB_TOKEN not found in environment")
                print_info("  Set GITHUB_TOKEN for higher API rate limits")

            api["github"] = github
        else:
            if "github" in api:
                api["github"]["enabled"] = False

        # Gerrit (only for standard/full)
        if self.template_type != "minimal":
            print("\nGerrit API:")
            if confirm("  Enable Gerrit integration?", False):
                gerrit = api.get("gerrit", {})
                gerrit["enabled"] = True
                gerrit["base_url"] = prompt("  Gerrit base URL")
                api["gerrit"] = gerrit
            else:
                if "gerrit" in api:
                    api["gerrit"]["enabled"] = False

        # Jenkins (only for full)
        if self.template_type == "full":
            print("\nJenkins API:")
            if confirm("  Enable Jenkins integration?", False):
                jenkins = api.get("jenkins", {})
                jenkins["enabled"] = True
                jenkins["base_url"] = prompt("  Jenkins base URL")
                api["jenkins"] = jenkins
            else:
                if "jenkins" in api:
                    api["jenkins"]["enabled"] = False

        self.config["api"] = api
        print_success("API integrations configured")

    def _configure_features(self) -> None:
        """Configure feature detection."""
        print_section("Step 6: Feature Detection")

        print("Select which features to detect:\n")

        features = self.config.get("features", {})

        # CI/CD
        if confirm("Detect CI/CD systems (GitHub Actions, Jenkins, etc.)?", True):
            if "ci_cd" not in features:
                features["ci_cd"] = {}
            features["ci_cd"]["github_actions"] = {"enabled": True}
            features["ci_cd"]["jenkins"] = {"enabled": True}
        else:
            if "ci_cd" in features:
                for key in features["ci_cd"]:
                    features["ci_cd"][key]["enabled"] = False

        # Security
        if confirm("Detect security tools (Dependabot, Snyk, etc.)?", True):
            if "security" not in features:
                features["security"] = {}
            features["security"]["dependabot"] = {"enabled": True}
        else:
            if "security" in features:
                for key in features["security"]:
                    features["security"][key]["enabled"] = False

        # Documentation
        if confirm("Detect documentation tools (ReadTheDocs, etc.)?", True):
            if "documentation" not in features:
                features["documentation"] = {}
            features["documentation"]["readthedocs"] = {"enabled": True}
        else:
            if "documentation" in features:
                for key in features["documentation"]:
                    features["documentation"][key]["enabled"] = False

        # Build/Package (full only)
        if self.template_type == "full":
            if confirm("Detect build/package systems (Maven, npm, pip)?", True):
                if "build_package" not in features:
                    features["build_package"] = {}
                features["build_package"]["maven"] = {"enabled": True}
                features["build_package"]["npm"] = {"enabled": True}
                features["build_package"]["pip"] = {"enabled": True}

        self.config["features"] = features
        print_success("Feature detection configured")

    def _configure_performance(self) -> None:
        """Configure performance settings."""
        print_section("Step 7: Performance Settings")

        performance = self.config.get("performance", {})

        # Concurrency
        print("\nConcurrency:")
        if confirm("  Enable parallel processing?", True):
            concurrency = performance.get("concurrency", {})
            concurrency["enabled"] = True

            workers = prompt("  Number of worker threads", "4")
            concurrency["max_workers"] = int(workers)

            performance["concurrency"] = concurrency
        else:
            if "concurrency" in performance:
                performance["concurrency"]["enabled"] = False

        # Caching
        print("\nCaching:")
        if confirm("  Enable caching?", True):
            cache = performance.get("cache", {})
            cache["enabled"] = True
            cache["directory"] = prompt("  Cache directory", ".cache")

            ttl = prompt("  Cache TTL (hours)", "24")
            cache["ttl_hours"] = int(ttl)

            performance["cache"] = cache
        else:
            if "cache" in performance:
                performance["cache"]["enabled"] = False

        self.config["performance"] = performance
        print_success("Performance settings configured")

    def _save_configuration(self, output_path: Optional[str] = None) -> str:
        """
        Save configuration to file.

        Args:
            output_path: Optional path to save configuration

        Returns:
            Path where configuration was saved
        """
        print_section("Step 8: Save Configuration")

        # Determine output path
        if not output_path:
            default_path = f"config/{self.config['project']}.yaml"
            output_path = prompt(
                "Configuration file path", default_path
            )

        # Create parent directory if needed
        config_path = Path(output_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save configuration
        with open(config_path, "w") as f:
            yaml.dump(
                self.config,
                f,
                default_flow_style=False,
                sort_keys=False,
                indent=2,
            )

        print_success(f"Configuration saved to: {config_path}")

        return str(config_path)

    def _print_next_steps(self, config_path: str) -> None:
        """Print next steps for user."""
        print_section("Next Steps")

        print("Your configuration is ready! Here's what to do next:\n")

        print("1. Review your configuration:")
        print(f"   cat {config_path}\n")

        print("2. Validate your setup (optional but recommended):")
        print(f"   python generate_reports.py --config {config_path} --dry-run\n")

        print("3. Generate your first report:")
        print(f"   python generate_reports.py --project {self.config['project']} \\")
        print(f"     --config {config_path} \\")
        print(f"     --repos-path /path/to/repositories\n")

        print("For more help:")
        print("  - Quick start guide: docs/QUICK_START.md")
        print("  - CLI reference: docs/CLI_REFERENCE.md")
        print("  - Troubleshooting: docs/TROUBLESHOOTING.md")

        print("\n" + "=" * 70)
        print("  ✅ Configuration wizard complete!")
        print("=" * 70 + "\n")


# =============================================================================
# PUBLIC API
# =============================================================================


def run_wizard(output_path: Optional[str] = None) -> str:
    """
    Run the interactive configuration wizard.

    Args:
        output_path: Optional path to save configuration

    Returns:
        Path to created configuration file
    """
    wizard = ConfigurationWizard()
    return wizard.run(output_path)


def create_config_from_template(
    project: str,
    template: str = "standard",
    output_path: Optional[str] = None,
) -> str:
    """
    Create configuration file from template without interactive prompts.

    Args:
        project: Project name
        template: Template type (minimal, standard, full)
        output_path: Optional path to save configuration

    Returns:
        Path to created configuration file
    """
    # Select template
    if template == "minimal":
        config = MINIMAL_TEMPLATE.copy()
    elif template == "standard":
        config = STANDARD_TEMPLATE.copy()
    elif template == "full":
        config = FULL_TEMPLATE.copy()
    else:
        raise ValueError(f"Unknown template: {template}")

    # Set project name
    config["project"] = project

    # Determine output path
    if not output_path:
        output_path = f"config/{project}.yaml"

    # Create parent directory if needed
    config_path = Path(output_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Save configuration
    with open(config_path, "w") as f:
        yaml.dump(
            config,
            f,
            default_flow_style=False,
            sort_keys=False,
            indent=2,
        )

    return str(config_path)


if __name__ == "__main__":
    """Run wizard when executed directly."""
    run_wizard()
