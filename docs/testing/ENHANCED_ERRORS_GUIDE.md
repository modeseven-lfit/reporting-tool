<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Enhanced Error Messages - Quick Reference Guide

**Purpose:** Improve test failure debugging with rich assertions and automatic diagnostics
**Phase:** 14, Step 3, Phase 4
**Status:** ✅ Production Ready

---

## Quick Start

### Import Enhanced Utilities

```python
from test_utils import (
    # Rich assertions
    assert_repository_state,
    assert_command_success,
    assert_no_error_logs,

    # Context managers
    assert_git_operation,
    assert_test_operation,

    # Artifact saving
    save_test_artifacts,

    # Git utilities
    get_git_status,
    get_git_log,
    get_repository_info,
)
```text

All utilities are also auto-imported via `conftest.py` and available in all tests.

---

## Rich Assertions

### `assert_repository_state()` - Validate Repository State

**Best for:** Checking repository state after operations

```python
# Example: Validate state after creating commits
def test_create_commits(temp_git_repo):
    create_test_commits(temp_git_repo, count=5)

    assert_repository_state(
        temp_git_repo,
        expected_branch="main",
        expected_commit_count=6,  # Initial + 5 new
        should_be_clean=True
    )
```

On failure, you get:

- ✅ List of which specific checks failed
- ✅ Current repository state (JSON)
- ✅ Recent git log for context
- ✅ Working directory status

Parameters:

- `repo_path` - Path to repository
- `expected_branch` - Expected current branch (optional)
- `expected_commit_count` - Expected number of commits (optional)
- `should_be_clean` - Whether working directory should be clean (optional)
- `custom_checks` - Dict of custom checks (optional)

---

### `assert_command_success()` - Validate Command Execution

**Best for:** Checking subprocess commands succeeded

```python
# Example: Validate git command output
def test_git_operations(temp_git_repo):
    result = run_git_command_safe(
        ["git", "log", "--oneline"],
        cwd=temp_git_repo
    )

    assert_command_success(
        result,
        operation="git log",
        expected_output="Initial commit"
    )
```text

On failure, you get:

- ✅ Operation description
- ✅ Return code
- ✅ Full command arguments
- ✅ Stdout and stderr output
- ✅ Expected vs actual output comparison

Parameters:

- `result` - subprocess.CompletedProcess object
- `operation` - Description of operation
- `expected_output` - Substring that should be in stdout (optional)

---

### `assert_no_error_logs()` - Validate Log Output

**Best for:** Checking logs don't contain errors

```python
# Example: Validate clean execution
def test_clean_execution(temp_git_repo):
    log_output = run_analysis(temp_git_repo)

    assert_no_error_logs(
        log_output,
        context="during repository analysis"
    )
```

On failure, you get:

- ✅ All ERROR lines extracted
- ✅ Full log output
- ✅ Context description

Parameters:

- `log_output` - Log output string to check
- `context` - Optional description of when logs were generated

---

## Context Managers

### `assert_git_operation()` - Enhanced Git Operation Errors

**Best for:** Wrapping git command sequences

```python
# Example: Provide context for git operations
def test_branch_workflow(temp_git_repo):
    with assert_git_operation("create feature branch", temp_git_repo):
        run_git_command_safe(
            ["git", "checkout", "-b", "feature"],
            cwd=temp_git_repo
        )

    with assert_git_operation("add commits to feature", temp_git_repo):
        create_file(temp_git_repo / "feature.txt")
        run_git_command_safe(["git", "add", "."], cwd=temp_git_repo)
        run_git_command_safe(
            ["git", "commit", "-m", "Add feature"],
            cwd=temp_git_repo
        )
```text

On failure, you get:

- ✅ Operation name (your description)
- ✅ Error type and message
- ✅ Current working directory
- ✅ Repository information (JSON)
- ✅ Git status output
- ✅ Recent git log

Parameters:

- `operation_name` - Description of what you're doing
- `repo_path` - Path to repository (optional, but recommended)

---

### `assert_test_operation()` - Enhanced Test Errors + Artifacts

**Best for:** Integration tests, complex workflows

```python
# Example: Integration test with artifact saving
def test_full_workflow(temp_git_repo):
    with assert_test_operation(
        "complete repository analysis workflow",
        save_artifacts_on_failure=True,
        artifact_path=temp_git_repo
    ):
        # Step 1: Analyze
        result = analyze_repository(temp_git_repo)

        # Step 2: Validate
        validate_metrics(result)

        # Step 3: Generate report
        report = generate_report(result)
        assert report is not None
```

On failure, you get:

- ✅ Operation description
- ✅ Error type and message
- ✅ Automatically saved artifacts (if enabled)
- ✅ Path to artifact directory

Parameters:

- `operation_name` - Description of operation
- `save_artifacts_on_failure` - Whether to save debugging artifacts
- `artifact_path` - Path to use for git info in artifacts (optional)

---

## Artifact Saving

### `save_test_artifacts()` - Manual Artifact Saving

**Best for:** Custom failure handling, non-standard scenarios

```python
# Example: Save artifacts on custom condition
def test_complex_scenario(temp_git_repo):
    try:
        result = complex_operation(temp_git_repo)

        if not validate(result):
            # Custom failure - save artifacts manually
            artifact_dir = save_test_artifacts(
                test_name="test_complex_scenario",
                error_message="Validation failed",
                repo_path=temp_git_repo,
                additional_info={
                    "result": result,
                    "validation_errors": get_errors()
                }
            )
            pytest.fail(f"Validation failed. Artifacts: {artifact_dir}")

    except Exception as e:
        artifact_dir = save_test_artifacts(
            test_name="test_complex_scenario",
            error_message=str(e),
            repo_path=temp_git_repo
        )
        raise AssertionError(f"Test failed. Artifacts: {artifact_dir}") from e
```text

Artifacts saved:

- ✅ `error.txt` - Error message and traceback
- ✅ `git_log.txt` - Recent commits (if repo provided)
- ✅ `git_status.txt` - Working directory status
- ✅ `repo_info.json` - Repository state
- ✅ `additional_info.json` - Custom metadata
- ✅ `environment.json` - Python version, env vars, cwd

Parameters:

- `test_name` - Name of the test
- `error_message` - Error message from failure
- `repo_path` - Path to repository (optional)
- `additional_info` - Dict of custom debug data (optional)

**Returns:** Path to artifact directory (timestamped and unique)

---

## Git Information Utilities

### `get_git_status()` - Get Repository Status

```python
status = get_git_status(repo_path)
# Returns porcelain format git status string
```

### `get_git_log()` - Get Recent Commits

```python
log = get_git_log(repo_path, max_commits=10)
# Returns formatted git log string
```text

### `get_repository_info()` - Get Comprehensive State

```python
info = get_repository_info(repo_path)
# Returns dict with:
# {
#   "path": str,
#   "exists": bool,
#   "branch": str,
#   "commit_count": int,
#   "working_dir_clean": bool,
#   "status": str
# }
```

---

## Usage Patterns

### Pattern 1: Simple State Validation

```python
def test_simple_validation(temp_git_repo):
    # Perform operation
    create_commits(temp_git_repo, 3)

    # Validate with rich assertion
    assert_repository_state(
        temp_git_repo,
        expected_commit_count=4,
        should_be_clean=True
    )
```text

### Pattern 2: Git Operation Sequences

```python
def test_git_workflow(temp_git_repo):
    with assert_git_operation("setup branches", temp_git_repo):
        run_git_command_safe(["git", "checkout", "-b", "dev"], cwd=temp_git_repo)
        create_file(temp_git_repo / "dev.txt")
        run_git_command_safe(["git", "add", "."], cwd=temp_git_repo)
        run_git_command_safe(["git", "commit", "-m", "Dev"], cwd=temp_git_repo)
```

### Pattern 3: Integration Tests with Artifacts

```python
def test_integration(temp_git_repo):
    with assert_test_operation(
        "full integration test",
        save_artifacts_on_failure=True,
        artifact_path=temp_git_repo
    ):
        step1_result = perform_step1(temp_git_repo)
        step2_result = perform_step2(step1_result)
        final_result = perform_step3(step2_result)

        assert final_result.success
```text

### Pattern 4: Nested Context Managers

```python
def test_nested_operations(temp_git_repo):
    with assert_test_operation("outer workflow"):
        with assert_git_operation("inner git ops", temp_git_repo):
            perform_git_operations()

        with assert_git_operation("more git ops", temp_git_repo):
            perform_more_operations()
```

---

## Best Practices

### Operation Names

✅ **Good:**

- "create feature branch for user-auth"
- "merge develop into main"
- "analyze repository time windows"

❌ **Bad:**

- "git stuff"
- "operations"
- "test"

**Rule:** Be specific, use action verbs, include context

---

### When to Use Each Tool

| Tool | Use When |
|------|----------|
| `assert_repository_state()` | Validating repo after operations |
| `assert_command_success()` | Checking subprocess succeeded |
| `assert_no_error_logs()` | Validating log output |
| `assert_git_operation()` | Wrapping git command sequences |
| `assert_test_operation()` | Integration/complex workflows |
| `save_test_artifacts()` | Custom failure handling |

---

### Artifact Management

Good practices:

- Clean up old artifacts periodically
- Add descriptive test names
- Use `additional_info` for test parameters
- Don't commit artifacts to git (use `.gitignore`)

Artifact location:

```text
test_artifacts/
├── test_name_20250105_143022/
│   ├── error.txt
│   ├── git_log.txt
│   ├── git_status.txt
│   ├── repo_info.json
│   └── environment.json
└── .gitignore  # Already configured
```

---

## Performance Impact

| Scenario | Impact |
|----------|--------|
| Passing tests | None (no overhead) |
| Failing tests (assertions) | ~10-50ms for error formatting |
| Failing tests (with artifacts) | ~100-200ms for file I/O |
| Memory usage | Minimal (only on failure) |
| Disk usage | ~10-50KB per failure |

**Conclusion:** No measurable impact on test suite performance.

---

## Common Pitfalls

### ❌ Pitfall 1: Forgetting repo_path

```python
# Bad - no repository context
with assert_git_operation("git stuff"):
    run_git_command_safe(["git", "commit", "-m", "x"])
```text

```python
# Good - includes repository context
with assert_git_operation("create commit", temp_git_repo):
    run_git_command_safe(["git", "commit", "-m", "x"], cwd=temp_git_repo)
```

### ❌ Pitfall 2: Generic operation names

```python
# Bad
with assert_test_operation("test"):
    complex_workflow()
```text

```python
# Good
with assert_test_operation("analyze time windows and generate report"):
    complex_workflow()
```

### ❌ Pitfall 3: Not using artifact saving for complex tests

```python
# Bad - failure is hard to debug
def test_complex_integration(temp_git_repo):
    result = multi_step_workflow(temp_git_repo)
    assert result.success
```text

```python
# Good - automatic artifact saving
def test_complex_integration(temp_git_repo):
    with assert_test_operation(
        "multi-step integration workflow",
        save_artifacts_on_failure=True,
        artifact_path=temp_git_repo
    ):
        result = multi_step_workflow(temp_git_repo)
        assert result.success
```

---

## Troubleshooting

### Q: Artifacts not being saved?

**A:** Check that:

1. `save_artifacts_on_failure=True` is set
2. An exception is actually being raised
3. The `test_artifacts/` directory is writable

### Q: Error messages too verbose?

**A:** This is intentional - detailed errors save debugging time. If needed, pipe test output to a file:

```bash
pytest tests/test_file.py -v > test_output.txt 2>&1
```text

### Q: How to clean up old artifacts?

**A:** Run periodically:

```bash
find test_artifacts/ -type d -mtime +7 -exec rm -rf {} +
# Removes artifacts older than 7 days
```

---

## Examples from Test Suite

See `tests/test_enhanced_errors.py` for 56 comprehensive examples covering:

- Git information utilities (10 tests)
- Dictionary diff formatting (5 tests)
- Repository state assertions (11 tests)
- Git operation context managers (6 tests)
- Test operation context managers (5 tests)
- Artifact saving (5 tests)
- Log validation (5 tests)
- Command success assertions (6 tests)
- Integration scenarios (4 tests)

All tests pass at 100% and demonstrate real-world usage patterns.

---

## See Also

- [Test Reliability Phase 4 Summary](../phase14/STEP3_PHASE4_SUMMARY.md)
- [Test Utilities API](../test_utils.py)
- [Test Writing Guide](TEST_WRITING_GUIDE.md)
- [Testing Guide](../TESTING_GUIDE.md)

---

**Last Updated:** 2025-01-05
**Maintainer:** Test Infrastructure Team
**Status:** ✅ Production Ready
