#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Git Utility Functions

This module provides utility functions for safely executing Git commands
with proper error handling and logging.
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional


def safe_git_command(
    cmd: list[str], cwd: Optional[Path], logger: logging.Logger
) -> tuple[bool, str]:
    """
    Execute a git command safely with error handling.

    Args:
        cmd: List of command arguments (e.g., ['git', 'log', '--oneline'])
        cwd: Working directory for the command (None for current directory)
        logger: Logger instance for recording errors

    Returns:
        Tuple of (success: bool, output_or_error: str)
        - If success=True, the second element is the stdout output
        - If success=False, the second element is the error message
    """
    try:
        git_result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout for long operations
            check=False,
        )

        if git_result.returncode == 0:
            return True, git_result.stdout
        else:
            error_msg = git_result.stderr.strip() or git_result.stdout.strip()
            logger.debug(f"Git command failed: {' '.join(cmd)}: {error_msg}")
            return False, error_msg

    except subprocess.TimeoutExpired:
        error_msg = f"Git command timed out after 300 seconds: {' '.join(cmd)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Git command exception: {e}"
        logger.error(error_msg)
        return False, error_msg
