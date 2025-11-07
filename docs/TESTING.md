# Testing Guide

**Version:** 1.1
**Last Updated:** 2025-11-03
**Phase:** 12 - Integration & System Tests, Step 5 Complete

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Test Organization](#test-organization)
- [Coverage Requirements](#coverage-requirements)
- [Performance Testing](#performance-testing)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## Overview

The Repository Reporting System has a comprehensive test suite with 1,100+ tests covering:

- **Unit Tests:** Test individual functions and classes in isolation
- **Integration Tests:** Test component interactions and workflows
- **Property-Based Tests:** Validate invariants using Hypothesis
- **Regression Tests:** Prevent known issues from recurring
- **Performance Tests:** Ensure performance thresholds are met
- **Benchmark Tests:** Track performance over time

### Test Suite Statistics

```text
Total Tests:        1,200+
Unit Tests:         ~300
Integration Tests:  122 (Phase 12, Step 5 - ✅ Complete)
Property Tests:     74
Regression Tests:   56
Performance Tests:  47 (16 thresholds + 31 benchmarks)

Overall Coverage:   ~62% (target: 85%+)
Execution Time:     < 45 minutes (full suite)
```

**Phase 12 Update:** Integration test suite expanded from 55 to 122 tests, achieving 152% of the 80-test target. See `docs/testing/phase-12-step-5-completion.md` for details.

---

## Quick Start

### Install Dependencies

```bash
# Install test dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock pytest-timeout
pip install hypothesis pytest-snapshot pytest-benchmark

# Verify installation
pytest --version
```text

### Run All Tests

```bash
# Run complete test suite
PYTHONPATH=. pytest -v

# Run with coverage
PYTHONPATH=. pytest -v --cov=src --cov-report=html

# Run specific category
PYTHONPATH=. pytest -v -m unit
PYTHONPATH=. pytest -v -m integration
```

### Quick Validation

```bash
# Smoke tests (< 1 minute)
PYTHONPATH=. pytest -v -m smoke --no-cov

# Fast unit tests (< 5 minutes)
PYTHONPATH=. pytest tests/unit/ -v --no-cov

# Performance thresholds (< 2 minutes)
PYTHONPATH=. pytest tests/performance/test_thresholds.py -v --no-cov
```text

---

## Test Categories

### 1. Smoke Tests

**Purpose:** Fast validation of critical paths
**Marker:** `@pytest.mark.smoke`
**Duration:** < 1 minute
**Count:** ~10 tests

Example:

```python
@pytest.mark.smoke
def test_basic_import():
    """Verify core modules can be imported."""
    from src.performance.cache import CacheManager
    assert CacheManager is not None

@pytest.mark.smoke
def test_cache_basic_operations():
    """Test basic cache functionality."""
    cache = CacheManager(cache_dir="/tmp/test", max_size_mb=10)
    cache.set(key, value, ttl=60)
    assert cache.get(key) == value
```

When to use:

- Pre-commit validation
- Quick sanity checks
- CI/CD fast feedback

### 2. Unit Tests

**Purpose:** Test individual functions/classes in isolation
**Marker:** `@pytest.mark.unit`
**Duration:** < 10 minutes
**Count:** ~300 tests
**Coverage Target:** 85%+

Example:

```python
@pytest.mark.unit
def test_cache_manager_set_and_get():
    """Test cache set and get operations."""
    cache = CacheManager(cache_dir=temp_dir, max_size_mb=10)

    key = CacheKey.repository("owner", "repo")
    value = {"data": "test"}

    cache.set(key, value, ttl=3600)
    result = cache.get(key)

    assert result == value

@pytest.mark.unit
def test_cache_expiration():
    """Test cache entry expiration."""
    cache = CacheManager(cache_dir=temp_dir, max_size_mb=10)

    key = CacheKey.repository("owner", "repo")
    cache.set(key, {"data": "test"}, ttl=0)  # Expired

    result = cache.get(key)
    assert result is None
```text

Best practices:

- Mock external dependencies
- Test edge cases and error conditions
- Use descriptive test names
- Assert one concept per test

### 3. Integration Tests

**Purpose:** Test component interactions and workflows
**Marker:** `@pytest.mark.integration`
**Duration:** < 15 minutes
**Count:** ~50 tests

Example:

```python
@pytest.mark.integration
def test_cache_with_parallel_processing():
    """Test cache integration with parallel processing."""
    cache = CacheManager(cache_dir=temp_dir, max_size_mb=20)

    def cached_processor(item):
        cache_key = CacheKey.repository("owner", item["name"])
        cached = cache.get(cache_key)
        if cached:
            return cached
        result = process_item(item)
        cache.set(cache_key, result, ttl=3600)
        return result

    with WorkerPool(max_workers=4) as pool:
        results = pool.map(cached_processor, items)

    assert len(results) == len(items)
```

Best practices:

- Test realistic workflows
- Use representative test data
- Clean up resources after tests
- Test error handling

### 4. Property-Based Tests

**Purpose:** Validate invariants and mathematical properties
**Marker:** `@pytest.mark.property`
**Duration:** < 10 minutes
**Count:** 74 tests

Example:

```python
from hypothesis import given, strategies as st

@pytest.mark.property
@given(st.integers(min_value=0, max_value=1000))
def test_time_window_duration_non_negative(seconds):
    """Duration should always be non-negative."""
    start_time = time.time()
    end_time = start_time + seconds

    window = TimeWindow(start_time=start_time, end_time=end_time)

    assert window.duration_seconds >= 0

@pytest.mark.property
@given(st.lists(st.integers(), min_size=1))
def test_aggregation_idempotent(values):
    """Aggregating twice should equal aggregating once."""
    result1 = aggregate(aggregate(values))
    result2 = aggregate(values)

    assert result1 == result2
```text

Best practices:

- Test mathematical invariants
- Use diverse input strategies
- Keep properties simple and clear
- Handle edge cases in strategies

### 5. Regression Tests

**Purpose:** Prevent known issues from recurring
**Marker:** `@pytest.mark.regression`
**Duration:** < 5 minutes
**Count:** 56 tests (25 known issues + 22 snapshots + 9 baseline)

Example:

```python
@pytest.mark.regression
def test_issue_001_empty_repository_handling():
    """
    ISSUE-001: Empty repositories should not cause crashes.

    Previously, processing empty repositories would raise
    AttributeError when accessing commit statistics.
    """
    repo = {"name": "empty", "commits": []}

    # Should not raise exception
    result = process_repository(repo)

    assert result["commit_count"] == 0
    assert result["lines_added"] == 0

@pytest.mark.regression
def test_json_snapshot_repository_output(snapshot):
    """Ensure JSON output format remains stable."""
    repo_data = generate_test_repository()
    result = format_repository_json(repo_data)

    snapshot.assert_match(result, "repository_output.json")
```

Best practices:

- Document the original issue
- Include issue tracking number
- Test the fix, not just the symptom
- Update snapshots when format changes intentionally

### 6. Performance Tests

**Purpose:** Ensure operations meet performance thresholds
**Marker:** `@pytest.mark.performance`
**Duration:** < 5 minutes
**Count:** 16 threshold tests

Example:

```python
@pytest.mark.performance
def test_cache_get_within_threshold(temp_cache_dir, perf_thresholds):
    """Test cache get operation meets latency threshold."""
    cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
    key = CacheKey.repository("owner", "repo")
    cache.set(key, {"data": "test"}, ttl=3600)

    start = time.perf_counter()
    result = cache.get(key)
    duration = time.perf_counter() - start

    assert result is not None
    assert_within_threshold(
        duration,
        perf_thresholds["cache_get"],
        "Cache get operation"
    )
```text

Best practices:

- Test realistic workloads
- Use consistent hardware for comparison
- Set reasonable thresholds with margins
- Document threshold rationale

### 7. Benchmark Tests

**Purpose:** Track performance over time with statistical analysis
**Marker:** `@pytest.mark.benchmark`
**Duration:** ~10 minutes
**Count:** 31 benchmark tests

Example:

```python
@pytest.mark.benchmark
def test_benchmark_cache_get(benchmark, temp_cache_dir):
    """Benchmark cache get operation."""
    cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
    key = CacheKey.repository("owner", "repo")
    cache.set(key, {"data": "test"}, ttl=3600)

    result = benchmark(cache.get, key)
    assert result is not None
```

Best practices:

- Use warmup iterations
- Run multiple rounds for statistical significance
- Compare against baselines
- Track trends over time

---

## Running Tests

### Basic Execution

```bash
# Run all tests
PYTHONPATH=. pytest -v

# Run specific directory
PYTHONPATH=. pytest tests/unit/ -v
PYTHONPATH=. pytest tests/integration/ -v

# Run specific file
PYTHONPATH=. pytest tests/unit/test_cache.py -v

# Run specific test
PYTHONPATH=. pytest tests/unit/test_cache.py::test_cache_get -v
```text

### By Marker

```bash
# Run tests by category
PYTHONPATH=. pytest -v -m smoke
PYTHONPATH=. pytest -v -m unit
PYTHONPATH=. pytest -v -m integration
PYTHONPATH=. pytest -v -m property
PYTHONPATH=. pytest -v -m regression
PYTHONPATH=. pytest -v -m performance

# Combine markers
PYTHONPATH=. pytest -v -m "unit or integration"
PYTHONPATH=. pytest -v -m "not slow"
```

### With Coverage

```bash
# Coverage report
PYTHONPATH=. pytest -v --cov=src --cov-report=html

# Coverage with branch analysis
PYTHONPATH=. pytest -v --cov=src --cov-branch --cov-report=term-missing

# Coverage for specific module
PYTHONPATH=. pytest -v --cov=src.performance --cov-report=html
```text

### Performance Testing

```bash
# Threshold validation (fast)
PYTHONPATH=. pytest tests/performance/test_thresholds.py -v --no-cov

# Benchmarks (slower)
PYTHONPATH=. pytest tests/performance/test_benchmarks.py --benchmark-only

# Save baseline
PYTHONPATH=. pytest tests/performance/test_benchmarks.py \
  --benchmark-only --benchmark-save=baseline

# Compare against baseline
PYTHONPATH=. pytest tests/performance/test_benchmarks.py \
  --benchmark-only --benchmark-compare=baseline
```

### Advanced Options

```bash
# Parallel execution (requires pytest-xdist)
PYTHONPATH=. pytest -v -n auto

# Stop on first failure
PYTHONPATH=. pytest -v -x

# Run last failed tests
PYTHONPATH=. pytest -v --lf

# Show slowest tests
PYTHONPATH=. pytest -v --durations=10

# Verbose output with print statements
PYTHONPATH=. pytest -v -s

# With timeout (requires pytest-timeout)
PYTHONPATH=. pytest -v --timeout=60
```text

---

## Writing Tests

### Test File Structure

```python
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for the cache management system.

This module tests all aspects of cache operations including:
- Get/set operations
- Expiration handling
- Size limits
- Invalidation
"""

import pytest
from src.performance.cache import CacheManager, CacheKey

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit


class TestCacheManager:
    """Tests for CacheManager class."""

    def test_basic_operations(self, temp_cache_dir):
        """Test basic cache get/set operations."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        # Test setup
        key = CacheKey.repository("owner", "repo")
        value = {"data": "test"}

        # Execute
        cache.set(key, value, ttl=3600)
        result = cache.get(key)

        # Verify
        assert result == value

    def test_expiration(self, temp_cache_dir):
        """Test cache entry expiration."""
        cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)

        key = CacheKey.repository("owner", "repo")
        cache.set(key, {"data": "test"}, ttl=0)  # Already expired

        result = cache.get(key)
        assert result is None
```

### Test Naming Conventions

```python
# Good test names
def test_cache_get_returns_value_when_exists():
def test_cache_get_returns_none_when_expired():
def test_cache_set_raises_error_when_full():
def test_worker_pool_creates_specified_number_of_workers():

# Poor test names
def test_cache():
def test_1():
def test_something():
```text

### Fixture Usage

```python
@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

@pytest.fixture
def sample_repository():
    """Generate sample repository data."""
    return {
        "name": "test-repo",
        "owner": "test-owner",
        "commits": [
            {"sha": "abc123", "message": "Initial commit"},
            {"sha": "def456", "message": "Add feature"},
        ]
    }

def test_with_fixtures(temp_cache_dir, sample_repository):
    """Test using fixtures."""
    cache = CacheManager(cache_dir=temp_cache_dir)
    cache.set("repo", sample_repository, ttl=3600)

    result = cache.get("repo")
    assert result == sample_repository
```

### Parametrized Tests

```python
@pytest.mark.parametrize("ttl,should_exist", [
    (3600, True),   # Future expiration
    (0, False),     # Already expired
    (-1, False),    # Negative TTL
])
def test_cache_expiration_scenarios(temp_cache_dir, ttl, should_exist):
    """Test various expiration scenarios."""
    cache = CacheManager(cache_dir=temp_cache_dir)
    cache.set("key", "value", ttl=ttl)

    result = cache.get("key")
    if should_exist:
        assert result == "value"
    else:
        assert result is None
```text

### Mocking

```python
from unittest.mock import Mock, patch, MagicMock

def test_with_mocked_dependency(mocker):
    """Test using mocked external dependency."""
    # Mock the external API call
    mock_api = mocker.patch('src.api.github_client.GitHubClient')
    mock_api.return_value.get_repository.return_value = {
        "name": "test-repo"
    }

    # Test code that uses the mocked API
    client = GitHubClient()
    result = client.get_repository("owner", "repo")

    assert result["name"] == "test-repo"
    mock_api.return_value.get_repository.assert_called_once()
```

---

## Test Organization

### Directory Structure

```text
tests/
├── README.md                   # Test suite overview
├── conftest.py                 # Global fixtures
│
├── unit/                       # Unit tests
│   ├── conftest.py
│   ├── test_cache.py
│   ├── test_parallel.py
│   └── test_batch.py
│
├── integration/                # Integration tests
│   ├── conftest.py
│   └── test_workflows.py
│
├── property/                   # Property-based tests
│   ├── conftest.py
│   ├── test_time_windows.py
│   ├── test_aggregations.py
│   └── test_transformations.py
│
├── regression/                 # Regression tests
│   ├── conftest.py
│   ├── test_known_issues.py
│   ├── test_json_snapshots.py
│   └── __snapshots__/
│
├── performance/                # Performance tests
│   ├── README.md
│   ├── conftest.py
│   ├── test_thresholds.py
│   └── test_benchmarks.py
│
├── fixtures/                   # Test fixtures
│   ├── __init__.py
│   ├── repositories.py
│   └── data.py
│
└── utils/                      # Test utilities
    ├── __init__.py
    ├── assertions.py
    └── helpers.py
```

### File Naming

- Test files: `test_<module>.py`
- Fixture files: `conftest.py` or `fixtures/<name>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<description>`

---

## Coverage Requirements

### Overall Targets

| Module | Target | Current | Status |
|--------|--------|---------|--------|
| src/performance/ | 90% | 100% | ✅ |
| src/util/ | 90% | 96% | ✅ |
| src/rendering/ | 85% | 95% | ✅ |
| src/cli/ | 85% | 90% | ✅ |
| src/config/ | 85% | ~75% | ⚠️ |
| src/domain/ | 85% | ~60% | ⚠️ |
| src/api/ | 85% | 50% | ⚠️ |
| Overall | 85% | ~62% | ⚠️ |

### Checking Coverage

```bash
# Generate coverage report
PYTHONPATH=. pytest --cov=src --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Terminal report with missing lines
PYTHONPATH=. pytest --cov=src --cov-report=term-missing

# Coverage for specific module
PYTHONPATH=. pytest --cov=src.performance --cov-report=term-missing
```text

### Coverage Configuration

In `pytest.ini`:

```ini
[pytest]
addopts =
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-branch
```

In `.coveragerc`:

```ini
[run]
source = src
omit =
    */tests/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```text

---

## Performance Testing

### Threshold Tests

Validate operations meet performance requirements:

```python
@pytest.mark.performance
def test_cache_get_within_threshold(temp_cache_dir, perf_thresholds):
    """Cache get should complete within 1ms."""
    cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
    key = CacheKey.repository("owner", "repo")
    cache.set(key, {"data": "test"}, ttl=3600)

    start = time.perf_counter()
    result = cache.get(key)
    duration = time.perf_counter() - start

    assert_within_threshold(
        duration,
        perf_thresholds["cache_get"],
        "Cache get operation",
        margin=0.1  # 10% margin
    )
```

### Benchmark Tests

Track performance over time:

```python
@pytest.mark.benchmark
def test_benchmark_cache_get(benchmark, temp_cache_dir):
    """Benchmark cache get operation."""
    cache = CacheManager(cache_dir=temp_cache_dir, max_size_mb=10)
    key = CacheKey.repository("owner", "repo")
    cache.set(key, {"data": "test"}, ttl=3600)

    # benchmark() runs the function multiple times
    # and collects statistics
    result = benchmark(cache.get, key)
    assert result is not None
```text

### Performance Thresholds

Defined in `tests/performance/conftest.py`:

```python
PERFORMANCE_THRESHOLDS = {
    # Latency (seconds)
    "cache_get": 0.001,              # 1ms
    "cache_set": 0.002,              # 2ms
    "cache_cleanup": 0.1,            # 100ms

    # Throughput (ops/sec)
    "cache_ops_per_second": 1000,

    # Memory (MB)
    "cache_max_size": 100,
}
```

---

## CI/CD Integration

### GitHub Actions

Tests run automatically on:

- Every pull request
- Push to main/develop
- Weekly performance tracking

### Workflows

1. **Pre-commit Checks** (< 5 min)
   - Smoke tests
   - Fast unit tests
   - Linting
   - Security scan

2. **Comprehensive Tests** (< 30 min)
   - Full test suite
   - Coverage reporting
   - Performance thresholds
   - Code quality checks

3. **Performance Tracking** (weekly)
   - Full benchmarks
   - Memory profiling
   - Trend analysis

### Local CI Simulation

```bash
# Install act
brew install act  # macOS

# Run workflow locally
act -j smoke-tests
act -j unit-tests
```text

---

## Best Practices

### 1. Test Independence

```python
# ✅ Good - tests are independent
def test_cache_get():
    cache = CacheManager()  # Fresh instance
    cache.set("key", "value")
    assert cache.get("key") == "value"

def test_cache_expiration():
    cache = CacheManager()  # Fresh instance
    cache.set("key", "value", ttl=0)
    assert cache.get("key") is None

# ❌ Bad - tests depend on each other
cache = CacheManager()  # Shared instance

def test_cache_get():
    cache.set("key", "value")
    assert cache.get("key") == "value"

def test_cache_expiration():
    # Depends on previous test!
    assert cache.get("key") == "value"
```

### 2. Clear Assertions

```python
# ✅ Good - clear assertion messages
assert result == expected, f"Expected {expected}, got {result}"
assert len(items) > 0, "Items list should not be empty"

# ❌ Bad - no context
assert result == expected
assert items
```text

### 3. Test One Thing

```python
# ✅ Good - tests one concept
def test_cache_get_returns_value():
    cache.set("key", "value")
    assert cache.get("key") == "value"

def test_cache_get_returns_none_when_missing():
    assert cache.get("nonexistent") is None

# ❌ Bad - tests multiple concepts
def test_cache():
    cache.set("key", "value")
    assert cache.get("key") == "value"
    assert cache.get("other") is None
    cache.clear()
    assert cache.size() == 0
```

### 4. Use Fixtures

```python
# ✅ Good - use fixtures for setup
@pytest.fixture
def cache(temp_cache_dir):
    return CacheManager(cache_dir=temp_cache_dir)

def test_cache_operations(cache):
    cache.set("key", "value")
    assert cache.get("key") == "value"

# ❌ Bad - duplicate setup
def test_cache_get():
    cache = CacheManager(cache_dir="/tmp/test")
    cache.set("key", "value")
    assert cache.get("key") == "value"

def test_cache_set():
    cache = CacheManager(cache_dir="/tmp/test")
    cache.set("key", "value")
    assert cache.get("key") == "value"
```text

### 5. Test Edge Cases

```python
def test_cache_with_empty_value():
    cache.set("key", "")
    assert cache.get("key") == ""

def test_cache_with_none_value():
    cache.set("key", None)
    assert cache.get("key") is None

def test_cache_with_large_value():
    large_value = "x" * (1024 * 1024)  # 1MB
    cache.set("key", large_value)
    assert cache.get("key") == large_value

def test_cache_with_special_characters():
    cache.set("key", "hello\nworld\t!")
    assert cache.get("key") == "hello\nworld\t!"
```

---

## Troubleshooting

### Common Issues

#### Tests Pass Locally but Fail in CI

**Cause:** Environment differences

Solution:

```bash
# Match CI Python version
python --version  # Should be 3.11

# Clean environment
pip install -r requirements.txt --force-reinstall

# Set PYTHONPATH
export PYTHONPATH=.
```text

#### Coverage Too Low

**Cause:** Missing tests or unmarked test files

Solution:

```bash
# Find uncovered code
pytest --cov=src --cov-report=term-missing

# Check test discovery
pytest --collect-only

# Verify test markers
pytest --markers
```

#### Performance Tests Fail

**Cause:** System under load or thresholds too strict

Solution:

```bash
# Close background apps
# Run tests in isolation
pytest tests/performance/test_thresholds.py -v

# Check actual vs threshold in output
# Adjust thresholds in conftest.py if needed
```text

#### Import Errors

**Cause:** PYTHONPATH not set

Solution:

```bash
# Always set PYTHONPATH
export PYTHONPATH=.
PYTHONPATH=. pytest -v

# Or install package in editable mode
pip install -e .
```

#### Fixture Not Found

**Cause:** Fixture in wrong conftest.py

Solution:

- Move fixture to appropriate conftest.py
- Global fixtures: `tests/conftest.py`
- Category fixtures: `tests/<category>/conftest.py`

---

## Additional Resources

### Documentation

- [Test README](../tests/README.md)
- [Performance Tests](../tests/performance/README.md)
- [CI/CD Integration](./CI_CD_INTEGRATION.md)
- [Coverage Report](./TEST_COVERAGE_REPORT.md)

### External Links

- [pytest Documentation](https://docs.pytest.org)
- [pytest-cov](https://pytest-cov.readthedocs.io)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io)
- [Hypothesis](https://hypothesis.readthedocs.io)
- [pytest-mock](https://pytest-mock.readthedocs.io)

### Getting Help

- Check test logs for detailed errors
- Review documentation in `docs/`
- File an issue in the repository
- Ask in team chat/forum

---

**Last Updated:** 2025-01-27
**Phase:** 11 - Test Coverage Expansion
**Version:** 1.0
**Status:** ✅ Complete
