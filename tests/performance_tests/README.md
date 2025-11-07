<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Performance Tests

This directory contains performance threshold tests and benchmarks for the Repository Reporting System.

## Overview

Performance testing ensures that critical operations meet latency, throughput, and memory requirements. This suite includes:

1. **Threshold Tests** (`test_thresholds.py`) - Verify operations complete within acceptable time/memory limits
2. **Benchmark Tests** (`test_benchmarks.py`) - Measure and track performance over time using pytest-benchmark

## Test Categories

### Cache Performance Thresholds

Tests cache operations meet performance requirements:

- **Get operations**: < 1ms latency
- **Set operations**: < 2ms latency
- **Cleanup operations**: < 100ms
- **Pattern invalidation**: < 5ms
- **Throughput**: > 1000 ops/second
- **Memory limits**: < 100MB total cache size

Example:

```python
def test_cache_get_within_threshold(temp_cache_dir, perf_thresholds):
    """Test cache get operation meets latency threshold."""
    manager = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
    # ... measure and assert within threshold
```text

### Parallel Processing Thresholds

Tests parallel processing meets performance targets:

- **Worker pool creation**: < 100ms
- **Processing per item**: < 50ms
- **Result aggregation**: < 10ms
- **Throughput**: > 50 items/second
- **Memory per item**: < 10MB

Example:

```python
def test_batch_processing_per_item_threshold(mock_repository_data, worker_count):
    """Test processing time per item in batch."""
    processor = ParallelRepositoryProcessor(...)
    # ... measure per-item performance
```

### Batch Operation Thresholds

Tests batch operations stay within limits:

- **Request batching**: < 10ms
- **Rate limit checks**: < 1ms
- **Request deduplication**: < 5ms
- **Throughput**: > 100 requests/second
- **Memory overhead**: < 50MB

Example:

```python
def test_request_batching_within_threshold(mock_api_responses):
    """Test request batching performance."""
    batcher = RequestBatcher(batch_size=10)
    # ... verify batching speed
```text

### Integration Thresholds

Tests integrated scenarios:

- Cache + parallel processing
- Memory-constrained batch processing
- Concurrent cache operations
- End-to-end workflows

Example:

```python
def test_end_to_end_cache_and_parallel_performance():
    """Test integrated cache and parallel processing."""
    # Second pass should be 2x faster due to caching
    assert second_pass_duration < first_pass_duration * 0.5
```

## Benchmark Tests

Uses pytest-benchmark for statistical performance measurement:

### Cache Benchmarks

- Get/set operations
- Cache misses
- Invalidation
- Cleanup
- Stats retrieval
- Key generation

### Parallel Processing Benchmarks

- Worker pool lifecycle
- Result aggregation
- Small/medium/large batch processing
- Worker auto-detection

### Batch Operation Benchmarks

- Queue operations
- Request batching
- Deduplication
- Rate limit checking
- Backoff calculation

### Integrated Benchmarks

- Cache-backed parallel processing
- End-to-end batch with cache
- Concurrent cache access

### Memory Benchmarks

- Large cache entries (1MB+)
- Many cache entries (100+)
- Large dataset processing (1000+ items)

### Comparison Benchmarks

- Cache hit vs miss
- Serial vs parallel
- Different batch sizes
- Optimization effectiveness

## Running Performance Tests

### Run All Performance Tests

```bash
pytest tests/performance/ -v
```text

### Run Only Threshold Tests

```bash
pytest tests/performance/test_thresholds.py -v -m performance
```

### Run Only Benchmarks

```bash
pytest tests/performance/test_benchmarks.py -v -m benchmark
```text

### Run with Benchmark Output

```bash
pytest tests/performance/test_benchmarks.py --benchmark-only --benchmark-verbose
```

### Compare Benchmark Results

```bash
# Save baseline
pytest tests/performance/test_benchmarks.py --benchmark-save=baseline

# Compare against baseline
pytest tests/performance/test_benchmarks.py --benchmark-compare=baseline
```text

### Generate Benchmark Report

```bash
pytest tests/performance/test_benchmarks.py --benchmark-only --benchmark-columns=min,max,mean,stddev,median
```

### Run with Memory Profiling

```bash
pytest tests/performance/ -v --profile
```text

## Performance Thresholds

Defined in `conftest.py`:

```python
PERFORMANCE_THRESHOLDS = {
    # Cache operations (seconds)
    "cache_get": 0.001,              # 1ms
    "cache_set": 0.002,              # 2ms
    "cache_cleanup": 0.1,            # 100ms
    "cache_invalidate": 0.005,       # 5ms

    # Parallel processing (seconds)
    "worker_pool_creation": 0.1,     # 100ms
    "batch_processing_per_item": 0.05, # 50ms per item
    "result_aggregation": 0.01,      # 10ms

    # Memory limits (MB)
    "cache_max_size": 100,           # 100MB
    "worker_memory_per_item": 10,    # 10MB per item

    # Throughput (items/second)
    "cache_ops_per_second": 1000,
    "batch_requests_per_second": 100,
    "parallel_items_per_second": 50,
}
```

## Fixtures

### Common Fixtures

- `perf_thresholds` - Performance threshold values
- `benchmark_config` - Benchmark configuration
- `temp_cache_dir` - Temporary cache directory
- `mock_cache_entries` - Mock cache data (100 entries)
- `mock_repository_data` - Mock repository data (50 repos)
- `mock_api_responses` - Mock API responses (100 responses)
- `large_dataset` - Large dataset for stress testing (1000 items)
- `worker_count` - Optimal worker count for testing
- `batch_size` - Optimal batch size for testing
- `memory_constraint_mb` - Memory limit for tests (50MB)

### Assertion Helpers

- `assert_within_threshold()` - Assert value within threshold + margin
- `assert_memory_within_limit()` - Assert memory within limit + margin
- `assert_throughput_meets_minimum()` - Assert throughput meets minimum

## Benchmark Configuration

Default configuration in `conftest.py`:

```python
BENCHMARK_CONFIG = {
    "min_rounds": 5,              # Minimum benchmark iterations
    "max_time": 1.0,              # 1 second max per benchmark
    "warmup": True,               # Enable warmup runs
    "warmup_iterations": 2,       # Number of warmup iterations
}
```text

## Performance Metrics

### Key Metrics Tracked

1. **Latency**
   - Mean, median, min, max
   - P95, P99 percentiles
   - Standard deviation

2. **Throughput**
   - Operations per second
   - Items processed per second
   - Requests per second

3. **Memory**
   - Peak memory usage
   - Average memory usage
   - Memory overhead per operation

4. **Scalability**
   - Performance vs. data size
   - Performance vs. worker count
   - Performance vs. batch size

## CI/CD Integration

Performance tests are designed for CI/CD:

### Fast Tests (< 10 seconds)

```bash
pytest tests/performance/test_thresholds.py -v --tb=short
```

### Full Benchmarks (Optional, slower)

```bash
pytest tests/performance/test_benchmarks.py --benchmark-only
```text

### Regression Detection

```bash
# In CI, compare against baseline
pytest tests/performance/test_benchmarks.py \
  --benchmark-compare=baseline \
  --benchmark-compare-fail=mean:10%
```

## Interpreting Results

### Threshold Test Results

✅ **Pass**: Operation completed within threshold + 10% margin
❌ **Fail**: Operation exceeded threshold + margin

Example output:

```text
PASSED test_cache_get_within_threshold
  Cache get operation: 0.000523s <= 0.001100s (threshold: 0.001000s + 10% margin)
```

### Benchmark Results

Shows statistical analysis:

```text
Name (time in ms)                Min      Max     Mean   StdDev   Median
--------------------------------------------------------------------------------
test_benchmark_cache_get      0.4231   0.8912   0.5123   0.0821   0.4987
test_benchmark_cache_set      0.8123   1.2341   0.9234   0.0912   0.8976
```

## Optimization Guidelines

### If Tests Fail

1. **Identify bottleneck**: Check which specific test is failing
2. **Profile code**: Use profiling tools to find slow operations
3. **Optimize hot paths**: Focus on frequently called code
4. **Consider caching**: Add caching where appropriate
5. **Parallelize**: Use parallel processing for independent operations
6. **Batch operations**: Group operations to reduce overhead

### Adjusting Thresholds

Thresholds should be:

- Based on real-world measurements
- Updated when optimizations are made
- Conservative but achievable
- Documented when changed

To update thresholds, modify `PERFORMANCE_THRESHOLDS` in `conftest.py`.

## Best Practices

1. **Run on consistent hardware** - Performance varies by machine
2. **Close background apps** - Reduce noise in measurements
3. **Use warm caches** - Include warmup iterations
4. **Test realistic data** - Use representative test data
5. **Monitor trends** - Track performance over time
6. **Set alerts** - Alert on regression > 10%
7. **Document changes** - Note why thresholds changed

## Performance Regression Tests

Located in `TestPerformanceRegression` class:

- Compare current performance vs. baseline
- Verify no degradation in key operations
- Check average and P95 latency
- Ensure throughput maintains levels

Example:

```python
def test_cache_performance_vs_baseline():
    """Verify cache performance hasn't regressed from baseline."""
    # Run baseline scenario
    # Check avg_latency < threshold * 2
    # Check p95_latency < threshold * 3
```text

## Test Coverage

Performance tests cover:

✅ Cache operations (get, set, cleanup, invalidation)
✅ Parallel processing (worker pools, batching, aggregation)
✅ Batch operations (batching, deduplication, rate limiting)
✅ Integrated scenarios (cache + parallel, end-to-end)
✅ Memory constraints (size limits, memory usage)
✅ Throughput validation (ops/sec requirements)
✅ Regression detection (baseline comparisons)

**Total Tests**: 47+ threshold tests, 30+ benchmark tests

## Maintenance

### Updating Baselines

When legitimate performance improvements are made:

```bash
# Update benchmark baseline
pytest tests/performance/test_benchmarks.py --benchmark-save=new_baseline
mv .benchmarks/new_baseline .benchmarks/baseline
```

### Adding New Tests

1. Add test to appropriate class in `test_thresholds.py` or `test_benchmarks.py`
2. Use existing fixtures or add new ones to `conftest.py`
3. Document the threshold/benchmark in this README
4. Run locally to verify
5. Update baseline if needed

### Reviewing Performance

Regularly review:

- Benchmark trend graphs
- Failed threshold tests
- Memory usage patterns
- Throughput metrics

## References

- **pytest-benchmark docs**: <https://pytest-benchmark.readthedocs.io/>
- **Performance testing best practices**: See project docs
- **Profiling tools**: cProfile, memory_profiler, py-spy
- **CI/CD integration**: See `.github/workflows/`

## Support

For performance issues:

1. Check test output for specific failures
2. Review benchmark comparison results
3. Profile slow operations
4. Consult optimization guidelines above
5. Open issue with performance data

---

**Last Updated**: Phase 11, Step 8 - Performance Threshold Tests
**Test Count**: 77+ tests (47 thresholds + 30 benchmarks)
**Coverage**: Critical performance paths (cache, parallel, batch)
**Status**: ✅ All tests passing
