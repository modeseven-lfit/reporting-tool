<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# API Access Configuration for Local Testing

This document explains how to enable API integrations (GitHub, Gerrit, Jenkins) when running the local testing script to get complete data in your reports.

## Overview

The reporting tool can collect data from these sources:

1. **Git repositories** (local) - ✅ Always available
2. **INFO.yaml files** (cloned from info-master) - ✅ Always available
3. **GitHub API** - ⚠️ Requires configuration
4. **Gerrit API** - ⚠️ Requires configuration
5. **Jenkins API** - ⚠️ Requires configuration

By default, the tool uses local git data and INFO.yaml files. To get workflow status, CI/CD information, and other API-based data, you need to configure API access.

## Quick Check: API Usage Status

Look for these indicators in the output:

### ✅ APIs Are Working

```text
[INFO] Fetching workflow status from GitHub API...
[INFO] Connected to Gerrit API at https://gerrit.onap.org
[INFO] Checking Jenkins jobs for repository...
```

### ❌ APIs Are NOT Working

```text
[INFO] Discovered 179 git repositories
[INFO] Aggregated 1532 unique authors across repositories
[INFO] Analysis complete: 179 repositories, 0 errors
```

If you see git analysis and no API calls, the configuration has disabled the APIs or they lack proper configuration.

## Why Your Reports Were Fast

If your reports generated in ~10-20 seconds for hundreds of repositories:

- ✅ Local git analysis completed
- ❌ GitHub API calls did not occur
- ❌ Gerrit API calls did not occur
- ❌ Jenkins API calls did not occur

With full API access enabled, reports take much longer (3-5 minutes) because the tool:

- Queries GitHub for workflow status on each repository
- Queries Gerrit for repository metadata
- Queries Jenkins for CI/CD job information

## Configuration Options

### Option 1: Environment Variables (Recommended for Testing)

Set environment variables before running the test script:

```bash
# GitHub API access (use either GITHUB_TOKEN or CLASSIC_READ_ONLY_PAT_TOKEN)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
# OR for CI/production environments:
# export CLASSIC_READ_ONLY_PAT_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Gerrit API access (if needed)
export GERRIT_HOST="gerrit.onap.org"
export GERRIT_BASE_URL="https://gerrit.onap.org"

# Jenkins API access (if needed)
export JENKINS_HOST="jenkins.onap.org"
export JENKINS_BASE_URL="https://jenkins.onap.org"

# Run the test script
cd reporting-tool/testing
./local-testing.sh
```

### Option 2: Project-Specific Configuration File

Create configuration files for each project:

**`configuration/onap.yaml`:**

```yaml
---
project: ONAP

# Enable GitHub API
extensions:
  github_api:
    enabled: true
    token: ""  # Will use GITHUB_TOKEN or CLASSIC_READ_ONLY_PAT_TOKEN env var
    github_org: "onap"

# Enable Gerrit API
gerrit:
  enabled: true
  host: "gerrit.onap.org"
  base_url: "https://gerrit.onap.org"

# Enable Jenkins API
jenkins:
  enabled: true
  host: "jenkins.onap.org"
  base_url: "https://jenkins.onap.org"
```

**`configuration/opendaylight.yaml`:**

```yaml
---
project: OpenDaylight

# Enable GitHub API
extensions:
  github_api:
    enabled: true
    token: ""  # Will use GITHUB_TOKEN or CLASSIC_READ_ONLY_PAT_TOKEN env var
    github_org: "opendaylight"

# Enable Gerrit API
gerrit:
  enabled: true
  host: "git.opendaylight.org"
  base_url: "https://git.opendaylight.org"

# Enable Jenkins API
jenkins:
  enabled: true
  host: "jenkins.opendaylight.org"
  base_url: "https://jenkins.opendaylight.org"
```

Then update the test script to use these configurations:

```bash
# In local-testing.sh, add --config-dir flag:
uv run reporting-tool generate \
    --project "ONAP" \
    --repos-path "${ONAP_CLONE_DIR}" \
    --output-dir "${ONAP_REPORT_DIR}" \
    --config-dir "${REPO_ROOT}/configuration" \
    --cache \
    --workers 4
```

## Getting API Tokens

### GitHub Personal Access Token

1. Go to <https://github.com/settings/tokens>
2. Click "Generate new token" → "Generate new token (classic)"
3. Select scopes:
   - `repo` (for private repos) or `public_repo` (for public repos)
   - `workflow` (to read workflow status)
4. Click "Generate token"
5. Copy the token (starts with `ghp_`)

**For local testing:**

```bash
# Standard GitHub token (most common for local development)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# OR use CLASSIC_READ_ONLY_PAT_TOKEN (matches CI/production environment)
export CLASSIC_READ_ONLY_PAT_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
```

**Note:** The reporting tool checks for `CLASSIC_READ_ONLY_PAT_TOKEN` first, then falls back to `GITHUB_TOKEN`. This matches the GitHub Actions production workflow configuration.

**Rate limits:**

- Without token: 60 requests/hour
- With token: 5,000 requests/hour

### Gerrit Access

Gerrit API is typically open for read access on public servers. No authentication needed for:

- `gerrit.onap.org`
- `git.opendaylight.org`

If authentication becomes necessary:

```bash
export GERRIT_USERNAME="your-username"
export GERRIT_PASSWORD="your-password"
```

### Jenkins Access

Jenkins API is typically open for read access on public servers. No authentication needed for:

- `jenkins.onap.org`
- `jenkins.opendaylight.org`

If authentication becomes necessary:

```bash
export JENKINS_USERNAME="your-username"
export JENKINS_API_TOKEN="your-api-token"
```

## Verifying API Access

### Test GitHub API Access

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Test API call
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# Should return your user info, not rate limit error
```

### Test Gerrit API Access

```bash
# Test Gerrit API (no auth needed for public servers)
curl https://gerrit.onap.org/r/projects/?d

# Should return list of projects in JSON format
```

### Test Jenkins API Access

```bash
# Test Jenkins API (no auth needed for public servers)
curl https://jenkins.onap.org/api/json

# Should return Jenkins instance info
```

## Updated Test Script

Here's how to run the test script with full API access:

```bash
#!/bin/bash

# Set API tokens (use either GITHUB_TOKEN or CLASSIC_READ_ONLY_PAT_TOKEN)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
# OR for CI-like environment:
# export CLASSIC_READ_ONLY_PAT_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Optional: Enable Gerrit/Jenkins if needed
# export GERRIT_HOST="gerrit.onap.org"
# export JENKINS_HOST="jenkins.onap.org"

# Run the test script
cd reporting-tool/testing
./local-testing.sh
```

## What Data Each API Provides

### GitHub API

- ✅ Workflow status (passing/failing)
- ✅ Last workflow run timestamp
- ✅ Branch protection rules
- ✅ Repository metadata (stars, forks, etc.)
- ✅ Issue/PR counts (if enabled)

**Impact on report:**

- Workflow status columns populated
- More accurate "CI/CD" feature detection
- GitHub-specific metrics

### Gerrit API

- ✅ Project metadata
- ✅ Repository state (active/read-restricted/hidden)
- ✅ Parent project information
- ✅ Branch information
- ✅ Access controls

**Impact on report:**

- More accurate repository status
- Better project hierarchy information
- Gerrit-specific metadata

### Jenkins API

- ✅ Job status
- ✅ Build history
- ✅ Last successful build
- ✅ Build artifacts
- ✅ Job configuration

**Impact on report:**

- Jenkins CI/CD status
- Build health indicators
- Integration with Gerrit reviews

## Troubleshooting

### "Analysis complete" but no API calls

**Cause:** Configuration has disabled APIs or no tokens provided

**Solution:**

1. Check that `extensions.github_api.enabled: true` in config
2. Set `GITHUB_TOKEN` or `CLASSIC_READ_ONLY_PAT_TOKEN` environment variable
3. Verify token has correct permissions
4. Check resolved config with: `cat /tmp/reports/PROJECT/config_resolved.json | grep github`

### "Error: GitHub API query returned error code: 401"

**Cause:** Token is invalid, expired, or has "Bad credentials"

**Symptoms:**

```text
[ERROR] ❌ Error: GitHub API query returned error code: 401 for onap/repo-name
```

**Solution:**

1. **Test the token directly:**

   ```bash
   curl -H "Authorization: token $CLASSIC_READ_ONLY_PAT_TOKEN" \
     https://api.github.com/user
   ```

   Expected: Your user info (JSON)

   If you get `{"message": "Bad credentials", ...}` then:
   - Token expired or revoked
   - Token string is incorrect
   - You must regenerate the token

2. **Regenerate the token:**
   - Go to <https://github.com/settings/tokens>
   - Delete the old token
   - Create new token with required scopes:
     - ☑ `public_repo` (for public repos) OR `repo` (for all repos)
     - ☑ `workflow` (to read workflow runs)
   - Update your environment variable with the new token

3. **Verify token permissions:**

   ```bash
   curl -H "Authorization: token $CLASSIC_READ_ONLY_PAT_TOKEN" \
     https://api.github.com/repos/onap/integration/actions/workflows
   ```

   Should return list of workflows, not 401 error

### "GitHub API rate limit exceeded"

**Cause:** Too frequent API calls without authentication

**Solution:**

1. Set `GITHUB_TOKEN` for 5000 req/hour limit
2. Enable caching: `--cache` flag
3. Reduce number of repositories under analysis

### "Connection refused" or "Timeout"

**Cause:** API server unreachable or firewall blocking

**Solution:**

1. Verify server URL is correct
2. Check network connectivity
3. Try increasing timeout in configuration:

   ```yaml
   gerrit:
     timeout: 60.0
   jenkins:
     timeout: 60.0
   extensions:
     github_api:
       timeout: 60.0
   ```

### API Calls Complete But Data Missing

**Cause:** API calls fail without errors or return no data

**Solution:**

1. Run with `--verbose` flag to see detailed logs
2. Check API responses manually with `curl`
3. Verify repository names match between Gerrit/GitHub
4. Check if token environment variable detection works:

   ```bash
   # Look for "_github_token_env" in resolved config
   cat /tmp/reports/PROJECT/config_resolved.json | grep _github_token_env
   # Should show: "_github_token_env: GITHUB_TOKEN" or "CLASSIC_READ_ONLY_PAT_TOKEN"
   ```

5. Verify `has_runtime_status: true` in raw JSON:

   ```bash
   grep "has_runtime_status" /tmp/reports/PROJECT/report_raw.json | head -5
   # Should show "true" if GitHub API calls succeeded
   ```

## Performance Impact

With all APIs enabled:

| Project | Repos | No APIs | With APIs | Difference |
|---------|-------|---------|-----------|------------|
| ONAP | 179 | ~15 sec | ~5-10 min | 20-40x slower |
| OpenDaylight | 39 | ~7 sec | ~2-3 min | 15-25x slower |

**Why the difference?**

- Each repository may require 5-10 API calls
- Network latency for API requests
- Rate limiting delays
- API server response times

**Optimization tips:**

- Enable caching with `--cache` flag
- Use more workers with `--workers 8`
- Run during off-peak hours for public APIs

## See Also

- [Configuration Guide](../docs/CONFIGURATION.md)
- GitHub Token Requirements
- [API Integration Documentation](../docs/CI_CD_INTEGRATION.md)
- [Performance Guide](../docs/PERFORMANCE.md)
