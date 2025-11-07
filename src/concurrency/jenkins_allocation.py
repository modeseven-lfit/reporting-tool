# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Jenkins job allocation context for thread-safe job tracking.

This module provides a thread-safe context for managing Jenkins job allocation
across concurrent repository analysis operations. It replaces the previous
global lock approach with instance-level isolation.

Thread Safety:
    All public methods are thread-safe and can be called from multiple threads
    concurrently. An internal lock protects all shared mutable state.

Example:
    >>> context = JenkinsAllocationContext()
    >>> jobs = context.get_cached_jobs("my-repo")
    >>> if jobs is None:
    >>>     jobs = fetch_jobs_from_api()
    >>>     allocated = context.allocate_jobs("my-repo", jobs)
    >>>     context.cache_jobs("my-repo", allocated)
"""

import threading
from typing import Any, Dict, List, Optional, Set


class JenkinsAllocationContext:
    """
    Thread-safe context for Jenkins job allocation within a single collection run.

    This class manages the allocation of Jenkins jobs to repositories, ensuring
    that each job is assigned to at most one repository (preventing duplicates).
    It also provides caching to avoid redundant API calls.

    Thread Safety:
        All public methods acquire an internal lock before accessing shared state.
        Multiple threads can safely call methods on the same instance.

    Attributes:
        allocated_jobs: Set of job names that have been allocated to repositories
        job_cache: Cached job data per repository name
        all_jobs: All jobs fetched from Jenkins (cached once)
        orphaned_jobs: Jobs that don't match any repository pattern
    """

    def __init__(self):
        """Initialize a new allocation context with empty state."""
        self._lock = threading.Lock()
        self.allocated_jobs: Set[str] = set()
        self.job_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.all_jobs: Dict[str, Any] = {}
        self.orphaned_jobs: Dict[str, Any] = {}

    def allocate_jobs(
        self,
        repo_name: str,
        jobs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Allocate jobs to a repository, filtering out already-allocated jobs.

        This method implements duplicate prevention: if a job has already been
        allocated to another repository, it will not be included in the result.

        Thread-safe: Uses internal lock for allocation state updates.

        Args:
            repo_name: Name of the repository requesting jobs
            jobs: List of job dictionaries (each must have a 'name' key)

        Returns:
            List of jobs allocated to this repository (subset of input jobs)

        Example:
            >>> jobs = [{"name": "job1", ...}, {"name": "job2", ...}]
            >>> allocated = context.allocate_jobs("repo1", jobs)
            >>> # allocated will exclude any jobs already given to other repos
        """
        with self._lock:
            allocated = []
            for job in jobs:
                job_name = job.get("name")
                if job_name and job_name not in self.allocated_jobs:
                    allocated.append(job)
                    self.allocated_jobs.add(job_name)
            return allocated

    def get_cached_jobs(self, repo_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached jobs for a repository.

        Thread-safe: Uses internal lock for cache read.

        Args:
            repo_name: Name of the repository

        Returns:
            Cached job list if available, None otherwise
        """
        with self._lock:
            return self.job_cache.get(repo_name)

    def cache_jobs(self, repo_name: str, jobs: List[Dict[str, Any]]) -> None:
        """
        Cache jobs for a repository.

        Thread-safe: Uses internal lock for cache write.

        Args:
            repo_name: Name of the repository
            jobs: List of jobs to cache
        """
        with self._lock:
            self.job_cache[repo_name] = jobs

    def set_all_jobs(self, all_jobs: Dict[str, Any]) -> None:
        """
        Set the complete list of all Jenkins jobs (typically fetched once).

        Thread-safe: Uses internal lock for write.

        Args:
            all_jobs: Dictionary containing all jobs from Jenkins API
        """
        with self._lock:
            self.all_jobs = all_jobs

    def get_all_jobs(self) -> Dict[str, Any]:
        """
        Get the complete list of all Jenkins jobs.

        Thread-safe: Uses internal lock for read. Returns a reference to
        the internal dict (caller should not modify).

        Returns:
            Dictionary containing all jobs from Jenkins API
        """
        with self._lock:
            return self.all_jobs

    def set_orphaned_jobs(self, orphaned: Dict[str, Any]) -> None:
        """
        Set orphaned jobs (jobs that don't match any repository).

        Thread-safe: Uses internal lock for write.

        Args:
            orphaned: Dictionary of orphaned job data
        """
        with self._lock:
            self.orphaned_jobs = orphaned

    def get_orphaned_jobs(self) -> Dict[str, Any]:
        """
        Get orphaned jobs.

        Thread-safe: Uses internal lock for read.

        Returns:
            Dictionary of orphaned job data
        """
        with self._lock:
            return self.orphaned_jobs

    def reset(self) -> None:
        """
        Reset all allocation state to initial (empty) values.

        Thread-safe: Uses internal lock for state reset.

        This is useful when starting a fresh collection run or when
        testing requires a clean state.
        """
        with self._lock:
            self.allocated_jobs.clear()
            self.job_cache.clear()
            self.all_jobs.clear()
            self.orphaned_jobs.clear()

    def get_allocation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current allocation state for auditing/debugging.

        Thread-safe: Uses internal lock for read. Returns a new dict
        (safe to modify).

        Returns:
            Dictionary with allocation statistics:
                - total_jobs: Total number of jobs in all_jobs
                - allocated_count: Number of jobs allocated to repositories
                - cached_repos: Number of repositories with cached jobs
                - orphaned_count: Number of orphaned jobs
        """
        with self._lock:
            total_jobs = len(self.all_jobs.get("jobs", []))
            return {
                "total_jobs": total_jobs,
                "allocated_count": len(self.allocated_jobs),
                "cached_repos": len(self.job_cache),
                "orphaned_count": len(self.orphaned_jobs),
            }

    def is_job_allocated(self, job_name: str) -> bool:
        """
        Check if a job has been allocated to any repository.

        Thread-safe: Uses internal lock for read.

        Args:
            job_name: Name of the job to check

        Returns:
            True if job is allocated, False otherwise
        """
        with self._lock:
            return job_name in self.allocated_jobs

    def get_allocated_job_names(self) -> List[str]:
        """
        Get a list of all allocated job names.

        Thread-safe: Uses internal lock for read. Returns a new list
        (safe to modify).

        Returns:
            List of job names that have been allocated
        """
        with self._lock:
            return list(self.allocated_jobs)
