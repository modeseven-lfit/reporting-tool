# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Repository manager for ci-management and global-jjb.

This module handles cloning, caching, and updating of git repositories needed
for JJB Attribution.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class JJBRepoManager:
    """
    Manage cloning and caching of ci-management repositories for JJB Attribution.

    This class handles:
    - Cloning repositories if they don't exist
    - Updating cached repositories if they're stale
    - Managing repository cache directory
    - Error handling for git operations
    """

    def __init__(self, cache_dir: Path = Path("/tmp"), update_interval: int = 86400):
        """
        Initialize repository manager.

        Args:
            cache_dir: Directory to cache cloned repositories
            update_interval: Seconds before repository is considered stale (default: 24h)
        """
        self.cache_dir = Path(cache_dir)
        self.update_interval = update_interval

        # Create cache directory if it doesn't exist
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache directory: {self.cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to create cache directory {self.cache_dir}: {e}")

    def ensure_repos(
        self, ci_management_url: str, branch: str = "master"
    ) -> Tuple[Path, Path]:
        """
        Ensure ci-management and global-jjb repositories are available.

        This method will:
        1. Clone repositories if they don't exist
        2. Update repositories if they're stale
        3. Return paths to both repositories

        Args:
            ci_management_url: Git URL for ci-management repository
            branch: Branch to checkout (default: master)

        Returns:
            Tuple of (ci_management_path, global_jjb_path)

        Raises:
            RuntimeError: If repositories cannot be cloned or accessed
        """
        logger.debug("Ensuring ci-management repositories are available...")

        # Ensure ci-management repository
        ci_mgmt_path = self._ensure_repo(
            self.cache_dir / "ci-management",
            ci_management_url,
            branch,
            "ci-management",
        )

        # Ensure global-jjb repository
        global_jjb_path = self._ensure_repo(
            self.cache_dir / "releng-global-jjb",
            "https://github.com/lfit/releng-global-jjb",
            "master",
            "global-jjb",
        )

        logger.debug(
            f"Repositories ready: ci-management={ci_mgmt_path}, global-jjb={global_jjb_path}"
        )

        return ci_mgmt_path, global_jjb_path

    def _ensure_repo(
        self, path: Path, url: str, branch: str, name: str
    ) -> Path:
        """
        Ensure a git repository exists and is up-to-date.

        Args:
            path: Local path for the repository
            url: Git URL to clone from
            branch: Branch to checkout
            name: Human-readable name for logging

        Returns:
            Path to the repository

        Raises:
            RuntimeError: If repository operations fail
        """
        if path.exists():
            logger.debug(f"{name} repository exists at {path}")

            # Check if repository needs updating
            if self._is_repo_stale(path):
                logger.info(f"{name} repository is stale, updating...")
                self._update_repo(path, name)
            else:
                logger.debug(f"{name} repository is up-to-date")
        else:
            logger.info(f"Cloning {name} repository from {url}...")
            self._clone_repo(path, url, branch, name)

        # Verify repository is valid
        if not self._is_valid_repo(path):
            raise RuntimeError(f"Invalid repository at {path}")

        return path

    def _is_repo_stale(self, path: Path) -> bool:
        """
        Check if a repository is stale and needs updating.

        Args:
            path: Path to the repository

        Returns:
            True if repository should be updated, False otherwise
        """
        try:
            # Get the last modification time of the .git directory
            git_dir = path / ".git"
            if not git_dir.exists():
                logger.warning(f"No .git directory found in {path}")
                return True

            mtime = git_dir.stat().st_mtime
            age = time.time() - mtime

            is_stale = age > self.update_interval
            if is_stale:
                logger.debug(
                    f"Repository {path.name} is {age / 3600:.1f} hours old "
                    f"(threshold: {self.update_interval / 3600:.1f} hours)"
                )

            return is_stale

        except Exception as e:
            logger.warning(f"Error checking repository age for {path}: {e}")
            return False  # Don't update if we can't check

    def _update_repo(self, path: Path, name: str) -> None:
        """
        Update an existing repository.

        Args:
            path: Path to the repository
            name: Human-readable name for logging
        """
        try:
            # Try to pull latest changes
            result = subprocess.run(
                ["git", "-C", str(path), "pull", "--ff-only"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if result.returncode == 0:
                logger.debug(f"Successfully updated {name} repository")
                logger.debug(f"Git pull output: {result.stdout.strip()}")
            else:
                logger.warning(
                    f"Failed to update {name} repository: {result.stderr.strip()}"
                )
                logger.warning("Continuing with existing cached version")

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout updating {name} repository")
            logger.warning("Continuing with existing cached version")
        except Exception as e:
            logger.warning(f"Error updating {name} repository: {e}")
            logger.warning("Continuing with existing cached version")

    def _clone_repo(
        self, path: Path, url: str, branch: str, name: str
    ) -> None:
        """
        Clone a git repository.

        Args:
            path: Local path for the repository
            url: Git URL to clone from
            branch: Branch to checkout
            name: Human-readable name for logging

        Raises:
            RuntimeError: If cloning fails
        """
        try:
            # Use shallow clone for faster operation
            cmd = [
                "git",
                "clone",
                "--depth",
                "1",
                "--branch",
                branch,
                url,
                str(path),
            ]

            logger.debug(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minutes timeout
                check=False,
            )

            if result.returncode == 0:
                logger.debug(f"Successfully cloned {name} repository")
            else:
                error_msg = f"Failed to clone {name} from {url}: {result.stderr.strip()}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)

        except subprocess.TimeoutExpired:
            error_msg = f"Timeout cloning {name} repository from {url}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"Error cloning {name} repository: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _is_valid_repo(self, path: Path) -> bool:
        """
        Check if a path contains a valid git repository.

        Args:
            path: Path to check

        Returns:
            True if valid repository, False otherwise
        """
        try:
            # Check if .git directory exists
            git_dir = path / ".git"
            if not git_dir.exists():
                logger.warning(f"No .git directory at {path}")
                return False

            # Check if we can run git commands
            result = subprocess.run(
                ["git", "-C", str(path), "status"],
                capture_output=True,
                timeout=10,
                check=False,
            )

            if result.returncode != 0:
                logger.warning(f"Git status failed at {path}")
                return False

            return True

        except Exception as e:
            logger.warning(f"Error validating repository at {path}: {e}")
            return False

    def clean_cache(self, older_than: Optional[int] = None) -> None:
        """
        Clean cached repositories.

        Args:
            older_than: Remove repositories older than this many seconds.
                       If None, removes all cached repositories.
        """
        if not self.cache_dir.exists():
            logger.debug("Cache directory doesn't exist, nothing to clean")
            return

        try:
            for repo_dir in self.cache_dir.iterdir():
                if not repo_dir.is_dir():
                    continue

                should_remove = False

                if older_than is None:
                    should_remove = True
                else:
                    try:
                        age = time.time() - repo_dir.stat().st_mtime
                        should_remove = age > older_than
                    except Exception:
                        continue

                if should_remove:
                    logger.debug(f"Removing cached repository: {repo_dir}")
                    try:
                        import shutil
                        shutil.rmtree(repo_dir)
                    except Exception as e:
                        logger.warning(f"Failed to remove {repo_dir}: {e}")

        except Exception as e:
            logger.warning(f"Error cleaning cache: {e}")

    def get_cache_info(self) -> dict:
        """
        Get information about cached repositories.

        Returns:
            Dictionary with cache statistics
        """
        info: dict[str, Any] = {
            "cache_dir": str(self.cache_dir),
            "exists": self.cache_dir.exists(),
            "repositories": [],
            "total_size_mb": 0,
        }

        if not self.cache_dir.exists():
            return info

        try:
            for repo_dir in self.cache_dir.iterdir():
                if not repo_dir.is_dir():
                    continue

                # Get repository size
                size = 0
                try:
                    for item in repo_dir.rglob("*"):
                        if item.is_file():
                            size += item.stat().st_size
                except Exception:
                    pass

                # Get age
                try:
                    age = time.time() - repo_dir.stat().st_mtime
                    age_hours = age / 3600
                except Exception:
                    age_hours = 0

                info["repositories"].append({
                    "name": repo_dir.name,
                    "path": str(repo_dir),
                    "size_mb": size / (1024 * 1024),
                    "age_hours": age_hours,
                })

                info["total_size_mb"] += size / (1024 * 1024)

        except Exception as e:
            logger.warning(f"Error getting cache info: {e}")

        return info
