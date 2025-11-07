# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Main entry point for python -m reporting_tool execution.

This module allows the package to be executed as a module:
    python -m reporting_tool [args]

This provides an alternative to the console script entry point
and is useful for development and testing.
"""

from reporting_tool.cli import cli_main

if __name__ == "__main__":
    cli_main()
