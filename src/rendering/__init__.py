# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Rendering package for repository reporting system.

This package provides template-based rendering for reports in multiple formats
(Markdown, HTML). It separates data preparation from presentation using Jinja2
templates and supports theme customization.

Architecture:
    - context.py: RenderContext for preparing data for templates
    - context_builder.py: RenderContextBuilder for data preparation (Phase 8)
    - template_renderer.py: Jinja2 template renderer (Phase 8)
    - modern_renderer.py: Modern renderer orchestrator (Phase 8)
    - renderer.py: ModernReportRenderer orchestrator (legacy)
    - formatters.py: Reusable formatting utilities (filters)
    - legacy_adapter.py: Backward compatibility wrapper for gradual migration

Phase: 8 - Renderer Modernization
"""

from .context import RenderContext
from .context_builder import RenderContextBuilder
from .template_renderer import TemplateRenderer as ModernTemplateRenderer
from .modern_renderer import ModernReportRenderer as NewModernReportRenderer
from .renderer import ModernReportRenderer, TemplateRenderer
from .formatters import (
    format_number,
    format_age,
    format_percentage,
    slugify,
    format_date,
)
from .legacy_adapter import LegacyRendererAdapter, create_legacy_renderer

__all__ = [
    "RenderContext",
    "RenderContextBuilder",
    "ModernTemplateRenderer",
    "NewModernReportRenderer",
    "ModernReportRenderer",
    "TemplateRenderer",
    "LegacyRendererAdapter",
    "create_legacy_renderer",
    "format_number",
    "format_age",
    "format_percentage",
    "slugify",
    "format_date",
]

__version__ = "1.0.0"
