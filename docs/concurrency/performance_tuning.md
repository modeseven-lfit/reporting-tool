<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Performance Tuning Guide

**Author:** Repository Reporting System Team
**Date:** 2025-01-16
**Version:** 1.0
**Phase:** 7 - Concurrency Strategy Refinement

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Profiling](#profiling)
3. [Configuration Tuning](#configuration-tuning)
4. [Optimization Strategies](#optimization-strategies)
5. [Hardware Considerations](#hardware-considerations)
6. [Case Studies](#case-studies)
7. [Advanced Topics](#advanced-topics)

---

## Quick Start

### 1. Measure First

Never optimize without data. Run the profiling script:

```bash
python scripts/profile_performance.py \
  --config config.json \
  --workers 1,4,8,16 \
  --analyze-hotspots
```text

### 2. Check Results

Open `docs/profiling/profiling_comparison.md` and look for:

- **Best worker count**: Which configuration is fastest?
- **Scaling efficiency**: Is it above 70%?
- **Bottlenecks**: CPU-bound or I/O-bound?

### 3. Apply Recommended Settings

```json
{
  "performance": {
    "max_workers": 8,
    "cache": true,
    "timeout": 30.0
  }
}
```

### 4. Verify Improvement

Run profiling again and compare results.

---

## Profiling

### Running the Profiler

#### Basic Profiling

```bash
# Profile with default worker counts (1, 4, 8)
python scripts/profile_performance.py --config config.json
```text

#### Custom Worker Counts

```bash
# Test specific configurations
python scripts/profile_performance.py \
  --config config.json \
  --workers 2,6,10,16
```

#### With Hotspot Analysis

```bash
# Generate detailed hotspot breakdown
python scripts/profile_performance.py \
  --config config.json \
  --workers 1,8 \
  --analyze-hotspots
```text

### Understanding Output

#### Profiling Comparison Report

**Location**: `docs/profiling/profiling_comparison.md`

**Key Metrics**:

```

| Workers | Wall Time (s) | CPU Time (s) | CPU Util (%) | Speedup |
|---------|---------------|--------------|--------------|---------|
| 1       | 120.0         | 115.0        | 95.8         | 1.00x   |
| 4       | 35.0          | 130.0        | 92.9         | 3.43x   |
| 8       | 20.0          | 145.0        | 90.6         | 6.00x   |
| 16      | 15.0          | 155.0        | 64.6         | 8.00x   |

```text

**Analysis**:

- **Wall Time**: Actual time elapsed (lower is better)
- **CPU Time**: Total CPU consumed by all threads
- **CPU Util**: How efficiently CPU is used
- **Speedup**: Improvement vs. sequential (1 worker)

**Optimal**: 8 workers (best speedup before efficiency drops)

#### Scaling Efficiency

```

Efficiency = (Actual Speedup / Ideal Speedup) × 100%

```text

**Example**:

- 8 workers, ideal speedup = 8.0x
- Actual speedup = 6.0x
- Efficiency = (6.0 / 8.0) × 100% = 75%

**Interpretation**:

- **90-100%**: Excellent (rare, nearly ideal scaling)
- **75-90%**: Good (typical for I/O-bound work)
- **50-75%**: Acceptable (some overhead, still beneficial)
- **<50%**: Poor (too much contention, reduce workers)

#### Hotspot Analysis

**Location**: `docs/profiling/hotspots_workers_N.md`

**CPU-Bound Functions** (focus for optimization):

```

_parse_git_log_output         25.3s  (CPU-intensive)
_parse_commit_data             12.1s  (CPU-intensive)
json.loads                      8.4s  (CPU-intensive)

```text

**I/O-Bound Functions** (expected bottlenecks):

```

subprocess.run                 45.2s  (I/O wait)
requests.get                   18.3s  (Network I/O)
open/read                       6.1s  (Disk I/O)

```text

**Optimization Priority**:

1. Fix CPU-bound hotspots first (biggest impact)
2. Reduce I/O calls (caching, batching)
3. Optimize lock contention (if present)

---

## Configuration Tuning

### max_workers

**Purpose**: Number of concurrent worker threads

**Default**: 8

**Tuning Guide**:

| Scenario | Recommended | Rationale |
|----------|-------------|-----------|
| Small projects (<10 repos) | 4 | Low overhead, sufficient parallelism |
| Medium projects (10-50 repos) | 8 | Balanced performance/resource usage |
| Large projects (>50 repos) | 12-16 | Maximize throughput |
| Fast disk (SSD) | Higher | Can handle more concurrent I/O |
| Slow disk (HDD, NFS) | Lower | Avoid I/O contention |
| CPU bottleneck | 4-6 | More won't help (GIL limitation) |
| I/O bottleneck | 12-16 | Can overlap I/O waits |
| Debugging | 1 | Sequential execution, easier tracing |

**Finding Optimal Value**:

```bash
# Test multiple values
for workers in 4 8 12 16; do
  echo "Testing $workers workers..."
  time reporting-tool generate --config config.json --max-workers $workers
done
```

**Rule of Thumb**:

```text
max_workers = min(num_cpus × 2, num_repos, 16)
```

### cache

**Purpose**: Enable caching of API responses and git data

**Default**: `true`

**Settings**:

```json
{
  "performance": {
    "cache": true   // Highly recommended
  }
}
```text

**Impact**:

- ✅ Reduces redundant API calls (10-50% speedup)
- ✅ Avoids re-parsing git logs
- ⚠️ Uses disk space (typically <100MB)

**Disable Only If**:

- Disk space is extremely limited
- Data must be fresh every run
- Debugging cache-related issues

### timeout

**Purpose**: Maximum time to wait for API calls

**Default**: 30.0 seconds

**Tuning**:

```json
{
  "performance": {
    "timeout": 60.0  // Increase for slow networks
  }
}
```

**Recommendations**:

- **Fast network**: 15.0s
- **Normal network**: 30.0s (default)
- **Slow/unreliable network**: 60.0s
- **Rate-limited APIs**: 90.0s

---

## Optimization Strategies

### 1. Reduce Work

#### Skip Unnecessary Analysis

```json
{
  "features": {
    "enabled": false  // Disable feature detection if not needed
  },
  "workflows": {
    "enabled": false  // Skip workflow analysis if not needed
  }
}
```text

**Impact**: 20-40% speedup (depending on skipped features)

#### Limit Time Windows

```json
{
  "time_windows": [
    {"name": "30d", "days": 30}
    // Remove longer windows if not needed
  ]
}
```

**Impact**: Proportional to number of windows removed

### 2. Optimize I/O

#### Use Local Disk

```bash
# Copy repos from network drive to local SSD
rsync -av /mnt/network/repos/ /tmp/local_repos/

# Run analysis on local copy
reporting-tool generate --repos-path /tmp/local_repos
```text

**Impact**: 2-5x speedup for network-mounted repos

#### Batch API Calls

Enable caching to reduce API roundtrips:

```json
{
  "performance": {
    "cache": true
  }
}
```

**Future Enhancement**: Batch prefetch (Phase 7 planned work)

### 3. Optimize CPU Usage

#### Enable Aggressive Garbage Collection

```python
import gc

# Before processing
gc.collect()
gc.set_threshold(700, 10, 10)  # More aggressive
```text

**Impact**: Reduces memory fragmentation, 5-10% speedup

#### Use PyPy (Advanced)

```bash
# Install PyPy
pypy3 -m uv sync  # Recommended
# or: pip install .

# Run with PyPy
pypy3 generate_reports.py --config config.json
```

**Impact**: 2-5x speedup for CPU-bound code (JIT compilation)

**Warning**: Test thoroughly, not all libraries support PyPy

### 4. Reduce Lock Contention

#### Check for Lock Bottlenecks

```bash
python -m cProfile -o profile.prof generate_reports.py
python -m pstats profile.prof
```text

```python
>>> sort cumtime
>>> stats 20
# Look for threading.Lock.acquire in top functions
```

#### Minimize Critical Sections

```python
# Before (lock held too long)
with self._lock:
    data = self.fetch_data()  # I/O under lock!
    result = self.process(data)  # CPU under lock!
    self.cache[key] = result

# After (minimal lock time)
data = self.fetch_data()  # Outside lock
result = self.process(data)  # Outside lock
with self._lock:
    self.cache[key] = result  # Only mutation under lock
```text

---

## Hardware Considerations

### CPU

**Impact**: High (for parsing, processing)

**Recommendations**:

- **2 cores**: max_workers = 2-4
- **4 cores**: max_workers = 6-8
- **8+ cores**: max_workers = 12-16

**Note**: Hyperthreading counts as separate cores

### Memory

**Impact**: Medium (each worker consumes memory)

**Typical Usage**:

- Base: ~500MB
- Per worker: ~100-200MB
- Large repos: +50MB per repo

**Example**:

- 8 workers × 150MB = 1.2GB
- Base = 0.5GB
- **Total**: ~1.7GB

**Recommendations**:

- **4GB RAM**: max_workers ≤ 8
- **8GB RAM**: max_workers ≤ 16
- **16GB+ RAM**: No limit

**If Memory Limited**:

```json
{
  "performance": {
    "max_workers": 4  // Reduce concurrency
  }
}
```

### Disk

**Impact**: High (git operations are I/O intensive)

**SSD vs HDD**:

| Metric | SSD | HDD |
|--------|-----|-----|
| Random I/O | Excellent | Poor |
| Sequential I/O | Excellent | Good |
| Recommended max_workers | 12-16 | 4-6 |

**Network Storage (NFS, SMB)**:

- Very slow for git operations
- Recommended: Copy to local disk first
- max_workers: 2-4 (avoid overwhelming network)

### Network

**Impact**: Medium (API calls)

**Fast Network (>100 Mbps)**:

- max_workers: 12-16
- timeout: 15-30s

**Slow Network (<10 Mbps)**:

- max_workers: 4-8
- timeout: 60-90s
- Enable aggressive caching

---

## Case Studies

### Case Study 1: Small Project (5 Repos)

**Environment**:

- 5 repositories, ~1000 commits each
- 4-core CPU, 8GB RAM
- SSD storage

**Initial Config**:

```json
{"performance": {"max_workers": 8}}
```text

**Results**:

```

Workers | Time (s) | Speedup
--------|----------|--------
1       | 45       | 1.0x
8       | 20       | 2.25x  ← Overhead dominates

```text

**Analysis**: Overhead of thread spawning is high for small workload

**Optimized Config**:

```json
{"performance": {"max_workers": 4}}
```

**Improved Results**:

```text
Workers | Time (s) | Speedup
--------|----------|--------
1       | 45       | 1.0x
4       | 15       | 3.0x    ← Better!
```

**Lesson**: Fewer workers can be faster for small projects

---

### Case Study 2: Large Project (100 Repos)

**Environment**:

- 100 repositories, ~5000 commits each
- 8-core CPU, 16GB RAM
- SSD storage

**Initial Config**:

```json
{"performance": {"max_workers": 8}}
```text

**Results**:

```

Workers | Time (s) | Speedup
--------|----------|--------
1       | 3600     | 1.0x
8       | 600      | 6.0x

```text

**Profiling**: I/O-bound (git subprocess dominates)

**Optimized Config**:

```json
{"performance": {"max_workers": 16}}
```

**Improved Results**:

```text
Workers | Time (s) | Speedup
--------|----------|--------
1       | 3600     | 1.0x
16      | 400      | 9.0x    ← 33% faster
```

**Lesson**: Large I/O-bound projects benefit from more workers

---

### Case Study 3: Network Storage

**Environment**:

- 30 repositories on NFS mount
- Fast CPU/RAM
- Slow network (10 Mbps)

**Initial Config**:

```json
{"performance": {"max_workers": 8}}
```text

**Results**:

```

Workers | Time (s) | Speedup
--------|----------|--------
1       | 600      | 1.0x
8       | 580      | 1.03x   ← Minimal benefit!

```text

**Profiling**: Network I/O saturated

**Optimized Approach**:

```bash
# Copy to local disk first
rsync -av /nfs/repos/ /tmp/repos/
reporting-tool generate --repos-path /tmp/repos
```

**Improved Results**:

```text
Workers | Time (s) | Speedup
--------|----------|--------
1       | 200      | 3.0x    ← vs. original
8       | 35       | 17.1x   ← vs. original
```

**Lesson**: Local disk copy is worth it for network storage

---

## Advanced Topics

### Process Pool for CPU-Bound Tasks

**When to Consider**:

- Profiling shows >80% CPU time in parsing
- Scaling efficiency <50% with thread pool
- Large repositories (millions of commits)

**Future Implementation** (Phase 7 planned):

```json
{
  "performance": {
    "strategy": "process",  // Use ProcessPoolExecutor
    "max_workers": 4        // Fewer workers (higher overhead)
  }
}
```text

**Tradeoffs**:

- ✅ Bypasses GIL (true parallelism)
- ✅ Good for CPU-intensive parsing
- ❌ Higher memory usage (separate processes)
- ❌ Slower startup (process spawning)
- ❌ Serialization overhead (pickling data)

**Recommendation**: Wait for profiling data before implementing

### Batch Prefetch

**Concept**: Fetch all API data upfront in single thread, then process in parallel

**Benefits**:

- Reduces API call volume (single batch request)
- Avoids redundant calls
- Better for rate-limited APIs

**Future Implementation** (Phase 7 planned):

```python
# Prefetch phase (single-threaded)
prefetcher = DataPrefetcher(jenkins_client, gerrit_client)
prefetched_data = prefetcher.fetch_all(repo_names)

# Analysis phase (parallel, using prefetched data)
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [
        executor.submit(analyze_repo, repo, prefetched_data)
        for repo in repos
    ]
```

**Impact**: 20-40% reduction in API calls

### Custom Worker Strategies

**Dynamic Worker Adjustment**:

```python
# Adjust based on system load
import os
cpu_count = os.cpu_count()
load_avg = os.getloadavg()[0]

if load_avg > cpu_count * 0.8:
    max_workers = max(1, cpu_count // 2)  # Reduce load
else:
    max_workers = cpu_count * 2  # Full power
```text

**Hybrid Approach** (I/O + CPU):

```python
# Use thread pool for I/O, process pool for CPU
io_pool = ThreadPoolExecutor(max_workers=8)
cpu_pool = ProcessPoolExecutor(max_workers=4)

# Fetch data with threads (I/O)
data_futures = [io_pool.submit(fetch_repo, r) for r in repos]

# Process data with processes (CPU)
result_futures = [
    cpu_pool.submit(parse_git_log, f.result())
    for f in data_futures
]
```

---

## Benchmarking Checklist

Before claiming performance improvement:

- [ ] Run profiling script with same configuration
- [ ] Test multiple worker counts (1, 4, 8, 16)
- [ ] Run each configuration 3 times (average results)
- [ ] Check for regressions (ensure results are identical)
- [ ] Measure memory usage (no significant increase)
- [ ] Document findings in profiling report
- [ ] Update recommendations based on data

---

## Summary

### Quick Wins

1. ✅ **Enable caching**: `"cache": true` (10-50% speedup)
2. ✅ **Tune max_workers**: Profile to find optimal value
3. ✅ **Use local disk**: Copy from network storage if needed
4. ✅ **Skip unused features**: Disable unnecessary analysis

### Long-Term Optimizations

1. ⏳ **Batch prefetch**: Reduce API call volume (planned)
2. ⏳ **Process pool**: For CPU-bound workloads (if profiling justifies)
3. ⏳ **Incremental analysis**: Only process changed repos (future)
4. ⏳ **Distributed execution**: Multiple machines (future)

### Best Practices

1. 📊 **Always profile first**: Don't guess, measure
2. 🎯 **Optimize bottlenecks**: Focus on top 3 hotspots
3. ⚖️ **Balance tradeoffs**: Speed vs. memory vs. complexity
4. ✅ **Verify correctness**: Ensure results are identical
5. 📝 **Document changes**: Record before/after metrics

---

**Need Help?** See [Troubleshooting](./model.md#troubleshooting) in the concurrency model guide.

**Found a bottleneck?** Report it with profiling data for investigation.

**Achieved great speedup?** Share your configuration as a case study!

---

**Version**: 1.0
**Last Updated**: 2025-01-16
**Maintained By**: Repository Reporting System Team
