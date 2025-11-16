# INFO.yaml Reporting - Quick Reference

> Quick reference for the INFO.yaml committer reporting feature

## Overview

The INFO.yaml reporting feature collects project metadata from the LF info-master repository and generates reports showing:
- Project lifecycle states (Active, Incubation, Archived)
- Project leads and committers with activity status
- Issue tracker links and validation
- Lifecycle distribution statistics

**Auto-Filtering**: The tool automatically detects your Gerrit server from the `repos_path` directory name (e.g., `gerrit.onap.org`) and shows **only** projects from that server, preventing cross-project contamination.

## Enable in Configuration

```yaml
info_yaml:
  enabled: true
  disable_archived_reports: true  # Exclude archived projects
  validate_urls: true              # Check issue tracker URLs
```

## Activity Status Colors

| Color | Status | Meaning |
|-------|--------|---------|
| 🟢 Green | Current | Commits within last 365 days |
| 🟠 Orange | Active | Commits between 365-1095 days |
| 🔴 Red | Inactive | No commits in 1095+ days |
| ⚫ Gray | Unknown | No Git data available |

## Report Sections

### 1. Committer Report Table

Shows all projects with:
- Project name (linked to issue tracker if valid)
- Creation date
- Lifecycle state
- Project lead (color-coded by activity)
- Committers (color-coded by activity)

### 2. Lifecycle Summary

Statistics table showing:
- Count of projects per lifecycle state
- Percentage distribution
- Total project count

## Configuration Options

```yaml
info_yaml:
  # Basic settings
  enabled: true
  clone_url: "https://gerrit.linuxfoundation.org/infra/releng/info-master"
  
  # For local development
  local_path: "testing/info-master"  # Use local clone instead
  
  # Activity thresholds (days)
  activity_windows:
    current: 365   # Green
    active: 1095   # Orange
    # Beyond active = Red
  
  # URL validation
  validate_urls: true
  url_timeout: 10.0
  url_retries: 2
  
  # Filtering
  disable_archived_reports: true        # Exclude archived projects
  filter_by_gerrit_server: null         # Override auto-detected server (optional)
  
  # Performance
  cache_parsed_data: true
  cache_ttl: 3600
```

## Server Auto-Detection

The tool automatically filters INFO.yaml data by detecting the Gerrit server from your `repos_path`:

```bash
# Analyzing ONAP repositories
reporting-tool generate --project ONAP --repos-path ./gerrit.onap.org
# → Detects server: gerrit.onap.org
# → Shows only ONAP projects

# Analyzing OpenDaylight repositories  
reporting-tool generate --project ODL --repos-path ./git.opendaylight.org
# → Detects server: git.opendaylight.org
# → Shows only OpenDaylight projects
```

This prevents duplicate `.github` entries and other cross-project issues.

## Control Report Inclusion

```yaml
output:
  include_sections:
    info_yaml: true  # Set false to exclude from reports
```

## Example Output

```markdown
## 📋 Committer INFO.yaml Report

| Project | Creation Date | Lifecycle State | Project Lead | Committers |
|---------|---------------|-----------------|--------------|------------|
| [aai-babel](https://jira.onap.org/projects/AAI) | 2017-07-14 | Mature | William Reehil | Manisha Aggarwal<br>James Forsyth |
| [aai-graphadmin](https://jira.onap.org/projects/AAI) | 2018-01-25 | Mature | William Reehil | Manisha Aggarwal<br>James Forsyth |

### Lifecycle State Summary

| Lifecycle State | Gerrit Project Count | Percentage |
|----------------|---------------------|------------|
| Mature | 88 | 54.0% |
| Incubation | 73 | 44.8% |
| Archived | 1 | 0.6% |

**Total Projects:** 163
```

## Programmatic Usage

```python
from pathlib import Path
from reporting_tool.collectors.info_yaml import INFOYamlCollector
from rendering.info_yaml_renderer import InfoYamlRenderer
from domain.info_yaml import ProjectInfo

# Configure
config = {
    "info_yaml": {
        "enabled": True,
        "validate_urls": False,  # Faster for testing
    }
}

# Collect data
collector = INFOYamlCollector(config)
info_master = Path("testing/info-master")
result = collector.collect(info_master)

print(f"Collected {result['total_projects']} projects")
print(f"Servers: {', '.join(result['servers'])}")

# Render report
projects = [ProjectInfo.from_dict(p) for p in result['projects']]
renderer = InfoYamlRenderer()
markdown = renderer.render_full_report_markdown(projects)

# Save
Path("info-yaml-report.md").write_text(markdown)
```

## With Git Enrichment

```python
# Collect Git metrics first
git_collector = GitDataCollector(config, time_windows, logger)
git_metrics = []

for repo_dir in repos_path.iterdir():
    if repo_dir.is_dir():
        metrics = git_collector.collect(repo_dir)
        git_metrics.append(metrics)

# Enrich INFO.yaml with Git activity
result = collector.collect(
    info_master,
    git_metrics=git_metrics,  # Adds activity colors
)

# Check enrichment
stats = collector.get_enrichment_statistics()
print(f"Matched: {stats['with_git_data']}")
print(f"Unmatched: {stats['without_git_data']}")
```

## Troubleshooting

### No projects collected?
- Check info-master path exists
- Verify server auto-detection: check that `repos_path` directory name matches server in info-master
- Verify INFO.yaml files are present in the server-specific subdirectory
- Disable `disable_archived_reports` temporarily

### All committers gray?
- Provide `git_metrics` to `collect()`
- Verify project names match repository names
- Check enrichment statistics

### Slow collection?
- Disable `validate_urls`
- Enable `cache_parsed_data`
- Filter by `filter_by_gerrit_server`

### URL validation errors?
- Increase `url_timeout`
- Increase `url_retries`
- Temporarily disable with `validate_urls: false`

## Key Points

✅ **Automatic Collection**: No manual data entry required  
✅ **Server Filtering**: Auto-detects Gerrit server from repos_path to prevent cross-project contamination  
✅ **Git Integration**: Activity colors based on actual commits  
✅ **Performance Optimized**: Caching and parallel processing  
✅ **Configurable**: Customize thresholds and filtering  
✅ **Production Ready**: Comprehensive error handling and logging

## See Also

- [Complete Documentation](INFO_YAML_REPORTING.md) - Full feature documentation
- [Configuration Guide](CONFIGURATION.md) - All configuration options
- [Testing Guide](../tests/README.md) - Test examples and fixtures

## Support

Issues or questions? Check:
1. [Troubleshooting section](INFO_YAML_REPORTING.md#troubleshooting)
2. Integration tests in `tests/integration/test_info_yaml_reporting_integration.py`
3. Enable debug logging: `logging.getLogger("reporting_tool.collectors.info_yaml").setLevel(logging.DEBUG)`
