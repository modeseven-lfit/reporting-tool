# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
INFO.yaml parser module.

Handles parsing of INFO.yaml files from the LF info-master repository,
extracting project metadata, committer information, and organizational data.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from domain.info_yaml import (
    CommitterInfo,
    IssueTracking,
    PersonInfo,
    ProjectInfo,
)

logger = logging.getLogger(__name__)


class INFOYamlParser:
    """
    Parser for INFO.yaml files.

    Extracts structured project information from YAML format and converts
    it into domain models for further processing.
    """

    def __init__(self, info_master_path: Path):
        """
        Initialize the parser.

        Args:
            info_master_path: Path to the root of the info-master repository
        """
        self.info_master_path = info_master_path
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse_file(self, yaml_file: Path) -> Optional[ProjectInfo]:
        """
        Parse a single INFO.yaml file.

        Args:
            yaml_file: Path to the INFO.yaml file

        Returns:
            ProjectInfo object if parsing succeeds, None otherwise
        """
        try:
            # Validate file exists and is readable
            if not yaml_file.exists():
                self.logger.warning(f"INFO.yaml file does not exist: {yaml_file}")
                return None

            if not yaml_file.is_file():
                self.logger.warning(f"Path is not a file: {yaml_file}")
                return None

            # Load YAML content
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                self.logger.warning(f"Empty or invalid YAML file: {yaml_file}")
                return None

            # Extract project information
            project_info = self._extract_project_info(yaml_file, data)
            return project_info

        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error in {yaml_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error parsing {yaml_file}: {e}")
            return None

    def parse_directory(self, directory: Path) -> List[ProjectInfo]:
        """
        Recursively parse all INFO.yaml files in a directory.

        Args:
            directory: Directory to search for INFO.yaml files

        Returns:
            List of successfully parsed ProjectInfo objects
        """
        projects: list[ProjectInfo] = []

        if not directory.exists():
            self.logger.error(f"Directory does not exist: {directory}")
            return projects

        if not directory.is_dir():
            self.logger.error(f"Path is not a directory: {directory}")
            return projects

        self.logger.info(f"Scanning directory for INFO.yaml files: {directory}")

        # Find all INFO.yaml files recursively
        yaml_files = list(directory.rglob("INFO.yaml"))
        self.logger.info(f"Found {len(yaml_files)} INFO.yaml files")

        # Parse each file
        for yaml_file in yaml_files:
            project_info = self.parse_file(yaml_file)
            if project_info:
                projects.append(project_info)

        self.logger.info(f"Successfully parsed {len(projects)} projects")
        return projects

    def _extract_project_info(
        self, yaml_file: Path, data: Dict[str, Any]
    ) -> Optional[ProjectInfo]:
        """
        Extract project information from parsed YAML data.

        Args:
            yaml_file: Path to the YAML file (for metadata)
            data: Parsed YAML data

        Returns:
            ProjectInfo object or None if extraction fails
        """
        try:
            # Extract relative path from info-master root
            relative_path = yaml_file.relative_to(self.info_master_path)
            path_parts = relative_path.parts

            # Extract gerrit server (first directory component)
            gerrit_server = path_parts[0] if len(path_parts) > 0 else "unknown"

            # Extract project path (everything except the last component which is INFO.yaml)
            # and the first component which is the gerrit server
            project_path_parts = list(path_parts[:-1])  # Remove INFO.yaml
            if len(project_path_parts) > 1:
                project_path_parts = project_path_parts[1:]  # Remove gerrit server
            project_path = "/".join(project_path_parts) if project_path_parts else ""

            # Full path includes the gerrit server
            full_path = str(relative_path.parent)

            # Extract project metadata
            project_name = data.get("project", "Unknown")
            creation_date = data.get("project_creation_date", "Unknown")
            lifecycle_state = data.get("lifecycle_state", "Unknown")

            # Extract project lead
            project_lead = self._extract_person(data.get("project_lead"))

            # Extract committers
            committers = self._extract_committers(data.get("committers", []))

            # Extract issue tracking
            issue_tracking = self._extract_issue_tracking(data.get("issue_tracking", {}))

            # Extract repositories
            repositories = self._extract_repositories(data.get("repositories", []))

            # Create ProjectInfo object
            project_info = ProjectInfo(
                project_name=project_name,
                gerrit_server=gerrit_server,
                project_path=project_path,
                full_path=full_path,
                creation_date=creation_date,
                lifecycle_state=lifecycle_state,
                project_lead=project_lead,
                committers=committers,
                issue_tracking=issue_tracking,
                repositories=repositories,
                yaml_file_path=str(yaml_file),
            )

            return project_info

        except ValueError as e:
            self.logger.error(f"Validation error for {yaml_file}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error extracting project info from {yaml_file}: {e}")
            return None

    def _extract_person(self, person_data: Any) -> Optional[PersonInfo]:
        """
        Extract person information from YAML data.

        Args:
            person_data: Person data from YAML (dict or None)

        Returns:
            PersonInfo object or None if data is invalid
        """
        if not person_data or not isinstance(person_data, dict):
            return None

        try:
            # Extract fields with defaults
            name = person_data.get("name", "Unknown")
            email = person_data.get("email", "")
            company = person_data.get("company", "")
            person_id = person_data.get("id", "")
            timezone = person_data.get("timezone", "")

            # Skip if name is Unknown or empty
            if not name or name == "Unknown":
                return None

            return PersonInfo(
                name=name,
                email=email,
                company=company,
                id=person_id,
                timezone=timezone,
            )
        except ValueError as e:
            self.logger.warning(f"Invalid person data: {e}")
            return None

    def _extract_committers(self, committers_data: Any) -> List[CommitterInfo]:
        """
        Extract committers list from YAML data.

        Args:
            committers_data: Committers list from YAML (list or None)

        Returns:
            List of CommitterInfo objects (may be empty)
        """
        if not committers_data or not isinstance(committers_data, list):
            return []

        committers = []
        for committer_data in committers_data:
            if not isinstance(committer_data, dict):
                continue

            try:
                # Extract fields with defaults
                name = committer_data.get("name", "Unknown")
                email = committer_data.get("email", "")
                company = committer_data.get("company", "")
                committer_id = committer_data.get("id", "")
                timezone = committer_data.get("timezone", "")

                # Skip if name is Unknown or empty
                if not name or name == "Unknown":
                    continue

                committer = CommitterInfo(
                    name=name,
                    email=email,
                    company=company,
                    id=committer_id,
                    timezone=timezone,
                    # Default to unknown activity status
                    activity_status="unknown",
                    activity_color="gray",
                )
                committers.append(committer)

            except ValueError as e:
                self.logger.warning(f"Invalid committer data: {e}")
                continue

        return committers

    def _extract_issue_tracking(self, issue_data: Any) -> IssueTracking:
        """
        Extract issue tracking information from YAML data.

        Args:
            issue_data: Issue tracking data from YAML (dict or None)

        Returns:
            IssueTracking object (may be empty if no data)
        """
        if not issue_data or not isinstance(issue_data, dict):
            return IssueTracking()

        tracker_type = issue_data.get("type", "")
        url = issue_data.get("url", "")

        return IssueTracking(
            type=tracker_type,
            url=url,
            is_valid=False,  # Will be validated later
            validation_error="",
        )

    def _extract_repositories(self, repositories_data: Any) -> List[str]:
        """
        Extract repositories list from YAML data.

        Args:
            repositories_data: Repositories list from YAML (list or None)

        Returns:
            List of repository names (may be empty)
        """
        if not repositories_data or not isinstance(repositories_data, list):
            return []

        repositories = []
        for repo in repositories_data:
            if isinstance(repo, str):
                repositories.append(repo)
            elif isinstance(repo, dict) and "name" in repo:
                repositories.append(repo["name"])

        return repositories


def parse_info_yaml_file(
    yaml_file: Path, info_master_path: Path
) -> Optional[ProjectInfo]:
    """
    Convenience function to parse a single INFO.yaml file.

    Args:
        yaml_file: Path to the INFO.yaml file
        info_master_path: Path to the root of the info-master repository

    Returns:
        ProjectInfo object if parsing succeeds, None otherwise
    """
    parser = INFOYamlParser(info_master_path)
    return parser.parse_file(yaml_file)


def parse_info_yaml_directory(directory: Path) -> List[ProjectInfo]:
    """
    Convenience function to parse all INFO.yaml files in a directory.

    Args:
        directory: Directory to search for INFO.yaml files

    Returns:
        List of successfully parsed ProjectInfo objects
    """
    parser = INFOYamlParser(directory)
    return parser.parse_directory(directory)
