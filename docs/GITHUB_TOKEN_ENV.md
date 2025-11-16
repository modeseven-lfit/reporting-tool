# GitHub Token Environment Variable Configuration

## Overview

The reporting tool needs a GitHub Personal Access Token (PAT) to query the GitHub API for workflow status, repository information, and other metadata. This document explains how to configure which environment variable the tool reads for the GitHub token.

## Default Behavior

By default, the tool reads the GitHub token from the **`GITHUB_TOKEN`** environment variable:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
reporting-tool generate --project my-project --repos-path ./repos
```

## Custom Environment Variable

You can specify a different environment variable name using the `--github-token-env` option:

```bash
export CUSTOM_TOKEN_VAR="ghp_your_token_here"
reporting-tool generate --project my-project --repos-path ./repos \
  --github-token-env CUSTOM_TOKEN_VAR
```

## CI/CD Environment

For existing CI/CD workflows that use `CLASSIC_READ_ONLY_PAT_TOKEN`, you can specify it explicitly:

```bash
export CLASSIC_READ_ONLY_PAT_TOKEN="ghp_your_token_here"
reporting-tool generate --project my-project --repos-path ./repos \
  --github-token-env CLASSIC_READ_ONLY_PAT_TOKEN
```

## Usage Examples

### Local Development (Default)

```bash
# Set the token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"

# Run the tool (uses GITHUB_TOKEN by default)
reporting-tool generate --project ONAP --repos-path ./repos
```

### GitHub Actions Workflow

```yaml
- name: Generate Report
  run: |
    reporting-tool generate \
      --project ${{ matrix.project }} \
      --repos-path /workspace/repos \
      --github-token-env CLASSIC_READ_ONLY_PAT_TOKEN
  env:
    CLASSIC_READ_ONLY_PAT_TOKEN: ${{ secrets.CLASSIC_READ_ONLY_PAT_TOKEN }}
```

### GitLab CI/CD

```yaml
generate_report:
  script:
    - export MY_GITHUB_TOKEN="${CI_GITHUB_TOKEN}"
    - reporting-tool generate 
        --project my-project 
        --repos-path ./repos
        --github-token-env MY_GITHUB_TOKEN
```

## Configuration Precedence

The tool looks for the GitHub token in the following order:

1. **Explicit token in config file** (highest priority)
   ```yaml
   extensions:
     github_api:
       token: "ghp_explicit_token"
   ```

2. **Environment variable** (specified via `--github-token-env` or default `GITHUB_TOKEN`)
   ```bash
   export GITHUB_TOKEN="ghp_env_token"
   ```

3. **No token** (lowest priority - GitHub API features will be disabled)

## Token Requirements

Regardless of which environment variable name you use, the token must be a **Classic Personal Access Token** with the following scopes:

- `repo:status` - Access to repository commit statuses
- `actions:read` - Access to workflow runs

**Why Classic PAT?**

Fine-grained tokens are scoped to a single organization, but the reporting tool often needs to access repositories across multiple Linux Foundation organizations. Classic PATs work across all organizations the token owner has access to.

## Creating a GitHub Token

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click **Generate new token** → **Generate new token (classic)**
3. Select scopes:
   - ✅ `repo:status`
   - ✅ `actions:read`
4. Generate and copy the token
5. Store it securely as an environment variable or secret

## Security Best Practices

### ✅ DO

- Store tokens in environment variables or secrets management systems
- Use CI/CD secret storage (GitHub Secrets, GitLab CI/CD variables, etc.)
- Set token expiration dates
- Rotate tokens regularly
- Use the minimum required scopes

### ❌ DON'T

- Hardcode tokens in configuration files
- Commit tokens to version control
- Share tokens between different systems
- Use tokens with unnecessary permissions

## Troubleshooting

### Token Not Found

**Symptom**: Warning message about missing GitHub token

```
[WARNING] GitHub API enabled but token not available (GITHUB_TOKEN).
          Workflow status will not be queried.
```

**Solutions**:
1. Verify the environment variable is set:
   ```bash
   echo $GITHUB_TOKEN
   ```

2. If using a custom variable name, ensure `--github-token-env` matches:
   ```bash
   # Wrong - variable is CUSTOM_TOKEN but flag says GITHUB_TOKEN
   export CUSTOM_TOKEN="ghp_xxx"
   reporting-tool generate --project test --repos-path ./repos
   
   # Correct - flag matches variable name
   export CUSTOM_TOKEN="ghp_xxx"
   reporting-tool generate --project test --repos-path ./repos \
     --github-token-env CUSTOM_TOKEN
   ```

### Token Permission Errors

**Symptom**: 403 or 401 errors when querying GitHub API

**Solutions**:
1. Verify token has required scopes (`repo:status`, `actions:read`)
2. Check token hasn't expired
3. Ensure token has access to the organizations/repositories you're querying

### Missing Workflow Status

**Symptom**: Workflow status shows as "unknown" or grey in reports

**Solutions**:
1. Verify GitHub token is set correctly
2. Check that you're using a Classic PAT (not fine-grained)
3. Confirm the token has `actions:read` scope
4. Ensure the repositories have GitHub Actions enabled

## Migration from CLASSIC_READ_ONLY_PAT_TOKEN

If you're migrating from older versions that used `CLASSIC_READ_ONLY_PAT_TOKEN`:

### Option 1: Rename Environment Variable (Recommended)

```bash
# Old
export CLASSIC_READ_ONLY_PAT_TOKEN="ghp_xxx"

# New
export GITHUB_TOKEN="ghp_xxx"
```

### Option 2: Use --github-token-env Flag

```bash
# Keep using the old variable name
export CLASSIC_READ_ONLY_PAT_TOKEN="ghp_xxx"

# Specify it explicitly
reporting-tool generate --project my-project --repos-path ./repos \
  --github-token-env CLASSIC_READ_ONLY_PAT_TOKEN
```

### Option 3: Update CI/CD Workflows

For GitHub Actions, update your workflow files:

```yaml
# Old
env:
  CLASSIC_READ_ONLY_PAT_TOKEN: ${{ secrets.CLASSIC_READ_ONLY_PAT_TOKEN }}

# New (Option A: Rename secret to GITHUB_TOKEN)
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

# New (Option B: Keep secret name, use flag)
run: |
  reporting-tool generate \
    --project ${{ matrix.project }} \
    --repos-path ./repos \
    --github-token-env CLASSIC_READ_ONLY_PAT_TOKEN
env:
  CLASSIC_READ_ONLY_PAT_TOKEN: ${{ secrets.CLASSIC_READ_ONLY_PAT_TOKEN }}
```

## Related Documentation

- [SETUP.md](../SETUP.md) - Complete setup guide
- [GITHUB_TOKEN_REQUIREMENTS.md](GITHUB_TOKEN_REQUIREMENTS.md) - Token requirements and permissions
- [API_ACCESS.md](../testing/API_ACCESS.md) - API access configuration
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions

## Summary

| Aspect | Details |
|--------|---------|
| **Default Variable** | `GITHUB_TOKEN` |
| **Legacy Variable** | `CLASSIC_READ_ONLY_PAT_TOKEN` |
| **CLI Option** | `--github-token-env VAR_NAME` |
| **Token Type** | Classic Personal Access Token |
| **Required Scopes** | `repo:status`, `actions:read` |
| **Precedence** | Config file > Environment variable > None |