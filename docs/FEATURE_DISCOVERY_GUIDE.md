<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Feature Discovery Guide

Quick Reference for Repository Reporting System Feature Discovery

---

## Overview

The Repository Reporting System includes comprehensive feature discovery tools to help you understand what features can be detected in your repositories and how to configure them.

---

## Quick Start

### List All Features

```bash
reporting-tool list-features
```text

Shows all 24 available features organized by 7 categories:

- Build & Package
- CI/CD
- Code Quality
- Documentation
- Repository
- Security
- Testing

### Show Detailed Feature Information

```bash
reporting-tool list-features --detail <feature-name>
```

Displays:

- Feature description
- Category
- Detection method
- Configuration file location
- Configuration example
- Related features

---

## Available Features

### Build & Package (5 features)

| Feature | Description |
|---------|-------------|
| `docker` | Docker containerization |
| `gradle` | Gradle build configuration |
| `maven` | Maven build configuration |
| `npm` | NPM package configuration |
| `sonatype` | Sonatype/Maven Central publishing |

### CI/CD (4 features)

| Feature | Description |
|---------|-------------|
| `dependabot` | Dependabot configuration detection |
| `github-actions` | GitHub Actions workflows |
| `github2gerrit` | GitHub to Gerrit workflow synchronization |
| `jenkins` | Jenkins CI/CD jobs |

### Code Quality (3 features)

| Feature | Description |
|---------|-------------|
| `linting` | Code linting configuration (pylint, flake8, etc.) |
| `pre-commit` | Pre-commit hooks configuration |
| `sonarqube` | SonarQube analysis configuration |

### Documentation (3 features)

| Feature | Description |
|---------|-------------|
| `mkdocs` | MkDocs documentation |
| `readthedocs` | ReadTheDocs integration |
| `sphinx` | Sphinx documentation |

### Repository (4 features)

| Feature | Description |
|---------|-------------|
| `github-mirror` | GitHub mirror repository detection |
| `gitreview` | Gerrit git-review configuration |
| `license` | License file detection |
| `readme` | README file quality check |

### Security (2 features)

| Feature | Description |
|---------|-------------|
| `secrets-detection` | Secrets and credentials detection |
| `security-scanning` | Security vulnerability scanning |

### Testing (3 features)

| Feature | Description |
|---------|-------------|
| `coverage` | Code coverage reporting |
| `junit` | JUnit testing framework |
| `pytest` | PyTest testing framework |

---

## Usage Examples

### Example 1: Explore All Features

```bash
# Basic list
reporting-tool list-features

# With configuration file info
reporting-tool list-features --verbose
```text

Output:

```

Available Feature Checks:

📁 Build & Package:
  • docker                   - Docker containerization
    Config: Dockerfile
  • gradle                   - Gradle build configuration
    Config: build.gradle or build.gradle.kts
  ...

Total: 24 features across 7 categories

💡 Use --show-feature <name> to see detailed information about a specific feature

```text

### Example 2: Learn About Dependabot

```bash
reporting-tool list-features --detail dependabot
```

Output:

```text
======================================================================
Feature: dependabot
======================================================================

📁 Category: CI/CD
📝 Description: Dependabot configuration detection

🔍 Detection Method:
  Checks for .github/dependabot.yml or .github/dependabot.yaml

📄 Configuration File(s):
  .github/dependabot.yml

📋 Configuration Example:

  version: 2
  updates:
    - package-ecosystem: "pip"
      directory: "/"
      schedule:
        interval: "weekly"

🔗 Related Features in CI/CD:
  • github-actions           - GitHub Actions workflows
  • github2gerrit            - GitHub to Gerrit workflow synchronization
  • jenkins                  - Jenkins CI/CD jobs

💡 Tip: Use --list-features to see all available features
```

### Example 3: Learn About Docker Feature

```bash
reporting-tool list-features --detail docker
```text

Output:

```

======================================================================
Feature: docker
======================================================================

📁 Category: Build & Package
📝 Description: Docker containerization

🔍 Detection Method:
  Checks for Dockerfile or docker-compose.yml

📄 Configuration File(s):
  Dockerfile

📋 Configuration Example:

  FROM python:3.10-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN uv sync  # Recommended

# or: pip install

  COPY . .
  CMD ["python", "app.py"]

🔗 Related Features in Build & Package:
  • gradle                   - Gradle build configuration
  • maven                    - Maven build configuration
  • npm                      - NPM package configuration
  • sonatype                 - Sonatype/Maven Central publishing

💡 Tip: Use --list-features to see all available features

```text

### Example 4: Check Unknown Feature

```bash
reporting-tool list-features --detail unknown-feature
```

Output:

```text
❌ Unknown feature: unknown-feature

Use --list-features to see all available features.
```

---

## Feature Categories

### Understanding Categories

Features are organized into 7 categories for easy navigation:

1. **Build & Package** - Build systems and package management
2. **CI/CD** - Continuous integration and deployment
3. **Code Quality** - Linting, formatting, and code analysis
4. **Documentation** - Documentation generation and hosting
5. **Repository** - Repository configuration and metadata
6. **Security** - Security scanning and secrets detection
7. **Testing** - Testing frameworks and coverage

---

## Detection Methods

Each feature has a specific detection method:

### File-Based Detection

Most features are detected by the presence of specific files:

- `dependabot` → `.github/dependabot.yml`
- `docker` → `Dockerfile`
- `maven` → `pom.xml`
- `pytest` → `pytest.ini` or `pyproject.toml`

### Content-Based Detection

Some features analyze file contents:

- `linting` → Checks for linting config in multiple files
- `sonatype` → Analyzes `pom.xml` for publishing configuration
- `readme` → Evaluates README quality

### Pattern-Based Detection

Some features use pattern matching:

- `github-mirror` → Checks repository description and topics
- `security-scanning` → Looks for security tools in CI/CD configs

---

## Configuration Examples

Each feature includes a real-world configuration example that you can use as a template.

### Python Project Example

```bash
# Check what features would help
reporting-tool list-features --detail pytest
reporting-tool list-features --detail pre-commit
reporting-tool list-features --detail coverage
```text

### Java Project Example

```bash
# Learn about Java features
reporting-tool list-features --detail maven
reporting-tool list-features --detail junit
reporting-tool list-features --detail sonarqube
```

### JavaScript Project Example

```bash
# Explore JS/Node features
reporting-tool list-features --detail npm
reporting-tool list-features --detail github-actions
```text

---

## Tips & Best Practices

### 1. Explore Before Analyzing

Run `--list-features` before your first analysis to understand what will be checked.

### 2. Use Verbose Mode

Add `--verbose` to see configuration file locations for each feature.

### 3. Check Related Features

When viewing a feature with `--show-feature`, check the "Related Features" section to discover complementary features.

### 4. Copy Configuration Examples

Use the configuration examples as starting points for your own projects.

### 5. No Analysis Required

Feature discovery commands work without `--project` or `--repos-path`:

```bash
# These work without full setup
reporting-tool list-features
reporting-tool list-features --detail docker
```

---

## Integration with Analysis

### View Features in Reports

When you run a full analysis, the JSON report includes detected features:

```json
{
  "features": {
    "dependabot": true,
    "github-actions": true,
    "docker": false,
    "pytest": true
  }
}
```text

### Feature-Based Filtering

Use feature information to plan your repository improvements:

1. Check what's missing: `--list-features`
2. Learn how to add it: `--show-feature <name>`
3. Implement the feature using the config example
4. Re-run analysis to verify detection

---

## Programmatic Access

### From Python Code

```python
from src.cli.features import (
    get_feature_info,
    list_all_features,
    show_feature_details,
    search_features,
    get_features_by_category
)

# Get feature information
info = get_feature_info('dependabot')
print(f"Category: {info.category}")
print(f"Config: {info.config_file}")

# List all features
output = list_all_features(verbose=True)
print(output)

# Show detailed info
details = show_feature_details('docker')
print(details)

# Search features
results = search_features('github')
for name, desc, category in results:
    print(f"{name}: {desc}")

# Get by category
ci_cd_features = get_features_by_category()['CI/CD']
```

---

## Troubleshooting

### Q: Feature not showing in list?

A: Only 24 core features are tracked. If you need a new feature, file an issue.

### Q: Configuration example doesn't work?

A: Examples are templates - adjust for your specific project needs.

### Q: Feature detected incorrectly?

A: Check the detection method with `--show-feature` to understand what files are checked.

### Q: Want to add a custom feature?

A: Edit `src/cli/features.py` and add to `AVAILABLE_FEATURES` registry.

---

## Advanced Usage

### Custom Feature Registry

You can extend the feature registry in your own code:

```python
from src.cli.features import AVAILABLE_FEATURES

# Add custom feature
AVAILABLE_FEATURES['my-custom-feature'] = (
    'My custom feature description',
    'Custom Category',
    'config/my-feature.yml',
    'example: config',
    'Checks for config/my-feature.yml'
)
```text

### Filtering Features

```python
from src.cli.features import get_features_in_category, search_features

# Get all CI/CD features
ci_cd = get_features_in_category('CI/CD')

# Search for GitHub-related features
github_features = search_features('github')
```

---

## See Also

- **CLI Guide:** `docs/CLI_GUIDE.md`
- **Feature Implementation:** `src/cli/features.py`
- **Feature Tests:** `tests/test_cli/test_features.py`
- **Phase 13 Summary:** `PHASE_13_STEP_3_COMPLETE.md`

---

**Last Updated:** December 2024
**Version:** Phase 13 - Enhanced Feature Discovery
**Status:** ✅ Complete
