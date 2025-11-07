# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
GitHub Organization Detection

Pure utility function for determining the GitHub organization name
from environment variables or repository paths.

Extracted from generate_reports.py as part of Phase 1 refactoring.
"""

import logging
import os
from pathlib import Path


def determine_github_org(repos_path: Path) -> tuple[str, str]:
    """
    Determine GitHub organization name - centralized function.

    This function uses a priority-based approach to determine the GitHub
    organization name for repositories:

    Priority:
    1. GITHUB_ORG environment variable (from PROJECTS_JSON matrix.github)
    2. Auto-derive from repos_path hostname

    Args:
        repos_path: Path to repositories directory (e.g., ./gerrit.onap.org)

    Returns:
        Tuple of (github_org, source) where:
        - github_org: Organization name (empty string if not found)
        - source: One of:
            - "environment_variable" if from GITHUB_ORG env var
            - "auto_derived" if derived from hostname
            - "" if not found

    Examples:
        >>> from pathlib import Path
        >>> # From environment variable
        >>> os.environ['GITHUB_ORG'] = 'myorg'
        >>> determine_github_org(Path('./gerrit.example.org'))
        ('myorg', 'environment_variable')

        >>> # Auto-derived from path
        >>> del os.environ['GITHUB_ORG']
        >>> determine_github_org(Path('./gerrit.onap.org'))
        ('onap', 'auto_derived')

        >>> # Not found
        >>> determine_github_org(Path('./some/other/path'))
        ('', '')

    Notes:
        - The config parameter was removed as it was unused in the original
          implementation
        - GitHub org is now purely derived from environment or path
        - Validates environment variable format (alphanumeric + hyphens only)
        - Auto-derivation assumes hostname format: gerrit.ORGNAME.tld or
          git.ORGNAME.tld
    """
    # Priority 1: Check GITHUB_ORG environment variable (from PROJECTS_JSON matrix.github)
    github_org = os.environ.get("GITHUB_ORG", "")
    if github_org:
        # Basic validation: alphanumeric and hyphens only
        # This prevents injection of invalid org names
        if _is_valid_github_org_name(github_org):
            return github_org, "environment_variable"
        else:
            logging.warning(
                f"Invalid GITHUB_ORG value '{github_org}' - must be alphanumeric with hyphens"
            )
            # Continue to auto-derivation fallback

    # Priority 2: Auto-derive from repos_path hostname
    # Examples:
    #   ./gerrit.onap.org -> onap
    #   ./git.opendaylight.org -> opendaylight
    derived_org = _derive_org_from_path(repos_path)
    if derived_org:
        return derived_org, "auto_derived"

    # Not found via any method
    return "", ""


def _is_valid_github_org_name(org_name: str) -> bool:
    """
    Validate GitHub organization name format.

    GitHub organization names must:
    - Be alphanumeric with hyphens
    - Not start or end with a hyphen
    - Be non-empty

    Args:
        org_name: Organization name to validate

    Returns:
        True if valid, False otherwise

    Examples:
        >>> _is_valid_github_org_name("my-org")
        True
        >>> _is_valid_github_org_name("myorg123")
        True
        >>> _is_valid_github_org_name("-invalid")
        False
        >>> _is_valid_github_org_name("invalid-")
        False
        >>> _is_valid_github_org_name("")
        False
        >>> _is_valid_github_org_name("my org")
        False
    """
    if not org_name:
        return False

    # Check for valid characters (alphanumeric and hyphen)
    if not all(c.isalnum() or c == '-' for c in org_name):
        return False

    # Check that it doesn't start or end with hyphen
    if org_name.startswith('-') or org_name.endswith('-'):
        return False

    return True


def _derive_org_from_path(repos_path: Path) -> str:
    """
    Derive organization name from repository path hostname.

    Expects path components containing hostname patterns like:
    - gerrit.ORGNAME.tld
    - git.ORGNAME.tld

    Args:
        repos_path: Path to repositories directory

    Returns:
        Organization name if found, empty string otherwise

    Examples:
        >>> _derive_org_from_path(Path('./gerrit.onap.org'))
        'onap'
        >>> _derive_org_from_path(Path('./git.opendaylight.org'))
        'opendaylight'
        >>> _derive_org_from_path(Path('./some/other/path'))
        ''
    """
    for part in repos_path.parts:
        part_lower = part.lower()

        # Look for gerrit.* or git.* patterns
        if 'gerrit.' in part_lower or 'git.' in part_lower:
            # Split hostname on dots and extract middle part
            # gerrit.onap.org -> ['gerrit', 'onap', 'org'] -> 'onap'
            parts = part.split('.')

            # Need at least 3 parts: prefix.org.tld
            if len(parts) >= 3:
                # Return the middle part (organization name)
                org_name = parts[1]

                # Validate before returning
                if _is_valid_github_org_name(org_name):
                    return org_name

    # No valid org found
    return ""


def format_source_for_display(source: str) -> str:
    """
    Format the source string for display in logs/reports.

    Args:
        source: Source identifier from determine_github_org

    Returns:
        Human-readable source description

    Examples:
        >>> format_source_for_display("environment_variable")
        'from JSON'
        >>> format_source_for_display("auto_derived")
        'auto/derived'
        >>> format_source_for_display("")
        'not configured'
    """
    source_map = {
        "environment_variable": "from JSON",
        "auto_derived": "auto/derived",
        "": "not configured"
    }
    return source_map.get(source, source)
