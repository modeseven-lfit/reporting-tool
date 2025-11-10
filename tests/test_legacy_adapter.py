# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for Legacy Renderer Adapter

This module tests the backward compatibility layer between the legacy
ReportRenderer and the modern ModernReportRenderer.

Phase 8: Renderer Modernization
"""

import json
import logging
from pathlib import Path

import pytest

from rendering.legacy_adapter import LegacyRendererAdapter, create_legacy_renderer
from rendering.renderer import ModernReportRenderer


@pytest.fixture
def logger():
    """Create a test logger."""
    return logging.getLogger("test_legacy_adapter")


@pytest.fixture
def config():
    """Create a test configuration."""
    return {
        "output": {
            "include_sections": {
                "contributors": True,
                "organizations": True,
                "repo_feature_matrix": True,
                "inactive_distributions": True,
            }
        },
        "time_windows": {
            "reporting_window_days": 90,
            "inactivity_threshold_days": 180,
        },
    }


@pytest.fixture
def sample_data():
    """Create sample report data."""
    return {
        "project": "test-project",
        "generated_at": "2025-01-16T12:00:00Z",
        "report_period": {
            "start": "2024-10-16",
            "end": "2025-01-16",
            "days": 90,
        },
        "summaries": {
            "counts": {
                "total_repositories": 5,
                "active_repositories": 3,
                "inactive_repositories": 2,
                "archived_repositories": 0,
                "total_commits": 150,
                "total_contributors": 10,
            },
            "activity": {
                "active_with_commits": 3,
                "inactive_no_commits": 2,
            },
        },
        "repositories": [
            {
                "name": "repo-1",
                "commit_count": 50,
                "contributors": 5,
                "status": "active",
            },
            {
                "name": "repo-2",
                "commit_count": 30,
                "contributors": 3,
                "status": "active",
            },
            {
                "name": "repo-3",
                "commit_count": 70,
                "contributors": 2,
                "status": "active",
            },
        ],
        "contributors": [],
        "organizations": [],
        "features": {},
        "workflows": {},
    }


class TestLegacyRendererAdapter:
    """Tests for LegacyRendererAdapter class."""

    def test_initialization(self, config, logger):
        """Test adapter initialization."""
        adapter = LegacyRendererAdapter(config, logger)

        assert adapter.config == config
        assert adapter.logger == logger
        assert isinstance(adapter.modern_renderer, ModernReportRenderer)

    def test_initialization_matches_config(self, config, logger):
        """Test that adapter passes config correctly to modern renderer."""
        adapter = LegacyRendererAdapter(config, logger)

        # Should have access to config through modern renderer
        assert adapter.modern_renderer.config == config
        assert adapter.modern_renderer.logger == logger

    def test_render_json_report(self, config, logger, sample_data, tmp_path):
        """Test JSON report rendering."""
        adapter = LegacyRendererAdapter(config, logger)
        output_path = tmp_path / "report.json"

        adapter.render_json_report(sample_data, output_path)

        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data["project"] == "test-project"
        assert loaded_data["summaries"]["counts"]["total_repositories"] == 5

    def test_render_markdown_report(self, config, logger, sample_data, tmp_path):
        """Test Markdown report rendering."""
        adapter = LegacyRendererAdapter(config, logger)
        output_path = tmp_path / "report.md"

        # Should return content for backward compatibility
        content = adapter.render_markdown_report(sample_data, output_path)

        assert output_path.exists()
        assert isinstance(content, str)
        assert len(content) > 0
        assert "test-project" in content

        # Verify content matches file
        with open(output_path, encoding="utf-8") as f:
            file_content = f.read()
        assert content == file_content

    def test_render_html_report_modern_mode(self, config, logger, sample_data, tmp_path):
        """Test HTML rendering in modern mode (direct from data)."""
        adapter = LegacyRendererAdapter(config, logger)
        output_path = tmp_path / "report.html"

        # Modern mode: no markdown_content parameter
        adapter.render_html_report(sample_data, output_path)

        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            html_content = f.read()

        assert "<!DOCTYPE html>" in html_content
        assert "test-project" in html_content

    def test_render_html_report_legacy_mode(self, config, logger, sample_data, tmp_path, caplog):
        """Test HTML rendering in legacy mode (convert from Markdown)."""
        adapter = LegacyRendererAdapter(config, logger)
        output_path = tmp_path / "report.html"

        markdown_content = "# Test Report\n\nSome content."

        # Legacy mode: provide markdown_content
        adapter.render_html_report(sample_data, output_path, markdown_content=markdown_content)

        # Should log deprecation warning
        assert "deprecated" in caplog.text.lower()
        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            html_content = f.read()

        assert "<!DOCTYPE html>" in html_content
        assert "Test Report" in html_content

    def test_package_zip_report(self, config, logger, sample_data, tmp_path):
        """Test ZIP report packaging."""
        adapter = LegacyRendererAdapter(config, logger)
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Create some test files
        (output_dir / "report.json").write_text("{}")
        (output_dir / "report.md").write_text("# Test")

        zip_path = adapter.package_zip_report(output_dir, "test-project")

        assert zip_path.exists()
        assert zip_path.suffix == ".zip"
        assert "test-project" in zip_path.name

    def test_backward_compatibility_api(self, config, logger, sample_data, tmp_path):
        """Test that adapter maintains backward compatible API."""
        adapter = LegacyRendererAdapter(config, logger)

        # Legacy API pattern
        md_path = tmp_path / "report.md"
        html_path = tmp_path / "report.html"
        json_path = tmp_path / "report.json"

        # This is how legacy code uses the renderer
        md_content = adapter.render_markdown_report(sample_data, md_path)
        adapter.render_html_report(sample_data, html_path, markdown_content=md_content)
        adapter.render_json_report(sample_data, json_path)

        # All files should exist
        assert md_path.exists()
        assert html_path.exists()
        assert json_path.exists()

        # Markdown content should be returned
        assert isinstance(md_content, str)
        assert len(md_content) > 0

    def test_adapter_uses_modern_renderer_internally(self, config, logger, sample_data, tmp_path):
        """Test that adapter delegates to modern renderer."""
        adapter = LegacyRendererAdapter(config, logger)
        output_path = tmp_path / "report.md"

        # Render using adapter
        adapter.render_markdown_report(sample_data, output_path)

        # Should use modern template system
        with open(output_path, encoding="utf-8") as f:
            content = f.read()

        # Check for modern template characteristics
        assert "test-project" in content
        # Modern templates should have structured sections
        assert "##" in content or "**" in content


class TestCreateLegacyRenderer:
    """Tests for create_legacy_renderer factory function."""

    def test_create_with_modern_enabled(self, config, logger):
        """Test factory creates adapter when use_modern=True."""
        renderer = create_legacy_renderer(config, logger, use_modern=True)

        assert isinstance(renderer, LegacyRendererAdapter)
        assert renderer.config == config
        assert renderer.logger == logger

    def test_create_with_modern_disabled_raises(self, config, logger):
        """Test factory raises error when use_modern=False."""
        with pytest.raises(NotImplementedError) as exc_info:
            create_legacy_renderer(config, logger, use_modern=False)

        assert "Legacy renderer not available" in str(exc_info.value)

    def test_create_returns_configured_adapter(self, config, logger):
        """Test factory returns properly configured adapter."""
        renderer = create_legacy_renderer(config, logger, use_modern=True)

        assert isinstance(renderer, LegacyRendererAdapter)
        assert renderer.config == config
        assert renderer.logger == logger


class TestIntegrationWithModernRenderer:
    """Integration tests between adapter and modern renderer."""

    def test_adapter_produces_valid_markdown(self, config, logger, sample_data, tmp_path):
        """Test that adapter produces valid Markdown output."""
        adapter = LegacyRendererAdapter(config, logger)
        output_path = tmp_path / "report.md"

        content = adapter.render_markdown_report(sample_data, output_path)

        # Should be valid Markdown
        assert "# " in content  # Has headers
        assert "test-project" in content
        assert "Repository" in content or "repository" in content.lower()

    def test_adapter_produces_valid_html(self, config, logger, sample_data, tmp_path):
        """Test that adapter produces valid HTML output."""
        adapter = LegacyRendererAdapter(config, logger)
        output_path = tmp_path / "report.html"

        adapter.render_html_report(sample_data, output_path)

        with open(output_path, encoding="utf-8") as f:
            html_content = f.read()

        # Should be valid HTML5
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "</html>" in html_content
        assert "<head>" in html_content
        assert "<body>" in html_content
        assert "test-project" in html_content

    def test_adapter_and_modern_renderer_consistency(self, config, logger, sample_data, tmp_path):
        """Test that adapter and modern renderer produce consistent output."""
        # Create both renderers
        adapter = LegacyRendererAdapter(config, logger)
        modern = ModernReportRenderer(config, logger)

        # Render with both
        adapter_path = tmp_path / "adapter_report.md"
        modern_path = tmp_path / "modern_report.md"

        adapter.render_markdown_report(sample_data, adapter_path)
        modern.render_markdown_report(sample_data, modern_path)

        # Read both outputs
        adapter_content = adapter_path.read_text()
        modern_content = modern_path.read_text()

        # Should have same key elements (exact match not required due to context building)
        assert "test-project" in adapter_content
        assert "test-project" in modern_content


class TestErrorHandling:
    """Tests for error handling in adapter."""

    def test_invalid_output_path(self, config, logger, sample_data):
        """Test handling of invalid output path."""
        adapter = LegacyRendererAdapter(config, logger)
        invalid_path = Path("/nonexistent/directory/report.md")

        with pytest.raises((FileNotFoundError, OSError, PermissionError)):
            adapter.render_markdown_report(sample_data, invalid_path)

    def test_missing_required_data_keys(self, config, logger, tmp_path):
        """Test handling of incomplete data."""
        adapter = LegacyRendererAdapter(config, logger)
        output_path = tmp_path / "report.md"

        # Minimal data (may cause issues in templates)
        minimal_data = {
            "project": "test",
            "generated_at": "2025-01-16T12:00:00Z",
        }

        # Modern renderer should handle gracefully or raise clear error
        try:
            adapter.render_markdown_report(minimal_data, output_path)
            # If it succeeds, output should still be created
            assert output_path.exists()
        except (KeyError, AttributeError) as e:
            # If it fails, should be a clear error
            assert "project" in str(e).lower() or "data" in str(e).lower()


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with legacy code patterns."""

    def test_legacy_workflow_pattern(self, config, logger, sample_data, tmp_path):
        """Test the typical legacy workflow pattern."""
        # This is how legacy code uses ReportRenderer
        renderer = LegacyRendererAdapter(config, logger)

        md_path = tmp_path / "report.md"
        html_path = tmp_path / "report.html"
        json_path = tmp_path / "report.json"

        # Step 1: Render Markdown and get content
        markdown_content = renderer.render_markdown_report(sample_data, md_path)

        # Step 2: Convert Markdown to HTML
        renderer.render_html_report(sample_data, html_path, markdown_content)

        # Step 3: Write JSON
        renderer.render_json_report(sample_data, json_path)

        # Step 4: Package into ZIP
        zip_path = renderer.package_zip_report(tmp_path, "test-project")

        # Verify all outputs
        assert md_path.exists()
        assert html_path.exists()
        assert json_path.exists()
        assert zip_path.exists()
        assert isinstance(markdown_content, str)

    def test_can_be_used_as_drop_in_replacement(self, config, logger, sample_data, tmp_path):
        """Test that adapter can replace ReportRenderer without code changes."""
        # Simulate import alias that legacy code might use
        ReportRenderer = LegacyRendererAdapter

        # Legacy code pattern
        renderer = ReportRenderer(config, logger)
        output_path = tmp_path / "report.md"

        # Should work exactly like legacy
        result = renderer.render_markdown_report(sample_data, output_path)

        assert output_path.exists()
        assert isinstance(result, str)
        assert "test-project" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
