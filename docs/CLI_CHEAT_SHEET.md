# CLI Cheat Sheet

**Repository Reporting System - Quick Reference**

---

## Getting Started

```bash
# First-time setup (interactive)
reporting-tool init

# First-time setup (template)
reporting-tool init --template standard --project my-project

# Generate report
reporting-tool generate --project my-project --repos-path ./repos
```

---

## Essential Commands

### Report Generation

```bash
# Basic report
reporting-tool generate --project NAME --repos-path PATH

# With caching
reporting-tool generate --project NAME --repos-path PATH --cache

# Parallel processing
reporting-tool generate --project NAME --repos-path PATH --workers 8

# Production run (optimized)
reporting-tool generate --project NAME --repos-path PATH --cache --workers 8 --quiet
```

### Validation

```bash
# Pre-flight check
reporting-tool generate --project NAME --repos-path PATH --dry-run

# Config validation only
reporting-tool validate config/NAME.yaml

# Show effective config
reporting-tool generate --project NAME --repos-path PATH --show-config
```

### Feature Discovery

```bash
# List all features
reporting-tool list-features

# Verbose feature list
reporting-tool list-features -v

# Feature details
reporting-tool list-features --filter FEATURE_NAME
```

---

## Common Options

### Required (or from config)

| Option | Description | Example |
|--------|-------------|---------|
| `--project NAME` | Project identifier | `--project kubernetes` |
| `--repos-path PATH` | Repository directory | `--repos-path /data/repos` |

### Configuration

| Option | Description | Example |
|--------|-------------|---------|
| `--config-dir PATH` | Config file location | `--config-dir ./configs` |
| `--output-dir PATH` | Output directory | `--output-dir ./reports` |
| `--init` | Run config wizard | `--init` |
| `--init-template T` | Use template (minimal/standard/full) | `--init-template standard` |
| `--config-output PATH` | Wizard output path | `--config-output custom.yaml` |

### Output Control

| Option | Description | Example |
|--------|-------------|---------|
| `--output-format FMT` | Format (html/json/all) | `--output-format all` |
| `--no-html` | Skip HTML output | `--no-html` |
| `--no-zip` | Skip ZIP archive | `--no-zip` |

### Performance

| Option | Description | Example |
|--------|-------------|---------|
| `--cache` | Enable caching | `--cache` |
| `--cache-dir PATH` | Cache directory | `--cache-dir /tmp/cache` |
| `--workers N` | Worker count (or 'auto') | `--workers 8` |

### Verbosity

| Option | Description | Use Case |
|--------|-------------|----------|
| `--quiet` / `-q` | Errors only | Production/CI |
| _(default)_ | Info level | Normal use |
| `--verbose` / `-v` | Detailed output | Monitoring |
| `-vv` | Debug output | Troubleshooting |
| `-vvv` | Trace output | Deep debugging |

### Special Modes

| Option | Description | Output |
|--------|-------------|--------|
| `--dry-run` | Validate setup | Pre-flight checks |
| `--validate-only` | Validate config | Config validation |
| `--list-features` | Show features | Feature list |
| `--show-feature NAME` | Feature details | Detailed info |
| `--show-config` | Display config | Effective config |
| `--help` | Show help | Usage info |
| `--version` | Show version | Version number |

---

## Quick Recipes

### Development Workflow

```bash
# 1. Create config
reporting-tool init --template standard --project dev-test

# 2. Validate
reporting-tool generate --project dev-test --repos-path ./test-repos --dry-run

# 3. First run with debugging
reporting-tool generate --project dev-test --repos-path ./test-repos --cache --workers 1 -vv

# 4. Subsequent runs (fast)
reporting-tool generate --project dev-test --repos-path ./test-repos --cache -v
```

### Production Deployment

```bash
# 1. Create production config
reporting-tool init --template full --project prod \
  --output /etc/reports/prod.yaml

# 2. Validate before run
reporting-tool generate --project prod --repos-path /data/repos --dry-run

# 3. Production run
reporting-tool generate --project prod --repos-path /data/repos \
  --cache --workers 8 --quiet
```

### Troubleshooting

```bash
# Maximum verbosity, single-threaded
reporting-tool generate --project debug --repos-path ./repos \
  --workers 1 -vvv 2>&1 | tee debug.log

# Check configuration
reporting-tool generate --project NAME --repos-path PATH --show-config

# Validate specific feature
reporting-tool list-features --filter docker
```

### CI/CD Pipeline

```bash
# Non-interactive, fast, minimal output
reporting-tool init \
  --template minimal \
  --project $PROJECT_NAME \
  --output /tmp/config.yaml && \
reporting-tool generate \
  --project $PROJECT_NAME \
  --repos-path $REPOS_PATH \
  --output-dir $OUTPUT_DIR \
  --cache \
  --workers $(nproc) \
  --quiet
```

### Performance Testing

```bash
# Baseline (sequential)
time reporting-tool generate --project test --repos-path ./repos --workers 1

# With caching
time reporting-tool generate --project test --repos-path ./repos --cache

# Parallel
time reporting-tool generate --project test --repos-path ./repos --cache --workers 8

# Maximum performance
time reporting-tool generate --project test --repos-path ./repos \
  --cache --workers 8 -v
```

---

## Configuration Override

```bash
# Override specific config values
reporting-tool generate --project NAME --repos-path PATH \
  --config-override KEY=VALUE

# Examples
--config-override time_windows.90d.days=60
--config-override workers=16
--config-override cache.enabled=true
--config-override output.format=json
```

---

## Exit Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 0 | Success | Report generated successfully |
| 1 | Error | Configuration error, API failure, processing error |
| 2 | Partial Success | Some repositories failed, incomplete data |
| 3 | Usage Error | Invalid arguments, missing required flags |
| 4 | System Error | Permission denied, disk space, dependencies |

**Exit Code Details:**

- **0 (SUCCESS)**: Operation completed with no errors or warnings
- **1 (ERROR)**: General error including config, API, network, or processing failures
- **2 (PARTIAL)**: Report generated but with warnings or incomplete data
- **3 (USAGE_ERROR)**: Invalid command syntax or arguments (won't improve on retry)
- **4 (SYSTEM_ERROR)**: System-level issues like permissions or disk space

**Usage in scripts:**

```bash
reporting-tool generate --project test --repos-path ./repos
EXIT_CODE=$?

case $EXIT_CODE in
  0) echo "✓ Success!" ;;
  1) echo "✗ Error - check logs" ;;
  2) echo "⚠ Partial success - review warnings" ;;
  3) echo "✗ Usage error - fix command syntax" ;;
  4) echo "✗ System error - check permissions/disk" ;;
  *) echo "✗ Unknown error: $?" ;;
esac

exit $EXIT_CODE
```

**Retry logic (for transient errors):**

```bash
# Retry codes 1, 2, 4 (transient errors)
# Don't retry code 3 (usage errors won't improve)
for i in 1 2 3; do
  reporting-tool generate --project test --repos-path ./repos
  CODE=$?
  [ $CODE -eq 0 ] && exit 0
  [ $CODE -eq 3 ] && echo "Usage error - won't retry" && exit 3
  echo "Attempt $i failed (code $CODE), retrying..."
  sleep 5
done
echo "Failed after 3 attempts"
exit 1
```

---

## Environment Variables

```bash
# GitHub authentication
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

# Gerrit authentication
export GERRIT_USERNAME="user"
export GERRIT_PASSWORD="pass"

# Disable colored output
export NO_COLOR=1

# Custom config location
export CONFIG_DIR="/etc/reports"

# Cache directory
export CACHE_DIR="/var/cache/reports"
```

---

## Feature Categories

### Build & Package (5)

- `docker` - Docker containerization
- `gradle` - Gradle build
- `maven` - Maven build
- `npm` - NPM packages
- `sonatype` - Sonatype publishing

### CI/CD (4)

- `dependabot` - Dependabot config
- `github-actions` - GitHub Actions
- `github2gerrit` - GitHub/Gerrit sync
- `jenkins` - Jenkins jobs

### Code Quality (3)

- `linting` - Code linters
- `pre-commit` - Pre-commit hooks
- `sonarqube` - SonarQube analysis

### Documentation (3)

- `mkdocs` - MkDocs
- `readthedocs` - ReadTheDocs
- `sphinx` - Sphinx

### Repository (4)

- `github-mirror` - GitHub mirrors
- `gitreview` - Gerrit git-review
- `license` - License files
- `readme` - README quality

### Security (2)

- `secrets-detection` - Secrets scanning
- `security-scanning` - Security scans

### Testing (3)

- `coverage` - Code coverage
- `junit` - JUnit tests
- `pytest` - PyTest tests

---

## Output Files

```
output/
├── {project}_report.html      # Main HTML report
├── {project}_report.json      # JSON data (if --output-format json/all)
└── {project}_report.zip       # Archive (unless --no-zip)
```

---

## Common Patterns

### Batch Processing

```bash
for project in proj1 proj2 proj3; do
  reporting-tool generate \
    --project "$project" \
    --repos-path "/data/$project" \
    --cache --quiet
done
```

### Conditional Execution

```bash
# Only run if validation passes
if reporting-tool generate --project test --repos-path ./repos --dry-run; then
  reporting-tool generate --project test --repos-path ./repos
fi
```

### Scheduled Reports

```bash
# Crontab entry: Daily at 2 AM
0 2 * * * cd /path/to/reports && \
  reporting-tool generate --project daily --repos-path /data/repos \
  --cache --quiet --output-dir /reports/$(date +\%Y-\%m-\%d)
```

### Error Handling

```bash
reporting-tool generate --project test --repos-path ./repos || {
  echo "Report generation failed!"
  exit 1
}
```

---

## Performance Tips

### Fast Development Iterations

```bash
--cache                 # Cache API calls
--workers 1             # Single-threaded (easier debugging)
-v                      # See what's happening
```

### Maximum Performance

```bash
--cache                 # Enable caching
--workers auto          # Use all CPU cores
--quiet                 # Minimal output overhead
```

### Debugging Slow Runs

```bash
-vv                     # Show timing breakdown
# Check:
# - Repository analysis time → use --cache
# - API call count → check cache hit rate
# - CPU utilization → adjust --workers
```

---

## Troubleshooting Checklist

### Report Won't Generate

- [ ] Config file exists? `ls config/{project}.yaml`
- [ ] Repos path exists? `ls {repos-path}`
- [ ] Run `--dry-run` for diagnostics
- [ ] Check permissions on output directory
- [ ] GitHub token set? `echo $GITHUB_TOKEN`

### Slow Performance

- [ ] Enable caching: `--cache`
- [ ] Use parallel processing: `--workers auto`
- [ ] Check cache hit rate: `-v`
- [ ] Reduce time window in config
- [ ] Check network latency

### Errors

- [ ] Read full error message (includes solutions!)
- [ ] Check exit code: `echo $?`
- [ ] Run with `-vvv` for details
- [ ] Validate config: `--validate-only`
- [ ] Check documentation for error code

---

## Learn More

- **Full CLI Reference:** [CLI_REFERENCE.md](CLI_REFERENCE.md)
- **Usage Examples:** [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- **CLI Guide:** [CLI_GUIDE.md](CLI_GUIDE.md)
- **Feature Discovery:** [FEATURE_DISCOVERY_GUIDE.md](FEATURE_DISCOVERY_GUIDE.md)
- **Config Wizard:** [CONFIG_WIZARD_GUIDE.md](CONFIG_WIZARD_GUIDE.md)
- **Performance:** [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md)

---

**Quick Help:**

```bash
reporting-tool --help
reporting-tool list-features
reporting-tool list-features --detail FEATURE
```

**Version:** 2.0 (Phase 13)
**Last Updated:** 2025-01-25
