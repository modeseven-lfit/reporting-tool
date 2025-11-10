# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for Enhanced Feature Discovery Module

Tests all new functionality added in Phase 13:
- Feature info retrieval
- Detailed feature display
- Enhanced list formatting
- Search functionality
- Configuration examples

Phase 13: CLI & User Experience Improvements
"""

import pytest

from cli.features import (
    AVAILABLE_FEATURES,
    FeatureInfo,
    format_feature_list_compact,
    format_search_results,
    get_all_categories,
    get_category_count,
    get_feature_category,
    get_feature_count,
    get_feature_description,
    get_feature_info,
    get_features_by_category,
    get_features_in_category,
    list_all_features,
    search_features,
    show_feature_details,
)


class TestFeatureInfo:
    """Test FeatureInfo named tuple and get_feature_info function."""

    def test_get_feature_info_valid(self):
        """Test retrieving info for a valid feature."""
        info = get_feature_info("dependabot")

        assert info is not None
        assert isinstance(info, FeatureInfo)
        assert info.name == "dependabot"
        assert info.description == "Dependabot configuration detection"
        assert info.category == "CI/CD"
        assert info.config_file is not None
        assert ".github/dependabot.yml" in info.config_file
        assert info.config_example is not None
        assert "version: 2" in info.config_example
        assert info.detection_method is not None

    def test_get_feature_info_invalid(self):
        """Test retrieving info for invalid feature."""
        info = get_feature_info("nonexistent-feature")
        assert info is None

    def test_get_feature_info_all_features(self):
        """Test that all features return valid info."""
        for feature_name in AVAILABLE_FEATURES:
            info = get_feature_info(feature_name)
            assert info is not None
            assert info.name == feature_name
            assert info.description
            assert info.category

    def test_feature_info_fields(self):
        """Test FeatureInfo has all expected fields."""
        info = get_feature_info("github-actions")

        assert hasattr(info, "name")
        assert hasattr(info, "description")
        assert hasattr(info, "category")
        assert hasattr(info, "config_file")
        assert hasattr(info, "config_example")
        assert hasattr(info, "detection_method")


class TestFeaturesByCategory:
    """Test category-based feature organization."""

    def test_get_features_by_category_structure(self):
        """Test the structure of features by category."""
        features = get_features_by_category()

        assert isinstance(features, dict)
        assert len(features) > 0

        # Check each category has a list of tuples
        for category, feature_list in features.items():
            assert isinstance(category, str)
            assert isinstance(feature_list, list)
            assert len(feature_list) > 0

            for item in feature_list:
                assert isinstance(item, tuple)
                assert len(item) == 2
                name, desc = item
                assert isinstance(name, str)
                assert isinstance(desc, str)

    def test_get_features_by_category_sorted(self):
        """Test features within each category are sorted."""
        features = get_features_by_category()

        for category, feature_list in features.items():
            names = [name for name, _ in feature_list]
            assert names == sorted(names), f"Features in {category} not sorted"

    def test_get_features_by_category_known_categories(self):
        """Test that known categories exist."""
        features = get_features_by_category()

        expected_categories = [
            "CI/CD",
            "Code Quality",
            "Documentation",
            "Build & Package",
            "Repository",
            "Testing",
            "Security",
        ]

        for expected in expected_categories:
            assert expected in features, f"Missing category: {expected}"


class TestListAllFeatures:
    """Test the list_all_features function."""

    def test_list_all_features_basic(self):
        """Test basic feature listing."""
        output = list_all_features()

        assert isinstance(output, str)
        assert "Available Feature Checks:" in output
        assert "CI/CD" in output
        assert "dependabot" in output
        assert "Total:" in output
        assert "features" in output.lower()

    def test_list_all_features_verbose(self):
        """Test verbose feature listing includes config files."""
        output = list_all_features(verbose=True)

        assert isinstance(output, str)
        assert "Config:" in output
        assert ".github" in output or "yml" in output or "xml" in output

    def test_list_all_features_non_verbose(self):
        """Test non-verbose listing doesn't include config files."""
        output = list_all_features(verbose=False)

        # Non-verbose should not have "Config:" lines
        assert "Config:" not in output

    def test_list_all_features_has_help_text(self):
        """Test output includes helpful tips."""
        output = list_all_features()

        assert "--show-feature" in output or "show-feature" in output

    def test_list_all_features_formatting(self):
        """Test consistent formatting."""
        output = list_all_features()

        # Should have emoji/symbols for categories
        assert "📁" in output
        # Should have bullets for features
        assert "•" in output
        # Should have tips
        assert "💡" in output

    def test_list_all_features_includes_all(self):
        """Test all features are included in output."""
        output = list_all_features()

        for feature_name in AVAILABLE_FEATURES:
            assert feature_name in output, f"Feature {feature_name} not in output"


class TestShowFeatureDetails:
    """Test detailed feature display."""

    def test_show_feature_details_valid(self):
        """Test showing details for a valid feature."""
        output = show_feature_details("dependabot")

        assert isinstance(output, str)
        assert "Feature: dependabot" in output
        assert "Category: CI/CD" in output
        assert "Description:" in output
        assert "Dependabot configuration detection" in output

    def test_show_feature_details_invalid(self):
        """Test showing details for invalid feature."""
        output = show_feature_details("nonexistent-feature")

        assert isinstance(output, str)
        assert "Unknown feature" in output or "❌" in output
        assert "nonexistent-feature" in output

    def test_show_feature_details_detection_method(self):
        """Test detection method is shown when available."""
        output = show_feature_details("dependabot")

        assert "Detection Method:" in output or "🔍" in output
        assert ".github/dependabot.y" in output

    def test_show_feature_details_config_file(self):
        """Test config file is shown when available."""
        output = show_feature_details("pytest")

        assert "Configuration File" in output or "📄" in output
        assert "pytest.ini" in output or "pyproject.toml" in output

    def test_show_feature_details_config_example(self):
        """Test config example is shown when available."""
        output = show_feature_details("maven")

        assert "Configuration Example" in output or "📋" in output
        assert "pom.xml" in output or "<project>" in output

    def test_show_feature_details_related_features(self):
        """Test related features are shown."""
        output = show_feature_details("dependabot")

        # Should show other CI/CD features
        assert "Related Features" in output or "🔗" in output
        # At least one other CI/CD feature should be mentioned
        assert "github-actions" in output or "jenkins" in output

    def test_show_feature_details_formatting(self):
        """Test consistent formatting with headers."""
        output = show_feature_details("docker")

        assert "=" in output  # Header separator
        assert "Feature:" in output
        assert output.count("=") >= 2  # Top and bottom separators

    def test_show_feature_details_all_features(self):
        """Test details can be shown for all features."""
        for feature_name in AVAILABLE_FEATURES:
            output = show_feature_details(feature_name)
            assert feature_name in output
            assert "Category:" in output
            assert "Description:" in output


class TestFeatureDescription:
    """Test get_feature_description function."""

    def test_get_feature_description_valid(self):
        """Test getting description for valid feature."""
        desc = get_feature_description("dependabot")
        assert desc == "Dependabot configuration detection"

    def test_get_feature_description_invalid(self):
        """Test getting description for invalid feature."""
        desc = get_feature_description("nonexistent")
        assert "Unknown feature" in desc

    def test_get_feature_description_all(self):
        """Test descriptions for all features."""
        for feature_name in AVAILABLE_FEATURES:
            desc = get_feature_description(feature_name)
            assert isinstance(desc, str)
            assert len(desc) > 0
            assert "Unknown" not in desc


class TestFeatureCategory:
    """Test get_feature_category function."""

    def test_get_feature_category_valid(self):
        """Test getting category for valid feature."""
        category = get_feature_category("dependabot")
        assert category == "CI/CD"

    def test_get_feature_category_invalid(self):
        """Test getting category for invalid feature."""
        category = get_feature_category("nonexistent")
        assert category == "Unknown"

    def test_get_feature_category_all(self):
        """Test categories for all features."""
        for feature_name in AVAILABLE_FEATURES:
            category = get_feature_category(feature_name)
            assert isinstance(category, str)
            assert len(category) > 0
            assert category != "Unknown"


class TestFeaturesInCategory:
    """Test get_features_in_category function."""

    def test_get_features_in_category_cicd(self):
        """Test getting CI/CD features."""
        features = get_features_in_category("CI/CD")

        assert isinstance(features, list)
        assert len(features) > 0
        assert "dependabot" in features
        assert "github-actions" in features

    def test_get_features_in_category_sorted(self):
        """Test features in category are sorted."""
        features = get_features_in_category("Testing")
        assert features == sorted(features)

    def test_get_features_in_category_empty(self):
        """Test getting features for non-existent category."""
        features = get_features_in_category("NonExistent")
        assert isinstance(features, list)
        assert len(features) == 0

    def test_get_features_in_category_all_categories(self):
        """Test getting features for all categories."""
        categories = get_all_categories()

        for category in categories:
            features = get_features_in_category(category)
            assert isinstance(features, list)
            assert len(features) > 0


class TestAllCategories:
    """Test get_all_categories function."""

    def test_get_all_categories_returns_list(self):
        """Test returns list of categories."""
        categories = get_all_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0

    def test_get_all_categories_sorted(self):
        """Test categories are sorted."""
        categories = get_all_categories()
        assert categories == sorted(categories)

    def test_get_all_categories_unique(self):
        """Test categories are unique."""
        categories = get_all_categories()
        assert len(categories) == len(set(categories))

    def test_get_all_categories_known(self):
        """Test known categories are present."""
        categories = get_all_categories()

        expected = ["CI/CD", "Testing", "Documentation"]
        for expected_cat in expected:
            assert expected_cat in categories


class TestSearchFeatures:
    """Test search_features function."""

    def test_search_features_by_name(self):
        """Test searching by feature name."""
        results = search_features("github")

        assert isinstance(results, list)
        assert len(results) > 0

        # Should find github-actions, github-mirror, github2gerrit
        feature_names = [name for name, _, _ in results]
        assert any("github" in name for name in feature_names)

    def test_search_features_by_description(self):
        """Test searching by description."""
        results = search_features("docker")

        assert isinstance(results, list)
        assert len(results) > 0

        # Should find docker feature
        feature_names = [name for name, _, _ in results]
        assert "docker" in feature_names

    def test_search_features_case_insensitive(self):
        """Test search is case-insensitive."""
        results_lower = search_features("docker")
        results_upper = search_features("DOCKER")
        results_mixed = search_features("Docker")

        assert len(results_lower) == len(results_upper)
        assert len(results_lower) == len(results_mixed)

    def test_search_features_no_results(self):
        """Test search with no matches."""
        results = search_features("xyzabc123")

        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_features_prefix_priority(self):
        """Test prefix matches come first."""
        results = search_features("git")

        # Features starting with 'git' should come before those just containing 'git'
        feature_names = [name for name, _, _ in results]

        if len(feature_names) >= 2:
            # First result should be a prefix match
            assert feature_names[0].startswith("git")

    def test_search_features_with_category_filter(self):
        """Test searching within a specific category."""
        results = search_features("test", category="Testing")

        # All results should be in Testing category
        for _, _, category in results:
            assert category == "Testing"

    def test_search_features_category_filter_no_results(self):
        """Test category filter excludes non-matching results."""
        # Search for 'docker' in Testing category (should find nothing)
        results = search_features("docker", category="Testing")

        assert len(results) == 0

    def test_search_features_returns_tuples(self):
        """Test search returns proper tuple format."""
        results = search_features("maven")

        assert len(results) > 0

        for result in results:
            assert isinstance(result, tuple)
            assert len(result) == 3
            name, desc, category = result
            assert isinstance(name, str)
            assert isinstance(desc, str)
            assert isinstance(category, str)


class TestFormatSearchResults:
    """Test format_search_results function."""

    def test_format_search_results_with_results(self):
        """Test formatting results with matches."""
        results = [
            ("dependabot", "Dependabot configuration detection", "CI/CD"),
            ("github-actions", "GitHub Actions workflows", "CI/CD"),
        ]

        output = format_search_results("github", results)

        assert isinstance(output, str)
        assert "Found 2 feature" in output
        assert "dependabot" in output
        assert "github-actions" in output

    def test_format_search_results_no_results(self):
        """Test formatting with no matches."""
        output = format_search_results("xyzabc", [])

        assert isinstance(output, str)
        assert "No features found" in output or "found matching" in output
        assert "xyzabc" in output

    def test_format_search_results_grouped_by_category(self):
        """Test results are grouped by category."""
        results = [
            ("dependabot", "Dependabot configuration", "CI/CD"),
            ("pytest", "PyTest testing", "Testing"),
            ("github-actions", "GitHub Actions", "CI/CD"),
        ]

        output = format_search_results("test", results)

        # Should have category headers
        assert "CI/CD" in output
        assert "Testing" in output

    def test_format_search_results_has_tips(self):
        """Test output includes helpful tips."""
        results = [("pytest", "PyTest", "Testing")]
        output = format_search_results("test", results)

        assert "--show-feature" in output or "show-feature" in output


class TestCompactList:
    """Test format_feature_list_compact function."""

    def test_format_feature_list_compact(self):
        """Test compact list formatting."""
        compact = format_feature_list_compact()

        assert isinstance(compact, str)
        assert "," in compact
        assert "dependabot" in compact

    def test_format_feature_list_compact_all_features(self):
        """Test all features are in compact list."""
        compact = format_feature_list_compact()

        for feature_name in AVAILABLE_FEATURES:
            assert feature_name in compact

    def test_format_feature_list_compact_sorted(self):
        """Test compact list is sorted."""
        compact = format_feature_list_compact()
        features = [f.strip() for f in compact.split(",")]

        assert features == sorted(features)


class TestFeatureCounts:
    """Test count functions."""

    def test_get_feature_count(self):
        """Test feature count matches registry."""
        count = get_feature_count()

        assert isinstance(count, int)
        assert count == len(AVAILABLE_FEATURES)
        assert count > 0

    def test_get_category_count(self):
        """Test category count."""
        count = get_category_count()

        assert isinstance(count, int)
        assert count > 0
        assert count == len(get_all_categories())

    def test_get_category_count_less_than_features(self):
        """Test there are fewer categories than features."""
        feature_count = get_feature_count()
        category_count = get_category_count()

        assert category_count < feature_count


class TestFeatureRegistry:
    """Test the AVAILABLE_FEATURES registry."""

    def test_registry_not_empty(self):
        """Test registry has features."""
        assert len(AVAILABLE_FEATURES) > 0

    def test_registry_structure(self):
        """Test each feature has proper structure."""
        for name, data in AVAILABLE_FEATURES.items():
            assert isinstance(name, str)
            assert isinstance(data, tuple)
            assert len(data) >= 2  # At least description and category

            description = data[0]
            category = data[1]

            assert isinstance(description, str)
            assert isinstance(category, str)
            assert len(description) > 0
            assert len(category) > 0

    def test_registry_has_config_examples(self):
        """Test features have config examples where appropriate."""
        features_with_examples = [
            name
            for name, data in AVAILABLE_FEATURES.items()
            if len(data) > 3 and data[3] is not None
        ]

        # Most features should have examples
        assert len(features_with_examples) > len(AVAILABLE_FEATURES) * 0.7

    def test_registry_has_detection_methods(self):
        """Test features have detection methods."""
        features_with_detection = [
            name
            for name, data in AVAILABLE_FEATURES.items()
            if len(data) > 4 and data[4] is not None
        ]

        # Most features should have detection methods
        assert len(features_with_detection) > len(AVAILABLE_FEATURES) * 0.7

    def test_registry_known_features_exist(self):
        """Test known important features exist."""
        expected_features = [
            "dependabot",
            "github-actions",
            "docker",
            "pytest",
            "maven",
            "pre-commit",
        ]

        for expected in expected_features:
            assert expected in AVAILABLE_FEATURES


class TestIntegration:
    """Integration tests for feature discovery."""

    def test_feature_workflow(self):
        """Test typical feature discovery workflow."""
        # 1. List all features
        all_features = list_all_features()
        assert len(all_features) > 0

        # 2. Search for specific features
        results = search_features("github")
        assert len(results) > 0

        # 3. Get details for a feature
        feature_name = results[0][0]
        details = show_feature_details(feature_name)
        assert feature_name in details

        # 4. Get category
        category = get_feature_category(feature_name)
        assert category in get_all_categories()

        # 5. Get other features in same category
        related = get_features_in_category(category)
        assert feature_name in related

    def test_all_features_have_complete_info(self):
        """Test all features can be displayed completely."""
        for feature_name in AVAILABLE_FEATURES:
            # Get info
            info = get_feature_info(feature_name)
            assert info is not None

            # Get description
            desc = get_feature_description(feature_name)
            assert len(desc) > 0

            # Get category
            cat = get_feature_category(feature_name)
            assert len(cat) > 0

            # Show details
            details = show_feature_details(feature_name)
            assert feature_name in details

    def test_categories_have_features(self):
        """Test every category has at least one feature."""
        categories = get_all_categories()

        for category in categories:
            features = get_features_in_category(category)
            assert len(features) > 0, f"Category {category} has no features"

    def test_search_finds_all_features(self):
        """Test all features can be found via search."""
        for feature_name in AVAILABLE_FEATURES:
            # Search by exact name should find it
            results = search_features(feature_name)
            feature_names = [name for name, _, _ in results]
            assert feature_name in feature_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
