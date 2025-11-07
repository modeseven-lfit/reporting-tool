<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Troubleshooting Guide

Repository Analysis Report Generator

Comprehensive guide to diagnosing and resolving common issues.

Last Updated: 2025-01-26
Version: 2.0 (Phase 14)

---

## Table of Contents

- [🔥 Most Common Issues](#-most-common-issues-start-here)
- [📊 Diagnostic Flowchart](#-diagnostic-flowchart)
- [Quick Diagnostics](#quick-diagnostics)
- [Configuration Errors](#configuration-errors)
- [Path and File Errors](#path-and-file-errors)
- [API and Network Errors](#api-and-network-errors)
- [Permission Errors](#permission-errors)
- [Validation Errors](#validation-errors)
- [Performance Issues](#performance-issues)
- [Parallel Execution Issues](#parallel-execution-issues)
- [Caching Issues](#caching-issues)
- [Output Issues](#output-issues)
- [Exit Codes Reference](#exit-codes-reference)
- [Advanced Debugging](#advanced-debugging)
- [🔗 Related Documentation](#-related-documentation)

---

## 🔥 Most Common Issues (Start Here!)

Before diving into detailed troubleshooting, check these common issues:

### 1. Configuration File Not Found

```bash
# Quick fix:
reporting-tool init --project my-project
```text

[Full details →](#error-configuration-file-not-found)

### 2. GitHub API 401 Unauthorized

```bash
# Quick fix:
export GITHUB_TOKEN="ghp_your_token_here"
```text

[Full details →](#error-github-api---401-unauthorized)

### 3. Slow Performance

```bash
# Quick fix:
--cache --workers auto
```text

[Full details →](#issue-reports-take-too-long-to-generate)

### 4. Permission Denied

```bash
# Quick fix:
chmod u+w output/
```

[Full details →](#error-permission-denied-file)

### 5. Exit Code 1 (Generic Error)

```bash
# Diagnose:
reporting-tool generate ... -vv 2>&1 | tee debug.log
```text

[Full details →](#exit-codes-reference)

**Still stuck?** Try the [Diagnostic Flowchart](#-diagnostic-flowchart) below.

---

## 📊 Diagnostic Flowchart

```text

┌─────────────────────────────────────────────────┐
│ Report Generation Failed?                       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│ Step 1: Check Exit Code                        │
│ $ echo $?                                       │
└────────────────┬────────────────────────────────┘
                 │
                 ├─ 0: Success ✓ (no issue)
                 │
                 ├─ 1: Error
                 │  └─▶ Check logs with -vv
                 │      └─▶ Common: config, API, processing
                 │
                 ├─ 2: Partial Success
                 │  └─▶ Review warnings
                 │      └─▶ Some repos may have failed
                 │
                 ├─ 3: Usage Error
                 │  └─▶ Fix command syntax
                 │      └─▶ Check --help
                 │
                 └─ 4: System Error
                    └─▶ Check permissions, disk space
                        └─▶ Verify dependencies

```text

Interactive Decision Tree:

1. **Exit code 1?** → [Configuration Errors](#configuration-errors) OR [API Errors](#api-and-network-errors)
2. **Exit code 2?** → Check warnings and review partial data
3. **Exit code 3?** → Fix command syntax, check required arguments
4. **Exit code 4?** → [Permission Errors](#permission-errors) OR Check disk space

**Still unsure?** Run diagnostics:

```bash
reporting-tool generate --project test --repos-path ./repos --dry-run
```

---

## Quick Diagnostics

Before diving into specific errors, try these quick diagnostic steps:

### 1. Run Validation

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --dry-run
```text

This performs comprehensive pre-flight checks and reports any issues.

### 2. Check Configuration

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --show-config
```text

Verify your configuration is being loaded correctly.

### 3. Enable Verbose Logging

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  -vv
```text

See detailed logs to understand what's happening.

---

## Configuration Errors

### Error: Configuration file not found

Error Message:

```

❌ Error: Configuration file not found: config/my-project.yaml

💡 Suggestion: Create config file using --init wizard

🔧 Quick Fix: reporting-tool init --project my-project

📚 Documentation: docs/CLI_QUICK_START.md

```text

Common Causes:

- Configuration file doesn't exist in expected location
- Project name doesn't match config filename
- Using wrong config directory
- File has wrong extension (.config vs .yaml)

Solutions:

1. **Run configuration wizard (recommended):**

   ```bash
   reporting-tool init --project my-project
   ```

2. **Use template:**

   ```bash
   reporting-tool init --template standard --project my-project
   ```

3. **Specify custom config directory:**

   ```bash
   reporting-tool generate --project my-project --repos-path ./repos --config-dir /path/to/custom/config
   ```

4. **Check project name matches filename:**

   ```bash
   # Config file should be: config/{project-name}.config
   ls -la config/*.config
   ```

---

### Error: Invalid YAML syntax

```text
❌ Error: Invalid YAML syntax: mapping values are not allowed here
  in "config/template.config", line 15, column 12

💡 Suggestion: Check YAML syntax - ensure proper indentation, no tabs, and valid structure

📚 Documentation: docs/configuration.md
```text

Common YAML Mistakes:

1. **Tabs instead of spaces:**

   ```yaml
   # BAD (contains tabs)
   project: my-project

   # GOOD (spaces only)
   project: my-project
   ```

2. **Inconsistent indentation:**

   ```yaml
   # BAD
   time_windows:
     90d:
       days: 90
      30d:  # Wrong indentation
       days: 30

   # GOOD
   time_windows:
     90d:
       days: 90
     30d:
       days: 30
   ```

3. **Missing colons:**

   ```yaml
   # BAD
   project my-project

   # GOOD
   project: my-project
   ```

4. **Incorrect list syntax:**

   ```yaml
   # BAD
   features:
     - feature1
     feature2  # Missing dash

   # GOOD
   features:
     - feature1
     - feature2
   ```

Validation Tools:

```bash
# Use yamllint if available
yamllint config/template.config

# Or validate with Python
python -c "import yaml; yaml.safe_load(open('config/template.config'))"
```

---

### Error: Missing required field

```text
❌ Error: Configuration validation failed with 1 error(s):
  - project: Required field missing

💡 Suggestion: Add the required field to your configuration file

📚 Documentation: docs/configuration.md
```text

Required fields:

- `project` - Project name
- `time_windows` - At least one time window
- `activity_thresholds` - Activity threshold configuration

Minimal valid config:

```yaml
project: my-project
repositories_path: /workspace/repos

time_windows:
  90d:
    days: 90

activity_thresholds:
  active_days: 365
  current_days: 90
```text

---

### Error: Template configuration not found

```

❌ Error: Template configuration not found: config/template.config

💡 Suggestion: Ensure template.config exists in the config directory or create it from template.config.example

📚 Documentation: docs/configuration.md

```text

Solution:

```bash
# Create from example
cp config/template.config.example config/template.config

# Or specify different config directory
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --config-dir /custom/path
```text

---

## Path and File Errors

### Error: Repository path does not exist

```text
❌ Error: File not found: /workspace/repos

💡 Suggestion: Verify the path exists and is accessible
```

Diagnostic steps:

1. **Check if path exists:**

   ```bash
   ls -la /workspace/repos
   ```

2. **Check permissions:**

   ```bash
   ls -ld /workspace/repos
   # Should show: drwxr-xr-x or similar (readable)
   ```

3. **Use absolute path:**

   ```bash
   # Instead of: --repos-path ./repos
   # Use: --repos-path $(pwd)/repos
   ```

4. **Check for typos:**

   ```bash
   # Common mistakes:
   # /worksapce/repos (typo)
   # /workspace/repo (missing 's')
   # /workspace/repos/ (trailing slash shouldn't matter but try without)
   ```

---

### Error: Output directory not writable

```text
❌ Error: Cannot write file: output/report.html

💡 Suggestion: Check file/directory permissions. You may need to run with
   appropriate privileges or choose a different output directory.
```text

Solutions:

1. **Check directory permissions:**

   ```bash
   ls -ld output/
   ```

2. **Create directory with correct permissions:**

   ```bash
   mkdir -p output
   chmod 755 output
   ```

3. **Use different output directory:**

   ```bash
   --output-dir /tmp/reports
   ```

4. **Check disk space:**

   ```bash
   df -h .
   ```

---

### Error: Template files not found

```text
❌ Error: Configuration error: Template file not found: templates/report.html.j2

💡 Suggestion: Ensure template files are present in the templates directory
```

Solution:

```bash
# Verify templates directory exists
ls -la templates/

# Should contain:
# - report.html.j2
# - report.md.j2
# - base.html.j2
# etc.

# If missing, re-clone repository or restore templates
```text

---

## API and Network Errors

### Error: GitHub API - 401 Unauthorized

```text

❌ Error: GitHub API error: 401 Unauthorized

💡 Suggestion: Check GitHub API token - it may be expired or invalid

📚 Documentation: docs/troubleshooting.md#api-errors

```text

Diagnostic steps:

1. **Check token is set:**

   ```bash
   echo $GITHUB_TOKEN
   # Should output: ghp_...
   ```

2. **Verify token format:**

   ```bash
   # Token should start with 'ghp_' (personal access token)
   # Or 'github_pat_' (fine-grained token)
   ```

3. **Test token manually:**

   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   ```

4. **Check token permissions:**
   - Go to <https://github.com/settings/tokens>
   - Ensure token has `repo:read` scope
   - For workflow status, needs `workflow:read` scope

5. **Generate new token:**
   - Visit: <https://github.com/settings/tokens/new>
   - Select scopes: `repo`, `workflow`
   - Copy token immediately (shown only once)
   - Set in environment: `export GITHUB_TOKEN="ghp_..."`

---

### Error: GitHub API - 403 Forbidden

```text
❌ Error: GitHub API error: 403 Forbidden

💡 Suggestion: Verify GitHub API token has required permissions

📚 Documentation: docs/troubleshooting.md#api-errors
```text

Causes:

- Insufficient token permissions
- Token doesn't have access to repository
- Organization requires SSO authentication

Solutions:

1. **Check token scopes:**

   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
   # Look for 'X-OAuth-Scopes' header
   ```

2. **Regenerate with correct scopes:**
   - Needs: `repo:read`, `workflow:read`

3. **For organization repos:**
   - Enable SSO for token
   - Go to token settings
   - Click "Configure SSO"
   - Authorize for organization

---

### Error: GitHub API - Rate Limit Exceeded

```text
❌ Error: GitHub API error: Rate limit exceeded

💡 Suggestion: Wait before retrying or use a different GitHub API token

📚 Documentation: docs/troubleshooting.md#api-errors
```text

Rate Limits:

- Unauthenticated: 60 requests/hour
- Authenticated: 5,000 requests/hour

Solutions:

1. **Use authenticated requests:**

   ```bash
   export GITHUB_TOKEN="ghp_..."
   ```

2. **Check rate limit status:**

   ```bash
   curl -H "Authorization: token $GITHUB_TOKEN" \
        https://api.github.com/rate_limit
   ```

3. **Wait for reset:**

   ```bash
   # Rate limit resets hourly
   # Check 'X-RateLimit-Reset' header
   ```

4. **Use multiple tokens (advanced):**
   - Rotate between tokens
   - Each token has independent rate limit

---

### Error: Network Connection Failed

```text
❌ Error: Failed to connect to https://api.github.com: Connection timeout

💡 Suggestion: Check your network connection. Verify that you can reach the
   required endpoints. You may need to configure proxy settings.

📚 Documentation: docs/troubleshooting.md#network-issues
```text

Diagnostic steps:

1. **Test connectivity:**

   ```bash
   curl https://api.github.com
   ping api.github.com
   ```

2. **Check DNS resolution:**

   ```bash
   nslookup api.github.com
   dig api.github.com
   ```

3. **Test with proxy:**

   ```bash
   export HTTP_PROXY="http://proxy:8080"
   export HTTPS_PROXY="http://proxy:8080"
   ```

4. **Check firewall:**

   ```bash
   # Ensure port 443 (HTTPS) is open
   telnet api.github.com 443
   ```

---

## Permission Errors

### Error: Permission denied (file)

```text
❌ Error: Cannot read file: /workspace/repos/repo1/.git/config

💡 Suggestion: Check file/directory permissions. You may need to run with
   appropriate privileges or choose a different output directory.
```text

Solutions:

1. **Check file permissions:**

   ```bash
   ls -la /workspace/repos/repo1/.git/config
   ```

2. **Fix repository permissions:**

   ```bash
   chmod -R u+r /workspace/repos/
   ```

3. **Check ownership:**

   ```bash
   ls -l /workspace/repos/
   # If owned by different user, change:
   sudo chown -R $USER:$USER /workspace/repos/
   ```

---

### Error: Permission denied (directory)

```text
❌ Error: Permission denied: output/

💡 Suggestion: Check file/directory permissions
```

Solutions:

1. **Create with correct permissions:**

   ```bash
   mkdir -p output
   chmod 755 output
   ```

2. **Use temporary directory:**

   ```bash
   --output-dir /tmp/reports
   ```

3. **Run with sudo (not recommended):**

   ```bash
   # Only if absolutely necessary
   sudo reporting-tool generate ...
   ```

---

## Validation Errors

### Error: TimeWindow validation failed

```text
❌ Error: Validation failed for 'TimeWindow.days': Field 'TimeWindow.days'
   must be positive (got: 0) Expected: integer > 0
```text

**Cause:** Invalid time window configuration

Solution:

```yaml
# BAD
time_windows:
  90d:
    days: 0  # Must be > 0

# GOOD
time_windows:
  90d:
    days: 90
```

---

### Error: Activity threshold ordering

```text
❌ Error: Configuration validation failed with 1 error(s):
  - activity_thresholds: current_days must be less than active_days
```text

**Cause:** Thresholds in wrong order

Solution:

```yaml
# BAD
activity_thresholds:
  active_days: 90
  current_days: 365  # Wrong: larger than active

# GOOD
activity_thresholds:
  active_days: 365
  current_days: 90
  inactive_days: 730
```text

**Rule:** `current_days < active_days < inactive_days`

---

## Performance Issues

### Issue: Reports take too long to generate

Symptoms:

- Analysis takes hours
- High CPU usage
- Progress seems stuck

Solutions:

1. **Enable caching:**

   ```bash
   --cache
   ```

   First run slow, subsequent runs 10-100x faster

2. **Increase parallelism:**

   ```bash
   --workers 16  # Or higher
   ```

3. **Reduce time windows:**

   ```yaml
   # Instead of analyzing multiple years
   time_windows:
     90d:
       days: 90  # Just last 90 days
   ```

4. **Limit repository count:**

   ```bash
   # Analyze subset for testing
   mkdir test-repos
   cp -r repos/important-repo test-repos/
   --repos-path test-repos
   ```

5. **Skip slow features:**

   ```yaml
   api:
     github:
       enabled: false  # Skip GitHub API calls
     jenkins:
       enabled: false  # Skip Jenkins checks
   ```

---

### Issue: High memory usage

Symptoms:

- System slows down
- Out of memory errors
- Swapping

Solutions:

1. **Reduce worker count:**

   ```bash
   --workers 4  # Or lower
   ```

2. **Process fewer repositories:**

   ```bash
   # Split into batches
   --repos-path batch1/
   --repos-path batch2/
   ```

3. **Disable caching:**

   ```bash
   # Don't use --cache
   ```

4. **Generate one format:**

   ```bash
   --output-format json  # Smallest memory footprint
   ```

---

## Parallel Execution Issues

### Issue: Tests/Processing hanging in parallel mode

Symptoms:

- Process appears stuck
- No output for extended period
- High CPU but no progress

Error Message:

```text
Process appears hung...
```

Solutions:

1. **Disable parallel execution temporarily:**

   ```bash
   reporting-tool generate --project test --repos-path ./repos --workers 1
   ```

2. **Check for resource contention:**

   ```bash
   # Monitor CPU and memory
   htop
   # or
   top
   ```

3. **Enable debug logging:**

   ```bash
   reporting-tool generate --project test --repos-path ./repos --workers 1 -vvv 2>&1 | tee debug.log
   ```

See Also:

- [Parallel Execution Guide](testing/PARALLEL_EXECUTION.md)
- [CLI FAQ: Performance](CLI_FAQ.md#performance)

---

### Issue: Flaky test failures in parallel mode

Symptoms:

- Tests pass sequentially but fail in parallel
- Intermittent failures
- State contamination errors

Solutions:

1. **Run tests sequentially to verify:**

   ```bash
   pytest --workers 1 -v
   ```

2. **Check test isolation:**
   - Tests should not share state
   - Use fixtures for setup/teardown
   - Avoid global variables
   - Use unique temporary directories

3. **Mark flaky tests (for test suites):**

   ```python
   @pytest.mark.flaky(reruns=3)
   def test_sometimes_fails():
       pass
   ```

See Also:

- [Test Writing Guide](testing/TEST_WRITING_GUIDE.md)
- [Test Prerequisites](testing/TEST_PREREQUISITES.md)

---

## Caching Issues

### Issue: Stale data in reports

Symptoms:

- Old commit data shown
- Repository updates not reflected
- Inconsistent metrics

Error Message:

```text
⚠ Warning: Cache data may be stale
```text

Solutions:

1. **Clear cache:**

   ```bash
   rm -rf .cache/repo-metrics
   ```

2. **Use custom cache directory:**

   ```bash
   reporting-tool generate --project test --repos-path ./repos --cache-dir /tmp/fresh-cache
   ```

3. **Disable caching temporarily:**

   ```bash
   # Don't use --cache flag
   reporting-tool generate --project test --repos-path ./repos
   ```

See Also:

- [CLI FAQ: When to use caching](CLI_FAQ.md#when-should-i-use-caching)

---

### Issue: Cache permission errors

Symptoms:

```text
❌ Error: Permission denied: .cache/repo-metrics/abc123.json
```

Common Causes:

- Cache directory created by different user
- Insufficient permissions
- Read-only filesystem

Solutions:

1. **Fix cache directory permissions:**

   ```bash
   chmod -R u+rw .cache/repo-metrics
   ```

2. **Use different cache location:**

   ```bash
   reporting-tool generate --project test --repos-path ./repos --cache-dir ~/cache/reports
   ```

3. **Clear and recreate:**

   ```bash
   rm -rf .cache
   mkdir -p .cache/repo-metrics
   chmod u+rw .cache/repo-metrics
   ```

---

## Output Issues

### Issue: HTML report doesn't display correctly

Symptoms:

- Broken formatting
- Missing styles
- JavaScript errors

Diagnostic steps:

1. **Check browser console:**
   - Open DevTools (F12)
   - Look for errors in Console tab

2. **Verify complete file:**

   ```bash
   ls -lh output/*.html
   # Should be several hundred KB
   ```

3. **Check for corruption:**

   ```bash
   file output/report.html
   # Should say: HTML document
   ```

Solutions:

1. **Regenerate report:**

   ```bash
   rm -rf output/
   reporting-tool generate ...
   ```

2. **Try different browser:**
   - Chrome, Firefox, Safari, Edge

3. **Check file permissions:**

   ```bash
   chmod 644 output/*.html
   ```

---

### Issue: JSON output is invalid

Symptoms:

- JSON parsing errors
- Truncated file
- Invalid syntax

Validation:

```bash
# Validate JSON
python -m json.tool output/report.json > /dev/null

# Or with jq
jq . output/report.json > /dev/null
```text

Solution:

```bash
# Regenerate with verbose logging
reporting-tool generate ... -vv
```text

---

## Exit Codes Reference

The tool uses standardized exit codes (0-4) for automation:

| Code | Meaning | Common Causes | Solution |
|------|---------|---------------|----------|
| `0` | Success | None | No action needed |
| `1` | Error | Config errors, API failures, processing errors, unexpected exceptions | Check logs with `-vv` |
| `2` | Partial Success | Some repositories failed, incomplete data, warnings present | Review warnings, check failed repos |
| `3` | Usage Error | Invalid arguments, missing required flags, incorrect syntax | Fix command syntax, check `--help` |
| `4` | System Error | Permission denied, out of disk space, missing dependencies | Check permissions, disk space, dependencies |

Using in scripts:

```bash
#!/bin/bash
reporting-tool generate --project test --repos-path ./repos
EXIT_CODE=$?

case $EXIT_CODE in
  0) echo "✓ Success" ;;
  1) echo "✗ Error - check logs for configuration, API, or processing issues" ;;
  2) echo "⚠ Partial success - report generated with warnings" ;;
  3) echo "✗ Usage error - check command syntax and arguments" ;;
  4) echo "✗ System error - check permissions, disk space, or dependencies" ;;
  *) echo "✗ Unknown error: $EXIT_CODE" ;;
esac

exit $EXIT_CODE
```

Retry Logic (for automation):

```bash
#!/bin/bash
# Retry on transient errors (codes 1, 2, 4)
# Don't retry usage errors (code 3)
MAX_RETRIES=3
RETRY=0

while [ $RETRY -lt $MAX_RETRIES ]; do
  reporting-tool generate --project test --repos-path ./repos
  EXIT_CODE=$?

  # Success - exit
  [ $EXIT_CODE -eq 0 ] && exit 0

  # Usage error - don't retry
  [ $EXIT_CODE -eq 3 ] && echo "Usage error - won't retry" && exit 3

  # Other errors - retry
  RETRY=$((RETRY + 1))
  echo "Attempt $RETRY failed (code $EXIT_CODE), retrying in 5s..."
  sleep 5
done

echo "Failed after $MAX_RETRIES attempts"
exit 1
```text

See Also:

- [CLI Reference: Exit Codes](CLI_REFERENCE.md#exit-codes) - Detailed exit code documentation
- [CLI FAQ: Error Handling](CLI_FAQ.md#error-handling) - Common error scenarios

---

## Advanced Debugging

### Enable Maximum Verbosity

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  -vvv  # TRACE level
```text

### Single-Threaded Debugging

```bash
# Easier to debug without parallelism
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  --workers 1 \
  -vv
```text

### Python Debugger

```bash
# Add breakpoint in code
python -m pdb -m reporting_tool.main \
  --project my-project \
  --repos-path /workspace/repos
```

### Capture Full Logs

```bash
reporting-tool generate \
  --project my-project \
  --repos-path /workspace/repos \
  -vv 2>&1 | tee debug.log
```text

### Test Specific Repository

```bash
# Isolate problematic repository
mkdir test
cp -r repos/problematic-repo test/
reporting-tool generate \
  --project test \
  --repos-path test/ \
  -vv
```text

### Verify Git Repository

```bash
# Check if repository is valid
cd repos/repo-name
git status
git log --oneline -10
```text

### Check Python Environment

```bash
# Verify Python version
python --version  # Should be 3.9+

# Check installed packages
pip list | grep -E '(yaml|jinja2|jsonschema|httpx|tqdm)'

# Reinstall dependencies
uv sync  # Recommended
# or: pip install . --force-reinstall
```

---

## Getting More Help

### 1. Check Documentation

- [CLI Reference](CLI_REFERENCE.md)
- [Configuration Guide](CONFIGURATION.md)
- [Quick Start](QUICK_START.md)

### 2. Use Built-in Diagnostics

```bash
# Validate configuration
--dry-run

# Check configuration
--show-config

# List features
--list-features
```text

### 3. Enable Verbose Logging

```bash
-vv  # Debug level
-vvv # Trace level
```text

### 4. Search for Similar Issues

Common patterns to search for:

- Error message text
- Exit code
- Stack trace snippets

---

## 🔗 Related Documentation

This troubleshooting guide works with other documentation:

### Quick Reference Guides

- **[CLI FAQ](CLI_FAQ.md)** - Quick answers to 60+ common questions
- **[CLI Quick Start](CLI_QUICK_START.md)** - Visual troubleshooting decision tree
- **[CLI Cheat Sheet](CLI_CHEAT_SHEET.md)** - Quick command reference

### Detailed Guides

- **[CLI Guide](CLI_GUIDE.md#troubleshooting)** - Comprehensive troubleshooting workflows
- **[CLI Reference](CLI_REFERENCE.md#exit-codes)** - Complete exit code documentation
- **[GitHub API Error Logging](../GITHUB_API_ERROR_LOGGING.md)** - API-specific troubleshooting

### Setup & Configuration

- **[Setup Guide](../SETUP.md)** - Initial setup troubleshooting
- **[Configuration Wizard](CONFIG_WIZARD_GUIDE.md)** - Configuration help
- **[GitHub Token Requirements](../GITHUB_TOKEN_REQUIREMENTS.md)** - Token troubleshooting

### Test Suite

- **[Parallel Execution Guide](testing/PARALLEL_EXECUTION.md)** - Parallel execution troubleshooting
- **[Test Writing Guide](testing/TEST_WRITING_GUIDE.md)** - Test isolation and best practices

### Navigation

Start at **[CLI Documentation Hub](CLI_README.md)** for all CLI documentation.

---

## Common Error Patterns

### Pattern: "Cannot find X"

Usually a path or configuration issue.

Check:

1. File/directory exists
2. Correct path (absolute vs relative)
3. Permissions
4. Configuration spelling

---

### Pattern: "Invalid X"

Usually a validation or format issue.

Check:

1. YAML syntax
2. Data types (number vs string)
3. Value ranges
4. Configuration schema

---

### Pattern: "Permission denied"

File system permission issue.

Check:

1. File permissions (`ls -l`)
2. Directory permissions (`ls -ld`)
3. Ownership (`ls -l`)
4. SELinux/AppArmor policies

---

### Pattern: "Connection refused/timeout"

Network or API issue.

Check:

1. Network connectivity
2. API tokens
3. Firewall rules
4. Proxy settings

---

Still stuck? The error messages include suggestions and documentation links to help you resolve issues quickly!

---

Last Updated: 2025-01-25
Version: Phase 9 Enhanced CLI

---

## INFO.yaml Reports

### No INFO.yaml Data Appears

**Symptom:** Report generated but no INFO.yaml section visible

**Solutions:**

```bash
# 1. Verify enabled in config
grep "info_yaml:" config.yaml -A 3

# 2. Check for INFO.yaml files
find /path/to/info-master -name "INFO.yaml" | wc -l

# 3. Verify configuration
reporting-tool config show | grep -A 20 "info_yaml:"

# 4. Check logs
tail -f logs/reporting-tool.log | grep -i "info.yaml"
```

**Fix:**

```yaml
info_yaml:
  enabled: true  # Must be true
  source:
    type: "git"
    url: "https://gerrit.linuxfoundation.org/infra/info-master"
```

### Slow URL Validation

**Symptom:** Report generation takes 10+ minutes, stuck on "Validating URLs"

**Cause:** Sequential URL validation (default)

**Solutions:**

```yaml
# Enable async validation (10x faster)
info_yaml:
  performance:
    async_validation: true
    max_concurrent_urls: 30  # Increase concurrency

  # Or reduce validation scope
  validation:
    timeout: 5.0  # Reduce from 10.0
    retries: 1    # Reduce from 2

  # Or disable validation temporarily
  validation:
    enabled: false  # Skip validation for speed
```

**Expected Performance:**

- Sequential: ~20 seconds for 100 URLs
- Async (20 concurrent): ~2 seconds for 100 URLs

### Wrong Activity Colors

**Symptom:** Committers have incorrect color codes (green/orange/red/gray)

**Causes:**

1. Email mismatch between INFO.yaml and Git commits
2. Wrong activity window thresholds
3. Git data not enriched

**Solutions:**

```yaml
# 1. Adjust activity windows
info_yaml:
  activity_windows:
    current: 365   # Change if too strict
    active: 1095   # Change if too lenient

# 2. Verify email matching
# Check committer email in INFO.yaml matches Git author email
```

```bash
# Debug: Compare INFO.yaml emails with Git emails
git -C /path/to/repo log --pretty=format:"%ae" --since="1 year ago" | sort -u
```

**Color Legend:**

- 🟢 Green: Last commit 0-365 days
- 🟠 Orange: Last commit 365-1095 days
- 🔴 Red: Last commit 1095+ days
- ⚫ Gray: No matching Git data

### Projects Not Found / Missing

**Symptom:** Expected projects don't appear in report

**Causes:**

1. Filtered by Gerrit server
2. Filtered by lifecycle state
3. Archived projects excluded
4. Parse errors

**Solutions:**

```yaml
# Remove filters to see all projects
info_yaml:
  filters:
    # Comment out to disable filtering
    # gerrit_servers:
    #   - "gerrit.onap.org"
    exclude_archived: false  # Include archived
```

```bash
# Check for parse errors
tail -f logs/reporting-tool.log | grep -i "parse error"

# List all INFO.yaml files
find info-master/ -name "INFO.yaml" -exec dirname {} \;
```

### Parse Errors

**Symptom:** "Failed to parse INFO.yaml" errors in logs

**Causes:**

1. Malformed YAML syntax
2. Missing required fields
3. Encoding issues

**Solutions:**

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('path/to/INFO.yaml'))"

# Check for required fields
cat path/to/INFO.yaml | grep -E "^project:|^project_creation_date:|^lifecycle_state:"
```

**Required Fields:**

```yaml
project: 'project-name'
project_creation_date: '2020-01-15'
lifecycle_state: 'Active'
project_lead:
  name: 'Jane Doe'
  email: 'jane@example.com'
```

### Cache Issues

**Symptom:** Stale data, outdated URLs, old activity colors

**Solutions:**

```bash
# Clear cache
rm -rf ~/.cache/reporting-tool/info-yaml/*

# Verify cache cleared
ls -la ~/.cache/reporting-tool/info-yaml/

# Disable cache temporarily
```

```yaml
info_yaml:
  performance:
    cache_enabled: false  # Disable for fresh data
```

### Memory Issues

**Symptom:** High memory usage, OOM errors with large INFO.yaml repos

**Solutions:**

```yaml
# Reduce cache size
info_yaml:
  performance:
    max_cache_entries: 500  # Reduce from 1000
    max_cache_size_mb: 50   # Reduce from 100

# Reduce concurrency
  performance:
    max_concurrent_urls: 10  # Reduce from 20

# Filter to reduce dataset
  filters:
    gerrit_servers:
      - "gerrit.onap.org"  # Only one server
    exclude_archived: true
```

### URL Validation Failures

**Symptom:** All URLs show as invalid, many validation errors

**Causes:**

1. Network connectivity issues
2. Firewall blocking requests
3. Timeout too short
4. Servers down

**Solutions:**

```yaml
# Increase timeout and retries
info_yaml:
  validation:
    timeout: 15.0  # Increase from 10.0
    retries: 3     # Increase from 2

# Or disable temporarily
  validation:
    enabled: false
```

```bash
# Test URL manually
curl -I -L https://jira.example.org --max-time 10

# Check network connectivity
ping jira.example.org
```

### Git Data Not Enriched

**Symptom:** All committers show gray (unknown status)

**Causes:**

1. No Git repositories provided
2. Repository paths incorrect
3. Email mismatches

**Solutions:**

```bash
# Verify Git repos provided
ls -la /path/to/repos/

# Check Git repositories match INFO.yaml repository list
cat info-master/gerrit.example.org/project/INFO.yaml | grep repositories: -A 10

# Verify committer emails match Git log
git log --pretty=format:"%ae" | sort -u
```

```yaml
# Ensure enrichment enabled
info_yaml:
  enable_git_enrichment: true  # Default: true
```

### Performance Optimization

**Symptom:** INFO.yaml report generation is slow

**Solutions:**

```yaml
# Full optimization
info_yaml:
  performance:
    # Enable async validation (10x faster)
    async_validation: true
    max_concurrent_urls: 30

    # Enable caching
    cache_enabled: true
    cache_ttl: 3600

    # Use local repository
  source:
    type: "local"
    local_path: "/data/info-master"  # Pre-cloned
    update_on_run: false  # Don't pull updates
```

**Expected Performance:**

- Small (50 projects): ~5 seconds
- Medium (150 projects): ~10 seconds
- Large (500 projects): ~30 seconds

### Debug Mode

Enable detailed logging to diagnose issues:

```yaml
info_yaml:
  log_level: "DEBUG"  # or via env var
```

```bash
# Run with debug logging
REPORTING_TOOL_INFO_YAML_LOG_LEVEL=DEBUG reporting-tool generate --config config.yaml

# Filter logs
tail -f logs/reporting-tool.log | grep "INFO.yaml"
```

---

**Need More Help?**

- [Configuration Guide](CONFIGURATION.md) - Complete INFO.yaml configuration
- [Usage Examples](USAGE_EXAMPLES.md) - INFO.yaml usage examples
- [Performance Guide](PERFORMANCE.md) - Optimization strategies
- [Developer Guide](DEVELOPER_GUIDE.md) - Internal architecture
