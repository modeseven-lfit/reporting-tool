<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# 📊 Repository Reporting System

> Comprehensive multi-repository analysis tool for Linux Foundation projects

Generate detailed reports on Git activity, contributor patterns, CI/CD workflows, and development practices across repositories.

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

- **[Getting Started Guide](docs/GETTING_STARTED.md)** - Complete installation and setup walkthrough
- **[Commands Reference](docs/COMMANDS.md)** - Full command-line reference with quick reference
- **[FAQ](docs/FAQ.md)** - Frequently asked questions
- **[Usage Examples](docs/USAGE_EXAMPLES.md)** - Real-world scenarios and patterns

### ⚙️ Setup & Configuration

- **[Configuration Guide](docs/CONFIGURATION.md)** - All configuration options (GitHub API, INFO.yaml, performance)
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment and operations
- **[CI/CD Integration](docs/CI_CD_INTEGRATION.md)** - GitHub Actions, GitLab CI, and automation

### 🔧 Advanced Usage

- **[Performance Guide](docs/PERFORMANCE.md)** - Optimization, caching, and scaling
- **[Feature Discovery](docs/FEATURE_DISCOVERY_GUIDE.md)** - Understanding automatic feature detection
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Problem solving and debugging

### 👨‍💻 Development

- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Architecture, API reference, and contributing
- **[Testing Guide](docs/TESTING.md)** - Test suite documentation

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
| **Check config** | `reporting-tool generate --project my-project --repos-path ./repos --dry-run` |
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
| **Getting Started** | [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) |
| **Commands** | [docs/COMMANDS.md](docs/COMMANDS.md) |
| **FAQ** | [docs/FAQ.md](docs/FAQ.md) |
| **Configuration** | [docs/CONFIGURATION.md](docs/CONFIGURATION.md) |
| **Usage Examples** | [docs/USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md) |
| **Performance** | [docs/PERFORMANCE.md](docs/PERFORMANCE.md) |
| **Troubleshooting** | [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) |
| **CI/CD Setup** | [docs/CI_CD_INTEGRATION.md](docs/CI_CD_INTEGRATION.md) |
| **Developer Guide** | [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) |

**→ [Complete Documentation Index](docs/INDEX.md)**

---

## 💡 Quick Tips

- 🎯 **First time?** Start with [Getting Started Guide](docs/GETTING_STARTED.md)
- ⚡ **Slow?** Add `--cache --workers 8` for parallel processing
- 🐛 **Issues?** Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- ❓ **Questions?** See [FAQ](docs/FAQ.md)
- 📖 **Need help?** Run `reporting-tool --help`

---

## 🤝 Support

- **Documentation**: [Complete Index](docs/INDEX.md)
- **Issues**: [GitHub Issues](https://github.com/lf-it/reporting-tool/issues)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

---

## 📜 License

Apache-2.0 License - Copyright 2025 The Linux Foundation

---

**Ready to get started?** → [Getting Started Guide](docs/GETTING_STARTED.md)
