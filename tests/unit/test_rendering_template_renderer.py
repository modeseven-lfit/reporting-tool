# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for TemplateRenderer.

Tests Jinja2 template rendering with custom filters and multi-format support.

Phase 8: Renderer Modernization
"""

import json

import jinja2
import pytest
from jinja2 import TemplateNotFound

from rendering.template_renderer import TemplateRenderer


class TestTemplateRendererInit:
    """Test TemplateRenderer initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        renderer = TemplateRenderer()

        assert renderer.theme == "default"
        assert renderer.env is not None
        assert renderer.logger is not None

    def test_init_with_custom_theme(self):
        """Test initialization with custom theme."""
        renderer = TemplateRenderer(theme="dark")

        assert renderer.theme == "dark"

    def test_init_with_custom_template_dir(self, tmp_path):
        """Test initialization with custom template directory."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        renderer = TemplateRenderer(template_dir=template_dir)

        assert renderer.template_dir == template_dir

    def test_filters_registered(self):
        """Test that custom filters are registered."""
        renderer = TemplateRenderer()

        # Check that custom filters are in the environment
        assert "format_number" in renderer.env.filters
        assert "format_date" in renderer.env.filters
        assert "format_percentage" in renderer.env.filters
        assert "pluralize" in renderer.env.filters

    def test_jinja_env_configured(self):
        """Test that Jinja2 environment is properly configured."""
        renderer = TemplateRenderer()

        assert renderer.env.autoescape is True
        assert renderer.env.trim_blocks is True
        assert renderer.env.lstrip_blocks is True
        assert renderer.env.keep_trailing_newline is True


class TestDefaultTemplateDir:
    """Test default template directory detection."""

    def test_get_default_template_dir(self):
        """Test default template directory is calculated correctly."""
        renderer = TemplateRenderer()

        # Should be src/templates
        assert renderer.template_dir.name == "templates"
        assert renderer.template_dir.parent.name == "src"


class TestRenderMarkdown:
    """Test Markdown rendering."""

    def test_render_markdown_basic(self, tmp_path):
        """Test basic Markdown rendering."""
        # Create template directory and file
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# {{ title }}\n\n{{ content }}")

        renderer = TemplateRenderer(template_dir=template_dir)

        context = {"title": "Test Report", "content": "This is a test."}
        result = renderer.render_markdown(context)

        assert "# Test Report" in result
        assert "This is a test." in result

    def test_render_markdown_with_filters(self, tmp_path):
        """Test Markdown rendering with custom filters."""
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("{{ count | format_number }} item{{ count | pluralize }}")

        renderer = TemplateRenderer(template_dir=template_dir)

        context = {"count": 1500}
        result = renderer.render_markdown(context)

        assert "1.5K items" in result

    def test_render_markdown_template_not_found(self, tmp_path):
        """Test Markdown rendering with missing template."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        renderer = TemplateRenderer(template_dir=template_dir)

        with pytest.raises(TemplateNotFound):
            renderer.render_markdown({})

    def test_render_markdown_preserves_whitespace(self, tmp_path):
        """Test Markdown rendering preserves trailing newline."""
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("Content\n")

        renderer = TemplateRenderer(template_dir=template_dir)
        result = renderer.render_markdown({})

        assert result.endswith("\n")


class TestRenderHTML:
    """Test HTML rendering."""

    def test_render_html_basic(self, tmp_path):
        """Test basic HTML rendering."""
        template_dir = tmp_path / "templates"
        html_dir = template_dir / "html"
        html_dir.mkdir(parents=True)

        template_file = html_dir / "report.html.j2"
        template_file.write_text("<h1>{{ title }}</h1>")

        renderer = TemplateRenderer(template_dir=template_dir)

        context = {"title": "Test Report"}
        result = renderer.render_html(context)

        assert "<h1>Test Report</h1>" in result

    def test_render_html_includes_theme(self, tmp_path):
        """Test HTML rendering includes theme in context."""
        template_dir = tmp_path / "templates"
        html_dir = template_dir / "html"
        html_dir.mkdir(parents=True)

        template_file = html_dir / "report.html.j2"
        template_file.write_text('<body class="theme-{{ theme }}">')

        renderer = TemplateRenderer(template_dir=template_dir, theme="dark")

        result = renderer.render_html({})

        assert "theme-dark" in result

    def test_render_html_autoescape(self, tmp_path):
        """Test HTML rendering autoescapes dangerous content."""
        template_dir = tmp_path / "templates"
        html_dir = template_dir / "html"
        html_dir.mkdir(parents=True)

        template_file = html_dir / "report.html.j2"
        template_file.write_text("{{ content }}")

        renderer = TemplateRenderer(template_dir=template_dir)

        context = {"content": '<script>alert("XSS")</script>'}
        result = renderer.render_html(context)

        # Should be escaped
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_render_html_template_not_found(self, tmp_path):
        """Test HTML rendering with missing template."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        renderer = TemplateRenderer(template_dir=template_dir)

        with pytest.raises(TemplateNotFound):
            renderer.render_html({})


class TestRenderJSON:
    """Test JSON rendering."""

    def test_render_json_basic(self):
        """Test basic JSON rendering."""
        renderer = TemplateRenderer()

        context = {"title": "Test", "count": 42}
        result = renderer.render_json(context)

        # Parse to verify valid JSON
        data = json.loads(result)
        assert data["title"] == "Test"
        assert data["count"] == 42

    def test_render_json_formatted(self):
        """Test JSON rendering is formatted with indentation."""
        renderer = TemplateRenderer()

        context = {"nested": {"key": "value"}}
        result = renderer.render_json(context)

        assert "  " in result  # Has indentation
        assert "\n" in result  # Has newlines

    def test_render_json_sorted_keys(self):
        """Test JSON rendering sorts keys."""
        renderer = TemplateRenderer()

        context = {"zebra": 1, "alpha": 2, "beta": 3}
        result = renderer.render_json(context)

        # Keys should be in alphabetical order
        assert result.index("alpha") < result.index("beta")
        assert result.index("beta") < result.index("zebra")

    def test_render_json_handles_non_serializable(self):
        """Test JSON rendering handles non-serializable objects."""
        from datetime import datetime

        renderer = TemplateRenderer()

        # datetime is not JSON serializable by default
        # but render_json uses default=str
        context = {"timestamp": datetime(2025, 1, 16, 10, 30, 0)}
        result = renderer.render_json(context)

        data = json.loads(result)
        assert "2025-01-16" in data["timestamp"]

    def test_render_json_empty_context(self):
        """Test JSON rendering with empty context."""
        renderer = TemplateRenderer()

        result = renderer.render_json({})

        assert result == "{}"


class TestRenderTemplate:
    """Test arbitrary template rendering."""

    def test_render_template_custom(self, tmp_path):
        """Test rendering custom template by name."""
        template_dir = tmp_path / "templates"
        custom_dir = template_dir / "custom"
        custom_dir.mkdir(parents=True)

        template_file = custom_dir / "test.txt.j2"
        template_file.write_text("Hello, {{ name }}!")

        renderer = TemplateRenderer(template_dir=template_dir)

        result = renderer.render_template("custom/test.txt.j2", {"name": "World"})

        assert result == "Hello, World!"

    def test_render_template_not_found(self, tmp_path):
        """Test rendering non-existent template."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        renderer = TemplateRenderer(template_dir=template_dir)

        with pytest.raises(TemplateNotFound):
            renderer.render_template("nonexistent.j2", {})

    def test_render_template_logs_error(self, tmp_path, caplog):
        """Test template rendering logs errors."""
        import logging

        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        renderer = TemplateRenderer(template_dir=template_dir)

        with caplog.at_level(logging.ERROR), pytest.raises(TemplateNotFound):
            renderer.render_template("missing.j2", {})

        assert "Template not found" in caplog.text


class TestListTemplates:
    """Test template listing."""

    def test_list_templates(self, tmp_path):
        """Test listing available templates."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create some templates
        (template_dir / "test1.j2").write_text("test")
        (template_dir / "test2.j2").write_text("test")
        subdir = template_dir / "sub"
        subdir.mkdir()
        (subdir / "test3.j2").write_text("test")

        renderer = TemplateRenderer(template_dir=template_dir)
        templates = renderer.list_templates()

        assert "test1.j2" in templates
        assert "test2.j2" in templates
        assert "sub/test3.j2" in templates or "sub\\test3.j2" in templates

    def test_list_templates_empty(self, tmp_path):
        """Test listing templates in empty directory."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        renderer = TemplateRenderer(template_dir=template_dir)
        templates = renderer.list_templates()

        assert templates == []


class TestCustomFilters:
    """Test custom Jinja2 filters."""

    def test_format_number_filter(self, tmp_path):
        """Test format_number filter in template."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("{{ value | format_number }}")

        renderer = TemplateRenderer(template_dir=template_dir)
        result = renderer.render_template("test.j2", {"value": 1234})

        assert "1.2K" in result

    def test_format_date_filter(self, tmp_path):
        """Test format_date filter in template."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("{{ date | format_date }}")

        renderer = TemplateRenderer(template_dir=template_dir)
        result = renderer.render_template("test.j2", {"date": "2025-01-16"})

        assert "2025-01-16" in result

    def test_format_percentage_filter(self, tmp_path):
        """Test format_percentage filter in template."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("{{ value | format_percentage }}")

        renderer = TemplateRenderer(template_dir=template_dir)
        result = renderer.render_template("test.j2", {"value": 45.678})

        assert "45.7%" in result

    def test_pluralize_filter(self, tmp_path):
        """Test pluralize filter in template."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("{{ count }} item{{ count | pluralize }}")

        renderer = TemplateRenderer(template_dir=template_dir)

        result1 = renderer.render_template("test.j2", {"count": 1})
        assert "1 item" in result1

        result2 = renderer.render_template("test.j2", {"count": 5})
        assert "5 items" in result2


class TestTemplateBlockHandling:
    """Test Jinja2 block features."""

    def test_trim_blocks(self, tmp_path):
        """Test trim_blocks configuration."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("Line 1\n{% if true %}\nLine 2\n{% endif %}\nLine 3")

        renderer = TemplateRenderer(template_dir=template_dir)
        result = renderer.render_template("test.j2", {})

        # trim_blocks should remove newline after {% if %}
        assert "Line 1\nLine 2\nLine 3" in result

    def test_lstrip_blocks(self, tmp_path):
        """Test lstrip_blocks configuration."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("  {% if true %}Content{% endif %}")

        renderer = TemplateRenderer(template_dir=template_dir)
        result = renderer.render_template("test.j2", {})

        # lstrip_blocks should remove leading whitespace before block
        assert result.strip() == "Content"


class TestErrorHandling:
    """Test error handling in rendering."""

    def test_render_markdown_logs_template_not_found(self, tmp_path, caplog):
        """Test render_markdown logs TemplateNotFound error."""
        import logging

        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        renderer = TemplateRenderer(template_dir=template_dir)

        with caplog.at_level(logging.ERROR), pytest.raises(TemplateNotFound):
            renderer.render_markdown({})

        assert "Template not found" in caplog.text

    def test_render_html_logs_template_not_found(self, tmp_path, caplog):
        """Test render_html logs TemplateNotFound error."""
        import logging

        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        renderer = TemplateRenderer(template_dir=template_dir)

        with caplog.at_level(logging.ERROR), pytest.raises(TemplateNotFound):
            renderer.render_html({})

        assert "Template not found" in caplog.text

    def test_render_json_logs_error(self, caplog):
        """Test render_json logs serialization errors."""
        import logging

        renderer = TemplateRenderer()

        # Create a non-serializable object without str conversion
        class NonSerializable:
            def __str__(self):
                raise ValueError("Cannot convert to string")

        with caplog.at_level(logging.ERROR), pytest.raises((TypeError, ValueError)):
            # This should raise because even default=str will fail
            renderer.render_json({"obj": NonSerializable()})

    def test_render_template_with_syntax_error(self, tmp_path):
        """Test rendering template with syntax error."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("{% if unclosed %}")

        renderer = TemplateRenderer(template_dir=template_dir)

        with pytest.raises((jinja2.TemplateSyntaxError, jinja2.TemplateError)):
            renderer.render_template("test.j2", {})


class TestComplexTemplates:
    """Test complex template scenarios."""

    def test_template_with_loops(self, tmp_path):
        """Test template with for loops."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("{% for item in items %}{{ item }}\n{% endfor %}")

        renderer = TemplateRenderer(template_dir=template_dir)
        result = renderer.render_template("test.j2", {"items": ["a", "b", "c"]})

        assert "a\n" in result
        assert "b\n" in result
        assert "c\n" in result

    def test_template_with_conditionals(self, tmp_path):
        """Test template with if/else."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("{% if show %}visible{% else %}hidden{% endif %}")

        renderer = TemplateRenderer(template_dir=template_dir)

        result1 = renderer.render_template("test.j2", {"show": True})
        assert "visible" in result1

        result2 = renderer.render_template("test.j2", {"show": False})
        assert "hidden" in result2

    def test_template_with_nested_data(self, tmp_path):
        """Test template with nested data structures."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        template_file = template_dir / "test.j2"
        template_file.write_text("{{ user.profile.name }}")

        renderer = TemplateRenderer(template_dir=template_dir)
        context = {"user": {"profile": {"name": "Alice"}}}
        result = renderer.render_template("test.j2", context)

        assert "Alice" in result


class TestThemeSupport:
    """Test theme handling."""

    def test_different_themes(self, tmp_path):
        """Test rendering with different themes."""
        template_dir = tmp_path / "templates"
        html_dir = template_dir / "html"
        html_dir.mkdir(parents=True)

        template_file = html_dir / "report.html.j2"
        template_file.write_text('<div class="{{ theme }}"></div>')

        renderer1 = TemplateRenderer(template_dir=template_dir, theme="light")
        result1 = renderer1.render_html({})
        assert "light" in result1

        renderer2 = TemplateRenderer(template_dir=template_dir, theme="dark")
        result2 = renderer2.render_html({})
        assert "dark" in result2

    def test_theme_not_in_markdown_context(self, tmp_path):
        """Test theme is not added to markdown context."""
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        # This template will fail if theme is in context but undefined
        template_file = markdown_dir / "report.md.j2"
        template_file.write_text(
            "{% if theme is defined %}{{ theme }}{% else %}no theme{% endif %}"
        )

        renderer = TemplateRenderer(template_dir=template_dir, theme="test")
        result = renderer.render_markdown({})

        # Theme should not be in markdown context
        assert "no theme" in result
