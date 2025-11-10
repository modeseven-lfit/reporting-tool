# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for rendering legacy adapter module.

This module tests the LegacyRendererAdapter which provides backward
compatibility between legacy and modern rendering systems.

Coverage target: 95%+
"""

import json
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from rendering.legacy_adapter import (
    LegacyRendererAdapter,
    create_legacy_renderer,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock(spec=logging.Logger)


@pytest.fixture
def sample_config():
    """Create sample configuration."""
    return {
        "gerrit_host": "gerrit.example.com",
        "time_windows": {
            "1y": {"days": 365},
            "90d": {"days": 90},
        },
        "output_dir": "/tmp/reports",
    }


@pytest.fixture
def sample_report_data():
    """Create sample report data."""
    return {
        "metadata": {
            "generated_at": "2024-12-19T10:00:00Z",
            "gerrit_host": "gerrit.example.com",
        },
        "repositories": [
            {
                "name": "test-repo",
                "total_commits": 100,
                "activity_status": "active",
            }
        ],
        "summary": {
            "total_repositories": 1,
            "total_commits": 100,
        },
    }


@pytest.fixture
def adapter(sample_config, mock_logger):
    """Create LegacyRendererAdapter instance."""
    with patch("rendering.legacy_adapter.ModernReportRenderer"):
        return LegacyRendererAdapter(sample_config, mock_logger)


# ============================================================================
# Initialization Tests
# ============================================================================


class TestLegacyRendererAdapterInitialization:
    """Tests for LegacyRendererAdapter initialization."""

    def test_initialization_success(self, sample_config, mock_logger):
        """Test successful adapter initialization."""
        with patch("rendering.legacy_adapter.ModernReportRenderer") as MockRenderer:
            adapter = LegacyRendererAdapter(sample_config, mock_logger)

            assert adapter.config == sample_config
            assert adapter.logger == mock_logger
            assert adapter.modern_renderer is not None
            MockRenderer.assert_called_once_with(sample_config, mock_logger)

    def test_stores_config(self, sample_config, mock_logger):
        """Test that adapter stores configuration."""
        with patch("rendering.legacy_adapter.ModernReportRenderer"):
            adapter = LegacyRendererAdapter(sample_config, mock_logger)
            assert adapter.config is sample_config

    def test_stores_logger(self, sample_config, mock_logger):
        """Test that adapter stores logger."""
        with patch("rendering.legacy_adapter.ModernReportRenderer"):
            adapter = LegacyRendererAdapter(sample_config, mock_logger)
            assert adapter.logger is mock_logger

    def test_creates_modern_renderer(self, sample_config, mock_logger):
        """Test that adapter creates modern renderer."""
        with patch("rendering.legacy_adapter.ModernReportRenderer") as MockRenderer:
            adapter = LegacyRendererAdapter(sample_config, mock_logger)
            assert adapter.modern_renderer == MockRenderer.return_value


# ============================================================================
# JSON Report Tests
# ============================================================================


class TestRenderJsonReport:
    """Tests for JSON report rendering."""

    def test_render_json_basic(self, adapter, sample_report_data, tmp_path):
        """Test basic JSON report rendering."""
        output_path = tmp_path / "report.json"

        adapter.render_json_report(sample_report_data, output_path)

        assert output_path.exists()
        with open(output_path) as f:
            loaded_data = json.load(f)
        assert loaded_data == sample_report_data

    def test_render_json_logs_output_path(self, adapter, sample_report_data, tmp_path, mock_logger):
        """Test that JSON rendering logs output path."""
        output_path = tmp_path / "report.json"

        adapter.render_json_report(sample_report_data, output_path)

        mock_logger.info.assert_called_once()
        assert str(output_path) in str(mock_logger.info.call_args)

    def test_render_json_pretty_formatted(self, adapter, sample_report_data, tmp_path):
        """Test that JSON output is pretty-formatted."""
        output_path = tmp_path / "report.json"

        adapter.render_json_report(sample_report_data, output_path)

        content = output_path.read_text()
        # Pretty-formatted JSON has newlines and indentation
        assert "\n" in content
        assert "  " in content  # Indentation

    def test_render_json_utf8_encoding(self, adapter, tmp_path):
        """Test that JSON uses UTF-8 encoding."""
        data = {
            "unicode_test": "日本語 русский عربي",
            "emoji": "🎉",
        }
        output_path = tmp_path / "unicode.json"

        adapter.render_json_report(data, output_path)

        with open(output_path, encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded["unicode_test"] == "日本語 русский عربي"
        assert loaded["emoji"] == "🎉"

    def test_render_json_datetime_conversion(self, adapter, tmp_path):
        """Test that JSON handles datetime objects via default=str."""
        from datetime import datetime

        data = {
            "timestamp": datetime(2024, 12, 19, 10, 0, 0),
            "value": 42,
        }
        output_path = tmp_path / "datetime.json"

        adapter.render_json_report(data, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        # Datetime should be converted to string
        assert "2024-12-19" in content

    def test_render_json_empty_data(self, adapter, tmp_path):
        """Test rendering empty JSON data."""
        output_path = tmp_path / "empty.json"

        adapter.render_json_report({}, output_path)

        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded == {}


# ============================================================================
# Markdown Report Tests
# ============================================================================


class TestRenderMarkdownReport:
    """Tests for Markdown report rendering."""

    def test_render_markdown_delegates_to_modern(self, adapter, sample_report_data, tmp_path):
        """Test that Markdown rendering delegates to modern renderer."""
        output_path = tmp_path / "report.md"
        mock_modern = adapter.modern_renderer

        # Setup: Modern renderer creates file
        def create_file(*args, **kwargs):
            output_path.write_text("# Test Report\n\nContent here.")

        mock_modern.render_markdown_report.side_effect = create_file

        result = adapter.render_markdown_report(sample_report_data, output_path)

        mock_modern.render_markdown_report.assert_called_once_with(sample_report_data, output_path)
        assert isinstance(result, str)

    def test_render_markdown_logs_output_path(
        self, adapter, sample_report_data, tmp_path, mock_logger
    ):
        """Test that Markdown rendering logs output path."""
        output_path = tmp_path / "report.md"

        # Setup file creation
        def create_file(*args, **kwargs):
            output_path.write_text("# Report")

        adapter.modern_renderer.render_markdown_report.side_effect = create_file

        adapter.render_markdown_report(sample_report_data, output_path)

        mock_logger.info.assert_called()
        log_message = str(mock_logger.info.call_args[0][0])
        assert str(output_path) in log_message
        assert "modern" in log_message.lower()

    def test_render_markdown_returns_content(self, adapter, sample_report_data, tmp_path):
        """Test that Markdown rendering returns file content."""
        output_path = tmp_path / "report.md"
        expected_content = "# Test Report\n\nThis is the content."

        def create_file(*args, **kwargs):
            output_path.write_text(expected_content)

        adapter.modern_renderer.render_markdown_report.side_effect = create_file

        result = adapter.render_markdown_report(sample_report_data, output_path)

        assert result == expected_content

    def test_render_markdown_backward_compatibility(self, adapter, sample_report_data, tmp_path):
        """Test backward compatibility: method returns content string."""
        output_path = tmp_path / "report.md"

        def create_file(*args, **kwargs):
            output_path.write_text("# Report")

        adapter.modern_renderer.render_markdown_report.side_effect = create_file

        result = adapter.render_markdown_report(sample_report_data, output_path)

        # Legacy code expects string return value
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# HTML Report Tests
# ============================================================================


class TestRenderHtmlReport:
    """Tests for HTML report rendering."""

    def test_render_html_modern_mode(self, adapter, sample_report_data, tmp_path):
        """Test HTML rendering in modern mode (no markdown_content)."""
        output_path = tmp_path / "report.html"

        adapter.render_html_report(sample_report_data, output_path)

        adapter.modern_renderer.render_html_report.assert_called_once_with(
            sample_report_data, output_path
        )

    def test_render_html_modern_logs_correctly(
        self, adapter, sample_report_data, tmp_path, mock_logger
    ):
        """Test that modern HTML rendering logs correctly."""
        output_path = tmp_path / "report.html"

        adapter.render_html_report(sample_report_data, output_path)

        # Should log modern mode
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("modern" in str(call).lower() for call in log_calls)

    def test_render_html_legacy_mode_with_markdown(
        self, adapter, sample_report_data, tmp_path, mock_logger
    ):
        """Test HTML rendering in legacy mode (with markdown_content)."""
        output_path = tmp_path / "report.html"
        markdown_content = "# Test\n\nContent"

        adapter.render_html_report(sample_report_data, output_path, markdown_content)

        # Should not call modern renderer
        adapter.modern_renderer.render_html_report.assert_not_called()

        # Should create HTML file
        assert output_path.exists()
        html_content = output_path.read_text()
        assert "<!DOCTYPE html>" in html_content

    def test_render_html_legacy_logs_deprecation(
        self, adapter, sample_report_data, tmp_path, mock_logger
    ):
        """Test that legacy mode logs deprecation warning."""
        output_path = tmp_path / "report.html"
        markdown_content = "# Test"

        adapter.render_html_report(sample_report_data, output_path, markdown_content)

        # Should log deprecation warning
        mock_logger.warning.assert_called_once()
        warning_msg = str(mock_logger.warning.call_args[0][0])
        assert "deprecated" in warning_msg.lower()

    def test_render_html_legacy_mode_creates_valid_html(
        self, adapter, sample_report_data, tmp_path
    ):
        """Test that legacy mode creates valid HTML structure."""
        output_path = tmp_path / "report.html"
        markdown_content = "# Header\n\nParagraph text"

        adapter.render_html_report(sample_report_data, output_path, markdown_content)

        html_content = output_path.read_text()
        assert "<!DOCTYPE html>" in html_content
        assert "<html" in html_content
        assert "<head>" in html_content
        assert "<body>" in html_content
        assert markdown_content in html_content

    def test_render_html_legacy_includes_styling(self, adapter, sample_report_data, tmp_path):
        """Test that legacy HTML includes CSS styling."""
        output_path = tmp_path / "report.html"

        adapter.render_html_report(sample_report_data, output_path, "# Test")

        html_content = output_path.read_text()
        assert "<style>" in html_content
        assert "font-family" in html_content

    def test_render_html_legacy_utf8_encoding(self, adapter, sample_report_data, tmp_path):
        """Test that legacy HTML uses UTF-8 encoding."""
        output_path = tmp_path / "unicode.html"
        markdown_content = "Unicode: 日本語 русский عربي 🎉"

        adapter.render_html_report(sample_report_data, output_path, markdown_content)

        html_content = output_path.read_text(encoding="utf-8")
        assert markdown_content in html_content
        assert 'charset="UTF-8"' in html_content

    def test_render_html_none_markdown_uses_modern(self, adapter, sample_report_data, tmp_path):
        """Test that None markdown_content triggers modern mode."""
        output_path = tmp_path / "report.html"

        adapter.render_html_report(sample_report_data, output_path, markdown_content=None)

        adapter.modern_renderer.render_html_report.assert_called_once()

    def test_render_html_empty_string_markdown_uses_legacy(
        self, adapter, sample_report_data, tmp_path
    ):
        """Test that empty string markdown_content still uses modern mode (empty string is falsy)."""
        output_path = tmp_path / "report.html"

        adapter.render_html_report(sample_report_data, output_path, markdown_content="")

        # Empty string is falsy in Python, so it uses modern mode
        adapter.modern_renderer.render_html_report.assert_called_once()


# ============================================================================
# ZIP Packaging Tests
# ============================================================================


class TestPackageZipReport:
    """Tests for ZIP report packaging."""

    @patch("util.zip_bundle.create_report_bundle")
    def test_package_zip_delegates_to_utility(self, mock_create_bundle, adapter, tmp_path):
        """Test that ZIP packaging delegates to utility function."""
        output_dir = tmp_path / "reports"
        output_dir.mkdir()
        project = "test-project"
        expected_path = tmp_path / "bundle.zip"
        mock_create_bundle.return_value = expected_path

        result = adapter.package_zip_report(output_dir, project)

        mock_create_bundle.assert_called_once_with(output_dir, project, adapter.logger)
        assert result == expected_path

    @patch("util.zip_bundle.create_report_bundle")
    def test_package_zip_passes_logger(self, mock_create_bundle, adapter, tmp_path, mock_logger):
        """Test that ZIP packaging passes logger to utility."""
        output_dir = tmp_path

        adapter.package_zip_report(output_dir, "project")

        call_args = mock_create_bundle.call_args[0]
        assert call_args[2] == mock_logger

    @patch("util.zip_bundle.create_report_bundle")
    def test_package_zip_returns_path(self, mock_create_bundle, adapter, tmp_path):
        """Test that ZIP packaging returns path from utility."""
        expected_path = Path("/tmp/test.zip")
        mock_create_bundle.return_value = expected_path

        result = adapter.package_zip_report(tmp_path, "project")

        assert result == expected_path


# ============================================================================
# Factory Function Tests
# ============================================================================


class TestCreateLegacyRenderer:
    """Tests for create_legacy_renderer factory function."""

    def test_create_with_modern_true(self, sample_config, mock_logger):
        """Test factory creates adapter when use_modern=True."""
        with patch("rendering.legacy_adapter.ModernReportRenderer"):
            renderer = create_legacy_renderer(sample_config, mock_logger, use_modern=True)

            assert isinstance(renderer, LegacyRendererAdapter)
            assert renderer.config == sample_config
            assert renderer.logger == mock_logger

    def test_create_default_uses_modern(self, sample_config, mock_logger):
        """Test factory defaults to use_modern=True."""
        with patch("rendering.legacy_adapter.ModernReportRenderer"):
            renderer = create_legacy_renderer(sample_config, mock_logger)

            assert isinstance(renderer, LegacyRendererAdapter)

    def test_create_with_modern_false_raises(self, sample_config, mock_logger):
        """Test factory raises NotImplementedError when use_modern=False."""
        with pytest.raises(NotImplementedError) as exc_info:
            create_legacy_renderer(sample_config, mock_logger, use_modern=False)

        assert "Legacy renderer not available" in str(exc_info.value)
        assert "use_modern=True" in str(exc_info.value)

    def test_create_passes_config_to_adapter(self, sample_config, mock_logger):
        """Test factory passes config to adapter."""
        with patch("rendering.legacy_adapter.ModernReportRenderer"):
            renderer = create_legacy_renderer(sample_config, mock_logger)

            assert renderer.config is sample_config

    def test_create_passes_logger_to_adapter(self, sample_config, mock_logger):
        """Test factory passes logger to adapter."""
        with patch("rendering.legacy_adapter.ModernReportRenderer"):
            renderer = create_legacy_renderer(sample_config, mock_logger)

            assert renderer.logger is mock_logger


# ============================================================================
# Integration Tests
# ============================================================================


class TestLegacyAdapterIntegration:
    """Integration tests for full adapter workflow."""

    def test_full_report_generation_workflow(
        self, sample_config, sample_report_data, tmp_path, mock_logger
    ):
        """Test complete report generation workflow."""
        with patch("rendering.legacy_adapter.ModernReportRenderer") as MockRenderer:
            adapter = LegacyRendererAdapter(sample_config, mock_logger)

            # Generate all report formats
            json_path = tmp_path / "report.json"
            md_path = tmp_path / "report.md"
            html_path = tmp_path / "report.html"

            # JSON
            adapter.render_json_report(sample_report_data, json_path)
            assert json_path.exists()

            # Markdown
            def create_md(*args, **kwargs):
                md_path.write_text("# Report")

            adapter.modern_renderer.render_markdown_report.side_effect = create_md
            md_content = adapter.render_markdown_report(sample_report_data, md_path)
            assert md_path.exists()
            assert isinstance(md_content, str)

            # HTML (modern)
            adapter.render_html_report(sample_report_data, html_path)
            MockRenderer.return_value.render_html_report.assert_called()

    def test_adapter_as_drop_in_replacement(
        self, sample_config, sample_report_data, tmp_path, mock_logger
    ):
        """Test adapter can be used as drop-in replacement for legacy renderer."""
        with patch("rendering.legacy_adapter.ModernReportRenderer"):
            # Create adapter
            renderer = create_legacy_renderer(sample_config, mock_logger)

            # Use legacy API
            output_path = tmp_path / "report.json"
            renderer.render_json_report(sample_report_data, output_path)

            # Should work without errors
            assert output_path.exists()

    def test_concurrent_rendering_operations(
        self, sample_config, sample_report_data, tmp_path, mock_logger
    ):
        """Test multiple rendering operations on same adapter."""
        with patch("rendering.legacy_adapter.ModernReportRenderer"):
            adapter = LegacyRendererAdapter(sample_config, mock_logger)

            # Multiple operations
            adapter.render_json_report(sample_report_data, tmp_path / "report1.json")
            adapter.render_json_report(sample_report_data, tmp_path / "report2.json")

            # Both should succeed
            assert (tmp_path / "report1.json").exists()
            assert (tmp_path / "report2.json").exists()


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================


class TestLegacyAdapterEdgeCases:
    """Tests for edge cases and error scenarios."""

    def test_render_json_with_none_values(self, adapter, tmp_path):
        """Test JSON rendering with None values."""
        data = {"key": None, "nested": {"value": None}}
        output_path = tmp_path / "null.json"

        adapter.render_json_report(data, output_path)

        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded["key"] is None

    def test_render_json_with_nested_structures(self, adapter, tmp_path):
        """Test JSON rendering with deeply nested structures."""
        data = {"level1": {"level2": {"level3": {"level4": {"value": 42}}}}}
        output_path = tmp_path / "nested.json"

        adapter.render_json_report(data, output_path)

        with open(output_path) as f:
            loaded = json.load(f)
        assert loaded["level1"]["level2"]["level3"]["level4"]["value"] == 42

    def test_render_markdown_file_not_created_by_modern(
        self, adapter, sample_report_data, tmp_path
    ):
        """Test error handling when modern renderer doesn't create file."""
        output_path = tmp_path / "missing.md"

        # Modern renderer doesn't create file
        adapter.modern_renderer.render_markdown_report.return_value = None

        with pytest.raises(FileNotFoundError):
            adapter.render_markdown_report(sample_report_data, output_path)

    def test_html_legacy_with_special_characters(self, adapter, sample_report_data, tmp_path):
        """Test legacy HTML with special HTML characters."""
        output_path = tmp_path / "special.html"
        markdown_content = "Test <script>alert('xss')</script>"

        adapter.render_html_report(sample_report_data, output_path, markdown_content)

        # Content should be in file (basic escaping not implemented in legacy)
        html_content = output_path.read_text()
        assert markdown_content in html_content

    def test_package_zip_with_nonexistent_directory(self, adapter, tmp_path):
        """Test ZIP packaging with non-existent directory."""
        nonexistent = tmp_path / "nonexistent"

        with patch("util.zip_bundle.create_report_bundle") as mock_bundle:
            # Let utility handle the error
            mock_bundle.side_effect = FileNotFoundError("Directory not found")

            with pytest.raises(FileNotFoundError):
                adapter.package_zip_report(nonexistent, "project")
