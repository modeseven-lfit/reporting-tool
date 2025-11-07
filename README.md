<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# 📊 Repository Reporting System

> Comprehensive multi-repository analysis tool for Linux Foundation projects

Generate detailed reports on Git activity, contributor patterns, CI/CD workflows, and development practices across multiple repositories.

---

## ⚡ Quick Start

```bash
# Install
pip install .

# Generate your first report
reporting-tool generate \
  --project my-project \
  --repos-path ./repos
```

**→ [Full Quick Start Guide](docs/QUICK_START.md)**

---

## 🚀 Key Features

- **📈 Git Analytics** - Commit activity, lines of code, contributor metrics across configurable time windows
- **🔍 Feature Detection** - Automatic detection of CI/CD, documentation, dependency management, security tools
- **👥 Contributor Intelligence** - Author and organization analysis with domain mapping
- **🌐 API Integration** - GitHub, Gerrit, and Jenkins API support
- **📊 Interactive Reports** - JSON (data), Markdown (readable), HTML (interactive), ZIP (bundled)
- **⚡ High Performance** - Parallel processing with caching support

---

## 📚 Documentation

### 🎯 Getting Started

- **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running in minutes
- **[CLI Cheat Sheet](docs/CLI_CHEAT_SHEET.md)** - Common commands at a glance
- **[CLI Guide](docs/CLI_GUIDE.md)** - Complete user guide with examples
- **[Usage Examples](docs/USAGE_EXAMPLES.md)** - Real-world scenarios

### ⚙️ Setup & Configuration

- **[Installation & Setup](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)** - Production deployment guide
- **[CLI Reference](docs/CLI_REFERENCE.md)** - Complete command reference
- **[Configuration Guide](docs/CONFIG_WIZARD_GUIDE.md)** - Configuration options and best practices
- **[GitHub Token Setup](docs/GITHUB_TOKEN_REQUIREMENTS.md)** - Required API tokens

### 🔧 Advanced Usage

- **[Performance Guide](docs/PERFORMANCE_GUIDE.md)** - Optimization and tuning
- **[Feature Discovery](docs/FEATURE_DISCOVERY_GUIDE.md)** - Understanding feature detection
- **[CI/CD Integration](docs/CI_CD_INTEGRATION.md)** - GitHub Actions and automation
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### 👨‍💻 Development

- **[Developer Guide](docs/DEVELOPER_QUICK_REFERENCE.md)** - Architecture and contribution guide
- **[Testing Guide](docs/TESTING_GUIDE.md)** - Running and writing tests

---

## 💻 Installation

### Using UV (Recommended)

```bash
# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the tool
uv run reporting-tool generate --project my-project --repos-path ./repos
```

### Using pip

```bash
# Install from source
pip install .

# Run the tool
reporting-tool generate --project my-project --repos-path ./repos
```

**→ [Detailed Setup Instructions](SETUP.md)**

---

## 🎯 Common Use Cases

| Use Case | Command |
|----------|---------|
| **Basic report** | `reporting-tool generate --project my-project --repos-path ./repos` |
| **With caching** | `reporting-tool generate --project my-project --repos-path ./repos --cache --workers 8` |
| **Validate config** | `reporting-tool generate --project my-project --repos-path ./repos --dry-run` |
| **List features** | `reporting-tool list-features` |
| **Get help** | `reporting-tool --help` |

**→ [More Examples](docs/USAGE_EXAMPLES.md)**

---

## 📊 Output Formats

```text
reports/
  <PROJECT>/
    ├── report_raw.json           # Complete dataset (canonical)
    ├── report.md                 # Markdown report (readable)
    ├── report.html               # Interactive HTML (sortable tables)
    ├── config_resolved.json      # Applied configuration
    └── <PROJECT>_report_bundle.zip  # Complete bundle
```

---

## 🔌 CI/CD Integration

### GitHub Actions

```yaml
- name: Generate Report
  run: |
    uv run reporting-tool generate \
      --project "${{ matrix.project }}" \
      --repos-path "./${{ matrix.server }}" \
      --cache \
      --quiet
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**→ [Full CI/CD Integration Guide](docs/CI_CD_INTEGRATION.md)**

---

## 🔧 Requirements

- **Python**: 3.10+ (supports 3.10, 3.11, 3.12, 3.13)
- **Dependencies**: PyYAML, httpx, Jinja2, typer, rich
- **Optional**: GitHub token for API features

**→ [Complete Requirements](docs/PRODUCTION_DEPLOYMENT_GUIDE.md#requirements)**

---

## 📖 Key Documentation Files

| Topic | Document |
|-------|----------|
| **Quick Start** | [docs/QUICK_START.md](docs/QUICK_START.md) |
| **CLI Reference** | [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md) |
| **CLI FAQ** | [docs/CLI_FAQ.md](docs/CLI_FAQ.md) |
| **Performance** | [docs/PERFORMANCE_GUIDE.md](docs/PERFORMANCE_GUIDE.md) |
| **Troubleshooting** | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| **GitHub Setup** | [docs/GITHUB_TOKEN_REQUIREMENTS.md](docs/GITHUB_TOKEN_REQUIREMENTS.md) |
| **CI/CD Setup** | [docs/CI_CD_INTEGRATION.md](docs/CI_CD_INTEGRATION.md) |
| **Developer Guide** | [docs/DEVELOPER_QUICK_REFERENCE.md](docs/DEVELOPER_QUICK_REFERENCE.md) |

**→ [Browse All Documentation](docs/)**

---

## 💡 Quick Tips

- 🎯 **First time?** Start with [Quick Start Guide](docs/QUICK_START.md)
- ⚡ **Slow?** Add `--cache --workers 8` for parallel processing
- 🐛 **Issues?** Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- ❓ **Questions?** See [CLI FAQ](docs/CLI_FAQ.md)
- 📖 **Need help?** Run `reporting-tool --help`

---

## 🤝 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/lf-it/reporting-tool/issues)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

## 📜 License

Apache-2.0 License - Copyright 2025 The Linux Foundation

---

**Ready to get started?** → [Quick Start Guide](docs/QUICK_START.md)
