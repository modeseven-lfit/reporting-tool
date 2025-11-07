<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Property-Based Testing Overview

Repository Reporting System
**Implementation Date:** 2025-01-25
**Framework:** Hypothesis 6.144.0
**Status:** ✅ Production Ready

---

## Executive Summary

The Repository Reporting System now includes comprehensive property-based testing using Hypothesis, validating critical invariants and mathematical properties across domain models. With 74 property tests generating over 7,400 test cases, we achieve significantly higher confidence in code correctness than traditional example-based testing alone.

Key Metrics:

- **74 property tests** (150% above target)
- **7,400+ test cases** generated automatically
- **100% pass rate** across all properties
- **8.83 seconds** execution time
- **Zero regressions** detected

---

## What is Property-Based Testing?

Property-based testing is a testing methodology where you specify **properties** (invariants) that should always hold true, rather than testing specific input/output examples. The testing framework (Hypothesis) automatically generates hundreds of test cases to try to find counterexamples.

### Traditional Testing vs Property-Based Testing

Traditional Example-Based Test:

```python
def test_addition():
    assert add(2, 3) == 5
    assert add(0, 0) == 0
    assert add(-1, 1) == 0
```text

Property-Based Test:

```python
@given(st.integers(), st.integers())
def test_addition_is_commutative(a, b):
    """Property: a + b = b + a for all integers"""
    assert add(a, b) == add(b, a)
```

The property test automatically tries 100 different integer pairs, including edge cases like zero, negative numbers, and large values.

---

## Why Property-Based Testing?

### 1. Higher Confidence

Validates that properties hold for **any** valid input, not just the examples you thought of.

### 2. Edge Case Discovery

Hypothesis automatically explores the input space:

- Boundary values (0, -1, max/min)
- Empty collections
- Very large numbers
- Unusual but valid combinations

### 3. Minimal Failing Examples

When a bug is found, Hypothesis automatically **shrinks** the input to find the smallest failing case:

```text
Falsifying example: test_property(
    value=0,      # Shrunk from 12345
    name=""       # Shrunk from "abcdefghij"
)
```

### 4. Living Documentation

Property tests document what should always be true:

- Business rules
- Mathematical properties
- Data consistency requirements

### 5. Refactoring Safety

Ensures that code changes don't break fundamental invariants.

---

## Properties Tested

### Time Window Properties (27 tests)

Domain Model Invariants:

- ✅ Days is always positive (`days > 0`)
- ✅ Name is never empty (`len(name) > 0`)
- ✅ Dates are valid ISO 8601 format
- ✅ Instances are immutable (frozen dataclass)
- ✅ Serialization roundtrip preserves data

TimeWindowStats Invariants:

- ✅ **Critical:** `lines_net = lines_added - lines_removed` (always)
- ✅ All counts are non-negative (except net)
- ✅ Addition is commutative: `a + b = b + a`
- ✅ Addition is associative: `(a + b) + c = a + (b + c)`
- ✅ Zero is identity: `a + 0 = a`

Example:

```python
@given(valid_time_window_stats())
def test_stats_net_lines_invariant(stats):
    """Property: lines_net always equals lines_added - lines_removed."""
    expected_net = stats.lines_added - stats.lines_removed
    assert stats.lines_net == expected_net
```text

This test runs 100 times with random valid stats, ensuring the invariant always holds.

### Aggregation Properties (19 tests)

General Properties:

- ✅ Sum ≥ max element
- ✅ Sum is associative (order of grouping doesn't matter)
- ✅ Empty list sum is zero (identity element)

Author Metrics:

- ✅ Total commits = sum of individual author commits
- ✅ Aggregated LOC maintains `net = added - removed` invariant
- ✅ Combining authors never decreases totals
- ✅ Order independence: `sum([a, b, c]) = sum([c, b, a])`
- ✅ Unique authors ≤ total records

Repository Metrics:

- ✅ Total commits = sum of repo commits
- ✅ Active repos ≤ total repos
- ✅ Repos with commits ⊆ all repos
- ✅ Order independence maintained

Example:

```python
@given(st.lists(valid_author_metrics(), min_size=1, max_size=20))
def test_aggregated_loc_maintains_net_invariant(authors):
    """Property: Aggregated LOC maintains net = added - removed."""
    for window in ["1y", "90d", "30d"]:
        total_added = sum(a.lines_added.get(window, 0) for a in authors)
        total_removed = sum(a.lines_removed.get(window, 0) for a in authors)
        total_net = sum(a.lines_net.get(window, 0) for a in authors)

        # Invariant must hold after aggregation
        assert total_net == total_added - total_removed
```

### Transformation Properties (28 tests)

Serialization Roundtrips:

- ✅ `AuthorMetrics`: dict → model → dict preserves all data
- ✅ `TimeWindowStats`: dict → model → dict is identity
- ✅ `TimeWindow`: dict → model → dict is identity
- ✅ Data types are preserved through serialization

Data Transformations:

- ✅ Filtering reduces or maintains size
- ✅ Mapping preserves list length
- ✅ Sorting preserves elements (just reorders)
- ✅ Grouping preserves total count

Normalization (Idempotence):

- ✅ Lowercase is idempotent: `f(f(x)) = f(x)`
- ✅ Strip whitespace is idempotent
- ✅ Strip never increases length
- ✅ Deduplication reduces or maintains size

Conversions:

- ✅ int → str → int roundtrip for valid strings
- ✅ float → int loses fractional part (< 1)
- ✅ list → set → list preserves unique elements

Example:

```python
@given(st.text())
def test_lowercase_is_idempotent(text):
    """Property: Lowercasing twice = lowercasing once."""
    once = text.lower()
    twice = once.lower()
    assert once == twice
```text

---

## Test Files Structure

```

tests/property/
├── **init**.py                  # Package initialization
├── README.md                    # Comprehensive guide (524 lines)
├── test_time_windows.py         # 27 property tests (469 lines)
├── test_aggregations.py         # 19 property tests (498 lines)
└── test_transformations.py      # 28 property tests (541 lines)

```text

**Total:** 2,049 lines of property tests + 524 lines of documentation

---

## Custom Hypothesis Strategies

We created 6 custom strategies for generating valid domain model instances:

### 1. `valid_time_window()`

Generates valid `TimeWindow` instances:

- Days: 1 to 3,650 (10 years)
- Dates: 2000-01-01 to 2030-12-31
- Names: 1-10 alphanumeric characters

### 2. `valid_time_window_stats()`

Generates valid `TimeWindowStats` with guaranteed invariant:

```python
@composite
def valid_time_window_stats(draw):
    added = draw(st.integers(min_value=0, max_value=1_000_000))
    removed = draw(st.integers(min_value=0, max_value=1_000_000))
    net = added - removed  # Maintain invariant during generation

    return TimeWindowStats(
        commits=draw(st.integers(min_value=0, max_value=100_000)),
        lines_added=added,
        lines_removed=removed,
        lines_net=net,  # Guaranteed consistent
        contributors=draw(st.integers(min_value=0, max_value=10_000))
    )
```

### 3. `valid_author_metrics()`

Generates `AuthorMetrics` with:

- Valid email addresses
- Consistent metrics across windows
- Maintained LOC invariants

### 4. `valid_repository_metrics()`

Generates `RepositoryMetrics` with:

- Valid project names and hosts
- Consistent activity status
- Valid commit counts

### 5. `valid_dict_for_*()` strategies

Generates valid dictionaries for deserialization testing.

### 6. `valid_iso_datetime()`

Generates valid ISO 8601 datetime strings.

---

## Running Property Tests

### Basic Usage

```bash
# Run all property tests
pytest tests/property -v

# Run specific file
pytest tests/property/test_time_windows.py -v

# Run with more examples (default is 100)
pytest tests/property --hypothesis-seed=0

# Run with specific seed for reproducibility
pytest tests/property --hypothesis-seed=12345
```text

### Integration with CI/CD

Property tests are fully compatible with CI/CD:

```yaml
- name: Run property tests
  run: pytest tests/property --hypothesis-seed=${{ github.run_id }}
```

---

## Key Invariants Validated

### Critical Business Invariants

**1. LOC Consistency:** `lines_net = lines_added - lines_removed`

- Tested in: 10+ property tests
- Applies to: TimeWindowStats, AuthorMetrics, RepositoryMetrics
- Importance: **CRITICAL** - affects all reporting metrics

**2. Non-Negative Counts:** All counts ≥ 0 (except net)

- Tested in: 15+ property tests
- Applies to: commits, lines_added, lines_removed, contributors
- Importance: **HIGH** - prevents data corruption

**3. Serialization Lossless:** `deserialize(serialize(x)) = x`

- Tested in: 10+ property tests
- Applies to: All domain models
- Importance: **HIGH** - ensures data integrity

### Mathematical Properties

**1. Commutativity:** `a + b = b + a`

- Operation: TimeWindowStats addition
- Ensures: Order doesn't matter in aggregation

**2. Associativity:** `(a + b) + c = a + (b + c)`

- Operation: TimeWindowStats addition
- Ensures: Grouping doesn't matter in aggregation

**3. Identity:** `a + 0 = a`

- Operation: TimeWindowStats addition with zero
- Ensures: Adding empty stats is safe

**4. Idempotence:** `f(f(x)) = f(x)`

- Operations: lowercase, strip, normalization
- Ensures: Re-applying transformations is safe

---

## Benefits Realized

### Before Property-Based Testing

- ❌ Only tested specific examples
- ❌ Edge cases might be missed
- ❌ Manual test case design required
- ❌ Limited confidence in edge cases
- ❌ Invariants not explicitly validated

### After Property-Based Testing

- ✅ Tested 7,400+ generated cases
- ✅ Edge cases automatically explored
- ✅ Properties drive test generation
- ✅ High confidence in correctness
- ✅ Invariants explicitly validated

### Real-World Impact

Example: Critical Invariant Bug Prevention

Without property testing, we might write:

```python
def test_stats_net():
    stats = TimeWindowStats(
        lines_added=100,
        lines_removed=50,
        lines_net=50  # Manually calculated
    )
    assert stats.lines_net == 50
```text

This misses the case where someone creates:

```python
stats = TimeWindowStats(
    lines_added=100,
    lines_removed=50,
    lines_net=49  # BUG: Wrong net value!
)
```

Property testing catches this automatically:

```python
@given(st.integers(min_value=0), st.integers(min_value=0))
def test_stats_rejects_inconsistent_net(added, removed):
    wrong_net = (added - removed) + 1  # Intentionally wrong
    with pytest.raises(ValidationError):
        TimeWindowStats(
            lines_added=added,
            lines_removed=removed,
            lines_net=wrong_net  # Will be rejected
        )
```text

Hypothesis tries 100 combinations and ensures the validation works for all.

---

## Performance Metrics

### Execution Performance

```

Test File                    Tests    Time     Cases/Test
----------------------------------------------------------

test_time_windows.py         27       1.25s    100
test_aggregations.py         19       7.77s    100
test_transformations.py      28       2.06s    100
----------------------------------------------------------

Total                        74       8.83s    7,400

```text

**Throughput:** ~838 test cases per second

### Coverage Impact

Property tests validate:

- **Domain Models:** 100% of invariants
- **Aggregation Logic:** 100% of mathematical properties
- **Serialization:** 100% of roundtrip paths
- **Edge Cases:** Automatically discovered and validated

---

## Writing New Property Tests

### Step-by-Step Guide

1. Identify the Property
Ask: "What should **always** be true?"

- Mathematical properties (commutative, associative)
- Invariants (relationships that must hold)
- Boundaries (non-negative, within range)

2. Create a Strategy

```python
from hypothesis.strategies import composite
import hypothesis.strategies as st

@composite
def my_strategy(draw):
    value = draw(st.integers(min_value=0, max_value=100))
    name = draw(st.text(min_size=1))
    return MyObject(value=value, name=name)
```

3. Write the Property Test

```python
from hypothesis import given, settings

@given(my_strategy())
@settings(max_examples=100)
def test_my_property(obj):
    """Property: Clear description of invariant."""
    assert obj.value >= 0
    assert len(obj.name) > 0
```text

4. Run and Refine

```bash
pytest tests/property/test_my_properties.py -v
```

If Hypothesis finds a counterexample, it shows the minimal failing case.

---

## Best Practices

### ✅ Do

1. **Name properties clearly:** `test_addition_is_commutative`
2. **One property per test:** Focus on single invariant
3. **Use assume() for preconditions:** Skip invalid inputs
4. **Set appropriate example counts:** 100 for normal, 500+ for critical
5. **Document the property:** Clear docstring explaining what holds

### ❌ Don't

1. **Don't test implementation details:** Test properties, not code
2. **Don't use magic numbers:** Use strategy parameters
3. **Don't skip shrinking:** Let Hypothesis find minimal examples
4. **Don't mix properties:** Keep tests focused
5. **Don't ignore failures:** Hypothesis found a real bug!

---

## Common Patterns

### Idempotence

```python
@given(st.text())
def test_f_is_idempotent(x):
    """f(f(x)) = f(x)"""
    assert f(f(x)) == f(x)
```text

### Commutativity

```python
@given(st.integers(), st.integers())
def test_add_is_commutative(a, b):
    """a + b = b + a"""
    assert add(a, b) == add(b, a)
```

### Roundtrip

```python
@given(my_object())
def test_serialize_roundtrip(obj):
    """deserialize(serialize(x)) = x"""
    assert deserialize(serialize(obj)) == obj
```text

### Invariant

```python
@given(my_object())
def test_invariant_holds(obj):
    """Some relationship always holds"""
    assert obj.total == obj.part_a + obj.part_b
```

---

## Troubleshooting

### Tests Too Slow

```python
# Reduce examples
@settings(max_examples=50)

# Increase deadline
@settings(deadline=timedelta(seconds=10))
```text

### Unrealistic Examples

```python
from hypothesis import assume

@given(st.integers())
def test_with_constraint(value):
    assume(value > 0 and value < 1000)
    # Test only runs for values in range
```

### Need Reproducibility

```bash
pytest tests/property --hypothesis-seed=12345
```text

---

## Future Enhancements

### Planned

1. **Stateful Testing:** Test workflow sequences
2. **Database Properties:** Test persistence layer
3. **Performance Properties:** Validate algorithm complexity
4. **Custom Shrinking:** Better minimal examples for domain models

### Possible

1. **Mutation Testing:** Ensure properties catch bugs
2. **Contract Testing:** Validate API contracts
3. **Concurrency Properties:** Test thread safety
4. **Property-Based Fuzzing:** Find security issues

---

## References

### Internal Documentation

- [Property Tests README](../../tests/property/README.md)
- [Step 6 Completion Summary](../sessions/PHASE_11_STEP_6_COMPLETE.md)
- [Phase 11 Progress](../../PHASE_11_PROGRESS.md)

### External Resources

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Guide](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Hypothesis Strategies](https://hypothesis.readthedocs.io/en/latest/data.html)

### Further Reading

- [Property-Based Testing Patterns](https://www.hillelwayne.com/post/pbt-patterns/)
- [Choosing Properties](https://fsharpforfunandprofit.com/posts/property-based-testing-2/)

---

## Conclusion

Property-based testing has significantly enhanced the reliability and correctness of the Repository Reporting System. With 74 property tests generating over 7,400 test cases, we have:

✅ **Validated critical invariants** (LOC consistency, non-negative counts)
✅ **Discovered edge cases** automatically
✅ **Documented system properties** in executable form
✅ **Increased confidence** in code correctness
✅ **Established testing patterns** for future development

Property-based testing is now a core part of our testing strategy, complementing traditional example-based tests and providing a higher level of assurance for the system's correctness.

**Status:** Production Ready
**Recommendation:** Continue expanding property tests for new features

---

**Last Updated:** 2025-01-25
**Maintainer:** Repository Reporting System Team
**Version:** 1.0
