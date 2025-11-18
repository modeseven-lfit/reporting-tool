<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Project Metadata and SSH Key Configuration

This document explains the project metadata system and SSH key handling in the local testing script.

## Overview

The testing script now uses a centralized project metadata file (`projects.json`) to automatically configure:

- Gerrit server hostnames
- Jenkins server hostnames
- GitHub organization names

This eliminates hardcoded server URLs and makes it easy to test multiple Linux Foundation projects.

## Project Metadata

### Location

`testing/projects.json`

### Structure

```json
[
  {
    "project": "ONAP",
    "gerrit": "gerrit.onap.org",
    "jenkins": "jenkins.onap.org"
  },
  {
    "project": "Opendaylight",
    "gerrit": "git.opendaylight.org",
    "jenkins": "jenkins.opendaylight.org"
  }
]
```

### Fields

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `project` | Yes | Project name (used for report directory) | `"ONAP"` |
| `gerrit` | Yes | Gerrit server hostname | `"gerrit.onap.org"` |
| `jenkins` | No | Jenkins server hostname | `"jenkins.onap.org"` |
| `github` | No | GitHub organization name | `"onap"` |

### Supported Projects

The metadata file includes configuration for these Linux Foundation projects:

1. **O-RAN-SC**
   - Gerrit: `gerrit.o-ran-sc.org`
   - Jenkins: `jenkins.o-ran-sc.org`

2. **ONAP**
   - Gerrit: `gerrit.onap.org`
   - Jenkins: `jenkins.onap.org`

3. **Opendaylight**
   - Gerrit: `git.opendaylight.org`
   - Jenkins: `jenkins.opendaylight.org`

4. **AGL (Automotive Grade Linux)**
   - Gerrit: `gerrit.automotivelinux.org`
   - Jenkins: `build.automotivelinux.org`
   - GitHub: `automotive-grade-linux`

5. **OPNFV**
   - Gerrit: `gerrit.opnfv.org`

6. **FDio**
   - Gerrit: `gerrit.fd.io`
   - Jenkins: `jenkins.fd.io`
   - GitHub: `fdio`

7. **LF Broadband**
   - Gerrit: `gerrit.lfbroadband.org`
   - Jenkins: `jenkins.lfbroadband.org`

8. **Linux Foundation**
   - Gerrit: `gerrit.linuxfoundation.org`

## How It Works

### 1. Loading Metadata

The script loads project metadata at startup:

```bash
load_project_metadata() {
    if [ ! -f "${PROJECTS_JSON}" ]; then
        log_error "Project metadata file not found: ${PROJECTS_JSON}"
        exit 1
    fi

    # Check if jq is available
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed"
        exit 1
    fi
}
```

### 2. Retrieving Project Information

The script queries project metadata using `jq`:

```bash
get_project_info() {
    local project_name="$1"
    local field="$2"

    jq -r ".[] | select(.project == \"${project_name}\") | .${field} // empty" "${PROJECTS_JSON}"
}
```

**Example usage:**

```bash
gerrit_host=$(get_project_info "ONAP" "gerrit")
# Returns: "gerrit.onap.org"

jenkins_host=$(get_project_info "ONAP" "jenkins")
# Returns: "jenkins.onap.org"
```

### 3. Automatic Configuration

The script automatically sets environment variables based on project metadata:

```bash
# Set Gerrit configuration
export GERRIT_HOST="${gerrit_host}"
export GERRIT_BASE_URL="https://${gerrit_host}"

# Set Jenkins configuration
export JENKINS_HOST="${jenkins_host}"
export JENKINS_BASE_URL="https://${jenkins_host}"

# Set GitHub organization
export GITHUB_ORG="${github_org}"
```

These environment variables are then used by the reporting tool to:

- Connect to Gerrit API for repository metadata
- Connect to Jenkins API for CI/CD information
- Derive GitHub URLs for workflow status

## SSH Key Configuration

### Why SSH Keys Are Needed

The reporting tool needs SSH access to clone the `info-master` repository from `gerrit.linuxfoundation.org`. This repository contains INFO.yaml files with project metadata and committer information.

### SSH Key Locations

The script checks for SSH keys in this order:

1. **Environment variable** (CI/CD mode):

   ```bash
   LF_GERRIT_INFO_MASTER_SSH_KEY
   ```

2. **Local file** (development mode):

   ```bash
   ~/.ssh/gerrit.linuxfoundation.org
   ```

### Setting Up SSH Keys

#### Option 1: Copy Existing Key (Recommended)

If you already have a Gerrit SSH key:

```bash
# Copy your key to the expected location
cp ~/.ssh/id_rsa ~/.ssh/gerrit.linuxfoundation.org

# Or create a symlink
ln -s ~/.ssh/id_rsa ~/.ssh/gerrit.linuxfoundation.org
```

#### Option 2: Use Environment Variable (CI/CD)

For CI/CD environments:

```bash
export LF_GERRIT_INFO_MASTER_SSH_KEY="$(cat ~/.ssh/id_rsa)"
```

### Automatic SSH Configuration

When a local SSH key is found, the script automatically configures SSH:

```bash
# Creates ~/.ssh/config entry:
Host gerrit.linuxfoundation.org
    HostName gerrit.linuxfoundation.org
    User ${USER}
    Port 29418
    IdentityFile ~/.ssh/gerrit.linuxfoundation.org
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

This allows seamless SSH access to Gerrit without additional configuration.

### Testing SSH Access

Verify your SSH configuration works:

```bash
ssh -p 29418 gerrit.linuxfoundation.org gerrit version
```

Expected output:

```bash
gerrit version 3.x.x
```

### Error Handling

If no SSH key is found, the script exits with a clear error message:

```bash
[ERROR] ❌ SSH key not found: /Users/username/.ssh/gerrit.linuxfoundation.org

To fix this:
  1. Copy your Gerrit SSH key to: /Users/username/.ssh/gerrit.linuxfoundation.org
  2. Or set LF_GERRIT_INFO_MASTER_SSH_KEY environment variable

Example:
  cp ~/.ssh/id_rsa /Users/username/.ssh/gerrit.linuxfoundation.org
  export LF_GERRIT_INFO_MASTER_SSH_KEY=$(cat ~/.ssh/id_rsa)
```

## Adding New Projects

To add a new project to the metadata:

1. **Edit `projects.json`**:

   ```json
   {
     "project": "My-Project",
     "gerrit": "gerrit.myproject.org",
     "jenkins": "jenkins.myproject.org",
     "github": "myproject-org"
   }
   ```

2. **Update the test script** to include the new project:

   ```bash
   # In local-testing.sh main() function:
   local projects=("ONAP" "Opendaylight" "My-Project")
   ```

3. **Run the test script**:

   ```bash
   ./local-testing.sh
   ```

The script will automatically:

- Clone repositories from the Gerrit server
- Configure API access to Gerrit and Jenkins
- Generate reports with proper API integration

## Benefits

### Before (Hardcoded)

```bash
ONAP_SERVER="gerrit.onap.org"
ODL_SERVER="git.opendaylight.org"

clone_onap() {
    uvx gerrit-clone clone --host "${ONAP_SERVER}" ...
}

clone_opendaylight() {
    uvx gerrit-clone clone --host "${ODL_SERVER}" ...
}
```

**Problems:**

- Duplicate code for each project
- Hard to add new projects
- Server URLs scattered throughout script
- No centralized configuration

### After (Metadata-Driven)

```bash
clone_project() {
    local project_name="$1"
    local gerrit_host="$2"

    uvx gerrit-clone clone --host "${gerrit_host}" ...
}

# In main():
for project in "${projects[@]}"; do
    local gerrit_host=$(get_project_info "${project}" "gerrit")
    clone_project "${project}" "${gerrit_host}"
done
```

**Benefits:**

- ✅ Single function handles all projects
- ✅ Easy to add new projects (edit JSON only)
- ✅ Centralized configuration
- ✅ Consistent handling across projects
- ✅ Automatic API configuration

## Troubleshooting

### "jq is not installed"

Install jq for JSON parsing:

```bash
# macOS
brew install jq

# Debian/Ubuntu
sudo apt-get install jq

# Fedora/RHEL
sudo dnf install jq
```

### "Project metadata file not found"

Ensure you're running the script from the testing directory:

```bash
cd reporting-tool/testing
./local-testing.sh
```

### "No Gerrit host found for project"

The project may not be in `projects.json`. Add it:

```json
{
  "project": "YourProject",
  "gerrit": "gerrit.yourproject.org"
}
```

### SSH Key Not Working

1. **Check key exists**:

   ```bash
   ls -la ~/.ssh/gerrit.linuxfoundation.org
   ```

2. **Check permissions**:

   ```bash
   chmod 600 ~/.ssh/gerrit.linuxfoundation.org
   ```

3. **Test SSH connection**:

   ```bash
   ssh -vvv -p 29418 gerrit.linuxfoundation.org gerrit version
   ```

4. **Verify public key is in Gerrit**:
   - Go to <https://gerrit.linuxfoundation.org/>
   - Settings → SSH Keys
   - Add your public key if missing

## See Also

- [Local Testing README](README.md) - Main testing documentation
- [API Access Configuration](API_ACCESS.md) - Detailed API setup guide
- [projects.json](projects.json) - Project metadata file
