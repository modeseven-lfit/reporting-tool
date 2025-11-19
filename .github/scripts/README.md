<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# GitHub Actions Scripts

This directory contains utility scripts used by GitHub Actions workflows for the reporting system.

---

## 📁 Scripts

### `generate-index.sh`

Generates HTML index pages for GitHub Pages.

**Usage:**

```bash
./generate-index.sh <report_dir> [environment]
```text

**Arguments:**

- `report_dir`: Directory containing reports (e.g., `.` for root or `previews/123`)
- `environment`: `production` or `previews` (default: `production`)

**What it does:**

1. Scans the report directory for `report.html` files
2. Reads metadata from `metadata.json` files
3. Generates a styled HTML index page with:
   - List of all available reports
   - Project names and slugs
   - Generation timestamps
   - Links to HTML and JSON reports

**Example:**

```bash
# Generate production index at root
./generate-index.sh . production

# Generate Preview report index
./generate-index.sh previews/123 previews
```text

**Output:**

- `index.html` - Production reports listing at root level
- `previews/index.html` - Parent index listing all PR previews
- `previews/<pr_number>/index.html` - Individual PR preview listing

---

### `download-artifacts.sh`

Downloads workflow run artifacts for meta-reporting and historical analysis.

**Usage:**

```bash
export GITHUB_TOKEN=ghp_...
./download-artifacts.sh <workflow_name> <output_dir> [days_back]
```text

**Arguments:**

- `workflow_name`: Name of the workflow (e.g., `reporting-production.yaml`)
- `output_dir`: Directory to store downloaded artifacts
- `days_back`: Number of days to look back (default: 30)

**Environment Variables:**

- `GITHUB_TOKEN`: Required - GitHub token with repo access
- `GITHUB_REPOSITORY`: Optional - Auto-detected from git remote

**What it does:**

1. Queries GitHub API for completed workflow runs
2. Filters runs by date threshold
3. Downloads raw data artifacts (to conserve space)
4. Extracts artifacts to organized directory structure
5. Generates summary index JSON

**Example:**

```bash
# Download last 90 days of production artifacts
export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
./download-artifacts.sh reporting-production.yaml ./historical-data 90
```text

**Output Structure:**

```text
output_dir/
├── summary.json                    # Download summary
├── run-123456/
│   ├── run-metadata.json          # Workflow run info
│   ├── raw-data-project1/
│   │   ├── report_raw.json
│   │   ├── config_resolved.json
│   │   └── metadata.json
│   └── raw-data-project2/
│       └── ...
└── run-123457/
    └── ...
```text

**Use Cases:**

- Historical trend analysis
- Migration progress tracking
- Meta-report generation
- Long-term data archiving

---

## 🔧 Deprecated Scripts

### `publish-reports.sh.deprecated`

**Status:** ⚠️ Deprecated

This script handled report publishing in the legacy system, pushing reports to a separate `gerrit-reports` repository. The new GitHub Pages publishing logic in the workflows replaces this functionality.

**Migration:** See [MIGRATION_CHECKLIST.md](../../docs/MIGRATION_CHECKLIST.md)

---

## 🚀 Quick Start

### Prerequisites

All scripts require:

- Bash shell (tested on Linux and macOS)
- Standard Unix utilities: `jq`, `curl`, `git`, `find`, `date`
- GitHub CLI or token for API access (required for download-artifacts.sh)

### Installation

Scripts are ready to use - no installation needed. Make them executable:

```bash
chmod +x .github/scripts/*.sh
```text

### Testing Scripts Locally

**Test index generation:**

```bash
# Create test structure
mkdir -p test-reports/production/test-project
echo '{"project":"Test"}' > test-reports/production/test-project/metadata.json
echo "<h1>Test</h1>" > test-reports/production/test-project/report.html

# Generate index
.github/scripts/generate-index.sh test-reports/production

# View result
open test-reports/production/index.html
```text

**Test artifact download:**

```bash
# Set token
export GITHUB_TOKEN=ghp_...

# Download recent artifacts
.github/scripts/download-artifacts.sh \
  reporting-production.yaml \
  ./test-downloads \
  7

# Check results
ls -la ./test-downloads/
```text

---

## 📋 Script Requirements

### System Dependencies

| Tool | Purpose | Check Command |
|------|---------|---------------|
| `bash` | Shell interpreter | `bash --version` |
| `jq` | JSON processing | `jq --version` |
| `curl` | HTTP requests | `curl --version` |
| `git` | Repository operations | `git --version` |
| `find` | File searching | `find --version` |
| `date` | Date formatting | `date --version` |
| `unzip` | Archive extraction | `unzip -v` |

### Installing Dependencies

**Ubuntu/Debian:**

```bash
sudo apt-get update
sudo apt-get install -y jq curl git findutils coreutils unzip
```text

**macOS:**

```bash
brew install jq curl git coreutils
```text

**Alpine Linux (Docker):**

```bash
apk add --no-cache bash jq curl git findutils coreutils unzip
```text

---

## 🔒 Security Considerations

### Token Security

- **Never commit tokens to repository**
- Use environment variables or GitHub secrets
- Rotate tokens on a schedule
- Use fine-grained tokens when possible
- Limit token scope to required permissions

### Script Safety

All scripts:

- Use `set -euo pipefail` for error handling
- Check inputs before processing
- Handle API errors properly
- Avoid exposing sensitive data in logs
- Clean up temporary files

---

## 🐛 Troubleshooting

### Common Issues

**`jq: command not found`**

```bash
# Install jq
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS
```text

**`Permission denied` error**

```bash
# Make scripts executable
chmod +x .github/scripts/*.sh
```text

**`Invalid JSON` error in generate-index.sh**

- Check that metadata.json files are valid JSON
- Verify report directory structure is correct
- Review script output for specific file causing issues

**`API rate limit exceeded` in download-artifacts.sh**

- Use authenticated requests (GITHUB_TOKEN)
- Reduce `days_back` parameter
- Wait for rate limit to reset (typically 1 hour)

**`No artifacts found` error**

- Verify workflow name is correct
- Check that workflow has completed without errors
- Ensure artifacts haven't expired (retention period)
- Verify GITHUB_TOKEN has correct permissions

---

## 🧪 Testing

### Running Script Tests

```bash
# Test generate-index.sh with sample data
bash tests/test-generate-index.sh

# Test download-artifacts.sh (requires token)
export GITHUB_TOKEN=ghp_...
bash tests/test-download-artifacts.sh
```text

### Manual Validation

**Check index generation output:**

```bash
# Generate index
./generate-index.sh production

# Check HTML
xmllint --html --noout production/index.html

# Check for required elements
grep -q "Available Reports" production/index.html && echo "✓ Title present"
grep -q "report.html" production/index.html && echo "✓ Links present"
```

**Check artifact downloads:**

```bash
# Download artifacts
export GITHUB_TOKEN=ghp_...
./download-artifacts.sh reporting-production.yaml ./test-output 7

# Check structure
[ -f ./test-output/summary.json ] && echo "✓ Summary exists"
[ -d ./test-output/run-* ] && echo "✓ Run directories created"
find ./test-output -name "report_raw.json" -type f | wc -l
```text

---

## 📚 More Resources

- [GitHub Pages Setup Guide](../../docs/GITHUB_PAGES_SETUP.md)
- [Migration Checklist](../../docs/MIGRATION_CHECKLIST.md)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub REST API Documentation](https://docs.github.com/en/rest)

---

## 🤝 Contributing

When modifying scripts:

1. **Test thoroughly** - Test on both Linux and macOS
2. **Handle errors** - Use proper error handling and validation
3. **Document changes** - Update this README
4. **Follow conventions** - Use consistent style and formatting
5. **Add comments** - Explain complex logic
6. **Update workflows** - If script interface changes

### Code Style

- Use `set -euo pipefail` at the start
- Quote variables: `"$VARIABLE"`
- Use meaningful variable names in UPPERCASE
- Add comments for non-obvious logic
- Check inputs before processing
- Provide helpful error messages

---

## 📝 Changelog

### Version 2.0 (2025-01)

- ✨ Added `generate-index.sh` for GitHub Pages
- ✨ Added `download-artifacts.sh` for meta-reporting
- ⚠️ Deprecated `publish-reports.sh` (legacy system)
- 📝 Created comprehensive documentation

### Version 1.0 (Legacy)

- Initial `publish-reports.sh` for gerrit-reports repository

---

**Last Updated:** 2025-01-XX
**Maintained By:** Linux Foundation Release Engineering
