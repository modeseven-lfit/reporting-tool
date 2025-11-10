# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for AuthorMetrics domain model.

Tests cover:
- Validation (empty email, negative counts, inconsistent net calculations)
- Edge cases (empty name normalization, missing domains)
- Dictionary conversion (to_dict, from_dict)
- Legacy format compatibility (repositories_touched as sets)
- Property methods (totals, window getters, affiliation)
"""

import pytest

from domain.author_metrics import AuthorMetrics


class TestAuthorMetricsValidation:
    """Test AuthorMetrics validation rules."""

    def test_empty_email_raises_error(self):
        """Empty email should raise ValueError."""
        with pytest.raises(ValueError, match="email cannot be empty"):
            AuthorMetrics(name="John Doe", email="")

    def test_empty_name_defaults_to_email(self):
        """Empty name should default to email address."""
        author = AuthorMetrics(name="", email="john@example.com")
        assert author.name == "john@example.com"

    def test_negative_commits_raises_error(self):
        """Negative commit counts should raise ValueError."""
        with pytest.raises(ValueError, match="commits.*must be non-negative"):
            AuthorMetrics(name="John Doe", email="john@example.com", commits={"1y": -5})

    def test_negative_lines_added_raises_error(self):
        """Negative lines_added should raise ValueError."""
        with pytest.raises(ValueError, match="lines_added.*must be non-negative"):
            AuthorMetrics(name="John Doe", email="john@example.com", lines_added={"1y": -100})

    def test_negative_lines_removed_raises_error(self):
        """Negative lines_removed should raise ValueError."""
        with pytest.raises(ValueError, match="lines_removed.*must be non-negative"):
            AuthorMetrics(name="John Doe", email="john@example.com", lines_removed={"90d": -50})

    def test_negative_repositories_touched_raises_error(self):
        """Negative repositories_touched should raise ValueError."""
        with pytest.raises(ValueError, match="repositories_touched.*must be non-negative"):
            AuthorMetrics(
                name="John Doe", email="john@example.com", repositories_touched={"30d": -2}
            )

    def test_inconsistent_lines_net_raises_error(self):
        """lines_net must equal lines_added - lines_removed."""
        with pytest.raises(ValueError, match="lines_net.*must equal"):
            AuthorMetrics(
                name="John Doe",
                email="john@example.com",
                commits={"1y": 10},
                lines_added={"1y": 200},
                lines_removed={"1y": 50},
                lines_net={"1y": 100},  # Should be 150
            )

    def test_consistent_lines_net_valid(self):
        """Correctly calculated lines_net should be valid."""
        author = AuthorMetrics(
            name="John Doe",
            email="john@example.com",
            commits={"1y": 10},
            lines_added={"1y": 200},
            lines_removed={"1y": 50},
            lines_net={"1y": 150},  # 200 - 50
        )
        assert author.lines_net["1y"] == 150

    def test_negative_lines_net_valid_if_consistent(self):
        """Negative lines_net is valid if it equals added - removed."""
        author = AuthorMetrics(
            name="John Doe",
            email="john@example.com",
            lines_added={"1y": 50},
            lines_removed={"1y": 200},
            lines_net={"1y": -150},  # Net deletion
        )
        assert author.lines_net["1y"] == -150


class TestAuthorMetricsCreation:
    """Test AuthorMetrics instance creation."""

    def test_minimal_author(self):
        """Create author with only required fields."""
        author = AuthorMetrics(name="Jane Doe", email="jane@example.com")
        assert author.name == "Jane Doe"
        assert author.email == "jane@example.com"
        assert author.username == ""
        assert author.domain == "unknown"
        assert author.commits == {}
        assert author.lines_added == {}
        assert author.lines_removed == {}
        assert author.lines_net == {}
        assert author.repositories_touched == {}

    def test_full_author(self):
        """Create author with all fields populated."""
        author = AuthorMetrics(
            name="John Smith",
            email="jsmith@acme.com",
            username="jsmith",
            domain="acme.com",
            commits={"1y": 100, "90d": 25, "30d": 10},
            lines_added={"1y": 5000, "90d": 1200, "30d": 400},
            lines_removed={"1y": 2000, "90d": 500, "30d": 150},
            lines_net={"1y": 3000, "90d": 700, "30d": 250},
            repositories_touched={"1y": 5, "90d": 3, "30d": 2},
        )
        assert author.name == "John Smith"
        assert author.email == "jsmith@acme.com"
        assert author.username == "jsmith"
        assert author.domain == "acme.com"
        assert author.commits["1y"] == 100
        assert author.lines_added["90d"] == 1200
        assert author.repositories_touched["30d"] == 2

    def test_zero_metrics_valid(self):
        """Zero counts should be valid."""
        author = AuthorMetrics(
            name="New Dev",
            email="newdev@example.com",
            commits={"1y": 0},
            lines_added={"1y": 0},
            lines_removed={"1y": 0},
            lines_net={"1y": 0},
        )
        assert author.commits["1y"] == 0
        assert author.total_commits == 0


class TestAuthorMetricsDictConversion:
    """Test dictionary serialization and deserialization."""

    def test_to_dict_full(self):
        """Convert full author to dictionary."""
        author = AuthorMetrics(
            name="Alice",
            email="alice@example.com",
            username="alice",
            domain="example.com",
            commits={"1y": 50},
            lines_added={"1y": 1000},
            lines_removed={"1y": 200},
            lines_net={"1y": 800},
            repositories_touched={"1y": 3},
        )
        data = author.to_dict()

        assert data["name"] == "Alice"
        assert data["email"] == "alice@example.com"
        assert data["username"] == "alice"
        assert data["domain"] == "example.com"
        assert data["commits"] == {"1y": 50}
        assert data["lines_added"] == {"1y": 1000}
        assert data["lines_removed"] == {"1y": 200}
        assert data["lines_net"] == {"1y": 800}
        assert data["repositories_touched"] == {"1y": 3}

    def test_to_dict_minimal(self):
        """Convert minimal author to dictionary."""
        author = AuthorMetrics(name="Bob", email="bob@test.com")
        data = author.to_dict()

        assert data["name"] == "Bob"
        assert data["email"] == "bob@test.com"
        assert data["username"] == ""
        assert data["domain"] == "unknown"
        assert data["commits"] == {}

    def test_from_dict_full(self):
        """Create author from full dictionary."""
        data = {
            "name": "Charlie",
            "email": "charlie@company.com",
            "username": "charlie",
            "domain": "company.com",
            "commits": {"1y": 75, "90d": 20},
            "lines_added": {"1y": 3000, "90d": 800},
            "lines_removed": {"1y": 1000, "90d": 300},
            "lines_net": {"1y": 2000, "90d": 500},
            "repositories_touched": {"1y": 4, "90d": 2},
        }
        author = AuthorMetrics.from_dict(data)

        assert author.name == "Charlie"
        assert author.email == "charlie@company.com"
        assert author.username == "charlie"
        assert author.domain == "company.com"
        assert author.commits["1y"] == 75
        assert author.lines_added["90d"] == 800

    def test_from_dict_minimal(self):
        """Create author from minimal dictionary."""
        data = {"email": "minimal@test.com"}
        author = AuthorMetrics.from_dict(data)

        # Email normalized to name when name is missing
        assert author.email == "minimal@test.com"
        assert author.name == "minimal@test.com"
        assert author.domain == "unknown"

    def test_from_dict_repositories_touched_as_sets(self):
        """Convert legacy repositories_touched sets to counts."""
        data = {
            "email": "legacy@test.com",
            "name": "Legacy User",
            "repositories_touched": {"1y": {"repo1", "repo2", "repo3"}, "90d": {"repo1", "repo2"}},
        }
        author = AuthorMetrics.from_dict(data)

        assert author.repositories_touched["1y"] == 3
        assert author.repositories_touched["90d"] == 2

    def test_from_dict_repositories_touched_mixed_types(self):
        """Handle mixed int/set values in repositories_touched."""
        data = {
            "email": "mixed@test.com",
            "name": "Mixed User",
            "repositories_touched": {
                "1y": {"repo1", "repo2"},  # Set
                "90d": 5,  # Already an int
            },
        }
        author = AuthorMetrics.from_dict(data)

        assert author.repositories_touched["1y"] == 2
        assert author.repositories_touched["90d"] == 5

    def test_round_trip_conversion(self):
        """Test to_dict -> from_dict preserves data."""
        original = AuthorMetrics(
            name="Round Trip",
            email="roundtrip@test.com",
            username="rtuser",
            domain="test.com",
            commits={"1y": 42},
            lines_added={"1y": 1000},
            lines_removed={"1y": 200},
            lines_net={"1y": 800},
            repositories_touched={"1y": 2},
        )

        data = original.to_dict()
        restored = AuthorMetrics.from_dict(data)

        assert restored.name == original.name
        assert restored.email == original.email
        assert restored.username == original.username
        assert restored.domain == original.domain
        assert restored.commits == original.commits
        assert restored.lines_added == original.lines_added
        assert restored.lines_removed == original.lines_removed
        assert restored.lines_net == original.lines_net
        assert restored.repositories_touched == original.repositories_touched


class TestAuthorMetricsProperties:
    """Test property methods and computed values."""

    def test_total_commits(self):
        """Sum commits across all windows."""
        author = AuthorMetrics(
            name="Test", email="test@example.com", commits={"1y": 100, "90d": 30, "30d": 10}
        )
        assert author.total_commits == 140

    def test_total_commits_empty(self):
        """Total commits should be 0 when no windows."""
        author = AuthorMetrics(name="Test", email="test@example.com")
        assert author.total_commits == 0

    def test_total_lines_added(self):
        """Sum lines_added across all windows."""
        author = AuthorMetrics(
            name="Test", email="test@example.com", lines_added={"1y": 5000, "90d": 1500, "30d": 500}
        )
        assert author.total_lines_added == 7000

    def test_total_lines_removed(self):
        """Sum lines_removed across all windows."""
        author = AuthorMetrics(
            name="Test",
            email="test@example.com",
            lines_removed={"1y": 2000, "90d": 600, "30d": 200},
        )
        assert author.total_lines_removed == 2800

    def test_total_lines_net(self):
        """Sum lines_net across all windows."""
        author = AuthorMetrics(
            name="Test", email="test@example.com", lines_net={"1y": 3000, "90d": 900, "30d": 300}
        )
        assert author.total_lines_net == 4200

    def test_total_lines_net_negative(self):
        """Total can be negative for net deleters."""
        author = AuthorMetrics(
            name="Cleanup",
            email="cleanup@example.com",
            lines_added={"1y": 100},
            lines_removed={"1y": 500},
            lines_net={"1y": -400},
        )
        assert author.total_lines_net == -400

    def test_is_affiliated_true(self):
        """Author with known domain is affiliated."""
        author = AuthorMetrics(name="Test", email="test@company.com", domain="company.com")
        assert author.is_affiliated is True

    def test_is_affiliated_false_unknown(self):
        """Author with 'unknown' domain is not affiliated."""
        author = AuthorMetrics(name="Test", email="test@personal.com", domain="unknown")
        assert author.is_affiliated is False

    def test_is_affiliated_false_empty(self):
        """Author with empty domain is not affiliated."""
        author = AuthorMetrics(name="Test", email="test@example.com", domain="")
        assert author.is_affiliated is False

    def test_get_commits_in_window(self):
        """Get commits for specific window."""
        author = AuthorMetrics(
            name="Test", email="test@example.com", commits={"1y": 100, "90d": 30}
        )
        assert author.get_commits_in_window("1y") == 100
        assert author.get_commits_in_window("90d") == 30
        assert author.get_commits_in_window("30d") == 0  # Missing

    def test_get_lines_added_in_window(self):
        """Get lines_added for specific window."""
        author = AuthorMetrics(
            name="Test", email="test@example.com", lines_added={"1y": 5000, "90d": 1500}
        )
        assert author.get_lines_added_in_window("1y") == 5000
        assert author.get_lines_added_in_window("30d") == 0

    def test_get_lines_removed_in_window(self):
        """Get lines_removed for specific window."""
        author = AuthorMetrics(name="Test", email="test@example.com", lines_removed={"1y": 2000})
        assert author.get_lines_removed_in_window("1y") == 2000
        assert author.get_lines_removed_in_window("90d") == 0

    def test_get_lines_net_in_window(self):
        """Get lines_net for specific window."""
        author = AuthorMetrics(
            name="Test", email="test@example.com", lines_net={"1y": 3000, "90d": -500}
        )
        assert author.get_lines_net_in_window("1y") == 3000
        assert author.get_lines_net_in_window("90d") == -500
        assert author.get_lines_net_in_window("30d") == 0

    def test_get_repositories_in_window(self):
        """Get repositories_touched for specific window."""
        author = AuthorMetrics(
            name="Test", email="test@example.com", repositories_touched={"1y": 5, "90d": 3}
        )
        assert author.get_repositories_in_window("1y") == 5
        assert author.get_repositories_in_window("90d") == 3
        assert author.get_repositories_in_window("30d") == 0


class TestAuthorMetricsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_name(self):
        """Handle unicode characters in name."""
        author = AuthorMetrics(name="José García", email="jose@example.com")
        assert author.name == "José García"

    def test_unicode_email(self):
        """Handle unicode in email (internationalized domains)."""
        author = AuthorMetrics(name="Test", email="test@例え.jp")
        assert author.email == "test@例え.jp"

    def test_very_large_metrics(self):
        """Handle very large metric values."""
        author = AuthorMetrics(
            name="Prolific",
            email="prolific@example.com",
            commits={"1y": 999999},
            lines_added={"1y": 10000000},
            lines_removed={"1y": 5000000},
            lines_net={"1y": 5000000},
        )
        assert author.total_commits == 999999
        assert author.total_lines_added == 10000000

    def test_many_time_windows(self):
        """Handle many different time windows."""
        windows = {f"{i}d": i * 10 for i in range(1, 101)}
        author = AuthorMetrics(name="Test", email="test@example.com", commits=windows)
        assert len(author.commits) == 100
        assert author.total_commits == sum(windows.values())

    def test_special_characters_in_username(self):
        """Handle special characters in username."""
        author = AuthorMetrics(name="Test", email="test@example.com", username="user-name_123.test")
        assert author.username == "user-name_123.test"

    def test_email_only_domain_extraction(self):
        """Email with no name should use email as name."""
        author = AuthorMetrics(name="", email="standalone@domain.com")
        assert author.name == "standalone@domain.com"

    def test_whitespace_trimming_not_automatic(self):
        """Whitespace is preserved (caller's responsibility to clean)."""
        author = AuthorMetrics(name="  Spaces  ", email="  test@example.com  ")
        assert author.name == "  Spaces  "
        assert author.email == "  test@example.com  "
