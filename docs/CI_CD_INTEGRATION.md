<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# CI/CD Integration Guide

**Version:** 1.0
**Last Updated:** 2025-01-27
**Phase:** 11 - Test Coverage Expansion, Step 9

---

## Overview

This document describes the CI/CD integration for the Repository Reporting System, including automated testing, performance tracking, code quality checks, and deployment workflows.

## Table of Contents

- [Workflow Overview](#workflow-overview)
- [GitHub Actions Workflows](#github-actions-workflows)
- [Test Execution Strategy](#test-execution-strategy)
- [Performance Monitoring](#performance-monitoring)
- [Code Quality Gates](#code-quality-gates)
- [Security Scanning](#security-scanning)
- [Artifact Management](#artifact-management)
- [Notification Strategy](#notification-strategy)
- [Local Development](#local-development)
- [Troubleshooting](#troubleshooting)

---

## Workflow Overview

### CI/CD Pipeline Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                    Pull Request Created                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Pre-commit Checks (< 5 min)               │
│  • Quick validation                                          │
│  • Smoke tests                                               │
│  • Fast unit tests                                           │
│  • Linting & formatting                                      │
│  • Security scan                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (on success)
┌─────────────────────────────────────────────────────────────┐
│               Comprehensive Test Suite (< 30 min)           │
│  • Unit tests (all modules)                                  │
│  • Integration tests                                         │
│  • Property-based tests                                      │
│  • Regression tests                                          │
│  • Performance threshold tests                               │
│  • Code quality analysis                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (on merge to main)
┌─────────────────────────────────────────────────────────────┐
│              Full Test Suite + Benchmarks                    │
│  • All tests with coverage                                   │
│  • Full benchmark suite                                      │
│  • Coverage report generation                                │
│  • Artifact archival                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ (weekly schedule)
┌─────────────────────────────────────────────────────────────┐
│            Performance Tracking (30 min)                     │
│  • Comprehensive benchmarks                                  │
│  • Memory profiling                                          │
│  • Trend analysis                                            │
│  • Performance dashboard update                              │
│  • Alert on threshold violations                             │
└─────────────────────────────────────────────────────────────┘
```

---

## GitHub Actions Workflows

### 1. Pre-commit Checks (`.github/workflows/pre-commit.yaml`)

**Trigger:** Pull request opened, synchronized, or reopened
**Duration:** < 5 minutes
**Purpose:** Fast feedback for developers

Jobs:

- `quick-checks`: Smoke tests and validation
- `fast-tests`: Unit tests without coverage
- `lint-and-format`: Code style and formatting
- `security-scan`: Security vulnerability scanning
- `pr-comment`: Summary posted to PR

Example Usage:

```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
```text

What It Validates:

- ✅ Smoke tests pass
- ✅ No syntax errors
- ✅ No debugging statements left in code
- ✅ Fast unit tests pass
- ✅ Code formatting meets standards
- ✅ No security vulnerabilities

### 2. Comprehensive Tests (`.github/workflows/tests.yaml`)

**Trigger:** Push to main/develop, pull requests
**Duration:** < 30 minutes
**Purpose:** Full test suite execution

Jobs:

- `smoke-tests`: Quick validation (Python 3.10, 3.11, 3.12)
- `unit-tests`: Full unit test suite with coverage
- `integration-tests`: Component integration tests
- `property-tests`: Property-based tests (Hypothesis)
- `regression-tests`: Regression and snapshot tests
- `performance-tests`: Performance threshold validation
- `code-quality`: Linting, type checking, code analysis
- `test-summary`: Combined results and coverage

Test Matrix:

```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
    os: [ubuntu-latest, macos-latest, windows-latest]
```

Coverage Requirements:

- Unit tests: 85%+ coverage
- Integration tests: Combined coverage tracked
- Reports uploaded to Codecov

### 3. Performance Tracking (`.github/workflows/performance-tracking.yaml`)

**Trigger:** Weekly schedule (Monday 00:00 UTC) or manual dispatch
**Duration:** < 30 minutes
**Purpose:** Long-term performance monitoring

Jobs:

- `benchmark-suite`: Full benchmark execution
- `memory-profiling`: Memory usage analysis
- `performance-dashboard`: Dashboard generation

Benchmark Configuration:

```yaml
--benchmark-min-rounds=10
--benchmark-warmup-iterations=3
--benchmark-save=tracking-$(date)
--benchmark-json=results.json
```text

Alerting:

- Creates GitHub issue on threshold violations
- Comments on recent PRs if performance degraded
- Archives results for 90 days (trends) and 365 days (history)

### 4. Workflow Triggers Summary

| Workflow | Trigger | Frequency | Duration |
|----------|---------|-----------|----------|
| Pre-commit | PR opened/updated | Per PR update | < 5 min |
| Tests | Push to main/develop, PR | Per commit | < 30 min |
| Performance | Schedule, Manual | Weekly | < 30 min |

---

## Test Execution Strategy

### Test Categories

#### 1. Smoke Tests

**Purpose:** Fast validation of critical paths
**Marker:** `@pytest.mark.smoke`
**Duration:** < 1 minute
**Coverage:** Basic functionality only

Example:

```python
@pytest.mark.smoke
def test_basic_import():
    """Verify core modules can be imported."""
    from src.performance.cache import CacheManager
    assert CacheManager is not None
```

#### 2. Unit Tests

**Purpose:** Test individual functions/classes
**Marker:** `@pytest.mark.unit`
**Duration:** < 10 minutes
**Coverage:** 85%+ of module code

Execution:

```bash
pytest tests/unit/ -v -m unit --cov=src
```text

#### 3. Integration Tests

**Purpose:** Test component interactions
**Marker:** `@pytest.mark.integration`
**Duration:** < 15 minutes
**Coverage:** Workflow scenarios

Execution:

```bash
pytest tests/integration/ -v -m integration
```

#### 4. Property-Based Tests

**Purpose:** Validate invariants
**Marker:** `@pytest.mark.property`
**Duration:** < 10 minutes
**Coverage:** 74 properties tested

Configuration:

```python
# Hypothesis settings for CI
settings.register_profile("ci", max_examples=1000, deadline=None)
settings.load_profile("ci")
```text

#### 5. Regression Tests

**Purpose:** Prevent known issues from recurring
**Marker:** `@pytest.mark.regression`
**Duration:** < 5 minutes
**Coverage:** 56 regression tests

Includes:

- Known issue tests (25 tests)
- JSON snapshot tests (22 tests)
- Baseline schema validation (9 tests)

#### 6. Performance Tests

**Purpose:** Ensure performance thresholds met
**Marker:** `@pytest.mark.performance` or `@pytest.mark.benchmark`
**Duration:** < 5 minutes (thresholds), ~10 minutes (benchmarks)
**Coverage:** 47 performance tests

Execution:

```bash
# Threshold validation (fast)
pytest tests/performance/test_thresholds.py -v -m performance

# Full benchmarks (slower)
pytest tests/performance/test_benchmarks.py --benchmark-only
```

### Test Execution Order

1. **Smoke tests** - Fail fast if basics broken
2. **Unit tests** - Core functionality validation
3. **Integration tests** - Component interaction
4. **Property tests** - Invariant validation
5. **Regression tests** - Known issue prevention
6. **Performance tests** - Threshold compliance

### Parallel Execution

Tests run in parallel jobs for speed:

```yaml
strategy:
  fail-fast: false
  matrix:
    test-suite: [unit, integration, property, regression, performance]
```text

Benefits:

- Faster feedback (5-10x speedup)
- Independent failure isolation
- Resource optimization

---

## Performance Monitoring

### Performance Thresholds

Defined in `tests/performance/conftest.py`:

```python
PERFORMANCE_THRESHOLDS = {
    # Cache operations (seconds)
    "cache_get": 0.001,              # 1ms
    "cache_set": 0.002,              # 2ms
    "cache_cleanup": 0.1,            # 100ms
    "cache_invalidate": 0.005,       # 5ms

    # Throughput (items/second)
    "cache_ops_per_second": 1000,
    "batch_requests_per_second": 100,
    "parallel_items_per_second": 50,

    # Memory limits (MB)
    "cache_max_size": 100,
    "worker_memory_per_item": 10,
}
```

### Benchmark Tracking

**Frequency:** Weekly (automated) + on-demand
**Retention:**

- Detailed results: 90 days
- Historical data: 365 days

Metrics Tracked:

- Min/Max/Mean/Median latency
- Standard deviation
- Operations per second
- Memory usage
- Throughput

Comparison:

- Against previous run
- Against baseline (main branch)
- Trend analysis over time

### Performance Alerts

Trigger Conditions:

- Threshold violation in performance tests
- Benchmark regression > 10%
- Memory usage exceeds limits

Actions:

- GitHub issue created automatically
- Comment on recent PRs
- Alert in Slack (if configured)

Example Alert:

```markdown
⚠️ Performance Alert: Threshold Violations

Date: 2025-01-27 12:00:00 UTC
Run: 123
Commit: abc123def

## Violations
- Cache get exceeded threshold: 1.2ms > 1.1ms (1ms + 10%)
- Throughput below minimum: 950 ops/sec < 900 ops/sec (1000 - 10%)

## Action Required
1. Review benchmark results
2. Profile slow operations
3. Consider optimization or threshold adjustment
```text

---

## Code Quality Gates

### Quality Checks

All code must pass before merge:

#### 1. Formatting (Black)

```bash
black --check src/ tests/
```

**Configuration:** Default Black style
**Line Length:** 88 characters
**Action:** `continue-on-error: true` (advisory)

#### 2. Import Sorting (isort)

```bash
isort --check-only src/ tests/
```text

**Configuration:** Compatible with Black
**Action:** `continue-on-error: true` (advisory)

#### 3. Linting (Flake8)

```bash
flake8 src/ tests/ --max-line-length=120
```

Ignored Rules:

- E203: Whitespace before ':'
- W503: Line break before binary operator

**Action:** `continue-on-error: true` (advisory)

#### 4. Type Checking (MyPy)

```bash
mypy src/ --ignore-missing-imports
```text

**Configuration:** Non-strict mode
**Action:** `continue-on-error: true` (advisory)

#### 5. Security (Bandit)

```bash
bandit -r src/ -f json
```

**Action:** `continue-on-error: true` (advisory)

### Quality Metrics

Target Metrics:

- Test Coverage: 85%+
- Type Hints: 70%+
- Documentation: All public APIs
- Security Issues: 0 high/critical

---

## Security Scanning

### Dependency Scanning

**Tool:** Safety
**Frequency:** Every PR, daily on main
**Database:** PyUp Safety DB

```bash
safety check --json
```text

**Action:** Advisory only (manual review required)

### Code Scanning

**Tool:** Bandit
**Frequency:** Every PR
**Severity Levels:** Low, Medium, High, Critical

```bash
bandit -r src/ -ll  # Low level and above
```

**Critical Issues:** Block merge
**High Issues:** Require review
**Medium/Low:** Advisory

### Secret Scanning

**Tool:** GitHub Secret Scanning (built-in)
**Scope:** All commits, all branches
**Action:** Automatic alerts, prevent push

---

## Artifact Management

### Artifacts Generated

| Artifact | Retention | Size | Purpose |
|----------|-----------|------|---------|
| Coverage Reports | 7 days | ~10 MB | Coverage analysis |
| Benchmark Results | 90 days | ~5 MB | Performance tracking |
| Benchmark History | 365 days | ~50 MB | Long-term trends |
| Test Reports | 7 days | ~2 MB | Test results |
| Security Scans | 7 days | ~1 MB | Vulnerability reports |
| Performance Dashboard | 365 days | ~500 KB | Performance overview |

### Artifact Access

Via GitHub UI:

1. Go to Actions tab
2. Select workflow run
3. Scroll to "Artifacts" section
4. Download desired artifact

Via CLI:

```bash
gh run download <run-id> -n <artifact-name>
```text

Example:

```bash
gh run download 12345 -n coverage-combined
```

### Artifact Structure

Coverage Report:

```text
coverage-combined/
├── coverage-summary.md
├── htmlcov/
│   ├── index.html
│   └── ...
└── coverage.xml
```

Benchmark Results:

```text
benchmark-results/
├── benchmark-results.json
├── benchmark-histogram.svg
└── .benchmarks/
    └── tracking-20250127-120000/
        └── 0001_*.json
```

---

## Notification Strategy

### GitHub Actions Notifications

Default Behavior:

- Email on first failure
- Email when fixed
- Email if workflow re-run fails

Disable for user:
Settings → Notifications → Actions → Configure

### PR Comments

Automated comments on PRs:

- Pre-commit check summary
- Test coverage report
- Performance comparison
- Security scan results

Example:

```markdown
## Pre-commit Check Results

| Check | Status |
|-------|--------|
| Quick Validation | ✅ success |
| Fast Tests | ✅ success |
| Linting & Formatting | ⚠️ failure |
| Security Scan | ✅ success |

### Next Steps
Some checks failed. Please review the logs.
```text

### Performance Alerts

Triggered on:

- Threshold violations
- Benchmark regressions > 10%
- Memory limit violations

Recipients:

- GitHub issue (labeled: performance, automated)
- Comments on recent open PRs
- Optional: Slack webhook (if configured)

---

## Local Development

### Running Tests Locally

#### Quick Validation

```bash
# Smoke tests
PYTHONPATH=. pytest -v -m smoke --no-cov

# Fast unit tests
PYTHONPATH=. pytest tests/unit/ -v --no-cov
```

#### Full Test Suite

```bash
# All tests with coverage
PYTHONPATH=. pytest -v --cov=src --cov-report=html

# Specific category
PYTHONPATH=. pytest -v -m integration
```text

#### Performance Tests

```bash
# Threshold validation (fast)
PYTHONPATH=. pytest tests/performance/test_thresholds.py -v

# Benchmarks (slower)
PYTHONPATH=. pytest tests/performance/test_benchmarks.py --benchmark-only
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```text

Hooks run automatically:

- Black formatting
- isort import sorting
- Flake8 linting
- Trailing whitespace removal
- YAML validation

### Local CI Simulation

Use `act` to run GitHub Actions locally:

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflow
act -j smoke-tests
act -j unit-tests
```

---

## Troubleshooting

### Common Issues

#### 1. Tests Fail Locally but Pass in CI

**Cause:** Environment differences
**Solution:**

```bash
# Ensure clean environment
uv sync  # or: pip install . --force-reinstall

# Check Python version
python --version  # Should match CI (3.11)

# Set PYTHONPATH
export PYTHONPATH=.
```text

#### 2. Coverage Too Low

**Cause:** Missing test files or markers
**Solution:**

```bash
# Check what's covered
pytest --cov=src --cov-report=term-missing

# Add missing tests to uncovered areas
# Mark tests with appropriate markers
```

#### 3. Performance Tests Fail

**Cause:** Resource contention on local machine
**Solution:**

```bash
# Close background applications
# Run with increased margins
pytest tests/performance/ -v --tb=short

# Check actual vs threshold in output
```text

#### 4. Benchmark Comparison Fails

**Cause:** No baseline exists
**Solution:**

```bash
# Create baseline
pytest tests/performance/test_benchmarks.py \
  --benchmark-only \
  --benchmark-save=baseline

# Then run comparison
pytest tests/performance/test_benchmarks.py \
  --benchmark-only \
  --benchmark-compare=baseline
```

#### 5. Workflow Not Triggering

**Cause:** Path filters or branch restrictions
**Solution:**

```yaml
# Check workflow triggers
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'tests/**'
```text

Verify:

- Changed files match path filters
- Branch is in trigger list
- Workflow file is in `.github/workflows/`

### Debug Mode

Enable debug logging:

In GitHub Actions:

1. Repository Settings → Secrets → Actions
2. Add secret: `ACTIONS_STEP_DEBUG` = `true`
3. Re-run workflow

In pytest:

```bash
pytest -vv --log-cli-level=DEBUG
```

### Getting Help

Resources:

- GitHub Actions Docs: <https://docs.github.com/actions>
- pytest Docs: <https://docs.pytest.org>
- pytest-benchmark: <https://pytest-benchmark.readthedocs.io>
- Hypothesis: <https://hypothesis.readthedocs.io>

Contact:

- File an issue: Project repository issues
- Internal docs: `tests/README.md`
- Performance docs: `tests/performance/README.md`

---

## Best Practices

### 1. Fast Feedback

- Keep smoke tests < 1 minute
- Run unit tests before integration tests
- Use fail-fast strategically

### 2. Resource Efficiency

- Cache pip dependencies
- Use concurrency for independent jobs
- Set appropriate timeouts

### 3. Maintainability

- Use descriptive job names
- Add comments to complex steps
- Keep workflows DRY (use composite actions)

### 4. Security

- Pin action versions with SHA
- Use step-security/harden-runner
- Scan dependencies regularly

### 5. Observability

- Upload artifacts for debugging
- Generate summary reports
- Track metrics over time

---

## Workflow Maintenance

### Regular Tasks

Weekly:

- Review performance tracking results
- Check for workflow deprecation warnings
- Update action versions if security issues

Monthly:

- Review artifact retention policies
- Analyze test execution times
- Optimize slow tests

Quarterly:

- Update Python version matrix
- Review and update thresholds
- Audit security scan results

### Version Updates

Action Updates:

```bash
# Check for updates
gh api repos/{owner}/{repo}/actions/workflows

# Update in workflows
# Always use SHA pinning for security
uses: actions/checkout@<new-sha>  # v4.2.1
```text

Python Version Updates:

```yaml
# Add new Python version to matrix
python-version: ['3.10', '3.11', '3.12', '3.13']
```

---

## Appendix

### A. Performance Threshold Reference

See `tests/performance/conftest.py` for complete list.

### B. Test Marker Reference

| Marker | Purpose | Count |
|--------|---------|-------|
| smoke | Fast validation | ~10 |
| unit | Unit tests | ~300 |
| integration | Integration tests | ~50 |
| property | Property-based | 74 |
| regression | Regression tests | 56 |
| performance | Threshold tests | 16 |
| benchmark | Benchmarks | 31 |

### C. Workflow File Locations

- `.github/workflows/tests.yaml` - Main test suite
- `.github/workflows/pre-commit.yaml` - Fast PR checks
- `.github/workflows/performance-tracking.yaml` - Scheduled benchmarks

### D. Coverage Targets

| Module | Target | Current |
|--------|--------|---------|
| src/performance/ | 90% | 100% ✅ |
| src/util/ | 90% | 96% ✅ |
| src/rendering/ | 85% | 95% ✅ |
| src/cli/ | 85% | 90% ✅ |
| Overall | 85% | ~62% |

---

**Document Version:** 1.0
**Last Review:** 2025-01-27
**Next Review:** 2025-04-27
**Owner:** Development Team
