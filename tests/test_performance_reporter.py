# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Tests for the performance monitoring and reporting module.

This module tests all aspects of performance reporting including:
- Metrics collection
- Report generation
- Trend analysis
- Alert evaluation
- Visualization
- Export functionality
"""

import json
from unittest.mock import MagicMock

from performance.reporter import (
    Alert,
    AlertRule,
    AlertSeverity,
    Metric,
    MetricsCollector,
    MetricsVisualizer,
    MetricTrend,
    MetricType,
    PerformanceReport,
    PerformanceReporter,
    create_performance_reporter,
)


class TestMetricType:
    """Test MetricType enum."""

    def test_metric_types(self):
        """Test metric type values."""
        assert MetricType.TIMING.value == "timing"
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.RATE.value == "rate"


class TestAlertSeverity:
    """Test AlertSeverity enum."""

    def test_severity_levels(self):
        """Test severity level values."""
        assert AlertSeverity.INFO.value == "info"
        assert AlertSeverity.WARNING.value == "warning"
        assert AlertSeverity.ERROR.value == "error"
        assert AlertSeverity.CRITICAL.value == "critical"


class TestMetric:
    """Test Metric dataclass."""

    def test_create_metric(self):
        """Test creating a metric."""
        metric = Metric(
            name="test_metric",
            value=42.5,
            metric_type=MetricType.GAUGE,
            tags={"env": "test"},
            unit="ms",
        )

        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.metric_type == MetricType.GAUGE
        assert metric.tags["env"] == "test"
        assert metric.unit == "ms"

    def test_metric_to_dict(self):
        """Test converting metric to dictionary."""
        metric = Metric(
            name="test_metric",
            value=100.0,
            metric_type=MetricType.COUNTER,
        )

        data = metric.to_dict()

        assert data["name"] == "test_metric"
        assert data["value"] == 100.0
        assert data["type"] == "counter"
        assert "timestamp" in data


class TestMetricTrend:
    """Test MetricTrend dataclass."""

    def test_create_trend(self):
        """Test creating a metric trend."""
        trend = MetricTrend(
            metric_name="execution_time",
            current_value=50.0,
            previous_value=100.0,
            change_percentage=-50.0,
            trend_direction="down",
            is_improvement=True,
        )

        assert trend.metric_name == "execution_time"
        assert trend.change_percentage == -50.0
        assert trend.is_improvement is True

    def test_trend_format(self):
        """Test formatting trend."""
        trend = MetricTrend(
            metric_name="memory_usage",
            current_value=200.0,
            previous_value=100.0,
            change_percentage=100.0,
            trend_direction="up",
            is_improvement=False,
        )

        formatted = trend.format()

        assert "memory_usage" in formatted
        assert "200.00" in formatted
        assert "100.0%" in formatted


class TestAlert:
    """Test Alert dataclass."""

    def test_create_alert(self):
        """Test creating an alert."""
        alert = Alert(
            severity=AlertSeverity.WARNING,
            metric_name="cpu_usage",
            message="CPU usage is high",
            value=85.0,
            threshold=80.0,
        )

        assert alert.severity == AlertSeverity.WARNING
        assert alert.metric_name == "cpu_usage"
        assert alert.value == 85.0

    def test_alert_format(self):
        """Test formatting alert."""
        alert = Alert(
            severity=AlertSeverity.ERROR,
            metric_name="memory",
            message="Memory exceeded threshold",
            value=1500.0,
            threshold=1000.0,
        )

        formatted = alert.format()

        assert "ERROR" in formatted
        assert "memory" in formatted
        assert "Memory exceeded threshold" in formatted


class TestAlertRule:
    """Test AlertRule dataclass."""

    def test_create_rule(self):
        """Test creating alert rule."""
        rule = AlertRule(
            metric_name="response_time",
            threshold=100.0,
            comparison=">",
            severity=AlertSeverity.WARNING,
            message_template="Response time {value} exceeds {threshold}",
        )

        assert rule.metric_name == "response_time"
        assert rule.threshold == 100.0
        assert rule.comparison == ">"

    def test_evaluate_rule_greater_than(self):
        """Test evaluating rule with > comparison."""
        rule = AlertRule(
            metric_name="test",
            threshold=100.0,
            comparison=">",
            severity=AlertSeverity.WARNING,
            message_template="Value {value} exceeds {threshold}",
        )

        # Should trigger
        alert = rule.evaluate(150.0)
        assert alert is not None
        assert alert.value == 150.0

        # Should not trigger
        alert = rule.evaluate(50.0)
        assert alert is None

    def test_evaluate_rule_less_than(self):
        """Test evaluating rule with < comparison."""
        rule = AlertRule(
            metric_name="test",
            threshold=50.0,
            comparison="<",
            severity=AlertSeverity.INFO,
            message_template="Value {value} below {threshold}",
        )

        # Should trigger
        alert = rule.evaluate(30.0)
        assert alert is not None

        # Should not trigger
        alert = rule.evaluate(60.0)
        assert alert is None

    def test_evaluate_rule_equals(self):
        """Test evaluating rule with == comparison."""
        rule = AlertRule(
            metric_name="test",
            threshold=100.0,
            comparison="==",
            severity=AlertSeverity.INFO,
            message_template="Value is exactly {threshold}",
        )

        # Should trigger
        alert = rule.evaluate(100.0)
        assert alert is not None

        # Should not trigger
        alert = rule.evaluate(100.1)
        assert alert is None


class TestPerformanceReport:
    """Test PerformanceReport dataclass."""

    def test_create_report(self):
        """Test creating performance report."""
        report = PerformanceReport(
            metrics=[
                Metric("test1", 100.0, MetricType.GAUGE),
                Metric("test2", 200.0, MetricType.COUNTER),
            ],
            trends=[],
            alerts=[],
            summary={"total": 300},
        )

        assert len(report.metrics) == 2
        assert report.summary["total"] == 300

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = PerformanceReport(
            metrics=[Metric("test", 100.0, MetricType.GAUGE)],
            summary={"key": "value"},
        )

        data = report.to_dict()

        assert "generated_at" in data
        assert "metrics" in data
        assert len(data["metrics"]) == 1
        assert data["summary"]["key"] == "value"

    def test_report_to_json(self):
        """Test converting report to JSON."""
        report = PerformanceReport(
            metrics=[Metric("test", 100.0, MetricType.GAUGE)],
        )

        json_str = report.to_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert "metrics" in data

    def test_report_format(self):
        """Test formatting report as string."""
        metric = Metric("test_metric", 42.0, MetricType.GAUGE, unit="ms")
        trend = MetricTrend(
            "memory",
            100.0,
            150.0,
            -33.3,
            "down",
            True,
        )
        alert = Alert(
            AlertSeverity.WARNING,
            "cpu",
            "CPU high",
            90.0,
            80.0,
        )

        report = PerformanceReport(
            metrics=[metric],
            trends=[trend],
            alerts=[alert],
            summary={"total_time": "10.5s"},
        )

        formatted = report.format()

        assert "PERFORMANCE REPORT" in formatted
        assert "SUMMARY" in formatted
        assert "ALERTS" in formatted
        assert "TRENDS" in formatted
        assert "METRICS" in formatted


class TestMetricsCollector:
    """Test MetricsCollector class."""

    def test_add_metric(self):
        """Test adding metrics."""
        collector = MetricsCollector()

        collector.add_metric(
            "test_metric",
            100.0,
            MetricType.GAUGE,
            tags={"env": "test"},
            unit="ms",
        )

        assert len(collector.metrics) == 1
        assert collector.metrics[0].name == "test_metric"
        assert collector.metrics[0].value == 100.0

    def test_get_metric_history(self):
        """Test getting metric history."""
        collector = MetricsCollector()

        # Add multiple values
        for i in range(5):
            collector.add_metric("test", float(i), MetricType.COUNTER)

        history = collector.get_metric_history("test")

        assert len(history) == 5
        assert history[-1].value == 4.0

    def test_get_latest_metric(self):
        """Test getting latest metric."""
        collector = MetricsCollector()

        collector.add_metric("test", 100.0, MetricType.GAUGE)
        collector.add_metric("test", 200.0, MetricType.GAUGE)

        latest = collector.get_latest_metric("test")

        assert latest is not None
        assert latest.value == 200.0

    def test_get_nonexistent_metric(self):
        """Test getting non-existent metric."""
        collector = MetricsCollector()

        latest = collector.get_latest_metric("nonexistent")

        assert latest is None

    def test_clear_metrics(self):
        """Test clearing metrics."""
        collector = MetricsCollector()

        collector.add_metric("test1", 100.0, MetricType.GAUGE)
        collector.add_metric("test2", 200.0, MetricType.GAUGE)

        assert len(collector.metrics) == 2

        collector.clear()

        assert len(collector.metrics) == 0


class TestMetricsVisualizer:
    """Test MetricsVisualizer class."""

    def test_create_ascii_chart(self):
        """Test creating ASCII chart."""
        visualizer = MetricsVisualizer()

        values = [10, 20, 30, 40, 50]
        chart = visualizer.create_ascii_chart(values, width=40, title="Test Chart")

        assert "Test Chart" in chart
        assert "10.00" in chart
        assert "50.00" in chart

    def test_create_ascii_chart_empty(self):
        """Test creating chart with no data."""
        visualizer = MetricsVisualizer()

        chart = visualizer.create_ascii_chart([])

        assert chart == "No data"

    def test_create_trend_chart(self):
        """Test creating trend chart."""
        visualizer = MetricsVisualizer()

        metrics = [
            Metric("test", 10.0, MetricType.GAUGE),
            Metric("test", 20.0, MetricType.GAUGE),
            Metric("test", 30.0, MetricType.GAUGE),
        ]

        chart = visualizer.create_trend_chart(metrics)

        assert "Trend: test" in chart

    def test_export_html(self, tmp_path):
        """Test exporting HTML report."""
        visualizer = MetricsVisualizer()

        report = PerformanceReport(
            metrics=[Metric("test", 100.0, MetricType.GAUGE)],
            summary={"key": "value"},
        )

        output_path = tmp_path / "report.html"
        visualizer.export_html(report, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "<html>" in content
        assert "Performance Report" in content


class TestPerformanceReporter:
    """Test PerformanceReporter class."""

    def test_initialization(self):
        """Test reporter initialization."""
        reporter = PerformanceReporter()

        assert reporter.collector is not None
        assert reporter.visualizer is not None
        assert len(reporter.alert_rules) > 0  # Default rules

    def test_add_alert_rule(self):
        """Test adding alert rule."""
        reporter = PerformanceReporter()

        initial_count = len(reporter.alert_rules)

        reporter.add_alert_rule(
            "test_metric",
            threshold=100.0,
            comparison=">",
            severity=AlertSeverity.WARNING,
            message_template="Test alert",
        )

        assert len(reporter.alert_rules) == initial_count + 1

    def test_collect_metrics_with_profiler(self):
        """Test collecting metrics from profiler."""
        reporter = PerformanceReporter()

        # Mock profiler
        profiler = MagicMock()
        mock_report = MagicMock()
        mock_report.total_time = 10.5
        mock_report.operation_count = 100
        profiler.get_report.return_value = mock_report

        reporter.collect_metrics(profiler=profiler)

        # Should have collected execution_time
        execution_time = reporter.collector.get_latest_metric("execution_time")
        assert execution_time is not None
        assert execution_time.value == 10.5

    def test_collect_metrics_with_cache(self):
        """Test collecting metrics from cache."""
        reporter = PerformanceReporter()

        # Mock cache
        cache = MagicMock()
        mock_stats = MagicMock()
        mock_stats.hit_rate = 0.75
        mock_stats.total_size_mb = 100.0
        mock_stats.entry_count = 500
        cache.get_stats.return_value = mock_stats

        reporter.collect_metrics(cache=cache)

        # Should have collected cache metrics
        hit_rate = reporter.collector.get_latest_metric("cache_hit_rate")
        assert hit_rate is not None
        assert hit_rate.value == 0.75

    def test_collect_metrics_with_memory_optimizer(self):
        """Test collecting metrics from memory optimizer."""
        reporter = PerformanceReporter()

        # Mock memory optimizer
        memory = MagicMock()
        mock_stats = MagicMock()
        mock_stats.peak_mb = 500.0
        mock_stats.current_mb = 300.0
        mock_stats.gc_collections = 10
        memory.get_stats.return_value = mock_stats

        reporter.collect_metrics(memory_optimizer=memory)

        # Should have collected memory metrics
        peak_memory = reporter.collector.get_latest_metric("peak_memory_mb")
        assert peak_memory is not None
        assert peak_memory.value == 500.0

    def test_set_baseline(self):
        """Test setting baseline metrics."""
        reporter = PerformanceReporter()

        baseline = {
            "execution_time": 100.0,
            "memory_usage": 500.0,
        }

        reporter.set_baseline(baseline)

        assert "execution_time" in reporter._baseline_metrics
        assert reporter._baseline_metrics["execution_time"] == 100.0

    def test_calculate_trends(self):
        """Test calculating trends."""
        reporter = PerformanceReporter()

        # Set baseline
        reporter.set_baseline(
            {
                "execution_time": 100.0,
                "memory_usage": 500.0,
            }
        )

        # Add current metrics
        reporter.collector.add_metric("execution_time", 80.0, MetricType.TIMING)
        reporter.collector.add_metric("memory_usage", 600.0, MetricType.GAUGE)

        trends = reporter.calculate_trends()

        assert len(trends) == 2

        # Find execution_time trend
        exec_trend = next(t for t in trends if t.metric_name == "execution_time")
        assert exec_trend.change_percentage == -20.0
        assert exec_trend.trend_direction == "down"

    def test_evaluate_alerts(self):
        """Test evaluating alerts."""
        reporter = PerformanceReporter()

        # Add metric that triggers alert
        reporter.collector.add_metric("peak_memory_mb", 1500.0, MetricType.GAUGE)

        alerts = reporter.evaluate_alerts()

        # Should trigger the default memory alert
        assert len(alerts) > 0
        memory_alerts = [a for a in alerts if a.metric_name == "peak_memory_mb"]
        assert len(memory_alerts) > 0

    def test_generate_report(self):
        """Test generating performance report."""
        reporter = PerformanceReporter()

        # Add some metrics
        reporter.collector.add_metric("test1", 100.0, MetricType.GAUGE)
        reporter.collector.add_metric("test2", 200.0, MetricType.COUNTER)

        report = reporter.generate_report()

        assert isinstance(report, PerformanceReport)
        assert len(report.metrics) == 2
        assert "total_alerts" in report.summary

    def test_save_report_json(self, tmp_path):
        """Test saving report as JSON."""
        reporter = PerformanceReporter()
        reporter.collector.add_metric("test", 100.0, MetricType.GAUGE)

        report = reporter.generate_report()
        output_path = tmp_path / "report.json"

        reporter.save_report(report, output_path, format="json")

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "metrics" in data

    def test_save_report_html(self, tmp_path):
        """Test saving report as HTML."""
        reporter = PerformanceReporter()
        reporter.collector.add_metric("test", 100.0, MetricType.GAUGE)

        report = reporter.generate_report()
        output_path = tmp_path / "report.html"

        reporter.save_report(report, output_path, format="html")

        assert output_path.exists()
        content = output_path.read_text()
        assert "<html>" in content

    def test_save_report_text(self, tmp_path):
        """Test saving report as text."""
        reporter = PerformanceReporter()
        reporter.collector.add_metric("test", 100.0, MetricType.GAUGE)

        report = reporter.generate_report()
        output_path = tmp_path / "report.txt"

        reporter.save_report(report, output_path, format="text")

        assert output_path.exists()
        content = output_path.read_text()
        assert "PERFORMANCE REPORT" in content


class TestIntegration:
    """Test reporter integration."""

    def test_full_reporting_workflow(self):
        """Test complete reporting workflow."""
        reporter = PerformanceReporter()

        # Set baseline
        reporter.set_baseline(
            {
                "execution_time": 100.0,
                "cache_hit_rate": 0.5,
            }
        )

        # Mock components
        profiler = MagicMock()
        mock_prof_report = MagicMock()
        mock_prof_report.total_time = 80.0
        mock_prof_report.operation_count = 150
        profiler.get_report.return_value = mock_prof_report

        cache = MagicMock()
        mock_cache_stats = MagicMock()
        mock_cache_stats.hit_rate = 0.75
        mock_cache_stats.total_size_mb = 50.0
        mock_cache_stats.entry_count = 100
        cache.get_stats.return_value = mock_cache_stats

        # Collect metrics
        reporter.collect_metrics(profiler=profiler, cache=cache)

        # Generate report
        report = reporter.generate_report()

        # Verify report
        assert len(report.metrics) > 0
        assert len(report.trends) > 0  # Should have trends from baseline
        assert "execution_time" in report.summary or "cache_hit_rate" in report.summary


def test_create_performance_reporter():
    """Test reporter factory function."""
    reporter = create_performance_reporter()

    assert isinstance(reporter, PerformanceReporter)
    assert reporter.collector is not None
    assert reporter.visualizer is not None
