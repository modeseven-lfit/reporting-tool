# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
ZIP Bundle Utilities

Functions for creating ZIP archives of report outputs.
Pure utility functions with no side effects beyond file I/O.

Extracted from generate_reports.py as part of Phase 1 refactoring.
"""

import logging
import zipfile
from pathlib import Path
from typing import Optional


def create_report_bundle(
    project_output_dir: Path,
    project: str,
    logger: logging.Logger
) -> Path:
    """
    Package all report artifacts into a ZIP file.

    Bundles JSON, Markdown, HTML, and resolved config files into a single
    compressed archive for easy distribution and archival.

    Args:
        project_output_dir: Directory containing report files to bundle
        project: Project name (used in ZIP filename)
        logger: Logger instance for progress/error messages

    Returns:
        Path to the created ZIP file

    Raises:
        OSError: If ZIP creation fails
        ValueError: If output directory doesn't exist or is empty

    Examples:
        >>> from pathlib import Path
        >>> import logging
        >>> logger = logging.getLogger(__name__)
        >>> output_dir = Path("reports/myproject")
        >>> zip_path = create_report_bundle(output_dir, "myproject", logger)
        >>> print(zip_path)
        reports/myproject/myproject_report_bundle.zip
    """
    if not project_output_dir.exists():
        raise ValueError(f"Output directory does not exist: {project_output_dir}")

    logger.info(f"Creating report bundle for project {project}")

    zip_path = project_output_dir / f"{project}_report_bundle.zip"

    # Count files to be added (for logging)
    files_to_add = [
        f for f in project_output_dir.iterdir()
        if f.is_file() and f != zip_path
    ]

    if not files_to_add:
        logger.warning(f"No files found to bundle in {project_output_dir}")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Add all files in the project output directory (except the ZIP itself)
        for file_path in files_to_add:
            # Add to ZIP with relative path structure
            arcname = f"reports/{project}/{file_path.name}"
            zipf.write(file_path, arcname)
            logger.debug(f"Added {file_path.name} to ZIP")

    file_count = len(files_to_add)
    logger.info(
        f"Report bundle created: {zip_path} ({file_count} file{'s' if file_count != 1 else ''})"
    )

    return zip_path


def validate_zip_bundle(zip_path: Path, expected_files: Optional[list[str]] = None) -> bool:
    """
    Validate that a ZIP bundle is readable and contains expected files.

    Args:
        zip_path: Path to ZIP file to validate
        expected_files: Optional list of filenames that must be present

    Returns:
        True if ZIP is valid and contains expected files, False otherwise

    Examples:
        >>> zip_path = Path("reports/myproject/myproject_report_bundle.zip")
        >>> validate_zip_bundle(zip_path)
        True
        >>> validate_zip_bundle(zip_path, ["report.json", "report.md"])
        True
    """
    if not zip_path.exists():
        return False

    try:
        with zipfile.ZipFile(zip_path, "r") as zipf:
            # Test ZIP integrity
            if zipf.testzip() is not None:
                return False

            # Check for expected files if provided
            if expected_files:
                zip_contents = zipf.namelist()
                for expected_file in expected_files:
                    # Check if any archive member ends with the expected filename
                    if not any(member.endswith(expected_file) for member in zip_contents):
                        return False

            return True
    except (zipfile.BadZipFile, OSError):
        return False
