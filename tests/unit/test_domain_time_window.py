# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for TimeWindow and TimeWindowStats domain models.

Tests cover:
- TimeWindow validation (positive days, non-empty name, ISO 8601 format)
- TimeWindowStats validation (non-negative counts, net consistency)
- Dictionary conversion (to_dict, from_dict)
- TimeWindowStats addition operator
- Edge cases (very large values, many windows, unicode)
"""

import dataclasses

import pytest

from cli.errors import ValidationError
from domain.time_window import TimeWindow, TimeWindowStats


class TestTimeWindowValidation:
    """Test TimeWindow validation rules."""

    def test_zero_days_raises_error(self):
        """Days must be positive."""
        with pytest.raises(ValidationError):
            TimeWindow(
                name="0d",
                days=0,
                start_date="2024-01-01T00:00:00Z",
                end_date="2024-01-01T00:00:00Z",
            )

    def test_negative_days_raises_error(self):
        """Negative days should raise error."""
        with pytest.raises(ValidationError):
            TimeWindow(
                name="invalid",
                days=-30,
                start_date="2024-01-01T00:00:00Z",
                end_date="2024-01-31T00:00:00Z",
            )

    def test_empty_name_raises_error(self):
        """Empty name should raise error."""
        with pytest.raises(ValidationError):
            TimeWindow(
                name="", days=30, start_date="2024-01-01T00:00:00Z", end_date="2024-01-31T00:00:00Z"
            )

    def test_invalid_start_date_format_raises_error(self):
        """Invalid ISO 8601 start_date should raise error."""
        with pytest.raises(ValidationError):
            TimeWindow(
                name="30d", days=30, start_date="not-a-date", end_date="2024-01-31T00:00:00Z"
            )

    def test_invalid_end_date_format_raises_error(self):
        """Invalid ISO 8601 end_date should raise error."""
        with pytest.raises(ValidationError):
            TimeWindow(
                name="30d", days=30, start_date="2024-01-01T00:00:00Z", end_date="2024-13-99"
            )

    def test_valid_iso_8601_with_z_suffix(self):
        """ISO 8601 with Z suffix should be valid."""
        window = TimeWindow(
            name="30d", days=30, start_date="2024-01-01T00:00:00Z", end_date="2024-01-31T23:59:59Z"
        )
        assert window.start_date == "2024-01-01T00:00:00Z"
        assert window.end_date == "2024-01-31T23:59:59Z"

    def test_valid_iso_8601_with_timezone(self):
        """ISO 8601 with timezone offset should be valid."""
        window = TimeWindow(
            name="1y",
            days=365,
            start_date="2023-01-01T00:00:00+00:00",
            end_date="2024-01-01T00:00:00+00:00",
        )
        assert window.days == 365

    def test_valid_iso_8601_no_timezone(self):
        """ISO 8601 without timezone should be valid."""
        window = TimeWindow(
            name="90d", days=90, start_date="2024-01-01T00:00:00", end_date="2024-03-31T23:59:59"
        )
        assert window.name == "90d"


class TestTimeWindowCreation:
    """Test TimeWindow instance creation."""

    def test_minimal_window(self):
        """Create window with minimal valid parameters."""
        window = TimeWindow(
            name="7d", days=7, start_date="2024-01-01T00:00:00Z", end_date="2024-01-08T00:00:00Z"
        )
        assert window.name == "7d"
        assert window.days == 7
        assert window.start_date == "2024-01-01T00:00:00Z"
        assert window.end_date == "2024-01-08T00:00:00Z"

    def test_standard_windows(self):
        """Create standard time windows (30d, 90d, 1y)."""
        w30 = TimeWindow(
            name="30d", days=30, start_date="2024-01-01T00:00:00Z", end_date="2024-01-31T00:00:00Z"
        )
        assert w30.name == "30d"
        assert w30.days == 30

        w90 = TimeWindow(
            name="90d", days=90, start_date="2023-10-03T00:00:00Z", end_date="2024-01-01T00:00:00Z"
        )
        assert w90.name == "90d"
        assert w90.days == 90

        w1y = TimeWindow(
            name="1y", days=365, start_date="2023-01-01T00:00:00Z", end_date="2024-01-01T00:00:00Z"
        )
        assert w1y.name == "1y"
        assert w1y.days == 365

    def test_frozen_dataclass(self):
        """TimeWindow should be immutable (frozen)."""
        window = TimeWindow(
            name="30d", days=30, start_date="2024-01-01T00:00:00Z", end_date="2024-01-31T00:00:00Z"
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            window.days = 60


class TestTimeWindowDictConversion:
    """Test dictionary serialization and deserialization."""

    def test_to_dict(self):
        """Convert TimeWindow to dictionary."""
        window = TimeWindow(
            name="90d", days=90, start_date="2024-01-01T00:00:00Z", end_date="2024-03-31T23:59:59Z"
        )
        data = window.to_dict()

        assert data["days"] == 90
        assert data["start"] == "2024-01-01T00:00:00Z"
        assert data["end"] == "2024-03-31T23:59:59Z"
        # Note: name is not in dict (passed separately in from_dict)

    def test_from_dict(self):
        """Create TimeWindow from dictionary."""
        data = {"days": 365, "start": "2023-01-01T00:00:00Z", "end": "2024-01-01T00:00:00Z"}
        window = TimeWindow.from_dict("1y", data)

        assert window.name == "1y"
        assert window.days == 365
        assert window.start_date == "2023-01-01T00:00:00Z"
        assert window.end_date == "2024-01-01T00:00:00Z"

    def test_round_trip_conversion(self):
        """Test to_dict -> from_dict preserves data."""
        original = TimeWindow(
            name="30d", days=30, start_date="2024-06-01T00:00:00Z", end_date="2024-07-01T00:00:00Z"
        )

        data = original.to_dict()
        restored = TimeWindow.from_dict("30d", data)

        assert restored.name == original.name
        assert restored.days == original.days
        assert restored.start_date == original.start_date
        assert restored.end_date == original.end_date


class TestTimeWindowStatsValidation:
    """Test TimeWindowStats validation rules."""

    def test_negative_commits_raises_error(self):
        """Negative commits should raise error."""
        with pytest.raises(ValidationError):
            TimeWindowStats(commits=-5)

    def test_negative_lines_added_raises_error(self):
        """Negative lines_added should raise error."""
        with pytest.raises(ValidationError):
            TimeWindowStats(lines_added=-100)

    def test_negative_lines_removed_raises_error(self):
        """Negative lines_removed should raise error."""
        with pytest.raises(ValidationError):
            TimeWindowStats(lines_removed=-50)

    def test_negative_contributors_raises_error(self):
        """Negative contributors should raise error."""
        with pytest.raises(ValidationError):
            TimeWindowStats(contributors=-3)

    def test_inconsistent_lines_net_raises_error(self):
        """lines_net must equal lines_added - lines_removed."""
        with pytest.raises(ValidationError):
            TimeWindowStats(
                lines_added=200,
                lines_removed=50,
                lines_net=100,  # Should be 150
            )

    def test_consistent_lines_net_valid(self):
        """Correctly calculated lines_net should be valid."""
        stats = TimeWindowStats(commits=10, lines_added=200, lines_removed=50, lines_net=150)
        assert stats.lines_net == 150

    def test_negative_lines_net_valid_if_consistent(self):
        """Negative lines_net is valid if it equals added - removed."""
        stats = TimeWindowStats(
            lines_added=50,
            lines_removed=200,
            lines_net=-150,  # Net deletion
        )
        assert stats.lines_net == -150

    def test_zero_values_valid(self):
        """All zeros should be valid."""
        stats = TimeWindowStats()
        assert stats.commits == 0
        assert stats.lines_added == 0
        assert stats.lines_removed == 0
        assert stats.lines_net == 0
        assert stats.contributors == 0


class TestTimeWindowStatsCreation:
    """Test TimeWindowStats instance creation."""

    def test_default_values(self):
        """Default stats should be all zeros."""
        stats = TimeWindowStats()
        assert stats.commits == 0
        assert stats.lines_added == 0
        assert stats.lines_removed == 0
        assert stats.lines_net == 0
        assert stats.contributors == 0

    def test_partial_values(self):
        """Create stats with partial values."""
        stats = TimeWindowStats(
            commits=25,
            lines_added=1000,
            lines_removed=0,
            lines_net=1000,  # Must be explicitly provided
        )
        assert stats.commits == 25
        assert stats.lines_added == 1000
        assert stats.lines_removed == 0
        assert stats.lines_net == 1000  # 1000 - 0
        assert stats.contributors == 0

    def test_full_values(self):
        """Create stats with all values."""
        stats = TimeWindowStats(
            commits=100, lines_added=5000, lines_removed=2000, lines_net=3000, contributors=15
        )
        assert stats.commits == 100
        assert stats.lines_added == 5000
        assert stats.lines_removed == 2000
        assert stats.lines_net == 3000
        assert stats.contributors == 15


class TestTimeWindowStatsDictConversion:
    """Test dictionary serialization and deserialization."""

    def test_to_dict_with_contributors(self):
        """Convert stats with contributors to dictionary."""
        stats = TimeWindowStats(
            commits=50, lines_added=2000, lines_removed=500, lines_net=1500, contributors=10
        )
        data = stats.to_dict()

        assert data["commits"] == 50
        assert data["lines_added"] == 2000
        assert data["lines_removed"] == 500
        assert data["lines_net"] == 1500
        assert data["contributors"] == 10

    def test_to_dict_without_contributors(self):
        """Convert stats without contributors to dictionary."""
        stats = TimeWindowStats(commits=20, lines_added=1000, lines_removed=200, lines_net=800)
        data = stats.to_dict()

        assert data["commits"] == 20
        assert data["lines_added"] == 1000
        assert data["lines_removed"] == 200
        assert data["lines_net"] == 800
        assert "contributors" not in data  # Omitted when 0

    def test_from_dict_full(self):
        """Create stats from full dictionary."""
        data = {
            "commits": 75,
            "lines_added": 3000,
            "lines_removed": 1000,
            "lines_net": 2000,
            "contributors": 12,
        }
        stats = TimeWindowStats.from_dict(data)

        assert stats.commits == 75
        assert stats.lines_added == 3000
        assert stats.lines_removed == 1000
        assert stats.lines_net == 2000
        assert stats.contributors == 12

    def test_from_dict_partial(self):
        """Create stats from partial dictionary."""
        data = {"commits": 30, "lines_added": 1500, "lines_removed": 0, "lines_net": 1500}
        stats = TimeWindowStats.from_dict(data)

        assert stats.commits == 30
        assert stats.lines_added == 1500
        assert stats.lines_removed == 0
        assert stats.lines_net == 1500
        assert stats.contributors == 0

    def test_from_dict_empty(self):
        """Create stats from empty dictionary."""
        stats = TimeWindowStats.from_dict({})
        assert stats.commits == 0
        assert stats.lines_added == 0
        assert stats.lines_removed == 0
        assert stats.lines_net == 0
        assert stats.contributors == 0

    def test_round_trip_conversion(self):
        """Test to_dict -> from_dict preserves data."""
        original = TimeWindowStats(
            commits=42, lines_added=2100, lines_removed=700, lines_net=1400, contributors=8
        )

        data = original.to_dict()
        restored = TimeWindowStats.from_dict(data)

        assert restored.commits == original.commits
        assert restored.lines_added == original.lines_added
        assert restored.lines_removed == original.lines_removed
        assert restored.lines_net == original.lines_net
        assert restored.contributors == original.contributors


class TestTimeWindowStatsAddition:
    """Test __add__ operator for stats aggregation."""

    def test_add_two_stats(self):
        """Add two TimeWindowStats together."""
        stats1 = TimeWindowStats(
            commits=50, lines_added=2000, lines_removed=500, lines_net=1500, contributors=5
        )
        stats2 = TimeWindowStats(
            commits=30, lines_added=1000, lines_removed=300, lines_net=700, contributors=3
        )

        result = stats1 + stats2

        assert result.commits == 80
        assert result.lines_added == 3000
        assert result.lines_removed == 800
        assert result.lines_net == 2200
        assert result.contributors == 8

    def test_add_with_zero_stats(self):
        """Add stats to zero stats (identity)."""
        stats = TimeWindowStats(
            commits=25, lines_added=1000, lines_removed=200, lines_net=800, contributors=4
        )
        zero = TimeWindowStats()

        result = stats + zero

        assert result.commits == stats.commits
        assert result.lines_added == stats.lines_added
        assert result.lines_removed == stats.lines_removed
        assert result.lines_net == stats.lines_net
        assert result.contributors == stats.contributors

    def test_add_multiple_stats(self):
        """Add multiple stats together."""
        s1 = TimeWindowStats(commits=10, lines_added=500, lines_removed=100, lines_net=400)
        s2 = TimeWindowStats(commits=20, lines_added=1000, lines_removed=200, lines_net=800)
        s3 = TimeWindowStats(commits=15, lines_added=750, lines_removed=150, lines_net=600)

        result = s1 + s2 + s3

        assert result.commits == 45
        assert result.lines_added == 2250
        assert result.lines_removed == 450
        assert result.lines_net == 1800

    def test_add_with_negative_net(self):
        """Add stats with negative net values."""
        stats1 = TimeWindowStats(lines_added=100, lines_removed=500, lines_net=-400)
        stats2 = TimeWindowStats(lines_added=200, lines_removed=100, lines_net=100)

        result = stats1 + stats2

        assert result.lines_added == 300
        assert result.lines_removed == 600
        assert result.lines_net == -300

    def test_add_returns_new_instance(self):
        """Addition should return a new instance, not modify originals."""
        stats1 = TimeWindowStats(commits=10)
        stats2 = TimeWindowStats(commits=20)

        result = stats1 + stats2

        assert result.commits == 30
        assert stats1.commits == 10  # Unchanged
        assert stats2.commits == 20  # Unchanged

    def test_add_with_non_stats_returns_not_implemented(self):
        """Adding non-TimeWindowStats should return NotImplemented."""
        stats = TimeWindowStats(commits=10)
        result = stats.__add__(42)
        assert result is NotImplemented


class TestTimeWindowEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_days(self):
        """Handle very large day counts."""
        window = TimeWindow(
            name="10y",
            days=3650,
            start_date="2014-01-01T00:00:00Z",
            end_date="2024-01-01T00:00:00Z",
        )
        assert window.days == 3650

    def test_single_day_window(self):
        """Handle single day window."""
        window = TimeWindow(
            name="1d", days=1, start_date="2024-01-01T00:00:00Z", end_date="2024-01-02T00:00:00Z"
        )
        assert window.days == 1

    def test_unicode_window_name(self):
        """Handle unicode in window name."""
        window = TimeWindow(
            name="año", days=365, start_date="2023-01-01T00:00:00Z", end_date="2024-01-01T00:00:00Z"
        )
        assert window.name == "año"

    def test_custom_window_names(self):
        """Handle custom window naming conventions."""
        custom = TimeWindow(
            name="quarter_1_2024",
            days=91,
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-04-01T00:00:00Z",
        )
        assert custom.name == "quarter_1_2024"


class TestTimeWindowStatsEdgeCases:
    """Test TimeWindowStats edge cases."""

    def test_very_large_values(self):
        """Handle very large metric values."""
        stats = TimeWindowStats(
            commits=1000000,
            lines_added=100000000,
            lines_removed=50000000,
            lines_net=50000000,
            contributors=10000,
        )
        assert stats.commits == 1000000
        assert stats.lines_added == 100000000

    def test_large_negative_net(self):
        """Handle large negative net (major code deletion)."""
        stats = TimeWindowStats(lines_added=1000, lines_removed=1000000, lines_net=-999000)
        assert stats.lines_net == -999000

    def test_equal_added_and_removed(self):
        """Handle case where added equals removed (net zero)."""
        stats = TimeWindowStats(lines_added=5000, lines_removed=5000, lines_net=0)
        assert stats.lines_net == 0
