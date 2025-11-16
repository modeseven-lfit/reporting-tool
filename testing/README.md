<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Local Testing Guide

This directory contains scripts for local testing of the reporting tool with real Gerrit server data.

## Overview

The `local-testing.sh` script automates the following workflow:

1. **Check for existing repositories** - Reuses already cloned repositories if present
2. **Clone repositories** (if needed) from Gerrit servers using `gerrit-clone` CLI tool
3. **Generate reports** using the `reporting-tool` on the cloned repositories
4. **Output results** to `/tmp/reports` for manual review

## Prerequisites

### Required Software

- **uv** - Package manager and tool runner
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- **git** - Git version control system
  ```bash
  # Usually pre-installed on most systems
  git --version
  ```

- **jq** - JSON parser for project metadata
  ```bash
  brew install jq  # macOS
  sudo apt-get install jq  # Debian/Ubuntu
  ```

### SSH Key Configuration

The script requires SSH access to clone the info-master repository from `gerrit.linuxfoundation.org`.

**Option 1: Use existing SSH key (recommended)**
```bash
# Copy your Gerrit SSH key to the expected location
cp ~/.ssh/id_rsa ~/.ssh/gerrit.linuxfoundation.org
# Or create a symlink
ln -s ~/.ssh/id_rsa ~/.ssh/gerrit.linuxfoundation.org
```

**Option 2: Set environment variable (CI/CD mode)**
```bash
export LF_GERRIT_INFO_MASTER_SSH_KEY="$(cat ~/.ssh/id_rsa)"
```

The script will automatically:
- Check for `LF_GERRIT_INFO_MASTER_SSH_KEY` environment variable first
- Fall back to `~/.ssh/gerrit.linuxfoundation.org` if not set
- Exit with error if neither is found

### Disk Space

Ensure you have sufficient disk space in `/tmp`:

- **ONAP**: ~50-100 GB (varies based on number of active repositories)
- **OpenDaylight**: ~10-20 GB (varies based on number of active repositories)

Check available space:
```bash
df -h /tmp
```

### API Access (Optional but Recommended)

By default, reports only use **local git data**. To include GitHub workflow status, Gerrit metadata, and Jenkins CI/CD information, you need to configure API access.

**Quick setup:**
```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

**📖 See [API_ACCESS.md](API_ACCESS.md) for complete API configuration guide**

Without API tokens, reports will be very fast (~10-20 seconds) but will **NOT** include:
- ✗ GitHub workflow status
- ✗ Gerrit repository metadata  
- ✗ Jenkins CI/CD information

With API tokens, reports take longer (~5-10 minutes) but include complete data.

## Quick Start

Run the testing script:

```bash
cd reporting-tool/testing
./local-testing.sh
```

The script will:

1. ✅ Load project metadata from `projects.json`
2. ✅ Check prerequisites (uv, git, jq)
3. 🔑 Verify SSH key for info-master access
4. 🔍 Check API configuration (GitHub/Gerrit/Jenkins)
5. 📁 Create output directories
6. 📥 Clone ONAP repositories to `/tmp/gerrit.onap.org` (if not already present)
7. 📥 Clone OpenDaylight repositories to `/tmp/git.opendaylight.org` (if not already present)
8. 📊 Generate ONAP report to `/tmp/reports/ONAP`
9. 📊 Generate OpenDaylight report to `/tmp/reports/Opendaylight`
10. 📋 Display summary of results

**Notes:** 
- The script uses project metadata from `projects.json` to configure Gerrit/Jenkins hosts automatically
- SSH key is required for info-master access (see SSH Key Configuration above)
- The script preserves existing cloned repositories to save time on subsequent runs
- Report directories are always cleaned and regenerated
- The script will warn you if API integrations are not configured
- See [API_ACCESS.md](API_ACCESS.md) to enable GitHub/Gerrit/Jenkins API access

## Output Structure

After successful execution, you'll have:

```
/tmp/
├── gerrit.onap.org/              # Cloned ONAP repositories
│   ├── aai/
│   ├── ccsdk/
│   ├── dcaegen2/
│   └── ...
│
├── git.opendaylight.org/         # Cloned OpenDaylight repositories
│   ├── aaa/
│   ├── controller/
│   ├── netconf/
│   └── ...
│
└── reports/
    ├── ONAP/                     # ONAP reports
    │   ├── report_raw.json       # Complete dataset (canonical)
    │   ├── report.md             # Markdown report (readable)
    │   ├── report.html           # Interactive HTML (sortable tables)
    │   ├── config_resolved.json  # Applied configuration
    │   └── ONAP_report_bundle.zip # Complete bundle
    │
    └── OpenDaylight/             # OpenDaylight reports
        ├── report_raw.json
        ├── report.md
        ├── report.html
        ├── config_resolved.json
        └── OpenDaylight_report_bundle.zip
```

## Configuration

### Project Metadata

The script uses `projects.json` to configure project-specific settings:

```json
[
  {
    "project": "ONAP",
    "gerrit": "gerrit.onap.org",
    "jenkins": "jenkins.onap.org"
  },
  {
    "project": "Opendaylight",
    "gerrit": "git.opendaylight.org",
    "jenkins": "jenkins.opendaylight.org"
  }
]
```

To add more projects, edit `testing/projects.json` with:
- `project` - Project name
- `gerrit` - Gerrit server hostname
- `jenkins` - Jenkins server hostname (optional)
- `github` - GitHub organization name (optional)

### Customizing Base Directories

Edit the script variables at the top of `local-testing.sh`:

```bash
# Base directories
CLONE_BASE_DIR="/tmp"
REPORT_BASE_DIR="/tmp/reports"

# SSH key location
SSH_KEY_PATH="${HOME}/.ssh/gerrit.linuxfoundation.org"
```

### gerrit-clone Options

The script uses these `gerrit-clone` options:

- `--https` - Clone via HTTPS (no SSH keys required)
- `--skip-archived` - Skip archived/inactive repositories
- `--threads 4` - Use 4 concurrent threads
- `--clone-timeout 600` - 10-minute timeout per repository
- `--retry-attempts 3` - Retry failed clones up to 3 times
- `--move-conflicting` - Move conflicting files to allow nested repos
- `--verbose` - Show detailed progress

To modify these, edit the `clone_onap()` and `clone_opendaylight()` functions in the script.

### reporting-tool Options

The script uses these `reporting-tool` options:

- `--cache` - Enable caching for better performance
- `--workers 4` - Use 4 concurrent workers

To modify these, edit the `generate_onap_report()` and `generate_opendaylight_report()` functions.

## Reviewing Reports

### Markdown Reports

Quick, human-readable overview:

```bash
# ONAP report
less /tmp/reports/ONAP/report.md

# OpenDaylight report
less /tmp/reports/OpenDaylight/report.md
```

### HTML Reports

Interactive reports with sortable tables:

```bash
# ONAP report (macOS)
open /tmp/reports/ONAP/report.html

# OpenDaylight report (macOS)
open /tmp/reports/OpenDaylight/report.html

# Linux
xdg-open /tmp/reports/ONAP/report.html
xdg-open /tmp/reports/OpenDaylight/report.html
```

### JSON Data

Complete structured data for programmatic analysis:

```bash
# ONAP data
jq '.' /tmp/reports/ONAP/report_raw.json | less

# OpenDaylight data
jq '.' /tmp/reports/OpenDaylight/report_raw.json | less
```

## Troubleshooting

### SSH Key Issues

If you see "❌ SSH key not found":

1. **Copy your SSH key to the expected location**:
   ```bash
   cp ~/.ssh/id_rsa ~/.ssh/gerrit.linuxfoundation.org
   ```

2. **Or set environment variable**:
   ```bash
   export LF_GERRIT_INFO_MASTER_SSH_KEY="$(cat ~/.ssh/id_rsa)"
   ```

3. **Test SSH access**:
   ```bash
   ssh -p 29418 gerrit.linuxfoundation.org gerrit version
   ```

### Clone Failures

If cloning fails:

1. **Check network connectivity**:
   ```bash
   ping gerrit.onap.org
   ping git.opendaylight.org
   ```

2. **Verify server accessibility**:
   ```bash
   curl -I https://gerrit.onap.org
   curl -I https://git.opendaylight.org
   ```

3. **Check disk space**:
   ```bash
   df -h /tmp
   ```

4. **Review clone logs** - The script outputs detailed progress

### Report Generation Failures

If report generation fails:

1. **Verify repositories were cloned**:
   ```bash
   ls -la /tmp/gerrit.onap.org/
   ls -la /tmp/git.opendaylight.org/
   ```

2. **Check for valid git repositories**:
   ```bash
   find /tmp/gerrit.onap.org -name ".git" -type d | head -5
   ```

3. **Run with verbose output** - Already enabled in the script

4. **Check the reporting-tool dependencies**:
   ```bash
   cd reporting-tool
   uv sync
   ```

### Out of Disk Space

If you run out of disk space:

1. **Clean up previous test runs**:
   ```bash
   rm -rf /tmp/gerrit.onap.org
   rm -rf /tmp/git.opendaylight.org
   rm -rf /tmp/reports
   ```

2. **Use a different directory** with more space:
   ```bash
   # Edit local-testing.sh
   CLONE_BASE_DIR="/path/to/larger/disk"
   REPORT_BASE_DIR="/path/to/larger/disk/reports"
   ```

3. **Clone with shallow depth** (edit the script):
   ```bash
   uvx gerrit-clone \
       --depth 1 \
       # ... other options
   ```

## Manual Testing

### Test Individual Steps

You can run individual steps manually:

#### 1. Clone ONAP only

```bash
uvx gerrit-clone clone \
    --host gerrit.onap.org \
    --path-prefix /tmp \
    --https \
    --skip-archived \
    --threads 4 \
    --verbose
```

#### 2. Clone OpenDaylight only

```bash
uvx gerrit-clone clone \
    --host git.opendaylight.org \
    --path-prefix /tmp \
    --https \
    --skip-archived \
    --threads 4 \
    --verbose
```

#### 3. Generate ONAP report only

```bash
cd reporting-tool
uv run reporting-tool generate \
    --project "ONAP" \
    --repos-path /tmp/gerrit.onap.org \
    --output-dir /tmp/reports \
    --cache \
    --workers 4
```

#### 4. Generate OpenDaylight report only

```bash
cd reporting-tool
uv run reporting-tool generate \
    --project "OpenDaylight" \
    --repos-path /tmp/git.opendaylight.org \
    --output-dir /tmp/reports \
    --cache \
    --workers 4
```

## Cleanup

### Remove Test Data

To clean up all test data:

```bash
rm -rf /tmp/gerrit.onap.org
rm -rf /tmp/git.opendaylight.org
rm -rf /tmp/reports
```

Or use the cleanup script:

```bash
cd reporting-tool/testing
./cleanup.sh
```

### Automatic Cleanup

The script automatically cleans up **report directories only** at the start of each run. Cloned repositories are preserved and reused to save time. To force a fresh clone, manually delete the repository directories first:

```bash
rm -rf /tmp/gerrit.onap.org
rm -rf /tmp/git.opendaylight.org
```

## Advanced Usage

### Test with Additional Projects

The script currently processes ONAP and Opendaylight by default. To test other projects:

1. **Edit `local-testing.sh`** and modify the projects array:
   ```bash
   # Change this line in the main() function:
   local projects=("ONAP" "Opendaylight" "O-RAN-SC" "AGL")
   ```

2. **Or test specific projects manually**:
   ```bash
   # Clone O-RAN-SC
   uvx gerrit-clone clone \
       --host gerrit.o-ran-sc.org \
       --path-prefix /tmp/gerrit.o-ran-sc.org
   
   # Generate report
   cd reporting-tool
   uv run reporting-tool generate \
       --project "O-RAN-SC" \
       --repos-path /tmp/gerrit.o-ran-sc.org \
       --output-dir /tmp/reports
   ```

### Use SSH Instead of HTTPS

If you have SSH keys configured:

```bash
# Remove --https and add SSH options
uvx gerrit-clone clone \
    --host gerrit.onap.org \
    --path-prefix /tmp \
    --ssh-user your-username \
    --ssh-private-key ~/.ssh/id_rsa \
    --threads 4 \
    --verbose
```

### Different Report Formats

Generate only specific report formats:

```bash
uv run reporting-tool generate \
    --project "ONAP" \
    --repos-path /tmp/gerrit.onap.org \
    --output-dir /tmp/reports/onap \
    --formats json markdown  # Only JSON and Markdown
```

## Performance Tips

1. **Increase threads** for faster cloning (if network allows):
   ```bash
   --threads 8
   ```

2. **Use shallow clones** for faster initial clone:
   ```bash
   --depth 1
   ```

3. **Enable caching** for repeated report generation:
   ```bash
   --cache
   ```

4. **Increase workers** for faster report generation:
   ```bash
   --workers 8
   ```

5. **Reuse cloned repositories** - The script automatically preserves cloned repos between runs, saving significant time on subsequent executions.

6. **Enable API access** - Set `GITHUB_TOKEN` and other API credentials for complete data. See [API_ACCESS.md](API_ACCESS.md).

## Project Metadata Reference

The `projects.json` file contains metadata for all supported Linux Foundation projects:

- **O-RAN-SC** - gerrit.o-ran-sc.org, jenkins.o-ran-sc.org
- **ONAP** - gerrit.onap.org, jenkins.onap.org
- **Opendaylight** - git.opendaylight.org, jenkins.opendaylight.org
- **AGL** - gerrit.automotivelinux.org, build.automotivelinux.org
- **OPNFV** - gerrit.opnfv.org
- **FDio** - gerrit.fd.io, jenkins.fd.io
- **LF Broadband** - gerrit.lfbroadband.org, jenkins.lfbroadband.org
- **Linux Foundation** - gerrit.linuxfoundation.org

This metadata is used to automatically configure API endpoints for each project.

## See Also

- [API Access Configuration](API_ACCESS.md) - **Enable GitHub/Gerrit/Jenkins APIs**
- [gerrit-clone documentation](https://github.com/lfreleng-actions/gerrit-clone-action)
- [reporting-tool documentation](../README.md)
- [Configuration guide](../docs/CONFIGURATION.md)
- [Performance guide](../docs/PERFORMANCE.md)