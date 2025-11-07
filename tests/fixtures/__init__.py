# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Test fixtures package.

This package contains reusable test fixtures for the reporting tool test suite.
"""

from .repositories import (
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


__all__ = [
    "clean_environment",
    "create_synthetic_repository",
    "create_test_config",
    "mock_github_env",
    "sample_author_data",
    "sample_commit_data",
    "sample_json_file",
    "sample_repository_data",
    "synthetic_repo_complex",
    "synthetic_repo_simple",
    "temp_git_repo",
    "temp_output_dir",
    "test_config_complete",
    "test_config_minimal",
    "test_config_with_repos",
]
