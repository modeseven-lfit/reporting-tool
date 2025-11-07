# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Root test configuration and fixtures.

This module configures pytest for all tests and makes the src/ directory
importable for all test modules.

Phase 13: CLI & UX Improvements - Fix test infrastructure
Phase 14: Test Reliability - Import test utilities from test_utils module
"""

import sys
from pathlib import Path

import pytest
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
from test_utils import (  # type: ignore[import-not-found]
    DEFAULT_TEST_TIMEOUTS,
    assert_command_success,
    assert_git_operation,
    assert_no_error_logs,
    assert_repository_state,
    assert_test_operation,
    ensure_clean_environment,
    format_dict_diff,
    get_git_log,
    # Enhanced error messages (Phase 14: Test Reliability - Phase 4)
    get_git_status,
    get_repository_info,
    mark_flaky,
    reset_global_state,
    retry_on_failure,
    run_git_command_safe,
    save_test_artifacts,
)


# Make fixtures and utilities available to all tests
__all__ = [
    # Fixtures
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
    # Test utilities
    "run_git_command_safe",
    "DEFAULT_TEST_TIMEOUTS",
    "retry_on_failure",
    "mark_flaky",
    "reset_global_state",
    "ensure_clean_environment",
    # Enhanced error messages
    "get_git_status",
    "get_git_log",
    "get_repository_info",
    "format_dict_diff",
    "assert_repository_state",
    "assert_git_operation",
    "assert_test_operation",
    "save_test_artifacts",
    "assert_no_error_logs",
    "assert_command_success",
    # Auto-reset fixtures
    "auto_reset_global_state",
    "auto_clean_environment",
]

# Add src directory to Python path so tests can import from src.*
# This fixes the ModuleNotFoundError: No module named 'src' issue
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
tests_path = Path(__file__).parent

sys.path.insert(0, str(src_path))

# Add tests directory to sys.path for consistent imports
if str(tests_path) not in sys.path:
    sys.path.insert(0, str(tests_path))


# ============================================================================
# Auto-Reset Fixtures for Test Isolation (Phase 14: Test Reliability - Phase 3)
# ============================================================================


@pytest.fixture(autouse=True)
def auto_reset_global_state():
    """
    Automatically reset global state before and after each test.

    This fixture runs automatically for every test (autouse=True) to ensure
    complete test isolation. It resets:
    - Global metrics collector
    - Performance caches
    - Benchmark runner state
    - Any other global singletons

    This prevents state leakage between tests and ensures tests can run
    in any order without affecting each other.
    """
    # Reset state before test
    reset_global_state()

    yield

    # Reset state after test
    reset_global_state()


@pytest.fixture(autouse=True)
def auto_clean_environment():
    """
    Automatically clean test environment variables before and after each test.

    This fixture runs automatically for every test (autouse=True) to ensure
    environment variables set by one test don't affect other tests.

    This is particularly important for tests that modify environment
    variables like GITHUB_TOKEN, GERRIT_URL, etc.
    """
    # Clean environment before test
    ensure_clean_environment()

    yield

    # Clean environment after test
    ensure_clean_environment()
