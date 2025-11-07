# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Data collectors for the reporting-tool package.

This package contains modules for collecting data from various sources:
- Git repositories (commits, contributors, activity metrics)
- API integrations (GitHub, Gerrit, Jenkins)
- Feature detection and analysis
"""

from .base import BaseCollector
from .git import GitDataCollector

__all__ = ['BaseCollector', 'GitDataCollector']
