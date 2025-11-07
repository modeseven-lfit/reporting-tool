<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Domain Models

This package contains type-safe domain models representing core business entities in the repository reporting system.

## Overview

Domain models replace ad-hoc dictionary structures with strongly-typed dataclasses that provide:

- **Type Safety**: Compile-time type checking with proper type hints
- **Validation**: Construction-time validation of business rules
- **Serialization**: Bidirectional conversion between objects and JSON-compatible dictionaries
- **Backwards Compatibility**: Seamless integration with legacy dict-based code
- **Documentation**: Self-documenting code with clear attribute definitions

## Models

### TimeWindow

Represents a named time period for metrics aggregation.

```python
from src.domain import TimeWindow

window = TimeWindow(
    name="1y",
    days=365,
    start_date="2023-01-01T00:00:00Z",
    end_date="2024-01-01T00:00:00Z",
)

# Serialize for JSON output
window_dict = window.to_dict()

# Deserialize from legacy format
window = TimeWindow.from_dict("1y", {
    "days": 365,
    "start": "2023-01-01T00:00:00Z",
    "end": "2024-01-01T00:00:00Z",
})
```

**Validation Rules:**

- `days` must be positive
- `name` cannot be empty
- Dates must be valid ISO 8601 format

### TimeWindowStats

Container for metrics aggregated over a time window.

```python
from src.domain import TimeWindowStats

stats = TimeWindowStats(
    commits=42,
    lines_added=1000,
    lines_removed=200,
    lines_net=800,
    contributors=5,
)

# Add stats together for aggregation
total = stats1 + stats2
```

**Validation Rules:**

- `commits`, `lines_added`, `lines_removed`, `contributors` must be non-negative
- `lines_net` = `lines_added` - `lines_removed` (validated automatically)
- `lines_net` can be negative (net deletion)

### RepositoryMetrics

Metrics for a single repository.

```python
from src.domain import RepositoryMetrics

metrics = RepositoryMetrics(
    gerrit_project="foo/bar",
    gerrit_host="gerrit.example.com",
    gerrit_url="https://gerrit.example.com/foo/bar",
    local_path="/tmp/repos/foo-bar",
    activity_status="active",
    has_any_commits=True,
    total_commits_ever=100,
    commit_counts={"1y": 50, "90d": 25},
    loc_stats={
        "1y": {"added": 1000, "removed": 200, "net": 800}
    },
)

# Convenience properties
if metrics.is_active:
    print(f"Active repository with {metrics.total_commits_ever} commits")

# Window-specific accessors
commits_last_year = metrics.get_commits_in_window("1y")
loc_stats = metrics.get_loc_stats_for_window("1y")
```

**Validation Rules:**

- Required fields: `gerrit_project`, `gerrit_host`, `gerrit_url`, `local_path`
- `activity_status` must be one of: `"current"`, `"active"`, `"inactive"`
- `total_commits_ever` must be non-negative
- If `has_any_commits` is False, `total_commits_ever` must be 0
- All commit counts must be non-negative
- LOC stats: `added` and `removed` must be non-negative, `net` = `added` - `removed`

### AuthorMetrics

Statistics for a single contributor.

```python
from src.domain import AuthorMetrics

author = AuthorMetrics(
    name="John Doe",
    email="john@example.com",
    username="johndoe",
    domain="example.com",
    commits={"1y": 42, "90d": 20},
    lines_added={"1y": 1000, "90d": 500},
    lines_removed={"1y": 200, "90d": 100},
    lines_net={"1y": 800, "90d": 400},
    repositories_touched={"1y": 5, "90d": 3},
)

# Aggregated totals
print(f"Total commits: {author.total_commits}")
print(f"Total lines added: {author.total_lines_added}")

# Organization affiliation
if author.is_affiliated:
    print(f"Works at: {author.domain}")
```

**Validation Rules:**

- `email` cannot be empty (primary identifier)
- If `name` is empty, defaults to `email`
- All commit/line counts must be non-negative
- Per-window consistency: `lines_net` = `lines_added` - `lines_removed`

**Legacy Compatibility:**

- `from_dict()` automatically converts repository sets to counts

### OrganizationMetrics

Aggregated statistics for an organization (by email domain).

```python
from src.domain import OrganizationMetrics

org = OrganizationMetrics(
    domain="example.com",
    contributor_count=25,
    commits={"1y": 500, "90d": 250},
    lines_added={"1y": 10000, "90d": 5000},
    lines_removed={"1y": 2000, "90d": 1000},
    lines_net={"1y": 8000, "90d": 4000},
    repositories_count={"1y": 15, "90d": 10},
)

# Check if known organization
if org.is_known_org:
    print(f"{org.domain}: {org.total_commits} commits by {org.contributor_count} contributors")
```

**Validation Rules:**

- `domain` cannot be empty
- `contributor_count` must be non-negative
- All metric counts must be non-negative
- Per-window consistency: `lines_net` = `lines_added` - `lines_removed`

### WorkflowStatus

CI/CD workflow detection results.

```python
from src.domain import WorkflowStatus

status = WorkflowStatus(
    has_github_actions=True,
    has_jenkins=True,
    workflow_files=[
        ".github/workflows/ci.yml",
        "Jenkinsfile",
    ],
    primary_ci_system="github_actions",  # Auto-detected if not specified
)

# CI system queries
if status.has_any_ci:
    systems = status.get_detected_systems()
    print(f"Detected CI systems: {', '.join(systems)}")

if status.has_multiple_ci_systems:
    print("Warning: Multiple CI systems configured")
```

**Validation Rules:**

- `primary_ci_system` must be one of: `"github_actions"`, `"jenkins"`, `"circleci"`, `"travis"`, `"gitlab_ci"`, or `None`
- Auto-detects primary CI if not specified (priority: GitHub Actions > Jenkins > CircleCI > Travis > GitLab CI)

## Usage Patterns

### Creating from Legacy Dictionaries

All domain models support `from_dict()` for gradual migration:

```python
# Legacy dictionary format
legacy_data = {
    "name": "John Doe",
    "email": "john@example.com",
    "commits": {"1y": 42},
    "lines_added": {"1y": 1000},
    "lines_removed": {"1y": 200},
    "lines_net": {"1y": 800},
}

# Convert to domain model
author = AuthorMetrics.from_dict(legacy_data)

# Use type-safe attributes
print(author.total_commits)
```

### Serializing to JSON

All domain models support `to_dict()` for JSON serialization:

```python
repo = RepositoryMetrics(...)

# Convert to dictionary for JSON output
data = repo.to_dict()

# Serialize to JSON
import json
json_output = json.dumps(data, indent=2)
```

### Round-Trip Compatibility

Domain models maintain backwards compatibility with legacy schemas:

```python
# Original data
original_dict = {...}

# Convert to domain model
model = AuthorMetrics.from_dict(original_dict)

# Serialize back to dict
restored_dict = model.to_dict()

# Should be equivalent to original
assert restored_dict == original_dict
```

### Validation at Construction

Domain models validate business rules at construction time:

```python
try:
    metrics = RepositoryMetrics(
        gerrit_project="foo/bar",
        gerrit_host="gerrit.example.com",
        gerrit_url="https://gerrit.example.com/foo/bar",
        local_path="/tmp/repos",
        has_any_commits=False,
        total_commits_ever=10,  # Inconsistent!
    )
except ValueError as e:
    print(f"Validation error: {e}")
    # Output: "Inconsistent state: has_any_commits is False but total_commits_ever > 0"
```

## Migration Strategy

The domain models are designed for gradual adoption:

1. **Phase 1**: Use `from_dict()` to convert legacy dictionaries to domain models
2. **Phase 2**: Use domain model attributes instead of dict key access
3. **Phase 3**: Update producers (data collectors) to create domain models directly
4. **Phase 4**: Remove legacy dict-based code paths

Example migration:

```python
# Before (Phase 1): Legacy dict access
def process_author(author_dict):
    commits = author_dict["commits"]["1y"]
    email = author_dict["email"]
    # ... more dict access

# After (Phase 2): Domain model access
def process_author(author_dict):
    author = AuthorMetrics.from_dict(author_dict)
    commits = author.get_commits_in_window("1y")
    email = author.email
    # ... type-safe attribute access

# Future (Phase 3): Direct domain model creation
def collect_author_data(...) -> AuthorMetrics:
    return AuthorMetrics(
        name=...,
        email=...,
        commits={...},
        # ...
    )
```

## Testing

Comprehensive unit tests are available in `tests/test_domain_models.py`:

- **Validation Tests**: Verify all business rules are enforced
- **Serialization Tests**: Ensure round-trip compatibility
- **Integration Tests**: Test models working together
- **60+ test cases** covering all models and edge cases

Run tests:

```bash
pytest tests/test_domain_models.py -v
```

## Design Principles

1. **Immutability**: Use frozen dataclasses where appropriate (TimeWindow)
2. **Fail Fast**: Validate at construction, not at serialization
3. **Explicit Over Implicit**: Clear error messages for validation failures
4. **Backwards Compatible**: Support legacy dict format indefinitely
5. **Self-Documenting**: Type hints and docstrings on all public APIs
6. **Single Responsibility**: Each model represents one business entity

## Version

Domain Model Schema Version: **1.0.0**

See `src/domain/__init__.py` for the current version.

## References

- **Refactoring Plan**: See `REFACTOR_PLAN.md` Phase 3
- **Tests**: `tests/test_domain_models.py`
- **API Documentation**: See docstrings in individual model files
