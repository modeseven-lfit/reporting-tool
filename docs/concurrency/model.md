<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Concurrency Model

**Author:** Repository Reporting System Team
**Date:** 2025-01-16
**Version:** 1.0
**Phase:** 7 - Concurrency Strategy Refinement

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Thread Safety Design](#thread-safety-design)
4. [Concurrency Strategies](#concurrency-strategies)
5. [Configuration](#configuration)
6. [Best Practices](#best-practices)
7. [Performance Tuning](#performance-tuning)
8. [Migration Guide](#migration-guide)
9. [Troubleshooting](#troubleshooting)
10. [References](#references)

---

## Overview

The repository reporting system uses **thread-based parallelism** to analyze multiple repositories concurrently. This document describes the concurrency model, thread safety guarantees, and best practices for working with concurrent code.

### Key Principles

1. **Thread-Safe by Design**: All shared state is protected by locks or immutable
2. **Instance-Level Isolation**: Each reporter instance has independent state
3. **Configurable Parallelism**: Concurrency can be adjusted via configuration
4. **No Global State**: All mutable state is instance-scoped
5. **Deterministic Results**: Concurrent execution produces identical results to sequential

### Concurrency Model Summary

```text
Main Thread
  └─> RepositoryReporter.generate_all_reports()
      ├─> Create JenkinsAllocationContext (per-instance)
      ├─> Create GitDataCollector (with context)
      └─> _analyze_repositories_parallel()
          └─> ThreadPoolExecutor (max_workers=8 default)
              ├─> Thread 1: _analyze_single_repository(repo1)
              ├─> Thread 2: _analyze_single_repository(repo2)
              ├─> ...
              └─> Thread N: _analyze_single_repository(repoN)
```

**Thread Safety Guarantee**: Multiple threads can safely analyze different repositories concurrently without data races or corruption.

---

## Architecture

### Components

#### 1. RepositoryReporter (Orchestrator)

**Role**: Main entry point, coordinates all reporting activities

**Thread Safety**:

- Creates per-instance state (not shared across threads)
- Spawns worker threads via `ThreadPoolExecutor`
- Collects results in main thread only

**Key Methods**:

- `generate_all_reports()` - Main entry point (single-threaded)
- `_analyze_repositories_parallel()` - Spawns worker threads
- `_analyze_single_repository()` - Worker function (thread-safe)

```python
class RepositoryReporter:
    def __init__(self, config, logger):
        # Instance-level state (one per reporter)
        self.jenkins_allocation_context = JenkinsAllocationContext()
        self.git_collector = GitDataCollector(config, {}, logger, self.jenkins_allocation_context)
        # ... other components
```text

#### 2. JenkinsAllocationContext (Thread-Safe State)

**Role**: Manages Jenkins job allocation with duplicate prevention

**Thread Safety**:

- Internal lock protects all mutations
- All public methods are thread-safe
- Lock-free reads via snapshot pattern (where applicable)

**Key Features**:

- Prevents same job from being allocated to multiple repositories
- Caches job data to avoid redundant API calls
- Tracks orphaned jobs (matched to archived projects)
- Provides allocation summary for auditing

```python
class JenkinsAllocationContext:
    def __init__(self):
        self._lock = threading.Lock()  # Instance-level lock
        self.allocated_jobs: Set[str] = set()
        self.job_cache: Dict[str, List[Dict]] = {}
        # ...

    def allocate_jobs(self, repo_name, jobs):
        with self._lock:  # Thread-safe allocation
            # ... duplicate prevention logic
```

**Design Benefits**:

- ✅ Instance-level (no global state)
- ✅ Fine-grained locking (minimal contention)
- ✅ Testable in isolation
- ✅ Multiple contexts can coexist independently

#### 3. GitDataCollector (Worker)

**Role**: Analyzes individual repositories (git metrics, features, etc.)

**Thread Safety**:

- Each worker thread calls `collect_repo_git_metrics()` with different repo
- Uses `JenkinsAllocationContext` for thread-safe job allocation
- No shared mutable state between worker calls
- Read-only access to configuration (immutable after load)

**Concurrency Pattern**:

```python
def collect_repo_git_metrics(self, repo_path):
    # Thread-safe operations:
    # 1. Git subprocess (isolated per thread)
    git_output = subprocess.run(["git", "log", ...])

    # 2. Parse output (CPU-bound, no shared state)
    commits = self._parse_git_log_output(git_output)

    # 3. Allocate Jenkins jobs (thread-safe via context)
    jobs = self._get_jenkins_jobs_for_repo(repo_name)
    # Uses: self.jenkins_allocation_context.allocate_jobs()
```text

#### 4. APIStatistics (Shared Stats)

**Role**: Track API call statistics across all threads

**Thread Safety**:

- Internal lock protects all counter increments
- Snapshot pattern for reads (copy data, release lock, format)
- Thread-safe by design (see Phase 7 Day 1)

```python
class APIStatistics:
    def __init__(self):
        self._lock = threading.Lock()
        self.stats = {...}

    def record_success(self, api_type):
        with self._lock:
            self.stats[api_type]["success"] += 1
```

#### 5. Other Components (Read-Only or Thread-Local)

- **Configuration**: Read-only after initialization (thread-safe)
- **Logger**: Python's `logging` module is thread-safe
- **FeatureRegistry**: Stateless feature detection (thread-safe)
- **ReportRenderer**: Creates reports from data (no shared state)

---

## Thread Safety Design

### Shared State Inventory

| Component | Shared? | Protection | Notes |
|-----------|---------|------------|-------|
| `JenkinsAllocationContext` | ✅ Yes | Internal lock | Instance-level, not global |
| `APIStatistics` | ✅ Yes | Internal lock | Shared across all threads |
| Configuration | ✅ Yes | Immutable | Read-only after load |
| Logger | ✅ Yes | Python stdlib | Thread-safe by design |
| Git subprocess | ❌ No | Isolated | Each thread runs own subprocess |
| Parsed data | ❌ No | Thread-local | Created per worker, no sharing |
| Results list | ✅ Yes | Main thread only | Only main thread writes |

### Locking Strategy

#### Instance-Level Locks (Preferred)

Each component that needs synchronization has its own lock:

```python
class MyThreadSafeClass:
    def __init__(self):
        self._lock = threading.Lock()  # Instance-level
        self.shared_state = {}

    def thread_safe_method(self):
        with self._lock:
            # Modify shared_state safely
```text

**Benefits**:

- No contention between unrelated instances
- Easier to test (no global state)
- Better encapsulation
- Scalable (fine-grained locking)

#### Global Locks (Deprecated)

**Before Phase 7**: Global lock for Jenkins allocation

```python
# OLD (DEPRECATED):
_jenkins_allocation_lock = threading.Lock()  # Module-level global

def some_method():
    with _jenkins_allocation_lock:  # All instances share this lock!
        # ... contention between unrelated collectors
```

**Problems**:

- ❌ Contention between independent operations
- ❌ Hard to test (global state)
- ❌ Poor encapsulation
- ❌ Not scalable

**After Phase 7**: Instance-level context

```python
# NEW (CURRENT):
context = JenkinsAllocationContext()  # Per-instance

def some_method():
    context.allocate_jobs(...)  # Internal lock, no global state
```text

### Lock-Free Patterns

**Immutability**: Configuration is read-only after initialization

```python
self.config = config  # Never modified after __init__
```

**Thread-Local State**: Each worker creates its own data

```python
def _analyze_single_repository(self, repo_path):
    metrics = {}  # Local to this thread, no sharing
    commits = self._parse_git_log_output(output)  # Local data
    return metrics  # Returned to main thread safely
```text

**Snapshot Pattern**: Copy data before releasing lock

```python
def get_stats(self):
    with self._lock:
        snapshot = copy.deepcopy(self.stats)  # Copy under lock
    # Lock released, can process snapshot without holding lock
    return format_stats(snapshot)
```

---

## Concurrency Strategies

### Current Strategy: Thread Pool

**Implementation**: `ThreadPoolExecutor` (Python standard library)

**Use Case**: I/O-bound operations (git subprocess, API calls)

**Configuration**:

```json
{
  "performance": {
    "max_workers": 8
  }
}
```text

**Characteristics**:

- ✅ Good for I/O-bound workloads (waiting on git, network)
- ✅ Low overhead (threads share memory)
- ✅ Simple to use and debug
- ⚠️ Limited by GIL for CPU-bound tasks
- ⚠️ Not ideal for heavy computation

**When to Use**:

- Analyzing multiple repositories (I/O-bound)
- Making API calls (network I/O)
- Running git commands (subprocess I/O)
- Default choice for this project ✅

### Alternative: Process Pool (Future)

**Implementation**: `ProcessPoolExecutor` (not yet implemented)

**Use Case**: CPU-bound operations (heavy parsing, computation)

**Potential Configuration**:

```json
{
  "performance": {
    "strategy": "process",
    "max_workers": 4
  }
}
```

**Characteristics**:

- ✅ Bypasses GIL (true parallelism)
- ✅ Good for CPU-bound workloads
- ❌ Higher overhead (process spawning, IPC)
- ❌ More complex (serialization required)
- ❌ Higher memory usage

**When to Consider**:

- Git log parsing is CPU bottleneck (profile first!)
- Large repositories (millions of commits)
- Heavy data processing workloads
- Decision pending profiling results

### Sequential (Fallback)

**Configuration**:

```json
{
  "performance": {
    "max_workers": 1
  }
}
```text

**When to Use**:

- Debugging (easier to trace)
- Small workloads (overhead not worth it)
- Testing (deterministic order)
- Resource-constrained environments

---

## Configuration

### Performance Settings

```json
{
  "performance": {
    "max_workers": 8,          // Number of parallel workers (1 = sequential)
    "cache": true,             // Enable caching (recommended)
    "timeout": 30.0            // API timeout in seconds
  }
}
```

### Recommended Settings

**Small Projects (<10 repos)**:

```json
{"performance": {"max_workers": 4}}
```text

**Medium Projects (10-50 repos)**:

```json
{"performance": {"max_workers": 8}}
```

**Large Projects (>50 repos)**:

```json
{"performance": {"max_workers": 16}}
```text

**Debugging**:

```json
{"performance": {"max_workers": 1}}  // Sequential execution
```

### Scaling Guidelines

**Formula**: `max_workers = min(num_cpus * 2, num_repos, 16)`

**Rationale**:

- I/O-bound: Can use more workers than CPUs (waiting time)
- Diminishing returns: Beyond 16 workers, overhead increases
- Memory: Each worker consumes memory (limit based on RAM)

**Example**:

- 4 CPU cores → max_workers = 8 (2× CPUs)
- 100 repositories → still cap at 16 (diminishing returns)
- 2 repositories → max_workers = 2 (no benefit beyond this)

---

## Best Practices

### For Contributors

#### 1. Avoid Shared Mutable State

❌ **Bad** (global mutable state):

```python
# Module-level global
cache = {}

def process_repo(repo):
    cache[repo] = ...  # Race condition!
```text

✅ **Good** (instance-level or local):

```python
class Processor:
    def __init__(self):
        self.cache = {}  # Instance-level
        self._lock = threading.Lock()

    def process_repo(self, repo):
        with self._lock:
            self.cache[repo] = ...  # Thread-safe
```

#### 2. Use Context Managers for Locks

❌ **Bad** (manual lock management):

```python
self._lock.acquire()
try:
    # ... critical section
finally:
    self._lock.release()
```text

✅ **Good** (context manager):

```python
with self._lock:
    # ... critical section
    # Lock automatically released
```

#### 3. Keep Critical Sections Small

❌ **Bad** (lock held too long):

```python
with self._lock:
    data = self.fetch_from_api()  # I/O under lock!
    processed = self.process_data(data)  # CPU under lock!
    self.cache[key] = processed
```text

✅ **Good** (minimal lock time):

```python
# Do expensive work outside lock
data = self.fetch_from_api()
processed = self.process_data(data)

# Only lock for mutation
with self._lock:
    self.cache[key] = processed
```

#### 4. Document Thread Safety

```python
class MyClass:
    """
    Brief description.

    Thread Safety:
        All public methods are thread-safe. Internal lock protects
        shared state. Safe to call from multiple threads concurrently.
    """

    def thread_safe_method(self):
        """
        Do something safely.

        Thread-safe: Uses internal lock for all mutations.
        """
        with self._lock:
            # ...
```text

#### 5. Test Concurrent Scenarios

```python
def test_concurrent_access():
    """Test that concurrent calls don't cause race conditions."""
    context = JenkinsAllocationContext()

    def worker(thread_id):
        jobs = [{"name": f"job-{thread_id}-{i}"} for i in range(10)]
        context.allocate_jobs(f"repo-{thread_id}", jobs)

    # Spawn many threads
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify no duplicates, no data loss
    assert len(context.allocated_jobs) == 1000
```

### For Users

#### 1. Start Conservative

Begin with `max_workers = 4`, measure performance, then adjust.

#### 2. Monitor Resource Usage

```bash
# Check CPU and memory while running
top -pid $(pgrep -f generate_reports)
```text

#### 3. Use Caching

Always enable caching for better performance:

```json
{"performance": {"cache": true}}
```

#### 4. Consider Disk I/O

If analyzing repositories on slow disk (network mount):

- Reduce `max_workers` (avoid I/O contention)
- Copy repos to local disk first

---

## Performance Tuning

### Profiling

Use the built-in profiling script:

```bash
python scripts/profile_performance.py \
  --config config.json \
  --workers 1,4,8,16 \
  --analyze-hotspots
```text

**Output**:

- `docs/profiling/profiling_comparison.md` - Performance comparison
- `docs/profiling/hotspots_workers_N.md` - Bottleneck analysis
- `docs/profiling/profile_workers_N.prof` - Detailed profile data

### Interpreting Results

**Scaling Efficiency**:

- 100%: Ideal (doubling workers halves time)
- 75-90%: Good (expected for I/O-bound)
- 50-75%: Acceptable (some overhead)
- <50%: Poor (too much contention/overhead)

**Example**:

```

Workers | Time (s) | Speedup | Efficiency
--------|----------|---------|------------
1       | 120.0    | 1.0x    | 100%
4       | 35.0     | 3.4x    | 85%   <- Good
8       | 20.0     | 6.0x    | 75%   <- Good
16      | 15.0     | 8.0x    | 50%   <- Diminishing returns

```text

**Recommendation**: Use 8 workers (best balance)

### Common Bottlenecks

#### Git Log Parsing (CPU-Bound)

**Symptom**: CPU at 100%, adding workers doesn't help

**Solution**: Consider ProcessPoolExecutor (future work)

#### API Rate Limits (I/O-Bound)

**Symptom**: Many threads waiting, low CPU usage

**Solution**:

- Reduce `max_workers`
- Implement batch prefetch (future work)
- Increase API timeout if hitting limits

#### Lock Contention

**Symptom**: Threads blocked waiting for locks

**Diagnosis**:

```bash
python -m cProfile -o profile.prof generate_reports.py
python -m pstats profile.prof
>>> sort cumtime
>>> stats 20
# Look for Lock.acquire in top functions
```

**Solution**:

- Reduce critical section size
- Use finer-grained locks
- Implement lock-free data structures

---

## Migration Guide

### From Global Lock to Instance Context

**Before (Phase 6 and earlier)**:

```python
# Global lock at module level
_jenkins_allocation_lock = threading.Lock()

class GitDataCollector:
    def __init__(self, config, time_windows, logger):
        self.allocated_jenkins_jobs = set()  # Instance state
        # ...

    def _get_jenkins_jobs_for_repo(self, repo_name):
        with _jenkins_allocation_lock:  # Global lock!
            # ... allocation logic
```text

**After (Phase 7)**:

```python
# No global lock

class GitDataCollector:
    def __init__(self, config, time_windows, logger,
                 jenkins_allocation_context=None):
        # Context is passed in or created
        self.jenkins_allocation_context = jenkins_allocation_context or JenkinsAllocationContext()
        # No instance state for allocation (managed by context)

    def _get_jenkins_jobs_for_repo(self, repo_name):
        # Use context methods (thread-safe internally)
        cached = self.jenkins_allocation_context.get_cached_jobs(repo_name)
        if cached:
            return cached
        # ...
```

**Caller Changes**:

```python
# Before:
collector = GitDataCollector(config, {}, logger)

# After:
context = JenkinsAllocationContext()  # Create context
collector = GitDataCollector(config, {}, logger, context)  # Pass it in
```text

### Benefits of Migration

1. ✅ **No Global State**: Each instance has independent context
2. ✅ **Better Testing**: Can test with isolated contexts
3. ✅ **No Contention**: Independent instances don't block each other
4. ✅ **Clearer Ownership**: Context owns allocation state explicitly
5. ✅ **Easier Debugging**: Can inspect context state directly

---

## Troubleshooting

### Issue: Deadlock

**Symptom**: Program hangs indefinitely

**Diagnosis**:

```bash
# Send SIGQUIT to get thread dump
kill -QUIT $(pgrep -f generate_reports)
```

**Common Causes**:

- Lock acquired twice in same thread (use `RLock` if needed)
- Circular wait (lock A → lock B, lock B → lock A)

**Solution**:

- Always acquire locks in consistent order
- Keep critical sections small
- Use timeouts: `lock.acquire(timeout=30)`

### Issue: Race Condition

**Symptom**: Inconsistent results, occasional errors

**Diagnosis**:

- Run with `max_workers=1` (sequential) - does it work?
- Add logging in critical sections
- Use thread sanitizer tools (e.g., `python -m pytest --thread-safe`)

**Solution**:

- Identify shared mutable state
- Add lock protection
- Use thread-safe data structures

### Issue: Poor Performance

**Symptom**: Adding workers doesn't improve speed

**Diagnosis**:

```bash
python scripts/profile_performance.py --config config.json --workers 1,4,8
```text

**Common Causes**:

- CPU-bound workload (GIL limitation)
- Lock contention (threads blocking each other)
- I/O bottleneck (disk, network)

**Solutions**:

- CPU-bound: Consider ProcessPoolExecutor
- Lock contention: Reduce critical section size
- I/O bottleneck: Check disk speed, network latency

### Issue: Memory Usage Too High

**Symptom**: OOM errors, high memory consumption

**Diagnosis**:

```bash
# Monitor memory
python -m memory_profiler generate_reports.py
```

**Solutions**:

- Reduce `max_workers` (fewer concurrent threads)
- Process repos in batches
- Enable garbage collection: `gc.collect()`
- Stream large data instead of loading all at once

---

## References

### Internal Documentation

- [Thread Safety Audit](./thread_safety_audit.md) - Detailed audit of all components
- [Phase 7 Plan](../../PHASE_7_CONCURRENCY_PLAN.md) - Implementation roadmap
- [Profiling Script](../../scripts/profile_performance.py) - Performance measurement tool

### External Resources

- [Python Threading](https://docs.python.org/3/library/threading.html)
- [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor)
- [ProcessPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#processpoolexecutor)
- [Thread Safety in Python](https://realpython.com/intro-to-python-threading/)
- [GIL Explanation](https://wiki.python.org/moin/GlobalInterpreterLock)

### Code Examples

See `tests/test_jenkins_allocation_context.py` for comprehensive examples of:

- Thread-safe allocation
- Concurrent cache access
- Stress testing (100 threads)
- Instance isolation

---

## Changelog

### Version 1.0 (2025-01-16)

- Initial documentation
- Covers Phase 7 concurrency refactoring
- Documents thread-safe design
- Includes migration guide from global lock to instance context
- Performance tuning recommendations
- Troubleshooting guide

---

**Questions?** See [Troubleshooting](#troubleshooting) or contact the development team.

**Contributing?** Read [Best Practices](#best-practices) before modifying concurrent code.
