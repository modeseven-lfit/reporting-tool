# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Feature Registry Module

This module contains the FeatureRegistry class for detecting features in repositories.
Extracted from generate_reports.py as part of Phase 3 refactoring.

The FeatureRegistry provides a plugin-style architecture for feature detection:
- Dependabot configuration
- GitHub workflows and GitHub Actions
- Pre-commit hooks
- Documentation systems (ReadTheDocs, Sphinx, MkDocs)
- Project types (Maven, Gradle, Python, Node, etc.)
- CI/CD integrations (Jenkins, GitHub Actions)
- Code quality tools
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# Import API clients for GitHub integration
from api.github_client import GitHubAPIClient


class FeatureRegistry:
    """
    Registry for repository feature detection functions.

    This class maintains a registry of feature detection functions and provides
    methods to scan repositories for various features like CI/CD configurations,
    documentation setups, dependency management, and project types.

    Features are detected by examining:
    - Configuration files (e.g., .github/dependabot.yml)
    - Project structure (e.g., presence of docs/ directory)
    - Git configuration (e.g., .gitreview for Gerrit)
    - GitHub API (e.g., workflow run status)

    Example:
        >>> config = {"features": {"enabled": ["dependabot", "workflows"]}}
        >>> logger = logging.getLogger(__name__)
        >>> registry = FeatureRegistry(config, logger)
        >>> features = registry.detect_features(Path("./my-repo"))
        >>> print(features["dependabot"])
        {"present": True, "files": [".github/dependabot.yml"]}
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        """
        Initialize the feature registry.

        Args:
            config: Configuration dictionary containing feature settings
            logger: Logger instance for debug/info/warning messages
        """
        self.config = config
        self.logger = logger
        self.checks: Dict[str, Callable] = {}

        # Get GitHub organization from config (already determined centrally in main())
        self.github_org = self.config.get("github", "")
        self.github_org_source = self.config.get("_github_org_source", "not_configured")

        if self.github_org:
            self.logger.debug(
                f"GitHub organization: '{self.github_org}' (source: {self.github_org_source})"
            )

        self._register_default_checks()

    def register(self, feature_name: str, check_function: Callable) -> None:
        """
        Register a feature detection function.

        Args:
            feature_name: Unique name for the feature
            check_function: Callable that takes a Path and returns feature info dict
        """
        self.checks[feature_name] = check_function

    def _register_default_checks(self) -> None:
        """Register all default feature detection checks."""
        self.register("dependabot", self._check_dependabot)
        self.register("github2gerrit_workflow", self._check_github2gerrit_workflow)
        self.register("g2g", self._check_g2g)
        self.register("pre_commit", self._check_pre_commit)
        self.register("readthedocs", self._check_readthedocs)
        self.register("sonatype_config", self._check_sonatype_config)
        self.register("project_types", self._check_project_types)
        self.register("workflows", self._check_workflows)
        self.register("gitreview", self._check_gitreview)
        self.register("github_mirror", self._check_github_mirror)

    def detect_features(self, repo_path: Path) -> Dict[str, Any]:
        """
        Scan repository for all enabled features.

        Args:
            repo_path: Path to the repository to scan

        Returns:
            Dictionary mapping feature names to their detection results

        Example:
            >>> features = registry.detect_features(Path("./repo"))
            >>> if features["dependabot"]["present"]:
            ...     print("Dependabot is configured!")
        """
        enabled_features = self.config.get("features", {}).get("enabled", [])
        results = {}

        for feature_name in enabled_features:
            if feature_name in self.checks:
                try:
                    results[feature_name] = self.checks[feature_name](repo_path)
                except Exception as e:
                    self.logger.warning(
                        f"Feature check '{feature_name}' failed for {repo_path.name}: {e}"
                    )
                    results[feature_name] = {"error": str(e)}

        return results

    def _check_dependabot(self, repo_path: Path) -> Dict[str, Any]:
        """
        Check for Dependabot configuration.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with keys: present (bool), files (list)
        """
        config_files = [".github/dependabot.yml", ".github/dependabot.yaml"]

        found_files = []
        for config_file in config_files:
            file_path = repo_path / config_file
            if file_path.exists():
                found_files.append(config_file)

        return {"present": len(found_files) > 0, "files": found_files}

    def _check_github2gerrit_workflow(self, repo_path: Path) -> Dict[str, Any]:
        """
        Check for GitHub to Gerrit workflow patterns.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with keys: present (bool), workflows (list of dicts)
        """
        workflows_dir = repo_path / ".github" / "workflows"
        if not workflows_dir.exists():
            return {"present": False, "workflows": []}

        gerrit_patterns = [
            "gerrit",
            "review",
            "submit",
            "replication",
            "github2gerrit",
            "gerrit-review",
            "gerrit-submit",
        ]

        matching_workflows: List[Dict[str, str]] = []
        try:
            # Process .yml files
            for workflow_file in workflows_dir.glob("*.yml"):
                try:
                    with open(workflow_file, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        for pattern in gerrit_patterns:
                            if pattern in content:
                                matching_workflows.append(
                                    {
                                        "file": workflow_file.name,
                                        "pattern": pattern,
                                    }
                                )
                                break
                except (IOError, UnicodeDecodeError):
                    continue

            # Also check .yaml files
            for workflow_file in workflows_dir.glob("*.yaml"):
                try:
                    with open(workflow_file, "r", encoding="utf-8") as f:
                        content = f.read().lower()
                        for pattern in gerrit_patterns:
                            if pattern in content:
                                matching_workflows.append(
                                    {
                                        "file": workflow_file.name,
                                        "pattern": pattern,
                                    }
                                )
                                break
                except (IOError, UnicodeDecodeError):
                    continue

        except OSError:
            return {"present": False, "workflows": []}

        return {"present": len(matching_workflows) > 0, "workflows": matching_workflows}

    def _check_g2g(self, repo_path: Path) -> Dict[str, Any]:
        """
        Check for specific GitHub to Gerrit workflow files.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with keys: present (bool), file_paths (list), file_path (str or None)
        """
        workflows_dir = repo_path / ".github" / "workflows"
        g2g_files = ["github2gerrit.yaml", "call-github2gerrit.yaml"]

        found_files = []
        for filename in g2g_files:
            file_path = workflows_dir / filename
            if file_path.exists():
                found_files.append(f".github/workflows/{filename}")

        return {
            "present": len(found_files) > 0,
            "file_paths": found_files,
            "file_path": found_files[0] if found_files else None,  # Backward compatibility
        }

    def _check_pre_commit(self, repo_path: Path) -> Dict[str, Any]:
        """
        Check for pre-commit configuration.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with keys: present (bool), config_file (str or None), repos_count (int)
        """
        config_files = [".pre-commit-config.yaml", ".pre-commit-config.yml"]

        found_config = None
        for config_file in config_files:
            file_path = repo_path / config_file
            if file_path.exists():
                found_config = config_file
                break

        result: Dict[str, Any] = {
            "present": found_config is not None,
            "config_file": found_config,
        }

        # If config exists, try to extract some basic info
        if found_config:
            try:
                config_path = repo_path / found_config
                with open(config_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Count number of repos/hooks (basic analysis)
                    repos_count = len(
                        re.findall(r"^\s*-\s*repo:", content, re.MULTILINE)
                    )
                    result["repos_count"] = repos_count
            except (IOError, UnicodeDecodeError):
                pass

        return result

    def _check_readthedocs(self, repo_path: Path) -> Dict[str, Any]:
        """
        Check for Read the Docs configuration.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with keys: present (bool), config_type (str or None), config_files (list)
        """
        # Check for RTD config files
        rtd_configs = [
            ".readthedocs.yml",
            ".readthedocs.yaml",
            "readthedocs.yml",
            "readthedocs.yaml",
        ]

        sphinx_configs = ["docs/conf.py", "doc/conf.py", "documentation/conf.py"]

        mkdocs_configs = ["mkdocs.yml", "mkdocs.yaml"]

        found_configs = []
        config_type = None

        # Check RTD config files
        for config in rtd_configs:
            if (repo_path / config).exists():
                found_configs.append(config)
                config_type = "readthedocs"

        # Check Sphinx configs
        for config in sphinx_configs:
            if (repo_path / config).exists():
                found_configs.append(config)
                if not config_type:
                    config_type = "sphinx"

        # Check MkDocs configs
        for config in mkdocs_configs:
            if (repo_path / config).exists():
                found_configs.append(config)
                if not config_type:
                    config_type = "mkdocs"

        return {
            "present": len(found_configs) > 0,
            "config_type": config_type,
            "config_files": found_configs,
        }

    def _check_sonatype_config(self, repo_path: Path) -> Dict[str, Any]:
        """
        Check for Sonatype configuration files.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with keys: present (bool), config_files (list)
        """
        sonatype_configs = [
            ".sonatype-lift.yaml",
            ".sonatype-lift.yml",
            "lift.toml",
            "lifecycle.json",
            ".lift.toml",
            "sonatype-lift.yml",
            "sonatype-lift.yaml",
        ]

        found_configs = []
        for config in sonatype_configs:
            if (repo_path / config).exists():
                found_configs.append(config)

        return {"present": len(found_configs) > 0, "config_files": found_configs}

    def _check_project_types(self, repo_path: Path) -> Dict[str, Any]:
        """
        Detect project types based on configuration files and repository characteristics.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with keys: detected_types (list), primary_type (str), details (list)
        """
        repo_name = repo_path.name.lower()

        # Static classifications based on repository names
        if repo_name == "ci-management":
            return {
                "detected_types": ["jjb"],
                "primary_type": "jjb",
                "details": [
                    {"type": "jjb", "files": ["repository_name"], "confidence": 100}
                ],
            }

        project_types = {
            "maven": ["pom.xml"],
            "gradle": [
                "build.gradle",
                "build.gradle.kts",
                "gradle.properties",
                "settings.gradle",
            ],
            "node": ["package.json"],
            "python": [
                "pyproject.toml",
                "requirements.txt",
                "setup.py",
                "setup.cfg",
                "Pipfile",
                "poetry.lock",
            ],
            "docker": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"],
            "go": ["go.mod", "go.sum"],
            "rust": ["Cargo.toml", "Cargo.lock"],
            "java": ["build.xml", "ivy.xml"],  # Ant
            "c_cpp": ["Makefile", "CMakeLists.txt", "configure.ac", "configure.in"],
            "dotnet": ["*.csproj", "*.sln", "project.json", "*.vbproj", "*.fsproj"],
            "ruby": ["Gemfile", "Rakefile", "*.gemspec"],
            "php": ["composer.json", "composer.lock"],
            "scala": ["build.sbt", "project/build.properties"],
            "swift": ["Package.swift"],
            "kotlin": ["build.gradle.kts"],
        }

        detected_types = []
        confidence_scores = {}

        for project_type, config_files in project_types.items():
            matches = []
            for config_pattern in config_files:
                if "*" in config_pattern:
                    # Handle glob patterns
                    try:
                        matching_files = list(repo_path.glob(config_pattern))
                        if matching_files:
                            matches.extend([f.name for f in matching_files])
                    except OSError:
                        continue
                else:
                    # Regular file check
                    if (repo_path / config_pattern).exists():
                        matches.append(config_pattern)

            if matches:
                detected_types.append(
                    {"type": project_type, "files": matches, "confidence": len(matches)}
                )
                confidence_scores[project_type] = len(matches)

        # Determine primary type (highest confidence)
        primary_type = None
        if detected_types:
            primary_type = max(confidence_scores.items(), key=lambda x: x[1])[0]

        # If no programming language detected, check for documentation as fallback
        if not detected_types and self._is_documentation_repository(repo_path):
            return {
                "detected_types": ["documentation"],
                "primary_type": "documentation",
                "details": [
                    {
                        "type": "documentation",
                        "files": self._get_doc_indicators(repo_path),
                        "confidence": 50,
                    }
                ],
            }

        return {
            "detected_types": [t["type"] for t in detected_types],
            "primary_type": primary_type,
            "details": detected_types,
        }

    def _is_documentation_repository(self, repo_path: Path) -> bool:
        """
        Determine if a repository is primarily for documentation (fallback only).

        Args:
            repo_path: Path to the repository

        Returns:
            True if repository appears to be primarily documentation
        """
        repo_name = repo_path.name.lower()

        # Only classify as documentation if repository name strongly indicates it
        strong_doc_patterns = ["documentation", "manual", "wiki", "guide", "tutorial"]
        if any(
            repo_name == pattern or repo_name.endswith(f"-{pattern}")
            for pattern in strong_doc_patterns
        ):
            return True

        # For repos named exactly "doc" or "docs"
        if repo_name in ["doc", "docs"]:
            return True

        # Check directory structure and file patterns - be more restrictive
        doc_indicators = self._get_doc_indicators(repo_path)
        return len(doc_indicators) >= 5  # Require more indicators for stronger confidence

    def _get_doc_indicators(self, repo_path: Path) -> List[str]:
        """
        Get list of documentation indicators found in the repository.

        Args:
            repo_path: Path to the repository

        Returns:
            List of documentation indicator file/directory names
        """
        indicators = []

        # Check for common documentation files
        doc_files = [
            "README.md",
            "README.rst",
            "README.txt",
            "DOCS.md",
            "DOCUMENTATION.md",
            "index.md",
            "index.rst",
            "index.html",
            "sphinx.conf",
            "conf.py",  # Sphinx
            "mkdocs.yml",
            "_config.yml",  # MkDocs/Jekyll
            "Gemfile",  # Jekyll
        ]

        for doc_file in doc_files:
            if (repo_path / doc_file).exists():
                indicators.append(doc_file)

        # Check for documentation directories
        doc_dirs = [
            "docs",
            "doc",
            "documentation",
            "_docs",
            "manual",
            "guides",
            "tutorials",
        ]
        for doc_dir in doc_dirs:
            if (repo_path / doc_dir).is_dir():
                indicators.append(f"{doc_dir}/")

        # Check for common documentation file extensions in root
        try:
            doc_extensions = [".md", ".rst", ".adoc", ".txt"]
            for ext in doc_extensions:
                if list(repo_path.glob(f"*{ext}")):
                    indicators.append(f"*{ext}")
        except OSError:
            pass

        # Check for static site generators
        static_generators = [
            ".gitbook",  # GitBook
            "_config.yml",  # Jekyll
            "mkdocs.yml",  # MkDocs
            "conf.py",  # Sphinx
            "book.toml",  # mdBook
            "docusaurus.config.js",  # Docusaurus
        ]

        for generator in static_generators:
            if (repo_path / generator).exists():
                indicators.append(generator)

        return indicators

    def _check_workflows(self, repo_path: Path) -> Dict[str, Any]:
        """
        Analyze GitHub workflows with optional GitHub API integration.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with workflow count, classification, and optional runtime status
        """
        workflows_dir = repo_path / ".github" / "workflows"
        if not workflows_dir.exists():
            return {
                "count": 0,
                "classified": {"verify": 0, "merge": 0, "other": 0},
                "files": [],
            }

        # Get classification patterns from config
        workflow_config = self.config.get("workflows", {}).get("classify", {})
        verify_patterns = workflow_config.get(
            "verify", ["verify", "test", "ci", "check"]
        )
        merge_patterns = workflow_config.get(
            "merge", ["merge", "release", "deploy", "publish"]
        )

        workflow_files = []
        classified = {"verify": 0, "merge": 0, "other": 0}

        try:
            # Process .yml files
            for workflow_file in workflows_dir.glob("*.yml"):
                workflow_info = self._analyze_workflow_file(
                    workflow_file, verify_patterns, merge_patterns
                )
                workflow_files.append(workflow_info)
                classified[workflow_info["classification"]] += 1

            # Process .yaml files
            for workflow_file in workflows_dir.glob("*.yaml"):
                workflow_info = self._analyze_workflow_file(
                    workflow_file, verify_patterns, merge_patterns
                )
                workflow_files.append(workflow_info)
                classified[workflow_info["classification"]] += 1

        except OSError:
            return {
                "count": 0,
                "classified": {"verify": 0, "merge": 0, "other": 0},
                "files": [],
            }

        # Extract just the workflow names for telemetry
        workflow_names = [workflow_info["name"] for workflow_info in workflow_files]

        # Base result with static analysis
        result = {
            "count": len(workflow_files),
            "classified": classified,
            "files": workflow_files,
            "workflow_names": workflow_names,
            "has_runtime_status": False,
        }

        # Try GitHub API integration if enabled and token available
        github_api_enabled = (
            self.config.get("extensions", {})
            .get("github_api", {})
            .get("enabled", False)
        )
        github_token = self.config.get("extensions", {}).get("github_api", {}).get(
            "token"
        ) or os.environ.get("CLASSIC_READ_ONLY_PAT_TOKEN")

        is_github_repo = self._is_github_repository(repo_path)

        self.logger.debug(
            f"GitHub API integration check for {repo_path.name}: "
            f"enabled={github_api_enabled}, has_token={bool(github_token)}, "
            f"github_org={self.github_org} (source={self.github_org_source}), "
            f"is_github_repo={is_github_repo}"
        )

        # Validate prerequisites for GitHub API integration
        if github_api_enabled and not github_token:
            self.logger.warning(
                f"GitHub API enabled but token not available (CLASSIC_READ_ONLY_PAT_TOKEN). "
                f"Workflow status will not be queried for {repo_path.name}"
            )

        if (
            github_api_enabled
            and github_token
            and self.github_org
            and is_github_repo
        ):
            try:
                owner, repo_name = self._extract_github_repo_info(repo_path, self.github_org)
                self.logger.debug(
                    f"Attempting GitHub API query for {owner}/{repo_name}"
                )
                if owner and repo_name:
                    github_client = GitHubAPIClient(github_token)
                    github_status = (
                        github_client.get_repository_workflow_status_summary(
                            owner, repo_name
                        )
                    )

                    # Merge GitHub API data with static analysis
                    result["github_api_data"] = github_status
                    result["has_runtime_status"] = True

                    self.logger.debug(
                        f"Retrieved GitHub workflow status for {owner}/{repo_name}"
                    )

                    # If no local workflows were found but GitHub has workflows, use GitHub as source
                    # This handles cases where Gerrit is primary but GitHub mirror has workflows
                    if not workflow_names and github_status.get("workflows"):
                        github_workflow_names = []
                        for workflow in github_status.get("workflows", []):
                            workflow_path = workflow.get("path", "")
                            if workflow_path:
                                file_name = os.path.basename(workflow_path)
                                github_workflow_names.append(file_name)

                        if github_workflow_names:
                            result["workflow_names"] = github_workflow_names
                            result["count"] = len(github_workflow_names)
                            self.logger.debug(
                                f"Using GitHub API as workflow source for {owner}/{repo_name}: "
                                f"{github_workflow_names}"
                            )

            except Exception as e:
                self.logger.warning(
                    f"Failed to fetch GitHub workflow status for {repo_path}: {e}"
                )

        return result

    def _analyze_workflow_file(
        self, workflow_file: Path, verify_patterns: List[str], merge_patterns: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze a single workflow file for classification.

        Args:
            workflow_file: Path to the workflow file
            verify_patterns: List of patterns indicating verify/test workflows
            merge_patterns: List of patterns indicating merge/release workflows

        Returns:
            Dict with workflow information and classification
        """
        workflow_info: Dict[str, Any] = {
            "name": workflow_file.name,
            "classification": "other",
            "triggers": [],
            "jobs": 0,
        }

        try:
            with open(workflow_file, "r", encoding="utf-8") as f:
                content = f.read().lower()
                filename_lower = workflow_file.name.lower()

                # Classification based on filename and content with scoring
                verify_score = 0
                merge_score = 0

                # Score verify patterns (filename matches count more)
                for pattern in verify_patterns:
                    pattern_lower = pattern.lower()
                    if pattern_lower in filename_lower:
                        verify_score += 3  # Higher weight for filename matches
                    elif re.search(r"\b" + re.escape(pattern_lower) + r"\b", content):
                        verify_score += 1

                # Score merge patterns (filename matches count more)
                for pattern in merge_patterns:
                    pattern_lower = pattern.lower()
                    if pattern_lower in filename_lower:
                        merge_score += 3  # Higher weight for filename matches
                    elif re.search(r"\b" + re.escape(pattern_lower) + r"\b", content):
                        merge_score += 1

                # Classify based on highest score
                if merge_score > verify_score:
                    workflow_info["classification"] = "merge"
                elif verify_score > 0:
                    workflow_info["classification"] = "verify"
                # else remains "other"

                # Extract basic info
                # Find triggers (on: section)
                trigger_matches = re.findall(r"on:\s*\n\s*-?\s*(\w+)", content)
                if trigger_matches:
                    workflow_info["triggers"] = trigger_matches
                else:
                    # Try alternative format
                    if "on: push" in content:
                        workflow_info["triggers"].append("push")
                    if "on: pull_request" in content:
                        workflow_info["triggers"].append("pull_request")

                # Count jobs
                job_matches = re.findall(r"^\s*(\w+):\s*$", content, re.MULTILINE)
                # Filter out common YAML keys that aren't jobs
                non_job_keys = {"on", "env", "defaults", "jobs", "name", "run-name"}
                jobs = [
                    job
                    for job in job_matches
                    if job not in non_job_keys and not job.startswith("step")
                ]
                workflow_info["jobs"] = len(set(jobs))  # Remove duplicates

        except (IOError, UnicodeDecodeError):
            # File couldn't be read, return basic info
            pass

        return workflow_info

    def _check_github_mirror(self, repo_path: Path) -> Dict[str, Any]:
        """
        Check if repository has a GitHub mirror that actually exists.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with keys: exists (bool), owner (str), repo (str), reason (str)
        """
        try:
            # First check if it looks like a GitHub repository
            has_github_indicators = self._is_github_repository(repo_path)

            if not has_github_indicators:
                return {
                    "exists": False,
                    "owner": "",
                    "repo": "",
                    "reason": "no_github_indicators",
                }

            # Check if the GitHub repository actually exists
            owner, repo_name = self._extract_github_repo_info(repo_path)
            if not owner or not repo_name:
                return {
                    "exists": False,
                    "owner": owner,
                    "repo": repo_name,
                    "reason": "cannot_determine_github_info",
                }

            # Verify the repository exists on GitHub
            exists = self._check_github_mirror_exists(repo_path)

            return {
                "exists": exists,
                "owner": owner,
                "repo": repo_name,
                "reason": "verified" if exists else "not_found_on_github",
            }

        except Exception as e:
            self.logger.debug(f"GitHub mirror check failed for {repo_path}: {e}")
            return {
                "exists": False,
                "owner": "",
                "repo": "",
                "reason": f"error: {str(e)}",
            }

    def _is_github_repository(self, repo_path: Path) -> bool:
        """
        Check if repository is hosted on GitHub by examining git remotes.

        Args:
            repo_path: Path to the repository

        Returns:
            True if repository has GitHub indicators
        """
        try:
            # Check for git directory
            git_dir = repo_path / ".git"
            if not git_dir.exists():
                return False

            # Read git config or remote files
            config_file = git_dir / "config"
            if config_file.exists():
                with open(config_file, "r") as f:
                    content = f.read()
                    # Check for GitHub remotes
                    if "github.com" in content.lower():
                        return True

            # For ONAP and other projects that are mirrored on GitHub,
            # check if they have GitHub workflows (indicates GitHub presence)
            workflows_dir = repo_path / ".github" / "workflows"
            if workflows_dir.exists() and any(workflows_dir.iterdir()):
                # If we have GitHub workflows, assume it's mirrored on GitHub
                return True

            return False
        except Exception:
            return False

    def _check_github_mirror_exists(self, repo_path: Path) -> bool:
        """
        Check if repository actually exists on GitHub by making an API call.

        Args:
            repo_path: Path to the repository

        Returns:
            True if repository exists on GitHub
        """
        try:
            owner, repo_name = self._extract_github_repo_info(repo_path)
            if not owner or not repo_name:
                return False

            # Try to access GitHub API to verify repository exists
            github_token = self.config.get("extensions", {}).get("github_api", {}).get(
                "token"
            ) or os.environ.get("CLASSIC_READ_ONLY_PAT_TOKEN")

            if github_token:
                try:
                    github_client = GitHubAPIClient(github_token)
                    response = github_client.client.get(f"/repos/{owner}/{repo_name}")
                    return bool(response.status_code == 200)
                except Exception as e:
                    self.logger.debug(
                        f"GitHub API check failed for {owner}/{repo_name}: {e}"
                    )

            # Fallback: make a simple HTTP request without authentication
            try:
                import httpx

                with httpx.Client(timeout=10.0) as client:
                    response = client.get(
                        f"https://api.github.com/repos/{owner}/{repo_name}"
                    )
                    return bool(response.status_code == 200)
            except Exception as e:
                self.logger.debug(
                    f"GitHub repository existence check failed for {owner}/{repo_name}: {e}"
                )
                return False

        except Exception:
            return False

    def _extract_github_repo_info(
        self, repo_path: Path, github_org: str = ""
    ) -> Tuple[str, str]:
        """
        Extract GitHub owner and repo name from git remote or configuration.

        Args:
            repo_path: Path to the repository
            github_org: GitHub organization name from configuration (for Gerrit mirrors)

        Returns:
            Tuple of (owner, repo_name)
        """
        try:
            git_dir = repo_path / ".git"
            config_file = git_dir / "config"

            if not config_file.exists():
                # For mirrored repos, use configured github_org
                return self._infer_github_info_from_path(repo_path, github_org)

            with open(config_file, "r") as f:
                content = f.read()

            # Look for GitHub remote URLs
            # Match both HTTPS and SSH formats
            patterns = [
                r"url = https://github\.com/([^/]+)/([^/\s]+)(?:\.git)?",
                r"url = git@github\.com:([^/]+)/([^/\s]+)(?:\.git)?",
            ]

            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    owner, repo = match.groups()
                    # Clean up repo name
                    repo = repo.rstrip(".git")
                    return owner, repo

            # Fallback to path-based inference for mirrored repos
            return self._infer_github_info_from_path(repo_path, github_org)
        except Exception:
            return "", ""

    def _infer_github_info_from_path(
        self, repo_path: Path, github_org: str = ""
    ) -> Tuple[str, str]:
        """
        Infer GitHub owner/repo from repository path for mirrored repos.

        For Gerrit repos mirrored to GitHub, the path structure is typically:
        ./gerrit.example.org/repo-name -> github_org/repo-name

        Args:
            repo_path: Path to the repository
            github_org: GitHub organization name from configuration

        Returns:
            Tuple of (owner, repo_name)
        """
        try:
            if not github_org:
                self.logger.debug(
                    f"Cannot infer GitHub info for {repo_path.name}: github_org not provided"
                )
                return "", ""

            # Get just the repository name from the path
            # For paths like ./gerrit.onap.org/aai/babel, we want "aai-babel"
            # For paths like ./gerrit.onap.org/simple-repo, we want "simple-repo"
            path_parts = repo_path.parts

            # Find the Gerrit host in the path (e.g., "gerrit.onap.org")
            gerrit_host_index = -1
            for i, part in enumerate(path_parts):
                if "gerrit" in part.lower() or "git" in part.lower():
                    gerrit_host_index = i
                    break

            if gerrit_host_index >= 0 and gerrit_host_index < len(path_parts) - 1:
                # Get all path components after the gerrit host
                repo_parts = path_parts[gerrit_host_index + 1:]
                if repo_parts:
                    # Join multi-level paths with hyphens
                    # e.g., ["aai", "babel"] -> "aai-babel"
                    repo_name = "-".join(repo_parts)
                    self.logger.debug(
                        f"Inferred GitHub repo: {github_org}/{repo_name} from path {repo_path}"
                    )
                    return github_org, repo_name

            # Fallback: use just the repo name
            repo_name = repo_path.name
            self.logger.debug(
                f"Using fallback GitHub repo: {github_org}/{repo_name} from path {repo_path}"
            )
            return github_org, repo_name

        except Exception as e:
            self.logger.debug(
                f"Failed to infer GitHub info for {repo_path}: {e}"
            )
            return "", ""

    def _check_gitreview(self, repo_path: Path) -> Dict[str, Any]:
        """
        Check for .gitreview configuration file.

        Args:
            repo_path: Path to the repository

        Returns:
            Dict with keys: present (bool), file (str or None), config (dict)
        """
        gitreview_file = repo_path / ".gitreview"

        if not gitreview_file.exists():
            return {"present": False, "file": None, "config": {}}

        # Parse .gitreview file content
        config = {}
        try:
            with open(gitreview_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        except (IOError, UnicodeDecodeError):
            # File exists but couldn't be read
            pass

        return {"present": True, "file": ".gitreview", "config": config}
