#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Performance profiling script for repository reporting system.

This script profiles the report generation process with different concurrency
settings to identify bottlenecks and establish baseline performance metrics.

Usage:
    python scripts/profile_performance.py --config config.json
    python scripts/profile_performance.py --config config.json --workers 1,4,8,16
    python scripts/profile_performance.py --config config.json --profile-output profile.prof
"""

import argparse
import cProfile
import json
import pstats
import sys
import time
from io import StringIO
from pathlib import Path
from typing import Any


# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_config(config_path: Path) -> dict[str, Any]:
    """Load configuration file."""
    with open(config_path) as f:
        return json.load(f)


def save_config(config: dict[str, Any], config_path: Path) -> None:
    """Save configuration file."""
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def run_with_profiling(
    config_path: Path, max_workers: int, profile_output: Path = None
) -> dict[str, Any]:
    """Run report generation with profiling enabled."""
    # Import here to avoid circular dependencies
    from generate_reports import RepositoryReporter

    # Load config and update max_workers
    config = load_config(config_path)
    if "performance" not in config:
        config["performance"] = {}
    config["performance"]["max_workers"] = max_workers

    # Create temporary config file
    temp_config = config_path.parent / f"temp_config_workers_{max_workers}.json"
    save_config(config, temp_config)

    print(f"\n{'=' * 80}")
    print(f"Profiling with max_workers={max_workers}")
    print(f"{'=' * 80}\n")

    # Create profiler
    profiler = cProfile.Profile()

    # Start timing
    start_time = time.time()
    start_cpu = time.process_time()

    # Run with profiling
    profiler.enable()
    try:
        reporter = RepositoryReporter(str(temp_config))
        reporter.generate_all_reports()
    finally:
        profiler.disable()

    # End timing
    end_time = time.time()
    end_cpu = time.process_time()

    # Calculate metrics
    wall_time = end_time - start_time
    cpu_time = end_cpu - start_cpu

    # Clean up temp config
    if temp_config.exists():
        temp_config.unlink()

    # Generate profile stats
    stats = pstats.Stats(profiler)

    # Save profile if requested
    if profile_output:
        profile_file = (
            profile_output.parent
            / f"{profile_output.stem}_workers_{max_workers}{profile_output.suffix}"
        )
        stats.dump_stats(str(profile_file))
        print(f"Profile saved to: {profile_file}")

    # Get top functions by cumulative time
    stream = StringIO()
    stats.stream = stream
    stats.sort_stats("cumulative")
    stats.print_stats(20)
    top_cumulative = stream.getvalue()

    # Get top functions by total time
    stream = StringIO()
    stats.stream = stream
    stats.sort_stats("tottime")
    stats.print_stats(20)
    top_tottime = stream.getvalue()

    # Print summary
    print(f"\nPerformance Summary (max_workers={max_workers}):")
    print(f"  Wall-clock time: {wall_time:.2f}s")
    print(f"  CPU time:        {cpu_time:.2f}s")
    print(f"  CPU utilization: {(cpu_time / wall_time * 100):.1f}%")

    print("\nTop 10 functions by cumulative time:")
    for line in top_cumulative.split("\n")[5:15]:  # Skip header, show top 10
        if line.strip():
            print(f"  {line}")

    return {
        "max_workers": max_workers,
        "wall_time": wall_time,
        "cpu_time": cpu_time,
        "cpu_utilization": cpu_time / wall_time if wall_time > 0 else 0,
        "top_cumulative": top_cumulative,
        "top_tottime": top_tottime,
    }


def run_comparison(config_path: Path, worker_counts: list[int], output_dir: Path) -> None:
    """Run profiling with multiple worker counts and compare results."""
    results = []

    for workers in worker_counts:
        profile_output = output_dir / f"profile_workers_{workers}.prof"
        result = run_with_profiling(config_path, workers, profile_output)
        results.append(result)

    # Save results to JSON
    results_file = output_dir / "profiling_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {results_file}")

    # Generate comparison report
    report_file = output_dir / "profiling_comparison.md"
    with open(report_file, "w") as f:
        f.write("# Performance Profiling Comparison\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Summary\n\n")
        f.write("| Workers | Wall Time (s) | CPU Time (s) | CPU Util (%) | Speedup |\n")
        f.write("|---------|---------------|--------------|--------------|----------|\n")

        baseline = results[0]["wall_time"]
        for r in results:
            speedup = baseline / r["wall_time"] if r["wall_time"] > 0 else 0
            f.write(
                f"| {r['max_workers']:7d} | {r['wall_time']:13.2f} | {r['cpu_time']:12.2f} | {r['cpu_utilization'] * 100:12.1f} | {speedup:8.2f}x |\n"
            )

        f.write("\n## Analysis\n\n")

        # Find best performer
        best = min(results, key=lambda x: x["wall_time"])
        f.write(
            f"**Best Performance**: {best['max_workers']} workers ({best['wall_time']:.2f}s)\n\n"
        )

        # Scaling efficiency
        if len(results) > 1:
            f.write("### Scaling Efficiency\n\n")
            for i, r in enumerate(results[1:], 1):
                ideal_speedup = results[i]["max_workers"] / results[0]["max_workers"]
                actual_speedup = baseline / r["wall_time"]
                efficiency = (actual_speedup / ideal_speedup * 100) if ideal_speedup > 0 else 0
                f.write(
                    f"- {r['max_workers']} workers: {efficiency:.1f}% efficient (ideal: {ideal_speedup:.1f}x, actual: {actual_speedup:.2f}x)\n"
                )

        f.write("\n## Detailed Profiles\n\n")
        f.write("See individual `.prof` files for detailed profiling data.\n")
        f.write("Use `python -m pstats profile_workers_N.prof` to analyze.\n\n")

        f.write("## Top Functions by Cumulative Time\n\n")
        for r in results:
            f.write(f"### Workers: {r['max_workers']}\n\n")
            f.write("```\n")
            f.write(r["top_cumulative"])
            f.write("```\n\n")

    print(f"Comparison report saved to: {report_file}")

    # Print summary
    print(f"\n{'=' * 80}")
    print("PROFILING COMPARISON SUMMARY")
    print(f"{'=' * 80}\n")
    print(
        f"{'Workers':>8} | {'Wall Time':>12} | {'CPU Time':>11} | {'CPU Util':>10} | {'Speedup':>8}"
    )
    print(f"{'-' * 8}-+-{'-' * 12}-+-{'-' * 11}-+-{'-' * 10}-+-{'-' * 8}")

    for r in results:
        speedup = baseline / r["wall_time"] if r["wall_time"] > 0 else 0
        print(
            f"{r['max_workers']:8d} | {r['wall_time']:10.2f}s | {r['cpu_time']:9.2f}s | {r['cpu_utilization'] * 100:9.1f}% | {speedup:7.2f}x"
        )

    print(f"\nBest: {best['max_workers']} workers ({best['wall_time']:.2f}s)")


def analyze_hotspots(profile_file: Path, output_file: Path) -> None:
    """Analyze profile to identify hotspots and categorize them."""
    stats = pstats.Stats(str(profile_file))

    # Get all stats
    stream = StringIO()
    stats.stream = stream
    stats.sort_stats("cumulative")
    stats.print_stats()
    all_stats = stream.getvalue()

    # Parse and categorize functions
    cpu_bound = []
    io_bound = []
    other = []

    # Keywords for categorization
    cpu_keywords = ["parse", "process", "analyze", "compile", "re.", "json.loads", "datetime"]
    io_keywords = ["subprocess", "read", "write", "open", "request", "http", "git"]

    for line in all_stats.split("\n")[5:]:  # Skip header
        if not line.strip() or "function calls" in line:
            continue

        # Simple categorization based on function names
        line_lower = line.lower()
        if any(kw in line_lower for kw in cpu_keywords):
            cpu_bound.append(line)
        elif any(kw in line_lower for kw in io_keywords):
            io_bound.append(line)
        else:
            other.append(line)

    # Write analysis
    with open(output_file, "w") as f:
        f.write("# Hotspot Analysis\n\n")
        f.write(f"**Profile**: {profile_file.name}\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("## CPU-Bound Operations\n\n")
        f.write("Functions that are primarily CPU-intensive:\n\n")
        f.write("```\n")
        for line in cpu_bound[:20]:
            f.write(f"{line}\n")
        f.write("```\n\n")

        f.write("## I/O-Bound Operations\n\n")
        f.write("Functions that are primarily I/O-intensive:\n\n")
        f.write("```\n")
        for line in io_bound[:20]:
            f.write(f"{line}\n")
        f.write("```\n\n")

        f.write("## Recommendations\n\n")
        f.write("Based on this analysis:\n\n")

        if len(cpu_bound) > len(io_bound):
            f.write("- **CPU-bound dominant**: Consider ProcessPoolExecutor for parallelism\n")
            f.write("- Focus on optimizing parsing and processing logic\n")
        elif len(io_bound) > len(cpu_bound):
            f.write("- **I/O-bound dominant**: ThreadPoolExecutor is appropriate\n")
            f.write("- Consider async I/O or batching requests\n")
        else:
            f.write("- **Mixed workload**: Current ThreadPoolExecutor is reasonable\n")
            f.write("- Consider hybrid approach with batch prefetch\n")

    print(f"Hotspot analysis saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Profile repository reporting performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to configuration file",
    )

    parser.add_argument(
        "--workers",
        type=str,
        default="1,4,8",
        help="Comma-separated list of max_workers values to test (default: 1,4,8)",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("docs/profiling"),
        help="Output directory for profiling results (default: docs/profiling)",
    )

    parser.add_argument(
        "--analyze-hotspots",
        action="store_true",
        help="Analyze hotspots and categorize CPU vs I/O bound operations",
    )

    args = parser.parse_args()

    # Parse worker counts
    worker_counts = [int(w.strip()) for w in args.workers.split(",")]

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Run profiling
    print("Starting performance profiling...")
    print(f"Config: {args.config}")
    print(f"Worker counts: {worker_counts}")
    print(f"Output directory: {args.output_dir}")

    run_comparison(args.config, worker_counts, args.output_dir)

    # Analyze hotspots if requested
    if args.analyze_hotspots:
        print("\nAnalyzing hotspots...")
        for workers in worker_counts:
            profile_file = args.output_dir / f"profile_workers_{workers}.prof"
            if profile_file.exists():
                output_file = args.output_dir / f"hotspots_workers_{workers}.md"
                analyze_hotspots(profile_file, output_file)

    print("\nProfiling complete!")


if __name__ == "__main__":
    main()
