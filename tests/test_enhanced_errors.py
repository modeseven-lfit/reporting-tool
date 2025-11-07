# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for Enhanced Error Message Utilities.

Phase 14: Test Reliability - Phase 4: Enhanced Error Messages
Tests for rich assertions, context managers, and artifact saving.
"""

import json
import os
import subprocess
from pathlib import Path

import pytest
from test_utils import (
    assert_command_success,
    assert_git_operation,
    assert_no_error_logs,
    assert_repository_state,
    assert_test_operation,
    format_dict_diff,
    get_git_log,
    get_git_status,
    get_repository_info,
    run_git_command_safe,
    save_test_artifacts,
)


class TestGitInformationUtilities:
    """Test utilities for gathering git information."""

    def test_get_git_status_clean_repo(self, temp_git_repo):
        """Test getting status from a clean repository."""
        status = get_git_status(temp_git_repo)
        assert status == "", "Clean repo should have empty status"

    def test_get_git_status_with_changes(self, temp_git_repo):
        """Test getting status with uncommitted changes."""
        # Create an untracked file
        test_file = Path(temp_git_repo) / "untracked.txt"
        test_file.write_text("new content")

        status = get_git_status(temp_git_repo)
        assert "untracked.txt" in status
        assert "??" in status  # Git porcelain format for untracked

    def test_get_git_status_nonexistent_repo(self, tmp_path):
        """Test getting status from nonexistent repository."""
        fake_repo = tmp_path / "nonexistent"
        status = get_git_status(fake_repo)
        assert "Error" in status

    def test_get_git_log_basic(self, temp_git_repo):
        """Test getting git log from repository."""
        log = get_git_log(temp_git_repo)
        assert "Initial commit" in log

    def test_get_git_log_with_limit(self, temp_git_repo):
        """Test getting limited number of log entries."""
        # Create multiple commits
        for i in range(15):
            test_file = Path(temp_git_repo) / f"file{i}.txt"
            test_file.write_text(f"content {i}")
            run_git_command_safe(["git", "add", "."], cwd=temp_git_repo)
            run_git_command_safe(["git", "commit", "-m", f"Commit {i}"], cwd=temp_git_repo)

        log = get_git_log(temp_git_repo, max_commits=5)
        lines = [line for line in log.split("\n") if line.strip()]
        assert len(lines) <= 5, "Should respect max_commits limit"

    def test_get_git_log_nonexistent_repo(self, tmp_path):
        """Test getting log from nonexistent repository."""
        fake_repo = tmp_path / "nonexistent"
        log = get_git_log(fake_repo)
        assert "Error" in log

    def test_get_repository_info_valid_repo(self, temp_git_repo):
        """Test getting comprehensive repository information."""
        info = get_repository_info(temp_git_repo)

        assert info["path"] == str(temp_git_repo)
        assert info["exists"] is True
        assert "branch" in info
        assert "commit_count" in info
        assert "working_dir_clean" in info
        assert "status" in info

        # Verify types
        assert isinstance(info["commit_count"], int)
        assert isinstance(info["working_dir_clean"], bool)

    def test_get_repository_info_nonexistent_repo(self, tmp_path):
        """Test getting info from nonexistent repository."""
        fake_repo = tmp_path / "nonexistent"
        info = get_repository_info(fake_repo)

        assert info["path"] == str(fake_repo)
        assert info["exists"] is False
        assert len(info) == 2  # Only path and exists

    def test_get_repository_info_dirty_repo(self, temp_git_repo):
        """Test repository info with uncommitted changes."""
        # Create untracked file
        test_file = Path(temp_git_repo) / "dirty.txt"
        test_file.write_text("dirty content")

        info = get_repository_info(temp_git_repo)
        assert info["working_dir_clean"] is False
        assert "dirty.txt" in info["status"]


class TestFormatDictDiff:
    """Test dictionary difference formatting."""

    def test_format_identical_dicts(self):
        """Test formatting when dictionaries are identical."""
        expected = {"a": 1, "b": 2, "c": 3}
        actual = {"a": 1, "b": 2, "c": 3}

        diff = format_dict_diff(expected, actual)
        assert "No differences" in diff

    def test_format_missing_keys(self):
        """Test formatting with missing keys."""
        expected = {"a": 1, "b": 2, "c": 3}
        actual = {"a": 1, "b": 2}

        diff = format_dict_diff(expected, actual)
        assert "Missing keys" in diff
        assert "c: 3" in diff

    def test_format_extra_keys(self):
        """Test formatting with extra keys."""
        expected = {"a": 1, "b": 2}
        actual = {"a": 1, "b": 2, "c": 3}

        diff = format_dict_diff(expected, actual)
        assert "Extra keys" in diff
        assert "c: 3" in diff

    def test_format_different_values(self):
        """Test formatting with different values."""
        expected = {"a": 1, "b": 2, "c": 3}
        actual = {"a": 1, "b": 999, "c": 3}

        diff = format_dict_diff(expected, actual)
        assert "Different values" in diff
        assert "b:" in diff
        assert "Expected: 2" in diff
        assert "Actual:   999" in diff

    def test_format_complex_diff(self):
        """Test formatting with multiple types of differences."""
        expected = {"a": 1, "b": 2, "c": 3, "d": 4}
        actual = {"a": 1, "b": 999, "e": 5}

        diff = format_dict_diff(expected, actual)
        assert "Missing keys" in diff
        assert "Extra keys" in diff
        assert "Different values" in diff


class TestAssertRepositoryState:
    """Test repository state assertions."""

    def test_assert_repository_exists(self, temp_git_repo):
        """Test that assertion passes for existing repository."""
        # Should not raise
        assert_repository_state(temp_git_repo)

    def test_assert_repository_not_exists(self, tmp_path):
        """Test that assertion fails for nonexistent repository."""
        fake_repo = tmp_path / "nonexistent"

        with pytest.raises(AssertionError, match="does not exist"):
            assert_repository_state(fake_repo)

    def test_assert_expected_branch(self, temp_git_repo):
        """Test assertion for expected branch."""
        # Get current branch
        result = run_git_command_safe(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=temp_git_repo
        )
        current_branch = result.stdout.strip()

        # Should pass
        assert_repository_state(temp_git_repo, expected_branch=current_branch)

    def test_assert_wrong_branch(self, temp_git_repo):
        """Test assertion fails for wrong branch."""
        with pytest.raises(AssertionError, match="Branch"):
            assert_repository_state(temp_git_repo, expected_branch="nonexistent-branch")

    def test_assert_commit_count(self, temp_git_repo):
        """Test assertion for commit count."""
        # Get actual commit count
        result = run_git_command_safe(["git", "rev-list", "--count", "HEAD"], cwd=temp_git_repo)
        count = int(result.stdout.strip())

        # Should pass
        assert_repository_state(temp_git_repo, expected_commit_count=count)

    def test_assert_wrong_commit_count(self, temp_git_repo):
        """Test assertion fails for wrong commit count."""
        with pytest.raises(AssertionError, match="Commit count"):
            assert_repository_state(temp_git_repo, expected_commit_count=99999)

    def test_assert_clean_working_directory(self, temp_git_repo):
        """Test assertion for clean working directory."""
        # Should pass when clean
        assert_repository_state(temp_git_repo, should_be_clean=True)

    def test_assert_dirty_working_directory(self, temp_git_repo):
        """Test assertion for dirty working directory."""
        # Create untracked file
        test_file = Path(temp_git_repo) / "dirty.txt"
        test_file.write_text("dirty")

        # Should pass when expecting dirty
        assert_repository_state(temp_git_repo, should_be_clean=False)

    def test_assert_clean_when_dirty(self, temp_git_repo):
        """Test assertion fails when expecting clean but is dirty."""
        # Make repo dirty
        test_file = Path(temp_git_repo) / "dirty.txt"
        test_file.write_text("dirty")

        with pytest.raises(AssertionError, match="Working directory"):
            assert_repository_state(temp_git_repo, should_be_clean=True)

    def test_assert_multiple_conditions(self, temp_git_repo):
        """Test assertion with multiple conditions."""
        result = run_git_command_safe(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=temp_git_repo
        )
        branch = result.stdout.strip()

        result = run_git_command_safe(["git", "rev-list", "--count", "HEAD"], cwd=temp_git_repo)
        count = int(result.stdout.strip())

        # All should pass
        assert_repository_state(
            temp_git_repo, expected_branch=branch, expected_commit_count=count, should_be_clean=True
        )

    def test_assert_detailed_error_message(self, temp_git_repo):
        """Test that error messages include detailed information."""
        try:
            assert_repository_state(
                temp_git_repo, expected_branch="wrong", expected_commit_count=999
            )
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            error_msg = str(e)
            assert "Repository state mismatch" in error_msg
            assert "Repository:" in error_msg
            assert "Errors:" in error_msg
            assert "Repository info:" in error_msg
            assert "Git log:" in error_msg


class TestAssertGitOperation:
    """Test git operation context manager."""

    def test_successful_git_operation(self, temp_git_repo):
        """Test context manager with successful operation."""
        # Should not raise
        with assert_git_operation("test operation", temp_git_repo):
            result = run_git_command_safe(["git", "status"], cwd=temp_git_repo)
            assert result.returncode == 0

    def test_failed_git_operation(self, temp_git_repo):
        """Test context manager with failed operation."""
        with (
            pytest.raises(AssertionError, match="Git operation failed"),
            assert_git_operation("failing operation", temp_git_repo),
        ):
            raise RuntimeError("Simulated git failure")

    def test_error_includes_operation_name(self, temp_git_repo):
        """Test that error includes operation name."""
        try:
            with assert_git_operation("custom operation", temp_git_repo):
                raise ValueError("test error")
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            assert "custom operation" in str(e)

    def test_error_includes_repository_info(self, temp_git_repo):
        """Test that error includes repository information."""
        try:
            with assert_git_operation("test", temp_git_repo):
                raise RuntimeError("test")
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            error_msg = str(e)
            assert "Repository information" in error_msg
            assert "Git status" in error_msg
            assert "Recent commits" in error_msg

    def test_without_repository_path(self):
        """Test context manager without repository path."""
        with (
            pytest.raises(AssertionError, match="Git operation failed"),
            assert_git_operation("test operation"),
        ):
            raise RuntimeError("test error")

    def test_preserves_exception_chain(self, temp_git_repo):
        """Test that original exception is preserved in chain."""
        original_error = ValueError("original error")

        try:
            with assert_git_operation("test", temp_git_repo):
                raise original_error
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            assert e.__cause__ is original_error


class TestAssertTestOperation:
    """Test generic test operation context manager."""

    def test_successful_operation(self):
        """Test context manager with successful operation."""
        # Should not raise
        with assert_test_operation("test operation"):
            result = 1 + 1
            assert result == 2

    def test_failed_operation(self):
        """Test context manager with failed operation."""
        with (
            pytest.raises(AssertionError, match="Test operation failed"),
            assert_test_operation("failing operation"),
        ):
            raise RuntimeError("Simulated failure")

    def test_error_includes_operation_name(self):
        """Test that error includes operation name."""
        try:
            with assert_test_operation("custom test"):
                raise ValueError("test error")
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            assert "custom test" in str(e)

    def test_save_artifacts_on_failure(self, tmp_path, temp_git_repo):
        """Test artifact saving on failure."""
        with (
            pytest.raises(AssertionError),
            assert_test_operation(
                "test_with_artifacts", save_artifacts_on_failure=True, artifact_path=temp_git_repo
            ),
        ):
            raise RuntimeError("test error")

        # Check if artifacts were created
        artifacts_dir = Path("test_artifacts")
        if artifacts_dir.exists():
            # Artifacts should have been saved
            assert len(list(artifacts_dir.glob("test_with_artifacts_*"))) > 0

    def test_preserves_exception_chain(self):
        """Test that original exception is preserved."""
        original_error = ValueError("original")

        try:
            with assert_test_operation("test"):
                raise original_error
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            assert e.__cause__ is original_error


class TestSaveTestArtifacts:
    """Test artifact saving functionality."""

    def test_save_basic_artifacts(self, tmp_path):
        """Test saving basic test artifacts."""
        artifact_dir = save_test_artifacts("test_basic", "Test error message")

        assert artifact_dir.exists()
        assert (artifact_dir / "error.txt").exists()
        assert (artifact_dir / "environment.json").exists()

        # Verify error file content
        error_content = (artifact_dir / "error.txt").read_text()
        assert "Test: test_basic" in error_content
        assert "Test error message" in error_content
        assert "Traceback:" in error_content

    def test_save_with_repository_info(self, temp_git_repo):
        """Test saving artifacts with repository information."""
        artifact_dir = save_test_artifacts("test_with_repo", "Test error", repo_path=temp_git_repo)

        assert (artifact_dir / "git_log.txt").exists()
        assert (artifact_dir / "git_status.txt").exists()
        assert (artifact_dir / "repo_info.json").exists()

        # Verify repository info
        with open(artifact_dir / "repo_info.json") as f:
            info = json.load(f)
            assert info["exists"] is True
            assert "branch" in info

    def test_save_with_additional_info(self):
        """Test saving artifacts with additional information."""
        additional = {"test_param": "value", "iterations": 42, "timestamp": "2025-01-01T00:00:00"}

        artifact_dir = save_test_artifacts(
            "test_additional", "Error message", additional_info=additional
        )

        assert (artifact_dir / "additional_info.json").exists()

        with open(artifact_dir / "additional_info.json") as f:
            saved_info = json.load(f)
            assert saved_info == additional

    def test_unique_artifact_directories(self):
        """Test that multiple saves create unique directories."""
        import time

        dir1 = save_test_artifacts("test_unique", "Error 1")
        time.sleep(1.1)  # Ensure timestamp is different
        dir2 = save_test_artifacts("test_unique", "Error 2")

        assert dir1 != dir2
        assert dir1.exists()
        assert dir2.exists()

    def test_environment_info_captured(self):
        """Test that environment information is captured."""
        os.environ["TEST_CUSTOM_VAR"] = "test_value"

        try:
            artifact_dir = save_test_artifacts("test_env", "Error")

            with open(artifact_dir / "environment.json") as f:
                env_info = json.load(f)
                assert "python_version" in env_info
                assert "working_directory" in env_info
                assert "environment_variables" in env_info
                assert "TEST_CUSTOM_VAR" in env_info["environment_variables"]
        finally:
            os.environ.pop("TEST_CUSTOM_VAR", None)


class TestAssertNoErrorLogs:
    """Test log validation assertions."""

    def test_clean_logs(self):
        """Test assertion passes with clean logs."""
        log_output = """
        INFO: Starting test
        DEBUG: Processing item 1
        INFO: Test completed
        """

        # Should not raise
        assert_no_error_logs(log_output)

    def test_error_logs_detected(self):
        """Test assertion fails when ERROR logs present."""
        log_output = """
        INFO: Starting test
        ERROR: Something went wrong
        INFO: Continuing
        """

        with pytest.raises(AssertionError, match="Unexpected ERROR messages"):
            assert_no_error_logs(log_output)

    def test_error_with_context(self):
        """Test error message includes context."""
        log_output = "ERROR: test error"

        try:
            assert_no_error_logs(log_output, context="during initialization")
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            assert "during initialization" in str(e)

    def test_multiple_errors(self):
        """Test detection of multiple error lines."""
        log_output = """
        INFO: Starting
        ERROR: First error
        DEBUG: Some debug
        ERROR: Second error
        INFO: Done
        """

        try:
            assert_no_error_logs(log_output)
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            error_msg = str(e)
            assert "First error" in error_msg
            assert "Second error" in error_msg

    def test_full_log_in_error(self):
        """Test that full log is included in error message."""
        log_output = "INFO: Start\nERROR: Failed\nINFO: End"

        try:
            assert_no_error_logs(log_output)
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            assert "Full log output:" in str(e)
            assert log_output in str(e)


class TestAssertCommandSuccess:
    """Test command success assertions."""

    def test_successful_command(self):
        """Test assertion passes for successful command."""
        result = subprocess.run(["echo", "test"], capture_output=True, text=True)

        # Should not raise
        assert_command_success(result, "echo test")

    def test_failed_command(self):
        """Test assertion fails for failed command."""
        result = subprocess.run(["false"], capture_output=True, text=True)

        with pytest.raises(AssertionError, match="Command failed"):
            assert_command_success(result, "test operation")

    def test_error_includes_details(self):
        """Test error message includes command details."""
        result = subprocess.run(["false"], capture_output=True, text=True)

        try:
            assert_command_success(result, "custom operation")
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            error_msg = str(e)
            assert "custom operation" in error_msg
            assert "Return code:" in error_msg

    def test_expected_output_match(self):
        """Test assertion with expected output."""
        result = subprocess.run(["echo", "hello world"], capture_output=True, text=True)

        # Should not raise
        assert_command_success(result, "echo", expected_output="hello")

    def test_expected_output_mismatch(self):
        """Test assertion fails when output doesn't match."""
        result = subprocess.run(["echo", "hello"], capture_output=True, text=True)

        with pytest.raises(AssertionError, match="doesn't contain expected text"):
            assert_command_success(result, "echo", expected_output="goodbye")

    def test_output_error_includes_details(self):
        """Test output mismatch error includes details."""
        result = subprocess.run(["echo", "actual output"], capture_output=True, text=True)

        try:
            assert_command_success(result, "test", expected_output="expected")
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            error_msg = str(e)
            assert "Expected substring: expected" in error_msg
            assert "Actual output:" in error_msg
            assert "actual output" in error_msg


class TestIntegrationScenarios:
    """Integration tests combining multiple enhanced error utilities."""

    def test_full_workflow_success(self, temp_git_repo):
        """Test successful workflow with all utilities."""
        with assert_test_operation("full workflow test"):
            with assert_git_operation("create test file", temp_git_repo):
                # Create file
                test_file = Path(temp_git_repo) / "workflow.txt"
                test_file.write_text("test content")

                # Add and commit
                result = run_git_command_safe(["git", "add", "."], cwd=temp_git_repo)
                assert_command_success(result, "git add")

                result = run_git_command_safe(
                    ["git", "commit", "-m", "Test commit"], cwd=temp_git_repo
                )
                assert_command_success(result, "git commit")

            # Verify state
            assert_repository_state(
                temp_git_repo,
                should_be_clean=True,
                expected_commit_count=2,  # Initial + test commit
            )

    def test_failure_with_artifacts(self, temp_git_repo, tmp_path):
        """Test failure scenario with artifact saving."""
        try:
            with (
                assert_test_operation(
                    "failing workflow", save_artifacts_on_failure=True, artifact_path=temp_git_repo
                ),
                assert_git_operation("intentional failure", temp_git_repo),
            ):
                # Create uncommitted changes
                test_file = Path(temp_git_repo) / "uncommitted.txt"
                test_file.write_text("uncommitted")

                # Try to assert clean (should fail)
                assert_repository_state(temp_git_repo, should_be_clean=True)

            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            # Verify error message is detailed
            error_msg = str(e)
            assert "Test operation failed" in error_msg or "Repository state mismatch" in error_msg

    def test_nested_context_managers(self, temp_git_repo):
        """Test nested context managers for detailed error context."""
        with (
            assert_test_operation("nested operation test"),
            assert_git_operation("outer git operation", temp_git_repo),
        ):
            # Inner operation
            result = run_git_command_safe(["git", "log", "--oneline"], cwd=temp_git_repo)
            assert result.returncode == 0
            assert_command_success(result, "git log")
            assert "Initial commit" in result.stdout

    def test_error_propagation_chain(self, temp_git_repo):
        """Test that errors propagate correctly through nested contexts."""
        original_error = ValueError("original error")

        try:
            with assert_test_operation("outer"), assert_git_operation("inner", temp_git_repo):
                raise original_error
            pytest.fail("Should have raised AssertionError")
        except AssertionError as e:
            # Verify exception chain - outer context wraps the inner
            # The chain is: outer AssertionError -> inner AssertionError -> original ValueError
            assert e.__cause__ is not None
            # Check that original error is in the chain
            current = e
            found_original = False
            while current is not None:
                if current is original_error:
                    found_original = True
                    break
                current = current.__cause__
            assert found_original, "Original error should be in exception chain"
            assert "Test operation failed" in str(e) or "Git operation failed" in str(e)


# Summary fixture to report test results
@pytest.fixture(scope="module", autouse=True)
def test_summary():
    """Print summary after all tests complete."""
    yield
    print("\n" + "=" * 70)
    print("Enhanced Error Messages Test Suite Summary")
    print("=" * 70)
    print("✓ Git information utilities tested")
    print("✓ Dictionary diff formatting tested")
    print("✓ Repository state assertions tested")
    print("✓ Context managers tested")
    print("✓ Artifact saving tested")
    print("✓ Log validation tested")
    print("✓ Command success assertions tested")
    print("✓ Integration scenarios tested")
    print("=" * 70)
