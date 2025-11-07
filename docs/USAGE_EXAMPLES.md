# Usage Examples

**Repository Analysis Report Generator**

Common workflows and real-world usage examples.

Last Updated: 2025-01-25
Version: 2.0 (Phase 13 - CLI & UX Improvements)

---

## Table of Contents

- [Getting Started](#getting-started)
- [Configuration Wizard](#configuration-wizard)
- [Feature Discovery](#feature-discovery)
- [Basic Usage](#basic-usage)
- [Development Workflows](#development-workflows)
- [Production Workflows](#production-workflows)
- [CI/CD Integration](#cicd-integration)
- [Advanced Scenarios](#advanced-scenarios)
- [Automation Examples](#automation-examples)
- [Troubleshooting Workflows](#troubleshooting-workflows)

---

## Getting Started

### Example 0: First-Time Setup (30 Seconds)

The fastest way to get started with the reporting system:

```bash
# Step 1: Run the interactive wizard
reporting-tool init --project my-first-project

# Follow the prompts:
# - Repository path: ./repos
# - Output directory: ./output
# - Press Enter for other defaults

# Step 2: Generate your first report
reporting-tool generate --project my-first-project --repos-path ./repos

# Step 3: View the report
open output/my-first-project_report.html
```

**What just happened?**

1. ✅ Created configuration file: `config/my-first-project.yaml`
2. ✅ Analyzed repositories in `./repos`
3. ✅ Generated HTML report in `output/`

**Time:** ~30 seconds

---

### Example 0b: Non-Interactive Setup (10 Seconds)

For automation or when you don't want prompts:

```bash
# Create config from template
reporting-tool init \
  --init-template standard \
  --project quick-start

# Generate report
reporting-tool generate --project quick-start --repos-path ./repos
```

**Templates:**

- `minimal` - Bare essentials (~50 lines)
- `standard` - Recommended defaults (~150 lines)
- `full` - All options documented (~400 lines)

**Time:** ~10 seconds

---

## Configuration Wizard

### Example W1: Interactive Configuration

Use the wizard for guided setup with validation:

```bash
reporting-tool init --project production-reports
```

**Sample interaction:**

```
🧙 Configuration Wizard
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Let's create a configuration for: production-reports

📁 Repository Configuration
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Repository path (where your repos are located):
Default: ./repos
Enter path: /data/production/repos

Output directory (where reports will be saved):
Default: ./output
Enter path: /reports/production

📊 Time Windows
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Configure analysis time windows? [Y/n]: Y

1-year window days [365]: 365
90-day window days [90]: 90
30-day window days [30]: 30

⚙️  Performance Options
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Enable caching for faster re-runs? [Y/n]: Y
Number of parallel workers [auto]: 16

✅ Configuration created: config/production-reports.yaml

Next steps:
  1. Review: cat config/production-reports.yaml
  2. Validate: reporting-tool generate --project production-reports --repos-path /data/production/repos --dry-run
  3. Generate: reporting-tool generate --project production-reports --repos-path /data/production/repos
```

---

### Example W2: Template-Based Configuration

Quick setup without interaction:

```bash
# Minimal (for CI/CD)
reporting-tool init \
  --init-template minimal \
  --project ci-reports \
  --config-output .github/report-config.yaml

# Standard (for most projects)
reporting-tool init \
  --init-template standard \
  --project team-reports

# Full (for complex projects with all options)
reporting-tool init \
  --init-template full \
  --project enterprise-reports
```

**When to use each:**

- **minimal**: CI/CD pipelines, quick testing
- **standard**: Most projects, recommended default
- **full**: Complex projects needing all options documented

---

### Example W3: Custom Output Location

Create config in a specific location:

```bash
reporting-tool init \
  --init-template standard \
  --project my-project \
  --config-output /etc/reports/custom-config.yaml
```

---

## Feature Discovery

### Example F1: List All Features

Discover what the reporting system can detect:

```bash
# Basic list (24 features)
reporting-tool list-features
```

**Output:**

```
📦 Repository Reporting System - Available Features

Total: 24 features across 7 categories

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏗️  BUILD & PACKAGE (5 features)

  📦 docker
     Docker containerization

  ⚙️  gradle
     Gradle build configuration

  📦 maven
     Maven build configuration
...
```

---

### Example F2: Detailed Feature Information

Learn about specific features:

```bash
# Learn about Docker detection
reporting-tool list-features --detail docker

# Learn about GitHub Actions
reporting-tool list-features --detail github-actions

# Learn about testing features
reporting-tool list-features --detail pytest
reporting-tool list-features --detail junit
reporting-tool list-features --detail coverage
```

**Example output:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 docker
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Description:
  Docker containerization

Category:
  🏗️  Build & Package

Configuration File:
  Dockerfile

Detection Method:
  Checks for Dockerfile in repository root

Configuration Example:
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN uv sync  # Recommended
# or
pip install .
  COPY . .
  CMD ["python", "app.py"]

Related Features:
  • github-actions (CI/CD)
  • jenkins (CI/CD)
```

---

### Example F3: Exploring Feature Categories

```bash
# List all features with verbose output
reporting-tool list-features -v

# Find CI/CD features
reporting-tool list-features | grep -A 10 "CI/CD"

# Find testing features
reporting-tool list-features --detail pytest
reporting-tool list-features --detail junit
reporting-tool list-features --detail coverage

# Find documentation features
reporting-tool list-features --detail sphinx
reporting-tool list-features --detail mkdocs
reporting-tool list-features --detail readthedocs

# Find security features
reporting-tool list-features --detail secrets-detection
reporting-tool list-features --detail security-scanning
```

---

## Basic Usage

### Example 1: First Report

Generate your first report with minimal setup:

```bash
# Clone repositories
mkdir -p ~/workspace/repos
cd ~/workspace/repos
git clone https://github.com/org/repo1.git
git clone https://github.com/org/repo2.git

# Create configuration
cd ~/project-reports
cp config/template.config.example config/template.config

# Generate report
reporting-tool generate \
  --project my-first-report \
  --repos-path ~/workspace/repos

# View result
open output/my-first-report_report.html
```

---

### Example 2: Quick Validation

Before running a full report, validate your setup:

```bash
reporting-tool generate \
  --project kubernetes \
  --repos-path /data/k8s-repos \
  --dry-run
```

**Output:**

```
🔍 Running pre-flight validation checks...

✅ Configuration validation: PASSED
✅ Path validation: PASSED
✅ API connectivity: PASSED
✅ System resources: PASSED
✅ Template validation: PASSED

All checks passed! Ready to generate reports.
```

---

### Example 3: View Configuration

Check what configuration will be used:

```bash
reporting-tool generate \
  --project kubernetes \
  --repos-path /data/k8s-repos \
  --show-config
```

---

## Development Workflows

### Workflow 1: Rapid Iteration with Caching

When developing or testing, use caching to speed up iterations:

```bash
# First run (slow - analyzes everything)
reporting-tool generate \
  --project dev-test \
  --repos-path ./test-repos \
  --cache \
  -v

# Subsequent runs (fast - uses cache)
# Modify templates, config, etc.
reporting-tool generate \
  --project dev-test \
  --repos-path ./test-repos \
  --cache \
  -v

# Clear cache when needed
rm -rf .cache/repo-metrics/
```

---

### Workflow 2: Testing with Subset

Test changes on a small subset before running on all repos:

```bash
# Create test subset
mkdir test-repos
cp -r repos/important-repo-1 test-repos/
cp -r repos/important-repo-2 test-repos/

# Run on subset
reporting-tool generate \
  --project test-subset \
  --repos-path test-repos/ \
  --cache \
  -vv

# If successful, run on full set
reporting-tool generate \
  --project full-report \
  --repos-path repos/ \
  --cache
```

---

### Workflow 3: Debug Mode

When troubleshooting issues:

```bash
# Maximum verbosity, single-threaded
reporting-tool generate \
  --project debug \
  --repos-path ./repos \
  --workers 1 \
  -vvv \
  2>&1 | tee debug.log

# Review logs
less debug.log
```

---

## Production Workflows

### Workflow 1: Multi-Project Organization

Generate reports for multiple projects:

```bash
#!/bin/bash
# generate-all-reports.sh

PROJECTS=("kubernetes" "prometheus" "grafana")
BASE_REPOS="/data/repos"
OUTPUT_BASE="/reports/$(date +%Y-%m-%d)"

for project in "${PROJECTS[@]}"; do
  echo "Generating report for: $project"

  reporting-tool generate \
    --project "$project" \
    --repos-path "$BASE_REPOS/$project" \
    --output-dir "$OUTPUT_BASE/$project" \
    --cache \
    --quiet

  if [ $? -eq 0 ]; then
    echo "✓ $project: SUCCESS"
  else
    echo "✗ $project: FAILED"
  fi
done

echo "All reports generated in: $OUTPUT_BASE"
```

---

### Workflow 2: Daily Automated Reports

Schedule daily report generation:

```bash
#!/bin/bash
# daily-report.sh

PROJECT="my-project"
REPOS="/data/repos"
OUTPUT="/reports/daily/$(date +%Y-%m-%d)"
ARCHIVE="/reports/archive"

# Generate report
reporting-tool generate \
  --project "$PROJECT" \
  --repos-path "$REPOS" \
  --output-dir "$OUTPUT" \
  --cache \
  --quiet

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  # Success - archive old reports
  find "$ARCHIVE" -type f -mtime +30 -delete

  # Copy to archive
  cp "$OUTPUT/${PROJECT}_report.html" "$ARCHIVE/${PROJECT}_$(date +%Y%m%d).html"

  # Send notification (optional)
  echo "Report generated: $OUTPUT" | mail -s "Daily Report Ready" team@example.com
else
  # Failure - send alert
  echo "Report generation failed with exit code $EXIT_CODE" | \
    mail -s "ALERT: Report Failed" ops@example.com
fi

exit $EXIT_CODE
```

**Cron schedule:**

```cron
# Run daily at 2 AM
0 2 * * * /path/to/daily-report.sh
```

---

### Workflow 3: Weekly Comprehensive Reports

Generate detailed weekly reports:

```bash
#!/bin/bash
# weekly-report.sh

PROJECT="weekly-comprehensive"
REPOS="/data/repos"
OUTPUT="/reports/weekly/$(date +%Y-W%V)"

# Pull latest changes
echo "Updating repositories..."
for repo in "$REPOS"/*; do
  if [ -d "$repo/.git" ]; then
    echo "  Updating: $(basename $repo)"
    (cd "$repo" && git pull --quiet)
  fi
done

# Generate comprehensive report
reporting-tool generate \
  --project "$PROJECT" \
  --repos-path "$REPOS" \
  --output-dir "$OUTPUT" \
  --output-format all \
  --workers 16 \
  -v

# Generate summary email
if [ $? -eq 0 ]; then
  cat > /tmp/weekly-email.txt << EOF
Weekly Repository Analysis Report

Report Date: $(date +%Y-%m-%d)
Report Location: $OUTPUT

View HTML Report: file://$OUTPUT/${PROJECT}_report.html

This is an automated weekly report.
EOF

  mail -s "Weekly Repository Report" team@example.com < /tmp/weekly-email.txt
fi
```

---

## CI/CD Integration

### Example 1: GitHub Actions

```yaml
# .github/workflows/generate-reports.yml
name: Generate Repository Reports

on:
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  generate:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout report generator
        uses: actions/checkout@v3
        with:
          repository: org/project-reports
          path: reporter

      - name: Checkout repositories
        uses: actions/checkout@v3
        with:
          repository: org/all-repos
          path: repos

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd reporter
          uv sync  # Recommended
# or
pip install .

      - name: Generate reports
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          cd reporter
          reporting-tool generate \
            --project ${{ github.repository }} \
            --repos-path ../repos \
            --output-dir ../output \
            --quiet

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: repository-reports
          path: output/

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./output
```

---

### Example 2: GitLab CI

```yaml
# .gitlab-ci.yml
generate-reports:
  stage: deploy
  image: python:3.11

  script:
    - uv sync  # Recommended
# or
pip install .
    - reporting-tool generate
        --project $CI_PROJECT_NAME
        --repos-path /data/repos
        --output-dir output/
        --quiet

  artifacts:
    paths:
      - output/
    expire_in: 30 days

  only:
    - schedules
```

---

### Example 3: Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any

    triggers {
        cron('0 2 * * 1')  // Weekly on Monday at 2 AM
    }

    stages {
        stage('Setup') {
            steps {
                sh 'uv sync  # Recommended
# or
pip install .'
            }
        }

        stage('Generate Reports') {
            steps {
                withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
                    sh '''
                        reporting-tool generate \
                            --project ${JOB_NAME} \
                            --repos-path /data/repos \
                            --output-dir output/ \
                            --quiet
                    '''
                }
            }
        }

        stage('Publish') {
            steps {
                publishHTML([
                    reportDir: 'output',
                    reportFiles: '*_report.html',
                    reportName: 'Repository Analysis'
                ])

                archiveArtifacts artifacts: 'output/**', allowEmptyArchive: false
            }
        }
    }

    post {
        failure {
            mail to: 'ops@example.com',
                 subject: "Report Generation Failed: ${env.JOB_NAME}",
                 body: "Build ${env.BUILD_NUMBER} failed. Check ${env.BUILD_URL}"
        }
    }
}
```

---

## Advanced Scenarios

### Scenario 1: Organization-Wide Analysis

Analyze repositories across multiple organizations:

```bash
#!/bin/bash
# org-analysis.sh

ORGS=("org1" "org2" "org3")
BASE_REPOS="/data/organizations"
OUTPUT_BASE="/reports/org-analysis/$(date +%Y-%m)"

# Clone/update all org repositories
for org in "${ORGS[@]}"; do
  echo "Processing organization: $org"

  # Update repositories (assuming already cloned)
  for repo in "$BASE_REPOS/$org"/*; do
    if [ -d "$repo/.git" ]; then
      (cd "$repo" && git pull --quiet)
    fi
  done

  # Generate org report
  reporting-tool generate \
    --project "$org" \
    --repos-path "$BASE_REPOS/$org" \
    --output-dir "$OUTPUT_BASE/$org" \
    --cache \
    --workers 16 \
    -v
done

# Generate combined summary
python scripts/combine-reports.py \
  --input "$OUTPUT_BASE" \
  --output "$OUTPUT_BASE/combined-summary.html"
```

---

### Scenario 2: Comparison Reports

Compare current state with previous month:

```bash
#!/bin/bash
# comparison-report.sh

PROJECT="my-project"
REPOS="/data/repos"
CURRENT_MONTH=$(date +%Y-%m)
PREV_MONTH=$(date -d "1 month ago" +%Y-%m)

# Generate current report
reporting-tool generate \
  --project "$PROJECT" \
  --repos-path "$REPOS" \
  --output-dir "/reports/$CURRENT_MONTH" \
  --cache

# Compare with previous
python scripts/compare-reports.py \
  --baseline "/reports/$PREV_MONTH/${PROJECT}_report.json" \
  --current "/reports/$CURRENT_MONTH/${PROJECT}_report.json" \
  --output "/reports/$CURRENT_MONTH/comparison.html"
```

---

### Scenario 3: Custom Time Windows

Generate report for specific time periods:

```bash
# Custom configuration with specific dates
cat > config/quarterly.config << EOF
project: quarterly-report
repositories_path: /data/repos

time_windows:
  q1_2024:
    days: 90
    start: "2024-01-01T00:00:00Z"
    end: "2024-03-31T23:59:59Z"
  q2_2024:
    days: 91
    start: "2024-04-01T00:00:00Z"
    end: "2024-06-30T23:59:59Z"

activity_thresholds:
  active_days: 365
  current_days: 90
EOF

reporting-tool generate \
  --project quarterly-report \
  --repos-path /data/repos
```

---

## Automation Examples

### Example 1: Email Distribution

Generate and email reports:

```bash
#!/bin/bash
# email-report.sh

PROJECT="$1"
RECIPIENTS="team@example.com"

# Generate report
reporting-tool generate \
  --project "$PROJECT" \
  --repos-path /data/repos \
  --output-dir /tmp/reports \
  --output-format html \
  --no-zip \
  --quiet

if [ $? -eq 0 ]; then
  # Email report as attachment
  echo "Please find attached the latest repository analysis report." | \
    mail -s "Repository Report: $PROJECT" \
         -a "/tmp/reports/${PROJECT}_report.html" \
         "$RECIPIENTS"
fi
```

---

### Example 2: Slack Notification

Send report link to Slack:

```bash
#!/bin/bash
# slack-notify.sh

PROJECT="$1"
OUTPUT_URL="https://reports.example.com/$(date +%Y-%m-%d)"
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Generate report
reporting-tool generate \
  --project "$PROJECT" \
  --repos-path /data/repos \
  --output-dir /var/www/reports/$(date +%Y-%m-%d) \
  --quiet

if [ $? -eq 0 ]; then
  # Send Slack notification
  curl -X POST "$SLACK_WEBHOOK" \
    -H 'Content-Type: application/json' \
    -d "{
      \"text\": \"📊 New repository report available\",
      \"attachments\": [{
        \"color\": \"good\",
        \"title\": \"$PROJECT Report\",
        \"title_link\": \"$OUTPUT_URL/${PROJECT}_report.html\",
        \"text\": \"Report generated on $(date)\",
        \"fields\": [
          {\"title\": \"Project\", \"value\": \"$PROJECT\", \"short\": true},
          {\"title\": \"Date\", \"value\": \"$(date +%Y-%m-%d)\", \"short\": true}
        ]
      }]
    }"
fi
```

---

### Example 3: Archive and Cleanup

Automatic archival and cleanup:

```bash
#!/bin/bash
# archive-reports.sh

REPORTS_DIR="/reports"
ARCHIVE_DIR="/reports/archive"
RETENTION_DAYS=90

# Find reports older than retention period
find "$REPORTS_DIR" -type f -name "*_report.html" -mtime +$RETENTION_DAYS | while read file; do
  # Compress and move to archive
  gzip "$file"
  mv "${file}.gz" "$ARCHIVE_DIR/"
done

# Delete very old archives (1 year)
find "$ARCHIVE_DIR" -type f -mtime +365 -delete

echo "Archival complete. Old reports compressed and moved."
```

---

## Troubleshooting Workflows

### Workflow 1: Identify Problematic Repository

If report generation fails, identify which repository causes issues:

```bash
#!/bin/bash
# test-each-repo.sh

REPOS_PATH="/data/repos"

for repo in "$REPOS_PATH"/*; do
  if [ ! -d "$repo/.git" ]; then
    continue
  fi

  repo_name=$(basename "$repo")
  echo "Testing: $repo_name"

  # Create temp directory with single repo
  temp_dir=$(mktemp -d)
  cp -r "$repo" "$temp_dir/"

  # Try to generate report
  reporting-tool generate \
    --project "test-$repo_name" \
    --repos-path "$temp_dir" \
    --output-dir /tmp/test-output \
    --quiet

  if [ $? -ne 0 ]; then
    echo "❌ FAILED: $repo_name"
  else
    echo "✓ OK: $repo_name"
  fi

  # Cleanup
  rm -rf "$temp_dir" /tmp/test-output
done
```

---

### Workflow 2: Performance Profiling

Identify performance bottlenecks:

```bash
#!/bin/bash
# profile-performance.sh

# Run with time tracking
time reporting-tool generate \
  --project performance-test \
  --repos-path /data/repos \
  --workers 1 \
  -vv 2>&1 | tee profile.log

# Analyze log for slow operations
echo "=== Slowest operations ==="
grep "took" profile.log | sort -k3 -n | tail -20

# Test with different worker counts
for workers in 1 4 8 16; do
  echo "Testing with $workers workers..."

  start=$(date +%s)
  reporting-tool generate \
    --project perf-test \
    --repos-path /data/repos \
    --workers $workers \
    --quiet
  end=$(date +%s)

  duration=$((end - start))
  echo "Workers: $workers, Time: ${duration}s"
done
```

---

### Workflow 3: Configuration Testing

Test different configurations:

```bash
#!/bin/bash
# test-configs.sh

CONFIGS=("config/prod.config" "config/dev.config" "config/test.config")

for config in "${CONFIGS[@]}"; do
  echo "Testing configuration: $config"

  # Validate
  reporting-tool generate \
    --project test \
    --repos-path /data/repos \
    --config-dir $(dirname "$config") \
    --dry-run

  if [ $? -eq 0 ]; then
    echo "✓ $config: VALID"
  else
    echo "❌ $config: INVALID"
  fi
done
```

---

## Tips and Best Practices

### Tip 1: Always Validate First

```bash
# Before production run
--dry-run
```

### Tip 2: Use Caching in Development

```bash
# Speed up iterations
--cache
```

### Tip 3: Start with Quiet Mode in Production

```bash
# Less noise in logs
--quiet
```

### Tip 4: Monitor Exit Codes

```bash
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  # Handle failure
fi
```

### Tip 5: Archive Old Reports

```bash
# Prevent disk space issues
find /reports -type f -mtime +90 -delete
```

---

### Example 9: Using Configuration Wizard in Automation

Even in scripts, you can use templates for consistency:

```bash
#!/bin/bash
# automated-setup.sh

PROJECTS=("kubernetes" "prometheus" "grafana")

for project in "${PROJECTS[@]}"; do
  echo "Setting up: $project"

  # Create config from template
  reporting-tool init \
    --init-template standard \
    --project "$project" \
    --config-output "config/${project}.yaml"

  # Validate
  reporting-tool generate \
    --project "$project" \
    --repos-path "/data/repos/$project" \
    --dry-run

  # Generate report
  reporting-tool generate \
    --project "$project" \
    --repos-path "/data/repos/$project" \
    --cache \
    --quiet
done
```

---

### Example 10: Performance Metrics

Monitor report generation performance:

```bash
# Basic timing
reporting-tool generate --project test --repos-path ./repos

# Detailed metrics
reporting-tool generate --project test --repos-path ./repos -v

# Debug profiling
reporting-tool generate --project test --repos-path ./repos -vv
```

**Verbose output:**

```
📊 Performance Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️  Timing Breakdown:
   Repository analysis:  28.5s (63%)
   Report generation:    12.3s (27%)
   Validation:            2.1s  (5%)
   Other:                 2.3s  (5%)

💾 Resource Usage:
   Peak memory:          256 MB
   CPU time:             42.3s
   Disk I/O:             145 MB

🌐 API Statistics:
   GitHub API calls:     156 total (89 cached, 57%)

📦 Repositories:
   Analyzed:             12
   Throughput:           0.27 repos/sec
```

---

## Tips and Best Practices

### Tip 1: Always Start with Wizard

```bash
# First time? Use the wizard!
reporting-tool init --project my-project
```

### Tip 2: Validate Before Long Runs

```bash
# Always dry-run first
reporting-tool generate --project test --repos-path ./repos --dry-run
```

### Tip 3: Use Feature Discovery

```bash
# Learn what's available
reporting-tool list-features
reporting-tool list-features --detail <feature-name>
```

### Tip 4: Monitor Performance

```bash
# Watch metrics to optimize
reporting-tool generate --project test --repos-path ./repos -v
```

### Tip 5: Use Templates in CI/CD

```bash
# Non-interactive setup
--init-template minimal
```

### Tip 6: Enable Caching

```bash
# Speed up iterations
--cache
```

### Tip 7: Monitor Exit Codes

```bash
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  # Handle failure
fi
```

### Tip 8: Archive Old Reports

```bash
# Prevent disk space issues
find /reports -type f -mtime +90 -delete
```

---

## Quick Reference

### First-Time User Journey

```bash
# 1. Learn about features
reporting-tool list-features

# 2. Create configuration
reporting-tool init --project my-project

# 3. Validate setup
reporting-tool generate --project my-project --repos-path ./repos --dry-run

# 4. Generate report
reporting-tool generate --project my-project --repos-path ./repos

# 5. View results
open output/my-project_report.html
```

### Power User Journey

```bash
# Template setup
reporting-tool init --template standard --project prod

# Optimized generation
reporting-tool generate \
  --project prod \
  --repos-path /data/repos \
  --cache \
  --workers auto \
  -v
```

---

**Need more examples? Check these guides:**

- [CLI Guide](CLI_GUIDE.md) - Complete CLI documentation
- [CLI Reference](CLI_REFERENCE.md) - All command options
- [CLI Cheat Sheet](CLI_CHEAT_SHEET.md) - Quick reference
- [Integration Patterns](INTEGRATION_PATTERNS.md) - CI/CD and automation
- [Feature Discovery Guide](FEATURE_DISCOVERY_GUIDE.md) - Feature details
- [Configuration Wizard Guide](CONFIG_WIZARD_GUIDE.md) - Setup walkthrough

---

Last Updated: 2025-01-25
Version: 2.0 (Phase 13 - CLI & UX Improvements)
Status: Production Ready
