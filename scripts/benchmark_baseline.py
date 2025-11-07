#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Baseline Performance Benchmark Script

This script establishes baseline performance metrics for the Repository Reporting System.
It runs the report generation with various repository counts and records timing,
memory usage, and operation statistics.

Usage:
    python scripts/benchmark_baseline.py --output baseline.json
    python scripts/benchmark_baseline.py --small-only
    python scripts/benchmark_baseline.py --compare baseline.json

Outputs:
    - JSON file with detailed performance metrics
    - Text report with human-readable summary
    - Comparison to previous baseline (if provided)
"""

import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from performance import PerformanceProfiler, ProfileReport


def setup_test_repositories(count: int, temp_dir: str) -> list[str]:
    """
    Create mock repository directories for testing.

    Args:
        count: Number of repositories to create
        temp_dir: Temporary directory for repos

    Returns:
        List of repository paths
    """
    repos = []
    base_path = Path(temp_dir)
    base_path.mkdir(parents=True, exist_ok=True)

    for i in range(count):
        repo_name = f"test-repo-{i:03d}"
        repo_path = base_path / repo_name
        repo_path.mkdir(exist_ok=True)

        # Create minimal git structure
        git_dir = repo_path / ".git"
        git_dir.mkdir(exist_ok=True)

        # Create some dummy files
        (repo_path / "README.md").write_text(f"# {repo_name}\n\nTest repository {i}")
        (repo_path / "src").mkdir(exist_ok=True)
        (repo_path / "src" / "main.py").write_text(f"# Main file for {repo_name}\n")

        repos.append(str(repo_path))

    return repos


def simulate_repository_analysis(
    repo_paths: list[str], profiler: PerformanceProfiler
) -> dict[str, Any]:
    """
    Simulate analyzing repositories with profiling.

    Args:
        repo_paths: List of repository paths
        profiler: Performance profiler

    Returns:
        Dictionary of analysis results
    """
    results = {
        "total_repos": len(repo_paths),
        "successful": 0,
        "failed": 0,
        "total_files": 0,
        "total_lines": 0,
    }

    for i, _repo_path in enumerate(repo_paths):
        profiler.memory_snapshot(f"before_repo_{i}")

        # Simulate git operations
        with profiler.track_operation(f"git_clone_{i}", category="git"):
            time.sleep(0.01)  # Simulate clone time

        with profiler.track_operation(f"git_log_{i}", category="git"):
            time.sleep(0.005)  # Simulate log fetch

        # Simulate file analysis
        with profiler.track_operation(f"analyze_structure_{i}", category="analysis"):
            time.sleep(0.02)  # Simulate structure analysis
            results["total_files"] += 2
            results["total_lines"] += 100

        # Simulate code quality checks
        with profiler.track_operation(f"quality_check_{i}", category="analysis"):
            time.sleep(0.015)  # Simulate quality checks

        # Simulate API calls
        with profiler.track_operation(f"api_fetch_{i}", category="api"):
            time.sleep(0.01)  # Simulate API request

        profiler.memory_snapshot(f"after_repo_{i}")
        results["successful"] += 1

    # Simulate report rendering
    with profiler.track_operation("render_json", category="rendering"):
        time.sleep(0.005)

    with profiler.track_operation("render_markdown", category="rendering"):
        time.sleep(0.01)

    with profiler.track_operation("render_html", category="rendering"):
        time.sleep(0.015)

    return results


def run_benchmark(repo_count: int, profiler_name: str) -> ProfileReport:
    """
    Run benchmark for a specific repository count.

    Args:
        repo_count: Number of repositories to analyze
        profiler_name: Name for the profiler

    Returns:
        Performance report
    """
    print(f"\n{'=' * 70}")
    print(f"Running benchmark: {repo_count} repositories")
    print(f"{'=' * 70}")

    # Create profiler
    profiler = PerformanceProfiler(name=profiler_name)

    # Setup test repositories
    temp_dir = tempfile.mkdtemp(prefix="benchmark_")

    try:
        print("Setting up test repositories...")
        with profiler.track_operation("setup_repos", category="io"):
            repos = setup_test_repositories(repo_count, temp_dir)

        # Start profiling
        profiler.start()
        print(f"Analyzing {repo_count} repositories...")

        # Run analysis
        results = simulate_repository_analysis(repos, profiler)

        # Stop profiling
        profiler.stop()

        # Record custom metrics
        profiler.record_metric("repository_count", repo_count, "repos")
        profiler.record_metric("total_files", results["total_files"], "files")
        profiler.record_metric("total_lines", results["total_lines"], "lines")
        profiler.record_metric(
            "success_rate", results["successful"] / results["total_repos"] * 100, "%"
        )

        # Generate report
        report = profiler.get_report()

        # Print summary
        print(f"\n{'=' * 70}")
        print(f"Benchmark Results: {repo_count} repositories")
        print(f"{'=' * 70}")
        print(report.format())

        return report

    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def save_baseline(reports: dict[str, ProfileReport], output_path: str):
    """
    Save baseline reports to file.

    Args:
        reports: Dictionary of benchmark name to report
        output_path: Output file path
    """
    baseline_data = {
        "timestamp": time.time(),
        "benchmarks": {name: report.to_dict() for name, report in reports.items()},
    }

    with open(output_path, "w") as f:
        json.dump(baseline_data, f, indent=2)

    print(f"\n✓ Baseline saved to: {output_path}")


def compare_to_baseline(current_reports: dict[str, ProfileReport], baseline_path: str):
    """
    Compare current results to baseline.

    Args:
        current_reports: Current benchmark reports
        baseline_path: Path to baseline JSON file
    """
    print(f"\n{'=' * 70}")
    print("Comparison to Baseline")
    print(f"{'=' * 70}")

    with open(baseline_path) as f:
        baseline_data = json.load(f)

    for name, current_report in current_reports.items():
        if name not in baseline_data["benchmarks"]:
            print(f"\n⚠️  No baseline found for: {name}")
            continue

        baseline = baseline_data["benchmarks"][name]
        current = current_report.to_dict()

        baseline_duration = baseline.get("total_duration", 0)
        current_duration = current.get("total_duration", 0)

        if baseline_duration > 0:
            change_pct = ((current_duration - baseline_duration) / baseline_duration) * 100

            print(f"\n{name}:")
            print(f"  Baseline: {baseline_duration:.2f}s")
            print(f"  Current:  {current_duration:.2f}s")

            if change_pct < 0:
                print(f"  Change:   {change_pct:.1f}% ✓ (faster)")
            elif change_pct > 10:
                print(f"  Change:   +{change_pct:.1f}% ⚠️  (slower)")
            else:
                print(f"  Change:   +{change_pct:.1f}% (similar)")


def main():
    """Main benchmark script."""
    parser = argparse.ArgumentParser(description="Run baseline performance benchmarks")
    parser.add_argument(
        "--output",
        default="baseline.json",
        help="Output file for baseline (default: baseline.json)",
    )
    parser.add_argument("--compare", help="Compare to existing baseline file")
    parser.add_argument(
        "--small-only", action="store_true", help="Run only small benchmark (10 repos)"
    )
    parser.add_argument("--large", action="store_true", help="Include large benchmark (50 repos)")

    args = parser.parse_args()

    print("=" * 70)
    print("Repository Reporting System - Baseline Performance Benchmark")
    print("=" * 70)

    # Define benchmark sizes
    benchmarks = []

    if args.small_only:
        benchmarks = [
            ("small", 10),
        ]
    elif args.large:
        benchmarks = [
            ("small", 10),
            ("medium", 25),
            ("large", 50),
        ]
    else:
        benchmarks = [
            ("small", 10),
            ("medium", 25),
        ]

    # Run benchmarks
    reports = {}

    for name, count in benchmarks:
        profiler_name = f"baseline_{name}_{count}repos"
        report = run_benchmark(count, profiler_name)
        reports[name] = report

    # Save baseline
    save_baseline(reports, args.output)

    # Compare if requested
    if args.compare:
        if os.path.exists(args.compare):
            compare_to_baseline(reports, args.compare)
        else:
            print(f"\n⚠️  Baseline file not found: {args.compare}")

    print(f"\n{'=' * 70}")
    print("Benchmark Complete")
    print(f"{'=' * 70}")

    # Summary
    print("\nSummary:")
    for name, report in reports.items():
        data = report.to_dict()
        duration = data.get("total_duration", 0)
        repo_count = data.get("custom_metrics", {}).get("repository_count", {}).get("value", 0)
        print(
            f"  {name.capitalize()}: {repo_count} repos in {duration:.2f}s ({duration / repo_count:.2f}s per repo)"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
