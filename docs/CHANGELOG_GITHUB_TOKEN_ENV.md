<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Changelog: GitHub Token Environment Variable Configuration

## Version: 2.0.0 (Feature Enhancement)

**Date**: January 2025

---

## Summary

The reporting tool now supports configurable GitHub token environment variable names via the new `--github-token-env` CLI option. This enhancement improves flexibility for different deployment environments while maintaining backward compatibility.

## What Changed

### Default Behavior (New)

- **Default environment variable**: `GITHUB_TOKEN` (was: hardcoded `CLASSIC_READ_ONLY_PAT_TOKEN`)
- The tool now reads from `GITHUB_TOKEN` by default, aligning with common GitHub conventions

### New CLI Option

```bash
--github-token-env VAR_NAME
```

Allows users to specify which environment variable contains their GitHub Personal Access Token.

## Migration Guide

### For Local Development (No Action Required)

If you already use `GITHUB_TOKEN`, no changes needed:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
reporting-tool generate --project my-project --repos-path ./repos
```

### For CI/CD Environments (Choose One Option)

#### Option 1: Rename Secret (Recommended)

Update your CI/CD secrets from `CLASSIC_READ_ONLY_PAT_TOKEN` to `GITHUB_TOKEN`

**Before:**

```yaml
env:
  CLASSIC_READ_ONLY_PAT_TOKEN: ${{ secrets.CLASSIC_READ_ONLY_PAT_TOKEN }}
```

**After:**

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### Option 2: Use CLI Flag (No Secret Changes)

Keep using `CLASSIC_READ_ONLY_PAT_TOKEN` and specify it explicitly:

```bash
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --github-token-env CLASSIC_READ_ONLY_PAT_TOKEN
```

**In GitHub Actions:**

```yaml
- name: Generate Report
  run: |
    reporting-tool generate \
      --project ${{ matrix.project }} \
      --repos-path ./repos \
      --github-token-env CLASSIC_READ_ONLY_PAT_TOKEN
  env:
    CLASSIC_READ_ONLY_PAT_TOKEN: ${{ secrets.CLASSIC_READ_ONLY_PAT_TOKEN }}
```

## Code Changes

### Files Modified

1. **`src/reporting_tool/cli.py`**
   - Added `--github-token-env` option to Typer CLI
   - Default value: `"GITHUB_TOKEN"`

2. **`src/cli/arguments.py`**
   - Added `--github-token-env` option to legacy argument parser
   - Default value: `"GITHUB_TOKEN"`

3. **`src/reporting_tool/main.py`**
   - Stores `github_token_env` in config as `_github_token_env`
   - Logs which environment variable is being used

4. **`src/reporting_tool/features/registry.py`**
   - Updated `_check_workflows()` to use configured token env var
   - Updated `_check_github_mirror_exists()` to use configured token env var
   - Changed from hardcoded `CLASSIC_READ_ONLY_PAT_TOKEN` to dynamic lookup

5. **`src/config/validator.py`**
   - Updated validation messages to reference configurable token variable

6. **`src/api/github_client.py`**
   - Updated error messages to be generic about token variable name

### Documentation Updates

1. **`SETUP.md`**
   - Updated GitHub token section with default and custom variable info
   - Added CLI usage examples

2. **`configuration/README.md`**
   - Updated environment variable reference

3. **`docs/GITHUB_TOKEN_ENV.md`** (NEW)
   - Comprehensive guide for token configuration
   - Examples for different environments
   - Troubleshooting section
   - Migration guide

### Tests Added

1. **`tests/test_github_token_env.py`** (NEW)
   - Tests for default behavior
   - Tests for custom environment variable names
   - Tests for CLI integration
   - Tests for backward compatibility

## Backward Compatibility

✅ **Fully backward compatible** - existing CI/CD workflows using `CLASSIC_READ_ONLY_PAT_TOKEN` continue to work by specifying `--github-token-env CLASSIC_READ_ONLY_PAT_TOKEN`

## Benefits

1. **Standards Compliance**: Aligns with common practice of using `GITHUB_TOKEN`
2. **Flexibility**: Supports any custom environment variable name
3. **CI/CD Friendly**: Easy to adapt to different CI/CD platforms
4. **Security**: No hardcoded variable names in application logic
5. **Developer Experience**: More intuitive for new users

## Examples

### Local Development

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
reporting-tool generate --project ONAP --repos-path ./repos
```

### GitHub Actions (New Style)

```yaml
- name: Generate Report
  run: reporting-tool generate --project ONAP --repos-path ./repos
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### GitHub Actions (Legacy Compatible)

```yaml
- name: Generate Report
  run: |
    reporting-tool generate \
      --project ONAP \
      --repos-path ./repos \
      --github-token-env CLASSIC_READ_ONLY_PAT_TOKEN
  env:
    CLASSIC_READ_ONLY_PAT_TOKEN: ${{ secrets.CLASSIC_READ_ONLY_PAT_TOKEN }}
```

### Custom Variable

```bash
export MY_CUSTOM_GH_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
reporting-tool generate \
  --project my-project \
  --repos-path ./repos \
  --github-token-env MY_CUSTOM_GH_TOKEN
```

## Testing

All existing tests pass, plus 12 new tests specifically for this feature:

```yaml
tests/test_github_token_env.py::TestGitHubTokenEnvConfiguration - 8 tests
tests/test_github_token_env.py::TestCLIIntegrationWithTokenEnv - 2 tests
tests/test_github_token_env.py::TestBackwardCompatibility - 2 tests
```

## Token Configuration Precedence

The tool looks for tokens in this order (highest to lowest priority):

1. **Explicit token in config file**

   ```yaml
   extensions:
     github_api:
       token: "ghp_explicit_token"
   ```

2. **Environment variable** (specified via `--github-token-env` or default)

   ```bash
   export GITHUB_TOKEN="ghp_env_token"
   ```

3. **No token** (GitHub API features disabled)

## Related Issues

- Improves compatibility with GitHub Actions workflows
- Resolves confusion about which environment variable to use
- Enables better integration with various CI/CD platforms

## Further Reading

- [GITHUB_TOKEN_ENV.md](GITHUB_TOKEN_ENV.md) - Complete configuration guide
- [SETUP.md](../SETUP.md) - General setup instructions
- [API_ACCESS.md](../testing/API_ACCESS.md) - API access configuration

---

**Breaking Changes**: None

**Deprecations**: None (but `CLASSIC_READ_ONLY_PAT_TOKEN` is now considered legacy)

**Recommended Action**: Update CI/CD workflows to use `GITHUB_TOKEN` or explicitly specify `--github-token-env`
