# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Performance monitoring and reporting module.

This module provides utilities for generating performance reports, visualizing metrics,
tracking trends, and comparing performance against baselines.

Classes:
    PerformanceReporter: Main performance reporting coordinator
    MetricsCollector: Collects metrics from all performance components
    MetricsVisualizer: Visualizes performance metrics
    PerformanceReport: Performance report data structure
    MetricTrend: Trend analysis for metrics
    AlertRule: Performance alert rules

Example:
    >>> from src.performance.reporter import PerformanceReporter
    >>> reporter = PerformanceReporter()
    >>> reporter.collect_metrics()
    >>> report = reporter.generate_report()
    >>> print(report.format())
"""

import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric types."""
    TIMING = "timing"
    COUNTER = "counter"
    GAUGE = "gauge"
    RATE = "rate"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "unit": self.unit,
        }


@dataclass
class MetricTrend:
    """Trend analysis for a metric."""
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # "up", "down", "stable"
    is_improvement: bool

    def format(self) -> str:
        """Format trend as string."""
        arrow = "↑" if self.trend_direction == "up" else "↓" if self.trend_direction == "down" else "→"
        color = "✅" if self.is_improvement else "⚠️" if abs(self.change_percentage) > 5 else "ℹ️"

        return (
            f"{color} {self.metric_name}: {self.current_value:.2f} "
            f"({arrow} {self.change_percentage:+.1f}%)"
        )


@dataclass
class Alert:
    """Performance alert."""
    severity: AlertSeverity
    metric_name: str
    message: str
    value: float
    threshold: float
    timestamp: float = field(default_factory=time.time)

    def format(self) -> str:
        """Format alert as string."""
        severity_icons = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨",
        }
        icon = severity_icons.get(self.severity, "•")
        return f"{icon} [{self.severity.value.upper()}] {self.metric_name}: {self.message}"


@dataclass
class AlertRule:
    """Alert rule definition."""
    metric_name: str
    threshold: float
    comparison: str  # ">", "<", ">=", "<=", "=="
    severity: AlertSeverity
    message_template: str

    def evaluate(self, value: float) -> Optional[Alert]:
        """Evaluate rule against value."""
        triggered = False

        if self.comparison == ">":
            triggered = value > self.threshold
        elif self.comparison == "<":
            triggered = value < self.threshold
        elif self.comparison == ">=":
            triggered = value >= self.threshold
        elif self.comparison == "<=":
            triggered = value <= self.threshold
        elif self.comparison == "==":
            triggered = value == self.threshold

        if triggered:
            message = self.message_template.format(
                value=value,
                threshold=self.threshold,
            )
            return Alert(
                severity=self.severity,
                metric_name=self.metric_name,
                message=message,
                value=value,
                threshold=self.threshold,
            )

        return None


@dataclass
class PerformanceReport:
    """Performance report data structure."""
    generated_at: float = field(default_factory=time.time)
    metrics: List[Metric] = field(default_factory=list)
    trends: List[MetricTrend] = field(default_factory=list)
    alerts: List[Alert] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "generated_at": self.generated_at,
            "generated_at_iso": datetime.fromtimestamp(self.generated_at).isoformat(),
            "metrics": [m.to_dict() for m in self.metrics],
            "trends": [
                {
                    "metric_name": t.metric_name,
                    "current_value": t.current_value,
                    "previous_value": t.previous_value,
                    "change_percentage": t.change_percentage,
                    "trend_direction": t.trend_direction,
                    "is_improvement": t.is_improvement,
                }
                for t in self.trends
            ],
            "alerts": [
                {
                    "severity": a.severity.value,
                    "metric_name": a.metric_name,
                    "message": a.message,
                    "value": a.value,
                    "threshold": a.threshold,
                }
                for a in self.alerts
            ],
            "summary": self.summary,
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def format(self) -> str:
        """Format report as string."""
        lines = [
            "=" * 80,
            "PERFORMANCE REPORT",
            "=" * 80,
            f"Generated: {datetime.fromtimestamp(self.generated_at).strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        # Summary section
        if self.summary:
            lines.append("SUMMARY")
            lines.append("-" * 80)
            for key, value in self.summary.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        # Alerts section
        if self.alerts:
            lines.append("ALERTS")
            lines.append("-" * 80)
            for alert in sorted(self.alerts, key=lambda a: a.severity.value, reverse=True):
                lines.append(f"  {alert.format()}")
            lines.append("")

        # Trends section
        if self.trends:
            lines.append("TRENDS")
            lines.append("-" * 80)
            for trend in self.trends:
                lines.append(f"  {trend.format()}")
            lines.append("")

        # Metrics section
        if self.metrics:
            lines.append("METRICS")
            lines.append("-" * 80)

            # Group by type
            metrics_by_type = defaultdict(list)
            for metric in self.metrics:
                metrics_by_type[metric.metric_type].append(metric)

            for metric_type, metrics in metrics_by_type.items():
                lines.append(f"  {metric_type.value.upper()}:")
                for metric in sorted(metrics, key=lambda m: m.name):
                    unit_str = f" {metric.unit}" if metric.unit else ""
                    lines.append(f"    {metric.name}: {metric.value:.2f}{unit_str}")
                lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)


class MetricsCollector:
    """Collects metrics from all performance components."""

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: List[Metric] = []
        self._metric_history: Dict[str, deque[Metric]] = defaultdict(lambda: deque(maxlen=100))

    def add_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
        unit: str = "",
    ) -> None:
        """
        Add a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Metric tags
            unit: Unit of measurement
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            unit=unit,
        )

        self.metrics.append(metric)
        self._metric_history[name].append(metric)

    def get_metric_history(self, name: str) -> List[Metric]:
        """Get metric history."""
        return list(self._metric_history.get(name, []))

    def get_latest_metric(self, name: str) -> Optional[Metric]:
        """Get latest metric value."""
        history = list(self._metric_history.get(name, []))
        return history[-1] if history else None

    def clear(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()


class MetricsVisualizer:
    """Visualizes performance metrics."""

    def __init__(self):
        """Initialize metrics visualizer."""
        pass

    def create_ascii_chart(
        self,
        values: List[float],
        width: int = 60,
        height: int = 10,
        title: str = "",
    ) -> str:
        """
        Create ASCII bar chart.

        Args:
            values: Values to chart
            width: Chart width
            height: Chart height
            title: Chart title

        Returns:
            ASCII chart string
        """
        if not values:
            return "No data"

        lines = []

        if title:
            lines.append(title)
            lines.append("-" * width)

        max_val = max(values)
        min_val = min(values)
        range_val = max_val - min_val if max_val != min_val else 1

        # Create bars
        for i, value in enumerate(values):
            normalized = (value - min_val) / range_val
            bar_length = int(normalized * (width - 20))
            bar = "█" * bar_length
            lines.append(f"{i:3d} | {bar} {value:.2f}")

        return "\n".join(lines)

    def create_trend_chart(
        self,
        metrics: List[Metric],
        width: int = 60,
        height: int = 10,
    ) -> str:
        """
        Create ASCII trend chart.

        Args:
            metrics: Metrics to chart
            width: Chart width
            height: Chart height

        Returns:
            ASCII chart string
        """
        if not metrics:
            return "No data"

        values = [m.value for m in metrics]
        return self.create_ascii_chart(values, width, height, f"Trend: {metrics[0].name}")

    def export_html(
        self,
        report: PerformanceReport,
        output_path: Union[str, Path],
    ) -> None:
        """
        Export report as HTML.

        Args:
            report: Performance report
            output_path: Output file path
        """
        output_path = Path(output_path)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Performance Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        .metric {{
            background-color: #f9f9f9;
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #4CAF50;
        }}
        .alert {{
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #ff9800;
            background-color: #fff3cd;
        }}
        .alert.error {{
            border-left-color: #f44336;
            background-color: #ffebee;
        }}
        .trend {{
            padding: 10px;
            margin: 5px 0;
            background-color: #e3f2fd;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #2196F3;
        }}
        .timestamp {{
            color: #777;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Performance Report</h1>
        <p class="timestamp">Generated: {datetime.fromtimestamp(report.generated_at).strftime('%Y-%m-%d %H:%M:%S')}</p>

        <h2>Summary</h2>
        <div class="summary">
"""

        for key, value in report.summary.items():
            html += f"""
            <div class="summary-card">
                <strong>{key}</strong><br>
                {value}
            </div>
"""

        html += """
        </div>

        <h2>Alerts</h2>
"""

        if report.alerts:
            for alert in report.alerts:
                alert_class = "error" if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL] else ""
                html += f"""
        <div class="alert {alert_class}">
            <strong>{alert.severity.value.upper()}</strong>: {alert.message}
        </div>
"""
        else:
            html += "<p>No alerts</p>"

        html += """
        <h2>Trends</h2>
"""

        if report.trends:
            for trend in report.trends:
                html += f"""
        <div class="trend">
            {trend.format()}
        </div>
"""
        else:
            html += "<p>No trends available</p>"

        html += """
        <h2>Metrics</h2>
"""

        for metric in report.metrics:
            unit_str = f" {metric.unit}" if metric.unit else ""
            html += f"""
        <div class="metric">
            <strong>{metric.name}</strong>: {metric.value:.2f}{unit_str}
            <span style="color: #777; font-size: 0.9em;">({metric.metric_type.value})</span>
        </div>
"""

        html += """
    </div>
</body>
</html>
"""

        output_path.write_text(html)
        logger.info(f"HTML report saved to {output_path}")


class PerformanceReporter:
    """Main performance reporting coordinator."""

    def __init__(self):
        """Initialize performance reporter."""
        self.collector = MetricsCollector()
        self.visualizer = MetricsVisualizer()
        self.alert_rules: List[AlertRule] = []
        self._baseline_metrics: Dict[str, float] = {}

        # Default alert rules
        self._add_default_rules()

        logger.info("Performance reporter initialized")

    def _add_default_rules(self) -> None:
        """Add default alert rules."""
        # Memory alerts
        self.add_alert_rule(
            "peak_memory_mb",
            threshold=1000,
            comparison=">",
            severity=AlertSeverity.WARNING,
            message_template="Peak memory usage ({value:.1f} MB) exceeds threshold ({threshold:.1f} MB)",
        )

        # Execution time alerts
        self.add_alert_rule(
            "execution_time",
            threshold=300,
            comparison=">",
            severity=AlertSeverity.WARNING,
            message_template="Execution time ({value:.1f}s) exceeds threshold ({threshold:.1f}s)",
        )

        # Cache hit rate alerts
        self.add_alert_rule(
            "cache_hit_rate",
            threshold=0.3,
            comparison="<",
            severity=AlertSeverity.INFO,
            message_template="Cache hit rate ({value:.1%}) is below target ({threshold:.1%})",
        )

    def add_alert_rule(
        self,
        metric_name: str,
        threshold: float,
        comparison: str,
        severity: AlertSeverity,
        message_template: str,
    ) -> None:
        """Add an alert rule."""
        rule = AlertRule(
            metric_name=metric_name,
            threshold=threshold,
            comparison=comparison,
            severity=severity,
            message_template=message_template,
        )
        self.alert_rules.append(rule)

    def collect_metrics(
        self,
        profiler=None,
        cache=None,
        memory_optimizer=None,
        batch_processor=None,
    ) -> None:
        """
        Collect metrics from performance components.

        Args:
            profiler: PerformanceProfiler instance
            cache: CacheManager instance
            memory_optimizer: MemoryOptimizer instance
            batch_processor: BatchProcessor instance
        """
        # Collect from profiler
        if profiler:
            try:
                report = profiler.get_report()

                if hasattr(report, 'total_time'):
                    self.collector.add_metric(
                        "execution_time",
                        report.total_time,
                        MetricType.TIMING,
                        unit="s",
                    )

                if hasattr(report, 'operation_count'):
                    self.collector.add_metric(
                        "total_operations",
                        report.operation_count,
                        MetricType.COUNTER,
                    )
            except Exception as e:
                logger.warning(f"Failed to collect profiler metrics: {e}")

        # Collect from cache
        if cache:
            try:
                stats = cache.get_stats()

                self.collector.add_metric(
                    "cache_hit_rate",
                    stats.hit_rate,
                    MetricType.GAUGE,
                )

                self.collector.add_metric(
                    "cache_size_mb",
                    stats.total_size_mb,
                    MetricType.GAUGE,
                    unit="MB",
                )

                self.collector.add_metric(
                    "cache_entries",
                    stats.entry_count,
                    MetricType.GAUGE,
                )
            except Exception as e:
                logger.warning(f"Failed to collect cache metrics: {e}")

        # Collect from memory optimizer
        if memory_optimizer:
            try:
                stats = memory_optimizer.get_stats()

                self.collector.add_metric(
                    "peak_memory_mb",
                    stats.peak_mb,
                    MetricType.GAUGE,
                    unit="MB",
                )

                self.collector.add_metric(
                    "current_memory_mb",
                    stats.current_mb,
                    MetricType.GAUGE,
                    unit="MB",
                )

                self.collector.add_metric(
                    "gc_collections",
                    stats.gc_collections,
                    MetricType.COUNTER,
                )
            except Exception as e:
                logger.warning(f"Failed to collect memory metrics: {e}")

        # Collect from batch processor
        if batch_processor:
            try:
                rate_limit_info = batch_processor.get_rate_limit_info()

                self.collector.add_metric(
                    "rate_limit_remaining",
                    rate_limit_info.remaining,
                    MetricType.GAUGE,
                )

                self.collector.add_metric(
                    "rate_limit_usage",
                    rate_limit_info.usage_percentage,
                    MetricType.GAUGE,
                )
            except Exception as e:
                logger.warning(f"Failed to collect batch processor metrics: {e}")

    def set_baseline(self, metrics: Dict[str, float]) -> None:
        """Set baseline metrics for comparison."""
        self._baseline_metrics = metrics.copy()
        logger.info(f"Baseline set with {len(metrics)} metrics")

    def calculate_trends(self) -> List[MetricTrend]:
        """Calculate trends by comparing to baseline."""
        trends = []

        for metric in self.collector.metrics:
            if metric.name in self._baseline_metrics:
                baseline_value = self._baseline_metrics[metric.name]
                current_value = metric.value

                if baseline_value == 0:
                    change_percentage = 0.0
                else:
                    change_percentage = ((current_value - baseline_value) / baseline_value) * 100

                # Determine trend direction
                if abs(change_percentage) < 1:
                    trend_direction = "stable"
                elif change_percentage > 0:
                    trend_direction = "up"
                else:
                    trend_direction = "down"

                # Determine if improvement (depends on metric)
                improvement_metrics = {
                    "cache_hit_rate": "up",
                    "execution_time": "down",
                    "peak_memory_mb": "down",
                    "current_memory_mb": "down",
                }

                desired_direction = improvement_metrics.get(metric.name, "stable")
                is_improvement = (
                    trend_direction == desired_direction or
                    trend_direction == "stable"
                )

                trend = MetricTrend(
                    metric_name=metric.name,
                    current_value=current_value,
                    previous_value=baseline_value,
                    change_percentage=change_percentage,
                    trend_direction=trend_direction,
                    is_improvement=is_improvement,
                )

                trends.append(trend)

        return trends

    def evaluate_alerts(self) -> List[Alert]:
        """Evaluate alert rules against metrics."""
        alerts = []

        for metric in self.collector.metrics:
            for rule in self.alert_rules:
                if rule.metric_name == metric.name:
                    alert = rule.evaluate(metric.value)
                    if alert:
                        alerts.append(alert)

        return alerts

    def generate_report(self) -> PerformanceReport:
        """Generate performance report."""
        trends = self.calculate_trends()
        alerts = self.evaluate_alerts()

        # Generate summary
        summary = {}

        # Add key metrics to summary
        for metric in self.collector.metrics:
            if metric.name in ["execution_time", "peak_memory_mb", "cache_hit_rate"]:
                unit_str = f" {metric.unit}" if metric.unit else ""
                summary[metric.name] = f"{metric.value:.2f}{unit_str}"

        # Add alert count
        summary["total_alerts"] = str(len(alerts))
        summary["critical_alerts"] = str(sum(
            1 for a in alerts if a.severity == AlertSeverity.CRITICAL
        ))

        report = PerformanceReport(
            metrics=self.collector.metrics.copy(),
            trends=trends,
            alerts=alerts,
            summary=summary,
        )

        logger.info(
            f"Generated report with {len(report.metrics)} metrics, "
            f"{len(report.trends)} trends, {len(report.alerts)} alerts"
        )

        return report

    def save_report(
        self,
        report: PerformanceReport,
        output_path: Union[str, Path],
        format: str = "json",
    ) -> None:
        """
        Save report to file.

        Args:
            report: Performance report
            output_path: Output file path
            format: Output format ("json", "html", "text")
        """
        output_path = Path(output_path)

        if format == "json":
            output_path.write_text(report.to_json())
        elif format == "html":
            self.visualizer.export_html(report, output_path)
        elif format == "text":
            output_path.write_text(report.format())
        else:
            raise ValueError(f"Unknown format: {format}")

        logger.info(f"Report saved to {output_path} ({format})")


def create_performance_reporter() -> PerformanceReporter:
    """
    Create performance reporter with default settings.

    Returns:
        Configured performance reporter
    """
    return PerformanceReporter()
