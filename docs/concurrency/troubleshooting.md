<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Concurrency Troubleshooting Guide

**Author:** Repository Reporting System Team
**Date:** 2025-01-16
**Version:** 1.0
**Phase:** 7 - Concurrency Strategy Refinement

---

## Table of Contents

1. [Common Issues](#common-issues)
2. [Debugging Tools](#debugging-tools)
3. [Error Messages](#error-messages)
4. [Performance Problems](#performance-problems)
5. [Data Integrity Issues](#data-integrity-issues)
6. [Resource Problems](#resource-problems)
7. [Getting Help](#getting-help)

---

## Common Issues

### Issue 1: Program Hangs / Deadlock

**Symptoms**:

- Program stops responding
- No progress for extended period
- CPU usage drops to 0%

**Diagnosis**:

```bash
# Get process ID
ps aux | grep generate_reports

# Send signal to print thread dump
kill -QUIT <pid>

# Or use Python debugger
python -c "import faulthandler; faulthandler.dump_traceback_later(10)" generate_reports.py
```text

**Common Causes**:

1. **Circular Lock Dependency**

   ```python
   # Thread A: acquires lock1, waits for lock2
   # Thread B: acquires lock2, waits for lock1
   # = DEADLOCK
   ```

2. **Re-acquiring Same Lock**

   ```python
   with self._lock:
       self.method_that_also_locks()  # Deadlock!
   ```

**Solutions**:

1. **Always acquire locks in same order**:

   ```python
   # Good: consistent order
   with lock_a:
       with lock_b:
           # ...
   ```

2. **Use RLock for recursive locking**:

   ```python
   self._lock = threading.RLock()  # Reentrant lock
   ```

3. **Add timeout to detect deadlocks**:

   ```python
   if self._lock.acquire(timeout=30):
       try:
           # Critical section
       finally:
           self._lock.release()
   else:
       raise TimeoutError("Possible deadlock detected")
   ```

---

### Issue 2: Race Condition / Inconsistent Results

**Symptoms**:

- Results vary between runs
- Occasional errors that disappear on retry
- Data inconsistencies (e.g., wrong counts)

**Diagnosis**:

```bash
# Run sequentially (no concurrency)
reporting-tool generate --max-workers 1

# Compare with concurrent run
reporting-tool generate --max-workers 8

# Results should be identical
diff output_sequential.json output_concurrent.json
```

**Common Causes**:

1. **Unprotected Shared State**:

   ```python
   # Bad: no lock protection
   self.counter += 1  # Race condition!
   ```

2. **Check-Then-Act Pattern**:

   ```python
   # Bad: not atomic
   if key not in self.cache:  # Check
       self.cache[key] = value  # Act (race!)
   ```

**Solutions**:

1. **Add lock protection**:

   ```python
   with self._lock:
       self.counter += 1  # Thread-safe
   ```

2. **Use atomic operations**:

   ```python
   # Thread-safe dict operations
   self.cache.setdefault(key, value)
   ```

3. **Make state immutable**:

   ```python
   # Read-only after initialization
   self.config = config  # Never modified
   ```

---

### Issue 3: Poor Scaling / No Speedup

**Symptoms**:

- Adding workers doesn't improve performance
- Speedup much less than expected
- Efficiency < 50%

**Diagnosis**:

```bash
# Profile with different worker counts
python scripts/profile_performance.py \
  --config config.json \
  --workers 1,4,8,16
```text

**Common Causes**:

1. **CPU-Bound with GIL**:
   - Python's Global Interpreter Lock limits parallelism
   - Only one thread executes Python bytecode at a time

2. **Lock Contention**:
   - Threads spend time waiting for locks
   - Critical sections too large

3. **I/O Saturation**:
   - Disk or network bandwidth maxed out
   - More threads don't help

**Solutions**:

**For CPU-Bound**:

```json
{
  "performance": {
    "strategy": "process",  // Future: Use ProcessPoolExecutor
    "max_workers": 4
  }
}
```

**For Lock Contention**:

```python
# Before: large critical section
with self._lock:
    data = self.fetch_data()  # I/O under lock!
    result = self.process(data)  # CPU under lock!
    self.cache[key] = result

# After: minimal critical section
data = self.fetch_data()  # Outside lock
result = self.process(data)  # Outside lock
with self._lock:
    self.cache[key] = result  # Only mutation
```text

**For I/O Saturation**:

```bash
# Copy to faster disk
rsync -av /slow/repos/ /fast/ssd/repos/

# Or reduce workers
{"performance": {"max_workers": 4}}
```

---

### Issue 4: Memory Leaks / High Memory Usage

**Symptoms**:

- Memory usage grows over time
- Out of memory errors
- System becomes unresponsive

**Diagnosis**:

```bash
# Monitor memory usage
python -m memory_profiler generate_reports.py

# Or use system tools
top -pid $(pgrep -f generate_reports)
```text

**Common Causes**:

1. **Accumulating References**:

   ```python
   # Bad: keeps all data in memory
   self.all_results.append(large_data)
   ```

2. **Circular References**:

   ```python
   # Can prevent garbage collection
   obj.parent = parent
   parent.child = obj
   ```

3. **Too Many Workers**:

   ```python
   # Each worker holds memory
   max_workers = 100  # Too many!
   ```

**Solutions**:

1. **Process in batches**:

   ```python
   # Don't load all at once
   for batch in chunks(repos, batch_size=10):
       process_batch(batch)
       # Memory released after each batch
   ```

2. **Explicit cleanup**:

   ```python
   import gc

   results = process_repos(repos)
   # ... use results ...
   del results
   gc.collect()  # Force garbage collection
   ```

3. **Reduce max_workers**:

   ```json
   {"performance": {"max_workers": 4}}  // Lower memory footprint
   ```

---

## Debugging Tools

### 1. Thread Dump

**Get current state of all threads**:

```python
import threading
import traceback

def dump_threads():
    for thread_id, frame in sys._current_frames().items():
        print(f"\n=== Thread {thread_id} ===")
        traceback.print_stack(frame)

# Call when debugging
dump_threads()
```

### 2. Lock Debugging

**Track lock acquisitions**:

```python
import threading

class DebugLock:
    def __init__(self, name):
        self._lock = threading.Lock()
        self.name = name

    def acquire(self, timeout=-1):
        print(f"[{threading.current_thread().name}] Acquiring {self.name}")
        result = self._lock.acquire(timeout=timeout)
        if result:
            print(f"[{threading.current_thread().name}] Acquired {self.name}")
        return result

    def release(self):
        print(f"[{threading.current_thread().name}] Releasing {self.name}")
        self._lock.release()
```text

### 3. Race Condition Detection

**Use ThreadSanitizer (Python 3.12+)**:

```bash
python -X dev -m pytest tests/ --thread-check
```

**Manual stress testing**:

```python
def test_concurrent_stress():
    errors = []

    def worker():
        try:
            for _ in range(1000):
                # Your concurrent operation
                context.allocate_jobs(...)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Race conditions detected: {errors}"
```text

### 4. Performance Profiling

**cProfile (built-in)**:

```bash
python -m cProfile -o profile.prof generate_reports.py
python -m pstats profile.prof
```

**py-spy (sampling profiler)**:

```bash
# Install
pip install py-spy

# Profile running process
py-spy top --pid $(pgrep -f generate_reports)

# Generate flamegraph
py-spy record -o profile.svg -- reporting-tool generate
```text

---

## Error Messages

### "RuntimeError: Lock is already acquired"

**Cause**: Attempting to acquire same lock twice in same thread

**Solution**: Use `threading.RLock()` instead of `threading.Lock()`

```python
# Change from:
self._lock = threading.Lock()

# To:
self._lock = threading.RLock()  # Reentrant
```

---

### "RuntimeError: maximum recursion depth exceeded"

**Cause**: Circular references or infinite recursion in concurrent code

**Solution**:

1. Check for circular lock dependencies
2. Add recursion guards
3. Review call stack for patterns

```python
def process(self, data, _depth=0):
    if _depth > 100:
        raise RecursionError("Too deep")
    # ... processing ...
```text

---

### "BrokenProcessPool: A process in the pool was terminated abruptly"

**Cause**: Process crashed in ProcessPoolExecutor

**Solution**:

1. Check for segfaults (native code)
2. Look for OOM kills
3. Add error handling in worker functions

```python
def worker(data):
    try:
        return process(data)
    except Exception as e:
        logger.exception(f"Worker failed: {e}")
        return {"error": str(e)}
```

---

### "TimeoutError: Lock acquire timed out"

**Cause**: Lock held too long or deadlock

**Solution**:

1. Increase timeout (if legitimate long operation)
2. Investigate deadlock (if timeout is frequent)
3. Reduce critical section size

```python
# Add logging to find culprit
with self._lock:
    start = time.time()
    # ... critical section ...
    duration = time.time() - start
    if duration > 1.0:
        logger.warning(f"Lock held for {duration:.2f}s")
```text

---

## Performance Problems

### Problem: Scaling Efficiency < 50%

**Diagnosis**:

```bash
python scripts/profile_performance.py --config config.json --workers 1,8
# Check efficiency in output
```

**If CPU-Bound**:

- Top functions are parsing, processing (not I/O)
- CPU utilization > 90%
- Consider ProcessPoolExecutor (future)

**If Lock Contention**:

- Threads blocked in `Lock.acquire()`
- Reduce critical section size
- Use finer-grained locks

**If I/O Saturation**:

- Disk/network bandwidth maxed
- Use faster storage
- Reduce max_workers

---

### Problem: Slower with Concurrency

**Diagnosis**:

```text
Workers | Time (s)
--------|----------
1       | 60
8       | 75       <-- Slower!
```

**Causes**:

1. **Thread overhead** dominates for small workloads
2. **Lock contention** creates serialization
3. **GIL thrashing** for CPU-bound code

**Solutions**:

1. Use fewer workers: `max_workers = 4`
2. Sequential for small projects: `max_workers = 1`
3. Batch work to amortize overhead

---

## Data Integrity Issues

### Problem: Duplicate Job Allocations

**Symptom**: Same Jenkins job allocated to multiple repos

**Diagnosis**:

```python
# Check for duplicates
summary = collector.get_jenkins_job_allocation_summary()
allocated = summary["allocated_job_names"]
if len(allocated) != len(set(allocated)):
    print("DUPLICATES FOUND!")
```text

**Cause**: Race condition in allocation logic

**Solution**: Ensure `JenkinsAllocationContext` is used correctly

```python
# Correct: use context methods (thread-safe)
allocated = context.allocate_jobs(repo_name, jobs)

# Wrong: direct access (not thread-safe)
for job in jobs:
    if job not in self.allocated_jobs:  # Race!
        self.allocated_jobs.add(job)
```

---

### Problem: Missing Data in Results

**Symptom**: Some repositories have incomplete data

**Diagnosis**:

```python
# Check for errors in results
for result in results:
    if "error" in result:
        print(f"Failed: {result['repo']}: {result['error']}")
```text

**Causes**:

1. Worker exception not caught
2. Timeout in subprocess
3. Race condition in data collection

**Solutions**:

```python
# Add comprehensive error handling
def _analyze_single_repository(self, repo_path):
    try:
        return self._do_analysis(repo_path)
    except Exception as e:
        self.logger.exception(f"Failed to analyze {repo_path}")
        return {
            "repo": repo_path.name,
            "error": str(e),
            "status": "failed"
        }
```

---

## Resource Problems

### Problem: Too Many Open Files

**Error**: `OSError: [Errno 24] Too many open files`

**Diagnosis**:

```bash
# Check file descriptor limit
ulimit -n

# List open files
lsof -p $(pgrep -f generate_reports)
```text

**Solutions**:

1. **Increase limit**:

   ```bash
   ulimit -n 4096
   ```

2. **Close files explicitly**:

   ```python
   with open(file) as f:
       data = f.read()
   # File closed automatically
   ```

3. **Reduce max_workers**:

   ```json
   {"performance": {"max_workers": 4}}
   ```

---

### Problem: High CPU Usage / System Unresponsive

**Diagnosis**:

```bash
# Check CPU per thread
top -H -p $(pgrep -f generate_reports)
```

**Solutions**:

1. **Reduce max_workers**:

   ```json
   {"performance": {"max_workers": 4}}
   ```

2. **Add delays**:

   ```python
   import time
   time.sleep(0.01)  # Yield CPU
   ```

3. **Lower priority**:

   ```bash
   nice -n 10 reporting-tool generate
   ```

---

## Getting Help

### Before Reporting an Issue

**Gather this information**:

1. **Configuration**:

   ```bash
   cat config.json
   ```

2. **System info**:

   ```bash
   python --version
   uname -a
   free -h
   df -h
   ```

3. **Error logs**:

   ```bash
   # Full error with traceback
   reporting-tool generate 2>&1 | tee error.log
   ```

4. **Profiling data**:

   ```bash
   python scripts/profile_performance.py --config config.json
   ```

### Reporting Template

```markdown
## Issue Description
Brief description of the problem

## Environment
- OS: macOS 13.0 / Ubuntu 22.04 / Windows 11
- Python: 3.11.6
- RAM: 16GB
- Disk: SSD / HDD / NFS
- CPU: 8 cores

## Configuration
```json
{
  "performance": {
    "max_workers": 8
  }
}
```text

## Steps to Reproduce

1. Clone repositories
2. Run: `reporting-tool generate --config config.json`
3. Observe error

## Expected Behavior

Should complete successfully

## Actual Behavior

Hangs after 5 minutes

## Logs

```

[ERROR] ...

```text

## Profiling Data

Attached: profiling_comparison.md

## What I've Tried

- Reduced max_workers to 4 (still hangs)
- Disabled caching (no change)
- Ran sequentially (works fine)

```

### Getting Support

1. **Documentation**:
   - [Concurrency Model](./model.md)
   - [Performance Tuning](./performance_tuning.md)
   - [Thread Safety Audit](./thread_safety_audit.md)

2. **Search Issues**:
   - Check existing GitHub issues
   - Search for error messages

3. **Contact Team**:
   - Create GitHub issue with template above
   - Include profiling data and logs
   - Tag as `concurrency` and `performance`

---

## Quick Diagnostic Checklist

**Performance Issues**:

- [ ] Run profiling script
- [ ] Check scaling efficiency
- [ ] Identify bottleneck (CPU/I/O/Lock)
- [ ] Try different max_workers values
- [ ] Enable caching
- [ ] Use local disk (not network)

**Data Issues**:

- [ ] Run sequentially (max_workers=1)
- [ ] Compare sequential vs concurrent results
- [ ] Check error logs for exceptions
- [ ] Verify all repos processed
- [ ] Check for race conditions

**Resource Issues**:

- [ ] Monitor memory usage
- [ ] Check disk space
- [ ] Verify file descriptor limits
- [ ] Review max_workers setting
- [ ] Check system load

**Stability Issues**:

- [ ] Enable debug logging
- [ ] Run with max_workers=1
- [ ] Check for deadlocks (thread dump)
- [ ] Add timeouts to locks
- [ ] Review recent code changes

---

**Version**: 1.0
**Last Updated**: 2025-01-16
**Maintained By**: Repository Reporting System Team
