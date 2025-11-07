<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Examples Directory

This directory contains example scripts and demonstrations for the Repository Reporting System.

## Available Examples

### `dry_run_demo.py` - Dry Run Validation Demonstration

Demonstrates the comprehensive dry run validation feature added in Phase 9.

**Usage:**

```bash
# Run all demonstrations
python examples/dry_run_demo.py

# Run specific demo (1-5)
python examples/dry_run_demo.py --demo 1

# Skip network checks
python examples/dry_run_demo.py --skip-network
```text

**Demonstrations Included:**

1. **Valid Configuration** - Shows successful validation with complete config
2. **Invalid Configuration** - Shows error handling for missing required fields
3. **Configuration with Warnings** - Shows warning vs error severity handling
4. **Advanced Usage** - Demonstrates programmatic validator usage
5. **Project Name Validation** - Shows edge cases for project name validation

**Features Demonstrated:**

- ✅ Configuration structure validation
- ✅ Required field checking
- ✅ Project name validation (length, characters)
- ✅ Path validation (existence, readability, repository detection)
- ✅ API credential checking
- ✅ System requirement verification (disk space, git, Python version)
- ✅ Rich visual output with emojis
- ✅ Actionable error messages with suggestions
- ✅ Warning vs error severity levels
- ✅ Custom result processing

**Example Output:**

```

======================================================================
🔍 DRY RUN VALIDATION RESULTS
======================================================================

❌ ERRORS:
  ✗ Project name is empty
     💡 Set project.name in config.yaml or use --project argument

⚠️  WARNINGS:
  ✓ API credentials: GitHub token not configured
     💡 Configure tokens in config.yaml or environment variables

✅ PASSED:
  ✓ Configuration structure valid
  ✓ Output directory writable: /tmp/output
  ✓ Git command available

----------------------------------------------------------------------

Total checks: 10
Passed: 8
Failed: 1
Warnings: 1
======================================================================

```text

## Purpose

These examples serve multiple purposes:

1. **Learning** - Help new users understand features
2. **Testing** - Verify functionality works as expected
3. **Documentation** - Demonstrate best practices
4. **Development** - Provide starting points for new features

## Adding New Examples

When adding new examples:

1. Create a descriptive filename (e.g., `feature_name_demo.py`)
2. Include comprehensive docstring with usage instructions
3. Add entry to this README
4. Ensure example is self-contained and well-commented
5. Test the example works as documented
6. Update related documentation if needed

## Related Documentation

- **Phase 9 Progress:** `docs/sessions/phase9_progress.md`
- **Dry Run Summary:** `docs/sessions/phase9_step3_dry_run_summary.md`
- **CLI Reference:** `docs/PHASE_9_CLI_UX_PLAN.md`
- **Source Code:** `src/cli/validation.py`
- **Tests:** `tests/test_cli_validation.py`

## Requirements

All examples require:

- Python 3.10+
- Repository reporting system source code
- Dependencies from project root

Run examples from the project root directory:

```bash
cd project-reports
python examples/dry_run_demo.py
```

## Support

For questions or issues with examples:

1. Check the related documentation (links above)
2. Review the source code and tests
3. Open an issue in the project repository
