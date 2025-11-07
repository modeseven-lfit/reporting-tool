# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Modern Report Renderer.

Orchestrates context building and template rendering for report generation.

Phase 8: Renderer Modernization
"""

from pathlib import Path
from typing import Any, Dict, Optional
import logging

from .context_builder import RenderContextBuilder
from .template_renderer import TemplateRenderer


class ModernReportRenderer:
    """
    Modern renderer for repository analysis reports.

    Coordinates context building and template rendering to generate
    reports in multiple formats (Markdown, HTML, JSON).

    Example:
        >>> renderer = ModernReportRenderer(theme='default')
        >>> renderer.render_markdown(analysis_data, output_path / 'report.md')
        >>> renderer.render_html(analysis_data, output_path / 'report.html')
    """

    def __init__(
        self,
        template_dir: Optional[Path] = None,
        theme: str = 'default'
    ):
        """
        Initialize modern renderer.

        Args:
            template_dir: Path to templates directory
            theme: Theme name for HTML rendering
        """
        self.theme = theme
        self.logger = logging.getLogger(__name__)

        # Create template renderer
        self.template_renderer = TemplateRenderer(
            template_dir=template_dir,
            theme=theme
        )

    def render_markdown(
        self,
        analysis_data: Dict[str, Any],
        output_path: Path
    ) -> bool:
        """
        Render Markdown report.

        Args:
            analysis_data: Raw analysis results
            output_path: Path to write Markdown file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build context
            builder = RenderContextBuilder(analysis_data)

            if not builder.validate():
                self.logger.error("Invalid analysis data")
                return False

            context = builder.build()

            # Render template
            content = self.template_renderer.render_markdown(context)

            # Write to file
            output_path.write_text(content, encoding='utf-8')

            self.logger.info(f"Markdown report written to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error rendering Markdown report: {e}")
            return False

    def render_html(
        self,
        analysis_data: Dict[str, Any],
        output_path: Path
    ) -> bool:
        """
        Render HTML report.

        Args:
            analysis_data: Raw analysis results
            output_path: Path to write HTML file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build context
            builder = RenderContextBuilder(analysis_data)

            if not builder.validate():
                self.logger.error("Invalid analysis data")
                return False

            context = builder.build()

            # Render template
            content = self.template_renderer.render_html(context)

            # Write to file
            output_path.write_text(content, encoding='utf-8')

            self.logger.info(f"HTML report written to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error rendering HTML report: {e}")
            return False

    def render_json(
        self,
        analysis_data: Dict[str, Any],
        output_path: Path
    ) -> bool:
        """
        Render JSON report.

        Args:
            analysis_data: Raw analysis results
            output_path: Path to write JSON file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build context
            builder = RenderContextBuilder(analysis_data)

            if not builder.validate():
                self.logger.error("Invalid analysis data")
                return False

            context = builder.build()

            # Render JSON
            content = self.template_renderer.render_json(context)

            # Write to file
            output_path.write_text(content, encoding='utf-8')

            self.logger.info(f"JSON report written to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error rendering JSON report: {e}")
            return False

    def get_context(self, analysis_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get rendering context without rendering.

        Useful for testing or custom rendering.

        Args:
            analysis_data: Raw analysis results

        Returns:
            Rendering context dictionary, or None if invalid
        """
        try:
            builder = RenderContextBuilder(analysis_data)

            if not builder.validate():
                self.logger.error("Invalid analysis data")
                return None

            return builder.build()

        except Exception as e:
            self.logger.error(f"Error building context: {e}")
            return None
