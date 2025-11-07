<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Parallel Test Execution Quick Reference

Quick guide for running tests in parallel with pytest-xdist

---

## TL;DR

```bash
# Run all tests in parallel (auto-detect workers)
pytest -n auto

# Run specific test suite in parallel
pytest -n auto tests/unit/

# Run with verbose output
pytest -n auto -v

# Exclude slow tests and run in parallel
pytest -n auto -m "not slow"
```text

**Result:** ~20% faster test execution (25:54 → 20:45)

---

## Installation

```bash
# Install parallel execution support
pip install pytest-xdist pytest-rerunfailures
```

---

## Common Commands

### Development

```bash
# Quick unit tests
pytest -n 4 tests/unit/ -x --tb=short

# Smoke tests (pre-commit)
pytest -n auto -m "smoke" -q

# Integration tests
pytest -n auto tests/integration/ -v
```text

### CI/CD

```bash
# Full test suite (excluding slow tests)
pytest -n auto -v --tb=short -m "not slow"

# With coverage
pytest -n auto --cov=src --cov-report=xml
```

### Debugging

```bash
# Run sequentially (no parallelization)
pytest

# Single worker (easier debugging)
pytest -n 1 -v

# Specific number of workers
pytest -n 4
```text

---

## Worker Count Options

| Option | Description | Use Case |
|--------|-------------|----------|
| `-n auto` | Auto-detect (recommended) | CI/CD, most cases |
| `-n 4` | Fixed 4 workers | Consistent performance |
| `-n logical` | Use logical CPU count | Max parallelization |
| `-n 1` | Single worker | Debugging |

---

## Load Distribution

```bash
# By file (default, recommended)
pytest -n auto --dist loadfile

# By scope (for many small files)
pytest -n auto --dist loadscope

# By group (manual grouping)
pytest -n auto --dist loadgroup
```

---

## Marking Tests

### Flaky Tests (timing-sensitive)

```python
@pytest.mark.flaky(reruns=3, reruns_delay=1)
def test_performance_threshold():
    """Automatically retry up to 3 times."""
    pass
```text

### Serial Tests (must not parallelize)

```python
@pytest.mark.serial
def test_global_state():
    """Run sequentially, not in parallel."""
    pass
```

### Grouping Tests

```python
@pytest.mark.xdist_group(name="database")
def test_db_operation():
    """Run with other database tests."""
    pass
```text

---

## Worker-Specific Fixtures

```python
@pytest.fixture
def temp_dir(tmp_path, worker_id):
    """Create unique temp dir per worker."""
    if worker_id == "master":
        return tmp_path
    return tmp_path / worker_id

@pytest.fixture
def port(worker_id):
    """Assign unique port per worker."""
    base_port = 8000
    if worker_id == "master":
        return base_port
    worker_num = int(worker_id.replace("gw", ""))
    return base_port + worker_num + 1
```

---

## Performance Metrics

| Execution Mode | Runtime | Speedup |
|---------------|---------|---------|
| Sequential | 25m 54s | 1.0x |
| Parallel (2 workers) | 22m 0s | 1.18x |
| Parallel (4 workers) | 21m 20s | 1.21x |
| **Parallel (8 workers)** | **20m 45s** | **1.25x** |
| Parallel (16 workers) | 20m 35s | 1.26x |

**Optimal:** 8 workers (auto-detected on typical machines)

---

## Troubleshooting

### Tests fail only in parallel?

Check for:

- Shared global state → Use `auto_reset` fixture
- File conflicts → Use `worker_id` in paths
- Port conflicts → Use worker-specific ports
- Race conditions → Add proper synchronization

```python
# Fix: Use auto_reset fixture
@pytest.fixture(autouse=True)
def reset_state(auto_reset):
    pass
```text

### Flaky test failures?

```python
# Solution: Mark as flaky
@pytest.mark.flaky(reruns=3, reruns_delay=1)
def test_timing_sensitive():
    pass
```

### Coverage warnings?

```bash
# These are cosmetic, coverage still accurate:
# "No contexts were measured"
# Safe to ignore.
```text

### Workers crash?

```bash
# Reduce worker count
pytest -n 4  # Instead of -n auto

# Or mark tests as serial
@pytest.mark.serial
def test_memory_intensive():
    pass
```

---

## Known Limitations

| Feature | Behavior in Parallel |
|---------|---------------------|
| **Benchmarks** | Auto-disabled (run separately) |
| **Random seed** | Per-worker (use --randomly-seed=X) |
| **Session fixtures** | Created per-worker |
| **Coverage context** | Warning shown (safe to ignore) |

### Running Benchmarks

```bash
# Benchmarks must run sequentially
pytest -m benchmark --benchmark-only
```text

---

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests
  run: |
    pip install pytest-xdist pytest-rerunfailures
    pytest -n auto -v --cov=src
```

### Pre-Commit Hook

```bash
#!/bin/bash
pytest -n auto -m "smoke" -q || exit 1
```text

---

## Environment Variables

```bash
# Set worker count
export PYTEST_XDIST_WORKER_COUNT=4
pytest -n $PYTEST_XDIST_WORKER_COUNT

# Set Hypothesis profile for parallel
export HYPOTHESIS_PROFILE=ci
pytest -n auto
```

---

## Best Practices

✅ **DO:**

- Use `-n auto` for automatic worker detection
- Mark flaky tests with `@pytest.mark.flaky`
- Use `worker_id` fixture for unique resources
- Ensure tests are isolated (use `auto_reset`)
- Run benchmarks separately

❌ **DON'T:**

- Share global state between tests
- Use hardcoded ports or file paths
- Assume specific test execution order
- Run resource-intensive tests with too many workers

---

## Quick Diagnostics

```bash
# Test parallel execution works
pytest -n 2 -v tests/test_isolation.py

# Compare sequential vs parallel
time pytest tests/
time pytest -n auto tests/

# Check for flaky tests
pytest -n auto --tb=short -v | grep RERUN

# Verify worker count
pytest -n auto -v | head -5
# Output: "8 workers [2368 items]"
```text

---

## Getting Help

- **Full Guide:** [PARALLEL_EXECUTION.md](PARALLEL_EXECUTION.md)
- **Test Writing:** [TEST_WRITING_GUIDE.md](TEST_WRITING_GUIDE.md)
- **Isolation:** [TEST_ISOLATION.md](TEST_ISOLATION.md)
- **pytest-xdist:** <https://pytest-xdist.readthedocs.io/>

---

## Summary

| Aspect | Value |
|--------|-------|
| **Command** | `pytest -n auto` |
| **Workers** | 8 (auto-detected) |
| **Speedup** | 1.25x (19.9% faster) |
| **Pass Rate** | 100% (maintained) |
| **Setup Time** | 5 minutes |

**Status:** ✅ Production Ready

Run `pytest -n auto` and save 5+ minutes on every test run!
