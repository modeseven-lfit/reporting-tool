<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Concurrency Configuration Guide

## Repository Reporting System - Quick Reference

**Version:** 2.0
**Last Updated:** January 29, 2025
**Type:** Quick Reference

---

## Overview

This quick reference covers concurrency configuration for the Repository Reporting System after Phase 7 (Concurrency Refinement). The system uses adaptive thread pools, hybrid execution (CPU/IO separation), and enhanced error handling.

### Default Behavior

The system is **pre-configured with optimal defaults**:

- ✅ Adaptive thread pool sizing
- ✅ Automatic CPU/IO separation
- ✅ Enhanced error handling with retry
- ✅ Resource monitoring

**Most users don't need to change anything!**

---

## Quick Start

### Basic Usage (Recommended)

```python
from src.rendering.modern_renderer import ModernReportRenderer

# Just use it - defaults are optimized
renderer = ModernReportRenderer(concurrent=True)
reports = renderer.render_batch(data_list)
```text

### Disable Concurrency (If Needed)

```python
# Sequential processing
renderer = ModernReportRenderer(concurrent=False)
```

---

## Thread Pool Configuration

### Adaptive Thread Pool (Default)

```python
from src.concurrency.adaptive_pool import AdaptiveThreadPool

# Auto-configure based on system (recommended)
pool = AdaptiveThreadPool()

# Manual configuration
pool = AdaptiveThreadPool(
    min_workers=2,              # Minimum threads
    max_workers=16,             # Maximum threads
    target_utilization=0.8,     # Target CPU utilization (80%)
    scale_up_threshold=0.9,     # Scale up at 90% utilization
    scale_down_threshold=0.3    # Scale down at 30% utilization
)
```text

### Worker Count Guidelines

| System | Recommended Workers | Notes |
|--------|-------------------|-------|
| 2 cores | 4-8 workers | Small system |
| 4 cores | 8-16 workers | Typical laptop |
| 8 cores | 16-32 workers | Workstation |
| 16+ cores | 32-64 workers | Server |

**Formula:** `workers = cpu_count * 2 to 4` for I/O-bound work

### Manual Thread Pool

```python
from concurrent.futures import ThreadPoolExecutor

# Simple fixed-size pool
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(task, data) for data in dataset]
    results = [f.result() for f in futures]
```

---

## Hybrid Execution (CPU vs I/O)

### Automatic Separation (Default)

```python
from src.concurrency.hybrid_executor import HybridExecutor

# Automatically uses correct pool type
executor = HybridExecutor()

# System decides: CPU-bound = processes, I/O-bound = threads
results = executor.execute_batch(tasks)
```text

### Manual Control

```python
# Force CPU-bound execution (uses processes)
executor.submit_cpu_bound(
    heavy_computation,
    large_dataset
)

# Force I/O-bound execution (uses threads)
executor.submit_io_bound(
    api_call,
    url
)
```

### When to Use Each

**CPU-bound (Processes):**

- Data processing
- Calculations
- Parsing large files
- Heavy algorithms

**I/O-bound (Threads):**

- API calls
- File I/O
- Network requests
- Database queries

---

## Error Handling Configuration

### Automatic Retry (Default)

```python
from src.concurrency.error_handler import ErrorHandler

# Retry with exponential backoff (enabled by default)
handler = ErrorHandler(
    max_retries=3,              # Try up to 3 times
    base_delay=1.0,             # Start with 1 second delay
    max_delay=30.0,             # Max 30 seconds between retries
    exponential_base=2.0        # Double delay each time
)
```text

### Custom Error Handling

```python
# Custom retry logic
handler = ErrorHandler(
    max_retries=5,              # More retries
    base_delay=0.5,             # Faster initial retry
    retry_on=[TimeoutError, ConnectionError],  # Specific errors
    should_log=True             # Log all retries
)

# Use with executor
with handler:
    result = risky_operation()
```

### Disable Retry

```python
# No automatic retry
handler = ErrorHandler(max_retries=0)
```text

---

## Resource Monitoring

### Memory Monitoring

```python
from src.concurrency.resource_monitor import ResourceMonitor

# Stop operations at 80% memory usage
with ResourceMonitor(max_memory_percent=80) as monitor:
    process_large_dataset(data)

    # Check current usage
    if monitor.memory_usage > 0.7:
        print("Warning: High memory usage")
```

### CPU Monitoring

```python
# Monitor CPU usage
monitor = ResourceMonitor(
    max_cpu_percent=90,         # Stop at 90% CPU
    check_interval=1.0          # Check every second
)

with monitor:
    cpu_intensive_task()
```text

### Combined Monitoring

```python
# Monitor both memory and CPU
monitor = ResourceMonitor(
    max_memory_percent=80,
    max_cpu_percent=90,
    check_interval=0.5          # Check twice per second
)
```

---

## Configuration Patterns

### Pattern 1: High Throughput

**Use Case:** Maximum speed, plenty of resources

```python
renderer = ModernReportRenderer(concurrent=True)

pool = AdaptiveThreadPool(
    max_workers=32,             # Many workers
    target_utilization=0.9      # Push hard
)

handler = ErrorHandler(max_retries=1)  # Fast failure
```text

### Pattern 2: Balanced (Recommended)

**Use Case:** Good performance, safe resource usage

```python
renderer = ModernReportRenderer(concurrent=True)

pool = AdaptiveThreadPool()   # Auto-configure (default)

handler = ErrorHandler()       # Default retry settings
```

### Pattern 3: Conservative

**Use Case:** Limited resources, stability priority

```python
renderer = ModernReportRenderer(concurrent=True)

pool = AdaptiveThreadPool(
    max_workers=4,              # Fewer workers
    target_utilization=0.6      # Lower utilization
)

handler = ErrorHandler(
    max_retries=5,              # More retries
    base_delay=2.0              # Longer delays
)

monitor = ResourceMonitor(
    max_memory_percent=70,      # Stricter limits
    max_cpu_percent=80
)
```text

### Pattern 4: Single-threaded

**Use Case:** Debugging, testing, or resource constraints

```python
renderer = ModernReportRenderer(concurrent=False)
# All operations run sequentially
```

---

## Environment Variables

Configure via environment variables:

```bash
# Thread pool settings
export CONCURRENT_WORKERS=16
export CONCURRENT_MAX_WORKERS=32
export TARGET_UTILIZATION=0.8

# Retry settings
export MAX_RETRIES=3
export RETRY_BASE_DELAY=1.0

# Resource limits
export MAX_MEMORY_PERCENT=80
export MAX_CPU_PERCENT=90

# Logging
export CONCURRENT_LOG_LEVEL=INFO
```text

---

## Monitoring & Debugging

### Get Pool Statistics

```python
pool = AdaptiveThreadPool()

# Get current stats
stats = pool.get_stats()
print(f"Active workers: {stats['active_workers']}")
print(f"Queue size: {stats['queue_size']}")
print(f"Total tasks: {stats['total_tasks']}")
print(f"Completed: {stats['completed_tasks']}")
print(f"Failed: {stats['failed_tasks']}")
print(f"Utilization: {stats['utilization']:.1%}")
```

### Enable Debug Logging

```python
import logging

# Enable debug logging for concurrency
logging.getLogger('src.concurrency').setLevel(logging.DEBUG)

# See what the pool is doing
pool = AdaptiveThreadPool()
# Logs will show scaling decisions, task execution, etc.
```text

### Performance Profiling

```python
from src.performance.profiler import PerformanceProfiler

with PerformanceProfiler() as profiler:
    pool = AdaptiveThreadPool()
    results = pool.map(process_item, items)

# View timing breakdown
print(profiler.get_stats())
```

---

## Common Issues & Solutions

### Issue 1: Too Many Threads

**Symptom:** System slows down with many workers

**Solution:**

```python
# Reduce worker count
pool = AdaptiveThreadPool(max_workers=8)  # Try fewer

# Or disable concurrency
renderer = ModernReportRenderer(concurrent=False)
```text

### Issue 2: Tasks Timing Out

**Symptom:** Operations fail with timeout errors

**Solution:**

```python
# Increase retry attempts and delays
handler = ErrorHandler(
    max_retries=5,
    base_delay=2.0,
    max_delay=60.0
)
```

### Issue 3: High Memory Usage

**Symptom:** Memory grows continuously

**Solution:**

```python
# Enable memory monitoring
with ResourceMonitor(max_memory_percent=70):
    process_data()

# Reduce workers
pool = AdaptiveThreadPool(max_workers=4)

# Process in smaller batches
from src.performance.batch import BatchProcessor
for batch in BatchProcessor(batch_size=50).process(data):
    process(batch)
```text

### Issue 4: Deadlocks or Hangs

**Symptom:** System stops responding

**Solution:**

```python
# Add timeout to operations
import signal

def timeout_handler(signum, frame):
    raise TimeoutError("Operation timed out")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout

try:
    result = long_running_operation()
finally:
    signal.alarm(0)  # Cancel timeout
```

---

## Best Practices

### DO ✅

1. **Use defaults** - Already optimized for most cases
2. **Monitor resources** - Enable ResourceMonitor for production
3. **Handle errors gracefully** - Use ErrorHandler with retry
4. **Profile before optimizing** - Measure, don't guess
5. **Scale gradually** - Start with fewer workers, increase if needed

### DON'T ❌

1. **Don't set workers too high** - More isn't always better
2. **Don't disable error handling** - Always have retry logic
3. **Don't ignore warnings** - Resource warnings mean trouble
4. **Don't mix CPU/IO** - Let HybridExecutor separate them
5. **Don't forget to cleanup** - Use context managers

---

## Testing Concurrency

### Test Thread Safety

```python
import pytest
from concurrent.futures import ThreadPoolExecutor

def test_thread_safety():
    """Test that operations are thread-safe."""
    renderer = ModernReportRenderer(concurrent=True)

    # Run same operation from multiple threads
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(renderer.render_template, 'test.html', data)
            for _ in range(100)
        ]
        results = [f.result() for f in futures]

    # All should succeed
    assert len(results) == 100
    assert all(r is not None for r in results)
```text

### Stress Test

```python
def stress_test_concurrency():
    """Stress test with many concurrent operations."""
    pool = AdaptiveThreadPool(max_workers=32)

    # Submit many tasks
    tasks = [pool.submit(process_item, i) for i in range(1000)]

    # All should complete
    results = [t.result() for t in tasks]
    assert len(results) == 1000
```

---

## Configuration Checklist

**Basic Setup:**

- [ ] Decide if concurrency is needed (usually yes)
- [ ] Use default settings initially
- [ ] Enable error handling with retry
- [ ] Add resource monitoring for production

**Optimization (if needed):**

- [ ] Profile to find bottlenecks
- [ ] Adjust worker counts based on testing
- [ ] Tune retry settings for your use case
- [ ] Set appropriate resource limits

**Production:**

- [ ] Enable comprehensive logging
- [ ] Monitor pool statistics
- [ ] Set up alerts for failures
- [ ] Document any custom configuration

---

## Summary

**Key Points:**

1. ✅ **Defaults work well** - No configuration needed for most cases
2. ✅ **Adaptive pools** - Automatically scale based on load
3. ✅ **CPU/IO separation** - System handles automatically
4. ✅ **Error handling** - Built-in retry with backoff
5. ✅ **Resource monitoring** - Prevents system overload

**When to Configure:**

- 🔧 Performance issues with defaults
- 🔧 Resource-constrained environment
- 🔧 Specific error handling requirements
- 🔧 Debugging or testing needs

**Current Performance:** 60+ concurrent renders/second with defaults

---

## Resources

### Documentation

- Performance Guide: `docs/guides/PERFORMANCE_OPTIMIZATION.md`
- Architecture Docs: `docs/architecture/`
- API Documentation: See docstrings

### Code Examples

- `tests/test_concurrency/` - Test examples
- `examples/concurrent_rendering.py` - Usage examples

### Getting Help

1. Check logs for errors
2. Review stats with `pool.get_stats()`
3. Enable debug logging
4. Consult architecture documentation

---

**Document Status:** Complete
**Last Reviewed:** January 29, 2025
**Next Review:** As needed
