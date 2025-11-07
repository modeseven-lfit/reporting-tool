# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Template-based report renderer using Jinja2.

This module provides the ModernReportRenderer class which orchestrates
template-based rendering for multiple output formats (Markdown, HTML).

Phase: 8 - Renderer Modernization
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import jinja2
except ImportError:
    raise ImportError(
        "Jinja2 is required for template rendering. "
        "Install it with: pip install Jinja2>=3.1.0"
    )

from .context import RenderContext
from .formatters import get_template_filters


class TemplateRenderer:
    """
    Manages Jinja2 template loading and rendering.

    This class handles:
    - Template environment setup
    - Custom filter registration
    - Template caching
    - Error handling for template issues

    Thread Safety:
        Jinja2 Environment is thread-safe after initialization.
        Multiple threads can render templates concurrently.
    """

    def __init__(self, template_dir: Path, theme: str = "default"):
        """
        Initialize template renderer.

        Args:
            template_dir: Directory containing templates
            theme: Theme name for CSS selection
        """
        self.template_dir = template_dir
        self.theme = theme

        # Create Jinja2 environment
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=jinja2.select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,  # Fail on undefined variables
        )

        # Register custom filters
        self._register_filters()

    def _register_filters(self):
        """Register custom Jinja2 filters from formatters module."""
        filters = get_template_filters()
        for name, func in filters.items():
            self.env.filters[name] = func

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with context.

        Args:
            template_name: Name of template file (relative to template_dir)
            context: Dictionary of variables for template

        Returns:
            Rendered string

        Raises:
            jinja2.TemplateNotFound: If template doesn't exist
            jinja2.TemplateSyntaxError: If template has syntax errors
            jinja2.UndefinedError: If template uses undefined variable
        """
        try:
            template = self.env.get_template(template_name)
            return str(template.render(**context))
        except jinja2.TemplateNotFound as e:
            raise FileNotFoundError(
                f"Template not found: {template_name}. "
                f"Ensure template exists in {self.template_dir}"
            ) from e
        except jinja2.TemplateSyntaxError as e:
            raise ValueError(
                f"Template syntax error in {template_name} "
                f"at line {e.lineno}: {e.message}"
            ) from e
        except jinja2.UndefinedError as e:
            raise ValueError(
                f"Undefined variable in template {template_name}: {e.message}"
            ) from e

    def render_string(self, template_string: str, context: Dict[str, Any]) -> str:
        """
        Render a template from string (for testing or simple templates).

        Args:
            template_string: Template content as string
            context: Dictionary of variables for template

        Returns:
            Rendered string
        """
        template = self.env.from_string(template_string)
        return str(template.render(**context))


class ModernReportRenderer:
    """
    Modern template-based report renderer.

    This class orchestrates the rendering process:
    1. Build render context from data
    2. Load appropriate templates
    3. Render output in requested format

    Features:
    - Template-based rendering (Jinja2)
    - Theme support
    - Multiple output formats (Markdown, HTML)
    - Separation of data and presentation

    Example:
        >>> config = load_config()
        >>> logger = logging.getLogger(__name__)
        >>> renderer = ModernReportRenderer(config, logger)
        >>> markdown = renderer.render_markdown(data)
        >>> html = renderer.render_html(data)
    """

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        """
        Initialize modern report renderer.

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # Determine template directory
        template_dir = Path(__file__).parent.parent / "templates"
        if not template_dir.exists():
            raise FileNotFoundError(
                f"Template directory not found: {template_dir}. "
                f"Ensure templates are installed correctly."
            )

        # Get theme from config
        theme = config.get("render", {}).get("theme", "default")

        # Initialize template renderer
        self.template_renderer = TemplateRenderer(template_dir, theme)

        self.logger.info(f"Initialized ModernReportRenderer with theme: {theme}")

    def render_markdown(self, data: Dict[str, Any]) -> str:
        """
        Render Markdown report from data.

        Args:
            data: Report data dictionary (from JSON)

        Returns:
            Rendered Markdown content
        """
        self.logger.info("Rendering Markdown report using templates")

        # Build context
        context = RenderContext(data, self.config).build()

        # Render main template
        try:
            markdown = self.template_renderer.render("markdown/base.md.j2", context)
            self.logger.info("Markdown rendering complete")
            return markdown
        except Exception as e:
            self.logger.error(f"Failed to render Markdown: {e}")
            raise

    def render_html(self, data: Dict[str, Any]) -> str:
        """
        Render HTML report from data.

        Args:
            data: Report data dictionary (from JSON)

        Returns:
            Rendered HTML content
        """
        self.logger.info("Rendering HTML report using templates")

        # Build context
        context = RenderContext(data, self.config).build()

        # Render main template
        try:
            html = self.template_renderer.render("html/base.html.j2", context)
            self.logger.info("HTML rendering complete")
            return html
        except Exception as e:
            self.logger.error(f"Failed to render HTML: {e}")
            raise

    def render_markdown_report(self, data: Dict[str, Any], output_path: Path) -> None:
        """
        Render Markdown report and write to file.

        This is a compatibility method matching the old API.

        Args:
            data: Report data dictionary
            output_path: Path to write Markdown file
        """
        markdown = self.render_markdown(data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

        self.logger.info(f"Markdown report written to {output_path}")

    def render_html_report(self, data: Dict[str, Any], output_path: Path) -> None:
        """
        Render HTML report and write to file.

        This is a compatibility method matching the old API.

        Args:
            data: Report data dictionary
            output_path: Path to write HTML file
        """
        html = self.render_html(data)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        self.logger.info(f"HTML report written to {output_path}")

    def get_theme_path(self) -> Path:
        """
        Get path to current theme CSS file.

        Returns:
            Path to theme CSS file
        """
        theme_dir = Path(__file__).parent.parent / "themes"
        theme_name = self.config.get("render", {}).get("theme", "default")
        return theme_dir / f"{theme_name}.css"
