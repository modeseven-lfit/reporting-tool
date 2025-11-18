<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# GitHub Token Environment Variable Configuration

## Overview

The reporting tool now supports configurable GitHub token environment variable names through the `--github-token-env` CLI option, providing flexibility for different deployment environments.

## Quick Start

### Default Behavior (GITHUB_TOKEN)

```bash
export GITHUB_TOKEN="ghp_your_token_here"
reporting-tool generate --project my-project --repos-path ./repos
```

### CI Environment (CLASSIC_READ_ONLY_PAT_TOKEN)

```bash
export CLASSIC_READ_ONLY_PAT_TOKEN="ghp_your_token_here"
reporting-tool generate --project my-project --repos-path ./repos \
  --github-token-env CLASSIC_READ_ONLY_PAT_TOKEN
```

### Custom Variable Name

```bash
export MY_GITHUB_TOKEN="ghp_your_token_here"
reporting-tool generate --project my-project --repos-path ./repos \
  --github-token-env MY_GITHUB_TOKEN
```

## Key Features

- **Default**: Reads from `GITHUB_TOKEN` (standard GitHub convention)
- **Configurable**: Use any environment variable name via `--github-token-env`
- **Backward Compatible**: Existing workflows using `CLASSIC_READ_ONLY_PAT_TOKEN` continue to work
- **CI/CD Friendly**: Easy to adapt to different CI/CD platforms

## Configuration Precedence

1. Explicit token in config file (highest priority)
2. Environment variable (specified via `--github-token-env`)
3. No token (GitHub API features disabled)

## CLI Option

```yaml
--github-token-env VAR_NAME
    Environment variable name for GitHub API token
    Default: GITHUB_TOKEN
    CI typically uses: CLASSIC_READ_ONLY_PAT_TOKEN
```

## Examples

### GitHub Actions

```yaml
- name: Generate Report
  run: reporting-tool generate --project ONAP --repos-path ./repos
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GitLab CI

```yaml
generate_report:
  script:
    - reporting-tool generate
        --project my-project
        --repos-path ./repos
        --github-token-env CI_GITHUB_TOKEN
  variables:
    CI_GITHUB_TOKEN: $CI_GITHUB_TOKEN
```

### Jenkins

```groovy
withCredentials([string(credentialsId: 'github-token', variable: 'GH_TOKEN')]) {
    sh '''
        reporting-tool generate \
            --project my-project \
            --repos-path ./repos \
            --github-token-env GH_TOKEN
    '''
}
```

## Migration from Legacy Workflows

### Option 1: Rename Secret (Recommended)

Change `CLASSIC_READ_ONLY_PAT_TOKEN` → `GITHUB_TOKEN` in your CI/CD secrets

### Option 2: Use CLI Flag

Keep existing secret name and specify `--github-token-env CLASSIC_READ_ONLY_PAT_TOKEN`

## Documentation

- [Complete Guide](../GITHUB_TOKEN_ENV.md) - Detailed configuration and troubleshooting
- [Setup Guide](../../SETUP.md) - General setup instructions
- [Changelog](../CHANGELOG_GITHUB_TOKEN_ENV.md) - Complete change details

## Benefits

✅ Standards compliance with GitHub conventions
✅ Flexible for various CI/CD platforms
✅ No breaking changes to existing workflows
✅ Improved developer experience
✅ Better security practices (no hardcoded variable names)
