# INFO.yaml Committer Reporting

This document describes the INFO.yaml committer reporting feature, which collects project metadata from the LF info-master repository and generates comprehensive reports showing project lifecycle state, leads, and committer activity status.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Configuration](#configuration)
- [Data Collection](#data-collection)
- [Report Output](#report-output)
- [Activity Status Coloring](#activity-status-coloring)
- [Integration with Git Metrics](#integration-with-git-metrics)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Overview

The INFO.yaml reporting feature provides visibility into project organization and committer activity by:

1. **Collecting** INFO.yaml files from the LF info-master repository
2. **Parsing** project metadata including leads, committers, lifecycle state
3. **Enriching** committer data with Git activity information
4. **Validating** issue tracker URLs for each project
5. **Rendering** comprehensive reports with activity color-coding

This feature helps organizations track:
- Active vs. inactive projects
- Committer activity patterns
- Project lifecycle distribution
- Issue tracker health
- Organizational structure

## Features

### Core Features

- ✅ **Automatic Collection**: Clones and parses all INFO.yaml files from info-master
- ✅ **Git Enrichment**: Cross-references committers with Git commit activity
- ✅ **Activity Coloring**: Visual indicators for committer activity status
- ✅ **URL Validation**: Checks issue tracker URLs for accessibility
- ✅ **Lifecycle Analysis**: Summarizes projects by lifecycle state
- ✅ **Server Filtering**: Filter by specific Gerrit server
- ✅ **Archived Filtering**: Optionally exclude archived projects
- ✅ **Performance Optimized**: Caching and parallel processing

### Report Sections

The INFO.yaml report includes two main sections:

1. **Committer Report Table**: Shows all projects with:
   - Project name (linked to issue tracker)
   - Creation date
   - Lifecycle state (Active, Incubation, Archived, etc.)
   - Project lead (with activity color)
   - Committers (with activity colors)

2. **Lifecycle Summary**: Statistics showing:
   - Count of projects per lifecycle state
   - Percentage distribution
   - Total project count

## Configuration

### Basic Configuration

Enable INFO.yaml collection in your configuration file:

```yaml
info_yaml:
  # Enable INFO.yaml committer report generation
  enabled: true
  
  # Clone URL for info-master repository
  clone_url: "https://gerrit.linuxfoundation.org/infra/releng/info-master"
  
  # Exclude archived projects from report
  disable_archived_reports: true
```

### Advanced Configuration

```yaml
info_yaml:
  enabled: true
  
  # Activity window thresholds (in days)
  activity_windows:
    current: 365   # Green - commits within last year
    active: 1095   # Orange - commits within last 3 years
    # Anything beyond 'active' is marked as inactive (red)
  
  # URL validation settings
  validate_urls: true        # Validate issue tracker URLs
  url_timeout: 10.0          # Timeout for URL checks (seconds)
  url_retries: 2             # Number of retry attempts
  
  # Filtering options
  disable_archived_reports: true        # Exclude archived projects
  filter_by_gerrit_server: null         # Override auto-detected server (optional)
  
  # Caching (improves performance on repeated runs)
  cache_parsed_data: true
  cache_ttl: 3600           # Cache lifetime in seconds
```

**Note**: The reporting tool automatically detects the Gerrit server from the 
`repos_path` directory name (e.g., `gerrit.onap.org`, `git.opendaylight.org`) 
and filters INFO.yaml data to only include projects from that server. This 
prevents cross-project contamination when generating reports for specific 
organizations.

### Local Development Configuration

For local development/testing, you can point to a local info-master clone:

```yaml
info_yaml:
  enabled: true
  
  # Use local path instead of cloning
  local_path: "testing/info-master"
  
  # Disable URL validation for faster testing
  validate_urls: false
```

### Report Section Control

Control whether the INFO.yaml section appears in reports:

```yaml
output:
  include_sections:
    info_yaml: true  # Set to false to exclude from reports
```

## Data Collection

### Collection Process

1. **Repository Access**: The info-master repository is cloned or accessed locally
2. **Server Detection**: Gerrit server is auto-detected from the repos_path directory name
3. **File Discovery**: INFO.yaml files are discovered for the detected server only
4. **Parsing**: Each file is parsed to extract project metadata
5. **Validation**: Issue tracker URLs are validated (if enabled)
6. **Enrichment**: Git metrics are used to determine committer activity
7. **Filtering**: Projects are further filtered based on configuration (e.g., exclude archived)

### INFO.yaml Structure

The collector extracts the following fields from each INFO.yaml file:

```yaml
project: 'Project Name'
project_creation_date: '2020-01-15'
lifecycle_state: 'Active'  # or Incubation, Archived, etc.

project_lead:
  name: 'Jane Doe'
  email: 'jane.doe@example.com'
  id: 'jdoe'
  company: 'Example Corp'
  timezone: 'America/Los_Angeles'

committers:
  - name: 'John Smith'
    email: 'john.smith@example.com'
    id: 'jsmith'
    company: 'Tech Inc'
  - name: 'Alice Johnson'
    email: 'alice.johnson@example.com'
    id: 'ajohnson'
    company: 'Dev Corp'

repositories:
  - project/repo1
  - project/repo2

issue_tracking:
  type: 'jira'
  url: 'https://jira.example.org/projects/PROJECT'
```

### Directory Structure

The info-master repository is organized by Gerrit server:

```
info-master/
├── gerrit.onap.org/          <- ONAP projects
│   ├── .github/
│   │   └── INFO.yaml
│   ├── aai/
│   │   └── INFO.yaml
│   ├── appc/
│   │   └── INFO.yaml
│   └── ...
├── git.opendaylight.org/     <- OpenDaylight projects
│   ├── .github/
│   │   └── INFO.yaml
│   ├── aaa/
│   │   └── INFO.yaml
│   └── ...
├── gerrit.o-ran-sc.org/      <- O-RAN-SC projects
│   ├── .github/
│   │   └── INFO.yaml
│   ├── ric-plt/
│   │   └── INFO.yaml
│   └── ...
└── ...
```

**Important**: Each Gerrit server has its own subdirectory in info-master. The 
reporting tool automatically filters to the relevant server based on the 
`repos_path` directory name to prevent cross-contamination. For example, when 
analyzing `gerrit.onap.org` repositories, only INFO.yaml files from the 
`gerrit.onap.org/` subdirectory are included.

## Report Output

### Example Output

#### Committer Report Table

```markdown
## 📋 Committer INFO.yaml Report

This report shows project information from INFO.yaml files, including lifecycle state, 
project leads, and committer activity status.

| Project | Creation Date | Lifecycle State | Project Lead | Committers |
|---------|---------------|-----------------|--------------|------------|
| [project-a](https://jira.example.org/projects/A) | 2020-01-15 | Active | <span style="color: green;" title="✅ Current - commits within last 365 days">Jane Doe</span> | <span style="color: green;" title="✅ Current - commits within last 365 days">John Smith</span><br><span style="color: green;" title="✅ Current - commits within last 365 days">Alice Johnson</span> |
| [project-b](https://jira.example.org/projects/B) | 2022-06-01 | Incubation | <span style="color: orange;" title="☑️ Active - commits between 365-1095 days">Bob Williams</span> | <span style="color: orange;" title="☑️ Active - commits between 365-1095 days">Carol Davis</span> |
| project-c | 2018-03-20 | Archived | <span style="color: red;" title="🛑 Inactive - no commits in 1095+ days">Frank Miller</span> | <span style="color: red;" title="🛑 Inactive - no commits in 1095+ days">Grace Lee</span> |
```

#### Lifecycle Summary

```markdown
### Lifecycle State Summary

| Lifecycle State | Gerrit Project Count | Percentage |
|----------------|---------------------|------------|
| Active | 125 | 62.5% |
| Incubation | 60 | 30.0% |
| Archived | 15 | 7.5% |

**Total Projects:** 200
```

## Activity Status Coloring

### Color Scheme

Committers and project leads are color-coded based on their most recent commit activity:

| Color | Status | Criteria | Tooltip |
|-------|--------|----------|---------|
| 🟢 Green | **Current** | Commits within last 365 days | ✅ Current - commits within last 365 days |
| 🟠 Orange | **Active** | Commits between 365-1095 days | ☑️ Active - commits between 365-1095 days |
| 🔴 Red | **Inactive** | No commits in 1095+ days | 🛑 Inactive - no commits in 1095+ days |
| ⚫ Gray | **Unknown** | No Git data available | Unknown activity status |

### Activity Determination

Activity status is determined at the **project level**, not per-committer:

1. All repositories for a project are analyzed
2. The most recent commit across all repos determines project activity
3. All committers for that project receive the same color
4. This approach reflects overall project health

Example:
- Project has 3 repos: last commits at 30, 45, and 200 days ago
- Project activity = 30 days (most recent)
- All committers colored **green** (current)

## Integration with Git Metrics

### Enrichment Process

When Git metrics are available, the INFO.yaml collector enriches committer data:

1. **Match Projects**: Projects are matched to repositories by name
2. **Extract Activity**: Days since last commit is extracted for each repository
3. **Determine Status**: Activity windows are applied to determine color
4. **Update Committers**: All committers get activity status and color

### Example Integration

```python
from reporting_tool.collectors import GitDataCollector, INFOYamlCollector

# Collect Git metrics
git_collector = GitDataCollector(config, time_windows, logger)
git_metrics = git_collector.collect_all_repositories(repos_path)

# Collect and enrich INFO.yaml data
info_collector = INFOYamlCollector(config)
info_data = info_collector.collect(
    info_master_path,
    git_metrics=git_metrics,  # Enrichment data
)

# Projects now have activity status
for project in info_data['projects']:
    print(f"{project['project_name']}: {project['has_git_data']}")
    for committer in project['committers']:
        print(f"  - {committer['name']}: {committer['activity_color']}")
```

### Without Git Enrichment

If Git metrics are not provided, all committers are marked as "unknown" (gray):

```python
# Collect without enrichment
info_data = info_collector.collect(info_master_path)

# All committers will have activity_status='unknown' and activity_color='gray'
```

## Usage Examples

### Basic Usage

```python
from pathlib import Path
from reporting_tool.collectors.info_yaml import INFOYamlCollector

# Configure collector
config = {
    "info_yaml": {
        "enabled": True,
        "validate_urls": False,  # Faster for testing
    }
}

# Create collector
collector = INFOYamlCollector(config)

# Collect data
info_master_path = Path("testing/info-master")
result = collector.collect(info_master_path)

# Access data
print(f"Total projects: {result['total_projects']}")
print(f"Servers: {', '.join(result['servers'])}")

for project in result['projects']:
    print(f"- {project['project_name']} ({project['lifecycle_state']})")
```

### With Git Enrichment

```python
from reporting_tool.collectors import GitDataCollector, INFOYamlCollector

# Collect Git metrics first
git_collector = GitDataCollector(config, time_windows, logger)
repos_path = Path("repositories")
git_metrics = []

for repo_dir in repos_path.iterdir():
    if repo_dir.is_dir():
        metrics = git_collector.collect(repo_dir)
        git_metrics.append(metrics)

# Enrich INFO.yaml with Git data
info_collector = INFOYamlCollector(config)
result = info_collector.collect(
    info_master_path,
    git_metrics=git_metrics,
)

# Check enrichment statistics
stats = info_collector.get_enrichment_statistics()
print(f"Projects with Git data: {stats['with_git_data']}")
print(f"Projects without Git data: {stats['without_git_data']}")
```

### Filter by Gerrit Server

```python
# Explicitly filter to a specific server (overrides auto-detection)
result = collector.collect_for_server(
    info_master_path,
    gerrit_server="gerrit.onap.org",
)

print(f"Projects on gerrit.onap.org: {result['total_projects']}")

# Or use the collect() method with gerrit_server parameter
result = collector.collect(
    info_master_path,
    gerrit_server="gerrit.onap.org",  # Filters to this server only
    git_metrics=git_metrics,
)
```

### Custom Activity Windows

```python
config = {
    "info_yaml": {
        "enabled": True,
        "activity_windows": {
            "current": 180,   # 6 months = current (green)
            "active": 730,    # 2 years = active (orange)
            # Beyond 2 years = inactive (red)
        }
    }
}

collector = INFOYamlCollector(config)
result = collector.collect(info_master_path, git_metrics=git_metrics)
```

### Rendering Reports

```python
from domain.info_yaml import ProjectInfo
from rendering.info_yaml_renderer import InfoYamlRenderer

# Convert to domain objects
projects = [ProjectInfo.from_dict(p) for p in result['projects']]

# Create renderer
renderer = InfoYamlRenderer(logger)

# Generate Markdown
committer_report = renderer.render_committer_report_markdown(projects)
lifecycle_summary = renderer.render_lifecycle_summary_markdown(projects)

# Or generate complete report
full_report = renderer.render_full_report_markdown(projects)

# Write to file
output_path = Path("reports/info-yaml-report.md")
output_path.write_text(full_report)
```

## Troubleshooting

### Common Issues

#### 1. No Projects Collected

**Symptom**: `total_projects: 0`

**Possible Causes**:
- info-master repository not cloned
- Incorrect path to info-master
- Wrong Gerrit server detected (check repos_path directory name)
- All projects filtered out (check `disable_archived_reports`)

**Solutions**:
```python
# Verify path
print(f"INFO master path: {collector.info_master_path}")
print(f"Path exists: {collector.info_master_path.exists()}")

# Check detected Gerrit server
from pathlib import Path
repos_path = Path("./gerrit.onap.org")
server = repos_path.name
print(f"Detected server: {server}")

# Check for INFO.yaml files in the server-specific subdirectory
server_path = collector.info_master_path / server
if server_path.exists():
    yaml_files = list(server_path.rglob("INFO.yaml"))
    print(f"Found {len(yaml_files)} INFO.yaml files for {server}")
else:
    print(f"Server path does not exist: {server_path}")

# Disable filters temporarily
config["info_yaml"]["disable_archived_reports"] = False
```

#### 2. No Git Enrichment

**Symptom**: All committers are gray (unknown status)

**Possible Causes**:
- Git metrics not provided to `collect()`
- Project names don't match repository names
- No matching repositories found

**Solutions**:
```python
# Check if Git metrics were provided
result = collector.collect(info_master_path, git_metrics=git_metrics)
stats = collector.get_enrichment_statistics()
print(f"Matched: {stats.get('with_git_data', 0)}")
print(f"Unmatched: {stats.get('without_git_data', 0)}")

# Verify project-to-repo matching
for project in result['projects']:
    print(f"{project['project_name']}: {project['has_git_data']}")
    print(f"  Repos: {project['repositories']}")
```

#### 3. URL Validation Failures

**Symptom**: Projects showing red with broken link indicators

**Possible Causes**:
- Issue tracker URLs are actually broken
- Network connectivity issues
- Timeout too short
- SSL certificate issues

**Solutions**:
```python
# Increase timeout
config["info_yaml"]["url_timeout"] = 30.0
config["info_yaml"]["url_retries"] = 5

# Disable validation for testing
config["info_yaml"]["validate_urls"] = False

# Check URL cache statistics
cache_stats = collector.get_url_cache_stats()
print(f"URLs cached: {cache_stats}")

# Clear cache if needed
collector.clear_url_cache()
```

#### 4. Performance Issues

**Symptom**: Collection takes a long time

**Solutions**:
```python
# Enable caching
config["info_yaml"]["cache_parsed_data"] = True
config["info_yaml"]["cache_ttl"] = 3600

# Disable URL validation (can be slow)
config["info_yaml"]["validate_urls"] = False

# Filter to specific server
result = collector.collect_for_server(
    info_master_path,
    gerrit_server="gerrit.example.org"
)
```

### Debugging Tips

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("reporting_tool.collectors.info_yaml")
logger.setLevel(logging.DEBUG)
```

Check collector state:

```python
# After collection
print(f"Projects collected: {len(collector.projects)}")
print(f"Enricher: {collector.enricher is not None}")
print(f"Parser: {collector.parser is not None}")

# Check individual project
project = collector.get_project_by_path("project-a")
if project:
    print(f"Project: {project.project_name}")
    print(f"Has Git data: {project.has_git_data}")
    print(f"Committers: {project.committer_count}")
```

## API Reference

### INFOYamlCollector

Main collector class for INFO.yaml data.

```python
class INFOYamlCollector(BaseCollector):
    def collect(
        self,
        source: Path,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Collect INFO.yaml data from info-master.
        
        Args:
            source: Path to info-master repository
            **kwargs:
                - gerrit_server: Filter by specific server
                - include_archived: Include archived projects
                - git_metrics: Git metrics for enrichment
        
        Returns:
            {
                "projects": List of project dicts,
                "lifecycle_summary": List of lifecycle summaries,
                "total_projects": int,
                "servers": List of server names,
            }
        """
```

### InfoYamlRenderer

Renders INFO.yaml data into formatted reports.

```python
class InfoYamlRenderer:
    def render_committer_report_markdown(
        self,
        projects: List[ProjectInfo],
        group_by_server: bool = False
    ) -> str:
        """
        Render committer report as Markdown.
        
        Args:
            projects: List of ProjectInfo objects
            group_by_server: Group projects by Gerrit server
        
        Returns:
            Markdown-formatted report
        """
    
    def render_lifecycle_summary_markdown(
        self,
        projects: List[ProjectInfo]
    ) -> str:
        """
        Render lifecycle state summary.
        
        Args:
            projects: List of ProjectInfo objects
        
        Returns:
            Markdown-formatted summary table
        """
    
    def render_full_report_markdown(
        self,
        projects: List[ProjectInfo],
        group_by_server: bool = False
    ) -> str:
        """
        Render complete INFO.yaml report.
        
        Includes committer report and lifecycle summary.
        
        Args:
            projects: List of ProjectInfo objects
            group_by_server: Group projects by server
        
        Returns:
            Complete Markdown report
        """
```

### Domain Models

```python
@dataclass
class ProjectInfo:
    """Complete project information from INFO.yaml."""
    project_name: str
    gerrit_server: str
    project_path: str
    creation_date: str
    lifecycle_state: str
    project_lead: Optional[PersonInfo]
    committers: List[CommitterInfo]
    issue_tracking: IssueTracking
    repositories: List[str]
    has_git_data: bool
    project_days_since_last_commit: Optional[int]

@dataclass
class CommitterInfo:
    """Committer with activity enrichment."""
    name: str
    email: str
    company: str
    activity_status: str  # "current", "active", "inactive", "unknown"
    activity_color: str   # "green", "orange", "red", "gray"
    days_since_last_commit: Optional[int]

@dataclass
class LifecycleSummary:
    """Summary statistics by lifecycle state."""
    state: str
    count: int
    percentage: float
```

## Server Detection and Filtering

### How It Works

The reporting tool automatically detects the Gerrit server from the `repos_path` 
directory name and filters INFO.yaml data accordingly:

1. **Server Detection**: When you run with `--repos-path ./gerrit.onap.org`, 
   the tool extracts `gerrit.onap.org` as the server name

2. **info-master Filtering**: Only INFO.yaml files from the 
   `info-master/gerrit.onap.org/` subdirectory are collected

3. **Result**: The report shows only ONAP projects, not OpenDaylight or other 
   LF projects

### Example

```bash
# Analyzing ONAP repositories
reporting-tool generate --project ONAP --repos-path ./gerrit.onap.org

# INFO.yaml collection will:
# - Detect server: gerrit.onap.org
# - Collect from: info-master/gerrit.onap.org/
# - Include: Only ONAP projects (.github, aai, appc, ccsdk, etc.)
# - Exclude: OpenDaylight, O-RAN-SC, and other projects
```

### Supported Server Patterns

The tool recognizes these directory name patterns:
- `gerrit.*` (e.g., gerrit.onap.org, gerrit.o-ran-sc.org)
- `git.*` (e.g., git.opendaylight.org)

### Override Auto-Detection

If needed, you can override the auto-detected server:

```yaml
info_yaml:
  filter_by_gerrit_server: "gerrit.onap.org"  # Force specific server
```

Or programmatically:

```python
result = collector.collect(
    info_master_path,
    gerrit_server="gerrit.onap.org",  # Override
)
```

## Related Documentation

- [Configuration Guide](CONFIGURATION.md)
- [Git Collection](GIT_COLLECTION.md)
- [Report Rendering](RENDERING.md)
- [Testing Guide](../tests/README.md)

## Support

For issues or questions:
1. Check existing documentation
2. Review test cases in `tests/integration/test_info_yaml_reporting_integration.py`
3. Enable debug logging
4. Check GitHub issues
5. Contact Release Engineering team