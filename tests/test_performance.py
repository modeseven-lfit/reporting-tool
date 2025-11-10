# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for the performance profiling module.

This module tests:
- PerformanceProfiler functionality
- OperationTimer accuracy
- MemoryTracker capabilities
- ProfileReport generation
- Metric aggregation
- Report export and comparison
"""

import json
import os
import tempfile
import time

import pytest

from performance import (
    AggregatedMetrics,
    MemoryTracker,
    OperationMetric,
    OperationTimer,
    PerformanceProfiler,
    ProfileReport,
    profile_operation,
)


class TestOperationTimer:
    """Tests for OperationTimer class."""

    def test_timer_basic_usage(self):
        """Test basic timing functionality."""
        timer = OperationTimer("test_op", category="test")

        with timer:
            time.sleep(0.1)  # Sleep 100ms

        assert timer.duration is not None
        assert timer.duration >= 0.1
        assert timer.duration < 0.15  # Allow some overhead
        assert timer.success is True
        assert timer.error is None

    def test_timer_measures_memory(self):
        """Test memory tracking in timer."""
        timer = OperationTimer("test_op", category="test")

        with timer:
            # Allocate some memory
            pass

        assert timer.memory_start is not None
        assert timer.memory_end is not None
        assert timer.memory_delta is not None

    def test_timer_handles_exceptions(self):
        """Test timer tracks failures correctly."""
        timer = OperationTimer("test_op", category="test")

        try:
            with timer:
                raise ValueError("Test error")
        except ValueError:
            pass

        assert timer.success is False
        assert timer.error is not None
        assert "ValueError" in timer.error

    def test_timer_with_profiler(self):
        """Test timer integration with profiler."""
        profiler = PerformanceProfiler()
        timer = OperationTimer("test_op", category="test", profiler=profiler)

        with timer:
            time.sleep(0.05)

        assert len(profiler.operations) == 1
        assert profiler.operations[0].name == "test_op"
        assert profiler.operations[0].category == "test"

    def test_timer_with_metadata(self):
        """Test timer stores metadata."""
        profiler = PerformanceProfiler()
        metadata = {"repo": "test-repo", "size": 100}
        timer = OperationTimer("test_op", category="test", profiler=profiler, metadata=metadata)

        with timer:
            pass

        assert profiler.operations[0].metadata == metadata


class TestMemoryTracker:
    """Tests for MemoryTracker class."""

    def test_memory_tracker_basic(self):
        """Test basic memory tracking."""
        tracker = MemoryTracker()
        tracker.start()

        # Allocate some memory
        data = [0] * 100000
        tracker.snapshot("after_allocation")

        del data
        tracker.stop()

        stats = tracker.get_stats()
        if stats.get("available"):
            assert stats["start_mb"] > 0
            assert stats["end_mb"] > 0
            assert len(stats["snapshots"]) >= 2

    def test_memory_tracker_snapshots(self):
        """Test memory snapshots with labels."""
        tracker = MemoryTracker()
        tracker.start()

        tracker.snapshot("checkpoint_1")
        tracker.snapshot("checkpoint_2")
        tracker.stop()

        stats = tracker.get_stats()
        if stats.get("available"):
            labels = [s["label"] for s in stats["snapshots"]]
            assert "start" in labels
            assert "checkpoint_1" in labels
            assert "checkpoint_2" in labels
            assert "end" in labels

    def test_memory_tracker_not_started(self):
        """Test tracker behavior when not started."""
        tracker = MemoryTracker()
        tracker.snapshot("test")  # Should not crash

        tracker.get_stats()
        # Should return empty or unavailable


class TestPerformanceProfiler:
    """Tests for PerformanceProfiler class."""

    def test_profiler_initialization(self):
        """Test profiler initialization."""
        profiler = PerformanceProfiler(name="test_profiler")

        assert profiler.name == "test_profiler"
        assert len(profiler.operations) == 0
        assert len(profiler.custom_metrics) == 0

    def test_profiler_track_operation(self):
        """Test tracking operations with context manager."""
        profiler = PerformanceProfiler()
        profiler.start()

        with profiler.track_operation("test_op", category="test"):
            time.sleep(0.05)

        profiler.stop()

        assert len(profiler.operations) == 1
        assert profiler.operations[0].name == "test_op"
        assert profiler.operations[0].success is True

    def test_profiler_multiple_operations(self):
        """Test tracking multiple operations."""
        profiler = PerformanceProfiler()
        profiler.start()

        with profiler.track_operation("op1", category="test"):
            time.sleep(0.02)

        with profiler.track_operation("op2", category="test"):
            time.sleep(0.03)

        with profiler.track_operation("op1", category="test"):
            time.sleep(0.02)

        profiler.stop()

        assert len(profiler.operations) == 3

    def test_profiler_custom_metrics(self):
        """Test recording custom metrics."""
        profiler = PerformanceProfiler()

        profiler.record_metric("repo_count", 42, "repositories")
        profiler.record_metric("total_size", 1024, "MB")

        assert "repo_count" in profiler.custom_metrics
        assert profiler.custom_metrics["repo_count"]["value"] == 42
        assert profiler.custom_metrics["repo_count"]["unit"] == "repositories"

    def test_profiler_memory_snapshots(self):
        """Test memory snapshots through profiler."""
        profiler = PerformanceProfiler()
        profiler.start()

        profiler.memory_snapshot("checkpoint_1")
        profiler.memory_snapshot("checkpoint_2")

        profiler.stop()

        stats = profiler.memory_tracker.get_stats()
        if stats.get("available"):
            assert len(stats["snapshots"]) >= 4  # start, 2 checkpoints, end

    def test_profiler_aggregated_metrics(self):
        """Test metric aggregation."""
        profiler = PerformanceProfiler()

        # Track same operation multiple times
        with profiler.track_operation("test_op", category="test"):
            time.sleep(0.02)

        with profiler.track_operation("test_op", category="test"):
            time.sleep(0.03)

        with profiler.track_operation("test_op", category="test"):
            time.sleep(0.025)

        aggregated = profiler.get_aggregated_metrics()

        assert "test:test_op" in aggregated
        metrics = aggregated["test:test_op"]
        assert metrics.count == 3
        assert metrics.name == "test_op"
        assert metrics.category == "test"
        assert metrics.success_count == 3
        assert metrics.error_count == 0

    def test_profiler_aggregation_with_errors(self):
        """Test aggregation includes error counts."""
        profiler = PerformanceProfiler()

        with profiler.track_operation("test_op", category="test"):
            pass

        try:
            with profiler.track_operation("test_op", category="test"):
                raise ValueError("Test error")
        except ValueError:
            pass

        aggregated = profiler.get_aggregated_metrics()
        metrics = aggregated["test:test_op"]

        assert metrics.count == 2
        assert metrics.success_count == 1
        assert metrics.error_count == 1
        assert metrics.success_rate == 50.0


class TestOperationMetric:
    """Tests for OperationMetric dataclass."""

    def test_metric_properties(self):
        """Test metric computed properties."""
        metric = OperationMetric(
            name="test",
            category="test",
            start_time=0.0,
            end_time=1.234,
            duration=1.234,
            memory_start=0,
            memory_end=1024 * 1024 * 10,  # 10 MB
            memory_delta=1024 * 1024 * 10,
            success=True,
        )

        assert metric.duration_ms == 1234.0
        assert metric.memory_mb == 10.0


class TestAggregatedMetrics:
    """Tests for AggregatedMetrics dataclass."""

    def test_aggregated_properties(self):
        """Test aggregated metric properties."""
        metrics = AggregatedMetrics(
            name="test",
            category="test",
            count=5,
            total_duration=5.0,
            avg_duration=1.0,
            min_duration=0.5,
            max_duration=1.5,
            total_memory_delta=1024 * 1024 * 50,  # 50 MB total
            avg_memory_delta=1024 * 1024 * 10,  # 10 MB avg
            success_count=4,
            error_count=1,
        )

        assert metrics.success_rate == 80.0
        assert metrics.avg_duration_ms == 1000.0
        assert metrics.avg_memory_mb == 10.0


class TestProfileReport:
    """Tests for ProfileReport class."""

    def test_report_generation(self):
        """Test report generation from profiler."""
        profiler = PerformanceProfiler(name="test_report")
        profiler.start()

        with profiler.track_operation("op1", category="test"):
            time.sleep(0.02)

        profiler.stop()

        report = profiler.get_report()

        assert isinstance(report, ProfileReport)
        assert report.profiler == profiler

    def test_report_format_text(self):
        """Test text formatting of report."""
        profiler = PerformanceProfiler(name="test_report")
        profiler.start()

        with profiler.track_operation("op1", category="test"):
            time.sleep(0.02)

        profiler.record_metric("test_metric", 42, "units")
        profiler.stop()

        report = profiler.get_report()
        text = report.format()

        assert "test_report" in text
        assert "op1" in text
        assert "test_metric" in text

    def test_report_format_detailed(self):
        """Test detailed text formatting."""
        profiler = PerformanceProfiler(name="test_report")

        with profiler.track_operation("op1", category="test"):
            pass

        report = profiler.get_report()
        detailed = report.format(detailed=True)

        assert "Detailed Operations" in detailed
        assert "op1" in detailed

    def test_report_to_dict(self):
        """Test report dictionary export."""
        profiler = PerformanceProfiler(name="test_report")
        profiler.start()

        with profiler.track_operation("op1", category="test"):
            time.sleep(0.02)

        profiler.stop()

        report = profiler.get_report()
        data = report.to_dict()

        assert data["profiler_name"] == "test_report"
        assert data["total_duration"] is not None
        assert "aggregated_metrics" in data
        assert data["operation_count"] == 1

    def test_report_to_json(self):
        """Test JSON export."""
        profiler = PerformanceProfiler(name="test_report")

        with profiler.track_operation("op1", category="test"):
            pass

        report = profiler.get_report()
        json_str = report.to_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["profiler_name"] == "test_report"

    def test_report_save_json(self):
        """Test saving report to JSON file."""
        profiler = PerformanceProfiler(name="test_report")

        with profiler.track_operation("op1", category="test"):
            pass

        report = profiler.get_report()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            report.save(filepath, format="json")

            assert os.path.exists(filepath)

            with open(filepath) as f:
                data = json.load(f)

            assert data["profiler_name"] == "test_report"
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_report_save_text(self):
        """Test saving report to text file."""
        profiler = PerformanceProfiler(name="test_report")

        with profiler.track_operation("op1", category="test"):
            pass

        report = profiler.get_report()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            filepath = f.name

        try:
            report.save(filepath, format="text")

            assert os.path.exists(filepath)

            with open(filepath) as f:
                content = f.read()

            assert "test_report" in content
            assert "op1" in content
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_report_compare_to_baseline(self):
        """Test comparison to baseline report."""
        # Create baseline
        baseline_profiler = PerformanceProfiler(name="baseline")
        baseline_profiler.start()

        with baseline_profiler.track_operation("op1", category="test"):
            time.sleep(0.1)

        baseline_profiler.stop()
        baseline_report = baseline_profiler.get_report()

        # Save baseline
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            baseline_path = f.name

        try:
            baseline_report.save(baseline_path, format="json")

            # Create current profiler (faster)
            current_profiler = PerformanceProfiler(name="current")
            current_profiler.start()

            with current_profiler.track_operation("op1", category="test"):
                time.sleep(0.05)  # Faster than baseline

            current_profiler.stop()
            current_report = current_profiler.get_report()

            # Compare
            comparison = current_report.compare_to_baseline(baseline_path)

            assert "baseline_duration" in comparison
            assert "current_duration" in comparison
            assert "duration_change_pct" in comparison
            assert comparison["improvement"] is True  # Should be faster
        finally:
            if os.path.exists(baseline_path):
                os.unlink(baseline_path)


class TestProfileOperationDecorator:
    """Tests for profile_operation decorator."""

    def test_decorator_basic(self):
        """Test basic decorator usage."""

        @profile_operation("test_func", category="test")
        def test_function():
            time.sleep(0.02)
            return 42

        result = test_function()

        assert result == 42

    def test_decorator_with_args(self):
        """Test decorator with function arguments."""

        @profile_operation("test_func", category="test")
        def test_function(x, y):
            return x + y

        result = test_function(1, 2)

        assert result == 3

    def test_decorator_handles_exceptions(self):
        """Test decorator preserves exceptions."""

        @profile_operation("test_func", category="test")
        def test_function():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_function()


class TestIntegrationScenarios:
    """Integration tests for realistic profiling scenarios."""

    def test_multi_category_operations(self):
        """Test profiling operations across multiple categories."""
        profiler = PerformanceProfiler(name="integration_test")
        profiler.start()

        with profiler.track_operation("clone_repo", category="git"):
            time.sleep(0.02)

        with profiler.track_operation("fetch_data", category="api"):
            time.sleep(0.03)

        with profiler.track_operation("analyze_code", category="analysis"):
            time.sleep(0.04)

        with profiler.track_operation("render_report", category="rendering"):
            time.sleep(0.01)

        profiler.stop()

        aggregated = profiler.get_aggregated_metrics()

        assert len(aggregated) == 4
        assert "git:clone_repo" in aggregated
        assert "api:fetch_data" in aggregated
        assert "analysis:analyze_code" in aggregated
        assert "rendering:render_report" in aggregated

    def test_nested_operations(self):
        """Test profiling nested operations."""
        profiler = PerformanceProfiler(name="nested_test")
        profiler.start()

        with profiler.track_operation("parent_op", category="test"):
            time.sleep(0.01)

            with profiler.track_operation("child_op_1", category="test"):
                time.sleep(0.01)

            with profiler.track_operation("child_op_2", category="test"):
                time.sleep(0.01)

        profiler.stop()

        assert len(profiler.operations) == 3

    def test_full_profiling_workflow(self):
        """Test complete profiling workflow."""
        profiler = PerformanceProfiler(name="workflow_test")
        profiler.start()

        # Simulate repository analysis
        for i in range(3):
            profiler.memory_snapshot(f"before_repo_{i}")

            with profiler.track_operation(f"clone_repo_{i}", category="git"):
                time.sleep(0.01)

            with profiler.track_operation(f"analyze_repo_{i}", category="analysis"):
                time.sleep(0.02)

            profiler.memory_snapshot(f"after_repo_{i}")

        profiler.record_metric("total_repos", 3, "repositories")
        profiler.stop()

        # Generate report
        report = profiler.get_report()

        # Validate
        assert len(profiler.operations) == 6
        assert "total_repos" in profiler.custom_metrics

        # Check aggregation
        aggregated = profiler.get_aggregated_metrics()

        # Should have aggregated the repeated operations
        git_ops = sum(1 for key in aggregated if key.startswith("git:"))
        analysis_ops = sum(1 for key in aggregated if key.startswith("analysis:"))

        assert git_ops == 3
        assert analysis_ops == 3

        # Validate report
        text_report = report.format()
        assert "workflow_test" in text_report
        assert "GIT:" in text_report
        assert "ANALYSIS:" in text_report


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_profiler_without_start_stop(self):
        """Test profiler used without explicit start/stop."""
        profiler = PerformanceProfiler()

        with profiler.track_operation("op1", category="test"):
            pass

        report = profiler.get_report()
        data = report.to_dict()

        # Should work but have None for start/end times
        assert data["start_time"] is None
        assert data["end_time"] is None

    def test_empty_profiler_report(self):
        """Test report generation from empty profiler."""
        profiler = PerformanceProfiler()
        report = profiler.get_report()

        text = report.format()
        assert "Performance Profile" in text

        data = report.to_dict()
        assert data["operation_count"] == 0

    def test_memory_tracker_without_psutil(self):
        """Test memory tracker gracefully handles missing psutil."""
        # This should not crash even if psutil is not available
        tracker = MemoryTracker()
        tracker.start()
        tracker.snapshot("test")
        tracker.stop()

        stats = tracker.get_stats()
        # Should return either data or unavailable status
        assert isinstance(stats, dict)

    def test_timer_exception_propagation(self):
        """Test timer doesn't suppress exceptions."""
        profiler = PerformanceProfiler()

        with (
            pytest.raises(RuntimeError, match="Test error"),
            profiler.track_operation("failing_op", category="test"),
        ):
            raise RuntimeError("Test error")

        # Operation should still be recorded
        assert len(profiler.operations) == 1
        assert profiler.operations[0].success is False
