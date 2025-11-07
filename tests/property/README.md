<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Property-Based Tests

**Testing Strategy:** Property-Based Testing with Hypothesis
**Purpose:** Validate invariants and mathematical properties across domain models
**Coverage:** Time windows, aggregations, transformations, and data conversions

---

## Overview

Property-based testing is a testing methodology where you specify **properties** (invariants) that should always hold true, and the testing framework (Hypothesis) generates hundreds of random test cases to try to find counterexamples.

Unlike traditional example-based tests that check specific inputs and outputs, property-based tests verify that certain rules always apply, regardless of the input.

**Benefits:**

- Discovers edge cases that humans might not think of
- Tests properties rather than specific examples
- Generates minimal failing examples when bugs are found
- Provides higher confidence in code correctness

---

## Test Categories

### 1. Time Window Properties (`test_time_windows.py`)

Tests invariants for `TimeWindow` and `TimeWindowStats` domain models:

**TimeWindow Properties:**

- Serialization roundtrip preserves data
- Instances are immutable (frozen dataclass)
- Days is always positive
- Name is never empty
- Dates are valid ISO 8601 format
- Rejects invalid inputs (non-positive days, empty names)

**TimeWindowStats Properties:**

- Serialization roundtrip preserves data
- Invariant: `lines_net = lines_added - lines_removed`
- All counts are non-negative (except net)
- Addition is commutative: `a + b = b + a`
- Addition is associative: `(a + b) + c = a + (b + c)`
- Zero is the identity element: `a + 0 = a`
- Addition preserves the net invariant
- Rejects invalid inputs (negative counts, inconsistent net)

**Example Property:**

```python
@given(valid_time_window_stats())
def test_stats_net_lines_invariant(self, stats: TimeWindowStats):
    """Property: lines_net always equals lines_added - lines_removed."""
    expected_net = stats.lines_added - stats.lines_removed
    assert stats.lines_net == expected_net
```

### 2. Aggregation Properties (`test_aggregations.py`)

Tests invariants for aggregating metrics across authors and repositories:

**General Aggregation Properties:**

- Sum ≥ max element
- Sum is associative
- Empty list sum is zero (identity)

**Author Metrics Aggregation:**

- Total commits = sum of individual author commits
- Aggregated LOC maintains net invariant
- Combining authors never decreases totals
- Order independence (commutative)
- Unique author count ≤ total records
- Domain grouping preserves totals

**Repository Metrics Aggregation:**

- Total commits = sum of repo commits
- Aggregated LOC maintains net invariant
- Active repos ≤ total repos
- Repos with commits ⊆ all repos
- Order independence

**TimeWindowStats Aggregation:**

- Aggregation preserves net invariant
- Sum of stats with 1 commit each = count of stats

**Example Property:**

```python
@given(st.lists(valid_author_metrics(), min_size=1, max_size=20))
def test_aggregated_loc_maintains_net_invariant(self, authors):
    """Property: Aggregated LOC maintains net = added - removed invariant."""
    for window in ["1y", "90d", "30d"]:
        total_added = sum(author.lines_added.get(window, 0) for author in authors)
        total_removed = sum(author.lines_removed.get(window, 0) for author in authors)
        total_net = sum(author.lines_net.get(window, 0) for author in authors)

        # Invariant must hold after aggregation
        assert total_net == total_added - total_removed
```

### 3. Transformation Properties (`test_transformations.py`)

Tests properties of data transformations and conversions:

**Serialization/Deserialization:**

- Roundtrip preserves data (dict → model → dict)
- Types are preserved
- All required fields maintained

**Data Transformations:**

- Filtering reduces or maintains size
- Mapping preserves list length
- Sorting preserves elements
- Grouping preserves total count

**Normalization:**

- Lowercase is idempotent: `f(f(x)) = f(x)`
- Strip is idempotent
- Strip never increases length
- Deduplication reduces or maintains size

**Conversions:**

- int → str → int is identity
- float → int loses fractional part
- list → set → list preserves unique elements
- dict → items → dict is identity

**Validation:**

- `max(0, x)` clamps negative to zero
- Clamping keeps values in range
- Default value replacement ensures non-empty results

**Example Property:**

```python
@given(valid_dict_for_author())
def test_author_from_dict_to_dict_roundtrip(self, author_dict):
    """Property: AuthorMetrics dict → model → dict is identity."""
    author = AuthorMetrics.from_dict(author_dict)
    result_dict = author.to_dict()

    # Should match original
    assert result_dict["email"] == author_dict["email"]
    assert result_dict["commits"] == author_dict["commits"]
    # ... all fields preserved
```

---

## Running Property Tests

### Run All Property Tests

```bash
# Run all property tests
pytest tests/property -v

# Run with detailed output
pytest tests/property -vv

# Run specific test file
pytest tests/property/test_time_windows.py -v
```

### Run Specific Test Class

```bash
# Run TimeWindow properties
pytest tests/property/test_time_windows.py::TestTimeWindowProperties -v

# Run aggregation properties
pytest tests/property/test_aggregations.py::TestAuthorMetricsAggregationProperties -v
```

### Control Number of Examples

```bash
# Run with more examples (default is 100)
pytest tests/property --hypothesis-seed=0 -v

# Run with specific seed for reproducibility
pytest tests/property --hypothesis-seed=12345 -v
```

### Find Minimal Failing Example

When Hypothesis finds a failing test, it automatically tries to find the **smallest** input that causes the failure (shrinking). This makes debugging much easier.

```bash
# Example output when a property fails:
# Falsifying example: test_some_property(
#     value=0,  # Shrunk from 12345
#     name=""   # Shrunk from "abcdefghij"
# )
```

---

## Hypothesis Strategies

Strategies are used to generate random test data. We define custom strategies for our domain models:

### Custom Strategies

**`valid_time_window()`**

- Generates valid `TimeWindow` instances
- Days: 1 to 3650 (10 years)
- Dates: 2000-01-01 to 2030-12-31
- Names: 1-10 characters

**`valid_time_window_stats()`**

- Generates valid `TimeWindowStats` instances
- Maintains invariant: `lines_net = lines_added - lines_removed`
- Non-negative values for commits, lines, contributors

**`valid_author_metrics()`**

- Generates valid `AuthorMetrics` instances
- Valid email addresses
- Consistent metrics across time windows
- Maintains LOC invariants

**`valid_repository_metrics()`**

- Generates valid `RepositoryMetrics` instances
- Valid project names and hosts
- Consistent activity status and commit counts

### Using Strategies

```python
from hypothesis import given
from tests.property.test_time_windows import valid_time_window

@given(valid_time_window())
def test_my_property(window):
    # Hypothesis generates 100 random TimeWindow instances by default
    assert window.days > 0
```

---

## Writing New Property Tests

### Step 1: Identify the Property

Think about what should **always** be true:

- Mathematical properties (commutative, associative, identity)
- Invariants (relationships that must hold)
- Roundtrip properties (serialize/deserialize)
- Boundaries (non-negative, within range)

### Step 2: Create a Strategy

Define how to generate valid test data:

```python
from hypothesis.strategies import composite
import hypothesis.strategies as st

@composite
def my_strategy(draw):
    """Generate valid test data."""
    value = draw(st.integers(min_value=0, max_value=100))
    name = draw(st.text(min_size=1, max_size=20))
    return MyObject(value=value, name=name)
```

### Step 3: Write the Property Test

```python
from hypothesis import given, settings

@given(my_strategy())
@settings(max_examples=100)
def test_my_property(obj):
    """Property: Describe what should always be true."""
    # Test the property
    assert obj.value >= 0
    assert len(obj.name) > 0
```

### Step 4: Run and Refine

```bash
pytest tests/property/test_my_new_properties.py -v
```

If Hypothesis finds a counterexample, it will show you the minimal failing case.

---

## Best Practices

### 1. Name Properties Clearly

```python
# ✅ Good - Clear property statement
def test_addition_is_commutative(self, a, b):
    """Property: a + b = b + a"""
    pass

# ❌ Bad - Unclear what property is being tested
def test_addition(self, a, b):
    pass
```

### 2. Test One Property Per Test

```python
# ✅ Good - Single property
@given(valid_time_window_stats())
def test_stats_net_lines_invariant(self, stats):
    """Property: lines_net = lines_added - lines_removed"""
    assert stats.lines_net == stats.lines_added - stats.lines_removed

# ❌ Bad - Multiple properties
@given(valid_time_window_stats())
def test_stats_properties(self, stats):
    assert stats.commits >= 0
    assert stats.lines_net == stats.lines_added - stats.lines_removed
    assert stats.contributors >= 0
```

### 3. Use Assume for Preconditions

```python
from hypothesis import assume

@given(st.integers(), st.integers())
def test_division_property(self, a, b):
    assume(b != 0)  # Skip cases where b is zero
    result = a / b
    # ... test property
```

### 4. Set Appropriate Example Counts

```python
# Quick smoke test
@settings(max_examples=10)
def test_quick_property(self, value):
    pass

# Thorough testing
@settings(max_examples=500)
def test_critical_property(self, value):
    pass
```

### 5. Use Deadlines for Slow Tests

```python
from hypothesis import settings
from datetime import timedelta

@settings(deadline=timedelta(seconds=5))
def test_potentially_slow_property(self, data):
    # Hypothesis will fail if this takes > 5 seconds
    pass
```

---

## Common Patterns

### Idempotence

A function is idempotent if applying it twice gives the same result as applying it once:

```python
@given(st.text())
def test_lowercase_is_idempotent(self, text):
    """Property: f(f(x)) = f(x)"""
    once = text.lower()
    twice = once.lower()
    assert once == twice
```

### Commutativity

An operation is commutative if order doesn't matter:

```python
@given(valid_time_window_stats(), valid_time_window_stats())
def test_addition_is_commutative(self, a, b):
    """Property: a + b = b + a"""
    assert (a + b) == (b + a)
```

### Associativity

An operation is associative if grouping doesn't matter:

```python
@given(st.integers(), st.integers(), st.integers())
def test_addition_is_associative(self, a, b, c):
    """Property: (a + b) + c = a + (b + c)"""
    assert (a + b) + c == a + (b + c)
```

### Identity Element

An identity element leaves other elements unchanged:

```python
@given(valid_time_window_stats())
def test_zero_is_identity(self, stats):
    """Property: a + 0 = a"""
    zero = TimeWindowStats()
    assert stats + zero == stats
```

### Roundtrip

Serialization followed by deserialization should be identity:

```python
@given(valid_author_metrics())
def test_serialization_roundtrip(self, author):
    """Property: deserialize(serialize(x)) = x"""
    serialized = author.to_dict()
    deserialized = AuthorMetrics.from_dict(serialized)
    assert deserialized == author
```

---

## Troubleshooting

### Tests Are Too Slow

```python
# Reduce number of examples
@settings(max_examples=50)

# Or increase deadline
@settings(deadline=timedelta(seconds=10))
```

### Hypothesis Finds Unrealistic Examples

```python
# Use assume() to filter
from hypothesis import assume

@given(st.integers())
def test_property(self, value):
    assume(value > 0 and value < 1000)
    # Test only runs for values in range
```

### Want Reproducible Tests

```bash
# Use a specific seed
pytest tests/property --hypothesis-seed=12345
```

### Need to Debug a Failing Example

```python
# Hypothesis will print the minimal failing example
# Copy it and create a regular test:

def test_specific_failing_case():
    # Use the exact values Hypothesis found
    stats = TimeWindowStats(commits=-1)  # This will fail
```

---

## Metrics

**Total Property Tests:** 60+
**Test Files:** 3
**Average Examples Per Test:** 100
**Total Test Cases Generated:** 6,000+

**Coverage:**

- TimeWindow: 20+ properties
- TimeWindowStats: 15+ properties
- Author Metrics: 10+ properties
- Repository Metrics: 8+ properties
- Transformations: 20+ properties

---

## References

### Documentation

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Guide](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Hypothesis Strategies](https://hypothesis.readthedocs.io/en/latest/data.html)

### Resources

- [Property-Based Testing Patterns](https://www.hillelwayne.com/post/pbt-patterns/)
- [Invariants and Properties](https://fsharpforfunandprofit.com/posts/property-based-testing-2/)

---

## Contributing

When adding new property tests:

1. **Identify the property** - What should always be true?
2. **Create a strategy** - How to generate valid test data?
3. **Write the test** - Use `@given` decorator
4. **Document the property** - Clear docstring
5. **Run and validate** - Ensure it passes and is meaningful

Example:

```python
@given(my_custom_strategy())
@settings(max_examples=100)
def test_my_new_property(self, data):
    """Property: Clear description of what should always hold."""
    # Arrange (if needed)

    # Act
    result = my_function(data)

    # Assert the property
    assert some_invariant_holds(result)
```

---

**Last Updated:** 2025-01-25
**Status:** ✅ Complete (60+ property tests, 100% passing)
