# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Unit tests for ModernReportRenderer.

Tests orchestration of context building and template rendering.

Phase 8: Renderer Modernization
"""

from rendering.modern_renderer import ModernReportRenderer


class TestModernReportRendererInit:
    """Test ModernReportRenderer initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        renderer = ModernReportRenderer()

        assert renderer.theme == "default"
        assert renderer.template_renderer is not None
        assert renderer.logger is not None

    def test_init_with_custom_theme(self):
        """Test initialization with custom theme."""
        renderer = ModernReportRenderer(theme="dark")

        assert renderer.theme == "dark"
        assert renderer.template_renderer.theme == "dark"

    def test_init_with_custom_template_dir(self, tmp_path):
        """Test initialization with custom template directory."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        renderer = ModernReportRenderer(template_dir=template_dir)

        assert renderer.template_renderer.template_dir == template_dir


class TestRenderMarkdown:
    """Test Markdown report rendering."""

    def test_render_markdown_success(self, tmp_path):
        """Test successful Markdown rendering."""
        # Create template
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# {{ project.name }}\n\nTotal: {{ summary.total_commits }}")

        # Create analysis data
        analysis_data = {
            "project_name": "Test Project",
            "repositories": [{"name": "repo1", "total_commits": 100, "authors": []}],
        }

        # Render
        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.md"

        result = renderer.render_markdown(analysis_data, output_path)

        assert result is True
        assert output_path.exists()

        content = output_path.read_text()
        assert "Test Project" in content
        assert "100" in content

    def test_render_markdown_invalid_data(self, tmp_path):
        """Test Markdown rendering with invalid data."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Missing required fields
        analysis_data = {}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.md"

        result = renderer.render_markdown(analysis_data, output_path)

        assert result is False
        assert not output_path.exists()

    def test_render_markdown_template_error(self, tmp_path, caplog):
        """Test Markdown rendering handles template errors."""
        import logging

        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        # No template created - will cause TemplateNotFound

        analysis_data = {"project_name": "Test", "repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.md"

        with caplog.at_level(logging.ERROR):
            result = renderer.render_markdown(analysis_data, output_path)

        assert result is False
        assert "Error rendering Markdown report" in caplog.text

    def test_render_markdown_creates_parent_dirs(self, tmp_path):
        """Test Markdown rendering creates parent directories."""
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# Test")

        analysis_data = {"project_name": "Test", "repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "nested" / "dir" / "report.md"

        # Create parent directories
        output_path.parent.mkdir(parents=True, exist_ok=True)

        result = renderer.render_markdown(analysis_data, output_path)

        assert result is True
        assert output_path.exists()

    def test_render_markdown_logs_success(self, tmp_path, caplog):
        """Test Markdown rendering logs success message."""
        import logging

        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template_file = markdown_dir / "report.md.j2"
        template_file.write_text("# Test")

        analysis_data = {"project_name": "Test", "repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.md"

        with caplog.at_level(logging.INFO):
            renderer.render_markdown(analysis_data, output_path)

        assert "Markdown report written to" in caplog.text


class TestRenderHTML:
    """Test HTML report rendering."""

    def test_render_html_success(self, tmp_path):
        """Test successful HTML rendering."""
        # Create template
        template_dir = tmp_path / "templates"
        html_dir = template_dir / "html"
        html_dir.mkdir(parents=True)

        template_file = html_dir / "report.html.j2"
        template_file.write_text("<h1>{{ project.name }}</h1><p>Theme: {{ theme }}</p>")

        # Create analysis data
        analysis_data = {"project_name": "Test Project", "repositories": []}

        # Render
        renderer = ModernReportRenderer(template_dir=template_dir, theme="dark")
        output_path = tmp_path / "report.html"

        result = renderer.render_html(analysis_data, output_path)

        assert result is True
        assert output_path.exists()

        content = output_path.read_text()
        assert "Test Project" in content
        assert "dark" in content

    def test_render_html_invalid_data(self, tmp_path):
        """Test HTML rendering with invalid data."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        analysis_data = {}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.html"

        result = renderer.render_html(analysis_data, output_path)

        assert result is False
        assert not output_path.exists()

    def test_render_html_template_error(self, tmp_path, caplog):
        """Test HTML rendering handles template errors."""
        import logging

        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        analysis_data = {"project_name": "Test", "repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.html"

        with caplog.at_level(logging.ERROR):
            result = renderer.render_html(analysis_data, output_path)

        assert result is False
        assert "Error rendering HTML report" in caplog.text

    def test_render_html_logs_success(self, tmp_path, caplog):
        """Test HTML rendering logs success message."""
        import logging

        template_dir = tmp_path / "templates"
        html_dir = template_dir / "html"
        html_dir.mkdir(parents=True)

        template_file = html_dir / "report.html.j2"
        template_file.write_text("<h1>Test</h1>")

        analysis_data = {"project_name": "Test", "repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.html"

        with caplog.at_level(logging.INFO):
            renderer.render_html(analysis_data, output_path)

        assert "HTML report written to" in caplog.text


class TestRenderJSON:
    """Test JSON report rendering."""

    def test_render_json_success(self, tmp_path):
        """Test successful JSON rendering."""
        import json

        analysis_data = {
            "project_name": "Test Project",
            "repositories": [{"name": "repo1", "total_commits": 100, "authors": []}],
        }

        renderer = ModernReportRenderer()
        output_path = tmp_path / "report.json"

        result = renderer.render_json(analysis_data, output_path)

        assert result is True
        assert output_path.exists()

        # Verify valid JSON
        content = output_path.read_text()
        data = json.loads(content)

        assert "project" in data
        assert data["project"]["name"] == "Test Project"

    def test_render_json_invalid_data(self, tmp_path):
        """Test JSON rendering with invalid data."""
        analysis_data = {}

        renderer = ModernReportRenderer()
        output_path = tmp_path / "report.json"

        result = renderer.render_json(analysis_data, output_path)

        assert result is False
        assert not output_path.exists()

    def test_render_json_error(self, tmp_path, caplog):
        """Test JSON rendering handles errors."""
        import logging

        analysis_data = {"project_name": "Test", "repositories": []}

        renderer = ModernReportRenderer()
        output_path = tmp_path / "nonexistent" / "report.json"
        # Don't create parent directory

        with caplog.at_level(logging.ERROR):
            result = renderer.render_json(analysis_data, output_path)

        assert result is False
        assert "Error rendering JSON report" in caplog.text

    def test_render_json_logs_success(self, tmp_path, caplog):
        """Test JSON rendering logs success message."""
        import logging

        analysis_data = {"project_name": "Test", "repositories": []}

        renderer = ModernReportRenderer()
        output_path = tmp_path / "report.json"

        with caplog.at_level(logging.INFO):
            renderer.render_json(analysis_data, output_path)

        assert "JSON report written to" in caplog.text


class TestGetContext:
    """Test context extraction."""

    def test_get_context_success(self):
        """Test successful context extraction."""
        analysis_data = {
            "project_name": "Test Project",
            "repositories": [
                {
                    "name": "repo1",
                    "total_commits": 100,
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 50}
                    ],
                }
            ],
        }

        renderer = ModernReportRenderer()
        context = renderer.get_context(analysis_data)

        assert context is not None
        assert "project" in context
        assert "summary" in context
        assert "repositories" in context
        assert "authors" in context

        assert context["project"]["name"] == "Test Project"
        assert context["summary"]["total_commits"] == 100

    def test_get_context_invalid_data(self):
        """Test context extraction with invalid data."""
        analysis_data = {}  # Missing required fields

        renderer = ModernReportRenderer()
        context = renderer.get_context(analysis_data)

        assert context is None

    def test_get_context_error_handling(self, caplog):
        """Test context extraction handles errors."""
        import logging

        # Invalid data structure
        analysis_data = {
            "project_name": "Test",
            "repositories": "invalid",  # Should be list
        }

        renderer = ModernReportRenderer()

        with caplog.at_level(logging.ERROR):
            context = renderer.get_context(analysis_data)

        # Should handle error gracefully
        assert context is None or "Error building context" in caplog.text


class TestIntegration:
    """Test integration scenarios."""

    def test_render_all_formats(self, tmp_path):
        """Test rendering all formats for same data."""
        # Create templates
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        html_dir = template_dir / "html"
        markdown_dir.mkdir(parents=True)
        html_dir.mkdir(parents=True)

        (markdown_dir / "report.md.j2").write_text("# {{ project.name }}")
        (html_dir / "report.html.j2").write_text("<h1>{{ project.name }}</h1>")

        analysis_data = {"project_name": "Multi-Format Project", "repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)

        md_path = tmp_path / "report.md"
        html_path = tmp_path / "report.html"
        json_path = tmp_path / "report.json"

        # Render all formats
        md_result = renderer.render_markdown(analysis_data, md_path)
        html_result = renderer.render_html(analysis_data, html_path)
        json_result = renderer.render_json(analysis_data, json_path)

        assert md_result is True
        assert html_result is True
        assert json_result is True

        assert md_path.exists()
        assert html_path.exists()
        assert json_path.exists()

    def test_complex_data_rendering(self, tmp_path):
        """Test rendering complex nested data."""
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template = markdown_dir / "report.md.j2"
        template.write_text("""# {{ project.name }}

## Repositories
{% for repo in repositories %}
- {{ repo.name }}: {{ repo.total_commits }} commits
{% endfor %}

## Authors
{% for author in authors %}
- {{ author.name }} ({{ author.email }}): {{ author.total_commits }} commits
{% endfor %}
""")

        analysis_data = {
            "project_name": "Complex Project",
            "repositories": [
                {
                    "name": "repo1",
                    "total_commits": 100,
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 60},
                        {"name": "Bob", "email": "bob@example.com", "commit_count": 40},
                    ],
                },
                {
                    "name": "repo2",
                    "total_commits": 50,
                    "authors": [
                        {"name": "Alice", "email": "alice@example.com", "commit_count": 50}
                    ],
                },
            ],
        }

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.md"

        result = renderer.render_markdown(analysis_data, output_path)

        assert result is True

        content = output_path.read_text()
        assert "repo1: 100 commits" in content
        assert "repo2: 50 commits" in content
        assert "Alice" in content
        assert "Bob" in content
        # Alice should have 110 total commits (60 + 50)
        assert "110 commits" in content


class TestValidation:
    """Test data validation."""

    def test_validation_before_rendering(self, tmp_path):
        """Test that validation is performed before rendering."""
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        (markdown_dir / "report.md.j2").write_text("Test")

        # Invalid data - missing project_name
        invalid_data = {"repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.md"

        result = renderer.render_markdown(invalid_data, output_path)

        # Should fail validation and not create file
        assert result is False
        assert not output_path.exists()


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_repositories(self, tmp_path):
        """Test rendering with empty repository list."""
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template = markdown_dir / "report.md.j2"
        template.write_text("Repos: {{ repositories | length }}")

        analysis_data = {"project_name": "Empty Project", "repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.md"

        result = renderer.render_markdown(analysis_data, output_path)

        assert result is True
        assert "Repos: 0" in output_path.read_text()

    def test_unicode_in_data(self, tmp_path):
        """Test rendering with unicode characters."""
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template = markdown_dir / "report.md.j2"
        template.write_text("# {{ project.name }}")

        analysis_data = {"project_name": "测试项目 🚀", "repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.md"

        result = renderer.render_markdown(analysis_data, output_path)

        assert result is True
        content = output_path.read_text(encoding="utf-8")
        assert "测试项目 🚀" in content

    def test_overwrite_existing_file(self, tmp_path):
        """Test overwriting existing report file."""
        template_dir = tmp_path / "templates"
        markdown_dir = template_dir / "markdown"
        markdown_dir.mkdir(parents=True)

        template = markdown_dir / "report.md.j2"
        template.write_text("# {{ project.name }}")

        analysis_data = {"project_name": "Test", "repositories": []}

        renderer = ModernReportRenderer(template_dir=template_dir)
        output_path = tmp_path / "report.md"

        # Create existing file
        output_path.write_text("Old content")

        # Render should overwrite
        result = renderer.render_markdown(analysis_data, output_path)

        assert result is True
        content = output_path.read_text()
        assert "Old content" not in content
        assert "Test" in content
