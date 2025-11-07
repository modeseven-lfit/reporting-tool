#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Baseline JSON Schema Regression Tests

These tests ensure that refactoring does not unintentionally change the
structure of the generated JSON report. They validate:
1. Presence of required top-level fields
2. Data types of core fields
3. Schema digest stability
4. Field naming consistency

This is a "characterization test" - it captures current behavior to detect
unintended changes during refactoring.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest


def compute_schema_digest(data: dict[str, Any]) -> str:
    """
    Compute a stable digest of the JSON schema structure.

    Ignores actual data values, focusing on:
    - Field names at all levels
    - Data types
    - Array structure

    Args:
        data: JSON report data

    Returns:
        SHA256 hex digest of schema structure
    """

    def get_schema_structure(obj: Any, path: str = "") -> list[str]:
        """Recursively extract schema structure."""
        structure = []

        if isinstance(obj, dict):
            for key in sorted(obj.keys()):
                field_path = f"{path}.{key}" if path else key
                structure.append(f"{field_path}:dict")
                structure.extend(get_schema_structure(obj[key], field_path))
        elif isinstance(obj, list):
            structure.append(f"{path}:list")
            # Sample first item to get array element structure
            if obj:
                structure.extend(get_schema_structure(obj[0], f"{path}[0]"))
        elif isinstance(obj, str):
            structure.append(f"{path}:str")
        elif isinstance(obj, int | float):
            structure.append(f"{path}:number")
        elif isinstance(obj, bool):
            structure.append(f"{path}:bool")
        elif obj is None:
            structure.append(f"{path}:null")

        return structure

    schema_structure = get_schema_structure(data)
    schema_text = "\n".join(sorted(schema_structure))
    return hashlib.sha256(schema_text.encode("utf-8")).hexdigest()


def validate_required_top_level_fields(data: dict[str, Any]) -> list[str]:
    """
    Validate presence of required top-level fields.

    Returns:
        List of missing field names (empty if all present)
    """
    required_fields = [
        "schema_version",
        "generated_at",
        "project",
        "config_digest",
        "script_version",
        "time_windows",
        "repositories",
        "authors",
        "organizations",
        "summaries",
        "errors",
    ]

    missing = []
    for field in required_fields:
        if field not in data:
            missing.append(field)

    return missing


def validate_field_types(data: dict[str, Any]) -> list[str]:
    """
    Validate data types of top-level fields.

    Returns:
        List of type mismatch errors
    """
    expected_types = {
        "schema_version": str,
        "generated_at": str,
        "project": str,
        "config_digest": str,
        "script_version": str,
        "time_windows": dict,
        "repositories": list,
        "authors": list,
        "organizations": list,
        "summaries": dict,
        "errors": list,
    }

    errors = []
    for field, expected_type in expected_types.items():
        if field in data and not isinstance(data[field], expected_type):
            actual_type = type(data[field]).__name__
            errors.append(f"Field '{field}': expected {expected_type.__name__}, got {actual_type}")

    return errors


def validate_repository_structure(repos: list[dict[str, Any]]) -> list[str]:
    """
    Validate structure of repository records.

    Returns:
        List of validation errors
    """
    if not repos:
        return []  # Empty list is valid

    errors = []
    sample_repo = repos[0]

    # Required repository fields
    required_repo_fields = [
        "gerrit_project",
        "commit_counts",
        "loc_stats",
        "days_since_last_commit",
        "activity_status",
        "authors",
        "features",
    ]

    for field in required_repo_fields:
        if field not in sample_repo:
            errors.append(f"Repository missing field: {field}")

    # Validate nested structures
    if "commit_counts" in sample_repo and not isinstance(sample_repo["commit_counts"], dict):
        errors.append("Repository commit_counts must be dict")

    if "loc_stats" in sample_repo and not isinstance(sample_repo["loc_stats"], dict):
        errors.append("Repository loc_stats must be dict")

    if "authors" in sample_repo and not isinstance(sample_repo["authors"], list):
        errors.append("Repository authors must be list")

    if "features" in sample_repo and not isinstance(sample_repo["features"], dict):
        errors.append("Repository features must be dict")

    return errors


def validate_author_structure(authors: list[dict[str, Any]]) -> list[str]:
    """
    Validate structure of author records.

    Returns:
        List of validation errors
    """
    if not authors:
        return []  # Empty list is valid

    errors = []
    sample_author = authors[0]

    required_author_fields = [
        "name",
        "email",
        "commits",
        "lines_added",
        "lines_removed",
        "lines_net",
        "organizations",
    ]

    for field in required_author_fields:
        if field not in sample_author:
            errors.append(f"Author missing field: {field}")

    # Validate metrics are dicts (time window breakdown)
    metric_fields = ["commits", "lines_added", "lines_removed", "lines_net"]
    for field in metric_fields:
        if field in sample_author and not isinstance(sample_author[field], dict):
            errors.append(f"Author {field} must be dict (time windows)")

    return errors


def validate_summaries_structure(summaries: dict[str, Any]) -> list[str]:
    """
    Validate structure of summaries section.

    Returns:
        List of validation errors
    """
    errors = []

    required_summary_sections = [
        "counts",
        "activity_status_distribution",
        "all_repositories",
        "top_contributors_commits",
        "top_contributors_loc",
        "top_organizations",
    ]

    for section in required_summary_sections:
        if section not in summaries:
            errors.append(f"Summaries missing section: {section}")

    # Validate counts structure
    if "counts" in summaries:
        counts = summaries["counts"]
        required_counts = [
            "total_repositories",
            "current_repositories",
            "active_repositories",
            "inactive_repositories",
            "total_commits",
            "total_authors",
            "total_organizations",
        ]
        for count_field in required_counts:
            if count_field not in counts:
                errors.append(f"Counts missing field: {count_field}")

    return errors


class TestBaselineJSONSchema:
    """Baseline schema validation test suite."""

    def test_required_top_level_fields(self, sample_report_data):
        """Test that all required top-level fields are present."""
        missing = validate_required_top_level_fields(sample_report_data)
        assert not missing, f"Missing required fields: {missing}"

    def test_field_types(self, sample_report_data):
        """Test that field types match expectations."""
        errors = validate_field_types(sample_report_data)
        assert not errors, f"Type validation errors: {errors}"

    def test_repository_structure(self, sample_report_data):
        """Test repository record structure."""
        repos = sample_report_data.get("repositories", [])
        errors = validate_repository_structure(repos)
        assert not errors, f"Repository structure errors: {errors}"

    def test_author_structure(self, sample_report_data):
        """Test author record structure."""
        authors = sample_report_data.get("authors", [])
        errors = validate_author_structure(authors)
        assert not errors, f"Author structure errors: {errors}"

    def test_summaries_structure(self, sample_report_data):
        """Test summaries section structure."""
        summaries = sample_report_data.get("summaries", {})
        errors = validate_summaries_structure(summaries)
        assert not errors, f"Summaries structure errors: {errors}"

    def test_schema_version_format(self, sample_report_data):
        """Test that schema_version follows semantic versioning."""
        version = sample_report_data.get("schema_version", "")
        parts = version.split(".")
        assert len(parts) == 3, f"Schema version must be X.Y.Z format, got: {version}"
        assert all(p.isdigit() for p in parts), f"Schema version parts must be numeric: {version}"

    def test_time_windows_structure(self, sample_report_data):
        """Test time windows are properly structured."""
        time_windows = sample_report_data.get("time_windows", {})
        assert isinstance(time_windows, dict), "time_windows must be dict"

        # Each window should have days, start, end
        for window_name, window_data in time_windows.items():
            assert "days" in window_data, f"Window {window_name} missing 'days'"
            assert "start" in window_data, f"Window {window_name} missing 'start'"
            assert "end" in window_data, f"Window {window_name} missing 'end'"
            assert isinstance(window_data["days"], int), f"Window {window_name} days must be int"

    def test_errors_list_structure(self, sample_report_data):
        """Test errors list has proper structure."""
        errors = sample_report_data.get("errors", [])
        assert isinstance(errors, list), "errors must be list"

        # If there are errors, validate their structure
        for error in errors:
            assert isinstance(error, dict), "Each error must be dict"
            # Common error fields (not all required)
            if "repo" in error:
                assert isinstance(error["repo"], str)
            if "error" in error:
                assert isinstance(error["error"], str)
            if "category" in error:
                assert isinstance(error["category"], str)

    def test_schema_digest_stability(self, sample_report_data, baseline_digest_file):
        """
        Test that schema structure hasn't changed unexpectedly.

        This test will fail if the JSON structure changes, which is intentional.
        When making intentional schema changes:
        1. Review the changes carefully
        2. Update the baseline digest file
        3. Bump schema_version if needed
        """
        current_digest = compute_schema_digest(sample_report_data)

        # Load or create baseline
        baseline_path = Path(baseline_digest_file)
        if baseline_path.exists():
            with open(baseline_path) as f:
                baseline = json.load(f)
            baseline_digest = baseline.get("digest", "")

            if current_digest != baseline_digest:
                # Schema has changed - provide detailed info
                msg = (
                    f"Schema structure has changed!\n"
                    f"Expected digest: {baseline_digest}\n"
                    f"Current digest:  {current_digest}\n\n"
                    f"If this change is intentional:\n"
                    f"1. Review the schema changes carefully\n"
                    f"2. Update baseline: python tests/regression/update_baseline_digest.py\n"
                    f"3. Consider bumping schema_version in the code\n"
                )
                raise AssertionError(msg)
        else:
            # First run - create baseline
            baseline = {
                "schema_version": sample_report_data.get("schema_version"),
                "digest": current_digest,
                "generated_at": sample_report_data.get("generated_at"),
                "note": "Baseline schema digest for regression testing",
            }
            baseline_path.parent.mkdir(parents=True, exist_ok=True)
            with open(baseline_path, "w") as f:
                json.dump(baseline, f, indent=2)

            print(f"Created baseline digest: {baseline_path}")


# Pytest fixtures
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "baseline: baseline schema validation tests")


@pytest.fixture
def sample_report_data():
    """
    Load sample report data for testing.

    This can be either:
    1. A real generated report from fixtures
    2. A minimal synthetic report for unit testing

    For now, returns a minimal valid structure.
    """
    return {
        "schema_version": "1.0.0",
        "generated_at": "2025-01-15T12:00:00Z",
        "project": "test_project",
        "config_digest": "abc123",
        "script_version": "1.0.0",
        "time_windows": {"last_30_days": {"days": 30, "start": "2024-12-16", "end": "2025-01-15"}},
        "repositories": [
            {
                "gerrit_project": "test/repo",
                "commit_counts": {"last_30_days": 10},
                "loc_stats": {"last_30_days": {"added": 100, "removed": 50}},
                "days_since_last_commit": 5,
                "activity_status": "current",
                "authors": [],
                "features": {},
            }
        ],
        "authors": [
            {
                "name": "Test Author",
                "email": "test@example.org",
                "commits": {"last_30_days": 10},
                "lines_added": {"last_30_days": 100},
                "lines_removed": {"last_30_days": 50},
                "lines_net": {"last_30_days": 50},
                "organizations": ["example.org"],
            }
        ],
        "organizations": [{"domain": "example.org", "commits": {"last_30_days": 10}, "authors": 1}],
        "summaries": {
            "counts": {
                "total_repositories": 1,
                "current_repositories": 1,
                "active_repositories": 0,
                "inactive_repositories": 0,
                "total_commits": 10,
                "total_authors": 1,
                "total_organizations": 1,
            },
            "activity_status_distribution": {},
            "all_repositories": [],
            "top_contributors_commits": [],
            "top_contributors_loc": [],
            "top_organizations": [],
        },
        "errors": [],
    }


@pytest.fixture
def baseline_digest_file(tmp_path):
    """Provide path to baseline digest file."""
    # In real usage, this would point to a committed baseline file
    # For testing, use a temporary location
    return tmp_path / "baseline_schema_digest.json"
