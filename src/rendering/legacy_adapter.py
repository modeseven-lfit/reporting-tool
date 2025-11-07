"""
Legacy Adapter for Report Rendering

This module provides backward compatibility between the legacy ReportRenderer
(in generate_reports.py) and the modern ModernReportRenderer (in rendering/).

The adapter allows gradual migration from the old rendering system to the new
template-based system without breaking existing code.

Phase 8: Renderer Modernization
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .renderer import ModernReportRenderer
from .context import RenderContext


class LegacyRendererAdapter:
    """
    Adapter that wraps ModernReportRenderer to match the legacy ReportRenderer API.

    This class allows the new rendering system to be used as a drop-in replacement
    for the old one, preserving the existing interface while using the modern
    template-based implementation internally.

    Example:
        >>> # Old code (still works):
        >>> renderer = LegacyRendererAdapter(config, logger)
        >>> renderer.render_markdown_report(data, output_path)

        >>> # Internally uses:
        >>> # modern_renderer.render_markdown_report(data, output_path)
    """

    def __init__(
        self,
        config: Dict[str, Any],
        logger: logging.Logger
    ) -> None:
        """
        Initialize the legacy adapter.

        Args:
            config: Configuration dictionary (legacy format)
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # Initialize modern renderer with config and logger
        self.modern_renderer = ModernReportRenderer(config, logger)

    def render_json_report(self, data: Dict[str, Any], output_path: Path) -> None:
        """
        Render JSON report (simple JSON serialization).

        Args:
            data: Report data dictionary
            output_path: Output file path
        """
        self.logger.info(f"Writing JSON report to {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def render_markdown_report(
        self,
        data: Dict[str, Any],
        output_path: Path
    ) -> str:
        """
        Render Markdown report using modern template system.

        This method maintains backward compatibility by:
        1. Converting legacy data format to render context
        2. Using modern template renderer
        3. Returning content string (for HTML conversion)

        Args:
            data: Report data in legacy format
            output_path: Output file path for Markdown

        Returns:
            Rendered Markdown content as string
        """
        self.logger.info(f"Rendering Markdown report (modern) to {output_path}")

        # Render using modern system
        self.modern_renderer.render_markdown_report(data, output_path)

        # Read back the content to return (for backward compatibility)
        # Legacy code expects this method to return the content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return content

    def render_html_report(
        self,
        data: Dict[str, Any],
        output_path: Path,
        markdown_content: Optional[str] = None
    ) -> None:
        """
        Render HTML report using modern template system.

        This method provides two modes:
        1. Legacy mode: Convert provided markdown_content to HTML
        2. Modern mode: Generate HTML directly from data using templates

        Args:
            data: Report data dictionary
            output_path: Output file path
            markdown_content: Optional pre-rendered Markdown (legacy mode)
        """
        if markdown_content:
            # Legacy mode: User provided markdown content to convert
            self.logger.info(
                f"Converting Markdown to HTML (legacy mode) at {output_path}"
            )
            # Use the legacy conversion for now, but log a deprecation warning
            self.logger.warning(
                "HTML conversion from Markdown is deprecated. "
                "Use render_html_report(data, path) for native HTML rendering."
            )
            self._convert_markdown_to_html_legacy(markdown_content, output_path)
        else:
            # Modern mode: Generate HTML directly from data
            self.logger.info(
                f"Rendering HTML report (modern) to {output_path}"
            )
            self.modern_renderer.render_html_report(data, output_path)

    def _convert_markdown_to_html_legacy(
        self,
        markdown_content: str,
        output_path: Path
    ) -> None:
        """
        Legacy Markdown-to-HTML conversion wrapper.

        For now, this generates a simple HTML wrapper around the Markdown content.
        In a future phase, this could use a Markdown parser or be removed entirely.

        Args:
            markdown_content: Markdown content string
            output_path: Output HTML file path
        """
        # Simple HTML wrapper (maintains basic compatibility)
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Repository Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            color: #333;
        }}
        pre {{
            background: #f5f5f5;
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 0.75rem;
            text-align: left;
        }}
        th {{
            background: #f5f5f5;
            font-weight: 600;
        }}
        code {{
            background: #f5f5f5;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: "Monaco", "Courier New", monospace;
            font-size: 0.9em;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}
    </style>
</head>
<body>
    <pre>{}</pre>
</body>
</html>"""

        html_content = html_template.format(markdown_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def package_zip_report(self, output_dir: Path, project: str) -> Path:
        """
        Package all report outputs into a ZIP file.

        This delegates to the utility function for consistency.

        Args:
            output_dir: Directory containing report files
            project: Project name

        Returns:
            Path to created ZIP file
        """
        from ..util.zip_bundle import create_report_bundle
        return create_report_bundle(output_dir, project, self.logger)


def create_legacy_renderer(
    config: Dict[str, Any],
    logger: logging.Logger,
    use_modern: bool = True
) -> LegacyRendererAdapter:
    """
    Factory function to create a renderer compatible with legacy code.

    This function provides a smooth migration path:
    - When use_modern=True: Returns LegacyRendererAdapter (new system)
    - When use_modern=False: Could return original ReportRenderer (not implemented)

    Args:
        config: Configuration dictionary
        logger: Logger instance
        use_modern: Whether to use modern renderer (default: True)

    Returns:
        Renderer instance compatible with legacy API

    Example:
        >>> config = load_configuration()
        >>> logger = logging.getLogger(__name__)
        >>> renderer = create_legacy_renderer(config, logger, use_modern=True)
        >>> renderer.render_markdown_report(data, Path("report.md"))
    """
    if not use_modern:
        raise NotImplementedError(
            "Legacy renderer not available. "
            "Set use_modern=True to use the modern renderer."
        )

    return LegacyRendererAdapter(config=config, logger=logger)
