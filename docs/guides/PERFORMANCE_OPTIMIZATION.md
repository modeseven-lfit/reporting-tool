<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Performance Optimization Guide

## Repository Reporting System - Quick Reference

**Version:** 2.0
**Last Updated:** January 29, 2025
**Type:** Quick Reference

---

## Overview

This quick reference covers performance optimization for the Repository Reporting System after Phase 7 (Concurrency Refinement) and Phase 8 (Renderer Modernization).

### Current Performance

- **HTML Rendering:** ~16ms average (6.2x faster than 100ms target)
- **Markdown Rendering:** ~12ms average
- **Concurrent Throughput:** 60+ renders per second
- **Thread Safety:** 100% validated

---

## Quick Wins

### 1. Use Concurrent Rendering

```python
from src.rendering.modern_renderer import ModernReportRenderer

# Enable concurrent rendering (default)
renderer = ModernReportRenderer(concurrent=True)

# Batch render multiple reports
reports = renderer.render_batch(report_data_list)
```text

**Impact:** 3-5x faster for multiple reports

### 2. Choose the Right Theme

```python
# Minimal theme = fastest rendering
renderer = ModernReportRenderer(theme='minimal')

# Default/Dark themes = slightly slower but more features
renderer = ModernReportRenderer(theme='default')
```

**Impact:** 10-15% faster with minimal theme

### 3. Cache Templates

```python
# Template caching is enabled by default
renderer = ModernReportRenderer(cache_templates=True)

# Clear cache if needed
renderer.clear_cache()
```text

**Impact:** 40-50% faster on repeated renders

---

## Concurrency Tuning

### Thread Pool Configuration

```python
from src.concurrency.adaptive_pool import AdaptiveThreadPool

# Auto-tune based on CPU cores (recommended)
pool = AdaptiveThreadPool()  # Uses optimal size

# Manual configuration
pool = AdaptiveThreadPool(
    min_workers=2,
    max_workers=16,
    target_utilization=0.8
)
```

### CPU vs I/O Operations

```python
from src.concurrency.hybrid_executor import HybridExecutor

# Automatically separates CPU and I/O bound work
executor = HybridExecutor()

# CPU-bound: uses process pool
executor.submit_cpu_bound(heavy_computation, data)

# I/O-bound: uses thread pool
executor.submit_io_bound(api_call, url)
```text

**Default Settings:**

- CPU-bound workers: `os.cpu_count()`
- I/O-bound workers: `os.cpu_count() * 5`

---

## Rendering Optimization

### Data Preparation

```python
from src.rendering.data_preparers import RepositoryDataPreparer

# Prepare data once, render many times
preparer = RepositoryDataPreparer()
prepared_data = preparer.prepare(raw_data)

# Reuse prepared data
html_default = renderer.render_template('repo.html', prepared_data)
renderer.set_theme('dark')
html_dark = renderer.render_template('repo.html', prepared_data)
```

### Minimize Template Complexity

```html
<!-- GOOD: Simple loop -->
{% for item in items %}
    <div>{{ item.name }}</div>
{% endfor %}

<!-- BAD: Nested loops and complex filters -->
{% for category in categories %}
    {% for item in items|selectattr('cat', 'eq', category)|sort %}
        {% if item.count > threshold %}
            <!-- Complex logic -->
        {% endif %}
    {% endfor %}
{% endfor %}
```text

### Template Best Practices

1. **Pre-filter data in Python** (not in templates)
2. **Avoid nested loops** when possible
3. **Use components** for reusable elements
4. **Cache calculated values** in data preparation

---

## Memory Optimization

### Batch Processing

```python
from src.performance.batch import BatchProcessor

# Process large datasets in batches
processor = BatchProcessor(batch_size=100)

for batch in processor.process(large_dataset):
    results = process_batch(batch)
    # Results are processed and released
```

### Resource Limits

```python
# Set memory limits for concurrent operations
from src.concurrency.resource_monitor import ResourceMonitor

monitor = ResourceMonitor(
    max_memory_percent=80,  # Stop at 80% memory
    check_interval=1.0      # Check every second
)

with monitor:
    # Your operations
    pass
```text

---

## Profiling & Monitoring

### Enable Performance Profiling

```python
from src.performance.profiler import PerformanceProfiler

# Profile a specific operation
with PerformanceProfiler() as profiler:
    result = renderer.render_template('repo.html', data)

# View results
print(profiler.get_stats())
```

### Benchmark Rendering

```python
from src.benchmarks.rendering import benchmark_renderer

# Run standard benchmarks
results = benchmark_renderer(
    renderer=renderer,
    templates=['repo.html', 'workflow.html'],
    iterations=100
)

print(f"Average time: {results['average_ms']}ms")
print(f"95th percentile: {results['p95_ms']}ms")
```text

### Monitor Concurrency

```python
from src.concurrency.adaptive_pool import AdaptiveThreadPool

pool = AdaptiveThreadPool()

# Get current statistics
stats = pool.get_stats()
print(f"Active workers: {stats['active_workers']}")
print(f"Queue size: {stats['queue_size']}")
print(f"Utilization: {stats['utilization']:.1%}")
```

---

## Common Performance Issues

### Issue 1: Slow Report Generation

**Symptom:** Reports take >500ms to generate

**Solutions:**

```python
# 1. Enable caching
renderer = ModernReportRenderer(cache_templates=True)

# 2. Use minimal theme
renderer.set_theme('minimal')

# 3. Reduce data size
prepared_data = preparer.prepare(raw_data, max_items=100)
```text

### Issue 2: High Memory Usage

**Symptom:** Memory usage grows continuously

**Solutions:**

```python
# 1. Use batch processing
for batch in BatchProcessor(batch_size=50).process(data):
    process(batch)

# 2. Clear caches periodically
renderer.clear_cache()

# 3. Enable resource monitoring
with ResourceMonitor(max_memory_percent=80):
    # Your code
    pass
```

### Issue 3: Thread Contention

**Symptom:** Adding more threads doesn't improve performance

**Solutions:**

```python
# 1. Reduce worker count
pool = AdaptiveThreadPool(max_workers=8)  # Try fewer workers

# 2. Check for GIL contention (use processes instead)
executor = HybridExecutor()
executor.submit_cpu_bound(cpu_heavy_task, data)

# 3. Profile to find bottleneck
with PerformanceProfiler() as profiler:
    # Your code
    pass
```text

---

## Performance Targets

### Rendering Targets

| Operation | Target | Typical | Status |
|-----------|--------|---------|--------|
| Markdown render | <50ms | ~12ms | ✅ Excellent |
| HTML render | <100ms | ~16ms | ✅ Excellent |
| Theme switch | <10ms | ~5ms | ✅ Excellent |

### Concurrency Targets

| Metric | Target | Typical | Status |
|--------|--------|---------|--------|
| Concurrent renders | >50/sec | 60+/sec | ✅ Excellent |
| Thread utilization | 70-90% | 80-85% | ✅ Optimal |
| Queue depth | <100 | <50 | ✅ Healthy |

### Memory Targets

| Resource | Target | Typical | Status |
|----------|--------|---------|--------|
| Base memory | <100MB | ~80MB | ✅ Good |
| Per render | <5MB | ~3MB | ✅ Excellent |
| Cache size | <50MB | ~30MB | ✅ Good |

---

## Configuration Examples

### High Performance (Speed Priority)

```python
# Maximum speed configuration
renderer = ModernReportRenderer(
    theme='minimal',              # Fastest theme
    cache_templates=True,         # Enable caching
    concurrent=True               # Parallel rendering
)

pool = AdaptiveThreadPool(
    max_workers=32,               # More workers
    target_utilization=0.9        # High utilization
)
```

### Balanced (Speed + Quality)

```python
# Balanced configuration (recommended)
renderer = ModernReportRenderer(
    theme='default',              # Good looking + fast
    cache_templates=True,
    concurrent=True
)

pool = AdaptiveThreadPool()       # Auto-configure
```text

### Low Resource (Memory Priority)

```python
# Minimal memory footprint
renderer = ModernReportRenderer(
    theme='minimal',
    cache_templates=False,        # No caching
    concurrent=False              # Sequential
)

pool = AdaptiveThreadPool(
    max_workers=4,                # Fewer workers
    target_utilization=0.7        # Lower utilization
)
```

---

## Performance Checklist

**Before Optimizing:**

- [ ] Profile to identify bottlenecks
- [ ] Set performance targets
- [ ] Establish baseline metrics

**Rendering Optimization:**

- [ ] Enable template caching
- [ ] Choose appropriate theme
- [ ] Pre-process data in Python
- [ ] Minimize template complexity
- [ ] Use components for reusability

**Concurrency Optimization:**

- [ ] Use adaptive thread pools
- [ ] Separate CPU/IO operations
- [ ] Monitor resource utilization
- [ ] Tune worker counts if needed

**Memory Optimization:**

- [ ] Use batch processing for large datasets
- [ ] Clear caches periodically
- [ ] Set memory limits
- [ ] Monitor memory usage

**Validation:**

- [ ] Run benchmarks
- [ ] Compare against targets
- [ ] Test under load
- [ ] Validate thread safety

---

## Getting Help

### Performance Issues

1. **Run profiler** to identify bottlenecks
2. **Check logs** for errors or warnings
3. **Review metrics** against targets
4. **Consult architecture docs** for design patterns

### Resources

- Architecture Documentation: `docs/architecture/`
- Template Guide: `docs/guides/TEMPLATE_DEVELOPMENT.md`
- Concurrency Guide: `docs/guides/CONCURRENCY_CONFIG.md`
- API Documentation: See docstrings in code

---

## Summary

**Key Takeaways:**

1. ✅ **Use defaults** - Already optimized for most cases
2. ✅ **Enable caching** - 40-50% faster repeated renders
3. ✅ **Profile first** - Don't guess, measure
4. ✅ **Batch processing** - For large datasets
5. ✅ **Monitor resources** - Prevent issues before they happen

**Current Performance:** Already exceeds all targets (6.2x faster than goal)

**When to Optimize:** Only if you have specific performance issues or requirements beyond defaults

---

**Document Status:** Complete
**Last Reviewed:** January 29, 2025
**Next Review:** As needed
