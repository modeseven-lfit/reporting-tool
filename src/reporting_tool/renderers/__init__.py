# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Report renderers for the reporting-tool package.

This package contains modules for rendering repository metrics and
aggregated data into various output formats:
- JSON (canonical structured data)
- Markdown (human-readable formatted text)
- HTML (styled web-viewable reports)
- ZIP (bundled report packages)
"""

from .report import ReportRenderer

__all__ = ['ReportRenderer']
