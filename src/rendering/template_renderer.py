# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Template Renderer with Jinja2 Support.

Provides a clean interface for template rendering with custom filters,
caching, and error handling.

Phase 8: Renderer Modernization
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import logging


class TemplateRenderer:
    """
    Modern template renderer with Jinja2.

    Handles template loading, custom filter registration, and rendering
    for multiple output formats (Markdown, HTML, JSON).

    Features:
        - Template caching
        - Custom Jinja2 filters
        - Multiple output formats
        - Theme support
        - Error handling

    Example:
        >>> renderer = TemplateRenderer(theme='default')
        >>> context = {'project': {'name': 'MyProject'}, ...}
        >>> markdown = renderer.render_markdown(context)
        >>> html = renderer.render_html(context)
    """

    def __init__(
        self,
        template_dir: Optional[Path] = None,
        theme: str = 'default'
    ):
        """
        Initialize template renderer.

        Args:
            template_dir: Path to templates directory (default: src/templates)
            theme: Theme name for HTML rendering
        """
        self.template_dir = template_dir or self._get_default_template_dir()
        self.theme = theme
        self.logger = logging.getLogger(__name__)

        # Create Jinja2 environment
        self.env = self._create_jinja_env()

        # Register custom filters
        self._register_filters()

    def _get_default_template_dir(self) -> Path:
        """Get default templates directory."""
        # Assuming we're in src/rendering/template_renderer.py
        current_file = Path(__file__)
        src_dir = current_file.parent.parent
        return src_dir / 'templates'

    def _create_jinja_env(self) -> Environment:
        """
        Create and configure Jinja2 environment.

        Returns:
            Configured Jinja2 Environment
        """
        loader = FileSystemLoader(str(self.template_dir))

        env = Environment(
            loader=loader,
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        return env

    def _register_filters(self):
        """Register custom Jinja2 filters."""
        from .formatters import (
            format_number,
            format_date,
            format_percentage,
            pluralize
        )

        self.env.filters['format_number'] = format_number
        self.env.filters['format_date'] = format_date
        self.env.filters['format_percentage'] = format_percentage
        self.env.filters['pluralize'] = pluralize

    def render_markdown(self, context: Dict[str, Any]) -> str:
        """
        Render Markdown report.

        Args:
            context: Template context data

        Returns:
            Rendered Markdown content

        Raises:
            TemplateNotFound: If template doesn't exist
            Exception: For other rendering errors
        """
        try:
            template = self.env.get_template('markdown/report.md.j2')
            return str(template.render(**context))
        except TemplateNotFound as e:
            self.logger.error(f"Template not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error rendering markdown template: {e}")
            raise

    def render_html(self, context: Dict[str, Any]) -> str:
        """
        Render HTML report.

        Args:
            context: Template context data

        Returns:
            Rendered HTML content

        Raises:
            TemplateNotFound: If template doesn't exist
            Exception: For other rendering errors
        """
        # Add theme to context
        context_with_theme = {**context, 'theme': self.theme}

        try:
            template = self.env.get_template('html/report.html.j2')
            return str(template.render(**context_with_theme))
        except TemplateNotFound as e:
            self.logger.error(f"Template not found: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error rendering HTML template: {e}")
            raise

    def render_json(self, context: Dict[str, Any]) -> str:
        """
        Render JSON report.

        Args:
            context: Template context data

        Returns:
            JSON string
        """
        # Clean context for JSON serialization
        # (remove any non-serializable objects)
        try:
            return json.dumps(context, indent=2, default=str, sort_keys=True)
        except Exception as e:
            self.logger.error(f"Error rendering JSON: {e}")
            raise

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render arbitrary template by name.

        Args:
            template_name: Template path relative to template_dir
            context: Template context data

        Returns:
            Rendered content

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            template = self.env.get_template(template_name)
            return str(template.render(**context))
        except TemplateNotFound as e:
            self.logger.error(f"Template not found: {template_name}")
            raise
        except Exception as e:
            self.logger.error(f"Error rendering template {template_name}: {e}")
            raise

    def list_templates(self) -> list:
        """
        List available templates.

        Returns:
            List of template names
        """
        return list(self.env.list_templates())
