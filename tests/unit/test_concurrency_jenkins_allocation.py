# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for JenkinsAllocationContext - thread-safe Jenkins job allocation.

This module tests:
- Thread-safe job allocation and deduplication
- Cache management for repository jobs
- Allocation state tracking
- Concurrent access patterns
- Orphaned job tracking
- State reset functionality
"""

import threading
import time

from concurrency.jenkins_allocation import JenkinsAllocationContext


class TestJenkinsAllocationContextBasics:
    """Tests for basic JenkinsAllocationContext functionality."""

    def test_initialization(self):
        """Test context initializes with empty state."""
        context = JenkinsAllocationContext()

        assert len(context.allocated_jobs) == 0
        assert len(context.job_cache) == 0
        assert len(context.all_jobs) == 0
        assert len(context.orphaned_jobs) == 0

    def test_initial_summary(self):
        """Test allocation summary on fresh context."""
        context = JenkinsAllocationContext()
        summary = context.get_allocation_summary()

        assert summary["total_jobs"] == 0
        assert summary["allocated_count"] == 0
        assert summary["cached_repos"] == 0
        assert summary["orphaned_count"] == 0

    def test_has_lock_attribute(self):
        """Test that context has internal lock."""
        context = JenkinsAllocationContext()
        assert hasattr(context, "_lock")
        # Lock type varies by Python version, just check it's a lock-like object
        assert hasattr(context._lock, "acquire")
        assert hasattr(context._lock, "release")


class TestJobAllocation:
    """Tests for job allocation functionality."""

    def test_allocate_single_job(self):
        """Test allocating a single job to a repository."""
        context = JenkinsAllocationContext()
        jobs = [{"name": "job1", "url": "http://jenkins/job/job1"}]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 1
        assert allocated[0]["name"] == "job1"
        assert context.is_job_allocated("job1")

    def test_allocate_multiple_jobs(self):
        """Test allocating multiple jobs to a repository."""
        context = JenkinsAllocationContext()
        jobs = [
            {"name": "job1", "url": "http://jenkins/job/job1"},
            {"name": "job2", "url": "http://jenkins/job/job2"},
            {"name": "job3", "url": "http://jenkins/job/job3"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 3
        assert all(context.is_job_allocated(f"job{i}") for i in range(1, 4))

    def test_allocate_empty_list(self):
        """Test allocating empty job list."""
        context = JenkinsAllocationContext()
        allocated = context.allocate_jobs("repo1", [])

        assert len(allocated) == 0
        assert len(context.allocated_jobs) == 0

    def test_allocate_jobs_without_names(self):
        """Test allocating jobs without 'name' field."""
        context = JenkinsAllocationContext()
        jobs = [
            {"url": "http://jenkins/job/job1"},  # Missing name
            {"name": "job2", "url": "http://jenkins/job/job2"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 1
        assert allocated[0]["name"] == "job2"

    def test_allocate_jobs_with_none_names(self):
        """Test allocating jobs with None as name."""
        context = JenkinsAllocationContext()
        jobs = [
            {"name": None, "url": "http://jenkins/job/job1"},
            {"name": "job2", "url": "http://jenkins/job/job2"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 1
        assert allocated[0]["name"] == "job2"

    def test_allocate_jobs_with_empty_string_names(self):
        """Test allocating jobs with empty string as name."""
        context = JenkinsAllocationContext()
        jobs = [
            {"name": "", "url": "http://jenkins/job/job1"},
            {"name": "job2", "url": "http://jenkins/job/job2"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 1
        assert allocated[0]["name"] == "job2"


class TestJobDeduplication:
    """Tests for job deduplication across repositories."""

    def test_duplicate_allocation_prevented(self):
        """Test that same job cannot be allocated twice."""
        context = JenkinsAllocationContext()
        jobs = [{"name": "job1", "url": "http://jenkins/job/job1"}]

        # First allocation
        allocated1 = context.allocate_jobs("repo1", jobs)
        assert len(allocated1) == 1

        # Second allocation attempt
        allocated2 = context.allocate_jobs("repo2", jobs)
        assert len(allocated2) == 0

    def test_duplicate_prevention_across_multiple_repos(self):
        """Test deduplication across multiple repositories."""
        context = JenkinsAllocationContext()

        jobs1 = [
            {"name": "job1", "url": "http://jenkins/job/job1"},
            {"name": "job2", "url": "http://jenkins/job/job2"},
        ]
        jobs2 = [
            {"name": "job2", "url": "http://jenkins/job/job2"},  # Duplicate
            {"name": "job3", "url": "http://jenkins/job/job3"},
        ]

        allocated1 = context.allocate_jobs("repo1", jobs1)
        allocated2 = context.allocate_jobs("repo2", jobs2)

        assert len(allocated1) == 2
        assert len(allocated2) == 1  # Only job3, job2 was filtered
        assert allocated2[0]["name"] == "job3"

    def test_partial_overlap(self):
        """Test allocation with partial job overlap."""
        context = JenkinsAllocationContext()

        jobs1 = [{"name": "job1"}, {"name": "job2"}, {"name": "job3"}]
        jobs2 = [{"name": "job2"}, {"name": "job3"}, {"name": "job4"}]

        allocated1 = context.allocate_jobs("repo1", jobs1)
        allocated2 = context.allocate_jobs("repo2", jobs2)

        assert len(allocated1) == 3
        assert len(allocated2) == 1
        assert allocated2[0]["name"] == "job4"

    def test_is_job_allocated_check(self):
        """Test checking if specific jobs are allocated."""
        context = JenkinsAllocationContext()
        jobs = [{"name": "job1"}, {"name": "job2"}]

        context.allocate_jobs("repo1", jobs)

        assert context.is_job_allocated("job1")
        assert context.is_job_allocated("job2")
        assert not context.is_job_allocated("job3")

    def test_get_allocated_job_names(self):
        """Test getting list of all allocated job names."""
        context = JenkinsAllocationContext()

        jobs1 = [{"name": "job1"}, {"name": "job2"}]
        jobs2 = [{"name": "job3"}]

        context.allocate_jobs("repo1", jobs1)
        context.allocate_jobs("repo2", jobs2)

        allocated_names = context.get_allocated_job_names()

        assert len(allocated_names) == 3
        assert set(allocated_names) == {"job1", "job2", "job3"}


class TestJobCaching:
    """Tests for job caching functionality."""

    def test_cache_single_repo(self):
        """Test caching jobs for a single repository."""
        context = JenkinsAllocationContext()
        jobs = [{"name": "job1"}, {"name": "job2"}]

        context.cache_jobs("repo1", jobs)
        cached = context.get_cached_jobs("repo1")

        assert cached is not None
        assert len(cached) == 2
        assert cached == jobs

    def test_cache_multiple_repos(self):
        """Test caching jobs for multiple repositories."""
        context = JenkinsAllocationContext()

        jobs1 = [{"name": "job1"}, {"name": "job2"}]
        jobs2 = [{"name": "job3"}]

        context.cache_jobs("repo1", jobs1)
        context.cache_jobs("repo2", jobs2)

        assert context.get_cached_jobs("repo1") == jobs1
        assert context.get_cached_jobs("repo2") == jobs2

    def test_get_uncached_repo(self):
        """Test getting cache for non-existent repository."""
        context = JenkinsAllocationContext()
        cached = context.get_cached_jobs("nonexistent")

        assert cached is None

    def test_cache_overwrite(self):
        """Test overwriting cached jobs for a repository."""
        context = JenkinsAllocationContext()

        jobs1 = [{"name": "job1"}]
        jobs2 = [{"name": "job2"}, {"name": "job3"}]

        context.cache_jobs("repo1", jobs1)
        context.cache_jobs("repo1", jobs2)

        cached = context.get_cached_jobs("repo1")
        assert len(cached) == 2
        assert cached == jobs2

    def test_cache_empty_list(self):
        """Test caching empty job list."""
        context = JenkinsAllocationContext()
        context.cache_jobs("repo1", [])

        cached = context.get_cached_jobs("repo1")
        assert cached is not None
        assert len(cached) == 0

    def test_cache_summary_count(self):
        """Test that summary reflects cached repository count."""
        context = JenkinsAllocationContext()

        context.cache_jobs("repo1", [{"name": "job1"}])
        context.cache_jobs("repo2", [{"name": "job2"}])
        context.cache_jobs("repo3", [{"name": "job3"}])

        summary = context.get_allocation_summary()
        assert summary["cached_repos"] == 3


class TestAllJobsManagement:
    """Tests for all jobs storage and retrieval."""

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

    def test_all_jobs_summary_count(self):
        """Test that summary reflects total job count."""
        context = JenkinsAllocationContext()
        all_jobs = {
            "jobs": [
                {"name": "job1"},
                {"name": "job2"},
                {"name": "job3"},
                {"name": "job4"},
                {"name": "job5"},
            ]
        }

        context.set_all_jobs(all_jobs)
        summary = context.get_allocation_summary()

        assert summary["total_jobs"] == 5

    def test_all_jobs_empty_dict(self):
        """Test setting all jobs as empty dict."""
        context = JenkinsAllocationContext()
        context.set_all_jobs({})

        summary = context.get_allocation_summary()
        assert summary["total_jobs"] == 0

    def test_all_jobs_no_jobs_key(self):
        """Test all jobs dict without 'jobs' key."""
        context = JenkinsAllocationContext()
        all_jobs = {"other": "data"}

        context.set_all_jobs(all_jobs)
        summary = context.get_allocation_summary()

        assert summary["total_jobs"] == 0

    def test_all_jobs_overwrite(self):
        """Test overwriting all jobs data."""
        context = JenkinsAllocationContext()

        jobs1 = {"jobs": [{"name": "job1"}]}
        jobs2 = {"jobs": [{"name": "job2"}, {"name": "job3"}]}

        context.set_all_jobs(jobs1)
        context.set_all_jobs(jobs2)

        retrieved = context.get_all_jobs()
        assert len(retrieved["jobs"]) == 2


class TestOrphanedJobs:
    """Tests for orphaned jobs management."""

    def test_set_and_get_orphaned_jobs(self):
        """Test setting and getting orphaned jobs."""
        context = JenkinsAllocationContext()
        orphaned = {
            "orphaned": [
                {"name": "orphan1"},
                {"name": "orphan2"},
            ]
        }

        context.set_orphaned_jobs(orphaned)
        retrieved = context.get_orphaned_jobs()

        assert retrieved == orphaned

    def test_orphaned_jobs_summary_count(self):
        """Test that summary reflects orphaned job count."""
        context = JenkinsAllocationContext()
        orphaned = {"jobs": [{"name": "orphan1"}, {"name": "orphan2"}]}

        context.set_orphaned_jobs(orphaned)
        summary = context.get_allocation_summary()

        assert summary["orphaned_count"] == 1  # Counts dict items, not nested list

    def test_orphaned_jobs_empty(self):
        """Test setting empty orphaned jobs."""
        context = JenkinsAllocationContext()
        context.set_orphaned_jobs({})

        retrieved = context.get_orphaned_jobs()
        assert len(retrieved) == 0

    def test_orphaned_jobs_overwrite(self):
        """Test overwriting orphaned jobs."""
        context = JenkinsAllocationContext()

        orphaned1 = {"data": "first"}
        orphaned2 = {"data": "second", "more": "info"}

        context.set_orphaned_jobs(orphaned1)
        context.set_orphaned_jobs(orphaned2)

        retrieved = context.get_orphaned_jobs()
        assert retrieved == orphaned2


class TestStateReset:
    """Tests for state reset functionality."""

    def test_reset_clears_all_state(self):
        """Test that reset clears all state."""
        context = JenkinsAllocationContext()

        # Populate all state
        context.allocate_jobs("repo1", [{"name": "job1"}])
        context.cache_jobs("repo2", [{"name": "job2"}])
        context.set_all_jobs({"jobs": [{"name": "job3"}]})
        context.set_orphaned_jobs({"orphaned": [{"name": "job4"}]})

        # Reset
        context.reset()

        # Verify all state is cleared
        assert len(context.allocated_jobs) == 0
        assert len(context.job_cache) == 0
        assert len(context.all_jobs) == 0
        assert len(context.orphaned_jobs) == 0

    def test_reset_summary(self):
        """Test that summary shows zeros after reset."""
        context = JenkinsAllocationContext()

        # Populate state
        context.allocate_jobs("repo1", [{"name": "job1"}])
        context.cache_jobs("repo1", [{"name": "job1"}])
        context.set_all_jobs({"jobs": [{"name": "job1"}]})
        context.set_orphaned_jobs({"orphaned": "data"})

        context.reset()
        summary = context.get_allocation_summary()

        assert summary["total_jobs"] == 0
        assert summary["allocated_count"] == 0
        assert summary["cached_repos"] == 0
        assert summary["orphaned_count"] == 0

    def test_reset_allows_reuse(self):
        """Test that context can be reused after reset."""
        context = JenkinsAllocationContext()

        # First use
        context.allocate_jobs("repo1", [{"name": "job1"}])
        assert context.is_job_allocated("job1")

        # Reset
        context.reset()

        # Second use - can allocate same job again
        allocated = context.allocate_jobs("repo2", [{"name": "job1"}])
        assert len(allocated) == 1
        assert context.is_job_allocated("job1")

    def test_multiple_resets(self):
        """Test multiple consecutive resets."""
        context = JenkinsAllocationContext()

        context.allocate_jobs("repo1", [{"name": "job1"}])
        context.reset()
        context.reset()
        context.reset()

        summary = context.get_allocation_summary()
        assert all(v == 0 for v in summary.values())


class TestConcurrentAccess:
    """Tests for thread-safe concurrent access."""

    def test_concurrent_allocation(self):
        """Test concurrent job allocation from multiple threads."""
        context = JenkinsAllocationContext()
        results = {}

        def allocate_jobs(repo_name: str, job_names: list[str]):
            jobs = [{"name": name} for name in job_names]
            allocated = context.allocate_jobs(repo_name, jobs)
            results[repo_name] = len(allocated)

        # Create overlapping job sets
        jobs1 = ["job1", "job2", "job3", "job4", "job5"]
        jobs2 = ["job3", "job4", "job5", "job6", "job7"]
        jobs3 = ["job5", "job6", "job7", "job8", "job9"]

        threads = [
            threading.Thread(target=allocate_jobs, args=("repo1", jobs1)),
            threading.Thread(target=allocate_jobs, args=("repo2", jobs2)),
            threading.Thread(target=allocate_jobs, args=("repo3", jobs3)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Total allocated should be 9 unique jobs
        total_allocated = sum(results.values())
        assert total_allocated == 9
        assert len(context.allocated_jobs) == 9

    def test_concurrent_cache_access(self):
        """Test concurrent cache operations."""
        context = JenkinsAllocationContext()
        barrier = threading.Barrier(10)

        def cache_and_retrieve(repo_id: int):
            barrier.wait()  # Synchronize start
            repo_name = f"repo{repo_id}"
            jobs = [{"name": f"job{repo_id}"}]

            context.cache_jobs(repo_name, jobs)
            cached = context.get_cached_jobs(repo_name)
            assert cached is not None

        threads = [threading.Thread(target=cache_and_retrieve, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        summary = context.get_allocation_summary()
        assert summary["cached_repos"] == 10

    def test_concurrent_all_jobs_access(self):
        """Test concurrent access to all jobs."""
        context = JenkinsAllocationContext()
        barrier = threading.Barrier(5)
        results = []

        def set_and_get_all_jobs(thread_id: int):
            barrier.wait()  # Synchronize start
            all_jobs = {"jobs": [{"name": f"job{thread_id}"}]}
            context.set_all_jobs(all_jobs)
            retrieved = context.get_all_jobs()
            results.append(retrieved)

        threads = [threading.Thread(target=set_and_get_all_jobs, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads completed without error
        assert len(results) == 5

    def test_concurrent_summary_generation(self):
        """Test concurrent summary generation while state changes."""
        context = JenkinsAllocationContext()
        summaries = []

        def allocate_and_summarize(repo_id: int):
            for i in range(10):
                jobs = [{"name": f"job{repo_id}_{i}"}]
                context.allocate_jobs(f"repo{repo_id}", jobs)
                summary = context.get_allocation_summary()
                summaries.append(summary)

        threads = [threading.Thread(target=allocate_and_summarize, args=(i,)) for i in range(5)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All summaries generated without error
        assert len(summaries) == 50

        # Final state should have 50 allocated jobs
        final_summary = context.get_allocation_summary()
        assert final_summary["allocated_count"] == 50

    def test_concurrent_is_job_allocated_checks(self):
        """Test concurrent job allocation checking."""
        context = JenkinsAllocationContext()

        # Pre-allocate some jobs
        context.allocate_jobs("repo1", [{"name": f"job{i}"} for i in range(100)])

        results = []

        def check_allocations():
            local_results = []
            for i in range(100):
                allocated = context.is_job_allocated(f"job{i}")
                local_results.append(allocated)
            results.extend(local_results)

        threads = [threading.Thread(target=check_allocations) for _ in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All checks should return True (1000 total checks)
        assert len(results) == 1000
        assert all(results)

    def test_concurrent_reset(self):
        """Test that concurrent reset doesn't cause issues."""
        context = JenkinsAllocationContext()

        def allocate_and_reset(thread_id: int):
            for _ in range(5):
                jobs = [{"name": f"job{thread_id}"}]
                context.allocate_jobs(f"repo{thread_id}", jobs)
                time.sleep(0.001)
                if thread_id % 2 == 0:
                    context.reset()

        threads = [threading.Thread(target=allocate_and_reset, args=(i,)) for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No crashes - state may vary but should be consistent
        summary = context.get_allocation_summary()
        assert isinstance(summary, dict)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_large_job_list(self):
        """Test allocation with very large job list."""
        context = JenkinsAllocationContext()
        jobs = [{"name": f"job{i}"} for i in range(10000)]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 10000
        assert len(context.allocated_jobs) == 10000

    def test_unicode_job_names(self):
        """Test jobs with unicode names."""
        context = JenkinsAllocationContext()
        jobs = [
            {"name": "job_日本語"},
            {"name": "job_русский"},
            {"name": "job_عربي"},
            {"name": "job_中文"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 4
        assert context.is_job_allocated("job_日本語")

    def test_special_characters_in_job_names(self):
        """Test jobs with special characters."""
        context = JenkinsAllocationContext()
        jobs = [
            {"name": "job-with-dashes"},
            {"name": "job_with_underscores"},
            {"name": "job.with.dots"},
            {"name": "job/with/slashes"},
            {"name": "job:with:colons"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 5

    def test_duplicate_jobs_in_same_request(self):
        """Test allocation request with duplicate job names."""
        context = JenkinsAllocationContext()
        jobs = [
            {"name": "job1"},
            {"name": "job1"},  # Duplicate
            {"name": "job2"},
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        # First job1 gets allocated, second is filtered out
        assert len(allocated) == 2
        assert sum(1 for j in allocated if j["name"] == "job1") == 1

    def test_job_with_complex_metadata(self):
        """Test jobs with complex nested metadata."""
        context = JenkinsAllocationContext()
        jobs = [
            {
                "name": "job1",
                "url": "http://jenkins/job/job1",
                "builds": [
                    {"number": 1, "result": "SUCCESS"},
                    {"number": 2, "result": "FAILURE"},
                ],
                "parameters": {
                    "param1": "value1",
                    "param2": ["list", "of", "values"],
                },
            }
        ]

        allocated = context.allocate_jobs("repo1", jobs)

        assert len(allocated) == 1
        assert allocated[0]["name"] == "job1"
        assert "builds" in allocated[0]
        assert "parameters" in allocated[0]

    def test_empty_repo_name(self):
        """Test allocation with empty repository name."""
        context = JenkinsAllocationContext()
        jobs = [{"name": "job1"}]

        allocated = context.allocate_jobs("", jobs)

        assert len(allocated) == 1
        assert context.is_job_allocated("job1")

    def test_none_repo_name(self):
        """Test caching with None as repository name."""
        context = JenkinsAllocationContext()
        jobs = [{"name": "job1"}]

        context.cache_jobs(None, jobs)
        cached = context.get_cached_jobs(None)

        assert cached == jobs

    def test_get_allocated_job_names_returns_copy(self):
        """Test that get_allocated_job_names returns a new list."""
        context = JenkinsAllocationContext()
        context.allocate_jobs("repo1", [{"name": "job1"}])

        names1 = context.get_allocated_job_names()
        names2 = context.get_allocated_job_names()

        # Should be equal but not the same object
        assert names1 == names2
        assert names1 is not names2

        # Modifying returned list shouldn't affect internal state
        names1.append("job2")
        assert "job2" not in context.get_allocated_job_names()


class TestIntegrationScenarios:
    """Tests for realistic integration scenarios."""

    def test_typical_allocation_workflow(self):
        """Test typical workflow: allocate, cache, check, summarize."""
        context = JenkinsAllocationContext()

        # Set all jobs from Jenkins
        all_jobs = {
            "jobs": [
                {"name": "job1"},
                {"name": "job2"},
                {"name": "job3"},
                {"name": "job4"},
            ]
        }
        context.set_all_jobs(all_jobs)

        # Allocate jobs to repositories
        allocated1 = context.allocate_jobs("repo1", [{"name": "job1"}, {"name": "job2"}])
        context.cache_jobs("repo1", allocated1)

        allocated2 = context.allocate_jobs("repo2", [{"name": "job2"}, {"name": "job3"}])
        context.cache_jobs("repo2", allocated2)

        # Check summary
        summary = context.get_allocation_summary()
        assert summary["total_jobs"] == 4
        assert summary["allocated_count"] == 3  # job1, job2, job3
        assert summary["cached_repos"] == 2

    def test_reallocation_after_reset(self):
        """Test reallocating jobs after reset."""
        context = JenkinsAllocationContext()

        # First allocation
        jobs = [{"name": "job1"}, {"name": "job2"}]
        allocated1 = context.allocate_jobs("repo1", jobs)
        assert len(allocated1) == 2

        # Reset and reallocate to different repo
        context.reset()
        allocated2 = context.allocate_jobs("repo2", jobs)
        assert len(allocated2) == 2

    def test_orphaned_jobs_workflow(self):
        """Test workflow with orphaned jobs."""
        context = JenkinsAllocationContext()

        # Set all jobs
        all_jobs = {"jobs": [{"name": f"job{i}"} for i in range(10)]}
        context.set_all_jobs(all_jobs)

        # Allocate some jobs
        context.allocate_jobs("repo1", [{"name": "job0"}, {"name": "job1"}])
        context.allocate_jobs("repo2", [{"name": "job2"}, {"name": "job3"}])

        # Set orphaned jobs (the rest)
        orphaned = {"jobs": [{"name": f"job{i}"} for i in range(4, 10)]}
        context.set_orphaned_jobs(orphaned)

        summary = context.get_allocation_summary()
        assert summary["allocated_count"] == 4
        assert summary["orphaned_count"] == 1  # One dict entry

    def test_multiple_repositories_no_conflicts(self):
        """Test multiple repositories with non-overlapping jobs."""
        context = JenkinsAllocationContext()

        repo_jobs = {
            "repo1": [{"name": "job1"}, {"name": "job2"}],
            "repo2": [{"name": "job3"}, {"name": "job4"}],
            "repo3": [{"name": "job5"}, {"name": "job6"}],
        }

        for repo_name, jobs in repo_jobs.items():
            allocated = context.allocate_jobs(repo_name, jobs)
            assert len(allocated) == 2
            context.cache_jobs(repo_name, allocated)

        # Verify all jobs allocated
        assert len(context.allocated_jobs) == 6

        # Verify all caches
        for repo_name in repo_jobs:
            cached = context.get_cached_jobs(repo_name)
            assert cached is not None
            assert len(cached) == 2
