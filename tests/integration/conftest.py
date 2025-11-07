# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Integration test configuration and fixtures.

This module makes fixtures from tests/fixtures available to integration tests.
"""

import sys
from pathlib import Path


# Add parent directory to path so we can import fixtures
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all fixtures from the fixtures module
from fixtures.repositories import (
    clean_environment,
    create_synthetic_repository,
    create_test_config,
    mock_github_env,
    sample_author_data,
    sample_commit_data,
    sample_json_file,
    sample_repository_data,
    synthetic_repo_complex,
    synthetic_repo_simple,
    temp_git_repo,
    temp_output_dir,
    test_config_complete,
    test_config_minimal,
    test_config_with_repos,
)


# Make fixtures available to integration tests
__all__ = [
    "temp_git_repo",
    "synthetic_repo_simple",
    "synthetic_repo_complex",
    "create_synthetic_repository",
    "test_config_minimal",
    "test_config_complete",
    "test_config_with_repos",
    "create_test_config",
    "sample_commit_data",
    "sample_repository_data",
    "sample_author_data",
    "temp_output_dir",
    "sample_json_file",
    "mock_github_env",
    "clean_environment",
]
