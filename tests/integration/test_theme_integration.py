# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Integration tests for theme system.

Tests the complete integration of themes with the rendering system,
including theme selection, CSS loading, template rendering, and fallback behavior.

Phase: 8 - Renderer Modernization - Day 5
"""

import json
import logging
from pathlib import Path

import pytest

from rendering.renderer import ModernReportRenderer
from rendering.template_renderer import TemplateRenderer


# Sample test data - matches expected format from context.py
SAMPLE_REPORT_DATA = {
    "project": "Test Project",
    "schema_version": "1.0.0",
    "metadata": {
        "generated_at": "2025-01-28T12:00:00Z",
        "report_version": "1.0.0",
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
    },
    "summaries": {
        "counts": {"total_repositories": 5, "total_contributors": 25, "total_organizations": 2}
    },
    "repositories": [
        {
            "name": "repo1",
            "url": "https://github.com/org/repo1",
            "total_commits": 200,
            "contributors_count": 5,
            "lines_added": 10000,
            "lines_removed": 4000,
        }
    ],
    "contributors": [
        {
            "name": "John Doe",
            "email": "john@example.com",
            "total_commits": 100,
            "lines_added": 5000,
            "lines_removed": 2000,
        }
    ],
    "organizations": [],
    "features": {},
    "workflows": [],
    "orphaned_jobs": [],
    "time_windows": [],
}


class TestThemeSystemIntegration:
    """Integration tests for theme system."""

    @pytest.fixture
    def theme_dir(self):
        """Get path to themes directory."""
        return Path(__file__).parent.parent.parent / "src" / "themes"

    @pytest.fixture
    def template_dir(self):
        """Get path to templates directory."""
        return Path(__file__).parent.parent.parent / "src" / "templates"

    @pytest.fixture
    def logger(self):
        """Create test logger."""
        return logging.getLogger(__name__)

    def test_theme_directories_exist(self, theme_dir):
        """Test that all theme directories exist."""
        assert theme_dir.exists(), "Themes directory should exist"

        # Check each theme
        for theme_name in ["default", "dark", "minimal"]:
            theme_path = theme_dir / theme_name
            assert theme_path.exists(), f"Theme directory {theme_name} should exist"
            assert theme_path.is_dir(), f"Theme {theme_name} should be a directory"

    def test_theme_files_exist(self, theme_dir):
        """Test that all theme files exist."""
        for theme_name in ["default", "dark", "minimal"]:
            theme_path = theme_dir / theme_name

            # Check CSS file
            css_file = theme_path / "theme.css"
            assert css_file.exists(), f"Theme CSS for {theme_name} should exist"
            assert css_file.is_file(), f"Theme CSS for {theme_name} should be a file"

            # Check config file
            config_file = theme_path / "config.json"
            assert config_file.exists(), f"Theme config for {theme_name} should exist"
            assert config_file.is_file(), f"Theme config for {theme_name} should be a file"

    def test_theme_css_valid(self, theme_dir):
        """Test that theme CSS files are valid (non-empty, proper syntax)."""
        for theme_name in ["default", "dark", "minimal"]:
            css_file = theme_dir / theme_name / "theme.css"

            content = css_file.read_text()
            assert len(content) > 0, f"Theme CSS for {theme_name} should not be empty"

            # Basic syntax checks
            assert ":root" in content, f"Theme {theme_name} should define CSS variables"
            assert "background" in content.lower(), f"Theme {theme_name} should define backgrounds"
            assert "color" in content.lower(), f"Theme {theme_name} should define colors"

    def test_theme_config_valid(self, theme_dir):
        """Test that theme config files are valid JSON."""
        for theme_name in ["default", "dark", "minimal"]:
            config_file = theme_dir / theme_name / "config.json"

            # Load and validate JSON
            with open(config_file) as f:
                config = json.load(f)

            # Check required fields
            assert "name" in config, f"Theme {theme_name} config should have 'name'"
            assert "description" in config, f"Theme {theme_name} config should have 'description'"
            assert "version" in config, f"Theme {theme_name} config should have 'version'"
            assert "colors" in config, f"Theme {theme_name} config should have 'colors'"
            assert "accessibility" in config, (
                f"Theme {theme_name} config should have 'accessibility'"
            )

    def test_template_renderer_with_default_theme(self, template_dir):
        """Test TemplateRenderer initialization with default theme."""
        renderer = TemplateRenderer(template_dir, theme="default")

        assert renderer.template_dir == template_dir
        assert renderer.theme == "default"
        assert renderer.env is not None

    def test_template_renderer_with_dark_theme(self, template_dir):
        """Test TemplateRenderer initialization with dark theme."""
        renderer = TemplateRenderer(template_dir, theme="dark")

        assert renderer.theme == "dark"

    def test_template_renderer_with_minimal_theme(self, template_dir):
        """Test TemplateRenderer initialization with minimal theme."""
        renderer = TemplateRenderer(template_dir, theme="minimal")

        assert renderer.theme == "minimal"

    def test_render_html_with_default_theme(self, logger):
        """Test HTML rendering with default theme."""
        config = {"render": {"theme": "default"}}
        renderer = ModernReportRenderer(config, logger)

        html = renderer.render_html(SAMPLE_REPORT_DATA)

        # Check that HTML is generated
        assert len(html) > 0
        assert "<!DOCTYPE html>" in html
        assert "Test Project" in html

        # Check theme reference
        assert 'data-theme="default"' in html
        assert "../themes/default/theme.css" in html

    def test_render_html_with_dark_theme(self, logger):
        """Test HTML rendering with dark theme."""
        config = {"render": {"theme": "dark"}}
        renderer = ModernReportRenderer(config, logger)

        html = renderer.render_html(SAMPLE_REPORT_DATA)

        # Check theme reference
        assert 'data-theme="dark"' in html
        assert "../themes/dark/theme.css" in html

    def test_render_html_with_minimal_theme(self, logger):
        """Test HTML rendering with minimal theme."""
        config = {"render": {"theme": "minimal"}}
        renderer = ModernReportRenderer(config, logger)

        html = renderer.render_html(SAMPLE_REPORT_DATA)

        # Check theme reference
        assert 'data-theme="minimal"' in html
        assert "../themes/minimal/theme.css" in html

    def test_render_html_without_theme_config(self, logger):
        """Test HTML rendering without theme in config (should default)."""
        config = {"render": {}}
        renderer = ModernReportRenderer(config, logger)

        html = renderer.render_html(SAMPLE_REPORT_DATA)

        # Should use default theme
        assert 'data-theme="default"' in html
        assert "../themes/default/theme.css" in html

    def test_render_markdown_with_theme(self, logger):
        """Test Markdown rendering (theme doesn't affect Markdown)."""
        config = {"render": {"theme": "dark"}}
        renderer = ModernReportRenderer(config, logger)

        markdown = renderer.render_markdown(SAMPLE_REPORT_DATA)

        # Check that Markdown is generated
        assert len(markdown) > 0
        assert "Test Project" in markdown

    def test_theme_switching_same_content(self, logger):
        """Test that different themes produce same content, just different styling."""
        themes = ["default", "dark", "minimal"]
        html_outputs = {}

        for theme in themes:
            config = {"render": {"theme": theme}}
            renderer = ModernReportRenderer(config, logger)
            html = renderer.render_html(SAMPLE_REPORT_DATA)
            html_outputs[theme] = html

        # All should contain the same project name
        for html in html_outputs.values():
            assert "Test Project" in html

        # But themes should be different
        assert html_outputs["default"] != html_outputs["dark"]
        assert html_outputs["default"] != html_outputs["minimal"]
        assert html_outputs["dark"] != html_outputs["minimal"]

    def test_render_to_file_with_theme(self, logger, tmp_path):
        """Test rendering HTML to file with theme."""
        config = {"render": {"theme": "dark"}}
        renderer = ModernReportRenderer(config, logger)

        output_file = tmp_path / "report.html"
        renderer.render_html_report(SAMPLE_REPORT_DATA, output_file)

        # Check file was created
        assert output_file.exists()

        # Check content
        content = output_file.read_text()
        assert 'data-theme="dark"' in content
        assert "../themes/dark/theme.css" in content

    def test_theme_metadata_in_html(self, logger):
        """Test that theme metadata is properly included in HTML."""
        config = {"render": {"theme": "default"}}
        renderer = ModernReportRenderer(config, logger)

        html = renderer.render_html(SAMPLE_REPORT_DATA)

        # Check for theme metadata
        assert '<html lang="en" data-theme="default">' in html
        assert '<meta name="theme" content="default">' in html

    def test_concurrent_rendering_different_themes(self, logger):
        """Test concurrent rendering with different themes (thread safety)."""
        import concurrent.futures

        themes = ["default", "dark", "minimal"] * 3  # 9 total renders

        def render_with_theme(theme):
            config = {"render": {"theme": theme}}
            renderer = ModernReportRenderer(config, logger)
            return renderer.render_html(SAMPLE_REPORT_DATA)

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(render_with_theme, theme) for theme in themes]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert len(results) == 9
        for html in results:
            assert "<!DOCTYPE html>" in html
            assert "Test Project" in html

    # Note: NewModernReportRenderer requires different data structure (context_builder format)
    # Coverage for theme functionality is provided by other tests using ModernReportRenderer


class TestThemeAccessibility:
    """Tests for theme accessibility compliance."""

    @pytest.fixture
    def theme_dir(self):
        """Get path to themes directory."""
        return Path(__file__).parent.parent.parent / "src" / "themes"

    def test_default_theme_wcag_aa_claim(self, theme_dir):
        """Test that default theme claims WCAG AA compliance."""
        config_file = theme_dir / "default" / "config.json"
        with open(config_file) as f:
            config = json.load(f)

        assert config["accessibility"]["wcag_level"] == "AA"
        assert config["accessibility"]["min_contrast_ratio"] >= 4.5

    def test_dark_theme_wcag_aa_claim(self, theme_dir):
        """Test that dark theme claims WCAG AA compliance."""
        config_file = theme_dir / "dark" / "config.json"
        with open(config_file) as f:
            config = json.load(f)

        assert config["accessibility"]["wcag_level"] == "AA"
        assert config["accessibility"]["min_contrast_ratio"] >= 4.5

    def test_minimal_theme_wcag_aaa_claim(self, theme_dir):
        """Test that minimal theme claims WCAG AAA compliance."""
        config_file = theme_dir / "minimal" / "config.json"
        with open(config_file) as f:
            config = json.load(f)

        assert config["accessibility"]["wcag_level"] == "AAA"
        assert config["accessibility"]["min_contrast_ratio"] >= 7.0


class TestThemePerformance:
    """Tests for theme performance characteristics."""

    @pytest.fixture
    def theme_dir(self):
        """Get path to themes directory."""
        return Path(__file__).parent.parent.parent / "src" / "themes"

    def test_theme_css_size(self, theme_dir):
        """Test that theme CSS files are reasonably sized."""
        for theme_name in ["default", "dark", "minimal"]:
            css_file = theme_dir / theme_name / "theme.css"
            size = css_file.stat().st_size

            # Should be under 25KB (unminified)
            assert size < 25000, f"Theme {theme_name} CSS is too large: {size} bytes"

    def test_minimal_theme_smallest(self, theme_dir):
        """Test that minimal theme is the smallest."""
        sizes = {}
        for theme_name in ["default", "dark", "minimal"]:
            css_file = theme_dir / theme_name / "theme.css"
            sizes[theme_name] = css_file.stat().st_size

        # Minimal should be smallest
        assert sizes["minimal"] <= sizes["default"]
        assert sizes["minimal"] <= sizes["dark"]


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing code."""

    @pytest.fixture
    def logger(self):
        """Create test logger."""
        return logging.getLogger(__name__)

    def test_renderer_without_theme_config(self, logger):
        """Test renderer works without theme in config (backward compat)."""
        config = {}  # No render section at all
        renderer = ModernReportRenderer(config, logger)

        html = renderer.render_html(SAMPLE_REPORT_DATA)

        # Should work and use default theme
        assert "<!DOCTYPE html>" in html
        assert 'data-theme="default"' in html

    def test_markdown_rendering_unchanged(self, logger):
        """Test that Markdown rendering is unchanged (no theme impact)."""
        config1 = {"render": {"theme": "default"}}
        config2 = {"render": {"theme": "dark"}}

        renderer1 = ModernReportRenderer(config1, logger)
        renderer2 = ModernReportRenderer(config2, logger)

        md1 = renderer1.render_markdown(SAMPLE_REPORT_DATA)
        md2 = renderer2.render_markdown(SAMPLE_REPORT_DATA)

        # Markdown should be identical regardless of theme
        assert md1 == md2

    def test_existing_api_compatibility(self, logger, tmp_path):
        """Test that existing API methods still work."""
        config = {"render": {"theme": "default"}}
        renderer = ModernReportRenderer(config, logger)

        # Test old-style methods
        md_file = tmp_path / "report.md"
        html_file = tmp_path / "report.html"

        renderer.render_markdown_report(SAMPLE_REPORT_DATA, md_file)
        renderer.render_html_report(SAMPLE_REPORT_DATA, html_file)

        # Both files should exist
        assert md_file.exists()
        assert html_file.exists()

        # Check content
        assert len(md_file.read_text()) > 0
        assert len(html_file.read_text()) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
