# CLI Guide - Repository Reporting System

**Complete Command-Line Interface Documentation**

Version: 3.0
Last Updated: 2025-01-30
Phase: 15 - Typer CLI Migration

---

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
- [Core Concepts](#core-concepts)
- [Command Reference](#command-reference)
- [Feature Discovery](#feature-discovery)
- [Configuration Wizard](#configuration-wizard)
- [Error Handling](#error-handling)
- [Performance Metrics](#performance-metrics)
- [Advanced Usage](#advanced-usage)
- [Integration Patterns](#integration-patterns)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Introduction

The Repository Reporting System provides a powerful command-line interface for analyzing Git repositories and generating comprehensive reports. This guide covers all CLI features, from basic usage to advanced techniques.

### Key Features

✨ **Feature Discovery** - Find and learn about supported features
🧙 **Configuration Wizard** - Interactive setup in under 2 minutes
🎯 **Smart Error Messages** - Actionable recovery steps and context
📊 **Performance Metrics** - Real-time execution statistics
🔧 **Flexible Configuration** - YAML, command-line, or environment variables
🚀 **Parallel Processing** - Analyze multiple repositories simultaneously
💾 **Intelligent Caching** - Avoid redundant work, speed up re-runs

### Quick Links

- [CLI Reference](CLI_REFERENCE.md) - Complete argument documentation
- [Usage Examples](USAGE_EXAMPLES.md) - Real-world scenarios
- [Feature Discovery Guide](FEATURE_DISCOVERY_GUIDE.md) - Feature details
- [Configuration Wizard Guide](CONFIG_WIZARD_GUIDE.md) - Setup walkthrough
- [Performance Guide](PERFORMANCE_GUIDE.md) - Optimization techniques

---

## Getting Started

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/project-reports.git
cd project-reports

# Install dependencies
uv sync  # Recommended
# or
pip install .

# Verify installation
reporting-tool --help
```

### Your First Report (30 seconds)

The fastest way to generate your first report:

```bash
# 1. Create a configuration file (interactive wizard)
reporting-tool init --project my-project

# 2. Answer a few questions (or use defaults)
# - Repository path: ./repos
# - Output directory: ./output
# - Other options: Press Enter for defaults

# 3. Generate report
reporting-tool generate --project my-project --repos-path ./repos
```

That's it! Your report is in `output/my-project_report.html`

### Your First Report (Template-Based, 10 seconds)

For non-interactive setup:

```bash
# Create config from template
reporting-tool init --template standard \
  --project my-project \
  --config-output config/my-project.yaml

# Generate report
reporting-tool generate --project my-project --repos-path ./repos
```

### Verify Everything Works

Before running on your repositories, validate your setup:

```bash
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --dry-run
```

**Expected output:**

```
🔍 Running pre-flight validation checks...

✅ Configuration validation: PASSED
✅ Path validation: PASSED
✅ API connectivity: PASSED
✅ System resources: PASSED
✅ Template validation: PASSED

All checks passed! Ready to generate reports.
```

---

### New in Version 3.0: Typer CLI

The CLI has been modernized with Typer and Rich for a better user experience:

**🎨 Beautiful Output**

- Colorized help text
- Progress bars
- Formatted tables
- Syntax highlighting

**🚀 Shell Completion**

```bash
# Enable auto-completion for your shell
reporting-tool --install-completion

# Now you can tab-complete commands and options!
```

**📋 Subcommands**

The new CLI is organized into logical subcommands:

| Command | Purpose |
|---------|---------|
| `generate` | Generate reports (main functionality) |
| `init` | Initialize configuration |
| `list-features` | Show available features |
| `validate` | Validate configuration files |

**💡 Better Help**

```bash
# Main help
reporting-tool --help

# Command-specific help
reporting-tool generate --help
reporting-tool init --help
```

**🔄 Migration from v1.x**

---

## Core Concepts

### Command Structure

The new CLI uses subcommands for different operations:

```bash
reporting-tool [COMMAND] [OPTIONS]
```

**Main Commands:**

```bash
# Generate reports
reporting-tool generate --project NAME --repos-path PATH [OPTIONS]

# Initialize configuration
reporting-tool init --project NAME [--template TYPE]

# List available features
reporting-tool list-features [--verbose]

# Validate configuration
reporting-tool validate --config PATH
```

**Basic Pattern for Report Generation:**

```bash
reporting-tool generate \
  --project NAME \           # Required (or use config file)
  --repos-path PATH \        # Required (or use config file)
  [--config-dir PATH] \      # Optional configuration
  [--output-dir PATH] \      # Optional output location
  [--output-format FORMAT] \ # Optional format control
  [OTHER OPTIONS]             # Additional options
```

### Three Ways to Configure

#### 1. Command-Line Arguments (Highest Priority)

```bash
reporting-tool generate \
  --project kubernetes \
  --repos-path /data/k8s-repos \
  --output-dir /reports/$(date +%Y-%m-%d) \
  --workers 16 \
  --cache
```

#### 2. Configuration File (Medium Priority)

```yaml
# config/kubernetes.yaml
project: kubernetes
repositories_path: /data/k8s-repos
output_directory: /reports

workers: 16
cache:
  enabled: true
```

```bash
reporting-tool generate --project kubernetes --repos-path /data/k8s-repos
```

#### 3. Environment Variables (Lowest Priority)

```bash
export GITHUB_TOKEN="ghp_xxxx"
export REPOS_PATH="/data/repos"

reporting-tool generate --project my-project --repos-path "$REPOS_PATH"
```

### Execution Modes

The CLI operates in different modes depending on the options provided:

| Mode | Command | Purpose |
|------|---------|---------|
| **Report Generation** | `generate --project --repos-path` | Standard report generation |
| **Validation** | `generate --dry-run` | Pre-flight checks only |
| **Configuration Wizard** | `init --project` | Interactive config creation |
| **Template Setup** | `init --template TYPE` | Quick config from template |
| **Feature Discovery** | `list-features` | Show available features |
| **Feature Details** | `list-features --detail NAME` | Detailed feature info |
| **Config Display** | `generate --show-config` | Display effective config |
| **Config Validation** | `validate --config PATH` | Config file validation |

### Information vs. Action

Some commands and options are **informational** (display information and exit):

```bash
--help                    # Show help
--version                 # Show version
list-features             # List all features
list-features --detail    # Feature details
generate --show-config    # Display effective config
```

These don't require `--project` or `--repos-path` (except `--show-config`).

Other commands and options are **actions** (perform operations):

```bash
generate               # Generate reports
init                   # Run configuration wizard
validate               # Validate config file
generate --dry-run     # Validate setup
```

---

## Command Reference

### Essential Commands

#### Generate a Report

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /path/to/repos
```

**What it does:**

1. Loads configuration from `config/my-project.yaml` (if exists)
2. Analyzes all repositories in `/path/to/repos`
3. Generates HTML report in `output/my-project_report.html`
4. Creates ZIP archive in `output/my-project_report.zip`

#### Validate Before Running

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /path/to/repos \
  --dry-run
```

**Checks performed:**

- Configuration file syntax and values
- Repository path exists and is readable
- GitHub/Gerrit API credentials (if configured)
- Output directory is writable
- Required templates exist
- System resources available

#### Show Effective Configuration

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /path/to/repos \
  --show-config
```

Shows the final configuration after merging:

1. Default values
2. Configuration file values
3. Environment variables
4. Command-line arguments

---

## Feature Discovery

### Overview

The feature discovery system helps you understand what the reporting system can detect in your repositories.

### List All Features

```bash
# Basic list
reporting-tool list-features

# Verbose mode (more details)
reporting-tool list-features -v

# Very verbose mode (all details)
reporting-tool list-features -vv
```

**Output example:**

```
📦 Repository Reporting System - Available Features

Total: 24 features across 7 categories

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏗️  BUILD & PACKAGE (5 features)

  📦 docker
     Docker containerization

  ⚙️  gradle
     Gradle build configuration

  📦 maven
     Maven build configuration

  📦 npm
     NPM package configuration

  📦 sonatype
     Sonatype/Maven Central publishing

🔄 CI/CD (4 features)
...
```

### Show Feature Details

```bash
reporting-tool list-features --detail <feature-name>
```

**Example:**

```bash
reporting-tool list-features --detail docker
```

**Output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 docker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Description:
  Docker containerization

Category:
  🏗️  Build & Package

Configuration File:
  Dockerfile

Detection Method:
  Checks for Dockerfile in repository root

Configuration Example:
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN uv sync  # Recommended
# or
pip install .
  COPY . .
  CMD ["python", "app.py"]

Related Features:
  • github-actions (CI/CD)
  • jenkins (CI/CD)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Use --list-features to see all available features
```

### Search Features

```bash
# Features are searchable in verbose mode
reporting-tool list-features -v | grep -i "test"
```

Or use the Python API:

```python
from src.cli.features import search_features

results = search_features("test")
for name, desc, category in results:
    print(f"{name}: {desc}")
```

### Common Feature Queries

```bash
# Find all CI/CD features
reporting-tool list-features | grep "CI/CD" -A 20

# Find testing features
reporting-tool list-features --detail pytest
reporting-tool list-features --detail junit
reporting-tool list-features --detail coverage

# Find documentation features
reporting-tool list-features --detail sphinx
reporting-tool list-features --detail mkdocs
reporting-tool list-features --detail readthedocs
```

---

## Configuration Wizard

### Interactive Wizard

The configuration wizard guides you through creating a complete configuration file:

```bash
reporting-tool init --project my-project
```

**What you'll configure:**

- Project name and description
- Repository paths
- Output settings
- Time windows
- Activity thresholds
- Feature detection
- API credentials
- Performance options

**Time estimate:** 2-5 minutes (interactive)

### Template-Based Setup

For quick, non-interactive setup:

```bash
# Minimal configuration (bare essentials)
reporting-tool init --template minimal \
  --project my-project

# Standard configuration (recommended defaults)
reporting-tool init --template standard \
  --project my-project

# Full configuration (all options)
reporting-tool init --template full \
  --project my-project
```

**Time estimate:** < 10 seconds

### Custom Output Location

```bash
reporting-tool init --template standard \
  --project my-project \
  --config-output /path/to/custom-config.yaml
```

### Template Comparison

| Template | Use Case | Settings | Size |
|----------|----------|----------|------|
| **minimal** | Quick testing, CI/CD | Essential only | ~50 lines |
| **standard** | Most projects | Recommended defaults | ~150 lines |
| **full** | Complex projects | All options documented | ~400 lines |

### After Wizard

The wizard creates:

1. Configuration file: `config/{project}.yaml`
2. Output directory: `output/` (if it doesn't exist)
3. Validation: Automatically validates the config

Next steps:

```bash
# Review the generated config
cat config/my-project.yaml

# Validate it
reporting-tool generate --project my-project --repos-path ./repos --validate-only

# Generate your first report
reporting-tool generate --project my-project --repos-path ./repos
```

---

## Error Handling

### Enhanced Error Messages

Phase 13 introduces rich error context with actionable recovery steps.

#### Example: Missing Configuration

**Old error:**

```
Error: Configuration file not found
```

**New error:**

```
❌ Configuration Error: Configuration file not found

📍 Context:
   File: config/my-project.yaml
   Project: my-project
   Current directory: /home/user/project-reports

🔧 How to fix this:

   1. Create configuration file using the wizard:
      reporting-tool init --project my-project

   2. Or create from template:
      reporting-tool init --template standard --project my-project

   3. Or specify different config directory:
      reporting-tool generate --project my-project --config-dir /path/to/configs

💡 Related errors:
   • Invalid configuration format
   • Configuration validation failed

📚 Documentation:
   https://docs.example.com/configuration
```

#### Example: API Authentication

**Error:**

```
❌ API Error: GitHub authentication failed (401 Unauthorized)

📍 Context:
   API: GitHub
   Endpoint: https://api.github.com/user
   Status: 401

🔧 How to fix this:

   1. Set your GitHub token:
      export GITHUB_TOKEN="ghp_your_token_here"

   2. Or add to configuration:
      github:
        token: ghp_your_token_here

   3. Create a token at:
      https://github.com/settings/tokens

   Required scopes: repo, read:org

💡 Test your token:
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

📚 Documentation:
   https://docs.github.com/authentication
```

#### Example: Invalid Repository Path

**Error:**

```
❌ Path Error: Repository path does not exist

📍 Context:
   Path: /data/repos
   Exists: False
   Type: directory

🔧 How to fix this:

   1. Check if the path is correct:
      ls -la /data/repos

   2. Create the directory if missing:
      mkdir -p /data/repos

   3. Or specify correct path:
      reporting-tool generate --project my-project --repos-path ./repos

💡 Tip: Use absolute paths for reliability

📚 Documentation:
   See CLI_REFERENCE.md#repository-paths
```

### Error Categories

| Category | Description | Exit Code |
|----------|-------------|-----------|
| **Configuration Error** | Invalid config files or values | 10 |
| **Path Error** | Missing or invalid paths | 11 |
| **API Error** | GitHub/Gerrit API failures | 12 |
| **Validation Error** | Schema validation failures | 13 |
| **Processing Error** | Report generation failures | 14 |
| **Permission Error** | File system permission issues | 15 |

### Exit Codes

The tool uses standardized exit codes (0-4) for automation:

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Operation completed successfully with no errors or warnings |
| 1 | Error | General error (configuration, API, processing failure) |
| 2 | Partial Success | Operation completed but with warnings or incomplete data |
| 3 | Usage Error | Invalid arguments or command syntax |
| 4 | System Error | System-level error (permissions, disk space, dependencies) |

```bash
# Check exit code in scripts
reporting-tool generate --project test --repos-path ./repos
EXIT_CODE=$?

case $EXIT_CODE in
  0) echo "✓ Success!" ;;
  1) echo "✗ Error - check logs for configuration, API, or processing issues" ;;
  2) echo "⚠ Partial success - report generated with warnings" ;;
  3) echo "✗ Usage error - check command syntax and arguments" ;;
  4) echo "✗ System error - check permissions, disk space, or dependencies" ;;
  *) echo "✗ Unknown error: $EXIT_CODE" ;;
esac
```

**Retry Logic:**

```bash
# Retry on transient errors (codes 1, 2, 4)
# Don't retry usage errors (code 3)
for i in 1 2 3; do
  reporting-tool generate --project test --repos-path ./repos
  CODE=$?
  [ $CODE -eq 0 ] && exit 0
  [ $CODE -eq 3 ] && echo "Usage error - won't retry" && exit 3
  echo "Attempt $i failed (code $CODE), retrying in 5s..."
  sleep 5
done
echo "Failed after 3 attempts"
exit 1
```

### Verbose Error Output

```bash
# More error details
reporting-tool generate --project test --repos-path ./repos -v

# Maximum error details
reporting-tool generate --project test --repos-path ./repos -vvv
```

---

## Performance Metrics

### Overview

Phase 13 adds comprehensive performance tracking and reporting.

### Enable Metrics

Metrics are automatically collected during report generation. View them with verbose mode:

```bash
# Basic timing
reporting-tool generate --project test --repos-path ./repos -v

# Detailed metrics
reporting-tool generate --project test --repos-path ./repos -vv

# Debug-level profiling
reporting-tool generate --project test --repos-path ./repos -vvv
```

### Metrics Output Levels

#### Normal Mode (default)

```
Report generated successfully!
Total execution time: 45.2s
```

#### Verbose Mode (-v)

```
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

#### Debug Mode (-vvv)

Includes detailed operation profiling:

```
🔬 Detailed Operation Profile:
   fetch_repository_data:         234 calls,  12.3s total,  52ms avg
   analyze_commits:               156 calls,   8.7s total,  56ms avg
   detect_features:                12 calls,   3.2s total, 267ms avg
   render_template:                 1 call,    2.1s total,   2.1s avg
   ...
```

### Interpreting Metrics

#### Timing Breakdown

Shows where time is spent:

- **Repository analysis** - Git operations, commit analysis
- **Report generation** - Template rendering, file writing
- **Validation** - Config and data validation
- **Other** - Initialization, cleanup

**Optimization tips:**

- High analysis time? Use `--cache` or `--workers`
- High generation time? Simplify templates or reduce data
- High validation time? Review complex validation rules

#### Resource Usage

- **Peak memory** - Maximum memory used (watch for memory leaks)
- **CPU time** - Total CPU seconds (vs. wall clock time)
- **Disk I/O** - Data read/written

**Warning signs:**

- Peak memory > 1GB for < 50 repos → potential memory issue
- CPU time ≈ wall time → not using parallelism effectively
- High disk I/O → consider using caching or tmpfs

#### API Statistics

- **Total calls** - All API requests made
- **Cached calls** - Requests served from cache
- **Cache hit rate** - Percentage cached (higher is better)

**Good cache hit rates:**

- First run: 0% (expected)
- Second run: 60-80% (good)
- Third+ run: 80-95% (excellent)

#### Repository Throughput

- **Throughput** - Repositories analyzed per second

**Typical rates:**

- Sequential (1 worker): 0.1-0.3 repos/sec
- Parallel (4 workers): 0.4-1.2 repos/sec
- Parallel (16 workers): 1.5-3.0 repos/sec

### Performance Comparison

Run multiple times to compare performance:

```bash
# First run (no cache)
time reporting-tool generate --project test --repos-path ./repos

# Second run (with cache)
time reporting-tool generate --project test --repos-path ./repos --cache

# Parallel run
time reporting-tool generate --project test --repos-path ./repos --cache --workers 8
```

---

## Advanced Usage

### Configuration Overrides

Override specific config values from command line:

```bash
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --config-override time_windows.90d.days=60 \
  --config-override workers=8
```

**Syntax:** `--config-override path.to.key=value`

**Examples:**

```bash
# Change time window
--config-override time_windows.90d.days=60

# Change worker count
--config-override workers=16

# Disable caching
--config-override cache.enabled=false

# Change output format
--config-override output.format=json
```

### Output Format Control

```bash
# HTML only (default)
reporting-tool generate --project test --repos-path ./repos

# JSON only
reporting-tool generate --project test --repos-path ./repos --output-format json --no-html

# Both HTML and JSON
reporting-tool generate --project test --repos-path ./repos --output-format all

# No ZIP archive
reporting-tool generate --project test --repos-path ./repos --no-zip
```

### Parallel Processing

```bash
# Auto-detect CPU cores
reporting-tool generate --project test --repos-path ./repos --workers auto

# Specific worker count
reporting-tool generate --project test --repos-path ./repos --workers 8

# Single-threaded (debugging)
reporting-tool generate --project test --repos-path ./repos --workers 1
```

**Guidelines:**

- Development: `--workers 1` (easier debugging)
- Production: `--workers auto` or `--workers $(nproc)`
- Limited resources: `--workers 4`

### Caching Strategies

```bash
# Enable caching
reporting-tool generate --project test --repos-path ./repos --cache

# Custom cache directory
reporting-tool generate --project test --repos-path ./repos --cache --cache-dir /tmp/cache

# Clear cache before run
rm -rf .cache/repo-metrics/
reporting-tool generate --project test --repos-path ./repos --cache
```

### Logging Control

```bash
# Quiet mode (errors only)
reporting-tool generate --project test --repos-path ./repos --quiet

# Info level (default)
reporting-tool generate --project test --repos-path ./repos

# Verbose
reporting-tool generate --project test --repos-path ./repos -v

# Debug
reporting-tool generate --project test --repos-path ./repos -vv

# Trace (maximum detail)
reporting-tool generate --project test --repos-path ./repos -vvv

# Custom log level
reporting-tool generate --project test --repos-path ./repos --log-level DEBUG
```

### Filtering Repositories

```bash
# Analyze specific repositories
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --filter "repo1,repo2,repo3"

# Exclude repositories
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --exclude "archived-*,test-*"
```

---

## Integration Patterns

### CI/CD Integration

#### GitHub Actions

```yaml
name: Weekly Repository Report
on:
  schedule:
    - cron: '0 2 * * 1'  # Monday 2 AM

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: uv sync  # Recommended
# or
pip install .

      - name: Generate report
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          reporting-tool init --template standard \
            --project ${{ github.repository }} \
            --repos-path ./repos \
            --quiet

      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: repository-report
          path: output/
```

#### GitLab CI

```yaml
generate-report:
  stage: deploy
  image: python:3.11
  script:
    - uv sync  # Recommended
# or
pip install .
    - reporting-tool generate
        --init-template standard
        --project $CI_PROJECT_NAME
        --repos-path /repos
        --quiet
  artifacts:
    paths:
      - output/
    expire_in: 30 days
  only:
    - schedules
```

#### Jenkins

```groovy
pipeline {
    agent any
    triggers {
        cron('0 2 * * 1')
    }
    stages {
        stage('Generate Report') {
            steps {
                sh '''
                    reporting-tool init --template standard \
                        --project ${JOB_NAME} \
                        --repos-path /data/repos \
                        --quiet
                '''
            }
        }
        stage('Publish') {
            steps {
                publishHTML([
                    reportDir: 'output',
                    reportFiles: '*_report.html',
                    reportName: 'Repository Analysis'
                ])
            }
        }
    }
}
```

### Scripting Integration

#### Bash Script

```bash
#!/bin/bash
# generate-all-reports.sh

set -e  # Exit on error

PROJECTS=("kubernetes" "prometheus" "grafana")
DATE=$(date +%Y-%m-%d)

for project in "${PROJECTS[@]}"; do
    echo "Generating report for: $project"

    reporting-tool generate \
  --project "$project" \
        --repos-path "/data/repos/$project" \
        --output-dir "/reports/$DATE/$project" \
        --cache \
        --quiet

    if [ $? -eq 0 ]; then
        echo "✓ $project: SUCCESS"
    else
        echo "✗ $project: FAILED"
        exit 1
    fi
done

echo "All reports generated in: /reports/$DATE"
```

#### Python Script

```python
#!/usr/bin/env python3
"""Generate reports for multiple projects."""

import subprocess
import sys
from pathlib import Path

PROJECTS = ["kubernetes", "prometheus", "grafana"]
BASE_REPOS = Path("/data/repos")
OUTPUT_BASE = Path(f"/reports/{datetime.now():%Y-%m-%d}")

for project in PROJECTS:
    print(f"Generating report for: {project}")

    result = subprocess.run([
        "reporting-tool", "generate",
        "--project", project,
        "--repos-path", str(BASE_REPOS / project),
        "--output-dir", str(OUTPUT_BASE / project),
        "--cache",
        "--quiet"
    ])

    if result.returncode == 0:
        print(f"✓ {project}: SUCCESS")
    else:
        print(f"✗ {project}: FAILED")
        sys.exit(1)

print(f"All reports generated in: {OUTPUT_BASE}")
```

### Monitoring Integration

#### Prometheus Metrics

```bash
# Export metrics in Prometheus format
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --export-metrics /var/lib/prometheus/textfile/reports.prom
```

#### Grafana Dashboard

```bash
# Generate JSON output for Grafana
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --output-format json \
  --output-dir /var/lib/grafana/data
```

---

## Troubleshooting

### Common Issues

#### Issue: "Configuration file not found"

**Symptoms:**

```
❌ Configuration Error: Configuration file not found
```

**Solutions:**

1. Create config with wizard: `--init --project NAME`
2. Check config directory: `ls config/`
3. Verify project name matches file: `config/{project}.yaml`

#### Issue: "Repository path does not exist"

**Symptoms:**

```
❌ Path Error: Repository path does not exist
```

**Solutions:**

1. Verify path: `ls -la /path/to/repos`
2. Use absolute path: `--repos-path /full/path/to/repos`
3. Check spelling and case sensitivity

#### Issue: "GitHub API error: 401 Unauthorized"

**Symptoms:**

```
❌ API Error: GitHub authentication failed (401)
```

**Solutions:**

1. Set token: `export GITHUB_TOKEN="ghp_xxxxx"`
2. Check token: `echo $GITHUB_TOKEN`
3. Test token: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`
4. Create new token: <https://github.com/settings/tokens>

#### Issue: "Permission denied: output/report.html"

**Symptoms:**

```
❌ Permission Error: Cannot write to output directory
```

**Solutions:**

1. Check permissions: `ls -la output/`
2. Fix permissions: `chmod -R u+w output/`
3. Use different directory: `--output-dir /tmp/reports`

#### Issue: "Report generation very slow"

**Symptoms:**

- Takes > 5 minutes for < 20 repositories
- High CPU but low throughput

**Solutions:**

1. Enable caching: `--cache`
2. Use parallel processing: `--workers 8`
3. Reduce time windows in config
4. Check network latency to GitHub/Gerrit

#### Issue: "Out of memory"

**Symptoms:**

```
MemoryError: Unable to allocate array
```

**Solutions:**

1. Reduce worker count: `--workers 2`
2. Process repositories in batches
3. Increase system swap space
4. Use server with more RAM

### Debug Mode

For difficult issues, use maximum verbosity:

```bash
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --workers 1 \
  -vvv \
  2>&1 | tee debug.log
```

This creates a `debug.log` with:

- All API calls and responses
- Repository processing details
- Template rendering steps
- Error stack traces
- Performance profiling

### Getting Help

1. **Check Documentation:**
   - [CLI Reference](CLI_REFERENCE.md)
   - [Usage Examples](USAGE_EXAMPLES.md)
   - [Troubleshooting Guide](TROUBLESHOOTING.md)

2. **Use Built-in Help:**

   ```bash
   reporting-tool --help
   reporting-tool list-features
   reporting-tool list-features --detail NAME
   ```

3. **Run Validation:**

   ```bash
   reporting-tool generate --dry-run
   reporting-tool validate
   ```

4. **Check Exit Codes:**

   ```bash
   echo $?  # Show last exit code
   ```

5. **Report Issues:**
   - Include: OS, Python version, command used
   - Attach: Configuration file (remove secrets!)
   - Attach: Debug log (`-vvv` output)
   - Describe: Expected vs. actual behavior

---

## Best Practices

### Configuration Management

✅ **DO:**

- Use configuration files for projects (not command-line args)
- Version control your config files (without secrets)
- Use environment variables for secrets
- Document custom configurations
- Use the wizard for initial setup

❌ **DON'T:**

- Hardcode tokens in config files
- Use long command lines (hard to maintain)
- Mix different config styles in one project

### Performance Optimization

✅ **DO:**

- Enable caching for development: `--cache`
- Use parallel processing: `--workers auto`
- Run validation before full reports: `--dry-run`
- Monitor with verbose mode: `-v`
- Clear old caches periodically

❌ **DON'T:**

- Use `--workers 1` in production (slow)
- Skip validation before long runs
- Ignore performance metrics

### Error Handling

✅ **DO:**

- Check exit codes in scripts
- Read error messages completely
- Follow suggested recovery steps
- Use `--dry-run` to catch issues early
- Enable verbose mode when debugging

❌ **DON'T:**

- Ignore error context and suggestions
- Suppress error output in scripts
- Continue on errors without investigation

### Automation

✅ **DO:**

- Use `--quiet` in CI/CD pipelines
- Implement proper error handling
- Archive old reports
- Monitor execution time
- Use `--init-template` for reproducibility

❌ **DON'T:**

- Use interactive wizard in automation
- Run without timeout controls
- Ignore failed runs
- Store unlimited old reports

### Development Workflow

✅ **DO:**

- Test with `--dry-run` first
- Use `--workers 1` when debugging
- Enable maximum verbosity: `-vvv`
- Test on small repository subset first
- Use caching to speed up iterations

❌ **DON'T:**

- Test on production repositories
- Skip validation
- Ignore warnings
- Use parallel processing while debugging

---

## Quick Reference Card

### Most Common Commands

```bash
# Create configuration
reporting-tool init --project NAME

# Generate report
reporting-tool generate --project NAME --repos-path PATH

# Validate setup
reporting-tool generate --project NAME --repos-path PATH --dry-run

# List features
reporting-tool list-features

# Show feature details
reporting-tool list-features --detail FEATURE

# Production run (optimized)
reporting-tool generate --project NAME --repos-path PATH --cache --workers auto --quiet
```

### Essential Options

| Option | Purpose | Example |
|--------|---------|---------|
| `--project NAME` | Project identifier | `--project kubernetes` |
| `--repos-path PATH` | Repository location | `--repos-path /data/repos` |
| `--cache` | Enable caching | `--cache` |
| `--workers N` | Parallel processing | `--workers 8` |
| `-v/-vv/-vvv` | Verbosity level | `-vv` |
| `--quiet` | Minimal output | `--quiet` |
| `--dry-run` | Validation only | `--dry-run` |
| `--init` | Run wizard | `--init` |

### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Operation completed successfully |
| 1 | Error | Configuration, API, or processing error |
| 2 | Partial | Completed with warnings or incomplete data |
| 3 | Usage Error | Invalid arguments or command syntax |
| 4 | System Error | Permission denied, disk space, or dependencies |

---

## See Also

- **[CLI Reference](CLI_REFERENCE.md)** - Complete option documentation
- **[Usage Examples](USAGE_EXAMPLES.md)** - Real-world scenarios
- **[Feature Discovery Guide](FEATURE_DISCOVERY_GUIDE.md)** - Feature details
- **[Configuration Wizard Guide](CONFIG_WIZARD_GUIDE.md)** - Setup guide
- **[Performance Guide](PERFORMANCE_GUIDE.md)** - Optimization techniques
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Problem solving
- **[Testing Guide](TESTING_GUIDE.md)** - Testing information

---

**Last Updated:** 2025-01-25
**Version:** 2.0 (Phase 13)
**Feedback:** Report issues or suggestions to the development team
