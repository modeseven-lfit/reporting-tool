# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
JJB Attribution module.

This module provides functionality for parsing and processing Jenkins Job Builder (JJB)
definitions from ci-management repositories to accurately allocate Jenkins jobs to
Gerrit projects using authoritative JJB configuration files.
"""

from .jjb_parser import JJBAttribution, JJBProject, JJBJobDefinition
from .repo_manager import JJBRepoManager

__all__ = [
    "JJBAttribution",
    "JJBProject",
    "JJBJobDefinition",
    "JJBRepoManager",
]
