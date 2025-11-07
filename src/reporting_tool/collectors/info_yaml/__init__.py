# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
INFO.yaml collector package.

This package provides functionality for collecting and processing INFO.yaml
files from the LF info-master repository, extracting project metadata and
committer information.

Main Components:
    - INFOYamlCollector: Main collector class
    - INFOYamlParser: Parser for INFO.yaml files
    - InfoYamlEnricher: Git data enrichment and activity calculation
    - CommitterMatcher: Committer-to-author matching
    - URLValidator: Issue tracker URL validation
    - Domain models: ProjectInfo, CommitterInfo, etc. (in src.domain.info_yaml)
"""

from .collector import INFOYamlCollector
from .enricher import InfoYamlEnricher
from .matcher import CommitterMatcher
from .parser import INFOYamlParser
from .validator import URLValidator

__all__ = [
    'INFOYamlCollector',
    'INFOYamlParser',
    'InfoYamlEnricher',
    'CommitterMatcher',
    'URLValidator',
]
