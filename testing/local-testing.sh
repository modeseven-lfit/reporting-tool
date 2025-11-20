#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory (assuming script is in reporting-tool/testing/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Configuration
CLONE_BASE_DIR="/tmp"
REPORT_BASE_DIR="/tmp/reports"
PROJECTS_JSON="${SCRIPT_DIR}/projects.json"

# SSH key configuration
SSH_KEY_PATH="${HOME}/.ssh/gerrit.linuxfoundation.org"

# Logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Load project metadata
load_project_metadata() {
    if [ ! -f "${PROJECTS_JSON}" ]; then
        log_error "Project metadata file not found: ${PROJECTS_JSON}"
        exit 1
    fi

    # Check if jq is available for JSON parsing
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install jq for JSON parsing:"
        log_error "  brew install jq  # macOS"
        log_error "  apt-get install jq  # Debian/Ubuntu"
        exit 1
    fi
}

# Get project info from metadata
get_project_info() {
    local project_name="$1"
    local field="$2"

    jq -r ".[] | select(.project == \"${project_name}\") | .${field} // empty" "${PROJECTS_JSON}"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if uvx is available
    if ! command -v uvx &> /dev/null; then
        log_error "uvx is not installed. Please install uv first:"
        log_error "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    # Check if git is available
    if ! command -v git &> /dev/null; then
        log_error "git is not installed. Please install git."
        exit 1
    fi

    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed. Please install jq:"
        log_error "  brew install jq  # macOS"
        log_error "  apt-get install jq  # Debian/Ubuntu"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Check and configure SSH key
check_ssh_key() {
    log_info "Checking SSH key configuration..."

    # Check if SSH key is set in environment (CI mode)
    if [ -n "${LF_GERRIT_INFO_MASTER_SSH_KEY:-}" ]; then
        log_success "SSH key found in LF_GERRIT_INFO_MASTER_SSH_KEY environment variable"
        return 0
    fi

    # Check if SSH key file exists locally
    if [ -f "${SSH_KEY_PATH}" ]; then
        log_success "SSH key found at ${SSH_KEY_PATH}"

        # Set up SSH config for info-master access
        log_info "Configuring SSH for info-master access..."

        # Ensure SSH directory exists
        mkdir -p ~/.ssh
        chmod 700 ~/.ssh

        # Check if SSH config already has the entry
        if ! grep -q "Host gerrit.linuxfoundation.org" ~/.ssh/config 2>/dev/null; then
            log_info "Adding SSH config entry for gerrit.linuxfoundation.org"
            cat >> ~/.ssh/config <<EOF

Host gerrit.linuxfoundation.org
    HostName gerrit.linuxfoundation.org
    User ${USER}
    Port 29418
    IdentityFile ${SSH_KEY_PATH}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
EOF
            chmod 600 ~/.ssh/config
        fi

        return 0
    fi

    # SSH key not found
    log_error "❌ SSH key not found: ${SSH_KEY_PATH}"
    log_error ""
    log_error "To fix this:"
    log_error "  1. Copy your Gerrit SSH key to: ${SSH_KEY_PATH}"
    log_error "  2. Or set LF_GERRIT_INFO_MASTER_SSH_KEY environment variable"
    log_error ""
    log_error "Example:"
    log_error "  cp ~/.ssh/id_rsa ${SSH_KEY_PATH}"
    log_error "  export LF_GERRIT_INFO_MASTER_SSH_KEY=\$(cat ~/.ssh/id_rsa)"
    exit 1
}

# Check API configuration
check_api_configuration() {
    log_info "Checking API configuration..."

    local has_github_token=false
    local github_token_env="GITHUB_TOKEN"

    # Check for GitHub token - support both GITHUB_TOKEN and CLASSIC_READ_ONLY_PAT_TOKEN
    if [ -n "${CLASSIC_READ_ONLY_PAT_TOKEN:-}" ]; then
        log_success "GitHub API: CLASSIC_READ_ONLY_PAT_TOKEN is set"
        has_github_token=true
        github_token_env="CLASSIC_READ_ONLY_PAT_TOKEN"
    elif [ -n "${GITHUB_TOKEN:-}" ]; then
        log_success "GitHub API: GITHUB_TOKEN is set"
        has_github_token=true
        github_token_env="GITHUB_TOKEN"
    else
        log_warning "GitHub API: Neither GITHUB_TOKEN nor CLASSIC_READ_ONLY_PAT_TOKEN is set"
    fi

    # Store the token env var name for later use
    export GITHUB_TOKEN_ENV="${github_token_env}"

    # Check for Gerrit config (optional - not used by current implementation)
    if [ -n "${GERRIT_HOST:-}" ]; then
        log_success "Gerrit API: GERRIT_HOST is set (${GERRIT_HOST})"
    else
        log_info "Gerrit API: Not configured (using projects.json configuration)"
    fi

    # Check for Jenkins config (optional - will use projects.json configuration)
    if [ -n "${JENKINS_HOST:-}" ]; then
        log_success "Jenkins API: JENKINS_HOST is set (${JENKINS_HOST})"
    else
        log_info "Jenkins API: Will use configuration from projects.json"
    fi

    echo ""

    if [ "$has_github_token" = false ]; then
        log_warning "=========================================="
        log_warning "⚠️  GITHUB TOKEN NOT SET"
        log_warning "=========================================="
        log_warning "Reports will use GitHub API with rate limits."
        log_warning ""
        log_warning "For full GitHub API access, set ONE of:"
        log_warning "  1. GITHUB_TOKEN environment variable"
        log_warning "  2. CLASSIC_READ_ONLY_PAT_TOKEN environment variable"
        log_warning ""
        log_warning "See testing/API_ACCESS.md for details"
        log_warning ""
        log_warning "Without a token, you may hit rate limits"
        log_warning "but reports will still include:"
        log_warning "  ✅ Local git data (commits, authors, etc.)"
        log_warning "  ✅ Jenkins CI/CD information (from projects.json)"
        log_warning "  ✅ INFO.yaml project data"
        log_warning "  ⚠️  GitHub workflows (limited by rate limits, NO STATUS COLORS)"
        log_warning "=========================================="
        echo ""
    else
        log_success "✅ Full API access configured using ${github_token_env}"
        log_success "   Reports will include GitHub workflow status colors"
    fi

    # Note about Jenkins and Gerrit
    log_info "📝 Note: Jenkins and Gerrit URLs are configured in testing/projects.json"
    log_info "   The report tool will automatically use those configurations."
}

# Clean up existing report directories only
cleanup_directories() {
    log_info "Cleaning up existing report directories..."

    if [ -d "${ONAP_REPORT_DIR}/ONAP" ]; then
        log_warning "Removing existing ${ONAP_REPORT_DIR}/ONAP"
        rm -rf "${ONAP_REPORT_DIR}/ONAP"
    fi

    if [ -d "${ODL_REPORT_DIR}/OpenDaylight" ]; then
        log_warning "Removing existing ${ODL_REPORT_DIR}/OpenDaylight"
        rm -rf "${ODL_REPORT_DIR}/OpenDaylight"
    fi

    log_success "Cleanup complete"
}



# Clone project repositories
clone_project() {
    local project_name="$1"
    local gerrit_host="$2"
    local clone_dir="${CLONE_BASE_DIR}/${gerrit_host}"

    if [ -d "${clone_dir}" ]; then
        log_info "${project_name} repositories already exist at ${clone_dir}, skipping clone"
        return 0
    fi

    log_info "Cloning ${project_name} repositories from ${gerrit_host} to ${clone_dir}..."

    if gerrit-clone-action \
        --host "${gerrit_host}" \
        --path-prefix "${clone_dir}" \
        --skip-archived \
        --threads 4 \
        --clone-timeout 600 \
        --retry-attempts 3 \
        --move-conflicting; then
        log_success "${project_name} repositories cloned successfully to ${clone_dir}"
        return 0
    else
        log_error "Failed to clone ${project_name} repositories"
        return 1
    fi
}

# Generate project report
generate_project_report() {
    local project_name="$1"
    local gerrit_host="$2"
    local jenkins_host="$3"
    local github_org="$4"
    local clone_dir="${CLONE_BASE_DIR}/${gerrit_host}"

    log_info "Generating ${project_name} report..."

    if [ ! -d "${clone_dir}" ]; then
        log_error "${project_name} clone directory not found: ${clone_dir}"
        return 1
    fi

    cd "${REPO_ROOT}"

    # Build command with optional parameters
    local cmd="uv run reporting-tool generate \
        --project \"${project_name}\" \
        --repos-path \"${clone_dir}\" \
        --output-dir \"${REPORT_BASE_DIR}\" \
        --cache \
        --workers 4"

    # Add github-token-env flag if using CLASSIC_READ_ONLY_PAT_TOKEN
    if [ -n "${GITHUB_TOKEN_ENV:-}" ] && [ "${GITHUB_TOKEN_ENV}" != "GITHUB_TOKEN" ]; then
        cmd="${cmd} \
        --github-token-env \"${GITHUB_TOKEN_ENV}\""
    fi

    # Add Gerrit host if available
    if [ -n "${gerrit_host}" ]; then
        export GERRIT_HOST="${gerrit_host}"
        export GERRIT_BASE_URL="https://${gerrit_host}"
    fi

    # Add Jenkins host if available
    if [ -n "${jenkins_host}" ]; then
        export JENKINS_HOST="${jenkins_host}"
        export JENKINS_BASE_URL="https://${jenkins_host}"
    fi

    # Add GitHub org if available
    if [ -n "${github_org}" ]; then
        export GITHUB_ORG="${github_org}"
    fi

    # Execute the command
    if eval "${cmd}"; then
        log_success "${project_name} report generated successfully in ${REPORT_BASE_DIR}/${project_name}"
        return 0
    else
        log_error "Failed to generate ${project_name} report"
        return 1
    fi
}

# Display summary
show_summary() {
    echo ""
    log_info "=========================================="
    log_info "Testing Complete - Summary"
    log_info "=========================================="
    echo ""

    log_info "Clone Directories:"
    # Use a while loop with proper quoting to avoid jq parsing errors
    jq -c '.[]' "${PROJECTS_JSON}" 2>/dev/null | while IFS= read -r project_data; do
        local project
        project=$(echo "$project_data" | jq -r '.project // "Unknown"' 2>/dev/null)
        local gerrit
        gerrit=$(echo "$project_data" | jq -r '.gerrit // empty' 2>/dev/null)

        if [ -n "${gerrit}" ]; then
            local clone_dir="${CLONE_BASE_DIR}/${gerrit}"
            if [ -d "${clone_dir}" ]; then
                echo "  - ${project}: ${clone_dir}"
            fi
        fi
    done
    echo ""

    log_info "Report Directories:"
    echo "  - All reports: ${REPORT_BASE_DIR}"
    echo ""

    log_info "Generated Reports:"
    for project_dir in "${REPORT_BASE_DIR}"/*; do
        if [ -d "${project_dir}" ]; then
            local project_name
            project_name=$(basename "${project_dir}")
            echo "  ${project_name} reports:"
            find "${project_dir}" -maxdepth 1 -type f -exec basename {} \; | while read -r file; do
                size=$(du -h "${project_dir}/${file}" 2>/dev/null | cut -f1)
                echo "    ${file} (${size})"
            done
            echo ""
        fi
    done

    log_success "You can now review the reports manually!"
    echo ""
}

# Main execution
main() {
    log_info "=========================================="
    log_info "Local Testing Script for Reporting Tool"
    log_info "=========================================="
    echo ""

    # Step 1: Load project metadata
    load_project_metadata

    # Step 2: Check prerequisites
    check_prerequisites
    echo ""

    # Step 3: Check SSH key
    check_ssh_key
    echo ""

    # Step 4: Check API configuration
    check_api_configuration

    # Step 5: Create base directories
    mkdir -p "${CLONE_BASE_DIR}"
    mkdir -p "${REPORT_BASE_DIR}"

    # Get projects to process (ONAP and Opendaylight for now)
    local projects=("ONAP" "Opendaylight")

    # Step 6: Clone repositories
    log_info "Step 1/2: Cloning Gerrit Repositories"
    log_info "------------------------------------------"
    for project in "${projects[@]}"; do
        local gerrit_host
        gerrit_host=$(get_project_info "${project}" "gerrit")

        if [ -n "${gerrit_host}" ]; then
            clone_project "${project}" "${gerrit_host}"
            echo ""
        else
            log_warning "No Gerrit host found for ${project}, skipping clone"
        fi
    done

    # Step 7: Generate reports
    log_info "Step 2/2: Generating Reports"
    log_info "------------------------------------------"
    for project in "${projects[@]}"; do
        local gerrit_host
        gerrit_host=$(get_project_info "${project}" "gerrit")
        local jenkins_host
        jenkins_host=$(get_project_info "${project}" "jenkins")
        local github_org
        github_org=$(get_project_info "${project}" "github")

        if [ -n "${gerrit_host}" ]; then
            # Clean up existing report directory for this project
            if [ -d "${REPORT_BASE_DIR}/${project}" ] && [ -n "${REPORT_BASE_DIR}" ] && [ -n "${project}" ]; then
                log_warning "Removing existing ${REPORT_BASE_DIR}/${project}"
                rm -rf "${REPORT_BASE_DIR:?}/${project}"
            fi

            generate_project_report "${project}" "${gerrit_host}" "${jenkins_host}" "${github_org}"
            echo ""
        else
            log_warning "No Gerrit host found for ${project}, skipping report generation"
        fi
    done

    # Step 8: Show summary
    show_summary
}

# Run main function
main "$@"
