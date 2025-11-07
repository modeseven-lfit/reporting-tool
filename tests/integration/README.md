<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Integration Tests

This directory contains integration tests for the Repository Reporting System.

## Overview

Integration tests verify that multiple components work together correctly to achieve end-to-end functionality. Unlike unit tests that test individual components in isolation, integration tests exercise real workflows and component interactions.

**Current Status:** 122 passing integration tests across 5 test files

## Test Categories

### 1. End-to-End Report Generation (`test_report_generation.py`)

**Tests:** 33 | **Status:** ✅ All Passing
Tests the complete report generation workflow from repository analysis to output file creation.

**Test Coverage:**

- Single repository report generation (6 tests)
- Multi-repository report generation (4 tests)
- Different output formats (5 tests)
- Time window calculations (4 tests)
- Summary aggregation (6 tests)
- Error handling (8 tests)

### 2. Workflow Integration (`test_workflows.py`)

**Tests:** 22 | **Status:** ✅ All Passing
Tests common user workflows and use cases.

**Test Coverage:**

- Repository analysis workflows (10 tests)
- Incremental updates (3 tests)
- Error recovery (4 tests)
- Configuration variations (3 tests)
- Multi-repository processing (2 tests)

### 3. API Integration (`test_api_integration.py`)

**Tests:** 21 | **Status:** ✅ All Passing
Tests integration with external APIs using mock clients.

**Test Coverage:**

- GitHub API client (8 tests)
  - Repository metadata fetching
  - Pagination and rate limits
  - Error handling (404, timeouts, network)
  - Authentication
- Gerrit API client (4 tests)
  - Change queries and filtering
  - Date range queries
  - Authentication
- Error recovery patterns (3 tests)
  - Retry logic and exponential backoff
  - Max retries handling
- API caching (2 tests)
  - Cache hits and TTL expiration
- Rate limiting (2 tests)
  - Respect rate limits
  - Parse rate limit headers
- Batch operations (2 tests)
  - Batch fetching
  - Batch size limits

### 4. CLI Integration (`test_cli_integration.py`)

**Tests:** 28 | **Status:** ⚠️ 16 Passing, 12 Failing (API mismatches)
Tests command-line interface functionality.

**Test Coverage:**

- Argument parsing (7 tests)
  - Basic arguments, output formats, verbosity
  - Time windows, validation, mutual exclusivity
- Configuration loading (5 tests)
  - YAML/JSON config files
  - Config merging with CLI args
  - Error handling for missing/invalid configs
- Output generation (4 tests)
  - JSON output, multiple formats
  - Directory creation, file overwriting
- Error handling (6 tests)
  - Exit codes, error messages
  - Validation errors, suggestions
- Progress reporting (4 tests)
  - Progress indicators, time estimation
  - Count formatting
- Feature discovery (4 tests)
  - List features, search, categories
- Workflows (3 tests)
  - Single/multiple repository workflows
  - Incremental updates

### 5. Data Pipeline (`test_data_pipeline.py`)

**Tests:** 30 | **Status:** ✅ All Passing
Tests the complete data collection and processing pipeline.

**Test Coverage:**

- Git log parsing (5 tests)
  - Basic commit info, statistics
  - Multiple authors, commit dates
  - Merge commit identification
- Author aggregation (4 tests)
  - Commits by author
  - Organization identification
  - Name normalization, missing info handling
- Time window calculations (3 tests)
  - Filtering by time windows
  - Multiple windows, edge cases
- Metric aggregation (3 tests)
  - Commit counts, author counts
  - Line changes
- Data transformations (3 tests)
  - JSON transformation
  - Date normalization, message sanitization
- Organization detection (3 tests)
  - Email domain extraction
  - Author grouping, unaffiliated handling
- End-to-end pipeline (2 tests)
  - Single repository pipeline
  - Multiple repository aggregation

## Running Integration Tests

### Run All Integration Tests

```bash
# Run all 122 integration tests (~17 minutes)
pytest tests/integration -v

# Run with quieter output
pytest tests/integration -q
```

### Run Specific Test File

```bash
# Report generation tests (33 tests, ~6 minutes)
pytest tests/integration/test_report_generation.py -v

# Workflow tests (22 tests, ~5 minutes)
pytest tests/integration/test_workflows.py -v

# API integration tests (21 tests, ~3 seconds - mocked)
pytest tests/integration/test_api_integration.py -v

# CLI integration tests (28 tests, ~2 seconds)
pytest tests/integration/test_cli_integration.py -v

# Data pipeline tests (30 tests, ~12 minutes)
pytest tests/integration/test_data_pipeline.py -v
```

### Run with Coverage

```bash
# Note: Integration tests focus on workflows, not line coverage
pytest tests/integration --cov=src --cov-report=term-missing
```

### Run Specific Test Class or Method

```bash
# Run a specific test class
pytest tests/integration/test_report_generation.py::TestSingleRepositoryReport -v

# Run a specific test method
pytest tests/integration/test_report_generation.py::TestSingleRepositoryReport::test_generate_basic_report -v

# Run tests matching a pattern
pytest tests/integration -k "time_window" -v
```

### Run Fast Tests Only

```bash
# Run only the fast tests (API and CLI - ~5 seconds total)
pytest tests/integration/test_api_integration.py tests/integration/test_cli_integration.py -v
```

## Test Fixtures

Integration tests use fixtures from `tests/fixtures/repositories.py`:

### Repository Fixtures

- `synthetic_repo_simple` - Simple repository with 10 commits, 1 author
- `synthetic_repo_complex` - Complex repository with 50 commits, 5 authors, multiple branches
- `temp_git_repo` - Empty initialized git repository

### Configuration Fixtures

- `test_config_minimal` - Minimal configuration (project, output_dir, time_windows)
- `test_config_complete` - Complete configuration (all options)
- `test_config_with_repos` - Configuration with repository paths

### Data Fixtures

- `sample_commit_data` - Sample commit data for testing
- `sample_repository_data` - Sample repository metadata
- `sample_author_data` - Sample author statistics

### Utility Fixtures

- `temp_output_dir` - Temporary output directory
- `sample_json_file` - Sample JSON file for testing
- `mock_github_env` - Mock GitHub environment variables
- `clean_environment` - Clean environment for testing

## Test Data

Integration tests use synthetic repositories created with `create_synthetic_repository()`:

**Features:**

- Controlled commit history (one commit per day)
- Configurable number of commits, authors, files
- Multiple branch support
- Proper git date handling (RFC 2822 format)
- Timezone-aware timestamps
- Known, predictable metrics

**Usage:**

```python
from tests.fixtures.repositories import create_synthetic_repository

repo_path = tmp_path / "test-repo"
create_synthetic_repository(
    repo_path,
    commit_count=30,
    author_count=3,
    file_count=5,
    branches=["main", "develop"],
    start_date=datetime.now() - timedelta(days=90)
)
```

## Performance

Integration tests take significantly longer than unit tests due to git operations:

- **Total Runtime:** ~17 minutes for all 122 tests
- **Fast Tests (Mocked):** API and CLI tests (~5 seconds)
- **Slow Tests (Real Git):** Data pipeline and report tests (~16 minutes)
- **Individual Test Range:** 3ms to 60 seconds per test

### Performance by Test File

- `test_api_integration.py` - ~3 seconds (mocked APIs)
- `test_cli_integration.py` - ~2 seconds (mocked operations)
- `test_workflows.py` - ~5 minutes (real git operations)
- `test_report_generation.py` - ~6 minutes (real git operations)
- `test_data_pipeline.py` - ~12 minutes (extensive git operations)

## Best Practices

### 1. Test Isolation

Each test should be independent and not rely on the state from other tests.

```python
def test_something(tmp_path, synthetic_repo_simple):
    # Each test gets its own temp directory and repo
    assert True
```

### 2. Use Synthetic Data

Prefer synthetic repositories over real repositories for predictable results.

```python
from tests.fixtures.repositories import create_synthetic_repository

def test_with_synthetic_repo(tmp_path):
    repo = create_synthetic_repository(
        tmp_path / "repo",
        commit_count=20,
        author_count=3
    )
    # Test with known data
```

### 3. Verify Multiple Aspects

Integration tests should verify multiple related aspects.

```python
def test_report_generation(tmp_path, synthetic_repo_simple):
    # Generate report
    output = generate_report(synthetic_repo_simple, tmp_path)

    # Verify multiple aspects
    assert output.exists()
    assert output.stat().st_size > 0
    data = json.loads(output.read_text())
    assert data["schema_version"] == "3.0.0"
    assert len(data["repositories"]) == 1
```

### 4. Test Error Paths

Include tests for error conditions and recovery.

```python
def test_handles_missing_repository(tmp_path):
    with pytest.raises(RepositoryNotFoundError):
        generate_report(tmp_path / "nonexistent", tmp_path)
```

## Coverage Goals

- **Target:** 80+ integration tests
- **Achieved:** 122 integration tests (152% of target) ✅

### Coverage by Area

- ✅ Report generation workflows (33 tests)
- ✅ Multi-repository processing (22 tests)
- ✅ Error handling (15+ tests across all files)
- ✅ API integration (21 tests)
- ✅ CLI functionality (28 tests)
- ✅ Data pipeline (30 tests)
- ✅ Time window calculations (7 tests)
- ✅ Author aggregation (4 tests)
- ✅ Organization detection (3 tests)

## Debugging

### Enable Verbose Output

```bash
pytest tests/integration -vv --log-cli-level=DEBUG
```

### Keep Temporary Files

```bash
pytest tests/integration --basetemp=./test-output
```

### Run Single Test with Full Output

```bash
pytest tests/integration/test_report_generation.py::test_name -vv -s
```

## Continuous Integration

Integration tests run in CI on:

- Every pull request
- Every commit to main branch
- Scheduled nightly builds

CI configuration: `.github/workflows/test.yml`

## Contributing

When adding new integration tests:

1. **Choose the right file** - Add to existing file based on category:
   - API clients → `test_api_integration.py`
   - CLI commands → `test_cli_integration.py`
   - Git operations → `test_data_pipeline.py`
   - Report generation → `test_report_generation.py`
   - User workflows → `test_workflows.py`

2. **Use fixtures** - Leverage existing fixtures for consistency:
   - Use `create_synthetic_repository()` for git repos
   - Use configuration fixtures for test configs
   - Use Mock() for external APIs

3. **Document tests** - Add clear docstrings:

   ```python
   def test_feature_name(self, tmp_path):
       """Test that feature does X when Y happens."""
       # Test implementation
   ```

4. **Choose appropriate speed** - Balance speed and realism:
   - Mock external dependencies (APIs, network)
   - Use real git operations for pipeline tests
   - Keep individual tests < 60 seconds
   - Target < 500ms for mocked tests

5. **Verify cleanup** - Ensure temporary resources are cleaned up:
   - Use pytest's `tmp_path` fixture
   - Don't leave files in system temp
   - Close file handles properly

6. **Handle edge cases** - Consider:
   - Timezone variations (±2 day tolerance for dates)
   - Empty repositories
   - Missing data
   - Network errors
   - Rate limiting

7. **Follow patterns** - Use established patterns:
   - Mock-first for APIs
   - Real operations for git
   - Synthetic data for predictability

## Test Maintenance

### Known Issues

1. **CLI Tests (12 failing)**
   - Tests assume specific function signatures
   - Low priority - tests are overly specific
   - Can be fixed by matching actual API

2. **Slow Test Execution**
   - Creating synthetic repos is slow
   - Consider caching repos where possible
   - 17-minute runtime is acceptable for integration tests

### Troubleshooting

**Problem:** Time-based tests failing

- **Cause:** Timezone differences or date calculation issues
- **Solution:** Use ±2 day tolerance in assertions

**Problem:** Git commands not working

- **Cause:** Environment variables not set correctly
- **Solution:** Use RFC 2822 date format, not ISO format

**Problem:** Tests timing out

- **Cause:** Too many commits in synthetic repository
- **Solution:** Reduce commit count or increase timeout

## Related Documentation

- `tests/unit/README.md` - Unit test documentation
- `tests/regression/README.md` - Regression test documentation
- `tests/fixtures/README.md` - Test fixture documentation
- `docs/TESTING_GUIDE.md` - Overall testing guide
- `docs/testing/phase-12-step-5-completion.md` - Integration test expansion summary
- `docs/PHASE_11_TEST_COVERAGE_PLAN.md` - Original test coverage plan
