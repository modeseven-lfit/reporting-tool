# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Property-based tests for data transformation operations.

These tests verify that data transformations maintain invariants,
are reversible where appropriate, and handle edge cases correctly
using Hypothesis to generate random test cases.
"""

from datetime import datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from domain.author_metrics import AuthorMetrics
from domain.time_window import TimeWindow, TimeWindowStats


# =============================================================================
# Hypothesis Strategies (Data Generators)
# =============================================================================


@composite
def valid_dict_for_author(draw):
    """Generate valid dictionary for AuthorMetrics.from_dict()."""
    email = draw(st.emails())
    name = draw(st.text(min_size=1, max_size=50))

    windows = ["1y", "90d", "30d"]
    commits = {}
    lines_added = {}
    lines_removed = {}
    lines_net = {}
    repos_touched = {}

    for window in windows:
        added = draw(st.integers(min_value=0, max_value=10_000))
        removed = draw(st.integers(min_value=0, max_value=10_000))

        commits[window] = draw(st.integers(min_value=0, max_value=1_000))
        lines_added[window] = added
        lines_removed[window] = removed
        lines_net[window] = added - removed
        repos_touched[window] = draw(st.integers(min_value=0, max_value=50))

    return {
        "name": name,
        "email": email,
        "username": draw(st.text(max_size=20)),
        "domain": email.split("@")[1] if "@" in email else "unknown",
        "commits": commits,
        "lines_added": lines_added,
        "lines_removed": lines_removed,
        "lines_net": lines_net,
        "repositories_touched": repos_touched,
    }


@composite
def valid_dict_for_time_window_stats(draw):
    """Generate valid dictionary for TimeWindowStats.from_dict()."""
    added = draw(st.integers(min_value=0, max_value=100_000))
    removed = draw(st.integers(min_value=0, max_value=100_000))

    return {
        "commits": draw(st.integers(min_value=0, max_value=10_000)),
        "lines_added": added,
        "lines_removed": removed,
        "lines_net": added - removed,
        "contributors": draw(st.integers(min_value=0, max_value=1_000)),
    }


@composite
def valid_dict_for_time_window(draw):
    """Generate valid dictionary for TimeWindow.from_dict()."""
    days = draw(st.integers(min_value=1, max_value=3650))
    start_dt = draw(st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 1, 1)))
    end_dt = start_dt + timedelta(days=days)

    return {
        "days": days,
        "start": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


# =============================================================================
# Serialization/Deserialization Property Tests
# =============================================================================


class TestSerializationProperties:
    """Property tests for model serialization and deserialization."""

    @given(valid_dict_for_author())
    @settings(max_examples=100)
    def test_author_from_dict_to_dict_roundtrip(self, author_dict):
        """Property: AuthorMetrics dict -> model -> dict is identity."""
        # Deserialize
        author = AuthorMetrics.from_dict(author_dict)

        # Serialize back
        result_dict = author.to_dict()

        # Should match original (all keys preserved)
        assert result_dict["email"] == author_dict["email"]
        assert result_dict["name"] == author_dict["name"]
        assert result_dict["username"] == author_dict["username"]
        assert result_dict["domain"] == author_dict["domain"]
        assert result_dict["commits"] == author_dict["commits"]
        assert result_dict["lines_added"] == author_dict["lines_added"]
        assert result_dict["lines_removed"] == author_dict["lines_removed"]
        assert result_dict["lines_net"] == author_dict["lines_net"]

    @given(valid_dict_for_time_window_stats())
    @settings(max_examples=100)
    def test_stats_from_dict_to_dict_roundtrip(self, stats_dict):
        """Property: TimeWindowStats dict -> model -> dict is identity."""
        # Deserialize
        stats = TimeWindowStats.from_dict(stats_dict)

        # Serialize back
        result_dict = stats.to_dict()

        # Core fields should match
        assert result_dict["commits"] == stats_dict["commits"]
        assert result_dict["lines_added"] == stats_dict["lines_added"]
        assert result_dict["lines_removed"] == stats_dict["lines_removed"]
        assert result_dict["lines_net"] == stats_dict["lines_net"]

    @given(valid_dict_for_time_window(), st.text(min_size=1, max_size=10))
    @settings(max_examples=100)
    def test_time_window_from_dict_to_dict_roundtrip(self, window_dict, name):
        """Property: TimeWindow dict -> model -> dict is identity."""
        # Deserialize
        window = TimeWindow.from_dict(name, window_dict)

        # Serialize back
        result_dict = window.to_dict()

        # Should match original dict
        assert result_dict["days"] == window_dict["days"]
        assert result_dict["start"] == window_dict["start"]
        assert result_dict["end"] == window_dict["end"]

    @given(valid_dict_for_author())
    @settings(max_examples=100)
    def test_author_serialization_preserves_data_types(self, author_dict):
        """Property: Serialization preserves data types."""
        author = AuthorMetrics.from_dict(author_dict)
        result = author.to_dict()

        # Check types are preserved
        assert isinstance(result["email"], str)
        assert isinstance(result["name"], str)
        assert isinstance(result["commits"], dict)
        assert isinstance(result["lines_added"], dict)
        assert isinstance(result["lines_removed"], dict)
        assert isinstance(result["lines_net"], dict)

        # Check nested types
        for window, count in result["commits"].items():
            assert isinstance(window, str)
            assert isinstance(count, int)


# =============================================================================
# Data Transformation Property Tests
# =============================================================================


class TestDataTransformationProperties:
    """Property tests for common data transformations."""

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.integers(min_value=0, max_value=1000),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=100)
    def test_filtering_dict_reduces_or_maintains_size(self, data):
        """Property: Filtering a dict reduces or maintains its size."""
        # Filter to only entries with values > threshold
        threshold = 100
        filtered = {k: v for k, v in data.items() if v > threshold}

        assert len(filtered) <= len(data)

    @given(st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_mapping_preserves_list_length(self, values):
        """Property: Mapping over a list preserves its length."""
        # Apply transformation
        transformed = [v * 2 for v in values]

        assert len(transformed) == len(values)

    @given(st.lists(st.integers(), min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_sorting_preserves_elements(self, values):
        """Property: Sorting preserves all elements (just reorders)."""
        sorted_values = sorted(values)

        # Same length
        assert len(sorted_values) == len(values)

        # Same elements (as multiset)
        assert sorted(values) == sorted(sorted_values)

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=10), st.integers(min_value=0, max_value=1000), min_size=1
        )
    )
    @settings(max_examples=100)
    def test_dict_keys_to_list_and_back_preserves_keys(self, data):
        """Property: Converting dict keys to list and back preserves keys."""
        keys_list = list(data.keys())
        reconstructed_keys = set(keys_list)
        original_keys = set(data.keys())

        assert reconstructed_keys == original_keys

    @given(st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=50))
    @settings(max_examples=100)
    def test_grouping_preserves_total_count(self, values):
        """Property: Grouping elements preserves total count."""
        # Group by value mod 10
        groups = {}
        for v in values:
            key = v % 10
            if key not in groups:
                groups[key] = []
            groups[key].append(v)

        # Total elements should be preserved
        total_in_groups = sum(len(group) for group in groups.values())
        assert total_in_groups == len(values)


# =============================================================================
# Normalization Property Tests
# =============================================================================


class TestNormalizationProperties:
    """Property tests for data normalization operations."""

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_lowercase_is_idempotent(self, text):
        """Property: Lowercasing is idempotent (applying twice = applying once)."""
        once = text.lower()
        twice = once.lower()

        assert once == twice

    @given(st.text(min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_strip_is_idempotent(self, text):
        """Property: Stripping whitespace is idempotent."""
        once = text.strip()
        twice = once.strip()

        assert once == twice

    @given(st.text())
    @settings(max_examples=100)
    def test_strip_reduces_or_maintains_length(self, text):
        """Property: Stripping never increases length."""
        stripped = text.strip()

        assert len(stripped) <= len(text)

    @given(st.emails())
    @settings(max_examples=100)
    def test_email_domain_extraction_has_at_sign(self, email):
        """Property: Email domain extraction requires @ sign."""
        if "@" in email:
            parts = email.split("@")
            assert len(parts) >= 2
            domain = parts[-1]  # Take last part (handles multiple @)
            assert len(domain) > 0

    @given(st.lists(st.integers(), min_size=1, max_size=100))
    @settings(max_examples=100)
    def test_deduplication_reduces_or_maintains_size(self, values):
        """Property: Deduplication reduces or maintains list size."""
        unique = list(set(values))

        assert len(unique) <= len(values)

        # No duplicates in result
        assert len(unique) == len(set(unique))


# =============================================================================
# Conversion Property Tests
# =============================================================================


class TestConversionProperties:
    """Property tests for type conversions."""

    @given(st.integers(min_value=0, max_value=1_000_000))
    @settings(max_examples=100)
    def test_int_to_str_to_int_roundtrip(self, value):
        """Property: int -> str -> int is identity for valid strings."""
        as_string = str(value)
        back_to_int = int(as_string)

        assert back_to_int == value

    @given(st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False))
    @settings(max_examples=100)
    def test_float_to_int_loses_precision(self, value):
        """Property: float -> int loses fractional part."""
        as_int = int(value)

        # Integer part should be <= original value (for positive)
        assert as_int <= value

        # Difference should be less than 1
        assert abs(value - as_int) < 1

    @given(st.lists(st.integers()))
    @settings(max_examples=100)
    def test_list_to_set_to_list_may_change_order(self, values):
        """Property: list -> set -> list may change order but preserves unique elements."""
        as_set = set(values)
        back_to_list = list(as_set)

        # Should have same unique elements
        assert set(back_to_list) == as_set
        assert set(back_to_list) == set(values)

    @given(st.dictionaries(st.text(min_size=1), st.integers()))
    @settings(max_examples=100)
    def test_dict_to_items_to_dict_roundtrip(self, data):
        """Property: dict -> items -> dict is identity."""
        items = list(data.items())
        reconstructed = dict(items)

        assert reconstructed == data


# =============================================================================
# Validation Transformation Properties
# =============================================================================


class TestValidationTransformationProperties:
    """Property tests for validation and sanitization transformations."""

    @given(st.integers())
    @settings(max_examples=100)
    def test_max_zero_clamps_negative_to_zero(self, value):
        """Property: max(0, x) clamps negative values to zero."""
        result = max(0, value)

        assert result >= 0
        if value >= 0:
            assert result == value
        else:
            assert result == 0

    @given(st.integers(min_value=-1000, max_value=1000), st.integers(min_value=1, max_value=100))
    @settings(max_examples=100)
    def test_clamp_keeps_value_in_range(self, value, max_val):
        """Property: Clamping keeps value within [0, max]."""
        clamped = max(0, min(value, max_val))

        assert clamped >= 0
        assert clamped <= max_val

    @given(st.text())
    @settings(max_examples=100)
    def test_empty_string_or_default(self, text):
        """Property: Empty string replacement provides non-empty result."""
        default = "unknown"
        result = text if text else default

        if text:
            assert result == text
        else:
            assert result == default
            assert len(result) > 0

    @given(st.lists(st.integers(), max_size=100))
    @settings(max_examples=100)
    def test_empty_list_or_default(self, values):
        """Property: Empty list replacement provides non-empty result."""
        default = [0]
        result = values if values else default

        if values:
            assert result == values
        else:
            assert result == default
            assert len(result) > 0


# =============================================================================
# Time Window Transformation Properties
# =============================================================================


class TestTimeWindowTransformationProperties:
    """Property tests for time window transformations."""

    @given(st.lists(valid_dict_for_time_window(), min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_window_list_to_dict_by_name_is_reversible(self, window_dicts):
        """Property: Converting window list to dict by name is reversible."""
        # Create windows with unique names
        windows = []
        for i, wd in enumerate(window_dicts):
            name = f"window_{i}"
            windows.append(TimeWindow.from_dict(name, wd))

        # Convert to dict
        window_dict = {w.name: w for w in windows}

        # Should have same number of entries
        assert len(window_dict) == len(windows)

        # All windows should be retrievable
        for window in windows:
            assert window.name in window_dict
            assert window_dict[window.name] == window

    @given(
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.integers(min_value=0, max_value=1000),
            min_size=1,
            max_size=5,
        )
    )
    @settings(max_examples=100)
    def test_extracting_window_values_preserves_keys(self, window_data):
        """Property: Extracting values from window dict preserves keys."""
        # Simulate extracting commit counts from windows
        windows = list(window_data.keys())

        extracted = {w: window_data[w] for w in windows}

        assert set(extracted.keys()) == set(window_data.keys())

    @given(
        st.lists(
            st.tuples(st.text(min_size=1, max_size=10), st.integers(min_value=0, max_value=1000)),
            min_size=1,
            max_size=10,
            unique_by=lambda x: x[0],
        )
    )
    @settings(max_examples=100)
    def test_merging_window_dicts_combines_keys(self, window_items):
        """Property: Merging window dicts combines all keys."""
        # Split into two dicts
        mid = len(window_items) // 2
        dict1 = dict(window_items[:mid]) if mid > 0 else {}
        dict2 = dict(window_items[mid:])

        # Merge
        merged = {**dict1, **dict2}

        # Should have all keys
        all_keys = {k for k, v in window_items}
        assert set(merged.keys()) == all_keys


# =============================================================================
# Aggregation Transformation Properties
# =============================================================================


class TestAggregationTransformationProperties:
    """Property tests for transformations in aggregations."""

    @given(
        st.lists(
            st.dictionaries(
                st.text(min_size=1, max_size=10),
                st.integers(min_value=0, max_value=100),
                min_size=1,
                max_size=5,
            ),
            min_size=1,
            max_size=20,
        )
    )
    @settings(max_examples=50)
    def test_summing_dicts_by_key_preserves_total(self, dict_list):
        """Property: Summing dicts by key preserves total sum."""
        # Calculate total across all dicts
        all_values = []
        for d in dict_list:
            all_values.extend(d.values())
        total_sum = sum(all_values)

        # Sum by key
        result = {}
        for d in dict_list:
            for k, v in d.items():
                result[k] = result.get(k, 0) + v

        # Total should be preserved
        assert sum(result.values()) == total_sum

    @given(st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=50))
    @settings(max_examples=100)
    def test_sum_then_count_vs_count_then_sum(self, values):
        """Property: Different aggregation orders may differ but both valid."""
        # Calculate sum and count
        total = sum(values)
        count = len(values)

        # Both should be valid
        assert total >= 0
        assert count > 0

        # Total should be sum of all elements (tautology but validates consistency)
        assert sum(values) == total

    @given(
        st.lists(
            st.tuples(st.text(min_size=1, max_size=10), st.integers(min_value=0, max_value=100)),
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=50)
    def test_groupby_then_sum_preserves_total(self, items):
        """Property: Group by key then sum preserves total."""
        total = sum(v for k, v in items)

        # Group by key
        grouped = {}
        for k, v in items:
            if k not in grouped:
                grouped[k] = 0
            grouped[k] += v

        # Sum of groups should equal original sum
        assert sum(grouped.values()) == total
