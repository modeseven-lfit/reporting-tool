<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Test Writing Guide

**Purpose:** Comprehensive guide for writing high-quality, maintainable tests
**Target Audience:** Developers, contributors
**Status:** ✅ Production Ready

---

## Table of Contents

- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Naming Conventions](#naming-conventions)
- [Test Categories](#test-categories)
- [Writing Effective Tests](#writing-effective-tests)
- [Using Fixtures](#using-fixtures)
- [Enhanced Error Messages](#enhanced-error-messages)
- [Assertions](#assertions)
- [Mocking](#mocking)
- [Performance Testing](#performance-testing)
- [Property-Based Testing](#property-based-testing)
- [Common Patterns](#common-patterns)
- [Anti-Patterns](#anti-patterns)
- [Best Practices](#best-practices)
- [Examples](#examples)

---

## Quick Start

### Minimal Test Template

```python
# tests/unit/test_my_feature.py

"""Tests for my_feature module."""

import pytest
from src.my_module import my_feature


def test_my_feature_basic_case():
    """Test my_feature handles basic case correctly."""
    # Arrange
    input_data = "test"

    # Act
    result = my_feature(input_data)

    # Assert
    assert result == "expected_output"
```text

### Test with Fixture

```python
def test_repository_analysis(temp_git_repo):
    """Test repository analysis with fixture."""
    # Arrange - fixture provides repo
    create_test_commits(temp_git_repo, count=5)

    # Act
    result = analyze_repository(temp_git_repo)

    # Assert
    assert result.commit_count == 6  # Initial + 5
    assert result.author_count > 0
```

### Test with Enhanced Errors

```python
def test_git_workflow(temp_git_repo):
    """Test git workflow with enhanced error context."""
    with assert_git_operation("create feature branch", temp_git_repo):
        run_git_command_safe(
            ["git", "checkout", "-b", "feature"],
            cwd=temp_git_repo
        )

    assert_repository_state(
        temp_git_repo,
        expected_branch="feature",
        should_be_clean=True
    )
```text

---

## Test Structure

### AAA Pattern (Arrange-Act-Assert)

Always structure tests in three clear sections:

```python
def test_format_number_thousands():
    """Test that thousands are formatted with K suffix."""
    # Arrange - Set up test data
    number = 5000

    # Act - Execute the code under test
    result = format_number(number)

    # Assert - Verify the outcome
    assert result == "5K"
```

Why AAA:

- ✅ Clear, predictable structure
- ✅ Easy to understand what's being tested
- ✅ Separates setup from verification
- ✅ Makes tests self-documenting

### Given-When-Then (Alternative)

For BDD-style tests:

```python
def test_repository_with_commits():
    """Test that repository analysis counts commits correctly."""
    # Given a repository with 5 commits
    repo = create_repository_with_commits(5)

    # When we analyze the repository
    result = analyze_repository(repo)

    # Then we get the correct commit count
    assert result.commit_count == 5
```text

---

## Naming Conventions

### Test File Names

**Pattern:** `test_<module_name>.py`

Examples:

- ✅ `test_formatting.py` - tests for `src/util/formatting.py`
- ✅ `test_github_api.py` - tests for GitHub API client
- ✅ `test_repository_metrics.py` - tests for repository metrics
- ❌ `formatting_test.py` - doesn't match pytest discovery
- ❌ `test.py` - too generic

Organization:

```

tests/
├── unit/
│   ├── test_formatting.py          # Unit tests
│   ├── test_github_api.py
│   └── test_domain_models.py
├── integration/
│   ├── test_data_pipeline.py       # Integration tests
│   └── test_end_to_end.py
└── performance/
    └── test_benchmarks.py          # Performance tests

```text

### Test Function Names

**Pattern:** `test_<what>_<condition>_<expected>`

Good examples:

```python
# What is tested, under what condition, what's expected
def test_format_number_thousands_returns_k_suffix():
    """Test formatting of thousands."""
    pass

def test_format_number_zero_returns_zero():
    """Test formatting of zero."""
    pass

def test_format_number_negative_preserves_sign():
    """Test formatting preserves negative sign."""
    pass
```

Anti-patterns:

```python
# Too vague
def test_format():  # ❌ What are we testing?
    pass

# Too generic
def test_numbers():  # ❌ What about numbers?
    pass

# Missing context
def test_returns_k():  # ❌ When? Under what conditions?
    pass
```text

### Test Class Names

**Pattern:** `Test<FeatureName>` or `Test<ClassName>`

```python
class TestNumberFormatter:
    """Tests for NumberFormatter class."""

    def test_format_thousands_returns_k_suffix(self):
        """Test thousands formatting."""
        formatter = NumberFormatter()
        assert formatter.format(5000) == "5K"

    def test_format_millions_returns_m_suffix(self):
        """Test millions formatting."""
        formatter = NumberFormatter()
        assert formatter.format(5_000_000) == "5M"
```

When to use classes:

- ✅ Grouping related tests
- ✅ Sharing setup/teardown logic
- ✅ Testing a specific class
- ❌ Don't use for simple function tests

---

## Test Categories

### Unit Tests

**Purpose:** Test individual functions/methods in isolation

**Location:** `tests/unit/`

Characteristics:

- Fast execution (< 100ms per test)
- No external dependencies
- Use mocks for dependencies
- Test single responsibility

Example:

```python
# tests/unit/test_formatting.py

def test_format_number_thousands():
    """Unit test - pure function, no dependencies."""
    result = format_number(5000)
    assert result == "5K"
```text

Marker:

```python
@pytest.mark.unit
def test_format_number():
    pass
```

### Integration Tests

**Purpose:** Test interaction between components

**Location:** `tests/integration/`

Characteristics:

- Slower execution (1-10 seconds)
- May use real dependencies
- Test component integration
- May create temporary resources

Example:

```python
# tests/integration/test_data_pipeline.py

@pytest.mark.integration
def test_repository_analysis_pipeline(temp_git_repo):
    """Integration test - tests multiple components together."""
    # Create real repository
    setup_repository(temp_git_repo)

    # Test full pipeline
    result = run_full_analysis(temp_git_repo)

    # Verify end-to-end behavior
    assert result.is_valid()
    assert result.has_metrics()
```text

### Performance Tests

**Purpose:** Verify performance meets thresholds

**Location:** `tests/performance/`

Characteristics:

- Measure execution time
- Check memory usage
- Verify scalability
- May take longer to run

Example:

```python
# tests/performance/test_benchmarks.py

@pytest.mark.performance
def test_analysis_performance_threshold(temp_git_repo, benchmark):
    """Performance test - verify meets threshold."""
    setup_large_repository(temp_git_repo, commits=1000)

    result = benchmark(analyze_repository, temp_git_repo)

    # Performance assertion
    assert benchmark.stats.mean < 5.0  # 5 seconds max
```

### Property-Based Tests

**Purpose:** Test properties that should always hold

**Location:** `tests/property/`

Example:

```python
from hypothesis import given, strategies as st

@pytest.mark.property
@given(st.integers(min_value=0, max_value=1_000_000))
def test_format_number_always_returns_string(number):
    """Property test - always returns string."""
    result = format_number(number)
    assert isinstance(result, str)
```text

---

## Writing Effective Tests

### 1. Test One Thing

Good:

```python
def test_format_number_thousands():
    """Test thousands formatting specifically."""
    assert format_number(5000) == "5K"

def test_format_number_millions():
    """Test millions formatting specifically."""
    assert format_number(5_000_000) == "5M"
```

Bad:

```python
def test_format_number():
    """Test all formatting - too broad!"""
    assert format_number(5000) == "5K"
    assert format_number(5_000_000) == "5M"
    assert format_number(0) == "0"
    assert format_number(-5000) == "-5K"
    # Hard to debug which assertion failed
```text

### 2. Make Tests Independent

Good:

```python
def test_cache_get(temp_cache):
    """Independent test - creates own data."""
    temp_cache.set("key", "value")
    assert temp_cache.get("key") == "value"

def test_cache_delete(temp_cache):
    """Independent test - creates own data."""
    temp_cache.set("key", "value")
    temp_cache.delete("key")
    assert temp_cache.get("key") is None
```

Bad:

```python
# Shared state between tests - fragile!
cache = {}

def test_cache_set():
    """Depends on clean cache state."""
    cache["key"] = "value"
    assert "key" in cache

def test_cache_delete():
    """Depends on test_cache_set running first!"""
    del cache["key"]  # Fails if previous test didn't run
    assert "key" not in cache
```text

### 3. Use Descriptive Assertions

Good:

```python
def test_repository_has_expected_commits(temp_git_repo):
    """Clear assertion with context."""
    result = analyze_repository(temp_git_repo)

    assert result.commit_count == 10, (
        f"Expected 10 commits, got {result.commit_count}"
    )
```

Better (with enhanced assertions):

```python
def test_repository_has_expected_commits(temp_git_repo):
    """Even clearer with enhanced assertions."""
    result = analyze_repository(temp_git_repo)

    assert_repository_state(
        temp_git_repo,
        expected_commit_count=10,
        should_be_clean=True
    )
    # Automatic detailed error message on failure
```text

### 4. Test Edge Cases

```python
def test_format_number_edge_cases():
    """Test edge cases explicitly."""
    assert format_number(0) == "0"
    assert format_number(-1) == "-1"
    assert format_number(999) == "999"
    assert format_number(1000) == "1K"
    assert format_number(1_000_000) == "1M"
    assert format_number(1_000_000_000) == "1B"

@pytest.mark.parametrize("number,expected", [
    (0, "0"),
    (-1, "-1"),
    (999, "999"),
    (1000, "1K"),
    (1_000_000, "1M"),
])
def test_format_number_parametrized(number, expected):
    """Parametrized edge case testing."""
    assert format_number(number) == expected
```

### 5. Test Error Conditions

```python
def test_divide_by_zero_raises_error():
    """Test that errors are raised appropriately."""
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_invalid_input_raises_value_error():
    """Test validation raises appropriate error."""
    with pytest.raises(ValueError, match="Invalid input"):
        process_data(None)
```text

---

## Using Fixtures

### When to Use Fixtures

Use fixtures for:

- ✅ Common test setup
- ✅ Resource creation/cleanup
- ✅ Test data
- ✅ Mocking setup

Don't use fixtures for:

- ❌ Simple values (just use variables)
- ❌ Test-specific setup (put in test)

### Basic Fixture

```python
@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {
        "name": "Test",
        "count": 10,
        "enabled": True
    }

def test_process_data(sample_data):
    """Test using fixture."""
    result = process(sample_data)
    assert result.is_valid()
```

### Fixture with Setup/Teardown

```python
@pytest.fixture
def database_connection():
    """Provide database connection with cleanup."""
    # Setup
    conn = create_connection()

    # Provide to test
    yield conn

    # Teardown (always runs)
    conn.close()

def test_database_query(database_connection):
    """Test using database fixture."""
    result = database_connection.query("SELECT 1")
    assert result is not None
```text

### Fixture Scope

```python
# Function scope (default) - runs for each test
@pytest.fixture(scope="function")
def temp_file():
    """New temp file for each test."""
    path = create_temp_file()
    yield path
    delete_temp_file(path)

# Module scope - runs once per module
@pytest.fixture(scope="module")
def expensive_resource():
    """Shared resource for all tests in module."""
    resource = create_expensive_resource()
    yield resource
    cleanup_resource(resource)

# Session scope - runs once per test session
@pytest.fixture(scope="session")
def database():
    """Shared database for entire test session."""
    db = setup_database()
    yield db
    teardown_database(db)
```

### Parametrized Fixtures

```python
@pytest.fixture(params=[10, 100, 1000])
def repository_with_commits(request, tmp_path):
    """Repository with varying commit counts."""
    repo = create_repository(tmp_path)
    create_commits(repo, count=request.param)
    return repo

def test_analysis_scales(repository_with_commits):
    """Test runs 3 times with different commit counts."""
    result = analyze(repository_with_commits)
    assert result.is_valid()
```text

---

## Enhanced Error Messages

### Use Context Managers

```python
def test_git_operations(temp_git_repo):
    """Test with enhanced error context."""
    with assert_git_operation("create branch", temp_git_repo):
        run_git_command_safe(
            ["git", "checkout", "-b", "feature"],
            cwd=temp_git_repo
        )

    with assert_git_operation("add commits", temp_git_repo):
        create_file(temp_git_repo / "file.txt")
        run_git_command_safe(["git", "add", "."], cwd=temp_git_repo)
        run_git_command_safe(
            ["git", "commit", "-m", "Add file"],
            cwd=temp_git_repo
        )
    # Automatic detailed error messages on failure
```

### Use Rich Assertions

```python
def test_repository_state(temp_git_repo):
    """Test with rich state assertions."""
    create_test_commits(temp_git_repo, 5)

    assert_repository_state(
        temp_git_repo,
        expected_branch="main",
        expected_commit_count=6,
        should_be_clean=True
    )
    # On failure, shows:
    # - Which checks failed
    # - Current repository state
    # - Git log
```text

### Save Artifacts on Failure

```python
def test_complex_workflow(temp_git_repo):
    """Test with automatic artifact saving."""
    with assert_test_operation(
        "complete analysis workflow",
        save_artifacts_on_failure=True,
        artifact_path=temp_git_repo
    ):
        result = run_complex_analysis(temp_git_repo)
        validate_results(result)
    # On failure, automatically saves debug info
```

---

## Assertions

### Built-in Assertions

```python
# Equality
assert result == expected
assert result != unexpected

# Identity
assert result is None
assert result is not None

# Membership
assert item in collection
assert item not in collection

# Type checking
assert isinstance(result, str)
assert not isinstance(result, int)

# Boolean
assert condition
assert not condition

# Exceptions
with pytest.raises(ValueError):
    raise_error()
```text

### Custom Assertions

```python
# Use from test_utils
from test_utils import (
    assert_repository_state,
    assert_command_success,
    assert_no_error_logs,
)

def test_with_custom_assertions(temp_git_repo):
    """Use custom assertions for better errors."""
    result = run_git_command_safe(["git", "status"], cwd=temp_git_repo)
    assert_command_success(result, "git status")
```

### Assertion Messages

```python
# Good - provides context
assert len(results) == 10, (
    f"Expected 10 results, got {len(results)}"
)

# Better - use f-strings for detail
assert result.success, (
    f"Operation failed: {result.error}\n"
    f"Exit code: {result.exit_code}\n"
    f"Output: {result.output}"
)
```text

---

## Mocking

### When to Mock

Mock when:

- ✅ Testing external API calls
- ✅ Testing slow operations
- ✅ Testing error conditions
- ✅ Isolating units under test

Don't mock when:

- ❌ Testing integration
- ❌ Mock makes test too complex
- ❌ Real implementation is simple/fast

### Basic Mocking

```python
from unittest.mock import Mock, patch

def test_api_call_with_mock():
    """Test API call with mocked response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}

    with patch('requests.get', return_value=mock_response):
        result = fetch_data("http://api.example.com")
        assert result == {"data": "test"}
```

### Mock with pytest-mock

```python
def test_with_pytest_mock(mocker):
    """Test with pytest-mock fixture."""
    mock_api = mocker.patch('src.api.client.fetch')
    mock_api.return_value = {"data": "test"}

    result = process_api_data()

    assert result is not None
    mock_api.assert_called_once()
```text

### Mock Side Effects

```python
def test_retry_on_failure(mocker):
    """Test retry logic with mock side effects."""
    mock_api = mocker.patch('src.api.client.fetch')

    # First call fails, second succeeds
    mock_api.side_effect = [
        Exception("Network error"),
        {"data": "success"}
    ]

    result = fetch_with_retry()

    assert result == {"data": "success"}
    assert mock_api.call_count == 2
```

---

## Performance Testing

### Basic Benchmark

```python
@pytest.mark.performance
def test_analysis_performance(temp_git_repo, benchmark):
    """Benchmark repository analysis."""
    setup_repository(temp_git_repo, commits=100)

    result = benchmark(analyze_repository, temp_git_repo)

    # Benchmark automatically captures timing stats
    assert result is not None
```text

### Performance Thresholds

```python
from test_utils import assert_performance_threshold

@pytest.mark.performance
def test_analysis_meets_threshold(temp_git_repo):
    """Test analysis completes within threshold."""
    setup_repository(temp_git_repo, commits=1000)

    assert_performance_threshold(
        lambda: analyze_repository(temp_git_repo),
        max_seconds=5.0,
        description="analyze 1000 commits"
    )
```

---

## Property-Based Testing

### Basic Property Test

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0))
def test_format_number_always_returns_string(number):
    """Property: format_number always returns string."""
    result = format_number(number)
    assert isinstance(result, str)

@given(st.text())
def test_parse_then_format_is_idempotent(text):
    """Property: parse then format returns original."""
    parsed = parse(text)
    formatted = format(parsed)
    assert parse(formatted) == parsed
```text

### Composite Strategies

```python
from hypothesis import given
from hypothesis.strategies import composite, integers, lists

@composite
def repository_data(draw):
    """Generate realistic repository data."""
    return {
        "commits": draw(integers(min_value=1, max_value=10000)),
        "authors": draw(integers(min_value=1, max_value=100)),
        "files": draw(integers(min_value=1, max_value=1000)),
    }

@given(repository_data())
def test_analysis_handles_various_sizes(repo_data):
    """Test analysis with generated data."""
    result = analyze(repo_data)
    assert result.is_valid()
```

---

## Common Patterns

### Pattern: Setup-Exercise-Verify

```python
def test_cache_operations():
    """Test cache with clear phases."""
    # Setup
    cache = Cache()

    # Exercise
    cache.set("key", "value")
    result = cache.get("key")

    # Verify
    assert result == "value"
```text

### Pattern: Test Fixtures for Shared Setup

```python
@pytest.fixture
def configured_analyzer():
    """Provide pre-configured analyzer."""
    analyzer = Analyzer()
    analyzer.configure(timeout=30, verbose=False)
    return analyzer

def test_analyze_with_fixture(configured_analyzer):
    """Test using shared setup."""
    result = configured_analyzer.analyze(data)
    assert result.is_valid()
```

### Pattern: Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    (0, "0"),
    (999, "999"),
    (1000, "1K"),
    (1_000_000, "1M"),
])
def test_format_number_cases(input, expected):
    """Test multiple cases efficiently."""
    assert format_number(input) == expected
```text

### Pattern: Test Error Paths

```python
def test_handles_missing_file():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path")

def test_validates_input():
    """Test input validation."""
    with pytest.raises(ValueError, match="Invalid"):
        process_data(None)
```

---

## Anti-Patterns

### ❌ Anti-Pattern: Tests That Don't Test

```python
# Bad - just exercises code, no verification
def test_analyze():
    analyze_repository(repo)
    # No assertions!
```text

### ❌ Anti-Pattern: Tests That Test Too Much

```python
# Bad - tests entire system in one test
def test_everything():
    setup_database()
    load_config()
    process_data()
    generate_report()
    send_email()
    # Too broad, hard to debug failures
```

### ❌ Anti-Pattern: Order-Dependent Tests

```python
# Bad - test depends on previous test
def test_step_1():
    global_state["key"] = "value"

def test_step_2():
    # Breaks if test_step_1 doesn't run first
    assert global_state["key"] == "value"
```text

### ❌ Anti-Pattern: Ignoring Test Failures

```python
# Bad - hiding failures
def test_unreliable():
    try:
        flaky_operation()
    except Exception:
        pass  # Ignoring failures!

# Good - use @mark_flaky instead
@mark_flaky(reason="Known timing issue")
def test_unreliable():
    flaky_operation()
```

### ❌ Anti-Pattern: Testing Implementation Details

```python
# Bad - tests internal implementation
def test_internal_cache():
    analyzer = Analyzer()
    assert analyzer._cache is not None  # Testing private attribute

# Good - test behavior
def test_analyzer_caches_results():
    analyzer = Analyzer()
    result1 = analyzer.analyze(data)
    result2 = analyzer.analyze(data)
    # Test observable behavior, not internals
    assert result1 == result2
```text

---

## Best Practices

### 1. Keep Tests Fast

- ✅ Unit tests: < 100ms each
- ✅ Integration tests: < 10s each
- ✅ Use mocks for slow operations
- ✅ Use fixtures to share expensive setup

### 2. Keep Tests Independent

- ✅ No shared mutable state
- ✅ Each test can run alone
- ✅ Tests can run in any order
- ✅ Use fixtures for setup

### 3. Keep Tests Readable

- ✅ Clear naming
- ✅ Good documentation
- ✅ Obvious assertions
- ✅ Minimal complexity

### 4. Keep Tests Maintainable

- ✅ Don't repeat yourself (use fixtures)
- ✅ Update tests with code
- ✅ Delete obsolete tests
- ✅ Use helper functions

### 5. Use Test Markers

```python
@pytest.mark.slow
@pytest.mark.integration
def test_full_analysis(temp_git_repo):
    """Mark tests for selective execution."""
    pass
```

---

## Examples

### Complete Example: Unit Test

```python
# tests/unit/test_formatting.py

"""Unit tests for formatting utilities."""

import pytest
from src.util.formatting import format_number


class TestFormatNumber:
    """Tests for format_number function."""

    def test_format_zero_returns_zero(self):
        """Test that zero is formatted as '0'."""
        assert format_number(0) == "0"

    def test_format_hundreds_returns_number(self):
        """Test that hundreds are returned as-is."""
        assert format_number(500) == "500"

    def test_format_thousands_returns_k_suffix(self):
        """Test that thousands use K suffix."""
        assert format_number(5000) == "5K"

    def test_format_millions_returns_m_suffix(self):
        """Test that millions use M suffix."""
        assert format_number(5_000_000) == "5M"

    def test_format_negative_preserves_sign(self):
        """Test that negative numbers preserve sign."""
        assert format_number(-5000) == "-5K"

    @pytest.mark.parametrize("number,expected", [
        (0, "0"),
        (1, "1"),
        (999, "999"),
        (1000, "1K"),
        (1500, "1.5K"),
        (1_000_000, "1M"),
        (-5000, "-5K"),
    ])
    def test_format_number_various_cases(self, number, expected):
        """Test various formatting cases."""
        assert format_number(number) == expected
```text

### Complete Example: Integration Test

```python
# tests/integration/test_repository_analysis.py

"""Integration tests for repository analysis."""

import pytest
from test_utils import (
    assert_repository_state,
    assert_git_operation,
    run_git_command_safe,
)


@pytest.mark.integration
class TestRepositoryAnalysis:
    """Integration tests for full repository analysis."""

    def test_analyze_simple_repository(self, temp_git_repo):
        """Test analysis of simple repository."""
        # Arrange
        with assert_git_operation("setup test commits", temp_git_repo):
            for i in range(5):
                file_path = temp_git_repo / f"file{i}.txt"
                file_path.write_text(f"content {i}")
                run_git_command_safe(["git", "add", "."], cwd=temp_git_repo)
                run_git_command_safe(
                    ["git", "commit", "-m", f"Commit {i}"],
                    cwd=temp_git_repo
                )

        # Act
        result = analyze_repository(temp_git_repo)

        # Assert
        assert result.commit_count == 6  # Initial + 5
        assert result.file_count > 0
        assert result.author_count == 1

        # Verify final state
        assert_repository_state(
            temp_git_repo,
            expected_branch="main",
            expected_commit_count=6,
            should_be_clean=True
        )

    def test_analyze_with_multiple_authors(self, temp_git_repo):
        """Test analysis with multiple authors."""
        # Arrange
        authors = [
            ("Alice", "alice@example.com"),
            ("Bob", "bob@example.com"),
        ]

        for name, email in authors:
            with assert_git_operation(f"create commit by {name}", temp_git_repo):
                # Set author
                run_git_command_safe(
                    ["git", "config", "user.name", name],
                    cwd=temp_git_repo
                )
                run_git_command_safe(
                    ["git", "config", "user.email", email],
                    cwd=temp_git_repo
                )

                # Create commit
                file_path = temp_git_repo / f"{name}.txt"
                file_path.write_text(f"By {name}")
                run_git_command_safe(["git", "add", "."], cwd=temp_git_repo)
                run_git_command_safe(
                    ["git", "commit", "-m", f"By {name}"],
                    cwd=temp_git_repo
                )

        # Act
        result = analyze_repository(temp_git_repo)

        # Assert
        assert result.author_count == 2
        assert "Alice" in result.authors
        assert "Bob" in result.authors
```

---

## See Also

- [Test Prerequisites](TEST_PREREQUISITES.md)
- [Enhanced Error Messages Guide](ENHANCED_ERRORS_GUIDE.md)
- [Testing Guide](../TESTING_GUIDE.md)
- [Test Reliability Plan](../phase14/TEST_RELIABILITY_PLAN.md)

---

**Last Updated:** 2025-01-05
**Maintainer:** Test Infrastructure Team
**Status:** ✅ Production Ready
