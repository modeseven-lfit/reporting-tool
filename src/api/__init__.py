# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
API Client Package

This package contains API clients for external services:
- GitHub API (workflow status, repository information)
- Gerrit API (project information, repository discovery)
- Jenkins API (job information, build status)

All API clients follow a standardized response envelope pattern for
consistent error handling and observability.

Extracted from generate_reports.py as part of Phase 2 refactoring.
"""

from .base_client import (
    APIResponse,
    APIError,
    BaseAPIClient,
)

from .github_client import GitHubAPIClient

from .gerrit_client import (
    GerritAPIClient,
    GerritAPIDiscovery,
    GerritAPIError,
    GerritConnectionError,
)

from .jenkins_client import JenkinsAPIClient

__all__ = [
    # Base classes and types
    'APIResponse',
    'APIError',
    'BaseAPIClient',

    # GitHub API
    'GitHubAPIClient',

    # Gerrit API
    'GerritAPIClient',
    'GerritAPIDiscovery',
    'GerritAPIError',
    'GerritConnectionError',

    # Jenkins API
    'JenkinsAPIClient',
]

__version__ = '1.0.0'
