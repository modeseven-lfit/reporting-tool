<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Configuration Directory

This directory contains configuration files for the Repository Reporting Tool.

## Overview

The reporting tool uses a **default-based configuration system** that allows projects to work out-of-the-box without requiring custom configuration files. This makes it easy to get started while still supporting project-specific customization.

## How It Works

1. **Default Configuration** (`default.yaml`)
   - Contains sensible defaults that work for 90% of projects
   - Automatically used when no project-specific configuration exists
   - Based on the `template.config` from the [project-reports](https://github.com/modeseven-lfit/project-reports) repository

2. **Project-Specific Configuration** (Optional)
   - Create `<project-name>.yaml` to customize settings for a specific project
   - Project settings **override** the defaults (deep merge)
   - Include settings you want to change from the defaults

3. **No Configuration Required**
   - If no project-specific config exists, the tool automatically uses `default.yaml`
   - The tool will run with the defaults

## File Structure

```text
configuration/
├── README.md                      # This file
├── default.yaml                   # Default configuration (do not change in projects)
├── organizational_domains.yaml    # Domain extraction rules for contributor organizations
├── test-project.yaml              # Example project configuration
└── <project>.yaml                 # Your project-specific configurations
```

## Quick Start

### Option 1: Use Defaults (Recommended for Most Projects)

Run the reporting tool - no configuration file needed!

```bash
reporting-tool generate \
  --project O-RAN-SC \
  --repos-path ./gerrit.o-ran-sc.org
```

The tool will automatically use `default.yaml`.

### Option 2: Create Project-Specific Configuration

Create a custom configuration if you need to override defaults:

1. **Copy the default as a template:**

   ```bash
   cp configuration/default.yaml configuration/ONAP.yaml
   ```

2. **Edit the settings you want to change:**

   ```yaml
   # configuration/ONAP.yaml
   project: ONAP

   # Override what you need
   performance:
     max_workers: 16  # Increase from default 8

   output:
     formats:
       - json
       - html  # Remove markdown
   ```

3. **Run with your project name:**

   ```bash
   reporting-tool generate \
     --project ONAP \
     --repos-path ./gerrit.onap.org
   ```

## Configuration Format

### Time Windows

Time windows define periods for analysis. The format uses a dictionary with a `days` key:

```yaml
time_windows:
  last_30:
    days: 30
  last_90:
    days: 90
  last_365:
    days: 365
  last_3_years:
    days: 1095
```

**Note:** The `_days` suffix in the key name is redundant since all values are in days.

### Activity Thresholds

Define when repositories are current, active, or inactive:

```yaml
activity_thresholds:
  current_days: 365      # ✅ Current: commits within last 365 days
  active_days: 1095      # ☑️ Active: commits between 365-1095 days
  # 🛑 Inactive: no commits in 1095+ days
```

### Output Configuration

```yaml
output:
  directory: reports
  formats:
    - json      # Machine-readable data
    - md        # Markdown reports
    - html      # Interactive HTML reports
  create_bundle: true
  include_sections:
    contributors: true
    organizations: true
    repo_feature_matrix: true
    # ... see default.yaml for all options
```

### Performance Settings

```yaml
performance:
  max_workers: 8      # Parallel workers
  cache: false        # Enable for faster later runs
```

### Feature Detection

```yaml
features:
  enabled:
    - dependabot
    - github2gerrit_workflow
    - pre_commit
    - readthedocs
    # ... see default.yaml for all available features

### Organizational Domain Mapping

The `organizational_domains.yaml` file controls how contributor email domains map to organizations:

```yaml
# Domains to preserve in full (don't truncate to last 2 parts)
preserve_full_domain:
  - "zte.com.cn"  # Chinese domain requiring 3 parts for proper ID

# Custom domain to organization mappings
custom_mappings:
  contractor.example.org: "Example Corp"

# Domains to ignore (will not be grouped)
ignore_domains:
  - "unknown"
  - "localhost"
```

**Default behavior:** Extract last 2 parts of domain

- `users.noreply.github.com` → `github.com`
- `contractor.linuxfoundation.org` → `linuxfoundation.org`

**With preservation:** Keep full domain

- `zte.com.cn` → `zte.com.cn` (preserved as configured)

```text

## Examples

### Example 1: Minimal Override (Change Workers)

```yaml
# configuration/O-RAN-SC.yaml
project: O-RAN-SC

performance:
  max_workers: 16
```

All other settings inherited from `default.yaml`.

### Example 2: Different Time Windows

```yaml
# configuration/ONAP.yaml
project: ONAP

time_windows:
  last_7:
    days: 7
  last_30:
    days: 30
  last_90:
    days: 90
```

### Example 3: Custom Output Formats

```yaml
# configuration/Akraino.yaml
project: Akraino

output:
  formats:
    - json
  create_bundle: false
```

## Best Practices

1. **Start with defaults** - Don't create a config file unless you need to
2. **Minimal overrides** - Specify settings that differ from defaults
3. **Document changes** - Add comments explaining why you override defaults
4. **Test locally first** - Check config changes before committing
5. **Keep aligned** - Follow the structure in `default.yaml`

## Environment Variables

Some settings can be overridden via environment variables:

- `GITHUB_TOKEN` (default) or custom variable via `--github-token-env` - GitHub API authentication
- `JENKINS_HOST` - Jenkins server URL
- `GITHUB_ORG` - GitHub organization for Gerrit mirrors

## Validation

Check your configuration before running:

```bash
# This will load and check the config
reporting-tool generate \
  --project O-RAN-SC \
  --repos-path ./gerrit.o-ran-sc.org \
  --dry-run
```

Or use Python directly:

```python
from pathlib import Path
from reporting_tool.config import load_configuration, validate_loaded_config

config = load_configuration(
    project='O-RAN-SC',
    config_dir=Path('configuration')
)
validate_loaded_config(config)  # Check configuration
print("✅ Configuration is valid")
```

## Migration from Old Format

If you have old configuration files with flat time windows:

**Old format:**

```yaml
time_windows:
  last_30_days: 30
  last_90_days: 90
```

**New format:**

```yaml
time_windows:
  last_30:
    days: 30
  last_90:
    days: 90
```

## Alignment with project-reports

This configuration system works with the [project-reports](https://github.com/modeseven-lfit/project-reports) repository. The `default.yaml` structure mirrors the `template.config` from that project to ensure consistency across tools.

The `organizational_domains.yaml` file comes from project-reports and provides consistent contributor organization mapping across both tools.

## Support

For questions or issues:

1. Check `default.yaml` for available configuration options
2. Review existing project configurations for examples
3. See the main project documentation
4. Open an issue on GitHub

---

**Last Updated:** 2025-01-15
**Schema Version:** 1.0.0
