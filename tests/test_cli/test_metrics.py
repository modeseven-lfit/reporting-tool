#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for Performance Metrics Module

Tests the performance metrics collection, timing, resource tracking,
and reporting functionality.
"""

import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from cli.metrics import (
    APIStatistics,
    MetricsCollector,
    OperationMetrics,
    ResourceUsage,
    TimingMetric,
    format_bytes,
    format_duration,
    format_percentage,
    get_metrics_collector,
    print_debug_metrics,
    print_performance_summary,
    record_api_call,
    reset_metrics_collector,
    time_operation,
)


# =============================================================================
# FORMATTING TESTS
# =============================================================================


class TestFormatting:
    """Test formatting helper functions."""

    def test_format_duration_milliseconds(self):
        """Test formatting sub-second durations."""
        assert format_duration(0.1) == "100ms"
        assert format_duration(0.05) == "50ms"
        assert format_duration(0.001) == "1ms"

    def test_format_duration_seconds(self):
        """Test formatting seconds."""
        assert format_duration(1.5) == "1.5s"
        assert format_duration(30.2) == "30.2s"
        assert format_duration(59.9) == "59.9s"

    def test_format_duration_minutes(self):
        """Test formatting minutes and seconds."""
        assert format_duration(60) == "1m 0s"
        assert format_duration(90) == "1m 30s"
        assert format_duration(135) == "2m 15s"
        assert format_duration(3599) == "59m 59s"

    def test_format_duration_hours(self):
        """Test formatting hours, minutes, and seconds."""
        assert format_duration(3600) == "1h 0m 0s"
        assert format_duration(3661) == "1h 1m 1s"
        assert format_duration(7200) == "2h 0m 0s"
        assert format_duration(10800) == "3h 0m 0s"

    def test_format_bytes_small(self):
        """Test formatting small byte counts."""
        assert format_bytes(100) == "100.0 B"
        assert format_bytes(500) == "500.0 B"
        assert format_bytes(1023) == "1023.0 B"

    def test_format_bytes_kb(self):
        """Test formatting kilobytes."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(2048) == "2.0 KB"
        assert format_bytes(1536) == "1.5 KB"

    def test_format_bytes_mb(self):
        """Test formatting megabytes."""
        assert format_bytes(1024 * 1024) == "1.0 MB"
        assert format_bytes(2.5 * 1024 * 1024) == "2.5 MB"

    def test_format_bytes_gb(self):
        """Test formatting gigabytes."""
        assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
        assert format_bytes(1.5 * 1024 * 1024 * 1024) == "1.5 GB"

    def test_format_percentage_normal(self):
        """Test formatting percentage with normal values."""
        result = format_percentage(30, 100)
        assert "30" in result
        assert "%" in result

    def test_format_percentage_zero_total(self):
        """Test formatting percentage with zero total."""
        result = format_percentage(10, 0)
        assert "0%" in result


# =============================================================================
# DATA STRUCTURE TESTS
# =============================================================================


class TestDataStructures:
    """Test data structure classes."""

    def test_timing_metric_creation(self):
        """Test TimingMetric creation."""
        metric = TimingMetric(name="test_op", duration=1.5, start_time=100.0, end_time=101.5)
        assert metric.name == "test_op"
        assert metric.duration == 1.5
        assert metric.start_time == 100.0
        assert metric.end_time == 101.5

    def test_timing_metric_str(self):
        """Test TimingMetric string representation."""
        metric = TimingMetric(name="test_op", duration=1.5, start_time=100.0, end_time=101.5)
        result = str(metric)
        assert "test_op" in result
        assert "1.5s" in result

    def test_api_statistics_cache_hit_rate(self):
        """Test API statistics cache hit rate calculation."""
        stats = APIStatistics(api_name="github")
        stats.total_calls = 100
        stats.cached_calls = 75

        assert stats.cache_hit_rate == 75.0

    def test_api_statistics_cache_hit_rate_zero_calls(self):
        """Test cache hit rate with zero calls."""
        stats = APIStatistics(api_name="github")
        assert stats.cache_hit_rate == 0.0

    def test_api_statistics_average_duration(self):
        """Test average duration calculation."""
        stats = APIStatistics(api_name="github")
        stats.total_calls = 10
        stats.total_duration = 5.0

        assert stats.average_duration == 0.5

    def test_api_statistics_calls_per_second(self):
        """Test calls per second calculation."""
        stats = APIStatistics(api_name="github")
        stats.total_calls = 100
        stats.total_duration = 50.0

        assert stats.calls_per_second == 2.0

    def test_resource_usage_creation(self):
        """Test ResourceUsage creation."""
        usage = ResourceUsage(
            peak_memory_mb=500.0, avg_memory_mb=300.0, cpu_time_seconds=10.0, cpu_utilization=150.0
        )
        assert usage.peak_memory_mb == 500.0
        assert usage.avg_memory_mb == 300.0
        assert usage.cpu_time_seconds == 10.0
        assert usage.cpu_utilization == 150.0

    def test_operation_metrics_creation(self):
        """Test OperationMetrics creation."""
        metric = OperationMetrics(operation_name="analyze_repo", duration=2.5, success=True)
        assert metric.operation_name == "analyze_repo"
        assert metric.duration == 2.5
        assert metric.success is True
        assert metric.error is None


# =============================================================================
# METRICS COLLECTOR TESTS
# =============================================================================


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_collector_initialization(self):
        """Test collector initializes correctly."""
        collector = MetricsCollector()
        assert collector._start_time > 0
        assert collector._end_time is None
        assert len(collector._timings) == 0

    def test_time_operation_context(self):
        """Test timing operation with context manager."""
        collector = MetricsCollector()

        with collector.time_operation("test_op"):
            time.sleep(0.01)  # Small delay

        assert len(collector._timings) == 1
        assert collector._timings[0].name == "test_op"
        assert collector._timings[0].duration >= 0.01

    def test_time_operation_with_metadata(self):
        """Test timing operation with metadata."""
        collector = MetricsCollector()

        with collector.time_operation("test_op", repo="test-repo"):
            time.sleep(0.01)

        assert collector._timings[0].metadata["repo"] == "test-repo"

    def test_record_timing(self):
        """Test manual timing recording."""
        collector = MetricsCollector()

        collector.record_timing(
            "manual_op", duration=1.5, start_time=100.0, end_time=101.5, custom_data="test"
        )

        assert len(collector._timings) == 1
        assert collector._timings[0].name == "manual_op"
        assert collector._timings[0].duration == 1.5
        assert collector._timings[0].metadata["custom_data"] == "test"

    def test_record_api_call(self):
        """Test API call recording."""
        collector = MetricsCollector()

        collector.record_api_call("github", 0.5, cached=False, failed=False)
        collector.record_api_call("github", 0.3, cached=True, failed=False)
        collector.record_api_call("github", 0.2, cached=True, failed=False)

        stats = collector._api_stats["github"]
        assert stats.total_calls == 3
        assert stats.cached_calls == 2
        assert stats.failed_calls == 0
        assert stats.total_duration == 1.0

    def test_record_api_call_failures(self):
        """Test recording failed API calls."""
        collector = MetricsCollector()

        collector.record_api_call("github", 0.5, failed=True)

        stats = collector._api_stats["github"]
        assert stats.total_calls == 1
        assert stats.failed_calls == 1

    def test_record_operation(self):
        """Test operation recording."""
        collector = MetricsCollector()

        collector.record_operation("analyze_repo", duration=2.5, success=True, repo_name="test")

        assert len(collector._operation_metrics) == 1
        assert collector._operation_metrics[0].operation_name == "analyze_repo"
        assert collector._operation_metrics[0].duration == 2.5
        assert collector._operation_metrics[0].success is True

    def test_record_operation_failure(self):
        """Test recording failed operations."""
        collector = MetricsCollector()

        collector.record_operation(
            "analyze_repo", duration=1.0, success=False, error="Repository not found"
        )

        assert collector._operation_metrics[0].success is False
        assert collector._operation_metrics[0].error == "Repository not found"

    def test_get_total_duration(self):
        """Test total duration calculation."""
        collector = MetricsCollector()
        time.sleep(0.1)

        duration = collector.get_total_duration()
        assert duration >= 0.1

    def test_finalize(self):
        """Test collector finalization."""
        collector = MetricsCollector()
        assert collector._end_time is None

        collector.finalize()
        assert collector._end_time is not None

    def test_get_timing_breakdown(self):
        """Test timing breakdown by category."""
        collector = MetricsCollector()

        collector.record_timing("git:clone", 1.0, 0, 1)
        collector.record_timing("git:fetch", 0.5, 1, 1.5)
        collector.record_timing("api:github", 0.3, 1.5, 1.8)
        collector.record_timing("api:gerrit", 0.2, 1.8, 2.0)

        breakdown = collector.get_timing_breakdown()

        assert breakdown["git"] == 1.5
        assert breakdown["api"] == 0.5

    def test_get_resource_usage(self):
        """Test resource usage retrieval."""
        collector = MetricsCollector()
        time.sleep(0.1)  # Let monitoring collect samples

        usage = collector.get_resource_usage()

        assert usage.peak_memory_mb >= 0
        assert usage.cpu_time_seconds >= 0
        assert usage.cpu_utilization >= 0

    @patch("builtins.print")
    def test_print_summary(self, mock_print):
        """Test summary printing."""
        collector = MetricsCollector()

        collector.record_operation("test_op", 1.0, success=True)
        collector.record_api_call("github", 0.5)

        collector.print_summary()

        # Should have printed something
        assert mock_print.call_count > 0

    @patch("builtins.print")
    def test_print_summary_verbose(self, mock_print):
        """Test verbose summary printing."""
        collector = MetricsCollector()

        collector.record_timing("git:clone", 1.0, 0, 1)
        collector.record_timing("api:github", 0.5, 1, 1.5)

        collector.print_summary(verbose=True)

        # Verbose mode should print more
        assert mock_print.call_count > 0

    @patch("builtins.print")
    def test_print_debug_metrics(self, mock_print):
        """Test debug metrics printing."""
        collector = MetricsCollector()

        collector.record_operation("slow_op", 10.0, success=True)
        collector.record_timing("test_op", 2.0, 0, 2)

        collector.print_debug_metrics()

        assert mock_print.call_count > 0

    def test_get_output_summary(self, tmp_path):
        """Test output files summary."""
        collector = MetricsCollector()

        # Create test files
        json_file = tmp_path / "output.json"
        html_file = tmp_path / "output.html"

        json_file.write_text('{"test": "data"}')
        html_file.write_text("<html></html>")

        output_files = {
            "JSON": json_file,
            "HTML": html_file,
        }

        summary = collector.get_output_summary(output_files)

        assert "JSON" in summary
        assert "HTML" in summary
        assert str(json_file) in summary


# =============================================================================
# GLOBAL INSTANCE TESTS
# =============================================================================


class TestGlobalInstance:
    """Test global metrics collector instance."""

    def test_get_metrics_collector(self):
        """Test getting global collector."""
        reset_metrics_collector()
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()

        # Should return same instance
        assert collector1 is collector2

    def test_reset_metrics_collector(self):
        """Test resetting global collector."""
        collector1 = get_metrics_collector()
        reset_metrics_collector()
        collector2 = get_metrics_collector()

        # Should be different instance
        assert collector1 is not collector2

    def test_time_operation_global(self):
        """Test time_operation with global collector."""
        reset_metrics_collector()

        with time_operation("test_op"):
            time.sleep(0.01)

        collector = get_metrics_collector()
        assert len(collector._timings) == 1

    def test_record_api_call_global(self):
        """Test record_api_call with global collector."""
        reset_metrics_collector()

        record_api_call("github", 0.5, cached=True)

        collector = get_metrics_collector()
        assert "github" in collector._api_stats

    @patch("builtins.print")
    def test_print_performance_summary_global(self, mock_print):
        """Test print_performance_summary with global collector."""
        reset_metrics_collector()

        with time_operation("test_op"):
            time.sleep(0.01)

        print_performance_summary()

        assert mock_print.call_count > 0

    @patch("builtins.print")
    def test_print_debug_metrics_global(self, mock_print):
        """Test print_debug_metrics with global collector."""
        reset_metrics_collector()

        with time_operation("test_op"):
            time.sleep(0.01)

        print_debug_metrics()

        assert mock_print.call_count > 0


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests for metrics collection."""

    def test_complete_workflow(self):
        """Test complete metrics collection workflow."""
        collector = MetricsCollector()

        # Simulate repository analysis
        with collector.time_operation("total_analysis"):
            # Git operations
            with collector.time_operation("git:clone", repo="repo1"):
                time.sleep(0.01)

            with collector.time_operation("git:fetch", repo="repo1"):
                time.sleep(0.01)

            # API calls
            collector.record_api_call("github", 0.1, cached=False)
            collector.record_api_call("github", 0.05, cached=True)

            # Record operation
            collector.record_operation("analyze_repo1", 0.5, success=True)

        # Verify metrics were collected
        assert len(collector._timings) == 3  # total, clone, fetch
        assert "github" in collector._api_stats
        assert len(collector._operation_metrics) == 1

        # Get summary
        duration = collector.get_total_duration()
        assert duration > 0

        breakdown = collector.get_timing_breakdown()
        assert "git" in breakdown
        assert "total_analysis" in breakdown

    def test_multiple_repos_analysis(self):
        """Test metrics for multiple repository analysis."""
        collector = MetricsCollector()

        repos = ["repo1", "repo2", "repo3"]

        for repo in repos:
            with collector.time_operation(f"analyze:{repo}", repo=repo):
                time.sleep(0.01)
                collector.record_api_call("github", 0.05)

        assert len(collector._timings) == 3
        stats = collector._api_stats["github"]
        assert stats.total_calls == 3

    def test_nested_timing(self):
        """Test nested timing operations."""
        collector = MetricsCollector()

        with collector.time_operation("outer"):
            time.sleep(0.01)
            with collector.time_operation("inner1"):
                time.sleep(0.01)
            with collector.time_operation("inner2"):
                time.sleep(0.01)

        assert len(collector._timings) == 3

        # Outer should be longer than either inner
        outer = next(t for t in collector._timings if t.name == "outer")
        inner1 = next(t for t in collector._timings if t.name == "inner1")
        inner2 = next(t for t in collector._timings if t.name == "inner2")

        assert outer.duration >= inner1.duration
        assert outer.duration >= inner2.duration


# =============================================================================
# EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_zero_duration_operation(self):
        """Test operation with zero duration."""
        collector = MetricsCollector()

        collector.record_timing("instant_op", 0.0, 0, 0)

        assert len(collector._timings) == 1
        assert collector._timings[0].duration == 0.0

    def test_no_operations(self):
        """Test collector with no operations."""
        collector = MetricsCollector()

        # Should not crash
        collector.finalize()
        duration = collector.get_total_duration()
        assert duration >= 0

    def test_very_long_operation(self):
        """Test formatting very long durations."""
        result = format_duration(36000)  # 10 hours
        assert "10h" in result

    def test_very_large_files(self):
        """Test formatting very large file sizes."""
        result = format_bytes(1024**4)  # 1 TB
        assert "TB" in result

    def test_concurrent_api_calls(self):
        """Test recording concurrent API calls."""
        collector = MetricsCollector()

        # Simulate concurrent calls to same API
        for _ in range(100):
            collector.record_api_call("github", 0.1, cached=False)

        stats = collector._api_stats["github"]
        assert stats.total_calls == 100

    def test_multiple_api_services(self):
        """Test tracking multiple API services."""
        collector = MetricsCollector()

        collector.record_api_call("github", 0.5)
        collector.record_api_call("gerrit", 0.3)
        collector.record_api_call("jenkins", 0.2)

        assert len(collector._api_stats) == 3
        assert "github" in collector._api_stats
        assert "gerrit" in collector._api_stats
        assert "jenkins" in collector._api_stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
