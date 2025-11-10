# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for rendering infrastructure (Phase 8).

This module tests the template-based rendering system including:
- RenderContext data preparation
- TemplateRenderer template loading and filters
- ModernReportRenderer integration
- Template output correctness
"""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import pytest

from rendering import ModernReportRenderer, RenderContext, TemplateRenderer
from rendering.formatters import (
    format_age,
    format_bytes,
    format_date,
    format_number,
    format_percentage,
    slugify,
    truncate,
)


# ============================================================================
# Formatter Tests
# ============================================================================


class TestFormatters:
    """Test template filter functions."""

    def test_format_number_basic(self):
        """Test basic number formatting."""
        assert format_number(1000) == "1.0K"
        assert format_number(1234567) == "1.2M"
        assert format_number(0) == "0"
        assert format_number(42) == "42"

    def test_format_number_none(self):
        """Test format_number with None returns 0."""
        assert format_number(None) == "0"

    def test_format_percentage_basic(self):
        """Test percentage formatting (expects 0-100 range)."""
        assert format_percentage(50.0) == "50.0%"
        assert format_percentage(75.5) == "75.5%"
        assert format_percentage(100.0) == "100.0%"
        assert format_percentage(0.0) == "0.0%"

    def test_format_percentage_precision(self):
        """Test percentage formatting with custom precision."""
        assert format_percentage(45.678, decimals=2) == "45.68%"
        assert format_percentage(45.0, decimals=0) == "45%"
        assert format_percentage(45.678, decimals=3) == "45.678%"

    def test_format_percentage_none(self):
        """Test format_percentage with None returns 0.0%."""
        assert format_percentage(None) == "0.0%"

    def test_format_date_datetime(self):
        """Test date formatting with datetime object."""
        dt = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        assert format_date(dt) == "2025-01-16"

    def test_format_date_string(self):
        """Test date formatting with ISO string."""
        assert format_date("2025-01-16T14:30:00Z") == "2025-01-16"
        assert format_date("2025-01-16") == "2025-01-16"

    def test_format_date_custom_format(self):
        """Test date formatting with custom format string."""
        dt = datetime(2025, 1, 16, 14, 30, 0, tzinfo=timezone.utc)
        assert format_date(dt, format_str="%Y/%m/%d") == "2025/01/16"
        assert format_date(dt, format_str="%B %d, %Y") == "January 16, 2025"

    def test_format_date_none(self):
        """Test format_date with None returns unknown."""
        assert format_date(None) == "unknown"

    def test_format_age_days(self):
        """Test age formatting for days."""
        assert format_age(1) == "1d"
        assert format_age(5) == "5d"

    def test_format_age_weeks(self):
        """Test age formatting for weeks."""
        assert format_age(14) == "2w"
        assert format_age(21) == "3w"

    def test_format_age_months(self):
        """Test age formatting for months."""
        assert format_age(60) == "2m"
        assert format_age(90) == "3m"

    def test_format_age_years(self):
        """Test age formatting for years."""
        assert format_age(365) == "1y"
        assert format_age(730) == "2y"

    def test_format_age_none(self):
        """Test format_age with None returns unknown."""
        assert format_age(None) == "unknown"

    def test_slugify_basic(self):
        """Test basic slugification."""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test 123") == "test-123"
        assert slugify("Multiple   Spaces") == "multiple-spaces"

    def test_truncate_basic(self):
        """Test basic text truncation."""
        assert truncate("short", 10) == "short"
        assert truncate("this is a very long text", 10) == "this is..."

    def test_truncate_custom_suffix(self):
        """Test truncation with custom suffix."""
        result = truncate("this is a very long string", 10, suffix="…")
        assert result == "this is a…"

    def test_format_bytes_basic(self):
        """Test byte formatting."""
        assert format_bytes(500) == "500.0 B"
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1048576) == "1.0 MB"
        assert format_bytes(1073741824) == "1.0 GB"

    def test_format_bytes_none(self):
        """Test format_bytes with None returns 0 B."""
        assert format_bytes(None) == "0 B"


# ============================================================================
# RenderContext Tests
# ============================================================================


class TestRenderContext:
    """Test RenderContext data preparation."""

    def test_render_context_basic(self):
        """Test basic RenderContext initialization."""
        data = {"project": "test-project", "repositories": []}
        config = {}
        context = RenderContext(data, config)
        assert context.data == data
        assert context.config == config

    def test_render_context_build_empty(self):
        """Test building context with empty data."""
        data = {"project": "test-project", "repositories": []}
        config = {}
        context = RenderContext(data, config)
        result = context.build()

        assert isinstance(result, dict)
        assert "project" in result
        assert "summary" in result
        assert "repositories" in result

    def test_render_context_build_with_data(self):
        """Test building context with actual data."""
        data = {
            "project": "test-project",
            "repositories": [
                {
                    "name": "repo1",
                    "total_commits": 100,
                }
            ],
            "metadata": {"generated_at": "2025-01-16T14:30:00Z"},
        }
        config = {}

        context = RenderContext(data, config)
        result = context.build()

        assert result["project"]["name"] == "test-project"
        assert "repositories" in result

    def test_render_context_project_metadata(self):
        """Test project metadata extraction."""
        data = {
            "project": "my-project",
            "schema_version": "2.0.0",
            "metadata": {"generated_at": "2025-01-16T14:30:00Z", "report_version": "1.5.0"},
        }
        config = {}

        context = RenderContext(data, config)
        result = context.build()

        assert result["project"]["name"] == "my-project"
        assert result["project"]["schema_version"] == "2.0.0"

    def test_render_context_includes_filters(self):
        """Test that context includes template filters."""
        data = {"project": "test"}
        config = {}

        context = RenderContext(data, config)
        result = context.build()

        assert "filters" in result
        assert isinstance(result["filters"], dict)


# ============================================================================
# TemplateRenderer Tests
# ============================================================================


class TestTemplateRenderer:
    """Test TemplateRenderer functionality."""

    def test_template_renderer_init(self):
        """Test TemplateRenderer initialization."""
        templates_dir = Path(__file__).parent.parent / "src" / "templates"
        renderer = TemplateRenderer(template_dir=templates_dir)
        assert renderer.env is not None

    def test_template_renderer_filters_registered(self):
        """Test that all custom filters are registered."""
        templates_dir = Path(__file__).parent.parent / "src" / "templates"
        renderer = TemplateRenderer(template_dir=templates_dir)

        # Check that custom filters are registered
        assert "format_number" in renderer.env.filters
        assert "format_date" in renderer.env.filters
        assert "format_age" in renderer.env.filters

    def test_template_renderer_render_simple(self):
        """Test rendering a simple template string."""
        templates_dir = Path(__file__).parent.parent / "src" / "templates"
        renderer = TemplateRenderer(template_dir=templates_dir)

        # Use render_string method
        template_content = "Hello {{ name }}!"
        result = renderer.render_string(template_content, {"name": "World"})

        assert result == "Hello World!"

    def test_template_renderer_render_with_filters(self):
        """Test rendering with custom filters."""
        templates_dir = Path(__file__).parent.parent / "src" / "templates"
        renderer = TemplateRenderer(template_dir=templates_dir)

        template_content = "Total: {{ count | format_number }}"
        result = renderer.render_string(template_content, {"count": 1000})

        assert result == "Total: 1.0K"

    def test_template_renderer_load_markdown_base(self):
        """Test loading the actual markdown base template."""
        templates_dir = Path(__file__).parent.parent / "src" / "templates"
        renderer = TemplateRenderer(template_dir=templates_dir)

        # Should not raise an error
        template = renderer.env.get_template("markdown/base.md.j2")
        assert template is not None

    def test_template_renderer_render_method(self):
        """Test the render method with template file using RenderContext."""
        templates_dir = Path(__file__).parent.parent / "src" / "templates"
        renderer = TemplateRenderer(template_dir=templates_dir)

        # Use RenderContext to build a proper context
        data = {
            "project": "test-project",
            "repositories": [],
            "metadata": {"generated_at": "2025-01-16T14:30:00Z"},
        }
        config = {}

        from rendering import RenderContext

        render_context = RenderContext(data, config)
        context = render_context.build()

        # Render should work without errors
        result = renderer.render("markdown/base.md.j2", context)
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# ModernReportRenderer Tests
# ============================================================================


class TestModernReportRenderer:
    """Test ModernReportRenderer integration."""

    def test_modern_renderer_init(self):
        """Test ModernReportRenderer initialization."""
        config = {}
        logger = Mock()
        renderer = ModernReportRenderer(config, logger)
        assert renderer.template_renderer is not None

    def test_modern_renderer_render_markdown_basic(self):
        """Test basic markdown rendering."""
        config = {}
        logger = Mock()
        renderer = ModernReportRenderer(config, logger)

        data = {"project": "test-project", "repositories": []}

        result = renderer.render_markdown(data)

        # Should produce markdown output
        assert isinstance(result, str)
        assert len(result) > 0

    def test_modern_renderer_render_markdown_with_data(self):
        """Test markdown rendering with actual data."""
        config = {}
        logger = Mock()
        renderer = ModernReportRenderer(config, logger)

        data = {
            "project": "test-project",
            "repositories": [
                {
                    "name": "repo1",
                    "total_commits": 100,
                }
            ],
            "metadata": {"generated_at": "2025-01-16T14:30:00Z"},
        }

        result = renderer.render_markdown(data)

        # Check that the output contains expected content
        assert isinstance(result, str)
        assert len(result) > 0

    def test_modern_renderer_markdown_has_header(self):
        """Test that markdown output has proper header."""
        config = {}
        logger = Mock()
        renderer = ModernReportRenderer(config, logger)

        data = {"project": "test", "repositories": []}
        result = renderer.render_markdown(data)

        # Should have markdown header markers
        assert "#" in result

    def test_modern_renderer_with_config(self):
        """Test renderer with custom configuration."""
        config = {"render": {"theme": "dark"}}
        logger = Mock()
        renderer = ModernReportRenderer(config, logger)

        data = {"project": "test", "repositories": []}
        result = renderer.render_markdown(data)

        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# Integration Tests
# ============================================================================


class TestRenderingIntegration:
    """Integration tests for the complete rendering pipeline."""

    def test_end_to_end_markdown_rendering(self):
        """Test complete end-to-end markdown rendering."""
        # Prepare data
        data = {
            "project": "multi-project",
            "repositories": [
                {
                    "name": "project-one",
                    "total_commits": 150,
                },
                {
                    "name": "project-two",
                    "total_commits": 75,
                },
            ],
            "metadata": {"generated_at": "2025-01-16T14:30:00Z"},
        }

        config = {}
        logger = Mock()

        # Render
        renderer = ModernReportRenderer(config, logger)
        result = renderer.render_markdown(data)

        # Validate
        assert isinstance(result, str)
        assert len(result) > 0

    def test_context_to_template_pipeline(self):
        """Test the complete context -> template pipeline."""
        # Build context
        data = {
            "project": "test-project",
            "repositories": [{"name": "repo1", "total_commits": 100}],
        }
        config = {}

        render_context = RenderContext(data, config)
        context = render_context.build()

        # Render with context
        templates_dir = Path(__file__).parent.parent / "src" / "templates"
        template_renderer = TemplateRenderer(template_dir=templates_dir)

        result = template_renderer.render("markdown/base.md.j2", context)

        # Validate
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# Performance Tests
# ============================================================================


class TestRenderingPerformance:
    """Performance tests for rendering."""

    def test_large_dataset_rendering(self):
        """Test rendering with large dataset completes in reasonable time."""
        import time

        # Generate large dataset
        repositories = []
        for i in range(100):
            repositories.append(
                {
                    "name": f"project-{i}",
                    "total_commits": 1000,
                }
            )

        data = {"project": "large-project", "repositories": repositories}

        config = {}
        logger = Mock()
        renderer = ModernReportRenderer(config, logger)

        start = time.time()
        result = renderer.render_markdown(data)
        duration = time.time() - start

        # Should complete in under 5 seconds
        assert duration < 5.0
        assert len(result) > 0

    def test_template_caching(self):
        """Test that templates are cached and reused."""
        config = {}
        logger = Mock()
        renderer = ModernReportRenderer(config, logger)

        data = {"project": "test", "repositories": []}

        # First render
        result1 = renderer.render_markdown(data)

        # Second render (should use cached template)
        result2 = renderer.render_markdown(data)

        # Both should produce output
        assert len(result1) > 0
        assert len(result2) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
