# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Custom exceptions for the reporting-tool package.

This module defines all custom exceptions used throughout the reporting tool,
providing clear error messages and error handling.
"""


class ReportingToolError(Exception):
    """Base exception for all reporting tool errors."""
    pass


class ConfigurationError(ReportingToolError):
    """Raised when configuration is invalid or missing."""
    pass


class CLIError(ReportingToolError):
    """Raised when CLI usage is incorrect."""
    pass


class GerritAPIError(ReportingToolError):
    """Raised when Gerrit API returns an error."""
    pass


class GerritConnectionError(ReportingToolError):
    """Raised when connection to Gerrit fails."""
    pass


class JenkinsAPIError(ReportingToolError):
    """Raised when Jenkins API returns an error."""
    pass


class JenkinsConnectionError(ReportingToolError):
    """Raised when connection to Jenkins fails."""
    pass


class GitHubAPIError(ReportingToolError):
    """Raised when GitHub API returns an error."""
    pass


class GitHubConnectionError(ReportingToolError):
    """Raised when connection to GitHub fails."""
    pass


class RepositoryError(ReportingToolError):
    """Raised when repository operations fail."""
    pass


class CollectionError(ReportingToolError):
    """Raised when data collection fails."""
    pass


class RenderingError(ReportingToolError):
    """Raised when report rendering fails."""
    pass


class ValidationError(ReportingToolError):
    """Raised when validation fails."""
    pass
