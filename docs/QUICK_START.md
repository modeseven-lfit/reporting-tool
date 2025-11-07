# Quick Start Guide

**Repository Analysis Report Generator**

Get up and running in 5 minutes or less!

Version: 3.0
Last Updated: 2025-01-30
Phase: 15 - Typer CLI Migration

---

## Prerequisites

- Python 3.10 or higher (currently supported: 3.10, 3.11, 3.12, 3.13)
- Git repositories to analyze (cloned locally)
- Basic understanding of YAML configuration

### Optional

- GitHub personal access token (for GitHub API features)
- Gerrit credentials (if using Gerrit)
- Jenkins credentials (if using Jenkins)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/project-reports.git
cd project-reports
```

### 2. Install Dependencies

**Recommended: Using UV (faster)**

```bash
uv sync
```

**Alternative: Using pip**

```bash
pip install .
```

**Verify installation:**

```bash
reporting-tool --version
```

---

## First Run: 3 Easy Steps

### Step 1: Prepare Your Repositories

Ensure your Git repositories are cloned in a directory:

```bash
# Example structure
/workspace/repos/
  ├── repo-1/
  ├── repo-2/
  └── repo-3/
```

### Step 2: Create Configuration

Use the interactive configuration wizard:

```bash
reporting-tool init --project my-project
```

**Or** use a template for quick setup:

```bash
reporting-tool init --project my-project --template standard
```

The wizard will create `config/my-project.yaml` with your settings:

```yaml
project: my-project
repositories_path: /workspace/repos
output_directory: ./output

time_windows:
  1y:
    days: 365
  90d:
    days: 90
  30d:
    days: 30

activity_thresholds:
  active_days: 365
  current_days: 90
  inactive_days: 730
```

### Step 3: Generate Your First Report

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos
```

**That's it!** Your reports will be in `./output/`

---

## Understanding the Output

After running, you'll find:

```
output/
├── my-project_report.html     # Interactive HTML report
├── my-project_report.json     # Raw JSON data
├── my-project_report.md       # Markdown summary
└── my-project_reports.zip     # Bundled archive
```

### View the Report

```bash
# Open HTML report in browser
open output/my-project_report.html

# Or on Linux
xdg-open output/my-project_report.html
```

---

## Common Use Cases

### Use Case 1: Single Project

You have one project with multiple repositories:

```bash
reporting-tool generate \
  --project kubernetes \
  --repos-path /workspace/k8s-repos
```

### Use Case 2: Multiple Projects

Create project-specific configs:

```bash
# Create configs for each project
reporting-tool init --project project-a --template standard
reporting-tool init --project project-b --template standard

# Edit configs if needed
vim config/project-a.yaml
vim config/project-b.yaml

# Generate reports
reporting-tool generate --project project-a --repos-path /repos/project-a
reporting-tool generate --project project-b --repos-path /repos/project-b
```

### Use Case 3: GitHub Integration

Enable GitHub features (Actions status, Dependabot, etc.):

```bash
# Set your token
export GITHUB_TOKEN="ghp_your_token_here"

# Or add to config
cat >> config/my-project.yaml << EOF
api:
  github:
    enabled: true
    token: "\${GITHUB_TOKEN}"
EOF

# Run with GitHub features
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos
```

### Use Case 4: Quick Validation

Before generating a full report, validate your setup:

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --dry-run
```

Output:

```
🔍 Running pre-flight validation checks...

✅ Configuration validation: PASSED
✅ Path validation: PASSED
✅ API connectivity: PASSED
✅ System resources: PASSED

All checks passed! Ready to generate reports.
```

### Use Case 5: Validate Configuration File

Check your configuration file for errors:

```bash
reporting-tool validate --config config/my-project.yaml
```

---

## New CLI Features

### Shell Completion

Enable auto-completion for faster command entry:

```bash
# Bash
reporting-tool --install-completion bash

# Zsh
reporting-tool --install-completion zsh

# Fish
reporting-tool --install-completion fish
```

After installation, restart your shell and enjoy tab completion!

### List Available Features

See what the tool can detect in your repositories:

```bash
reporting-tool list-features
```

### Contextual Help

Get help for any command:

```bash
reporting-tool --help
reporting-tool generate --help
reporting-tool init --help
reporting-tool list-features --help
reporting-tool validate --help
```

---

## Configuration Tips

### Minimal Configuration

The absolute minimum config (created by `init`):

```yaml
project: my-project
repositories_path: /workspace/repos

time_windows:
  90d:
    days: 90

activity_thresholds:
  active_days: 365
  current_days: 90
```

### Recommended Configuration

For better results, add:

```yaml
project: my-project
repositories_path: /workspace/repos
output_directory: ./output

time_windows:
  1y:
    days: 365
  90d:
    days: 90
  30d:
    days: 30

activity_thresholds:
  active_days: 365
  current_days: 90
  inactive_days: 730

api:
  github:
    enabled: true
    token: "${GITHUB_TOKEN}"

privacy:
  anonymize_emails: false

performance:
  max_workers: 8
  cache_enabled: true
```

---

## Performance Tips

### Enable Caching (10-100x Faster)

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --cache
```

**First run:** Slow (analyzes all repos)
**Subsequent runs:** Fast (uses cached metrics)

**Clear cache when needed:**

```bash
rm -rf .cache/repo-metrics/
```

### Increase Parallelism

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --workers 16
```

Default is CPU count. Increase for more parallelism.

### Generate Only What You Need

```bash
# Only JSON (fastest)
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --output-format json

# Only HTML (for viewing)
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --output-format html \
  --no-zip
```

---

## Troubleshooting

### Problem: "Command not found: reporting-tool"

**Solution:** Make sure the package is installed:

```bash
# Check installation
reporting-tool --version

# If not installed, install it
uv sync
# or
pip install .
```

### Problem: "Configuration file not found"

```bash
# Create config with wizard
reporting-tool init --project my-project

# Or use a template
reporting-tool init --project my-project --template standard

# Or specify custom location
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --config-dir /path/to/config
```

### Problem: "GitHub API rate limit exceeded"

**Solution:** Use a personal access token:

```bash
# Create token at: https://github.com/settings/tokens
# Needs: repo (read), workflow (read)

export GITHUB_TOKEN="ghp_your_token_here"
```

### Problem: Reports are slow to generate

**Solutions:**

1. **Enable caching:**

   ```bash
   reporting-tool generate --project my-project --repos-path /workspace/repos --cache
   ```

2. **Increase workers:**

   ```bash
   reporting-tool generate --project my-project --repos-path /workspace/repos --workers 16
   ```

3. **Reduce time windows:**

   ```yaml
   # Only analyze last 90 days
   time_windows:
     90d:
       days: 90
   ```

4. **Generate specific format:**

   ```bash
   reporting-tool generate --project my-project --repos-path /workspace/repos --output-format json
   ```

### Problem: Not sure what went wrong

**Enable verbose logging:**

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  -vv
```

---

## Next Steps

### Learn More

- 📖 [CLI Reference](CLI_REFERENCE.md) - Complete command reference
- 📖 [CLI Guide](CLI_GUIDE.md) - Comprehensive CLI documentation
- 📖 [Configuration Guide](CONFIGURATION.md) - Advanced configuration
- 📖 [Usage Examples](USAGE_EXAMPLES.md) - More examples and workflows
- 📖 [Typer Migration Guide](TYPER_CLI_MIGRATION.md) - Upgrading from v1.x
- 📖 [Troubleshooting](TROUBLESHOOTING.md) - Detailed error solutions

### Explore Features

```bash
# See all available features
reporting-tool list-features

# Check your configuration
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --show-config

# Validate configuration file
reporting-tool validate --config config/my-project.yaml
```

### Automate Reports

Create a simple script:

```bash
#!/bin/bash
# daily-report.sh

PROJECT="my-project"
REPOS="/workspace/repos"
OUTPUT="/reports/$(date +%Y-%m-%d)"

reporting-tool generate \
  --project "$PROJECT" \
  --repos-path "$REPOS" \
  --output-dir "$OUTPUT" \
  --cache \
  --quiet

echo "Report generated: $OUTPUT"
```

Schedule with cron:

```bash
# Run daily at 2 AM
0 2 * * * /path/to/daily-report.sh
```

---

## Example: Complete Workflow

Here's a complete workflow from scratch:

```bash
# 1. Setup
mkdir -p workspace/repos
cd workspace/repos
git clone https://github.com/org/repo1.git
git clone https://github.com/org/repo2.git
cd ../..

# 2. Install
uv sync

# 3. Configure (interactive)
reporting-tool init --project my-project

# 4. Validate
reporting-tool generate \
  --project my-project \
  --repos-path workspace/repos \
  --dry-run

# 5. Generate (first run)
reporting-tool generate \
  --project my-project \
  --repos-path workspace/repos \
  -v

# 6. Generate (subsequent runs with cache)
reporting-tool generate \
  --project my-project \
  --repos-path workspace/repos \
  --cache \
  -v

# 7. View results
open output/my-project_report.html
```

---

## Migrating from v1.x?

If you're upgrading from the old `reporting-tool generate` command structure:

**Old way:**

```bash
reporting-tool generate --project my-project --repos-path ./repos
```

**New way:**

```bash
reporting-tool generate --project my-project --repos-path ./repos
```

See the **[Typer Migration Guide](TYPER_CLI_MIGRATION.md)** for complete migration instructions and a detailed command mapping.

---

## Tips for Success

1. **Start simple** - Use `init` with a template and add features as needed
2. **Validate first** - Always run `--dry-run` before full generation
3. **Use caching** - Speeds up subsequent runs dramatically
4. **Enable completion** - Tab completion makes commands faster to type
5. **Check logs** - Use `-v` or `-vv` to see what's happening
6. **Read errors carefully** - Error messages include helpful suggestions
7. **Validate configs** - Use `reporting-tool validate` to check configuration files

---

## Getting Help

### Built-in Help

```bash
reporting-tool --help
reporting-tool generate --help
```

### Check Version

```bash
reporting-tool --version
```

### List Features

```bash
reporting-tool list-features
```

### Validation

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --dry-run
```

### Validate Config

```bash
reporting-tool validate --config config/my-project.yaml
```

### Verbose Output

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  -vv
```

### Documentation

- [CLI Quick Start](CLI_QUICK_START.md)
- [CLI Guide](CLI_GUIDE.md)
- [CLI Reference](CLI_REFERENCE.md)
- [Configuration Guide](CONFIGURATION.md)
- [Troubleshooting](TROUBLESHOOTING.md)

---

## Subcommand Overview

| Command | Purpose | Example |
|---------|---------|---------|
| `generate` | Generate reports | `reporting-tool generate --project my-proj --repos-path ./repos` |
| `init` | Initialize configuration | `reporting-tool init --project my-proj` |
| `list-features` | Show available features | `reporting-tool list-features` |
| `validate` | Validate config file | `reporting-tool validate --config config/my-proj.yaml` |

---

**Welcome aboard! Happy reporting! 🚀**

---

Last Updated: 2025-01-30
Version: 3.0 (Phase 15 - Typer CLI Migration)
