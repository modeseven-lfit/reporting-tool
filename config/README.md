<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Configuration Templates

This directory contains **template configuration files** that the reporting-tool Python package bundles and distributes.

## 📋 Purpose

These templates serve as the foundation for project-specific configurations:

- `default.yaml` - Default configuration used by all projects
- `organizational_domains.yaml` - Organization domain mappings
- `test-project.yaml` - Example project configuration for testing

## 🚀 Usage

### For End Users

**Do NOT edit files in this directory directly.** These are templates distributed with the package.

Instead:

1. **Copy** templates to `/configuration/` directory in your repository
2. **Customize** the copied files for your specific projects
3. Run the reporting tool pointing to your `/configuration/` directory

```bash
# Copy the default template
cp config/default.yaml configuration/default.yaml

# Create a project-specific configuration
cp config/default.yaml configuration/my-project.yaml

# Edit your project configuration
vim configuration/my-project.yaml

# Run with your configuration
reporting-tool generate --project my-project --repos-path ./repos
```

### Configuration Location Priority

The reporting tool looks for configurations in this order:

1. `/configuration/` directory (for customized, project-specific configs)
2. `/config/` directory (for package-bundled templates - as fallback)

## 📂 Directory Structure

```text
/config/                          # Template files (this directory)
├── README.md                     # This file
├── default.yaml                  # Base configuration template
├── organizational_domains.yaml   # Domain mappings template
└── test-project.yaml            # Test/example configuration

/configuration/                   # Your customized configurations
├── default.yaml                  # Your base settings
├── onap.yaml                     # ONAP-specific settings
├── opendaylight.yaml            # OpenDaylight-specific settings
└── organizational_domains.yaml   # Your domain mappings
```

## ⚠️ Important Notes

- **Package Distribution**: The PyPI package includes files from `/config/`
- **Git Repository**: Your `/configuration/` directory should contain project-specific settings
- **Version Control**: Add `/configuration/` to your repository, keep `/config/` as-is
- **Updates**: Package updates may change `/config/` templates - your `/configuration/` files remain unchanged

## 🔧 For Developers

If you're developing the reporting-tool package:

- Edit templates in `/config/` to change default behavior
- Test changes with `test-project.yaml`
- Ensure templates remain generic and well-documented
- Update this README if you add new template files

## 📖 Related Documentation

- [Configuration Guide](../docs/CONFIGURATION.md) - Full configuration reference
- [Getting Started](../docs/GETTING_STARTED.md) - Quick start guide
- [SETUP.md](../SETUP.md) - Deployment and setup instructions

---

**Version:** 1.0
**Last Updated:** 2025-01-XX
