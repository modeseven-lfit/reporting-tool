# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Reporting Tool - Comprehensive Multi-Repository Analysis Tool

A modern Python package for analyzing Git repositories and generating
comprehensive reports with metrics, feature detection, and contributor analysis.

Key Features:
- Git activity metrics across configurable time windows
- Automatic CI/CD workflow detection (Jenkins, GitHub Actions)
- Contributor and organization analysis
- Multi-format output (JSON, Markdown, HTML, ZIP)
- Gerrit API integration
- Performance-optimized with concurrent processing

Usage:
    From command line:
        $ reporting-tool generate --project my-project --repos-path ./repos

    With configuration:
        $ reporting-tool generate --project my-project --config-dir ./config

For more information:
    - GitHub: https://github.com/lfit/reporting-tool
    - License: Apache-2.0
"""

from reporting_tool._version import __version__

__author__ = "The Linux Foundation"
__license__ = "Apache-2.0"

# Public API (to be implemented)
__all__ = [
    "__version__",
    "__author__",
    "__license__",
]
