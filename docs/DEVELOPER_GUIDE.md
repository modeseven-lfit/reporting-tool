<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Developer Quick Reference Guide

Reporting Tool - Refactored Architecture
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
```text

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

```text
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
```text

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
```text

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
```text

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
```text

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

```text

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
```text

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
```text

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
```text

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
```text

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
```text

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
```text

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
```text

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
```text

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

---

## INFO.yaml Report Type

The INFO.yaml collector generates reports on project metadata, committer activity, and lifecycle states.

### Architecture

```text
INFOYamlCollector
├── Parser (YAML parsing)
├── Enricher (Git data enrichment)
├── Matcher (Committer matching)
├── Validator (URL validation)
├── Metrics (Performance tracking)
└── Cache (Multi-level caching)
```

### Using the Collector

```python
from src.reporting_tool.collectors.info_yaml.collector import InfoYamlCollector

# Initialize
collector = InfoYamlCollector(
    source_url="https://gerrit.linuxfoundation.org/infra/info-master",
    source_branch="main",
    activity_windows={"current": 365, "active": 1095},
    validate_urls=True,
)

# Collect data
projects = collector.collect(git_metrics=git_data)

# Access results
for project in projects:
    print(f"{project.project_name}: {project.lifecycle_state}")
    for committer in project.committers:
        print(f"  - {committer.name} ({committer.activity_color})")
```

### Parser API

Parse individual INFO.yaml files:

```python
from src.reporting_tool.collectors.info_yaml.parser import InfoYamlParser

parser = InfoYamlParser()

# Parse from file
project = parser.parse_file("path/to/INFO.yaml")

# Parse from string
yaml_content = """
project: 'my-project'
lifecycle_state: 'Active'
"""
project = parser.parse_string(yaml_content)

# Access parsed data
print(project.project_name)
print(project.lifecycle_state)
print([c.name for c in project.committers])
```

### Enricher API

Enrich projects with Git activity data:

```python
from src.reporting_tool.collectors.info_yaml.enricher import InfoYamlEnricher

enricher = InfoYamlEnricher(
    activity_windows={"current": 365, "active": 1095},
    validate_urls=True,
    url_timeout=10.0,
)

# Enrich single project
enriched_project = enricher.enrich_project(project, git_metrics)

# Enrich multiple projects (with async URL validation)
enriched_projects = enricher.enrich_projects(
    projects,
    git_metrics,
    use_async_validation=True,
    max_concurrent_urls=20,
)

# Check enrichment stats
stats = enricher.get_enrichment_statistics(enriched_projects)
print(f"Projects with Git data: {stats['with_git_data']}")
print(f"Valid URLs: {stats['url_validation']['valid_urls']}")
```

### Validator API

Validate URLs (sync and async):

```python
from src.reporting_tool.collectors.info_yaml.validator import (
    URLValidator,
    validate_urls_async,
    validate_urls_sync,
)

# Synchronous validation
validator = URLValidator(timeout=10.0, retries=2, cache_enabled=True)
is_valid, error = validator.validate("https://jira.example.com")

# Async validation (10x faster)
import asyncio

urls = ["https://jira.example.com", "https://github.com/example/repo"]
results = asyncio.run(validate_urls_async(urls, max_concurrent=10))

# Smart sync/async wrapper
results = validate_urls_sync(urls, use_async=True, max_concurrent=20)
```

### Matcher API

Match committers to Git authors:

```python
from src.reporting_tool.collectors.info_yaml.matcher import CommitterMatcher

matcher = CommitterMatcher()

# Find matching author
committer_email = "john.doe@example.com"
git_authors = [
    {"email": "john.doe@example.com", "name": "John Doe"},
    {"email": "jane.smith@example.com", "name": "Jane Smith"},
]

match = matcher.find_matching_author(committer_email, git_authors)
if match:
    print(f"Matched: {match['name']}")
```

### Metrics API

Track performance metrics:

```python
from src.reporting_tool.collectors.info_yaml.metrics import MetricsCollector

collector = MetricsCollector()

# Use context manager for timing
with collector.timer("parse_yaml"):
    # ... parsing work ...
    pass

# Record metrics
collector.record_files_found(150)
collector.record_file_parsed(success=True)
collector.record_projects(total=150, with_git_data=142, without_git_data=8)

# Get results
metrics = collector.get_metrics()
print(metrics.get_summary())

# Export for monitoring
metrics_dict = metrics.to_dict()
```

### Cache API

Multi-level caching (memory + disk):

```python
from src.reporting_tool.collectors.info_yaml.cache import create_info_yaml_cache

# Create cache
cache = create_info_yaml_cache(
    cache_dir="/var/cache/reporting-tool",
    max_memory_entries=1000,
    ttl=3600,  # 1 hour
    enable_disk_cache=True,
)

# Use cache
value = cache.get("my-key")
if value is None:
    value = expensive_computation()
    cache.set("my-key", value, ttl=3600)

# Get statistics
stats = cache.get_stats()
print(f"Hit rate: {stats['memory']['hit_rate']}%")

# Clear cache
cache.clear()
```

### Data Models

Key data structures:

```python
from src.domain.info_yaml import ProjectInfo, CommitterInfo, IssueTracker

# ProjectInfo
project = ProjectInfo(
    project_name="my-project",
    project_path="gerrit.example.org/my-project",
    lifecycle_state="Active",
    creation_date="2020-01-15",
    project_lead=CommitterInfo(name="Jane Doe", email="jane@example.com"),
    committers=[...],
    repositories=["repo1", "repo2"],
    issue_tracking=IssueTracker(url="https://jira.example.com"),
    has_git_data=True,
)

# CommitterInfo
committer = CommitterInfo(
    name="John Doe",
    email="john@example.com",
    company="ACME Corp",
    activity_status="current",  # "current", "active", "inactive", "unknown"
    activity_color="green",      # "green", "orange", "red", "gray"
    days_since_last_commit=180,
)
```

### Rendering

Render INFO.yaml data to HTML/Markdown:

```python
from src.rendering.info_yaml_renderer import InfoYamlRenderer

renderer = InfoYamlRenderer()

# Render committer report
html = renderer.render_committer_report(
    projects=enriched_projects,
    format="html",  # or "markdown"
    group_by_server=True,
)

# Render lifecycle summary
summary = renderer.render_lifecycle_summary(
    projects=enriched_projects,
    format="markdown",
)
```

### Testing

Example test structure:

```python
import pytest
from src.reporting_tool.collectors.info_yaml.parser import InfoYamlParser

def test_parse_valid_yaml():
    """Test parsing a valid INFO.yaml file."""
    parser = InfoYamlParser()

    yaml_content = """
    project: 'test-project'
    lifecycle_state: 'Active'
    project_lead:
      name: 'Test Lead'
      email: 'lead@example.com'
    """

    project = parser.parse_string(yaml_content)

    assert project.project_name == "test-project"
    assert project.lifecycle_state == "Active"
    assert project.project_lead.name == "Test Lead"

@pytest.mark.asyncio
async def test_async_url_validation():
    """Test async URL validation."""
    from src.reporting_tool.collectors.info_yaml.validator import URLValidator

    validator = URLValidator()
    is_valid, error = await validator.validate_async("https://example.com")

    assert is_valid is True
    assert error == ""
```

### Configuration Schema

```python
INFO_YAML_CONFIG_SCHEMA = {
    "enabled": bool,
    "source": {
        "type": str,  # "git" or "local"
        "url": str,
        "branch": str,
        "local_path": str,
    },
    "filters": {
        "gerrit_servers": list[str],
        "exclude_archived": bool,
    },
    "activity_windows": {
        "current": int,  # days
        "active": int,   # days
    },
    "validation": {
        "enabled": bool,
        "timeout": float,
        "retries": int,
    },
    "performance": {
        "async_validation": bool,
        "max_concurrent_urls": int,
        "cache_enabled": bool,
        "cache_ttl": int,
    },
}
```

### Performance Characteristics

**Benchmarks:**

- Parsing: ~1-2ms per INFO.yaml file
- Enrichment: ~5-10ms per project
- URL validation (sync): ~100-200ms per URL
- URL validation (async): ~10-20ms per URL (with concurrency=20)
- Total (150 projects, async): ~8-10 seconds

**Memory Usage:**

- ~0.4MB per project
- ~100MB for cache (configurable)
- ~50MB base overhead

**Scaling:**

- Linear scaling up to 1000 projects
- Async validation scales with concurrency
- Cache reduces subsequent runs by 60-80%

### Extension Points

Add custom functionality:

```python
# Custom URL validator
class CustomURLValidator(URLValidator):
    def validate(self, url: str) -> Tuple[bool, str]:
        # Custom validation logic
        return super().validate(url)

# Custom enricher
class CustomEnricher(InfoYamlEnricher):
    def enrich_project(self, project, git_metrics):
        # Custom enrichment logic
        project = super().enrich_project(project, git_metrics)
        # Additional enrichment
        return project

# Custom renderer
class CustomRenderer(InfoYamlRenderer):
    def render_committer_report(self, projects, format="html"):
        # Custom rendering logic
        return custom_template.render(projects=projects)
```

---

**Related Documentation:**

- [Configuration Guide](CONFIGURATION.md) - INFO.yaml configuration
- [Usage Examples](USAGE_EXAMPLES.md) - Usage patterns
- [Testing Guide](TESTING.md) - Test suite documentation
