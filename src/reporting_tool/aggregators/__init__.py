# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Data aggregators for the reporting-tool package.

This package contains modules for aggregating repository metrics into
global summaries including:
- Repository classification (current/active/inactive)
- Author and organization rollups
- Top/least active repository rankings
- Contributor leaderboards
- Activity status distribution analysis
"""

from .data import DataAggregator

__all__ = ['DataAggregator']
