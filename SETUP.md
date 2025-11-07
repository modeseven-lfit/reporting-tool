<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Reporting Workflow Setup

This document describes the setup and usage of the GitHub CI/CD reporting
workflow for analyzing Linux Foundation projects hosted on Gerrit servers.

## Overview

The reporting workflow (`reporting.yaml`) provides:

1. **Run automatically** every Monday at 7:00 AM UTC
2. **Support manual execution** via GitHub's workflow dispatch
3. **Process projects** in parallel using matrix jobs
4. **Clone entire Gerrit servers** using the `gerrit-clone-action`
5. **Perform analytics** on the downloaded repositories
6. **Generate comprehensive reports** with results and summaries

## Configuration

### GitHub Secrets: Required Tokens

The workflow requires **TWO separate GitHub Personal Access Tokens** for
different purposes:

#### 1. CLASSIC_READ_ONLY_PAT_TOKEN (Classic PAT)

**Purpose**: Query workflow status and GitHub API data across all
organizations.

**⚠️ IMPORTANT**: You **MUST use a Classic Personal Access Token**, not a
fine-grained token, because fine-grained tokens work with a single
organization and cannot span the Linux Foundation organizations
needed for cross-org reporting.

**Required Scopes**:

- `repo:status` (access to repository commit statuses)
- `actions:read` (access to workflow runs)

**Quick Setup**:

1. Go to <https://github.com/settings/tokens>
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes: `repo:status` and `actions:read`
4. Generate and copy the token
5. Go to your repository's **Settings** → **Secrets and variables** → **Actions**
6. Click "New repository secret"
7. Name: `CLASSIC_READ_ONLY_PAT_TOKEN`
8. Value: Paste your token
9. Click "Add secret"

#### 2. GERRIT_REPORTS_PAT_TOKEN (Fine-grained PAT)

**Purpose**: Push generated reports to the `modeseven-lfit/gerrit-reports` repository.

**⚠️ IMPORTANT**: This should be a **Fine-grained Personal Access Token** with
write access specifically scoped to the gerrit-reports repository.

**Required Permissions**:

- **Repository access**: `modeseven-lfit/gerrit-reports`
- **Permissions**: Contents (Read and write)

**Quick Setup**:

1. Go to <https://github.com/settings/tokens?type=beta>
2. Click "Generate new token"
3. Token name: `Gerrit Reports Publishing`
4. Set token duration (recommend 90 days or 1 year)
5. Repository access: "Select repositories" → Choose
   `modeseven-lfit/gerrit-reports`
6. Permissions → Repository permissions → Contents: "Read and write"
7. Generate token and copy it
8. Go to your repository's **Settings** → **Secrets and variables** → **Actions**
9. Click "New repository secret"
10. Name: `GERRIT_REPORTS_PAT_TOKEN`
11. Value: Paste your token
12. Click "Add secret"

For detailed instructions on creating and configuring tokens, see:
**[GitHub Token Requirements Documentation](./GITHUB_TOKEN_REQUIREMENTS.md)**

### GitHub Variable: PROJECTS_JSON

The workflow requires a GitHub repository variable called `PROJECTS_JSON` that
contains an array of project configurations:

```json
[
  { "project": "O-RAN-SC", "server": "gerrit.o-ran-sc.org" },
  { "project": "ONAP", "server": "gerrit.onap.org" },
  { "project": "Opendaylight", "server": "git.opendaylight.org" }
]
```text
#### Setting up the Variable

1. Go to your repository's **Settings** → **Secrets and variables** →
   **Actions**
2. Click **Variables** tab
3. Click **New repository variable**
4. Name: `PROJECTS_JSON`
5. Value: The JSON array above (customize as needed)

## Workflow Structure

### Jobs

1. **verify**: Checks the `PROJECTS_JSON` configuration
2. **analyze**: Clones repositories and performs analysis
3. **summary**: Generates a final summary report/results

### Security Features

- **Hardened runners** using `step-security/harden-runner`
- **Minimal permissions** with explicit permission grants
- **Input validation** to prevent configuration errors

## Report Generation

The workflow uses the `reporting-tool` CLI to generate comprehensive repository analysis reports:

```bash
uv run reporting-tool generate \
  --project "$project" \
  --repos-path "./gerrit-server-clone" \
  --config-dir "./configuration" \
  --output-dir "./reports" \
  --verbose
```

### What Gets Analyzed

The reporting tool automatically analyzes:

- **Git Activity**: Commit history, lines of code, contributor metrics
- **CI/CD Status**: Jenkins builds, GitHub Actions workflows
- **Feature Detection**: Dependabot, pre-commit hooks, documentation
- **Contributors**: Author and organization analysis
- **Repository Health**: Activity status, aging, maintenance indicators

### Analysis Output

The tool generates multiple report formats:

- **JSON** (`report_raw.json`): Complete dataset for further processing
- **Markdown** (`report.md`): Human-readable text report
- **HTML** (`report.html`): Interactive report with sortable tables
- **ZIP Bundle**: Complete package with all formats

### Customization

To customize the analysis:

1. **Configuration**: Edit files in `configuration/` directory
   - `template.config`: Default settings for all projects
   - `<project>.config`: Project-specific overrides

2. **Time Windows**: Adjust analysis periods in project config:

   ```yaml
   time_windows:
     last_30_days: 30
     last_365_days: 365
   ```

3. **Features**: Enable/disable feature detection in config:

   ```yaml
   features:
     enabled:
       - dependabot
       - pre-commit
       - readthedocs
   ```

For detailed configuration options, see [Configuration Guide](docs/CONFIG_WIZARD_GUIDE.md).

## Artifacts

The workflow generates the following artifacts:

- **Clone manifests**: JSON files with repository clone results
- **Analysis outputs**: Per-project analysis results in JSON format
- **GitHub Step Summaries**: Rich markdown summaries including:
  - Repository structure analysis with disk usage
  - Clone statistics and largest repositories
  - Detailed analysis results from the Python script

Artifacts have a 30-day retention period and are available for download from
the workflow run page.

## Manual Execution

To run the workflow manually:

1. Go to **Actions** tab in your repository
2. Select **📊 Project Reports** workflow
3. Click **Run workflow**
4. Click **Run workflow** button (uses the current branch)

## Monitoring

The workflow includes comprehensive logging and error handling:

- **Input validation**: Ensures `PROJECTS_JSON` is properly formatted
- **Clone monitoring**: Tracks success/failure rates for repository cloning
- **Structure analysis**: Validates cloned data and provides disk usage metrics
- **Error reporting**: Clear error messages and status indicators
- **Timeout protection**: Jobs have reasonable timeout limits

## Customization

### Adding New Projects

1. Update the `PROJECTS_JSON` variable with the new project information
2. The workflow will automatically include the new project in the next run

### Modifying Clone Behavior

Edit the `gerrit-clone-action` parameters in the workflow:

- `threads`: Number of concurrent clone operations
- `clone-timeout`: Timeout per repository clone
- `skip-archived`: Whether to skip archived repositories
- `depth`: Create shallow clones with specified depth

### Changing the Schedule

Change the `cron` expression in the workflow file:

```yaml
schedule:
  # Run every Monday at 7:00 AM UTC
  - cron: '0 7 * * 1'
```text
## Troubleshooting

### Common Issues

1. **Missing PROJECTS_JSON**: Ensure the repository variable exists properly
2. **Invalid JSON**: Check JSON syntax using online tools
3. **Gerrit connectivity**: Check that Gerrit servers are accessible
4. **Permission errors**: Verify repository permissions and secrets
5. **Grey workflow status in reports**: Check `CLASSIC_READ_ONLY_PAT_TOKEN` exists
   and is a Classic PAT with required scopes (see [GitHub Token Requirements](./GITHUB_TOKEN_REQUIREMENTS.md))
6. **Report publishing failures**: Check `GERRIT_REPORTS_PAT_TOKEN` exists and has
   Contents: Read and write permissions for `modeseven-lfit/gerrit-reports`

### Debugging

1. Check the workflow logs in the Actions tab
2. Review the GitHub Step Summary for detailed information
3. Download and examine the generated artifacts
4. Test the reporting tool locally:
   ```bash
   # Install the tool
   pip install -e .

   # Run a test report
   reporting-tool generate \
     --project test-project \
     --repos-path ./test-repos \
     --dry-run
   ```

5. For GitHub API issues, see [GitHub Token Requirements](docs/GITHUB_TOKEN_REQUIREMENTS.md)
6. For configuration issues, see [Configuration Guide](docs/CONFIG_WIZARD_GUIDE.md)
7. For general troubleshooting, see [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## Further Documentation

For more detailed information:

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in 5 minutes
- **[CLI Guide](docs/CLI_GUIDE.md)** - Complete CLI reference
- **[Configuration Guide](docs/CONFIG_WIZARD_GUIDE.md)** - Configuration options
- **[CI/CD Integration](docs/CI_CD_INTEGRATION.md)** - GitHub Actions setup
- **[Performance Guide](docs/PERFORMANCE_GUIDE.md)** - Optimization tips
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Documentation Index](docs/INDEX.md)** - Complete documentation hub

## Future Enhancements

Planned improvements for the reporting workflow include:

- **Historical tracking** and trend analysis across report runs
- **Custom notification systems** for significant changes
- **Enhanced dashboard** with interactive visualizations
- **Integration with external tools** and databases
- **Automated remediation** suggestions for inactive repositories
