# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Git operation optimization module for the Repository Reporting System.

This module provides utilities for optimizing git operations including shallow
clones, reference repositories, batch operations, and efficient git configuration.

Classes:
    GitOptimizer: Main coordinator for git optimizations
    ReferenceRepository: Manage reference repositories for faster clones
    ShallowCloneStrategy: Strategy for determining shallow clone parameters
    GitOperationCache: Cache git operation results
    GitConfig: Git configuration optimization

Example:
    >>> from src.performance import GitOptimizer
    >>>
    >>> optimizer = GitOptimizer(use_shallow=True, use_references=True)
    >>> repo_path = optimizer.clone_optimized(
    ...     url="https://github.com/user/repo.git",
    ...     destination="./repos/repo"
    ... )
"""

import os
import subprocess
import shutil
import hashlib
import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import tempfile


class CloneStrategy(Enum):
    """Strategy for cloning repositories."""
    FULL = "full"
    SHALLOW = "shallow"
    REFERENCE = "reference"
    SHALLOW_REFERENCE = "shallow_reference"


class GitOperationType(Enum):
    """Types of git operations."""
    CLONE = "clone"
    FETCH = "fetch"
    LOG = "log"
    DIFF = "diff"
    STATUS = "status"


@dataclass
class GitConfig:
    """
    Configuration for git optimization.

    Attributes:
        shallow_clone: Enable shallow clones
        shallow_depth: Depth for shallow clones
        use_reference_repos: Use reference repositories
        reference_dir: Directory for reference repositories
        parallel_fetch: Number of parallel fetch operations
        compression: Git compression level (0-9)
        http_post_buffer: HTTP post buffer size in bytes
    """
    shallow_clone: bool = True
    shallow_depth: int = 1
    use_reference_repos: bool = True
    reference_dir: str = "./.git-references"
    parallel_fetch: int = 4
    compression: int = 9
    http_post_buffer: int = 524288000  # 500MB

    def validate(self):
        """Validate configuration."""
        if self.shallow_depth < 1:
            raise ValueError(f"shallow_depth must be >= 1, got {self.shallow_depth}")
        if self.parallel_fetch < 1:
            raise ValueError(f"parallel_fetch must be >= 1, got {self.parallel_fetch}")
        if not 0 <= self.compression <= 9:
            raise ValueError(f"compression must be 0-9, got {self.compression}")
        if self.http_post_buffer < 1024:
            raise ValueError(f"http_post_buffer must be >= 1024, got {self.http_post_buffer}")


@dataclass
class GitOperationResult:
    """Result from a git operation."""
    operation: GitOperationType
    success: bool
    duration: float
    output: str = ""
    error: str = ""
    strategy: Optional[CloneStrategy] = None

    @property
    def is_success(self) -> bool:
        """Check if operation was successful."""
        return self.success

    @property
    def is_failure(self) -> bool:
        """Check if operation failed."""
        return not self.success


class ShallowCloneStrategy:
    """
    Strategy for determining when and how to use shallow clones.

    Shallow clones are faster and use less disk space but have limitations
    for certain operations (e.g., full history analysis).
    """

    def __init__(self, default_depth: int = 1):
        """
        Initialize shallow clone strategy.

        Args:
            default_depth: Default depth for shallow clones
        """
        self.default_depth = default_depth

    def should_use_shallow(
        self,
        analysis_type: str = "basic",
        needs_history: bool = False,
        needs_branches: bool = False
    ) -> bool:
        """
        Determine if shallow clone is appropriate.

        Args:
            analysis_type: Type of analysis to perform
            needs_history: Whether full history is needed
            needs_branches: Whether branch information is needed

        Returns:
            True if shallow clone is safe to use
        """
        # Don't use shallow if full history needed
        if needs_history:
            return False

        # Don't use shallow if branch analysis needed
        if needs_branches:
            return False

        # Safe for basic analysis (file structure, current state)
        if analysis_type in ("basic", "structure", "files", "current"):
            return True

        # Default to shallow for most cases
        return True

    def get_depth(self, analysis_type: str = "basic") -> int:
        """
        Get appropriate depth for shallow clone.

        Args:
            analysis_type: Type of analysis to perform

        Returns:
            Depth for shallow clone
        """
        # Deeper clones for certain analysis types
        depth_map = {
            "basic": 1,
            "structure": 1,
            "recent": 10,
            "commits": 50,
            "history": 100,
        }

        return depth_map.get(analysis_type, self.default_depth)


class ReferenceRepository:
    """
    Manage reference repositories for faster clones.

    Reference repositories store git objects locally and are referenced
    during clone operations to avoid re-downloading common objects.
    """

    def __init__(self, reference_dir: str = "./.git-references"):
        """
        Initialize reference repository manager.

        Args:
            reference_dir: Directory to store reference repositories
        """
        self.reference_dir = Path(reference_dir)
        self.reference_dir.mkdir(parents=True, exist_ok=True)

    def _get_reference_path(self, repo_url: str) -> Path:
        """
        Get path for reference repository.

        Args:
            repo_url: Repository URL

        Returns:
            Path to reference repository
        """
        # Create hash of URL for directory name
        url_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:16]
        # Extract repo name from URL
        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')
        return self.reference_dir / f"{repo_name}_{url_hash}"

    def has_reference(self, repo_url: str) -> bool:
        """
        Check if reference repository exists.

        Args:
            repo_url: Repository URL

        Returns:
            True if reference exists
        """
        ref_path = self._get_reference_path(repo_url)
        return ref_path.exists() and (ref_path / ".git").exists()

    def create_reference(self, repo_url: str, update: bool = False) -> Optional[Path]:
        """
        Create or update reference repository.

        Args:
            repo_url: Repository URL
            update: Update existing reference if True

        Returns:
            Path to reference repository, or None on failure
        """
        ref_path = self._get_reference_path(repo_url)

        try:
            if ref_path.exists() and not update:
                return ref_path

            if ref_path.exists() and update:
                # Update existing reference
                subprocess.run(
                    ["git", "fetch", "--all"],
                    cwd=ref_path,
                    check=True,
                    capture_output=True,
                    timeout=300
                )
                return ref_path

            # Create new reference (bare clone)
            ref_path.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", "--bare", repo_url, str(ref_path)],
                check=True,
                capture_output=True,
                timeout=600
            )

            return ref_path

        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception) as e:
            # Reference creation failed, not critical
            return None

    def get_reference(self, repo_url: str, auto_create: bool = True) -> Optional[Path]:
        """
        Get reference repository path.

        Args:
            repo_url: Repository URL
            auto_create: Create reference if it doesn't exist

        Returns:
            Path to reference repository, or None if not available
        """
        if self.has_reference(repo_url):
            return self._get_reference_path(repo_url)

        if auto_create:
            return self.create_reference(repo_url)

        return None

    def cleanup_old_references(self, max_age_days: int = 30) -> int:
        """
        Clean up old reference repositories.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of references cleaned up
        """
        if not self.reference_dir.exists():
            return 0

        count = 0
        now = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60

        for ref_path in self.reference_dir.iterdir():
            if not ref_path.is_dir():
                continue

            # Check age
            mtime = ref_path.stat().st_mtime
            age = now - mtime

            if age > max_age_seconds:
                try:
                    shutil.rmtree(ref_path)
                    count += 1
                except Exception:
                    pass

        return count


class GitOptimizer:
    """
    Main coordinator for git operation optimizations.

    This class provides optimized git operations including shallow clones,
    reference repositories, and efficient git configuration.

    Example:
        >>> optimizer = GitOptimizer(use_shallow=True, use_references=True)
        >>> result = optimizer.clone_optimized(
        ...     url="https://github.com/user/repo.git",
        ...     destination="./repos/repo"
        ... )
        >>> if result.is_success:
        ...     print(f"Cloned in {result.duration:.2f}s")
    """

    def __init__(
        self,
        config: Optional[GitConfig] = None,
        profiler: Optional[Any] = None
    ):
        """
        Initialize git optimizer.

        Args:
            config: Git configuration (uses defaults if None)
            profiler: Optional performance profiler
        """
        self.config = config or GitConfig()
        self.config.validate()
        self.profiler = profiler

        # Initialize sub-components
        self.shallow_strategy = ShallowCloneStrategy(
            default_depth=self.config.shallow_depth
        )

        self.reference_repo = None
        if self.config.use_reference_repos:
            self.reference_repo = ReferenceRepository(
                reference_dir=self.config.reference_dir
            )

    def _apply_git_config(self, repo_path: str):
        """
        Apply optimized git configuration to repository.

        Args:
            repo_path: Path to repository
        """
        configs = [
            ("fetch.parallel", str(self.config.parallel_fetch)),
            ("core.compression", str(self.config.compression)),
            ("http.postBuffer", str(self.config.http_post_buffer)),
        ]

        for key, value in configs:
            try:
                subprocess.run(
                    ["git", "config", key, value],
                    cwd=repo_path,
                    check=False,
                    capture_output=True,
                    timeout=5
                )
            except Exception:
                # Non-critical, continue
                pass

    def _run_git_command(
        self,
        args: List[str],
        operation: GitOperationType,
        cwd: Optional[str] = None,
        timeout: int = 300
    ) -> GitOperationResult:
        """
        Run a git command with timing and error handling.

        Args:
            args: Git command arguments
            operation: Type of git operation
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            GitOperationResult
        """
        start_time = time.perf_counter()

        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                timeout=timeout,
                text=True
            )

            duration = time.perf_counter() - start_time

            return GitOperationResult(
                operation=operation,
                success=result.returncode == 0,
                duration=duration,
                output=result.stdout,
                error=result.stderr if result.returncode != 0 else ""
            )

        except subprocess.TimeoutExpired:
            duration = time.perf_counter() - start_time
            return GitOperationResult(
                operation=operation,
                success=False,
                duration=duration,
                error=f"Command timed out after {timeout}s"
            )

        except Exception as e:
            duration = time.perf_counter() - start_time
            return GitOperationResult(
                operation=operation,
                success=False,
                duration=duration,
                error=str(e)
            )

    def clone_optimized(
        self,
        url: str,
        destination: str,
        strategy: Optional[CloneStrategy] = None,
        branch: Optional[str] = None
    ) -> GitOperationResult:
        """
        Clone repository with optimizations.

        Args:
            url: Repository URL
            destination: Destination path
            strategy: Clone strategy (auto-detect if None)
            branch: Specific branch to clone

        Returns:
            GitOperationResult
        """
        # Auto-detect strategy
        if strategy is None:
            if self.config.use_reference_repos and self.config.shallow_clone:
                strategy = CloneStrategy.SHALLOW_REFERENCE
            elif self.config.use_reference_repos:
                strategy = CloneStrategy.REFERENCE
            elif self.config.shallow_clone:
                strategy = CloneStrategy.SHALLOW
            else:
                strategy = CloneStrategy.FULL

        # Build git clone command
        cmd = ["git", "clone"]

        # Add shallow clone options
        if strategy in (CloneStrategy.SHALLOW, CloneStrategy.SHALLOW_REFERENCE):
            cmd.extend(["--depth", str(self.config.shallow_depth)])
            cmd.append("--single-branch")

        # Add reference repository
        if strategy in (CloneStrategy.REFERENCE, CloneStrategy.SHALLOW_REFERENCE):
            if self.reference_repo:
                ref_path = self.reference_repo.get_reference(url, auto_create=True)
                if ref_path:
                    cmd.extend(["--reference", str(ref_path)])

        # Add branch if specified
        if branch:
            cmd.extend(["--branch", branch])

        # Add URL and destination
        cmd.extend([url, destination])

        # Track with profiler if available
        if self.profiler:
            with self.profiler.track_operation(
                f"git_clone_{Path(destination).name}",
                category="git",
                metadata={"strategy": strategy.value, "url": url}
            ):
                result = self._run_git_command(cmd, GitOperationType.CLONE, timeout=600)
        else:
            result = self._run_git_command(cmd, GitOperationType.CLONE, timeout=600)

        result.strategy = strategy

        # Apply git config if successful
        if result.is_success and os.path.exists(destination):
            self._apply_git_config(destination)

        return result

    def fetch_optimized(
        self,
        repo_path: str,
        remote: str = "origin",
        prune: bool = True
    ) -> GitOperationResult:
        """
        Fetch with optimizations.

        Args:
            repo_path: Path to repository
            remote: Remote name
            prune: Prune deleted branches

        Returns:
            GitOperationResult
        """
        cmd = ["git", "fetch", remote]

        if prune:
            cmd.append("--prune")

        if self.profiler:
            with self.profiler.track_operation(
                f"git_fetch_{Path(repo_path).name}",
                category="git"
            ):
                return self._run_git_command(cmd, GitOperationType.FETCH, cwd=repo_path)
        else:
            return self._run_git_command(cmd, GitOperationType.FETCH, cwd=repo_path)

    def get_log(
        self,
        repo_path: str,
        max_count: Optional[int] = None,
        since: Optional[str] = None,
        format: str = "oneline"
    ) -> GitOperationResult:
        """
        Get git log with optimizations.

        Args:
            repo_path: Path to repository
            max_count: Maximum number of commits
            since: Get commits since date/time
            format: Log format

        Returns:
            GitOperationResult
        """
        cmd = ["git", "log", f"--format={format}"]

        if max_count:
            cmd.extend(["-n", str(max_count)])

        if since:
            cmd.extend(["--since", since])

        return self._run_git_command(cmd, GitOperationType.LOG, cwd=repo_path, timeout=60)

    def batch_clone(
        self,
        repositories: List[Tuple[str, str]],
        parallel_processor: Optional[Any] = None
    ) -> List[GitOperationResult]:
        """
        Clone multiple repositories, optionally in parallel.

        Args:
            repositories: List of (url, destination) tuples
            parallel_processor: Optional ParallelRepositoryProcessor

        Returns:
            List of GitOperationResults
        """
        if parallel_processor:
            # Use parallel processing
            def clone_func(repo_info):
                url, dest = repo_info
                return self.clone_optimized(url, dest)

            aggregated = parallel_processor.process_repositories(
                repositories=repositories,
                processor_func=clone_func
            )

            # Extract GitOperationResults from aggregated results
            results = []
            for item in aggregated.successful:
                results.append(item.result)
            for item in aggregated.failed:
                # Create error result
                url, dest = repositories[len(results)]
                results.append(GitOperationResult(
                    operation=GitOperationType.CLONE,
                    success=False,
                    duration=item.duration,
                    error=item.error or "Unknown error"
                ))

            return results
        else:
            # Sequential cloning
            results = []
            for url, destination in repositories:
                result = self.clone_optimized(url, destination)
                results.append(result)

            return results

    def get_statistics(self, results: List[GitOperationResult]) -> Dict[str, Any]:
        """
        Get statistics from git operation results.

        Args:
            results: List of git operation results

        Returns:
            Dictionary with statistics
        """
        if not results:
            return {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0
            }

        successful = [r for r in results if r.is_success]
        failed = [r for r in results if r.is_failure]

        total_duration = sum(r.duration for r in results)
        avg_duration = total_duration / len(results)

        # Group by strategy
        strategy_counts: dict[str, int] = {}
        for result in results:
            if result.strategy:
                key = result.strategy.value
                strategy_counts[key] = strategy_counts.get(key, 0) + 1

        return {
            "total": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(results) * 100,
            "total_duration": total_duration,
            "avg_duration": avg_duration,
            "min_duration": min(r.duration for r in results),
            "max_duration": max(r.duration for r in results),
            "strategies": strategy_counts
        }


# Utility functions

def optimize_git_config_global():
    """
    Apply optimized git configuration globally.

    This sets system-wide git config for better performance.
    """
    configs = {
        "fetch.parallel": "4",
        "core.compression": "9",
        "http.postBuffer": "524288000",
        "core.preloadindex": "true",
        "core.fscache": "true",
        "gc.auto": "256",
    }

    for key, value in configs.items():
        try:
            subprocess.run(
                ["git", "config", "--global", key, value],
                check=False,
                capture_output=True,
                timeout=5
            )
        except Exception:
            pass


def estimate_clone_time(repo_size_mb: float, strategy: CloneStrategy) -> float:
    """
    Estimate clone time based on repository size and strategy.

    Args:
        repo_size_mb: Repository size in megabytes
        strategy: Clone strategy

    Returns:
        Estimated time in seconds
    """
    # Base rate: MB per second (conservative estimate)
    base_rate = 5.0

    # Strategy multipliers
    multipliers = {
        CloneStrategy.FULL: 1.0,
        CloneStrategy.SHALLOW: 0.3,
        CloneStrategy.REFERENCE: 0.5,
        CloneStrategy.SHALLOW_REFERENCE: 0.2,
    }

    multiplier = multipliers.get(strategy, 1.0)

    return (repo_size_mb / base_rate) * multiplier
