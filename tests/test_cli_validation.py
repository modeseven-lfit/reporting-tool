# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for CLI Validation Module

Tests for dry run mode and pre-flight checks including:
- Configuration validation
- API credential checks
- Filesystem validation
- Network connectivity
- System requirements

Phase 9: CLI & UX Improvements
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from cli.validation import (
    DryRunValidator,
    ValidationResult,
    dry_run,
)


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult class."""

    def test_passed_result(self):
        """Test passed validation result."""
        result = ValidationResult(True, "Check passed")
        self.assertTrue(result.passed)
        self.assertEqual(result.message, "Check passed")
        self.assertIsNone(result.suggestion)
        self.assertEqual(result.severity, "error")

    def test_failed_result(self):
        """Test failed validation result."""
        result = ValidationResult(False, "Check failed", suggestion="Fix it", severity="warning")
        self.assertFalse(result.passed)
        self.assertEqual(result.message, "Check failed")
        self.assertEqual(result.suggestion, "Fix it")
        self.assertEqual(result.severity, "warning")

    def test_repr(self):
        """Test string representation."""
        passed = ValidationResult(True, "Success")
        failed = ValidationResult(False, "Failed")

        self.assertIn("✓", repr(passed))
        self.assertIn("Success", repr(passed))
        self.assertIn("✗", repr(failed))
        self.assertIn("Failed", repr(failed))


class TestDryRunValidator(unittest.TestCase):
    """Test DryRunValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repos_dir = Path(self.temp_dir) / "repos"
        self.output_dir = Path(self.temp_dir) / "output"
        self.repos_dir.mkdir()

        # Create a sample git repo
        sample_repo = self.repos_dir / "test-repo"
        sample_repo.mkdir()
        (sample_repo / ".git").mkdir()

        self.valid_config = {
            "project": {"name": "test-project"},
            "paths": {"repos": str(self.repos_dir)},
            "output": {"dir": str(self.output_dir)},
            "api": {
                "github": {
                    "token": "ghp_test1234567890123456789012345678901234",
                    "url": "https://api.github.com",
                },
                "gerrit": {"auth": "user:pass"},
            },
            "cache": {"enabled": False},
        }

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_validate_config_structure_success(self):
        """Test successful configuration structure validation."""
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_config_structure()

        self.assertTrue(result.passed)
        self.assertIn("valid", result.message.lower())

    def test_validate_config_structure_missing_sections(self):
        """Test configuration structure validation with missing sections."""
        config = {"project": {}}
        validator = DryRunValidator(config)
        result = validator._validate_config_structure()

        self.assertFalse(result.passed)
        self.assertIn("missing", result.message.lower())
        self.assertIn("paths", result.message)

    def test_validate_required_fields_success(self):
        """Test successful required fields validation."""
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_required_fields()

        self.assertTrue(result.passed)
        self.assertIn("present", result.message.lower())

    def test_validate_required_fields_missing(self):
        """Test required fields validation with missing fields."""
        config = {"project": {}, "paths": {}, "output": {}}
        validator = DryRunValidator(config)
        result = validator._validate_required_fields()

        self.assertFalse(result.passed)
        self.assertIn("missing", result.message.lower())
        self.assertIn("project.name", result.message)

    def test_validate_project_name_success(self):
        """Test successful project name validation."""
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_project_name()

        self.assertTrue(result.passed)
        self.assertIn("test-project", result.message)

    def test_validate_project_name_empty(self):
        """Test project name validation with empty name."""
        config = self.valid_config.copy()
        config["project"] = {"name": ""}
        validator = DryRunValidator(config)
        result = validator._validate_project_name()

        self.assertFalse(result.passed)
        self.assertIn("empty", result.message.lower())

    def test_validate_project_name_too_long(self):
        """Test project name validation with name too long."""
        config = self.valid_config.copy()
        config["project"] = {"name": "a" * 101}
        validator = DryRunValidator(config)
        result = validator._validate_project_name()

        self.assertFalse(result.passed)
        self.assertIn("too long", result.message.lower())

    def test_validate_project_name_invalid_chars(self):
        """Test project name validation with invalid characters."""
        config = self.valid_config.copy()
        config["project"] = {"name": "test/project"}
        validator = DryRunValidator(config)
        result = validator._validate_project_name()

        self.assertFalse(result.passed)
        self.assertIn("invalid", result.message.lower())

    def test_validate_repos_path_success(self):
        """Test successful repos path validation."""
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_repos_path()

        self.assertTrue(result.passed)
        self.assertIn("1 repositories", result.message)

    def test_validate_repos_path_not_configured(self):
        """Test repos path validation when not configured."""
        config = self.valid_config.copy()
        config["paths"] = {}
        validator = DryRunValidator(config)
        result = validator._validate_repos_path()

        self.assertFalse(result.passed)
        self.assertIn("not configured", result.message.lower())

    def test_validate_repos_path_not_exists(self):
        """Test repos path validation when path doesn't exist."""
        config = self.valid_config.copy()
        config["paths"]["repos"] = "/nonexistent/path"
        validator = DryRunValidator(config)
        result = validator._validate_repos_path()

        self.assertFalse(result.passed)
        self.assertIn("does not exist", result.message.lower())

    def test_validate_repos_path_not_directory(self):
        """Test repos path validation when path is not a directory."""
        config = self.valid_config.copy()
        file_path = Path(self.temp_dir) / "file.txt"
        file_path.write_text("test")
        config["paths"]["repos"] = str(file_path)
        validator = DryRunValidator(config)
        result = validator._validate_repos_path()

        self.assertFalse(result.passed)
        self.assertIn("not a directory", result.message.lower())

    def test_validate_repos_path_no_repos(self):
        """Test repos path validation with no repositories."""
        empty_dir = Path(self.temp_dir) / "empty"
        empty_dir.mkdir()
        config = self.valid_config.copy()
        config["paths"]["repos"] = str(empty_dir)
        validator = DryRunValidator(config)
        result = validator._validate_repos_path()

        self.assertTrue(result.passed)
        self.assertEqual(result.severity, "warning")
        self.assertIn("No repositories found", result.message)

    def test_validate_api_credentials_success(self):
        """Test successful API credentials validation."""
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_api_credentials()

        self.assertTrue(result.passed)
        self.assertIn("configured", result.message.lower())

    def test_validate_api_credentials_missing_github(self):
        """Test API credentials validation with missing GitHub token."""
        config = self.valid_config.copy()
        config["api"] = {"github": {}, "gerrit": {"auth": "test"}}
        validator = DryRunValidator(config)
        result = validator._validate_api_credentials()

        self.assertTrue(result.passed)
        self.assertEqual(result.severity, "warning")
        self.assertIn("GitHub token", result.message)

    def test_validate_api_credentials_invalid_github_token(self):
        """Test API credentials validation with invalid GitHub token."""
        config = self.valid_config.copy()
        config["api"]["github"]["token"] = "ghp_short"
        validator = DryRunValidator(config)
        result = validator._validate_api_credentials()

        self.assertTrue(result.passed)
        self.assertEqual(result.severity, "warning")
        self.assertIn("invalid", result.message.lower())

    @patch("socket.create_connection")
    def test_validate_network_connectivity_success(self, mock_connect):
        """Test successful network connectivity validation."""
        mock_connect.return_value = MagicMock()
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_network_connectivity()

        self.assertTrue(result.passed)
        self.assertIn("available", result.message.lower())

    @patch("socket.create_connection")
    def test_validate_network_connectivity_failure(self, mock_connect):
        """Test network connectivity validation failure."""
        mock_connect.side_effect = OSError("Network error")
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_network_connectivity()

        self.assertTrue(result.passed)
        self.assertEqual(result.severity, "warning")
        self.assertIn("failed", result.message.lower())

    @patch("urllib.request.urlopen")
    def test_validate_api_endpoints_success(self, mock_urlopen):
        """Test successful API endpoints validation."""
        mock_urlopen.return_value = MagicMock()
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_api_endpoints()

        self.assertTrue(result.passed)
        self.assertIn("reachable", result.message.lower())

    @patch("urllib.request.urlopen")
    def test_validate_api_endpoints_failure(self, mock_urlopen):
        """Test API endpoints validation with unreachable endpoints."""
        mock_urlopen.side_effect = Exception("Connection failed")
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_api_endpoints()

        self.assertTrue(result.passed)
        self.assertEqual(result.severity, "warning")
        self.assertIn("unreachable", result.message.lower())

    def test_validate_output_directory_success(self):
        """Test successful output directory validation."""
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_output_directory()

        self.assertTrue(result.passed)
        self.assertIn("writable", result.message.lower())
        self.assertTrue(self.output_dir.exists())

    def test_validate_output_directory_creates_if_missing(self):
        """Test output directory validation creates directory if missing."""
        self.assertFalse(self.output_dir.exists())
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_output_directory()

        self.assertTrue(result.passed)
        self.assertTrue(self.output_dir.exists())

    @patch("shutil.disk_usage")
    def test_validate_disk_space_success(self, mock_disk):
        """Test successful disk space validation."""
        mock_disk.return_value = MagicMock(free=10 * 1024**3)  # 10 GB
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_disk_space()

        self.assertTrue(result.passed)
        self.assertIn("available", result.message.lower())
        self.assertIn("GB", result.message)

    @patch("shutil.disk_usage")
    def test_validate_disk_space_low(self, mock_disk):
        """Test disk space validation with low space."""
        mock_disk.return_value = MagicMock(free=500 * 1024**2)  # 500 MB
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_disk_space()

        self.assertTrue(result.passed)
        self.assertEqual(result.severity, "warning")
        self.assertIn("Low disk space", result.message)

    def test_validate_cache_directory_disabled(self):
        """Test cache directory validation when caching disabled."""
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_cache_directory()

        self.assertTrue(result.passed)
        self.assertEqual(result.severity, "info")
        self.assertIn("disabled", result.message.lower())

    def test_validate_cache_directory_enabled(self):
        """Test cache directory validation when caching enabled."""
        config = self.valid_config.copy()
        cache_dir = Path(self.temp_dir) / "cache"
        config["cache"] = {"enabled": True, "dir": str(cache_dir)}
        validator = DryRunValidator(config)
        result = validator._validate_cache_directory()

        self.assertTrue(result.passed)
        self.assertIn("writable", result.message.lower())
        self.assertTrue(cache_dir.exists())

    @patch("shutil.which")
    def test_validate_git_available_success(self, mock_which):
        """Test successful git availability validation."""
        mock_which.return_value = "/usr/bin/git"
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_git_available()

        self.assertTrue(result.passed)
        self.assertIn("available", result.message.lower())

    @patch("shutil.which")
    def test_validate_git_available_failure(self, mock_which):
        """Test git availability validation failure."""
        mock_which.return_value = None
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_git_available()

        self.assertFalse(result.passed)
        self.assertIn("not found", result.message.lower())

    def test_validate_python_version_success(self):
        """Test successful Python version validation."""
        validator = DryRunValidator(self.valid_config)
        result = validator._validate_python_version()

        # Should pass on Python 3.8+

        self.assertTrue(result.passed)

    def test_validate_all_success(self):
        """Test validate_all with successful validation."""
        validator = DryRunValidator(self.valid_config)

        with (
            patch.object(validator, "_validate_network_connectivity") as mock_net,
            patch.object(validator, "_validate_api_endpoints") as mock_api,
        ):
            mock_net.return_value = ValidationResult(True, "Network OK")
            mock_api.return_value = ValidationResult(True, "APIs OK")

            success, results = validator.validate_all()

        self.assertTrue(success)
        self.assertGreater(len(results), 0)

        # Check that various validations were included
        messages = [r.message for r in results]
        self.assertTrue(any("configuration" in m.lower() for m in messages))
        self.assertTrue(any("project name" in m.lower() for m in messages))

    def test_validate_all_with_errors(self):
        """Test validate_all with validation errors."""
        config = self.valid_config.copy()
        config["project"]["name"] = ""  # Invalid
        validator = DryRunValidator(config)

        success, results = validator.validate_all(skip_network=True)

        self.assertFalse(success)
        errors = [r for r in results if not r.passed and r.severity == "error"]
        self.assertGreater(len(errors), 0)

    def test_validate_all_skip_network(self):
        """Test validate_all with skip_network=True."""
        validator = DryRunValidator(self.valid_config)
        success, results = validator.validate_all(skip_network=True)

        # Network checks should not be included
        messages = [r.message for r in results]
        self.assertFalse(any("connectivity" in m.lower() for m in messages))
        self.assertFalse(any("endpoints" in m.lower() for m in messages))

    def test_print_results(self):
        """Test print_results method."""
        validator = DryRunValidator(self.valid_config)
        results = [
            ValidationResult(True, "Check 1 passed"),
            ValidationResult(False, "Check 2 failed", "Fix it", "error"),
            ValidationResult(True, "Warning check", "Consider this", "warning"),
            ValidationResult(True, "Info", severity="info"),
        ]

        # Should not raise exception
        validator.print_results(results)


class TestDryRunFunction(unittest.TestCase):
    """Test dry_run function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.repos_dir = Path(self.temp_dir) / "repos"
        self.output_dir = Path(self.temp_dir) / "output"
        self.repos_dir.mkdir()

        self.valid_config = {
            "project": {"name": "test"},
            "paths": {"repos": str(self.repos_dir)},
            "output": {"dir": str(self.output_dir)},
            "api": {},
            "cache": {"enabled": False},
        }

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_dry_run_success(self):
        """Test dry_run with successful validation."""
        exit_code = dry_run(self.valid_config, skip_network=True)
        self.assertEqual(exit_code, 0)

    def test_dry_run_failure(self):
        """Test dry_run with validation failure."""
        config = self.valid_config.copy()
        config["project"]["name"] = ""  # Invalid

        exit_code = dry_run(config, skip_network=True)
        self.assertEqual(exit_code, 1)

    def test_dry_run_with_logger(self):
        """Test dry_run with logger."""
        import logging

        logger = logging.getLogger("test")

        exit_code = dry_run(self.valid_config, logger=logger, skip_network=True)
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
