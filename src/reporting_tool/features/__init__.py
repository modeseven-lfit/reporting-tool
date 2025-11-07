# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Feature detection for the reporting-tool package.

This package contains modules for detecting features in repositories:
- CI/CD systems (Jenkins, GitHub Actions, GitLab CI)
- Dependency management (requirements.txt, package.json, pom.xml)
- Documentation (README, docs/, ReadTheDocs)
- Code quality tools (pre-commit, linters, formatters)
- Security tools (Dependabot, CodeQL)
"""

from .registry import FeatureRegistry

__all__ = ["FeatureRegistry"]
