# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for OrganizationMetrics domain model.

Tests cover:
- Validation (empty domain, negative counts, inconsistent net calculations)
- Edge cases (unknown domain, zero metrics, very large values)
- Dictionary conversion (to_dict, from_dict)
- Property methods (totals, window getters, is_known_org)
"""

import pytest

from domain.organization_metrics import OrganizationMetrics


class TestOrganizationMetricsValidation:
    """Test OrganizationMetrics validation rules."""

    def test_empty_domain_raises_error(self):
        """Empty domain should raise ValueError."""
        with pytest.raises(ValueError, match="domain cannot be empty"):
            OrganizationMetrics(domain="")

    def test_negative_contributor_count_raises_error(self):
        """Negative contributor_count should raise ValueError."""
        with pytest.raises(ValueError, match="contributor_count must be non-negative"):
            OrganizationMetrics(domain="example.com", contributor_count=-5)

    def test_negative_commits_raises_error(self):
        """Negative commit counts should raise ValueError."""
        with pytest.raises(ValueError, match="commits.*must be non-negative"):
            OrganizationMetrics(domain="example.com", commits={"1y": -10})

    def test_negative_lines_added_raises_error(self):
        """Negative lines_added should raise ValueError."""
        with pytest.raises(ValueError, match="lines_added.*must be non-negative"):
            OrganizationMetrics(domain="example.com", lines_added={"1y": -1000})

    def test_negative_lines_removed_raises_error(self):
        """Negative lines_removed should raise ValueError."""
        with pytest.raises(ValueError, match="lines_removed.*must be non-negative"):
            OrganizationMetrics(domain="example.com", lines_removed={"90d": -500})

    def test_negative_repositories_count_raises_error(self):
        """Negative repositories_count should raise ValueError."""
        with pytest.raises(ValueError, match="repositories_count.*must be non-negative"):
            OrganizationMetrics(domain="example.com", repositories_count={"30d": -3})

    def test_inconsistent_lines_net_raises_error(self):
        """lines_net must equal lines_added - lines_removed."""
        with pytest.raises(ValueError, match="lines_net.*must equal"):
            OrganizationMetrics(
                domain="example.com",
                commits={"1y": 100},
                lines_added={"1y": 5000},
                lines_removed={"1y": 1000},
                lines_net={"1y": 3000},  # Should be 4000
            )

    def test_consistent_lines_net_valid(self):
        """Correctly calculated lines_net should be valid."""
        org = OrganizationMetrics(
            domain="example.com",
            commits={"1y": 100},
            lines_added={"1y": 5000},
            lines_removed={"1y": 1000},
            lines_net={"1y": 4000},
        )
        assert org.lines_net["1y"] == 4000

    def test_negative_lines_net_valid_if_consistent(self):
        """Negative lines_net is valid if it equals added - removed."""
        org = OrganizationMetrics(
            domain="cleanup.com",
            lines_added={"1y": 500},
            lines_removed={"1y": 2000},
            lines_net={"1y": -1500},  # Net deletion
        )
        assert org.lines_net["1y"] == -1500


class TestOrganizationMetricsCreation:
    """Test OrganizationMetrics instance creation."""

    def test_minimal_organization(self):
        """Create organization with only domain."""
        org = OrganizationMetrics(domain="example.com")

        assert org.domain == "example.com"
        assert org.contributor_count == 0
        assert org.commits == {}
        assert org.lines_added == {}
        assert org.lines_removed == {}
        assert org.lines_net == {}
        assert org.repositories_count == {}

    def test_full_organization(self):
        """Create organization with all fields populated."""
        org = OrganizationMetrics(
            domain="acme.com",
            contributor_count=50,
            commits={"1y": 5000, "90d": 1200, "30d": 400},
            lines_added={"1y": 250000, "90d": 60000, "30d": 20000},
            lines_removed={"1y": 100000, "90d": 25000, "30d": 8000},
            lines_net={"1y": 150000, "90d": 35000, "30d": 12000},
            repositories_count={"1y": 25, "90d": 20, "30d": 15},
        )

        assert org.domain == "acme.com"
        assert org.contributor_count == 50
        assert org.commits["1y"] == 5000
        assert org.lines_added["90d"] == 60000
        assert org.repositories_count["30d"] == 15

    def test_zero_metrics_valid(self):
        """Zero counts should be valid."""
        org = OrganizationMetrics(
            domain="startup.com",
            contributor_count=0,
            commits={"1y": 0},
            lines_added={"1y": 0},
            lines_removed={"1y": 0},
            lines_net={"1y": 0},
        )
        assert org.contributor_count == 0
        assert org.total_commits == 0

    def test_unknown_domain_valid(self):
        """'unknown' domain should be valid."""
        org = OrganizationMetrics(domain="unknown")
        assert org.domain == "unknown"
        assert org.is_known_org is False


class TestOrganizationMetricsDictConversion:
    """Test dictionary serialization and deserialization."""

    def test_to_dict_minimal(self):
        """Convert minimal organization to dictionary."""
        org = OrganizationMetrics(domain="test.com")
        data = org.to_dict()

        assert data["domain"] == "test.com"
        assert data["contributor_count"] == 0
        assert data["commits"] == {}
        assert data["lines_added"] == {}
        assert data["lines_removed"] == {}
        assert data["lines_net"] == {}
        assert data["repositories_count"] == {}

    def test_to_dict_full(self):
        """Convert full organization to dictionary."""
        org = OrganizationMetrics(
            domain="company.com",
            contributor_count=100,
            commits={"1y": 10000, "90d": 2500},
            lines_added={"1y": 500000, "90d": 125000},
            lines_removed={"1y": 200000, "90d": 50000},
            lines_net={"1y": 300000, "90d": 75000},
            repositories_count={"1y": 50, "90d": 40},
        )
        data = org.to_dict()

        assert data["domain"] == "company.com"
        assert data["contributor_count"] == 100
        assert data["commits"]["1y"] == 10000
        assert data["lines_added"]["90d"] == 125000
        assert data["repositories_count"]["1y"] == 50

    def test_from_dict_minimal(self):
        """Create organization from minimal dictionary."""
        data = {"domain": "minimal.com"}
        org = OrganizationMetrics.from_dict(data)

        assert org.domain == "minimal.com"
        assert org.contributor_count == 0
        assert org.commits == {}

    def test_from_dict_full(self):
        """Create organization from full dictionary."""
        data = {
            "domain": "bigcorp.com",
            "contributor_count": 200,
            "commits": {"1y": 20000, "90d": 5000},
            "lines_added": {"1y": 1000000, "90d": 250000},
            "lines_removed": {"1y": 400000, "90d": 100000},
            "lines_net": {"1y": 600000, "90d": 150000},
            "repositories_count": {"1y": 100, "90d": 80},
        }
        org = OrganizationMetrics.from_dict(data)

        assert org.domain == "bigcorp.com"
        assert org.contributor_count == 200
        assert org.commits["90d"] == 5000
        assert org.lines_net["1y"] == 600000

    def test_from_dict_defaults(self):
        """from_dict should use defaults for missing fields."""
        data = {"domain": "defaults.com"}
        org = OrganizationMetrics.from_dict(data)

        assert org.domain == "defaults.com"
        assert org.contributor_count == 0
        assert org.commits == {}
        assert org.lines_added == {}

    def test_round_trip_conversion(self):
        """Test to_dict -> from_dict preserves data."""
        original = OrganizationMetrics(
            domain="roundtrip.com",
            contributor_count=75,
            commits={"1y": 7500, "90d": 1875},
            lines_added={"1y": 375000, "90d": 93750},
            lines_removed={"1y": 150000, "90d": 37500},
            lines_net={"1y": 225000, "90d": 56250},
            repositories_count={"1y": 37, "90d": 30},
        )

        data = original.to_dict()
        restored = OrganizationMetrics.from_dict(data)

        assert restored.domain == original.domain
        assert restored.contributor_count == original.contributor_count
        assert restored.commits == original.commits
        assert restored.lines_added == original.lines_added
        assert restored.lines_removed == original.lines_removed
        assert restored.lines_net == original.lines_net
        assert restored.repositories_count == original.repositories_count


class TestOrganizationMetricsProperties:
    """Test property methods and computed values."""

    def test_total_commits(self):
        """Sum commits across all windows."""
        org = OrganizationMetrics(domain="test.com", commits={"1y": 1000, "90d": 250, "30d": 80})
        assert org.total_commits == 1330

    def test_total_commits_empty(self):
        """Total commits should be 0 when no windows."""
        org = OrganizationMetrics(domain="test.com")
        assert org.total_commits == 0

    def test_total_lines_added(self):
        """Sum lines_added across all windows."""
        org = OrganizationMetrics(
            domain="test.com", lines_added={"1y": 50000, "90d": 12500, "30d": 4000}
        )
        assert org.total_lines_added == 66500

    def test_total_lines_removed(self):
        """Sum lines_removed across all windows."""
        org = OrganizationMetrics(
            domain="test.com", lines_removed={"1y": 20000, "90d": 5000, "30d": 1600}
        )
        assert org.total_lines_removed == 26600

    def test_total_lines_net(self):
        """Sum lines_net across all windows."""
        org = OrganizationMetrics(
            domain="test.com", lines_net={"1y": 30000, "90d": 7500, "30d": 2400}
        )
        assert org.total_lines_net == 39900

    def test_total_lines_net_negative(self):
        """Total can be negative for net deleters."""
        org = OrganizationMetrics(
            domain="cleanup.com",
            lines_added={"1y": 1000},
            lines_removed={"1y": 5000},
            lines_net={"1y": -4000},
        )
        assert org.total_lines_net == -4000

    def test_is_known_org_true(self):
        """Organization with real domain is known."""
        org = OrganizationMetrics(domain="company.com")
        assert org.is_known_org is True

    def test_is_known_org_false_unknown(self):
        """Organization with 'unknown' domain is not known."""
        org = OrganizationMetrics(domain="unknown")
        assert org.is_known_org is False

    def test_is_known_org_false_empty_domain(self):
        """Cannot create org with empty domain."""
        # This should raise error, not create org
        with pytest.raises(ValueError):
            OrganizationMetrics(domain="")

    def test_get_commits_in_window(self):
        """Get commits for specific window."""
        org = OrganizationMetrics(domain="test.com", commits={"1y": 1000, "90d": 250})
        assert org.get_commits_in_window("1y") == 1000
        assert org.get_commits_in_window("90d") == 250
        assert org.get_commits_in_window("30d") == 0  # Missing

    def test_get_lines_added_in_window(self):
        """Get lines_added for specific window."""
        org = OrganizationMetrics(domain="test.com", lines_added={"1y": 50000, "90d": 12500})
        assert org.get_lines_added_in_window("1y") == 50000
        assert org.get_lines_added_in_window("30d") == 0

    def test_get_lines_removed_in_window(self):
        """Get lines_removed for specific window."""
        org = OrganizationMetrics(domain="test.com", lines_removed={"1y": 20000})
        assert org.get_lines_removed_in_window("1y") == 20000
        assert org.get_lines_removed_in_window("90d") == 0

    def test_get_lines_net_in_window(self):
        """Get lines_net for specific window."""
        org = OrganizationMetrics(domain="test.com", lines_net={"1y": 30000, "90d": -500})
        assert org.get_lines_net_in_window("1y") == 30000
        assert org.get_lines_net_in_window("90d") == -500
        assert org.get_lines_net_in_window("30d") == 0

    def test_get_repositories_in_window(self):
        """Get repositories_count for specific window."""
        org = OrganizationMetrics(domain="test.com", repositories_count={"1y": 50, "90d": 40})
        assert org.get_repositories_in_window("1y") == 50
        assert org.get_repositories_in_window("90d") == 40
        assert org.get_repositories_in_window("30d") == 0


class TestOrganizationMetricsEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_unicode_domain(self):
        """Handle unicode characters in domain."""
        org = OrganizationMetrics(domain="例え.jp")
        assert org.domain == "例え.jp"

    def test_very_large_contributor_count(self):
        """Handle very large contributor counts."""
        org = OrganizationMetrics(domain="opensource.org", contributor_count=100000)
        assert org.contributor_count == 100000

    def test_very_large_metrics(self):
        """Handle very large metric values."""
        org = OrganizationMetrics(
            domain="huge.com",
            commits={"1y": 10000000},
            lines_added={"1y": 1000000000},
            lines_removed={"1y": 500000000},
            lines_net={"1y": 500000000},
        )
        assert org.total_commits == 10000000
        assert org.total_lines_added == 1000000000

    def test_many_time_windows(self):
        """Handle many different time windows."""
        windows = {f"{i}d": i * 100 for i in range(1, 101)}
        org = OrganizationMetrics(domain="many-windows.com", commits=windows)
        assert len(org.commits) == 100
        assert org.total_commits == sum(windows.values())

    def test_special_characters_in_domain(self):
        """Handle special characters in domain."""
        org = OrganizationMetrics(domain="sub-domain.example.co.uk")
        assert org.domain == "sub-domain.example.co.uk"

    def test_numeric_domain(self):
        """Handle numeric-looking domains."""
        org = OrganizationMetrics(domain="123.456.com")
        assert org.domain == "123.456.com"

    def test_single_contributor(self):
        """Handle organization with single contributor."""
        org = OrganizationMetrics(domain="solo.com", contributor_count=1, commits={"1y": 100})
        assert org.contributor_count == 1

    def test_mixed_positive_negative_net(self):
        """Handle mixed positive and negative net across windows."""
        org = OrganizationMetrics(
            domain="mixed.com",
            lines_added={"1y": 10000, "90d": 500, "30d": 100},
            lines_removed={"1y": 5000, "90d": 1000, "30d": 50},
            lines_net={"1y": 5000, "90d": -500, "30d": 50},
        )
        assert org.lines_net["1y"] == 5000
        assert org.lines_net["90d"] == -500
        assert org.total_lines_net == 4550

    def test_all_zero_except_contributors(self):
        """Handle org with contributors but no activity."""
        org = OrganizationMetrics(
            domain="inactive.com",
            contributor_count=10,
            commits={"1y": 0},
            lines_added={"1y": 0},
            lines_removed={"1y": 0},
            lines_net={"1y": 0},
        )
        assert org.contributor_count == 10
        assert org.total_commits == 0

    def test_repositories_without_commits(self):
        """Handle case where repos exist but no commits."""
        org = OrganizationMetrics(
            domain="repos.com", repositories_count={"1y": 10}, commits={"1y": 0}
        )
        assert org.repositories_count["1y"] == 10
        assert org.commits["1y"] == 0

    def test_hyphenated_domain(self):
        """Handle hyphenated domain names."""
        org = OrganizationMetrics(domain="my-company-name.com")
        assert org.domain == "my-company-name.com"

    def test_subdomain(self):
        """Handle subdomain organizational identifiers."""
        org = OrganizationMetrics(domain="eng.company.com")
        assert org.domain == "eng.company.com"
