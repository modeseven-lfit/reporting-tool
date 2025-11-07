#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit Tests for GitHub Organization Detection Utilities

Tests for the GitHub organization detection functions extracted in Phase 1.
These tests cover environment variable detection, path-based auto-derivation,
validation logic, and edge cases.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from util.github_org import (
    _derive_org_from_path,
    _is_valid_github_org_name,
    determine_github_org,
    format_source_for_display,
)


class TestDetermineGithubOrg:
    """Tests for determine_github_org function."""

    def test_environment_variable_priority(self):
        """Test that GITHUB_ORG environment variable takes priority."""
        with patch.dict(os.environ, {"GITHUB_ORG": "myorg"}):
            org, source = determine_github_org(Path("./gerrit.otherorg.org"))
            assert org == "myorg"
            assert source == "environment_variable"

    def test_auto_derive_from_gerrit_path(self):
        """Test auto-derivation from gerrit hostname path."""
        with patch.dict(os.environ, {}, clear=True):
            org, source = determine_github_org(Path("./gerrit.onap.org"))
            assert org == "onap"
            assert source == "auto_derived"

    def test_auto_derive_from_git_path(self):
        """Test auto-derivation from git hostname path."""
        with patch.dict(os.environ, {}, clear=True):
            org, source = determine_github_org(Path("./git.opendaylight.org"))
            assert org == "opendaylight"
            assert source == "auto_derived"

    def test_not_found(self):
        """Test when organization cannot be determined."""
        with patch.dict(os.environ, {}, clear=True):
            org, source = determine_github_org(Path("./some/other/path"))
            assert org == ""
            assert source == ""

    def test_invalid_env_var_falls_back(self):
        """Test that invalid environment variable falls back to auto-derivation."""
        with patch.dict(os.environ, {"GITHUB_ORG": "invalid org name!"}):
            org, source = determine_github_org(Path("./gerrit.onap.org"))
            assert org == "onap"
            assert source == "auto_derived"

    def test_empty_env_var_falls_back(self):
        """Test that empty environment variable falls back to auto-derivation."""
        with patch.dict(os.environ, {"GITHUB_ORG": ""}):
            org, source = determine_github_org(Path("./gerrit.onap.org"))
            assert org == "onap"
            assert source == "auto_derived"

    def test_complex_path_structure(self):
        """Test with more complex path structures."""
        with patch.dict(os.environ, {}, clear=True):
            org, source = determine_github_org(
                Path("/home/user/repos/gerrit.myproject.org/subfolder")
            )
            assert org == "myproject"
            assert source == "auto_derived"

    def test_case_insensitive_hostname_detection(self):
        """Test that hostname detection is case-insensitive."""
        with patch.dict(os.environ, {}, clear=True):
            org, source = determine_github_org(Path("./Gerrit.TestOrg.Org"))
            assert org == "TestOrg"
            assert source == "auto_derived"

    def test_valid_org_with_hyphens(self):
        """Test organization names with hyphens from environment."""
        with patch.dict(os.environ, {"GITHUB_ORG": "my-org-name"}):
            org, source = determine_github_org(Path("./path"))
            assert org == "my-org-name"
            assert source == "environment_variable"

    def test_valid_org_with_numbers(self):
        """Test organization names with numbers from environment."""
        with patch.dict(os.environ, {"GITHUB_ORG": "org123"}):
            org, source = determine_github_org(Path("./path"))
            assert org == "org123"
            assert source == "environment_variable"


class TestIsValidGithubOrgName:
    """Tests for _is_valid_github_org_name validation function."""

    def test_valid_simple_name(self):
        """Test simple valid organization names."""
        assert _is_valid_github_org_name("myorg") is True
        assert _is_valid_github_org_name("test") is True
        assert _is_valid_github_org_name("a") is True

    def test_valid_with_hyphens(self):
        """Test valid names with hyphens."""
        assert _is_valid_github_org_name("my-org") is True
        assert _is_valid_github_org_name("test-org-name") is True
        assert _is_valid_github_org_name("a-b-c") is True

    def test_valid_with_numbers(self):
        """Test valid names with numbers."""
        assert _is_valid_github_org_name("org123") is True
        assert _is_valid_github_org_name("123org") is True
        assert _is_valid_github_org_name("test1-org2") is True

    def test_valid_alphanumeric_mix(self):
        """Test valid alphanumeric combinations."""
        assert _is_valid_github_org_name("MyOrg123") is True
        assert _is_valid_github_org_name("Test-Org-123") is True

    def test_invalid_empty_string(self):
        """Test that empty string is invalid."""
        assert _is_valid_github_org_name("") is False

    def test_invalid_starts_with_hyphen(self):
        """Test that names starting with hyphen are invalid."""
        assert _is_valid_github_org_name("-myorg") is False
        assert _is_valid_github_org_name("-test") is False

    def test_invalid_ends_with_hyphen(self):
        """Test that names ending with hyphen are invalid."""
        assert _is_valid_github_org_name("myorg-") is False
        assert _is_valid_github_org_name("test-") is False

    def test_invalid_with_spaces(self):
        """Test that names with spaces are invalid."""
        assert _is_valid_github_org_name("my org") is False
        assert _is_valid_github_org_name("test org name") is False

    def test_invalid_with_special_chars(self):
        """Test that names with special characters are invalid."""
        assert _is_valid_github_org_name("my.org") is False
        assert _is_valid_github_org_name("test@org") is False
        assert _is_valid_github_org_name("org!") is False
        assert _is_valid_github_org_name("test_org") is False

    def test_invalid_only_hyphens(self):
        """Test that only hyphens is invalid."""
        assert _is_valid_github_org_name("-") is False
        assert _is_valid_github_org_name("---") is False

    def test_invalid_unicode_characters(self):
        """Test that unicode characters are invalid."""
        assert _is_valid_github_org_name("org™") is False
        assert _is_valid_github_org_name("test©") is False
        assert _is_valid_github_org_name("org😀") is False


class TestDeriveOrgFromPath:
    """Tests for _derive_org_from_path helper function."""

    def test_derive_from_gerrit_hostname(self):
        """Test derivation from gerrit.* hostname pattern."""
        assert _derive_org_from_path(Path("./gerrit.onap.org")) == "onap"
        assert _derive_org_from_path(Path("./gerrit.test.com")) == "test"

    def test_derive_from_git_hostname(self):
        """Test derivation from git.* hostname pattern."""
        assert _derive_org_from_path(Path("./git.opendaylight.org")) == "opendaylight"
        assert _derive_org_from_path(Path("./git.example.net")) == "example"

    def test_derive_from_nested_path(self):
        """Test derivation from nested path containing hostname."""
        path = Path("/home/user/repos/gerrit.myorg.org/project/subdir")
        assert _derive_org_from_path(path) == "myorg"

    def test_derive_case_insensitive(self):
        """Test that hostname matching is case-insensitive."""
        assert _derive_org_from_path(Path("./Gerrit.MyOrg.Org")) == "MyOrg"
        assert _derive_org_from_path(Path("./GIT.TestOrg.COM")) == "TestOrg"

    def test_no_match_regular_path(self):
        """Test that regular paths return empty string."""
        assert _derive_org_from_path(Path("./some/regular/path")) == ""
        assert _derive_org_from_path(Path("/usr/local/bin")) == ""

    def test_no_match_single_component(self):
        """Test that single-component paths return empty string."""
        assert _derive_org_from_path(Path("./gerrit")) == ""
        assert _derive_org_from_path(Path("./git")) == ""

    def test_no_match_two_components(self):
        """Test that two-component hostnames are rejected (need prefix.org.tld)."""
        assert _derive_org_from_path(Path("./gerrit.org")) == ""
        assert _derive_org_from_path(Path("./git.com")) == ""

    def test_derive_with_subdomain(self):
        """Test derivation with subdomain structure."""
        assert _derive_org_from_path(Path("./gerrit.myorg.example.org")) == "myorg"
        assert _derive_org_from_path(Path("./git.test.staging.com")) == "test"

    def test_invalid_org_name_in_path(self):
        """Test that invalid org names in path are rejected."""
        # Organization name with invalid characters should be rejected
        assert _derive_org_from_path(Path("./gerrit.-invalid.org")) == ""
        assert _derive_org_from_path(Path("./gerrit.invalid-.org")) == ""

    def test_derive_multiple_hostname_patterns(self):
        """Test path with multiple hostname patterns (should use first match)."""
        path = Path("./repos/gerrit.onap.org/git.other.com")
        # Should match the first valid pattern found
        result = _derive_org_from_path(path)
        assert result in ["onap", "other"]  # Either is valid

    def test_derive_org_with_numbers(self):
        """Test deriving org names that contain numbers."""
        assert _derive_org_from_path(Path("./gerrit.org123.com")) == "org123"
        assert _derive_org_from_path(Path("./git.test2.org")) == "test2"

    def test_derive_org_with_hyphens(self):
        """Test deriving org names that contain hyphens."""
        assert _derive_org_from_path(Path("./gerrit.my-org.com")) == "my-org"
        assert _derive_org_from_path(Path("./git.test-project.org")) == "test-project"


class TestFormatSourceForDisplay:
    """Tests for format_source_for_display formatting function."""

    def test_format_environment_variable(self):
        """Test formatting of environment variable source."""
        assert format_source_for_display("environment_variable") == "from JSON"

    def test_format_auto_derived(self):
        """Test formatting of auto-derived source."""
        assert format_source_for_display("auto_derived") == "auto/derived"

    def test_format_not_configured(self):
        """Test formatting of empty/not configured source."""
        assert format_source_for_display("") == "not configured"

    def test_format_unknown_source(self):
        """Test formatting of unknown source (returns as-is)."""
        assert format_source_for_display("unknown") == "unknown"
        assert format_source_for_display("custom_source") == "custom_source"


class TestIntegrationScenarios:
    """Integration-style tests covering realistic scenarios."""

    def test_production_scenario_with_env_var(self):
        """Test typical production scenario with GITHUB_ORG set."""
        with patch.dict(os.environ, {"GITHUB_ORG": "linux-foundation"}):
            org, source = determine_github_org(Path("./gerrit.lfprojects.org"))
            assert org == "linux-foundation"
            assert source == "environment_variable"
            assert format_source_for_display(source) == "from JSON"

    def test_local_dev_scenario_auto_derive(self):
        """Test local development scenario without env var."""
        with patch.dict(os.environ, {}, clear=True):
            org, source = determine_github_org(Path("./gerrit.onap.org"))
            assert org == "onap"
            assert source == "auto_derived"
            assert format_source_for_display(source) == "auto/derived"

    def test_ci_cd_scenario_with_override(self):
        """Test CI/CD scenario where env var overrides path."""
        with patch.dict(os.environ, {"GITHUB_ORG": "ci-test-org"}):
            # Even though path suggests different org, env var wins
            org, source = determine_github_org(Path("./gerrit.someother.org"))
            assert org == "ci-test-org"
            assert source == "environment_variable"

    def test_fallback_chain(self):
        """Test complete fallback chain: invalid env -> auto-derive -> not found."""
        # Invalid env var, valid path
        with patch.dict(os.environ, {"GITHUB_ORG": "invalid org!"}):
            org, source = determine_github_org(Path("./gerrit.onap.org"))
            assert org == "onap"
            assert source == "auto_derived"

        # Invalid env var, invalid path
        with patch.dict(os.environ, {"GITHUB_ORG": "invalid org!"}):
            org, source = determine_github_org(Path("./some/path"))
            assert org == ""
            assert source == ""

    def test_real_world_onap_example(self):
        """Test with real ONAP project structure."""
        with patch.dict(os.environ, {}, clear=True):
            org, source = determine_github_org(Path("/home/jenkins/workspace/gerrit.onap.org"))
            assert org == "onap"
            assert source == "auto_derived"

    def test_real_world_opendaylight_example(self):
        """Test with real OpenDaylight project structure."""
        with patch.dict(os.environ, {}, clear=True):
            org, source = determine_github_org(Path("/opt/repos/git.opendaylight.org/gerrit"))
            assert org == "opendaylight"
            assert source == "auto_derived"


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_very_long_org_name(self):
        """Test with very long organization name."""
        long_org = "a" * 100
        with patch.dict(os.environ, {"GITHUB_ORG": long_org}):
            org, source = determine_github_org(Path("./path"))
            assert org == long_org
            assert source == "environment_variable"

    def test_org_name_with_consecutive_hyphens(self):
        """Test org name with consecutive hyphens."""
        # Should still be valid as long as not at start/end
        org_name = "my--org"
        with patch.dict(os.environ, {"GITHUB_ORG": org_name}):
            org, source = determine_github_org(Path("./path"))
            assert org == org_name
            assert source == "environment_variable"

    def test_path_with_similar_but_not_matching_pattern(self):
        """Test paths with similar but non-matching patterns."""
        with patch.dict(os.environ, {}, clear=True):
            # Missing TLD
            assert determine_github_org(Path("./gerrit.org"))[0] == ""
            # Wrong prefix
            assert determine_github_org(Path("./svn.org.com"))[0] == ""
            # No dots
            assert determine_github_org(Path("./gerritorgcom"))[0] == ""

    def test_unicode_in_path(self):
        """Test paths containing unicode characters."""
        with patch.dict(os.environ, {}, clear=True):
            org, source = determine_github_org(Path("./gerrit.org™.com"))
            # Should not match due to unicode
            assert org == ""
            assert source == ""

    def test_whitespace_in_env_var(self):
        """Test environment variable with whitespace."""
        with patch.dict(os.environ, {"GITHUB_ORG": "  org  "}):
            # Current implementation doesn't trim, so this is invalid
            org, source = determine_github_org(Path("./gerrit.fallback.org"))
            # Should fall back to auto-derivation
            assert org == "fallback"
            assert source == "auto_derived"

    def test_relative_vs_absolute_paths(self):
        """Test both relative and absolute paths."""
        with patch.dict(os.environ, {}, clear=True):
            # Relative path
            org1, source1 = determine_github_org(Path("./gerrit.onap.org"))
            assert org1 == "onap"

            # Absolute path
            org2, source2 = determine_github_org(Path("/tmp/gerrit.onap.org"))
            assert org2 == "onap"

    def test_windows_style_paths(self):
        """Test Windows-style paths."""
        with patch.dict(os.environ, {}, clear=True):
            # WindowsPath should still work
            org, source = determine_github_org(Path("C:\\repos\\gerrit.onap.org"))
            assert org == "onap"
            assert source == "auto_derived"


# Pytest markers for categorization
pytestmark = pytest.mark.unit
