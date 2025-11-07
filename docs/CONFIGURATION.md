<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

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

Benefits:

- ✅ Zero to first report in <5 minutes
- ✅ No YAML knowledge required
- ✅ Smart defaults prevent errors
- ✅ Environment auto-detection
- ✅ Validation included

---

## Quick Start

### First-Time Users

Recommended: Interactive wizard

```bash
reporting-tool init
```text

Follow the prompts to create your configuration. Takes ~2 minutes.

### Experienced Users

Quick setup with template

```bash
reporting-tool init --template standard --project my-project
```

Creates a configuration in 10 seconds.

---

## Usage Modes

### 1. Interactive Wizard Mode

Command:

```bash
reporting-tool init [--config-output PATH]
```text

When to use:

- First time using the system
- Want guided configuration
- Need to customize settings
- Learning what options are available

**Time:** ~2 minutes

---

### 2. Template-Based Mode

Command:

```bash
reporting-tool init --template TEMPLATE --project NAME [--config-output PATH]
```

When to use:

- Quick setup needed
- Standard configuration sufficient
- Automation/scripting
- CI/CD pipelines

**Time:** ~10 seconds

---

## Templates

### Minimal Template

**Best for:** Quick testing, simple projects

Includes:

- Project name
- Time windows (365/90 days)
- Output settings (JSON, Markdown, HTML)

What's excluded:

- API integrations
- Feature detection
- Performance settings

Use when:

- Testing the system
- Minimal analysis needed
- Learning the basics

Command:

```bash
reporting-tool init --template minimal --project test-project
```text

---

### Standard Template (Recommended)

**Best for:** Most projects

Includes:

- All minimal template features
- GitHub API integration
- Basic feature detection (CI/CD, security, docs)
- ZIP bundle creation
- Common time windows

What's excluded:

- Gerrit/Jenkins integrations
- Advanced features (Maven, npm, SonarQube)
- Performance tuning

Use when:

- Working with GitHub repositories
- Need standard feature detection
- Want recommended settings

Command:

```bash
reporting-tool init --template standard --project my-project
```

---

### Full Template

**Best for:** Production deployments, advanced users

Includes:

- All standard template features
- All API integrations (GitHub, Gerrit, Jenkins)
- All feature detection
- Performance settings (concurrency, caching)
- Extended time windows

Use when:

- Production deployment
- Multiple API sources
- Performance optimization needed
- Advanced feature detection required

Command:

```bash
reporting-tool init --template full --project production-project
```text

---

## Interactive Wizard

### Step-by-Step Flow

#### Step 1: Template Selection

```

Which template would you like to use?

  1. Minimal - Basic settings only (quickest setup)
→ 2. Standard - Common features and integrations (recommended)
  3. Full - All features and advanced options

```text

**Recommendation:** Start with **Standard** (option 2)

---

#### Step 2: Basic Settings

```

Project name [my-project]: acme-tools

```text

Tips:

- Use lowercase with hyphens (e.g., `acme-tools`)
- Avoid spaces and special characters
- Keep it short and descriptive

---

#### Step 3: Time Windows

```

Use default reporting window (365 days / 1 year)? [Y/n]:
Use default recent activity window (90 days)? [Y/n]:

```text

Common configurations:

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

```text

Recommendations:

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

```text

Environment detection:

- Automatically detects `GITHUB_TOKEN` environment variable
- Shows success message if found
- Warns if not found (optional for public repos)

Tips:

- Enable GitHub for better rate limits
- Only enable Gerrit/Jenkins if you use them

---

#### Step 6: Feature Detection

```

Detect CI/CD systems (GitHub Actions, Jenkins, etc.)? [Y/n]: y
Detect security tools (Dependabot, Snyk, etc.)? [Y/n]: y
Detect documentation tools (ReadTheDocs, etc.)? [Y/n]: y

```text

Recommendations:

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

```text

---

#### Step 8: Save Configuration

```

Configuration file path [config/acme-tools.yaml]:

```text

Path recommendations:

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

```text

---

## Non-Interactive Creation

### Basic Usage

Minimal config:

```bash
reporting-tool init --template minimal --project my-project
```

Standard config:

```bash
reporting-tool init --template standard --project my-project
```text

Full config:

```bash
reporting-tool init --template full --project my-project
```

---

### Custom Output Path

Specify output location:

```bash
reporting-tool init --template standard \
  --project my-project \
  --config-output custom/path/config.yaml
```text

Automatically created paths:

```bash
# Default path (if not specified)
config/my-project.yaml

# Custom path
custom/path/config.yaml
```

---

### Programmatic Usage

From Python code:

```python
from cli.wizard import create_config_from_template

# Create configuration
config_path = create_config_from_template(
    project="my-project",
    template="standard",
    output_path="config/my-project.yaml"
)

print(f"Configuration created: {config_path}")
```text

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
```text

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
```text

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

Solution:

```bash
# Use template-based creation instead
reporting-tool init --template standard --project my-project
```text

---

### Problem: "GITHUB_TOKEN not found" warning

**Cause:** Environment variable not set

Solution:

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

Solution:

```bash
# Use a writable directory
reporting-tool init --config-output ~/config.yaml

# Or create directory first
mkdir -p config
chmod 755 config
reporting-tool init
```text

---

### Problem: Want to change configuration after creation

Solution:

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

Solution:

```bash
# Use dry-run mode
reporting-tool generate --config config/my-project.yaml --dry-run

# Shows validation results:
# ✓ Configuration valid
# ✓ Paths accessible
# ✓ APIs reachable
# ✓ Permissions OK
```text

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
```text

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

Q: Can I run the wizard multiple times?
A: Yes! It will overwrite the existing file. Make a backup first if needed.

Q: Do I need a GitHub token?
A: Optional for public repos, recommended for private repos and better rate limits.

Q: Can I edit the config file after creation?
A: Yes! It's just a YAML file. Edit it with any text editor.

Q: Which template should I use?
A: Standard template is recommended for most users.

Q: Can I use this in CI/CD?
A: Yes! Use `--init-template` for non-interactive creation.

Q: What if I make a mistake?
A: Just run the wizard again, or edit the YAML file directly.

Q: Can I create multiple configurations?
A: Yes! Use `--config-output` to specify different paths.

Q: Is the wizard required?
A: No, you can create config files manually. The wizard just makes it easier.

---

Ready to get started?

```bash
reporting-tool init
```

---

*Configuration Wizard Guide - Phase 13, Step 5*
*Last Updated: 2025-01-XX*

---

## INFO.yaml Reports Configuration

The reporting tool can generate comprehensive INFO.yaml reports that combine project metadata with Git activity analysis.

### Enable INFO.yaml Reports

```yaml
# config.yaml
info_yaml:
  enabled: true

  source:
    type: "git"  # or "local"
    url: "https://gerrit.linuxfoundation.org/infra/info-master"
    branch: "main"
```

### Complete INFO.yaml Configuration

```yaml
info_yaml:
  # Basic Settings
  enabled: true

  # Data Source
  source:
    type: "git"  # "git" or "local"
    url: "https://gerrit.linuxfoundation.org/infra/info-master"
    branch: "main"
    local_path: null  # Use if type is "local"
    update_on_run: true  # Pull updates before processing

  # Filtering
  filters:
    gerrit_servers:  # Only include these servers
      - "gerrit.onap.org"
      - "gerrit.o-ran-sc.org"
    exclude_archived: true  # Exclude archived projects
    exclude_lifecycle_states:  # Exclude these states
      - "End of Life"

  # Activity Windows (days)
  activity_windows:
    current: 365    # Green: 0-365 days
    active: 1095    # Orange: 365-1095 days
    # Red: 1095+ days (implicit)

  # URL Validation
  validation:
    enabled: true
    timeout: 10.0  # seconds
    retries: 2

  # Performance
  performance:
    async_validation: true  # Parallel URL validation
    max_concurrent_urls: 20  # Concurrent requests
    cache_enabled: true
    cache_ttl: 3600  # Cache lifetime (seconds)
    cache_dir: "~/.cache/reporting-tool/info-yaml"
    max_cache_entries: 1000
    max_cache_size_mb: 100

  # Output
  output:
    include_in_report: true
    sections:
      - "committer_report"
      - "lifecycle_summary"
    format: "html"  # "html" or "markdown"
```

### Activity Window Configuration

Control how committer activity is classified:

```yaml
info_yaml:
  activity_windows:
    current: 365   # 🟢 Green: Active within 1 year
    active: 1095   # 🟠 Orange: Active 1-3 years ago
    # 🔴 Red: Inactive 3+ years (automatic)
    # ⚫ Gray: No Git data (automatic)
```

**Color Legend:**

- 🟢 **Green (Current):** Last commit within 365 days
- 🟠 **Orange (Active):** Last commit 365-1095 days ago
- 🔴 **Red (Inactive):** Last commit 1095+ days ago
- ⚫ **Gray (Unknown):** No matching Git data

**Adjust for your project:**

```yaml
# Fast-moving projects (shorter windows)
activity_windows:
  current: 180   # 6 months
  active: 730    # 2 years

# Stable projects (longer windows)
activity_windows:
  current: 730   # 2 years
  active: 1825   # 5 years
```

### Filtering Options

#### Filter by Gerrit Server

```yaml
info_yaml:
  filters:
    gerrit_servers:
      - "gerrit.onap.org"
      - "gerrit.o-ran-sc.org"
      - "gerrit.opnfv.org"
```

#### Filter by Lifecycle State

```yaml
info_yaml:
  filters:
    # Include only these states
    include_lifecycle_states:
      - "Active"
      - "Incubation"

    # Or exclude certain states
    exclude_lifecycle_states:
      - "Archived"
      - "End of Life"

    # Or simply exclude archived
    exclude_archived: true
```

### Performance Optimization

#### Enable Async URL Validation

```yaml
info_yaml:
  performance:
    async_validation: true  # 10x faster validation
    max_concurrent_urls: 30  # Increase for more speed
```

**Benefits:**

- 10x faster than sequential validation
- Validates 100 URLs in ~2 seconds (vs ~20 seconds)
- Configurable concurrency limits

#### Enable Caching

```yaml
info_yaml:
  performance:
    cache_enabled: true
    cache_ttl: 3600  # 1 hour
    cache_dir: "/var/cache/reporting-tool"
    max_cache_entries: 1000
```

**Benefits:**

- 60-80% cache hit rate
- Survives application restarts
- Reduces network requests

### URL Validation Configuration

```yaml
info_yaml:
  validation:
    enabled: true
    timeout: 10.0  # Seconds to wait for response
    retries: 2     # Number of retry attempts
```

**Adjust for reliability:**

```yaml
# For slow or unreliable servers
validation:
  timeout: 15.0
  retries: 3

# For fast networks
validation:
  timeout: 5.0
  retries: 1

# Disable for speed (not recommended)
validation:
  enabled: false
```

### Local INFO.yaml Repository

Use a local clone for faster iteration:

```yaml
info_yaml:
  source:
    type: "local"
    local_path: "/data/info-master"
    update_on_run: false  # Don't pull updates
```

```bash
# One-time setup
git clone https://gerrit.linuxfoundation.org/infra/info-master /data/info-master

# Fast subsequent runs
reporting-tool generate --config config.yaml
```

### Environment Variables

Override configuration with environment variables:

```bash
# Enable/disable
export REPORTING_TOOL_INFO_YAML_ENABLED=true

# Data source
export REPORTING_TOOL_INFO_YAML_SOURCE_URL="https://gerrit.linuxfoundation.org/infra/info-master"
export REPORTING_TOOL_INFO_YAML_SOURCE_LOCAL_PATH="/data/info-master"

# Performance
export REPORTING_TOOL_INFO_YAML_ASYNC_VALIDATION=true
export REPORTING_TOOL_INFO_YAML_MAX_CONCURRENT_URLS=30
export REPORTING_TOOL_INFO_YAML_CACHE_ENABLED=true

# Activity windows
export REPORTING_TOOL_INFO_YAML_ACTIVITY_WINDOW_CURRENT=365
export REPORTING_TOOL_INFO_YAML_ACTIVITY_WINDOW_ACTIVE=1095
```

### Configuration Examples

#### Example 1: Development Setup

```yaml
info_yaml:
  enabled: true
  source:
    type: "local"
    local_path: "./info-master"
  validation:
    enabled: false  # Skip for speed
  performance:
    cache_enabled: false  # Fresh data each run
```

#### Example 2: Production Setup

```yaml
info_yaml:
  enabled: true
  source:
    type: "git"
    url: "https://gerrit.linuxfoundation.org/infra/info-master"
    update_on_run: true
  performance:
    async_validation: true
    max_concurrent_urls: 20
    cache_enabled: true
    cache_ttl: 3600
  validation:
    enabled: true
    timeout: 10.0
    retries: 2
  filters:
    exclude_archived: true
```

#### Example 3: High-Performance Setup

```yaml
info_yaml:
  enabled: true
  performance:
    async_validation: true
    max_concurrent_urls: 50  # Maximum concurrency
    cache_enabled: true
    cache_ttl: 7200  # 2-hour cache
    cache_dir: "/dev/shm/reporting-cache"  # Use RAM disk
```

#### Example 4: Filtered Report

```yaml
info_yaml:
  enabled: true
  filters:
    gerrit_servers:
      - "gerrit.onap.org"  # ONAP only
    lifecycle_states:
      - "Active"  # Active projects only
    exclude_archived: true
  activity_windows:
    current: 180  # 6 months for active threshold
    active: 730   # 2 years for orange
```

### Validation

Test your configuration before running:

```bash
# Dry run to validate config
reporting-tool generate --config config.yaml --dry-run

# Check INFO.yaml-specific config
reporting-tool config show | grep -A 20 "info_yaml:"
```

### Troubleshooting Configuration

#### Issue: INFO.yaml data not appearing

**Check:**

```bash
# Verify enabled
grep "enabled: true" config.yaml

# Verify source configured
grep -A 5 "info_yaml:" config.yaml
```

#### Issue: Slow performance

**Solution:**

```yaml
# Enable async + caching
info_yaml:
  performance:
    async_validation: true
    max_concurrent_urls: 30
    cache_enabled: true
```

#### Issue: Wrong activity colors

**Solution:**

```yaml
# Adjust activity windows
info_yaml:
  activity_windows:
    current: 180   # Shorter window
    active: 730    # Adjust to your needs
```

---

**Related Documentation:**

- [Usage Examples](USAGE_EXAMPLES.md) - INFO.yaml usage examples
- [Troubleshooting](TROUBLESHOOTING.md) - Common INFO.yaml issues
- [Performance](PERFORMANCE.md) - Optimization strategies

---

## GitHub API Authentication

The reporting tool can integrate with GitHub's API to fetch additional repository data such as workflow status, pull requests, and other metadata.

### Token Types

GitHub offers two types of Personal Access Tokens (PAT):

| Type | Multi-Organization | Use Case |
|------|-------------------|----------|
| **Classic PAT** | ✅ Yes | **Recommended** - Works across all organizations |
| **Fine-Grained PAT** | ❌ No | Single organization only |

**For cross-organization reporting, you MUST use a Classic PAT.**

### Creating a Classic Personal Access Token

1. **Navigate to GitHub Settings**
   - Go to <https://github.com/settings/tokens>
   - Or: Profile → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generate New Token (Classic)**
   - Click "Generate new token (classic)"
   - Give it a descriptive name: `reporting-tool-access`
   - Set expiration (recommend 90 days or custom)

3. **Select Scopes**

   **Required scopes:**
   - ☑ `repo` - Repository access (read metadata and workflows)
   - ☑ `actions:read` - Read workflow runs and status

   **Optional but recommended:**
   - ☑ `read:org` - Read organization membership
   - ☑ `read:user` - Read user profiles

4. **Generate and Save Token**
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)
   - Store securely (password manager, secrets management system)

### Configuration

#### Option 1: Environment Variable (Recommended)

```bash
# Set environment variable
export GITHUB_TOKEN=ghp_your_token_here

# Run tool
reporting-tool generate --project my-project --repos-path ./repos
```

#### Option 2: Configuration File

```yaml
# config/my-project.yaml
github_api:
  enabled: true
  token: ghp_your_token_here  # Not recommended for version control
```

**⚠️ Warning:** Never commit tokens to version control!

#### Option 3: Separate Secrets File

```yaml
# config/my-project.yaml
github_api:
  enabled: true
  token_file: ~/.secrets/github-token.txt
```

```bash
# ~/.secrets/github-token.txt
ghp_your_token_here
```

```bash
# Secure the file
chmod 600 ~/.secrets/github-token.txt
```

### GitHub API Configuration Options

```yaml
github_api:
  # Enable/disable GitHub API integration
  enabled: true

  # Authentication
  token: ghp_your_token_here          # Direct token (not recommended)
  token_env: "GITHUB_TOKEN"            # Environment variable name
  token_file: ~/.secrets/github-token.txt  # Token file path

  # Rate Limiting
  rate_limit:
    requests_per_hour: 5000  # GitHub default for authenticated
    retry_on_limit: true     # Wait and retry when rate limited
    retry_delay: 60          # Seconds to wait before retry

  # Timeouts
  timeout: 30.0  # Request timeout in seconds

  # Features
  features:
    fetch_workflows: true     # Fetch GitHub Actions workflow data
    fetch_pull_requests: true # Fetch PR data
    fetch_issues: true        # Fetch issues data
    fetch_releases: true      # Fetch releases data
```

### Testing Your Token

```bash
# Test token validity
curl -H "Authorization: token ghp_your_token_here" \
  https://api.github.com/user

# Check rate limit
curl -H "Authorization: token ghp_your_token_here" \
  https://api.github.com/rate_limit

# Test with the tool
reporting-tool generate \
  --project test \
  --repos-path ./repos \
  --dry-run \
  --verbose
```

### Token Security Best Practices

1. **Never commit tokens to version control**

   ```bash
   # Add to .gitignore
   echo "*.token.txt" >> .gitignore
   echo "*secrets*" >> .gitignore
   ```

2. **Use environment variables in CI/CD**

   ```yaml
   # GitHub Actions
   env:
     GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

   # GitLab CI
   variables:
     GITHUB_TOKEN: $GITHUB_TOKEN
   ```

3. **Rotate tokens regularly**
   - Set expiration dates
   - Generate new tokens quarterly
   - Revoke old tokens immediately

4. **Use minimal scopes**
   - Only grant necessary permissions
   - Avoid `admin:*` or `delete:*` scopes
   - Review scope requirements periodically

5. **Store securely**
   - Use password managers (1Password, LastPass, etc.)
   - Use secrets management (HashiCorp Vault, AWS Secrets Manager)
   - Encrypt at rest

### Multi-Organization Access

For cross-organization reporting:

```yaml
github_api:
  enabled: true
  token_env: "GITHUB_TOKEN"

  # Organizations to query
  organizations:
    - "onap"
    - "opendaylight"
    - "o-ran-sc"
    - "lfnetworking"
```

**Requirements:**

- Classic PAT (not fine-grained)
- User must be member of all listed organizations
- `repo` and `actions:read` scopes required

### Rate Limiting

GitHub API has rate limits:

| Authentication | Requests/Hour |
|---------------|---------------|
| Unauthenticated | 60 |
| Authenticated (PAT) | 5,000 |
| GitHub Actions | 1,000 (per repository) |

**Handle rate limits:**

```yaml
github_api:
  rate_limit:
    retry_on_limit: true
    retry_delay: 60
    max_retries: 3
```

**Monitor rate limits:**

```bash
# Check remaining quota
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit | jq '.rate'
```

### Troubleshooting

#### "Bad credentials" Error

**Cause:** Invalid or expired token

**Solution:**

```bash
# Verify token
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# Generate new token if expired
# Update configuration with new token
```

#### "Not Found" Error for Private Repos

**Cause:** Token lacks `repo` scope

**Solution:**

- Regenerate token with `repo` scope
- Update token in configuration

#### Rate Limit Exceeded

**Cause:** Too many API requests

**Solution:**

```yaml
# Enable caching
github_api:
  caching:
    enabled: true
    ttl: 3600  # Cache for 1 hour

# Reduce request frequency
github_api:
  rate_limit:
    retry_on_limit: true
    retry_delay: 120  # Wait 2 minutes
```

#### "Resource not accessible by token" Error

**Cause:** Missing organization membership or scope

**Solution:**

1. Verify organization membership
2. Ensure Classic PAT (not fine-grained)
3. Check `read:org` scope if needed

### Advanced Configuration

#### Proxy Support

```yaml
github_api:
  proxy:
    http: http://proxy.example.com:8080
    https: https://proxy.example.com:8443
    no_proxy: localhost,127.0.0.1
```

#### Custom GitHub Enterprise

```yaml
github_api:
  base_url: https://github.enterprise.com/api/v3
  token_env: "GHE_TOKEN"
```

#### Retry Strategy

```yaml
github_api:
  retry:
    max_attempts: 3
    backoff_factor: 2  # Exponential backoff
    status_codes: [429, 500, 502, 503, 504]
```

### Performance Optimization

```yaml
github_api:
  # Enable caching
  caching:
    enabled: true
    ttl: 3600
    max_entries: 1000

  # Parallel requests
  concurrency:
    enabled: true
    max_workers: 10

  # Request batching
  batching:
    enabled: true
    batch_size: 100
```

### CI/CD Integration

#### GitHub Actions

```yaml
name: Generate Reports
on: [push]

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Generate Report
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          reporting-tool generate \
            --project my-project \
            --repos-path ./repos
```

#### GitLab CI

```yaml
generate-report:
  script:
    - reporting-tool generate --project my-project --repos-path ./repos
  variables:
    GITHUB_TOKEN: $GITHUB_TOKEN
```

---

**Related Documentation:**

- [Getting Started](GETTING_STARTED.md) - Setup and first report
- [Usage Examples](USAGE_EXAMPLES.md) - GitHub API usage examples
- [Troubleshooting](TROUBLESHOOTING.md) - Common GitHub API issues
- [CI/CD Integration](CI_CD_INTEGRATION.md) - Automation setup
