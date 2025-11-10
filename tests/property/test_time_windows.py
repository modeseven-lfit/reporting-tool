# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Property-based tests for TimeWindow and TimeWindowStats domain models.

These tests use Hypothesis to generate random but valid inputs and verify
that certain properties and invariants always hold true, helping to discover
edge cases that example-based tests might miss.
"""

from datetime import datetime, timedelta

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite

from cli.errors import ValidationError
from domain.time_window import TimeWindow, TimeWindowStats


# =============================================================================
# Hypothesis Strategies (Data Generators)
# =============================================================================


@composite
def valid_iso_datetime(draw):
    """Generate valid ISO 8601 datetime strings."""
    # Generate a datetime between 2000-01-01 and 2030-12-31
    start = datetime(2000, 1, 1)
    end = datetime(2030, 12, 31)

    # Generate random number of days
    days_diff = (end - start).days
    random_days = draw(st.integers(min_value=0, max_value=days_diff))

    dt = start + timedelta(days=random_days)

    # Return as ISO format with Z suffix
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


@composite
def valid_time_window(draw):
    """Generate valid TimeWindow instances."""
    # Generate window properties
    days = draw(st.integers(min_value=1, max_value=3650))  # 1 day to 10 years
    name = draw(
        st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"
            ),
        )
    )

    # Generate start date
    start_dt = draw(st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 1, 1)))

    # End date is start + days
    end_dt = start_dt + timedelta(days=days)

    start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return TimeWindow(name=name, days=days, start_date=start_str, end_date=end_str)


@composite
def valid_time_window_stats(draw):
    """Generate valid TimeWindowStats instances."""
    # Generate LOC changes that maintain the invariant: net = added - removed
    lines_added = draw(st.integers(min_value=0, max_value=1_000_000))
    lines_removed = draw(st.integers(min_value=0, max_value=1_000_000))
    lines_net = lines_added - lines_removed  # Must be consistent

    return TimeWindowStats(
        commits=draw(st.integers(min_value=0, max_value=100_000)),
        lines_added=lines_added,
        lines_removed=lines_removed,
        lines_net=lines_net,
        contributors=draw(st.integers(min_value=0, max_value=10_000)),
    )


# =============================================================================
# TimeWindow Property Tests
# =============================================================================


class TestTimeWindowProperties:
    """Property-based tests for TimeWindow domain model."""

    @given(valid_time_window())
    @settings(max_examples=100)
    def test_time_window_roundtrip_serialization(self, window: TimeWindow):
        """Property: TimeWindow serialization roundtrip preserves data."""
        # Serialize to dict
        data = window.to_dict()

        # Deserialize back
        restored = TimeWindow.from_dict(window.name, data)

        # Should be identical
        assert restored.name == window.name
        assert restored.days == window.days
        assert restored.start_date == window.start_date
        assert restored.end_date == window.end_date
        assert restored == window

    @given(valid_time_window())
    @settings(max_examples=100)
    def test_time_window_is_immutable(self, window: TimeWindow):
        """Property: TimeWindow instances are immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            window.days = 999

        with pytest.raises(AttributeError):
            window.name = "changed"

    @given(valid_time_window())
    @settings(max_examples=100)
    def test_time_window_days_always_positive(self, window: TimeWindow):
        """Property: TimeWindow days is always positive."""
        assert window.days > 0

    @given(valid_time_window())
    @settings(max_examples=100)
    def test_time_window_name_never_empty(self, window: TimeWindow):
        """Property: TimeWindow name is never empty."""
        assert len(window.name) > 0
        assert window.name.strip() != ""

    @given(valid_time_window())
    @settings(max_examples=100)
    def test_time_window_dates_are_valid_iso8601(self, window: TimeWindow):
        """Property: TimeWindow dates are always valid ISO 8601 format."""
        # Should parse without errors
        start = datetime.fromisoformat(window.start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(window.end_date.replace("Z", "+00:00"))

        assert isinstance(start, datetime)
        assert isinstance(end, datetime)

    @given(valid_time_window())
    @settings(max_examples=100)
    def test_time_window_dict_has_required_keys(self, window: TimeWindow):
        """Property: TimeWindow.to_dict() always has required keys."""
        data = window.to_dict()

        assert "days" in data
        assert "start" in data
        assert "end" in data

        # Should not have 'name' in dict (it's provided separately in from_dict)
        assert "name" not in data

    @given(
        st.integers(min_value=1, max_value=3650),
        st.text(min_size=1, max_size=20),
        valid_iso_datetime(),
        valid_iso_datetime(),
    )
    @settings(max_examples=100)
    def test_time_window_creation_with_valid_inputs_succeeds(self, days, name, start, end):
        """Property: TimeWindow creation succeeds with any valid inputs."""
        try:
            window = TimeWindow(name=name, days=days, start_date=start, end_date=end)
            assert window.days == days
            assert window.name == name
        except Exception as e:
            # Should not raise for valid inputs
            pytest.fail(f"Unexpected exception with valid inputs: {e}")

    @given(
        st.integers(max_value=0),  # Invalid: non-positive
        st.text(min_size=1),
        valid_iso_datetime(),
        valid_iso_datetime(),
    )
    @settings(max_examples=50)
    def test_time_window_rejects_non_positive_days(self, invalid_days, name, start, end):
        """Property: TimeWindow rejects non-positive days."""
        with pytest.raises(ValidationError):
            TimeWindow(name=name, days=invalid_days, start_date=start, end_date=end)

    @given(st.integers(min_value=1, max_value=3650), valid_iso_datetime(), valid_iso_datetime())
    @settings(max_examples=50)
    def test_time_window_rejects_empty_name(self, days, start, end):
        """Property: TimeWindow rejects empty name."""
        with pytest.raises(ValidationError):
            TimeWindow(name="", days=days, start_date=start, end_date=end)

    @given(valid_time_window(), valid_time_window())
    @settings(max_examples=100)
    def test_time_window_equality_is_value_based(self, w1: TimeWindow, w2: TimeWindow):
        """Property: TimeWindow equality is based on values, not identity."""
        if (
            w1.name == w2.name
            and w1.days == w2.days
            and w1.start_date == w2.start_date
            and w1.end_date == w2.end_date
        ):
            assert w1 == w2
        else:
            assert w1 != w2


# =============================================================================
# TimeWindowStats Property Tests
# =============================================================================


class TestTimeWindowStatsProperties:
    """Property-based tests for TimeWindowStats domain model."""

    @given(valid_time_window_stats())
    @settings(max_examples=100)
    def test_stats_roundtrip_serialization(self, stats: TimeWindowStats):
        """Property: TimeWindowStats serialization roundtrip preserves data."""
        # Serialize to dict
        data = stats.to_dict()

        # Deserialize back
        restored = TimeWindowStats.from_dict(data)

        # Should be identical
        assert restored.commits == stats.commits
        assert restored.lines_added == stats.lines_added
        assert restored.lines_removed == stats.lines_removed
        assert restored.lines_net == stats.lines_net
        assert restored.contributors == stats.contributors

    @given(valid_time_window_stats())
    @settings(max_examples=100)
    def test_stats_net_lines_invariant(self, stats: TimeWindowStats):
        """Property: lines_net always equals lines_added - lines_removed."""
        expected_net = stats.lines_added - stats.lines_removed
        assert stats.lines_net == expected_net

    @given(valid_time_window_stats())
    @settings(max_examples=100)
    def test_stats_all_counts_non_negative_except_net(self, stats: TimeWindowStats):
        """Property: All counts are non-negative (except net which can be negative)."""
        assert stats.commits >= 0
        assert stats.lines_added >= 0
        assert stats.lines_removed >= 0
        assert stats.contributors >= 0
        # lines_net can be negative

    @given(valid_time_window_stats(), valid_time_window_stats())
    @settings(max_examples=100)
    def test_stats_addition_is_commutative(self, stats1: TimeWindowStats, stats2: TimeWindowStats):
        """Property: Addition of stats is commutative (a + b = b + a)."""
        sum1 = stats1 + stats2
        sum2 = stats2 + stats1

        assert sum1.commits == sum2.commits
        assert sum1.lines_added == sum2.lines_added
        assert sum1.lines_removed == sum2.lines_removed
        assert sum1.lines_net == sum2.lines_net
        assert sum1.contributors == sum2.contributors

    @given(valid_time_window_stats(), valid_time_window_stats(), valid_time_window_stats())
    @settings(max_examples=100)
    def test_stats_addition_is_associative(
        self, s1: TimeWindowStats, s2: TimeWindowStats, s3: TimeWindowStats
    ):
        """Property: Addition of stats is associative ((a + b) + c = a + (b + c))."""
        sum_left = (s1 + s2) + s3
        sum_right = s1 + (s2 + s3)

        assert sum_left.commits == sum_right.commits
        assert sum_left.lines_added == sum_right.lines_added
        assert sum_left.lines_removed == sum_right.lines_removed
        assert sum_left.lines_net == sum_right.lines_net

    @given(valid_time_window_stats())
    @settings(max_examples=100)
    def test_stats_has_identity_element(self, stats: TimeWindowStats):
        """Property: Adding zero stats (identity) doesn't change the value."""
        zero = TimeWindowStats()  # All zeros

        result = stats + zero

        assert result.commits == stats.commits
        assert result.lines_added == stats.lines_added
        assert result.lines_removed == stats.lines_removed
        assert result.lines_net == stats.lines_net
        assert result.contributors == stats.contributors

    @given(valid_time_window_stats(), valid_time_window_stats())
    @settings(max_examples=100)
    def test_stats_addition_preserves_net_invariant(
        self, stats1: TimeWindowStats, stats2: TimeWindowStats
    ):
        """Property: Addition preserves the net = added - removed invariant."""
        result = stats1 + stats2

        expected_net = result.lines_added - result.lines_removed
        assert result.lines_net == expected_net

    @given(
        st.integers(min_value=0, max_value=1_000_000), st.integers(min_value=0, max_value=1_000_000)
    )
    @settings(max_examples=100)
    def test_stats_can_represent_any_loc_change(self, added, removed):
        """Property: Stats can represent any valid LOC change (added/removed)."""
        net = added - removed

        stats = TimeWindowStats(
            commits=1, lines_added=added, lines_removed=removed, lines_net=net, contributors=1
        )

        assert stats.lines_added == added
        assert stats.lines_removed == removed
        assert stats.lines_net == net

    @given(
        st.integers(min_value=0, max_value=100),
        st.integers(min_value=0, max_value=1000),
        st.integers(min_value=0, max_value=1000),
    )
    @settings(max_examples=50)
    def test_stats_rejects_inconsistent_net(self, commits, added, removed):
        """Property: Stats rejects inconsistent net value."""
        # Create WRONG net value
        wrong_net = (added - removed) + 1  # Off by one

        assume(wrong_net != added - removed)  # Ensure it's actually wrong

        with pytest.raises(ValidationError):
            TimeWindowStats(
                commits=commits,
                lines_added=added,
                lines_removed=removed,
                lines_net=wrong_net,
                contributors=1,
            )

    @given(st.integers(max_value=-1))
    @settings(max_examples=50)
    def test_stats_rejects_negative_commits(self, negative):
        """Property: Stats rejects negative commit counts."""
        with pytest.raises(ValidationError):
            TimeWindowStats(commits=negative)

    @given(st.integers(max_value=-1))
    @settings(max_examples=50)
    def test_stats_rejects_negative_lines_added(self, negative):
        """Property: Stats rejects negative lines_added."""
        with pytest.raises(ValidationError):
            TimeWindowStats(lines_added=negative, lines_net=negative)

    @given(st.integers(max_value=-1))
    @settings(max_examples=50)
    def test_stats_rejects_negative_lines_removed(self, negative):
        """Property: Stats rejects negative lines_removed."""
        with pytest.raises(ValidationError):
            TimeWindowStats(lines_removed=negative, lines_net=0 - negative)

    @given(st.integers(max_value=-1))
    @settings(max_examples=50)
    def test_stats_rejects_negative_contributors(self, negative):
        """Property: Stats rejects negative contributor counts."""
        with pytest.raises(ValidationError):
            TimeWindowStats(contributors=negative)

    @given(valid_time_window_stats())
    @settings(max_examples=100)
    def test_stats_to_dict_includes_contributors_conditionally(self, stats: TimeWindowStats):
        """Property: to_dict() includes contributors only if > 0."""
        data = stats.to_dict()

        if stats.contributors > 0:
            assert "contributors" in data
            assert data["contributors"] == stats.contributors
        else:
            # May or may not include it when zero, but if included should be 0
            if "contributors" in data:
                assert data["contributors"] == 0

    @given(st.lists(valid_time_window_stats(), min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_stats_sum_of_list_equals_sequential_addition(self, stats_list):
        """Property: Sum of list equals sequential addition."""
        # Calculate sum using sequential addition
        sequential_sum = stats_list[0]
        for stats in stats_list[1:]:
            sequential_sum = sequential_sum + stats

        # Calculate using reduce
        from functools import reduce

        reduce_sum = reduce(lambda a, b: a + b, stats_list)

        assert sequential_sum.commits == reduce_sum.commits
        assert sequential_sum.lines_added == reduce_sum.lines_added
        assert sequential_sum.lines_removed == reduce_sum.lines_removed
        assert sequential_sum.lines_net == reduce_sum.lines_net


# =============================================================================
# Integration Property Tests
# =============================================================================


class TestTimeWindowIntegrationProperties:
    """Property tests for TimeWindow and TimeWindowStats interaction."""

    @given(
        valid_time_window(),
        st.dictionaries(st.text(min_size=1, max_size=10), valid_time_window_stats()),
    )
    @settings(max_examples=50)
    def test_time_window_can_map_to_stats(self, window, stats_dict):
        """Property: TimeWindow names can be used as keys for stats."""
        # This simulates the common pattern: Dict[str, TimeWindowStats]
        # where the key is a window name

        if window.name in stats_dict:
            stats = stats_dict[window.name]
            assert isinstance(stats, TimeWindowStats)

            # Stats should be valid
            assert stats.lines_net == stats.lines_added - stats.lines_removed

    @given(st.lists(valid_time_window(), min_size=2, max_size=5, unique_by=lambda w: w.name))
    @settings(max_examples=50)
    def test_unique_window_names_create_unique_keys(self, windows):
        """Property: Unique TimeWindow names create unique dictionary keys."""
        window_dict = {w.name: w for w in windows}

        # Should have same number of entries
        assert len(window_dict) == len(windows)

        # Each window should be retrievable
        for window in windows:
            assert window.name in window_dict
            assert window_dict[window.name] == window
