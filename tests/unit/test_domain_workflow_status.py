# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for WorkflowStatus domain model.

Tests cover:
- Validation (valid CI systems, primary CI detection)
- Edge cases (no CI, multiple CI systems, auto-detection)
- Dictionary conversion (to_dict, from_dict)
- Property methods (has_any_ci, ci_system_count, get_detected_systems)
"""

import pytest

from domain.workflow_status import WorkflowStatus


class TestWorkflowStatusValidation:
    """Test WorkflowStatus validation rules."""

    def test_invalid_primary_ci_system_raises_error(self):
        """Invalid primary_ci_system should raise ValueError."""
        with pytest.raises(ValueError, match="primary_ci_system must be one of"):
            WorkflowStatus(primary_ci_system="invalid_system")

    def test_valid_primary_ci_systems(self):
        """Valid CI systems should be accepted."""
        valid_systems = [
            "github_actions",
            "jenkins",
            "circleci",
            "travis",
            "gitlab_ci",
        ]
        for system in valid_systems:
            status = WorkflowStatus(primary_ci_system=system)
            assert status.primary_ci_system == system

    def test_none_primary_ci_system_valid(self):
        """None should be a valid primary_ci_system."""
        status = WorkflowStatus(primary_ci_system=None)
        assert status.primary_ci_system is None

    def test_auto_detect_github_actions(self):
        """Auto-detect GitHub Actions as primary when not explicitly set."""
        status = WorkflowStatus(has_github_actions=True)
        assert status.primary_ci_system == "github_actions"

    def test_auto_detect_jenkins(self):
        """Auto-detect Jenkins as primary when GitHub Actions not present."""
        status = WorkflowStatus(has_jenkins=True)
        assert status.primary_ci_system == "jenkins"

    def test_auto_detect_circleci(self):
        """Auto-detect CircleCI as primary when higher priority systems absent."""
        status = WorkflowStatus(has_circleci=True)
        assert status.primary_ci_system == "circleci"

    def test_auto_detect_travis(self):
        """Auto-detect Travis as primary when higher priority systems absent."""
        status = WorkflowStatus(has_travis=True)
        assert status.primary_ci_system == "travis"

    def test_auto_detect_gitlab_ci(self):
        """Auto-detect GitLab CI as primary when all others absent."""
        status = WorkflowStatus(has_gitlab_ci=True)
        assert status.primary_ci_system == "gitlab_ci"

    def test_auto_detect_priority_order(self):
        """GitHub Actions takes precedence over other systems."""
        status = WorkflowStatus(has_github_actions=True, has_jenkins=True, has_circleci=True)
        assert status.primary_ci_system == "github_actions"

    def test_explicit_primary_overrides_auto_detect(self):
        """Explicitly set primary_ci_system should not be overridden."""
        status = WorkflowStatus(
            has_github_actions=True, has_jenkins=True, primary_ci_system="jenkins"
        )
        assert status.primary_ci_system == "jenkins"


class TestWorkflowStatusCreation:
    """Test WorkflowStatus instance creation."""

    def test_default_no_ci(self):
        """Default status should have no CI systems."""
        status = WorkflowStatus()
        assert status.has_github_actions is False
        assert status.has_jenkins is False
        assert status.has_circleci is False
        assert status.has_travis is False
        assert status.has_gitlab_ci is False
        assert status.workflow_files == []
        assert status.primary_ci_system is None
        assert status.additional_metadata == {}

    def test_github_actions_only(self):
        """Create status with only GitHub Actions."""
        status = WorkflowStatus(
            has_github_actions=True, workflow_files=[".github/workflows/ci.yml"]
        )
        assert status.has_github_actions is True
        assert status.has_jenkins is False
        assert status.primary_ci_system == "github_actions"
        assert len(status.workflow_files) == 1

    def test_jenkins_only(self):
        """Create status with only Jenkins."""
        status = WorkflowStatus(has_jenkins=True, workflow_files=["Jenkinsfile"])
        assert status.has_jenkins is True
        assert status.primary_ci_system == "jenkins"

    def test_multiple_ci_systems(self):
        """Create status with multiple CI systems."""
        status = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=True,
            has_circleci=True,
            workflow_files=[".github/workflows/test.yml", "Jenkinsfile", ".circleci/config.yml"],
        )
        assert status.has_github_actions is True
        assert status.has_jenkins is True
        assert status.has_circleci is True
        assert len(status.workflow_files) == 3

    def test_with_additional_metadata(self):
        """Create status with additional metadata."""
        status = WorkflowStatus(
            has_github_actions=True,
            additional_metadata={"workflow_count": 5, "badges": ["build", "coverage"]},
        )
        assert status.additional_metadata["workflow_count"] == 5
        assert "build" in status.additional_metadata["badges"]


class TestWorkflowStatusDictConversion:
    """Test dictionary serialization and deserialization."""

    def test_to_dict_no_ci(self):
        """Convert status with no CI to dictionary."""
        status = WorkflowStatus()
        data = status.to_dict()

        assert data["has_github_actions"] is False
        assert data["has_jenkins"] is False
        assert data["has_circleci"] is False
        assert data["has_travis"] is False
        assert data["has_gitlab_ci"] is False
        assert "workflow_files" not in data  # Omitted when empty
        assert "primary_ci_system" not in data  # Omitted when None

    def test_to_dict_single_ci(self):
        """Convert status with single CI system to dictionary."""
        status = WorkflowStatus(
            has_github_actions=True, workflow_files=[".github/workflows/ci.yml"]
        )
        data = status.to_dict()

        assert data["has_github_actions"] is True
        assert data["has_jenkins"] is False
        assert data["workflow_files"] == [".github/workflows/ci.yml"]
        assert data["primary_ci_system"] == "github_actions"

    def test_to_dict_multiple_ci(self):
        """Convert status with multiple CI systems to dictionary."""
        status = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=True,
            workflow_files=["ci.yml", "Jenkinsfile"],
            additional_metadata={"key": "value"},
        )
        data = status.to_dict()

        assert data["has_github_actions"] is True
        assert data["has_jenkins"] is True
        assert data["workflow_files"] == ["ci.yml", "Jenkinsfile"]
        assert data["primary_ci_system"] == "github_actions"
        assert data["additional_metadata"] == {"key": "value"}

    def test_to_dict_omits_empty_fields(self):
        """Empty lists and dicts should be omitted from output."""
        status = WorkflowStatus(has_circleci=True)
        data = status.to_dict()

        assert "workflow_files" not in data
        assert "additional_metadata" not in data

    def test_from_dict_no_ci(self):
        """Create status from dictionary with no CI."""
        data = {
            "has_github_actions": False,
            "has_jenkins": False,
            "has_circleci": False,
            "has_travis": False,
            "has_gitlab_ci": False,
        }
        status = WorkflowStatus.from_dict(data)

        assert status.has_github_actions is False
        assert status.has_jenkins is False
        assert status.primary_ci_system is None

    def test_from_dict_single_ci(self):
        """Create status from dictionary with single CI."""
        data = {
            "has_github_actions": True,
            "workflow_files": [".github/workflows/test.yml"],
            "primary_ci_system": "github_actions",
        }
        status = WorkflowStatus.from_dict(data)

        assert status.has_github_actions is True
        assert status.workflow_files == [".github/workflows/test.yml"]
        assert status.primary_ci_system == "github_actions"

    def test_from_dict_multiple_ci(self):
        """Create status from dictionary with multiple CI systems."""
        data = {
            "has_github_actions": True,
            "has_jenkins": True,
            "has_circleci": False,
            "has_travis": False,
            "has_gitlab_ci": False,
            "workflow_files": ["ci.yml", "Jenkinsfile"],
            "primary_ci_system": "jenkins",
            "additional_metadata": {"custom": "data"},
        }
        status = WorkflowStatus.from_dict(data)

        assert status.has_github_actions is True
        assert status.has_jenkins is True
        assert status.primary_ci_system == "jenkins"
        assert status.additional_metadata["custom"] == "data"

    def test_from_dict_defaults(self):
        """from_dict should use defaults for missing fields."""
        data = {}
        status = WorkflowStatus.from_dict(data)

        assert status.has_github_actions is False
        assert status.has_jenkins is False
        assert status.workflow_files == []
        assert status.primary_ci_system is None

    def test_round_trip_conversion(self):
        """Test to_dict -> from_dict preserves data."""
        original = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=True,
            workflow_files=[".github/workflows/ci.yml", "Jenkinsfile"],
            additional_metadata={"branches": ["main", "develop"]},
        )

        data = original.to_dict()
        restored = WorkflowStatus.from_dict(data)

        assert restored.has_github_actions == original.has_github_actions
        assert restored.has_jenkins == original.has_jenkins
        assert restored.workflow_files == original.workflow_files
        assert restored.primary_ci_system == original.primary_ci_system
        assert restored.additional_metadata == original.additional_metadata


class TestWorkflowStatusProperties:
    """Test property methods and computed values."""

    def test_has_any_ci_true(self):
        """has_any_ci should be True when any CI system detected."""
        for attr in [
            "has_github_actions",
            "has_jenkins",
            "has_circleci",
            "has_travis",
            "has_gitlab_ci",
        ]:
            status = WorkflowStatus(**{attr: True})
            assert status.has_any_ci is True

    def test_has_any_ci_false(self):
        """has_any_ci should be False when no CI systems detected."""
        status = WorkflowStatus()
        assert status.has_any_ci is False

    def test_ci_system_count_zero(self):
        """ci_system_count should be 0 when no CI."""
        status = WorkflowStatus()
        assert status.ci_system_count == 0

    def test_ci_system_count_one(self):
        """ci_system_count should be 1 when single CI."""
        status = WorkflowStatus(has_github_actions=True)
        assert status.ci_system_count == 1

    def test_ci_system_count_multiple(self):
        """ci_system_count should count all detected systems."""
        status = WorkflowStatus(has_github_actions=True, has_jenkins=True, has_circleci=True)
        assert status.ci_system_count == 3

    def test_ci_system_count_all(self):
        """ci_system_count with all systems enabled."""
        status = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=True,
            has_circleci=True,
            has_travis=True,
            has_gitlab_ci=True,
        )
        assert status.ci_system_count == 5

    def test_has_multiple_ci_systems_true(self):
        """has_multiple_ci_systems should be True when > 1."""
        status = WorkflowStatus(has_github_actions=True, has_jenkins=True)
        assert status.has_multiple_ci_systems is True

    def test_has_multiple_ci_systems_false_one(self):
        """has_multiple_ci_systems should be False with one system."""
        status = WorkflowStatus(has_github_actions=True)
        assert status.has_multiple_ci_systems is False

    def test_has_multiple_ci_systems_false_none(self):
        """has_multiple_ci_systems should be False with no systems."""
        status = WorkflowStatus()
        assert status.has_multiple_ci_systems is False

    def test_get_detected_systems_none(self):
        """get_detected_systems should return empty list when no CI."""
        status = WorkflowStatus()
        systems = status.get_detected_systems()
        assert systems == []

    def test_get_detected_systems_single(self):
        """get_detected_systems should return single system."""
        status = WorkflowStatus(has_github_actions=True)
        systems = status.get_detected_systems()
        assert systems == ["github_actions"]

    def test_get_detected_systems_multiple(self):
        """get_detected_systems should return all detected systems."""
        status = WorkflowStatus(has_github_actions=True, has_jenkins=True, has_circleci=True)
        systems = status.get_detected_systems()
        assert "github_actions" in systems
        assert "jenkins" in systems
        assert "circleci" in systems
        assert len(systems) == 3

    def test_get_detected_systems_all(self):
        """get_detected_systems with all systems."""
        status = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=True,
            has_circleci=True,
            has_travis=True,
            has_gitlab_ci=True,
        )
        systems = status.get_detected_systems()
        assert systems == ["github_actions", "jenkins", "circleci", "travis", "gitlab_ci"]

    def test_get_detected_systems_order(self):
        """get_detected_systems should maintain consistent order."""
        status = WorkflowStatus(has_gitlab_ci=True, has_github_actions=True, has_travis=True)
        systems = status.get_detected_systems()
        # Should be in definition order
        assert systems[0] == "github_actions"
        assert systems[1] == "travis"
        assert systems[2] == "gitlab_ci"


class TestWorkflowStatusEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_many_workflow_files(self):
        """Handle many workflow files."""
        files = [f".github/workflows/workflow{i}.yml" for i in range(100)]
        status = WorkflowStatus(has_github_actions=True, workflow_files=files)
        assert len(status.workflow_files) == 100

    def test_unicode_in_workflow_files(self):
        """Handle unicode in workflow file paths."""
        status = WorkflowStatus(
            has_github_actions=True, workflow_files=[".github/workflows/тест.yml"]
        )
        assert status.workflow_files[0] == ".github/workflows/тест.yml"

    def test_complex_additional_metadata(self):
        """Handle complex nested metadata."""
        metadata = {
            "workflows": {
                "ci": {"triggers": ["push", "pull_request"]},
                "cd": {"triggers": ["release"]},
            },
            "matrix": {"os": ["ubuntu", "macos", "windows"], "python": ["3.8", "3.9", "3.10"]},
        }
        status = WorkflowStatus(has_github_actions=True, additional_metadata=metadata)
        assert status.additional_metadata["workflows"]["ci"]["triggers"][0] == "push"
        assert len(status.additional_metadata["matrix"]["os"]) == 3

    def test_empty_workflow_files_list(self):
        """Empty workflow_files list should be valid."""
        status = WorkflowStatus(has_github_actions=True, workflow_files=[])
        assert status.workflow_files == []
        assert status.has_github_actions is True

    def test_workflow_files_without_ci_flags(self):
        """Can have workflow_files without CI flags set."""
        status = WorkflowStatus(workflow_files=[".github/workflows/unknown.yml"])
        assert len(status.workflow_files) == 1
        assert status.has_any_ci is False

    def test_all_ci_systems_enabled(self):
        """All CI systems can be enabled simultaneously."""
        status = WorkflowStatus(
            has_github_actions=True,
            has_jenkins=True,
            has_circleci=True,
            has_travis=True,
            has_gitlab_ci=True,
        )
        assert status.has_any_ci is True
        assert status.ci_system_count == 5
        assert status.has_multiple_ci_systems is True

    def test_special_characters_in_file_paths(self):
        """Handle special characters in workflow file paths."""
        status = WorkflowStatus(
            has_github_actions=True,
            workflow_files=[
                ".github/workflows/test-ci.yml",
                ".github/workflows/deploy_prod.yml",
                ".github/workflows/check@v2.yml",
            ],
        )
        assert len(status.workflow_files) == 3
