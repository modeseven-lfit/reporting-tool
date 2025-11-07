#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit Tests for ZIP Bundle Utilities

Tests for the ZIP bundling functions extracted in Phase 1 refactoring.
These tests cover ZIP creation, validation, error handling, and edge cases.
"""

import logging
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from util.zip_bundle import (
    create_report_bundle,
    validate_zip_bundle,
)


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory with sample report files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "test_project"
        project_dir.mkdir()

        # Create sample report files
        (project_dir / "report.json").write_text('{"test": "data"}')
        (project_dir / "report.md").write_text("# Test Report")
        (project_dir / "report.html").write_text("<html><body>Test</body></html>")
        (project_dir / "config.yaml").write_text("setting: value")

        yield project_dir


@pytest.fixture
def empty_project_dir():
    """Create an empty temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "empty_project"
        project_dir.mkdir()
        yield project_dir


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    return MagicMock(spec=logging.Logger)


class TestCreateReportBundle:
    """Tests for create_report_bundle function."""

    def test_create_bundle_success(self, temp_project_dir, mock_logger):
        """Test successful ZIP bundle creation."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # Verify ZIP was created
        assert zip_path.exists()
        assert zip_path.name == "test_project_report_bundle.zip"
        assert zip_path.parent == temp_project_dir

        # Verify logger was called
        mock_logger.info.assert_called()

    def test_bundle_contains_all_files(self, temp_project_dir, mock_logger):
        """Test that ZIP contains all project files."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()

            # Check that all files are included
            assert any("report.json" in name for name in names)
            assert any("report.md" in name for name in names)
            assert any("report.html" in name for name in names)
            assert any("config.yaml" in name for name in names)

    def test_bundle_structure(self, temp_project_dir, mock_logger):
        """Test that ZIP has correct internal structure."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()

            # All files should be under reports/project_name/
            for name in names:
                assert name.startswith("reports/test_project/")

    def test_bundle_compression(self, temp_project_dir, mock_logger):
        """Test that ZIP uses compression."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            # Check compression type
            for info in zipf.infolist():
                assert info.compress_type == zipfile.ZIP_DEFLATED

    def test_bundle_content_integrity(self, temp_project_dir, mock_logger):
        """Test that file contents are preserved in ZIP."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            # Read and verify JSON content
            json_content = None
            for name in zipf.namelist():
                if name.endswith("report.json"):
                    json_content = zipf.read(name).decode("utf-8")
                    break

            assert json_content == '{"test": "data"}'

    def test_bundle_excludes_existing_zip(self, temp_project_dir, mock_logger):
        """Test that existing ZIP files are not included in new ZIP."""
        # Create an existing ZIP
        existing_zip = temp_project_dir / "test_project_report_bundle.zip"
        existing_zip.write_text("old zip")

        # Create new bundle
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # The new ZIP should not contain itself
        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            assert not any("_report_bundle.zip" in name for name in names)

    def test_bundle_with_empty_directory(self, empty_project_dir, mock_logger):
        """Test bundle creation with empty directory."""
        zip_path = create_report_bundle(empty_project_dir, "empty_project", mock_logger)

        # ZIP should still be created
        assert zip_path.exists()

        # Logger should warn about empty directory
        mock_logger.warning.assert_called()
        warning_message = mock_logger.warning.call_args[0][0]
        assert "No files found" in warning_message

    def test_bundle_nonexistent_directory(self, mock_logger):
        """Test error when directory doesn't exist."""
        nonexistent = Path("/nonexistent/directory")

        with pytest.raises(ValueError, match="does not exist"):
            create_report_bundle(nonexistent, "test", mock_logger)

    def test_bundle_with_subdirectories(self, temp_project_dir, mock_logger):
        """Test that only files in root directory are included (not subdirs)."""
        # Create a subdirectory with files
        subdir = temp_project_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested content")

        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()

            # Subdirectory files should not be included
            assert not any("nested.txt" in name for name in names)

            # Root files should still be included
            assert any("report.json" in name for name in names)

    def test_bundle_return_value(self, temp_project_dir, mock_logger):
        """Test that function returns correct Path object."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        assert isinstance(zip_path, Path)
        assert zip_path.exists()
        assert zip_path.is_file()

    def test_bundle_logging_output(self, temp_project_dir, mock_logger):
        """Test that appropriate logging messages are generated."""
        create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # Check that info messages were logged
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]

        # Should log start and completion
        assert any("Creating report bundle" in msg for msg in info_calls)
        assert any("Report bundle created" in msg for msg in info_calls)

    def test_bundle_with_special_characters_in_filename(self, temp_project_dir, mock_logger):
        """Test bundling files with special characters in names."""
        # Create file with special characters
        special_file = temp_project_dir / "report-2024_v1.0.json"
        special_file.write_text('{"version": "1.0"}')

        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            assert any("report-2024_v1.0.json" in name for name in names)

    def test_bundle_large_file(self, temp_project_dir, mock_logger):
        """Test bundling with a large file."""
        # Create a larger file (1MB)
        large_file = temp_project_dir / "large_report.txt"
        large_file.write_text("x" * (1024 * 1024))

        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        assert zip_path.exists()

        # Verify compression reduced size
        original_size = large_file.stat().st_size
        compressed_size = zip_path.stat().st_size
        assert compressed_size < original_size

    def test_bundle_multiple_file_types(self, temp_project_dir, mock_logger):
        """Test bundling various file types."""
        # Add different file types
        (temp_project_dir / "data.csv").write_text("col1,col2\n1,2")
        (temp_project_dir / "script.py").write_text("print('hello')")
        (temp_project_dir / "README.txt").write_text("readme content")

        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            assert any("data.csv" in name for name in names)
            assert any("script.py" in name for name in names)
            assert any("README.txt" in name for name in names)


class TestValidateZipBundle:
    """Tests for validate_zip_bundle function."""

    def test_validate_valid_zip(self, temp_project_dir, mock_logger):
        """Test validation of a valid ZIP file."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        assert validate_zip_bundle(zip_path) is True

    def test_validate_nonexistent_zip(self):
        """Test validation of nonexistent file."""
        nonexistent = Path("/nonexistent/file.zip")
        assert validate_zip_bundle(nonexistent) is False

    def test_validate_corrupted_zip(self, temp_project_dir):
        """Test validation of corrupted ZIP file."""
        corrupted_zip = temp_project_dir / "corrupted.zip"
        corrupted_zip.write_text("This is not a valid ZIP file")

        assert validate_zip_bundle(corrupted_zip) is False

    def test_validate_zip_with_corrupted_member(self, temp_project_dir, mock_logger):
        """Test validation of ZIP with corrupted member (testzip path)."""
        # Create a valid ZIP first
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # Corrupt the ZIP by truncating it
        with open(zip_path, "r+b") as f:
            f.seek(0, 2)  # Go to end
            size = f.tell()
            # Truncate to corrupt the last member
            f.truncate(size - 50)

        # This should return False due to ZIP corruption
        assert validate_zip_bundle(zip_path) is False

    def test_validate_with_expected_files(self, temp_project_dir, mock_logger):
        """Test validation with expected files list."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # Validate with correct expected files
        expected = ["report.json", "report.md", "report.html"]
        assert validate_zip_bundle(zip_path, expected) is True

    def test_validate_missing_expected_file(self, temp_project_dir, mock_logger):
        """Test validation fails when expected file is missing."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # Validate with file that doesn't exist
        expected = ["report.json", "missing_file.txt"]
        assert validate_zip_bundle(zip_path, expected) is False

    def test_validate_empty_expected_list(self, temp_project_dir, mock_logger):
        """Test validation with empty expected files list."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # Empty list should pass (just validates ZIP integrity)
        assert validate_zip_bundle(zip_path, []) is True

    def test_validate_none_expected_files(self, temp_project_dir, mock_logger):
        """Test validation with None for expected files."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # None should pass (just validates ZIP integrity)
        assert validate_zip_bundle(zip_path, None) is True

    def test_validate_partial_filename_match(self, temp_project_dir, mock_logger):
        """Test that validation matches on filename suffix."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # Should match even without full path
        expected = ["report.json"]
        assert validate_zip_bundle(zip_path, expected) is True

    def test_validate_case_sensitive_filenames(self, temp_project_dir, mock_logger):
        """Test that filename matching is case-sensitive."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # Case mismatch should fail
        expected = ["REPORT.JSON"]  # Wrong case
        assert validate_zip_bundle(zip_path, expected) is False

    def test_validate_regular_file_not_zip(self, temp_project_dir):
        """Test validation of regular file (not ZIP)."""
        regular_file = temp_project_dir / "regular.txt"
        regular_file.write_text("just text")

        assert validate_zip_bundle(regular_file) is False

    def test_validate_empty_zip(self, temp_project_dir):
        """Test validation of empty ZIP file."""
        empty_zip = temp_project_dir / "empty.zip"

        with zipfile.ZipFile(empty_zip, "w", zipfile.ZIP_DEFLATED):
            pass  # Create empty ZIP

        # Empty ZIP is still valid
        assert validate_zip_bundle(empty_zip) is True

    def test_validate_zip_with_directory_entries(self, temp_project_dir):
        """Test validation of ZIP containing directory entries."""
        zip_with_dirs = temp_project_dir / "with_dirs.zip"

        with zipfile.ZipFile(zip_with_dirs, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("reports/", "")  # Directory entry
            zipf.writestr("reports/test.txt", "content")

        assert validate_zip_bundle(zip_with_dirs) is True
        assert validate_zip_bundle(zip_with_dirs, ["test.txt"]) is True


class TestEdgeCases:
    """Edge case and boundary condition tests."""

    def test_bundle_with_unicode_filenames(self, temp_project_dir, mock_logger):
        """Test bundling files with unicode characters in names."""
        unicode_file = temp_project_dir / "report_日本語.txt"
        unicode_file.write_text("content")

        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        assert zip_path.exists()

        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            # Unicode filename should be preserved
            assert any("日本語" in name for name in names)

    def test_bundle_with_very_long_filename(self, temp_project_dir, mock_logger):
        """Test bundling file with very long name."""
        long_name = "report_" + "x" * 200 + ".txt"
        long_file = temp_project_dir / long_name
        long_file.write_text("content")

        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        assert zip_path.exists()

    def test_bundle_with_hidden_files(self, temp_project_dir, mock_logger):
        """Test bundling hidden files (starting with dot)."""
        hidden_file = temp_project_dir / ".hidden_config"
        hidden_file.write_text("hidden content")

        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            # Hidden files should be included
            assert any(".hidden_config" in name for name in names)

    def test_bundle_with_zero_byte_file(self, temp_project_dir, mock_logger):
        """Test bundling empty (0-byte) files."""
        empty_file = temp_project_dir / "empty.txt"
        empty_file.touch()

        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with zipfile.ZipFile(zip_path, "r") as zipf:
            names = zipf.namelist()
            assert any("empty.txt" in name for name in names)

    def test_bundle_permission_error(self, temp_project_dir, mock_logger):
        """Test handling of permission errors."""
        with (
            patch("zipfile.ZipFile", side_effect=PermissionError("Access denied")),
            pytest.raises(PermissionError),
        ):
            create_report_bundle(temp_project_dir, "test_project", mock_logger)

    def test_validate_zip_io_error(self, temp_project_dir, mock_logger):
        """Test validation handles I/O errors gracefully."""
        zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

        with patch("zipfile.ZipFile", side_effect=OSError("I/O error")):
            assert validate_zip_bundle(zip_path) is False

    def test_bundle_project_name_with_special_chars(self, temp_project_dir, mock_logger):
        """Test bundle creation with special characters in project name."""
        project_name = "test-project_v1.0"

        zip_path = create_report_bundle(temp_project_dir, project_name, mock_logger)

        assert zip_path.name == f"{project_name}_report_bundle.zip"
        assert zip_path.exists()

    def test_bundle_with_symlinks(self, temp_project_dir, mock_logger):
        """Test handling of symbolic links in directory."""
        # Create a regular file and a symlink to it
        regular_file = temp_project_dir / "original.txt"
        regular_file.write_text("original content")

        try:
            symlink_file = temp_project_dir / "symlink.txt"
            symlink_file.symlink_to(regular_file)

            zip_path = create_report_bundle(temp_project_dir, "test_project", mock_logger)

            assert zip_path.exists()
        except OSError:
            # Skip test if symlinks not supported (e.g., Windows without admin)
            pytest.skip("Symlinks not supported on this platform")


class TestLoggingBehavior:
    """Tests focused on logging behavior."""

    def test_debug_logging_for_each_file(self, temp_project_dir, mock_logger):
        """Test that debug message is logged for each file added."""
        create_report_bundle(temp_project_dir, "test_project", mock_logger)

        # Should have debug calls for each file
        debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]

        assert any("report.json" in msg for msg in debug_calls)
        assert any("report.md" in msg for msg in debug_calls)
        assert any("report.html" in msg for msg in debug_calls)

    def test_info_logging_includes_file_count(self, temp_project_dir, mock_logger):
        """Test that completion message includes file count."""
        create_report_bundle(temp_project_dir, "test_project", mock_logger)

        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        completion_msg = [msg for msg in info_calls if "Report bundle created" in msg][0]

        # Should mention number of files (4 in this case)
        assert "4 files" in completion_msg

    def test_logging_singular_file(self, empty_project_dir, mock_logger):
        """Test that logging uses singular 'file' for count of 1."""
        # Create exactly one file
        (empty_project_dir / "single.txt").write_text("content")

        create_report_bundle(empty_project_dir, "test", mock_logger)

        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        completion_msg = [msg for msg in info_calls if "Report bundle created" in msg][0]

        # Should use "1 file" not "1 files"
        assert "1 file)" in completion_msg or "1 file " in completion_msg


# Pytest markers for categorization
pytestmark = pytest.mark.unit
