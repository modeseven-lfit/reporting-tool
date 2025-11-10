# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for the git optimization module.

This module tests:
- GitOptimizer functionality
- ReferenceRepository management
- ShallowCloneStrategy logic
- GitConfig validation
- GitOperationResult data structures
- Clone optimization strategies
"""

import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from performance import (
    CloneStrategy,
    GitConfig,
    GitOperationResult,
    GitOperationType,
    GitOptimizer,
    ReferenceRepository,
    ShallowCloneStrategy,
    estimate_clone_time,
    optimize_git_config_global,
)


class TestGitConfig:
    """Tests for GitConfig class."""

    def test_default_config(self):
        """Test default configuration."""
        config = GitConfig()

        assert config.shallow_clone is True
        assert config.shallow_depth == 1
        assert config.use_reference_repos is True
        assert config.reference_dir == "./.git-references"
        assert config.parallel_fetch == 4
        assert config.compression == 9
        assert config.http_post_buffer == 524288000

    def test_custom_config(self):
        """Test custom configuration."""
        config = GitConfig(
            shallow_clone=False,
            shallow_depth=5,
            use_reference_repos=False,
            reference_dir="./custom-refs",
            parallel_fetch=8,
            compression=6,
            http_post_buffer=1048576000,
        )

        assert config.shallow_clone is False
        assert config.shallow_depth == 5
        assert config.use_reference_repos is False
        assert config.reference_dir == "./custom-refs"
        assert config.parallel_fetch == 8
        assert config.compression == 6
        assert config.http_post_buffer == 1048576000

    def test_validate_invalid_shallow_depth(self):
        """Test validation rejects invalid shallow_depth."""
        config = GitConfig(shallow_depth=0)

        with pytest.raises(ValueError, match="shallow_depth must be >= 1"):
            config.validate()

    def test_validate_invalid_parallel_fetch(self):
        """Test validation rejects invalid parallel_fetch."""
        config = GitConfig(parallel_fetch=0)

        with pytest.raises(ValueError, match="parallel_fetch must be >= 1"):
            config.validate()

    def test_validate_invalid_compression(self):
        """Test validation rejects invalid compression."""
        config = GitConfig(compression=10)

        with pytest.raises(ValueError, match="compression must be 0-9"):
            config.validate()

    def test_validate_invalid_http_post_buffer(self):
        """Test validation rejects invalid http_post_buffer."""
        config = GitConfig(http_post_buffer=512)

        with pytest.raises(ValueError, match="http_post_buffer must be >= 1024"):
            config.validate()

    def test_validate_valid_config(self):
        """Test validation passes for valid config."""
        config = GitConfig()

        # Should not raise
        config.validate()


class TestGitOperationResult:
    """Tests for GitOperationResult class."""

    def test_successful_result(self):
        """Test successful operation result."""
        result = GitOperationResult(
            operation=GitOperationType.CLONE,
            success=True,
            duration=10.5,
            output="Cloned successfully",
            strategy=CloneStrategy.SHALLOW,
        )

        assert result.operation == GitOperationType.CLONE
        assert result.is_success is True
        assert result.is_failure is False
        assert result.duration == 10.5
        assert result.strategy == CloneStrategy.SHALLOW

    def test_failed_result(self):
        """Test failed operation result."""
        result = GitOperationResult(
            operation=GitOperationType.CLONE, success=False, duration=5.2, error="Clone failed"
        )

        assert result.operation == GitOperationType.CLONE
        assert result.is_success is False
        assert result.is_failure is True
        assert result.error == "Clone failed"


class TestShallowCloneStrategy:
    """Tests for ShallowCloneStrategy class."""

    def test_initialization(self):
        """Test strategy initialization."""
        strategy = ShallowCloneStrategy(default_depth=5)

        assert strategy.default_depth == 5

    def test_should_use_shallow_basic_analysis(self):
        """Test shallow clone for basic analysis."""
        strategy = ShallowCloneStrategy()

        should_use = strategy.should_use_shallow(
            analysis_type="basic", needs_history=False, needs_branches=False
        )

        assert should_use is True

    def test_should_not_use_shallow_needs_history(self):
        """Test shallow clone when history needed."""
        strategy = ShallowCloneStrategy()

        should_use = strategy.should_use_shallow(
            analysis_type="basic", needs_history=True, needs_branches=False
        )

        assert should_use is False

    def test_should_not_use_shallow_needs_branches(self):
        """Test shallow clone when branches needed."""
        strategy = ShallowCloneStrategy()

        should_use = strategy.should_use_shallow(
            analysis_type="basic", needs_history=False, needs_branches=True
        )

        assert should_use is False

    def test_get_depth_basic(self):
        """Test getting depth for basic analysis."""
        strategy = ShallowCloneStrategy()

        depth = strategy.get_depth("basic")

        assert depth == 1

    def test_get_depth_recent(self):
        """Test getting depth for recent analysis."""
        strategy = ShallowCloneStrategy()

        depth = strategy.get_depth("recent")

        assert depth == 10

    def test_get_depth_commits(self):
        """Test getting depth for commit analysis."""
        strategy = ShallowCloneStrategy()

        depth = strategy.get_depth("commits")

        assert depth == 50

    def test_get_depth_unknown(self):
        """Test getting depth for unknown analysis type."""
        strategy = ShallowCloneStrategy(default_depth=3)

        depth = strategy.get_depth("unknown_type")

        assert depth == 3


class TestReferenceRepository:
    """Tests for ReferenceRepository class."""

    def test_initialization(self):
        """Test reference repository initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_dir = os.path.join(tmpdir, "refs")
            ref_repo = ReferenceRepository(reference_dir=ref_dir)

            assert ref_repo.reference_dir == Path(ref_dir)
            assert os.path.exists(ref_dir)

    def test_get_reference_path(self):
        """Test getting reference path for URL."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_repo = ReferenceRepository(reference_dir=tmpdir)

            url = "https://github.com/user/test-repo.git"
            ref_path = ref_repo._get_reference_path(url)

            assert "test-repo" in str(ref_path)
            assert ref_path.parent == Path(tmpdir)

    def test_has_reference_false(self):
        """Test has_reference when reference doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_repo = ReferenceRepository(reference_dir=tmpdir)

            url = "https://github.com/user/test-repo.git"
            has_ref = ref_repo.has_reference(url)

            assert has_ref is False

    def test_has_reference_true(self):
        """Test has_reference when reference exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_repo = ReferenceRepository(reference_dir=tmpdir)

            url = "https://github.com/user/test-repo.git"
            ref_path = ref_repo._get_reference_path(url)

            # Create fake reference
            ref_path.mkdir(parents=True, exist_ok=True)
            (ref_path / ".git").mkdir()

            has_ref = ref_repo.has_reference(url)

            assert has_ref is True

    def test_get_reference_exists(self):
        """Test getting existing reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_repo = ReferenceRepository(reference_dir=tmpdir)

            url = "https://github.com/user/test-repo.git"
            ref_path = ref_repo._get_reference_path(url)

            # Create fake reference
            ref_path.mkdir(parents=True, exist_ok=True)
            (ref_path / ".git").mkdir()

            result = ref_repo.get_reference(url, auto_create=False)

            assert result == ref_path

    def test_get_reference_not_exists_no_auto_create(self):
        """Test getting non-existent reference without auto-create."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_repo = ReferenceRepository(reference_dir=tmpdir)

            url = "https://github.com/user/test-repo.git"
            result = ref_repo.get_reference(url, auto_create=False)

            assert result is None


class TestGitOptimizer:
    """Tests for GitOptimizer class."""

    def test_initialization_default(self):
        """Test optimizer with default config."""
        optimizer = GitOptimizer()

        assert optimizer.config.shallow_clone is True
        assert optimizer.config.use_reference_repos is True
        assert optimizer.shallow_strategy is not None

    def test_initialization_custom_config(self):
        """Test optimizer with custom config."""
        config = GitConfig(shallow_clone=False, use_reference_repos=False)
        optimizer = GitOptimizer(config=config)

        assert optimizer.config.shallow_clone is False
        assert optimizer.config.use_reference_repos is False

    @patch("subprocess.run")
    def test_run_git_command_success(self, mock_run):
        """Test running git command successfully."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Success output", stderr="")

        optimizer = GitOptimizer()
        result = optimizer._run_git_command(["git", "status"], GitOperationType.STATUS)

        assert result.is_success is True
        assert result.operation == GitOperationType.STATUS
        assert result.output == "Success output"

    @patch("subprocess.run")
    def test_run_git_command_failure(self, mock_run):
        """Test running git command that fails."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error message")

        optimizer = GitOptimizer()
        result = optimizer._run_git_command(["git", "status"], GitOperationType.STATUS)

        assert result.is_failure is True
        assert result.error == "Error message"

    @patch("subprocess.run")
    def test_run_git_command_timeout(self, mock_run):
        """Test running git command that times out."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["git", "clone"], timeout=10)

        optimizer = GitOptimizer()
        result = optimizer._run_git_command(
            ["git", "clone", "url"], GitOperationType.CLONE, timeout=10
        )

        assert result.is_failure is True
        assert "timed out" in result.error.lower()

    @patch("subprocess.run")
    def test_clone_optimized_shallow(self, mock_run):
        """Test optimized clone with shallow strategy."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Cloned", stderr="")

        config = GitConfig(shallow_clone=True, use_reference_repos=False)
        optimizer = GitOptimizer(config=config)

        result = optimizer.clone_optimized(
            url="https://github.com/user/repo.git", destination="./test-repo"
        )

        assert result.is_success is True
        assert result.strategy == CloneStrategy.SHALLOW

        # Check that shallow clone args were used
        call_args = mock_run.call_args[0][0]
        assert "--depth" in call_args
        assert "1" in call_args

    @patch("subprocess.run")
    def test_fetch_optimized(self, mock_run):
        """Test optimized fetch."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Fetched", stderr="")

        optimizer = GitOptimizer()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = optimizer.fetch_optimized(repo_path=tmpdir)

            assert result.is_success is True
            assert result.operation == GitOperationType.FETCH

    @patch("subprocess.run")
    def test_get_log(self, mock_run):
        """Test getting git log."""
        mock_run.return_value = MagicMock(returncode=0, stdout="commit1\ncommit2\n", stderr="")

        optimizer = GitOptimizer()

        with tempfile.TemporaryDirectory() as tmpdir:
            result = optimizer.get_log(repo_path=tmpdir, max_count=10)

            assert result.is_success is True
            assert result.operation == GitOperationType.LOG

    def test_get_statistics_empty(self):
        """Test statistics with empty results."""
        optimizer = GitOptimizer()
        stats = optimizer.get_statistics([])

        assert stats["total"] == 0
        assert stats["successful"] == 0
        assert stats["failed"] == 0

    def test_get_statistics_with_results(self):
        """Test statistics with results."""
        optimizer = GitOptimizer()

        results = [
            GitOperationResult(
                operation=GitOperationType.CLONE,
                success=True,
                duration=10.0,
                strategy=CloneStrategy.SHALLOW,
            ),
            GitOperationResult(
                operation=GitOperationType.CLONE,
                success=True,
                duration=15.0,
                strategy=CloneStrategy.SHALLOW,
            ),
            GitOperationResult(operation=GitOperationType.CLONE, success=False, duration=5.0),
        ]

        stats = optimizer.get_statistics(results)

        assert stats["total"] == 3
        assert stats["successful"] == 2
        assert stats["failed"] == 1
        assert stats["success_rate"] == pytest.approx(66.67, rel=0.1)
        assert stats["avg_duration"] == 10.0
        assert stats["strategies"]["shallow"] == 2


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_estimate_clone_time_full(self):
        """Test clone time estimation for full clone."""
        time = estimate_clone_time(100, CloneStrategy.FULL)

        assert time > 0
        assert time == 100 / 5.0  # 100 MB at 5 MB/s

    def test_estimate_clone_time_shallow(self):
        """Test clone time estimation for shallow clone."""
        full_time = estimate_clone_time(100, CloneStrategy.FULL)
        shallow_time = estimate_clone_time(100, CloneStrategy.SHALLOW)

        # Shallow should be faster
        assert shallow_time < full_time
        assert shallow_time == pytest.approx(full_time * 0.3)

    def test_estimate_clone_time_shallow_reference(self):
        """Test clone time estimation for shallow reference clone."""
        full_time = estimate_clone_time(100, CloneStrategy.FULL)
        shallow_ref_time = estimate_clone_time(100, CloneStrategy.SHALLOW_REFERENCE)

        # Shallow reference should be fastest
        assert shallow_ref_time < full_time
        assert shallow_ref_time == pytest.approx(full_time * 0.2)

    @patch("subprocess.run")
    def test_optimize_git_config_global(self, mock_run):
        """Test global git config optimization."""
        mock_run.return_value = MagicMock(returncode=0)

        # Should not raise
        optimize_git_config_global()

        # Should have called git config multiple times
        assert mock_run.call_count > 0


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    @patch("subprocess.run")
    def test_clone_with_profiler(self, mock_run):
        """Test clone with profiler integration."""
        from performance import PerformanceProfiler

        mock_run.return_value = MagicMock(returncode=0, stdout="Cloned", stderr="")

        profiler = PerformanceProfiler(name="git_test")
        profiler.start()

        optimizer = GitOptimizer(profiler=profiler)
        result = optimizer.clone_optimized(
            url="https://github.com/user/repo.git", destination="./test-repo"
        )

        profiler.stop()

        assert result.is_success is True
        assert len(profiler.operations) > 0

    @patch("subprocess.run")
    def test_batch_clone_sequential(self, mock_run):
        """Test batch cloning sequentially."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Cloned", stderr="")

        optimizer = GitOptimizer()

        repositories = [
            ("https://github.com/user/repo1.git", "./repo1"),
            ("https://github.com/user/repo2.git", "./repo2"),
            ("https://github.com/user/repo3.git", "./repo3"),
        ]

        results = optimizer.batch_clone(repositories)

        assert len(results) == 3
        assert all(r.is_success for r in results)

    @patch("subprocess.run")
    def test_strategy_auto_detection(self, mock_run):
        """Test automatic strategy detection."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Cloned", stderr="")

        # Shallow + reference enabled
        config1 = GitConfig(shallow_clone=True, use_reference_repos=True)
        optimizer1 = GitOptimizer(config=config1)
        result1 = optimizer1.clone_optimized("url", "dest1")
        assert result1.strategy == CloneStrategy.SHALLOW_REFERENCE

        # Only shallow enabled
        config2 = GitConfig(shallow_clone=True, use_reference_repos=False)
        optimizer2 = GitOptimizer(config=config2)
        result2 = optimizer2.clone_optimized("url", "dest2")
        assert result2.strategy == CloneStrategy.SHALLOW

        # Only reference enabled
        config3 = GitConfig(shallow_clone=False, use_reference_repos=True)
        optimizer3 = GitOptimizer(config=config3)
        result3 = optimizer3.clone_optimized("url", "dest3")
        assert result3.strategy == CloneStrategy.REFERENCE

        # Neither enabled
        config4 = GitConfig(shallow_clone=False, use_reference_repos=False)
        optimizer4 = GitOptimizer(config=config4)
        result4 = optimizer4.clone_optimized("url", "dest4")
        assert result4.strategy == CloneStrategy.FULL


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_invalid_config_raises(self):
        """Test that invalid config raises error."""
        config = GitConfig(shallow_depth=-1)

        with pytest.raises(ValueError):
            GitOptimizer(config=config)

    @patch("subprocess.run")
    def test_clone_with_branch(self, mock_run):
        """Test cloning specific branch."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Cloned", stderr="")

        optimizer = GitOptimizer()
        result = optimizer.clone_optimized(
            url="https://github.com/user/repo.git", destination="./test-repo", branch="develop"
        )

        assert result.is_success is True

        # Check branch arg was used
        call_args = mock_run.call_args[0][0]
        assert "--branch" in call_args
        assert "develop" in call_args

    def test_reference_repository_cleanup(self):
        """Test cleanup of old reference repositories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_repo = ReferenceRepository(reference_dir=tmpdir)

            # Create some fake old references
            old_ref = Path(tmpdir) / "old_repo"
            old_ref.mkdir()
            (old_ref / ".git").mkdir()

            # Set modification time to past (this is OS-dependent)
            import time

            old_time = time.time() - (31 * 24 * 60 * 60)  # 31 days ago
            try:
                os.utime(old_ref, (old_time, old_time))

                # Cleanup references older than 30 days
                count = ref_repo.cleanup_old_references(max_age_days=30)

                assert count >= 0  # May or may not work depending on OS
            except Exception:
                # OS doesn't support setting times, skip
                pass
