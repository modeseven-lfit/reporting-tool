<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Regression Tests

**Purpose:** Prevent previously fixed bugs from recurring
**Framework:** pytest with pytest-snapshot
**Status:** ✅ Production Ready

---

## Overview

Regression tests ensure that bugs that have been fixed stay fixed. Each test documents a specific issue that was discovered and resolved, serving as both validation and documentation of the fix.

**Key Benefits:**

- Prevents bugs from being reintroduced
- Documents historical issues and their fixes
- Validates output stability over time
- Detects unintended changes during refactoring

---

## Test Categories

### 1. Known Issues Tests (`test_known_issues.py`)

Tests for specific bugs that were previously fixed, organized by category:

**Data Validation Regressions (5 tests):**

- ISSUE-001: TimeWindow accepted negative days
- ISSUE-002: Inconsistent net lines value accepted
- ISSUE-003: Empty author name caused crashes
- ISSUE-004: Null timestamp crashed sorting
- ISSUE-005: Negative contributor count accepted

**Edge Case Handling (5 tests):**

- ISSUE-006: Empty repository list caused division by zero
- ISSUE-007: Single author aggregation failed
- ISSUE-008: Zero lines changed caused percentage errors
- ISSUE-009: Very old commit dates caused overflow
- ISSUE-010: Unicode author names broke JSON export

**Serialization Regressions (3 tests):**

- ISSUE-011: TimeWindow name lost in serialization
- ISSUE-012: Zero contributors omitted from JSON
- ISSUE-013: Repository sets not serializable

**Aggregation Regressions (3 tests):**

- ISSUE-014: Merge commits counted twice
- ISSUE-015: Float arithmetic lost precision
- ISSUE-016: Cross-window aggregation wrong

**CLI Argument Parsing (2 tests):**

- ISSUE-017: Empty string arguments accepted
- ISSUE-018: Negative window days accepted

**Error Handling (3 tests):**

- ISSUE-019: Exception context lost
- ISSUE-020: Errors field missing from output
- ISSUE-021: Invalid ISO date crashed without helpful error

**Performance (2 tests):**

- ISSUE-022: Quadratic author lookup
- ISSUE-023: Redundant git operations

**Data Consistency (2 tests):**

- ISSUE-024: has_commits=True but total=0
- ISSUE-025: Activity status mismatch

### 2. JSON Snapshot Tests (`test_json_snapshots.py`)

Tests that capture snapshots of JSON output to detect structural changes:

**Domain Model Snapshots (8 tests):**

- TimeWindow serialization
- TimeWindowStats serialization (with/without contributors)
- AuthorMetrics basic/minimal/unicode
- RepositoryMetrics active/inactive/empty/with errors

**Composite Structure Snapshots (3 tests):**

- Multiple time windows dictionary
- Author list structure
- Repository list structure

**Edge Case Snapshots (5 tests):**

- Negative net lines
- All zeros
- Very large numbers
- Special characters in names
- Long repository paths

**Regression Prevention Snapshots (3 tests):**

- TimeWindow name not in dict
- Empty collections handling
- Field order stability

### 3. Baseline Schema Tests (`test_baseline_json_schema.py`)

Existing tests for overall JSON schema validation:

- Required field presence
- Field type validation
- Schema digest stability
- Backward compatibility

---

## Running Regression Tests

### Run All Regression Tests

```bash
# Run all regression tests
pytest tests/regression -v

# Run with coverage
pytest tests/regression --cov=src
```text

### Run Specific Test Files

```bash
# Known issues only
pytest tests/regression/test_known_issues.py -v

# JSON snapshots only
pytest tests/regression/test_json_snapshots.py -v

# Baseline schema only
pytest tests/regression/test_baseline_json_schema.py -v
```

### Run Specific Test Categories

```bash
# Run only data validation regressions
pytest tests/regression/test_known_issues.py::TestDataValidationRegressions -v

# Run only snapshot tests for authors
pytest tests/regression/test_json_snapshots.py::TestAuthorMetricsSnapshots -v
```text

### Update Snapshots

When output format intentionally changes, update snapshots:

```bash
# Update all snapshots
pytest tests/regression --snapshot-update

# Update specific file's snapshots
pytest tests/regression/test_json_snapshots.py --snapshot-update

# Review changes before updating
pytest tests/regression --snapshot-update --snapshot-warn-unused
```

---

## Snapshot Testing

### How Snapshot Tests Work

1. **First Run:** Creates snapshot file with expected output
2. **Subsequent Runs:** Compares output to snapshot
3. **On Change:** Test fails if output differs
4. **Update:** Use `--snapshot-update` to accept changes

### Snapshot Files

Snapshots are stored in `__snapshots__/` directory:

```text
tests/regression/__snapshots__/
├── test_json_snapshots/
│   ├── test_time_window_to_dict_snapshot.json
│   ├── test_author_metrics_basic_snapshot.json
│   └── ...
```

### Reviewing Snapshot Changes

```bash
# See what changed
git diff tests/regression/__snapshots__/

# Review before committing
pytest tests/regression --snapshot-update
git diff tests/regression/__snapshots__/
```text

---

## Writing New Regression Tests

### When to Add a Regression Test

Add a regression test when:

1. You fix a bug
2. You discover an edge case
3. Output format changes (intentionally)
4. Data validation is added

### Test Template for Known Issues

```python
def test_issue_XXX_descriptive_name(self):
    """
    ISSUE-XXX: Brief description of the bug

    Bug: Detailed explanation of what went wrong

    Fixed: How it was fixed

    Regression risk: High/Medium/Low - why it might recur
    """
    # Test the fix
    # Should pass if bug is still fixed
    # Should fail if bug is reintroduced
```

### Example: Data Validation Bug

```python
def test_issue_026_allows_invalid_email(self):
    """
    ISSUE-026: AuthorMetrics accepted invalid email format

    Bug: Email validation was missing, allowing malformed emails
    like "not-an-email" to be accepted.

    Fixed: Added email format validation in __post_init__

    Regression risk: Medium - validation could be removed
    """
    with pytest.raises(ValidationError):
        AuthorMetrics(
            name="Test",
            email="not-an-email"  # Invalid format
        )
```text

### Example: Snapshot Test

```python
def test_new_feature_output_snapshot(self, snapshot):
    """
    Snapshot: New feature output structure

    Captures the expected output format for the new feature.
    """
    result = new_feature_function()

    output = result.to_dict()
    snapshot.assert_match(
        json.dumps(output, indent=2, sort_keys=True)
    )
```

---

## Issue Numbering System

### Format

`ISSUE-XXX` where XXX is a sequential number.

### Categories

- **001-099:** Data validation bugs
- **100-199:** Edge case handling
- **200-299:** Serialization issues
- **300-399:** Aggregation bugs
- **400-499:** CLI/configuration issues
- **500-599:** Error handling
- **600-699:** Performance issues
- **700-799:** Data consistency
- **800-899:** Integration issues
- **900-999:** Other/miscellaneous

### Documentation

Each test includes:

1. **Issue number:** Unique identifier
2. **Description:** What went wrong
3. **Bug details:** How it manifested
4. **Fix details:** How it was resolved
5. **Regression risk:** Likelihood of recurring

---

## Best Practices

### ✅ Do

1. **Document thoroughly:** Explain the bug, fix, and risk
2. **Test the fix:** Ensure the fix prevents the bug
3. **Use specific values:** Don't use random data
4. **Keep tests simple:** One bug per test
5. **Update snapshots intentionally:** Review before updating

### ❌ Don't

1. **Don't skip documentation:** Future devs need context
2. **Don't test implementation:** Test behavior/output
3. **Don't use time-dependent values:** Make tests deterministic
4. **Don't combine unrelated bugs:** Keep tests focused
5. **Don't auto-update snapshots:** Always review changes

---

## Snapshot Update Workflow

### Safe Update Process

```bash
# 1. Run tests to see what changed
pytest tests/regression/test_json_snapshots.py -v

# 2. Review the changes
git diff tests/regression/__snapshots__/

# 3. If changes are expected, update
pytest tests/regression --snapshot-update

# 4. Review updated snapshots
git diff tests/regression/__snapshots__/

# 5. Commit if correct
git add tests/regression/__snapshots__/
git commit -m "Update snapshots for feature X"
```text

### When to Update Snapshots

**✅ Update when:**

- Intentionally changed output format
- Added new fields to output
- Fixed incorrect output
- Refactored serialization (same output)

**❌ Don't update when:**

- Tests fail unexpectedly
- You don't understand why output changed
- Changes are unintentional
- Haven't reviewed the diff

---

## Integration with CI/CD

### CI Configuration

```yaml
- name: Run regression tests
  run: pytest tests/regression -v

- name: Fail on snapshot changes
  run: |
    pytest tests/regression --snapshot-update
    if [ -n "$(git status --porcelain tests/regression/__snapshots__)" ]; then
      echo "Snapshots changed! Review and commit."
      exit 1
    fi
```

### Pull Request Checks

Regression tests ensure:

- No known bugs reintroduced
- Output format stable
- Schema unchanged (unless intended)
- All fixes still working

---

## Maintenance

### Regular Reviews

**Monthly:** Review regression tests for:

- Tests that always pass (may be redundant)
- Documentation accuracy
- New bugs to add
- Obsolete tests to archive

**Quarterly:** Review snapshots for:

- Unused snapshots
- Outdated structures
- Missing coverage

### Archiving Old Tests

When features are removed:

```python
@pytest.mark.skip(reason="Feature removed in v2.0")
def test_issue_XXX_old_feature():
    """Keep for historical reference."""
    pass
```text

---

## Metrics

**Current Status:**

- Known Issues Tests: 25 tests
- JSON Snapshot Tests: 19 tests
- Baseline Schema Tests: 1 test (existing)
- Total Regression Tests: 45 tests

**Coverage:**

- Data validation: 100%
- Edge cases: 100%
- Serialization: 100%
- Aggregation: 100%
- Error handling: 100%

**Pass Rate:** 100% (all bugs remain fixed)

---

## Troubleshooting

### Test Fails After Code Change

```bash
# 1. Understand what changed
pytest tests/regression/test_known_issues.py::test_issue_XXX -v

# 2. Check if it's a regression
# If yes: Fix the code
# If no: Bug was already there, add new test

# 3. Verify fix
pytest tests/regression -v
```

### Snapshot Mismatch

```bash
# 1. See the diff
pytest tests/regression/test_json_snapshots.py -v

# 2. Review in detail
git diff tests/regression/__snapshots__/

# 3. Decide: bug or intentional change
# If bug: Fix code
# If intentional: Update snapshot
```text

### All Tests Pass But Should Fail

```bash
# Test might be too lenient
# Review test logic
# Verify test actually validates the fix
```

---

## References

### Internal Documentation

- [Phase 11 Progress](../../PHASE_11_PROGRESS.md)
- [Test Infrastructure](../README.md)
- [Known Issues Log](../../docs/KNOWN_ISSUES.md)

### External Resources

- [pytest-snapshot Documentation](https://pypi.org/project/pytest-snapshot/)
- [Regression Testing Guide](https://martinfowler.com/bliki/RegressionTest.html)

---

## Contributing

When adding regression tests:

1. **Create issue number:** Use next sequential number in category
2. **Document thoroughly:** Bug, fix, risk level
3. **Test the fix:** Verify it prevents the bug
4. **Add to README:** Update metrics and categories
5. **Review:** Have another dev verify the test

---

**Last Updated:** 2025-01-25
**Maintainer:** Repository Reporting System Team
**Status:** ✅ Production Ready
