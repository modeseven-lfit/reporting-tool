# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for JenkinsAllocationContext (Phase 7 - Concurrency).

This module tests the thread-safe Jenkins job allocation context,
including concurrent access scenarios and isolation between instances.
"""

import threading

from concurrency.jenkins_allocation import JenkinsAllocationContext


class TestJenkinsAllocationContextBasics:
    """Test basic functionality of JenkinsAllocationContext."""

    def test_initialization(self):
        """Test context initializes with empty state."""
        context = JenkinsAllocationContext()

        assert len(context.allocated_jobs) == 0
        assert len(context.job_cache) == 0
        assert len(context.all_jobs) == 0
        assert len(context.orphaned_jobs) == 0

    def test_allocate_jobs_single_repo(self):
        """Test allocating jobs to a single repository."""
        context = JenkinsAllocationContext()
        jobs = [
            {"name": "job1", "url": "http://example.com/job1"},
            {"name": "job2", "url": "http://example.com/job2"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 2
        assert allocated[0]["name"] == "job1"
        assert allocated[1]["name"] == "job2"
        assert "job1" in context.allocated_jobs
        assert "job2" in context.allocated_jobs

    def test_allocate_jobs_prevents_duplicates(self):
        """Test that job allocation prevents duplicates."""
        context = JenkinsAllocationContext()
        jobs1 = [
            {"name": "job1", "url": "http://example.com/job1"},
            {"name": "shared-job", "url": "http://example.com/shared"},
        ]
        jobs2 = [
            {"name": "shared-job", "url": "http://example.com/shared"},
            {"name": "job2", "url": "http://example.com/job2"},
        ]

        allocated1 = context.allocate_jobs("repo1", jobs1)
        allocated2 = context.allocate_jobs("repo2", jobs2)

        # repo1 gets both jobs
        assert len(allocated1) == 2
        assert allocated1[0]["name"] == "job1"
        assert allocated1[1]["name"] == "shared-job"

        # repo2 only gets job2 (shared-job already allocated)
        assert len(allocated2) == 1
        assert allocated2[0]["name"] == "job2"

    def test_cache_jobs(self):
        """Test caching jobs for a repository."""
        context = JenkinsAllocationContext()
        jobs = [{"name": "job1", "url": "http://example.com/job1"}]

        context.cache_jobs("repo1", jobs)

        cached = context.get_cached_jobs("repo1")
        assert cached is not None
        assert len(cached) == 1
        assert cached[0]["name"] == "job1"

    def test_get_cached_jobs_returns_none_when_not_cached(self):
        """Test that get_cached_jobs returns None for uncached repos."""
        context = JenkinsAllocationContext()

        cached = context.get_cached_jobs("nonexistent")

        assert cached is None

    def test_set_and_get_all_jobs(self):
        """Test setting and getting all jobs."""
        context = JenkinsAllocationContext()
        all_jobs = {
            "jobs": [
                {"name": "job1"},
                {"name": "job2"},
                {"name": "job3"},
            ]
        }

        context.set_all_jobs(all_jobs)

        retrieved = context.get_all_jobs()
        assert retrieved == all_jobs
        assert len(retrieved["jobs"]) == 3

    def test_set_and_get_orphaned_jobs(self):
        """Test setting and getting orphaned jobs."""
        context = JenkinsAllocationContext()
        orphaned = {
            "orphan1": {"project": "archived-project", "state": "ARCHIVED"},
            "orphan2": {"project": "deleted-project", "state": "DELETED"},
        }

        context.set_orphaned_jobs(orphaned)

        retrieved = context.get_orphaned_jobs()
        assert retrieved == orphaned
        assert len(retrieved) == 2

    def test_reset(self):
        """Test resetting all state."""
        context = JenkinsAllocationContext()

        # Populate state
        jobs = [{"name": "job1"}]
        context.allocate_jobs("repo1", jobs)
        context.cache_jobs("repo1", jobs)
        context.set_all_jobs({"jobs": jobs})
        context.set_orphaned_jobs({"orphan1": {"state": "ARCHIVED"}})

        # Verify state is populated
        assert len(context.allocated_jobs) > 0
        assert len(context.job_cache) > 0
        assert len(context.get_all_jobs()) > 0
        assert len(context.get_orphaned_jobs()) > 0

        # Reset
        context.reset()

        # Verify state is empty
        assert len(context.allocated_jobs) == 0
        assert len(context.job_cache) == 0
        assert len(context.get_all_jobs()) == 0
        assert len(context.get_orphaned_jobs()) == 0

    def test_get_allocation_summary(self):
        """Test getting allocation summary."""
        context = JenkinsAllocationContext()

        # Setup state
        all_jobs = {
            "jobs": [
                {"name": "job1"},
                {"name": "job2"},
                {"name": "job3"},
            ]
        }
        context.set_all_jobs(all_jobs)

        jobs = [{"name": "job1"}, {"name": "job2"}]
        context.allocate_jobs("repo1", jobs)
        context.cache_jobs("repo1", jobs)

        orphaned = {"orphan1": {"state": "ARCHIVED"}}
        context.set_orphaned_jobs(orphaned)

        summary = context.get_allocation_summary()

        assert summary["total_jobs"] == 3
        assert summary["allocated_count"] == 2
        assert summary["cached_repos"] == 1
        assert summary["orphaned_count"] == 1

    def test_is_job_allocated(self):
        """Test checking if a job is allocated."""
        context = JenkinsAllocationContext()

        jobs = [{"name": "job1"}]
        context.allocate_jobs("repo1", jobs)

        assert context.is_job_allocated("job1") is True
        assert context.is_job_allocated("job2") is False

    def test_get_allocated_job_names(self):
        """Test getting list of allocated job names."""
        context = JenkinsAllocationContext()

        jobs = [
            {"name": "job1"},
            {"name": "job2"},
            {"name": "job3"},
        ]
        context.allocate_jobs("repo1", jobs)

        names = context.get_allocated_job_names()

        assert len(names) == 3
        assert "job1" in names
        assert "job2" in names
        assert "job3" in names


class TestJenkinsAllocationContextConcurrency:
    """Test thread safety of JenkinsAllocationContext."""

    def test_concurrent_allocations(self):
        """Test concurrent job allocations from multiple threads."""
        context = JenkinsAllocationContext()

        # Create jobs for multiple repos
        jobs_per_repo = [
            [{"name": f"repo1-job{i}"} for i in range(10)],
            [{"name": f"repo2-job{i}"} for i in range(10)],
            [{"name": f"repo3-job{i}"} for i in range(10)],
            [{"name": f"repo4-job{i}"} for i in range(10)],
        ]

        results = [None] * 4

        def allocate_jobs(repo_index: int):
            repo_name = f"repo{repo_index + 1}"
            jobs = jobs_per_repo[repo_index]
            allocated = context.allocate_jobs(repo_name, jobs)
            results[repo_index] = allocated

        # Start threads
        threads = [threading.Thread(target=allocate_jobs, args=(i,)) for i in range(4)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify all jobs were allocated
        total_allocated = sum(len(r) for r in results)
        assert total_allocated == 40

        # Verify no duplicates in allocated_jobs set
        assert len(context.allocated_jobs) == 40

    def test_concurrent_cache_access(self):
        """Test concurrent cache reads and writes."""
        context = JenkinsAllocationContext()

        # Pre-populate cache
        for i in range(10):
            context.cache_jobs(f"repo{i}", [{"name": f"job{i}"}])

        read_results = [None] * 10

        def read_cache(index: int):
            repo_name = f"repo{index}"
            cached = context.get_cached_jobs(repo_name)
            read_results[index] = cached

        # Concurrent reads
        threads = [threading.Thread(target=read_cache, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify all reads succeeded
        assert all(r is not None for r in read_results)
        assert all(len(r) == 1 for r in read_results)

    def test_concurrent_summary_access(self):
        """Test concurrent access to allocation summary."""
        context = JenkinsAllocationContext()

        # Setup initial state
        all_jobs = {"jobs": [{"name": f"job{i}"} for i in range(100)]}
        context.set_all_jobs(all_jobs)

        summaries = [None] * 20

        def get_summary(index: int):
            summaries[index] = context.get_allocation_summary()

        # Concurrent summary reads
        threads = [threading.Thread(target=get_summary, args=(i,)) for i in range(20)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify all summaries are consistent
        assert all(s is not None for s in summaries)
        assert all(s["total_jobs"] == 100 for s in summaries)

    def test_stress_test_allocations(self):
        """Stress test with many concurrent allocations."""
        context = JenkinsAllocationContext()

        # 100 threads each allocating 10 jobs
        num_threads = 100
        jobs_per_thread = 10

        def allocate(thread_id: int):
            jobs = [{"name": f"thread{thread_id}-job{i}"} for i in range(jobs_per_thread)]
            context.allocate_jobs(f"repo{thread_id}", jobs)

        threads = [threading.Thread(target=allocate, args=(i,)) for i in range(num_threads)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify total allocations
        assert len(context.allocated_jobs) == num_threads * jobs_per_thread


class TestJenkinsAllocationContextIsolation:
    """Test isolation between multiple context instances."""

    def test_multiple_contexts_are_independent(self):
        """Test that multiple contexts maintain independent state."""
        context1 = JenkinsAllocationContext()
        context2 = JenkinsAllocationContext()

        jobs1 = [{"name": "job1"}]
        jobs2 = [{"name": "job1"}]  # Same job name

        # Allocate same job to different contexts
        allocated1 = context1.allocate_jobs("repo1", jobs1)
        allocated2 = context2.allocate_jobs("repo2", jobs2)

        # Both should succeed (no sharing)
        assert len(allocated1) == 1
        assert len(allocated2) == 1

        # Verify independence
        assert "job1" in context1.allocated_jobs
        assert "job1" in context2.allocated_jobs
        assert len(context1.allocated_jobs) == 1
        assert len(context2.allocated_jobs) == 1

    def test_reset_does_not_affect_other_contexts(self):
        """Test that resetting one context doesn't affect others."""
        context1 = JenkinsAllocationContext()
        context2 = JenkinsAllocationContext()

        jobs = [{"name": "job1"}]
        context1.allocate_jobs("repo1", jobs)
        context2.allocate_jobs("repo2", jobs)

        # Reset context1
        context1.reset()

        # Verify context1 is empty
        assert len(context1.allocated_jobs) == 0

        # Verify context2 is unchanged
        assert len(context2.allocated_jobs) == 1
        assert "job1" in context2.allocated_jobs


class TestJenkinsAllocationContextEdgeCases:
    """Test edge cases and error conditions."""

    def test_allocate_empty_jobs_list(self):
        """Test allocating an empty list of jobs."""
        context = JenkinsAllocationContext()

        allocated = context.allocate_jobs("repo1", [])

        assert len(allocated) == 0

    def test_allocate_jobs_with_missing_name(self):
        """Test allocating jobs where some lack a 'name' field."""
        context = JenkinsAllocationContext()
        jobs = [
            {"name": "job1"},
            {"url": "http://example.com/job2"},  # Missing name
            {"name": "job3"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        # Only jobs with names should be allocated
        assert len(allocated) == 2
        assert allocated[0]["name"] == "job1"
        assert allocated[1]["name"] == "job3"

    def test_allocate_jobs_with_none_name(self):
        """Test allocating jobs with None as name."""
        context = JenkinsAllocationContext()
        jobs = [
            {"name": "job1"},
            {"name": None},
            {"name": "job3"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        # Only jobs with non-None names should be allocated
        assert len(allocated) == 2

    def test_cache_overwrite(self):
        """Test that caching overwrites previous cache."""
        context = JenkinsAllocationContext()

        jobs1 = [{"name": "job1"}]
        jobs2 = [{"name": "job2"}]

        context.cache_jobs("repo1", jobs1)
        context.cache_jobs("repo1", jobs2)

        cached = context.get_cached_jobs("repo1")

        # Should have the second set
        assert len(cached) == 1
        assert cached[0]["name"] == "job2"

    def test_get_allocation_summary_with_empty_all_jobs(self):
        """Test allocation summary when all_jobs is empty."""
        context = JenkinsAllocationContext()

        summary = context.get_allocation_summary()

        assert summary["total_jobs"] == 0
        assert summary["allocated_count"] == 0
        assert summary["cached_repos"] == 0

    def test_get_orphaned_jobs_summary_with_missing_jobs_key(self):
        """Test orphaned jobs count - orphaned_jobs is a dict of job info."""
        context = JenkinsAllocationContext()

        # Set orphaned jobs (dict structure: {job_name: {info}})
        context.set_orphaned_jobs({"orphan1": {"state": "ARCHIVED"}})

        summary = context.get_allocation_summary()

        # Should count orphaned jobs correctly (length of dict)
        assert summary["orphaned_count"] == 1


class TestJenkinsAllocationContextIntegration:
    """Integration tests simulating real-world usage patterns."""

    def test_typical_workflow(self):
        """Test a typical workflow: initialize, allocate, cache, summarize."""
        context = JenkinsAllocationContext()

        # Step 1: Initialize with all jobs from Jenkins
        all_jobs = {
            "jobs": [
                {"name": "repo1-build"},
                {"name": "repo1-test"},
                {"name": "repo2-build"},
                {"name": "shared-infrastructure"},
            ]
        }
        context.set_all_jobs(all_jobs)

        # Step 2: Allocate jobs to repositories
        repo1_jobs = [{"name": "repo1-build"}, {"name": "repo1-test"}]
        allocated1 = context.allocate_jobs("repo1", repo1_jobs)
        context.cache_jobs("repo1", allocated1)

        repo2_jobs = [{"name": "repo2-build"}]
        allocated2 = context.allocate_jobs("repo2", repo2_jobs)
        context.cache_jobs("repo2", allocated2)

        # Step 3: Mark orphaned jobs
        orphaned = {"shared-infrastructure": {"state": "INFRASTRUCTURE"}}
        context.set_orphaned_jobs(orphaned)

        # Step 4: Get summary
        summary = context.get_allocation_summary()

        # Verify summary
        assert summary["total_jobs"] == 4
        assert summary["allocated_count"] == 3
        assert summary["cached_repos"] == 2
        assert summary["orphaned_count"] == 1

        # Verify cache retrieval
        assert context.get_cached_jobs("repo1") is not None
        assert context.get_cached_jobs("repo2") is not None
        assert context.get_cached_jobs("repo3") is None

    def test_concurrent_workflow_with_multiple_repos(self):
        """Test concurrent processing of multiple repositories."""
        context = JenkinsAllocationContext()

        # Initialize with all jobs
        all_jobs = {"jobs": [{"name": f"job{i}"} for i in range(100)]}
        context.set_all_jobs(all_jobs)

        # Simulate concurrent repository processing
        num_repos = 10

        def process_repo(repo_index: int):
            repo_name = f"repo{repo_index}"
            # Each repo gets 10 jobs
            jobs = [{"name": f"job{repo_index * 10 + i}"} for i in range(10)]
            allocated = context.allocate_jobs(repo_name, jobs)
            context.cache_jobs(repo_name, allocated)

        threads = [threading.Thread(target=process_repo, args=(i,)) for i in range(num_repos)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify results
        summary = context.get_allocation_summary()
        assert summary["total_jobs"] == 100
        assert summary["allocated_count"] == 100
        assert summary["cached_repos"] == 10
