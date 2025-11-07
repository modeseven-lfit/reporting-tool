# Developer Quick Reference Guide

**Reporting Tool - Refactored Architecture**
**Version:** 2.0 (Post-Refactoring)
**Last Updated:** 2025-01-24

---

## 🚀 Quick Start

### Running the Tool

```bash
# Basic usage
reporting-tool generate --project myproject --repos-path ./repos

# With options
reporting-tool generate \
  --project myproject \
  --repos-path ./repos \
  --output-dir ./reports \
  --config-dir ./config \
  --verbose
```

### Programmatic Usage

```python
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

# Import components
from reporting_tool.reporter import RepositoryReporter
import logging

# Setup
config = {...}  # Your configuration
logger = logging.getLogger(__name__)

# Run analysis
reporter = RepositoryReporter(config, logger)
report_data = reporter.analyze_repositories(Path('./repos'))
```

---

## 📦 Module Structure

### Core Modules

| Module | Purpose | Lines | Phase |
|--------|---------|-------|-------|
| `generate_reports.py` | Entry point, CLI, config | 1,861 | Main |
| `reporter.py` | Main orchestration | 522 | Phase 7 |
| `collectors/git.py` | Git data collection | 1,155 | Phase 4 |
| `renderers/report.py` | Output generation | 1,724 | Phase 6 |
| `features/registry.py` | Feature detection | 550 | Phase 3 |
| `aggregators/data.py` | Data aggregation | 454 | Phase 5 |
| `api/github_client.py` | GitHub API | ~330 | Phase 2 |
| `api/gerrit_client.py` | Gerrit API | ~150 | Phase 2 |
| `api/jenkins_client.py` | Jenkins API | ~420 | Phase 2 |

### Directory Layout

```
reporting-tool/
├── generate_reports.py          # Main entry point
├── configuration/               # Config files
│   ├── template.config
│   └── project.config
└── src/
    ├── api/                     # External API clients
    │   ├── github_client.py
    │   ├── gerrit_client.py
    │   └── jenkins_client.py
    ├── reporting_tool/          # Core system
    │   ├── reporter.py          # ⭐ Main orchestrator
    │   ├── config.py
    │   ├── collectors/
    │   │   └── git.py
    │   ├── aggregators/
    │   │   └── data.py
    │   ├── renderers/
    │   │   └── report.py
    │   └── features/
    │       └── registry.py
    └── util/                    # Utilities
        ├── formatting.py
        ├── github_org.py
        ├── zip_bundle.py
        └── git.py
```

---

## 🔧 Common Tasks

### Adding a New Feature Detector

1. **Edit:** `src/reporting_tool/features/registry.py`
2. **Add method:** `def _detect_my_feature(self, repo_path: Path) -> bool:`
3. **Register in:** `self.feature_detectors` dict in `__init__`
4. **Test:** Verify detection logic works

```python
def _detect_my_feature(self, repo_path: Path) -> bool:
    """Detect if repository has my feature."""
    feature_file = repo_path / "my-feature.yml"
    return feature_file.exists()

# In __init__:
self.feature_detectors = {
    # ... existing detectors ...
    "my_feature": self._detect_my_feature,
}
```

### Adding a New Aggregation

1. **Edit:** `src/reporting_tool/aggregators/data.py`
2. **Add method:** `def compute_my_rollup(self, data: list) -> dict:`
3. **Call from:** `aggregate_global_data()` or create new public method

```python
def compute_my_rollup(self, repos: list[dict]) -> dict:
    """Compute custom rollup statistics."""
    result = {}
    # Your aggregation logic
    return result
```

### Adding a New Output Format

1. **Edit:** `src/reporting_tool/renderers/report.py`
2. **Add method:** `def render_my_format(self, data: dict, path: Path) -> None:`
3. **Call from:** `RepositoryReporter.generate_reports()`

```python
def render_my_format(self, data: dict, output_path: Path) -> None:
    """Render report in my custom format."""
    # Your rendering logic
    output_path.write_text(result)
```

### Adding a New API Client

1. **Create:** `src/api/my_service_client.py`
2. **Implement:** Client class with `__init__`, methods, error handling
3. **Import in:** `generate_reports.py` and use in collectors

```python
class MyServiceAPIClient:
    """Client for My Service API."""

    def __init__(self, host: str, timeout: float = 30.0):
        self.host = host
        self.timeout = timeout
        # Setup client

    def get_data(self, resource: str) -> dict:
        """Fetch data from API."""
        # Implementation
        pass
```

---

## 🧪 Testing

### Import Testing

```bash
# Test individual module imports
python3 -c "import sys; sys.path.insert(0, 'src'); \
  from reporting_tool.reporter import RepositoryReporter; \
  print('✅ Import successful')"
```

### Diagnostics

```bash
# Run diagnostics (if available)
python3 -m pylint src/reporting_tool/
python3 -m mypy src/reporting_tool/
```

### Functional Testing

```bash
# Validate configuration
reporting-tool generate --project test --repos-path ./test-repos --validate-only

# Test with small dataset
reporting-tool generate --project test --repos-path ./test-repos --verbose
```

---

## 📊 Data Flow

### Analysis Pipeline

```
1. CLI/Main Entry
   ↓
2. Configuration Loading
   ↓
3. RepositoryReporter.analyze_repositories()
   ├── Clone info-master (optional)
   ├── Discover repositories
   ├── Parallel analysis
   │   ├── GitDataCollector (per repo)
   │   └── FeatureRegistry (per repo)
   ├── DataAggregator
   └── Jenkins allocation summary
   ↓
4. RepositoryReporter.generate_reports()
   ├── ReportRenderer.render_json_report()
   ├── ReportRenderer.render_markdown_report()
   ├── ReportRenderer.render_html_report()
   └── create_report_bundle() (ZIP)
   ↓
5. Output files in reports/ directory
```

### Key Data Structures

```python
# Report data structure
report_data = {
    "schema_version": "1.0.0",
    "generated_at": "2025-01-24T12:00:00Z",
    "project": "myproject",
    "config_digest": "abc123...",
    "script_version": "1.0.0",
    "time_windows": {...},
    "repositories": [...],    # List of repo metrics
    "authors": [...],         # Author rollups
    "organizations": [...],   # Org rollups
    "summaries": {...},       # Global summaries
    "errors": [...]           # Error records
}

# Repository record
repository = {
    "name": "repo-name",
    "path": "relative/path",
    "git_metrics": {...},
    "features": {...},
    "gerrit_info": {...},
    "jenkins_jobs": [...],
    "github_workflows": [...],
    "authors": [...]          # Author contributions
}
```

---

## 🔍 Common Import Patterns

### Main Components

```python
# Full orchestration
from reporting_tool.reporter import RepositoryReporter

# Data collection
from reporting_tool.collectors import GitDataCollector

# Feature detection
from reporting_tool.features import FeatureRegistry

# Aggregation
from reporting_tool.aggregators import DataAggregator

# Rendering
from reporting_tool.renderers import ReportRenderer

# Configuration
from reporting_tool.config import (
    load_configuration,
    save_resolved_config,
    compute_config_digest
)
```

### API Clients

```python
from api.github_client import GitHubAPIClient
from api.gerrit_client import GerritAPIClient, GerritAPIDiscovery
from api.jenkins_client import JenkinsAPIClient
```

### Utilities

```python
from util.formatting import format_number, format_age, UNKNOWN_AGE
from util.github_org import determine_github_org
from util.zip_bundle import create_report_bundle
from util.git import safe_git_command
```

---

## ⚙️ Configuration

### Configuration File Structure

```yaml
# configuration/template.config
project: "default"
schema_version: "1.0.0"

activity_thresholds:
  current_days: 90
  active_days: 365

time_windows:
  last_30_days: 30
  last_90_days: 90
  last_365_days: 365

features:
  enabled:
    - ci_cd
    - documentation
    - testing

extensions:
  github_api:
    enabled: true
  gerrit_api:
    enabled: true
  jenkins_api:
    enabled: true

performance:
  max_workers: 8
```

### Environment Variables

```bash
# GitHub API token
export CLASSIC_READ_ONLY_PAT_TOKEN="ghp_..."

# GitHub organization (from PROJECTS_JSON)
export GITHUB_ORG="myorg"

# GitHub Actions step summary
export GITHUB_STEP_SUMMARY="/path/to/summary.md"
```

---

## 🐛 Debugging

### Enable Verbose Logging

```bash
reporting-tool generate --project test --repos-path ./repos --verbose
# or
reporting-tool generate --project test --repos-path ./repos --log-level DEBUG
```

### Check API Statistics

```python
from generate_reports import api_stats

# After running analysis
print(api_stats.format_console_output())
```

### Inspect Report Data

```python
import json

# Load generated report
with open('reports/myproject/report_raw.json') as f:
    data = json.load(f)

# Inspect structure
print(f"Repositories: {len(data['repositories'])}")
print(f"Authors: {len(data['authors'])}")
print(f"Errors: {len(data['errors'])}")
```

---

## 🎯 Best Practices

### Code Style

- **PEP 8** compliance
- **Type hints** for function signatures
- **Docstrings** for all public methods
- **Error handling** with try/except
- **Logging** instead of print statements

### Module Design

- **Single responsibility** per module
- **Clear interfaces** between components
- **Dependency injection** for testability
- **Minimal coupling** between modules
- **No circular dependencies**

### Testing Approach

- **Unit tests** for individual functions
- **Integration tests** for workflows
- **Mock external APIs** in tests
- **Test edge cases** and errors
- **Maintain test coverage** >80%

---

## 📚 Key Classes

### RepositoryReporter

**Purpose:** Main orchestration
**Location:** `src/reporting_tool/reporter.py`

```python
reporter = RepositoryReporter(config, logger)
report_data = reporter.analyze_repositories(repos_path)
files = reporter.generate_reports(repos_path, output_dir)
```

### GitDataCollector

**Purpose:** Git metrics collection
**Location:** `src/reporting_tool/collectors/git.py`

```python
collector = GitDataCollector(config, time_windows, logger)
metrics = collector.collect_repo_git_metrics(repo_path)
```

### FeatureRegistry

**Purpose:** Feature detection
**Location:** `src/reporting_tool/features/registry.py`

```python
registry = FeatureRegistry(config, logger)
features = registry.detect_features(repo_path)
```

### DataAggregator

**Purpose:** Data aggregation
**Location:** `src/reporting_tool/aggregators/data.py`

```python
aggregator = DataAggregator(config, logger)
authors = aggregator.compute_author_rollups(repos)
orgs = aggregator.compute_org_rollups(authors)
summaries = aggregator.aggregate_global_data(repos)
```

### ReportRenderer

**Purpose:** Report generation
**Location:** `src/reporting_tool/renderers/report.py`

```python
renderer = ReportRenderer(config, logger)
renderer.render_json_report(data, json_path)
renderer.render_markdown_report(data, md_path)
renderer.render_html_report(markdown, html_path)
```

---

## 🔗 External Resources

- **Repository:** [Link to repository]
- **Documentation:** `docs/` directory
- **Issue Tracker:** [Link to issues]
- **Contributing:** `CONTRIBUTING.md`
- **License:** Apache 2.0

---

## 💡 Tips & Tricks

### Performance Optimization

```python
# Adjust parallel workers
config["performance"]["max_workers"] = 4  # or 1 for sequential

# Disable HTML generation
reporting-tool generate ... --no-html

# Disable ZIP bundling
reporting-tool generate ... --no-zip
```

### Custom Time Windows

```yaml
# configuration/project.config
time_windows:
  last_7_days: 7
  last_14_days: 14
  last_30_days: 30
  last_quarter: 90
  last_year: 365
```

### Debugging Git Issues

```python
from util.git import safe_git_command
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
success, output = safe_git_command(
    ["git", "log", "--oneline", "-5"],
    Path("./repo"),
    logger
)
print(f"Success: {success}")
print(f"Output: {output}")
```

---

**Questions?** Check the docs or open an issue!

*Last Updated: 2025-01-24*
