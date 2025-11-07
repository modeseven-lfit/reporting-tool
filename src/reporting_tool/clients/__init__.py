# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
API clients for the reporting-tool package.

This package contains clients for interacting with external APIs:
- GitHub API (workflow status, repository information)
- Gerrit API (code review system integration)
- Jenkins API (CI/CD build status)

All clients support:
- Thread-safe operation
- Connection pooling
- Error handling and retry logic
- Statistics tracking
"""

# Clients will be imported as they are created
# from .github import GitHubAPIClient
# from .gerrit import GerritAPIClient, GerritAPIDiscovery
# from .jenkins import JenkinsAPIClient

__all__ = []
