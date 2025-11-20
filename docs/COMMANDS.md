<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Command Reference

**Complete command-line reference for the Repository Reporting System**

---

## 🎯 Quick Reference

Essential commands for daily use:

```bash
# Generate report
reporting-tool generate --project NAME --repos-path PATH

# With optimization
reporting-tool generate --project NAME --repos-path PATH --cache --workers 8

# Dry run (validate only)
reporting-tool generate --project NAME --repos-path PATH --dry-run

# Show help
reporting-tool --help
```

---

Complete Command-Line Interface Reference

Version: 2.0
Last Updated: 2025-01-25
Phase: 13 - CLI & UX Improvements

Repository Analysis Report Generator - Command Line Interface

Version: Phase 9 (Enhanced CLI)
Last Updated: 2025-01-25

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Command Syntax](#command-syntax)
- [Required Arguments](#required-arguments)
- [Configuration Options](#configuration-options)
- [Configuration Wizard](#configuration-wizard)
- [Feature Discovery](#feature-discovery)
- [Output Options](#output-options)
- [Behavioral Options](#behavioral-options)
- [Verbosity Control](#verbosity-control)
- [Special Modes](#special-modes)
- [Advanced Options](#advanced-options)
- [Performance Metrics](#performance-metrics)
- [Exit Codes](#exit-codes)
- [Environment Variables](#environment-variables)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [See Also](#see-also)

---

## Overview

The Repository Analysis Report Generator is a command-line tool that analyzes Git repositories and generates comprehensive reports including:

- Commit activity and contributor statistics
- CI/CD workflow status (Jenkins, GitHub Actions)
- Feature detection (Dependabot, pre-commit, ReadTheDocs, etc.)
- Organization and contributor rankings
- Inactive repository identification

---

## Quick Start

```bash
# Basic usage
reporting-tool generate --project my-project --repos-path /path/to/repos

# Validate configuration first
reporting-tool generate --project my-project --repos-path /path/to/repos --dry-run

# Generate with verbose output
reporting-tool generate --project my-project --repos-path /path/to/repos -vv
```text

---

## Command Syntax

```text
reporting-tool generate [OPTIONS]
```text

All options can be specified in any order, but `--project` and `--repos-path` are required.

---

## Required Arguments

### `--project NAME`

**Description:** Project name for reporting
**Required:** Yes
**Type:** String
**Purpose:**

- Used for configuration overrides (looks for `{NAME}.config`)
- Used in output file naming
- Displayed in reports

Examples:

```bash
--project kubernetes
--project my-awesome-project
--project "Multi Word Project"  # Use quotes for spaces
```

Notes:

- Case-sensitive for configuration file matching
- Falls back to case-insensitive search if exact match not found
- Should match configuration file name (without `.config` extension)

---

### `--repos-path PATH`

**Description:** Path to directory containing cloned repositories
**Required:** Yes
**Type:** Path (absolute or relative)
**Purpose:**

- Specifies where Git repositories are located
- All immediate subdirectories are analyzed as repositories
- Must be readable by the process

Examples:

```bash
--repos-path /workspace/repos
--repos-path ./repositories
--repos-path ~/projects/open-source
```text

Notes:

- Path must exist and be accessible
- Repositories should be Git repositories (contain `.git` directory)
- Nested repository structures are supported
- Symbolic links are followed

---

## Configuration Options

### `--config-dir PATH`

**Description:** Configuration directory containing YAML config files
**Required:** No
**Default:** `./config`
**Type:** Path

Examples:

```bash
--config-dir /etc/repo-reports/config
--config-dir ./custom-config
```text

Expected Files:

- `template.config` (required) - Base configuration
- `{project}.config` (optional) - Project-specific overrides

**See also:** [Configuration Guide](CONFIGURATION.md)

---

### `--output-dir PATH`

**Description:** Output directory for generated reports
**Required:** No
**Default:** `./output`
**Type:** Path

Examples:

```bash
--output-dir /var/reports/output
--output-dir ./reports/$(date +%Y-%m-%d)
```text

Notes:

- Directory is created if it doesn't exist
- Must have write permissions
- Previous reports are overwritten

---

> **Note:** Configuration wizard (`init`) and feature listing (`list-features`) commands are not yet implemented.
> - To create configuration: Copy `/config/default.yaml` to `/configuration/<project>.yaml` and customize
> - Features are automatically detected during report generation (see generated reports for detected features)

---

## Output Options

### `--output-format FORMAT`

**Description:** Specify which output format(s) to generate
**Required:** No
**Default:** `all`
**Choices:** `json`, `md`, `html`, `all`

Examples:

```bash
--output-format html      # Only HTML reports
--output-format json      # Only JSON data
--output-format md        # Only Markdown reports
--output-format all       # All formats (default)
```text

Output Files:

- `json`: `{project}_report.json`
- `md`: `{project}_report.md`
- `html`: `{project}_report.html` (with CSS/JS)
- `all`: All of the above

---

### `--no-html`

**Description:** Skip HTML report generation
**Required:** No
**Type:** Flag (boolean)
**Deprecated:** Use `--output-format` instead

Example:

```bash
--no-html  # Deprecated: use --output-format json instead
```text

---

### `--no-zip`

**Description:** Skip ZIP bundle creation
**Required:** No
**Type:** Flag (boolean)

Example:

```bash
--no-zip  # Don't create output.zip archive
```text

Notes:

- By default, all outputs are bundled into `{project}_reports.zip`
- Use this flag to skip ZIP creation (faster, less disk usage)

---

## Behavioral Options

### `--cache`

**Description:** Enable caching of git metrics
**Required:** No
**Type:** Flag (boolean)
**Default:** Disabled

Examples:

```bash
--cache  # Enable caching
```

Benefits:

- Speeds up subsequent runs (10-100x faster)
- Useful during development and testing
- Stores metrics in `.cache/repo-metrics/`

Caveats:

- Cache is not invalidated automatically
- Manual cleanup may be needed: `rm -rf .cache/repo-metrics/`
- Disk space usage increases

---

### `--workers N`

**Description:** Number of worker threads for parallel processing
**Required:** No
**Default:** CPU count
**Type:** Integer (1-64)

Examples:

```bash
--workers 4   # Use 4 threads
--workers 1   # Single-threaded (useful for debugging)
--workers 16  # High parallelism
```text

Notes:

- More workers = faster processing (up to a point)
- Diminishing returns beyond 2x CPU count
- Single-threaded mode useful for debugging
- Network-bound operations may not benefit

---

## Verbosity Control

Verbosity and quiet mode are mutually exclusive.

### `--verbose`, `-v`

**Description:** Increase verbosity level
**Required:** No
**Type:** Count (can be used multiple times)
**Levels:**

- (none): WARNING and above
- `-v`: INFO and above
- `-vv`: DEBUG and above
- `-vvv`: TRACE (maximum detail)

Examples:

```bash
reporting-tool generate --project test --repos-path ./repos -v     # INFO
reporting-tool generate --project test --repos-path ./repos -vv    # DEBUG
reporting-tool generate --project test --repos-path ./repos -vvv   # TRACE
```text

Use Cases:

- `-v`: Normal operation, want to see progress
- `-vv`: Debugging issues, need detailed logs
- `-vvv`: Deep troubleshooting, maximum information

---

### `--quiet`, `-q`

**Description:** Suppress non-error output
**Required:** No
**Type:** Flag (boolean)

Example:

```bash
reporting-tool generate --project test --repos-path ./repos --quiet
```text

Behavior:

- Only errors and warnings are displayed
- No progress indicators or status messages
- Useful for automation and scripts
- Exit code still indicates success/failure

---

## Special Modes

### `--dry-run`

**Description:** Validate configuration without executing analysis
**Required:** No
**Type:** Flag (boolean)

Example:

```bash
reporting-tool generate --project test --repos-path ./repos --dry-run
```

Validation Checks:

- ✓ Configuration file exists and is valid YAML
- ✓ Required fields are present
- ✓ Repository paths exist and are accessible
- ✓ Output directory is writable
- ✓ Template files are present
- ✓ API endpoints are reachable (optional)
- ✓ System resources are sufficient

Output:

```text
🔍 Running pre-flight validation checks...

✅ Configuration validation: PASSED
✅ Path validation: PASSED
✅ API connectivity: PASSED
✅ System resources: PASSED
✅ Template validation: PASSED

All checks passed! Ready to generate reports.
```text

Exit Codes:

- `0`: All validations passed
- `2`: Configuration errors
- `6`: Validation failures

---

> **Note:** `--validate-only` and `--show-config` flags are not yet implemented. Use `--dry-run` for configuration validation.

---

## Advanced Options

### `--log-level LEVEL`

**Description:** Override log level from configuration
**Required:** No
**Choices:** `DEBUG`, `INFO`, `WARNING`, `ERROR`
**Default:** From configuration (usually `INFO`)

Examples:

```bash
--log-level DEBUG
--log-level ERROR
```text

---

### `--cache-dir PATH`

**Description:** Custom cache directory
**Required:** No
**Default:** `.cache/repo-metrics`
**Type:** Path

Example:

```bash
--cache-dir /tmp/repo-cache
```text

---

### `--config-override KEY=VALUE`

**Description:** Override specific configuration values
**Required:** No
**Type:** Key=Value pair (can be used multiple times)

Examples:

```bash
--config-override activity_thresholds.active_days=180
--config-override api.github.enabled=false
--config-override "privacy.anonymize_emails=true"
```text

Notes:

- Use dot notation for nested keys
- Quote values with spaces
- Can be used multiple times
- Overrides both template and project config

---

## Performance Metrics

Performance metrics are automatically collected during report generation and displayed based on verbosity level.

### Viewing Metrics

```bash
# Basic timing (default)
reporting-tool generate --project test --repos-path ./repos

# Detailed metrics (verbose)
reporting-tool generate --project test --repos-path ./repos -v

# Debug-level profiling (very verbose)
reporting-tool generate --project test --repos-path ./repos -vv

# Trace-level profiling (maximum detail)
reporting-tool generate --project test --repos-path ./repos -vvv
```

### Output Levels

#### Normal Mode (default)

```text
Report generated successfully!
Total execution time: 45.2s
```text

#### Verbose Mode (-v)

```text
📊 Performance Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️  Timing Breakdown:
   Repository analysis:  28.5s (63%)
   Report generation:    12.3s (27%)
   Validation:            2.1s  (5%)
   Other:                 2.3s  (5%)

💾 Resource Usage:
   Peak memory:          256 MB
   CPU time:             42.3s
   Disk I/O:             145 MB

🌐 API Statistics:
   GitHub API calls:     156 total (89 cached, 57%)
   Gerrit API calls:     23 total (12 cached, 52%)

📦 Repositories:
   Analyzed:             12
   Throughput:           0.27 repos/sec

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Total execution time: 45.2s
```

#### Debug Mode (-vv, -vvv)

Includes detailed operation profiling:

```text
🔬 Detailed Operation Profile:
   fetch_repository_data:    234 calls,  12.3s total,  52ms avg
   analyze_commits:          156 calls,   8.7s total,  56ms avg
   detect_features:           12 calls,   3.2s total, 267ms avg
   render_template:            1 call,    2.1s total,   2.1s avg
   ...
```text

### Metrics Categories

Timing Breakdown:

- Repository analysis time
- Report generation time
- Validation time
- Other operations

Resource Usage:

- Peak memory consumption
- CPU time utilized
- Disk I/O (read/write)

API Statistics:

- Total API calls
- Cached calls
- Cache hit rate
- Average response time

Repository Metrics:

- Repositories analyzed
- Throughput (repos/sec)
- Average processing time

### Performance Tips

Fast iterations:

```bash
--cache --workers 1 -v
```text

Maximum performance:

```bash
--cache --workers auto --quiet
```

Debug slow runs:

```bash
-vv  # Shows timing breakdown and bottlenecks
```text

**See also:** Performance Guide

---

## Exit Codes

The tool uses standardized exit codes for automation and scripting:

| Code | Meaning | Description |
|------|---------|-------------|
| `0` | Success | Operation completed successfully with no errors or warnings |
| `1` | Error | General error (configuration, API, processing failure) |
| `2` | Partial Success | Operation completed but with warnings or incomplete data |
| `3` | Usage Error | Invalid arguments or command syntax |
| `4` | System Error | System-level error (permissions, disk space, dependencies) |

Exit Code Details:

- **Code 0 (SUCCESS)**: Report generated successfully, all repositories processed, no errors or warnings
- **Code 1 (ERROR)**: Includes configuration errors, API failures, network errors, data processing errors, or unexpected exceptions
- **Code 2 (PARTIAL)**: Some repositories failed to process, incomplete data collected, or non-fatal errors occurred
- **Code 3 (USAGE_ERROR)**: Missing required arguments, invalid argument values, conflicting options, or incorrect command syntax
- **Code 4 (SYSTEM_ERROR)**: Permission denied, out of disk space, missing system dependencies, or resource exhaustion

Usage in Scripts:

```bash
#!/bin/bash
reporting-tool generate --project test --repos-path ./repos
EXIT_CODE=$?

case $EXIT_CODE in
  0) echo "✓ Success - report generated successfully" ;;
  1) echo "✗ Error - check logs for configuration, API, or processing issues" ;;
  2) echo "⚠ Partial success - report generated with warnings" ;;
  3) echo "✗ Usage error - check command syntax and arguments" ;;
  4) echo "✗ System error - check permissions, disk space, or dependencies" ;;
  *) echo "✗ Unknown error ($EXIT_CODE)" ;;
esac

exit $EXIT_CODE
```text

Retry Logic:

```bash
#!/bin/bash
# Retry on transient errors (codes 1, 2, 4)
MAX_RETRIES=3
RETRY=0

while [ $RETRY -lt $MAX_RETRIES ]; do
  reporting-tool generate --project test --repos-path ./repos
  EXIT_CODE=$?

  case $EXIT_CODE in
    0) echo "Success!"; exit 0 ;;
    3) echo "Usage error - won't retry"; exit 3 ;;
    1|2|4)
      RETRY=$((RETRY + 1))
      echo "Attempt $RETRY failed (code $EXIT_CODE), retrying..."
      sleep 5
      ;;
  esac
done

echo "Failed after $MAX_RETRIES attempts"
exit 1
```text

---

## Environment Variables

The following environment variables are supported:

### `GITHUB_TOKEN`

**Description:** GitHub API personal access token
**Required:** If GitHub integration is enabled
**Format:** `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

Example:

```bash
export GITHUB_TOKEN="ghp_abc123..."
reporting-tool generate --project test --repos-path ./repos
```

**Alternative:** Configure in `config/template.config` or `config/{project}.config`

---

### `GERRIT_USERNAME` / `GERRIT_PASSWORD`

**Description:** Gerrit API credentials
**Required:** If Gerrit integration is enabled

Example:

```bash
export GERRIT_USERNAME="myuser"
export GERRIT_PASSWORD="mypass"
reporting-tool generate --project test --repos-path ./repos
```text

---

### `NO_COLOR`

**Description:** Disable colored output
**Values:** Any non-empty value

Example:

```bash
NO_COLOR=1 reporting-tool generate --project test --repos-path ./repos
```text

---

## Examples

### Basic Report Generation

```bash
# Minimal command
reporting-tool generate \
  --project kubernetes \
  --repos-path /workspace/k8s-repos

# With custom output directory
reporting-tool generate \
  --project kubernetes \
  --repos-path /workspace/k8s-repos \
  --output-dir /var/reports/k8s
```text

### Validation and Testing

```bash
# Validate configuration
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --dry-run

# View resolved configuration with dry-run
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --show-config
```

### Performance Optimization

```bash
# Enable caching for faster subsequent runs
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --cache

# Increase parallelism
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --workers 16

# Both optimizations
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --cache \
  --workers 16
```text

### Output Format Control

```bash
# Generate only JSON (no HTML/Markdown)
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --output-format json

# Generate HTML only (no ZIP)
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --output-format html \
  --no-zip
```text

### Debugging and Troubleshooting

```bash
# Verbose output
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  -vv

# Maximum debug information
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  -vvv

# Single-threaded for easier debugging
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --workers 1 \
  -vv
```text

### Automation and CI/CD

```bash
# Quiet mode for scripts
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --quiet

# With error handling
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --quiet || echo "Report generation failed with exit code $?"

# Scheduled report generation
0 2 * * * cd /workspace && reporting-tool generate \
  --project nightly \
  --repos-path ./repos \
  --output-dir /reports/$(date +\%Y-\%m-\%d) \
  --quiet
```

### Configuration Overrides

```bash
# Override specific settings
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --config-override activity_thresholds.active_days=180 \
  --config-override api.github.enabled=false

# Multiple overrides
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --config-override activity_thresholds.active_days=90 \
  --config-override activity_thresholds.current_days=30 \
  --config-override privacy.anonymize_emails=true
```text

---

## Troubleshooting

### Common Issues

#### "Configuration file not found"

```text
❌ Error: Configuration file not found: config/test.config

💡 Suggestion: Create a config.yaml file or specify a different path with --config

📚 Documentation: docs/configuration.md
```text

Solutions:

1. Create the configuration file
2. Use `--config-dir` to specify alternate location
3. Check project name matches config file name

---

#### "Repository path does not exist"

```

❌ Error: Repository path does not exist: /path/to/repos

💡 Suggestion: Verify the path exists and is accessible

```text

Solutions:

1. Verify path exists: `ls -la /path/to/repos`
2. Check permissions: `ls -ld /path/to/repos`
3. Use absolute path instead of relative
4. Check for typos in path

---

#### "GitHub API error: 401 Unauthorized"

```text
❌ Error: GitHub API error: 401 Unauthorized

💡 Suggestion: Check GitHub API token - it may be expired or invalid

📚 Documentation: docs/troubleshooting.md#api-errors
```text

Solutions:

1. Verify token is set: `echo $GITHUB_TOKEN`
2. Check token has correct permissions
3. Generate new token at <https://github.com/settings/tokens>
4. Ensure token hasn't expired

---

#### "Permission denied: output/reports.html"

```

❌ Error: Permission denied: output/reports.html

💡 Suggestion: Check file/directory permissions. You may need to run with
   appropriate privileges or choose a different output directory.

```text

Solutions:

1. Check directory permissions: `ls -ld output/`
2. Create directory with correct permissions: `mkdir -p output && chmod 755 output`
3. Use different output directory: `--output-dir /tmp/reports`

---

#### "Validation failed for 'TimeWindow.days'"

```text
❌ Error: Validation failed for 'TimeWindow.days': Field 'TimeWindow.days'
   must be positive (got: 0) Expected: integer > 0
```text

Solutions:

1. Check configuration file for invalid values
2. Ensure time window configurations are correct
3. Run `--show-config` to see resolved values

---

### Getting Help

Run validation:

```bash
reporting-tool generate --project test --repos-path ./repos --dry-run
```

Enable verbose logging:

```bash
reporting-tool generate --project test --repos-path ./repos -vv
```text

Check configuration:

```bash
reporting-tool generate --project test --repos-path ./repos --show-config
```text

Configuration validation:

```bash
reporting-tool generate --project test --repos-path ./repos --dry-run
```

---

## See Also

- Quick Start Guide - Getting started tutorial
- [Configuration Guide](CONFIGURATION.md) - Config file reference
- [Usage Examples](USAGE_EXAMPLES.md) - Common workflows
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Detailed error solutions

---

**Last Updated:** 2025-01-25
**Version:** 2.0 (Phase 13 - CLI & UX Improvements)
**Feedback:** Report issues or suggestions to the development team
**Status:** Production Ready
