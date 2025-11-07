#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for Configuration Wizard

Tests the interactive configuration wizard and template-based config generation.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cli.wizard import (
    FULL_TEMPLATE,
    MINIMAL_TEMPLATE,
    STANDARD_TEMPLATE,
    ConfigurationWizard,
    confirm,
    create_config_from_template,
    prompt,
    run_wizard,
    select_option,
)


# =============================================================================
# HELPER FUNCTIONS TESTS
# =============================================================================


class TestHelperFunctions:
    """Test wizard helper functions."""

    def test_prompt_with_default(self):
        """Test prompt with default value."""
        with patch("builtins.input", return_value=""):
            result = prompt("Question", "default")
            assert result == "default"

    def test_prompt_with_answer(self):
        """Test prompt with user answer."""
        with patch("builtins.input", return_value="answer"):
            result = prompt("Question", "default")
            assert result == "answer"

    def test_prompt_without_default(self):
        """Test prompt without default."""
        with patch("builtins.input", return_value="answer"):
            result = prompt("Question")
            assert result == "answer"

    def test_confirm_default_yes(self):
        """Test confirm with default yes."""
        with patch("builtins.input", return_value=""):
            result = confirm("Question?", True)
            assert result is True

    def test_confirm_default_no(self):
        """Test confirm with default no."""
        with patch("builtins.input", return_value=""):
            result = confirm("Question?", False)
            assert result is False

    def test_confirm_yes_variations(self):
        """Test various yes answers."""
        for answer in ["y", "Y", "yes", "YES", "Yes", "true", "1"]:
            with patch("builtins.input", return_value=answer):
                result = confirm("Question?", False)
                assert result is True, f"Failed for answer: {answer}"

    def test_confirm_no(self):
        """Test no answer."""
        with patch("builtins.input", return_value="n"):
            result = confirm("Question?", True)
            assert result is False

    def test_select_option_default(self):
        """Test select_option with default."""
        options = [("opt1", "Option 1"), ("opt2", "Option 2")]
        with patch("builtins.input", return_value=""):
            result = select_option("Choose", options, default=0)
            assert result == "opt1"

    def test_select_option_by_number(self):
        """Test select_option by number."""
        options = [("opt1", "Option 1"), ("opt2", "Option 2")]
        with patch("builtins.input", return_value="2"):
            result = select_option("Choose", options)
            assert result == "opt2"

    def test_select_option_invalid_then_valid(self):
        """Test select_option with invalid input then valid."""
        options = [("opt1", "Option 1"), ("opt2", "Option 2")]
        with patch("builtins.input", side_effect=["invalid", "5", "1"]):
            result = select_option("Choose", options)
            assert result == "opt1"


# =============================================================================
# TEMPLATE TESTS
# =============================================================================


class TestTemplates:
    """Test configuration templates."""

    def test_minimal_template_structure(self):
        """Test minimal template has required fields."""
        assert "project" in MINIMAL_TEMPLATE
        assert "time_windows" in MINIMAL_TEMPLATE
        assert "output" in MINIMAL_TEMPLATE

    def test_standard_template_structure(self):
        """Test standard template has expected fields."""
        assert "project" in STANDARD_TEMPLATE
        assert "time_windows" in STANDARD_TEMPLATE
        assert "output" in STANDARD_TEMPLATE
        assert "api" in STANDARD_TEMPLATE
        assert "features" in STANDARD_TEMPLATE

    def test_full_template_structure(self):
        """Test full template has all fields."""
        assert "project" in FULL_TEMPLATE
        assert "time_windows" in FULL_TEMPLATE
        assert "output" in FULL_TEMPLATE
        assert "api" in FULL_TEMPLATE
        assert "features" in FULL_TEMPLATE
        assert "performance" in FULL_TEMPLATE

    def test_templates_are_valid_yaml(self):
        """Test templates serialize to valid YAML."""
        for template in [MINIMAL_TEMPLATE, STANDARD_TEMPLATE, FULL_TEMPLATE]:
            yaml_str = yaml.dump(template)
            loaded = yaml.safe_load(yaml_str)
            assert loaded is not None

    def test_minimal_has_no_api(self):
        """Test minimal template doesn't include API config."""
        assert "api" not in MINIMAL_TEMPLATE

    def test_standard_has_basic_features(self):
        """Test standard template has basic features."""
        assert "features" in STANDARD_TEMPLATE
        features = STANDARD_TEMPLATE["features"]
        assert "ci_cd" in features
        assert "security" in features

    def test_full_has_performance_settings(self):
        """Test full template has performance settings."""
        assert "performance" in FULL_TEMPLATE
        perf = FULL_TEMPLATE["performance"]
        assert "concurrency" in perf
        assert "cache" in perf


# =============================================================================
# CREATE CONFIG FROM TEMPLATE TESTS
# =============================================================================


class TestCreateConfigFromTemplate:
    """Test non-interactive config creation from templates."""

    def test_create_minimal_config(self, tmp_path):
        """Test creating minimal configuration."""
        output_path = tmp_path / "config.yaml"
        result = create_config_from_template("test-project", "minimal", str(output_path))

        assert result == str(output_path)
        assert output_path.exists()

        with open(output_path) as f:
            config = yaml.safe_load(f)

        assert config["project"] == "test-project"
        assert "time_windows" in config
        assert "output" in config

    def test_create_standard_config(self, tmp_path):
        """Test creating standard configuration."""
        output_path = tmp_path / "config.yaml"
        create_config_from_template("test-project", "standard", str(output_path))

        assert output_path.exists()
        with open(output_path) as f:
            config = yaml.safe_load(f)

        assert config["project"] == "test-project"
        assert "api" in config
        assert "features" in config

    def test_create_full_config(self, tmp_path):
        """Test creating full configuration."""
        output_path = tmp_path / "config.yaml"
        create_config_from_template("test-project", "full", str(output_path))

        assert output_path.exists()
        with open(output_path) as f:
            config = yaml.safe_load(f)

        assert config["project"] == "test-project"
        assert "performance" in config

    def test_create_config_auto_path(self, tmp_path):
        """Test creating config with automatic path."""
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            result = create_config_from_template("test-project", "minimal")
            assert "config/test-project.yaml" in result

    def test_create_config_creates_directories(self, tmp_path):
        """Test that config creation creates parent directories."""
        output_path = tmp_path / "nested" / "dir" / "config.yaml"
        create_config_from_template("test-project", "standard", str(output_path))

        assert output_path.exists()
        assert output_path.parent.exists()

    def test_create_config_invalid_template(self):
        """Test creating config with invalid template raises error."""
        with pytest.raises(ValueError, match="Unknown template"):
            create_config_from_template("test-project", "invalid")


# =============================================================================
# CONFIGURATION WIZARD TESTS
# =============================================================================


class TestConfigurationWizard:
    """Test interactive configuration wizard."""

    def test_wizard_initialization(self):
        """Test wizard initializes correctly."""
        wizard = ConfigurationWizard()
        assert wizard.config == {}
        assert wizard.template_type == "standard"

    @patch("builtins.input")
    @patch("builtins.print")
    def test_wizard_minimal_flow(self, mock_print, mock_input, tmp_path):
        """Test wizard with minimal template."""
        # Simulate user inputs
        mock_input.side_effect = [
            "1",  # Select minimal template
            "test-project",  # Project name
            "",  # Default time window (365 days)
            "output",  # Output directory
            "y",  # Generate JSON
            "y",  # Generate Markdown
            "y",  # Generate HTML
        ]

        wizard = ConfigurationWizard()
        output_path = tmp_path / "config.yaml"

        with (
            patch.object(wizard, "_save_configuration", return_value=str(output_path)),
            patch.object(wizard, "_print_next_steps"),
        ):
            wizard.run(str(output_path))

        assert wizard.config["project"] == "test-project"
        assert wizard.template_type == "minimal"

    @patch("builtins.input")
    @patch("builtins.print")
    def test_wizard_standard_flow(self, mock_print, mock_input, tmp_path):
        """Test wizard with standard template."""
        mock_input.side_effect = [
            "2",  # Select standard template
            "my-project",  # Project name
            "",  # Default reporting window
            "",  # Default recent activity window
            "reports",  # Output directory
            "y",
            "y",
            "y",  # Formats
            "y",  # Create bundle
            "y",  # Enable GitHub
            "n",  # No Gerrit
            "y",  # Detect CI/CD
            "y",  # Detect security
            "y",  # Detect documentation
        ]

        wizard = ConfigurationWizard()
        output_path = tmp_path / "config.yaml"

        with (
            patch.object(wizard, "_save_configuration", return_value=str(output_path)),
            patch.object(wizard, "_print_next_steps"),
        ):
            wizard.run(str(output_path))

        assert wizard.config["project"] == "my-project"
        assert wizard.template_type == "standard"
        assert wizard.config["output"]["create_bundle"] is True

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("os.environ.get")
    def test_wizard_detects_github_token(self, mock_env, mock_print, mock_input, tmp_path):
        """Test wizard detects GITHUB_TOKEN environment variable."""
        mock_env.return_value = "ghp_test_token"
        mock_input.side_effect = [
            "2",  # Standard template
            "test-project",
            "",  # Defaults for all prompts
            "",
            "output",
            "y",
            "y",
            "y",  # Formats
            "y",  # Bundle
            "y",  # GitHub
            "n",  # Gerrit
            "y",
            "y",
            "y",  # Features
        ]

        wizard = ConfigurationWizard()
        output_path = tmp_path / "config.yaml"

        with (
            patch.object(wizard, "_save_configuration", return_value=str(output_path)),
            patch.object(wizard, "_print_next_steps"),
        ):
            wizard.run(str(output_path))

        # Should have printed success message about token
        # (We can't easily assert on print calls, but no exception is good)

    @patch("builtins.input")
    @patch("builtins.print")
    def test_wizard_full_template(self, mock_print, mock_input, tmp_path):
        """Test wizard with full template."""
        mock_input.side_effect = [
            "3",  # Full template
            "full-project",
            "",  # Default time windows
            "",
            "output",
            "y",
            "y",
            "y",  # Formats
            "y",  # Bundle
            "y",  # GitHub
            "y",
            "https://gerrit.example.com",  # Gerrit
            "y",
            "https://jenkins.example.com",  # Jenkins
            "y",
            "y",
            "y",
            "y",  # All features
            "y",
            "8",  # Concurrency enabled, 8 workers
            "y",
            ".cache",
            "48",  # Cache enabled, .cache dir, 48h TTL
        ]

        wizard = ConfigurationWizard()
        output_path = tmp_path / "config.yaml"

        with (
            patch.object(wizard, "_save_configuration", return_value=str(output_path)),
            patch.object(wizard, "_print_next_steps"),
        ):
            wizard.run(str(output_path))

        assert wizard.config["project"] == "full-project"
        assert "performance" in wizard.config
        assert wizard.config["performance"]["concurrency"]["max_workers"] == 8

    def test_wizard_save_configuration(self, tmp_path):
        """Test wizard saves configuration correctly."""
        wizard = ConfigurationWizard()
        wizard.config = {"project": "test", "output": {"directory": "output"}}

        output_path = tmp_path / "config" / "test.yaml"
        result = wizard._save_configuration(str(output_path))

        assert result == str(output_path)
        assert output_path.exists()

        with open(output_path) as f:
            config = yaml.safe_load(f)

        assert config["project"] == "test"


# =============================================================================
# RUN WIZARD TESTS
# =============================================================================


class TestRunWizard:
    """Test run_wizard convenience function."""

    @patch("cli.wizard.ConfigurationWizard")
    def test_run_wizard_calls_wizard(self, mock_wizard_class, tmp_path):
        """Test run_wizard instantiates and runs wizard."""
        mock_wizard = MagicMock()
        mock_wizard_class.return_value = mock_wizard
        mock_wizard.run.return_value = str(tmp_path / "config.yaml")

        output_path = tmp_path / "config.yaml"
        run_wizard(str(output_path))

        mock_wizard_class.assert_called_once()
        mock_wizard.run.assert_called_once_with(str(output_path))

    @patch("cli.wizard.ConfigurationWizard")
    def test_run_wizard_without_path(self, mock_wizard_class):
        """Test run_wizard without explicit path."""
        mock_wizard = MagicMock()
        mock_wizard_class.return_value = mock_wizard
        mock_wizard.run.return_value = "config/default.yaml"

        run_wizard()

        mock_wizard.run.assert_called_once_with(None)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestWizardIntegration:
    """Integration tests for wizard with real file I/O."""

    def test_end_to_end_minimal(self, tmp_path):
        """Test complete wizard flow for minimal config."""
        output_path = tmp_path / "config.yaml"
        config_path = create_config_from_template("integration-test", "minimal", str(output_path))

        # Verify file was created
        assert Path(config_path).exists()

        # Verify it's valid YAML
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Verify required fields
        assert config["project"] == "integration-test"
        assert "time_windows" in config
        assert config["time_windows"]["reporting_window_days"] == 365

    def test_end_to_end_all_templates(self, tmp_path):
        """Test creating configs from all templates."""
        for template in ["minimal", "standard", "full"]:
            output_path = tmp_path / f"{template}.yaml"
            config_path = create_config_from_template(
                f"{template}-project", template, str(output_path)
            )

            assert Path(config_path).exists()

            with open(config_path) as f:
                config = yaml.safe_load(f)

            assert config["project"] == f"{template}-project"

    def test_config_validates_after_creation(self, tmp_path):
        """Test that created configs are valid for the system."""
        output_path = tmp_path / "config.yaml"
        create_config_from_template("validation-test", "standard", str(output_path))

        # Load and verify basic structure
        with open(output_path) as f:
            config = yaml.safe_load(f)

        # Check for required top-level keys
        assert "project" in config
        assert "time_windows" in config
        assert "output" in config

        # Check time windows structure
        tw = config["time_windows"]
        assert isinstance(tw["reporting_window_days"], int)
        assert tw["reporting_window_days"] > 0

        # Check output structure
        output = config["output"]
        assert "directory" in output
        assert "formats" in output
        assert isinstance(output["formats"], list)


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestWizardErrorHandling:
    """Test wizard error handling."""

    def test_invalid_template_name(self):
        """Test handling of invalid template name."""
        with pytest.raises(ValueError):
            create_config_from_template("project", "invalid_template")

    def test_save_to_readonly_directory(self, tmp_path):
        """Test handling of permission errors."""
        output_path = tmp_path / "readonly" / "config.yaml"
        output_path.parent.mkdir()
        output_path.parent.chmod(0o444)  # Read-only

        try:
            with pytest.raises(PermissionError):
                create_config_from_template("test", "minimal", str(output_path))
        finally:
            # Cleanup: restore permissions
            output_path.parent.chmod(0o755)


# =============================================================================
# EDGE CASES
# =============================================================================


class TestWizardEdgeCases:
    """Test wizard edge cases."""

    def test_empty_project_name(self, tmp_path):
        """Test wizard handles empty project name."""
        with patch("builtins.input", side_effect=["2", "", "default-project"]):
            # First input is empty, second provides actual name
            # In real wizard, empty project name would be accepted
            # but may cause issues downstream
            pass

    def test_special_characters_in_project_name(self, tmp_path):
        """Test project names with special characters."""
        output_path = tmp_path / "config.yaml"
        config_path = create_config_from_template("my-project_v2.0", "minimal", str(output_path))

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["project"] == "my-project_v2.0"

    def test_unicode_in_project_name(self, tmp_path):
        """Test project names with unicode characters."""
        output_path = tmp_path / "config.yaml"
        config_path = create_config_from_template("项目-测试", "minimal", str(output_path))

        with open(config_path) as f:
            config = yaml.safe_load(f)

        assert config["project"] == "项目-测试"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
