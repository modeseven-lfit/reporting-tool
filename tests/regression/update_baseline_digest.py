#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Update Baseline Schema Digest

This script regenerates the baseline schema digest after intentional schema changes.
Use this after:
1. Making intentional changes to the JSON report structure
2. Verifying the changes are correct
3. Deciding to update the regression baseline

Usage:
    python tests/regression/update_baseline_digest.py [--report-path PATH]

Options:
    --report-path PATH    Path to a reference JSON report (default: auto-generate)
    --dry-run            Show what would be updated without writing
    --force              Skip confirmation prompt
"""

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def compute_schema_digest(data: dict[str, Any]) -> str:
    """
    Compute a stable digest of the JSON schema structure.

    This must match the algorithm in test_baseline_json_schema.py

    Args:
        data: JSON report data

    Returns:
        SHA256 hex digest of schema structure
    """

    def get_schema_structure(obj: Any, path: str = "") -> list[str]:
        """Recursively extract schema structure."""
        structure = []

        if isinstance(obj, dict):
            for key in sorted(obj.keys()):
                field_path = f"{path}.{key}" if path else key
                structure.append(f"{field_path}:dict")
                structure.extend(get_schema_structure(obj[key], field_path))
        elif isinstance(obj, list):
            structure.append(f"{path}:list")
            # Sample first item to get array element structure
            if obj:
                structure.extend(get_schema_structure(obj[0], f"{path}[0]"))
        elif isinstance(obj, str):
            structure.append(f"{path}:str")
        elif isinstance(obj, int | float):
            structure.append(f"{path}:number")
        elif isinstance(obj, bool):
            structure.append(f"{path}:bool")
        elif obj is None:
            structure.append(f"{path}:null")

        return structure

    schema_structure = get_schema_structure(data)
    schema_text = "\n".join(sorted(schema_structure))
    return hashlib.sha256(schema_text.encode("utf-8")).hexdigest()


def load_report_data(report_path: Path) -> dict[str, Any]:
    """Load JSON report data from file."""
    if not report_path.exists():
        print(f"Error: Report file not found: {report_path}", file=sys.stderr)
        sys.exit(1)

    with open(report_path) as f:
        return json.load(f)


def get_baseline_digest_path() -> Path:
    """Get the path to the baseline digest file."""
    script_dir = Path(__file__).parent
    fixtures_dir = script_dir.parent / "fixtures" / "expected_outputs"
    fixtures_dir.mkdir(parents=True, exist_ok=True)
    return fixtures_dir / "baseline_schema_digest.json"


def update_baseline_digest(report_data: dict[str, Any], dry_run: bool = False) -> None:
    """
    Update the baseline schema digest file.

    Args:
        report_data: JSON report data
        dry_run: If True, show what would be done without writing
    """
    digest = compute_schema_digest(report_data)
    baseline_path = get_baseline_digest_path()

    # Load existing baseline if it exists
    existing_digest = None
    if baseline_path.exists():
        with open(baseline_path) as f:
            existing = json.load(f)
            existing_digest = existing.get("digest")

    # Create new baseline
    baseline = {
        "schema_version": report_data.get("schema_version", "unknown"),
        "digest": digest,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "note": "Baseline schema digest for regression testing",
        "updated_by": "update_baseline_digest.py",
    }

    # Show what would change
    print("=" * 70)
    print("BASELINE DIGEST UPDATE")
    print("=" * 70)
    print(f"Baseline file: {baseline_path}")
    print(f"Schema version: {baseline['schema_version']}")
    print(f"New digest: {digest}")

    if existing_digest:
        if existing_digest == digest:
            print("\n✅ No changes detected - digest is already up to date")
            return
        else:
            print(f"Old digest: {existing_digest}")
            print("\n⚠️  Schema structure has changed!")
    else:
        print("\n📝 Creating new baseline (no existing baseline found)")

    if dry_run:
        print("\n[DRY RUN] Would write:")
        print(json.dumps(baseline, indent=2))
        return

    # Write updated baseline
    with open(baseline_path, "w") as f:
        json.dump(baseline, f, indent=2)
        f.write("\n")  # Add trailing newline

    print(f"\n✅ Baseline digest updated: {baseline_path}")
    print("\nNext steps:")
    print("1. Review the schema changes carefully")
    print("2. Commit the updated baseline_schema_digest.json")
    print("3. Consider bumping schema_version if this is a breaking change")


def generate_sample_report() -> dict[str, Any]:
    """
    Generate a sample report by running the reporting system.

    This is used when no report path is provided.
    """
    print("Generating sample report from fixtures...", file=sys.stderr)

    # For now, return a minimal valid structure
    # In a full implementation, this would:
    # 1. Run generate_reports.py on test fixtures
    # 2. Return the generated JSON

    return {
        "schema_version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project": "baseline_test",
        "config_digest": "test",
        "script_version": "1.0.0",
        "time_windows": {},
        "repositories": [],
        "authors": [],
        "organizations": [],
        "summaries": {
            "counts": {},
            "activity_status_distribution": {},
            "all_repositories": [],
            "top_contributors_commits": [],
            "top_contributors_loc": [],
            "top_organizations": [],
        },
        "errors": [],
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update baseline schema digest for regression testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update from existing report
  python update_baseline_digest.py --report-path reports/myproject/report_raw.json

  # Auto-generate and update
  python update_baseline_digest.py

  # Preview changes without writing
  python update_baseline_digest.py --dry-run
        """,
    )

    parser.add_argument("--report-path", type=Path, help="Path to a reference JSON report")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be updated without writing"
    )
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")

    args = parser.parse_args()

    # Load or generate report data
    if args.report_path:
        report_data = load_report_data(args.report_path)
    else:
        report_data = generate_sample_report()

    # Confirm unless --force or --dry-run
    if not args.force and not args.dry_run:
        baseline_path = get_baseline_digest_path()
        print(f"\nThis will update: {baseline_path}")
        response = input("Continue? [y/N] ")
        if response.lower() not in ("y", "yes"):
            print("Aborted.")
            return 0

    # Update baseline
    update_baseline_digest(report_data, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
