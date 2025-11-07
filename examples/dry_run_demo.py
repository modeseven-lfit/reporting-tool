#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Dry Run Demonstration Script

This script demonstrates the dry run validation feature of the repository
reporting system. It shows how to validate configuration before running
expensive analysis operations.

Usage:
    python examples/dry_run_demo.py [--skip-network]

Phase 9: CLI & UX Improvements
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from cli.validation import dry_run, DryRunValidator


def demo_valid_config():
    """Demonstrate dry run with valid configuration."""
    print("\n" + "="*70)
    print("DEMO 1: Valid Configuration")
    print("="*70)

    config = {
        'project': {
            'name': 'example-project'
        },
        'paths': {
            'repos': '.'
        },
        'output': {
            'dir': '/tmp/example-output'
        },
        'api': {
            'github': {
                'token': 'ghp_example1234567890123456789012345678',
                'url': 'https://api.github.com'
            },
            'gerrit': {
                'auth': 'user:pass'
            }
        },
        'cache': {
            'enabled': False
        }
    }

    exit_code = dry_run(config, skip_network=True)
    return exit_code


def demo_invalid_config():
    """Demonstrate dry run with invalid configuration."""
    print("\n" + "="*70)
    print("DEMO 2: Invalid Configuration (Missing Fields)")
    print("="*70)

    config = {
        'project': {},  # Missing name
        'paths': {},    # Missing repos
        'output': {}    # Missing dir
    }

    exit_code = dry_run(config, skip_network=True)
    return exit_code


def demo_warnings():
    """Demonstrate dry run with warnings."""
    print("\n" + "="*70)
    print("DEMO 3: Configuration with Warnings")
    print("="*70)

    config = {
        'project': {
            'name': 'test-project'
        },
        'paths': {
            'repos': '/tmp'  # Exists but no repos
        },
        'output': {
            'dir': '/tmp/output'
        },
        'api': {},  # No credentials (warning, not error)
        'cache': {
            'enabled': False
        }
    }

    exit_code = dry_run(config, skip_network=True)
    return exit_code


def demo_advanced_usage():
    """Demonstrate advanced validator usage."""
    print("\n" + "="*70)
    print("DEMO 4: Advanced Validator Usage")
    print("="*70)

    config = {
        'project': {'name': 'advanced-demo'},
        'paths': {'repos': '.'},
        'output': {'dir': '/tmp/output'},
        'api': {},
        'cache': {'enabled': False}
    }

    # Create validator
    validator = DryRunValidator(config)

    # Run validation
    success, results = validator.validate_all(skip_network=True)

    # Custom result processing
    print("\nCustom Result Processing:")
    print("-" * 70)

    errors = [r for r in results if not r.passed and r.severity == 'error']
    warnings = [r for r in results if r.severity == 'warning']
    successes = [r for r in results if r.passed and r.severity not in ['warning', 'info']]

    print(f"\nSummary:")
    print(f"  Total checks: {len(results)}")
    print(f"  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Passed: {len(successes)}")

    if errors:
        print(f"\nFirst error: {errors[0].message}")
        if errors[0].suggestion:
            print(f"Suggestion: {errors[0].suggestion}")

    print("\n" + "="*70)
    print("Full validation output:")
    print("="*70)
    validator.print_results(results)

    return 0 if success else 1


def demo_project_name_validation():
    """Demonstrate project name validation edge cases."""
    print("\n" + "="*70)
    print("DEMO 5: Project Name Validation")
    print("="*70)

    test_cases = [
        ('valid-project', True, "Valid: alphanumeric and dashes"),
        ('', False, "Invalid: empty name"),
        ('a' * 101, False, "Invalid: too long (>100 chars)"),
        ('test/project', False, "Invalid: contains slash"),
        ('test:project', False, "Invalid: contains colon"),
    ]

    for name, should_pass, description in test_cases:
        print(f"\n{description}")
        print(f"Project name: '{name[:50]}{'...' if len(name) > 50 else ''}'")

        config = {
            'project': {'name': name},
            'paths': {'repos': '.'},
            'output': {'dir': '/tmp/output'},
            'api': {},
            'cache': {'enabled': False}
        }

        validator = DryRunValidator(config)
        result = validator._validate_project_name()

        status = "✓ PASS" if result.passed else "✗ FAIL"
        print(f"Result: {status}")
        if not result.passed:
            print(f"Error: {result.message}")
            if result.suggestion:
                print(f"Suggestion: {result.suggestion}")


def main():
    """Run all demonstrations."""
    import argparse

    parser = argparse.ArgumentParser(description="Dry run validation demonstration")
    parser.add_argument(
        '--skip-network',
        action='store_true',
        help='Skip network connectivity checks'
    )
    parser.add_argument(
        '--demo',
        type=int,
        choices=[1, 2, 3, 4, 5],
        help='Run specific demo (1-5), or all if not specified'
    )

    args = parser.parse_args()

    print("\n" + "="*70)
    print("DRY RUN VALIDATION DEMONSTRATION")
    print("="*70)
    print("\nThis script demonstrates the dry run validation feature.")
    print("It shows various validation scenarios and output formats.")

    demos = [
        (1, demo_valid_config),
        (2, demo_invalid_config),
        (3, demo_warnings),
        (4, demo_advanced_usage),
        (5, demo_project_name_validation),
    ]

    if args.demo:
        # Run specific demo
        for num, demo_func in demos:
            if num == args.demo:
                demo_func()
                break
    else:
        # Run all demos
        for num, demo_func in demos:
            demo_func()
            print()  # Extra spacing between demos

    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nKey Features Demonstrated:")
    print("  ✓ Configuration structure validation")
    print("  ✓ Required field checking")
    print("  ✓ Project name validation")
    print("  ✓ Path validation")
    print("  ✓ API credential checking")
    print("  ✓ System requirement verification")
    print("  ✓ Rich visual output")
    print("  ✓ Actionable error messages")
    print("  ✓ Warning vs error severity")
    print("  ✓ Custom result processing")
    print("\nFor more information, see:")
    print("  - docs/sessions/phase9_step3_dry_run_summary.md")
    print("  - docs/sessions/phase9_progress.md")
    print("  - src/cli/validation.py")
    print()


if __name__ == '__main__':
    main()
