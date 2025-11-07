# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
API statistics tracking for the reporting-tool package.

This module provides statistics tracking for API calls to external services
(GitHub, Gerrit, Jenkins) including success/error counts and performance metrics.
"""

import os
import threading
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class APIStatistics:
    """
    Thread-safe statistics tracker for API calls.

    Tracks successful calls, errors, and exceptions for multiple API services
    (GitHub, Gerrit, Jenkins) with thread-safe counters.
    """

    def __init__(self):
        """Initialize API statistics tracking."""
        self._lock = threading.Lock()
        self._stats: Dict[str, Dict[str, int]] = {
            'github': {'success': 0, 'error': 0, 'exception': 0},
            'gerrit': {'success': 0, 'error': 0, 'exception': 0},
            'jenkins': {'success': 0, 'error': 0, 'exception': 0},
        }
        self._info_master_fetched = False

    def record_success(self, service: str) -> None:
        """
        Record a successful API call.

        Args:
            service: Service name ('github', 'gerrit', 'jenkins')
        """
        with self._lock:
            if service in self._stats:
                self._stats[service]['success'] += 1

    def record_error(self, service: str, status_code: Optional[int] = None) -> None:
        """
        Record an API error (non-2xx response).

        Args:
            service: Service name ('github', 'gerrit', 'jenkins')
            status_code: HTTP status code (optional)
        """
        with self._lock:
            if service in self._stats:
                self._stats[service]['error'] += 1
                logger.debug(f"{service} API error: {status_code}")

    def record_exception(self, service: str, exception: Exception) -> None:
        """
        Record an API exception (connection failure, timeout, etc.).

        Args:
            service: Service name ('github', 'gerrit', 'jenkins')
            exception: Exception that occurred
        """
        with self._lock:
            if service in self._stats:
                self._stats[service]['exception'] += 1
                logger.debug(f"{service} API exception: {type(exception).__name__}")

    def record_info_master(self, fetched: bool) -> None:
        """
        Record whether info-master repository was fetched.

        Args:
            fetched: True if info-master was successfully fetched
        """
        with self._lock:
            self._info_master_fetched = fetched

    def get_total_calls(self, service: str) -> int:
        """
        Get total number of API calls for a service.

        Args:
            service: Service name ('github', 'gerrit', 'jenkins')

        Returns:
            Total number of calls (success + error + exception)
        """
        with self._lock:
            if service in self._stats:
                stats = self._stats[service]
                return stats['success'] + stats['error'] + stats['exception']
            return 0

    def get_total_errors(self, service: str) -> int:
        """
        Get total number of errors and exceptions for a service.

        Args:
            service: Service name ('github', 'gerrit', 'jenkins')

        Returns:
            Total number of errors (error + exception)
        """
        with self._lock:
            if service in self._stats:
                stats = self._stats[service]
                return stats['error'] + stats['exception']
            return 0

    def has_errors(self) -> bool:
        """
        Check if any API has errors.

        Returns:
            True if any service has errors or exceptions
        """
        with self._lock:
            for service_stats in self._stats.values():
                if service_stats['error'] > 0 or service_stats['exception'] > 0:
                    return True
            return False

    def _get_snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of current statistics (thread-safe).

        Returns:
            Copy of statistics dictionary
        """
        with self._lock:
            return {
                'stats': {k: v.copy() for k, v in self._stats.items()},
                'info_master_fetched': self._info_master_fetched
            }

    def format_console_output(self) -> str:
        """
        Format statistics for console output.

        Returns:
            Formatted string for console display, or empty string if no calls made
        """
        snapshot = self._get_snapshot()
        stats = snapshot['stats']

        # Check if any calls were made
        has_calls = any(
            s['success'] + s['error'] + s['exception'] > 0
            for s in stats.values()
        )

        if not has_calls:
            return ""

        lines = ["\n📊 API Call Statistics:"]

        for service, service_stats in stats.items():
            total = service_stats['success'] + service_stats['error'] + service_stats['exception']
            if total > 0:
                success = service_stats['success']
                error = service_stats['error']
                exception = service_stats['exception']

                # Calculate success rate
                success_rate = (success / total * 100) if total > 0 else 0

                # Format status indicator
                if error + exception == 0:
                    status = "✅"
                elif success > error + exception:
                    status = "⚠️"
                else:
                    status = "❌"

                lines.append(
                    f"   {status} {service.capitalize()}: {total} calls "
                    f"({success} success, {error} errors, {exception} exceptions) "
                    f"- {success_rate:.1f}% success rate"
                )

        # Add info-master status if relevant
        if snapshot['info_master_fetched']:
            lines.append("   ✅ Info-master repository fetched")

        return "\n".join(lines)

    def write_to_step_summary(self) -> None:
        """
        Write statistics to GitHub Actions step summary.

        Writes a formatted table of API statistics to the GITHUB_STEP_SUMMARY
        file for visibility in GitHub Actions workflow runs.
        """
        step_summary = os.getenv("GITHUB_STEP_SUMMARY")
        if not step_summary:
            return

        snapshot = self._get_snapshot()
        stats = snapshot['stats']

        # Check if any calls were made
        has_calls = any(
            s['success'] + s['error'] + s['exception'] > 0
            for s in stats.values()
        )

        if not has_calls:
            return

        try:
            with open(step_summary, 'a') as f:
                f.write("\n## 📊 API Call Statistics\n\n")
                f.write("| Service | Total Calls | Success | Errors | Exceptions | Success Rate |\n")
                f.write("|---------|-------------|---------|--------|------------|-------------|\n")

                for service, service_stats in stats.items():
                    total = service_stats['success'] + service_stats['error'] + service_stats['exception']
                    if total > 0:
                        success = service_stats['success']
                        error = service_stats['error']
                        exception = service_stats['exception']
                        success_rate = (success / total * 100) if total > 0 else 0

                        # Status emoji
                        if error + exception == 0:
                            status = "✅"
                        elif success > error + exception:
                            status = "⚠️"
                        else:
                            status = "❌"

                        f.write(
                            f"| {status} {service.capitalize()} | {total} | {success} | "
                            f"{error} | {exception} | {success_rate:.1f}% |\n"
                        )

                if snapshot['info_master_fetched']:
                    f.write("\n**Info-master repository:** ✅ Fetched successfully\n")

                f.write("\n")

        except Exception as e:
            logger.warning(f"Failed to write API statistics to step summary: {e}")

    def get_summary_dict(self) -> Dict[str, Any]:
        """
        Get statistics as a dictionary for JSON serialization.

        Returns:
            Dictionary with statistics data
        """
        snapshot = self._get_snapshot()
        stats = snapshot['stats']

        summary = {
            'services': {},
            'info_master_fetched': snapshot['info_master_fetched'],
            'timestamp': datetime.now().isoformat()
        }

        for service, service_stats in stats.items():
            total = service_stats['success'] + service_stats['error'] + service_stats['exception']
            if total > 0:
                success_rate = (service_stats['success'] / total * 100) if total > 0 else 0
                summary['services'][service] = {
                    'total_calls': total,
                    'success': service_stats['success'],
                    'errors': service_stats['error'],
                    'exceptions': service_stats['exception'],
                    'success_rate': round(success_rate, 2)
                }

        return summary
