<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Production Deployment Guide

**Version:** 1.0.0
**Date:** 2025-01-29
**Status:** PRODUCTION READY
**System:** Repository Reporting System

---

## Table of Contents

1. [Overview](#overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Methods](#deployment-methods)
4. [Local Installation Deployment](#local-installation-deployment)
5. [GitHub Actions Deployment](#github-actions-deployment)
6. [Configuration Management](#configuration-management)
7. [Secrets Management](#secrets-management)
8. [Initial Deployment](#initial-deployment)
9. [Smoke Testing](#smoke-testing)
10. [Monitoring Setup](#monitoring-setup)
11. [Post-Deployment Validation](#post-deployment-validation)
12. [Rollback Procedures](#rollback-procedures)
13. [Troubleshooting](#troubleshooting)
14. [Maintenance](#maintenance)
15. [Appendix](#appendix)

---

## Overview

### Purpose

This guide provides step-by-step instructions for deploying the Repository Reporting System to production environments. It covers all deployment methods, configuration, validation, and operational procedures.

### Scope

- **Target Audience:** DevOps engineers, system administrators, technical leads
- **Deployment Types:** Local installation, GitHub Actions, CI/CD pipelines
- **Environments:** Production, staging, development
- **Prerequisites:** System validated per PRODUCTION_READINESS.md

### Deployment Philosophy

1. **Safety First:** All deployments include rollback plans
2. **Incremental:** Deploy in stages, validate each step
3. **Automated:** Minimize manual steps, maximize repeatability
4. **Monitored:** Track metrics before, during, and after deployment
5. **Documented:** Record all changes, issues, and decisions

### Deployment Timeline

| Phase | Duration | Activities |
|-------|----------|------------|
| Pre-deployment | 1-2 hours | Checklist, environment prep, config |
| Deployment | 30-60 min | Install, configure, test |
| Validation | 30-45 min | Smoke tests, monitoring setup |
| Stabilization | 24-48 hours | Monitor, fine-tune, support |

**Total Time:** 2-4 hours (initial), 1-2 hours (subsequent)

---

## Pre-Deployment Checklist

### ✅ Planning & Preparation

Before Starting Deployment:

- [ ] Read this entire guide
- [ ] Review [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md)
- [ ] Identify deployment window (recommended: off-peak hours)
- [ ] Notify stakeholders of deployment schedule
- [ ] Prepare rollback plan
- [ ] Backup existing configurations (if upgrading)
- [ ] Review recent changes (CHANGELOG.md)

### ✅ System Requirements

Hardware Requirements:

- [ ] **Minimum:** 2 CPU cores, 2 GB RAM, 5 GB disk
- [ ] **Recommended:** 8 CPU cores, 8 GB RAM, 20 GB disk
- [ ] Network connectivity: HTTPS outbound to GitHub, Gerrit, Jenkins
- [ ] Sufficient disk I/O: >50 MB/s write throughput

Software Requirements:

- [ ] **Python:** 3.10, 3.11, or 3.12 installed

  ```bash
  python --version
  # Expected: Python 3.10.x, 3.11.x, or 3.12.x
  ```

- [ ] **pip:** Latest version

  ```bash
  pip --version
  # Expected: pip 23.x or higher
  ```

- [ ] **Git:** 2.x or higher

  ```bash
  git --version
  # Expected: git version 2.x
  ```

- [ ] **Operating System:** Linux, macOS, or Windows with WSL

### ✅ Access Requirements

GitHub Access:

- [ ] GitHub Personal Access Token (PAT) created
- [ ] Token scopes: `repo` (private) or `public_repo` (public only)
- [ ] Token tested and working

  ```bash
  curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
  # Should return your user info (200 OK)
  ```

- [ ] Rate limit confirmed: 5000 req/hr (authenticated)

Gerrit Access (if applicable):

- [ ] Gerrit credentials obtained
- [ ] API access verified

  ```bash
  curl -u "$GERRIT_USERNAME:$GERRIT_PASSWORD" https://gerrit.example.com/a/projects/
  # Should return project list or empty array (200 OK)
  ```

Jenkins Access (if applicable):

- [ ] Jenkins URL confirmed
- [ ] API access verified (authentication optional)

### ✅ Network Requirements

- [ ] Outbound HTTPS (443) allowed to:
  - `github.com`
  - `api.github.com`
  - Gerrit servers (if used)
  - Jenkins servers (if used)
- [ ] DNS resolution working
- [ ] Proxy configured (if required)

  ```bash
  export HTTP_PROXY="http://proxy.example.com:8080"
  export HTTPS_PROXY="http://proxy.example.com:8080"
  ```

### ✅ Security Checklist

- [ ] No credentials in Git repository
- [ ] `.gitignore` configured properly
- [ ] Pre-commit hooks installed (optional but recommended)
- [ ] Secrets stored securely (environment variables or secret manager)
- [ ] File permissions set correctly (600 for config files with secrets)

### ✅ Documentation Review

- [ ] [README.md](../README.md) - Project overview
- [ ] [CLI_QUICK_START.md](CLI_QUICK_START.md) - Quick start guide
- [ ] [CLI_REFERENCE.md](CLI_REFERENCE.md) - CLI reference
- [ ] [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problem resolution
- [ ] [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) - Validation report

### ✅ Team Readiness

- [ ] Deployment lead identified
- [ ] On-call engineer available
- [ ] Stakeholders notified
- [ ] Communication channel ready (Slack, email, etc.)
- [ ] Escalation path documented

---

## Deployment Methods

### Method Comparison

| Method | Use Case | Complexity | Automation | Best For |
|--------|----------|------------|------------|----------|
| **Local Installation** | Manual execution, testing, development | Low | Manual | One-time reports, testing |
| **GitHub Actions** | Automated, scheduled, CI/CD | Medium | High | Regular reports, CI/CD |
| **Docker** (planned) | Containerized, portable | Medium | High | Multi-env, orchestration |

### Choosing a Deployment Method

Use Local Installation if:

- You need to run reports manually on-demand
- You're testing or developing locally
- You have a single server/workstation
- You prefer direct control

Use GitHub Actions if:

- You want automated, scheduled report generation
- You're using GitHub already
- You want reports integrated with CI/CD
- You prefer cloud-based execution

Docker (Future):

- Containerized deployment
- Multi-environment consistency
- Kubernetes orchestration
- Planned for future release

---

## Local Installation Deployment

### Step 1: Environment Setup

1.1 Create Project Directory

```bash
# Choose installation location
export INSTALL_DIR="/opt/project-reports"  # or ~/project-reports
sudo mkdir -p $INSTALL_DIR
sudo chown $USER:$USER $INSTALL_DIR
cd $INSTALL_DIR
```text

1.2 Clone Repository

```bash
# Clone from GitHub
git clone https://github.com/lfit/project-reports.git .

# Or clone specific version/tag
git clone --branch v1.0.0 https://github.com/lfit/project-reports.git .

# Verify clone
ls -la
# Should see: generate_reports.py, src/, tests/, docs/, etc.
```

1.3 Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# Or: venv\Scripts\activate  # Windows

# Verify activation
which python
# Should show: /opt/project-reports/venv/bin/python
```text

1.4 Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
uv sync  # Recommended
# or: pip install .

# Verify installation
pip list
# Should show: httpx, PyYAML, Jinja2, etc.

# Test import
python -c "import httpx, yaml, jinja2; print('All imports successful')"
# Expected: All imports successful
```

### Step 2: Configuration

2.1 Create Configuration Directory

```bash
# Configuration directory should already exist
ls -la config/
# Should see: template.config, examples/, etc.

# Create project-specific config
mkdir -p config/production
```text

2.2 Initialize Configuration

```bash
# Generate configuration template
reporting-tool init --template --project PRODUCTION

# This creates: config/PRODUCTION.yaml
ls -la config/PRODUCTION.yaml
```

2.3 Edit Configuration

```bash
# Edit with your preferred editor
nano config/PRODUCTION.yaml
# Or: vim config/PRODUCTION.yaml
# Or: code config/PRODUCTION.yaml
```text

Example Production Configuration:

```yaml
# config/PRODUCTION.yaml
project: PRODUCTION
version: '1.0'

# Repository paths
repos_path: /data/repositories
output_path: /data/reports

# API Configuration
api:
  github:
    # Token from environment variable (recommended)
    token: ${GITHUB_TOKEN}
    # Or specify directly (NOT RECOMMENDED in production)
    # token: ghp_xxxxxxxxxxxx

  gerrit:
    # Optional: Only if using Gerrit
    enabled: false
    # username: ${GERRIT_USERNAME}
    # password: ${GERRIT_PASSWORD}

  jenkins:
    # Optional: Only if using Jenkins
    enabled: false
    # url: https://jenkins.example.com

# Performance Settings
workers: 8  # Adjust based on CPU cores (1-2 per core)
cache_enabled: true
cache_ttl: 7  # days

# Output Settings
output_format: all  # text, html, json, or all
generate_html: true
generate_json: true

# Logging
log_level: INFO
log_timestamps: true

# Features
include:
  - summary
  - repositories
  - contributors
  - organizations
  - features
  - workflows
```

2.4 Validate Configuration

```bash
# Test configuration syntax
reporting-tool generate --config config/PRODUCTION.yaml --dry-run

# Expected output:
# ✅ Configuration valid
# ✅ All required fields present
# ✅ Repository path exists
# ✅ API credentials available
```text

### Step 3: Set Up Secrets

3.1 Environment Variables Method (Recommended)

```bash
# Create secrets file (not in Git)
cat > /opt/project-reports/.env << 'EOF'
# GitHub API Token
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Gerrit Credentials (if applicable)
export GERRIT_USERNAME="your-username"
export GERRIT_PASSWORD="your-password"

# Jenkins Credentials (if applicable)
export JENKINS_USERNAME="your-username"
export JENKINS_TOKEN="your-api-token"
EOF

# Secure the file
chmod 600 /opt/project-reports/.env

# Add to .gitignore (should already be there)
echo ".env" >> .gitignore
```

3.2 Load Secrets

```bash
# Load environment variables
source /opt/project-reports/.env

# Verify secrets loaded
echo $GITHUB_TOKEN | cut -c1-10
# Should show: ghp_xxxxxx (first 10 chars)

# Test GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
# Should show your rate limit (5000/hr for authenticated)
```text

3.3 Persist for Future Sessions

```bash
# Add to shell profile (optional)
echo "source /opt/project-reports/.env" >> ~/.bashrc
# Or: ~/.bash_profile, ~/.zshrc, etc.

# For systemd service (see Appendix A)
```

### Step 4: Initial Test Run

4.1 Test with Small Dataset

```bash
# Create test repository directory
mkdir -p /tmp/test-repos

# Clone a single test repository
cd /tmp/test-repos
git clone https://github.com/octocat/Hello-World.git

# Run report generation
cd /opt/project-reports
reporting-tool generate \
  --project TEST \
  --repos-path /tmp/test-repos \
  --output-format text \
  --workers 1

# Check output
ls -la TEST-report.txt
cat TEST-report.txt
```text

4.2 Expected Output

```

Repository Reporting System - Test Run
======================================

Processing: Hello-World
  ✅ Repository analyzed successfully
  ✅ Features detected: 2
  ✅ Contributors counted: 3

Report generated: TEST-report.txt
Duration: 3.2s
Repositories: 1
Success: 1 (100%)

```text

4.3 Verify Results

```bash
# Check exit code
echo $?
# Expected: 0 (success)

# Check report content
grep "Success" TEST-report.txt
# Should show summary statistics

# Check for errors in output
grep -i "error\|failed" TEST-report.txt
# Should show no errors
```

### Step 5: Production Test Run

5.1 Run with Actual Data

```bash
# Set repository path (adjust to your environment)
export REPOS_PATH="/data/repositories"

# Run report generation
reporting-tool generate \
  --project PRODUCTION \
  --repos-path $REPOS_PATH \
  --config config/PRODUCTION.yaml

# Monitor progress
# (Output shows real-time progress)
```text

5.2 Monitor Execution

```bash
# In another terminal, monitor resources
watch -n 1 'ps aux | grep python'

# Monitor memory
watch -n 1 'free -h'

# Monitor disk I/O
iostat -x 1
```

5.3 Verify Completion

```bash
# Check exit code
echo $?
# Expected: 0

# Check generated files
ls -lah PRODUCTION-report.*
# Should see: .txt, .html, .json

# Check file sizes
du -h PRODUCTION-report.*
# Should be reasonable sizes

# Preview reports
head -20 PRODUCTION-report.txt
```text

### Step 6: Schedule Automated Execution (Optional)

6.1 Create Wrapper Script

```bash
# Create execution wrapper
cat > /opt/project-reports/run-reports.sh << 'EOF'
#!/bin/bash
# Repository Reports - Production Execution Wrapper

set -euo pipefail

# Configuration
INSTALL_DIR="/opt/project-reports"
LOG_DIR="$INSTALL_DIR/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/report-$TIMESTAMP.log"

# Create log directory
mkdir -p "$LOG_DIR"

# Load environment
source "$INSTALL_DIR/.env"
source "$INSTALL_DIR/venv/bin/activate"

# Change to project directory
cd "$INSTALL_DIR"

# Run report generation
echo "=== Report Generation Started: $(date) ===" | tee -a "$LOG_FILE"
reporting-tool generate \
  --project PRODUCTION \
  --config config/PRODUCTION.yaml \
  2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=$?
echo "=== Report Generation Finished: $(date) ===" | tee -a "$LOG_FILE"
echo "Exit Code: $EXIT_CODE" | tee -a "$LOG_FILE"

# Cleanup old logs (keep last 30 days)
find "$LOG_DIR" -name "report-*.log" -mtime +30 -delete

exit $EXIT_CODE
EOF

# Make executable
chmod +x /opt/project-reports/run-reports.sh
```

6.2 Set Up Cron Job

```bash
# Edit crontab
crontab -e

# Add daily execution at 2 AM
0 2 * * * /opt/project-reports/run-reports.sh

# Or weekly on Sunday at 2 AM
# 0 2 * * 0 /opt/project-reports/run-reports.sh

# Save and exit

# Verify cron entry
crontab -l
```text

6.3 Set Up systemd Timer (Alternative)

See Appendix A for systemd service and timer configuration.

### Step 7: Monitoring Setup

7.1 Log Rotation

```bash
# Create logrotate config
sudo tee /etc/logrotate.d/project-reports << 'EOF'
/opt/project-reports/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    missingok
    create 0644 project-reports project-reports
}
EOF

# Test logrotate
sudo logrotate -d /etc/logrotate.d/project-reports
```

7.2 Set Up Alerts (Optional)

```bash
# Create alert script
cat > /opt/project-reports/alert-on-failure.sh << 'EOF'
#!/bin/bash
# Send alert if report generation fails

LOG_FILE="$1"
EXIT_CODE=$(tail -1 "$LOG_FILE" | grep -oP 'Exit Code: \K\d+')

if [ "$EXIT_CODE" != "0" ]; then
    # Send email alert (requires mailutils)
    echo "Report generation failed with exit code $EXIT_CODE" | \
        mail -s "ALERT: Report Generation Failed" ops-team@example.com

    # Or send Slack notification
    # curl -X POST -H 'Content-type: application/json' \
    #   --data '{"text":"Report generation failed"}' \
    #   $SLACK_WEBHOOK_URL
fi
EOF

chmod +x /opt/project-reports/alert-on-failure.sh

# Update wrapper script to call alert script
```text

### Step 8: Deployment Verification

8.1 Verification Checklist

- [ ] Installation directory created and accessible
- [ ] Repository cloned successfully
- [ ] Virtual environment created and activated
- [ ] Dependencies installed correctly
- [ ] Configuration file created and valid
- [ ] Secrets configured securely
- [ ] Test run completed successfully
- [ ] Production run completed successfully
- [ ] Reports generated in all formats
- [ ] Scheduled execution configured (if applicable)
- [ ] Logging configured and working
- [ ] Monitoring set up
- [ ] Documentation accessible

8.2 Health Check

```bash
# Run health check
cd /opt/project-reports
source venv/bin/activate
source .env

# Check system health
python -c "
import sys
import httpx
import yaml
import jinja2
from pathlib import Path

print('✅ Python version:', sys.version.split()[0])
print('✅ Dependencies installed')
print('✅ GITHUB_TOKEN:', 'Set' if 'GITHUB_TOKEN' in os.environ else 'NOT SET')
print('✅ Installation: /opt/project-reports')
"
```

---

## GitHub Actions Deployment

### Step 1: Repository Setup

1.1 Fork or Use Repository

```bash
# If you haven't already, fork the repository
# Or use it directly in your organization's repo
```text

1.2 Enable Actions

1. Go to your repository on GitHub
2. Click **Settings** → **Actions** → **General**
3. Under **Actions permissions**, select:
   - "Allow all actions and reusable workflows"
4. Click **Save**

### Step 2: Configure Secrets

2.1 Add Repository Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add the following secrets:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `GITHUB_TOKEN` | Automatic (GitHub provides) | Yes |
| `GERRIT_USERNAME` | Your Gerrit username | If using Gerrit |
| `GERRIT_PASSWORD` | Your Gerrit password/token | If using Gerrit |
| `JENKINS_USERNAME` | Your Jenkins username | If using Jenkins |
| `JENKINS_TOKEN` | Your Jenkins API token | If using Jenkins |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | Optional |

**Note:** `GITHUB_TOKEN` is automatically available in GitHub Actions.

2.2 Verify Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Verify all required secrets are listed
3. Secrets cannot be viewed after creation (security feature)

### Step 3: Create Workflow File

3.1 Create Workflow Directory

```bash
# In your local clone
mkdir -p .github/workflows
```

3.2 Create Reporting Workflow

Create file `.github/workflows/generate-reports.yaml`:

```yaml
# .github/workflows/generate-reports.yaml
name: Generate Repository Reports

on:
  # Schedule: Daily at 2 AM UTC
  schedule:
    - cron: '0 2 * * *'

  # Manual trigger
  workflow_dispatch:
    inputs:
      project:
        description: 'Project name'
        required: false
        default: 'PRODUCTION'
      workers:
        description: 'Number of workers'
        required: false
        default: '8'

  # On push to main (optional)
  # push:
  #   branches: [ main ]

# Limit concurrency
concurrency:
  group: report-generation
  cancel-in-progress: false

# Required permissions
permissions:
  contents: write  # For uploading artifacts
  actions: read

jobs:
  generate-reports:
    name: Generate Reports
    runs-on: ubuntu-latest
    timeout-minutes: 60

    steps:
      - name: Harden Runner
        uses: step-security/harden-runner@v2
        with:
          egress-policy: audit

      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for git operations

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          uv sync  # Recommended
# or: pip install .

      - name: Clone repositories
        run: |
          # Clone your repositories to analyze
          mkdir -p repos
          cd repos

          # Example: Clone specific repositories
          # git clone https://github.com/org/repo1.git
          # git clone https://github.com/org/repo2.git

          # Or use API to discover repos
          # (Add your repository discovery logic here)

      - name: Generate reports
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GERRIT_USERNAME: ${{ secrets.GERRIT_USERNAME }}
          GERRIT_PASSWORD: ${{ secrets.GERRIT_PASSWORD }}
          PROJECT: ${{ github.event.inputs.project || 'PRODUCTION' }}
          WORKERS: ${{ github.event.inputs.workers || '8' }}
        run: |
          reporting-tool generate \
            --project "$PROJECT" \
            --repos-path repos \
            --workers "$WORKERS" \
            --output-format all

      - name: Upload reports as artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: reports-${{ github.run_number }}
          path: |
            *-report.txt
            *-report.html
            *-report.json
          retention-days: 30

      - name: Upload to release (optional)
        if: success() && github.event_name == 'schedule'
        uses: softprops/action-gh-release@v1
        with:
          tag_name: report-${{ github.run_number }}
          files: |
            *-report.txt
            *-report.html
            *-report.json

      - name: Notify on failure
        if: failure()
        run: |
          # Send notification (Slack, email, etc.)
          echo "Report generation failed"
          # curl -X POST -H 'Content-type: application/json' \
          #   --data '{"text":"Report generation failed"}' \
          #   ${{ secrets.SLACK_WEBHOOK_URL }}
```text

3.3 Commit and Push Workflow

```bash
git add .github/workflows/generate-reports.yaml
git commit -m "Add automated report generation workflow"
git push origin main
```

### Step 4: Configure Workflow Variables

4.1 Set Repository Variables (Optional)

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **Variables** tab
3. Click **New repository variable**
4. Add configuration variables:

| Variable Name | Value | Purpose |
|---------------|-------|---------|
| `REPOS_PATH` | `repos` | Repository path |
| `OUTPUT_FORMAT` | `all` | Output format |
| `DEFAULT_WORKERS` | `8` | Worker count |

### Step 5: Test Workflow

5.1 Manual Trigger

1. Go to **Actions** tab
2. Click **Generate Repository Reports** workflow
3. Click **Run workflow** dropdown
4. Select branch: `main`
5. (Optional) Override inputs:
   - Project: `TEST`
   - Workers: `4`
6. Click **Run workflow**

5.2 Monitor Execution

1. Click on the running workflow
2. Click on the job: **Generate Reports**
3. Watch real-time logs
4. Check each step for errors

5.3 Download Artifacts

1. Once complete, scroll to **Artifacts** section
2. Download `reports-{run_number}`
3. Extract and review reports

### Step 6: Schedule Verification

6.1 Verify Schedule

- Workflow should run daily at 2 AM UTC (per cron schedule)
- Check **Actions** tab for scheduled runs
- First scheduled run: Next day at 2 AM UTC

6.2 Adjust Schedule (If Needed)

Edit `.github/workflows/generate-reports.yaml`:

```yaml
schedule:
  # Daily at 2 AM UTC
  - cron: '0 2 * * *'

  # Weekly on Monday at 2 AM UTC
  # - cron: '0 2 * * 1'

  # Twice daily at 2 AM and 2 PM UTC
  # - cron: '0 2,14 * * *'
```text

Commit and push changes.

### Step 7: Deployment Verification

7.1 Verification Checklist

- [ ] Repository has Actions enabled
- [ ] All required secrets configured
- [ ] Workflow file created and committed
- [ ] Manual workflow trigger successful
- [ ] Reports generated correctly
- [ ] Artifacts uploaded successfully
- [ ] Schedule configured (if applicable)
- [ ] Notifications working (if configured)

7.2 Post-Deployment Monitoring

- Monitor workflow runs in **Actions** tab
- Review artifacts after each run
- Check for failures or warnings
- Validate report content

---

## Configuration Management

### Configuration Files

Directory Structure:

```

config/
├── template.config          # Base template
├── PRODUCTION.yaml          # Production config
├── STAGING.yaml             # Staging config (optional)
├── development.yaml         # Development config (optional)
└── examples/
    ├── simple.yaml          # Simple example
    └── advanced.yaml        # Advanced example

```text

### Configuration Priority

Priority Order (highest to lowest):

1. **Command-line arguments**

   ```bash
   --project PROD --workers 8
   ```

2. **Environment variables**

   ```bash
   export GITHUB_TOKEN="ghp_xxx"
   export WORKERS=8
   ```

3. **Configuration file**

   ```yaml
   # config/PRODUCTION.yaml
   workers: 8
   ```

4. **Template defaults**

   ```yaml
   # config/template.config
   workers: 4  # fallback default
   ```

### Configuration Best Practices

1. Use Environment Variables for Secrets

✅ **Good:**

```yaml
api:
  github:
    token: ${GITHUB_TOKEN}
```

❌ **Bad:**

```yaml
api:
  github:
    token: ghp_hardcoded_token_here
```text

2. Document All Settings

```yaml
# Number of parallel workers (1-32)
# Recommended: 1-2 per CPU core
# Higher values = faster processing but more memory
workers: 8
```

3. Use Environment-Specific Configs

```bash
# Production
reporting-tool generate --config config/PRODUCTION.yaml

# Staging
reporting-tool generate --config config/STAGING.yaml

# Development
reporting-tool generate --config config/development.yaml
```text

4. Version Control Configs (Without Secrets)

```bash
# Add to Git
git add config/PRODUCTION.yaml

# But exclude files with secrets
echo "config/*-secrets.yaml" >> .gitignore
echo ".env" >> .gitignore
```

### Configuration Validation

Validate Before Deployment:

```bash
# Dry run
reporting-tool generate \
  --config config/PRODUCTION.yaml \
  --dry-run

# Check for errors
echo $?  # Should be 0

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/PRODUCTION.yaml'))"
```text

---

## Secrets Management

### Security Principles

1. **Never commit secrets to Git**
2. **Use environment variables or secret managers**
3. **Rotate secrets regularly (90 days recommended)**
4. **Use least-privilege access**
5. **Audit secret access**

### Method 1: Environment Variables (Recommended for Local)

Setup:

```bash
# Create .env file (not in Git)
cat > .env << 'EOF'
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export GERRIT_USERNAME="user"
export GERRIT_PASSWORD="pass"
EOF

# Secure the file
chmod 600 .env

# Load secrets
source .env

# Verify (show first 10 chars only)
echo $GITHUB_TOKEN | cut -c1-10
```

Persistence:

```bash
# Option 1: Load manually each session
source /opt/project-reports/.env

# Option 2: Add to shell profile
echo "source /opt/project-reports/.env" >> ~/.bashrc

# Option 3: Use systemd environment file (see Appendix A)
```text

### Method 2: GitHub Actions Secrets (Recommended for GitHub)

Setup:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add secret:
   - Name: `GITHUB_TOKEN` (auto-provided)
   - Name: `GERRIT_USERNAME` (if needed)
   - Name: `GERRIT_PASSWORD` (if needed)
4. Click **Add secret**

Usage in Workflow:

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  GERRIT_USERNAME: ${{ secrets.GERRIT_USERNAME }}
  GERRIT_PASSWORD: ${{ secrets.GERRIT_PASSWORD }}
```

### Method 3: Secret Management Systems (Enterprise)

HashiCorp Vault:

```bash
# Install Vault CLI
# ...

# Read secret from Vault
export GITHUB_TOKEN=$(vault kv get -field=token secret/github)

# Use in script
reporting-tool generate ...
```text

AWS Secrets Manager:

```bash
# Install AWS CLI
# ...

# Read secret from AWS
export GITHUB_TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id github-token \
  --query SecretString \
  --output text)

# Use in script
reporting-tool generate ...
```

Azure Key Vault:

```bash
# Install Azure CLI
# ...

# Read secret from Azure
export GITHUB_TOKEN=$(az keyvault secret show \
  --vault-name my-vault \
  --name github-token \
  --query value \
  --output tsv)

# Use in script
reporting-tool generate ...
```text

### Secret Rotation

Rotation Schedule:

- GitHub tokens: Every 90 days
- Gerrit credentials: Per org policy
- Jenkins tokens: Per org policy

Rotation Process:

1. Generate new secret
2. Test new secret
3. Update secret in environment
4. Verify application works
5. Revoke old secret
6. Document rotation in log

Rotation Script Example:

```bash
#!/bin/bash
# rotate-github-token.sh

OLD_TOKEN="$GITHUB_TOKEN"
NEW_TOKEN="$1"

# Test new token
if curl -f -H "Authorization: token $NEW_TOKEN" https://api.github.com/user > /dev/null 2>&1; then
    echo "✅ New token valid"

    # Update .env file
    sed -i "s/$OLD_TOKEN/$NEW_TOKEN/" /opt/project-reports/.env

    # Reload
    source /opt/project-reports/.env

    echo "✅ Token rotated successfully"
    echo "⚠️  Revoke old token at: https://github.com/settings/tokens"
else
    echo "❌ New token invalid"
    exit 1
fi
```

---

## Initial Deployment

### Deployment Workflow

```mermaid
graph TD
    A[Pre-Deployment Checklist] --> B[Install & Configure]
    B --> C[Test with Small Dataset]
    C --> D{Tests Pass?}
    D -->|No| E[Troubleshoot & Fix]
    E --> C
    D -->|Yes| F[Test with Production Data]
    F --> G{Production Tests Pass?}
    G -->|No| E
    G -->|Yes| H[Enable Monitoring]
    H --> I[Schedule Automation]
    I --> J[Deployment Complete]
```text

### Deployment Day Checklist

Morning of Deployment (T-4 hours):

- [ ] Review deployment plan
- [ ] Verify all prerequisites met
- [ ] Backup existing configs (if upgrading)
- [ ] Notify stakeholders: "Deployment starting in 4 hours"
- [ ] Ensure rollback plan ready

Deployment Start (T-0):

- [ ] Announce: "Deployment in progress"
- [ ] Disable existing cron jobs (if upgrading)
- [ ] Take snapshot/backup

Deployment Execution (T+0 to T+60min):

- [ ] Install/upgrade system
- [ ] Configure settings
- [ ] Set up secrets
- [ ] Run smoke tests
- [ ] Verify all checks pass

Deployment Verification (T+60 to T+90min):

- [ ] Run production test
- [ ] Verify reports generated
- [ ] Check monitoring
- [ ] Enable scheduled jobs

Deployment Complete (T+90min):

- [ ] Announce: "Deployment complete"
- [ ] Monitor for 24-48 hours
- [ ] Document any issues
- [ ] Update team on status

### Communication Template

Pre-Deployment Notice:

```

Subject: Repository Reporting System Deployment - [DATE] at [TIME]

Team,

We will be deploying the Repository Reporting System on [DATE] at [TIME].

Expected Duration: 2-4 hours
Deployment Window: [START TIME] - [END TIME]
Impact: None expected (new system or upgrade)

Pre-Deployment:

- All prerequisites verified
- Rollback plan prepared
- Testing completed successfully

During Deployment:

- System will be deployed and configured
- Smoke tests will be run
- Monitoring will be enabled

Post-Deployment:

- Reports will be generated on schedule
- Monitoring active for 48 hours
- Support available via #project-reports Slack channel

Questions? Contact: [DEPLOYMENT LEAD]

```text

Post-Deployment Notice:

```

Subject: Repository Reporting System Deployment - COMPLETE

Team,

The Repository Reporting System deployment is complete.

Status: ✅ SUCCESS
Completion Time: [TIME]
Reports Generated: [COUNT]
All Tests: PASSED

Next Steps:

- Monitoring active for 48 hours
- First scheduled report: [DATE/TIME]
- Access reports at: [LINK]

Issues? Contact: [DEPLOYMENT LEAD] or #project-reports

```text

---

## Smoke Testing

### Purpose

Smoke tests verify basic functionality after deployment:

- System installs correctly
- Dependencies work
- Configuration valid
- Reports can be generated
- No critical errors

### Smoke Test Suite

Test 1: Installation Verification

```bash
#!/bin/bash
# smoke-test-1-installation.sh

echo "=== Smoke Test 1: Installation ==="

# Check Python version
python --version || exit 1
echo "✅ Python available"

# Check dependencies
python -c "import httpx, yaml, jinja2" || exit 1
echo "✅ Dependencies installed"

# Check scripts
test -f generate_reports.py || exit 1
echo "✅ Main script present"

echo "✅ Installation verification PASSED"
```

Test 2: Configuration Validation

```bash
#!/bin/bash
# smoke-test-2-configuration.sh

echo "=== Smoke Test 2: Configuration ==="

# Check config file exists
test -f config/PRODUCTION.yaml || exit 1
echo "✅ Configuration file exists"

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('config/PRODUCTION.yaml'))" || exit 1
echo "✅ Configuration valid YAML"

# Dry run
reporting-tool generate --config config/PRODUCTION.yaml --dry-run || exit 1
echo "✅ Configuration accepted"

echo "✅ Configuration validation PASSED"
```text

Test 3: Secrets Verification

```bash
#!/bin/bash
# smoke-test-3-secrets.sh

echo "=== Smoke Test 3: Secrets ==="

# Check GitHub token
test -n "$GITHUB_TOKEN" || exit 1
echo "✅ GITHUB_TOKEN set"

# Test GitHub API access
curl -f -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user > /dev/null || exit 1
echo "✅ GitHub API accessible"

# Check rate limit
RATE_LIMIT=$(curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit | jq -r '.rate.limit')
test "$RATE_LIMIT" -eq 5000 || exit 1
echo "✅ GitHub token authenticated (5000 req/hr)"

echo "✅ Secrets verification PASSED"
```

Test 4: Small Dataset Test

```bash
#!/bin/bash
# smoke-test-4-small-dataset.sh

echo "=== Smoke Test 4: Small Dataset ==="

# Create test directory
mkdir -p /tmp/smoke-test
cd /tmp/smoke-test

# Clone single test repo
git clone --depth 1 https://github.com/octocat/Hello-World.git || exit 1
echo "✅ Test repository cloned"

# Generate report
cd /opt/project-reports
reporting-tool generate \
  --project SMOKE_TEST \
  --repos-path /tmp/smoke-test \
  --output-format text \
  --workers 1 || exit 1
echo "✅ Report generated"

# Verify output
test -f SMOKE_TEST-report.txt || exit 1
grep -q "Hello-World" SMOKE_TEST-report.txt || exit 1
echo "✅ Report contains expected data"

# Cleanup
rm -rf /tmp/smoke-test SMOKE_TEST-report.txt

echo "✅ Small dataset test PASSED"
```text

Test 5: Full Feature Test

```bash
#!/bin/bash
# smoke-test-5-full-features.sh

echo "=== Smoke Test 5: Full Features ==="

# Generate all formats
reporting-tool generate \
  --project FEATURE_TEST \
  --repos-path /tmp/smoke-test \
  --output-format all \
  --workers 4 || exit 1
echo "✅ All formats generated"

# Verify all outputs
test -f FEATURE_TEST-report.txt || exit 1
test -f FEATURE_TEST-report.html || exit 1
test -f FEATURE_TEST-report.json || exit 1
echo "✅ All output files present"

# Verify JSON valid
python -c "import json; json.load(open('FEATURE_TEST-report.json'))" || exit 1
echo "✅ JSON output valid"

# Verify HTML valid (basic check)
grep -q "<html>" FEATURE_TEST-report.html || exit 1
echo "✅ HTML output valid"

# Cleanup
rm -f FEATURE_TEST-report.*

echo "✅ Full feature test PASSED"
```

### Running Smoke Tests

Run All Tests:

```bash
#!/bin/bash
# run-all-smoke-tests.sh

set -e

# Change to project directory
cd /opt/project-reports
source venv/bin/activate
source .env

# Run all smoke tests
./smoke-test-1-installation.sh
./smoke-test-2-configuration.sh
./smoke-test-3-secrets.sh
./smoke-test-4-small-dataset.sh
./smoke-test-5-full-features.sh

echo ""
echo "========================================="
echo "✅ ALL SMOKE TESTS PASSED"
echo "========================================="
```text

Expected Output:

```

=== Smoke Test 1: Installation ===
✅ Python available
✅ Dependencies installed
✅ Main script present
✅ Installation verification PASSED

=== Smoke Test 2: Configuration ===
✅ Configuration file exists
✅ Configuration valid YAML
✅ Configuration accepted
✅ Configuration validation PASSED

=== Smoke Test 3: Secrets ===
✅ GITHUB_TOKEN set
✅ GitHub API accessible
✅ GitHub token authenticated (5000 req/hr)
✅ Secrets verification PASSED

=== Smoke Test 4: Small Dataset ===
✅ Test repository cloned
✅ Report generated
✅ Report contains expected data
✅ Small dataset test PASSED

=== Smoke Test 5: Full Features ===
✅ All formats generated
✅ All output files present
✅ JSON output valid
✅ HTML output valid
✅ Full feature test PASSED

=========================================
✅ ALL SMOKE TESTS PASSED
=========================================

```text

### Smoke Test Failure Handling

If Any Test Fails:

1. **Stop deployment immediately**
2. **Review error messages**
3. **Check logs for details**
4. **Fix the issue**
5. **Re-run smoke tests**
6. **If fix not immediately available: Rollback**

---

## Monitoring Setup

### Logging Configuration

1. Structured Logging

```yaml
# config/PRODUCTION.yaml
logging:
  level: INFO
  format: structured
  timestamps: true
  output: both  # console and file
  file: logs/production.log
  rotation:
    max_size: 100MB
    max_age: 30  # days
    compress: true
```

2. Log Levels by Environment

| Environment | Log Level | Rationale |
|-------------|-----------|-----------|
| Production | INFO | Normal operations only |
| Staging | DEBUG | Detailed diagnostics |
| Development | DEBUG | Full debugging |

3. Log Analysis

```bash
# View recent logs
tail -f /opt/project-reports/logs/production.log

# Search for errors
grep -i "error\|exception" logs/production.log

# Count errors by type
grep "ERROR" logs/production.log | cut -d: -f3 | sort | uniq -c

# View specific time range
grep "2025-01-29" logs/production.log
```text

### Metrics Collection

1. API Statistics

Automatically tracked and reported:

```

API Statistics:
┌──────────┬─────────┬─────────┬─────────┬─────────┬──────────┐
│ API      │ Calls   │ Success │ Errors  │ Avg(ms) │ P95(ms)  │
├──────────┼─────────┼─────────┼─────────┼─────────┼──────────┤
│ GitHub   │ 1,245   │ 99.8%   │ 0.2%    │ 180     │ 420      │
│ Gerrit   │ 856     │ 99.9%   │ 0.1%    │ 95      │ 320      │
│ Jenkins  │ 342     │ 99.5%   │ 0.5%    │ 240     │ 680      │
└──────────┴─────────┴─────────┴─────────┴─────────┴──────────┘

```text

2. Performance Metrics

Track over time:

- Execution duration
- Repositories processed per second
- Memory usage (peak)
- CPU utilization
- Cache hit rate
- Disk I/O

3. Business Metrics

Track for reporting:

- Total repositories processed
- Reports generated
- Features detected
- Contributors counted
- Organizations discovered

### Dashboard Setup (GitHub Actions)

GitHub Actions automatically provides:

1. **Workflow Status Dashboard**
   - Success/failure rates
   - Execution duration trends
   - Resource usage

2. **API Statistics Summary**
   - Written to GITHUB_STEP_SUMMARY
   - Visible in Actions UI
   - Downloadable as artifact

3. **Artifacts**
   - Generated reports
   - Logs
   - Metrics (JSON format)

Accessing Dashboard:

1. Go to **Actions** tab
2. Click on workflow run
3. View summary and metrics
4. Download artifacts for analysis

### Alert Configuration

1. Failure Alerts (GitHub Actions)

```yaml
# In workflow file
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Report generation failed'
    webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
```

2. Performance Degradation Alerts

```bash
# In wrapper script
DURATION=$(grep "Duration:" logs/latest.log | awk '{print $2}')
THRESHOLD=600  # 10 minutes

if [ "$DURATION" -gt "$THRESHOLD" ]; then
    echo "WARNING: Execution took ${DURATION}s (threshold: ${THRESHOLD}s)"
    # Send alert
fi
```text

3. Error Rate Alerts

```bash
# Check error rate
ERRORS=$(grep -c "ERROR" logs/latest.log)
if [ "$ERRORS" -gt 10 ]; then
    echo "CRITICAL: $ERRORS errors found (threshold: 10)"
    # Send alert
fi
```

### Monitoring Best Practices

1. **Baseline Metrics:** Record normal performance during first week
2. **Set Thresholds:** Alert on >20% deviation from baseline
3. **Regular Review:** Check metrics weekly
4. **Incident Response:** Have runbook for each alert type
5. **Continuous Improvement:** Adjust thresholds based on experience

---

## Post-Deployment Validation

### Validation Timeline

Immediate (Day 1):

- Verify deployment completed successfully
- Run smoke tests
- Check monitoring dashboards
- Review initial report generation

Short-term (Week 1):

- Monitor daily executions
- Verify scheduled runs working
- Check report quality
- Collect user feedback

Long-term (Month 1):

- Analyze performance trends
- Optimize configuration
- Address any recurring issues
- Plan improvements

### Day 1 Checklist

Within 1 Hour:

- [ ] Smoke tests passed
- [ ] Initial report generated successfully
- [ ] All output formats created
- [ ] No errors in logs
- [ ] Monitoring dashboards showing data

Within 24 Hours:

- [ ] First scheduled run completed (if applicable)
- [ ] Reports accessible to users
- [ ] No alerts triggered
- [ ] Performance within expected range
- [ ] Stakeholders notified of success

### Week 1 Checklist

Daily Checks:

- [ ] Scheduled runs completing successfully
- [ ] Reports generated correctly
- [ ] No error rate increase
- [ ] Performance stable
- [ ] Resource usage normal

Weekly Review:

- [ ] Review all execution logs
- [ ] Analyze performance metrics
- [ ] Check for any patterns/issues
- [ ] User feedback collected
- [ ] Documentation gaps identified

### Month 1 Checklist

Performance Review:

- [ ] Execution time trend analyzed
- [ ] Resource usage optimized
- [ ] Cache hit rate reviewed
- [ ] API usage patterns understood
- [ ] Bottlenecks identified

Reliability Review:

- [ ] Error rates acceptable (<1%)
- [ ] No recurring failures
- [ ] Recovery mechanisms tested
- [ ] Monitoring effective
- [ ] Alerts actionable

User Experience Review:

- [ ] Reports meeting user needs
- [ ] Documentation helpful
- [ ] Support requests manageable
- [ ] Feature requests collected
- [ ] Training needs identified

### Success Criteria

Deployment is considered successful if:

✅ **All smoke tests pass**
✅ **Reports generated correctly**
✅ **Error rate <1%**
✅ **Performance meets SLOs**
✅ **Scheduled executions working**
✅ **Monitoring functional**
✅ **No critical issues**
✅ **User feedback positive**

If criteria not met:

- Investigate issues
- Fix if possible
- Consider rollback if severe
- Document lessons learned

---

## Rollback Procedures

### When to Rollback

Rollback Triggers:

🔴 **Immediate Rollback Required:**

- Data corruption or loss
- Security vulnerability introduced
- System-wide failure (>50% error rate)
- Critical functionality broken
- Compliance violation

🟡 **Rollback Considered:**

- Performance degradation >2x
- Error rate >10%
- Unable to generate reports
- Recurring failures

### Rollback Methods

Method 1: Git-Based Rollback (Local)

**RTO:** <5 minutes

```bash
# 1. Identify last known good commit
cd /opt/project-reports
git log --oneline -10

# 2. Revert to previous version
git revert <commit-hash>
# Or: git reset --hard <commit-hash>

# 3. Reinstall dependencies
source venv/bin/activate
uv sync  # Recommended
# or: pip install .

# 4. Verify
reporting-tool --version
./run-all-smoke-tests.sh

# 5. Restart scheduled jobs
crontab -l  # Verify cron entries
```text

Method 2: Configuration Rollback

**RTO:** <2 minutes

```bash
# 1. Restore config from backup
cp config/PRODUCTION.yaml.backup config/PRODUCTION.yaml

# 2. Verify configuration
reporting-tool generate --config config/PRODUCTION.yaml --dry-run

# 3. Test
reporting-tool generate --project TEST --repos-path /tmp/test
```

Method 3: GitHub Actions Rollback

**RTO:** <10 minutes

Option A: Re-run Previous Workflow

1. Go to **Actions** tab
2. Find last successful run
3. Click **Re-run jobs** → **Re-run all jobs**

Option B: Pin to Previous Version

1. Edit `.github/workflows/generate-reports.yaml`
2. Change checkout step:

   ```yaml
   - uses: actions/checkout@v4
     with:
       ref: v1.0.0  # Pin to specific version
   ```

3. Commit and push

Option C: Disable Workflow

1. Go to **Actions** tab
2. Click on workflow
3. Click **···** menu → **Disable workflow**

### Rollback Procedure

Step-by-Step Rollback:

1. **Announce Rollback**

   ```text
   Subject: ROLLBACK IN PROGRESS - Repository Reporting System

   Team, we are initiating a rollback due to [REASON].
   Expected completion: [TIME]
   Impact: [DESCRIPTION]
   ```

2. **Stop Current Processes**

   ```bash
   # Stop scheduled jobs
   crontab -r  # Remove all cron jobs
   # Or disable specific job

   # Kill running processes
   pkill -f generate_reports.py
   ```

3. **Execute Rollback**

   ```bash
   # Use appropriate method (see above)
   # Git-based, config, or GitHub Actions
   ```

4. **Verify Rollback**

   ```bash
   # Run smoke tests
   ./run-all-smoke-tests.sh

   # Check version
   reporting-tool --version

   # Test report generation
   reporting-tool generate --project TEST --repos-path /tmp/test
   ```

5. **Restore Services**

   ```bash
   # Re-enable cron jobs (if applicable)
   crontab -e
   # Add back cron entries

   # Or restart systemd service
   sudo systemctl restart project-reports
   ```

6. **Monitor**

   ```bash
   # Watch logs
   tail -f logs/production.log

   # Check for errors
   grep -i error logs/production.log
   ```

7. **Announce Completion**

   ```text
   Subject: ROLLBACK COMPLETE - Repository Reporting System

   Rollback completed successfully.
   System restored to previous version.
   All services operational.

   Next steps:
   - Root cause analysis
   - Fix planning
   - Testing before re-deployment
   ```

### Post-Rollback Actions

Immediate (within 1 hour):

- [ ] Confirm system stable
- [ ] Verify reports generating
- [ ] Check monitoring
- [ ] Update stakeholders

Short-term (within 24 hours):

- [ ] Root cause analysis
- [ ] Document incident
- [ ] Create bug fix plan
- [ ] Update tests to catch issue

Long-term (within 1 week):

- [ ] Implement fixes
- [ ] Enhanced testing
- [ ] Update runbooks
- [ ] Post-mortem meeting
- [ ] Plan re-deployment

### Rollback Testing

Test rollback procedures quarterly:

```bash
# Rollback test script
#!/bin/bash
# test-rollback.sh

echo "=== Rollback Test (Dry Run) ==="

# Simulate rollback
git log --oneline -5
echo "Would rollback to: $(git log --oneline -1)"

# Test restore from backup
test -f config/PRODUCTION.yaml.backup
echo "✅ Backup exists"

# Verify smoke tests work
./run-all-smoke-tests.sh

echo "✅ Rollback test successful"
```text

---

## Troubleshooting

### Common Deployment Issues

Issue 1: Installation Fails

Symptoms:

```

ERROR: Could not install packages

```text

Diagnosis:

```bash
# Check Python version
python --version

# Check pip version
pip --version

# Check network connectivity
ping pypi.org
```

Solution:

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install with verbose output
uv sync  # Recommended
# or: pip install . -v

# Or install dependencies individually
pip install httpx
pip install PyYAML
pip install Jinja2
```text

Issue 2: Configuration Invalid

Symptoms:

```

❌ Error: Invalid YAML syntax

```text

Diagnosis:

```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('config/PRODUCTION.yaml'))"

# Check for tabs (YAML requires spaces)
grep -P '\t' config/PRODUCTION.yaml
```

Solution:

```bash
# Fix YAML syntax
# Common issues:
# - Tabs instead of spaces
# - Incorrect indentation
# - Missing quotes around special chars

# Use yamllint for detailed validation
pip install yamllint
yamllint config/PRODUCTION.yaml
```text

Issue 3: Secrets Not Found

Symptoms:

```

❌ Error: GITHUB_TOKEN not found

```text

Diagnosis:

```bash
# Check if secret is set
echo $GITHUB_TOKEN

# Check if .env file exists
test -f .env && echo "Found" || echo "Missing"

# Check file permissions
ls -la .env
```

Solution:

```bash
# Load secrets
source .env

# Or set directly
export GITHUB_TOKEN="ghp_xxx"

# Verify
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```text

Issue 4: Permission Denied

Symptoms:

```

❌ Error: Permission denied: '/data/reports'

```text

Diagnosis:

```bash
# Check directory permissions
ls -ld /data/reports

# Check ownership
stat /data/reports
```

Solution:

```bash
# Fix permissions
sudo chown -R $USER:$USER /data/reports
chmod 755 /data/reports

# Or use different directory
mkdir -p ~/reports
reporting-tool generate --output-path ~/reports
```text

Issue 5: GitHub API Rate Limit

Symptoms:

```

⚠️  Warning: GitHub API rate limit exceeded

```text

Diagnosis:

```bash
# Check rate limit
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit

# Output shows:
# "remaining": 0
# "reset": 1706543600  # Unix timestamp
```

Solution:

```bash
# Wait for reset (shown in rate limit response)
# Or use caching to reduce API calls
reporting-tool generate --cache-enabled

# Or reduce workers
reporting-tool generate --workers 4

# Check when limit resets
date -d @$(curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit | jq '.rate.reset')
```text

Issue 6: Out of Memory

Symptoms:

```

Killed

# Or

MemoryError

```text

Diagnosis:

```bash
# Check memory usage
free -h

# Check system logs
dmesg | grep -i "out of memory"
```

Solution:

```bash
# Reduce workers
reporting-tool generate --workers 2

# Process in batches
reporting-tool generate --repos-path /data/repos/batch1
reporting-tool generate --repos-path /data/repos/batch2

# Or increase system memory
```text

Issue 7: GitHub Actions Workflow Fails

Symptoms:

- Workflow shows red X
- Job fails at specific step

Diagnosis:

1. Click on failed workflow run
2. Click on failed job
3. Expand failed step
4. Read error message

Solution:

```yaml
# Common fixes:

# 1. Missing secrets
# Go to Settings → Secrets → Add GITHUB_TOKEN

# 2. Timeout
timeout-minutes: 120  # Increase timeout

# 3. Checkout depth
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Full history

# 4. Python version
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'  # Specify exact version
```

### Diagnostic Commands

System Health:

```bash
# Check disk space
df -h

# Check memory
free -h

# Check CPU
top
# Or: htop

# Check network
ping github.com
curl -I https://api.github.com
```text

Application Health:

```bash
# Verify installation
reporting-tool --version

# Run dry-run
reporting-tool generate --config config/PRODUCTION.yaml --dry-run

# Check dependencies
pip list

# Test imports
python -c "import httpx, yaml, jinja2; print('OK')"
```

Configuration:

```bash
# Validate YAML
python -c "import yaml; print(yaml.safe_load(open('config/PRODUCTION.yaml')))"

# Check secrets
echo $GITHUB_TOKEN | cut -c1-10

# Test API access
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```text

### Getting Help

1. Check Documentation:

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [CLI_FAQ.md](CLI_FAQ.md)
- [ERROR_HANDLING_BEST_PRACTICES.md](ERROR_HANDLING_BEST_PRACTICES.md)

2. Search Issues:

- GitHub Issues: <https://github.com/lfit/project-reports/issues>
- Search for error message

3. Enable Debug Logging:

```bash
reporting-tool generate \
  --log-level DEBUG \
  --project TEST \
  2>&1 | tee debug.log
```

4. Contact Support:

- Slack: #project-reports
- Email: <project-reports@linuxfoundation.org>
- Create issue: <https://github.com/lfit/project-reports/issues/new>

Include in Support Request:

- Error message (full text)
- Configuration file (with secrets removed)
- Log output (relevant portions)
- Steps to reproduce
- System information (OS, Python version)

---

## Maintenance

### Regular Maintenance Tasks

Daily:

- [ ] Review execution logs
- [ ] Check for failures
- [ ] Monitor resource usage
- [ ] Verify reports generated

Weekly:

- [ ] Review error rates
- [ ] Check performance trends
- [ ] Update documentation as needed
- [ ] Review user feedback

Monthly:

- [ ] Update dependencies
- [ ] Review security advisories
- [ ] Rotate secrets (if applicable)
- [ ] Backup configurations
- [ ] Review and archive old logs

Quarterly:

- [ ] Rotate tokens/credentials
- [ ] Review and optimize performance
- [ ] Update documentation
- [ ] Test rollback procedures
- [ ] Disaster recovery drill

Annually:

- [ ] Comprehensive security audit
- [ ] Performance benchmark comparison
- [ ] Architecture review
- [ ] User satisfaction survey
- [ ] Capacity planning

### Updating Dependencies

Check for Updates:

```bash
# Check outdated packages
pip list --outdated

# Or use pip-check
pip install pip-check
pip-check
```text

Update Process:

```bash
# 1. Backup current environment
pip freeze > requirements-backup.txt

# 2. Update specific package
pip install --upgrade httpx

# 3. Test
./run-all-smoke-tests.sh

# 4. If issues, rollback
pip install -r requirements-backup.txt

# 5. If successful, update requirements.txt
pip freeze > requirements.txt
```

Security Updates:

```bash
# Check for vulnerabilities
pip install pip-audit
pip-audit

# Update vulnerable packages immediately
pip install --upgrade <package-name>

# Test thoroughly before deploying
```text

### Upgrading to New Version

Pre-Upgrade:

1. Review CHANGELOG.md
2. Read upgrade notes
3. Backup configurations
4. Test in staging environment
5. Plan rollback

Upgrade Process:

```bash
# 1. Backup
cp -r /opt/project-reports /opt/project-reports.backup
cp config/PRODUCTION.yaml config/PRODUCTION.yaml.backup

# 2. Pull latest code
cd /opt/project-reports
git fetch origin
git checkout v2.0.0  # Or: git pull origin main

# 3. Update dependencies
source venv/bin/activate
uv sync  # Recommended
# or: pip install .

# 4. Run smoke tests
./run-all-smoke-tests.sh

# 5. Test with real data
reporting-tool generate --project TEST --repos-path /tmp/test

# 6. If successful, deploy
# Restart cron/systemd as needed

# 7. Monitor closely for 24-48 hours
```

Post-Upgrade:

- Monitor execution logs
- Check performance metrics
- Verify reports quality
- Address any issues immediately
- Document changes

### Backup Strategy

What to Backup:

1. **Configurations** (critical)
   - `config/*.yaml`
   - `.env` (encrypted)
   - Custom templates

2. **Generated Reports** (important)
   - Latest reports
   - Historical reports (optional)

3. **Cache** (optional, regeneratable)
   - API response cache
   - Metadata cache

Backup Frequency:

- Configurations: On every change + daily
- Reports: After each generation
- Cache: Optional (can be regenerated)

Backup Script:

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/project-reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR/$TIMESTAMP"

# Backup configurations
cp -r config "$BACKUP_DIR/$TIMESTAMP/"

# Backup reports (last 7 days)
find . -name "*-report.*" -mtime -7 -exec cp {} "$BACKUP_DIR/$TIMESTAMP/" \;

# Compress
tar -czf "$BACKUP_DIR/backup-$TIMESTAMP.tar.gz" "$BACKUP_DIR/$TIMESTAMP"
rm -rf "$BACKUP_DIR/$TIMESTAMP"

# Cleanup old backups (keep 30 days)
find "$BACKUP_DIR" -name "backup-*.tar.gz" -mtime +30 -delete

echo "Backup complete: $BACKUP_DIR/backup-$TIMESTAMP.tar.gz"
```text

Restore from Backup:

```bash
# Extract backup
tar -xzf /backup/project-reports/backup-20250129_120000.tar.gz

# Restore configurations
cp -r backup-20250129_120000/config/* /opt/project-reports/config/

# Verify
reporting-tool generate --config config/PRODUCTION.yaml --dry-run
```

---

## Appendix

### Appendix A: systemd Service Configuration

**Service File:** `/etc/systemd/system/project-reports.service`

```ini
[Unit]
Description=Repository Reporting System
After=network.target

[Service]
Type=oneshot
User=project-reports
Group=project-reports
WorkingDirectory=/opt/project-reports
Environment="PATH=/opt/project-reports/venv/bin"
EnvironmentFile=/opt/project-reports/.env
ExecStart=/opt/project-reports/venv/bin/reporting-tool generate --project PRODUCTION --config config/PRODUCTION.yaml
StandardOutput=append:/opt/project-reports/logs/service.log
StandardError=append:/opt/project-reports/logs/service.log
TimeoutSec=3600

[Install]
WantedBy=multi-user.target
```text

**Timer File:** `/etc/systemd/system/project-reports.timer`

```ini
[Unit]
Description=Repository Reporting System Timer
Requires=project-reports.service

[Timer]
# Daily at 2 AM
OnCalendar=daily
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Setup:

```bash
# Create service user
sudo useradd -r -s /bin/false project-reports
sudo chown -R project-reports:project-reports /opt/project-reports

# Install service files
sudo cp project-reports.service /etc/systemd/system/
sudo cp project-reports.timer /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start timer
sudo systemctl enable project-reports.timer
sudo systemctl start project-reports.timer

# Check status
sudo systemctl status project-reports.timer
sudo systemctl list-timers
```text

### Appendix B: Docker Deployment (Future)

**Dockerfile** (planned for future release):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set up user
RUN useradd -m -u 1000 reporter && chown -R reporter:reporter /app
USER reporter

# Default command
ENTRYPOINT ["python", "generate_reports.py"]
CMD ["--help"]
```

**Docker Compose** (planned):

```yaml
version: '3.8'

services:
  reporter:
    image: lfit/project-reports:latest
    volumes:
      - ./repos:/repos:ro
      - ./config:/app/config:ro
      - ./output:/output
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GERRIT_USERNAME=${GERRIT_USERNAME}
      - GERRIT_PASSWORD=${GERRIT_PASSWORD}
    command: >
      --project PRODUCTION
      --repos-path /repos
      --output-path /output
      --config /app/config/PRODUCTION.yaml
```text

### Appendix C: Monitoring Dashboards

**Grafana Dashboard** (future):

```json
{
  "dashboard": {
    "title": "Repository Reporting System",
    "panels": [
      {
        "title": "Execution Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "report_generation_duration_seconds"
          }
        ]
      },
      {
        "title": "API Call Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(api_calls_total[5m])"
          }
        ]
      }
    ]
  }
}
```

### Appendix D: Performance Tuning

Optimal Worker Count:

```python
import os
import multiprocessing

# Recommended: 1-2 workers per CPU core
cpu_count = multiprocessing.cpu_count()
optimal_workers = min(cpu_count * 2, 16)  # Cap at 16
print(f"Recommended workers: {optimal_workers}")
```text

Memory Optimization:

```bash
# For systems with limited memory
export WORKERS=4
export CACHE_ENABLED=false  # Disable caching if memory-constrained

# Or process in batches
reporting-tool generate --repos-path /data/repos/batch1
reporting-tool generate --repos-path /data/repos/batch2
```

Disk I/O Optimization:

```yaml
# config/PRODUCTION.yaml
cache:
  enabled: true
  location: /fast-disk/cache  # Use SSD if available
  compression: true  # Reduce disk usage
```text

### Appendix E: Troubleshooting Decision Tree

```

Error Occurred?
│
├─ Installation Issue?
│  ├─ Dependencies fail → Check Python version, upgrade pip
│  ├─ Permission denied → Fix directory permissions
│  └─ Network error → Check connectivity, proxy settings
│
├─ Configuration Issue?
│  ├─ YAML syntax error → Validate YAML, check indentation
│  ├─ Missing field → Review template.config
│  └─ Invalid value → Check CLI_REFERENCE.md for valid values
│
├─ Authentication Issue?
│  ├─ Token not found → Set GITHUB_TOKEN environment variable
│  ├─ Token invalid → Generate new token, check scopes
│  └─ Rate limit → Wait for reset or enable caching
│
├─ Runtime Issue?
│  ├─ Out of memory → Reduce workers, process in batches
│  ├─ Timeout → Increase workers, enable caching
│  └─ Permission error → Check file/directory permissions
│
└─ Output Issue?
   ├─ Report empty → Check repository path, verify data
   ├─ Format error → Validate output format setting
   └─ Missing sections → Check include settings in config

```text

### Appendix F: Security Checklist

Pre-Deployment Security Review:

- [ ] No hardcoded credentials in code
- [ ] Secrets stored securely (env vars or secret manager)
- [ ] `.gitignore` excludes secret files
- [ ] File permissions secure (600 for secret files)
- [ ] HTTPS enforced for all API calls
- [ ] Certificate validation enabled
- [ ] Input validation implemented
- [ ] No sensitive data in logs
- [ ] Dependencies scanned for vulnerabilities
- [ ] REUSE compliance verified (100%)
- [ ] License compliance checked
- [ ] Security advisories reviewed

Post-Deployment Security Monitoring:

- [ ] Regular dependency scans (weekly)
- [ ] Secret rotation schedule (90 days)
- [ ] Access log review (monthly)
- [ ] Security patch application (as available)
- [ ] Vulnerability assessment (quarterly)
- [ ] Security audit (annually)

### Appendix G: Contact Information

Support Channels:

- **Documentation:** <https://github.com/lfit/project-reports/tree/main/docs>
- **Issues:** <https://github.com/lfit/project-reports/issues>
- **Discussions:** <https://github.com/lfit/project-reports/discussions>
- **Slack:** #project-reports (internal)
- **Email:** <project-reports@linuxfoundation.org>

Escalation Path:

1. **L1 Support:** Team member (check docs, search issues)
2. **L2 Support:** Maintainer (technical investigation)
3. **L3 Support:** Core team (deep expertise)
4. **L4 Support:** Vendor/upstream (GitHub, Python, etc.)

On-Call:

- **Primary:** Check team roster
- **Secondary:** Check team roster
- **Escalation:** Technical lead

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-01-29 | Repository Reporting System Team | Initial production deployment guide |

---

## Feedback & Improvements

This deployment guide is a living document. If you find issues, have suggestions, or discover better practices, please:

1. **Create an issue:** <https://github.com/lfit/project-reports/issues/new>
2. **Submit a PR:** Update this guide and submit for review
3. **Share in Slack:** #project-reports channel

Questions about this guide?
See [CLI_FAQ.md](CLI_FAQ.md) or create an issue.

---

End of Production Deployment Guide

**Status:** PRODUCTION READY
**Version:** 1.0.0
**Last Updated:** 2025-01-29
**Next Review:** 2025-04-29 (quarterly)
