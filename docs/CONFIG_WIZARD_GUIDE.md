# Configuration Wizard - Quick Reference Guide

**Quick Start:** Creating your first configuration in under 2 minutes

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Usage Modes](#usage-modes)
- [Templates](#templates)
- [Interactive Wizard](#interactive-wizard)
- [Non-Interactive Creation](#non-interactive-creation)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

---

## Overview

The Configuration Wizard helps you create valid configuration files for the Repository Reporting System without manual YAML editing. Choose from three templates based on your needs, or use the interactive wizard for guided setup.

**Benefits:**

- ✅ Zero to first report in <5 minutes
- ✅ No YAML knowledge required
- ✅ Smart defaults prevent errors
- ✅ Environment auto-detection
- ✅ Validation included

---

## Quick Start

### First-Time Users

**Recommended: Interactive wizard**

```bash
reporting-tool init
```

Follow the prompts to create your configuration. Takes ~2 minutes.

### Experienced Users

**Quick setup with template**

```bash
reporting-tool init --template standard --project my-project
```

Creates a configuration in 10 seconds.

---

## Usage Modes

### 1. Interactive Wizard Mode

**Command:**

```bash
reporting-tool init [--config-output PATH]
```

**When to use:**

- First time using the system
- Want guided configuration
- Need to customize settings
- Learning what options are available

**Time:** ~2 minutes

---

### 2. Template-Based Mode

**Command:**

```bash
reporting-tool init --template TEMPLATE --project NAME [--config-output PATH]
```

**When to use:**

- Quick setup needed
- Standard configuration sufficient
- Automation/scripting
- CI/CD pipelines

**Time:** ~10 seconds

---

## Templates

### Minimal Template

**Best for:** Quick testing, simple projects

**Includes:**

- Project name
- Time windows (365/90 days)
- Output settings (JSON, Markdown, HTML)

**What's excluded:**

- API integrations
- Feature detection
- Performance settings

**Use when:**

- Testing the system
- Minimal analysis needed
- Learning the basics

**Command:**

```bash
reporting-tool init --template minimal --project test-project
```

---

### Standard Template (Recommended)

**Best for:** Most projects

**Includes:**

- All minimal template features
- GitHub API integration
- Basic feature detection (CI/CD, security, docs)
- ZIP bundle creation
- Common time windows

**What's excluded:**

- Gerrit/Jenkins integrations
- Advanced features (Maven, npm, SonarQube)
- Performance tuning

**Use when:**

- Working with GitHub repositories
- Need standard feature detection
- Want recommended settings

**Command:**

```bash
reporting-tool init --template standard --project my-project
```

---

### Full Template

**Best for:** Production deployments, advanced users

**Includes:**

- All standard template features
- All API integrations (GitHub, Gerrit, Jenkins)
- All feature detection
- Performance settings (concurrency, caching)
- Extended time windows

**Use when:**

- Production deployment
- Multiple API sources
- Performance optimization needed
- Advanced feature detection required

**Command:**

```bash
reporting-tool init --template full --project production-project
```

---

## Interactive Wizard

### Step-by-Step Flow

#### Step 1: Template Selection

```
Which template would you like to use?
  1. Minimal - Basic settings only (quickest setup)
→ 2. Standard - Common features and integrations (recommended)
  3. Full - All features and advanced options
```

**Recommendation:** Start with **Standard** (option 2)

---

#### Step 2: Basic Settings

```
Project name [my-project]: acme-tools
```

**Tips:**

- Use lowercase with hyphens (e.g., `acme-tools`)
- Avoid spaces and special characters
- Keep it short and descriptive

---

#### Step 3: Time Windows

```
Use default reporting window (365 days / 1 year)? [Y/n]:
Use default recent activity window (90 days)? [Y/n]:
```

**Common configurations:**

- **365/90 days:** Annual reports (default, recommended)
- **90/30 days:** Quarterly reports
- **30/7 days:** Monthly reports
- **1095/365 days:** Three-year analysis

---

#### Step 4: Output Settings

```
Output directory [output]: reports

Output formats:
  Generate JSON? [Y/n]: y
  Generate Markdown? [Y/n]: y
  Generate HTML? [Y/n]: y

Create ZIP bundle of all reports? [Y/n]: y
```

**Recommendations:**

- **All formats:** Most flexible (default)
- **JSON only:** For programmatic use
- **HTML only:** For human viewing
- **ZIP bundle:** Yes for archival

---

#### Step 5: API Integrations

```
GitHub API:
  Enable GitHub API integration? [Y/n]: y

Gerrit API:
  Enable Gerrit integration? [y/N]: n
```

**Environment detection:**

- Automatically detects `GITHUB_TOKEN` environment variable
- Shows success message if found
- Warns if not found (optional for public repos)

**Tips:**

- Enable GitHub for better rate limits
- Only enable Gerrit/Jenkins if you use them

---

#### Step 6: Feature Detection

```
Detect CI/CD systems (GitHub Actions, Jenkins, etc.)? [Y/n]: y
Detect security tools (Dependabot, Snyk, etc.)? [Y/n]: y
Detect documentation tools (ReadTheDocs, etc.)? [Y/n]: y
```

**Recommendations:**

- Enable all for comprehensive analysis
- Disable if you don't need specific categories

---

#### Step 7: Performance Settings (Full template only)

```
Concurrency:
  Enable parallel processing? [Y/n]: y
  Number of worker threads [4]: 8

Caching:
  Enable caching? [Y/n]: y
  Cache directory [.cache]:
  Cache TTL (hours) [24]: 48
```

---

#### Step 8: Save Configuration

```
Configuration file path [config/acme-tools.yaml]:
```

**Path recommendations:**

- Default: `config/{project}.yaml` (recommended)
- Custom: Any path you prefer
- Directories created automatically

---

### Next Steps After Wizard

The wizard shows you what to do next:

```
1. Review your configuration:
   cat config/acme-tools.yaml

2. Validate your setup:
   reporting-tool generate --config config/acme-tools.yaml --dry-run

3. Generate your first report:
   reporting-tool generate --project acme-tools \
     --config config/acme-tools.yaml \
     --repos-path /path/to/repositories
```

---

## Non-Interactive Creation

### Basic Usage

**Minimal config:**

```bash
reporting-tool init --template minimal --project my-project
```

**Standard config:**

```bash
reporting-tool init --template standard --project my-project
```

**Full config:**

```bash
reporting-tool init --template full --project my-project
```

---

### Custom Output Path

**Specify output location:**

```bash
reporting-tool init --template standard \
  --project my-project \
  --config-output custom/path/config.yaml
```

**Automatically created paths:**

```bash
# Default path (if not specified)
config/my-project.yaml

# Custom path
custom/path/config.yaml
```

---

### Programmatic Usage

**From Python code:**

```python
from cli.wizard import create_config_from_template

# Create configuration
config_path = create_config_from_template(
    project="my-project",
    template="standard",
    output_path="config/my-project.yaml"
)

print(f"Configuration created: {config_path}")
```

---

## Examples

### Example 1: First-Time Setup

**Scenario:** New user, first time using the system

```bash
# Step 1: Run interactive wizard
reporting-tool init

# Answer prompts:
# - Template: 2 (standard)
# - Project: acme-tools
# - Accept all defaults
# - Enable GitHub API
# - Enable all features

# Step 2: Review generated config
cat config/acme-tools.yaml

# Step 3: Validate
reporting-tool generate --config config/acme-tools.yaml --dry-run

# Step 4: Generate report
reporting-tool generate --project acme-tools \
  --config config/acme-tools.yaml \
  --repos-path /workspace/repos
```

**Time:** ~5 minutes total

---

### Example 2: Quick Testing

**Scenario:** Quick test with minimal setup

```bash
# Create minimal config (10 seconds)
reporting-tool init --template minimal --project test

# Generate report immediately
reporting-tool generate --project test \
  --repos-path /tmp/test-repos \
  --quiet
```

**Time:** ~30 seconds

---

### Example 3: Production Deployment

**Scenario:** Production environment with all features

```bash
# Create full config
reporting-tool init --template full \
  --project production \
  --config-output /etc/repo-reports/config.yaml

# Edit to customize (optional)
vim /etc/repo-reports/config.yaml

# Validate configuration
reporting-tool generate \
  --config /etc/repo-reports/config.yaml \
  --dry-run

# Generate reports
reporting-tool generate --project production \
  --config /etc/repo-reports/config.yaml \
  --repos-path /data/repositories \
  --workers 16 \
  --cache
```

---

### Example 4: CI/CD Pipeline

**Scenario:** Automated configuration in GitHub Actions

```yaml
# .github/workflows/reports.yml
name: Generate Reports

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Create configuration
        run: |
          reporting-tool init --template standard \
            --project ${{ github.repository }} \
            --config-output /tmp/config.yaml

      - name: Generate reports
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          reporting-tool generate --project ${{ github.repository }} \
            --config /tmp/config.yaml \
            --repos-path ./repos \
            --quiet

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: reports
          path: output/
```

---

### Example 5: Multiple Projects

**Scenario:** Create configs for multiple projects

```bash
# Create configs for each project
for project in api-gateway user-service data-processor; do
  reporting-tool init --template standard \
    --project "$project" \
    --config-output "config/${project}.yaml"
done

# Generate reports for all
for config in config/*.yaml; do
  project=$(basename "$config" .yaml)
  reporting-tool generate --project "$project" \
    --config "$config" \
    --repos-path "repos/$project"
done
```

---

## Troubleshooting

### Problem: Wizard exits immediately

**Cause:** Terminal doesn't support interactive input

**Solution:**

```bash
# Use template-based creation instead
reporting-tool init --template standard --project my-project
```

---

### Problem: "GITHUB_TOKEN not found" warning

**Cause:** Environment variable not set

**Solution:**

```bash
# Set token (Linux/macOS)
export GITHUB_TOKEN=ghp_your_token_here

# Set token (Windows)
set GITHUB_TOKEN=ghp_your_token_here

# Or run without token (public repos only, lower rate limits)
reporting-tool init
```

---

### Problem: Permission denied when saving config

**Cause:** Output directory not writable

**Solution:**

```bash
# Use a writable directory
reporting-tool init --config-output ~/config.yaml

# Or create directory first
mkdir -p config
chmod 755 config
reporting-tool init
```

---

### Problem: Want to change configuration after creation

**Solution:**

```bash
# Option 1: Edit the YAML file directly
vim config/my-project.yaml

# Option 2: Re-run the wizard
reporting-tool init --config-output config/my-project.yaml
# (overwrites existing file)

# Option 3: Create new config with different name
reporting-tool init --config-output config/my-project-v2.yaml
```

---

### Problem: Need to validate configuration

**Solution:**

```bash
# Use dry-run mode
reporting-tool generate --config config/my-project.yaml --dry-run

# Shows validation results:
# ✓ Configuration valid
# ✓ Paths accessible
# ✓ APIs reachable
# ✓ Permissions OK
```

---

## Next Steps

### After Creating Configuration

1. **Review the configuration file**

   ```bash
   cat config/my-project.yaml
   ```

2. **Validate your setup**

   ```bash
   reporting-tool generate --config config/my-project.yaml --dry-run
   ```

3. **Generate your first report**

   ```bash
   reporting-tool generate --project my-project \
     --config config/my-project.yaml \
     --repos-path /path/to/repos
   ```

4. **Review the output**

   ```bash
   # JSON data
   cat output/my-project.json | jq .

   # Markdown report
   cat output/my-project.md

   # HTML report
   open output/my-project.html
   ```

---

### Further Reading

- **[CLI Reference](CLI_REFERENCE.md)** - All command-line options
- **[Quick Start Guide](QUICK_START.md)** - Complete getting started guide
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Configuration Schema](../config/README.md)** - YAML configuration details

---

## Template Comparison

| Feature | Minimal | Standard | Full |
|---------|---------|----------|------|
| **Setup Time** | 30 sec | 2 min | 4 min |
| **Project name** | ✓ | ✓ | ✓ |
| **Time windows** | ✓ | ✓ | ✓ |
| **Output formats** | ✓ | ✓ | ✓ |
| **ZIP bundle** | ✗ | ✓ | ✓ |
| **GitHub API** | ✗ | ✓ | ✓ |
| **Gerrit API** | ✗ | ✗ | ✓ |
| **Jenkins API** | ✗ | ✗ | ✓ |
| **Basic features** | ✗ | ✓ | ✓ |
| **All features** | ✗ | ✗ | ✓ |
| **Performance** | ✗ | ✗ | ✓ |
| **Best for** | Testing | Most users | Production |

---

## Command Reference

### Interactive Mode

```bash
reporting-tool init [OPTIONS]

Options:
  --config-output PATH    Output path for config file
```

### Template Mode

```bash
reporting-tool init --template TEMPLATE --project NAME [OPTIONS]

Required:
  --project NAME          Project name
  --init-template TYPE    Template: minimal, standard, or full

Optional:
  --config-output PATH    Output path (default: config/{project}.yaml)
```

---

## Tips & Best Practices

### 1. Start Simple

Begin with the **minimal** or **standard** template, then customize as needed.

### 2. Use Defaults

The wizard's defaults are carefully chosen. Press Enter to accept them.

### 3. Review Before Running

Always review the generated config file before your first report.

### 4. Validate First

Use `--dry-run` to validate your configuration before generating reports.

### 5. Version Control

Check your configuration files into version control for team consistency.

### 6. Template Reuse

Save customized configs as templates for future projects.

### 7. Environment Variables

Use `GITHUB_TOKEN` for better API rate limits (recommended).

### 8. Automation

Use template mode (`--init-template`) for scripting and CI/CD.

---

## FAQ

**Q: Can I run the wizard multiple times?**
A: Yes! It will overwrite the existing file. Make a backup first if needed.

**Q: Do I need a GitHub token?**
A: Optional for public repos, recommended for private repos and better rate limits.

**Q: Can I edit the config file after creation?**
A: Yes! It's just a YAML file. Edit it with any text editor.

**Q: Which template should I use?**
A: Standard template is recommended for most users.

**Q: Can I use this in CI/CD?**
A: Yes! Use `--init-template` for non-interactive creation.

**Q: What if I make a mistake?**
A: Just run the wizard again, or edit the YAML file directly.

**Q: Can I create multiple configurations?**
A: Yes! Use `--config-output` to specify different paths.

**Q: Is the wizard required?**
A: No, you can create config files manually. The wizard just makes it easier.

---

**Ready to get started?**

```bash
reporting-tool init
```

---

*Configuration Wizard Guide - Phase 13, Step 5*
*Last Updated: 2025-01-XX*
