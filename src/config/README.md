<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Configuration Validation Package

Comprehensive configuration validation framework for the Repository Reporting System.

## Overview

This package provides robust configuration validation using JSON Schema with additional semantic validation, security checks, and performance warnings. It ensures configurations are correct before analysis begins, preventing runtime errors and providing clear, actionable error messages.

## Features

- ✅ **JSON Schema Validation**: Strict schema enforcement with detailed error messages
- ✅ **Semantic Validation**: Logical consistency checks (e.g., threshold ordering)
- ✅ **Security Warnings**: Detects hardcoded tokens and privacy concerns
- ✅ **Performance Checks**: Warns about resource-intensive settings
- ✅ **Schema Version Compatibility**: Ensures backward compatibility
- ✅ **Helpful Suggestions**: Provides actionable fixes for validation errors
- ✅ **Multi-level Reporting**: Errors, warnings, and informational messages

## Quick Start

### Basic Validation

```python
from src.config import validate_config_file, print_validation_result
from pathlib import Path

# Validate a configuration file
result = validate_config_file(Path("configuration/myproject.config"))

# Print results
print_validation_result(result, verbose=True)

# Check validity
if result.is_valid:
    print("✅ Configuration is valid!")
else:
    print("❌ Configuration has errors:")
    for error in result.errors:
        print(f"  - {error}")
```text

### Programmatic Validation

```python
from src.config import ConfigValidator

# Create validator
validator = ConfigValidator()

# Validate dictionary
config = {
    "project": "my-project",
    "output": {"include_sections": {...}},
    "time_windows": {...},
    "activity_thresholds": {...},
    "schema_version": "1.0.0"
}

result = validator.validate(config)

# Access specific issue types
if result.has_errors:
    for error in result.errors:
        print(f"ERROR at {error.path}: {error.message}")
        if error.suggestion:
            print(f"  Suggestion: {error.suggestion}")

if result.has_warnings:
    for warning in result.warnings:
        print(f"WARNING: {warning.message}")
```

### Command Line Validation

```python
from src.config import validate_config_file, print_validation_result
import sys

result = validate_config_file(Path("config/template.config"))
print_validation_result(result, verbose=True)

# Exit with appropriate code
sys.exit(0 if result.is_valid else 1)
```text

## Validation Levels

The validator provides three levels of feedback:

### 1. Errors (Critical)

Configuration is invalid and cannot be used. Must be fixed.

- Missing required fields
- Invalid data types
- Out-of-range values
- Schema violations
- Semantic inconsistencies (e.g., current_days >= active_days)

### 2. Warnings (Important)

Configuration is valid but may cause issues. Should be reviewed.

- Hardcoded secrets
- Suboptimal performance settings
- Missing optional but recommended fields
- Out-of-order time windows

### 3. Info (Informational)

FYI messages about configuration choices.

- Using older (but compatible) schema version
- Privacy settings disabled
- Optional features not enabled

## Validation Categories

Issues are categorized for easier filtering and handling:

- **SCHEMA**: JSON schema violations
- **SEMANTIC**: Logical inconsistencies
- **COMPATIBILITY**: Version/backward compatibility
- **SECURITY**: Security concerns
- **PERFORMANCE**: Performance impact
- **DEPRECATED**: Deprecated settings

## Required Configuration Fields

Every configuration must include:

```yaml
project: "project-name"  # Alphanumeric, dash, underscore only

output:
  include_sections:
    contributors: true
    organizations: true
    # ... other sections

time_windows:
  last_30_days: 30        # 1-30 days
  last_90_days: 90        # 30-90 days
  last_365_days: 365      # 90-365 days
  last_3_years: 1095      # 365-1095 days

activity_thresholds:
  current_days: 365       # Must be < active_days
  active_days: 1095       # Must be > current_days

schema_version: "1.0.0"   # Semantic versioning
```

## Semantic Validation Rules

Beyond schema validation, the validator enforces:

### Activity Thresholds Ordering

```python
# ❌ INVALID
activity_thresholds:
  current_days: 1095
  active_days: 365  # Error: active_days must be > current_days

# ✅ VALID
activity_thresholds:
  current_days: 365
  active_days: 1095
```text

### Time Windows Ordering

```python
# ⚠️ WARNING
time_windows:
  last_30_days: 30
  last_90_days: 25   # Warning: not in ascending order
  last_365_days: 365
```

### Conditional Requirements

```python
# ❌ INVALID - enabled but no host
gerrit:
  enabled: true
  host: ""  # Error: host required when enabled

# ✅ VALID
gerrit:
  enabled: true
  host: "gerrit.example.org"
```text

## Security Validation

### Hardcoded Token Detection

```python
# ⚠️ WARNING
extensions:
  github_api:
    enabled: true
    token: "ghp_1234567890abcdef"  # Warning: hardcoded token

# ✅ RECOMMENDED
extensions:
  github_api:
    enabled: true
    token: ""  # Use environment variable instead
```

### Privacy Settings

```python
# ℹ️ INFO
privacy:
  mask_emails: false
  anonymize_authors: false
  # Info: Consider enabling for public reports
```text

## Performance Validation

### Worker Count

```python
# ⚠️ WARNING
performance:
  max_workers: 24  # Warning: may cause resource contention

# ✅ RECOMMENDED
performance:
  max_workers: 8  # 4-16 workers recommended
```

### Pagination Settings

```python
# ⚠️ WARNING
html_tables:
  entries_per_page: 500  # Warning: may slow browser

# ✅ RECOMMENDED
html_tables:
  entries_per_page: 50  # 20-100 recommended
```text

## Schema Version Compatibility

The validator checks schema version compatibility:

```python
# ✅ Current version
schema_version: "1.0.0"

# ℹ️ Compatible but older
schema_version: "1.0.0"  # If current is 1.1.0

# ❌ Incompatible
schema_version: "2.0.0"  # Major version change

# ⚠️ Missing
# schema_version not specified - warning issued
```

## Error Message Format

Validation issues include helpful context:

```text
[ERROR] at 'activity_thresholds': current_days (1095) must be less than active_days (365)
  Suggestion: Set current_days < active_days (e.g., current=365, active=1095)

[WARNING] at 'extensions.github_api.token': GitHub token appears to be hardcoded in configuration
  Suggestion: Use environment variable CLASSIC_READ_ONLY_PAT_TOKEN instead

[INFO] at 'privacy': Email masking and author anonymization are both disabled
  Suggestion: Consider enabling privacy.mask_emails or privacy.anonymize_authors for public reports
```

## ValidationResult API

```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationIssue]
    warnings: List[ValidationIssue]
    infos: List[ValidationIssue]

    @property
    def has_errors(self) -> bool: ...

    @property
    def has_warnings(self) -> bool: ...

    def add_error(message, category, path, suggestion): ...
    def add_warning(message, category, path, suggestion): ...
    def add_info(message, category, path, suggestion): ...
```text

## ValidationIssue API

```python
@dataclass
class ValidationIssue:
    level: ValidationLevel      # ERROR, WARNING, INFO
    category: ValidationCategory  # SCHEMA, SEMANTIC, etc.
    message: str
    path: str                   # Dot-notation path (e.g., "gerrit.host")
    suggestion: Optional[str]   # Helpful fix suggestion

    def __str__(self) -> str: ...
```

## Integration with Main Application

### Validate on Startup

```python
from src.config import validate_config_file

def load_configuration(config_path: Path) -> Dict[str, Any]:
    """Load and validate configuration."""
    # Validate before loading
    result = validate_config_file(config_path)

    if not result.is_valid:
        print_validation_result(result)
        raise ValueError("Invalid configuration")

    # Print warnings but continue
    if result.has_warnings:
        print_validation_result(result)

    # Load and return config
    with open(config_path) as f:
        return yaml.safe_load(f)
```text

### Validate-Only Mode

```python
if args.validate_only:
    result = validate_config_file(config_path)
    print_validation_result(result, verbose=True)
    sys.exit(0 if result.is_valid else 1)
```

### Progressive Enhancement

```python
# Graceful degradation for missing jsonschema
try:
    from src.config import ConfigValidator
    validator = ConfigValidator()
    result = validator.validate(config)
    if not result.is_valid:
        # Handle validation errors
        pass
except ImportError:
    # Fall back to basic validation
    if "project" not in config:
        raise ValueError("Missing required field: project")
```text

## Custom Schema Path

```python
from pathlib import Path
from src.config import ConfigValidator

# Use custom schema
validator = ConfigValidator(
    schema_path=Path("/path/to/custom/schema.json")
)

result = validator.validate(config)
```

## Testing

The package includes comprehensive tests:

```bash
# Run all config validation tests
pytest tests/test_config_validation.py -v

# Run specific test category
pytest tests/test_config_validation.py::test_semantic_validation -v

# Check test coverage
pytest tests/test_config_validation.py --cov=src.config --cov-report=html
```text

## Dependencies

- **Required**: `jsonschema` (JSON Schema validation)
- **Optional**: `pyyaml` (for YAML config files)

Install with:

```bash
pip install jsonschema pyyaml
```

## Design Principles

1. **Fail Fast**: Validate configuration before starting analysis
2. **Clear Messages**: Provide actionable error messages with suggestions
3. **Multiple Levels**: Distinguish between errors, warnings, and info
4. **Schema-Driven**: Use JSON Schema for consistent validation
5. **Semantic Awareness**: Check logical consistency beyond schema
6. **Security Conscious**: Warn about security anti-patterns
7. **Performance Aware**: Flag potentially slow configurations
8. **Backwards Compatible**: Support older schema versions when possible

## Common Validation Errors

### 1. Missing Required Field

```text
ERROR: Missing required field: 'project'
Suggestion: Add 'project: your-project-name' to your configuration
```

**Fix**: Add the required field to your config file.

### 2. Invalid Type

```text
ERROR at 'time_windows.last_30_days': Invalid type: expected integer, got string
```

**Fix**: Change value from string to integer (e.g., `30` not `"30"`).

### 3. Threshold Ordering

```text
ERROR at 'activity_thresholds': current_days (1095) must be less than active_days (365)
Suggestion: Set current_days < active_days (e.g., current=365, active=1095)
```

**Fix**: Ensure `current_days < active_days`.

### 4. Conditional Requirement

```text
ERROR at 'gerrit.host': Gerrit is enabled but no host specified
Suggestion: Set gerrit.host to your Gerrit server hostname
```

**Fix**: Add `host` when `enabled: true`.

## Migration from Manual Validation

### Before (Manual Validation)

```python
def load_configuration(config_path):
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Manual checks scattered throughout code
    if "project" not in config:
        raise ValueError("Missing project")

    if config.get("activity_thresholds", {}).get("current_days", 0) >= \
       config.get("activity_thresholds", {}).get("active_days", 999):
        raise ValueError("Invalid thresholds")

    # ... many more checks
    return config
```text

### After (Schema Validation)

```python
from src.config import validate_config_file

def load_configuration(config_path):
    # Single validation call
    result = validate_config_file(config_path)

    if not result.is_valid:
        print_validation_result(result)
        raise ValueError("Invalid configuration")

    with open(config_path) as f:
        return yaml.safe_load(f)
```

## Future Enhancements

Planned features for future versions:

- [ ] Configuration migration tool (upgrade old configs)
- [ ] Configuration generator/wizard
- [ ] IDE integration (VS Code schema)
- [ ] Environment variable interpolation validation
- [ ] Cross-field dependency validation
- [ ] Configuration profiles (dev/staging/prod)
- [ ] Performance profiling of validation
- [ ] Custom validator plugins

## Support

For issues or questions:

1. Check this README
2. Review test examples in `tests/test_config_validation.py`
3. Check the JSON schema at `src/config/schema.json`
4. File an issue with validation output

## License

Apache-2.0 - See LICENSE file for details.
