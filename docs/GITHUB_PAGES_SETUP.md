<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# GitHub Pages Reporting System Setup Guide

This guide covers the complete setup and migration to the new GitHub Pages-based reporting system.

---

## 🎯 Overview

The new reporting system publishes reports directly to GitHub Pages on this repository, eliminating the need for a separate `gerrit-reports` repository and the associated `GERRIT_REPORTS_PAT_TOKEN`.

### Key Changes

| Aspect | Old System | New System |
| ------- | ------- | ------- |
| **Deployment Target** | Separate `gerrit-reports` repo | GitHub Pages on same repo |
| **Branch** | `main` in external repo | `gh-pages` branch |
| **Authentication** | `GERRIT_REPORTS_PAT_TOKEN` | Built-in `GITHUB_TOKEN` |
| **Production Reports** | Pushed to external repo | `/production/` on Pages |
| **Preview Reports** | Not available | `/pr-preview/<pr-number>/` |
| **Workflows** | Single `reporting.yaml` | Separate production & PR workflows |

---

## 📋 Prerequisites

### Required Secrets

1. **CLASSIC_READ_ONLY_PAT_TOKEN** (Required)
   - Used for GitHub API queries (workflow status, repository info)
   - Permissions needed: `repo` (read-only), `workflow` (read)
   - Create at: <https://github.com/settings/tokens>

2. **LF_GERRIT_INFO_MASTER_SSH_KEY** (Optional)
   - SSH key for cloning `info-master` repository
   - Falls back to HTTPS if not provided
   - Format: Private SSH key

### Required Variables

1. **PROJECTS_JSON**
   - Array of project configurations
   - Format:

     ```json
     [
       {
         "project": "Project Name",
         "slug": "project-name",
         "gerrit": "gerrit.example.org",
         "jenkins": "jenkins.example.org",
         "github": "github-org-name"
       }
     ]
     ```

     **Required fields:**
     - `project`: Full project name
     - `slug`: Short identifier for artifact naming (lowercase, no spaces)
     - `gerrit`: Gerrit server hostname

---

## 🚀 Initial Setup

### Step 1: Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Under **Source**, select:
   - **Deploy from a branch**
   - Branch: `gh-pages`
   - Folder: `/ (root)`
3. Click **Save**

### Step 2: Create `gh-pages` Branch

```bash
# Create an orphan branch (no history)
git checkout --orphan gh-pages

# Remove all files from staging
git rm -rf .

# Create initial structure
mkdir -p production pr-preview

# Create a placeholder index
cat > index.html <<'EOF'
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Reports - Coming Soon</title>
</head>
<body>
  <h1>Reports Coming Soon</h1>
  <p>Reports will be published here after the first workflow run.</p>
</body>
</html>
EOF

# Commit and push
git add index.html production pr-preview
git commit -m "chore: initialize gh-pages branch"
git push origin gh-pages

# Return to main branch
git checkout main
```text

### Step 3: Configure Repository Permissions

1. Go to **Settings** → **Actions** → **General**
2. Under **Workflow permissions**, select:
   - ✅ **Read and write permissions**
3. Enable **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

### Step 4: Set Up Secrets and Variables

#### Add Secrets

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**

**CLASSIC_READ_ONLY_PAT_TOKEN:**

```text
Name: CLASSIC_READ_ONLY_PAT_TOKEN
Secret: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```text

**LF_GERRIT_INFO_MASTER_SSH_KEY** (optional):

```text
Name: LF_GERRIT_INFO_MASTER_SSH_KEY
Secret: -----BEGIN OPENSSH PRIVATE KEY-----
        [your key content]
        -----END OPENSSH PRIVATE KEY-----
```text

#### Add Variables

1. Click **Variables** tab
2. Click **New repository variable**

**PROJECTS_JSON:**

```text
Name: PROJECTS_JSON
Value: [
  {
    "project": "ONAP",
    "gerrit": "gerrit.onap.org",
    "jenkins": "jenkins.onap.org",
    "github": "onap"
  },
  {
    "project": "O-RAN-SC",
    "gerrit": "gerrit.o-ran-sc.org",
    "jenkins": "jenkins.o-ran-sc.org",
    "github": "o-ran-sc"
  }
]
```text

**Email Notification Variables (Optional):**

To enable email notifications for production report completion:

```text
Name: SEND_EMAIL_NOTIFICATIONS
Value: true
```text

```text
Name: SMTP_SERVER
Value: email-smtp.us-west-2.amazonaws.com
```text

```text
Name: SMTP_USERNAME
Value: AKIAIOSFODNN7EXAMPLE
```text

```text
Name: REPORT_EMAIL_ADDRESS
Value: reports@example.org
```text

**Email Notification Secret:**

```text
Name: SMTP_PASSWORD
Secret: [Your SMTP password or AWS SES credentials]
```text

**Email Notification Configuration:**

The production reports workflow can send email notifications upon completion. To enable:

1. Set `SEND_EMAIL_NOTIFICATIONS` variable to `true`
2. Configure SMTP server details (variables):
   - `SMTP_SERVER` - SMTP server hostname
   - `SMTP_USERNAME` - SMTP username (for AWS SES, this is the SMTP username)
   - `REPORT_EMAIL_ADDRESS` - Recipient email address
3. Add `SMTP_PASSWORD` secret with your SMTP password

The email will include:
- ✅ Completion status with emojis (✅ success, ❌ failure, ⚠️ cancelled, ⏭️ skipped)
- Job results for Verify, Analyze, Publish, and Copy steps
- Links to all published project reports (when successful)
- Direct link to the workflow run

To disable email notifications:
- Set `SEND_EMAIL_NOTIFICATIONS` to `false` or remove the variable

**Note:** The FROM address is set to `no-reply@linuxfoundation.org` and must be verified with your SMTP provider (e.g., AWS SES verified sender).

---

## 🔄 Migration from Old System

### Step 1: Remove Old Token (GERRIT_REPORTS_PAT_TOKEN)

The `GERRIT_REPORTS_PAT_TOKEN` is no longer needed and can be deleted:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Find **GERRIT_REPORTS_PAT_TOKEN**
3. Click **Remove**

### Step 2: Update Workflows

The old `reporting.yaml` workflow has been replaced with:

- **`reporting-production.yaml`** - Production reports (scheduled)
- **`reporting-pr-preview.yaml`** - Preview report reports

The old workflow file has been renamed to `reporting.yaml.deprecated` and is no longer active.

### Step 3: Verify New Workflows

1. Navigate to **Actions** tab
2. You should see two new workflows:
   - 📊 Production Reports
   - 🔍 Preview Report Reports

---

## 📊 Workflow Details

### Production Reports Workflow

**File:** `.github/workflows/reporting-production.yaml`

**Triggers:**

- 🕐 **Schedule:** Monday at 7:00 AM UTC
- 🔧 **Manual:** workflow_dispatch

**What it does:**

1. Validates configuration and secrets
2. Clones all Gerrit repositories (parallel)
3. Clones `info-master` for committer data
4. Generates reports for each project
5. Publishes to `gh-pages` branch at `/production/`
6. Uploads artifacts with 90-day retention

**Output Location:**

```text
https://<owner>.github.io/<repo>/production/<project-slug>/report.html
```text

### Preview Report Workflow

**File:** `.github/workflows/reporting-pr-preview.yaml`

**Triggers:**

- Pull requests modifying:
  - `src/**/*.py`
  - `tests/**/*.py`
  - `.github/workflows/reporting-*.yaml`
  - `.github/scripts/*.sh`
  - `pyproject.toml`
  - `uv.lock`

**What it does:**

1. Runs on PR with code changes
2. Processes **first 2 projects only** (resource conservation)
3. Generates preview reports
4. Publishes to `gh-pages` at `/pr-preview/<pr-number>/`
5. Comments on PR with preview link
6. Uploads artifacts with 30-day retention

**Output Location:**

```text
https://<owner>.github.io/<repo>/pr-preview/<pr-number>/<project-slug>/report.html
```text

**Key Features:**

- ✅ Validates reporting code changes before merge
- ✅ Does NOT overwrite production reports
- ✅ Limited to 2 projects to save CI resources
- ✅ Automatic PR comments with preview links

---

## 🗂️ GitHub Pages Structure

```text
https://<owner>.github.io/<repo>/
├── index.html                          # Landing page
├── production/                         # Production reports
│   ├── index.html                      # Production report list
│   ├── onap/
│   │   ├── report.html
│   │   ├── report_raw.json
│   │   ├── report.md
│   │   └── metadata.json
│   ├── o-ran-sc/
│   │   ├── report.html
│   │   ├── report_raw.json
│   │   └── metadata.json
│   └── ...
└── pr-preview/                         # Preview report reports
    ├── 123/                            # PR number
    │   ├── index.html
    │   ├── onap/
    │   │   └── report.html
    │   └── o-ran-sc/
    │       └── report.html
    └── 456/
        └── ...
```text

---

## 📦 Artifact Retention

### Production Workflow

| Artifact Type | Retention | Purpose |
| ------- | ------- | ------- |
| Raw data (JSON) | 90 days | Meta-reporting, trend analysis |
| Complete reports | 90 days | Full report package |
| Clone manifests | 90 days | Repository tracking |
| Clone logs | 90 days | Debugging |

### Preview Report Workflow

| Artifact Type | Retention | Purpose |
| ------- | ------- | ------- |
| Raw data (JSON) | 30 days | Validation |
| Preview reports | 30 days | Review |
| Clone manifests | 30 days | Debugging |

---

## 🔧 Maintenance

### Manual Trigger

To manually trigger a production report:

1. Go to **Actions** tab
2. Select **📊 Production Reports**
3. Click **Run workflow**
4. Choose branch (usually `main`)
5. Click **Run workflow**

### Viewing Reports

**Production Reports:**

```text
https://<owner>.github.io/<repo>/production/
```text

**Preview Report (after PR created):**

```text
https://<owner>.github.io/<repo>/pr-preview/<pr-number>/
```text

### Downloading Artifacts for Meta-Reporting

Use the provided script to download historical artifact data:

```bash
# Set your GitHub token
export GITHUB_TOKEN=ghp_...

# Download artifacts from last 90 days
.github/scripts/download-artifacts.sh \
  reporting-production.yaml \
  ./meta-report-data \
  90
```text

This downloads all raw JSON data files which can be used to generate:

- Migration progress tracking
- Jenkins job → GitHub Actions transition metrics
- Repository activity trends
- Historical comparisons

---

## 🐛 Troubleshooting

### Reports Not Appearing

**Check GitHub Pages Status:**

1. Go to **Settings** → **Pages**
2. Verify branch is set to `gh-pages`
3. Check for deployment status

**Check Workflow Status:**

1. Go to **Actions** tab
2. Check if workflows completed successfully
3. Review logs for errors

**Check gh-pages Branch:**

```bash
git fetch origin gh-pages
git checkout gh-pages
ls -la production/
```text

### Preview Reports Not Working

**Check PR Comment:**

- Bot should comment on PR with preview link
- If no comment, check workflow logs

**Check gh-pages Branch:**

```bash
git checkout gh-pages
ls -la pr-preview/<pr-number>/
```text

**Permissions Issue:**

- Ensure workflow has `contents: write` permission
- Check repository settings allow Actions to write

### Missing Secrets Error

```text
Error: CLASSIC_READ_ONLY_PAT_TOKEN secret is not set
```text

**Solution:**

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Verify secret exists and is spelled correctly
3. Regenerate token if expired

### Clone Failures

If repository cloning fails:

1. **Check Gerrit server accessibility**
2. **Verify SSH key** (if using SSH)
3. **Check workflow timeout settings**
4. Review clone logs in artifacts

---

## 📈 Monitoring

### Key Metrics to Track

1. **Workflow Success Rate**
   - Monitor in Actions tab
   - Set up notifications for failures

2. **Artifact Storage Usage**
   - Check Settings → Actions → Storage
   - Adjust retention if needed

3. **Report Generation Time**
   - Review workflow run durations
   - Optimize if exceeding 60 minutes

4. **GitHub Pages Deployment**
   - Monitor Pages deployments
   - Check for build errors

---

## 🔐 Security Considerations

### Token Permissions

**CLASSIC_READ_ONLY_PAT_TOKEN:**

- ✅ Use fine-grained token when possible
- ✅ Limit to specific repositories
- ✅ Set expiration date
- ✅ Use read-only permissions only

**Built-in GITHUB_TOKEN:**

- ✅ Automatically scoped to repository
- ✅ Expires after workflow run
- ✅ No manual token management needed

### SSH Keys

**LF_GERRIT_INFO_MASTER_SSH_KEY:**

- ✅ Use dedicated deployment key
- ✅ Limit to read-only access
- ✅ Rotate periodically
- ✅ Monitor usage

---

## 🎯 Best Practices

### Production Reports

1. **Schedule appropriately**
   - Monday 7am UTC catches weekend activity
   - Avoid peak hours

2. **Monitor failures**
   - Set up notifications
   - Review logs regularly

3. **Archive old reports**
   - Download artifacts before retention expires
   - Store externally for long-term analysis

### Preview Reports

1. **Limit scope**
   - Only test with 2 projects
   - Keeps CI costs reasonable

2. **Review before merge**
   - Always check preview reports
   - Verify formatting and data

3. **Clean up old previews**
   - Periodically remove old Preview report directories
   - Keep `gh-pages` branch clean

### Artifacts

1. **Download raw data regularly**
   - Use download script
   - Build historical dataset

2. **Monitor storage usage**
   - Adjust retention if needed
   - Archive important runs externally

---

## 📚 Additional Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Actions Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [Workflow Artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)

---

## 🆘 Getting Help

If you encounter issues:

1. Check this documentation
2. Review workflow logs in Actions tab
3. Check GitHub Pages deployment status
4. Verify all secrets and variables are set
5. Open an issue with:
   - Workflow run link
   - Error messages
   - Steps to reproduce

---

**Last Updated:** 2025-01-XX

**Migration Status:** ✅ Ready for production use
