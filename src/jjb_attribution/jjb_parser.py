# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Jenkins Job Builder (JJB) Attribution Parser.

This module parses JJB YAML files from ci-management repositories to extract
job definitions and map them to Gerrit projects. It provides accurate Jenkins
job attribution based on authoritative JJB configuration files.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

logger = logging.getLogger(__name__)


# Register JJB-specific YAML tags to prevent warnings
# These tags are used in JJB templates but we don't need to process them
def _jjb_tag_constructor(loader, node):
    """
    Constructor for JJB-specific YAML tags.

    Jenkins Job Builder uses custom YAML tags like !include-raw-escape: and !j2:
    for including shell scripts and Jinja2 templates. These tags cause warnings
    when parsed with standard yaml.safe_load() because they're not recognized.

    This constructor handles these tags gracefully by returning their values as-is.
    We don't need to process these tags for job name extraction - we only need
    the job-template definitions and project configurations.

    Supported tags:
    - !include-raw: - Include raw shell script
    - !include-raw-escape: - Include shell script with escaping
    - !include: - Generic include
    - !j2: - Jinja2 template processing
    - !j2-yaml: - Jinja2 with YAML output

    Args:
        loader: YAML loader instance
        node: YAML node to construct

    Returns:
        Constructed value based on node type
    """
    # Return the node value as-is (we don't need to process these)
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    elif isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


# Register all JJB custom tags
yaml.SafeLoader.add_constructor('!include-raw:', _jjb_tag_constructor)
yaml.SafeLoader.add_constructor('!include-raw-escape:', _jjb_tag_constructor)
yaml.SafeLoader.add_constructor('!include-raw-escape', _jjb_tag_constructor)
yaml.SafeLoader.add_constructor('!include:', _jjb_tag_constructor)
yaml.SafeLoader.add_constructor('!include', _jjb_tag_constructor)
yaml.SafeLoader.add_constructor('!j2:', _jjb_tag_constructor)
yaml.SafeLoader.add_constructor('!j2', _jjb_tag_constructor)
yaml.SafeLoader.add_constructor('!j2-yaml:', _jjb_tag_constructor)
yaml.SafeLoader.add_constructor('!j2-yaml', _jjb_tag_constructor)


@dataclass
class JJBJobDefinition:
    """Represents a Jenkins job definition from JJB."""

    template_name: str
    project_name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    expanded_names: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"JJBJobDefinition(template={self.template_name}, project={self.project_name})"


@dataclass
class JJBProject:
    """Represents a project block from a JJB YAML file."""

    name: str
    gerrit_project: Optional[str]
    jobs: list[JJBJobDefinition] = field(default_factory=list)
    parameters: dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"JJBProject(name={self.name}, gerrit={self.gerrit_project}, jobs={len(self.jobs)})"


class JJBAttribution:
    """
    Parser for Jenkins Job Builder (JJB) attribution.

    This class parses JJB YAML files to extract job definitions and map them
    to Gerrit projects, enabling accurate Jenkins job attribution based on
    authoritative JJB configuration files from ci-management repositories.
    """

    def __init__(self, ci_management_path: Path, global_jjb_path: Path):
        """
        Initialize the CI-Management parser.

        Args:
            ci_management_path: Path to the ci-management repository
            global_jjb_path: Path to the global-jjb repository
        """
        self.ci_management_path = Path(ci_management_path)
        self.global_jjb_path = Path(global_jjb_path)
        self.jjb_path = self.ci_management_path / "jjb"

        # Cache for parsed data
        self._templates: dict[str, dict[str, Any]] = {}
        self._job_groups: dict[str, list[str]] = {}
        self._project_cache: dict[str, list[JJBProject]] = {}
        self._gerrit_to_jjb_map: dict[str, Path] = {}

        # Verify paths exist
        if not self.ci_management_path.exists():
            logger.warning(f"CI-Management path does not exist: {self.ci_management_path}")
        if not self.global_jjb_path.exists():
            logger.warning(f"Global-JJB path does not exist: {self.global_jjb_path}")

        logger.debug(f"Initialized JJBAttribution with ci-management: {self.ci_management_path}")

    def load_templates(self) -> None:
        """
        Load JJB templates and job-groups from both global-jjb and ci-management.

        Parses all YAML files in global-jjb and ci-management to extract job-template
        definitions and job-group definitions for accurate job expansion.

        Templates from ci-management override those from global-jjb if they have the same name.
        """
        logger.info("Loading JJB templates and job-groups...")

        # Load from global-jjb first
        if self.global_jjb_path.exists():
            jjb_templates_path = self.global_jjb_path / "jjb"
            if jjb_templates_path.exists():
                template_files = list(jjb_templates_path.glob("*.yaml")) + list(
                    jjb_templates_path.glob("*.yml")
                )
                logger.info(f"Found {len(template_files)} template files in global-jjb")

                for template_file in template_files:
                    try:
                        self._load_template_file(template_file)
                    except Exception as e:
                        logger.warning(f"Failed to load template file {template_file}: {e}")
            else:
                logger.warning(f"JJB templates path does not exist: {jjb_templates_path}")
        else:
            logger.warning("Global-JJB path does not exist, skipping global-jjb templates")

        # Load from ci-management (these override global-jjb if same name)
        if self.jjb_path.exists():
            # Load top-level template files (e.g., global-templates-java.yaml)
            ci_template_files = list(self.jjb_path.glob("global-templates-*.yaml")) + list(
                self.jjb_path.glob("global-templates-*.yml")
            )
            logger.info(f"Found {len(ci_template_files)} global template files in ci-management")

            for template_file in ci_template_files:
                try:
                    self._load_template_file(template_file)
                except Exception as e:
                    logger.warning(f"Failed to load template file {template_file}: {e}")
        else:
            logger.warning(f"CI-Management JJB path does not exist: {self.jjb_path}")

        logger.info(f"Loaded {len(self._templates)} job templates and {len(self._job_groups)} job groups")

    def _load_template_file(self, template_file: Path) -> None:
        """Load templates and job-groups from a single YAML file."""
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, list):
                return

            for item in data:
                if isinstance(item, dict):
                    # Load job-template definitions
                    if "job-template" in item:
                        template = item["job-template"]
                        template_id = template.get("id")
                        template_name = template.get("name")

                        # Store by id if available, otherwise by name
                        if template_id:
                            self._templates[template_id] = template
                            logger.debug(f"Loaded template by id: {template_id} -> {template_name}")
                        elif template_name:
                            self._templates[template_name] = template
                            logger.debug(f"Loaded template by name: {template_name}")

                    # Load job-group definitions
                    elif "job-group" in item:
                        job_group = item["job-group"]
                        group_name = job_group.get("name")
                        jobs_list = job_group.get("jobs", [])

                        if group_name and jobs_list:
                            # Store the list of job templates in this group
                            self._job_groups[group_name] = jobs_list
                            logger.debug(f"Loaded job-group: {group_name} with {len(jobs_list)} jobs")

        except yaml.YAMLError as e:
            logger.warning(f"YAML error in {template_file}: {e}")
        except Exception as e:
            logger.warning(f"Error loading {template_file}: {e}")

    def find_jjb_file(self, gerrit_project: str) -> Optional[Path]:
        """
        Find the JJB YAML file for a given Gerrit project.

        Mapping logic:
        - "aai/babel" → jjb/aai/aai-babel.yaml
        - "ccsdk/apps" → jjb/ccsdk/ccsdk-apps.yaml
        - "integration" → jjb/integration/integration.yaml

        Args:
            gerrit_project: Gerrit project name (e.g., "aai/babel")

        Returns:
            Path to the JJB file, or None if not found
        """
        if gerrit_project in self._gerrit_to_jjb_map:
            return self._gerrit_to_jjb_map[gerrit_project]

        if not self.jjb_path.exists():
            logger.warning(f"JJB path does not exist: {self.jjb_path}")
            return None

        # Try different mapping strategies
        jjb_file = self._find_jjb_file_strategies(gerrit_project)

        if jjb_file:
            self._gerrit_to_jjb_map[gerrit_project] = jjb_file
            logger.debug(f"Mapped {gerrit_project} -> {jjb_file}")

        return jjb_file

    def _find_jjb_file_strategies(self, gerrit_project: str) -> Optional[Path]:
        """Try different strategies to find the JJB file."""
        # Strategy 1: Direct mapping with slashes to dashes
        # "aai/babel" -> "aai-babel.yaml"
        parts = gerrit_project.split("/")
        if len(parts) >= 2:
            parent_dir = self.jjb_path / parts[0]
            if parent_dir.exists() and parent_dir.is_dir():
                # Try exact match: aai/babel -> aai-babel.yaml
                jjb_name = "-".join(parts) + ".yaml"
                jjb_file = parent_dir / jjb_name
                if jjb_file.exists():
                    return jjb_file

                # Try with yml extension
                jjb_file = parent_dir / (jjb_name.replace(".yaml", ".yml"))
                if jjb_file.exists():
                    return jjb_file

                # Try without parent prefix: aai/babel -> babel.yaml
                jjb_name = "-".join(parts[1:]) + ".yaml"
                jjb_file = parent_dir / jjb_name
                if jjb_file.exists():
                    return jjb_file

        # Strategy 2: Single component project
        # "integration" -> "integration/integration.yaml"
        if "/" not in gerrit_project:
            project_dir = self.jjb_path / gerrit_project
            if project_dir.exists() and project_dir.is_dir():
                jjb_file = project_dir / f"{gerrit_project}.yaml"
                if jjb_file.exists():
                    return jjb_file

                jjb_file = project_dir / f"{gerrit_project}.yml"
                if jjb_file.exists():
                    return jjb_file

        # Strategy 3: Search by scanning files for matching project field
        return self._search_by_project_field(gerrit_project)

    def _search_by_project_field(self, gerrit_project: str) -> Optional[Path]:
        """Search for JJB file by looking for 'project' field in YAML files."""
        if not self.jjb_path.exists():
            return None

        # Get all YAML files recursively
        yaml_files = list(self.jjb_path.glob("**/*.yaml")) + list(
            self.jjb_path.glob("**/*.yml")
        )

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not isinstance(data, list):
                    continue

                for item in data:
                    if isinstance(item, dict) and "project" in item:
                        project_block = item["project"]
                        project_field = project_block.get("project")
                        if project_field == gerrit_project:
                            logger.debug(
                                f"Found {gerrit_project} in {yaml_file} via project field scan"
                            )
                            return yaml_file

            except Exception as e:
                logger.debug(f"Error scanning {yaml_file}: {e}")
                continue

        return None

    def parse_project_jobs(self, gerrit_project: str) -> list[str]:
        """
        Parse JJB files to get expected job names for a project.

        Args:
            gerrit_project: Gerrit project name (e.g., "aai/babel")

        Returns:
            List of expected job name patterns/names
        """
        if gerrit_project in self._project_cache:
            projects = self._project_cache[gerrit_project]
            return self._extract_job_names(projects)

        jjb_file = self.find_jjb_file(gerrit_project)
        if not jjb_file:
            logger.debug(f"No JJB file found for project: {gerrit_project}")
            return []

        projects = self._parse_jjb_file(jjb_file, gerrit_project)
        self._project_cache[gerrit_project] = projects

        return self._extract_job_names(projects)

    def _parse_jjb_file(self, jjb_file: Path, gerrit_project: str) -> list[JJBProject]:
        """Parse a JJB YAML file and extract project blocks."""
        projects: list[JJBProject] = []

        try:
            with open(jjb_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, list):
                logger.warning(f"JJB file {jjb_file} does not contain a list")
                return projects

            for item in data:
                if isinstance(item, dict) and "project" in item:
                    project_block = item["project"]
                    project_field = project_block.get("project")

                    # Only process projects matching the Gerrit project
                    if project_field and project_field != gerrit_project:
                        continue

                    jjb_project = self._parse_project_block(project_block)
                    if jjb_project:
                        projects.append(jjb_project)

            logger.debug(f"Parsed {len(projects)} project blocks from {jjb_file}")

        except yaml.YAMLError as e:
            logger.error(f"YAML error parsing {jjb_file}: {e}")
        except Exception as e:
            logger.error(f"Error parsing {jjb_file}: {e}")

        return projects

    def _parse_project_block(self, project_block: dict[str, Any]) -> Optional[JJBProject]:
        """Parse a single project block from JJB YAML."""
        try:
            name = project_block.get("name", "")
            gerrit_project = project_block.get("project")
            project_name = project_block.get("project-name", name)

            jjb_project = JJBProject(
                name=name, gerrit_project=gerrit_project, parameters=project_block
            )

            # Extract jobs
            jobs_list = project_block.get("jobs", [])
            for job_item in jobs_list:
                if isinstance(job_item, str):
                    # Check if this is a job-group reference
                    expanded_jobs = self._expand_job_group(job_item, project_name, project_block)

                    if expanded_jobs:
                        # This was a job-group, add all expanded jobs
                        for expanded_template in expanded_jobs:
                            job_def = JJBJobDefinition(
                                template_name=expanded_template,
                                project_name=project_name,
                                parameters=project_block,
                            )
                            jjb_project.jobs.append(job_def)
                    else:
                        # Simple job reference: "gerrit-maven-verify"
                        job_def = JJBJobDefinition(
                            template_name=job_item,
                            project_name=project_name,
                            parameters=project_block,
                        )
                        jjb_project.jobs.append(job_def)

                elif isinstance(job_item, dict):
                    # Job with parameters: {"gerrit-maven-stage": {"sign-artifacts": true}}
                    for template_name, params in job_item.items():
                        merged_params = {**project_block}
                        if isinstance(params, dict):
                            merged_params.update(params)

                        # Check if this is a job-group reference
                        expanded_jobs = self._expand_job_group(template_name, project_name, merged_params)

                        if expanded_jobs:
                            # This was a job-group, add all expanded jobs
                            for expanded_template in expanded_jobs:
                                job_def = JJBJobDefinition(
                                    template_name=expanded_template,
                                    project_name=project_name,
                                    parameters=merged_params,
                                )
                                jjb_project.jobs.append(job_def)
                        else:
                            job_def = JJBJobDefinition(
                                template_name=template_name,
                                project_name=project_name,
                                parameters=merged_params,
                            )
                            jjb_project.jobs.append(job_def)

            return jjb_project

        except Exception as e:
            logger.warning(f"Error parsing project block: {e}")
            return None

    def _extract_job_names(self, projects: list[JJBProject]) -> list[str]:
        """Extract all job names from parsed projects."""
        job_names = []

        for project in projects:
            for job_def in project.jobs:
                # Try to expand the job template to actual names
                expanded = self._expand_job_template(job_def)
                job_names.extend(expanded)

        return job_names

    def _expand_job_group(self, job_name: str, project_name: str, params: dict[str, Any]) -> list[str]:
        """
        Expand a job-group reference to its component job templates.

        Job groups in JJB are defined like:
        - job-group:
            name: "{project-name}-gerrit-docker-jobs"
            jobs:
              - gerrit-docker-verify
              - gerrit-docker-merge

        When a project references "{project-name}-gerrit-docker-jobs", we need to:
        1. Check if the job_name (with template variables) matches a job-group name
        2. Return the list of job templates in that group

        Args:
            job_name: Job name that might be a job-group reference (e.g., "{project-name}-gerrit-docker-jobs")
            project_name: Project name to substitute into the pattern
            params: Parameters for variable substitution

        Returns:
            List of job template names if this is a job-group, empty list otherwise
        """
        # Check if this job name (potentially with template variables) matches a job-group
        # Job-groups are stored with their template names like "{project-name}-gerrit-docker-jobs"
        if job_name in self._job_groups:
            logger.debug(f"Expanding job-group: {job_name} -> {self._job_groups[job_name]}")
            return self._job_groups[job_name]

        # Not a job-group
        return []

    def _expand_job_template(self, job_def: JJBJobDefinition) -> list[str]:
        """
        Expand a job template to actual job names.

        This is a simplified expansion that handles common cases.
        For full expansion, we would need to integrate with JJB library.
        """
        template_name = job_def.template_name
        params = job_def.parameters
        project_name = job_def.project_name

        # Check if we have a template definition
        template = self._templates.get(template_name)

        if template:
            # Use the template's name pattern
            name_pattern = template.get("name", "")
            return self._expand_name_pattern(name_pattern, params)

        # Fallback: Generate common job name patterns
        # This handles cases where templates aren't loaded
        return self._generate_common_job_patterns(template_name, project_name, params)

    def _expand_name_pattern(self, pattern: str, params: dict[str, Any]) -> list[str]:
        """Expand a JJB name pattern with parameters."""
        job_names = []

        # Handle stream expansion
        streams = params.get("stream", [])
        if streams:
            for stream_item in streams:
                if isinstance(stream_item, str):
                    stream_name = stream_item
                    stream_vars: dict[str, Any] = {}
                elif isinstance(stream_item, dict):
                    stream_name = list(stream_item.keys())[0]
                    # Extract nested variables from the stream dictionary
                    stream_vars = stream_item[stream_name] if isinstance(stream_item[stream_name], dict) else {}
                else:
                    continue

                # Create a copy of params with stream value and merge nested stream variables
                stream_params = {**params, "stream": stream_name, **stream_vars}
                expanded = self._substitute_variables(pattern, stream_params)
                job_names.append(expanded)
        else:
            # No stream, just expand with params
            expanded = self._substitute_variables(pattern, params)
            job_names.append(expanded)

        return job_names

    def _substitute_variables(self, pattern: str, params: dict[str, Any]) -> str:
        """Substitute {variable} placeholders in a pattern."""
        result = pattern

        # Find all {variable} patterns
        variables = re.findall(r"\{([^}]+)\}", pattern)

        for var in variables:
            value = params.get(var, f"{{{var}}}")  # Keep placeholder if not found

            # Skip list/dict values - they need stream expansion
            if isinstance(value, (list, dict)):
                continue

            if isinstance(value, str):
                result = result.replace(f"{{{var}}}", value)
            elif isinstance(value, (int, float, bool)):
                result = result.replace(f"{{{var}}}", str(value))

        return result

    def _generate_common_job_patterns(
        self, template_name: str, project_name: str, params: dict[str, Any]
    ) -> list[str]:
        """
        Generate common job name patterns when template isn't available.

        This provides reasonable job names based on common LF conventions.
        """
        job_names = []

        # Get common parameters
        mvn_version = params.get("mvn-version", "mvn36")
        java_version = params.get("java-version", "openjdk11")
        streams = params.get("stream", [{"master": {"branch": "master"}}])

        # Handle stream variations
        stream_names = []
        if streams:
            for stream_item in streams:
                if isinstance(stream_item, str):
                    stream_names.append(stream_item)
                elif isinstance(stream_item, dict):
                    stream_names.extend(stream_item.keys())

        if not stream_names:
            stream_names = ["master"]

        # Common template patterns
        patterns = {
            "gerrit-maven-verify": f"{project_name}-maven-verify-{{stream}}-{mvn_version}-{java_version}",
            "gerrit-maven-merge": f"{project_name}-maven-merge-{{stream}}-{mvn_version}-{java_version}",
            "gerrit-maven-stage": f"{project_name}-maven-stage-{{stream}}-{mvn_version}-{java_version}",
            "gerrit-maven-docker-stage": f"{project_name}-maven-docker-stage-{{stream}}",
            "gerrit-maven-sonar": f"{project_name}-sonar",
            "gerrit-maven-clm": f"{project_name}-clm",
            "github-maven-verify": f"{project_name}-maven-verify-{{stream}}-{mvn_version}-{java_version}",
            "github-maven-merge": f"{project_name}-maven-merge-{{stream}}-{mvn_version}-{java_version}",
        }

        # Get pattern for this template
        pattern = patterns.get(template_name)

        if pattern:
            if "{stream}" in pattern:
                # Expand for each stream
                for stream in stream_names:
                    job_name = pattern.replace("{stream}", stream)
                    job_names.append(job_name)
            else:
                job_names.append(pattern)
        else:
            # Unknown template, create a generic name
            job_names.append(f"{project_name}-{template_name}")

        return job_names

    def get_all_projects(self) -> dict[str, list[JJBProject]]:
        """
        Get all projects from all JJB files.

        Returns:
            Dictionary mapping Gerrit project names to their JJB project definitions
        """
        all_projects: dict[str, list[JJBProject]] = {}

        if not self.jjb_path.exists():
            logger.warning(f"JJB path does not exist: {self.jjb_path}")
            return all_projects

        # Find all YAML files
        yaml_files = list(self.jjb_path.glob("**/*.yaml")) + list(
            self.jjb_path.glob("**/*.yml")
        )

        logger.info(f"Scanning {len(yaml_files)} JJB files...")

        for yaml_file in yaml_files:
            # Skip global files
            if yaml_file.name.startswith("global-"):
                continue

            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if not isinstance(data, list):
                    continue

                for item in data:
                    if isinstance(item, dict) and "project" in item:
                        project_block = item["project"]
                        gerrit_project = project_block.get("project")

                        if not gerrit_project:
                            continue

                        jjb_project = self._parse_project_block(project_block)
                        if jjb_project:
                            if gerrit_project not in all_projects:
                                all_projects[gerrit_project] = []
                            all_projects[gerrit_project].append(jjb_project)

            except Exception as e:
                logger.debug(f"Error scanning {yaml_file}: {e}")
                continue

        logger.info(f"Found {len(all_projects)} Gerrit projects with JJB definitions")
        return all_projects

    def get_project_summary(self) -> dict[str, int]:
        """
        Get a summary of projects and job counts.

        Returns:
            Dictionary with statistics about parsed projects
        """
        all_projects = self.get_all_projects()

        total_jobs = 0
        for projects in all_projects.values():
            for project in projects:
                total_jobs += len(project.jobs)

        return {
            "gerrit_projects": len(all_projects),
            "jjb_project_blocks": sum(len(p) for p in all_projects.values()),
            "total_jobs": total_jobs,
            "templates_loaded": len(self._templates),
        }
