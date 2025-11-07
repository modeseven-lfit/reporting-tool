<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# CLI Frequently Asked Questions (FAQ)

Repository Reporting System - Command Line Interface FAQ

Version: 2.0
Last Updated: 2025-01-26
Phase: 14 - CLI Documentation Polish

---

## Table of Contents

- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Performance](#performance)
- [Troubleshooting](#troubleshooting)
- [Advanced Usage](#advanced-usage)
- [Integration](#integration)
- [Error Handling](#error-handling)

---

## Getting Started

### Q: Which command-line flags are required?

**A:** Only two flags are required (unless in special modes):

```bash
--project NAME          # Project identifier
--repos-path PATH       # Path to repository directory
```text

However, first-time users should start with the configuration wizard:

```bash
reporting-tool init --project my-project
```

After creating a configuration file, you can run with just:

```bash
reporting-tool generate --project my-project --repos-path ./repos
```text

---

### Q: How do I create my first report?

**A:** Follow this 3-step process:

Step 1: Run the configuration wizard

```bash
reporting-tool init --project my-project
```

Step 2: Validate your setup

```bash
reporting-tool generate --project my-project --repos-path ./repos --dry-run
```text

Step 3: Generate the report

```bash
reporting-tool generate --project my-project --repos-path ./repos
```

Your report will be in the `output/` directory.

---

### Q: What's the difference between `--init` and `--init-template`?

A:

- **`--init`**: Interactive wizard that asks you questions
  - Best for: First-time users, custom configurations
  - Time: 2-3 minutes
  - Example: `reporting-tool init --project my-project`

- **`--init-template TEMPLATE`**: Non-interactive, uses a preset template
  - Best for: CI/CD, quick setup, standard configurations
  - Time: 10 seconds
  - Templates: `minimal`, `standard`, `full`
  - Example: `reporting-tool init --template standard --project my-project`

When to use which:

- Use `--init` if you're new or need custom settings
- Use `--init-template standard` for most projects
- Use `--init-template minimal` for quick tests
- Use `--init-template full` for comprehensive analysis

---

### Q: Where are the output files created?

**A:** By default, in the `./output/` directory:

```text
output/
├── {project}_report.html      # Interactive HTML report
├── {project}_report.json      # Raw JSON data
├── {project}_report.md        # Markdown report
└── {project}_report.zip       # Complete bundle
```

You can customize with:

```bash
--output-dir /custom/path
```text

---

### Q: How do I see what the tool is doing?

**A:** Use verbosity flags:

```bash
# Standard output (INFO level)
reporting-tool generate --project test --repos-path ./repos

# Verbose (detailed progress)
reporting-tool generate --project test --repos-path ./repos -v

# Debug (very detailed)
reporting-tool generate --project test --repos-path ./repos -vv

# Trace (everything)
reporting-tool generate --project test --repos-path ./repos -vvv

# Quiet (errors only)
reporting-tool generate --project test --repos-path ./repos --quiet
```

**Recommendation:** Use `-v` for development, `--quiet` for production.

---

## Configuration

### Q: Where should I put my configuration file?

**A:** The default location is:

```text
./config/{project}.yaml
```

For example, if `--project my-project`, the file should be:

```text
./config/my-project.yaml
```

You can customize the directory with:

```bash
--config-dir /custom/config/path
```text

---

### Q: How do I override specific configuration settings?

**A:** Use `--config-override`:

```bash
# Single override
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --config-override cache.enabled=true

# Multiple overrides
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --config-override time_windows.90d.days=60 \
  --config-override workers=16
```

Common overrides:

- `time_windows.90d.days=60` - Change time window
- `workers=8` - Set worker count
- `cache.enabled=true` - Enable caching
- `output.format=json` - Change output format

---

### Q: What's the configuration priority order?

**A:** From highest to lowest priority:

1. **Command-line arguments** (e.g., `--workers 8`)
2. **Configuration overrides** (e.g., `--config-override workers=8`)
3. **Configuration file** (e.g., `config/my-project.yaml`)
4. **Environment variables** (e.g., `GITHUB_TOKEN`)
5. **Built-in defaults**

Example:

```bash
# Configuration file says: workers=4
# Command line says: --workers 8
# Result: Uses 8 workers (command line wins)
```text

---

### Q: How do I view my effective configuration?

**A:** Use `--show-config`:

```bash
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --show-config
```

This shows the final merged configuration after all overrides are applied.

---

### Q: Can I use the same configuration for multiple projects?

**A:** Yes! Use `--config-override` to customize per-project:

```bash
# Shared config at config/shared.yaml
reporting-tool generate \
  --project project-a \
  --repos-path ./repos-a \
  --config-dir ./config \
  --config-override project=project-a

reporting-tool generate \
  --project project-b \
  --repos-path ./repos-b \
  --config-dir ./config \
  --config-override project=project-b
```text

Or create project-specific configs that inherit from a base:

```yaml
# config/base.yaml
_extends: ./shared.yaml
project: my-project
```

---

## Performance

### Q: How can I speed up report generation?

**A:** Use these optimization flags:

```bash
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --cache \              # Enable caching (biggest impact)
  --workers auto \       # Use all CPU cores
  --quiet                # Reduce logging overhead
```text

Performance tips:

- First run: ~25 minutes (100 repos)
- With `--cache`: ~5 minutes (subsequent runs)
- With `--workers auto`: ~20% faster
- Combined: **~4 minutes** (80% improvement)

---

### Q: What's the optimal worker count?

**A:** Use `--workers auto` to automatically detect:

```bash
--workers auto    # Recommended: Uses CPU count
```

Manual settings:

```bash
--workers 1       # Single-threaded (debugging)
--workers 4       # 4 parallel workers
--workers 8       # 8 parallel workers
--workers 16      # 16 parallel workers (high-end systems)
```text

Guidelines:

- **Development:** `--workers 1` (easier debugging)
- **CI/CD:** `--workers auto` (maximize speed)
- **Production:** `--workers auto` (best performance)
- **Debugging:** `--workers 1` (deterministic behavior)

---

### Q: When should I use caching?

**A:** **Almost always!** Caching provides massive speedups:

Use caching when:

- ✅ Running multiple reports on same repositories
- ✅ Iterating on configuration changes
- ✅ Repository data hasn't changed
- ✅ You want faster subsequent runs

Don't use caching when:

- ❌ First-time report generation (no cache exists yet)
- ❌ Repositories have been updated (will use stale data)
- ❌ Testing cache-related issues

Enable caching:

```bash
--cache                          # Use default cache location
--cache --cache-dir /tmp/cache   # Use custom cache location
```

Cache invalidation:

```bash
# Clear cache
rm -rf .cache/repo-metrics

# Or use custom location
rm -rf /custom/cache/path
```text

---

### Q: How much faster is parallel execution?

**A:** Typical improvements with `--workers auto`:

- **Sequential (1 worker):** 25:54 (1554s)
- **Parallel (8 workers):** 20:45 (1246s)
- **Improvement:** ~20% faster (saves 5+ minutes)

Combined with caching:

- **First run (no cache):** 25:54
- **Cached + parallel:** ~4:00
- **Total improvement:** ~84% faster

---

## Troubleshooting

### Q: Why is my report generation failing?

**A:** Follow this diagnostic flowchart:

Step 1: Check exit code

```bash
reporting-tool generate --project test --repos-path ./repos
echo $?
```

- **Exit 0:** Success (no issue)
- **Exit 1:** Configuration/API/processing error → Check logs
- **Exit 2:** Partial success → Review warnings
- **Exit 3:** Invalid arguments → Fix command syntax
- **Exit 4:** System error → Check permissions/disk space

Step 2: Run with debug logging

```bash
reporting-tool generate --project test --repos-path ./repos -vvv 2>&1 | tee debug.log
```text

Step 3: Validate configuration

```bash
reporting-tool generate --project test --repos-path ./repos --dry-run
```

---

### Q: How do I debug API errors?

A:

Step 1: Check authentication

```bash
# Verify GitHub token is set
echo $GITHUB_TOKEN

# If not set:
export GITHUB_TOKEN="ghp_your_token_here"
```text

Step 2: Run with API logging

```bash
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  -vv 2>&1 | grep -i "api"
```

Step 3: Check token permissions

- GitHub: Needs `repo` or `public_repo` scope
- Gerrit: Needs valid username/password

Common API errors:

- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Repository doesn't exist
- `429 Too Many Requests`: Rate limit exceeded (use `--cache`)

---

### Q: What do different exit codes mean?

A:

| Code | Meaning | What to Do |
|------|---------|------------|
| `0` | Success | Nothing - all good! |
| `1` | Error | Check logs for config/API/processing errors |
| `2` | Partial | Review warnings, report may be incomplete |
| `3` | Usage Error | Fix command syntax, check `--help` |
| `4` | System Error | Check permissions, disk space, dependencies |

Detailed diagnosis:

Exit 1 (ERROR):

```bash
# Run validation
reporting-tool validate --project test --repos-path ./repos --validate-only

# Check configuration
reporting-tool generate --project test --repos-path ./repos --show-config

# Review logs
reporting-tool generate --project test --repos-path ./repos -vv
```text

Exit 2 (PARTIAL):

```bash
# Check which repositories failed
grep -i "error\|warn" output/logs/*.log

# Review incomplete sections in report
less output/{project}_report.json
```

Exit 3 (USAGE_ERROR):

```bash
# Check required arguments
reporting-tool --help

# Verify syntax
reporting-tool generate --project test --repos-path ./repos --dry-run
```text

Exit 4 (SYSTEM_ERROR):

```bash
# Check permissions
ls -la output/
ls -la config/

# Check disk space
df -h

# Check dependencies
pip list | grep -E "PyYAML|httpx|jsonschema"
```

---

### Q: The tool is running very slowly. What should I check?

A:

Quick fixes (try first):

```bash
# Enable caching (biggest impact)
--cache

# Use parallel processing
--workers auto

# Reduce verbosity
--quiet
```text

Diagnostic steps:

1. Check cache status

```bash
# Run with -v to see cache hit rate
reporting-tool generate --project test --repos-path ./repos --cache -v | grep cache
```

2. Check worker utilization

```bash
# Run with top/htop in another terminal
reporting-tool generate --project test --repos-path ./repos --workers auto
```text

3. Profile performance

```bash
# Use Python profiler
python -m cProfile -o profile.stats -m reporting_tool.main \
  --project test --repos-path ./repos
```

4. Check network latency

```bash
# Test API connectivity
time curl -s https://api.github.com/rate_limit
```text

---

### Q: How do I fix "Configuration file not found" error?

A:

Error message:

```

❌ Configuration file not found: my-project.yaml
   Searched in: ./config

```text

Solutions:

Option 1: Create the configuration file

```bash
# Run the wizard
reporting-tool init --project my-project
```

Option 2: Use a template

```bash
# Create from template
reporting-tool init --template standard --project my-project
```text

Option 3: Specify custom config directory

```bash
# If config is elsewhere
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --config-dir /custom/path
```

Option 4: Check file naming

```bash
# File must match project name
# If --project my-project, file should be:
./config/my-project.yaml  # NOT .yml, NOT My-Project.yaml
```text

---

## Advanced Usage

### Q: Can I generate reports programmatically from Python?

**A:** Yes! Import and use the main function:

```python
from reporting_tool.main import main
from argparse import Namespace

# Set up arguments
args = Namespace(
    project='my-project',
    repos_path='./repos',
    config_dir='configuration',
    output_dir='reports',
    cache=True,
    quiet=True,
    verbose=False,
    no_html=False,
    no_zip=False,
    validate_only=False
)

# Run report generation
exit_code = main(args)

if exit_code == 0:
    print("Report generated successfully!")
else:
    print(f"Report generation failed with code {exit_code}")
```

Or use the CLI module directly:

```python
from src.cli import parse_arguments, validate_arguments
from src.config import load_config

args = parse_arguments(['--project', 'test', '--repos-path', './repos'])
validate_arguments(args)
config = load_config(args)
# ... proceed with report generation
```text

---

### Q: How do I integrate with CI/CD pipelines?

**A:** Use non-interactive mode with templates:

GitHub Actions:

```yaml
- name: Generate Report
  run: |
    reporting-tool init \
      --init-template standard \
      --project ${{ matrix.project }} \
      --config-output /tmp/config.yaml

    reporting-tool generate \
      --project ${{ matrix.project }} \
      --repos-path ./repos \
      --cache \
      --workers auto \
      --quiet
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

GitLab CI:

```yaml
generate-report:
  script:
    - reporting-tool init --template standard --project $CI_PROJECT_NAME
    - reporting-tool generate --project $CI_PROJECT_NAME --repos-path ./repos --cache --quiet
  artifacts:
    paths:
      - output/
```text

Jenkins:

```groovy
sh """
  reporting-tool init --template standard --project ${PROJECT_NAME}
  reporting-tool generate --project ${PROJECT_NAME} --repos-path ./repos --cache --quiet
"""
```

---

### Q: Can I customize the output format?

**A:** Yes! Use `--output-format`:

```bash
# Generate only HTML
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --output-format html

# Generate only JSON
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --output-format json

# Generate only Markdown
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --output-format md

# Generate all formats (default)
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --output-format all
```text

Skip ZIP archive:

```bash
--no-zip
```

---

### Q: How do I filter or select specific repositories?

**A:** Currently, filtering is done in the configuration file:

```yaml
# config/my-project.yaml
repositories:
  include:
    - "repo-*"           # Include all repos starting with "repo-"
    - "project-core"     # Include specific repo
  exclude:
    - "*-test"           # Exclude test repos
    - "archived-*"       # Exclude archived repos
```text

**Alternative:** Pre-filter the repos directory:

```bash
# Create temporary directory with only desired repos
mkdir -p /tmp/filtered-repos
cp -r ./repos/project-* /tmp/filtered-repos/

# Run report on filtered set
reporting-tool generate --project test --repos-path /tmp/filtered-repos
```

---

### Q: Can I run reports on a schedule?

**A:** Yes! Use cron or system schedulers:

Crontab (Linux/Mac):

```bash
# Edit crontab
crontab -e

# Add daily report at 2 AM
0 2 * * * cd /path/to/project && reporting-tool generate \
  --project daily \
  --repos-path ./repos \
  --cache \
  --quiet \
  --output-dir /reports/$(date +\%Y-\%m-\%d)
```text

systemd timer (Linux):

```ini
# /etc/systemd/system/repo-report.timer
[Unit]
Description=Daily Repository Report

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Windows Task Scheduler:

```powershell
schtasks /create /tn "Repository Report" /tr "reporting-tool generate --project daily --repos-path C:\repos --cache --quiet" /sc daily /st 02:00
```text

---

## Integration

### Q: How do I set up GitHub authentication?

**A:** Export your GitHub Personal Access Token:

```bash
# Set for current session
export GITHUB_TOKEN="ghp_your_token_here"

# Set permanently (Linux/Mac)
echo 'export GITHUB_TOKEN="ghp_your_token_here"' >> ~/.bashrc
source ~/.bashrc

# Set permanently (Windows)
setx GITHUB_TOKEN "ghp_your_token_here"
```

Token requirements:

- **Scope:** `repo` (for private repos) or `public_repo` (for public repos)
- **Type:** Classic token or fine-grained token
- **See:** [GITHUB_TOKEN_REQUIREMENTS.md](../GITHUB_TOKEN_REQUIREMENTS.md)

---

### Q: Do I need both GitHub and Gerrit credentials?

**A:** No, it depends on your repositories:

GitHub only:

```bash
export GITHUB_TOKEN="ghp_xxx"
# No Gerrit credentials needed
```text

Gerrit only:

```bash
export GERRIT_USERNAME="your-username"
export GERRIT_PASSWORD="your-password"
# No GitHub token needed
```

Both:

```bash
export GITHUB_TOKEN="ghp_xxx"
export GERRIT_USERNAME="your-username"
export GERRIT_PASSWORD="your-password"
```text

The tool will only use the credentials it needs based on repository sources.

---

### Q: How do I use environment files (.env)?

**A:** While not natively supported, you can source them:

```bash
# Create .env file
cat > .env << EOF
GITHUB_TOKEN=ghp_xxx
GERRIT_USERNAME=user
GERRIT_PASSWORD=pass
EOF

# Source before running
source .env
reporting-tool generate --project test --repos-path ./repos

# Or inline
env $(cat .env | xargs) reporting-tool generate --project test --repos-path ./repos
```

Using python-dotenv (if installed):

```python
from dotenv import load_dotenv
load_dotenv()

# Now run reporting-tool
```text

---

## Error Handling

### Q: Should I retry on failure?

**A:** Depends on the exit code:

Retry these (transient errors):

- Exit 1 (ERROR) - Network/API issues may resolve
- Exit 2 (PARTIAL) - Some repos may succeed on retry
- Exit 4 (SYSTEM_ERROR) - Resource issues may clear

Don't retry these (permanent errors):

- Exit 3 (USAGE_ERROR) - Syntax won't improve on retry

Example retry logic:

```bash
for i in 1 2 3; do
  reporting-tool generate --project test --repos-path ./repos
  CODE=$?

  # Success - exit
  [ $CODE -eq 0 ] && exit 0

  # Usage error - don't retry
  [ $CODE -eq 3 ] && echo "Fix command syntax" && exit 3

  # Other errors - retry
  echo "Attempt $i failed (code $CODE), retrying in 5s..."
  sleep 5
done

echo "Failed after 3 attempts"
exit 1
```

---

### Q: How do I handle warnings vs errors?

**A:** Check the exit code:

- **Exit 0:** No warnings or errors - use report with confidence
- **Exit 2:** Warnings present - review report, may have gaps
- **Exit 1:** Errors occurred - report may be invalid

Review warnings:

```bash
# Check for warnings in output
reporting-tool generate --project test --repos-path ./repos -v 2>&1 | grep -i warn

# In production, log warnings
reporting-tool generate --project test --repos-path ./repos --quiet 2>&1 | tee report.log
```text

---

## See Also

- [CLI Reference](CLI_REFERENCE.md) - Complete command documentation
- [CLI Guide](CLI_GUIDE.md) - Comprehensive user guide
- [CLI Cheat Sheet](CLI_CHEAT_SHEET.md) - Quick reference
- [Usage Examples](USAGE_EXAMPLES.md) - Real-world scenarios
- [Configuration Wizard Guide](CONFIG_WIZARD_GUIDE.md) - Configuration help

---

**Last Updated:** 2025-01-26
**Version:** 2.0 (Phase 14)

**Have more questions?** Open an issue or check the [CLI Guide](CLI_GUIDE.md) for detailed information.
