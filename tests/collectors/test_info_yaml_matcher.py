# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for INFO.yaml committer matcher.

Tests the matching logic for matching INFO.yaml committers to Git authors
based on email addresses and names.
"""

from typing import Any

import pytest

from reporting_tool.collectors.info_yaml.matcher import (
    CommitterMatcher,
    match_committer_to_authors,
)


@pytest.fixture
def sample_authors() -> list[dict[str, Any]]:
    """Sample Git authors for testing."""
    return [
        {"name": "John Doe", "email": "john.doe@example.com"},
        {"name": "Jane Smith", "email": "jane.smith@example.com"},
        {"name": "Bob Wilson", "email": "bob.wilson@company.org"},
        {"name": "Alice Johnson", "email": "alice.j@techcorp.com"},
        {"name": "Charlie Brown", "email": "cbrown@mail.com"},
    ]


class TestCommitterMatcher:
    """Tests for CommitterMatcher class."""

    def test_create_matcher(self):
        """Test creating a matcher instance."""
        matcher = CommitterMatcher()

        assert matcher is not None
        assert matcher.email_match_enabled is True
        assert matcher.name_match_enabled is True
        assert matcher.case_sensitive is False

    def test_create_matcher_with_config(self):
        """Test creating matcher with custom configuration."""
        config = {
            "email_match_enabled": False,
            "name_match_enabled": True,
            "case_sensitive": True,
        }
        matcher = CommitterMatcher(config)

        assert matcher.email_match_enabled is False
        assert matcher.name_match_enabled is True
        assert matcher.case_sensitive is True

    def test_match_by_email_exact(self, sample_authors: list[dict[str, Any]]):
        """Test exact email matching."""
        matcher = CommitterMatcher()

        result = matcher.match_committer_to_authors(
            "john.doe@example.com", "John Doe", sample_authors
        )

        assert result is not None
        assert result["email"] == "john.doe@example.com"
        assert result["name"] == "John Doe"

    def test_match_by_email_case_insensitive(self, sample_authors: list[dict[str, Any]]):
        """Test case-insensitive email matching."""
        matcher = CommitterMatcher()

        result = matcher.match_committer_to_authors(
            "JOHN.DOE@EXAMPLE.COM", "John Doe", sample_authors
        )

        assert result is not None
        assert result["email"] == "john.doe@example.com"

    def test_match_by_email_with_whitespace(self, sample_authors: list[dict[str, Any]]):
        """Test email matching with whitespace."""
        matcher = CommitterMatcher()

        result = matcher.match_committer_to_authors(
            "  john.doe@example.com  ", "John Doe", sample_authors
        )

        assert result is not None
        assert result["email"] == "john.doe@example.com"

    def test_match_by_name_exact(self, sample_authors: list[dict[str, Any]]):
        """Test exact name matching."""
        matcher = CommitterMatcher()

        # No email, only name
        result = matcher.match_committer_to_authors("", "Jane Smith", sample_authors)

        assert result is not None
        assert result["name"] == "Jane Smith"
        assert result["email"] == "jane.smith@example.com"

    def test_match_by_name_case_insensitive(self, sample_authors: list[dict[str, Any]]):
        """Test case-insensitive name matching."""
        matcher = CommitterMatcher()

        result = matcher.match_committer_to_authors("", "jane smith", sample_authors)

        assert result is not None
        assert result["name"] == "Jane Smith"

    def test_match_by_last_name(self, sample_authors: list[dict[str, Any]]):
        """Test fuzzy matching by last name."""
        matcher = CommitterMatcher()

        result = matcher.match_committer_to_authors(
            "",
            "Robert Wilson",  # Different first name, same last name
            sample_authors,
        )

        assert result is not None
        assert result["name"] == "Bob Wilson"

    def test_no_match_found(self, sample_authors: list[dict[str, Any]]):
        """Test when no match is found."""
        matcher = CommitterMatcher()

        result = matcher.match_committer_to_authors(
            "unknown@example.com", "Unknown Person", sample_authors
        )

        assert result is None

    def test_email_match_preferred_over_name(self, sample_authors: list[dict[str, Any]]):
        """Test that email matching is preferred over name matching."""
        matcher = CommitterMatcher()

        # Provide email that matches one author and name that matches another
        result = matcher.match_committer_to_authors(
            "john.doe@example.com", "Jane Smith", sample_authors
        )

        # Should match by email (John Doe), not by name (Jane Smith)
        assert result is not None
        assert result["email"] == "john.doe@example.com"
        assert result["name"] == "John Doe"

    def test_match_with_empty_authors(self):
        """Test matching with empty authors list."""
        matcher = CommitterMatcher()

        result = matcher.match_committer_to_authors("test@example.com", "Test User", [])

        assert result is None

    def test_match_with_no_email_or_name(self, sample_authors: list[dict[str, Any]]):
        """Test matching with no email or name provided."""
        matcher = CommitterMatcher()

        result = matcher.match_committer_to_authors("", "", sample_authors)

        assert result is None

    def test_email_match_disabled(self, sample_authors: list[dict[str, Any]]):
        """Test with email matching disabled."""
        config = {"email_match_enabled": False}
        matcher = CommitterMatcher(config)

        # Provide both email and name
        result = matcher.match_committer_to_authors(
            "john.doe@example.com", "John Doe", sample_authors
        )

        # Should match by name since email matching is disabled
        assert result is not None
        assert result["name"] == "John Doe"

    def test_name_match_disabled(self, sample_authors: list[dict[str, Any]]):
        """Test with name matching disabled."""
        config = {"name_match_enabled": False}
        matcher = CommitterMatcher(config)

        # Provide only name (no email)
        result = matcher.match_committer_to_authors("", "Jane Smith", sample_authors)

        # Should not match since name matching is disabled
        assert result is None

    def test_normalize_email(self):
        """Test email normalization."""
        matcher = CommitterMatcher()

        # Test various normalizations
        # Note: dots are removed by normalization patterns
        assert matcher._normalize_email("Test@Example.COM") == "test@examplecom"
        assert matcher._normalize_email("  test@example.com  ") == "test@examplecom"
        assert matcher._normalize_email("john.doe@example.com") == "johndoe@examplecom"
        assert matcher._normalize_email("") == ""

    def test_normalize_name(self):
        """Test name normalization."""
        matcher = CommitterMatcher()

        # Test various normalizations
        assert matcher._normalize_name("John Doe") == "john doe"
        assert matcher._normalize_name("  John   Doe  ") == "john doe"
        assert matcher._normalize_name("John-Doe") == "johndoe"
        assert matcher._normalize_name("") == ""

    def test_match_committers_bulk(self, sample_authors: list[dict[str, Any]]):
        """Test bulk matching of multiple committers."""
        matcher = CommitterMatcher()

        committers = [
            {"name": "John Doe", "email": "john.doe@example.com"},
            {"name": "Jane Smith", "email": "jane.smith@example.com"},
            {"name": "Unknown Person", "email": "unknown@example.com"},
        ]

        results = matcher.match_committers_bulk(committers, sample_authors)

        assert len(results) == 3
        assert results["john.doe@example.com"] is not None
        assert results["jane.smith@example.com"] is not None
        assert results["unknown@example.com"] is None

    def test_get_match_statistics(self, sample_authors: list[dict[str, Any]]):
        """Test getting match statistics."""
        matcher = CommitterMatcher()

        committers = [
            {"name": "John Doe", "email": "john.doe@example.com"},
            {"name": "Jane Smith", "email": "jane.smith@example.com"},
            {"name": "Unknown Person", "email": "unknown@example.com"},
            {"name": "Bob Wilson", "email": ""},  # Name match only
        ]

        stats = matcher.get_match_statistics(committers, sample_authors)

        assert stats["total_committers"] == 4
        assert stats["matched"] == 3  # 2 email matches + 1 name match
        assert stats["unmatched"] == 1
        assert stats["email_matches"] == 2
        assert stats["name_matches"] == 1


class TestConvenienceFunction:
    """Tests for convenience function."""

    def test_match_committer_to_authors_function(self, sample_authors: list[dict[str, Any]]):
        """Test the convenience function."""
        result = match_committer_to_authors("john.doe@example.com", "John Doe", sample_authors)

        assert result is not None
        assert result["email"] == "john.doe@example.com"
        assert result["name"] == "John Doe"
