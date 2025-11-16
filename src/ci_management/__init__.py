"""
CI Management integration module.

This module provides functionality for parsing and processing Jenkins Job Builder (JJB)
definitions from ci-management repositories to accurately allocate Jenkins jobs to
Gerrit projects.
"""

from .jjb_parser import CIManagementParser, JJBProject, JJBJobDefinition

__all__ = [
    "CIManagementParser",
    "JJBProject",
    "JJBJobDefinition",
]