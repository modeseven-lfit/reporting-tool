#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
#
# Simple script to copy all workflow artifacts to gerrit-reports repository
# Uses git clone/push instead of GitHub API for simplicity and robustness
#
# Usage: copy-artifacts-simple.sh <date-folder> <workflow-run-id> <artifacts-dir> <token>

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ ${NC}$*"
}

log_success() {
    echo -e "${GREEN}✓${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $*"
}

log_error() {
    echo -e "${RED}✗${NC} $*" >&2
}

# Validate inputs
if [ $# -ne 4 ]; then
    log_error "Usage: $0 <date-folder> <workflow-run-id> <artifacts-dir> <token>"
    log_error "  date-folder: Date in YYYY-MM-DD format (e.g., 2025-11-21)"
    log_error "  workflow-run-id: GitHub workflow run ID"
    log_error "  artifacts-dir: Directory containing downloaded artifacts"
    log_error "  token: GitHub PAT token for authentication"
    exit 1
fi

DATE_FOLDER="$1"
WORKFLOW_RUN_ID="$2"
ARTIFACTS_DIR="$3"
GITHUB_TOKEN="$4"

# Validate token
if [ -z "$GITHUB_TOKEN" ]; then
    log_error "GitHub token not provided"
    exit 1
fi

log_info "Token validation: OK"

# Validate date format
if ! [[ "$DATE_FOLDER" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    log_error "Invalid date format: $DATE_FOLDER (expected YYYY-MM-DD)"
    exit 1
fi

# Validate artifacts directory exists
if [ ! -d "$ARTIFACTS_DIR" ]; then
    log_error "Artifacts directory not found: $ARTIFACTS_DIR"
    exit 1
fi

# Convert to absolute path
ARTIFACTS_DIR=$(cd "$ARTIFACTS_DIR" && pwd)

# Repository details
REMOTE_REPO="modeseven-lfit/gerrit-reports"
TARGET_PATH="data/artifacts/${DATE_FOLDER}"
CLONE_DIR=$(mktemp -d)

log_info "=== Starting artifact transfer ==="
log_info "Date folder: ${DATE_FOLDER}"
log_info "Workflow run: ${WORKFLOW_RUN_ID}"
log_info "Artifacts source: ${ARTIFACTS_DIR}"
log_info "Target repository: ${REMOTE_REPO}"
log_info "Target path: ${TARGET_PATH}"
log_info ""

# Cleanup function
cleanup() {
    if [ -d "$CLONE_DIR" ]; then
        log_info "Cleaning up temporary directory..."
        rm -rf "$CLONE_DIR"
    fi
}
trap cleanup EXIT

# Configure git
git config --global user.name "GitHub Actions"
git config --global user.email "actions@github.com"

# Clone the repository
log_info "Cloning ${REMOTE_REPO}..."
if ! git clone "https://x-access-token:${GITHUB_TOKEN}@github.com/${REMOTE_REPO}.git" "$CLONE_DIR"; then
    log_error "Failed to clone repository"
    exit 1
fi

cd "$CLONE_DIR"

# Step 2: Delete existing date folder if it exists
if [ -d "$TARGET_PATH" ]; then
    log_warning "Existing folder found: ${TARGET_PATH}"
    log_info "Removing existing folder..."
    git rm -rf "$TARGET_PATH"
    git commit -m "Remove existing artifacts for ${DATE_FOLDER}" || true
    log_success "Removed existing folder"
fi

# Step 3: Create the target directory
log_info "Creating target directory: ${TARGET_PATH}"
mkdir -p "$TARGET_PATH"

# Step 4: Copy all artifacts
log_info "Copying artifacts..."
TOTAL_ARTIFACTS=0
TOTAL_FILES=0

# Copy each artifact directory
for artifact_dir in "$ARTIFACTS_DIR"/*; do
    if [ ! -d "$artifact_dir" ]; then
        continue
    fi

    artifact_name=$(basename "$artifact_dir")
    target_dir="${TARGET_PATH}/${artifact_name}"

    log_info "  Copying ${artifact_name}..."

    # Create target directory
    mkdir -p "$target_dir"

    # Copy all files from artifact
    file_count=0
    for file in "$artifact_dir"/*; do
        if [ -f "$file" ]; then
            cp "$file" "$target_dir/"
            file_count=$((file_count + 1))
        fi
    done

    log_success "    Copied ${file_count} files to ${artifact_name}/"
    TOTAL_ARTIFACTS=$((TOTAL_ARTIFACTS + 1))
    TOTAL_FILES=$((TOTAL_FILES + file_count))
done

if [ $TOTAL_ARTIFACTS -eq 0 ]; then
    log_error "No artifacts found in ${ARTIFACTS_DIR}"
    exit 1
fi

log_success "Copied ${TOTAL_FILES} files from ${TOTAL_ARTIFACTS} artifacts"

# Create README
log_info "Creating README..."
cat > "${TARGET_PATH}/README.md" << EOF
# Gerrit Reports - ${DATE_FOLDER}

Generated on: $(date -u +"%Y-%m-%d %H:%M:%S UTC")

## Summary

- **Date**: ${DATE_FOLDER}
- **Total Artifacts**: ${TOTAL_ARTIFACTS}
- **Total Files**: ${TOTAL_FILES}
- **Workflow Run**: [${WORKFLOW_RUN_ID}](https://github.com/modeseven-lfit/gerrit-reporting-tool/actions/runs/${WORKFLOW_RUN_ID})

## Contents

This directory contains all artifacts from the production reports workflow run.

Each subdirectory corresponds to a workflow artifact:
- \`reports-<slug>\`: Generated report files (HTML, Markdown, JSON)
- \`raw-data-<slug>\`: Raw data JSON files
- \`clone-log-<slug>\`: Repository clone logs
- \`clone-manifest-<slug>\`: Repository clone manifests

## Artifacts

EOF

# List all artifacts
for artifact_dir in "$TARGET_PATH"/*; do
    if [ -d "$artifact_dir" ] && [ "$(basename "$artifact_dir")" != "README.md" ]; then
        artifact_name=$(basename "$artifact_dir")
        file_count=$(find "$artifact_dir" -type f | wc -l | tr -d ' ')
        echo "- **${artifact_name}**: ${file_count} files" >> "${TARGET_PATH}/README.md"
    fi
done

log_success "Created README.md"

# Add all files to git
log_info "Committing changes..."
git add "$TARGET_PATH"

# Check if there are changes to commit
if git diff --cached --quiet; then
    log_warning "No changes to commit"
    exit 0
fi

# Commit and push
git commit -m "Add artifacts for ${DATE_FOLDER}

- Workflow run: ${WORKFLOW_RUN_ID}
- Artifacts: ${TOTAL_ARTIFACTS}
- Files: ${TOTAL_FILES}
- Generated: $(date -u +"%Y-%m-%d %H:%M:%S UTC")"

log_info "Pushing to remote repository..."
if ! git push origin main; then
    log_error "Failed to push changes"
    exit 1
fi

log_success "✨ Successfully transferred all artifacts!"
log_info "View at: https://github.com/${REMOTE_REPO}/tree/main/${TARGET_PATH}"
